"""Deterministic LOG-C06 P6 blocker reconstruction.

This module is a read-only, source-shaped projection for the P6 review.  It
does not change staging status, write the canonical ledger, or publish an
opening position.  The workbook parser stores source cells one column and
one row to the right of their physical Sheet2 coordinates; the small helper
below reverses that representation for the source-context tables shown to an
Owner.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


P6_RECONCILIATION_VERSION = "log-c06-p6-owner-review-reconciliation-v1"
P6_SOURCE_HASH = "857db72b86220a4af302c0de6900710c49f44b2223c458c009748dd767840b70"
P6_SOURCE_RANGE = "Sheet2!A1:Z282"

P6_TRANSFER_ROWS = (201, 202, 203, 204, 205)
P6_GOODS_DETAIL_ROWS = tuple(range(213, 220))
P6_GOODS_SUBTOTAL_ROW = 224
P6_FREIGHT_ROWS = (229, 230)
P6_FREIGHT_SUBTOTAL_ROW = 235
P6_FREIGHT_CUMULATIVE_ROW = 236

P6_GOODS_SUBTOTAL = Decimal("16929.56")
P6_FREIGHT_SUBTOTAL = Decimal("7060")
P6_FREIGHT_TOTAL = Decimal("18560")
P6_TRANSFER_CONVERTED_TOTAL = Decimal("392796.30579784507")
P6_TRANSFER_ON_BEHALF_TOTAL = Decimal("392790")
P6_TRANSFER_VND_INPUT_TOTAL = Decimal("1531120000")
P6_TRANSFER_COLUMN_DIFFERENCE = Decimal("6.30579784507")

P6_BASE_OPENING = Decimal("161576.5473994435")
P6_SHIPMENT_COST_EXPECTATION = Decimal("418060.79")
P6_RESIDUAL_SOURCE_AMOUNT = Decimal("1572")
P6_RESIDUAL_ADJACENT_AMOUNT = Decimal("1572.5800933125972")
P6_RESIDUAL_CHECKPOINT_AMOUNT = Decimal("1578.5474")

_CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        result = Decimal(str(value).replace(",", ""))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _row(item: Mapping[str, Any]) -> int:
    try:
        return int(item.get("source_row") or 0)
    except (TypeError, ValueError):
        return 0


def _proposal(item: Mapping[str, Any]) -> Mapping[str, Any]:
    proposal = item.get("proposal")
    return proposal if isinstance(proposal, Mapping) else {}


def _date_for(item: Mapping[str, Any]) -> str | None:
    raw = item.get("raw_date") or item.get("inherited_date_context")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10]).isoformat()
    except ValueError:
        return None


def _column_number(column: str) -> int:
    number = 0
    for character in column:
        number = number * 26 + (ord(character) - ord("A") + 1)
    return number


def _column_name(number: int) -> str:
    result = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _physical_cells(item: Mapping[str, Any]) -> dict[str, Any]:
    """Return raw_values as physical Sheet2 cells.

    The staging parser's raw_values use ``column+1`` and ``row+1`` keys.  A
    source item whose key is ``N230`` therefore represents physical
    ``M229``.  This transformation is deliberately local to the P6 source
    investigation and does not mutate the staged document.
    """

    raw_values = item.get("raw_values")
    if not isinstance(raw_values, Mapping):
        return {}
    physical: dict[str, Any] = {}
    for key, value in raw_values.items():
        match = _CELL_RE.match(str(key).upper())
        if not match:
            continue
        column, row_text = match.groups()
        row_number = int(row_text) - 1
        column_number = _column_number(column) - 1
        if row_number < 1 or column_number < 1:
            continue
        physical[f"{_column_name(column_number)}{row_number}"] = value
    return physical


def _physical_cell(item: Mapping[str, Any], column: str) -> Any:
    physical = _physical_cells(item)
    source_row = _row(item)
    return physical.get(f"{column}{source_row}")


def _physical_source_cells(item: Mapping[str, Any]) -> list[str]:
    source_row = _row(item)
    return sorted(
        cell
        for cell in _physical_cells(item)
        if cell[1:].isdigit() and int(cell[1:]) == source_row
    )


def _parse_vnd(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*VND", text, flags=re.IGNORECASE)
    return _decimal(match.group(1)) if match else None


def _money(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _source_row_evidence(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "staging_source_row": _row(item),
        "physical_source_row": _row(item),
        "source_reference": item.get("source_reference") or f"Sheet2!row {_row(item)}",
        "physical_source_cells": [f"Sheet2!{cell}" for cell in _physical_source_cells(item)],
        "date": _date_for(item),
    }


def _transfer_row(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_source_row_evidence(item),
        "vnd_input": _money(_parse_vnd(_physical_cell(item, "B"))),
        "converted_cny": _money(_decimal(_physical_cell(item, "C"))),
        "chuyen_ho_cny": _money(_decimal(_physical_cell(item, "D"))),
        "physical_columns": {
            "date": _physical_cell(item, "A"),
            "vnd_input": _physical_cell(item, "B"),
            "hach_ra_tien_te": _physical_cell(item, "C"),
            "chuyen_ho": _physical_cell(item, "D"),
        },
    }


def _sum_field(rows: Iterable[Mapping[str, Any]], field: str) -> Decimal:
    return sum(
        (_decimal(row.get(field)) or Decimal("0") for row in rows),
        Decimal("0"),
    )


def _transfer_reconstruction(items_by_row: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    rows = [
        _transfer_row(items_by_row[row])
        for row in P6_TRANSFER_ROWS
        if row in items_by_row
    ]
    groups = []
    for group_key, group_rows in (
        ("201", (201,)),
        ("202-203", (202, 203)),
        ("204-205", (204, 205)),
    ):
        group = [row for row in rows if row["staging_source_row"] in group_rows]
        groups.append(
            {
                "group_key": group_key,
                "staging_source_rows": list(group_rows),
                "physical_source_rows": list(group_rows),
                "converted_cny": _money(_sum_field(group, "converted_cny")),
                "chuyen_ho_cny": _money(_sum_field(group, "chuyen_ho_cny")),
                "vnd_input": _money(_sum_field(group, "vnd_input")),
                "source_cells": sorted(
                    cell
                    for row in group
                    for cell in row["physical_source_cells"]
                ),
            }
        )
    converted = _sum_field(rows, "converted_cny")
    on_behalf = _sum_field(rows, "chuyen_ho_cny")
    vnd_input = _sum_field(rows, "vnd_input")
    return {
        "table_title": "NHAN CHUYEN TIEN USD (2026-T4+5)",
        "source_rows": list(P6_TRANSFER_ROWS),
        "source_cells": sorted(
            cell for row in rows for cell in row["physical_source_cells"]
        ),
        "rows": rows,
        "groups": groups,
        "totals": {
            "hach_ra_tien_te_cny": _money(converted),
            "chuyen_ho_cny": _money(on_behalf),
            "vnd_input": _money(vnd_input),
            "column_difference_cny": _money(converted - on_behalf),
        },
        "expected_totals": {
            "hach_ra_tien_te_cny": _money(P6_TRANSFER_CONVERTED_TOTAL),
            "chuyen_ho_cny": _money(P6_TRANSFER_ON_BEHALF_TOTAL),
            "vnd_input": _money(P6_TRANSFER_VND_INPUT_TOTAL),
            "column_difference_cny": _money(P6_TRANSFER_COLUMN_DIFFERENCE),
        },
        "semantic_status": "OWNER_REQUIRED",
        "known": [
            "The source is a conversion/transfer-on-behalf table, not a freight table.",
            "C is Hach ra tien te and D is chuyen ho; the grouped D cells are merged in the source.",
            "The table has no explicit SALE, shipment, or A Bo relationship.",
        ],
        "unknown": [
            "Whether this group is a financial leg between A Bo and Thanh.",
            "Which column, if any, is the opening-impact leg after the business meaning is confirmed.",
        ],
    }


def _goods_row(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_source_row_evidence(item),
        "description": _physical_cell(item, "B"),
        "shipment_code": _physical_cell(item, "C"),
        "weight": _money(_decimal(_physical_cell(item, "E"))),
        "cbm": _money(_decimal(_physical_cell(item, "F"))),
        "unit_price": _money(_decimal(_physical_cell(item, "G"))),
        "goods_amount": _money(_decimal(_physical_cell(item, "H"))),
        "freight_total": _money(_decimal(_physical_cell(item, "M"))),
        "sale": _physical_cell(item, "N"),
        "operational_only": True,
        "financial_leg": "UNKNOWN",
    }


def _goods_reconstruction(items_by_row: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    rows = [
        _goods_row(items_by_row[row])
        for row in P6_GOODS_DETAIL_ROWS
        if row in items_by_row
    ]
    subtotal_item = items_by_row.get(P6_GOODS_SUBTOTAL_ROW)
    subtotal = _decimal(_physical_cell(subtotal_item, "H")) if subtotal_item else None
    goods_total = _sum_field(rows, "goods_amount")
    subtotal_difference = (
        subtotal - goods_total
        if subtotal is not None
        else None
    )
    return {
        "table_title": "TOYS (6月) - goods detail",
        "source_rows": list(P6_GOODS_DETAIL_ROWS),
        "rows": rows,
        "goods_amount_sum": _money(goods_total),
        "subtotal_row": P6_GOODS_SUBTOTAL_ROW,
        "subtotal_source_cell": f"Sheet2!H{P6_GOODS_SUBTOTAL_ROW}",
        "subtotal_amount": _money(subtotal),
        "subtotal_difference": _money(subtotal_difference),
        "subtotal_exact_match": (
            subtotal_difference is not None
            and abs(subtotal_difference) <= Decimal("0.000001")
        ),
        "freight_total_cells_present": any(row.get("freight_total") is not None for row in rows),
        "classification": "REFERENCE_ONLY",
        "opening_effect": 0.0,
        "reason": (
            "H is the goods-value/THANH TIEN field; H213:H219 sums exactly to "
            "H224=16,929.56, and no row-level freight-total cell exists."
        ),
        "known": [
            "The operational detail belongs to SALE Thanh in the source SALE column.",
            "The lines are shipment/goods detail, not a proven A Bo payable freight event.",
        ],
        "unknown": [
            "No A Bo financial leg is established by these rows.",
        ],
    }


def _freight_row(item: Mapping[str, Any]) -> dict[str, Any]:
    component_columns = {column: _money(_decimal(_physical_cell(item, column))) for column in "FGHIJKL"}
    return {
        **_source_row_evidence(item),
        "description": _physical_cell(item, "D"),
        "vehicle": _physical_cell(item, "E"),
        "freight_components": component_columns,
        "freight_total": _money(_decimal(_physical_cell(item, "M"))),
        "sale": _physical_cell(item, "N"),
        "currency": "UNKNOWN",
        "direction": "UNKNOWN",
        "source_total_cell": f"Sheet2!M{_row(item)}",
        "sale_cell": f"Sheet2!N{_row(item)}",
    }


def _freight_reconstruction(items_by_row: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    rows = [
        _freight_row(items_by_row[row])
        for row in P6_FREIGHT_ROWS
        if row in items_by_row
    ]
    subtotal_item = items_by_row.get(P6_FREIGHT_SUBTOTAL_ROW)
    cumulative_item = items_by_row.get(P6_FREIGHT_CUMULATIVE_ROW)
    subtotal = _decimal(_physical_cell(subtotal_item, "M")) if subtotal_item else None
    cumulative = _decimal(_physical_cell(cumulative_item, "M")) if cumulative_item else None
    row_total = _sum_field(rows, "freight_total")
    return {
        "table_title": "(TOYS-THANH) 2026-6 freight",
        "source_rows": list(P6_FREIGHT_ROWS),
        "rows": rows,
        "row_total_sum": _money(row_total),
        "subtotal_row": P6_FREIGHT_SUBTOTAL_ROW,
        "subtotal_source_cell": f"Sheet2!M{P6_FREIGHT_SUBTOTAL_ROW}",
        "subtotal_amount": _money(subtotal),
        "subtotal_exact_match": subtotal == row_total,
        "cumulative_summary_row": P6_FREIGHT_CUMULATIVE_ROW,
        "cumulative_summary_amount": _money(cumulative),
        "currency": "UNKNOWN",
        "direction": "UNKNOWN",
        "ownership": "SALE Thanh (explicit source SALE field)",
        "classification": "POST_BASE_REVIEW_REQUIRED",
        "known": [
            "M229=5,610 and M230=1,450 are row-level freight totals.",
            "M229+M230=M235=7,060; M235 is a subtotal, not another event.",
            "N229 and N230 explicitly say Thanh.",
        ],
        "unknown": [
            "The workbook does not state the currency for this table.",
            "The workbook does not establish that A Bo paid/chuyen ho this amount for Thanh.",
        ],
    }


def _shipment_cost_provenance() -> dict[str, Any]:
    return {
        "expected_amount": _money(P6_SHIPMENT_COST_EXPECTATION),
        "status": "NOT_FOUND_AFTER_BOUNDED_SOURCE_SCAN",
        "exact_source_cells": [],
        "exact_source_match": False,
        "formula_or_cached_formula_evidence": False,
        "numeric_nearby_summary_cells": [
            {"source_cell": "Sheet2!C89", "amount": 458340.0},
            {"source_cell": "Sheet2!C92", "amount": 457669.0},
            {"source_cell": "Sheet2!L164", "amount": 505228.63},
            {"source_cell": "Sheet2!L175", "amount": 512907.23},
            {"source_cell": "Sheet2!J184", "amount": 520872.23},
            {"source_cell": "Sheet2!H225", "amount": 537801.79},
            {"source_cell": "Sheet2!M236", "amount": 544861.79},
            {"source_cell": "Sheet2!M238", "amount": 415761.0},
        ],
        "conclusion": (
            "No workbook cell or unique source-component combination proves "
            "418,060.79 or its as-of date. The historical amount remains a "
            "reconciliation checkpoint, not an inferred event."
        ),
        "material_difference": True,
    }


def _residual_audit() -> dict[str, Any]:
    return {
        "staging_source_row": 96,
        "physical_source_cells": ["Sheet2!C97", "Sheet2!D97", "Sheet2!E97", "Sheet2!H97", "Sheet2!J97"],
        "source_amount_cny": _money(P6_RESIDUAL_SOURCE_AMOUNT),
        "adjacent_conversion_value_cny": _money(P6_RESIDUAL_ADJACENT_AMOUNT),
        "comparison_checkpoint_cny": _money(P6_RESIDUAL_CHECKPOINT_AMOUNT),
        "checkpoint_exact_source_match": False,
        "source_difference_from_1572": _money(P6_RESIDUAL_CHECKPOINT_AMOUNT - P6_RESIDUAL_SOURCE_AMOUNT),
        "source_difference_from_adjacent_conversion": _money(
            P6_RESIDUAL_CHECKPOINT_AMOUNT - P6_RESIDUAL_ADJACENT_AMOUNT
        ),
        "review_status": "REVIEW_REQUIRED",
        "opening_effect": 0.0,
        "conclusion": (
            "1,578.5474 is not a source amount in the workbook and no deterministic "
            "formula links it to row 96. Keep row 96 excluded; do not change the opening."
        ),
    }


def _temporal_boundary() -> dict[str, Any]:
    return {
        "last_event_embedded_in_base": {
            "date": "2026-05-28",
            "source": "C198 / Sheet2!C200",
            "meaning": "latest physically dated received-group source component in the verified base lineage",
        },
        "first_event_not_embedded_in_base": {
            "date": "2026-05-29",
            "source": "Sheet2!A201:E205 transfer/conversion group",
            "meaning": "first source-dated group after the received-group boundary; financial effect remains unresolved",
        },
        "proposed_opening_as_of_date": "2026-05-28",
        "confidence": "LOW",
        "confidence_reason": (
            "The source-date boundary for the received group is clear, but the "
            "418,060.79 shipment-cost checkpoint has no provable source cell/date."
        ),
        "alternatives_rejected": [
            "2026-05-29 is the first post-base event date, not the proposed opening as-of date.",
            "2026-06-23 has no source evidence as the opening boundary; the latest investigated freight row is 2026-06-22.",
        ],
    }


def _opening_scenarios() -> dict[str, Any]:
    base = P6_BASE_OPENING
    transfer_d = P6_TRANSFER_ON_BEHALF_TOTAL
    transfer_c = P6_TRANSFER_CONVERTED_TOTAL
    freight = P6_FREIGHT_SUBTOTAL
    return {
        "currency": "CNY only; no VND/USD conversion is performed",
        "base": {
            "label": "Current draft; unresolved P6 groups excluded",
            "amount": _money(base),
            "increment": 0.0,
            "status": "CURRENT_PROVISIONAL",
        },
        "freight_229_230_if_owner_confirms_cny_paid_on_behalf": {
            "label": "Add 7,060 once",
            "amount": _money(base + freight),
            "increment": _money(freight),
            "status": "ILLUSTRATIVE_ONLY",
        },
        "transfer_201_205_if_d_is_confirmed_opening_leg": {
            "label": "Add D chuyen ho total 392,790 once",
            "amount": _money(base + transfer_d),
            "increment": _money(transfer_d),
            "status": "ILLUSTRATIVE_ONLY",
        },
        "transfer_201_205_if_c_is_confirmed_opening_leg": {
            "label": "Add C Hach ra tien te total 392,796.30579784507 once",
            "amount": _money(base + transfer_c),
            "increment": _money(transfer_c),
            "status": "ILLUSTRATIVE_ONLY",
        },
        "both_using_d_leg": {
            "label": "Both unresolved groups confirmed; D leg selected",
            "amount": _money(base + transfer_d + freight),
            "increment": _money(transfer_d + freight),
            "status": "ILLUSTRATIVE_ONLY",
        },
        "both_using_c_leg": {
            "label": "Both unresolved groups confirmed; C leg selected",
            "amount": _money(base + transfer_c + freight),
            "increment": _money(transfer_c + freight),
            "status": "ILLUSTRATIVE_ONLY",
        },
        "guard": "These scenarios are not opening publication and do not convert currencies or add checkpoints.",
    }


def _beginner_owner_pack(
    transfer: Mapping[str, Any],
    freight: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "decision_count": 2,
        "only_genuine_unresolved_items": True,
        "decisions": [
            {
                "decision_id": "LOG-C06-P6-201-205",
                "title": "Bảng chuyển tiền/đổi tiền ngày 29–30/05",
                "source_rows": list(P6_TRANSFER_ROWS),
                "observed_amounts": transfer.get("totals"),
                "simple_question": (
                    "Nhóm này có thực sự là tiền giữa A Bò và Thành không? Nếu có, "
                    "Owner xác nhận dùng cột C (quy đổi) hay cột D (chuyển hộ)."
                ),
                "yes_effect": "Chỉ sau khi xác nhận: đưa đúng một cột, đúng một chiều, vào CNY opening; không cộng cả C và D.",
                "no_effect": "Không đưa nhóm này vào opening; giữ lại như bảng quy đổi/tham chiếu.",
                "required_fields": ["business_relationship", "opening_leg_column", "direction", "currency"],
                "status": "OWNER_REQUIRED",
            },
            {
                "decision_id": "LOG-C06-P6-229-230",
                "title": "Cước nhóm Thành ngày 10/06 và 22/06",
                "source_rows": list(P6_FREIGHT_ROWS),
                "subtotal": freight.get("subtotal_amount"),
                "source_cells": ["Sheet2!M229", "Sheet2!M230", "Sheet2!M235", "Sheet2!N229", "Sheet2!N230"],
                "simple_question": (
                    "Tổng cước 7.060 này có phải A Bò đã chi/chuyển hộ cho Thành không, "
                    "và khoản này là tiền gì?"
                ),
                "yes_effect": "Sau khi xác nhận tiền tệ và chiều tiền: thêm 7.060 đúng một lần nếu là CNY A Bò chi hộ.",
                "no_effect": "Không thêm vào opening; giữ nhóm là cước/operational reference.",
                "required_fields": ["currency", "a_bo_paid_on_behalf", "direction", "shipment_allocation_optional"],
                "status": "OWNER_REQUIRED",
            },
        ],
        "cutover_lock": "DRAFT / NOT_APPROVED / NOT_LIVE",
    }


def build_p6_reconciliation(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the P6 source reconstruction and minimum Owner question pack."""

    rows = [dict(item) for item in items]
    items_by_row = {_row(item): item for item in rows}
    transfer = _transfer_reconstruction(items_by_row)
    goods = _goods_reconstruction(items_by_row)
    freight = _freight_reconstruction(items_by_row)
    source_hash_known = P6_SOURCE_HASH in {
        str(item.get("source_file_hash") or "").lower() for item in rows
    }
    return {
        "version": P6_RECONCILIATION_VERSION,
        "source_hash": P6_SOURCE_HASH,
        "source_range": P6_SOURCE_RANGE,
        "source_hash_known": source_hash_known,
        "transfer_201_205": transfer,
        "goods_213_219": goods,
        "freight_229_230": freight,
        "shipment_cost_418060_79": _shipment_cost_provenance(),
        "residual_1572_vs_1578_5474": _residual_audit(),
        "temporal_boundary": _temporal_boundary(),
        "opening_scenarios": _opening_scenarios(),
        "beginner_owner_decision_pack": _beginner_owner_pack(transfer, freight),
        "double_count_guards": [
            "Rows 213–219 are goods detail; H224 is their subtotal and is not an opening event.",
            "Rows 229–230 are the only row-level freight amounts; M235=7,060 is a subtotal and M236 is cumulative summary.",
            "For rows 201–205, C and D are different columns/legs; never add both without an Owner-selected meaning.",
            "418,060.79 remains a checkpoint expectation; no source-cell event is created.",
            "1,572 remains excluded from opening; 1,578.5474 is not a source event.",
        ],
        "canonical_mutation_oracle": {
            "canonical_writes": 0,
            "opening_published": False,
            "staging_only": True,
        },
    }


def is_verified_goods_detail_reference(item: Mapping[str, Any]) -> bool:
    """Return whether a staged row is the verified 213–219 goods detail."""

    return (
        _row(item) in P6_GOODS_DETAIL_ROWS
        and str(item.get("source_file_hash") or "").lower() == P6_SOURCE_HASH
        and str(item.get("review_status") or "") == "NOT_APPLICABLE"
        and _physical_cell(item, "N") not in (None, "")
        and _physical_cell(item, "M") in (None, "")
        and _physical_cell(item, "H") is not None
    )


__all__ = [
    "P6_BASE_OPENING",
    "P6_FREIGHT_ROWS",
    "P6_FREIGHT_SUBTOTAL",
    "P6_GOODS_DETAIL_ROWS",
    "P6_GOODS_SUBTOTAL",
    "P6_RECONCILIATION_VERSION",
    "P6_SOURCE_HASH",
    "P6_TRANSFER_ROWS",
    "build_p6_reconciliation",
    "is_verified_goods_detail_reference",
]
