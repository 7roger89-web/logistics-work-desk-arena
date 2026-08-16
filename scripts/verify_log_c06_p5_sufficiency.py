"""Compatibility sweep for the current LOG-C06 opening-impact contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_db
from core.historical_cutover_sufficiency import (
    CATEGORIES,
    CATEGORY_MATERIAL,
    CATEGORY_POST_REVIEW,
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


def main() -> int:
    db = get_db()
    items = load_staging_items(db, source_file_hash=VERIFIED_SOURCE_HASH)
    result = build_cutover_sufficiency(items)
    draft = build_cutover_draft(
        items,
        proposed_cutover_date="2026-08-15",
        generated_by="log-c06-p5-integrity-sweep",
        generated_at="2026-08-15T00:00:00+00:00",
    )

    assert source_file_hash(SOURCE) == VERIFIED_SOURCE_HASH
    assert len(items) == 289
    assert set(result["category_counts"]) == set(CATEGORIES)
    assert sum(result["category_counts"].values()) == len(items)
    assert result["category_counts"] == EXPECTED_CATEGORY_COUNTS
    assert result["unresolved_material_count"] == 0
    assert len(result["post_base_review_required_events"]) == 7
    assert result["opening_material_blocker_count"] == 7
    assert len(result["post_base_confirmed_events"]) == 0
    assert result["supersession_graph"]["checkpoint_events_counted"] == 0
    assert result["candidate_opening"]["amount"] == float(VERIFIED_BASE_AMOUNT)
    assert result["candidate_opening"]["post_base_confirmed_increases"] == 0.0
    assert result["candidate_opening"]["post_base_confirmed_reductions"] == 0.0
    assert result["readiness"] == "NOT_READY"
    assert "TEMPORAL_SCOPE_UNCERTAIN" in result["readiness_reasons"]
    assert "POST_BASE_REVIEW_REQUIRED" in result["readiness_reasons"]
    assert "UNRESOLVED_MATERIAL_ITEMS" not in result["readiness_reasons"]
    assert draft["opening_sufficiency"]["category_counts"] == EXPECTED_CATEGORY_COUNTS
    assert draft["cutover_sufficiency_status"] == "NOT_READY"
    assert draft["canonical_mutations"] == 0
    assert draft["approval_status"] == "NOT_APPROVED"
    assert draft["live_status"] == "NOT_LIVE"

    actions = list_review_actions(db)
    assert len(actions) == 27
    assert all(record.get("canonical_writes") == 0 for record in actions)

    status_counts = {
        status: sum(1 for item in items if item.get("review_status") == status)
        for status in ("CONFIRMED", "REVIEW_REQUIRED", "NOT_APPLICABLE", "RAW", "REJECTED")
    }
    material_rows = [
        {
            "source_row": row["source_row"],
            "category": row["category"],
            "amount": row["amount"],
            "currency": row["currency"],
            "structured_sale": row["structured_sale"],
            "reason": row["reason"],
        }
        for row in result["items"]
        if row["category"] in {CATEGORY_MATERIAL, CATEGORY_POST_REVIEW}
    ]
    summary = {
        "source_hash_unchanged": True,
        "staging_items": len(items),
        "category_counts": result["category_counts"],
        "category_amounts_by_currency": result["category_amounts_by_currency"],
        "material_count": result["unresolved_material_count"],
        "opening_material_blocker_count": result["opening_material_blocker_count"],
        "post_base_review_count": len(result["post_base_review_required_events"]),
        "post_base_confirmed_count": len(result["post_base_confirmed_events"]),
        "material_rows": material_rows,
        "temporal_scope": result["temporal_scope"],
        "candidate_opening": result["candidate_opening"],
        "readiness": result["readiness"],
        "readiness_reasons": result["readiness_reasons"],
        "checkpoint_events_counted": result["supersession_graph"]["checkpoint_events_counted"],
        "status_counts": status_counts,
        "audit_records": len(actions),
        "canonical_writes": 0,
        "opening_published": False,
        "cutover": "DRAFT / NOT_APPROVED / NOT_LIVE",
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
