from __future__ import annotations

import copy
import unittest
from datetime import date

from core.finance_review import (
    STATUS_CONFIRMED,
    STATUS_DUE_SOON,
    STATUS_MISSING_EVIDENCE,
    STATUS_OVERDUE,
    STATUS_RESTRICTED,
    STATUS_UNKNOWN,
    STATUS_UNALLOCATED,
    build_finance_review_items,
    summarize_finance_review,
)


TT = {"party_type": "partner", "party_id": "TT", "name": "Thành"}
PARTNER = {"party_type": "partner", "party_id": "P-01", "name": "Partner One"}
CUSTOMER = {"party_type": "customer", "party_id": "C-01", "name": "Customer One"}


def obligation(record_id: str, amount: float, *, currency: str = "USD", due_date: str = "2026-08-20", shipment_ids=None, classification_status: str = "CONFIRMED", evidence=True):
    row = {
        "id": record_id,
        "from_party": CUSTOMER,
        "to_party": PARTNER,
        "amount": amount,
        "currency": currency,
        "due_date": due_date,
        "shipment_ids": shipment_ids or [],
        "internal_sale_owner": "Thành",
        "classification_status": classification_status,
    }
    if evidence:
        row["evidence_refs"] = [{"reference": record_id}]
    return row


def transaction(record_id: str, amount: float, *, currency: str = "USD", shipment_ids=None, restriction=None, classification_status: str = "CONFIRMED", evidence=True):
    row = {
        "id": record_id,
        "source_party": CUSTOMER,
        "holder_party": PARTNER,
        "beneficial_owner": TT,
        "amount": amount,
        "currency": currency,
        "transaction_kind": "held_money",
        "shipment_ids": shipment_ids or [],
        "internal_sale_owner": "Thành",
        "classification_status": classification_status,
        "restriction": restriction or {"status": "NONE"},
    }
    if evidence:
        row["evidence_refs"] = [{"reference": record_id}]
    return row


class FinanceReviewProjectionTests(unittest.TestCase):
    def test_due_and_overdue_obligations_are_actionable(self):
        rows = build_finance_review_items(
            [
                obligation("OBL-DUE", 100, due_date="2026-08-20"),
                obligation("OBL-OVERDUE", 200, due_date="2026-08-10"),
            ],
            [],
            [],
            today=date(2026, 8, 16),
        )
        by_id = {row["record_id"]: row for row in rows}
        self.assertEqual(by_id["OBL-DUE"]["status"], STATUS_DUE_SOON)
        self.assertEqual(by_id["OBL-OVERDUE"]["status"], STATUS_OVERDUE)

    def test_unallocated_money_is_first_class_and_not_shipment_required(self):
        rows = build_finance_review_items([], [transaction("TX-UNALLOCATED", 500)], [], today=date(2026, 8, 16))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], STATUS_UNALLOCATED)
        self.assertEqual(rows[0]["shipment_ids"], [])
        self.assertTrue(rows[0]["read_only"])

    def test_unknown_restricted_and_missing_evidence_do_not_enter_confirmed_totals(self):
        rows = build_finance_review_items(
            [obligation("OBL-UNKNOWN", 100, classification_status="UNKNOWN"), obligation("OBL-NO-EVIDENCE", 200, evidence=False)],
            [transaction("TX-RESTRICTED", 300, restriction={"status": "RESTRICTED"})],
            [],
            today=date(2026, 8, 16),
        )
        by_id = {row["record_id"]: row for row in rows}
        self.assertEqual(by_id["OBL-UNKNOWN"]["status"], STATUS_UNKNOWN)
        self.assertEqual(by_id["OBL-NO-EVIDENCE"]["status"], STATUS_MISSING_EVIDENCE)
        self.assertEqual(by_id["TX-RESTRICTED"]["status"], STATUS_RESTRICTED)
        summary = summarize_finance_review(rows)
        self.assertEqual(summary["totals_by_currency"]["USD"]["confirmed_outstanding"], 0.0)
        self.assertEqual(summary["totals_by_currency"]["USD"]["excluded_amount"], 600.0)
        self.assertGreater(summary["counts"][STATUS_UNKNOWN], 0)

    def test_currencies_are_kept_separate_and_partner_filter_is_generic(self):
        rows = build_finance_review_items(
            [obligation("OBL-USD", 100, currency="USD"), obligation("OBL-CNY", 200, currency="CNY")],
            [],
            [],
            party_type="partner",
            party_id="P-01",
            today=date(2026, 8, 16),
        )
        summary = summarize_finance_review(rows)
        self.assertEqual(set(summary["totals_by_currency"]), {"USD", "CNY"})
        self.assertNotIn("A Bò", {row["party"] for row in rows})
        self.assertTrue(all(row["party_id"] == "P-01" for row in rows))

    def test_customer_filter_and_search_do_not_mutate_inputs(self):
        rows = [obligation("OBL-CUSTOMER", 100)]
        before = copy.deepcopy(rows)
        result = build_finance_review_items(rows, [], [], party_type="customer", party_id="C-01", search="customer", today=date(2026, 8, 16))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["party_id"], "C-01")
        self.assertEqual(rows, before)


if __name__ == "__main__":
    unittest.main()
