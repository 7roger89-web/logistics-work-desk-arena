from __future__ import annotations

import unittest
from decimal import Decimal

from core.utils import get_shipment_business_date, parse_date_optional, to_decimal


class UtilsTests(unittest.TestCase):
    def test_vietnamese_thousand_separator(self):
        self.assertEqual(to_decimal("5.000.000"), Decimal("5000000"))

    def test_international_separator(self):
        self.assertEqual(to_decimal("1,234,567.89"), Decimal("1234567.89"))

    def test_dates(self):
        self.assertEqual(str(parse_date_optional("29/07/2026")), "2026-07-29")
        self.assertEqual(str(parse_date_optional("2026-07-29")), "2026-07-29")

    def test_shipment_business_date_prefers_nested_document_date(self):
        shipment = {
            "created_at": "2026-08-06",
            "data": {"0.0": {"created_at": "2025-12-18"}},
        }
        self.assertEqual(str(get_shipment_business_date(shipment)), "2025-12-18")

    def test_shipment_business_date_does_not_invent_today(self):
        self.assertIsNone(get_shipment_business_date({"data": {"0.0": {"created_at": "invalid"}}}))

    def test_shipment_business_date_uses_legacy_top_level_fallback(self):
        self.assertEqual(
            str(get_shipment_business_date({"created_at": "2026-07-29", "data": {"0.0": {}}})),
            "2026-07-29",
        )

    # --- LG05 Incident Fix: order_date priority over created_at ---

    def test_shipment_business_date_prefers_order_date_over_created_at(self):
        """LG05 incident fix: order_date (Ngày đặt hàng) should be preferred
        over created_at (Ngày tạo) for dashboard period filtering."""
        shipment = {
            "id": "TEST-001",
            "created_at": "2026-08-06",
            "data": {
                "0.0": {
                    "order_date": "2026-08-15",
                    "created_at": "2026-07-15",
                }
            },
        }
        result = get_shipment_business_date(shipment)
        self.assertEqual(str(result), "2026-08-15")

    def test_shipment_business_date_order_date_dd_mm_yyyy_format(self):
        """GETFLY files use dd/mm/yyyy format for order_date."""
        shipment = {
            "id": "TEST-002",
            "created_at": "2026-08-06",
            "data": {
                "0.0": {
                    "order_date": "25/08/2026",
                    "created_at": "01/07/2026",
                }
            },
        }
        result = get_shipment_business_date(shipment)
        self.assertEqual(str(result), "2026-08-25")

    def test_shipment_business_date_fallback_to_created_at_when_no_order_date(self):
        """When order_date is missing, fall back to created_at."""
        shipment = {
            "id": "TEST-003",
            "created_at": "2026-08-06",
            "data": {
                "0.0": {
                    "created_at": "2026-07-15",
                }
            },
        }
        result = get_shipment_business_date(shipment)
        self.assertEqual(str(result), "2026-07-15")

    def test_shipment_business_date_returns_none_when_no_dates(self):
        """When neither order_date nor created_at exists, return None."""
        shipment = {
            "id": "TEST-004",
            "data": {"0.0": {}},
        }
        result = get_shipment_business_date(shipment)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
