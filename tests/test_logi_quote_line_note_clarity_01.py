"""LOGI_QUOTE_LINE_NOTE_CLARITY_01 — per-service-line note ownership (Issue #90).

Issue #88 already proved that ONE quote line's optional ``Ghi chú`` round trips
through the canonical writers. Issue #90 is about *ownership clarity*: when a
quote has SEVERAL service lines, every line must own exactly one note, and no
note may leak, migrate, or become a hidden quote-level shared note.

This focused lane proves the multi-line authority behind the UI:

    LINE 1 NOTE=A / LINE 2 NOTE=B
      create  -> fresh readback -> line1=A, line2=B
      edit line2=B2 -> fresh readback -> line1 STILL=A, line2=B2
      delete line1 -> surviving line keeps ITS OWN note (B2), A disappears
      add a line -> that line starts with its own blank note

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. Production is never touched; no writer, field, or
schema is added by this task.
"""

from __future__ import annotations

import json

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


def _line(code: str, name: str, sell: int, cost: int, note: str | None = None) -> dict:
    """One UI service-line draft exactly as the Báo Giá card submits it."""
    line = {
        "code": code, "serviceName": name, "unit": "Lần", "qty": 1,
        "currency": "VND", "costUnit": cost, "sellUnit": sell, "taxPct": 8,
    }
    if note is not None:
        line["note"] = note
    return line


NOTE_A = "Giá đã gồm bốc xếp"
NOTE_B = "Chưa gồm kiểm hóa"
NOTE_B2 = "Chưa gồm kiểm hóa — khách tự làm"


def _create_payload(lines):
    return {
        "customerId": "CUST-ANPHAT", "salesOwner": "Minh Tú",
        "origin": "Bằng Tường", "destination": "KCN Quế Võ", "route": "Hữu Nghị",
        "incoterm": "DAP", "transportMode": "Road", "goodsDescription": "Linh kiện",
        "expectedDeliveryDate": "2026-09-20", "serviceLines": lines,
    }


def _notes(projection: dict) -> list[str]:
    return [line["note"] for line in projection["serviceLines"]]


def _persisted_notes(qid: str) -> list[str]:
    """Fresh backend read (bypasses any UI state)."""
    doc = logi_c1.read_quote(qid)
    return [line["note"] for line in doc["service_lines"]]


def test_two_lines_keep_distinct_notes_through_create_and_fresh_readback(staging, event_seq):
    """LINE 1 NOTE=A / LINE 2 NOTE=B -> readback keeps A on 1 and B on 2."""
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
        _line("DV-TQ", "Thông quan", 3000000, 2500000, NOTE_B),
    ]))
    assert out["ok"], out
    qid = out["id"]

    assert _notes(out["readback"]) == [NOTE_A, NOTE_B]
    assert _persisted_notes(qid) == [NOTE_A, NOTE_B]
    # The notes are attached to the lines they were typed into, not to slots.
    persisted = logi_c1.read_quote(qid)["service_lines"]
    assert [line["code"] for line in persisted] == ["DV-VC-TQ", "DV-TQ"]
    assert [line["service_name"] for line in persisted] == ["Cước xe TQ", "Thông quan"]
    assert [line["line_no"] for line in persisted] == [1, 2]
    assert [line["note"] for line in persisted] == [NOTE_A, NOTE_B]


def test_one_blank_line_never_inherits_another_line_note(staging, event_seq):
    """A note is never a quote-level shared value: an untouched line stays blank."""
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
        _line("DV-TQ", "Thông quan", 3000000, 2500000),  # note omitted entirely
    ]))
    assert out["ok"], out
    assert _notes(out["readback"]) == [NOTE_A, ""]
    assert _persisted_notes(out["id"]) == [NOTE_A, ""]


def test_edit_second_line_note_preserves_first_line_note_and_money(staging, event_seq):
    """LINE 2 NOTE=B -> B2 must not touch LINE 1's note or LINE 1's money."""
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
        _line("DV-TQ", "Thông quan", 3000000, 2500000, NOTE_B),
    ]))
    assert out["ok"], out
    qid = out["id"]
    before = logi_c1.read_quote(qid)
    line1_before = dict(before["service_lines"][0])
    calc_before = before["calculation"]

    out = _dispatch(event_seq, "quote_edit", {
        "id": qid,
        "serviceLines": [
            _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
            _line("DV-TQ", "Thông quan", 3000000, 2500000, NOTE_B2),
        ],
    })
    assert out["ok"], out

    # Fresh readback after the edit.
    assert _notes(out["readback"]) == [NOTE_A, NOTE_B2]
    assert _persisted_notes(qid) == [NOTE_A, NOTE_B2]

    after = logi_c1.read_quote(qid)
    line1_after = dict(after["service_lines"][0])
    assert line1_after["note"] == NOTE_A, "editing line 2 rewrote line 1's note"
    for key in ("code", "service_name", "qty", "currency", "cost_unit", "sell_unit",
                "tax_pct", "cost_total", "sell_total", "cost_vnd", "sell_vnd",
                "tax_vnd", "line_no"):
        assert line1_after[key] == line1_before[key], f"line 1 {key} changed"
    # A note-only edit is annotation: the quote arithmetic is byte-identical.
    assert after["calculation"] == calc_before


def test_delete_first_line_does_not_migrate_its_note_to_the_survivor(staging, event_seq):
    """Removing line 1 removes only that line and its own note."""
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
        _line("DV-TQ", "Thông quan", 3000000, 2500000, NOTE_B),
    ]))
    assert out["ok"], out
    qid = out["id"]

    # The UI sends the SAME surviving line object; note B travels with its line.
    out = _dispatch(event_seq, "quote_edit", {
        "id": qid,
        "serviceLines": [_line("DV-TQ", "Thông quan", 3000000, 2500000, NOTE_B)],
    })
    assert out["ok"], out

    lines = logi_c1.read_quote(qid)["service_lines"]
    assert len(lines) == 1
    assert lines[0]["code"] == "DV-TQ"
    assert lines[0]["note"] == NOTE_B, "the surviving line lost or inherited a note"
    assert lines[0]["line_no"] == 1
    # The deleted line's note must not survive anywhere in the stored document.
    dumped = json.dumps(logi_c1.read_quote(qid), ensure_ascii=False, default=str)
    assert NOTE_A not in dumped
    assert _notes(out["readback"]) == [NOTE_B]


def test_note_count_tracks_line_count_across_add_and_remove(staging, event_seq):
    """3 lines own 3 notes; removing the middle one leaves the other two intact."""
    n1, n2, n3 = "ghi chú dòng 1", "ghi chú dòng 2", "ghi chú dòng 3"
    out = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-1", "Cước xe TQ", 1000000, 900000, n1),
        _line("DV-2", "Thông quan", 2000000, 1900000, n2),
        _line("DV-3", "Bốc xếp", 3000000, 2900000, n3),
    ]))
    assert out["ok"], out
    qid = out["id"]
    assert _notes(out["readback"]) == [n1, n2, n3]
    assert len(out["readback"]["serviceLines"]) == 3

    out = _dispatch(event_seq, "quote_edit", {
        "id": qid,
        "serviceLines": [
            _line("DV-1", "Cước xe TQ", 1000000, 900000, n1),
            _line("DV-3", "Bốc xếp", 3000000, 2900000, n3),
        ],
    })
    assert out["ok"], out
    assert _notes(out["readback"]) == [n1, n3]
    lines = logi_c1.read_quote(qid)["service_lines"]
    assert [line["line_no"] for line in lines] == [1, 2]
    assert [line["note"] for line in lines] == [n1, n3]


def test_note_is_not_a_new_persisted_field(staging, event_seq):
    """NEW_PERSISTED_FIELDS=0 — a noted line persists the SAME key set as a plain one."""
    noted = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000, NOTE_A),
    ]))
    plain = _dispatch(event_seq, "quote_create", _create_payload([
        _line("DV-VC-TQ", "Cước xe TQ", 28500000, 26000000),
    ]))
    assert noted["ok"] and plain["ok"], (noted, plain)

    keyed = set(logi_c1.read_quote(noted["id"])["service_lines"][0])
    bare = set(logi_c1.read_quote(plain["id"])["service_lines"][0])
    assert "note" in keyed and "note" in bare
    assert keyed == bare, f"note changed the persisted line schema: {keyed ^ bare}"
