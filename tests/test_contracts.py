from __future__ import annotations

import unittest

from views.contracts import _shipment_matches_contract, normalize_contract_no


class ContractRelationshipTests(unittest.TestCase):
    def test_contract_number_normalization_is_stable(self):
        self.assertEqual(normalize_contract_no("  ct-2026 / 07 "), "CT2026/07")

    def test_direct_contract_link_matches_many_shipments(self):
        shipment = {"contract_id": "ct-2026-07", "data": {"entrustment": {"active": False}}}
        self.assertTrue(_shipment_matches_contract(shipment, "CT 2026 07"))

    def test_legacy_entrustment_link_remains_readable(self):
        shipment = {"data": {"entrustment": {"active": True, "contract_no": "C-01"}}}
        self.assertTrue(_shipment_matches_contract(shipment, "C01"))


if __name__ == "__main__":
    unittest.main()
