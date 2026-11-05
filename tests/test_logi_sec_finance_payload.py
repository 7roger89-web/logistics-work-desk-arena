"""LOGI-SEC-FINANCE-PAYLOAD-20261105 — server payload boundary for finance_view.

The bounded security fix: an actor WITHOUT ``finance_view`` (Sale, anonymous)
must never receive restricted finance data through the backend payload that
``views.logi_view_model.build_view_model`` hands to the React renderer
(``views.logi_shell.render`` -> component ``data`` channel).

Proven here, on the isolated staging database (mongomock), through the REAL
``build_view_model`` path — no mocked view model, no fake renderer payload:

    synthetic shipment with finance sentinel 123456789 VND (actual line
    price/cost, customer payment, canonical ledger obligation)
      -> build_view_model() as Admin / Support / Viewer / Sale / anonymous
      -> serialize the finance-bearing sections exactly as the renderer
         would receive them, and scan for the sentinel (raw + derived)
      -> Sale still sees shipment id, journey, customer and commercial quote
      -> stale Admin write outcomes + GetFly preview lingering in the same
         session must not leak to Sale after a role downgrade
      -> the frontend role selector (React state only) cannot change the
         server-side actor

Production database is never touched.

NOTE on the sentinel scan scope: the whole-model JSON is NOT scanned for the
raw ``123456789`` substring, because the seeded authority master carries the
bank account number ``0123456789`` (which contains that substring) inside
``model["authority"]`` — an unrelated, pre-existing exposure that this task
does NOT change (see ACCEPTANCE.md). The scan covers exactly the finance
payload paths named in the task packet: shipments[].finance, receivables,
payables, reconciliation, home aggregates, ceoReport, partnerContext.finance,
lastWrites and getfly.
"""

from __future__ import annotations

import copy
import json

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm


SENTINEL = 123456789
SENTINEL_TEXT = str(SENTINEL)
SHIPMENT = "LO-SEC-0306"
SOURCE_SHIPMENT = "LO-0306"
PARTNER = "AGT-PHUANH"

# Finance-bearing payload paths named in the task packet. Each is scanned
# (serialized) for the sentinel after every build.
FINANCE_PATHS = (
    "shipments",
    "receivables",
    "payables",
    "reconciliation",
    "home",
    "ceoReport",
    "partnerContext",
    "lastWrites",
    "getfly",
)

ROLE_USERS = {
    "admin": {"username": "admin.user", "role": "admin", "user_id": "U-ADMIN"},
    "support": {"username": "support.user", "role": "support", "user_id": "U-SUPPORT"},
    "viewer": {"username": "viewer.user", "role": "viewer", "user_id": "U-VIEWER"},
    "sale": {"username": "sale.user", "role": "sale", "user_id": "U-SALE"},
}


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_role(role: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = dict(ROLE_USERS[role])


def _as_anonymous() -> None:
    import streamlit as st

    st.session_state["current_user"] = {}


def _dispatch(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _seed_sentinel_shipment(seq_fn) -> None:
    """Clone LO-0306 with finance sentinel in every restricted money field.

    LO-0306 is An Phát (CUST-ANPHAT), so the legacy quote fallback still
    finds the BG-0306 commercial quote — the quote must SURVIVE redaction
    for Sale while the sentinel finance must not.
    """
    from core.database import save_shipment_atomic

    source = vm.read_shipment(SOURCE_SHIPMENT)
    assert source is not None, "seed shipment LO-0306 must exist"
    ship = copy.deepcopy(source)
    ship["id"] = SHIPMENT
    ship["shipment_id"] = SHIPMENT
    ship["version"] = 0
    ship["data"]["3.4"]["details"] = [
        {
            "id": "SEC-LINE-1",
            "name_full": "Cước xe sentinel",
            "display_name": "Cước xe sentinel",
            "code": "DV-SEC",
            "unit": "Lần",
            "qty": 1,
            "price": SENTINEL,
            "cost": SENTINEL,
            "vat_line": 0,
            "note": "",
        }
    ]
    ship["data"]["3.4"]["payments"] = [
        {
            "id": "SEC-PAY-1",
            "request_id": "SEC-REQ-1",
            "date": "2026-09-10",
            "amount": SENTINEL,
            "note": "Thu sentinel",
            "created_by": "staging.support",
        }
    ]
    assert save_shipment_atomic(ship, expected_version=0), "sentinel shipment must save"

    # Canonical ledger obligation with the same sentinel (C2D truth).
    out = _dispatch(seq_fn, "partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "SEC-OBL-1",
        "amount": SENTINEL, "currency": "VND",
        "note": "Phải trả sentinel đối tác",
    })
    assert out["ok"], out["error"]


def _seed_stale_session_state() -> None:
    """Lingering Admin-session artefacts: a finance write outcome and a
    GetFly preview, both carrying the sentinel. They model an Admin who
    wrote/parsed finance in this browser session before a role downgrade
    (or logout/login in the same tab) handed the session to Sale."""
    import streamlit as st

    ship = vm.read_shipment(SHIPMENT)
    assert ship is not None
    readback = rd.shipment_projection(ship)
    assert SENTINEL_TEXT in json.dumps(readback, default=str), "fixture readback must carry the sentinel"
    st.session_state["logi_last_writes"] = [
        {
            "event": "payment_record",
            "shipmentId": SHIPMENT,
            "ok": True,
            "error": "",
            "readback": readback,
        }
    ]
    money_line = {
        "line_id": "DH-SEC::L1",
        "product_code": "P-SEC",
        "product_name": "Hàng sentinel",
        "product_note": "",
        "qty": 1,
        "cost": SENTINEL,
        "price": SENTINEL,
        "revenue": SENTINEL,
        "profit": SENTINEL,
    }
    st.session_state["logi_getfly_preview"] = {
        "status": "READY",
        "previewId": "GF-SEC",
        "requestId": "SEC-REQ",
        "filename": "DSDH-sec.xlsx",
        "fingerprint": "sec",
        "normalizedRows": [{"order_id": "DH-SEC", **money_line}],
        "orders": [
            {
                "orderId": "DH-SEC",
                "customerName": "An Phát JSC",
                "customerCode": "",
                "customerId": "CUST-ANPHAT",
                "customerMatch": "UNKNOWN",
                "orderDate": "2026-09-10",
                "sourceStatus": "",
                "existing": False,
                "serviceLines": [dict(money_line)],
                "revenue": SENTINEL,
                "profit": SENTINEL,
            }
        ],
        "summary": {"orders": 1, "revenue": SENTINEL, "profit": SENTINEL},
    }


def _row(model: dict, shipment_id: str = SHIPMENT) -> dict:
    return next(r for r in model["shipments"] if r["id"] == shipment_id)


def _finance_sections(model: dict) -> dict:
    """Exactly the finance-bearing payload paths, serialized as the
    renderer receives them."""
    return {path: model.get(path) for path in FINANCE_PATHS}


def _assert_no_sentinel(model: dict, where: str) -> None:
    blob = json.dumps(_finance_sections(model), default=str)
    assert SENTINEL_TEXT not in blob, f"sentinel leaked to {where}: {blob[:600]}"


def _assert_sentinel_present(model: dict, where: str) -> None:
    blob = json.dumps(_finance_sections(model), default=str)
    assert SENTINEL_TEXT in blob, f"sentinel missing for {where} (fixture broken?)"


# ---------------------------------------------------------------------------
# Distinguishing test — Sale must not receive restricted finance data
# ---------------------------------------------------------------------------

def test_sale_payload_contains_no_finance_sentinel(staging, event_seq):
    """Fixture sentinel 123456789; Sale session; renderer payload must not
    contain it through any raw or derived finance field."""
    _seed_sentinel_shipment(event_seq)
    _seed_stale_session_state()
    _as_role("sale")
    import streamlit as st

    # Select the sentinel partner so partnerContext.finance actually renders.
    st.session_state["logi_partner_context_selection"] = PARTNER

    model = vm.build_view_model()

    _assert_no_sentinel(model, "Sale")

    # Per-field: restricted money is UNKNOWN (None), never a fabricated 0.
    finance = _row(model)["finance"]
    assert finance["restricted"] is True
    assert finance["receivable"] is None
    assert finance["received"] is None
    assert finance["receivableNet"] is None
    assert finance["outstanding"] is None
    assert finance["payable"] is None
    assert finance["profit"] is None
    assert finance["profitMargin"] is None
    assert finance["commission"] is None
    assert finance["actual"] == []
    assert finance["payments"] == []
    assert finance["partner"]["payable"] is None
    assert finance["partner"]["remaining"] is None
    assert finance["partner"]["payments"] == []

    # Derived aggregates carry no sentinel either.
    assert model["receivables"]["totals"] == {}
    assert model["payables"]["rows"] == []
    assert model["payables"]["totals"] == {}
    assert model["reconciliation"]["rows"] == []
    assert model["home"]["outstandingTotal"] is None
    assert model["home"]["outstandingTotalLabel"] == rd.UNKNOWN_LABEL
    assert model["ceoReport"]["receivables"]["hasAuthoritativeAmounts"] is False
    assert model["ceoReport"]["financeActual"]["positions"] == []
    assert model["ceoReport"]["topCustomers"] == []
    assert model["partnerContext"]["finance"]["rows"] == []
    assert model["partnerContext"]["selectedKey"], "partner identity still shown"
    assert model["getfly"]["summary"]["revenue"] is None
    assert model["getfly"]["summary"]["profit"] is None

    # Stale Admin readback in lastWrites is redacted, not replayed raw.
    assert model["lastWrites"], "stale outcome must still be delivered (redacted)"
    readback = model["lastWrites"][0]["readback"]
    assert readback["finance"]["receivable"] is None
    assert readback["finance"]["actual"] == []

    # Sale still sees the permitted shipment, customer, journey and quote.
    row = _row(model)
    assert row["id"] == SHIPMENT
    assert row["customer"] == "An Phát JSC"
    assert row["journey"], "journey must survive redaction"
    assert row["route"], "route must survive redaction"
    assert row["status"], "status must survive redaction"
    quote = finance["quote"]
    assert quote, "commercial quote must survive redaction for Sale"
    assert any(line.get("amount") == 28500000 for line in quote), "BG-0306 quote line kept"


def test_sale_payload_matches_admin_quote(staging, event_seq):
    """The commercial quote Sale sees is byte-identical to Admin's quote —
    redaction preserves commercial data, it does not invent or drop it."""
    _seed_sentinel_shipment(event_seq)
    _as_role("admin")
    admin_quote = _row(vm.build_view_model())["finance"]["quote"]
    assert admin_quote, "fixture must project a quote for Admin"

    _as_role("sale")
    sale_quote = _row(vm.build_view_model())["finance"]["quote"]
    assert sale_quote == admin_quote


# ---------------------------------------------------------------------------
# Roles that hold finance_view keep their existing authorized data
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["admin", "support", "viewer"])
def test_authorized_roles_retain_finance_sentinel(staging, event_seq, role):
    """Admin / Support / Viewer hold finance_view: the sentinel stays in
    their payload exactly as before (no narrowing of the role matrix)."""
    _seed_sentinel_shipment(event_seq)
    _seed_stale_session_state()
    _as_role(role)
    import streamlit as st

    st.session_state["logi_partner_context_selection"] = PARTNER

    model = vm.build_view_model()
    _assert_sentinel_present(model, role)

    finance = _row(model)["finance"]
    assert finance["receivable"] == SENTINEL
    assert finance["payable"] == SENTINEL
    assert finance["received"] == SENTINEL
    assert finance["actual"][0]["amount"] == SENTINEL
    assert finance["payments"][0]["amount"] == SENTINEL
    assert finance["partner"]["payable"] == SENTINEL
    assert model["payables"]["rows"], "C2D worklist keeps the ledger row"
    assert any(
        row.get("partnerId") == PARTNER and row.get("remaining") == SENTINEL
        for row in model["payables"]["rows"]
    ), "C2D row keeps the sentinel remaining amount"
    assert model["partnerContext"]["finance"]["rows"], "partner context keeps finance rows"
    assert SENTINEL_TEXT in json.dumps(model["partnerContext"]["finance"], default=str)


def test_anonymous_gate_is_fail_closed(staging, event_seq):
    """Fail closed at the gate itself: with no authenticated identity,
    ``_can_view_finance()`` is False — even though the bare role matrix
    would fall back to Viewer (which holds finance_view) — and the
    standalone payload helpers redact stale finance under that gate.

    A full ``build_view_model()`` as anonymous is NOT observable on the
    sandbox transport: ``ensure_backend()`` promotes an empty session to the
    staging SUPPORT actor before the payload is built (pre-existing staging
    behaviour, pinned by the next test). In production ``require_login()``
    stops an anonymous session before any payload is built at all.
    """
    import streamlit as st

    _seed_sentinel_shipment(event_seq)
    _seed_stale_session_state()
    _as_anonymous()

    assert vm._can_view_finance() is False

    readback = vm._last_writes_readback()
    assert readback, "stale outcome still delivered (redacted)"
    assert readback[0]["readback"]["finance"]["receivable"] is None
    assert readback[0]["readback"]["finance"]["actual"] == []

    preview = vm._getfly_preview_projection()
    assert preview["summary"]["revenue"] is None
    assert preview["summary"]["profit"] is None
    assert all(
        line.get("revenue") is None and line.get("profit") is None
        for order in preview["orders"]
        for line in order["serviceLines"]
    )
    assert all(
        row.get("cost") is None for row in preview["normalizedRows"]
    )


def test_sandbox_promotes_anonymous_to_staging_actor(staging, event_seq):
    """Pins pre-existing staging behaviour (NOT a security claim): on the
    sandbox transport ``ensure_backend()`` logs an empty session in as the
    staging SUPPORT actor, so a ``build_view_model()`` started anonymous
    renders as SUPPORT. Production never reaches the build anonymous:
    ``require_login()`` renders the login screen first."""
    _seed_sentinel_shipment(event_seq)
    _as_anonymous()

    model = vm.build_view_model()
    assert model["user"]["role"] == "SUPPORT"


# ---------------------------------------------------------------------------
# Role downgrade in the same session must not replay stale finance
# ---------------------------------------------------------------------------

def test_role_downgrade_same_session_drops_stale_finance(staging, event_seq):
    """Support builds a payload WITH the sentinel, then the same session is
    downgraded to Sale (stale lastWrites + GetFly preview still in session
    state): the rebuilt payload must not contain the sentinel."""
    _seed_sentinel_shipment(event_seq)
    _seed_stale_session_state()

    _as_role("support")
    _assert_sentinel_present(vm.build_view_model(), "support before downgrade")

    _as_role("sale")
    model = vm.build_view_model()
    _assert_no_sentinel(model, "sale after downgrade")
    assert _row(model)["id"] == SHIPMENT
    assert _row(model)["journey"]


def test_frontend_role_selector_cannot_bypass_server(staging, event_seq):
    """The React role selector is client state only: stuffing an admin-looking
    value into a client-side key must not change the server-side actor or
    the payload. Authorization reads st.session_state.current_user only."""
    _seed_sentinel_shipment(event_seq)
    _seed_stale_session_state()
    _as_role("sale")
    import streamlit as st

    st.session_state["role_selector"] = "admin"  # decoy: no server code reads this
    st.session_state["display_role"] = "ADMIN"

    model = vm.build_view_model()
    assert model["user"]["role"] == "SALE"
    _assert_no_sentinel(model, "sale with spoofed client role")


# ---------------------------------------------------------------------------
# UI-safe shape + writers unchanged
# ---------------------------------------------------------------------------

def test_restricted_finance_shape_is_ui_safe(staging, event_seq):
    """React dereferences s.finance.actual.length, s.finance.currency,
    s.finance.partner and s.finance.payments directly: the restricted block
    must keep those keys with the right types, never None/absent."""
    _seed_sentinel_shipment(event_seq)
    _as_role("sale")

    finance = _row(vm.build_view_model())["finance"]
    assert isinstance(finance["actual"], list)
    assert isinstance(finance["payments"], list)
    assert isinstance(finance["quote"], list)
    assert isinstance(finance["currency"], str) and finance["currency"]
    assert isinstance(finance["partner"], dict)
    assert isinstance(finance["partner"]["payments"], list)
    assert finance["hasActualLines"] is False


def test_finance_writers_and_ledger_outcomes_unchanged(staging, event_seq):
    """The read-boundary fix must not change write behaviour: Support still
    records a receipt (same writer, same readback) and Sale is still refused
    at the writer boundary."""
    _seed_sentinel_shipment(event_seq)

    _as_role("support")
    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 5_000_000,
        "requestId": "SEC-WRITE-1", "date": "2026-09-10", "note": "Thu tiền khách",
    })
    assert out["ok"], out["error"]
    assert out["readback"]["finance"]["received"] == SENTINEL + 5_000_000

    _as_role("sale")
    blocked = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 500_000_000,
        "requestId": "SEC-WRITE-DENIED", "note": "Thu tiền khách",
    })
    assert blocked["ok"] is False
    assert "quyền" in blocked["error"]

    fresh = vm.read_shipment(SHIPMENT)
    assert not [p for p in fresh["data"]["3.4"]["payments"]
                if p.get("request_id") == "SEC-WRITE-DENIED"]
