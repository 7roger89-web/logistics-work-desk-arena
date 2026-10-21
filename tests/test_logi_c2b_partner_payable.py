"""LOGI-GOOD C2B — ONE shipment → ONE partner payable → ONE real payment.

Owner journey proven here, on the single existing staging shipment ``LO-0308``
and the single existing partner ``AGT-PHUANH`` (CÔNG TY TNHH PHÚ ANH LOGISTICS,
already in the ``authority_agents`` master):

    EXISTING SHIPMENT
      → ACTUAL COST OWED TO ONE PARTNER (core.logic accrued cost, 57,000,000 VND)
      → PARTNER PAYABLE (canonical financial_obligations)
      → ONE REAL PAYMENT (canonical financial_transactions + financial_allocations)
      → REMAINING PAYABLE (derived, never stored)
      → AUDIT / RBAC
      → FRESH READBACK
      → REOPEN AND SEE THE SAME BUSINESS TRUTH

Every money assertion re-derives the position from the canonical collections
(``core.financial_ledger.shipment_partner_position``) — never from the event
result and never from frontend state.

Semantics preserved (never equated by this slice):
    COST ACTUAL ≠ CASH PAID — the payable obligation is an explicit write.
    PAYABLE ≠ COST          — the obligation references the cost as evidence.
    UNKNOWN ≠ ZERO          — no records ⇒ None; a derived 0 is a true zero.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

# The ONE existing shipment and the ONE existing partner of this slice.
SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
PARTNER_NAME = "CÔNG TY TNHH PHÚ ANH LOGISTICS"
COMPANY = "TT-COMPANY"
CCY = "VND"
ACCRUED_COST = 57_000_000.0  # the seeded actual line's cost (qty 1 × 57,000,000)
PAY_ONE = 20_000_000.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + the deterministic staging actor."""
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


def _position() -> dict:
    """Fresh canonical read of the shipment's partner position."""
    from core.financial_ledger import shipment_partner_position

    return shipment_partner_position(SHIPMENT)


def _partner_view() -> dict:
    """Finance-projection partner block, rebuilt from a fresh database read."""
    return rd.finance_projection(vm.read_shipment(SHIPMENT), {})["partner"]


def _establish_payable(seq_fn, amount: float = ACCRUED_COST, request_id: str = "C2B-TEST-OBL-1"):
    return _dispatch(seq_fn, "partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": request_id,
        "amount": amount, "currency": CCY, "note": "Phải trả cước xe TQ theo chi phí thực tế",
    })


def _pay(seq_fn, request_id: str, amount: float = PAY_ONE, partner: str = PARTNER):
    return _dispatch(seq_fn, "partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": partner, "requestId": request_id,
        "amount": amount, "currency": CCY, "note": "Chuyển khoản thanh toán đối tác",
    })


# ---------------------------------------------------------------------------
# A + B + J — linkage targets exist; nothing established ⇒ UNKNOWN, never 0
# ---------------------------------------------------------------------------

def test_c2b_shipment_and_partner_identity_exist(staging):
    """A/B: the slice uses REAL existing identities only."""
    from core.database import load_authority_agents
    from core.logic import calculate_from_shipment

    ship = vm.read_shipment(SHIPMENT)
    assert ship is not None, "the existing shipment must exist in staging"
    assert ship.get("currency") == CCY
    agents = load_authority_agents() or {}
    agent = agents.get(PARTNER)
    assert agent and rd.text(agent.get("legal_name")) == PARTNER_NAME

    # The accrued cost owed to the partner per the canonical shipment calc.
    assert calculate_from_shipment(ship)["cost"] == ACCRUED_COST


def test_c2b_unknown_stays_unknown_before_any_ledger_record(staging):
    """J: with no obligation/payment records, payable/paid/remaining are UNKNOWN — never 0."""
    position = _position()
    assert position["status"] == "UNKNOWN"
    assert position["payable"] is None and position["paid"] is None and position["remaining"] is None
    view = _partner_view()
    assert view["payable"] is None and view["paid"] is None and view["remaining"] is None
    # Staging authority_agents now carries TWO records: the Trường Thành
    # role-2 partner AND the historical Phú Anh one. The single-partner
    # suggestion is a convenience for a ONE-record catalog only, so with >1
    # catalog partner the projection must not pick one for the operator
    # (never invent a partner).
    assert view["suggested"] is False
    assert view["partnerId"] is None and view["partnerName"] is None
    # The suggestion branch itself is unchanged: with exactly ONE catalog
    # partner it still offers that partner, clearly marked as suggested.
    single = rd._partner_projection(
        SHIPMENT, agents={PARTNER: {"agent_id": PARTNER, "legal_name": PARTNER_NAME}}
    )
    assert single["suggested"] is True and single["partnerId"] == PARTNER
    assert single["partnerName"] == PARTNER_NAME


# ---------------------------------------------------------------------------
# C — accrued cost read from the authoritative backend
# ---------------------------------------------------------------------------

def test_c2b_accrued_cost_is_read_not_assumed(staging):
    from core.logic import calculate_from_shipment

    ship = vm.read_shipment(SHIPMENT)
    summary = calculate_from_shipment(ship)
    assert summary["currency"] == CCY
    assert summary["cost"] == ACCRUED_COST


# ---------------------------------------------------------------------------
# Payable → D…H — record payable, one real payment, fresh readback, idempotency
# ---------------------------------------------------------------------------

def test_c2b_full_payment_journey(staging, event_seq):
    from core.database import load_audit_logs
    from core.financial_ledger import ALLOCATIONS, OBLIGATIONS, TRANSACTIONS

    # --- PARTNER PAYABLE (explicit, evidence-linked; PAYABLE ≠ COST) --------
    out = _establish_payable(event_seq)
    assert out["ok"], out["error"]

    fresh = _position()
    assert fresh["status"] == "CONFIRMED"
    assert fresh["currency"] == CCY and fresh["payable"] == ACCRUED_COST
    # A true derived zero: the obligation exists, nothing allocated yet.
    assert fresh["paid"] == 0.0 and fresh["remaining"] == ACCRUED_COST
    obligation = fresh["obligations"][0]
    # A + B: shipment and partner linkage persisted on the canonical record.
    assert obligation["obligation_id"] == out["obligationId"]
    assert SHIPMENT in obligation["shipment_ids"]
    assert obligation["to_party"]["party_id"] == PARTNER
    assert obligation["from_party"]["party_id"] == COMPANY
    assert obligation["purpose"] == "partner_cost_payable"
    evidence = obligation["evidence_refs"][0]
    assert evidence["accrued_cost"] == ACCRUED_COST and evidence["currency"] == CCY

    # --- ONE REAL PAYMENT ----------------------------------------------------
    pay = _pay(event_seq, "C2B-TEST-PAY-1")
    assert pay["ok"], pay["error"]

    fresh = _position()
    assert fresh["paid"] == PAY_ONE and fresh["remaining"] == ACCRUED_COST - PAY_ONE
    assert fresh["payable"] == ACCRUED_COST and fresh["currency"] == CCY
    payment = fresh["payments"][0]
    assert payment["transaction_id"] == pay["transactionId"]
    assert payment["amount"] == PAY_ONE and payment["currency"] == CCY
    assert payment["holder_party"]["party_id"] == PARTNER
    assert payment["source_party"]["party_id"] == COMPANY
    assert payment["allocated"] == PAY_ONE and payment["unallocated"] == 0.0
    # The allocation binds the payment to the payable obligation.
    group = fresh["partners"][0]
    assert group["obligations"][0]["allocation_ids"], "allocation must exist"
    assert group["obligations"][0]["outstanding"] == ACCRUED_COST - PAY_ONE

    # --- E: event-result-independent fresh readback via the UI projection ---
    view = _partner_view()
    assert view["partnerId"] == PARTNER and view["partnerName"] == PARTNER_NAME
    assert view["currency"] == CCY
    assert view["payable"] == ACCRUED_COST and view["paid"] == PAY_ONE
    assert view["remaining"] == ACCRUED_COST - PAY_ONE
    assert len(view["payments"]) == 1 and view["payments"][0]["requestId"] == "C2B-TEST-PAY-1"

    # --- F: SAME intent replayed ⇒ absorbed, no duplicate financial effect ---
    replay = _pay(event_seq, "C2B-TEST-PAY-1")
    assert replay["ok"], replay["error"]
    assert replay["transactionId"] == pay["transactionId"]
    assert "already applied" in (replay.get("message") or replay.get("error") or "").lower() or \
           replay.get("message") == "financial action already applied"
    fresh = _position()
    assert len(fresh["payments"]) == 1
    assert fresh["paid"] == PAY_ONE and fresh["remaining"] == ACCRUED_COST - PAY_ONE

    # --- G: a NEW genuine intent of the same amount stays DISTINCT ----------
    second = _pay(event_seq, "C2B-TEST-PAY-2")
    assert second["ok"], second["error"]
    assert second["transactionId"] != pay["transactionId"]
    assert second["allocationId"] != pay["allocationId"]
    fresh = _position()
    assert len(fresh["payments"]) == 2
    assert fresh["paid"] == 2 * PAY_ONE
    assert fresh["remaining"] == ACCRUED_COST - 2 * PAY_ONE

    # --- H: remaining payable is exactly right, derived at read time --------
    assert fresh["partners"][0]["totals_by_currency"] == {
        CCY: {"payable": ACCRUED_COST, "paid": 2 * PAY_ONE, "remaining": ACCRUED_COST - 2 * PAY_ONE}
    }

    # --- M: audit evidence exists for every canonical write -----------------
    assert load_audit_logs(OBLIGATIONS, out["obligationId"]), "obligation audit missing"
    assert load_audit_logs(TRANSACTIONS, pay["transactionId"]), "transaction audit missing"
    assert load_audit_logs(ALLOCATIONS, pay["allocationId"]), "allocation audit missing"
    for row in load_audit_logs(TRANSACTIONS, pay["transactionId"]):
        assert row.get("actor") == logi_sandbox.STAGING_ACTOR["username"]


# ---------------------------------------------------------------------------
# I — currency stays explicit; cross-currency is refused, never combined
# ---------------------------------------------------------------------------

def test_c2b_currency_is_explicit_and_never_combined(staging, event_seq):
    _establish_payable(event_seq)

    # A USD payment against a VND payable: the typed event bounds the intent
    # per currency before any write — no record, no FX, no fake balance.
    refused = _dispatch(event_seq, "partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "C2B-TEST-PAY-USD",
        "amount": 100.0, "currency": "USD",
    })
    assert not refused["ok"]
    fresh = _position()
    assert fresh["paid"] == 0.0 and fresh["remaining"] == ACCRUED_COST
    assert set(fresh["totals_by_currency"].get(CCY, {})) == {"payable", "paid", "remaining"}
    assert fresh["currency"] == CCY  # single explicit currency, never a mix


# ---------------------------------------------------------------------------
# Overpay guard — a payment beyond outstanding is refused before any write
# ---------------------------------------------------------------------------

def test_c2b_overpay_is_refused_without_writes(staging, event_seq):
    _establish_payable(event_seq, amount=PAY_ONE, request_id="C2B-TEST-OBL-SMALL")
    refused = _pay(event_seq, "C2B-TEST-PAY-OVER", amount=PAY_ONE + 1)
    assert not refused["ok"]
    assert "vượt" in refused["error"].lower()
    fresh = _position()
    assert fresh["paid"] == 0.0 and len(fresh["payments"]) == 0


def test_c2b_payment_without_open_payable_is_refused(staging, event_seq):
    refused = _pay(event_seq, "C2B-TEST-PAY-NO-OBL")
    assert not refused["ok"]
    # UNKNOWN != ZERO for the untouched shipment-side view as well.
    other = rd.finance_projection(vm.read_shipment("LO-0299"), {})["partner"]
    assert other["payable"] is None and other["paid"] is None and other["remaining"] is None


# ---------------------------------------------------------------------------
# K + L — allowed role writes; denied role fails at the backend boundary
# ---------------------------------------------------------------------------

def test_c2b_allowed_role_writes(staging, event_seq):
    """K: the staging SUPPORT operator holds finance_write and succeeds."""
    import streamlit as st

    assert st.session_state["current_user"]["role"] == "SUPPORT"
    out = _establish_payable(event_seq)
    assert out["ok"], out["error"]


def test_c2b_denied_role_fails_at_backend_boundary(staging, event_seq):
    """L: SALE has no finance_write — the typed event is refused server-side."""
    import streamlit as st

    st.session_state["current_user"] = {
        "username": "minhtu", "full_name": "Minh Tú", "role": "SALE", "user_id": "SALE-MINHTU",
    }
    out = _establish_payable(event_seq)
    assert not out["ok"]
    assert "RBAC" in out["error"] and "finance_write" in out["error"]
    pay = _pay(event_seq, "C2B-TEST-PAY-DENIED")
    assert not pay["ok"] and "RBAC" in pay["error"]

    # No canonical record was created by the denied role.
    from core.database import get_db
    from core.financial_ledger import ALLOCATIONS, OBLIGATIONS, TRANSACTIONS

    db = get_db()
    assert db[OBLIGATIONS].count_documents({}) == 0
    assert db[TRANSACTIONS].count_documents({}) == 0
    assert db[ALLOCATIONS].count_documents({}) == 0


# ---------------------------------------------------------------------------
# N — fresh session reopen shows the same business truth
# ---------------------------------------------------------------------------

def test_c2b_fresh_session_reopen_shows_same_truth(staging, event_seq):
    _establish_payable(event_seq)
    _pay(event_seq, "C2B-TEST-PAY-1")

    before = _position()
    before_view = _partner_view()

    # Simulate a fresh app/session: drop the view-model's cached session state
    # and rebuild every projection from a brand-new database read.
    import streamlit as st

    st.session_state["logi_vm"] = None
    st.session_state["logi_phase_b_session"] = None

    after = _position()
    after_view = _partner_view()
    for key in ("payable", "paid", "remaining", "currency", "status", "partner_key"):
        assert after[key] == before[key], key
    assert [p["transaction_id"] for p in after["payments"]] == \
           [p["transaction_id"] for p in before["payments"]]
    for key in ("partnerId", "partnerName", "payable", "paid", "remaining", "currency"):
        assert after_view[key] == before_view[key], key
    assert after_view["remaining"] == ACCRUED_COST - PAY_ONE


# ---------------------------------------------------------------------------
# UNSUPPORTED-boundary honesty — an unknown partner can never receive money
# ---------------------------------------------------------------------------

def test_c2b_unknown_partner_is_refused(staging, event_seq):
    out = _dispatch(event_seq, "partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": "AGT-DOES-NOT-EXIST",
        "requestId": "C2B-TEST-OBL-GHOST", "amount": 1_000_000, "currency": CCY,
    })
    assert not out["ok"] and "đối tác" in out["error"]
    pay = _pay(event_seq, "C2B-TEST-PAY-GHOST", partner="AGT-DOES-NOT-EXIST")
    assert not pay["ok"] and "đối tác" in pay["error"]
