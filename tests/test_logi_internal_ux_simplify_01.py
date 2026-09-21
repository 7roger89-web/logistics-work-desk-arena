"""LOGI_INTERNAL_UX_SIMPLIFY_01 — focused backend acceptance.

Covers the parts of Issue #88 that live behind the dispatcher/projection:

    H–K. each quote service line carries an OPTIONAL ``Ghi chú`` that round
         trips create → fresh readback and edit → fresh readback, while the
         price/tax/margin/FX arithmetic stays byte-identical.
    P.   surviving backend-rendered links (handbook) route to surviving
         surfaces — no href to a removed top-level module.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_c1
from views import logi_sandbox


@pytest.fixture()
def staging():
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
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _line(**over):
    base = {
        "code": "DV-VC-TQ", "serviceName": "Cước xe TQ", "unit": "Lần", "qty": 2,
        "currency": "VND", "costUnit": 26000000, "sellUnit": 28500000, "taxPct": 8,
    }
    base.update(over)
    return base


def _create_payload(lines):
    return {
        "customerId": "CUST-ANPHAT", "salesOwner": "Minh Tú",
        "origin": "Bằng Tường", "destination": "KCN Quế Võ", "route": "Hữu Nghị",
        "incoterm": "DAP", "transportMode": "Road", "goodsDescription": "Linh kiện",
        "expectedDeliveryDate": "2026-09-20", "serviceLines": lines,
    }


def test_quote_line_note_survives_create_and_fresh_readback(staging, event_seq):
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line(note="giá đã gồm bốc xếp tại kho"),
        _line(code="DV-TQ", serviceName="Thông quan", sellUnit=3000000,
              costUnit=2500000, taxPct=8),  # note omitted entirely
    ]))
    assert out["ok"], out
    qid = out["id"]

    # Fresh backend read: the canonical document carries the note verbatim.
    doc = logi_c1.read_quote(qid)
    assert doc["service_lines"][0]["note"] == "giá đã gồm bốc xếp tại kho"
    assert doc["service_lines"][1]["note"] == ""

    # View-model projection (what the desk reads back) exposes it too.
    projected = [line["note"] for line in out["readback"]["serviceLines"]]
    assert projected == ["giá đã gồm bốc xếp tại kho", ""]


def test_quote_line_note_survives_edit_and_fresh_readback(staging, event_seq):
    out = _dispatch(event_seq, "quote_create", _create_payload([_line()]))
    assert out["ok"], out
    qid = out["id"]
    assert out["readback"]["serviceLines"][0]["note"] == ""

    out = _dispatch(event_seq, "quote_edit", {
        "id": qid,
        "serviceLines": [_line(note="khách yêu cầu giao trước 20/09")],
    })
    assert out["ok"], out
    assert out["readback"]["serviceLines"][0]["note"] == "khách yêu cầu giao trước 20/09"

    doc = logi_c1.read_quote(qid)
    assert doc["service_lines"][0]["note"] == "khách yêu cầu giao trước 20/09"

    # Clearing the note persists as blank (wholesale line replace), not stale.
    out = _dispatch(event_seq, "quote_edit", {"id": qid, "serviceLines": [_line()]})
    assert out["ok"], out
    assert out["readback"]["serviceLines"][0]["note"] == ""
    assert logi_c1.read_quote(qid)["service_lines"][0]["note"] == ""


def test_quote_note_leaves_commercial_arithmetic_unchanged(staging, event_seq):
    """The note is annotation only: identical money with/without it."""
    plain = _dispatch(event_seq, "quote_create", _create_payload([_line()]))
    noted = _dispatch(event_seq, "quote_create", _create_payload([
        _line(note="ghi chú dài có dấu tiếng Việt — 123"),
    ]))
    assert plain["ok"] and noted["ok"], (plain, noted)
    calc_keys = (
        "sellingPriceTotalVnd", "estimatedCostVnd", "estimatedMarginVnd",
    )
    for key in calc_keys:
        assert noted["readback"][key] == plain["readback"][key], key
    assert logi_c1.read_quote(noted["id"])["calculation"] == \
        logi_c1.read_quote(plain["id"])["calculation"]


def test_quote_projection_defaults_legacy_line_without_note():
    """Old persisted lines (no ``note`` key) project as blank, never crash."""
    projected = logi_c1.quote_projection({
        "id": "Q-LEGACY", "quote_no": "QT-LEGACY", "status": "DRAFT",
        "service_lines": [{"code": "DV-X", "service_name": "X cũ"}],
    })
    assert projected["serviceLines"][0]["note"] == ""


def test_handbook_links_avoid_removed_top_level_modules():
    """Surviving backend-rendered links route to surviving surfaces only."""
    from views import handbook as hb

    projection = hb.handbook_projection()
    hrefs = [
        link.get("href", "")
        for section in projection["sections"]
        for entry in section["entries"]
        for link in entry.get("links", [])
    ]
    assert hrefs, "handbook carries no links at all"
    removed = [h for h in hrefs if h in {"/viec-can-xu-ly", "/theo-doi", "/thoa-thuan-ban-giao"}]
    assert removed == [], f"handbook still routes to removed modules: {removed}"
