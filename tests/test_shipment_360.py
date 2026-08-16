import unittest
from copy import deepcopy

from core.shipment_360 import UNKNOWN, build_shipment_360_summary


def _shipment(**finance):
    return {
        "shipment_id": "S-360-001",
        "id": "S-360-001",
        "customer": "Lục Giác",
        "currency": "VND",
        "status": "done",
        "data": {
            "0.0": {"st": "done"},
            "2.4": {"gnt": {"ds_thue": []}},
            "3.4": finance,
        },
    }


class Shipment360Tests(unittest.TestCase):
    def test_reuses_customer_calculation_and_does_not_call_cost_payable(self):
        shipment = _shipment(
            details=[{"qty": 2, "price": 100, "cost": 60, "vat_line": 10}],
            commission={"total": 10},
            payments=[{"id": "PAY-1", "amount": 100, "date": "2026-08-14"}],
        )

        view = build_shipment_360_summary(shipment)

        self.assertEqual(view["receivable"]["total"]["value"], 220.0)
        self.assertEqual(view["receivable"]["collected"]["value"], 100.0)
        self.assertEqual(view["receivable"]["outstanding"]["value"], 120.0)
        self.assertEqual(view["known_cost"]["value"], 120.0)
        self.assertIn("payable", view)
        self.assertEqual(view["payable"]["total"]["status"], UNKNOWN)
        self.assertEqual(view["financial_status"], "CHỜ THU")
        self.assertTrue(view["closure_status"].startswith("CHƯA THỂ TẤT TOÁN"))
        self.assertEqual(view["payments"][0]["allocation_status"], UNKNOWN)
        self.assertTrue(view["read_only"])

    def test_keeps_agency_scope_tax_and_fx_relationships_explicit(self):
        shipment = _shipment(
            details=[{"qty": 1, "price": 1000, "cost": 500, "vat_line": 0}],
            commission={"total": 0},
            payments=[],
            agency={"fee_vnd": 1000, "collected_vnd": 200, "paid_vnd": 300},
        )
        shipment["contract_id"] = "CON-001"
        shipment["data"]["2.4"]["gnt"]["ds_thue"] = [
            {"ten": "VAT", "ndkt": "1701", "tien": 20},
            {"ten": "Tờ khai", "ndkt": "1702", "tien": 30},
        ]
        proxy = {
            "PX-1": {
                "id": "PX-1",
                "linked_id": "CON-001",
                "contract_id": "CON-001",
                "amount_vnd": 1500000,
                "amount_fc_needed": 62.464,
                "amount_fc_paid": 20.0,
                "amount_fc_remain": 42.464,
                "currency": "RMB",
                "exchange_rate": 3500,
                "created_at": "2026-08-14T10:00:00",
                "beneficiary": "A Bò",
            }
        }
        entrustments = {
            "W-1": {
                "id": "W-1",
                "linked_type": "Hợp đồng",
                "linked_id": "CON-001",
                "deposits": [{"Số tiền (VND)": 1000000}],
                "payments": [
                    {
                        "Loại Tiền": "CNY",
                        "Số Tiền Ngoại Tệ": 62.464,
                        "Tỷ giá Báo Khách": 3600,
                        "Tỷ giá Thực Tế": 3500,
                    }
                ],
            }
        }

        view = build_shipment_360_summary(shipment, proxy_payments=proxy, entrustments=entrustments)

        self.assertTrue(view["payable"]["known"])
        self.assertEqual(view["payable"]["total"]["value"], 1000.0)
        self.assertEqual(view["payable"]["settled"]["value"], 500.0)
        self.assertEqual(view["payable"]["outstanding"]["value"], 500.0)
        self.assertEqual(view["tax"]["value"], 50.0)
        self.assertEqual(view["tax"]["status"], "KNOWN")
        proxy_row = next(row for row in view["relationships"] if row["type"] == "proxy_payment")
        self.assertEqual(proxy_row["original_amount"], 62.464)
        self.assertEqual(proxy_row["exchange_rate"], 3500.0)
        self.assertEqual(proxy_row["original_currency"], "RMB")
        wallet_row = next(row for row in view["relationships"] if row["type"] == "entrustment")
        self.assertEqual(wallet_row["payment_legs"][0]["reported_rate"], 3600.0)
        self.assertEqual(wallet_row["payment_legs"][0]["actual_rate"], 3500.0)
        self.assertTrue(any(row["type"] == "contract" and row["id"] == "CON-001" for row in view["relationships"]))

    def test_preserves_unknowns_and_does_not_mutate_input(self):
        shipment = _shipment(
            details=[],
            payments=[],
            unallocated_amount=12,
        )
        before = deepcopy(shipment)

        view = build_shipment_360_summary(shipment)

        self.assertEqual(shipment, before)
        self.assertEqual(view["unallocated"]["status"], "KNOWN")
        self.assertEqual(view["unallocated"]["value"], 12.0)
        self.assertEqual(view["unreconciled"]["status"], UNKNOWN)
        self.assertEqual(view["actual_profit"]["status"], UNKNOWN)
        self.assertEqual(view["payable"]["total"]["status"], UNKNOWN)
        self.assertEqual(view["financial_status"], "CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU")


if __name__ == "__main__":
    unittest.main()
