"""Metadata-only persistence for reproducible Debit Draft snapshots.

This module deliberately sits outside the financial-ledger write paths. It
stores the already-derived report/debit payload, source references, and
version identity. It never writes obligations, transactions, allocations,
corrections, payments, or a derived financial position.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from core.debit_draft import (
    DEBIT_STATUS_DRAFT,
    DEBIT_STATUS_READY_FOR_REVIEW,
    DEBIT_STATUS_SUPERSEDED,
    snapshot_content_hash,
)
from core.utils import utc_now


SNAPSHOT_COLLECTION = "debit_draft_snapshots"
SNAPSHOT_DOCUMENT_TYPE = "DEBIT_DRAFT_SNAPSHOT"
SNAPSHOT_STATUSES = frozenset(
    {DEBIT_STATUS_DRAFT, DEBIT_STATUS_READY_FOR_REVIEW, DEBIT_STATUS_SUPERSEDED}
)
SNAPSHOT_REQUEST_INDEX = "uq_debit_draft_snapshot_request"


class DebitSnapshotConflictError(RuntimeError):
    """Raised when one request identity is reused for different content."""


def _string(value: Any) -> str:
    return str(value or "").strip()


def _period(document: Mapping[str, Any]) -> dict[str, Any]:
    period = document.get("period")
    if not isinstance(period, Mapping):
        return {"start": None, "end": None}
    return {"start": period.get("start"), "end": period.get("end")}


def _add_unique(target: list[str], values: Iterable[Any]) -> None:
    for value in values:
        token = _string(value)
        if token and token not in target:
            target.append(token)


def _reference_sets(debit_draft: Mapping[str, Any], manager_report: Mapping[str, Any]) -> dict[str, list[str]]:
    result = {
        "ledger_record_ids": [],
        "obligation_ids": [],
        "transaction_ids": [],
        "allocation_ids": [],
        "correction_ids": [],
        "shipment_ids": [],
    }
    by_currency = debit_draft.get("by_currency") or {}
    if not isinstance(by_currency, Mapping):
        by_currency = {}
    for values in by_currency.values():
        if not isinstance(values, Mapping):
            continue
        references = values.get("references") or {}
        if isinstance(references, Mapping):
            for name in result:
                _add_unique(result[name], references.get(name) or [])
        for line in [*(values.get("included_items") or []), *(values.get("excluded_items") or [])]:
            if not isinstance(line, Mapping):
                continue
            _add_unique(result["ledger_record_ids"], line.get("source_record_ids") or [])
            _add_unique(result["obligation_ids"], [line.get("obligation_id")])
            _add_unique(result["transaction_ids"], [line.get("transaction_id")])
            _add_unique(result["allocation_ids"], line.get("allocation_ids") or [])
            state = line.get("correction_reversal_state") or {}
            if isinstance(state, Mapping):
                _add_unique(result["correction_ids"], [state.get("correction_id"), state.get("reversed_by")])
            _add_unique(result["shipment_ids"], line.get("shipment_ids") or [])
    report_preview = manager_report.get("debit_preview") if isinstance(manager_report, Mapping) else None
    if isinstance(report_preview, Mapping) and report_preview is not debit_draft:
        preview_refs = _reference_sets(report_preview, {})
        for name in result:
            _add_unique(result[name], preview_refs[name])
    return result


def _correction_reversal_states(debit_draft: Mapping[str, Any]) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    for currency, values in (debit_draft.get("by_currency") or {}).items():
        if not isinstance(values, Mapping):
            continue
        for line in [*(values.get("included_items") or []), *(values.get("excluded_items") or [])]:
            if not isinstance(line, Mapping):
                continue
            state = line.get("correction_reversal_state") or {}
            if not isinstance(state, Mapping):
                continue
            states.append(
                {
                    "currency": str(currency),
                    "bucket": line.get("bucket"),
                    "record_id": line.get("record_id"),
                    "status": state.get("status"),
                    "is_reversed": bool(state.get("is_reversed")),
                    "reversed_by": state.get("reversed_by"),
                    "correction_id": state.get("correction_id"),
                }
            )
    return states


def _stable_content(
    debit_draft: Mapping[str, Any],
    manager_report: Mapping[str, Any],
    *,
    period: Mapping[str, Any],
    party_key: str,
    sale_owner: str,
) -> dict[str, Any]:
    return {
        "document_type": SNAPSHOT_DOCUMENT_TYPE,
        "period": deepcopy(dict(period)),
        "party_key": party_key,
        "sale_owner": sale_owner,
        "debit_draft": deepcopy(dict(debit_draft)),
        "manager_report": deepcopy(dict(manager_report)),
    }


def build_debit_snapshot_document(
    debit_draft: Mapping[str, Any],
    *,
    manager_report: Mapping[str, Any] | None = None,
    request_id: str,
    prepared_by: str = "system",
    version: int = 1,
    status: str = DEBIT_STATUS_READY_FOR_REVIEW,
    snapshot_id: str | None = None,
    supersedes_snapshot_id: str | None = None,
    generated_at: Any | None = None,
) -> dict[str, Any]:
    """Build a Mongo-ready snapshot without performing any write."""

    if status not in SNAPSHOT_STATUSES:
        raise ValueError(f"unsupported debit snapshot status: {status}")
    stable_request_id = _string(request_id)
    if not stable_request_id:
        raise ValueError("request_id is required for a Debit Draft snapshot")
    if int(version) < 1:
        raise ValueError("snapshot version must be positive")
    debit_copy = deepcopy(dict(debit_draft))
    report_copy = deepcopy(dict(manager_report or {}))
    period = _period(debit_copy)
    party_key = _string(debit_copy.get("party_key") or report_copy.get("party_key"))
    sale_owner = _string(debit_copy.get("internal_sale_owner") or debit_copy.get("sale_owner") or report_copy.get("sale_owner"))
    references = _reference_sets(debit_copy, report_copy)
    by_currency = debit_copy.get("by_currency") or {}
    totals_by_currency = {
        str(currency): {
            "payable_subtotal": values.get("payable_subtotal", 0),
            "credit_subtotal": values.get("credit_subtotal", 0),
            "settled_amount": values.get("settled_amount", 0),
            "received_on_behalf_allocated": values.get("received_on_behalf_allocated", 0),
            "debit_ready_amount": values.get("debit_ready_amount", 0),
        }
        for currency, values in by_currency.items()
        if isinstance(values, Mapping)
    }
    exclusions_by_currency = {
        str(currency): deepcopy(values.get("excluded_items") or [])
        for currency, values in by_currency.items()
        if isinstance(values, Mapping)
    }
    content_hash = snapshot_content_hash(
        _stable_content(
            debit_copy,
            report_copy,
            period=period,
            party_key=party_key,
            sale_owner=sale_owner,
        )
    )
    return {
        "document_type": SNAPSHOT_DOCUMENT_TYPE,
        "snapshot_id": _string(snapshot_id) or f"debit-snapshot-{uuid4().hex}",
        "request_id": stable_request_id,
        "version": int(version),
        "status": status,
        "supersedes_snapshot_id": _string(supersedes_snapshot_id) or None,
        "period": period,
        "party": deepcopy(debit_copy.get("party") or report_copy.get("party") or {}),
        "party_key": party_key,
        "sale_owner": sale_owner,
        "currencies": sorted(str(value) for value in (debit_copy.get("currencies") or by_currency.keys())),
        "debit_draft": debit_copy,
        "manager_report": report_copy,
        "references": references,
        "ledger_record_ids": references["ledger_record_ids"],
        "obligation_ids": references["obligation_ids"],
        "transaction_ids": references["transaction_ids"],
        "allocation_ids": references["allocation_ids"],
        "correction_ids": references["correction_ids"],
        "shipment_ids": references["shipment_ids"],
        "correction_reversal_state": _correction_reversal_states(debit_copy),
        "totals_by_currency": totals_by_currency,
        "exclusions_by_currency": exclusions_by_currency,
        "content_hash": content_hash,
        "generated_at": generated_at if generated_at is not None else utc_now(),
        "prepared_by": _string(prepared_by) or "system",
        "read_only": True,
        "financial_effect_write_count": 0,
        "deterministic": True,
    }


def next_debit_snapshot_version(
    db: Any,
    *,
    party_key: str,
    sale_owner: str,
    period: Mapping[str, Any],
) -> int:
    """Return the next version for one party/owner/period scope."""

    query = {
        "document_type": SNAPSHOT_DOCUMENT_TYPE,
        "party_key": _string(party_key),
        "sale_owner": _string(sale_owner),
        "period.start": period.get("start"),
        "period.end": period.get("end"),
    }
    versions = []
    for row in db[SNAPSHOT_COLLECTION].find(query, {"version": 1}):
        try:
            versions.append(int(row.get("version") or 0))
        except (TypeError, ValueError):
            continue
    return max(versions, default=0) + 1


def ensure_debit_snapshot_index(db: Any) -> Any:
    """Ensure retry identity is unique without touching financial collections."""

    return db[SNAPSHOT_COLLECTION].create_index(
        "request_id",
        unique=True,
        name=SNAPSHOT_REQUEST_INDEX,
        partialFilterExpression={"request_id": {"$type": "string"}},
    )


def get_debit_draft_snapshot(
    db: Any,
    *,
    snapshot_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any] | None:
    """Read one snapshot by immutable snapshot or retry identity."""

    stable_snapshot_id = _string(snapshot_id)
    stable_request_id = _string(request_id)
    if not stable_snapshot_id and not stable_request_id:
        raise ValueError("snapshot_id or request_id is required")
    query = {"snapshot_id": stable_snapshot_id} if stable_snapshot_id else {"request_id": stable_request_id}
    return db[SNAPSHOT_COLLECTION].find_one(query)


def list_debit_draft_snapshots(
    db: Any,
    *,
    party_key: str,
    sale_owner: str,
    period: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """List metadata snapshots for the reopen/version surface."""

    query: dict[str, Any] = {
        "document_type": SNAPSHOT_DOCUMENT_TYPE,
        "party_key": _string(party_key),
        "sale_owner": _string(sale_owner),
    }
    if period is not None:
        query["period.start"] = period.get("start")
        query["period.end"] = period.get("end")
    rows = list(db[SNAPSHOT_COLLECTION].find(query))
    return sorted(rows, key=lambda row: int(row.get("version") or 0), reverse=True)


def save_debit_draft_snapshot(
    db: Any,
    debit_draft: Mapping[str, Any],
    *,
    manager_report: Mapping[str, Any] | None = None,
    request_id: str,
    prepared_by: str = "system",
    version: int | None = None,
    status: str = DEBIT_STATUS_READY_FOR_REVIEW,
    supersedes_snapshot_id: str | None = None,
    generated_at: Any | None = None,
) -> dict[str, Any]:
    """Insert one immutable metadata snapshot with retry-safe identity."""

    stable_request_id = _string(request_id)
    if not stable_request_id:
        raise ValueError("request_id is required for a Debit Draft snapshot")
    collection = db[SNAPSHOT_COLLECTION]
    ensure_debit_snapshot_index(db)
    existing = collection.find_one({"request_id": stable_request_id})
    period = _period(debit_draft)
    party_key = _string(debit_draft.get("party_key"))
    sale_owner = _string(debit_draft.get("internal_sale_owner") or debit_draft.get("sale_owner"))
    report_copy = manager_report or {}
    stable_content_hash = snapshot_content_hash(
        _stable_content(
            debit_draft,
            report_copy,
            period=period,
            party_key=party_key,
            sale_owner=sale_owner,
        )
    )
    if existing is not None:
        if _string(existing.get("content_hash")) != stable_content_hash:
            raise DebitSnapshotConflictError(
                f"request_id {stable_request_id} đã tồn tại với nội dung Debit Draft khác"
            )
        return {"ok": True, "created": False, "reused": True, "snapshot": existing, "message": "retry_reused"}
    if version is None:
        version = next_debit_snapshot_version(
            db,
            party_key=party_key,
            sale_owner=sale_owner,
            period=period,
        )
    document = build_debit_snapshot_document(
        debit_draft,
        manager_report=report_copy,
        request_id=stable_request_id,
        prepared_by=prepared_by,
        version=version,
        status=status,
        supersedes_snapshot_id=supersedes_snapshot_id,
        generated_at=generated_at,
    )
    try:
        collection.insert_one(document)
    except DuplicateKeyError:
        retry = collection.find_one({"request_id": stable_request_id})
        if retry is not None and _string(retry.get("content_hash")) == stable_content_hash:
            return {"ok": True, "created": False, "reused": True, "snapshot": retry, "message": "retry_reused"}
        raise DebitSnapshotConflictError(
            f"request_id {stable_request_id} đã được dùng cho nội dung Debit Draft khác"
        ) from None
    if supersedes_snapshot_id:
        collection.update_one(
            {"snapshot_id": _string(supersedes_snapshot_id)},
            {
                "$set": {
                    "status": DEBIT_STATUS_SUPERSEDED,
                    "superseded_by_snapshot_id": document["snapshot_id"],
                    "updated_at": utc_now(),
                }
            },
        )
    return {"ok": True, "created": True, "reused": False, "snapshot": document, "message": "created"}


__all__ = [
    "DebitSnapshotConflictError",
    "SNAPSHOT_COLLECTION",
    "SNAPSHOT_DOCUMENT_TYPE",
    "SNAPSHOT_REQUEST_INDEX",
    "SNAPSHOT_STATUSES",
    "build_debit_snapshot_document",
    "ensure_debit_snapshot_index",
    "get_debit_draft_snapshot",
    "list_debit_draft_snapshots",
    "next_debit_snapshot_version",
    "save_debit_draft_snapshot",
]
