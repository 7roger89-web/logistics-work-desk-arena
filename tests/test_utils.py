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


if __name__ == "__main__":
    unittest.main()
