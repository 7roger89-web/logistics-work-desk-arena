"""LOGI-GOOD C2D — global partner-payable worklist (THANH TOÁN ĐỐI TÁC / PHẢI TRẢ).

One Owner-facing global workspace projected over the EXISTING canonical C2B
partner truth. No new ledger, no new accounting model: the read reuses
``core.financial_ledger.shipment_partner_position`` per shipment (flattened to
SHIPMENT × PARTNER × CURRENCY), and the payment action is the SAME canonical
``save_transaction`` + ``allocate_transaction`` path proven in C2B, driven by
the typed ``partner_payment_record`` event.

Proven here, on the isolated staging database (mongomock):

    GLOBAL READ → per shipment × partner × currency payable/paid/remaining
      → multi-partner support
      → multi-currency separation (VND/USD/CNY never summed)
      → UNKNOWN != ZERO (no canonical records ⇒ NO row, never a 0 payable)
      → record one partner payment FROM the global row
      → fresh readback updates the global worklist
      → same-intent idempotency / new-intent distinct
      → cross-currency refusal before mutation
      → overpay guard before mutation
      → RBAC allowed / denied at the backend writer boundary
      → audit evidence

Production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm


SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
PARTNER_NAME = "CÔNG TY TNHH PHÚ ANH LOGISTICS"
CCY = "VND"
ACCRUED_COST = 57_000_000.0
PAY_ONE = 20_000_000.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _worklist() -> dict:
    """The global partner-payable worklist from a freshly built view model."""
    return vm.build_view_model()["payables"]


def _row(shipment_id: str = SHIPMENT, partner_id: str = PARTNER, currency: str = CCY) -> dict:
    return next(
        r for r in _worklist()["rows"]
        if r["shipmentId"] == shipment_id and r["partnerId"] == partner_id and r["currency"] == currency
    )


def _establish_payable(seq_fn, amount: float = ACCRUED_COST, currency: str = CCY,
                       request_id: str = "C2D-TEST-OBL-1"):
    return _dispatch(seq_fn, "partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": request_id,
        "amount": amount, "currency": currency, "note": "Phải trả chi phí đối tác theo thực tế lô",
    })


def _pay(seq_fn, request_id: str, amount: float = PAY_ONE, currency: str = CCY,
         partner: str = PARTNER):
    return _dispatch(seq_fn, "partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": partner, "requestId": request_id,
        "amount": amount, "currency": currency, "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })


# ---------------------------------------------------------------------------
# A — global read is a projection over existing canonical C2B truth
# ---------------------------------------------------------------------------

def test_c2d_global_read_is_empty_without_any_canonical_payable(staging):
    """UNKNOWN != ZERO: with no obligation/payment records the worklist has
    NO row — absence is never reported as a 0 payable."""
    worklist = _worklist()
    assert worklist["rows"] == []
    assert worklist["totals_by_currency"] == {}
    assert worklist["status"] == "UNKNOWN"


def test_c2d_global_read_projects_shipment_partner_currency_rows(staging, event_seq):
    """The global row re-derives the SAME truth as shipment_partner_position."""
    from core.financial_ledger import shipment_partner_position

    out = _establish_payable(event_seq)
    assert out["ok"], out["error"]

    row = _row()
    assert row["partnerId"] == PARTNER
    assert row["partnerName"] == PARTNER_NAME  # resolved from authority_agents master
    assert row["shipmentId"] == SHIPMENT
    assert row["currency"] == CCY
    assert row["payable"] == ACCRUED_COST
    assert row["paid"] == 0.0
    assert row["remaining"] == ACCRUED_COST
    assert row["status"] == "CONFIRMED"
    assert out["obligationId"] in row["obligationIds"]

    # Cross-check against the canonical per-shipment read (not the event).
    position = shipment_partner_position(SHIPMENT)
    totals = position["partners"][0]["totals_by_currency"][CCY]
    assert row["payable"] == totals["payable"]
    assert row["paid"] == totals["paid"]
    assert row["remaining"] == totals["remaining"]


def test_c2d_multi_partner_projection(staging):
    """Two partners on one shipment → two global rows, never merged."""
    from core.database import get_db
    from core.financial_ledger import OBLIGATIONS

    db = get_db()
    db[OBLIGATIONS].insert_one({
        "id": "OBL-C2D-OTHER",
        "record_type": "obligation",
        "from_party": {"party_type": "company", "party_id": "TT-COMPANY", "name": "COMPANY"},
        "from_party_key": "company:TT-COMPANY",
        "to_party": {"party_type": "agent", "party_id": "AGT-OTHER", "name": "Đối tác khác"},
        "to_party_key": "agent:AGT-OTHER",
        "amount": 10_000_000.0,
        "currency": "VND",
        "purpose": "partner_cost_payable",
        "shipment_ids": [SHIPMENT],
        "shipment_id": SHIPMENT,
        "status": "active",
    })
    db[OBLIGATIONS].insert_one({
        "id": "OBL-C2D-PHUANH",
        "record_type": "obligation",
        "from_party": {"party_type": "company", "party_id": "TT-COMPANY", "name": "COMPANY"},
        "from_party_key": "company:TT-COMPANY",
        "to_party": {"party_type": "agent", "party_id": PARTNER, "name": PARTNER_NAME},
        "to_party_key": f"agent:{PARTNER}",
        "amount": ACCRUED_COST,
        "currency": "VND",
        "purpose": "partner_cost_payable",
        "shipment_ids": [SHIPMENT],
        "shipment_id": SHIPMENT,
        "status": "active",
    })

    rows = [r for r in _worklist()["rows"] if r["shipmentId"] == SHIPMENT]
    partner_ids = {r["partnerId"] for r in rows}
    assert {"AGT-OTHER", PARTNER}.issubset(partner_ids)
    assert len(rows) == 2
    # Master-resolved name for the known partner; record-name fallback otherwise.
    phu_anh = next(r for r in rows if r["partnerId"] == PARTNER)
    other = next(r for r in rows if r["partnerId"] == "AGT-OTHER")
    assert phu_anh["partnerName"] == PARTNER_NAME
    assert other["partnerName"] == "Đối tác khác"


# ---------------------------------------------------------------------------
# B — multi-currency separation: never summed together
# ---------------------------------------------------------------------------

def test_c2d_multi_currency_separation(staging, event_seq):
    """VND + USD obligations for the same partner stay two rows + two totals."""
    _establish_payable(event_seq, amount=ACCRUED_COST, currency="VND", request_id="C2D-OBL-VND")
    _establish_payable(event_seq, amount=1_500.0, currency="USD", request_id="C2D-OBL-USD")

    worklist = _worklist()
    vnd = next(r for r in worklist["rows"] if r["currency"] == "VND")
    usd = next(r for r in worklist["rows"] if r["currency"] == "USD")
    assert vnd["payable"] == ACCRUED_COST
    assert usd["payable"] == 1_500.0
    # The two currencies are never combined into a single figure.
    assert vnd["payable"] != usd["payable"]
    assert set(worklist["totals_by_currency"].keys()) == {"VND", "USD"}
    assert "grand_total" not in worklist and "total" not in worklist


# ---------------------------------------------------------------------------
# C — record one partner payment FROM the global row, fresh readback updates
# ---------------------------------------------------------------------------

def test_c2d_payment_from_global_row_updates_fresh_readback(staging, event_seq):
    _establish_payable(event_seq)

    before = _row()
    assert before["remaining"] == ACCRUED_COST

    out = _pay(event_seq, "C2D-TEST-PAY-1")
    assert out["ok"], out["error"]
    assert out["transactionId"] and out["allocationId"]

    # Fresh readback — a rebuilt view model, not the event payload.
    after = _row()
    assert after["paid"] == PAY_ONE
    assert after["remaining"] == ACCRUED_COST - PAY_ONE

    totals = _worklist()["totals_by_currency"][CCY]
    assert totals["paid"] >= PAY_ONE
    assert totals["remaining"] == totals["payable"] - totals["paid"]


# ---------------------------------------------------------------------------
# D — same-intent idempotent, new-intent distinct
# ---------------------------------------------------------------------------

def test_c2d_same_intent_replay_has_no_duplicate_effect(staging, event_seq):
    _establish_payable(event_seq)
    first = _pay(event_seq, "C2D-TEST-IDEM")
    replay = _pay(event_seq, "C2D-TEST-IDEM")
    assert first["ok"] and replay["ok"]
    assert replay["transactionId"] == first["transactionId"]
    assert _row()["paid"] == PAY_ONE


def test_c2d_new_intent_is_a_distinct_payment(staging, event_seq):
    _establish_payable(event_seq)
    a = _pay(event_seq, "C2D-TEST-NEW-1")
    b = _pay(event_seq, "C2D-TEST-NEW-2")
    assert a["ok"] and b["ok"]
    assert a["transactionId"] != b["transactionId"]
    assert a["allocationId"] != b["allocationId"]
    assert _row()["paid"] == 2 * PAY_ONE


# ---------------------------------------------------------------------------
# E — cross-currency refusal + overpay guard, both before mutation
# ---------------------------------------------------------------------------

def test_c2d_cross_currency_payment_is_refused_before_mutation(staging, event_seq):
    _establish_payable(event_seq)
    refused = _pay(event_seq, "C2D-TEST-PAY-USD", amount=100.0, currency="USD")
    assert not refused["ok"]
    row = _row()
    assert row["paid"] == 0.0 and row["remaining"] == ACCRUED_COST


def test_c2d_overpay_is_refused_before_mutation(staging, event_seq):
    _establish_payable(event_seq, amount=PAY_ONE, request_id="C2D-OBL-SMALL")
    refused = _pay(event_seq, "C2D-TEST-PAY-OVER", amount=PAY_ONE + 1)
    assert not refused["ok"]
    assert "vượt" in refused["error"].lower()
    assert _row()["paid"] == 0.0


def test_c2d_payment_without_open_payable_is_refused(staging, event_seq):
    refused = _pay(event_seq, "C2D-TEST-PAY-NO-OBL")
    assert not refused["ok"]


# ---------------------------------------------------------------------------
# F — RBAC at the backend writer boundary + audit
# ---------------------------------------------------------------------------

def test_c2d_allowed_role_records_payment(staging, event_seq):
    import streamlit as st
    from core.auth import can_operate_business

    _establish_payable(event_seq)
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    assert can_operate_business("finance_write") is True
    out = _pay(event_seq, "C2D-TEST-ALLOW")
    assert out["ok"], out["error"]


def test_c2d_denied_role_is_refused_at_the_backend_writer(staging, event_seq):
    import streamlit as st

    _establish_payable(event_seq)
    st.session_state["current_user"] = {
        "username": "minhtu", "full_name": "Minh Tú", "role": "SALE", "user_id": "SALE-MINHTU",
    }
    refused = _pay(event_seq, "C2D-TEST-DENIED")
    assert not refused["ok"]
    assert "RBAC" in refused["error"] and "finance_write" in refused["error"]
    # No canonical transaction/allocation was written by the denied role.
    from core.database import get_db
    from core.financial_ledger import ALLOCATIONS, TRANSACTIONS

    db = get_db()
    assert db[TRANSACTIONS].count_documents({}) == 0
    assert db[ALLOCATIONS].count_documents({}) == 0


def test_c2d_partner_payment_is_audited(staging, event_seq):
    from core.database import load_audit_logs
    from core.financial_ledger import TRANSACTIONS

    _establish_payable(event_seq)
    out = _pay(event_seq, "C2D-TEST-AUDIT")
    assert out["ok"]
    rows = load_audit_logs(TRANSACTIONS, out["transactionId"])
    assert rows, "transaction audit missing"
    assert {row.get("actor") for row in rows} == {logi_sandbox.STAGING_ACTOR["username"]}


# ---------------------------------------------------------------------------
# G — fresh session reopen shows the same business truth
# ---------------------------------------------------------------------------

def test_c2d_fresh_session_reopen_shows_same_truth(staging, event_seq):
    _establish_payable(event_seq)
    _pay(event_seq, "C2D-TEST-PAY-1")

    before = _row()

    import streamlit as st

    st.session_state["logi_vm"] = None
    st.session_state["logi_phase_b_session"] = None

    after = _row()
    for key in ("partnerId", "partnerName", "shipmentId", "currency", "payable", "paid", "remaining", "status"):
        assert after[key] == before[key], key
    assert after["remaining"] == ACCRUED_COST - PAY_ONE
