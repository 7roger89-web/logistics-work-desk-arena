"""Confirmed-only opening-position and cutover-draft calculations for LOG-C06.

This module is intentionally pure.  It never reads the canonical ledger or a
database and never creates a live financial effect.  Historical rows remain
separate by currency and by business component; a single cross-currency total is
not produced.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from core.historical_cutover_sufficiency import build_cutover_sufficiency
from core.historical_owner_reconciliation import build_owner_reconciliation
from core.historical_staging import UNKNOWN_CURRENCY


OPENING_MODEL_VERSION = "log-c06-opening-v2"
ALLOWED_CURRENCIES = frozenset({"CNY", "USD", "VND"})
ALLOWED_DRAFT_STATUSES = frozenset({"DRAFT", "READY_FOR_OWNER_REVIEW", "SUPERSEDED"})
BUCKET_LABELS = {
    "payable_to_a_bo": "Payable to A Bò",
    "payment_to_a_bo_settled": "Payment to A Bò / settled",
    "held_credit": "Held money / credit",
    "received_on_behalf_available": "Received on behalf / available",
    "paid_on_behalf_settled": "Paid on behalf / settled",
    "unallocated_confirmed": "Unallocated confirmed",
    "restricted_confirmed": "Restricted confirmed",
}
EVENT_BUCKETS = {
    "payable_to_a_bo": "payable_to_a_bo",
    "payment_to_a_bo": "payment_to_a_bo_settled",
    "held_money_credit": "held_credit",
    "refund_return_credit": "held_credit",
    "received_on_behalf": "received_on_behalf_available",
    "paid_on_behalf": "paid_on_behalf_settled",
    "unallocated": "unallocated_confirmed",
}
EXCLUDED_STATUS_REASONS = {
    "RAW": "RAW_NOT_REVIEWED",
    "PROPOSED": "PROPOSED_NOT_CONFIRMED",
    "REVIEW_REQUIRED": "REVIEW_REQUIRED",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
    "REJECTED": "REJECTED_OR_UNKNOWN",
}


class OpeningModelError(ValueError):
    """Raised when a draft input is structurally invalid."""


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decimal_amount(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def _currency(proposal: Mapping[str, Any]) -> str:
    return str(proposal.get("currency") or UNKNOWN_CURRENCY).upper()


def _source_trace(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_item_id": item.get("source_item_id"),
        "source_file_hash": item.get("source_file_hash"),
        "sheet": item.get("sheet"),
        "source_row": item.get("source_row"),
        "source_cell_range": item.get("source_cell_range"),
        "source_reference": item.get("source_reference"),
        "amount": (item.get("proposal") or {}).get("amount", item.get("raw_amount")),
        "currency": _currency(item.get("proposal") or {}),
    }


def _component(item: Mapping[str, Any], amount: Decimal, bucket: str) -> dict[str, Any]:
    proposal = item.get("proposal") or {}
    trace = _source_trace(item)
    trace.update(
        {
            "bucket": bucket,
            "bucket_label": BUCKET_LABELS[bucket],
            "event_type": proposal.get("event_type"),
            "candidate_bucket": proposal.get("candidate_bucket"),
            "signed_amount": float(amount),
            "related_amount": proposal.get("related_amount"),
            "related_currency": proposal.get("related_currency"),
            "fx_rate": proposal.get("fx_rate"),
        }
    )
    return trace


def _excluded(item: Mapping[str, Any], reason: str) -> dict[str, Any]:
    trace = _source_trace(item)
    proposal = item.get("proposal") or {}
    trace.update(
        {
            "review_status": item.get("review_status"),
            "event_type": proposal.get("event_type"),
            "reason": reason,
            "anomalies": list(item.get("anomaly_flags") or proposal.get("anomalies") or []),
            "opening_inclusion": proposal.get("opening_inclusion"),
            "opening_lineage": proposal.get("opening_lineage"),
            "reconciliation_role": proposal.get("reconciliation_role"),
        }
    )
    return trace


def _bucket_for_confirmed(proposal: Mapping[str, Any]) -> str | None:
    candidate = str(proposal.get("candidate_bucket") or "").strip()
    if candidate in BUCKET_LABELS:
        return candidate
    event_type = str(proposal.get("event_type") or proposal.get("financial_case") or "").strip()
    if event_type in EVENT_BUCKETS:
        return EVENT_BUCKETS[event_type]
    if event_type == "fx_conversion_context":
        return "restricted_confirmed"
    if event_type == "adjustment":
        return None
    return None


def _item_eligibility(item: Mapping[str, Any]) -> tuple[str | None, Decimal | None, str | None]:
    status = str(item.get("review_status") or "RAW")
    proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
    if status != "CONFIRMED":
        return None, None, EXCLUDED_STATUS_REASONS.get(status, "NOT_CONFIRMED")
    currency = _currency(proposal)
    amount = _decimal_amount(proposal.get("amount", item.get("raw_amount")))
    if currency not in ALLOWED_CURRENCIES:
        return None, amount, "UNKNOWN_OR_UNSUPPORTED_CURRENCY"
    if amount is None:
        return None, None, "AMOUNT_UNRESOLVED"
    if proposal.get("opening_inclusion") == "embedded_in_snapshot":
        return None, amount, "EMBEDDED_IN_SNAPSHOT"
    if proposal.get("opening_inclusion") == "exclude_summary" or proposal.get("reconciliation_role") == "summary_checkpoint":
        return None, amount, "CHECKPOINT_NOT_COMPONENT"
    if proposal.get("checkpoint_key") or proposal.get("restriction") == "historical_checkpoint":
        return None, amount, "CHECKPOINT_NOT_COMPONENT"
    if proposal.get("restriction") in {"unresolved_unknown", "currency_unknown"}:
        return None, amount, "UNRESOLVED_RESTRICTION"
    bucket = _bucket_for_confirmed(proposal)
    if bucket is None:
        return None, amount, "UNKNOWN_OR_UNALLOCATED_EVENT"
    return bucket, amount, None


def _empty_currency() -> dict[str, Any]:
    buckets = {
        name: {"label": label, "amount": 0.0, "count": 0, "components": []}
        for name, label in BUCKET_LABELS.items()
    }
    return {
        "currency": None,
        "buckets": buckets,
        "confirmed_source_item_ids": [],
        "confirmed_component_count": 0,
        "excluded_unresolved_amount": 0.0,
        "excluded_unresolved_source_item_ids": [],
        "formula": "Buckets remain separate; no cross-currency net total is calculated.",
    }


def build_draft_opening_position(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build per-currency components from confirmed, non-checkpoint items only."""

    rows = [dict(item) for item in items]
    by_currency: dict[str, dict[str, Any]] = {}
    for currency in sorted(ALLOWED_CURRENCIES):
        current = _empty_currency()
        current["currency"] = currency
        by_currency[currency] = current
    excluded: list[dict[str, Any]] = []
    included_ids: list[str] = []

    for item in rows:
        bucket, amount, reason = _item_eligibility(item)
        proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
        currency = _currency(proposal)
        if reason is not None or bucket is None or amount is None:
            excluded_row = _excluded(item, reason or "UNRESOLVED")
            excluded.append(excluded_row)
            if amount is not None and currency in by_currency:
                by_currency[currency]["excluded_unresolved_amount"] = float(
                    Decimal(str(by_currency[currency]["excluded_unresolved_amount"])) + amount
                )
                by_currency[currency]["excluded_unresolved_source_item_ids"].append(
                    item.get("source_item_id")
                )
            continue
        component = _component(item, amount, bucket)
        currency_data = by_currency[currency]
        bucket_data = currency_data["buckets"][bucket]
        bucket_data["amount"] = float(Decimal(str(bucket_data["amount"])) + amount)
        bucket_data["count"] += 1
        bucket_data["components"].append(component)
        currency_data["confirmed_source_item_ids"].append(item.get("source_item_id"))
        currency_data["confirmed_component_count"] += 1
        included_ids.append(str(item.get("source_item_id")))

    for currency_data in by_currency.values():
        currency_data["confirmed_source_item_ids"] = sorted(
            str(value) for value in currency_data["confirmed_source_item_ids"] if value
        )
        currency_data["excluded_unresolved_source_item_ids"] = sorted(
            str(value) for value in currency_data["excluded_unresolved_source_item_ids"] if value
        )
        for bucket_data in currency_data["buckets"].values():
            bucket_data["components"] = sorted(
                bucket_data["components"],
                key=lambda component: (
                    str(component.get("sheet") or ""),
                    int(component.get("source_row") or 0),
                    str(component.get("source_item_id") or ""),
                ),
            )

    excluded = sorted(
        excluded,
        key=lambda row: (
            str(row.get("currency") or ""),
            str(row.get("sheet") or ""),
            int(row.get("source_row") or 0),
            str(row.get("source_item_id") or ""),
        ),
    )
    unresolved_by_currency: dict[str, float] = defaultdict(float)
    for row in excluded:
        amount = _decimal_amount(row.get("amount"))
        if amount is not None:
            unresolved_by_currency[str(row.get("currency") or UNKNOWN_CURRENCY)] += float(amount)
    embedded_snapshot_ids = sorted(
        str(row.get("source_item_id"))
        for row in excluded
        if row.get("reason") == "EMBEDDED_IN_SNAPSHOT" and row.get("source_item_id")
    )
    summary_ids = sorted(
        str(row.get("source_item_id"))
        for row in excluded
        if row.get("reason") == "CHECKPOINT_NOT_COMPONENT" and row.get("source_item_id")
    )
    return {
        "model_version": OPENING_MODEL_VERSION,
        "currency_order": sorted(ALLOWED_CURRENCIES),
        "currencies": by_currency,
        "excluded": excluded,
        "confirmed_source_item_ids": sorted(set(included_ids)),
        "excluded_source_item_ids": sorted(
            str(row.get("source_item_id")) for row in excluded if row.get("source_item_id")
        ),
        "unresolved_excluded_by_currency": {
            currency: unresolved_by_currency[currency]
            for currency in sorted(unresolved_by_currency)
        },
        "counts": {
            "input_items": len(rows),
            "confirmed_components": len(included_ids),
            "excluded_items": len(excluded),
            "review_required_excluded": sum(
                1 for row in excluded if row.get("reason") == "REVIEW_REQUIRED"
            ),
            "checkpoint_excluded": sum(
                1 for row in excluded if row.get("reason") == "CHECKPOINT_NOT_COMPONENT"
            ),
            "embedded_snapshot_excluded": len(embedded_snapshot_ids),
        },
        "cross_currency_total": None,
        "opening_lineage": {
            "base_source_components": sorted(set(included_ids)),
            "post_base_events": [],
            "embedded_snapshot_source_item_ids": embedded_snapshot_ids,
            "summary_source_item_ids": summary_ids,
            "formula": "BASE / SOURCE COMPONENTS + POST-BASE EVENTS = DRAFT OPENING POSITION",
            "double_count_protection": [
                "Embedded snapshot credits are excluded from standalone opening.",
                "Checkpoint summaries are excluded from their source components.",
            ],
        },
        "explanation": "Only CONFIRMED, known-currency, non-checkpoint, non-embedded components enter the draft; all other rows remain explicitly excluded.",
    }


def _checkpoint_operation(proposal: Mapping[str, Any]) -> str | None:
    operation = proposal.get("checkpoint_operation") or proposal.get("checkpoint_formula")
    if operation in {"sum", "difference"}:
        return str(operation)
    return None


def reconcile_checkpoints(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Reconcile only explicitly linked checkpoint components; otherwise stay unknown."""

    rows = {str(item.get("source_item_id")): dict(item) for item in items if item.get("source_item_id")}
    checkpoints = [
        item
        for item in rows.values()
        if (item.get("proposal") or {}).get("checkpoint_key")
    ]
    results: list[dict[str, Any]] = []
    for checkpoint in sorted(checkpoints, key=lambda item: str(item.get("source_item_id"))):
        proposal = checkpoint.get("proposal") or {}
        expected = _decimal_amount(proposal.get("amount", checkpoint.get("raw_amount")))
        currency = _currency(proposal)
        component_ids = [
            str(value)
            for value in (proposal.get("checkpoint_component_ids") or checkpoint.get("checkpoint_component_ids") or [])
            if str(value) in rows
        ]
        operation = _checkpoint_operation(proposal)
        base = {
            "checkpoint_source_item_id": checkpoint.get("source_item_id"),
            "checkpoint_key": proposal.get("checkpoint_key"),
            "expected_amount": float(expected) if expected is not None else None,
            "currency": currency,
            "checkpoint_source": _source_trace(checkpoint),
            "component_source_item_ids": sorted(component_ids),
            "operation": operation,
            "component_sources": [],
            "component_amount": None,
            "difference": None,
            "status": "UNKNOWN_SEMANTICS",
            "reason": "No explicit checkpoint component IDs and formula were supplied.",
        }
        if (
            proposal.get("opening_inclusion") == "embedded_in_snapshot"
            or proposal.get("reconciliation_role") == "snapshot_checkpoint"
        ):
            base["status"] = "EMBEDDED_IN_SNAPSHOT"
            base["reason"] = "Snapshot checkpoint is a base lineage marker; it is not a component sum or a new opening event."
            results.append(base)
            continue
        if expected is None or currency not in ALLOWED_CURRENCIES or not component_ids or operation is None:
            results.append(base)
            continue
        components = [rows[item_id] for item_id in component_ids]
        if any(str((item.get("proposal") or {}).get("currency") or UNKNOWN_CURRENCY).upper() != currency for item in components):
            base["reason"] = "Checkpoint and components use different currencies."
            results.append(base)
            continue
        if any(item.get("review_status") != "CONFIRMED" for item in components):
            base["reason"] = "At least one linked checkpoint component is not CONFIRMED."
            base["component_sources"] = [_source_trace(item) for item in components]
            results.append(base)
            continue
        amounts = [_decimal_amount((item.get("proposal") or {}).get("amount", item.get("raw_amount"))) for item in components]
        if any(amount is None for amount in amounts):
            base["reason"] = "At least one linked checkpoint component has an unresolved amount."
            results.append(base)
            continue
        component_amount = sum((amount for amount in amounts if amount is not None), Decimal("0"))
        calculated = component_amount if operation == "sum" else amounts[0] - sum(amounts[1:], Decimal("0"))
        difference = calculated - expected
        base.update(
            {
                "component_sources": [_source_trace(item) for item in components],
                "component_amount": float(calculated),
                "difference": float(difference),
                "status": "EXACT_MATCH" if difference == 0 else "DIFFERENCE",
                "reason": "Explicit checkpoint formula reconciled against confirmed components."
                if difference == 0
                else "Explicit checkpoint formula differs from the confirmed component total.",
            }
        )
        results.append(base)
    return results


def build_cutover_draft(
    items: Iterable[Mapping[str, Any]],
    *,
    proposed_cutover_date: str,
    generated_by: str,
    draft_version: int = 1,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Create a reproducible, non-live cutover draft with readiness gates."""

    try:
        cutover_date = date.fromisoformat(str(proposed_cutover_date)).isoformat()
    except ValueError as error:
        raise OpeningModelError("proposed_cutover_date must be ISO YYYY-MM-DD.") from error
    if not str(generated_by or "").strip():
        raise OpeningModelError("generated_by is required for the cutover draft audit trail.")
    if int(draft_version) < 1:
        raise OpeningModelError("draft_version must be positive.")
    rows = [dict(item) for item in items]
    position = build_draft_opening_position(rows)
    checkpoints = reconcile_checkpoints(rows)
    owner_reconciliation = build_owner_reconciliation(rows)
    opening_sufficiency = build_cutover_sufficiency(rows)
    if opening_sufficiency["source_hash_known"]:
        # LOG-C06's verified source has a separate opening-impact gate.  The
        # historical staging review may still contain unresolved metadata or
        # reference rows; only unresolved items that can change the opening
        # remain blockers for this scope.
        readiness_reasons = list(opening_sufficiency["readiness_reasons"])
    else:
        # Preserve the generic opening-model contract for callers that are not
        # operating on the verified LOG-C06 workbook.
        readiness_reasons = []
        if position["counts"]["confirmed_components"] == 0:
            readiness_reasons.append("NO_CONFIRMED_COMPONENTS")
        if position["counts"]["review_required_excluded"] > 0:
            readiness_reasons.append("REVIEW_REQUIRED_ITEMS_REMAIN")
        if UNKNOWN_CURRENCY in position["unresolved_excluded_by_currency"]:
            readiness_reasons.append("UNKNOWN_CURRENCY_REMAINS")
        if any(result["status"] not in {"EXACT_MATCH", "EMBEDDED_IN_SNAPSHOT"} for result in checkpoints):
            readiness_reasons.append("CHECKPOINT_NOT_RECONCILED")
        if any(row.get("reason") in {"AMOUNT_UNRESOLVED", "UNKNOWN_OR_UNALLOCATED_EVENT"} for row in position["excluded"]):
            readiness_reasons.append("UNRESOLVED_EVENT_OR_AMOUNT")
        if owner_reconciliation.get("material_difference_count", 0) > 0:
            readiness_reasons.append("OWNER_CHECKPOINT_DIFFERENCE")
    readiness = "READY" if not readiness_reasons else "NOT_READY"
    draft_status = "READY_FOR_OWNER_REVIEW" if readiness == "READY" else "DRAFT"
    source_hashes = sorted(
        {
            str(item.get("source_file_hash"))
            for item in rows
            if item.get("source_file_hash")
        }
    )
    deterministic_snapshot = {
        "model_version": OPENING_MODEL_VERSION,
        "draft_version": int(draft_version),
        "proposed_cutover_date": cutover_date,
        "source_hashes": source_hashes,
        "position": position,
        "checkpoints": checkpoints,
        "owner_reconciliation": owner_reconciliation,
        "opening_sufficiency": opening_sufficiency,
        "readiness": readiness,
        "readiness_reasons": sorted(set(readiness_reasons)),
    }
    snapshot_hash = _stable_hash(deterministic_snapshot)
    draft = {
        "draft_id": "C06-DRAFT-" + snapshot_hash[:20],
        "draft_type": "CUTOVER_DRAFT",
        "model_version": OPENING_MODEL_VERSION,
        "draft_version": int(draft_version),
        "status": draft_status,
        "cutover_readiness": readiness,
        "readiness_reasons": sorted(set(readiness_reasons)),
        "proposed_cutover_date": cutover_date,
        "generated_by": str(generated_by).strip(),
        "generated_at": generated_at or _utc_now_iso(),
        "source_hashes": source_hashes,
        "source_item_ids": sorted(
            str(item.get("source_item_id")) for item in rows if item.get("source_item_id")
        ),
        "confirmed_source_item_ids": position["confirmed_source_item_ids"],
        "excluded_source_item_ids": position["excluded_source_item_ids"],
        "position_by_currency": position["currencies"],
        "opening_lineage": position["opening_lineage"],
        "checkpoint_reconciliation": checkpoints,
        "owner_reconciliation": owner_reconciliation,
        "opening_sufficiency": opening_sufficiency,
        "cutover_sufficiency_status": opening_sufficiency["readiness"],
        "unresolved_excluded_by_currency": position["unresolved_excluded_by_currency"],
        "exclusions": position["excluded"],
        "snapshot_hash": snapshot_hash,
        "canonical_mutations": 0,
        "owner_confirmation_required": True,
        "approval_status": "NOT_APPROVED",
        "live_status": "NOT_LIVE",
        "allowed_statuses": sorted(ALLOWED_DRAFT_STATUSES),
        "why": position["explanation"],
        "canonical_mutation_oracle": {
            "canonical_writes": 0,
            "canonical_collections_touched": [],
            "opening_published": False,
        },
    }
    return draft


__all__ = [
    "ALLOWED_CURRENCIES",
    "ALLOWED_DRAFT_STATUSES",
    "BUCKET_LABELS",
    "OPENING_MODEL_VERSION",
    "OpeningModelError",
    "build_cutover_draft",
    "build_draft_opening_position",
    "reconcile_checkpoints",
]
