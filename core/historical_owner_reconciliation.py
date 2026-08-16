"""Pure LOG-C06 Owner-decision lineage and checkpoint reconciliation.

The functions in this module consume staged item dictionaries only.  They do
not read a database, change review status, or create a canonical financial
effect.  The source-row constants are deliberately scoped to the Owner
decisions already confirmed for the LOG-C06 staging review.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


OWNER_RECONCILIATION_VERSION = "log-c06-owner-reconciliation-v2"
OWNER_DECISION_BATCH_ID = "LOG-C06-OWNER-DECISIONS-2026-08-15"

SNAPSHOT_SOURCE_ROW = 86
SNAPSHOT_AMOUNT = Decimal("99824.43")
CREDIT_SOURCE_ROW = 16

CHECKPOINT_SOURCE_ROW = 129
CHECKPOINT_AMOUNT = Decimal("134973")
CHECKPOINT_COMPONENT_ROWS = (103, 104, 105, 106, 107, 108, 111, 114, 116, 120, 121)
BG_GREEN_SOURCE_ROW = 99
FULL_PAID_ON_BEHALF_AMOUNT = Decimal("159998")

# These are the six historical oracle labels from LOG-C06.  The late labels
# point to the physical source cells on rows 192/199/200; keeping the oracle
# label separate from the staging row prevents the old off-by-two alias from
# being treated as a new business event.
RECEIVED_GROUP_ROWS = (102, 109, 115, 192, 199, 200)
RECEIVED_GROUP_EXPECTED_AMOUNT = Decimal("416482.2426005565")
SHIPMENT_COST_EXPECTED_AMOUNT = Decimal("418060.79")
HISTORICAL_POSITION_EXPECTED_AMOUNT = Decimal("161576.5473994435")

RECEIVED_SOURCE_ORACLES = (
    {
        "oracle_id": "C102",
        "staging_source_row": 102,
        "source_cell": "Sheet2!C102",
        "source_excel_row": 102,
        "verified_amount": Decimal("62464"),
        "raw_note": "nhan ho wa WC (c\u1ee7a x\u01b0\u1edfng \u0111\u1ed3 ch\u01a1i th\u00e0nh v\u0169)",
        "context": "nha may do choi / Thanh Vu chuyen tien cho Thanh",
        "currency_context": "CNY",
    },
    {
        "oracle_id": "C109",
        "staging_source_row": 109,
        "source_cell": "Sheet2!C109",
        "source_excel_row": 109,
        "verified_amount": Decimal("1687"),
        "raw_note": "nhan ho wa WC - nh\u00e0 m\u00e1y n\u1ed9i th\u1ea5t thanh to\u00e1n ti\u1ec1n vc",
        "context": "nha may Luc Giac thanh toan tien van chuyen cho Thanh",
        "currency_context": "CNY",
    },
    {
        "oracle_id": "C115",
        "staging_source_row": 115,
        "source_cell": "Sheet2!C115",
        "source_excel_row": 115,
        "verified_amount": Decimal("25297.24260055654"),
        "raw_note": "ty gia 3953",
        "context": "Thanh chuyen tien; C115 = 100,000,000 VND / 3,953",
        "currency_context": "CNY; source conversion context 100000000 VND / 3953",
        "fx_rate": Decimal("3953"),
        "related_source_cell": "Sheet2!B115",
        "related_raw_value": Decimal("100000000"),
    },
    {
        "oracle_id": "C190",
        "staging_source_row": 192,
        "source_cell": "Sheet2!C192",
        "source_excel_row": 192,
        "verified_amount": Decimal("183549"),
        "raw_note": "xuong chuyen phi van chuyen da mo hoa don (4 xe ngay 4/4)",
        "context": "Thanh; historical oracle C190 maps to physical source row 192",
        "currency_context": "CNY",
    },
    {
        "oracle_id": "C197",
        "staging_source_row": 199,
        "source_cell": "Sheet2!C199",
        "source_excel_row": 199,
        "verified_amount": Decimal("19000"),
        "raw_note": "Phi bao quan cua 4 xe ngay 21/4",
        "context": "Thanh; historical oracle C197 maps to physical source row 199",
        "currency_context": "CNY",
    },
    {
        "oracle_id": "C198",
        "staging_source_row": 200,
        "source_cell": "Sheet2!C200",
        "source_excel_row": 200,
        "verified_amount": Decimal("124485"),
        "raw_note": "xuong chuyen phi van chuyen da mo hoa don (4 xe ngay 21/4)",
        "context": "Thanh; historical oracle C198 maps to physical source row 200",
        "currency_context": "CNY",
    },
)
RECEIVED_SOURCE_ORACLE_BY_ROW = {
    entry["staging_source_row"]: entry for entry in RECEIVED_SOURCE_ORACLES
}

SNAPSHOT_AMOUNT_SOURCE_CELL = "Sheet2!E86"
SNAPSHOT_NOTE_CELL = "Sheet2!D86"
SNAPSHOT_NOTE = "c\u1ee7a th\u00e0nh = E76 + 83"
SNAPSHOT_RECONSTRUCTION = {
    "formula": "Sheet2!E77 + Sheet2!E85",
    "component_cells": ["Sheet2!E77", "Sheet2!E85"],
    "component_values": [Decimal("96324.43"), Decimal("3500")],
    "reconstructed_amount": Decimal("99824.43"),
}

OLD_M89_RECEIVED_AMOUNT = Decimal("89448.24260055654")
OLD_M89_POSITION = Decimal("170374.18739944347")
RECONCILIATION_TOLERANCE = Decimal("0.0000000001")

PAID_GROUP_KEY = "PAID_ON_BEHALF_FULL_159998_CNY"
PAID_CHECKPOINT_GROUP_KEY = "PAID_ON_BEHALF_CHECKPOINT_134973_CNY"
RECEIVED_GROUP_KEY = "RECEIVED_ON_BEHALF_416482_2426005565_CNY"
SNAPSHOT_LINEAGE_KEY = "SNAPSHOT_99824_43_EMBEDS_CREDIT_24576_CNY"


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


def _currency(item: Mapping[str, Any]) -> str:
    proposal = _proposal(item)
    return str(proposal.get("currency") or item.get("raw_currency") or "UNKNOWN").upper()


def _source_reference(item: Mapping[str, Any]) -> str:
    return str(item.get("source_reference") or f"{item.get('sheet')}!row {_source_row(item)}")


def _trace(item: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None
    proposal = _proposal(item)
    amount = _amount(item)
    technical_lineage = proposal.get("technical_lineage")
    if not isinstance(technical_lineage, Mapping):
        technical_lineage = {}
    return {
        "source_item_id": item.get("source_item_id"),
        "source_reference": _source_reference(item),
        "source_row": _source_row(item),
        "source_cell": (
            proposal.get("amount_source_cell")
            or technical_lineage.get("source_cell")
            or f"C{_source_row(item)}"
        ),
        "amount_source_kind": proposal.get("amount_source_kind"),
        "amount_source_raw_value": proposal.get("amount_source_raw_value"),
        "amount": float(amount) if amount is not None else None,
        "currency": _currency(item),
        "review_status": item.get("review_status") or "RAW",
        "event_type": proposal.get("event_type"),
        "reconciliation_role": proposal.get("reconciliation_role"),
    }


def _by_source_row(items: Iterable[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for item in items:
        row = _source_row(item)
        if row and row not in result:
            result[row] = dict(item)
    return result


def _raw_snapshot_amount(item: Mapping[str, Any] | None) -> Decimal | None:
    if item is None:
        return None
    raw_values = item.get("raw_values")
    if not isinstance(raw_values, Mapping):
        return None
    preferred_keys = (
        f"E{SNAPSHOT_SOURCE_ROW}",
        f"F{SNAPSHOT_SOURCE_ROW}",
        f"F{SNAPSHOT_SOURCE_ROW + 1}",
        f"E{SNAPSHOT_SOURCE_ROW + 1}",
    )
    for key in preferred_keys:
        amount = _decimal(raw_values.get(key))
        if amount is not None:
            return amount
    for key, value in raw_values.items():
        if str(key).upper().startswith(("E", "F")):
            amount = _decimal(value)
            if amount is not None:
                return amount
    return None


def _sum_amounts(items: Iterable[Mapping[str, Any]]) -> Decimal:
    return sum((_amount(item) or Decimal("0") for item in items), Decimal("0"))


def _status_for_difference(total: Decimal, expected: Decimal, *, missing: bool = False) -> str:
    if missing:
        return "INCOMPLETE_SOURCE_SET"
    return "EXACT_MATCH" if abs(total - expected) <= RECONCILIATION_TOLERANCE else "DIFFERENCE"


def _checkpoint_difference(total: Decimal, expected: Decimal) -> Decimal:
    difference = total - expected
    return Decimal("0") if abs(difference) <= RECONCILIATION_TOLERANCE else difference


def _component_rows(
    by_row: Mapping[int, Mapping[str, Any]],
    source_rows: Iterable[int],
) -> list[dict[str, Any]]:
    return [
        trace
        for row in source_rows
        if (trace := _trace(by_row.get(row))) is not None
    ]


def build_received_source_reconciliation(
    items: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare the six verified source oracles to their staged rows.

    The source oracle metadata is read-only evidence captured from the
    workbook.  ``items`` is the current staging projection.  No balancing
    value is invented when a row is absent or not confirmed.
    """

    by_row = _by_source_row(items)
    rows: list[dict[str, Any]] = []
    for oracle in RECEIVED_SOURCE_ORACLES:
        staging_row = int(oracle["staging_source_row"])
        item = by_row.get(staging_row)
        proposal = _proposal(item or {})
        staged_raw = _decimal(item.get("raw_amount")) if item else None
        normalized = _amount(item) if item else None
        confirmed = normalized if item and item.get("review_status") == "CONFIRMED" else None
        included = confirmed
        verified = oracle["verified_amount"]
        if item is None:
            classification = "MISSING_STAGING_ROW"
            exclusion_reason = "No staging item exists for the verified physical source row."
        elif confirmed is None:
            classification = str(item.get("review_status") or "REVIEW_REQUIRED")
            exclusion_reason = "Staged row is not confirmed, so it is excluded from the included total."
        else:
            classification = str(proposal.get("event_type") or proposal.get("classification") or "unknown")
            exclusion_reason = None
        technical_lineage = proposal.get("technical_lineage")
        if not isinstance(technical_lineage, Mapping):
            technical_lineage = {}
        row = {
            "source_oracle": oracle["oracle_id"],
            "source_cell": oracle["source_cell"],
            "source_excel_row": oracle["source_excel_row"],
            "verified_raw_value": float(verified),
            "verified_amount": float(verified),
            "raw_note": oracle["raw_note"],
            "context": oracle["context"],
            "currency_context": oracle["currency_context"],
            "related_source_cell": oracle.get("related_source_cell"),
            "related_raw_value": (
                float(oracle["related_raw_value"])
                if oracle.get("related_raw_value") is not None
                else None
            ),
            "fx_rate": float(oracle["fx_rate"]) if oracle.get("fx_rate") is not None else None,
            "staging_source_item_id": item.get("source_item_id") if item else None,
            "staging_source_row": staging_row,
            "staged_raw_amount": float(staged_raw) if staged_raw is not None else None,
            "normalized_amount": float(normalized) if normalized is not None else None,
            "confirmed_amount": float(confirmed) if confirmed is not None else None,
            "included_amount": float(included) if included is not None else 0.0,
            "delta": float(verified - (included or Decimal("0"))),
            "classification": classification,
            "exclusion_reason": exclusion_reason,
            "technical_lineage": dict(technical_lineage) if technical_lineage else None,
        }
        rows.append(row)
    delta_sum = sum(
        (Decimal(str(row["delta"])) for row in rows),
        Decimal("0"),
    )
    verified_total = sum((oracle["verified_amount"] for oracle in RECEIVED_SOURCE_ORACLES), Decimal("0"))
    included_total = sum((Decimal(str(row["included_amount"])) for row in rows), Decimal("0"))
    return {
        "oracle_count": len(RECEIVED_SOURCE_ORACLES),
        "rows": rows,
        "verified_total": float(verified_total),
        "included_total": float(included_total),
        "delta_sum": float(delta_sum),
        "expected_total": float(RECEIVED_GROUP_EXPECTED_AMOUNT),
        "status": "RECONCILED" if delta_sum == Decimal("0") else "DIFFERENCE",
        "row_mapping_note": "C190/C197/C198 are historical oracle labels mapped to physical rows C192/C199/C200.",
    }


def build_owner_reconciliation(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the Owner-confirmed component/checkpoint graph without mutation."""

    rows = [dict(item) for item in items]
    by_row = _by_source_row(rows)
    credit = by_row.get(CREDIT_SOURCE_ROW)
    snapshot = by_row.get(SNAPSHOT_SOURCE_ROW)
    checkpoint = by_row.get(CHECKPOINT_SOURCE_ROW)
    checkpoint_components = [
        by_row[row]
        for row in CHECKPOINT_COMPONENT_ROWS
        if row in by_row
    ]
    paid_components = [
        item
        for row in (BG_GREEN_SOURCE_ROW, *CHECKPOINT_COMPONENT_ROWS)
        if (item := by_row.get(row)) is not None
    ]
    received_components = [
        by_row[row]
        for row in RECEIVED_GROUP_ROWS
        if row in by_row
    ]

    checkpoint_component_total = _sum_amounts(checkpoint_components)
    paid_component_total = _sum_amounts(paid_components)
    received_component_total = _sum_amounts(received_components)
    received_source_reconciliation = build_received_source_reconciliation(rows)
    received_missing = len(received_components) != len(RECEIVED_GROUP_ROWS)
    checkpoint_missing = len(checkpoint_components) != len(CHECKPOINT_COMPONENT_ROWS)
    paid_missing = len(paid_components) != 1 + len(CHECKPOINT_COMPONENT_ROWS)

    snapshot_raw_amount = _raw_snapshot_amount(snapshot)
    snapshot_status = "MISSING_SOURCE" if snapshot is None else "EMBEDDED_IN_SNAPSHOT"
    if snapshot is not None and snapshot_raw_amount is not None and abs(snapshot_raw_amount - SNAPSHOT_AMOUNT) > Decimal("0.005"):
        snapshot_status = "SOURCE_VALUE_DIFFERENCE"
    snapshot_trace = _trace(snapshot)
    if snapshot_trace is not None:
        snapshot_trace["checkpoint_amount_from_raw_values"] = float(snapshot_raw_amount) if snapshot_raw_amount is not None else None

    checkpoint_reconciliation = {
        "checkpoint_key": "THANH_ACCUMULATED_134973",
        "checkpoint_source": _trace(checkpoint),
        "expected_amount": float(CHECKPOINT_AMOUNT),
        "currency": "CNY",
        "operation": "sum",
        "component_rows": _component_rows(by_row, CHECKPOINT_COMPONENT_ROWS),
        "component_source_item_ids": [
            str(item.get("source_item_id"))
            for item in checkpoint_components
            if item.get("source_item_id")
        ],
        "component_amount": float(checkpoint_component_total),
        "difference": float(_checkpoint_difference(checkpoint_component_total, CHECKPOINT_AMOUNT)),
        "status": _status_for_difference(
            checkpoint_component_total,
            CHECKPOINT_AMOUNT,
            missing=checkpoint_missing,
        ),
        "summary_is_not_component": True,
        "opening_inclusion": "exclude_summary",
        "double_count_guard": {
            "summary_source_row": CHECKPOINT_SOURCE_ROW,
            "summary_source_item_id": checkpoint.get("source_item_id") if checkpoint else None,
            "summary_added_as_event": False,
            "component_rows_plus_summary_forbidden": True,
        },
    }

    full_paid_group = {
        "group_key": PAID_GROUP_KEY,
        "meaning": "A Bò chi/chuyển hộ cho Thành",
        "currency": "CNY",
        "expected_amount": float(FULL_PAID_ON_BEHALF_AMOUNT),
        "formula": "134,973 + 25,025 = 159,998 CNY",
        "component_rows": _component_rows(
            by_row,
            (BG_GREEN_SOURCE_ROW, *CHECKPOINT_COMPONENT_ROWS),
        ),
        "component_source_item_ids": [
            str(item.get("source_item_id"))
            for item in paid_components
            if item.get("source_item_id")
        ],
        "component_amount": float(paid_component_total),
        "difference": float(_checkpoint_difference(paid_component_total, FULL_PAID_ON_BEHALF_AMOUNT)),
        "status": _status_for_difference(
            paid_component_total,
            FULL_PAID_ON_BEHALF_AMOUNT,
            missing=paid_missing,
        ),
        "subgroups": [
            {
                "group_key": "BG_GREEN_D99_25025_CNY",
                "source_rows": [BG_GREEN_SOURCE_ROW],
                "amount": float(_amount(by_row[BG_GREEN_SOURCE_ROW]) or Decimal("0"))
                if BG_GREEN_SOURCE_ROW in by_row
                else None,
            },
            {
                "group_key": PAID_CHECKPOINT_GROUP_KEY,
                "source_rows": list(CHECKPOINT_COMPONENT_ROWS),
                "amount": float(checkpoint_component_total),
                "checkpoint_source_row": CHECKPOINT_SOURCE_ROW,
            },
        ],
        "derived_total_is_not_an_additional_event": True,
        "double_count_guard": {
            "checkpoint_summary_row": CHECKPOINT_SOURCE_ROW,
            "checkpoint_summary_excluded_from_components": True,
            "derived_total_excluded_from_components": True,
            "source_component_count": 1 + len(CHECKPOINT_COMPONENT_ROWS),
        },
    }

    received_group = {
        "group_key": RECEIVED_GROUP_KEY,
        "meaning": "A Bò nhận hộ / tiền vào cho Thành",
        "currency": "CNY",
        "expected_amount": float(RECEIVED_GROUP_EXPECTED_AMOUNT),
        "source_cell_rows": list(RECEIVED_GROUP_ROWS),
        "component_source_rows": list(RECEIVED_GROUP_ROWS),
        "source_oracle_ids": [entry["oracle_id"] for entry in RECEIVED_SOURCE_ORACLES],
        "physical_source_cells": [entry["source_cell"] for entry in RECEIVED_SOURCE_ORACLES],
        "component_rows": _component_rows(by_row, RECEIVED_GROUP_ROWS),
        "component_source_item_ids": [
            str(item.get("source_item_id"))
            for item in received_components
            if item.get("source_item_id")
        ],
        "component_amount": float(received_component_total),
        "difference": float(_checkpoint_difference(received_component_total, RECEIVED_GROUP_EXPECTED_AMOUNT)),
        "expected_minus_source": float(_checkpoint_difference(RECEIVED_GROUP_EXPECTED_AMOUNT, received_component_total)),
        "status": _status_for_difference(
            received_component_total,
            RECEIVED_GROUP_EXPECTED_AMOUNT,
            missing=received_missing,
        ),
        "checkpoint_status": (
            "RECONCILED"
            if received_source_reconciliation["status"] == "RECONCILED"
            else "DIFFERENCE"
        ),
        "source_reconciliation": received_source_reconciliation,
        "missing_source_rows": [
            row for row in RECEIVED_GROUP_ROWS if row not in by_row
        ],
        "allocation": "unallocated unless a canonical shipment link is separately proven",
        "double_count_guard": {
            "components_are_separate_money_events": True,
            "do_not_merge_with_paid_on_behalf_group": True,
            "checkpoint_total_is_expectation_only": True,
        },
    }

    received_position_base = (
        RECEIVED_GROUP_EXPECTED_AMOUNT
        if received_group["status"] == "EXACT_MATCH"
        else received_component_total
    )
    historical_position = {
        "checkpoint_key": "HISTORICAL_ABO_POSITION_161576_5473994435",
        "shipment_costs": float(SHIPMENT_COST_EXPECTED_AMOUNT),
        "paid_on_behalf": float(FULL_PAID_ON_BEHALF_AMOUNT),
        "received_on_behalf_expected": float(RECEIVED_GROUP_EXPECTED_AMOUNT),
        "expected_position": float(HISTORICAL_POSITION_EXPECTED_AMOUNT),
        "formula": "418,060.79 + 159,998 - 416,482.2426005565 = 161,576.5473994435 CNY",
        "source_received_total": received_group["component_amount"],
        "source_received_difference": received_group["difference"],
        "reconstructed_position_using_source_received": float(
            SHIPMENT_COST_EXPECTED_AMOUNT
            + FULL_PAID_ON_BEHALF_AMOUNT
            - received_position_base
        )
        if not received_missing and not paid_missing
        else None,
        "difference_vs_expected_position": float(
            SHIPMENT_COST_EXPECTED_AMOUNT
            + FULL_PAID_ON_BEHALF_AMOUNT
            - received_position_base
            - HISTORICAL_POSITION_EXPECTED_AMOUNT
        )
        if not received_missing and not paid_missing
        else None,
        "status": "CHECKPOINT_EXPECTATION",
        "opening_truth": "not_published_and_not_automatically_used_as_current_opening",
        "remaining_material_differences": [
            {
                "difference_key": "RECEIVED_GROUP_SOURCE_VS_CHECKPOINT",
                "amount": received_group["difference"],
                "absolute_amount": abs(received_group["difference"]),
                "source_rows": list(RECEIVED_GROUP_ROWS),
                "reason": "Six Owner-named source cells do not reproduce the 416,482.2426005565 expectation.",
            }
        ]
        if received_components and received_group["status"] != "EXACT_MATCH"
        else [],
    }
    old_m89_reconciliation = {
        "checkpoint_name": "old M89",
        "old_received_group": float(OLD_M89_RECEIVED_AMOUNT),
        "old_position": float(OLD_M89_POSITION),
        "superseded_by": {
            "received_group": float(RECEIVED_GROUP_EXPECTED_AMOUNT),
            "position": float(HISTORICAL_POSITION_EXPECTED_AMOUNT),
        },
        "status": "SUPERSEDED_CHECKPOINT",
        "do_not_combine_snapshots": True,
        "formula": "old M89 = 170,374.18739944347; later additions C190+C197+C198 = 327,034",
    }

    graph_nodes: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    for item in paid_components + received_components + [credit, snapshot, checkpoint]:
        trace = _trace(item)
        if trace and trace["source_item_id"] not in {
            node.get("source_item_id") for node in graph_nodes
        }:
            graph_nodes.append({"node_type": "source_item", **trace})
    graph_nodes.extend(
        [
            {
                "node_type": "checkpoint",
                "node_id": "CHECKPOINT_99824_43_CNY",
                "amount": float(SNAPSHOT_AMOUNT),
                "currency": "CNY",
                "source_row": SNAPSHOT_SOURCE_ROW,
                "source_item_id": snapshot.get("source_item_id") if snapshot else None,
            },
            {
                "node_type": "checkpoint",
                "node_id": "CHECKPOINT_134973_CNY",
                "amount": float(CHECKPOINT_AMOUNT),
                "currency": "CNY",
                "source_row": CHECKPOINT_SOURCE_ROW,
                "source_item_id": checkpoint.get("source_item_id") if checkpoint else None,
            },
            {
                "node_type": "derived_group",
                "node_id": PAID_GROUP_KEY,
                "amount": float(FULL_PAID_ON_BEHALF_AMOUNT),
                "currency": "CNY",
            },
            {
                "node_type": "checkpoint_expectation",
                "node_id": RECEIVED_GROUP_KEY,
                "amount": float(RECEIVED_GROUP_EXPECTED_AMOUNT),
                "currency": "CNY",
            },
        ]
    )
    if credit and snapshot:
        graph_edges.append(
            {
                "from_source_item_id": credit.get("source_item_id"),
                "to_node_id": "CHECKPOINT_99824_43_CNY",
                "relationship": "embedded_in_snapshot",
                "amount": float(_amount(credit) or Decimal("0")),
                "double_count_forbidden": True,
            }
        )
    for item in checkpoint_components:
        graph_edges.append(
            {
                "from_source_item_id": item.get("source_item_id"),
                "to_node_id": "CHECKPOINT_134973_CNY",
                "relationship": "component_of",
                "double_count_forbidden": False,
            }
        )
    if checkpoint:
        graph_edges.append(
            {
                "from_source_item_id": checkpoint.get("source_item_id"),
                "to_node_id": "CHECKPOINT_134973_CNY",
                "relationship": "summary_identity",
                "financial_event": False,
                "double_count_forbidden": True,
            }
        )
    for item in paid_components:
        graph_edges.append(
            {
                "from_source_item_id": item.get("source_item_id"),
                "to_node_id": PAID_GROUP_KEY,
                "relationship": "component_of_derived_total",
                "double_count_forbidden": False,
            }
        )
    for item in received_components:
        graph_edges.append(
            {
                "from_source_item_id": item.get("source_item_id"),
                "to_node_id": RECEIVED_GROUP_KEY,
                "relationship": "component_of_checkpoint_expectation",
                "double_count_forbidden": False,
            }
        )

    return {
        "version": OWNER_RECONCILIATION_VERSION,
        "owner_decision_batch_id": OWNER_DECISION_BATCH_ID,
        "snapshot_credit_lineage": {
            "lineage_key": SNAPSHOT_LINEAGE_KEY,
            "credit_source": _trace(credit),
            "snapshot_checkpoint": snapshot_trace,
            "snapshot_amount": float(SNAPSHOT_AMOUNT),
            "confirmed_snapshot_amount": float(SNAPSHOT_AMOUNT),
            "source_amount_cell": SNAPSHOT_AMOUNT_SOURCE_CELL,
            "source_note_cell": SNAPSHOT_NOTE_CELL,
            "source_note": SNAPSHOT_NOTE,
            "source_reconstruction": {
                "formula": SNAPSHOT_RECONSTRUCTION["formula"],
                "component_cells": list(SNAPSHOT_RECONSTRUCTION["component_cells"]),
                "component_values": [float(value) for value in SNAPSHOT_RECONSTRUCTION["component_values"]],
                "reconstructed_amount": float(SNAPSHOT_RECONSTRUCTION["reconstructed_amount"]),
                "cached_formula_present": False,
                "stored_numeric_value": float(snapshot_raw_amount) if snapshot_raw_amount is not None else None,
            },
            "status": snapshot_status,
            "opening_inclusion": "embedded_in_snapshot",
            "standalone_opening_amount": 0.0,
            "formula": "24,576 CNY -> historical checkpoint 99,824.43 CNY -> opening lineage; do not subtract twice",
            "double_count_guard": {
                "credit_reapplied_to_snapshot": False,
                "credit_reapplied_to_opening": False,
                "snapshot_is_not_added_as_a_new_event": True,
            },
        },
        "checkpoint_134973": checkpoint_reconciliation,
        "paid_on_behalf_group": full_paid_group,
        "received_on_behalf_group": received_group,
        "old_m89_reconciliation": old_m89_reconciliation,
        "historical_position_checkpoint": historical_position,
        "component_checkpoint_graph": {
            "node_count": len(graph_nodes),
            "edge_count": len(graph_edges),
            "nodes": graph_nodes,
            "edges": graph_edges,
            "double_count_protection": [
                "CHECKPOINT_134973_CNY is a summary, not an additional event.",
                "PAID_ON_BEHALF_FULL_159998_CNY is derived from 25,025 plus the 134,973 components.",
                "CHECKPOINT_99824_43_CNY already embeds the 24,576 credit.",
            ],
        },
        "opening_lineage": {
            "base_source_components": [
                PAID_GROUP_KEY,
                RECEIVED_GROUP_KEY,
            ],
            "post_base_events": [],
            "position_scope": "confirmed_staging_buckets_only",
            "embedded_snapshot_components_excluded": [
                str(credit.get("source_item_id")) if credit else None
            ],
            "summary_rows_excluded": [
                str(checkpoint.get("source_item_id")) if checkpoint else None
            ],
            "opening_publication": "forbidden_until_separate_owner_approval",
        },
        "material_difference_count": len(historical_position["remaining_material_differences"]),
        "cutover_lock": "DRAFT / NOT_APPROVED / NOT_LIVE",
        "canonical_mutations": 0,
    }


__all__ = [
    "BG_GREEN_SOURCE_ROW",
    "CHECKPOINT_AMOUNT",
    "CHECKPOINT_COMPONENT_ROWS",
    "CHECKPOINT_SOURCE_ROW",
    "CREDIT_SOURCE_ROW",
    "FULL_PAID_ON_BEHALF_AMOUNT",
    "OWNER_DECISION_BATCH_ID",
    "OWNER_RECONCILIATION_VERSION",
    "PAID_CHECKPOINT_GROUP_KEY",
    "PAID_GROUP_KEY",
    "RECEIVED_GROUP_EXPECTED_AMOUNT",
    "RECEIVED_GROUP_KEY",
    "RECEIVED_GROUP_ROWS",
    "RECEIVED_SOURCE_ORACLES",
    "RECEIVED_SOURCE_ORACLE_BY_ROW",
    "OLD_M89_POSITION",
    "OLD_M89_RECEIVED_AMOUNT",
    "RECONCILIATION_TOLERANCE",
    "SHIPMENT_COST_EXPECTED_AMOUNT",
    "SNAPSHOT_AMOUNT",
    "SNAPSHOT_LINEAGE_KEY",
    "SNAPSHOT_SOURCE_ROW",
    "SNAPSHOT_AMOUNT_SOURCE_CELL",
    "SNAPSHOT_NOTE_CELL",
    "build_received_source_reconciliation",
    "build_owner_reconciliation",
]
