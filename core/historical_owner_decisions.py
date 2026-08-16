"""Audited, staging-only application of the LOG-C06 Owner decisions.

This module deliberately calls the existing review-action store instead of
editing staging documents directly.  Every change therefore has an actor,
reason, deterministic request id, review-version check, and an append-only
review audit record.  The module has no canonical-ledger dependency.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from core.historical_owner_reconciliation import (
    BG_GREEN_SOURCE_ROW,
    CHECKPOINT_COMPONENT_ROWS,
    CHECKPOINT_SOURCE_ROW,
    CREDIT_SOURCE_ROW,
    OWNER_DECISION_BATCH_ID,
    PAID_CHECKPOINT_GROUP_KEY,
    PAID_GROUP_KEY,
    RECEIVED_GROUP_KEY,
    RECEIVED_GROUP_ROWS,
    RECEIVED_SOURCE_ORACLE_BY_ROW,
    SNAPSHOT_LINEAGE_KEY,
    SNAPSHOT_SOURCE_ROW,
    build_owner_reconciliation,
)
from core.historical_staging import SALE_OWNER
from core.historical_staging_store import (
    ReviewActionConflict,
    StagingStoreError,
    apply_review_action,
    ensure_staging_indexes,
    load_staging_items,
)


OWNER_ACTOR = "owner-confirmed:LOG-C06"
NOT_CONFIRMED_SOURCE_ROWS = (96,)
LEGACY_RECEIVED_ALIAS_ROWS = (190, 197, 198)
TECHNICAL_LINEAGE_REPAIR_ID = "LOG-C06-P4-TECHNICAL-LINEAGE-REPAIR-2026-08-15"


class OwnerDecisionApplyError(StagingStoreError):
    """Raised when the Owner batch cannot pass its all-or-nothing preflight."""


_EXPECTED_AMOUNTS: dict[int, Decimal] = {
    16: Decimal("24576"),
    99: Decimal("25025"),
    102: Decimal("62464"),
    103: Decimal("4900"),
    104: Decimal("37564"),
    105: Decimal("6400"),
    106: Decimal("5600"),
    107: Decimal("22176"),
    108: Decimal("14784"),
    109: Decimal("1687"),
    111: Decimal("3669"),
    114: Decimal("10000"),
    115: Decimal("25297.24260055654"),
    116: Decimal("10000"),
    120: Decimal("6360"),
    121: Decimal("13520"),
    129: Decimal("134973"),
    192: Decimal("183549"),
    199: Decimal("19000"),
    200: Decimal("124485"),
}


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _source_row(item: Mapping[str, Any]) -> int:
    try:
        return int(item.get("source_row") or 0)
    except (TypeError, ValueError):
        return 0


def _proposal(item: Mapping[str, Any]) -> Mapping[str, Any]:
    proposal = item.get("proposal")
    return proposal if isinstance(proposal, Mapping) else {}


def _amount(item: Mapping[str, Any]) -> Decimal | None:
    proposal = _proposal(item)
    return _decimal(proposal.get("amount", item.get("raw_amount")))


def _source_reference(item: Mapping[str, Any]) -> str:
    return str(item.get("source_reference") or f"{item.get('sheet')}!row {_source_row(item)}")


def _request_id(source_item_id: str, decision_id: str) -> str:
    safe_source = "".join(character if character.isalnum() else "-" for character in source_item_id)
    safe_decision = "".join(character if character.isalnum() else "-" for character in decision_id)
    return f"log-c06-owner-{safe_decision}-{safe_source}"


def _base_patch(*, decision_id: str, group_key: str, context: str) -> dict[str, Any]:
    return {
        "internal_sale_owner": SALE_OWNER,
        "candidate_internal_sale_owner": SALE_OWNER,
        "holder": "A Bò",
        "beneficial_owner": SALE_OWNER,
        "beneficiary": SALE_OWNER,
        "a_bo_relationship": "A Bò holder/partner; Owner-confirmed Thành money leg",
        "shipment": None,
        "allocation_status": "unallocated",
        "business_context": context,
        "owner_decision_batch": OWNER_DECISION_BATCH_ID,
        "owner_decision_id": decision_id,
        "owner_decision_status": "CONFIRMED",
        "historical_group_key": group_key,
        "evidence_sufficiency": "owner_confirmed",
        "confidence": "owner_confirmed",
        "sale_confidence": "owner_confirmed",
        "sale_evidence": "owner_decision_confirmation",
        "reconciliation_role": "source_component",
    }


def _received_patch(source_row: int) -> dict[str, Any]:
    if source_row == 102:
        decision_id = "OWNER-D2-62464-RECEIVED-ON-BEHALF"
        context = "Nhà máy đồ chơi / Thành Vũ chuyển tiền cho Thành; A Bò nhận hộ."
    elif source_row == 109:
        decision_id = "OWNER-D3-1687-LUC-GIAC-FREIGHT"
        context = "Nhà máy Lục Giác thanh toán tiền vận chuyển cho Thành; A Bò nhận hộ."
    else:
        decision_id = "OWNER-D9-416482-RECEIVED-GROUP"
        oracle = RECEIVED_SOURCE_ORACLE_BY_ROW.get(source_row)
        oracle_id = oracle["oracle_id"] if oracle else f"row {source_row}"
        context = f"Owner-confirmed received-on-behalf group member {oracle_id}; shipment linkage remains unresolved."
    patch = _base_patch(
        decision_id=decision_id,
        group_key=RECEIVED_GROUP_KEY,
        context=context,
    )
    patch.update(
        {
            "event_type": "received_on_behalf",
            "financial_case": "received_on_behalf",
            "classification": "received_on_behalf",
            "candidate_bucket": "received_on_behalf",
            "reconciliation_role": "received_group_component",
            "allocation_status": "unallocated",
            "shipment": None,
        }
    )
    if source_row == 115:
        patch.update(
            {
                "business_context": "Received group component with VND→CNY conversion context preserved; the FX leg is not counted twice.",
                "fx_context": {
                    "fx_rate": 3953.0,
                    "related_amount": 100000000.0,
                    "related_currency": "VND",
                    "context_only": True,
                },
            }
        )
    return patch


def _paid_component_patch(source_row: int) -> dict[str, Any]:
    patch = _base_patch(
        decision_id="OWNER-D6-134973-COMPONENT-GROUP",
        group_key=PAID_GROUP_KEY,
        context=f"Owner-confirmed A Bò paid/transferred on behalf for Thành; checkpoint component C{source_row}.",
    )
    patch.update(
        {
            "event_type": "paid_on_behalf",
            "financial_case": "paid_on_behalf",
            "classification": "paid_on_behalf",
            "candidate_bucket": "paid_on_behalf",
            "reconciliation_role": "paid_on_behalf_checkpoint_component",
            "checkpoint_group_key": PAID_CHECKPOINT_GROUP_KEY,
            "allocation_status": "unallocated",
        }
    )
    return patch


def _decision_patch(source_row: int, *, snapshot_item_id: str | None) -> tuple[str, dict[str, Any]]:
    if source_row == CREDIT_SOURCE_ROW:
        patch = _base_patch(
            decision_id="OWNER-D1-24576-EMBEDDED-CREDIT",
            group_key=SNAPSHOT_LINEAGE_KEY,
            context="A Bò credit/reduction for Thành related to the Lục Giác USD transfer; already embedded in the 99,824.43 checkpoint.",
        )
        patch.update(
            {
                "event_type": "refund_return_credit",
                "financial_case": "refund_return_credit",
                "classification": "refund_return_credit",
                "candidate_bucket": "held_credit",
                "reconciliation_role": "credit_embedded_in_snapshot",
                "opening_inclusion": "embedded_in_snapshot",
                "opening_lineage": {
                    "lineage_key": SNAPSHOT_LINEAGE_KEY,
                    "mode": "embedded_in_snapshot",
                    "source_item_id": None,
                    "snapshot_source_item_id": snapshot_item_id,
                    "snapshot_amount": 99824.43,
                    "embedded_amount": 24576.0,
                    "reapply_to_opening": False,
                },
            }
        )
        return "OWNER-D1-24576-EMBEDDED-CREDIT", patch
    if source_row in set(RECEIVED_GROUP_ROWS):
        patch = _received_patch(source_row)
        return str(patch["owner_decision_id"]), patch
    if source_row == BG_GREEN_SOURCE_ROW:
        patch = _base_patch(
            decision_id="OWNER-D5-25025-BG-GREEN-PAID-ON-BEHALF",
            group_key=PAID_GROUP_KEY,
            context="A Bò chi/chuyển hộ cho Thành đối với B&G Green; customer receipt into Trường Thành is retained as a separate leg.",
        )
        patch.update(
            {
                "event_type": "paid_on_behalf",
                "financial_case": "paid_on_behalf",
                "classification": "paid_on_behalf",
                "candidate_bucket": "paid_on_behalf",
                "beneficiary": "B&G Green",
                "customer": "B&G Green",
                "financial_effect": "increases_debt_thanh_to_a_bo",
                "settlement_status": "paid_on_behalf_not_settled_by_customer_receipt",
                "reconciliation_role": "paid_on_behalf_group_component",
                "money_legs": [
                    {
                        "leg_id": "CUSTOMER_TO_TRUONG_THANH",
                        "from": "B&G Green customer",
                        "to": "Trường Thành account",
                        "amount": 25025.0,
                        "currency": "CNY",
                        "event_type": "customer_receipt",
                        "settlement_effect_on_a_bo": "none_proven",
                    },
                    {
                        "leg_id": "A_BO_TO_BG_GREEN",
                        "from": "A Bò",
                        "to": "B&G Green / beneficiary",
                        "amount": 25025.0,
                        "currency": "CNY",
                        "event_type": "paid_on_behalf",
                        "financial_effect": "increases_debt_thanh_to_a_bo",
                    },
                ],
                "receipt_leg": {
                    "from": "B&G Green customer",
                    "to": "Trường Thành account",
                    "amount": 25025.0,
                    "currency": "CNY",
                    "settlement_of_a_bo_obligation": False,
                },
                "paid_on_behalf_leg": {
                    "from": "A Bò",
                    "to": "B&G Green / beneficiary",
                    "amount": 25025.0,
                    "currency": "CNY",
                    "settled": False,
                },
            }
        )
        return "OWNER-D5-25025-BG-GREEN-PAID-ON-BEHALF", patch
    if source_row in CHECKPOINT_COMPONENT_ROWS:
        patch = _paid_component_patch(source_row)
        return "OWNER-D6-134973-COMPONENT-GROUP", patch
    if source_row == CHECKPOINT_SOURCE_ROW:
        component_ids = []
        patch = _base_patch(
            decision_id="OWNER-D6-134973-CHECKPOINT-SUMMARY",
            group_key=PAID_GROUP_KEY,
            context="Owner-confirmed 134,973 CNY checkpoint: summary of 11 paid-on-behalf component rows, not a new money event.",
        )
        patch.update(
            {
                "event_type": "checkpoint_summary",
                "financial_case": "checkpoint_summary",
                "classification": "checkpoint_summary",
                "candidate_bucket": None,
                "restriction": "historical_checkpoint",
                "checkpoint_key": "THANH_ACCUMULATED",
                "checkpoint_component_ids": component_ids,
                "checkpoint_operation": "sum",
                "checkpoint_group_key": PAID_CHECKPOINT_GROUP_KEY,
                "checkpoint_summary_amount": 134973.0,
                "reconciliation_role": "summary_checkpoint",
                "opening_inclusion": "exclude_summary",
            }
        )
        return "OWNER-D6-134973-CHECKPOINT-SUMMARY", patch
    raise OwnerDecisionApplyError(f"No deterministic Owner decision exists for source row {source_row}.")


def _preflight(
    items: Iterable[Mapping[str, Any]],
) -> tuple[dict[int, dict[str, Any]], list[int]]:
    by_row = {
        _source_row(item): dict(item)
        for item in items
        if _source_row(item)
    }
    target_rows = set(_EXPECTED_AMOUNTS)
    missing = sorted(target_rows - set(by_row))
    if missing:
        raise OwnerDecisionApplyError(
            "Owner batch preflight failed; missing source rows: " + ", ".join(map(str, missing))
        )
    mismatches: list[str] = []
    for row, expected in _EXPECTED_AMOUNTS.items():
        item = by_row[row]
        amount = _amount(item)
        currency = str((_proposal(item).get("currency") or item.get("raw_currency") or "UNKNOWN")).upper()
        if amount != expected or currency != "CNY":
            mismatches.append(f"row {row}: amount={amount!s} currency={currency}")
    if mismatches:
        raise OwnerDecisionApplyError(
            "Owner batch preflight failed; source amount/currency mismatch: " + "; ".join(mismatches)
        )
    return by_row, sorted(target_rows)


def _technical_repair_request_id(source_item_id: str, repair_key: str) -> str:
    safe_source = "".join(character if character.isalnum() else "-" for character in source_item_id)
    safe_key = "".join(character if character.isalnum() else "-" for character in repair_key)
    return f"log-c06-lineage-repair-{safe_key}-{safe_source}"


def _technical_repair_patch(source_row: int, item: Mapping[str, Any]) -> dict[str, Any]:
    if source_row == SNAPSHOT_SOURCE_ROW:
        return {
            "amount": 99824.43,
            "currency": "CNY",
            "event_type": "checkpoint_summary",
            "financial_case": "checkpoint_summary",
            "classification": "checkpoint_summary",
            "candidate_bucket": None,
            "restriction": "historical_checkpoint",
            "checkpoint_key": "THANH_ACCUMULATED",
            "reconciliation_role": "snapshot_checkpoint",
            "opening_inclusion": "embedded_in_snapshot",
            "amount_source_cell": "E86",
            "amount_source_label": "",
            "amount_source_raw_value": 99824.43,
            "amount_source_kind": "numeric_cell",
            "parser_version": "log-c06-staging-v2",
            "technical_lineage_status": "corrected_parser_amount_source",
            "technical_lineage_repair_id": TECHNICAL_LINEAGE_REPAIR_ID,
            "technical_lineage": {
                "source_cell": "Sheet2!E86",
                "source_note_cell": "Sheet2!D86",
                "source_note": "c\u1ee7a th\u00e0nh = E76 + 83",
                "stored_numeric_value": 99824.43,
                "reconstruction_formula": "Sheet2!E77 + Sheet2!E85",
                "reconstruction_cells": ["Sheet2!E77", "Sheet2!E85"],
                "reconstruction_values": [96324.43, 3500.0],
                "reconstructed_amount": 99824.43,
                "cached_formula_present": False,
                "parser_selected_amount_cell_before_repair": "D86",
                "parser_selected_amount_before_repair": 7683.0,
                "source_reference_text_is_not_amount": True,
            },
            "reasons": [
                "Technical parser repair: D86 formula/reference text was not an amount; E86 is the stored numeric checkpoint value.",
                "The 24,576 CNY credit remains embedded in this snapshot and is not reapplied.",
            ],
        }
    if source_row in LEGACY_RECEIVED_ALIAS_ROWS:
        prior_proposal = _proposal(item)
        prior_decision_id = prior_proposal.get("owner_decision_id")
        return {
            "candidate_bucket": None,
            "reconciliation_role": "technical_lineage_excluded",
            "opening_inclusion": "excluded_until_review",
            "owner_decision_status": "SUPERSEDED_TECHNICAL_ALIAS",
            "superseded_owner_decision_id": prior_decision_id,
            "technical_lineage_status": "superseded_wrong_source_alias",
            "technical_lineage_repair_id": TECHNICAL_LINEAGE_REPAIR_ID,
            "technical_lineage": {
                "source_cell": f"Sheet2!C{source_row}",
                "source_row": source_row,
                "excluded_from_received_oracle_group": True,
                "correct_received_oracle_rows": {
                    "190": "Sheet2!C192 / oracle C190",
                    "197": "Sheet2!C199 / oracle C197",
                    "198": "Sheet2!C200 / oracle C198",
                },
                "raw_value_preserved": True,
            },
            "reasons": [
                "Technical lineage repair: legacy Owner group alias pointed at the wrong physical source row; original raw value and review history are preserved.",
                "This row is not included in the six-source received-on-behalf checkpoint.",
            ],
        }
    raise OwnerDecisionApplyError(f"No technical lineage repair exists for source row {source_row}.")


def _apply_technical_lineage_repairs(
    db: Any,
    items: Iterable[Mapping[str, Any]],
    *,
    source_file_hash: str | None,
    actor: str,
    acted_at: str | None,
) -> list[dict[str, Any]]:
    """Repair known parser/source-row aliases through the audited store."""

    by_row = {_source_row(item): dict(item) for item in items if _source_row(item)}
    repairs: list[dict[str, Any]] = []
    for source_row in (SNAPSHOT_SOURCE_ROW, *LEGACY_RECEIVED_ALIAS_ROWS):
        current = by_row.get(source_row)
        if current is None:
            continue
        current_proposal = _proposal(current)
        if current_proposal.get("technical_lineage_status") == (
            "corrected_parser_amount_source"
            if source_row == SNAPSHOT_SOURCE_ROW
            else "superseded_wrong_source_alias"
        ):
            repairs.append(
                {
                    "source_row": source_row,
                    "source_item_id": current.get("source_item_id"),
                    "status": "SKIPPED_ALREADY_REPAIRED",
                    "technical_repair": True,
                }
            )
            continue
        source_item_id = str(current.get("source_item_id"))
        repair_key = "row86-e86" if source_row == SNAPSHOT_SOURCE_ROW else f"legacy-row-{source_row}"
        request_id = _technical_repair_request_id(source_item_id, repair_key)
        patch = _technical_repair_patch(source_row, current)
        reason = (
            f"Technical LOG-C06 lineage repair {TECHNICAL_LINEAGE_REPAIR_ID}; "
            "staging review only; no canonical mutation."
        )
        try:
            result = apply_review_action(
                db,
                source_item_id,
                "lineage_repair",
                actor=actor,
                reason=reason,
                request_id=request_id,
                correction=patch,
                acted_at=acted_at,
                expected_review_version=int(current.get("review_version") or 0),
            )
        except ReviewActionConflict as error:
            raise OwnerDecisionApplyError(
                f"Technical lineage repair stopped at source row {source_row}: {error}"
            ) from error
        repairs.append(
            {
                "source_row": source_row,
                "source_item_id": source_item_id,
                "request_id": request_id,
                "status": result.get("status"),
                "after_status": result.get("after_status") or (result.get("item") or {}).get("review_status"),
                "technical_repair": True,
            }
        )
    return repairs


def apply_owner_decisions(
    db: Any,
    *,
    actor: str = OWNER_ACTOR,
    source_file_hash: str | None = None,
    acted_at: str | None = None,
) -> dict[str, Any]:
    """Apply the confirmed Owner decisions to staging only, safely and retryably."""

    ensure_staging_indexes(db)
    items = load_staging_items(db, source_file_hash=source_file_hash)
    if source_file_hash is None:
        source_hashes = sorted(
            {
                str(item.get("source_file_hash"))
                for item in items
                if item.get("source_file_hash")
            }
        )
        if len(source_hashes) > 1:
            raise OwnerDecisionApplyError(
                "Owner batch requires an explicit source_file_hash when staging contains multiple workbook batches."
            )
    by_row, target_rows = _preflight(items)
    snapshot_item_id = by_row.get(SNAPSHOT_SOURCE_ROW, {}).get("source_item_id")
    checkpoint_item_id = by_row.get(CHECKPOINT_SOURCE_ROW, {}).get("source_item_id")
    component_ids = [
        by_row[row].get("source_item_id")
        for row in CHECKPOINT_COMPONENT_ROWS
        if by_row[row].get("source_item_id")
    ]

    # The component id list is part of the summary patch and must be built
    # after preflight, so no summary can accidentally point at an absent row.
    applied: list[dict[str, Any]] = []
    for source_row in target_rows:
        decision_id, patch = _decision_patch(
            source_row,
            snapshot_item_id=str(snapshot_item_id) if snapshot_item_id else None,
        )
        if source_row == CREDIT_SOURCE_ROW:
            patch["opening_lineage"] = deepcopy(patch["opening_lineage"])
            patch["opening_lineage"]["source_item_id"] = by_row[source_row].get("source_item_id")
        if source_row == CHECKPOINT_SOURCE_ROW:
            patch["checkpoint_component_ids"] = list(component_ids)
            patch["checkpoint_source_item_id"] = checkpoint_item_id
        current_items = load_staging_items(db, source_file_hash=source_file_hash)
        current = next(
            (item for item in current_items if _source_row(item) == source_row),
            None,
        )
        if current is None:
            raise OwnerDecisionApplyError(f"Staging item for source row {source_row} disappeared during batch.")
        source_item_id = str(current.get("source_item_id"))
        reason = f"Owner-confirmed LOG-C06 decision {decision_id}; staging review only; no canonical mutation."
        request_id = _request_id(source_item_id, decision_id)
        try:
            result = apply_review_action(
                db,
                source_item_id,
                "correct",
                actor=actor,
                reason=reason,
                request_id=request_id,
                correction=patch,
                acted_at=acted_at,
                expected_review_version=int(current.get("review_version") or 0),
            )
        except ReviewActionConflict as error:
            raise OwnerDecisionApplyError(
                f"Owner batch stopped at source row {source_row}: {error}"
            ) from error
        applied.append(
            {
                "source_row": source_row,
                "source_item_id": source_item_id,
                "decision_id": decision_id,
                "request_id": request_id,
                "status": result.get("status"),
                "after_status": result.get("after_status") or (result.get("item") or {}).get("review_status"),
            }
        )

    technical_repairs = _apply_technical_lineage_repairs(
        db,
        load_staging_items(db, source_file_hash=source_file_hash),
        source_file_hash=source_file_hash,
        actor=actor,
        acted_at=acted_at,
    )
    final_items = load_staging_items(db, source_file_hash=source_file_hash)
    reconciliation = build_owner_reconciliation(final_items)
    status_counts: dict[str, int] = {}
    for item in final_items:
        status = str(item.get("review_status") or "RAW")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "owner_decision_batch_id": OWNER_DECISION_BATCH_ID,
        "actor": actor,
        "source_file_hash": source_file_hash,
        "target_source_rows": target_rows,
        "not_confirmed_source_rows": list(NOT_CONFIRMED_SOURCE_ROWS),
        "applied": applied,
        "technical_repairs": technical_repairs,
        "applied_count": sum(1 for item in applied if item["status"] == "APPLIED")
        + sum(1 for item in technical_repairs if item["status"] == "APPLIED"),
        "idempotent_count": sum(1 for item in applied if item["status"] == "IDEMPOTENT")
        + sum(1 for item in technical_repairs if item["status"] in {"IDEMPOTENT", "SKIPPED_ALREADY_REPAIRED"}),
        "status_counts": dict(sorted(status_counts.items())),
        "reconciliation": reconciliation,
        "canonical_writes": 0,
        "cutover_status": "DRAFT",
        "approval_status": "NOT_APPROVED",
        "live_status": "NOT_LIVE",
    }


__all__ = [
    "LEGACY_RECEIVED_ALIAS_ROWS",
    "NOT_CONFIRMED_SOURCE_ROWS",
    "OWNER_ACTOR",
    "OWNER_DECISION_BATCH_ID",
    "OwnerDecisionApplyError",
    "TECHNICAL_LINEAGE_REPAIR_ID",
    "apply_owner_decisions",
]
