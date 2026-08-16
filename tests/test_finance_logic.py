from __future__ import annotations

import unittest

from core.logic import apply_financial_snapshot, calculate_shipment_financials


class FinanceLogicTests(unittest.TestCase):
    def test_vat_is_not_profit(self):
        result = calculate_shipment_financials(
            [{"qty": 1, "price": 100_000_000, "cost": 80_000_000, "vat_line": 8}],
            {"total": 5_000_000},
            [],
        )
        self.assertEqual(result["revenue_net"], 100_000_000)
        self.assertEqual(result["output_vat"], 8_000_000)
        self.assertEqual(result["receivable"], 108_000_000)
        self.assertEqual(result["profit"], 15_000_000)
        self.assertEqual(result["debt"], 108_000_000)

    def test_legacy_aliases_are_supported(self):
        result = calculate_shipment_financials(
            [{"qty": "2", "price_out": "1,500,000", "price_in": "1.000.000", "vat": "10"}],
            [{"amount": 100_000}],
            [{"amount": 1_000_000}],
        )
        self.assertEqual(result["receivable"], 3_300_000)
        self.assertEqual(result["cost"], 2_000_000)
        self.assertEqual(result["profit"], 900_000)
        self.assertEqual(result["debt"], 2_300_000)

    def test_snapshot_updates_legacy_fields(self):
        shipment = {
            "id": "SHP-1",
            "data": {"3.4": {"details": [{"qty": 1, "price": 1_000_000, "cost": 500_000, "vat_line": 10}], "commission": {"total": 0}, "payments": []}},
        }
        apply_financial_snapshot(shipment)
        finance = shipment["data"]["3.4"]
        self.assertEqual(finance["out"], 1_100_000)
        self.assertEqual(finance["out_net"], 1_000_000)
        self.assertEqual(finance["profit"], 500_000)


if __name__ == "__main__":
    unittest.main()
