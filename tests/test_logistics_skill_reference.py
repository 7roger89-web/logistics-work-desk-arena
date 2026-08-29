"""Focused fixture and behavior tests for the pure LOG-SKILL01 references."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from skills.logistics.reference.intake import normalize_customer_intake
from skills.logistics.reference.payment import assess_commercial_consistency, calculate_payment_scenario
from skills.logistics.reference.quote import build_quote
from skills.logistics.reference.sales import OBJECTION_LIBRARY, build_sales_response


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "skills" / "logistics" / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class LogisticsReferenceTests(unittest.TestCase):
    def test_simple_shipment_intake_is_ready_and_source_preserving(self) -> None:
        fixture = load_fixture("simple_shipment.json")
        original = copy.deepcopy(fixture)
        result = normalize_customer_intake(fixture)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["customer"]["company"], "An Phat Import Co.")
        self.assertEqual(result["cargo"]["cbm"], 3.84)
        self.assertEqual(len(result["factory_lots"]), 1)
        self.assertFalse(result["authority"]["customer_message_verified"])
        self.assertEqual(fixture, original)

    def test_incomplete_intake_returns_explicit_missing_input(self) -> None:
        result = normalize_customer_intake(load_fixture("incomplete_customer_message.json"))
        self.assertEqual(result["status"], "NEEDS_CUSTOMER_INPUT")
        self.assertEqual(
            set(result["missing_information"]),
            {
                "shipment.incoterm",
                "cargo.cbm",
                "factory_lots[0].pickup_address",
            },
        )
        self.assertEqual(result["shipment"]["incoterm"], "UNKNOWN")
        self.assertEqual(result["cargo"]["cbm"], "UNKNOWN")
        self.assertEqual(result["factory_lots"][0]["pickup_address"], "UNKNOWN")

    def test_multiple_factory_lots_remain_separate(self) -> None:
        fixture = load_fixture("simple_shipment.json")
        fixture["factory_lots"].append(
            {
                "factory_name": "Shenzhen Second Factory",
                "pickup_address": "Bao'an, Shenzhen, China",
                "contact": "Chen Yu",
                "phone": "+86 138 0000 2222",
                "cargo_ready_date": "2026-09-02",
            }
        )
        result = normalize_customer_intake(fixture)
        self.assertEqual(result["status"], "READY")
        self.assertEqual([lot["factory_name"] for lot in result["factory_lots"]], [
            "Guangzhou Bright Factory",
            "Shenzhen Second Factory",
        ])

    def test_usd_payment_is_decimal_and_traceable(self) -> None:
        result = calculate_payment_scenario(
            {
                "scenario": "A",
                "invoice_amount_usd": 10000,
                "bank_service_fee_usd": 10,
                "wire_fee_usd": 20,
                "bank_conversion_fee_vnd": 250000,
                "fx_snapshot": {
                    "usd_to_vnd": 25000,
                    "captured_at": "2026-08-29T09:00:00+07:00",
                    "source": "manual:bank-quote",
                },
                "fee_sources": {
                    "bank_service_fee_usd": "manual:bank-fee",
                    "wire_fee_usd": "manual:wire-fee",
                    "bank_conversion_fee_vnd": "manual:conversion-fee",
                },
            }
        )
        self.assertEqual(result["status"], "CALCULATED")
        self.assertEqual(result["amounts"]["received_usd"], "9960.00")
        self.assertEqual(result["amounts"]["received_vnd"], "249000000.00")
        self.assertEqual(
            [entry["stage"] for entry in result["calculation_trace"]],
            ["INPUT", "RATE", "FEE", "INTERMEDIATE_AMOUNT", "FINAL_AMOUNT"],
        )
        self.assertIsNone(result["payment_instruction"])

    def test_rmb_payment_fixture_is_deterministic(self) -> None:
        result = calculate_payment_scenario(load_fixture("rmb_factory.json"))
        self.assertEqual(result["status"], "CALCULATED")
        self.assertEqual(result["amounts"]["net_usd"], "11965.00")
        self.assertEqual(result["amounts"]["gross_rmb"], "85190.80")
        self.assertEqual(result["amounts"]["received_rmb"], "85070.80")
        self.assertEqual(
            [entry["stage"] for entry in result["calculation_trace"]],
            ["INPUT", "RATE", "FEE", "INTERMEDIATE_AMOUNT", "FINAL_AMOUNT"],
        )
        self.assertTrue(result["authority"]["authorized_flow_confirmed"])
        self.assertIsNone(result["payment_instruction"])

    def test_missing_fx_does_not_become_an_estimate(self) -> None:
        payload = {
            "scenario": "A",
            "invoice_amount_usd": 10000,
            "bank_service_fee_usd": 10,
            "wire_fee_usd": 20,
            "bank_conversion_fee_vnd": 250000,
            "fee_sources": {
                "bank_service_fee_usd": "manual:bank-fee",
                "wire_fee_usd": "manual:wire-fee",
                "bank_conversion_fee_vnd": "manual:conversion-fee",
            },
        }
        result = calculate_payment_scenario(payload)
        self.assertEqual(result["status"], "NEEDS_CUSTOMER_INPUT")
        self.assertEqual(result["calculation_trace"], [])
        self.assertEqual(result["amounts"], {})
        self.assertTrue(any(path.startswith("fx_snapshot") for path in result["missing_information"]))

    def test_commercial_discrepancy_fails_closed(self) -> None:
        result = calculate_payment_scenario(load_fixture("compliance_discrepancy.json"))
        self.assertEqual(result["status"], "COMPLIANCE_REVIEW_REQUIRED")
        self.assertEqual(result["calculation_trace"], [])
        self.assertIsNone(result["payment_instruction"])
        self.assertIsNone(result["compliance_review"]["evasion_guidance"])
        self.assertTrue(result["compliance_review"]["required_documents"])
        assessment = assess_commercial_consistency(
            {"invoice": {"amount": 100, "currency": "USD"}, "payment": {"amount": 90, "currency": "USD"}}
        )
        self.assertEqual(assessment["status"], "COMPLIANCE_REVIEW_REQUIRED")

    def test_complete_quote_labels_costs_and_keeps_advice_separate(self) -> None:
        request = load_fixture("simple_shipment.json")["quote_request"]
        original = copy.deepcopy(request)
        result = build_quote(request)
        self.assertEqual(result["status"], "READY_FOR_REVIEW")
        self.assertEqual(result["cost_basis"]["known_cost_vnd"], "10300000.00")
        self.assertEqual(result["cost_basis"]["estimated_cost_vnd"], "1200000.00")
        self.assertEqual(result["cost_basis"]["total_cost_vnd"], "11500000.00")
        self.assertEqual(result["selling_price"]["total"], "14000000.00")
        self.assertIn("KNOWN_COST", result["cost_basis"]["labels"])
        self.assertIn("ESTIMATED_COST", result["cost_basis"]["labels"])
        self.assertIn("ASSUMPTION", result["cost_basis"]["labels"])
        self.assertEqual(result["pricing_advice"]["used_in_cost_calculation"], False)
        self.assertFalse(result["authority"]["quote_is_invoice"])
        self.assertFalse(result["authority"]["quote_is_customs_declaration"])
        self.assertEqual(request, original)

    def test_quote_missing_freight_source_and_fx_is_incomplete(self) -> None:
        result = build_quote(
            {
                "quote_id": "LOG-Q-INCOMPLETE",
                "version": 1,
                "customer": "Demo Importer",
                "route": {"origin": "China", "destination": "Vietnam"},
                "shipment_summary": {"goods": "unknown"},
                "currency": "USD",
                "service_lines": [
                    {
                        "line_id": "freight",
                        "description": "Road freight",
                        "cost_type": "freight",
                        "quantity": 1,
                        "unit_cost": 999999,
                        "currency": "USD",
                    }
                ],
                "valid_until": "2026-09-05",
                "pricing_strategy_advice": {"suggested_price": 999999999},
            }
        )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["service_lines"][0]["cost_status"], "UNKNOWN_COST")
        self.assertEqual(result["cost_basis"]["total_cost_vnd"], "UNKNOWN")
        self.assertEqual(result["selling_price"]["total"], "UNKNOWN")
        self.assertIn("service_lines[0].cost_source_or_manual_input", result["missing_information"])
        self.assertTrue(any(path.startswith("fx_snapshot") for path in result["missing_information"]))
        self.assertEqual(result["pricing_advice"]["used_in_cost_calculation"], False)
        self.assertNotIn("999999999", json.dumps(result["cost_basis"], ensure_ascii=False))

    def test_sales_output_covers_objections_and_is_human_review_only(self) -> None:
        expected = {
            "price_higher",
            "competitor_cheaper",
            "delivery_time",
            "customs_clearance",
            "delay",
            "why_information",
            "factory_rmb",
            "not_ready",
        }
        self.assertEqual(set(OBJECTION_LIBRARY), expected)
        forbidden_promises = ("đảm bảo thông quan", "guaranteed customs", "100% thông quan", "đảm bảo thời gian")
        for key in expected:
            result = build_sales_response(key)
            self.assertEqual(result["status"], "READY_FOR_REVIEW")
            self.assertFalse(result["can_send"])
            self.assertTrue(result["human_review_required"])
            self.assertIn("sales_handoff", result)
            self.assertIn("next_action", result)
            reply = result["reply_draft"].lower()
            self.assertFalse(any(text in reply for text in forbidden_promises), key)

    def test_sales_fact_layer_requires_verification_and_source(self) -> None:
        result = build_sales_response(
            "delivery_time",
            {
                "cargo_ready_date": {"value": "2026-09-01", "verified": True, "source": "customer-doc-1"},
                "border_condition": {"value": "open", "verified": False, "source": "unreviewed-message"},
                "unsupported_claim": "fast",
            },
        )
        facts = result["content_layers"]["facts"]
        assumptions = result["content_layers"]["assumptions"]
        self.assertEqual([fact["key"] for fact in facts], ["cargo_ready_date"])
        self.assertTrue(any(item["key"] == "border_condition" for item in assumptions))
        self.assertTrue(any(item["key"] == "unsupported_claim" for item in assumptions))
        self.assertFalse(result["authority"]["delivery_time_promised"])


if __name__ == "__main__":
    unittest.main()
