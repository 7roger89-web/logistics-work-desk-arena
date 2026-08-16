"""Pure LOG-C05 manager-report and Debit Draft behavior tests.

All data in this module is synthetic and in memory.  No live Mongo database,
workbook, payment endpoint, or AI client is used.
"""

from __future__ import annotations

from copy import deepcopy
import unittest

from core.debit_draft import build_debit_draft, build_manager_report
from core.financial_ledger import project_partner_financial_position
from tests.test_reconciliation_desk import (
    ABO,
    BG_GREEN,
    FACTORY,
    TT,
    _fixture_history,
    _obligation,
    _transaction,
)


class LogC05ReportDebitTests(unittest.TestCase):
    def setUp(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        self.position = project_partner_financial_position(
            ABO,
            obligations,
            transactions,
            allocations,
            internal_sale_owner="Thành",
        )

    def test_manager_report_has_header_summary_and_deterministic_explanation(self) -> None:
        report = build_manager_report(
            self.position,
            period_start="2026-08-01",
            period_end="2026-08-31",
            report_date="2026-08-14",
        )
        self.assertEqual(report["title"], "BÁO CÁO CÔNG NỢ A BÒ — SALE THÀNH")
        self.assertEqual(report["status"], "DRAFT")
        self.assertEqual(report["currencies"], ["CNY", "VND"])
        cny = report["summary_by_currency"]["CNY"]
        self.assertEqual(cny["received_on_behalf"], 64_151)
        self.assertEqual(cny["paid_on_behalf"], 134_973)
        self.assertEqual(cny["unknown"], 1_572)
        self.assertEqual(cny["restricted"], 8_000)
        explanation = report["explanations"]["CNY"]
        self.assertTrue(explanation["deterministic"])
        self.assertIn("=", explanation["formula"])
        self.assertIn("OBL-160000", explanation["source_record_ids"])

    def test_golden_credit_and_received_rows_are_source_backed(self) -> None:
        draft = build_debit_draft(self.position)
        cny = draft["by_currency"]["CNY"]
        included_ids = {value for line in cny["included_items"] for value in line["source_record_ids"]}
        self.assertIn("TX-CREDIT-24576", included_ids)
        self.assertIn("TX-RECEIVED-62464", included_ids)
        self.assertIn("TX-RECEIVED-1687", included_ids)
        paid_line = next(line for line in cny["payable_lines"] if line["transaction_id"] == "TX-PAID-134973")
        self.assertEqual(paid_line["amount"], 134_973)

    def test_unknown_and_restricted_are_visible_as_excluded(self) -> None:
        draft = build_debit_draft(self.position)
        excluded = draft["by_currency"]["CNY"]["excluded_items"]
        by_id = {item["transaction_id"]: item for item in excluded if item.get("transaction_id")}
        self.assertEqual(by_id["TX-UNKNOWN-1572"]["category"], "unknown")
        self.assertEqual(by_id["TX-RESTRICTED"]["category"], "restricted")
        self.assertEqual(by_id["TX-UNKNOWN-1572"]["amount"], 1_572)

    def test_customer_receipt_leg_does_not_become_abo_settlement(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        transactions.append(
            _transaction(
                "TX-BG-25025-RELATED",
                25_025,
                source=BG_GREEN,
                holder=TT,
                beneficial=ABO,
                kind="payment",
                note="customer receipt leg only",
            )
        )
        position = project_partner_financial_position(ABO, obligations, transactions, allocations, internal_sale_owner="Thành")
        included_ids = {
            source_id
            for values in (build_debit_draft(position).get("by_currency") or {}).values()
            for line in values.get("included_items") or []
            for source_id in line.get("source_record_ids") or []
        }
        self.assertNotIn("TX-BG-25025-RELATED", included_ids)

    def test_important_shipments_are_derived_and_sorted(self) -> None:
        report = build_manager_report(self.position)
        shipments = report["important_shipments"]
        self.assertTrue(shipments)
        self.assertIn("L-001", {row["shipment_id"] for row in shipments})
        self.assertEqual(shipments, sorted(shipments, key=lambda row: (-abs(row["impact_amount"]), row["currency"], row["shipment_id"])))

    def test_partner_report_difference_is_visible_and_never_added_to_debit(self) -> None:
        report = build_manager_report(self.position, reported_by_currency={"CNY": 225_546, "VND": 1_900_000})
        differences = {row["currency"]: row for row in report["partner_difference"]}
        self.assertTrue(differences["CNY"]["has_difference"])
        self.assertEqual(differences["CNY"]["action"], "Cần đối soát chênh lệch với A Bò")
        draft = report["debit_preview"]
        cny = draft["by_currency"]["CNY"]
        self.assertEqual(cny["debit_ready_amount"], report["summary_by_currency"]["CNY"]["debit_eligible_amount"])
        partner_lines = [item for item in cny["excluded_items"] if item.get("category") == "partner_difference"]
        self.assertEqual(len(partner_lines), 1)

    def test_clean_fixture_exactly_reconciles_to_40000_cny(self) -> None:
        obligations = [
            _obligation("OBL-CLEAN", 100_000, day=2),
            _obligation("OBL-RECEIVED-TARGET", 20_000, to_party=FACTORY, day=3, purpose="received-on-behalf allocation"),
        ]
        transactions = [
            _transaction("TX-ALREADY-PAID", 10_000, kind="payment", day=4),
            _transaction("TX-HELD-ELIGIBLE", 30_000, kind="held_money", day=5),
            _transaction(
                "TX-RECEIVED-ALLOCATED",
                20_000,
                kind="received_on_behalf",
                source=FACTORY,
                holder=ABO,
                beneficial=TT,
                day=6,
            ),
        ]
        allocations = [
            {
                "id": "ALC-ALREADY-PAID",
                "record_type": "allocation",
                "transaction_id": "TX-ALREADY-PAID",
                "obligation_id": "OBL-CLEAN",
                "amount": 10_000,
                "currency": "CNY",
                "status": "active",
                "created_at": "2026-08-07",
                "evidence_refs": [{"kind": "fixture", "reference": "ALC-ALREADY-PAID"}],
            },
            {
                "id": "ALC-RECEIVED-ALLOCATED",
                "record_type": "allocation",
                "transaction_id": "TX-RECEIVED-ALLOCATED",
                "obligation_id": "OBL-RECEIVED-TARGET",
                "amount": 20_000,
                "currency": "CNY",
                "status": "active",
                "created_at": "2026-08-08",
                "evidence_refs": [{"kind": "fixture", "reference": "ALC-RECEIVED-ALLOCATED"}],
            },
        ]
        position = project_partner_financial_position(ABO, obligations, transactions, allocations, internal_sale_owner="Thành")
        draft = build_debit_draft(position)
        cny = draft["by_currency"]["CNY"]
        self.assertEqual(cny["payable_subtotal"], 90_000)
        self.assertEqual(cny["credit_subtotal"], 50_000)
        self.assertEqual(cny["settled_amount"], 10_000)
        self.assertEqual(cny["received_on_behalf_allocated"], 20_000)
        self.assertEqual(cny["debit_ready_amount"], 40_000)
        self.assertIn("100000 CNY", cny["formula"])
        self.assertIn("10000 CNY · Đã thanh toán / đã cấn", cny["formula"])
        self.assertIn("= 40000 CNY", cny["formula"])
        self.assertIn("TX-RECEIVED-ALLOCATED", cny["references"]["transaction_ids"])
        self.assertIn("ALC-ALREADY-PAID", cny["references"]["allocation_ids"])

    def test_multi_currency_never_creates_one_combined_total(self) -> None:
        draft = build_debit_draft(self.position)
        self.assertEqual(draft["currencies"], ["CNY", "VND"])
        self.assertNotIn("total", draft)
        self.assertIn("CNY", draft["by_currency"])
        self.assertIn("VND", draft["by_currency"])

    def test_currency_mismatch_reversed_and_already_settled_are_excluded(self) -> None:
        position = {
            "party": ABO,
            "party_key": "partner:ABO",
            "internal_sale_owner": "Thành",
            "totals_by_currency": {"CNY": {}},
            "buckets": {
                "payable_to_partner": [],
                "held_credit": [
                    {
                        "transaction_id": "TX-SETTLED",
                        "currency": "CNY",
                        "amount": 5_000,
                        "unallocated": 5_000,
                        "internal_sale_owner": "Thành",
                        "already_settled": True,
                        "evidence_refs": [{"kind": "fixture", "reference": "TX-SETTLED"}],
                    },
                    {
                        "transaction_id": "TX-REVERSED",
                        "currency": "CNY",
                        "amount": 6_000,
                        "unallocated": 6_000,
                        "internal_sale_owner": "Thành",
                        "status": "reversed",
                        "evidence_refs": [{"kind": "fixture", "reference": "TX-REVERSED"}],
                    },
                ],
                "received_on_behalf": [
                    {
                        "transaction_id": "TX-CURRENCY-MISMATCH",
                        "currency": "CNY",
                        "amount": 7_000,
                        "allocated": 7_000,
                        "internal_sale_owner": "Thành",
                        "review_reason": "incompatible allocation currency",
                        "evidence_refs": [{"kind": "fixture", "reference": "TX-CURRENCY-MISMATCH"}],
                    }
                ],
                "paid_on_behalf": [],
                "unallocated": [],
                "unknown": [],
                "restricted": [],
            },
        }
        excluded = build_debit_draft(position)["by_currency"]["CNY"]["excluded_items"]
        by_id = {row["transaction_id"]: row for row in excluded}
        self.assertEqual(by_id["TX-SETTLED"]["category"], "already_settled")
        self.assertEqual(by_id["TX-REVERSED"]["category"], "reversed")
        self.assertEqual(by_id["TX-CURRENCY-MISMATCH"]["category"], "currency_mismatch")

    def test_calculation_is_read_only(self) -> None:
        before = deepcopy(self.position)
        draft = build_debit_draft(self.position)
        report = build_manager_report(self.position)
        self.assertEqual(self.position, before)
        self.assertEqual(draft["financial_effect_write_count"], 0)
        self.assertEqual(report["financial_effect_write_count"], 0)


if __name__ == "__main__":
    unittest.main()
