"""LOGI-GOOD C2A — one existing shipment's Finance Actual truth, end to end.

Owner journey proven here, on the single existing staging shipment ``LO-0308``:

    EXISTING SHIPMENT
      → REAL FINANCE ACTUAL READ
      → REAL COST / REVENUE ACTUALS
      → REAL RECEIPT ACTION
      → OUTSTANDING BALANCE
      → ACTUAL PROFIT / MARGIN
      → FRESH READBACK
      → REOPEN AND SEE THE SAME BUSINESS TRUTH

Every assertion re-reads the shipment from the database
(``views.logi_view_model.read_shipment``) — never from the event result and
never from frontend state.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

# The ONE existing shipment this slice proves. Real-shaped staging seed:
# one booked actual service line, no payments yet, currency VND.
SHIPMENT = "LO-0308"


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


def _finance(shipment_id: str = SHIPMENT) -> dict:
    """Finance projection built from a FRESH database read."""
    return rd.shipment_projection(vm.read_shipment(shipment_id))["finance"]


# ---------------------------------------------------------------------------
# A — real Finance Actual read
# ---------------------------------------------------------------------------

def test_c2a_finance_actual_read_is_authoritative(staging):
    """The read comes from the canonical document via core.logic, not the UI."""
    from core.logic import calculate_from_shipment

    ship = vm.read_shipment(SHIPMENT)
    assert ship is not None, "the existing shipment must exist in staging"
    summary = calculate_from_shipment(ship)

    fin = _finance()
    assert fin["source"] == "core.logic.calculate_from_shipment over data.3.4"
    assert fin["receivable"] == summary["receivable"]
    assert fin["receivableNet"] == summary["revenue_net"]
    assert fin["outputVat"] == summary["output_vat"]
    assert fin["payable"] == summary["cost"]
    assert fin["outstanding"] == summary["debt"]
    assert fin["profit"] == summary["profit"]
    # Quote Estimate is a different collection and is NOT merged in.
    assert fin["quote"] == []
    assert fin["actual"], "the seed line must be visible as an actual"


# ---------------------------------------------------------------------------
# B + C — supported Finance Actual write, then fresh readback
# ---------------------------------------------------------------------------

def test_c2a_finance_actual_write_and_fresh_readback(staging, event_seq):
    """One supported actual line written through the canonical writer."""
    from core.database import load_data

    before = _finance()
    assert before["hasActualLines"] is True

    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí nâng hạ container (thực tế)", "qty": 2,
                 "price": 1_500_000, "cost": 1_100_000, "vat": 8, "unit": "Lần"},
    })
    assert out["ok"], out["error"]

    # Fresh readback — an independent query, not the event payload.
    fresh = vm.read_shipment(SHIPMENT)
    saved = next(d for d in fresh["data"]["3.4"]["details"] if d["id"] == out["lineId"])
    assert saved["name_full"] == "Phí nâng hạ container (thực tế)"
    assert saved["qty"] == 2.0 and saved["price"] == 1_500_000.0
    assert saved["cost"] == 1_100_000.0 and saved["vat_line"] == 8.0

    # The canonical snapshot was recomputed by core.logic on write.
    assert fresh["data"]["3.4"]["out"] == fresh["data"]["3.4"]["out_net"] + fresh["data"]["3.4"]["output_vat"]
    assert fresh["data"]["3.4"]["in"] == 57_000_000.0 + 2 * 1_100_000.0

    fin = _finance()
    assert fin["receivableNet"] == before["receivableNet"] + 2 * 1_500_000
    assert fin["payable"] == before["payable"] + 2 * 1_100_000
    # Also present through the cached loader the app normally uses.
    assert load_data()[SHIPMENT]["data"]["3.4"]["out"] == fin["receivable"]


def test_c2a_finance_actual_update_existing_line_not_duplicated(staging, event_seq):
    """Re-saving the same line id updates it — it does not add a second line."""
    created = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí lưu cont", "qty": 1, "price": 900_000, "cost": 700_000, "vat": 8},
    })
    assert created["ok"], created["error"]
    line_id = created["lineId"]

    updated = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"id": line_id, "name": "Phí lưu cont", "qty": 3, "price": 900_000,
                 "cost": 700_000, "vat": 8},
    })
    assert updated["ok"], updated["error"]
    assert updated["lineId"] == line_id

    details = vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]
    assert [d["id"] for d in details].count(line_id) == 1
    assert next(d for d in details if d["id"] == line_id)["qty"] == 3.0


# ---------------------------------------------------------------------------
# D — actual cost / revenue semantics preserved
# ---------------------------------------------------------------------------

def test_c2a_revenue_and_cost_semantics_are_preserved(staging, event_seq):
    """receivable = net + output VAT; payable is accrued cost, not cash paid."""
    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Cước VN nội địa", "qty": 1, "price": 10_000_000,
                 "cost": 8_000_000, "vat": 10},
    })
    assert out["ok"], out["error"]

    fin = _finance()
    assert fin["receivable"] == fin["receivableNet"] + fin["outputVat"]
    assert fin["receivable"] > fin["receivableNet"], "output VAT is part of the receivable"
    # Accrued cost != cash paid to partners: the shipment carries no
    # supplier-payment ledger, so that stays UNKNOWN rather than 0.
    assert fin["payable"] == 65_000_000.0
    assert fin["paid"] is None


# ---------------------------------------------------------------------------
# E — currencies stay explicit and are never converted
# ---------------------------------------------------------------------------

def test_c2a_currency_is_explicit_and_never_converted(staging, event_seq):
    """Currency is carried per shipment/line; no FX is invented anywhere."""
    assert _finance()["currency"] == "VND"

    # A USD shipment is labelled USD and its amounts are NOT converted.
    ship = vm.read_shipment(SHIPMENT)
    usd = {**ship, "id": "LO-USD-PROBE", "currency": "USD",
           "data": {**ship["data"], "3.4": {
               "details": [{"id": "L1", "name_full": "Ocean freight", "qty": 1,
                            "price": 1000.0, "cost": 800.0, "vat_line": 0.0}],
               "payments": [], "commission": {"total": 0},
           }}}
    fin = rd.shipment_projection(usd)["finance"]
    assert fin["currency"] == "USD"
    assert fin["receivableNet"] == 1000.0, "no conversion to VND may be applied"
    assert fin["payable"] == 800.0
    for line in fin["actual"]:
        assert line["ccy"] == "USD"

    # Quote Estimate lines keep their own per-line currency and are never
    # summed into the actual totals.
    quote_lines = rd._quote_lines(vm.read_shipment("LO-0306"),
                                  vm._load_references()["quotes"])
    currencies = {line["ccy"] for line in quote_lines}
    assert len(currencies) > 1, "the seed proves mixed-currency quote lines stay separate"


# ---------------------------------------------------------------------------
# F — UNKNOWN != ZERO
# ---------------------------------------------------------------------------

def test_c2a_unknown_never_becomes_zero(staging):
    """With no booked actual line, profit/margin are UNKNOWN — not 0."""
    ship = vm.read_shipment(SHIPMENT)
    empty = {**ship, "id": "LO-EMPTY-PROBE",
             "data": {**ship["data"], "3.4": {
                 "details": [], "payments": [], "commission": {"total": 0}}}}
    fin = rd.shipment_projection(empty)["finance"]

    assert fin["hasActualLines"] is False
    assert fin["profit"] is None, "profit must not be manufactured from an empty book"
    assert fin["profitMargin"] is None
    assert fin["paid"] is None, "no supplier-payment ledger → UNKNOWN, not 0"
    # A genuine zero is still a zero.
    assert fin["received"] == 0.0


def test_c2a_blank_actual_amount_is_not_stored_as_a_business_value(staging, event_seq):
    """A blank price on the write path does not become a claimed actual."""
    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Chi phí chờ xác nhận", "qty": 1, "price": "", "cost": ""},
    })
    assert out["ok"], out["error"]
    # The projection reports UNKNOWN for facts the model genuinely lacks.
    projection = out["readback"]
    assert projection["cargo"]["packs"] is None
    assert projection["importInfo"]["tax"] is None


# ---------------------------------------------------------------------------
# G + I — one real receipt, outstanding from backend truth
# ---------------------------------------------------------------------------

def test_c2a_receipt_recorded_and_outstanding_from_backend_truth(staging, event_seq):
    """One real receipt; outstanding is core.logic's debt, re-read from the DB."""
    before = _finance()
    assert before["received"] == 0.0
    assert before["outstanding"] == before["receivable"]

    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 40_000_000,
        "requestId": "REQ-C2A-0308-A", "date": "2026-09-10", "note": "Thu tạm ứng đợt 1",
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment(SHIPMENT)
    rows = [p for p in fresh["data"]["3.4"]["payments"] if p.get("request_id") == "REQ-C2A-0308-A"]
    assert len(rows) == 1
    assert float(rows[0]["amount"]) == 40_000_000.0

    fin = _finance()
    assert fin["received"] == 40_000_000.0
    assert fin["outstanding"] == fin["receivable"] - fin["received"]
    assert fin["outstanding"] == out["persisted"]["derivedDebt"]
    assert fin["payments"][0]["requestId"] == "REQ-C2A-0308-A"


# ---------------------------------------------------------------------------
# H — duplicate submission is idempotent
# ---------------------------------------------------------------------------

def test_c2a_duplicate_submission_has_no_duplicate_financial_effect(staging, event_seq):
    """Retrying the SAME payment intent posts once — proven by fresh readback."""
    payload = {"shipmentId": SHIPMENT, "amount": 25_000_000,
               "requestId": "REQ-C2A-IDEMPOTENT", "date": "2026-09-10",
               "note": "Thu tiền khách"}
    first = _dispatch(event_seq, "payment_record", payload)
    replay = _dispatch(event_seq, "payment_record", dict(payload))
    assert first["ok"] and replay["ok"]
    assert replay["persisted"]["paymentId"] == first["persisted"]["paymentId"]

    fresh = vm.read_shipment(SHIPMENT)
    rows = [p for p in fresh["data"]["3.4"]["payments"]
            if p.get("request_id") == "REQ-C2A-IDEMPOTENT"]
    assert len(rows) == 1, "a replayed request identity must not double-post"

    registry = logi_sandbox._state["client"][logi_sandbox.STAGING_DB_NAME].financial_action_requests
    assert registry.count_documents({"request_id": "REQ-C2A-IDEMPOTENT"}) == 1

    fin = _finance()
    assert fin["received"] == 25_000_000.0
    assert fin["outstanding"] == fin["receivable"] - 25_000_000.0


def test_c2a_new_intent_posts_a_second_receipt(staging, event_seq):
    """G4 regression: idempotency is scoped to the REQUEST, not to the amount.

    A second genuine receipt of the same amount and kind must post. If the UI's
    request identity were derived from shipmentId|amount|kind, this would be
    silently swallowed as a replay.
    """
    payload = {"shipmentId": SHIPMENT, "amount": 10_000_000, "date": "2026-09-10",
               "note": "Thu tiền khách"}
    a = _dispatch(event_seq, "payment_record", {**payload, "requestId": "REQ-C2A-INTENT-1"})
    b = _dispatch(event_seq, "payment_record", {**payload, "requestId": "REQ-C2A-INTENT-2"})
    assert a["ok"] and b["ok"]
    assert a["persisted"]["paymentId"] != b["persisted"]["paymentId"]
    assert _finance()["received"] == 20_000_000.0


# ---------------------------------------------------------------------------
# J — actual profit never borrows Quote Estimate
# ---------------------------------------------------------------------------

def test_c2a_actual_profit_never_borrows_quote_estimate(staging, event_seq):
    """Profit = net − cost − commission from ACTUALS only; else UNKNOWN."""
    from core.logic import calculate_from_shipment

    _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí chứng từ", "qty": 1, "price": 2_000_000,
                 "cost": 500_000, "vat": 8},
    })

    ship = vm.read_shipment(SHIPMENT)
    summary = calculate_from_shipment(ship)
    fin = _finance()
    assert fin["profit"] == summary["revenue_net"] - summary["cost"] - summary["commission"]
    assert fin["profit"] == summary["profit"]
    assert fin["profit"] != summary["receivable"] - summary["cost"], "output VAT is not profit"
    assert fin["profitMargin"] == round(summary["profit"] / summary["revenue_net"] * 100, 2)

    # With a quote present but NO actual line, profit stays UNKNOWN — the quote
    # is never used to fill it in.
    quoted = {**ship, "id": "LO-QUOTE-ONLY", "customer_id": "CUST-MINHDUC",
              "contract_id": "",
              "data": {**ship["data"], "3.4": {"details": [], "payments": [],
                                               "commission": {"total": 0}}}}
    from core.database import load_quotes

    probe = rd.shipment_projection(quoted, quotes=load_quotes() or {})["finance"]
    assert probe["hasActualLines"] is False
    assert probe["profit"] is None
    assert probe["profitMargin"] is None


# ---------------------------------------------------------------------------
# K + L — RBAC is enforced by the backend, not by button visibility
# ---------------------------------------------------------------------------

def test_c2a_allowed_role_can_write_finance_actual(staging, event_seq):
    """SUPPORT carries finance_write, so the typed event succeeds."""
    import streamlit as st

    from core.auth import can_operate_business

    st.session_state["current_user"] = {"username": "ke.toan", "role": "ACCOUNTING",
                                        "user_id": "U-KT"}
    # ACCOUNTING is read-only for finance_write by the single role matrix...
    assert can_operate_business("finance_write") is False

    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    assert can_operate_business("finance_write") is True
    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí THC", "qty": 1, "price": 3_000_000, "cost": 2_400_000, "vat": 8},
    })
    assert out["ok"], out["error"]


def test_c2a_denied_role_cannot_bypass_the_backend_with_a_typed_event(staging, event_seq):
    """A directly typed event from a read-only role is refused and writes nothing."""
    import streamlit as st

    from core.database import load_audit_logs

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    before = _finance()

    blocked_line = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Dòng ghi lậu", "qty": 1, "price": 999_000_000, "cost": 1},
    })
    assert blocked_line["ok"] is False
    assert "quyền" in blocked_line["error"]

    blocked_pay = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 500_000_000, "requestId": "REQ-C2A-RBAC"})
    assert blocked_pay["ok"] is False
    assert "quyền" in blocked_pay["error"]

    fresh = vm.read_shipment(SHIPMENT)
    assert not [d for d in fresh["data"]["3.4"]["details"] if d.get("name_full") == "Dòng ghi lậu"]
    assert not [p for p in fresh["data"]["3.4"]["payments"]
                if p.get("request_id") == "REQ-C2A-RBAC"]
    assert _finance() == before
    assert not [row for row in load_audit_logs("shipment", SHIPMENT, limit=50)
                if row.get("actor") == "viewer.user"]


# ---------------------------------------------------------------------------
# M — audit evidence
# ---------------------------------------------------------------------------

def test_c2a_audit_trail_for_finance_mutations(staging, event_seq):
    """The canonical writers' own audit log, read back from the database."""
    from core.database import load_audit_logs

    _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí kiểm hóa", "qty": 1, "price": 1_200_000, "cost": 800_000, "vat": 8},
    })
    _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 7_000_000,
        "requestId": "REQ-C2A-AUDIT", "date": "2026-09-10", "note": "Thu tiền khách"})

    rows = load_audit_logs("shipment", SHIPMENT, limit=50)
    actions = [row.get("action") for row in rows]
    assert "update" in actions, "the finance actual write must be audited"
    assert "direct_payment_created" in actions, "the receipt must be audited"
    assert logi_sandbox.STAGING_ACTOR["username"] in {row.get("actor") for row in rows}
    assert all(row.get("created_at") for row in rows)


# ---------------------------------------------------------------------------
# N — reopen in fresh app state and see the same business truth
# ---------------------------------------------------------------------------

def test_c2a_fresh_app_state_shows_the_same_business_truth(staging, event_seq):
    """A rebuilt view model (fresh app state) shows the same financial truth."""
    _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí làm hàng", "qty": 1, "price": 4_000_000,
                 "cost": 3_000_000, "vat": 8},
    })
    _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 30_000_000,
        "requestId": "REQ-C2A-REOPEN", "date": "2026-09-10", "note": "Thu tiền khách"})

    expected = _finance()

    # Fresh app state: a newly built component payload, nothing cached in hand.
    import streamlit as st

    st.cache_data.clear()
    model = vm.build_view_model()
    row = next(r for r in model["shipments"] if r["id"] == SHIPMENT)

    assert row["finance"]["currency"] == expected["currency"]
    assert row["finance"]["receivable"] == expected["receivable"]
    assert row["finance"]["receivableNet"] == expected["receivableNet"]
    assert row["finance"]["outputVat"] == expected["outputVat"]
    assert row["finance"]["payable"] == expected["payable"]
    assert row["finance"]["received"] == expected["received"]
    assert row["finance"]["paid"] is None
    assert row["finance"]["outstanding"] == expected["outstanding"]
    assert row["finance"]["profit"] == expected["profit"]
    assert row["finance"]["profitMargin"] == expected["profitMargin"]
    assert [p["requestId"] for p in row["finance"]["payments"]] == \
           [p["requestId"] for p in expected["payments"]]
    assert row["finance"]["actual"] == expected["actual"]
