"""Behavior tests for LOG-C09 read-only entity context projections."""

from __future__ import annotations

import unittest
from copy import deepcopy

from core.entity_context import (
    build_customer_context,
    build_factory_context,
    build_partner_context,
    list_context_entities,
)
from core.shipment_360 import UNKNOWN


def _shipments() -> dict[str, dict]:
    return {
        "S-001": {
            "id": "S-001",
            "customer": "Acme",
            "customer_id": "CUS-1",
            "status": "pending",
            "customer_required_date": "2026-08-30",
            "factories": [{
                "factory_name": "Factory North",
                "lot_id": "LOT-1",
                "product": "Widgets",
                "quantity": 12,
                "weight": 400,
                "cbm": 2.5,
                "factory_ready_date": "2026-08-20",
                "required_information_complete": True,
            }],
            "partner": {"name": "Blue Agent", "role": "Pickup agent"},
            "data": {"0.0": {"mode": "Sea"}, "1.2": {"pol": "Yantian", "pod": "Cat Lai"}, "3.4": {}},
        },
        "S-002": {
            "id": "S-002",
            "customer": "Acme",
            "customer_id": "CUS-1",
            "status": "done",
            "factories": [{"factory_name": "Factory North", "lot_id": "LOT-2"}],
            "partner": {"name": "Blue Agent", "role": "Documentation"},
            "data": {"3.4": {}},
        },
        "S-003": {
            "id": "S-003",
            "customer": "Other Customer",
            "customer_id": "CUS-2",
            "status": "pending",
            "data": {"3.4": {}},
        },
    }


class EntityContextTests(unittest.TestCase):
    def test_customer_context_separates_master_from_related_shipments(self) -> None:
        customers = {"CUS-1": {"id": "CUS-1", "name": "Acme", "contact_person": "Lan", "phone": "0900"}}
        shipments = _shipments()
        shipments["S-001"]["id"] = "legacy-s-001"
        shipments["S-001\t"] = shipments.pop("S-001")
        before = deepcopy(shipments)

        view = build_customer_context("CUS-1", customers["CUS-1"], shipments)

        self.assertEqual(shipments, before)
        self.assertEqual(view["master"]["fields"]["contact"], "Lan")
        self.assertEqual(view["shipments"][0]["shipment_id"], "S-001\t")
        self.assertEqual([row["shipment_id"] for row in view["active_shipments"]], ["S-001\t"])
        self.assertEqual([row["shipment_id"] for row in view["history_shipments"]], ["S-002"])
        self.assertTrue(view["read_only"])

    def test_factory_context_keeps_multi_lot_unknowns_truthful(self) -> None:
        view = build_factory_context("Factory North", _shipments())

        self.assertEqual([row["lot"] for row in view["lots"]], ["LOT-1", "LOT-2"])
        self.assertEqual(view["lots"][0]["quantity"], "12")
        self.assertEqual(view["lots"][1]["quantity"], UNKNOWN)
        self.assertEqual(view["master"]["status"], UNKNOWN)
        self.assertIn("shipment/lot-specific", view["lots"][0]["source"])

    def test_partner_context_is_generic_and_does_not_aggregate_finance(self) -> None:
        view = build_partner_context("Blue Agent", _shipments())

        self.assertEqual(view["roles"], ["Documentation", "Pickup agent"])
        self.assertEqual(len(view["shipments"]), 2)
        self.assertEqual(len(view["financial_projection"]), 2)
        self.assertNotIn("balance", view)
        self.assertIn("per-shipment", view["financial_note"].casefold())

    def test_entity_index_contains_customer_factory_partner_options(self) -> None:
        customers = {"CUS-1": {"id": "CUS-1", "name": "Acme"}}
        options = list_context_entities(customers, _shipments())
        self.assertEqual({option["entity_type"] for option in options}, {"customer", "factory", "partner"})


if __name__ == "__main__":
    unittest.main()
