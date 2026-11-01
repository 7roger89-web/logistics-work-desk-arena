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

    def test_g1_foreign_customer_id_never_falls_back_to_matching_name(self) -> None:
        master = {"id": "CUS-1", "name": "Acme"}
        foreign = _shipments()["S-003"]
        foreign["customer"] = "Acme"
        foreign["customer_id"] = "CUS-2"
        result = build_customer_context("CUS-1", master, {"foreign": foreign},
                                        quotes={"Q1": {"id": "Q1", "customer_id": "CUS-2",
                                                       "customer_name": "Acme"}})
        self.assertEqual(result["shipments"], [])
        self.assertEqual(result["quotations"], [])

        # Same canonical ID remains linked even if the cached legal name is old.
        renamed = dict(foreign, customer_id="CUS-1", customer="Historical Acme")
        result = build_customer_context("CUS-1", master, {"renamed": renamed})
        self.assertEqual(len(result["shipments"]), 1)

        # Legacy name-only rows never auto-link into shipments/quotes/agreements/contracts;
        # they stay strictly in reconciliation_candidates with zero portal/profile grant.
        legacy = dict(foreign, customer_id="", customer="Acme")
        result = build_customer_context(
            "CUS-1",
            master,
            {"legacy": legacy},
            quotes={"Q-LEG": {"id": "Q-LEG", "quote_no": "BG-LEG", "customer_id": "", "customer_name": "Acme",
                              "calculation": {"selling_price_total_vnd": 99_000_000, "estimated_margin_vnd": 25_000_000}}},
            agreements={"AGR-LEG": {"agreement_id": "AGR-LEG", "agreement_no": "TT-LEG", "customer_id": None, "customer_name": "Acme"}},
            contracts={"HD-LEG": {"id": "HD-LEG", "contract_no": "HDMB-LEG", "customer_id": "   ", "client": "Acme"}},
        )
        self.assertEqual(result["shipments"], [])
        self.assertEqual(result["quotations"], [])
        self.assertEqual(result["agreements"], [])
        self.assertEqual(result["contracts"], [])
        self.assertEqual(
            [(row["record_type"], row["bucket"], row["auto_linked"], row["portal_grant"])
             for row in result["reconciliation_candidates"]],
            [
                ("agreement", "CANDIDATE_REVIEW", False, False),
                ("contract", "CANDIDATE_REVIEW", False, False),
                ("quotation", "CANDIDATE_REVIEW", False, False),
                ("shipment", "CANDIDATE_REVIEW", False, False),
            ],
        )

        legacy["client"] = "Conflicting Legal Entity"
        result = build_customer_context("CUS-1", master, {"legacy": legacy})
        self.assertEqual(result["shipments"], [])
        self.assertEqual(result["reconciliation_candidates"][0]["bucket"], "CONFLICT")
        self.assertEqual(result["reconciliation_candidates"][0]["reason_code"], "CACHED_CUSTOMER_NAMES_DIFFER")

    def test_g1_duplicate_customer_names_never_leak_idless_records_across_profiles(self) -> None:
        import json

        customers = {
            "CUST-DUP-A": {"id": "CUST-DUP-A", "name": "Công Ty Trùng Tên G1"},
            "CUST-DUP-B": {"id": "CUST-DUP-B", "name": "Công Ty Trùng Tên G1"},
        }
        shipments = {
            "LO-NOID": dict(_shipments()["S-001"], id="LO-NOID", shipment_id="LO-NOID",
                            customer="Công Ty Trùng Tên G1", client="Công Ty Trùng Tên G1", customer_id=""),
        }
        quotes = {
            "Q-NOID": {
                "id": "Q-NOID",
                "quote_no": "BG-NOID-01",
                "customer_name": "Công Ty Trùng Tên G1",
                "customer_id": "",
                "status": "APPROVED",
                "calculation": {"selling_price_total_vnd": 158_765_432, "estimated_margin_vnd": 41_234_567},
            }
        }
        agreements = {
            "AGR-NOID": {
                "agreement_id": "AGR-NOID",
                "agreement_no": "TT-NOID-01",
                "customer_name": "Công Ty Trùng Tên G1",
                "customer_id": None,
                "status": "ACTIVE",
                "commercial_snapshot": {"incoterm": "DDP"},
            }
        }
        contracts = {
            "HD-NOID": {
                "id": "HD-NOID",
                "contract_no": "HDMB-NOID-01",
                "client": "Công Ty Trùng Tên G1",
                "customer_id": "",
                "status": "active",
                "value": 999_888_777,
            }
        }

        for cid in ("CUST-DUP-A", "CUST-DUP-B"):
            ctx = build_customer_context(
                cid,
                customers[cid],
                shipments,
                quotes=quotes,
                agreements=agreements,
                contracts=contracts,
                customers=customers,
            )
            self.assertEqual(ctx["shipments"], [])
            self.assertEqual(ctx["active_shipments"], [])
            self.assertEqual(ctx["quotations"], [])
            self.assertEqual(ctx["active_quotations"], [])
            self.assertEqual(ctx["agreements"], [])
            self.assertEqual(ctx["active_agreements"], [])
            self.assertEqual(ctx["contracts"], [])
            self.assertEqual(ctx["active_contracts"], [])
            self.assertEqual(len(ctx["reconciliation_candidates"]), 4)
            for row in ctx["reconciliation_candidates"]:
                self.assertEqual(row["bucket"], "CONFLICT")
                self.assertEqual(row["reason_code"], "CUSTOMER_NAME_AMBIGUOUS")
                self.assertFalse(row["auto_linked"])
                self.assertFalse(row["portal_grant"])
            dumped = json.dumps(ctx, ensure_ascii=False)
            self.assertNotIn("158765432", dumped)
            self.assertNotIn("41234567", dumped)
            self.assertNotIn("999888777", dumped)

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
