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
    st.session_state.pop("logi_inbox_query", None)
    st.session_state.pop("logi_inbox_attachment_download", None)
    yield transport
    logi_sandbox.reset_backend()
    st.session_state.pop("logi_inbox_query", None)
    st.session_state.pop("logi_inbox_attachment_download", None)
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
    assert "inbox_snippet_attach" in vm.ALL_EVENTS
    assert "inbox_snippet_download" in vm.ALL_EVENTS
    assert "inbox_snippet_search" in vm.ALL_EVENTS
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
    assert model["inbox"]["canRead"] is True
    assert isinstance(model["inbox"]["snippets"], list)


def _jpeg_bytes() -> bytes:
    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (16, 12), (200, 24, 24)).save(buf, format="JPEG", quality=88)
    return buf.getvalue()


PDF_BYTES = b"%PDF-1.4\nsynthetic-inbox-pdf SYN-FILE\n%%EOF"


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _file_payload(name: str, mime: str, data: bytes) -> dict:
    return {"fileName": name, "mime": mime, "size": len(data), "base64": _b64(data)}


def _ensure_shipments() -> None:
    from core.database import get_db

    db = get_db()
    for sid in ("LO-TEST-1", "LO-TEST-2"):
        if db.shipments.find_one({"id": sid}) is None:
            db.shipments.insert_one({"id": sid, "is_deleted": False, "customer": "SYN customer"})


def _gridfs_count() -> int:
    from core.database import get_db
    from core.gridfs_client import GRIDFS_BUCKET

    db = get_db()
    try:
        return int(db[f"{GRIDFS_BUCKET}.files"].count_documents({}))
    except Exception:
        return 0


def test_mismatched_request_id_is_rejected(staging):
    from core.database import load_inbox_snippets

    session = {"seq": 0}
    first = _create(session, 1, "REQ-MISMATCH", "H-TEST original payload")
    assert first["ok"]
    second = _create(session, 2, "REQ-MISMATCH", "H-TEST different payload")
    assert not second["ok"]
    assert "nội dung khác" in (second.get("error") or "").lower()
    rows = load_inbox_snippets()
    assert len(rows) == 1
    assert rows[0]["raw_text"] == "H-TEST original payload"


def test_link_replay_does_not_resurrect_unlink(staging):
    from core.database import load_inbox_snippet

    session = {"seq": 0}
    created = _create(session, 1, "REQ-REL-1", "H-TEST replay link")
    snippet_id = created["id"]
    link = _dispatch(session, 2, "inbox_snippet_link", {
        "requestId": "REQ-OLD-LINK",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert link["ok"]
    unlink = _dispatch(session, 3, "inbox_snippet_link", {
        "requestId": "REQ-NEW-UNLINK",
        "snippetIds": [snippet_id],
        "action": "unlink",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert unlink["ok"]
    replay = _dispatch(session, 4, "inbox_snippet_link", {
        "requestId": "REQ-OLD-LINK",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert replay["ok"]
    fresh = load_inbox_snippet(snippet_id)
    assert CONTRACT_ID not in (fresh.get("contract_ids") or [])


def test_snippet_peer_failure_does_not_leave_one_sided_link(staging, monkeypatch):
    from core.database import get_db, load_inbox_snippet, relate_inbox_snippets
    from pymongo.errors import PyMongoError

    session = {"seq": 0}
    left = _create(session, 1, "REQ-PEER-A", "H-TEST peer A")
    right = _create(session, 2, "REQ-PEER-B", "H-TEST peer B")
    db = get_db()
    real = db.quick_notes.update_one
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise PyMongoError("synthetic peer fail")
        return real(*args, **kwargs)

    monkeypatch.setattr(db.quick_notes, "update_one", flaky)
    out = relate_inbox_snippets(
        snippet_ids=[left["id"]],
        action="link",
        target_type="snippet",
        target_id=right["id"],
        request_id="REQ-PEER-LINK",
    )
    assert not out["ok"]
    left_row = load_inbox_snippet(left["id"])
    right_row = load_inbox_snippet(right["id"])
    assert right["id"] not in (left_row.get("linked_snippet_ids") or [])
    assert left["id"] not in (right_row.get("linked_snippet_ids") or [])


def test_viewer_cannot_read_inbox_projection(staging):
    session = {"seq": 0}
    created = _create(session, 1, "REQ-SECRET", "H-TEST secret snippet")
    assert created["ok"]
    _as("viewer", "viewer")
    inbox = vm.build_view_model()["inbox"]
    assert inbox["canRead"] is False
    assert inbox["canWrite"] is False
    assert inbox["snippets"] == []
    assert inbox["count"] == 0


def test_search_finds_note_beyond_page(staging):
    session = {"seq": 0}
    needle = _create(session, 1, "REQ-NEEDLE", "NEEDLE-501-SYN unique older snippet")
    assert needle["ok"]
    for index in range(500):
        out = _create(session, index + 2, f"REQ-FILL-{index}", f"H-TEST filler {index:04d}")
        assert out["ok"], out
    model = vm.build_view_model()["inbox"]
    assert model["count"] >= 501
    assert len(model["snippets"]) <= 50
    assert model["hasMore"] is True
    assert all("NEEDLE-501-SYN" not in (row.get("rawText") or "") for row in model["snippets"])
    search = _dispatch(session, 600, "inbox_snippet_search", {
        "requestId": "REQ-SEARCH-NEEDLE",
        "query": "NEEDLE-501-SYN",
        "filter": "all",
    })
    assert search["ok"], search
    found = vm.build_view_model()["inbox"]
    assert any("NEEDLE-501-SYN" in (row.get("rawText") or "") for row in found["snippets"])


def test_jpeg_pdf_multi_link_same_file_id_and_unlink_keeps_bytes(staging):
    from core.database import get_db, load_inbox_snippet

    _ensure_shipments()
    jpeg = _jpeg_bytes()
    pdf = PDF_BYTES
    before_files = _gridfs_count()
    session = {"seq": 0}
    created = _dispatch(session, 1, "inbox_snippet_create", {
        "requestId": "REQ-FILES-1",
        "rawText": "",
        "files": [
            _file_payload("anh-dan.jpg", "image/jpeg", jpeg),
            _file_payload("scan.pdf", "application/pdf", pdf),
        ],
    })
    assert created["ok"], created
    assert not created.get("partial")
    snippet_id = created["id"]
    public = created["readback"]
    assert public["rawText"] == ""
    assert len(public["attachments"]) == 2
    public_blob = str(public)
    assert "storage_file_id" not in public_blob
    assert "sha256" not in public_blob.lower()
    for key in ("storage_file_id", "sha256", "drive_file_id"):
        assert key not in public
        assert all(key not in item for item in public["attachments"])
    stored = load_inbox_snippet(snippet_id)
    file_ids = [row["storage_file_id"] for row in stored["attachments"]]
    assert len(file_ids) == 2
    assert all(file_ids)
    assert _gridfs_count() == before_files + 2

    link_ship = _dispatch(session, 2, "inbox_snippet_link", {
        "requestId": "REQ-LINK-LO1",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "shipment",
        "targetId": "LO-TEST-1",
    })
    assert link_ship["ok"], link_ship
    link_hd = _dispatch(session, 3, "inbox_snippet_link", {
        "requestId": "REQ-LINK-HD",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "contract",
        "targetId": CONTRACT_ID,
    })
    assert link_hd["ok"], link_hd
    linked = load_inbox_snippet(snippet_id)
    assert linked["shipment_ids"] == ["LO-TEST-1"]
    assert CONTRACT_ID in linked["contract_ids"]
    assert [row["storage_file_id"] for row in linked["attachments"]] == file_ids

    inbox = vm.build_view_model()["inbox"]
    assert snippet_id in {row["id"] for row in inbox.get("byShipmentId", {}).get("LO-TEST-1", [])}
    assert snippet_id in {row["id"] for row in inbox.get("byContractId", {}).get(CONTRACT_ID, [])}

    unlink = _dispatch(session, 4, "inbox_snippet_link", {
        "requestId": "REQ-UNLINK-LO1",
        "snippetIds": [snippet_id],
        "action": "unlink",
        "targetType": "shipment",
        "targetId": "LO-TEST-1",
    })
    assert unlink["ok"], unlink
    after_unlink = load_inbox_snippet(snippet_id)
    assert "LO-TEST-1" not in (after_unlink.get("shipment_ids") or [])
    assert [row["storage_file_id"] for row in after_unlink["attachments"]] == file_ids
    assert _gridfs_count() == before_files + 2

    relink = _dispatch(session, 5, "inbox_snippet_link", {
        "requestId": "REQ-LINK-LO2",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "shipment",
        "targetId": "LO-TEST-2",
    })
    assert relink["ok"], relink
    after_lo2 = load_inbox_snippet(snippet_id)
    assert after_lo2["shipment_ids"] == ["LO-TEST-2"]
    assert [row["storage_file_id"] for row in after_lo2["attachments"]] == file_ids
    assert _gridfs_count() == before_files + 2

    download = _dispatch(session, 6, "inbox_snippet_download", {
        "requestId": "REQ-DOWN-1",
        "snippetId": snippet_id,
        "attachmentId": after_lo2["attachments"][1]["id"],
        "shipmentId": "LO-TEST-2",
    })
    assert download["ok"], download
    mismatch = _dispatch(session, 7, "inbox_snippet_download", {
        "requestId": "REQ-DOWN-BAD",
        "snippetId": snippet_id,
        "attachmentId": after_lo2["attachments"][1]["id"],
        "shipmentId": "LO-TEST-1",
    })
    assert not mismatch["ok"]
    assert mismatch.get("gate") == "INBOX_TARGET_MISMATCH"

    ship_dl = vm._handle_attachment_download({
        "requestId": "REQ-SHIP-DL",
        "shipmentId": "LO-TEST-2",
        "attachmentId": after_lo2["attachments"][0]["id"],
    })
    assert not ship_dl["ok"]
    assert ship_dl.get("gate") in {"ATTACHMENT_NOT_FOUND", "SHIPMENT_MISMATCH"}


def test_unauthorized_never_reaches_byte_store(staging, monkeypatch):
    calls = {"n": 0}
    import core.inbox_attachments as inbox_files

    real = inbox_files.store_inbox_bytes

    def wrapped(**kwargs):
        calls["n"] += 1
        return real(**kwargs)

    monkeypatch.setattr(inbox_files, "store_inbox_bytes", wrapped)
    session = {"seq": 0}
    _as("viewer", "viewer")
    out = _dispatch(session, 1, "inbox_snippet_create", {
        "requestId": "REQ-VIEWER-FILE",
        "rawText": "",
        "files": [_file_payload("scan.pdf", "application/pdf", PDF_BYTES)],
    })
    assert not out["ok"]
    assert calls["n"] == 0


def test_partial_file_failure_retries_without_duplicate_note(staging, monkeypatch):
    from core.database import load_inbox_snippets, load_inbox_snippet
    import core.inbox_attachments as inbox_files

    real = inbox_files.store_inbox_bytes
    calls = {"n": 0}

    def wrapped(**kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            return {"ok": False, "code": "GRIDFS_FAILED", "error": "synthetic second-file fail"}
        return real(**kwargs)

    monkeypatch.setattr(inbox_files, "store_inbox_bytes", wrapped)
    session = {"seq": 0}
    first = _dispatch(session, 1, "inbox_snippet_create", {
        "requestId": "REQ-PARTIAL",
        "rawText": "H-TEST partial files",
        "files": [
            _file_payload("one.pdf", "application/pdf", PDF_BYTES),
            _file_payload("two.jpg", "image/jpeg", _jpeg_bytes()),
        ],
    })
    assert first["ok"], first
    assert first.get("partial") is True
    assert len(load_inbox_snippets()) == 1
    snippet_id = first["id"]
    stored = load_inbox_snippet(snippet_id)
    assert len(stored.get("attachments") or []) == 1
    retry = _dispatch(session, 2, "inbox_snippet_attach", {
        "requestId": "REQ-PARTIAL-RETRY",
        "snippetId": snippet_id,
        "files": [_file_payload("two.jpg", "image/jpeg", _jpeg_bytes())],
    })
    assert retry["ok"], retry
    assert not retry.get("partial")
    assert len(load_inbox_snippets()) == 1
    again = load_inbox_snippet(snippet_id)
    assert len(again.get("attachments") or []) == 2


def test_drive_stub_uses_inbox_year_month_and_does_not_move_on_link(staging, monkeypatch):
    from core.database import load_inbox_snippet
    import core.inbox_attachments as inbox_files

    class FakeDrive:
        def __init__(self):
            self.folders: list[tuple[str, str]] = []
            self.uploads: list[tuple[str, str]] = []
            self.files: dict[str, bytes] = {}
            self.n = 0
            self.settings = type("S", (), {"root_folder_id": "ROOT", "configured": True, "missing": []})()

        def ensure_folder(self, name, parent_id):
            self.n += 1
            self.folders.append((str(name), str(parent_id)))
            return f"F-{self.n}"

        def upload_file(self, *, name, mime, data, parent_id, description=""):
            self.n += 1
            fid = f"D-{self.n}"
            self.uploads.append((str(name), str(parent_id)))
            self.files[fid] = bytes(data)
            return {"fileId": fid, "name": name}

        def download_file(self, file_id):
            return self.files[file_id]

        def delete_file(self, file_id):
            self.files.pop(file_id, None)
            return True

    drive = FakeDrive()
    real = inbox_files.store_inbox_bytes

    def wrapped(**kwargs):
        kwargs["storage_backend"] = "drive_shared"
        kwargs["drive"] = drive
        return real(**kwargs)

    monkeypatch.setattr(inbox_files, "store_inbox_bytes", wrapped)
    _ensure_shipments()
    session = {"seq": 0}
    created = _dispatch(session, 1, "inbox_snippet_create", {
        "requestId": "REQ-DRIVE-1",
        "rawText": "H-TEST drive stub",
        "files": [_file_payload("scan.pdf", "application/pdf", PDF_BYTES)],
    })
    assert created["ok"], created
    names = [row[0] for row in drive.folders]
    assert names[0] == "Inbox"
    assert len(names[1]) == 4 and names[1].isdigit()
    assert len(names[2]) == 2 and names[2].isdigit()
    assert len(drive.uploads) == 1
    snippet_id = created["id"]
    _dispatch(session, 2, "inbox_snippet_link", {
        "requestId": "REQ-DRIVE-LINK",
        "snippetIds": [snippet_id],
        "action": "link",
        "targetType": "shipment",
        "targetId": "LO-TEST-1",
    })
    assert len(drive.uploads) == 1
    assert not hasattr(drive, "moved")
    stored = load_inbox_snippet(snippet_id)
    assert stored["attachments"][0]["storage_backend"] == "drive_shared"


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
