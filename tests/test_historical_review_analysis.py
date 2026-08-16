"""Deterministic Owner-review analysis tests for LOG-C06."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from core.historical_review_analysis import (
    GOLDEN_EXPECTED_AMOUNTS,
    READY_FOR_OWNER_CONFIRMATION,
    REVIEW_REQUIRED,
    UNKNOWN,
    build_review_analysis,
)
from core.historical_staging import stage_workbook


SOURCE = Path(r"D:\Copy of TOYS-2025 - Copy.xls")


class HistoricalReviewAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE.is_file():
            raise unittest.SkipTest(f"Historical source workbook is unavailable: {SOURCE}")
        cls.batch = stage_workbook(SOURCE, imported_at="2026-08-15T00:00:00+00:00")
        cls.items_before = copy.deepcopy(cls.batch["items"])
        cls.analysis = build_review_analysis(cls.batch["items"])

    def _row(self, source_row: int) -> dict:
        matches = [
            row
            for row in self.analysis["golden_items"]
            if row.get("source_row") == source_row
        ]
        if matches:
            return matches[0]
        matches = [
            row
            for row in self.analysis.get("_derived_items", [])
            if row.get("source_row") == source_row
        ]
        raise AssertionError(f"Missing analysis row {source_row}: {matches}")

    def test_golden_items_are_business_ready_without_confirmation(self):
        golden = {row["source_row"]: row for row in self.analysis["golden_items"]}
        self.assertEqual(set(golden), set(GOLDEN_EXPECTED_AMOUNTS))
        self.assertEqual(
            [row["source_row"] for row in self.analysis["golden_items"]],
            [16, 102, 109, 96, 99, 129],
        )
        for source_row, expected_amount in GOLDEN_EXPECTED_AMOUNTS.items():
            with self.subTest(source_row=source_row):
                row = golden[source_row]
                self.assertEqual(row["amount"], float(expected_amount))
                self.assertEqual(row["currency"], "CNY")
                self.assertIn("Sheet2!", row["source_reference"])
                self.assertIn("title", row["business"])
                self.assertIn("owner_question", row["business"])

        self.assertEqual(golden[16]["owner_review_state"], READY_FOR_OWNER_CONFIRMATION)
        self.assertEqual(golden[102]["owner_review_state"], READY_FOR_OWNER_CONFIRMATION)
        self.assertEqual(golden[109]["owner_review_state"], READY_FOR_OWNER_CONFIRMATION)
        self.assertEqual(golden[96]["owner_review_state"], REVIEW_REQUIRED)
        self.assertEqual(golden[99]["owner_review_state"], READY_FOR_OWNER_CONFIRMATION)
        self.assertEqual(golden[129]["owner_review_state"], READY_FOR_OWNER_CONFIRMATION)

    def test_checkpoint_has_unique_exact_candidate_and_never_becomes_component(self):
        checkpoint = self.analysis["checkpoint_reconstruction"]
        self.assertEqual(checkpoint["status"], "EXACT_MATCH_CANDIDATE")
        self.assertEqual(
            checkpoint["candidate_rows"],
            [103, 104, 105, 106, 107, 108, 111, 114, 116, 120, 121],
        )
        self.assertEqual(
            [component["source_row"] for component in checkpoint["candidate_components"]],
            checkpoint["candidate_rows"],
        )
        self.assertEqual(
            sum(component["amount"] for component in checkpoint["candidate_components"]),
            134973.0,
        )
        self.assertEqual(checkpoint["candidate_component_amount"], 134973.0)
        self.assertEqual(checkpoint["difference"], 0.0)
        self.assertEqual(checkpoint["exact_solution_count"], 1)
        self.assertTrue(checkpoint["checkpoint_is_not_component"])
        self.assertTrue(checkpoint["double_count_guard"]["checkpoint_id_excluded_from_components"])
        self.assertTrue(checkpoint["double_count_guard"]["checkpoint_must_not_enter_opening"])
        excluded_rows = {row["source_row"] for row in checkpoint["context_exclusion_rows"]}
        self.assertEqual(excluded_rows, {109, 115})
        self.assertNotIn(129, checkpoint["candidate_rows"])

    def test_all_review_items_have_exactly_one_cluster(self):
        expected_counts = {
            "MISSING_OR_UNCERTAIN_CURRENCY": 75,
            "CHECKPOINT_OR_SUMMARY": 27,
            "LIKELY_DUPLICATE": 4,
            "PAID_ON_BEHALF": 9,
            "MATERIAL_AMBIGUITY": 15,
            "INHERITED_DATE_ONLY": 34,
            "CUSTOMER_RECEIPT_LEG": 1,
            "RECEIVED_ON_BEHALF": 2,
            "EXPLICIT_SALE_MISSING_EVENT": 6,
            "FX_CONTEXT": 12,
        }
        clusters = {cluster["cluster_key"]: cluster for cluster in self.analysis["clusters"]}
        self.assertEqual(
            {key: cluster["count"] for key, cluster in clusters.items()},
            expected_counts,
        )
        self.assertEqual(self.analysis["review_required_count"], 185)
        self.assertEqual(self.analysis["clustered_review_count"], 185)
        self.assertEqual(sum(cluster["count"] for cluster in clusters.values()), 185)
        self.assertTrue(all(cluster["one_owner_rule"] for cluster in clusters.values() if cluster["cluster_key"] in {"CHECKPOINT_OR_SUMMARY", "FX_CONTEXT", "CUSTOMER_RECEIPT_LEG"}))

    def test_analysis_is_read_only_and_decision_pack_is_bounded(self):
        self.assertEqual(self.batch["items"], self.items_before)
        self.assertEqual(self.analysis["current_status_counts"], {
            "NOT_APPLICABLE": 60,
            "PROPOSED": 5,
            "RAW": 39,
            "REVIEW_REQUIRED": 185,
        })
        self.assertEqual(self.analysis["owner_decision_pack"]["decision_count"], 6)
        self.assertEqual(self.analysis["owner_decision_pack"]["cutover_lock"], "DRAFT / NOT_APPROVED / NOT_LIVE")
        self.assertEqual(self.analysis["safety"]["canonical_mutations"], 0)
        self.assertFalse(self.analysis["safety"]["input_items_mutated"])
        self.assertFalse(self.analysis["safety"]["review_status_mutated"])
        self.assertFalse(self.analysis["safety"]["confirmed_rows_created"])
        self.assertEqual(self.analysis["owner_review_state_counts"][UNKNOWN], 133)

    def test_module_has_no_ui_or_canonical_write_dependency(self):
        source = Path(__file__).resolve().parents[1] / "core" / "historical_review_analysis.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("import streamlit", text)
        self.assertNotIn("historical_staging_store", text)
        self.assertNotIn("financial_ledger", text)
        self.assertNotIn("get_db", text)


if __name__ == "__main__":
    unittest.main()
