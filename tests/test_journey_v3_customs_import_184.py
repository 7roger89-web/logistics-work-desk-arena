"""Issue #184 — Journey V3 Customs Import product slice truth boundaries.

Focused regression coverage for the smallest seams this slice touches:

A. declaration registration != customs clearance
B. G08 — empty finance book stays UNKNOWN (never a manufactured 0)
C. G06 — multi-partner ledger groups both survive the shipment projection
D. G09 — a past ETD without ATD is not consumed as actual movement
E. upload != business completion (attachments never flip completion facts)
F. exactly one authoritative primary action

Pure-projection tests: no DB, no network, no Streamlit session.
"""
from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from core.shipment_journey import build_journey
from views import logi_real_data as rd


def _obligation(oid: str, party_id: str, party_name: str, amount: float, ccy: str, sid: str) -> dict:
    return {
        "id": oid,
        "to_party": {"party_id": party_id, "name": party_name},
        "to_party_key": party_id,
        "shipment_ids": [sid],
        "amount": amount,
        "currency": ccy,
        "status": "CONFIRMED",
        "allocated": 0.0,
        "outstanding": amount,
        "allocation_ids": [],
        "created_at": "2026-10-01",
        "purpose": "agent fee",
    }


def _ledger(sid: str, obligations: list) -> dict:
    return {
        "financial_obligations": obligations,
        "financial_transactions": [],
        "financial_allocations": [],
    }


def _sea_profile() -> dict:
    return {
        "mode": "SEA",
        "stages": [
            {"code": "MAIN_CARRIAGE", "label": "Chặng chính", "reason": "SERVICE_SCOPE"},
            {"code": "SEA_DOCUMENTS", "label": "CT sea", "reason": "SERVICE_SCOPE"},
            {"code": "IMPORT_CUSTOMS", "label": "HQ nhập", "reason": "SERVICE_SCOPE"},
        ],
        "serviceScope": ["MAIN_CARRIAGE", "SEA_DOCUMENTS", "IMPORT_CUSTOMS"],
        "serviceScopeConfirmed": True,
    }


def _journey(shipment: dict, operational: dict) -> dict:
    return build_journey(
        shipment, profile=_sea_profile(), operational=operational,
        primary={}, dashboard={}, attachments=[],
    )


class DeclarationNotClearanceTest(unittest.TestCase):
    def test_tk_registered_without_clearance_is_not_done(self):
        shipment = {"id": "T184-A1", "data": {
            "2.4": {"tk_no": "106598723450", "customs_status": False, "clearance_date": ""},
            "1.2": {}, "2.7": {}}}
        node = next(n for n in _journey(shipment, {"main_leg": {}, "pickup_leg": {}})["nodes"]
                    if n["id"] == "customs-import")
        self.assertFalse(node["completed"])
        self.assertIn("106598723450", node["evidence"])

    def test_explicit_clearance_marks_done(self):
        shipment = {"id": "T184-A2", "data": {
            "2.4": {"tk_no": "106598723450", "customs_status": True, "clearance_date": "2026-10-05"},
            "1.2": {}, "2.7": {}}}
        node = next(n for n in _journey(shipment, {"main_leg": {}, "pickup_leg": {}})["nodes"]
                    if n["id"] == "customs-import")
        self.assertTrue(node["completed"])


class UnknownFinanceTest(unittest.TestCase):
    def test_empty_book_stays_unknown(self):
        fin = rd.finance_projection({"id": "T184-B1", "data": {"3.4": {"details": [], "payments": []}}}, {})
        for key in ("receivable", "receivableNet", "outputVat", "outstanding", "payable"):
            self.assertIsNone(fin[key], f"{key} must be UNKNOWN, not 0")
        # B2 (Issue #184 repair): `received` is payment-derived, not
        # line-derived — a genuine zero when no payment exists, never
        # UNKNOWN merely because the payments list is empty.
        # UNKNOWN book != settled balance.
        self.assertEqual(fin["received"], 0.0)
        self.assertFalse(fin["hasActualLines"])

    def test_booked_lines_keep_real_numbers(self):
        fin = rd.finance_projection({"id": "T184-B2", "data": {"3.4": {"details": [
            {"id": "l1", "display_name": "Cước biển", "price": 10000000,
             "cost": 8000000, "qty": 1, "vat": 10},
        ], "payments": []}}}, {})
        self.assertEqual(fin["receivable"], 11000000.0)
        self.assertEqual(fin["payable"], 8000000.0)
        # No payment records -> received is a genuine zero (receivables_projection contract).
        self.assertEqual(fin["received"], 0.0)

    def test_payment_records_make_received_known(self):
        fin = rd.finance_projection({"id": "T184-B3", "data": {"3.4": {
            "details": [],
            "payments": [{"id": "p1", "amount": 5000000, "date": "2026-10-01"}],
        }}}, {})
        self.assertEqual(fin["received"], 5000000.0)
        # ...but line-derived money is still UNKNOWN without booked lines.
        self.assertIsNone(fin["receivable"])

    def test_reversed_only_payment_keeps_received_zero(self):
        # B2: `received` is the NON-REVERSED receipt total — a reversed-only
        # book reads a genuine zero, never the reversed amount, never UNKNOWN.
        fin = rd.finance_projection({"id": "T184-B4", "data": {"3.4": {
            "details": [],
            "payments": [{"id": "p1", "amount": 5000000, "date": "2026-10-01",
                          "status": "reversed"}],
        }}}, {})
        self.assertEqual(fin["received"], 0.0)
        self.assertIsNone(fin["receivable"])


class MultiPartnerTest(unittest.TestCase):
    def test_two_partner_groups_both_survive(self):
        sid = "T184-C1"
        proj = rd._partner_projection(sid, ledger=_ledger(sid, [
            _obligation("ob1", "china-agent", "China Agent", 84000, "CNY", sid),
            _obligation("ob2", "phu-anh", "Phú Anh", 50000000, "VND", sid),
        ]), agents={})
        groups = proj.get("partners") or []
        self.assertEqual(sorted(g["partnerName"] for g in groups), ["China Agent", "Phú Anh"])
        # No arbitrary "main partner" is selected for the convenience fields.
        self.assertFalse(proj.get("partnerName"))
        by_name = {g["partnerName"]: g for g in groups}
        self.assertEqual(by_name["China Agent"]["totalsByCurrency"]["CNY"]["payable"], 84000.0)
        self.assertEqual(by_name["Phú Anh"]["totalsByCurrency"]["VND"]["payable"], 50000000.0)
        # Currencies are never combined across groups.
        self.assertNotIn("VND", by_name["China Agent"]["totalsByCurrency"])
        self.assertNotIn("CNY", by_name["Phú Anh"]["totalsByCurrency"])

    def test_single_partner_convenience_unchanged(self):
        sid = "T184-C2"
        proj = rd._partner_projection(sid, ledger=_ledger(sid, [
            _obligation("ob1", "china-agent", "China Agent", 84000, "CNY", sid),
        ]), agents={})
        self.assertEqual(proj.get("partnerName"), "China Agent")
        self.assertEqual(proj.get("payable"), 84000.0)

    def test_no_records_stays_unknown(self):
        proj = rd._partner_projection("T184-C3", ledger=_ledger("T184-C3", []), agents={})
        self.assertIsNone(proj.get("payable"))


class ScheduleVsActualTest(unittest.TestCase):
    def _operational(self, **kw) -> dict:
        main = {"etd": "2026-09-01", "eta": "2026-09-20", "atd": "", "ata": "", "booking_no": "BK1"}
        main.update(kw)
        return {"main_leg": main, "pickup_leg": {}}

    def test_past_etd_without_atd_is_not_movement(self):
        by_id = {n["id"]: n for n in _journey(
            {"id": "T184-D1", "data": {"2.4": {}, "1.2": {}, "2.7": {}}},
            self._operational())["nodes"]}
        self.assertFalse(by_id["transit"]["completed"])
        self.assertFalse(by_id["etd"]["completed"])
        self.assertNotIn("ATD", by_id["transit"]["evidence"])

    def test_atd_present_makes_transit_current(self):
        journey = _journey(
            {"id": "T184-D2", "data": {"2.4": {}, "1.2": {}, "2.7": {}}},
            self._operational(atd="2026-09-02"))
        self.assertEqual(journey.get("currentStageId"), "transit")


class UploadNotCompletionTest(unittest.TestCase):
    def test_customs_attachment_does_not_complete_import(self):
        shipment = {"id": "T184-E1", "data": {
            "2.4": {"tk_no": "106598723450", "customs_status": False, "clearance_date": ""},
            "1.2": {}, "2.7": {}}}
        attachments = [{"id": "a1", "category": "customs", "file_name": "hoa-don-phu-anh.pdf"}]
        journey = build_journey(
            shipment, profile=_sea_profile(),
            operational={"main_leg": {}, "pickup_leg": {}},
            primary={}, dashboard={}, attachments=attachments)
        node = next(n for n in journey["nodes"] if n["id"] == "customs-import")
        self.assertFalse(node["completed"])
        self.assertIn("a1", node["documentIds"])


class SinglePrimaryActionTest(unittest.TestCase):
    def test_exactly_one_primary_action_shape(self):
        action = rd.compose_primary_action(
            shipment_id="T184-F1", dashboard={}, execution_profile={},
            status_tab="nhap")
        self.assertIsInstance(action, dict)
        self.assertEqual(set(action.keys()), {"text", "detail", "priority", "route"})
        self.assertTrue(action["text"])

    def test_critical_dashboard_action_wins(self):
        action = rd.compose_primary_action(
            shipment_id="T184-F2",
            dashboard={"top_alert": {"severity": "critical", "label": "Thiếu chứng từ",
                                    "detail": "Còn thiếu 2 tệp"}},
            execution_profile={}, status_tab="nhap")
        self.assertEqual(action["priority"], "Khan")
        self.assertIn("Thiếu chứng từ", action["text"])


class SuggestedPartnerTest(unittest.TestCase):
    """B6 (Issue #184 repair) — a catalog suggestion must not look canonical.

    Single catalog authority-agent + zero ledger partner groups =>
    suggested=True, name from the catalog, money stays UNKNOWN (no payable
    is invented from the catalog). The Quick Panel must render it visibly
    qualified, never as an established partner debt.
    """

    def test_catalog_suggestion_stays_qualified(self):
        sid = "T184-G1"
        proj = rd._partner_projection(
            sid,
            ledger=_ledger(sid, []),
            agents={"a1": {"agent_id": "agent-1", "legal_name": "Đại lý Gợi ý"}},
        )
        self.assertTrue(proj.get("suggested"))
        self.assertEqual(proj.get("partnerName"), "Đại lý Gợi ý")
        # No obligation is inferred from the catalog.
        self.assertIsNone(proj.get("payable"))
        self.assertIsNone(proj.get("paid"))
        self.assertIsNone(proj.get("remaining"))
        self.assertIsNone(proj.get("currency"))
        self.assertFalse(proj.get("partners"))

    def test_panel_qualifies_suggested_partner(self):
        # UI seam pin: the qualified block is keyed on partner.suggested and
        # carries the canonical "đề xuất từ danh mục" wording.
        src = (Path(__file__).resolve().parent.parent
               / "component" / "src" / "components" / "ShipmentJourney.tsx").read_text(encoding="utf-8")
        self.assertIn("ci-partner-suggested", src)
        self.assertIn("partner.suggested", src)
        self.assertIn("Đề xuất từ danh mục", src)
        self.assertIn("chưa xác nhận đối tác phải trả", src)


if __name__ == "__main__":
    unittest.main()
