"""LOGI-SEC-NESTED-COST-LEAK-20261106 — nested cost leak in C1 projections.

The commercial-boundary round closed the top-level quote/agreement fields,
but the NESTED objects still carried cost data to actors with
``commercial_view`` but WITHOUT ``commercial_write`` (Viewer, legacy Sales):

* Finding A — ``excelQuote.options[A/B]``: ``_calculate_excel_quote`` prices
  each option's service lines with ``calculate_quote``, so every line carries
  ``cost_total`` / ``cost_vnd`` / ``calculation_basis`` (a string that EMBEDS
  the cost figure as "; chi phí ...") / ``internal_note`` / ``cost_source``,
  and each option's ``calculation`` carries ``estimated_cost_vnd`` /
  ``estimated_margin_vnd`` / ``estimated_margin_pct``. The old
  ``_restricted_excel_quote`` cleared only ``source_costs`` and
  ``cost_unit``.
* Finding B — ``agreement.commercialSnapshot.serviceLines``:
  ``_services_from_quote`` copies the quote's priced lines, so each line
  carries ``calculation_snapshot.calculation_basis`` (same cost-embedding
  string) and ``source_reference`` (= the cost-source text). The old
  ``_restricted_agreement`` cleared only ``estimated_margin_vnd``.

Proven here, on the isolated staging database (mongomock), through the REAL
``build_view_model`` path, the REAL C1 handlers and the REAL
``calculate_quote`` — no mocked view model, no fake renderer payload.
Production database is never touched.

Sentinels are distinct values that do not collide with the staging bank
account numbers (0123456789 / 9876543210), the fixture's real cost
(31800000) or each other. The recursive JSON scan runs on the EXACT
protected branch (``excelQuote``, ``commercialSnapshot``, the replayed
readback) — never on the whole model, so a bank-account substring elsewhere
cannot false-positive. ``calculation_basis`` is asserted None field-level
(the string embeds the figure); the scan proves the figure itself is gone
from every nested copy.

    XCOST_A=51234567, XSELL_A=91234567, XMARGIN_A=40000000,
    XCOST_B=62345678, XSELL_B=87654321, XMARGIN_B=25308643,
    XNOTE_A="NOTE-COST-A-9871", XSRC_A="SRC-COST-A-9872",
    XNOTE_B="NOTE-COST-B-9873", XSRC_B="SRC-COST-B-9874",
    fixture real cost 31800000 (source_costs).

Classification decisions pinned here (see FOCUSED-REVIEW.md):
* excelQuote top-level ``calculation`` (goods/estimate VND) and ``customs``
  (duty/vat ESTIMATE) stay — sell-side customer-facing estimate, a different
  fact from the F-1 ACTUAL duty/VAT (shipments[].importInfo, finance_view).
* ``unknown_reasons`` ("Chưa biết tổng chi phí...") stays — it states cost
  is UNKNOWN and carries no figure and no source.
* Per-line ``rate_snapshot_id`` / ``rate_row_id`` stay — identifiers, no
  money, no lookup path in the payload for the restricted actor.
"""

from __future__ import annotations

import base64
import json

import pytest

from scripts.make_luc_giac_quote_fixture import build_luc_giac_fixture
from views import logi_c1, logi_sandbox
from views import logi_view_model as vm

# Distinct sentinels (see module docstring for the collision rule).
XCOST_A = 51234567
XSELL_A = 91234567
XMARGIN_A = 40000000
XCOST_B = 62345678
XSELL_B = 87654321
XMARGIN_B = 25308643
XNOTE_A = "NOTE-COST-A-9871"
XSRC_A = "SRC-COST-A-9872"
XNOTE_B = "NOTE-COST-B-9873"
XSRC_B = "SRC-COST-B-9874"
FIXTURE_COST = "31800000"

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
    db.customers.insert_one({"id": "CUST-LUCGIAC-TEST", "name": "Công ty Lục Giác"})
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
    """Needles found anywhere in the JSON rendering of ONE protected branch.

    A hit means a cost figure or a cost string survived in that branch.
    Numbers render as e.g. 51234567.0, so the needle is the digit string.
    """
    text = json.dumps(branch, default=str, ensure_ascii=False)
    return [n for n in needles if str(n) in text]


COST_NEEDLES = [str(XCOST_A), str(XCOST_B), XNOTE_A, XSRC_A, XNOTE_B, XSRC_B]
MARGIN_NEEDLES = [str(XMARGIN_A), str(XMARGIN_B)]


def _costed_details(seq_fn):
    """Real fixture workbook parsed by the real import, then BOTH options
    costed with distinct sentinel lines (real calculate_quote prices them).
    Run as Support (sales_write). Returns (details, source_bytes)."""
    source = build_luc_giac_fixture()
    out = _dispatch_c1(seq_fn, "quote_import_excel", {
        "customerId": "CUST-LUCGIAC-TEST", "fileName": "luc-giac-fixture.xlsx",
        "base64": base64.b64encode(source).decode(), "requestId": "NEST-IMP-1"})
    assert out["ok"], out
    details = out["readback"]
    assert details["source_costs"], "fixture must parse real source_costs"
    details["options"]["A"]["service_lines"] = [{
        "id": "fee-a", "service_name": "Vận chuyển A", "qty": 1, "unit": "Lần",
        "currency": "VND", "cost_unit": XCOST_A, "sell_unit": XSELL_A,
        "sell_confirmed": True, "tax_pct": None,
        "internal_note": XNOTE_A, "cost_source": XSRC_A}]
    details["options"]["A"]["scope"] = "Sentinel scope A"
    details["options"]["B"]["service_lines"] = [{
        "id": "fee-b", "service_name": "Vận chuyển B", "qty": 1, "unit": "Lần",
        "currency": "VND", "cost_unit": XCOST_B, "sell_unit": XSELL_B,
        "sell_confirmed": True, "tax_pct": None,
        "internal_note": XNOTE_B, "cost_source": XSRC_B}]
    details["options"]["B"]["scope"] = "Sentinel scope B"
    return details, source


def _create_costed_quote(seq_fn):
    """Real import + real quote_create with both options costed. Returns the
    created quote id. Run as Support."""
    details, _source = _costed_details(seq_fn)
    created = _dispatch_c1(seq_fn, "quote_create", {
        "customerId": "CUST-LUCGIAC-TEST", "salesOwner": "Sale test",
        "goodsDescription": "Bàn họp văn phòng", "incoterm": "EXW",
        "transportMode": "Sea", "excelQuote": details, "fx": {},
        "requestId": "NEST-CREATE-1"})
    assert created["ok"], created
    return created["id"]


def _create_costed_agreement(seq_fn, qid):
    """Drive the costed quote to ACCEPTED through the real transition
    handler, then create the agreement through the real handler. Returns
    the agreement id. Run as Support."""
    for target in ("READY_FOR_REVIEW", "ACCEPTED"):
        out = _dispatch_c1(seq_fn, "quote_transition", {
            "id": qid, "nextStatus": target, "requestId": f"NEST-TR-{target}"})
        assert out["ok"], out
    out = _dispatch_c1(seq_fn, "agreement_create", {
        "quoteId": qid, "requestId": "NEST-AGR-1"})
    assert out["ok"], out
    return out["id"]


def _find_quote(model, qid):
    found = [q for q in model["quotes"] if q.get("id") == qid]
    assert len(found) == 1, f"quote {qid} must appear exactly once, got {len(found)}"
    return found[0]


def _find_agreement(model, aid):
    found = [a for a in model["agreements"] if a.get("id") == aid]
    assert len(found) == 1, f"agreement {aid} must appear exactly once, got {len(found)}"
    return found[0]


def _store_last_writes(outcomes) -> None:
    import streamlit as st

    st.session_state["logi_last_writes"] = list(outcomes)


def _last_write(model, event):
    rows = [r for r in model["lastWrites"] if r.get("event") == event]
    assert len(rows) == 1, f"exactly one {event} outcome expected, got {len(rows)}"
    return rows[0]


def _assert_excel_options_restricted(xq, role):
    """Both options A and B: every nested cost figure/string is gone, sell
    prices and structure survive."""
    assert _scan_branch(xq, COST_NEEDLES + MARGIN_NEEDLES) == [], role
    assert xq["source_costs"] == [], role
    for key, cost, sell in (("A", XCOST_A, XSELL_A), ("B", XCOST_B, XSELL_B)):
        opt = xq["options"][key]
        line = opt["service_lines"][0]
        assert line["cost_unit"] is None, (role, key)
        assert line["cost_total"] is None, (role, key)
        assert line["cost_vnd"] is None, (role, key)
        assert line["calculation_basis"] is None, (role, key)
        assert line["internal_note"] is None, (role, key)
        assert line["cost_source"] is None, (role, key)
        assert line["sell_unit"] == sell, (role, key)
        assert line["sell_total"] == sell, (role, key)
        assert line["sell_vnd"] == sell, (role, key)
        calc = opt["calculation"]
        assert calc["estimated_cost_vnd"] is None, (role, key)
        assert calc["estimated_margin_vnd"] is None, (role, key)
        assert calc["estimated_margin_pct"] is None, (role, key)
        assert calc["selling_price_before_tax_vnd"] == sell, (role, key)


def _assert_excel_options_full(xq, role):
    """Privileged actor: the nested cost data is intact, both options."""
    assert _scan_branch(xq["options"]["A"], [str(XCOST_A), XNOTE_A, XSRC_A]) != [], role
    for key, cost, sell, margin in (
            ("A", XCOST_A, XSELL_A, XMARGIN_A), ("B", XCOST_B, XSELL_B, XMARGIN_B)):
        opt = xq["options"][key]
        line = opt["service_lines"][0]
        assert line["cost_unit"] == cost, (role, key)
        assert line["cost_total"] == cost, (role, key)
        assert line["cost_vnd"] == cost, (role, key)
        assert f"chi phí {cost}" in (line["calculation_basis"] or ""), (role, key)
        assert line["sell_unit"] == sell, (role, key)
        calc = opt["calculation"]
        assert calc["estimated_cost_vnd"] == cost, (role, key)
        assert calc["estimated_margin_vnd"] == margin, (role, key)
        assert calc["estimated_margin_pct"] is not None, (role, key)


# ---------------------------------------------------------------------------
# Tests — model paths (Finding A + Finding B)
# ---------------------------------------------------------------------------

def test_nested_excel_cost_stripped_for_viewer(staging, event_seq):
    """Finding A: Viewer/legacy Sales receive NO nested cost figure or cost
    string from either excelQuote option; sell prices, goods and structure
    survive. Admin/Support/Sale keep the full nested data. Accounting and
    Operations receive no C1 quotes at all."""
    _as_role("support")
    qid = _create_costed_quote(event_seq)

    for role in ("admin", "support", "sale"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model, qid)
        _assert_excel_options_full(quote["excelQuote"], role)
        assert quote["excelQuote"]["source_costs"], role
        # Top-level sell-side estimate is customer-facing and stays.
        assert quote["excelQuote"]["goods"], role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model, qid)
        _assert_excel_options_restricted(quote["excelQuote"], role)
        # Goods table + source facts stay (documented classification).
        assert quote["excelQuote"]["goods"], role
        assert quote["excelQuote"]["source_facts"], role
        # Top-level quote fields were already gated in the previous round.
        assert quote["serviceLines"][0]["costUnit"] is None, role
        assert quote["serviceLines"][0]["sellUnit"] == XSELL_A, role

    for role in ("accounting", "operations"):
        _as_role(role)
        model = vm.build_view_model()
        assert model["quotes"] == [], f"{role} must receive no C1 quotes"


def test_nested_agreement_cost_strings_stripped(staging, event_seq):
    """Finding B: the agreement's service lines must not carry the cost
    basis string or the cost-source text to Viewer/legacy Sales; the sell
    terms survive. Admin/Support/Sale keep the full snapshot."""
    _as_role("support")
    qid = _create_costed_quote(event_seq)
    aid = _create_costed_agreement(event_seq, qid)

    for role in ("admin", "support", "sale"):
        _as_role(role)
        model = vm.build_view_model()
        agreement = _find_agreement(model, aid)
        line = agreement["commercialSnapshot"]["serviceLines"][0]
        assert f"chi phí {XCOST_A}" in line["calculation_snapshot"]["calculation_basis"], role
        assert line["source_reference"] == XSRC_A, role
        assert line["sell_unit"] == XSELL_A, role
        assert line["calculation_snapshot"]["sell_total"] == XSELL_A, role
        summary = agreement["commercialSnapshot"]["calculationSummary"]
        assert summary["estimated_margin_vnd"] == XMARGIN_A, role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        agreement = _find_agreement(model, aid)
        snap = agreement["commercialSnapshot"]
        assert _scan_branch(snap, [str(XCOST_A), XSRC_A, str(XMARGIN_A)]) == [], role
        line = snap["serviceLines"][0]
        assert line["calculation_snapshot"]["calculation_basis"] is None, role
        assert line["source_reference"] is None, role
        assert line["sell_unit"] == XSELL_A, role
        assert line["calculation_snapshot"]["sell_total"] == XSELL_A, role
        assert snap["calculationSummary"]["estimated_margin_vnd"] is None, role

    for role in ("accounting", "operations"):
        _as_role(role)
        model = vm.build_view_model()
        agreement = _find_agreement(model, aid)
        assert agreement["commercialSnapshot"]["serviceLines"] == [], role
        assert agreement["commercialSnapshot"]["calculationSummary"] == {}, role


# ---------------------------------------------------------------------------
# Tests — lastWrites replay (downgrade, same session)
# ---------------------------------------------------------------------------

def test_downgrade_quote_transition_readback_no_nested_cost(staging, event_seq):
    """A quote_transition outcome recorded as Support must not replay nested
    Excel cost figures/strings to a downgraded actor."""
    _as_role("support")
    qid = _create_costed_quote(event_seq)
    out = _dispatch_c1(event_seq, "quote_transition", {
        "id": qid, "nextStatus": "READY_FOR_REVIEW", "requestId": "NEST-TR-1"})
    assert out["ok"], out
    assert f"chi phí {XCOST_A}" in out["readback"]["excelQuote"]["options"]["A"]["service_lines"][0]["calculation_basis"]
    _store_last_writes([out])

    for role in ("operations", "accounting"):
        _as_role(role)
        model = vm.build_view_model()
        assert _last_write(model, "quote_transition")["readback"] == {}, role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        readback = _last_write(model, "quote_transition")["readback"]
        _assert_excel_options_restricted(readback["excelQuote"], role)
        assert readback["serviceLines"][0]["sellUnit"] == XSELL_A, role
        row = _last_write(model, "quote_transition")
        assert row["ok"] is True and row["requestId"] == "NEST-TR-1"


def test_downgrade_agreement_transition_readback_no_cost_strings(staging, event_seq):
    """An agreement_transition outcome recorded as Support must not replay
    the cost basis string or cost-source text to a downgraded actor."""
    _as_role("support")
    qid = _create_costed_quote(event_seq)
    aid = _create_costed_agreement(event_seq, qid)
    out = _dispatch_c1(event_seq, "agreement_transition", {
        "id": aid, "nextStatus": "REVIEWING", "requestId": "NEST-AGR-TR-1"})
    assert out["ok"], out
    snap = out["readback"]["commercialSnapshot"]
    assert f"chi phí {XCOST_A}" in snap["serviceLines"][0]["calculation_snapshot"]["calculation_basis"]
    _store_last_writes([out])

    _as_role("operations")
    model = vm.build_view_model()
    readback = _last_write(model, "agreement_transition")["readback"]
    assert readback["commercialSnapshot"]["serviceLines"] == []
    assert readback["commercialSnapshot"]["calculationSummary"] == {}
    assert readback["id"] == aid  # shell identity survives

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        readback = _last_write(model, "agreement_transition")["readback"]
        snap = readback["commercialSnapshot"]
        assert _scan_branch(snap, [str(XCOST_A), XSRC_A, str(XMARGIN_A)]) == [], role
        line = snap["serviceLines"][0]
        assert line["calculation_snapshot"]["calculation_basis"] is None, role
        assert line["source_reference"] is None, role
        assert line["calculation_snapshot"]["sell_total"] == XSELL_A, role
        assert snap["calculationSummary"]["estimated_margin_vnd"] is None, role
        row = _last_write(model, "agreement_transition")
        assert row["ok"] is True


def test_downgrade_quote_preview_readback_no_nested_cost(staging, event_seq):
    """A quote_preview outcome recorded as Support must not replay nested
    Excel cost data to a downgraded actor; the customer snapshot is
    untouched (it never carried cost)."""
    _as_role("support")
    details, _source = _costed_details(event_seq)
    out = _dispatch_c1(event_seq, "quote_preview", {
        "customerId": "CUST-LUCGIAC-TEST", "excelQuote": details, "fx": {},
        "requestId": "NEST-PREV-1"})
    assert out["ok"], out
    assert f"chi phí {XCOST_A}" in out["readback"]["quote"]["excelQuote"]["options"]["A"]["service_lines"][0]["calculation_basis"]
    _store_last_writes([out])

    for role in ("operations", "accounting"):
        _as_role(role)
        model = vm.build_view_model()
        assert _last_write(model, "quote_preview")["readback"] == {}, role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        readback = _last_write(model, "quote_preview")["readback"]
        _assert_excel_options_restricted(readback["quote"]["excelQuote"], role)
        assert readback["customer"], "customer snapshot survives"
        row = _last_write(model, "quote_preview")
        assert row["ok"] is True and row["requestId"] == "NEST-PREV-1"


def test_downgrade_quote_import_readback_no_nested_cost(staging, event_seq):
    """A quote_import_excel outcome (real parsed fixture workbook, real
    priced options) recorded as Support must not replay source costs or
    nested cost figures to Viewer; Sale keeps the real fixture cost."""
    _as_role("support")
    source = build_luc_giac_fixture()
    out = _dispatch_c1(event_seq, "quote_import_excel", {
        "customerId": "CUST-LUCGIAC-TEST", "fileName": "luc-giac-fixture.xlsx",
        "base64": base64.b64encode(source).decode(), "requestId": "NEST-IMP-2"})
    assert out["ok"], out
    assert out["readback"]["source_costs"], "fixture must parse real source_costs"
    assert FIXTURE_COST in json.dumps(out["readback"], default=str)
    _store_last_writes([out])

    _as_role("viewer")
    model = vm.build_view_model()
    readback = _last_write(model, "quote_import_excel")["readback"]
    assert readback["source_costs"] == []
    assert _scan_branch(readback, [FIXTURE_COST]) == []
    assert readback["goods"], "goods table survives"

    _as_role("sale")
    model = vm.build_view_model()
    readback = _last_write(model, "quote_import_excel")["readback"]
    assert readback["source_costs"], "Sale keeps the real source costs"
    assert FIXTURE_COST in json.dumps(readback["source_costs"], default=str)


def test_restricted_nested_payload_ui_shape(staging, event_seq):
    """Restricted nested payloads stay UI-safe: options A/B and their
    calculations are present as dicts, service lines stay lists with sell
    figures, the agreement keeps its sell lines — restricted money is None,
    never 0, and nothing the UI iterates over becomes None."""
    _as_role("support")
    qid = _create_costed_quote(event_seq)
    aid = _create_costed_agreement(event_seq, qid)

    _as_role("viewer")
    model = vm.build_view_model()
    quote = _find_quote(model, qid)
    xq = quote["excelQuote"]
    assert set(xq["options"].keys()) == {"A", "B"}
    for key in ("A", "B"):
        opt = xq["options"][key]
        assert isinstance(opt["service_lines"], list) and len(opt["service_lines"]) == 1
        assert isinstance(opt["calculation"], dict)
        assert opt["calculation"]["selling_price_before_tax_vnd"] is not None
        assert opt["calculation"]["estimated_cost_vnd"] is None  # None, never 0
        assert opt["calculation"]["estimated_margin_vnd"] is None
    agreement = _find_agreement(model, aid)
    lines = agreement["commercialSnapshot"]["serviceLines"]
    assert isinstance(lines, list) and len(lines) == 1
    assert lines[0]["calculation_snapshot"]["sell_total"] == XSELL_A
    assert lines[0]["calculation_snapshot"]["calculation_basis"] is None
