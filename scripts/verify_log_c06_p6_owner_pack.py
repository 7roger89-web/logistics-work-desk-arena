"""Independent LOG-C06 P6 source/blocker and Owner-pack verification."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import xlrd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_db
from core.historical_cutover_sufficiency import (
    VERIFIED_BASE_AMOUNT,
    VERIFIED_SOURCE_HASH,
    build_cutover_sufficiency,
)
from core.historical_opening import build_cutover_draft
from core.historical_staging import source_file_hash
from core.historical_staging_store import list_review_actions, load_staging_items


SOURCE = Path(r"D:\Copy of TOYS-2025 - Copy.xls")
EXPECTED_CATEGORY_COUNTS = {
    "EMBEDDED_IN_VERIFIED_BASE": 19,
    "POST_BASE_CONFIRMED": 0,
    "POST_BASE_REVIEW_REQUIRED": 7,
    "REFERENCE_ONLY": 81,
    "NOT_APPLICABLE": 122,
    "UNRESOLVED_NON_MATERIAL": 60,
    "UNRESOLVED_MATERIAL": 0,
}


def _workbook_scan(path: Path) -> dict[str, object]:
    workbook = xlrd.open_workbook(path, on_demand=True, formatting_info=False)
    exact_418: list[str] = []
    exact_1578: list[str] = []
    nearby: list[dict[str, object]] = []
    for sheet in workbook.sheets():
        for row in range(sheet.nrows):
            for column in range(sheet.ncols):
                value = sheet.cell_value(row, column)
                cell = f"{sheet.name}!{chr(65 + column)}{row + 1}" if column < 26 else f"{sheet.name}!{row + 1}:{column + 1}"
                if isinstance(value, (int, float)):
                    decimal_value = Decimal(str(value))
                    if decimal_value == Decimal("418060.79"):
                        exact_418.append(cell)
                    if abs(decimal_value - Decimal("1578.5474")) <= Decimal("0.000001"):
                        exact_1578.append(cell)
                    if Decimal("400000") <= decimal_value <= Decimal("600000"):
                        nearby.append({"source_cell": cell, "amount": float(decimal_value)})
    currency_text_hits: list[str] = []
    sheet2 = workbook.sheet_by_name("Sheet2")
    for row in range(227, min(236, sheet2.nrows)):
        for column in range(sheet2.ncols):
            value = sheet2.cell_value(row, column)
            if isinstance(value, str) and any(
                marker in value.casefold()
                for marker in ("cny", "rmb", "yuan", "currency", "元")
            ):
                currency_text_hits.append(f"Sheet2!{chr(65 + column)}{row + 1}")
    return {
        "exact_418060_79_cells": exact_418,
        "exact_1578_5474_cells": exact_1578,
        "nearby_numeric_cells": nearby,
        "june_freight_currency_text_hits": currency_text_hits,
    }


def main() -> int:
    db = get_db()
    items = load_staging_items(db, source_file_hash=VERIFIED_SOURCE_HASH)
    result = build_cutover_sufficiency(items)
    p6 = result["p6_reconciliation"]
    scan = _workbook_scan(SOURCE)
    draft = build_cutover_draft(
        items,
        proposed_cutover_date="2026-08-15",
        generated_by="log-c06-p6-owner-pack-verifier",
        generated_at="2026-08-15T00:00:00+00:00",
    )

    assert source_file_hash(SOURCE) == VERIFIED_SOURCE_HASH
    assert len(items) == 289
    assert result["category_counts"] == EXPECTED_CATEGORY_COUNTS
    assert result["unresolved_material_count"] == 0
    assert result["opening_material_blocker_count"] == 7
    assert len(result["post_base_review_required_events"]) == 7
    assert result["candidate_opening"]["amount"] == float(VERIFIED_BASE_AMOUNT)
    assert result["readiness"] == "NOT_READY"
    assert result["readiness_reasons"] == [
        "OPENING_CURRENCY_UNKNOWN",
        "POST_BASE_REVIEW_REQUIRED",
        "TEMPORAL_SCOPE_UNCERTAIN",
    ]

    category_by_row = {row["source_row"]: row["category"] for row in result["items"]}
    assert all(category_by_row[row] == "REFERENCE_ONLY" for row in range(213, 220))
    assert all(category_by_row[row] == "POST_BASE_REVIEW_REQUIRED" for row in (201, 202, 203, 204, 205, 229, 230))

    transfer = p6["transfer_201_205"]
    assert transfer["totals"]["hach_ra_tien_te_cny"] == 392796.30579784507
    assert transfer["totals"]["chuyen_ho_cny"] == 392790.0
    assert transfer["totals"]["vnd_input"] == 1531120000.0
    assert transfer["totals"]["column_difference_cny"] == 6.30579784505476
    assert len(transfer["groups"]) == 3

    goods = p6["goods_213_219"]
    assert goods["goods_amount_sum"] == 16929.56
    assert goods["subtotal_amount"] == 16929.56
    assert goods["subtotal_exact_match"] is True
    assert goods["freight_total_cells_present"] is False

    freight = p6["freight_229_230"]
    assert freight["row_total_sum"] == 7060.0
    assert freight["subtotal_amount"] == 7060.0
    assert freight["subtotal_exact_match"] is True
    assert freight["currency"] == "UNKNOWN"
    assert freight["direction"] == "UNKNOWN"

    assert p6["beginner_owner_decision_pack"]["decision_count"] == 2
    assert p6["shipment_cost_418060_79"]["exact_source_cells"] == []
    assert scan["exact_418060_79_cells"] == []
    assert scan["exact_1578_5474_cells"] == []
    assert scan["june_freight_currency_text_hits"] == []
    assert p6["residual_1572_vs_1578_5474"]["opening_effect"] == 0.0

    boundary = p6["temporal_boundary"]
    assert boundary["last_event_embedded_in_base"]["date"] == "2026-05-28"
    assert boundary["first_event_not_embedded_in_base"]["date"] == "2026-05-29"
    assert boundary["proposed_opening_as_of_date"] == "2026-05-28"
    assert boundary["confidence"] == "LOW"

    assert draft["opening_sufficiency"]["category_counts"] == EXPECTED_CATEGORY_COUNTS
    assert draft["cutover_sufficiency_status"] == "NOT_READY"
    assert draft["canonical_mutations"] == 0
    assert draft["approval_status"] == "NOT_APPROVED"
    assert draft["live_status"] == "NOT_LIVE"

    actions = list_review_actions(db)
    assert len(actions) == 27
    assert all(record.get("canonical_writes") == 0 for record in actions)

    summary = {
        "source_hash_unchanged": True,
        "staging_items": len(items),
        "category_counts": result["category_counts"],
        "review_status_counts": result["review_status_counts"],
        "review_classification_counts": result["review_classification_counts"],
        "opening_material_blocker_count": result["opening_material_blocker_count"],
        "owner_decision_count": p6["beginner_owner_decision_pack"]["decision_count"],
        "transfer_201_205": transfer["totals"],
        "goods_213_219": {
            "goods_amount_sum": goods["goods_amount_sum"],
            "subtotal_amount": goods["subtotal_amount"],
            "subtotal_exact_match": goods["subtotal_exact_match"],
        },
        "freight_229_230": {
            "row_total_sum": freight["row_total_sum"],
            "subtotal_amount": freight["subtotal_amount"],
            "subtotal_exact_match": freight["subtotal_exact_match"],
            "currency": freight["currency"],
            "direction": freight["direction"],
        },
        "shipment_cost_provenance": p6["shipment_cost_418060_79"],
        "residual_audit": p6["residual_1572_vs_1578_5474"],
        "temporal_boundary": boundary,
        "opening_scenarios": p6["opening_scenarios"],
        "source_scan": scan,
        "candidate_opening": result["candidate_opening"],
        "readiness": result["readiness"],
        "readiness_reasons": result["readiness_reasons"],
        "audit_records": len(actions),
        "canonical_writes": 0,
        "opening_published": False,
        "cutover": "DRAFT / NOT_APPROVED / NOT_LIVE",
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
