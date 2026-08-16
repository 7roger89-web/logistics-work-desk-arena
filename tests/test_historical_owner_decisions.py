"""LOG-C06 Owner-decision batch, lineage, and staging-only oracle tests."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from core.historical_opening import build_cutover_draft
from core.historical_owner_decisions import apply_owner_decisions
from core.historical_owner_reconciliation import (
    CHECKPOINT_COMPONENT_ROWS,
    RECEIVED_GROUP_ROWS,
    build_owner_reconciliation,
)
from core.historical_review_analysis import build_review_analysis
from core.historical_staging import stage_workbook
from core.historical_staging_store import (
    REVIEW_ACTIONS_COLLECTION,
    STAGING_COLLECTION,
    ensure_staging_indexes,
    load_staging_items,
    persist_staging_batch,
)


SOURCE = Path(r"D:\Copy of TOYS-2025 - Copy.xls")


class _Result:
    def __init__(self, matched_count: int = 0):
        self.matched_count = matched_count


class _Collection:
    def __init__(self):
        self.documents: list[dict] = []

    @staticmethod
    def _matches(document: dict, query: dict) -> bool:
        return all(document.get(key) == value for key, value in query.items())

    def create_index(self, *args, **kwargs):
        return kwargs.get("name")

    def find_one(self, query: dict):
        for document in self.documents:
            if self._matches(document, query):
                return copy.deepcopy(document)
        return None

    def find(self, query: dict):
        return [copy.deepcopy(document) for document in self.documents if self._matches(document, query)]

    def insert_one(self, document: dict):
        self.documents.append(copy.deepcopy(document))

    def replace_one(self, query: dict, document: dict, *, upsert: bool):
        for index, current in enumerate(self.documents):
            if self._matches(current, query):
                self.documents[index] = copy.deepcopy(document)
                return _Result(1)
        if upsert:
            self.insert_one(document)
        return _Result(0)


class _Database(dict):
    def __init__(self):
        super().__init__()
        self[STAGING_COLLECTION] = _Collection()
        self[REVIEW_ACTIONS_COLLECTION] = _Collection()
        self.canonical_accesses: list[str] = []

    def __getitem__(self, name):
        if name not in {STAGING_COLLECTION, REVIEW_ACTIONS_COLLECTION}:
            self.canonical_accesses.append(name)
            raise AssertionError(f"canonical collection touched: {name}")
        return super().__getitem__(name)


class HistoricalOwnerDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.is_file():
            raise unittest.SkipTest(f"Historical source workbook is unavailable: {SOURCE}")
        cls.batch = stage_workbook(SOURCE, imported_at="2026-08-15T00:00:00+00:00")

    def setUp(self):
        self.db = _Database()
        ensure_staging_indexes(self.db)
        persist_staging_batch(self.db, self.batch)

    def test_owner_batch_applies_confirmed_clusters_and_keeps_row_1572_review(self):
        before = {
            item["source_item_id"]: {
                "raw_values": copy.deepcopy(item.get("raw_values")),
                "raw_text": item.get("raw_text"),
                "raw_amount": item.get("raw_amount"),
                "raw_sale": item.get("raw_sale"),
            }
            for item in load_staging_items(self.db)
        }
        result = apply_owner_decisions(
            self.db,
            source_file_hash=self.batch["source_file_hash"],
            acted_at="2026-08-15T03:00:00+00:00",
        )
        self.assertEqual(result["applied_count"], 24)
        self.assertEqual(result["idempotent_count"], 0)
        self.assertEqual(result["canonical_writes"], 0)
        self.assertEqual(result["cutover_status"], "DRAFT")
        self.assertEqual(result["approval_status"], "NOT_APPROVED")
        self.assertEqual(result["live_status"], "NOT_LIVE")
        self.assertEqual(result["status_counts"]["CONFIRMED"], 20)
        self.assertEqual(result["status_counts"]["REVIEW_REQUIRED"], 170)

        items = load_staging_items(self.db, source_file_hash=self.batch["source_file_hash"])
        by_row = {item["source_row"]: item for item in items}
        self.assertEqual(by_row[96]["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(by_row[96]["proposal"]["event_type"], "paid_on_behalf")
        self.assertEqual(by_row[16]["review_status"], "CONFIRMED")
        self.assertEqual(by_row[16]["proposal"]["opening_inclusion"], "embedded_in_snapshot")
        self.assertFalse(by_row[16]["proposal"]["opening_lineage"]["reapply_to_opening"])
        self.assertEqual(by_row[99]["proposal"]["event_type"], "paid_on_behalf")
        self.assertEqual(len(by_row[99]["proposal"]["money_legs"]), 2)
        self.assertEqual(by_row[129]["proposal"]["event_type"], "checkpoint_summary")
        self.assertEqual(
            [by_row[row]["source_item_id"] for row in CHECKPOINT_COMPONENT_ROWS],
            by_row[129]["proposal"]["checkpoint_component_ids"],
        )
        self.assertEqual(by_row[86]["review_status"], "REVIEW_REQUIRED")
        self.assertAlmostEqual(by_row[86]["proposal"]["amount"], 99824.43, places=9)
        self.assertEqual(by_row[86]["proposal"]["amount_source_cell"], "E86")
        self.assertEqual(by_row[86]["proposal"]["technical_lineage_status"], "corrected_parser_amount_source")
        self.assertEqual(by_row[190]["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(by_row[197]["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(by_row[198]["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(by_row[192]["review_status"], "CONFIRMED")
        self.assertEqual(by_row[199]["review_status"], "CONFIRMED")
        self.assertEqual(by_row[200]["review_status"], "CONFIRMED")

        for item in items:
            previous = before[item["source_item_id"]]
            self.assertEqual(item.get("raw_values"), previous["raw_values"])
            self.assertEqual(item.get("raw_text"), previous["raw_text"])
            self.assertEqual(item.get("raw_amount"), previous["raw_amount"])
            self.assertEqual(item.get("raw_sale"), previous["raw_sale"])
        self.assertEqual(self.db.canonical_accesses, [])

    def test_owner_batch_is_idempotent_and_reconciliation_exposes_difference(self):
        first = apply_owner_decisions(
            self.db,
            source_file_hash=self.batch["source_file_hash"],
            acted_at="2026-08-15T03:00:00+00:00",
        )
        second = apply_owner_decisions(
            self.db,
            source_file_hash=self.batch["source_file_hash"],
            acted_at="2026-08-15T04:00:00+00:00",
        )
        self.assertEqual(second["applied_count"], 0)
        self.assertEqual(second["idempotent_count"], 24)
        self.assertEqual(len(self.db[REVIEW_ACTIONS_COLLECTION].documents), 24)

        reconciliation = second["reconciliation"]
        self.assertEqual(reconciliation["snapshot_credit_lineage"]["status"], "EMBEDDED_IN_SNAPSHOT")
        self.assertEqual(reconciliation["checkpoint_134973"]["status"], "EXACT_MATCH")
        self.assertEqual(reconciliation["paid_on_behalf_group"]["status"], "EXACT_MATCH")
        self.assertEqual(reconciliation["paid_on_behalf_group"]["component_amount"], 159998.0)
        received = reconciliation["received_on_behalf_group"]
        self.assertEqual(received["component_source_rows"], list(RECEIVED_GROUP_ROWS))
        self.assertAlmostEqual(received["component_amount"], 416482.2426005565, places=9)
        self.assertAlmostEqual(received["difference"], 0.0, places=9)
        self.assertEqual(received["checkpoint_status"], "RECONCILED")
        self.assertEqual(received["source_reconciliation"]["status"], "RECONCILED")
        self.assertAlmostEqual(received["source_reconciliation"]["delta_sum"], 0.0, places=9)
        self.assertEqual(
            [row["source_oracle"] for row in received["source_reconciliation"]["rows"]],
            ["C102", "C109", "C115", "C190", "C197", "C198"],
        )
        self.assertEqual(
            [row["source_cell"] for row in received["source_reconciliation"]["rows"]],
            ["Sheet2!C102", "Sheet2!C109", "Sheet2!C115", "Sheet2!C192", "Sheet2!C199", "Sheet2!C200"],
        )
        self.assertEqual(reconciliation["old_m89_reconciliation"]["status"], "SUPERSEDED_CHECKPOINT")
        self.assertEqual(reconciliation["historical_position_checkpoint"]["expected_position"], 161576.5473994435)
        self.assertAlmostEqual(
            reconciliation["historical_position_checkpoint"]["reconstructed_position_using_source_received"],
            161576.5473994435,
            places=9,
        )
        self.assertEqual(reconciliation["material_difference_count"], 0)
        self.assertEqual(first["canonical_writes"], 0)
        analysis = build_review_analysis(load_staging_items(self.db))
        self.assertEqual(analysis["checkpoint_reconstruction"]["status"], "EXACT_MATCH_CANDIDATE")
        self.assertEqual(analysis["checkpoint_reconstruction"]["candidate_rows"], list(CHECKPOINT_COMPONENT_ROWS))

    def test_opening_draft_uses_confirmed_buckets_and_excludes_snapshot_summary(self):
        apply_owner_decisions(
            self.db,
            source_file_hash=self.batch["source_file_hash"],
            acted_at="2026-08-15T03:00:00+00:00",
        )
        items = load_staging_items(self.db, source_file_hash=self.batch["source_file_hash"])
        draft = build_cutover_draft(
            items,
            proposed_cutover_date="2026-08-15",
            generated_by="owner-review-test",
            generated_at="2026-08-15T03:05:00+00:00",
        )
        cny = draft["position_by_currency"]["CNY"]["buckets"]
        self.assertEqual(cny["paid_on_behalf_settled"]["amount"], 159998.0)
        self.assertAlmostEqual(cny["received_on_behalf_available"]["amount"], 416482.2426005565, places=9)
        self.assertEqual(draft["position_by_currency"]["CNY"]["buckets"]["held_credit"]["amount"], 0.0)
        excluded = {
            row["source_item_id"]: row["reason"]
            for row in draft["exclusions"]
        }
        by_row = {item["source_row"]: item for item in items}
        self.assertEqual(excluded[by_row[16]["source_item_id"]], "EMBEDDED_IN_SNAPSHOT")
        self.assertEqual(excluded[by_row[129]["source_item_id"]], "CHECKPOINT_NOT_COMPONENT")
        self.assertNotIn("OWNER_CHECKPOINT_DIFFERENCE", draft["readiness_reasons"])
        self.assertEqual(draft["canonical_mutations"], 0)
        self.assertEqual(draft["approval_status"], "NOT_APPROVED")
        self.assertEqual(draft["live_status"], "NOT_LIVE")
        self.assertEqual(draft["opening_lineage"]["post_base_events"], [])

    def test_reconciliation_is_pure_for_staged_items(self):
        items = load_staging_items(self.db)
        before = copy.deepcopy(items)
        result = build_owner_reconciliation(items)
        self.assertEqual(items, before)
        self.assertEqual(result["canonical_mutations"], 0)
        self.assertEqual(result["cutover_lock"], "DRAFT / NOT_APPROVED / NOT_LIVE")


if __name__ == "__main__":
    unittest.main()
