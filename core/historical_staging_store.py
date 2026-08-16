"""Staging-only persistence and review audit helpers for LOG-C06.

The store deliberately accepts a database-like object instead of importing the
application's canonical database provider.  A caller may pass Mongo's database
handle or an isolated fake mapping in tests.  No function in this module writes
financial obligations, transactions, allocations, corrections, payments, or
canonical partner projections.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping
from uuid import uuid4

from core.historical_staging import (
    PARSER_VERSION,
    SALE_OWNER,
    STAGING_STATES,
    UNKNOWN_CURRENCY,
)


STAGING_COLLECTION = "legacy_historical_staging"
REVIEW_ACTIONS_COLLECTION = "legacy_historical_review_actions"
REVIEW_ACTIONS = frozenset({"confirm", "correct", "lineage_repair", "not_thanh", "unknown"})
REVIEW_ACTION_STATUSES = frozenset({"APPLIED", "IDEMPOTENT"})
REVIEW_METADATA_FIELDS = frozenset(
    {"review_status", "review_reason", "review_history", "review_version", "proposal"}
)
PROPOSAL_CORRECTION_FIELDS = frozenset(
    {
        "internal_sale_owner",
        "candidate_internal_sale_owner",
        "source",
        "payer",
        "holder",
        "beneficial_owner",
        "beneficiary",
        "customer",
        "a_bo_relationship",
        "shipment",
        "financial_case",
        "event_type",
        "amount",
        "currency",
        "fx_rate",
        "related_amount",
        "related_currency",
        "classification",
        "restriction",
        "candidate_allocation",
        "candidate_bucket",
        "evidence_sufficiency",
        "confidence",
        "reasons",
        "anomalies",
        "sale_evidence",
        "sale_confidence",
        "source_party_evidence",
        "checkpoint_key",
        "checkpoint_references",
        "checkpoint_component_ids",
        "checkpoint_operation",
        "checkpoint_formula",
        "checkpoint_group_key",
        "checkpoint_summary_amount",
        "checkpoint_source_item_id",
        "owner_decision_batch",
        "owner_decision_id",
        "owner_decision_status",
        "owner_decision_ids",
        "business_context",
        "financial_effect",
        "allocation_status",
        "settlement_status",
        "money_legs",
        "receipt_leg",
        "paid_on_behalf_leg",
        "fx_context",
        "opening_inclusion",
        "opening_lineage",
        "reconciliation_role",
        "historical_group_key",
        "checkpoint_component_group",
        "amount_source_cell",
        "amount_source_label",
        "amount_source_raw_value",
        "amount_source_kind",
        "technical_lineage",
        "technical_lineage_status",
        "technical_lineage_repair_id",
        "superseded_owner_decision_id",
        "parser_version",
    }
)
IMMUTABLE_SOURCE_FIELDS = frozenset(
    {
        "source_item_id",
        "source_file",
        "source_file_hash",
        "sheet",
        "source_row",
        "source_cell_range",
        "source_reference",
        "raw_values",
        "raw_cell_types",
        "raw_text",
        "raw_note",
        "raw_date",
        "raw_date_serial",
        "inherited_date_context",
        "raw_sale",
        "raw_customer",
        "raw_reference",
        "raw_amount",
        "raw_currency",
        "parser_version",
        "imported_at",
    }
)


class StagingStoreError(RuntimeError):
    """Base error for a staging-only persistence or review failure."""


class ReviewActionConflict(StagingStoreError):
    """Raised when a retry or concurrent review request is not safe to apply."""


class ReviewValidationError(StagingStoreError):
    """Raised when an action would create an invalid staging proposal."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _collection(db: Any, name: str) -> Any:
    if db is None:
        raise StagingStoreError("Staging database is unavailable; no hidden fallback was used.")
    try:
        return db[name]
    except (KeyError, TypeError, AttributeError):
        collection = getattr(db, name, None)
        if collection is None:
            raise StagingStoreError(f"Staging collection {name!r} is unavailable.")
        return collection


def _find_one(collection: Any, query: Mapping[str, Any]) -> dict[str, Any] | None:
    result = collection.find_one(dict(query))
    return deepcopy(dict(result)) if result is not None else None


def _find_many(collection: Any, query: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    result = collection.find(dict(query or {}))
    return [deepcopy(dict(item)) for item in result]


def _insert_one(collection: Any, document: Mapping[str, Any]) -> None:
    collection.insert_one(deepcopy(dict(document)))


def _replace_one(collection: Any, query: Mapping[str, Any], document: Mapping[str, Any]) -> None:
    result = collection.replace_one(dict(query), deepcopy(dict(document)), upsert=False)
    matched = getattr(result, "matched_count", None)
    if matched is not None and matched != 1:
        raise StagingStoreError("Staging item disappeared before the review update completed.")


def _create_index(collection: Any, keys: list[tuple[str, int]], *, unique: bool, name: str) -> Any:
    creator = getattr(collection, "create_index", None)
    if creator is None:
        return None
    return creator(keys, unique=unique, name=name)


def ensure_staging_indexes(db: Any) -> dict[str, Any]:
    """Create only the two indexes required by the staging/audit boundary."""

    staging = _collection(db, STAGING_COLLECTION)
    actions = _collection(db, REVIEW_ACTIONS_COLLECTION)
    return {
        "staging_source_item_id": _create_index(
            staging, [("source_item_id", 1)], unique=True, name="c06_source_item_id_unique"
        ),
        "staging_source_lookup": _create_index(
            staging,
            [("source_file_hash", 1), ("sheet", 1), ("source_row", 1)],
            unique=True,
            name="c06_source_row_unique",
        ),
        "review_request_id": _create_index(
            actions, [("request_id", 1)], unique=True, name="c06_review_request_unique"
        ),
        "review_source_item_id": _create_index(
            actions, [("source_item_id", 1), ("acted_at", 1)], unique=False, name="c06_review_item_time"
        ),
    }


def _merge_import(existing: Mapping[str, Any] | None, incoming: Mapping[str, Any]) -> dict[str, Any]:
    """Merge a deterministic import while preserving review metadata and raw evidence."""

    if existing is None:
        document = deepcopy(dict(incoming))
        document.setdefault("review_version", 0)
        document.setdefault("review_history", [])
        return document

    current = deepcopy(dict(existing))
    incoming_copy = deepcopy(dict(incoming))
    for field in IMMUTABLE_SOURCE_FIELDS:
        if field in current:
            incoming_copy[field] = deepcopy(current[field])
    has_review_history = bool(current.get("review_history")) or current.get("review_status") not in {
        None,
        "RAW",
    }
    if has_review_history:
        for field in REVIEW_METADATA_FIELDS:
            if field in current:
                incoming_copy[field] = deepcopy(current[field])
    incoming_copy["review_version"] = int(current.get("review_version") or 0)
    incoming_copy.setdefault("review_history", deepcopy(current.get("review_history") or []))
    if "_id" in current:
        incoming_copy["_id"] = current["_id"]
    incoming_copy["last_seen_at"] = incoming.get("imported_at")
    return incoming_copy


def persist_staging_batch(db: Any, batch: Mapping[str, Any]) -> dict[str, Any]:
    """Idempotently import items into the staging collection only."""

    if not isinstance(batch.get("items"), list):
        raise StagingStoreError("A staging batch must contain an items list.")
    staging = _collection(db, STAGING_COLLECTION)
    inserted = 0
    updated = 0
    for item in batch["items"]:
        if not isinstance(item, Mapping) or not item.get("source_item_id"):
            raise StagingStoreError("Every staged item needs a deterministic source_item_id.")
        source_item_id = str(item["source_item_id"])
        existing = _find_one(staging, {"source_item_id": source_item_id})
        document = _merge_import(existing, item)
        if existing is None:
            _insert_one(staging, document)
            inserted += 1
        else:
            _replace_one(staging, {"source_item_id": source_item_id}, document)
            updated += 1
    return {
        "source_file": batch.get("source_file"),
        "source_file_hash": batch.get("source_file_hash"),
        "parser_version": batch.get("parser_version", PARSER_VERSION),
        "item_count": len(batch["items"]),
        "inserted": inserted,
        "updated": updated,
        "collection": STAGING_COLLECTION,
        "canonical_writes": 0,
    }


def load_staging_items(
    db: Any,
    *,
    source_file_hash: str | None = None,
) -> list[dict[str, Any]]:
    """Load staged items in stable source order from the staging collection."""

    staging = _collection(db, STAGING_COLLECTION)
    query = {"source_file_hash": source_file_hash} if source_file_hash else {}
    items = _find_many(staging, query)
    return sorted(
        items,
        key=lambda item: (
            str(item.get("sheet") or ""),
            int(item.get("source_row") or 0),
            str(item.get("source_item_id") or ""),
        ),
    )


def load_staging_batch(db: Any, *, source_file_hash: str | None = None) -> dict[str, Any]:
    items = load_staging_items(db, source_file_hash=source_file_hash)
    hashes = sorted({str(item.get("source_file_hash")) for item in items if item.get("source_file_hash")})
    return {
        "source_file_hash": hashes[0] if len(hashes) == 1 else source_file_hash,
        "parser_version": items[0].get("parser_version") if items else PARSER_VERSION,
        "item_count": len(items),
        "items": items,
        "collection": STAGING_COLLECTION,
    }


def _validate_action(action: str, actor: str, reason: str, request_id: str) -> str:
    normalized_action = str(action or "").strip().casefold()
    if normalized_action not in REVIEW_ACTIONS:
        raise ReviewValidationError(f"Unsupported LOG-C06 review action: {action!r}")
    if not str(actor or "").strip():
        raise ReviewValidationError("Review action actor is required.")
    if not str(reason or "").strip():
        raise ReviewValidationError("Review action reason is required for auditability.")
    if not str(request_id or "").strip():
        raise ReviewValidationError("Review action request_id is required for idempotent retry.")
    return normalized_action


def _existing_request(actions: Any, request_id: str) -> dict[str, Any] | None:
    return _find_one(actions, {"request_id": request_id})


def _validate_correction_patch(correction: Mapping[str, Any] | None) -> dict[str, Any]:
    patch = deepcopy(dict(correction or {}))
    unknown_fields = sorted(set(patch) - PROPOSAL_CORRECTION_FIELDS)
    if unknown_fields:
        raise ReviewValidationError(
            "Correction may change proposal fields only; forbidden fields: " + ", ".join(unknown_fields)
        )
    if "currency" in patch:
        currency = str(patch["currency"] or UNKNOWN_CURRENCY).upper()
        if currency not in {"CNY", "USD", "VND", UNKNOWN_CURRENCY}:
            raise ReviewValidationError(f"Unsupported staging currency: {currency}")
        patch["currency"] = currency
    if "internal_sale_owner" in patch and patch["internal_sale_owner"] not in {None, SALE_OWNER}:
        raise ReviewValidationError("A confirmed SALE owner must be Thành or null in LOG-C06.")
    if "amount" in patch and patch["amount"] is not None:
        try:
            patch["amount"] = float(patch["amount"])
        except (TypeError, ValueError):
            raise ReviewValidationError("Corrected proposal amount must be numeric.")
    return patch


def _proposal_for_action(
    *,
    item: Mapping[str, Any],
    action: str,
    correction: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str, str]:
    proposal = deepcopy(dict(item.get("proposal") or {}))
    patch = _validate_correction_patch(correction)
    if action == "lineage_repair":
        if not patch:
            raise ReviewValidationError("The lineage_repair action requires an explicit proposal correction.")
        proposal.update(patch)
        proposal["lineage_repair_applied"] = True
        proposal.setdefault("reasons", []).append("Technical source-lineage repair; no business reclassification inferred.")
        return proposal, "REVIEW_REQUIRED", "Technical source-lineage repair applied; returned to Owner Review."
    if action == "correct":
        if not patch:
            raise ReviewValidationError("The correct action requires an explicit proposal correction.")
        proposal.update(patch)
        proposal["correction_applied"] = True
        proposal.setdefault("reasons", []).append("Confirmed after explicit owner correction review.")
        return proposal, "CONFIRMED", "Corrected and confirmed by owner review."
    if action == "confirm":
        return proposal, "CONFIRMED", "Confirmed from the staged proposal by owner review."
    if action == "not_thanh":
        proposal["internal_sale_owner"] = None
        proposal["beneficial_owner"] = None
        proposal["beneficiary"] = None
        proposal["restriction"] = "not_thanh"
        return proposal, "NOT_APPLICABLE", "Marked as not belonging to SALE Thành."
    proposal["classification"] = "unknown"
    proposal["event_type"] = "unknown"
    proposal["candidate_bucket"] = None
    proposal["restriction"] = "unresolved_unknown"
    return proposal, "REJECTED", "Marked unknown and excluded from opening position."


def apply_review_action(
    db: Any,
    source_item_id: str,
    action: str,
    *,
    actor: str,
    reason: str,
    request_id: str | None = None,
    correction: Mapping[str, Any] | None = None,
    acted_at: str | None = None,
    expected_review_version: int | None = None,
) -> dict[str, Any]:
    """Apply one audited, idempotent metadata-only review action."""

    request = request_id or str(uuid4())
    normalized_action = _validate_action(action, actor, reason, request)
    staging = _collection(db, STAGING_COLLECTION)
    actions = _collection(db, REVIEW_ACTIONS_COLLECTION)
    prior_action = _existing_request(actions, request)
    if prior_action is not None:
        same_subject = prior_action.get("source_item_id") == source_item_id
        same_action = prior_action.get("action") == normalized_action
        if not same_subject or not same_action:
            raise ReviewActionConflict("request_id was already used for a different staging action.")
        current = _find_one(staging, {"source_item_id": source_item_id})
        if current is None:
            raise StagingStoreError("Idempotent review action exists but its staging item is missing.")
        result = deepcopy(prior_action)
        result["status"] = "IDEMPOTENT"
        result["item"] = current
        return result

    current = _find_one(staging, {"source_item_id": source_item_id})
    if current is None:
        raise StagingStoreError(f"Staging item {source_item_id!r} was not found.")
    if current.get("review_status") in {"NOT_APPLICABLE", "REJECTED"} and normalized_action != "unknown":
        raise ReviewActionConflict("A closed staging item cannot be silently reopened by this action.")
    current_version = int(current.get("review_version") or 0)
    if expected_review_version is not None and current_version != int(expected_review_version):
        raise ReviewActionConflict(
            f"Review version conflict: expected {expected_review_version}, current {current_version}."
        )
    before_status = str(current.get("review_status") or "RAW")
    before_proposal = deepcopy(current.get("proposal") or {})
    proposal, after_status, default_reason = _proposal_for_action(
        item=current,
        action=normalized_action,
        correction=correction,
    )
    timestamp = acted_at or _utc_now_iso()
    history_entry = {
        "request_id": request,
        "action": normalized_action,
        "actor": str(actor).strip(),
        "acted_at": timestamp,
        "reason": str(reason).strip(),
        "before_status": before_status,
        "after_status": after_status,
        "before_proposal_hash": _stable_hash(before_proposal),
        "after_proposal_hash": _stable_hash(proposal),
    }
    updated = deepcopy(current)
    updated["proposal"] = proposal
    updated["review_status"] = after_status
    updated["review_reason"] = str(reason).strip() or default_reason
    updated["review_history"] = list(updated.get("review_history") or []) + [history_entry]
    updated["review_version"] = current_version + 1
    updated["last_review_action_id"] = request

    audit_record = {
        "_id": request,
        "request_id": request,
        "source_item_id": source_item_id,
        "action": normalized_action,
        "actor": str(actor).strip(),
        "acted_at": timestamp,
        "reason": str(reason).strip(),
        "before_status": before_status,
        "after_status": after_status,
        "before_proposal_hash": history_entry["before_proposal_hash"],
        "after_proposal_hash": history_entry["after_proposal_hash"],
        "review_version": updated["review_version"],
        "status": "APPLIED",
        "canonical_writes": 0,
        "staging_collection": STAGING_COLLECTION,
        "audit_collection": REVIEW_ACTIONS_COLLECTION,
    }
    if correction:
        audit_record["correction"] = deepcopy(dict(correction))
    try:
        _replace_one(staging, {"source_item_id": source_item_id}, updated)
        _insert_one(actions, audit_record)
    except Exception:
        # Keep the staging item and its append-only review audit record in
        # lockstep even when the audit collection rejects the write.  The
        # caller can safely retry with the same deterministic request_id.
        try:
            _replace_one(staging, {"source_item_id": source_item_id}, current)
        except Exception as rollback_error:
            raise StagingStoreError(
                "Review action failed and its staging rollback also failed."
            ) from rollback_error
        raise
    audit_record["item"] = updated
    return audit_record


def list_review_actions(db: Any, *, source_item_id: str | None = None) -> list[dict[str, Any]]:
    actions = _collection(db, REVIEW_ACTIONS_COLLECTION)
    query = {"source_item_id": source_item_id} if source_item_id else {}
    return sorted(
        _find_many(actions, query),
        key=lambda item: (str(item.get("acted_at") or ""), str(item.get("request_id") or "")),
    )


__all__ = [
    "IMMUTABLE_SOURCE_FIELDS",
    "PROPOSAL_CORRECTION_FIELDS",
    "REVIEW_ACTIONS",
    "REVIEW_ACTIONS_COLLECTION",
    "REVIEW_ACTION_STATUSES",
    "STAGING_COLLECTION",
    "StagingStoreError",
    "ReviewActionConflict",
    "ReviewValidationError",
    "apply_review_action",
    "ensure_staging_indexes",
    "list_review_actions",
    "load_staging_batch",
    "load_staging_items",
    "persist_staging_batch",
]
