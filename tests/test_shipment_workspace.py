"""Focused tests for the read-only LOG-C08 Shipment 360 workspace view."""

from __future__ import annotations

import unittest
from copy import deepcopy
from datetime import date

from core.shipment_workspace import UNKNOWN, build_shipment_workspace_view


def _shipment() -> dict:
    return {
        "shipment_id": "LG-001",
        "customer": "Lục Giác",
        "customer_id": "CUS-LG",
        "status": "pending",
        "internal_sale_owner": "SALE Thành",
        "customer_required_date": "2026-08-30",
        "planned_delivery_date": "2026-08-31",
        "info_pending": True,
        "factories": [
            {
                "lot_id": "LG-LOT-01",
                "factory_name": "Nhà máy A",
                "product": "Bộ gá",
                "quantity": 10,
                "factory_ready_date": "2026-08-11",
                "pickup_contact": "Mai",
                "required_information_complete": True,
            },
            {
                "lot_id": "LG-LOT-02",
                "factory_name": "Nhà máy B",
                "product": "Keo công nghiệp",
                "quantity": 20,
                "required_information_complete": False,
            },
        ],
        "data": {
            "0.0": {"created_at": "2026-08-01", "mode": "Sea", "incoterm": "EXW"},
            "1.2": {"pol": "Yantian", "pod": "Cat Lai", "booking_no": "BK-001", "etd": "2026-08-12"},
            "2.4": {"tk_no": "TK-001"},
            "2.6": {"arrival_date": "2026-08-20", "free_time": 7},
            "2.7": {"addr": "Kho Bình Dương", "delivery_date": "2026-08-30"},
            "3.4": {"details": [], "payments": []},
        },
    }


class ShipmentWorkspaceTests(unittest.TestCase):
    def test_builds_action_first_multi_factory_workspace_without_mutation(self) -> None:
        source = _shipment()
        before = deepcopy(source)

        view = build_shipment_workspace_view(source, today=date(2026, 8, 14))

        self.assertEqual(source, before)
        self.assertEqual(view["shipment_id"], "LG-001")
        self.assertEqual(view["customer"], "Lục Giác")
        self.assertEqual(view["operational_status"], "pending")
        self.assertIn("CHƯA", view["financial_status"])
        self.assertEqual(view["next_action"]["code"], "CUSTOMER_DEADLINE_RISK")
        self.assertEqual(len(view["factory_lots"]), 2)
        self.assertEqual(view["factory_lots"][0]["completeness"], "ĐỦ DỮ LIỆU")
        self.assertEqual(view["factory_lots"][1]["completeness"], "CẦN BỔ SUNG")
        self.assertEqual(view["factory_lots_status"], "KNOWN")

    def test_documents_and_timeline_show_known_evidence_without_claiming_completeness(self) -> None:
        view = build_shipment_workspace_view(_shipment(), today=date(2026, 8, 14))

        statuses = {row["document"]: row["status"] for row in view["documents"]}
        self.assertEqual(statuses["Booking / vận đơn"], "CÓ DỮ LIỆU")
        self.assertEqual(statuses["Tờ khai hải quan"], "CÓ DỮ LIỆU")
        self.assertEqual(statuses["Registry chứng từ chuẩn"], UNKNOWN)
        self.assertEqual(view["documents_status"], "PARTIAL")
        self.assertGreaterEqual({row["event"] for row in view["timeline"]}, {"Tạo lô", "ETD", "ETA", "Giao hàng"})
        self.assertEqual(view["history_status"], "KNOWN")

    def test_missing_collections_remain_unknown_and_explicit(self) -> None:
        shipment = _shipment()
        shipment.pop("factories")
        shipment["data"].pop("1.2")
        shipment["data"].pop("2.4")
        shipment["data"]["2.6"] = {}

        view = build_shipment_workspace_view(shipment, today=date(2026, 8, 14))

        self.assertEqual(view["factory_lots"], [])
        self.assertEqual(view["factory_lots_status"], UNKNOWN)
        self.assertEqual(view["documents_status"], UNKNOWN)
        self.assertTrue(any(row["status"] == UNKNOWN for row in view["documents"]))
        self.assertTrue(any(alert["code"] == "MISSING_ETA" for alert in view["alerts"]))

    def test_explicit_document_registry_is_used_as_source(self) -> None:
        shipment = _shipment()
        shipment["documents"] = [
            {"name": "Commercial Invoice", "status": "ĐÃ NHẬN", "step": "Hồ sơ thương mại", "source": "drive://invoice"},
            {"name": "Packing List", "present": False, "required": True},
        ]

        view = build_shipment_workspace_view(shipment, today=date(2026, 8, 14))

        self.assertEqual(view["documents_status"], "KNOWN")
        self.assertEqual(view["documents"][0]["source"], "drive://invoice")
        self.assertEqual(view["documents"][1]["status"], "CHƯA CÓ DỮ LIỆU")


if __name__ == "__main__":
    unittest.main()
