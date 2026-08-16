"""Synthetic LOG-C04 projection and reconciliation fixtures.

These tests intentionally stay in memory/pure functions.  They must never use
the application's Mongo database or import the real workbook.
"""

from __future__ import annotations

import unittest
from datetime import date

from core.financial_ledger import (
    CONFIRMED,
    NONE_RESTRICTION,
    RESTRICTED,
    UNKNOWN,
    project_partner_financial_position,
)
from core.reconciliation import (
    build_all_currency_explanations,
    build_money_location_trace,
    build_period_reconciliation,
    build_review_inbox,
    compare_reported_position,
    search_partner_position,
)


TT = {"party_type": "partner", "party_id": "TT", "name": "Trường Thành"}
ABO = {"party_type": "partner", "party_id": "ABO", "name": "A Bò"}
FACTORY = {"party_type": "factory", "party_id": "FACTORY-CN", "name": "Nhà máy đồ chơi"}
LUC_GIAC = {"party_type": "factory", "party_id": "LUC-GIAC", "name": "Lục Giác"}
BG_GREEN = {"party_type": "customer", "party_id": "BG-GREEN", "name": "B&G Green"}


def _obligation(
    obligation_id: str,
    amount: int,
    *,
    currency: str = "CNY",
    owner: str | None = "Thành",
    to_party: dict | None = None,
    day: int = 2,
    purpose: str = "chi hộ vận chuyển",
) -> dict:
    row = {
        "id": obligation_id,
        "record_type": "obligation",
        "from_party": TT,
        "to_party": to_party or ABO,
        "amount": amount,
        "currency": currency,
        "purpose": purpose,
        "shipment_ids": ["L-001"],
        "internal_sale_owner": owner,
        "status": "active",
        "created_at": f"2026-08-{day:02d}",
        "evidence_refs": [{"kind": "fixture", "reference": obligation_id}],
        "source_refs": [{"kind": "workbook-row", "reference": obligation_id}],
        "provenance": {"source_type": "fixture", "source_id": obligation_id},
    }
    return row


def _transaction(
    transaction_id: str,
    amount: int,
    *,
    currency: str = "CNY",
    kind: str = "held_money",
    source: dict = TT,
    holder: dict = ABO,
    beneficial: dict | None = TT,
    owner: str | None = "Thành",
    classification: str = CONFIRMED,
    restriction: str = NONE_RESTRICTION,
    day: int = 3,
    note: str | None = None,
) -> dict:
    row = {
        "id": transaction_id,
        "record_type": "transaction",
        "source_party": source,
        "holder_party": holder,
        "beneficial_owner": beneficial,
        "beneficiary_party": TT,
        "amount": amount,
        "currency": currency,
        "transaction_kind": kind,
        "shipment_ids": ["L-001"],
        "internal_sale_owner": owner,
        "classification_status": classification,
        "restriction": {"status": restriction},
        "status": "active",
        "occurred_at": f"2026-08-{day:02d}",
        "evidence_refs": [{"kind": "fixture", "reference": transaction_id}],
        "source_refs": [{"kind": "statement", "reference": transaction_id}],
        "provenance": {"source_type": "fixture", "source_id": transaction_id},
    }
    if note:
        row["note"] = note
    return row


def _fixture_history() -> tuple[list[dict], list[dict], list[dict]]:
    obligations = [
        _obligation("OBL-160000", 160_000, day=2, purpose="A Bò phải nhận từ TT"),
        _obligation("OBL-PARTIAL", 50_000, day=4, purpose="lô L-001"),
        _obligation("OBL-RECEIVED-LINK", 62_464, to_party=FACTORY, day=5, purpose="chuyển nhà máy"),
        _obligation("OBL-VND", 2_000_000, currency="VND", day=6),
        _obligation("OBL-MISSING-OWNER", 9_999, owner=None, day=7),
    ]
    transactions = [
        _transaction("TX-CREDIT-24576", 24_576, day=3, note="credit lịch sử"),
        _transaction(
            "TX-RECEIVED-62464",
            62_464,
            kind="received_on_behalf",
            source=FACTORY,
            beneficial=TT,
            day=4,
            note="nhà máy chuyển qua A Bò để chuyển cho Thành",
        ),
        _transaction(
            "TX-RECEIVED-1687",
            1_687,
            kind="received_on_behalf",
            source=LUC_GIAC,
            beneficial=TT,
            day=5,
            note="Lục Giác thanh toán tiền vận chuyển cho Thành",
        ),
        _transaction(
            "TX-UNKNOWN-1572",
            1_572,
            classification=UNKNOWN,
            day=6,
            note="món của Thành",
        ),
        _transaction(
            "TX-RESTRICTED",
            8_000,
            restriction=RESTRICTED,
            day=7,
        ),
        _transaction(
            "TX-PAID-134973",
            134_973,
            kind="paid_on_behalf",
            source=ABO,
            holder=FACTORY,
            beneficial=TT,
            day=8,
            note="nhóm chuyển hộ: B&G, ABING, Lục Giác, Khung tranh Đà Lạt",
        ),
        _transaction("TX-PARTIAL", 30_000, day=9),
        _transaction(
            "TX-BG-25025",
            25_025,
            source=BG_GREEN,
            holder=TT,
            beneficial=BG_GREEN,
            kind="payment",
            day=10,
            note="khách chuyển vào tài khoản Trường Thành",
        ),
        _transaction("TX-VND-HELD", 100_000, currency="VND", day=11),
    ]
    allocations = [
        {
            "id": "ALC-PARTIAL",
            "record_type": "allocation",
            "transaction_id": "TX-PARTIAL",
            "obligation_id": "OBL-PARTIAL",
            "amount": 12_500,
            "currency": "CNY",
            "status": "active",
            "shipment_ids": ["L-001"],
            "created_at": "2026-08-10",
            "evidence_refs": [{"kind": "fixture", "reference": "ALC-PARTIAL"}],
            "source_refs": [{"kind": "allocation", "reference": "ALC-PARTIAL"}],
        },
    ]
    return obligations, transactions, allocations


class ReconciliationDeskFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        self.position = project_partner_financial_position(
            ABO,
            obligations,
            transactions,
            allocations,
            internal_sale_owner="Thành",
        )

    def test_payable_and_held_buckets_are_separate_by_currency(self) -> None:
        cny = self.position["totals_by_currency"]["CNY"]
        vnd = self.position["totals_by_currency"]["VND"]
        self.assertGreater(cny["payable_to_partner"], 0)
        self.assertGreater(cny["held_credit"], 0)
        self.assertEqual(vnd["payable_to_partner"], 2_000_000)
        self.assertEqual(vnd["held_credit"], 100_000)
        self.assertEqual(set(self.position["net_position_by_currency"]), {"CNY", "VND"})

    def test_received_on_behalf_keeps_62464_and_1687_as_first_class_rows(self) -> None:
        rows = self.position["buckets"]["received_on_behalf"]
        amounts = {row["transaction_id"]: row["received_amount"] for row in rows}
        self.assertEqual(amounts["TX-RECEIVED-62464"], 62_464)
        self.assertEqual(amounts["TX-RECEIVED-1687"], 1_687)
        self.assertEqual(self.position["totals_by_currency"]["CNY"]["received_on_behalf"], 64_151)

    def test_paid_on_behalf_is_separate_and_does_not_settle_bg_leg(self) -> None:
        rows = self.position["buckets"]["paid_on_behalf"]
        self.assertEqual({row["transaction_id"] for row in rows}, {"TX-PAID-134973"})
        self.assertEqual(rows[0]["spent_amount"], 134_973)
        all_ids = {
            row.get("transaction_id")
            for bucket in self.position["buckets"].values()
            for row in bucket
        }
        self.assertNotIn("TX-BG-25025", all_ids)

    def test_unknown_and_restricted_are_visible_but_excluded(self) -> None:
        inbox = build_review_inbox(self.position)
        ids = {row["transaction_id"] for row in inbox if row.get("transaction_id")}
        self.assertIn("TX-UNKNOWN-1572", ids)
        self.assertIn("TX-RESTRICTED", ids)
        explanation = build_all_currency_explanations(self.position)["CNY"]
        excluded_ids = set(explanation["source_record_ids"]) - {
            item_id for line in explanation["lines"] for item_id in line["source_record_ids"]
        }
        self.assertIn("TX-UNKNOWN-1572", excluded_ids)
        self.assertTrue(explanation["deterministic"])

    def test_partial_allocation_derives_remaining_held_and_payable(self) -> None:
        held = next(row for row in self.position["buckets"]["held_credit"] if row["transaction_id"] == "TX-PARTIAL")
        payable = next(row for row in self.position["buckets"]["payable_to_partner"] if row["obligation_id"] == "OBL-PARTIAL")
        self.assertEqual(held["unallocated"], 17_500)
        self.assertEqual(payable["outstanding"], 37_500)
        self.assertEqual(held["allocation_history"][0]["id"], "ALC-PARTIAL")

    def test_owner_filter_is_exact_and_missing_live_owner_is_truthful(self) -> None:
        coverage = self.position["owner_coverage"]
        self.assertEqual(coverage["requested_owner"], "Thành")
        self.assertGreaterEqual(coverage["matching_owner_count"], 1)
        self.assertGreaterEqual(coverage["missing_owner_count"], 1)
        self.assertIn("Thành", coverage["known_owners"])

    def test_explanation_reconciles_to_confirmed_total_with_record_ids(self) -> None:
        explanation = build_all_currency_explanations(self.position)["CNY"]
        signed = sum(line["signed_amount"] for line in explanation["lines"])
        self.assertEqual(signed, explanation["confirmed_total"])
        self.assertIn("OBL-160000", explanation["source_record_ids"])
        self.assertIn("TX-CREDIT-24576", explanation["source_record_ids"])
        self.assertIn("=", explanation["formula"])

    def test_search_62464_surfaces_received_fixture(self) -> None:
        results = search_partner_position(self.position, "62464")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["transaction_id"], "TX-RECEIVED-62464")

    def test_money_location_trace_shows_source_holder_beneficial_and_remaining(self) -> None:
        row = next(row for row in self.position["buckets"]["received_on_behalf"] if row["transaction_id"] == "TX-RECEIVED-62464")
        trace = build_money_location_trace(row)
        labels = " ".join(step["label"] for step in trace["steps"])
        self.assertEqual(trace["remaining"], 62_464)
        self.assertIn("Luồng tiền ban đầu", labels)
        self.assertIn("Chủ sở hữu hưởng lợi", labels)
        self.assertIn("chưa phân bổ", labels)
        self.assertEqual(trace["source_record_ids"][0], "TX-RECEIVED-62464")

    def test_partner_report_difference_has_rule_based_candidate_categories(self) -> None:
        comparison = compare_reported_position(self.position, {"CNY": 0, "VND": 0})
        cny = next(row for row in comparison["comparisons"] if row["currency"] == "CNY")
        self.assertTrue(comparison["has_difference"])
        self.assertIn("unallocated", cny["candidate_unmatched_categories"])
        self.assertIn("unknown", cny["candidate_unmatched_categories"])
        self.assertTrue(comparison["rule_based"])

    def test_period_reconciliation_is_draft_and_separates_confirmed_review(self) -> None:
        period = build_period_reconciliation(
            self.position,
            start=date(2026, 8, 1),
            end=date(2026, 8, 14),
        )
        self.assertTrue(period["draft"])
        self.assertFalse(period["close_or_lock"])
        self.assertIn("CNY", period["by_currency"])
        self.assertIn("current_confirmed_position", period["by_currency"]["CNY"])
        self.assertEqual(period["by_currency"]["CNY"]["allocations_netting"], -12_500)
        self.assertTrue(period["deterministic"])


if __name__ == "__main__":
    unittest.main()
