"""LOGI-SEC-QUOTE-NOTE-BOUNDARY-20261106 — operator note boundary.

Finding C (CONFIRMED by the probe in evidence/probe_note_leak.py/.log):
the per-line operator ``note`` is free-form text carried verbatim by
``views/logi_c1.py:_quote_payload`` (and ``_handle_quote_edit``) and
projected verbatim by ``quote_projection`` into
``serviceLines[*].note`` — while ``_restricted_quote`` cleared only the
cost figures. A Viewer / legacy Sales actor (``commercial_view`` without
``commercial_write``) therefore received the operator's cost-bearing note
("INTERNAL-COST-742913: giá vốn agent 24000000") even though its
``costUnit`` was already None. The customer snapshot allowlist
(``core.quotations.customer_quote_snapshot``) never publishes the operator
note — only the customer-facing ``customerNotes`` list — so stripping it
for the restricted actor matches the customer boundary.

Proven here, on the isolated staging database (mongomock), through the REAL
``build_view_model`` path and the REAL C1 handlers — no mocked view model,
no fake renderer payload. Production database is never touched.

Sentinel: NOTE_NEEDLE = "INTERNAL-COST-742913" inside the note text
"INTERNAL-COST-742913: giá vốn agent 24000000" (costUnit 24000000,
sellUnit 32000000). The recursive JSON scan runs on the EXACT protected
branch (the C1 quote / the replayed readback) — never on the whole model.
"""

from __future__ import annotations

import json

import pytest

from views import logi_c1, logi_sandbox
from views import logi_view_model as vm

NOTE_TEXT = "INTERNAL-COST-742913: giá vốn agent 24000000"
NOTE_NEEDLE = "INTERNAL-COST-742913"
SELL = 32000000
COST = 24000000
CUSTOMER_NOTE = "Ghi chú công khai cho khách."

ROLE_USERS = {
    "admin": {"username": "admin.user", "role": "admin", "user_id": "U-ADMIN"},
    "support": {"username": "support.user", "role": "support", "user_id": "U-SUPPORT"},
    "viewer": {"username": "viewer.user", "role": "viewer", "user_id": "U-VIEWER"},
    "sale": {"username": "sale.user", "role": "sale", "user_id": "U-SALE"},
    "sales": {"username": "sales.user", "role": "sales", "user_id": "U-SALES"},
    "operations": {"username": "ops.user", "role": "operations", "user_id": "U-OPS"},
    "accounting": {"username": "acct.user", "role": "accounting", "user_id": "U-ACCT"},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    from core.database import get_db

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    db = get_db()
    db.customers.insert_one({"id": "CUST-NOTE-TEST", "name": "Công ty Note Test"})
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


def _dispatch_c1(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _scan_branch(branch, needles):
    text = json.dumps(branch, default=str, ensure_ascii=False)
    return [n for n in needles if str(n) in text]


def _create_noted_quote(seq_fn):
    """Real non-Excel quote_create as Support, one line with a cost-bearing
    operator note. Returns the created quote id."""
    created = _dispatch_c1(seq_fn, "quote_create", {
        "customerId": "CUST-NOTE-TEST", "salesOwner": "Sale test",
        "goodsDescription": "Hàng kiểm chứng ghi chú", "incoterm": "EXW",
        "transportMode": "Road",
        "serviceLines": [{"serviceName": "Vận chuyển", "qty": 1, "unit": "Lần",
                          "currency": "VND", "sellUnit": SELL, "costUnit": COST,
                          "taxPct": None, "note": NOTE_TEXT}],
        "customerNotes": [CUSTOMER_NOTE],
        "requestId": "NOTE-CREATE-1"})
    assert created["ok"], created
    return created["id"], created


def _find_quote(model, qid):
    found = [q for q in model["quotes"] if q.get("id") == qid]
    assert len(found) == 1, f"quote {qid} must appear exactly once, got {len(found)}"
    return found[0]


def _store_last_writes(outcomes) -> None:
    import streamlit as st

    st.session_state["logi_last_writes"] = list(outcomes)


def _last_write(model, event):
    rows = [r for r in model["lastWrites"] if r.get("event") == event]
    assert len(rows) == 1, f"exactly one {event} outcome expected, got {len(rows)}"
    return rows[0]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_operator_note_stripped_for_viewer_and_sales(staging, event_seq):
    """Finding C: Viewer/legacy Sales receive NO operator note (the cost
    string is gone from the whole quote branch); sell price and the
    customer-facing notes survive. Admin/Support/Sale keep the note and
    the cost figure. Accounting/Operations receive no C1 quotes."""
    _as_role("support")
    qid, _created = _create_noted_quote(event_seq)

    for role in ("admin", "support", "sale"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model, qid)
        assert quote["serviceLines"][0]["note"] == NOTE_TEXT, role
        assert quote["serviceLines"][0]["costUnit"] == COST, role
        assert quote["serviceLines"][0]["sellUnit"] == SELL, role
        assert quote["customerNotes"] == [CUSTOMER_NOTE], role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model, qid)
        assert quote["serviceLines"][0]["note"] is None, role
        assert _scan_branch(quote, [NOTE_NEEDLE]) == [], role
        assert quote["serviceLines"][0]["costUnit"] is None, role
        assert quote["serviceLines"][0]["sellUnit"] == SELL, role
        assert quote["customerNotes"] == [CUSTOMER_NOTE], role

    for role in ("accounting", "operations"):
        _as_role(role)
        model = vm.build_view_model()
        assert model["quotes"] == [], f"{role} must receive no C1 quotes"


def test_downgrade_create_edit_transition_readbacks_no_note(staging, event_seq):
    """Outcomes recorded as Support must not replay the operator note to a
    downgraded actor — quote_create, quote_edit and quote_transition."""
    _as_role("support")
    qid, created = _create_noted_quote(event_seq)
    assert created["readback"]["serviceLines"][0]["note"] == NOTE_TEXT
    edited = _dispatch_c1(event_seq, "quote_edit", {
        "id": qid,
        "serviceLines": [{"serviceName": "Vận chuyển", "qty": 1, "unit": "Lần",
                          "currency": "VND", "sellUnit": SELL, "costUnit": COST,
                          "taxPct": None, "note": NOTE_TEXT}],
        "requestId": "NOTE-EDIT-1"})
    assert edited["ok"], edited
    assert edited["readback"]["serviceLines"][0]["note"] == NOTE_TEXT
    transitioned = _dispatch_c1(event_seq, "quote_transition", {
        "id": qid, "nextStatus": "READY_FOR_REVIEW", "requestId": "NOTE-TR-1"})
    assert transitioned["ok"], transitioned
    assert transitioned["readback"]["serviceLines"][0]["note"] == NOTE_TEXT
    _store_last_writes([created, edited, transitioned])

    for role in ("operations", "accounting"):
        _as_role(role)
        model = vm.build_view_model()
        for event in ("quote_create", "quote_edit", "quote_transition"):
            assert _last_write(model, event)["readback"] == {}, (role, event)

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        for event in ("quote_create", "quote_edit", "quote_transition"):
            readback = _last_write(model, event)["readback"]
            assert readback["serviceLines"][0]["note"] is None, (role, event)
            assert _scan_branch(readback, [NOTE_NEEDLE]) == [], (role, event)
            assert readback["serviceLines"][0]["sellUnit"] == SELL, (role, event)
            assert readback["customerNotes"] == [CUSTOMER_NOTE], (role, event)
        row = _last_write(model, "quote_transition")
        assert row["ok"] is True and row["requestId"] == "NOTE-TR-1"


def test_downgrade_quote_preview_readback_no_note(staging, event_seq):
    """A quote_preview outcome recorded as Support runs through the same
    fixed helper on replay: the nested quote's operator note is None for
    Viewer/Sales and the customer snapshot is untouched; Operations and
    Accounting get an empty readback. (The preview producer is Excel-only,
    so this pins the replay path of the shared helper.)"""
    import base64

    from scripts.make_luc_giac_quote_fixture import build_luc_giac_fixture

    _as_role("support")
    source = build_luc_giac_fixture()
    imported = _dispatch_c1(event_seq, "quote_import_excel", {
        "customerId": "CUST-NOTE-TEST", "fileName": "luc-giac-fixture.xlsx",
        "base64": base64.b64encode(source).decode(), "requestId": "NOTE-IMP-1"})
    assert imported["ok"], imported
    details = imported["readback"]
    # The raw fixture proposal carries no service lines; cost one line so
    # the preview quote has a priced top-level service line to inspect.
    # (Excel draft lines have no `note` key — the projection yields "" —
    # so this pins the replay path running the fixed helper, not a leak
    # of the plain-quote note, which tests 1–2 already prove.)
    details["options"]["A"]["service_lines"] = [{
        "id": "fee-a", "service_name": "Vận chuyển", "qty": 1, "unit": "Lần",
        "currency": "VND", "cost_unit": COST, "sell_unit": SELL,
        "sell_confirmed": True, "tax_pct": None}]
    details["options"]["A"]["scope"] = "Preview scope"
    out = _dispatch_c1(event_seq, "quote_preview", {
        "customerId": "CUST-NOTE-TEST", "excelQuote": details,
        "fx": {}, "requestId": "NOTE-PREV-1"})
    assert out["ok"], out
    assert out["readback"]["quote"]["serviceLines"], "preview must price one line"
    _store_last_writes([out])

    for role in ("operations", "accounting"):
        _as_role(role)
        model = vm.build_view_model()
        assert _last_write(model, "quote_preview")["readback"] == {}, role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        readback = _last_write(model, "quote_preview")["readback"]
        assert readback["quote"]["serviceLines"][0]["note"] is None, role
        assert readback["customer"], "customer snapshot survives"
        row = _last_write(model, "quote_preview")
        assert row["ok"] is True and row["requestId"] == "NOTE-PREV-1"


def test_restricted_note_ui_shape_and_source_unmutated(staging, event_seq):
    """Restricted payload stays UI-safe and the redaction never mutates the
    stored quote: the restricted line is still a dict, note is None (never
    0 or a missing key), sell price survives, and the stored note is
    intact after restricted renders."""
    from core.database import load_quotes

    _as_role("support")
    qid, _created = _create_noted_quote(event_seq)

    _as_role("viewer")
    model = vm.build_view_model()
    quote = _find_quote(model, qid)
    line = quote["serviceLines"][0]
    assert isinstance(line, dict)
    assert "note" in line and line["note"] is None
    assert line["sellUnit"] == SELL
    assert quote["customerNotes"] == [CUSTOMER_NOTE]

    _as_role("sales")
    vm.build_view_model()
    stored = load_quotes()[qid]
    assert stored["service_lines"][0]["note"] == NOTE_TEXT
    assert stored["service_lines"][0]["cost_unit"] == COST
