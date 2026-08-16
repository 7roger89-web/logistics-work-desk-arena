from __future__ import annotations

import unittest

from core.payment_logic import allocate_lump_sum, get_customer_debt_overview


class PaymentLogicTests(unittest.TestCase):
    def shipments(self):
        return {
            "S2": {
                "id": "S2", "customer_id": "KH1", "customer": "ABC",
                "data": {"0.0": {"created_at": "2026-02-01"}, "3.4": {"details": [{"qty": 1, "price": 2_000_000, "cost": 0, "vat_line": 0}], "commission": {}, "payments": []}},
            },
            "S1": {
                "id": "S1", "customer_id": "KH1", "customer": "ABC",
                "data": {"0.0": {"created_at": "2026-01-01"}, "3.4": {"details": [{"qty": 1, "price": 1_000_000, "cost": 0, "vat_line": 0}], "commission": {}, "payments": []}},
            },
        }

    def test_fifo_oldest_first(self):
        debt, total, rows = get_customer_debt_overview("KH1", self.shipments())
        self.assertEqual(debt, 3_000_000)
        self.assertEqual([row["id"] for row in rows], ["S1", "S2"])
        plan, remaining = allocate_lump_sum(1_500_000, rows)
        self.assertEqual(plan[0]["shipment_id"], "S1")
        self.assertEqual(plan[0]["pay_amount"], 1_000_000)
        self.assertEqual(plan[1]["shipment_id"], "S2")
        self.assertEqual(plan[1]["pay_amount"], 500_000)
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()
