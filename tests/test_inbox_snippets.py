"""Issue #212 — Bể thông tin / ghi nhanh.

Synthetic capture → persist → search/filter → link. Isolated mongomock only.
Does not touch production, does not book payments, does not alter team_note.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from views import logi_inbox
from views import logi_sandbox
from views import logi_view_model as vm


CONTRACT_ID = "HDMB-0306"

# Synthetic only — no real bank IDs, accounts, or customer chat.
SNIPPETS = [
    ("usd-1", "H-TEST USD remittance 1 — SYN-USD-001 TESTBANK credit"),
    ("usd-2", "H-TEST USD remittance 2 — SYN-USD-002 TESTBANK credit"),
    ("cny-in-1", "H-TEST China received 1 — SYN-CNY-IN-001 conversion"),
    ("cny-in-2", "H-TEST China received 2 — SYN-CNY-IN-002 conversion"),
    ("rmb-1", "H-TEST factory RMB payout 1 — SYN-RMB-001"),
    ("rmb-2", "H-TEST factory RMB payout 2 — SYN-RMB-002"),
    ("rmb-3", "H-TEST factory RMB payout 3 — SYN-RMB-003"),
    ("rmb-4", "H-TEST factory RMB payout 4 — SYN-RMB-004"),
    ("rmb-5", "H-TEST factory RMB payout 5 — SYN-RMB-005"),
    ("rmb-6", "H-TEST factory RMB payout 6 — SYN-RMB-006"),
]
UNRELATED = ("unrelated", "Lunch order SYN-MISC — weather chat, independent snippet")


@pytest.fixture()
def staging():
    import streamlit as st

    previous = st.session_state.get("current_user")
    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    logi_sandbox.reset_backend()
    if previous is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = previous


def _as(role: str, username: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username,
        "full_name": username,
        "role": role,
        "user_id": f"ID-{username}",
    }


def _dispatch(session: dict, seq: int, name: str, payload: dict) -> dict:
    outcomes = logi_inbox.consume_inbox_triggers(
        session, {name: {"seq": seq, "event": name, "payload": payload}}
    )
    assert len(outcomes) == 1
    return outcomes[0]


def _create(session: dict, seq: int, request_id: str, text: str, **extra) -> dict:
    payload = {"requestId": request_id, "rawText": text, **extra}
    return _dispatch(session, seq, "inbox_snippet_create", payload)


def test_events_are_wired_and_do_not_look_like_handbook_authoring(staging):
    assert logi_inbox.INBOX_EVENTS <= vm.ALL_EVENTS
    assert "inbox_snippet_create" in vm.ALL_EVENTS
    assert "inbox_snippet_link" in vm.ALL_EVENTS
    # Handbook authoring must stay absent; names must not contain "note".
    assert not any("note" in name for name in logi_inbox.INBOX_EVENTS)


def test_capture_eleven_snippets_refresh_link_and_team_note(staging):
    from core.database import (
        get_db,
        load_audit_logs,
        load_inbox_snippets,
        load_quick_note,
        save_quick_note,
    )

    assert save_quick_note("legacy team sticky SYN-TEAM")
    before_tx = get_db()["financial_transactions"].count_documents({})
    before_ct = get_db()["contract_transactions"].count_documents({})

    session = {"seq": 0}
    # Arbitrary order: RMB payouts, then USD, then China received, then leftover.
    order = [
        SNIPPETS[4], SNIPPETS[0], SNIPPETS[5], SNIPPETS[2], SNIPPETS[6],
        SNIPPETS[1], SNIPPETS[7], SNIPPETS[3], SNIPPETS[8], SNIPPETS[9],
        UNRELATED,
    ]
    created = {}
    for index, (key, text) in enumerate(order, start=1):
        out = _create(session, index, f"REQ-{key}", text, source="bank" if "USD" in text or "RMB" in text or "CNY" in text else "other")
        assert out["ok"], out
        assert out["readback"]["rawText"] == text
        assert out["readback"]["amount"] is None
        assert out["readback"]["fxRate"] is None
        assert out["readback"]["currency"] == ""
        assert out["readback"]["unverified"] is True
        assert out["readback"]["linked"] is False
        created[key] = out["id"]

    rows = load_inbox_snippets()
    assert len(rows) == 11
    assert all(row["id"] != "team_note" for row in rows)
    assert [row["id"] for row in rows] == [row["id"] for row in sorted(rows, key=lambda r: str(r.get("created_at")), reverse=True)]

    note, _updated = load_quick_note()
    assert note == "legacy team sticky SYN-TEAM"

    model = vm.build_view_model()
    inbox = model["inbox"]
    assert inbox["count"] == 11
    assert inbox["unlinkedCount"] == 11
    assert all(item["id"] != "team_note" for item in inbox["snippets"])
    assert any("H-TEST" in item["rawText"] for item in inbox["snippets"])
    leftover = next(item for item in inbox["snippets"] if item["id"] == created["unrelated"])
    assert leftover["linked"] is False

    linked_ids = [created[key] for key, _text in SNIPPETS]
    out = _dispatch(session, 20, "inbox_snippet_link", {
        "requestId": "REQ-LINK-CONTRACT",
        "snippetIds": linked_ids,
        "action": "link",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert out["ok"], out
    assert len(out["readback"]["snippets"]) == 10

    refreshed = vm.build_view_model()["inbox"]
    assert refreshed["count"] == 11
    assert refreshed["linkedCount"] == 10
    assert refreshed["unlinkedCount"] == 1
    linked_now = [item for item in refreshed["snippets"] if item["id"] in set(linked_ids)]
    assert all(CONTRACT_ID in item["contractIds"] for item in linked_now)
    leftover = next(item for item in refreshed["snippets"] if item["id"] == created["unrelated"])
    assert leftover["linked"] is False
    assert leftover["contractIds"] == []

    # Optional snippet-to-snippet link (credit ↔ remittance), still not 1:1 accounting.
    out = _dispatch(session, 21, "inbox_snippet_link", {
        "requestId": "REQ-LINK-SNIPPET",
        "snippetIds": [created["cny-in-1"]],
        "action": "link",
        "targetType": "snippet",
        "targetId": created["usd-1"],
    })
    assert out["ok"], out
    peer = load_inbox_snippets()
    by_id = {row["id"]: row for row in peer}
    assert created["usd-1"] in by_id[created["cny-in-1"]]["linked_snippet_ids"]
    assert created["cny-in-1"] in by_id[created["usd-1"]]["linked_snippet_ids"]
    assert by_id[created["cny-in-1"]]["raw_text"] == SNIPPETS[2][1]

    out = _dispatch(session, 22, "inbox_snippet_link", {
        "requestId": "REQ-UNLINK",
        "snippetIds": [created["rmb-1"]],
        "action": "unlink",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert out["ok"], out
    assert CONTRACT_ID not in (load_inbox_snippets() and next(r for r in load_inbox_snippets() if r["id"] == created["rmb-1"])["contract_ids"])

    out = _dispatch(session, 23, "inbox_snippet_link", {
        "requestId": "REQ-RELINK",
        "snippetIds": [created["rmb-1"]],
        "action": "link",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert out["ok"], out
    relinked = next(r for r in load_inbox_snippets() if r["id"] == created["rmb-1"])
    assert CONTRACT_ID in relinked["contract_ids"]
    assert relinked["raw_text"] == SNIPPETS[4][1]

    contract_vm = next(c for c in vm.build_view_model()["contracts"] if c["id"] == CONTRACT_ID)
    linked_on_contract = [
        item for item in vm.build_view_model()["inbox"]["snippets"]
        if CONTRACT_ID in item["contractIds"]
    ]
    assert len(linked_on_contract) == 10
    assert contract_vm["id"] == CONTRACT_ID

    audit = load_audit_logs("inbox_snippet", created["usd-1"])
    assert any(row.get("action") == "create" for row in audit)
    assert any(row.get("action") == "link_contract" for row in audit)
    assert get_db()["financial_transactions"].count_documents({}) == before_tx
    assert get_db()["contract_transactions"].count_documents({}) == before_ct
    assert load_quick_note()[0] == "legacy team sticky SYN-TEAM"


def test_idempotent_create_and_seq_replay(staging):
    from core.database import load_inbox_snippets

    session = {"seq": 0}
    first = _create(session, 1, "REQ-DUP", "H-TEST synthetic once")
    assert first["ok"] and not first.get("duplicate")
    second = _create(session, 2, "REQ-DUP", "H-TEST synthetic once")
    assert second["ok"] and second.get("duplicate")
    assert second["id"] == first["id"]
    assert len(load_inbox_snippets()) == 1

    replay = logi_inbox.consume_inbox_triggers(
        session,
        {"inbox_snippet_create": {"seq": 2, "event": "inbox_snippet_create", "payload": {
            "requestId": "REQ-DUP", "rawText": "H-TEST synthetic once",
        }}},
    )
    assert replay == []
    assert len(load_inbox_snippets()) == 1


def test_double_save_lock_does_not_create_blank_or_overwrite_original(staging):
    from core.database import create_inbox_snippet, load_inbox_snippet

    blank = create_inbox_snippet(raw_text="  ", request_id="REQ-BLANK")
    assert not blank["ok"]
    original = create_inbox_snippet(raw_text="H-TEST original SYN", request_id="REQ-ORIG")
    assert original["ok"]
    snippet_id = original["snippet"]["id"]
    from core.database import relate_inbox_snippets
    relate_inbox_snippets(
        snippet_ids=[snippet_id],
        action="link",
        target_type="contract",
        target_id=CONTRACT_ID,
        request_id="REQ-ORIG-LINK",
    )
    fresh = load_inbox_snippet(snippet_id)
    assert fresh["raw_text"] == "H-TEST original SYN"


def test_rbac_viewer_cannot_write(staging):
    session = {"seq": 0}
    _as("viewer", "viewer")
    out = _create(session, 1, "REQ-VIEWER", "H-TEST should be refused")
    assert not out["ok"]
    assert "quyền" in (out.get("error") or "").lower() or "RBAC" in (out.get("error") or "")

    import streamlit as st
    st.session_state.pop("current_user", None)
    out = _create({"seq": 0}, 1, "REQ-ANON", "H-TEST anonymous")
    assert not out["ok"]

    _as("SUPPORT", "staging.support")


def test_view_model_inbox_slice_empty_on_fresh_staging(staging):
    model = vm.build_view_model()
    assert "inbox" in model
    assert model["inbox"]["unverified"] is True
    assert model["inbox"]["canWrite"] is True
    assert isinstance(model["inbox"]["snippets"], list)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required for the shell DOM lane")
def test_dom_acceptance_inbox_desktop_and_mobile():
    root = Path(__file__).resolve().parents[1]
    bundle = root / "component" / "dist" / "logi-shell.js"
    script = root / "tests" / "component" / "dom_acceptance_inbox_snippets.mjs"
    assert bundle.is_file(), "component bundle missing — npm run build in component/"
    result = subprocess.run(
        ["node", str(script)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
    assert result.returncode == 0, "inbox DOM acceptance failed"
    assert "6 checks passed" in result.stdout
