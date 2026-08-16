from __future__ import annotations

import unittest

from core.validators import validate_shipment


class ValidatorTests(unittest.TestCase):
    def base_shipment(self):
        return {
            "id": "SHP-1",
            "customer": "Công ty ABC",
            "status": "pending",
            "data": {
                "0.0": {"created_at": "2026-07-29"},
                "1.2": {"etd": "2026-07-30"},
                "2.6": {"arrival_date": "2026-08-02"},
                "2.7": {},
                "3.4": {"details": [], "commission": {"total": 0}, "payments": []},
            },
        }

    def test_missing_customer_is_blocking(self):
        shipment = self.base_shipment()
        shipment["customer"] = ""
        result = validate_shipment(shipment)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "CUSTOMER_REQUIRED" for issue in result.errors))

    def test_etd_after_eta_is_warning(self):
        shipment = self.base_shipment()
        shipment["data"]["1.2"]["etd"] = "03/08/2026"
        shipment["data"]["2.6"]["arrival_date"] = "02/08/2026"
        result = validate_shipment(shipment)
        self.assertTrue(result.is_valid)
        self.assertTrue(any(issue.code == "ETD_AFTER_ETA" for issue in result.warnings))

    def test_negative_payment_is_blocking(self):
        shipment = self.base_shipment()
        shipment["data"]["3.4"]["payments"] = [{"id": "P1", "amount": -1000}]
        result = validate_shipment(shipment)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "INVALID_PAYMENT" for issue in result.errors))


if __name__ == "__main__":
    unittest.main()
