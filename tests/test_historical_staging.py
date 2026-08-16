"""Golden and safety tests for LOG-C06 historical staging."""

from __future__ import annotations

import hashlib
import math
import unittest
from pathlib import Path

from core.historical_staging import (
    PARSER_VERSION,
    SALE_OWNER,
    UNKNOWN_CURRENCY,
    _proposal_status,
    _sale_proposal,
    normalize_text,
    source_file_hash,
    stage_fixture_rows,
    stage_workbook,
    summarize_staging,
)


SOURCE = Path(r"D:\Copy of TOYS-2025 - Copy.xls")
EXPECTED_SOURCE_HASH = "857db72b86220a4af302c0de6900710c49f44b2223c458c009748dd767840b70"


class HistoricalStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE.is_file():
            raise unittest.SkipTest(f"Historical source workbook is unavailable: {SOURCE}")
        cls.before_hash = source_file_hash(SOURCE)
        cls.batch = stage_workbook(SOURCE, imported_at="2026-08-15T00:00:00+00:00")

    @classmethod
    def _sheet2_row(cls, row_number: int) -> dict:
        matches = [
            item
            for item in cls.batch["items"]
            if item.get("sheet") == "Sheet2" and item.get("source_row") == row_number
        ]
        if len(matches) != 1:
            raise AssertionError(f"Expected one Sheet2 row {row_number}, got {len(matches)}")
        return matches[0]

    def test_source_provenance_and_read_only_hash(self):
        self.assertEqual(self.before_hash, EXPECTED_SOURCE_HASH)
        self.assertEqual(self.batch["source_file_hash"], EXPECTED_SOURCE_HASH)
        self.assertEqual(self.batch["parser_version"], PARSER_VERSION)
        self.assertEqual(source_file_hash(SOURCE), self.before_hash)
        self.assertGreater(self.batch["item_count"], 0)
        self.assertTrue(all(item["source_file_hash"] == EXPECTED_SOURCE_HASH for item in self.batch["items"]))

    def test_golden_historical_amounts_and_source_rows(self):
        expected = {
            16: 24576.0,
            96: 1572.0,
            99: 25025.0,
            102: 62464.0,
            109: 1687.0,
            129: 134973.0,
            192: 183549.0,
            199: 19000.0,
            200: 124485.0,
        }
        for row_number, amount in expected.items():
            with self.subTest(row=row_number):
                item = self._sheet2_row(row_number)
                self.assertEqual(item["raw_amount"], amount)
                self.assertEqual(item["proposal"]["amount"], amount)
                self.assertIn(f"!", item["source_reference"])
                self.assertEqual(item["source_file_hash"], EXPECTED_SOURCE_HASH)

    def test_row86_uses_numeric_checkpoint_cell_not_formula_reference_text(self):
        item = self._sheet2_row(86)
        self.assertAlmostEqual(item["raw_amount"], 99824.43, places=9)
        self.assertAlmostEqual(item["proposal"]["amount"], 99824.43, places=9)
        self.assertEqual(item["proposal"]["amount_source_cell"], "E86")
        self.assertEqual(item["proposal"]["amount_source_kind"], "numeric_cell")
        self.assertEqual(item["raw_values"]["D86"], "của thành = E76 + 83")
        self.assertEqual(item["raw_values"]["E86"], 99824.43000000001)

    def test_sale_thanh_is_explicit_only(self):
        explicit = self._sheet2_row(109)
        self.assertEqual(explicit["raw_sale"], "thành")
        self.assertEqual(explicit["proposal"]["internal_sale_owner"], SALE_OWNER)
        self.assertEqual(explicit["proposal"]["sale_evidence"], "explicit_sale_field")
        self.assertEqual(explicit["review_status"], "PROPOSED")

        text_only = self._sheet2_row(96)
        self.assertIsNone(text_only["proposal"]["internal_sale_owner"])
        self.assertEqual(text_only["proposal"]["candidate_internal_sale_owner"], SALE_OWNER)
        self.assertEqual(text_only["proposal"]["sale_evidence"], "free_text_only")
        self.assertEqual(text_only["review_status"], "REVIEW_REQUIRED")

    def test_other_sale_is_separated_from_thanh(self):
        other_sales = [
            item
            for item in self.batch["items"]
            if item.get("raw_amount") is not None
            and (item.get("proposal") or {}).get("sale_evidence") == "explicit_other_sale"
        ]
        self.assertGreater(len(other_sales), 0)
        self.assertTrue(all(item["review_status"] == "NOT_APPLICABLE" for item in other_sales))
        self.assertTrue(all(item["proposal"].get("internal_sale_owner") != SALE_OWNER for item in other_sales))

    def test_currency_and_fx_context_stays_per_currency(self):
        fx_item = self._sheet2_row(115)
        proposal = fx_item["proposal"]
        self.assertEqual(proposal["currency"], "CNY")
        self.assertEqual(proposal["related_currency"], "VND")
        self.assertEqual(proposal["related_amount"], 100000000.0)
        self.assertEqual(proposal["fx_rate"], 3953.0)
        self.assertTrue(math.isclose(proposal["amount"], 100000000.0 / 3953.0, rel_tol=0, abs_tol=0.000001))

    def test_event_classification_keeps_customer_receipt_and_on_behalf_distinct(self):
        receipt = self._sheet2_row(99)
        received = self._sheet2_row(102)
        self.assertEqual(receipt["proposal"]["event_type"], "customer_receipt")
        self.assertEqual(received["proposal"]["event_type"], "received_on_behalf")
        self.assertEqual(receipt["review_status"], "REVIEW_REQUIRED")
        self.assertEqual(received["review_status"], "REVIEW_REQUIRED")

    def test_checkpoint_is_evidence_not_component(self):
        checkpoint = self._sheet2_row(129)
        proposal = checkpoint["proposal"]
        self.assertEqual(proposal["event_type"], "adjustment")
        self.assertEqual(proposal["checkpoint_key"], "THANH_ACCUMULATED")
        self.assertIsNone(proposal["candidate_bucket"])
        self.assertIn("CHECKPOINT_EVIDENCE", checkpoint["anomaly_flags"])
        self.assertEqual(checkpoint["review_status"], "REVIEW_REQUIRED")

    def test_anomalies_are_flagged_without_autocorrection(self):
        out_of_sequence = self._sheet2_row(35)
        inherited_date = self._sheet2_row(96)
        self.assertEqual(out_of_sequence["raw_date"], "2026-12-18")
        self.assertIn("DATE_OUT_OF_SEQUENCE", out_of_sequence["anomaly_flags"])
        self.assertEqual(inherited_date["raw_date"], None)
        self.assertEqual(inherited_date["inherited_date_context"], "2026-01-22")
        self.assertIn("INHERITED_DATE_CONTEXT", inherited_date["anomaly_flags"])
        self.assertGreater(
            sum(1 for item in self.batch["items"] if "DUPLICATE_LOOKING" in item["anomaly_flags"]),
            0,
        )

    def test_summary_surfaces_review_work_and_unknown_currency(self):
        summary = summarize_staging(self.batch["items"])
        self.assertEqual(summary["confirmed"], 0)
        self.assertGreater(summary["needs_review"], 0)
        self.assertGreater(summary["other_sale"], 0)
        self.assertGreater(summary["anomalies"], 0)
        self.assertGreater(summary["currencies"].get(UNKNOWN_CURRENCY, 0), 0)

    def test_fixture_review_status_does_not_promote_free_text_sale(self):
        sale = _sale_proposal(None, "món của Thành")
        proposal = {
            "sale_evidence": sale["sale_evidence"],
            "currency": "CNY",
            "event_type": "received_on_behalf",
            "anomalies": ["MISSING_SALE"],
        }
        self.assertIsNone(sale["internal_sale_owner"])
        self.assertEqual(sale["candidate_internal_sale_owner"], SALE_OWNER)
        self.assertEqual(_proposal_status(proposal), "REVIEW_REQUIRED")
        fixture = stage_fixture_rows([{"raw_text": "món của Thành", "proposal": proposal}])
        self.assertEqual(fixture[0]["parser_version"], PARSER_VERSION)
        self.assertEqual(fixture[0]["review_status"], "RAW")

    def test_parser_has_no_ui_or_canonical_ledger_dependency(self):
        source = Path(__file__).resolve().parents[1] / "core" / "historical_staging.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("import streamlit", text)
        self.assertNotIn("financial_ledger", text)
        self.assertNotIn("get_db", text)


if __name__ == "__main__":
    unittest.main()
