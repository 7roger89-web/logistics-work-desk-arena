import unittest
from types import SimpleNamespace
from unittest.mock import patch

from views.quotations import ui_sales_module
from core.database import load_quotes, save_quotes_to_cloud
from core.quotations import (
    build_shipment_draft,
    calculate_quote,
    calculate_remittance_estimate,
    new_quote_document,
    prepare_quote_for_persistence,
    transition_quote,
)


class QuotationDomainTests(unittest.TestCase):
    def base(self):
        return {
            "customer_id": "C1",
            "customer_name": "Fixture Customer",
            "sales_owner": "Thành",
            "origin": "China",
            "destination": "Vietnam",
            "incoterm": "EXW",
            "factory_lots": [{"lot_no": 1, "pickup_address": "Fixture pickup"}],
            "fx_snapshot": {"rates_to_vnd": {"USD": 25000, "CNY": 3500, "VND": 1}},
            "service_lines": [{"code": "EXW", "service_name": "China pickup", "qty": 2, "currency": "USD", "cost_unit": 100, "sell_unit": 150, "tax_pct": 0}],
            "entrusted_import": {"active": False},
            "remittance_estimate": {"remitted_amount_usd": 1000, "bank_fee_pct": 0.2, "swift_fee_usd": 5, "receiving_bank_fee_usd": 2, "agent_conversion_fee_usd": 1, "rmb_conversion_fee_cny": 10},
            "include_remittance_in_cost": True,
        }

    def test_multicurrency_explainable_totals(self):
        quote = new_quote_document(self.base())
        self.assertEqual(quote["calculation"]["selling_price_before_tax_vnd"], 7500000)
        self.assertEqual(quote["calculation"]["estimated_cost_vnd"], 5285000)
        self.assertTrue(quote["calculation"]["not_finance_ledger"])
        self.assertEqual(quote["fx_snapshot"]["rates_to_vnd"]["USD"], 25000.0)

    def test_entrusted_value_without_threshold_does_not_force_review(self):
        payload = self.base()
        payload["entrusted_import"] = {"active": True, "goods_value": 20000, "goods_currency": "USD", "rate_pct": 2.5}
        quote = new_quote_document(payload)
        fee = quote["fees"]["entrusted_import"]
        self.assertFalse(fee["commercial_review_required"])
        self.assertEqual(fee["high_value_threshold_status"], "POLICY_NOT_CONFIGURED")
        self.assertIsNone(fee["high_value_threshold"])
        self.assertEqual(fee["amount_vnd"], 12500000)

    def test_entrusted_rate_outside_reference_range_requires_review(self):
        payload = self.base()
        payload["entrusted_import"] = {"active": True, "goods_value": 20000, "goods_currency": "USD", "rate_pct": 3.5}
        quote = new_quote_document(payload)
        fee = quote["fees"]["entrusted_import"]
        self.assertTrue(fee["commercial_review_required"])
        self.assertIn("ngoài khoảng", fee["commercial_review_reasons"][0])

    def test_explicit_review_and_configured_policy_require_review(self):
        payload = self.base()
        payload["entrusted_import"] = {"active": True, "goods_value": 20000, "goods_currency": "USD", "rate_pct": 2.5, "review_requested": True, "review_reason": "Manager yêu cầu kiểm tra biên lợi nhuận.", "high_value_review_policy": {"threshold": 15000, "currency": "USD", "reason": "Policy thương mại đã cấu hình."}}
        quote = new_quote_document(payload)
        fee = quote["fees"]["entrusted_import"]
        self.assertTrue(fee["commercial_review_required"])
        self.assertEqual(fee["high_value_threshold_status"], "CONFIGURED")
        self.assertEqual(fee["high_value_threshold"], 15000.0)
        self.assertEqual(len(fee["commercial_review_reasons"]), 2)

    def test_remittance_formula(self):
        result = calculate_remittance_estimate(self.base()["remittance_estimate"], self.base()["fx_snapshot"])
        self.assertEqual(result["bank_fee_usd"], 2.0)
        self.assertEqual(result["estimated_total_usd"], 10.0)
        self.assertEqual(result["estimated_total_vnd"], 285000.0)

    def test_persistence_stamp_is_stable_and_estimate_only(self):
        quote = new_quote_document(self.base())
        first = prepare_quote_for_persistence(quote, actor="sale-a")
        second = prepare_quote_for_persistence(quote, actor="sale-a")
        self.assertEqual(first["write_request_id"], second["write_request_id"])
        self.assertEqual(first["write_request_id"], f"quote:{quote['id']}:v1")
        self.assertTrue(first["provenance"]["estimate_only"])
        self.assertFalse(first["ledger_posted"])

    def test_quote_persistence_isolated_and_finance_free(self):
        class FakeCollection:
            def __init__(self):
                self.docs = {}
            def find_one(self, query, projection=None, **kwargs):
                del projection, kwargs
                return self.docs.get(query.get("id"))
            def update_one(self, query, update, upsert=False, session=None):
                key = query["id"]
                payload = dict(update["$set"])
                self.docs[key] = payload
                return object()
            def find(self, query, projection=None):
                return list(self.docs.values())
            def insert_one(self, document, session=None):
                self.docs[str(document.get("event_id", len(self.docs)))] = dict(document)
                return object()

        class FakeDb:
            def __init__(self):
                self.collections = {"quotes": FakeCollection()}
                self.audit_logs = FakeCollection()
                self.accessed = []
            def __getitem__(self, name):
                self.accessed.append(name)
                return self.collections[name]

        fake_db = FakeDb()
        quote = prepare_quote_for_persistence(new_quote_document(self.base()), actor="sale-a")
        sale_user = {
            "user_id": "sale-fixture-01",
            "username": "sale.fixture",
            "display_name": "Sale Fixture",
            "role": "sale",
        }
        with patch("core.auth.st", new=SimpleNamespace(session_state={"current_user": sale_user})), \
             patch("core.database.get_db", return_value=fake_db):
            self.assertTrue(save_quotes_to_cloud({quote["id"]: quote}))
            self.assertTrue(save_quotes_to_cloud({quote["id"]: quote}))
            readback = load_quotes()
        self.assertGreaterEqual(fake_db.accessed.count("quotes"), 2)
        self.assertEqual(len(fake_db.collections["quotes"].docs), 1)
        self.assertIn(quote["id"], readback)
        self.assertEqual(readback[quote["id"]]["write_request_id"], quote["write_request_id"])
        self.assertNotIn("financial_transactions", fake_db.accessed)
        self.assertNotIn("financial_obligations", fake_db.accessed)

    def test_lifecycle_and_shipment_mapping(self):
        quote = new_quote_document(self.base())
        quote = transition_quote(quote, "READY_FOR_REVIEW", "sale")
        quote = transition_quote(quote, "ACCEPTED", "sale")
        quote = transition_quote(quote, "READY_TO_CREATE_SHIPMENT", "sale")
        draft = build_shipment_draft(quote, "SHP-FIXTURE-001")
        self.assertEqual(draft["quote_reference"], quote["quote_no"])
        self.assertEqual(draft["customer_id"], "C1")
        self.assertTrue(draft["commercial_estimate"]["not_finance_ledger"])
        self.assertEqual(draft["data"]["3.4"]["payments"], [])


if __name__ == "__main__":
    unittest.main()
