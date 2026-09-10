"""LOGI-GOOD C2C — global customer-receivable worklist (Owner slice).

One Owner-facing "THU TIỀN KHÁCH / PHẢI THU" workspace projected over the
EXISTING shipment/customer/finance truth. No new ledger, no new accounting
model: the read is ``views.logi_real_data.receivables_projection`` over the
same ``core.logic`` snapshot every other page already reads, and the receipt
action is the SAME canonical ``save_direct_shipment_payment`` writer (request
identity) proven in C2A.

Proven here, on the isolated staging database (mongomock):

    GLOBAL READ → per-shipment receivable/received/outstanding
      → multi-currency separation (VND/USD/CNY never summed)
      → UNKNOWN != ZERO (no actual lines ⇒ receivable is not 0)
      → Quote Estimate never used as actual receivable
      → record one receipt from the workspace (same payment writer)
      → fresh readback updates the worklist
      → same-intent idempotency / new-intent distinct
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
    """The global receivable worklist from a freshly built view model."""
    return vm.build_view_model()["receivables"]


def _row(shipment_id: str = SHIPMENT) -> dict:
    return next(r for r in _worklist()["rows"] if r["id"] == shipment_id)


# ---------------------------------------------------------------------------
# A + B + C — global read is a projection over existing shipment/customer/finance truth
# ---------------------------------------------------------------------------

def test_c2c_global_read_projects_multiple_existing_shipments(staging):
    """Multiple existing shipments are projected, one row each, from real truth."""
    from core.logic import calculate_from_shipment

    worklist = _worklist()
    assert len(worklist["rows"]) >= 2, "at least multiple existing shipments projected"

    for row in worklist["rows"]:
        ship = vm.read_shipment(row["id"])
        assert ship is not None
        summary = calculate_from_shipment(ship)
        assert row["receivable"] == summary["receivable"]
        assert row["received"] == summary["paid"]
        assert row["outstanding"] == summary["debt"]
        assert row["customer"], "customer must come from real customer truth"
        # currency carried per row, never converted
        assert row["currency"] == summary["currency"]


def test_c2c_per_currency_totals_are_grouped_and_never_summed_across_currencies(staging):
    """VND / USD / CNY totals stay separate — no FX engine, no grand total."""
    rows = [
        {"id": "A", "customer": "c", "customerId": "", "currency": "VND",
         "finance": {"currency": "VND", "hasActualLines": True,
                     "receivable": 100.0, "received": 40.0, "outstanding": 60.0},
         "sale": "S", "support": "SP", "status": "x", "statusTone": "blue"},
        {"id": "B", "customer": "c", "customerId": "", "currency": "USD",
         "finance": {"currency": "USD", "hasActualLines": True,
                     "receivable": 10.0, "received": 2.0, "outstanding": 8.0},
         "sale": "S", "support": "SP", "status": "x", "statusTone": "blue"},
        {"id": "C", "customer": "c", "customerId": "", "currency": "CNY",
         "finance": {"currency": "CNY", "hasActualLines": True,
                     "receivable": 500.0, "received": 100.0, "outstanding": 400.0},
         "sale": "S", "support": "SP", "status": "x", "statusTone": "blue"},
    ]
    projected = rd.receivables_projection(rows)
    totals = projected["totals"]

    assert set(totals.keys()) == {"VND", "USD", "CNY"}
    assert totals["VND"]["receivable"] == 100.0
    assert totals["USD"]["receivable"] == 10.0
    assert totals["CNY"]["receivable"] == 500.0
    # No cross-currency grand total exists anywhere in the projection.
    assert "grand_total" not in projected
    assert "total" not in projected


# ---------------------------------------------------------------------------
# F — UNKNOWN != ZERO
# ---------------------------------------------------------------------------

def test_c2c_missing_actual_is_unknown_not_zero(staging):
    """A shipment with no booked actual line has receivable/outstanding UNKNOWN."""
    ship = vm.read_shipment(SHIPMENT)
    empty = {**ship, "id": "LO-EMPTY", "customer": "Khách chưa chốt",
             "data": {**ship["data"], "3.4": {"details": [], "payments": [],
                                              "commission": {"total": 0}}}}
    # Simulate: seed the worklist through the real projection path by feeding a
    # row built by shipment_projection (which is what build_view_model does).
    row = rd.shipment_projection(empty)
    worklist = rd.receivables_projection([row])
    rec = worklist["rows"][0]

    assert rec["hasActualLines"] is False
    assert rec["receivable"] is None, "missing actual must not become 0"
    assert rec["outstanding"] is None
    # A genuine zero stays zero: no payments recorded ⇒ received == 0.
    assert rec["received"] == 0.0
    # No totals manufactured from an unknown book.
    assert "VND" not in worklist["totals"]


# ---------------------------------------------------------------------------
# G — quote estimate is never used as the actual receivable
# ---------------------------------------------------------------------------

def test_c2c_quote_estimate_is_not_used_as_receivable(staging):
    """The worklist receivable equals core.logic over actuals, never the quote."""
    from core.logic import calculate_from_shipment

    row = _row()
    ship = vm.read_shipment(SHIPMENT)
    assert row["receivable"] == calculate_from_shipment(ship)["receivable"]
    # The receivable projection has no quote source anywhere.
    assert "quote" not in row


# ---------------------------------------------------------------------------
# H + I — record one receipt from the global workspace, fresh readback updates it
# ---------------------------------------------------------------------------

def test_c2c_record_receipt_and_fresh_readback_updates_worklist(staging, event_seq):
    """The SAME payment writer, driven from the global workspace row."""
    before = _row()
    assert before["received"] == 0.0
    assert before["outstanding"] == before["receivable"]

    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 30_000_000,
        "requestId": "REQ-C2C-0308-1", "date": "2026-09-10", "note": "Thu tiền khách",
    })
    assert out["ok"], out["error"]

    # Fresh readback — a rebuilt view model, not the event payload.
    after = _row()
    assert after["received"] == 30_000_000.0
    assert after["outstanding"] == before["receivable"] - 30_000_000.0

    # Per-currency totals move with the same truth.
    totals = _worklist()["totals"]
    assert totals["VND"]["received"] >= 30_000_000.0
    assert totals["VND"]["outstanding"] == totals["VND"]["receivable"] - totals["VND"]["received"]


# ---------------------------------------------------------------------------
# J + K — same-intent idempotent, new-intent distinct
# ---------------------------------------------------------------------------

def test_c2c_same_intent_replay_has_no_duplicate_effect(staging, event_seq):
    """Retrying the SAME request identity posts once."""
    payload = {"shipmentId": SHIPMENT, "amount": 15_000_000,
               "requestId": "REQ-C2C-IDEM", "date": "2026-09-10", "note": "Thu tiền khách"}
    first = _dispatch(event_seq, "payment_record", payload)
    replay = _dispatch(event_seq, "payment_record", dict(payload))
    assert first["ok"] and replay["ok"]
    assert replay["persisted"]["paymentId"] == first["persisted"]["paymentId"]

    fresh = vm.read_shipment(SHIPMENT)
    rows = [p for p in fresh["data"]["3.4"]["payments"] if p.get("request_id") == "REQ-C2C-IDEM"]
    assert len(rows) == 1
    assert _row()["received"] == 15_000_000.0


def test_c2c_new_intent_is_a_distinct_receipt(staging, event_seq):
    """A second genuine receipt of the same amount posts a distinct record."""
    payload = {"shipmentId": SHIPMENT, "amount": 10_000_000, "date": "2026-09-10",
               "note": "Thu tiền khách"}
    a = _dispatch(event_seq, "payment_record", {**payload, "requestId": "REQ-C2C-1"})
    b = _dispatch(event_seq, "payment_record", {**payload, "requestId": "REQ-C2C-2"})
    assert a["ok"] and b["ok"]
    assert a["persisted"]["paymentId"] != b["persisted"]["paymentId"]
    assert _row()["received"] == 20_000_000.0


# ---------------------------------------------------------------------------
# L + M + N — RBAC at the backend writer boundary + audit
# ---------------------------------------------------------------------------

def test_c2c_allowed_role_records_receipt(staging, event_seq):
    import streamlit as st
    from core.auth import can_operate_business

    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    assert can_operate_business("finance_write") is True
    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 5_000_000,
        "requestId": "REQ-C2C-ALLOW", "note": "Thu tiền khách"})
    assert out["ok"], out["error"]


def test_c2c_denied_role_is_refused_at_the_backend_writer(staging, event_seq):
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    blocked = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 500_000_000,
        "requestId": "REQ-C2C-DENIED", "note": "Thu tiền khách"})
    assert blocked["ok"] is False
    assert "quyền" in blocked["error"]

    fresh = vm.read_shipment(SHIPMENT)
    assert not [p for p in fresh["data"]["3.4"]["payments"]
                if p.get("request_id") == "REQ-C2C-DENIED"]


def test_c2c_receipt_is_audited(staging, event_seq):
    from core.database import load_audit_logs

    _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 8_000_000,
        "requestId": "REQ-C2C-AUDIT", "note": "Thu tiền khách"})
    rows = load_audit_logs("shipment", SHIPMENT, limit=50)
    assert "direct_payment_created" in [row.get("action") for row in rows]
    assert logi_sandbox.STAGING_ACTOR["username"] in {row.get("actor") for row in rows}
    assert all(row.get("created_at") for row in rows)
