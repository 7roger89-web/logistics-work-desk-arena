"""LOG-C05 snapshot/version and metadata-only write oracle tests."""

from __future__ import annotations

from copy import deepcopy
import unittest

from core.debit_draft import build_debit_draft, build_manager_report
from core.debit_snapshot import (
    DEBIT_STATUS_SUPERSEDED,
    SNAPSHOT_COLLECTION,
    DebitSnapshotConflictError,
    build_debit_snapshot_document,
    get_debit_draft_snapshot,
    list_debit_draft_snapshots,
    next_debit_snapshot_version,
    save_debit_draft_snapshot,
)
from core.financial_ledger import project_partner_financial_position
from tests.test_financial_ledger import _MemoryDatabase
from tests.test_reconciliation_desk import ABO, _fixture_history


class LogC05SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        self.position = project_partner_financial_position(
            ABO,
            obligations,
            transactions,
            allocations,
            internal_sale_owner="Thành",
        )
        self.draft = build_debit_draft(self.position, period_start="2026-08-01", period_end="2026-08-31")
        self.report = build_manager_report(self.position, period_start="2026-08-01", period_end="2026-08-31")
        self.db = _MemoryDatabase()
        self.db.financial_obligations.insert_one({"id": "canonical-obligation", "amount": 100})
        self.db.financial_transactions.insert_one({"id": "canonical-transaction", "amount": 50})
        self.db.financial_allocations.insert_one({"id": "canonical-allocation", "amount": 10})
        self.before_canonical = {
            name: deepcopy(self.db[name].docs)
            for name in ("financial_obligations", "financial_transactions", "financial_allocations")
        }

    def test_snapshot_shape_contains_source_ids_state_totals_and_hash(self) -> None:
        snapshot = build_debit_snapshot_document(
            self.draft,
            manager_report=self.report,
            request_id="REQ-C05-V1",
            prepared_by="Thành",
            version=1,
        )
        self.assertEqual(snapshot["document_type"], "DEBIT_DRAFT_SNAPSHOT")
        self.assertEqual(snapshot["status"], "READY_FOR_REVIEW")
        self.assertEqual(snapshot["version"], 1)
        self.assertEqual(snapshot["period"], {"start": "2026-08-01", "end": "2026-08-31"})
        self.assertIn("OBL-160000", snapshot["obligation_ids"])
        self.assertIn("TX-CREDIT-24576", snapshot["transaction_ids"])
        self.assertIn("ALC-PARTIAL", snapshot["allocation_ids"])
        self.assertTrue(snapshot["correction_reversal_state"])
        self.assertIn("CNY", snapshot["totals_by_currency"])
        self.assertTrue(snapshot["content_hash"])
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["financial_effect_write_count"], 0)

    def test_retry_is_idempotent_and_conflicting_request_is_rejected(self) -> None:
        first = save_debit_draft_snapshot(
            self.db,
            self.draft,
            manager_report=self.report,
            request_id="REQ-C05-RETRY",
            prepared_by="Thành",
        )
        retry = save_debit_draft_snapshot(
            self.db,
            self.draft,
            manager_report=self.report,
            request_id="REQ-C05-RETRY",
            prepared_by="other-user",
        )
        self.assertTrue(first["created"])
        self.assertTrue(retry["reused"])
        self.assertEqual(first["snapshot"]["snapshot_id"], retry["snapshot"]["snapshot_id"])
        self.assertEqual(len(self.db[SNAPSHOT_COLLECTION].docs), 1)

        conflicting = deepcopy(self.draft)
        conflicting["by_currency"]["CNY"]["debit_ready_amount"] += 1
        with self.assertRaises(DebitSnapshotConflictError):
            save_debit_draft_snapshot(
                self.db,
                conflicting,
                manager_report=self.report,
                request_id="REQ-C05-RETRY",
            )

    def test_v2_preserves_v1_and_marks_only_metadata_superseded(self) -> None:
        first = save_debit_draft_snapshot(
            self.db,
            self.draft,
            manager_report=self.report,
            request_id="REQ-C05-V1",
            version=1,
        )
        v1 = deepcopy(first["snapshot"])
        changed = deepcopy(self.draft)
        changed["by_currency"]["CNY"]["debit_ready_amount"] += 500
        second = save_debit_draft_snapshot(
            self.db,
            changed,
            manager_report=self.report,
            request_id="REQ-C05-V2",
            version=2,
            supersedes_snapshot_id=v1["snapshot_id"],
        )
        v1_readback = get_debit_draft_snapshot(self.db, snapshot_id=v1["snapshot_id"])
        v2_readback = get_debit_draft_snapshot(self.db, request_id="REQ-C05-V2")
        self.assertEqual(v1_readback["version"], 1)
        self.assertEqual(v1_readback["debit_draft"], v1["debit_draft"])
        self.assertEqual(v1_readback["status"], DEBIT_STATUS_SUPERSEDED)
        self.assertEqual(v1_readback["superseded_by_snapshot_id"], second["snapshot"]["snapshot_id"])
        self.assertEqual(v2_readback["version"], 2)
        self.assertEqual(v2_readback["supersedes_snapshot_id"], v1["snapshot_id"])
        self.assertEqual(next_debit_snapshot_version(self.db, party_key=self.draft["party_key"], sale_owner=self.draft["internal_sale_owner"], period=self.draft["period"]), 3)
        self.assertEqual([row["version"] for row in list_debit_draft_snapshots(self.db, party_key=self.draft["party_key"], sale_owner=self.draft["internal_sale_owner"], period=self.draft["period"])], [2, 1])

    def test_snapshot_write_does_not_change_canonical_collections_or_position(self) -> None:
        position_before = deepcopy(self.position)
        result = save_debit_draft_snapshot(
            self.db,
            self.draft,
            manager_report=self.report,
            request_id="REQ-C05-ORACLE",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(self.position, position_before)
        for name, before_docs in self.before_canonical.items():
            self.assertEqual(self.db[name].docs, before_docs)
        self.assertEqual(set(self.db.collections), set(self.before_canonical) | {SNAPSHOT_COLLECTION})
        self.assertEqual(result["snapshot"]["financial_effect_write_count"], 0)


if __name__ == "__main__":
    unittest.main()
