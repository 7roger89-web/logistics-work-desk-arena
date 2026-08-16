"""Independent LOG-C06 P4 staging/reconciliation integrity sweep."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_db
from core.historical_opening import build_cutover_draft
from core.historical_owner_reconciliation import build_owner_reconciliation
from core.historical_staging import source_file_hash
from core.historical_staging_store import list_review_actions, load_staging_items


SOURCE = Path(r"D:\Copy of TOYS-2025 - Copy.xls")
SOURCE_HASH = "857db72b86220a4af302c0de6900710c49f44b2223c458c009748dd767840b70"


def main() -> int:
    db = get_db()
    items = load_staging_items(db, source_file_hash=SOURCE_HASH)
    by_row = {int(item["source_row"]): item for item in items}
    reconciliation = build_owner_reconciliation(items)
    received = reconciliation["received_on_behalf_group"]
    source_table = received["source_reconciliation"]
    draft = build_cutover_draft(
        items,
        proposed_cutover_date="2026-08-15",
        generated_by="log-c06-p4-integrity-sweep",
        generated_at="2026-08-15T05:20:00+00:00",
    )
    assert source_file_hash(SOURCE) == SOURCE_HASH
    assert source_table["status"] == "RECONCILED"
    assert source_table["delta_sum"] == 0.0
    assert received["component_amount"] == 416482.2426005565
    assert reconciliation["paid_on_behalf_group"]["component_amount"] == 159998.0
    assert reconciliation["historical_position_checkpoint"]["difference_vs_expected_position"] == 0.0
    assert by_row[16]["source_item_id"] not in draft["confirmed_source_item_ids"]
    assert by_row[129]["source_item_id"] not in draft["confirmed_source_item_ids"]
    assert by_row[86]["proposal"]["amount"] == 99824.43
    assert by_row[86]["proposal"]["technical_lineage_status"] == "corrected_parser_amount_source"
    assert by_row[86]["raw_amount"] == 7683.0
    assert all(by_row[row]["review_status"] == "REVIEW_REQUIRED" for row in (190, 197, 198))
    assert all(
        by_row[row]["proposal"].get("technical_lineage_status") == "superseded_wrong_source_alias"
        for row in (190, 197, 198)
    )
    actions = list_review_actions(db)
    assert len(actions) == 27
    assert all(record.get("canonical_writes") == 0 for record in actions)
    assert draft["canonical_mutations"] == 0
    assert draft["approval_status"] == "NOT_APPROVED"
    assert draft["live_status"] == "NOT_LIVE"
    summary = {
        "source_hash_unchanged": True,
        "received_reconciled": True,
        "received_total": received["component_amount"],
        "received_row_delta_sum": source_table["delta_sum"],
        "paid_on_behalf_total": reconciliation["paid_on_behalf_group"]["component_amount"],
        "historical_position": reconciliation["historical_position_checkpoint"]["reconstructed_position_using_source_received"],
        "audit_records": len(actions),
        "canonical_writes": 0,
        "opening_published": False,
        "cutover": "DRAFT / NOT_APPROVED / NOT_LIVE",
        "status_counts": {
            status: sum(1 for item in items if item.get("review_status") == status)
            for status in ("CONFIRMED", "REVIEW_REQUIRED", "NOT_APPLICABLE", "RAW", "REJECTED")
        },
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
