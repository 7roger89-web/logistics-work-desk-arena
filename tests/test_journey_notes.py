"""Trao đổi theo công đoạn (Trường Thành ↔ một khách hàng) — isolated tests.

Everything runs on mongomock plus a fake byte store. No Cloud, no production,
no real Google Drive: the storage backend is injected per test.
"""
from __future__ import annotations

import base64
import contextlib
import json
import time
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest

from core import journey_notes as notes
from views import journey_discussion as discussion
from views import journey_inline

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

CUSTOMER_A = "CUST-LUCGIAC"
CUSTOMER_B = "CUST-MINHDUC"
EMAIL_A = "portal.lucgiac@example.com"
LOT_A = "G1-LG-001"
LOT_B = "G1-MD-001"

SALE = {"kind": "user", "username": "sale.thanh", "role": "sale"}
SUPPORT = {"kind": "user", "username": "support.ha", "role": "support"}
VIEWER = {"kind": "user", "username": "xem.thu", "role": "viewer"}
CUSTOMER_ACTOR = {"kind": "customer", "customer_id": CUSTOMER_A, "name": "Lục Giác"}
FOREIGN_ACTOR = {"kind": "customer", "customer_id": CUSTOMER_B, "name": "Minh Đức"}

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8Dw"
    "HwAFAAH/q842iQAAAABJRU5ErkJggg=="
)

FAKE_AUTH = {
    "required": True,
    "redirect_uri": "http://localhost:8501/oauth2callback",
    "cookie_secret": "S" * 48,
    "google": {
        "client_id": "staging-client-id.apps.googleusercontent.com",
        "client_secret": "STAGING_TEST_ONLY_CLIENT_SECRET",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    },
}


class FakeStore:
    """Smallest injectable byte store standing in for GridFS/Drive."""

    def __init__(self, *, fail: bool = False):
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.fail = fail
        self.counter = 0
        self.reads = 0

    def upload_file(self, *, name: str, mime: str, data: bytes, metadata=None):
        if self.fail:
            raise RuntimeError("STORE_DOWN")
        self.counter += 1
        file_id = f"fs-{self.counter}"
        self.files[file_id] = bytes(data)
        return {"storage_file_id": file_id, "stored_name": name, "stored_size": len(data)}

    def download_file(self, file_id: str):
        self.reads += 1
        if file_id not in self.files:
            raise KeyError(file_id)
        return self.files[file_id]

    def delete_file(self, file_id: str):
        self.deleted.append(file_id)
        return self.files.pop(file_id, None) is not None


@pytest.fixture
def db():
    database = mongomock.MongoClient()["journey_notes_test"]
    database.customers.insert_many([
        {"id": CUSTOMER_A, "name": "Lục Giác", "portal_access_email": EMAIL_A},
        {"id": CUSTOMER_B, "name": "Minh Đức"},
    ])
    database.shipments.insert_many([
        {"id": LOT_A, "customer_id": CUSTOMER_A, "transport_mode": "SEA"},
        {"id": LOT_B, "customer_id": CUSTOMER_B, "transport_mode": "ROAD"},
    ])
    return database


@pytest.fixture
def store():
    return FakeStore()


def _write(db, *, body="Kiểm tra chứng từ", stage="customs", visibility=notes.VISIBILITY_CUSTOMER,
           actor=SALE, files=(), store=None, lot=LOT_A, customer=CUSTOMER_A):
    return notes.create_stage_note(
        customer_id=customer, shipment_id=lot, stage_id=stage, body=body,
        visibility=visibility, actor=actor, files=files, db=db, gridfs=store,
        storage_backend="gridfs",
    )


def _internal(db, stage=""):
    return notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id=stage, actor=SALE, db=db)


def _customer(db, stage="", actor=CUSTOMER_ACTOR):
    return notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id=stage, actor=actor, db=db)


# --------------------------------------------------------------------------
# Write permissions and scoping
# --------------------------------------------------------------------------

def test_internal_note_is_saved_readable_and_hidden_from_customer(db):
    _write(db, body="Ghi chú nội bộ: chưa chốt giá", visibility=notes.VISIBILITY_INTERNAL)
    thread = _internal(db)
    assert len(thread) == 1
    assert thread[0]["body"] == "Ghi chú nội bộ: chưa chốt giá"
    assert thread[0]["visibility"] == notes.VISIBILITY_INTERNAL
    assert thread[0]["author_name"] == "sale.thanh"
    assert _customer(db) == []


def test_customer_visible_note_reaches_both_sides(db):
    _write(db, body="Cần bổ sung packing list", visibility=notes.VISIBILITY_CUSTOMER)
    assert [row["body"] for row in _customer(db)] == ["Cần bổ sung packing list"]
    assert len(_internal(db)) == 1


def test_customer_write_is_forced_to_customer_visibility(db):
    _write(db, body="Khách xác nhận địa chỉ", actor=CUSTOMER_ACTOR,
           visibility=notes.VISIBILITY_INTERNAL)
    row = _internal(db)[0]
    assert row["visibility"] == notes.VISIBILITY_CUSTOMER
    assert row["author_kind"] == "customer"


@pytest.mark.parametrize("actor", [VIEWER, {"kind": "user", "username": "x", "role": "unknown"},
                                   {"kind": "user", "username": "", "role": "admin"},
                                   {"kind": "robot"}, None, "admin"])
def test_write_is_refused_without_permission(db, actor):
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, actor=actor)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


@pytest.mark.parametrize("actor", [SALE, SUPPORT, {"kind": "user", "username": "a", "role": "admin"}])
def test_roles_with_shipment_edit_may_write(db, actor):
    assert _write(db, actor=actor)["ok"] is True


def test_customer_cannot_write_to_another_customers_lot(db):
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, actor=FOREIGN_ACTOR, lot=LOT_A)
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, actor=CUSTOMER_ACTOR, lot=LOT_B, customer=CUSTOMER_B)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


def test_unknown_stage_empty_body_and_foreign_lot_are_refused(db):
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, stage="space")
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, body="   ")
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, lot="NO-SUCH-LOT")
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


# --------------------------------------------------------------------------
# Read scoping: stage, lot, tenant, reload
# --------------------------------------------------------------------------

def test_notes_are_scoped_to_one_stage_and_one_lot(db):
    _write(db, body="Mốc lấy hàng", stage="pickup")
    _write(db, body="Mốc thông quan", stage="customs")
    _write(db, body="Lô khác", stage="pickup", lot=LOT_B, customer=CUSTOMER_B)
    assert [row["body"] for row in _internal(db, stage="pickup")] == ["Mốc lấy hàng"]
    assert [row["body"] for row in _internal(db, stage="customs")] == ["Mốc thông quan"]
    assert len(_internal(db)) == 2
    assert "Lô khác" not in json.dumps(_internal(db), ensure_ascii=False)


def test_other_customer_reads_nothing_from_this_lot(db):
    _write(db, visibility=notes.VISIBILITY_CUSTOMER)
    assert _customer(db, actor=FOREIGN_ACTOR) == []
    assert notes.list_stage_notes(
        customer_id=CUSTOMER_B, shipment_id=LOT_B, actor=FOREIGN_ACTOR, db=db) == []


def test_notes_survive_a_reload(db):
    _write(db, body="Nội dung sau reload", visibility=notes.VISIBILITY_CUSTOMER)
    for _ in range(3):
        assert [row["body"] for row in _customer(db)] == ["Nội dung sau reload"]
    stored = db.quick_notes.find_one({"kind": notes.JOURNEY_NOTE_KIND})
    assert stored["customer_id"] == CUSTOMER_A and stored["shipment_id"] == LOT_A


def test_legacy_quick_notes_are_never_returned(db):
    db.quick_notes.insert_many([
        {"id": "team_note", "content": "Sổ tay đội"},
        {"id": "note-1", "kind": "inbox_snippet", "raw_text": "Mẩu tin hộp thư đến",
         "shipment_ids": [LOT_A]},
    ])
    assert _internal(db) == []
    assert _customer(db) == []


# --------------------------------------------------------------------------
# Attachments: real byte store injected, no storage ids leak
# --------------------------------------------------------------------------

def _png(name="bang-ke.png"):
    return {"name": name, "mime": "image/png", "data": PNG_1PX, "size": len(PNG_1PX)}


def test_attachment_is_stored_listed_and_downloadable_by_staff(db, store):
    outcome = _write(db, body="Đã gửi ảnh tờ khai", files=[_png()], store=store)
    assert outcome["ok"] is True
    row = _internal(db)[0]
    assert len(row["attachments"]) == 1
    attachment = row["attachments"][0]
    assert attachment["name"] == "bang-ke.png"
    serialized = json.dumps(row)
    assert "storage_file_id" not in serialized and "sha256" not in serialized
    read = notes.read_note_attachment(
        note_id=row["id"], attachment_id=attachment["id"], actor=SALE, db=db, gridfs=store)
    assert read["ok"] is True and read["data"] == PNG_1PX


def test_customer_may_read_only_visible_attachments(db, store):
    _write(db, body="Ảnh nội bộ", visibility=notes.VISIBILITY_INTERNAL, files=[_png("noi-bo.png")],
           store=store)
    _write(db, body="Ảnh cho khách", visibility=notes.VISIBILITY_CUSTOMER,
           files=[_png("cho-khach.png")], store=store)
    visible = [row for row in _customer(db) if row["attachments"]]
    assert len(visible) == 1
    attachment = visible[0]["attachments"][0]
    assert attachment["name"] == "cho-khach.png"
    read = notes.read_note_attachment(
        note_id=visible[0]["id"], attachment_id=attachment["id"],
        actor=CUSTOMER_ACTOR, db=db, gridfs=store)
    assert read["ok"] is True
    internal_row = next(row for row in _internal(db) if row["visibility"] == notes.VISIBILITY_INTERNAL)
    denied = notes.read_note_attachment(
        note_id=internal_row["id"], attachment_id=internal_row["attachments"][0]["id"],
        actor=CUSTOMER_ACTOR, db=db, gridfs=store)
    assert denied["ok"] is False and denied.get("data", b"") == b""
    foreign = notes.read_note_attachment(
        note_id=visible[0]["id"], attachment_id=attachment["id"],
        actor=FOREIGN_ACTOR, db=db, gridfs=store)
    assert foreign["ok"] is False


def test_storage_failure_leaves_no_note_and_compensates_bytes(db):
    broken = FakeStore(fail=True)
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, body="Kèm tệp", files=[_png()], store=broken)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


def test_unsupported_or_empty_file_is_refused(db, store):
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, files=[{"name": "malware.exe", "mime": "application/octet-stream",
                           "data": b"MZ", "size": 2}], store=store)
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, files=[{"name": "empty.png", "mime": "image/png", "data": b"", "size": 0}],
               store=store)
    assert store.files == {}
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


# --------------------------------------------------------------------------
# Internal UI (mocked Streamlit) and customer portal (real Streamlit AppTest)
# --------------------------------------------------------------------------

class FakeStreamlit:
    """Minimal recorder standing in for the Streamlit surface used here."""

    def __init__(self, *, body="", visibility_index=0, uploads=(), send=False, download=False,
                 stage_index=0):
        self.session_state = {}
        self.markdowns: list[str] = []
        self.captions: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.downloads: list[dict] = []
        self.body = body
        self.visibility_index = visibility_index
        self.uploads = uploads
        self.send = send
        self.download = download
        self.stage_index = stage_index

    def expander(self, *args, **kwargs):
        return contextlib.nullcontext()

    def selectbox(self, label, options, index=0, key=None, **kwargs):
        return options[self.stage_index]

    def radio(self, label, options, index=0, **kwargs):
        return options[self.visibility_index]

    def text_area(self, label, key=None, **kwargs):
        return self.body

    def file_uploader(self, *args, **kwargs):
        return list(self.uploads)

    def button(self, label, key=None, **kwargs):
        if label == "Gửi":
            return self.send
        return self.download

    def download_button(self, label, data=b"", file_name="", mime="", key=None, **kwargs):
        self.downloads.append({"file_name": file_name, "size": len(data or b"")})

    def markdown(self, text, **kwargs):
        self.markdowns.append(str(text))

    def caption(self, text, **kwargs):
        self.captions.append(str(text))

    def divider(self):
        return None

    def error(self, text, **kwargs):
        self.errors.append(str(text))

    def warning(self, text, **kwargs):
        self.errors.append(str(text))

    def success(self, text, **kwargs):
        self.successes.append(str(text))

    def rerun(self):
        """Real Streamlit restarts the script; the recorder only notes it."""
        self.reruns = getattr(self, "reruns", 0) + 1
        return None


def _run_internal(db, store=None, **kwargs):
    fake = FakeStreamlit(**kwargs)
    with (
        patch.object(discussion, "st", fake),
        patch("core.inbox_attachments._resolve_gridfs", return_value=store or FakeStore()),
    ):
        discussion.render_internal_discussion(LOT_A, CUSTOMER_A, SALE, db=db)
    return fake


def test_internal_ui_shows_both_visibilities_and_can_post(db):
    _write(db, body="Nội bộ: giữ xe", visibility=notes.VISIBILITY_INTERNAL, stage="pickup")
    _write(db, body="Khách: chờ xác nhận", visibility=notes.VISIBILITY_CUSTOMER, stage="pickup")
    fake = _run_internal(db, stage_index=1)
    text = "\n".join(fake.markdowns)
    assert "Nội bộ: giữ xe" in text and "Khách: chờ xác nhận" in text
    assert "Nội bộ Trường Thành" in text and "Khách hàng nhìn thấy" in text


def test_note_text_is_escaped_before_rendering(db):
    _write(db, body="<script>alert(1)</script> & <b>chào</b>", stage="customs",
           visibility=notes.VISIBILITY_CUSTOMER)
    fake = _run_internal(db, stage_index=4)
    text = "\n".join(fake.markdowns)
    assert "<script>" not in text and "&lt;script&gt;" in text
    assert "<b>chào</b>" not in text


def test_internal_ui_posts_a_note(db):
    fake = _run_internal(db, stage_index=4, body="Chờ khách bổ sung C/O", send=True)
    assert fake.successes and not fake.errors
    rows = _internal(db, stage="customs")
    assert [row["body"] for row in rows] == ["Chờ khách bổ sung C/O"]
    assert rows[0]["visibility"] == notes.VISIBILITY_INTERNAL


def test_internal_ui_can_publish_a_customer_visible_note(db):
    fake = _run_internal(db, stage_index=4, body="Vui lòng xác nhận", send=True,
                         visibility_index=1)
    assert fake.successes
    rows = _internal(db, stage="customs")
    assert rows[0]["visibility"] == notes.VISIBILITY_CUSTOMER
    assert [row["body"] for row in _customer(db, stage="customs")] == ["Vui lòng xác nhận"]


def test_internal_ui_reports_errors_without_writing(db):
    fake = _run_internal(db, stage_index=0, body="   ", send=True)
    assert fake.errors and not fake.successes
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


def test_internal_ui_download_requires_the_exact_attachment(db, store):
    _write(db, body="Ảnh tờ khai", stage="customs", files=[_png()], store=store)
    row = _internal(db)[0]
    fake = _run_internal(db, store=store, stage_index=4, download=True)
    assert fake.downloads and fake.downloads[0]["size"] == len(PNG_1PX)
    # A stale id from another note is refused.
    assert notes.read_note_attachment(
        note_id=row["id"], attachment_id="att-does-not-exist", actor=SALE, db=db,
        gridfs=store)["ok"] is False


def _claims(email: str):
    return {
        "is_logged_in": True, "provider": "google", "aud": FAKE_AUTH["google"]["client_id"],
        "iss": "https://accounts.google.com", "email": email, "email_verified": True,
        "exp": int(time.time()) + 600, "sub": "staging-google-subject",
    }


def _portal(db, email=EMAIL_A):
    from core import customer_portal as portal
    from core.customer_portal_publish import publish_verified_sources

    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(email)),
        patch.object(portal, "get_db", return_value=db),
        patch("core.database.get_db", return_value=db),
        patch("core.journey_notes._resolve_db", return_value=db),
    ):
        app.run()
    return app


def _visible(app):
    values = []
    for name in ("markdown", "caption", "text", "success", "error", "warning", "info"):
        for element in getattr(app, name, []):
            values.append(str(getattr(element, "value", "")))
            label = getattr(element, "label", None)
            if label:
                values.append(str(label))
    return "\n".join(values)


def test_internal_pane_runs_in_a_real_streamlit_script(db):
    """The same pane through the real Streamlit runtime, not only the fake."""
    script = (
        "import streamlit as st\n"
        "from views.journey_discussion import render_internal_discussion\n"
        f"render_internal_discussion('{LOT_A}', '{CUSTOMER_A}', "
        "{'username': 'sale.thanh', 'role': 'sale'})\n"
    )
    app = AppTest.from_string(script, default_timeout=120)
    with (
        patch("core.database.get_db", return_value=db),
        patch("core.inbox_attachments._resolve_gridfs", return_value=FakeStore()),
    ):
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        areas = list(app.text_area)
        assert areas and areas[0].label == "Nội dung trao đổi"
        areas[0].set_value("Chốt xe tải 8 tấn")
        senders = [element for element in app.button if element.label == "Gửi"]
        assert senders
        senders[0].click()
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert "Đã lưu trao đổi" in _visible(app)
    rows = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, actor=SALE, db=db)
    assert [row["body"] for row in rows] == ["Chốt xe tải 8 tấn"]


def _portal_inline(db, store, email=EMAIL_A):
    """The REAL portal entrypoint with only the component boundary stubbed.

    The browser half (bubble, composer, reply, download) is exercised by the
    jsdom acceptance tests; here we prove the server half: the payload the node
    gets, the one-shot write, the refusal paths and the reload.
    """
    from views import customer_dashboard as dash

    state: dict = {"model": None, "result": None}

    def fake_render(model, **kwargs):
        state["model"] = model
        return state["result"]

    stack = _portal_stack(db, store, email)
    stack.enter_context(patch.object(dash.component, "render", fake_render))
    app = AppTest.from_file(str(APP_PATH), default_timeout=180)
    app.secrets = {"auth": FAKE_AUTH}
    return app, state, stack


def _trigger(state, event, payload, seq=1):
    state["result"] = {
        event: {"seq": seq, "event": event, "payload": payload},
    }


def _focus(app, shipment=LOT_A, stage="pickup"):
    app.session_state["logi_journey_focus"] = {
        "shipment_id": shipment, "stage_id": stage,
    }


def test_customer_portal_posts_and_reloads_a_stage_comment(db, store):
    """Issue #236: the node payload carries the thread; posting happens in-map."""
    _seed_public_event(db)
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        # Fail condition: no Streamlit conversation form anywhere in the portal.
        assert not list(app.text_area)
        assert not list(app.file_uploader)
        assert not [e for e in app.expander if "Trao đổi" in e.label]
        discussion = state["model"]["discussion"]
        assert discussion["shipmentId"] == LOT_A
        assert discussion["stageId"] == "pickup"
        assert discussion["notes"] == []

        _trigger(state, "journey_note_create", {
            "shipmentId": LOT_A, "stageId": "pickup",
            "body": "Xác nhận địa chỉ giao hàng", "visibility": "CUSTOMER",
            "replyToId": "", "files": [], "requestId": "REQ-PORTAL-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        outcome = state["model"]["discussion"]["outcome"]
        assert outcome["ok"] is True and outcome["requestId"] == "REQ-PORTAL-1"
        state["result"] = None
        app.run()          # reloads and delivers the saved note
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert [note["body"] for note in discussion["notes"]] == [
            "Xác nhận địa chỉ giao hàng",
        ]
        assert discussion["notes"][0]["visibility"] == notes.VISIBILITY_CUSTOMER

    rows = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id="pickup",
        actor=CUSTOMER_ACTOR, db=db)
    assert [row["body"] for row in rows] == ["Xác nhận địa chỉ giao hàng"]
    assert rows[0]["visibility"] == notes.VISIBILITY_CUSTOMER


def test_customer_portal_never_shows_internal_notes(db):
    from core import customer_portal as portal
    from core.customer_portal_publish import publish_verified_sources

    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
        "stage_id": "pickup", "public_title": "Đã lấy hàng",
        "occurred_at": "2026-10-28T01:00:00Z", "verified": True,
        "verified_at": "2026-10-28T02:00:00Z", "visibility": "CUSTOMER",
    })
    ok, _ = publish_verified_sources(
        CUSTOMER_A, LOT_A, event_versions={"EV-1": "v1"}, document_versions={},
        expected_current_version="", actor_role="admin", actor_username="staging-admin", db=db)
    assert ok
    _write(db, body="NỘI TỐI MẬT GIÁ VỐN", visibility=notes.VISIBILITY_INTERNAL, stage="pickup")

    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(EMAIL_A)),
        patch.object(portal, "get_db", return_value=db),
        patch("core.database.get_db", return_value=db),
    ):
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        visible = _visible(app)
    assert "NỘI TỐI MẬT GIÁ VỐN" not in visible
    assert "Nội bộ Trường Thành" not in visible


# --------------------------------------------------------------------------
# Security regressions: tenant assignment/revocation and local widget state
# --------------------------------------------------------------------------

def test_shipment_reassignment_revokes_old_tenant_notes_and_bytes(db, store):
    _write(
        db, actor=CUSTOMER_ACTOR, visibility=notes.VISIBILITY_CUSTOMER,
        body="Chứng từ thuộc lô cũ", files=[_png()], store=store,
    )
    original_note = _customer(db)[0]
    attachment_id = original_note["attachments"][0]["id"]
    assert notes.read_note_attachment(
        note_id=original_note["id"], attachment_id=attachment_id,
        actor=CUSTOMER_ACTOR, db=db, gridfs=store,
    )["ok"] is True
    db.shipments.update_one(
        {"id": LOT_A}, {"$set": {"customer_id": CUSTOMER_B}},
    )
    assert _customer(db) == []
    assert notes.read_note_attachment(
        note_id=original_note["id"], attachment_id=attachment_id,
        actor=CUSTOMER_ACTOR, db=db, gridfs=store,
    )["ok"] is False
    # The new tenant must not inherit the old customer's note automatically.
    assert notes.list_stage_notes(
        customer_id=CUSTOMER_B, shipment_id=LOT_A, actor=FOREIGN_ACTOR, db=db,
    ) == []
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, actor=CUSTOMER_ACTOR)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 1


def test_removed_shipment_denies_old_stage_notes_and_download(db, store):
    _write(db, files=[_png()], store=store)
    original = _internal(db)[0]
    db.shipments.update_one({"id": LOT_A}, {"$set": {"is_deleted": True}})
    assert _internal(db) == []
    assert notes.read_note_attachment(
        note_id=original["id"], attachment_id=original["attachments"][0]["id"],
        actor=SALE, db=db, gridfs=store,
    )["ok"] is False


def test_streamlit_customer_composer_keys_are_scoped_per_tenant_and_lot(db):
    from types import SimpleNamespace

    fake = FakeStreamlit()
    keys = []
    original_area = fake.text_area

    def capture_area(label, key=None, **kwargs):
        keys.append(key)
        return original_area(label, key=key, **kwargs)

    fake.text_area = capture_area
    with patch.object(discussion, "st", fake):
        discussion.render_customer_discussion(
            [SimpleNamespace(reference=LOT_A)],
            SimpleNamespace(customer_id=CUSTOMER_A, display_name="Lục Giác"),
            db=db, key_prefix="jd_customer",
        )
        discussion.render_customer_discussion(
            [SimpleNamespace(reference=LOT_B)],
            SimpleNamespace(customer_id=CUSTOMER_B, display_name="Minh Đức"),
            db=db, key_prefix="jd_customer",
        )
    assert len(keys) == 2 and keys[0] != keys[1]
    assert CUSTOMER_A in keys[0] and CUSTOMER_B in keys[1]



def test_revoked_attachment_status_blocks_download_and_listing(db, store):
    _write(db, actor=CUSTOMER_ACTOR, files=[_png()], store=store)
    note = _customer(db)[0]
    item_id = note["attachments"][0]["id"]
    db.quick_notes.update_one(
        {"id": note["id"]}, {"$set": {"attachments.0.status": "REVOKED"}},
    )
    assert _customer(db)[0]["attachments"] == []
    assert notes.read_note_attachment(
        note_id=note["id"], attachment_id=item_id,
        actor=CUSTOMER_ACTOR, db=db, gridfs=store,
    )["ok"] is False


def test_latest_notes_remain_visible_after_read_limit(db):
    from datetime import datetime, timedelta, timezone

    first = datetime(2026, 10, 30, tzinfo=timezone.utc)
    for i in range(notes.MAX_NOTES_READ + 1):
        db.quick_notes.insert_one({
            "id": f"jn-{i:03d}", "kind": notes.JOURNEY_NOTE_KIND,
            "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
            "stage_id": "pickup", "visibility": notes.VISIBILITY_CUSTOMER,
            "body": f"Thông tin {i}", "author_kind": "user",
            "author_name": "sale.thanh", "author_role": "sale",
            "created_at": (first + timedelta(minutes=i)).isoformat(),
        })
    rows = _customer(db)
    assert len(rows) == notes.MAX_NOTES_READ
    assert rows[0]["id"] == "jn-001"
    assert rows[-1]["id"] == f"jn-{notes.MAX_NOTES_READ:03d}"


# --------------------------------------------------------------------------
# PR #234 session QA — real Streamlit UI: chọn công đoạn, gửi, reload, xem lại
# --------------------------------------------------------------------------

STAGE_OPTIONS = [
    "00 · Kế hoạch", "01 · Lấy hàng", "02 · Gom hàng", "03 · Vận chuyển",
    "04 · Thông quan", "05 · Giao hàng", "06 · Thanh toán",
]

_INTERNAL_SCRIPT = (
    "import streamlit as st\n"
    "from views.journey_discussion import render_internal_discussion\n"
    "cust = st.session_state.get('qa_cust', {cust!r})\n"
    "lot = st.session_state.get('qa_lot', {lot!r})\n"
    "if st.button('switch_customer'):\n"
    "    st.session_state['qa_cust'] = {other!r}\n"
    "    st.session_state['qa_lot'] = {other_lot!r}\n"
    "render_internal_discussion(lot, cust, {{'username': 'sale.thanh', 'role': 'sale'}})\n"
).format(cust=CUSTOMER_A, lot=LOT_A, other=CUSTOMER_B, other_lot=LOT_B)


def _internal_stack(db, store):
    """Keep the DB/byte-store patches alive across several AppTest runs."""
    stack = contextlib.ExitStack()
    stack.enter_context(patch("core.database.get_db", return_value=db))
    stack.enter_context(patch("core.inbox_attachments._resolve_gridfs", return_value=store))
    return stack


def _internal_app(db, store, script=_INTERNAL_SCRIPT):
    return AppTest.from_string(script, default_timeout=120), _internal_stack(db, store)


def _portal_stack(db, store, email=EMAIL_A):
    from core import customer_portal as portal

    stack = contextlib.ExitStack()
    stack.enter_context(patch("streamlit.user_info._get_user_info", return_value=_claims(email)))
    stack.enter_context(patch.object(portal, "get_db", return_value=db))
    stack.enter_context(patch("core.database.get_db", return_value=db))
    stack.enter_context(patch.object(notes, "_resolve_db", return_value=db))
    stack.enter_context(patch("core.inbox_attachments._resolve_gridfs", return_value=store))
    return stack


def _portal_app(db, store, email=EMAIL_A):
    app = AppTest.from_file(str(APP_PATH), default_timeout=180)
    app.secrets = {"auth": FAKE_AUTH}
    return app, _portal_stack(db, store, email)


def _seed_public_event(db, *, shipment=LOT_A, customer=CUSTOMER_A, stage="pickup", event="EV-1"):
    from core.customer_portal_publish import publish_verified_sources

    db.public_events.insert_one({
        "id": event, "version": "v1", "customer_id": customer, "shipment_id": shipment,
        "stage_id": stage, "public_title": "Đã lấy hàng",
        "occurred_at": "2026-10-28T01:00:00Z", "verified": True,
        "verified_at": "2026-10-28T02:00:00Z", "visibility": "CUSTOMER",
    })
    ok, message = publish_verified_sources(
        customer, shipment, event_versions={event: "v1"}, document_versions={},
        expected_current_version="", actor_role="admin", actor_username="staging-admin", db=db,
    )
    assert ok, message


def _send_button(app):
    senders = [element for element in app.button if element.label == "Gửi"]
    assert senders, "không thấy nút Gửi"
    return senders[0]


def _attachment_buttons(app):
    return [element for element in app.button if element.label.startswith("📎")]


def test_ui_stage_selection_sends_and_shows_the_note_immediately(db, store):
    """Trường Thành chọn đúng công đoạn → gửi → thấy ngay, không cần reload tay."""
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        app.selectbox[0].set_value(STAGE_OPTIONS[2]).run()      # Gom hàng
        app.text_area[0].set_value("Chốt cont 40HC").run()
        _send_button(app).click().run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert "Đã lưu trao đổi" in _visible(app)
        assert "Chốt cont 40HC" in _visible(app)
        assert app.selectbox[0].value == STAGE_OPTIONS[2]
    rows = _internal(db, stage="consolidate")
    assert [row["body"] for row in rows] == ["Chốt cont 40HC"]
    assert _internal(db, stage="customs") == []


def test_ui_draft_is_scoped_to_its_stage_and_empty_uploads_are_not_reused(db, store):
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()      # Lấy hàng
        app.text_area[0].set_value("Nháp cho lấy hàng").run()
        app.file_uploader[0].upload("anh-lay-hang.png", PNG_1PX, "image/png").run()
        app.selectbox[0].set_value(STAGE_OPTIONS[4]).run()      # Thông quan
        assert app.text_area[0].value == ""
        assert not (app.file_uploader[0].value or [])
        _send_button(app).click().run()
        # Switching stage without typing must not resend the previous stage's text.
        assert "Nhập nội dung hoặc đính kèm chứng từ" in _visible(app)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0


def test_ui_upload_then_reload_keeps_the_document_and_downloads_it(db, store):
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[4]).run()      # Thông quan
        app.file_uploader[0].upload("to-khai.png", PNG_1PX, "image/png").run()
        app.text_area[0].set_value("Đã nộp tờ khai").run()
        _send_button(app).click().run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert len(_attachment_buttons(app)) == 1

        # A brand-new script run is the reload: the file must still be there.
        reloaded = AppTest.from_string(_INTERNAL_SCRIPT, default_timeout=120)
        reloaded.run()
        reloaded.selectbox[0].set_value(STAGE_OPTIONS[4]).run()
        assert "Đã nộp tờ khai" in _visible(reloaded)
        buttons = _attachment_buttons(reloaded)
        assert len(buttons) == 1 and "to-khai.png" in buttons[0].label
        buttons[0].click().run()
        assert not reloaded.exception, [str(e.value) for e in reloaded.exception]
        downloads = [element for element in reloaded.download_button if element.label == "⬇️ Tải xuống"]
        assert downloads, "không hiện nút tải chứng từ sau khi mở đính kèm"

        # The same stage only: another công đoạn must stay empty.
        reloaded.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert _attachment_buttons(reloaded) == []
    assert len(store.files) == 1
    row = _internal(db)[0]
    assert len(row["attachments"]) == 1
    assert notes.read_note_attachment(
        note_id=row["id"], attachment_id=row["attachments"][0]["id"],
        actor=SALE, db=db, gridfs=store,
    )["data"] == PNG_1PX


def test_ui_revoked_document_is_not_listed_or_downloadable(db, store):
    outcome = _write(db, body="Ảnh thu hồi", stage="pickup", files=[_png()], store=store)
    db.quick_notes.update_one(
        {"id": outcome["note"]["id"]}, {"$set": {"attachments.0.status": "REVOKED"}},
    )
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert "Ảnh thu hồi" in _visible(app)
        assert _attachment_buttons(app) == []
        assert not [element for element in app.download_button]
    assert notes.read_note_attachment(
        note_id=outcome["note"]["id"],
        attachment_id=outcome["note"]["attachments"][0]["id"],
        actor=SALE, db=db, gridfs=store,
    )["ok"] is False


def test_ui_reassigned_lot_hides_previous_notes_and_files(db, store):
    _write(db, body="CỦA CHỦ CŨ", stage="pickup", files=[_png()], store=store)
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert "CỦA CHỦ CŨ" in _visible(app) and len(_attachment_buttons(app)) == 1

        db.shipments.update_one({"id": LOT_A}, {"$set": {"customer_id": CUSTOMER_B}})
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert "CỦA CHỦ CŨ" not in _visible(app)
        assert _attachment_buttons(app) == []
    assert notes.list_stage_notes(
        customer_id=CUSTOMER_B, shipment_id=LOT_A, actor=FOREIGN_ACTOR, db=db,
    ) == []


def test_ui_deleted_lot_hides_previous_notes_and_files(db, store):
    _write(db, body="LÔ SẮP XOÁ", stage="pickup", files=[_png()], store=store)
    db.shipments.update_one({"id": LOT_A}, {"$set": {"is_deleted": True}})
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert "LÔ SẮP XOÁ" not in _visible(app)
        assert _attachment_buttons(app) == []


def test_ui_switching_customer_clears_thread_draft_and_staged_file(db, store):
    _write(db, body="KHÁCH A NỘI DUNG", stage="pickup", files=[_png()], store=store)
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        assert "KHÁCH A NỘI DUNG" in _visible(app)
        app.text_area[0].set_value("NHÁP CỦA KHÁCH A").run()
        app.file_uploader[0].upload("a.png", PNG_1PX, "image/png").run()
        switchers = [element for element in app.button if element.label == "switch_customer"]
        assert switchers
        switchers[0].click().run()
        app.run()          # the click only publishes the new customer for the next run
        assert app.text_area[0].value == ""
        assert not (app.file_uploader[0].value or [])
        visible = _visible(app)
        assert "KHÁCH A NỘI DUNG" not in visible and "NHÁP CỦA KHÁCH A" not in visible
        assert _attachment_buttons(app) == []


def test_ui_more_than_four_files_is_refused_without_writing(db, store):
    app, stack = _internal_app(db, store)
    with stack:
        app.run()
        app.selectbox[0].set_value(STAGE_OPTIONS[1]).run()
        app.file_uploader[0].set_value(
            [(f"tep-{i}.png", PNG_1PX, "image/png") for i in range(notes.MAX_FILES_PER_SUBMIT + 1)]
        ).run()
        app.text_area[0].set_value("Gửi 5 tệp").run()
        _send_button(app).click().run()
        assert f"Tối đa {notes.MAX_FILES_PER_SUBMIT} tệp" in _visible(app)
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 0
    assert store.files == {}


_STAFF_INLINE_SCRIPT = (
    "import streamlit as st\n"
    "from views import journey_inline\n"
    "user = {'username': 'sale.thanh', 'role': 'sale'}\n"
    "st.session_state['out'] = journey_inline.consume_staff_triggers(\n"
    "    {'seq': 0}, st.session_state['event'], user=user,\n"
    "    shipments=st.session_state['rows'],\n"
    ")\n"
)


def _staff_inline_write(db, store, payload) -> dict:
    """The shell's OWN trigger path: one typed create event, no Streamlit form."""
    with _internal_stack(db, store):
        app = AppTest.from_string(_STAFF_INLINE_SCRIPT, default_timeout=120)
        app.session_state["rows"] = [{
            "id": LOT_A, "customerId": CUSTOMER_A,
            "journey": {"nodes": [{"id": "pickup-1", "label": "Lấy hàng"}]},
        }]
        app.session_state["event"] = {
            "journey_note_create": {
                "seq": 1, "event": "journey_note_create", "payload": payload,
            },
        }
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        outcomes = app.session_state["out"]
    assert len(outcomes) == 1
    return outcomes[0]


def test_ui_staff_public_note_file_and_customer_reply_meet_at_the_same_stage(db, store):
    """Hai phía, một công đoạn: Trường Thành công khai → khách xem/tải → khách trả lời."""
    _seed_public_event(db)
    _write(db, body="NỘI BỘ: giá vốn", stage="pickup",
           visibility=notes.VISIBILITY_INTERNAL, store=store)

    # --- staff half: the in-map composer publishes a note + a real file ------
    outcome = _staff_inline_write(db, store, {
        "shipmentId": LOT_A, "stageId": "pickup", "nodeId": "pickup-1",
        "body": "Cần khách xác nhận tờ khai", "visibility": "CUSTOMER",
        "replyToId": "", "requestId": "REQ-STAFF-1",
        "files": [{"name": "to-khai.png", "mime": "image/png",
                   "base64": base64.b64encode(PNG_1PX).decode()}],
    })
    assert outcome["ok"] is True and outcome["gate"] == "SAVED"
    assert outcome["persisted"]["attachments"] == 1
    root = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id="pickup",
        actor=SALE, db=db)
    root_id = next(row["id"] for row in root if row["body"] == "Cần khách xác nhận tờ khai")
    attachment_id = next(row["attachments"][0]["id"] for row in root
                         if row["body"] == "Cần khách xác nhận tờ khai")

    # --- customer half: same stage, same lot, INTERNAL invisible in payload --
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        bodies = {note["body"] for note in discussion["notes"]}
        assert "Cần khách xác nhận tờ khai" in bodies
        assert "NỘI BỘ: giá vốn" not in json.dumps(state["model"], ensure_ascii=False)
        shown = next(note for note in discussion["notes"]
                     if note["body"] == "Cần khách xác nhận tờ khai")
        assert [att["name"] for att in shown["attachments"]] == ["to-khai.png"]

        # download: identifiers out, server bytes in
        _trigger(state, "journey_note_download", {
            "shipmentId": LOT_A, "stageId": "pickup", "noteId": root_id,
            "attachmentId": attachment_id, "requestId": "REQ-DL-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        download = state["model"]["discussion"]["download"]
        assert download["name"] == "to-khai.png"
        assert base64.b64decode(download["base64"]) == PNG_1PX

        # reply under the visible root
        state["result"] = None
        _trigger(state, "journey_note_create", {
            "shipmentId": LOT_A, "stageId": "pickup",
            "body": "Khách đã xác nhận tờ khai", "visibility": "CUSTOMER",
            "replyToId": root_id, "files": [], "requestId": "REQ-CUST-1",
        }, seq=2)
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        state["result"] = None
        app.run()          # reload
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        tree = {note["body"]: note for note in discussion["notes"]}
        assert [reply["body"] for reply in tree["Cần khách xác nhận tờ khai"]["replies"]] == [
            "Khách đã xác nhận tờ khai",
        ]

    thread = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id="pickup", actor=SALE, db=db)
    assert {row["body"] for row in thread} == {
        "NỘI BỘ: giá vốn", "Cần khách xác nhận tờ khai", "Khách đã xác nhận tờ khai",
    }
    reply_row = next(row for row in thread if row["body"] == "Khách đã xác nhận tờ khai")
    assert reply_row["reply_to_id"] == root_id
    assert reply_row["author_kind"] == "customer"
    assert reply_row["visibility"] == notes.VISIBILITY_CUSTOMER


def test_ui_customer_cannot_see_or_write_another_lots_thread(db, store):
    """Lục Giác chỉ thấy lô của mình; lô của khách khác bị từ chối ở server."""
    _seed_public_event(db)
    _write(db, body="LÔ CỦA KHÁCH KHÁC", stage="pickup", customer=CUSTOMER_B, lot=LOT_B,
           actor=SUPPORT, store=store)
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert "LÔ CỦA KHÁCH KHÁC" not in json.dumps(state["model"], ensure_ascii=False)
        assert LOT_B not in json.dumps(
            [note["body"] for note in state["model"]["discussion"]["notes"]],
            ensure_ascii=False,
        )

        # A hand-crafted payload for another tenant is refused, not written.
        _trigger(state, "journey_note_create", {
            "shipmentId": LOT_B, "stageId": "pickup",
            "body": "GỬI SANG LÔ KHÁC", "visibility": "CUSTOMER",
            "replyToId": "", "files": [], "requestId": "REQ-FOREIGN-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert state["model"]["discussion"]["outcome"]["ok"] is False
        assert db.quick_notes.count_documents(
            {"kind": notes.JOURNEY_NOTE_KIND, "shipment_id": LOT_B,
             "body": "GỬI SANG LÔ KHÁC"},
        ) == 0

        # Replaying the very same trigger (rerun/double click) writes once.
        state["result"] = None
        _trigger(state, "journey_note_create", {
            "shipmentId": LOT_A, "stageId": "pickup",
            "body": "CHỈ MỘT LẦN", "visibility": "CUSTOMER",
            "replyToId": "", "files": [], "requestId": "REQ-ONCE-1",
        }, seq=3)
        app.run()
        state["result"] = None
        app.run()
        assert db.quick_notes.count_documents(
            {"kind": notes.JOURNEY_NOTE_KIND, "body": "CHỈ MỘT LẦN"},
        ) == 1
    with pytest.raises(notes.JourneyNoteDenied):
        _write(db, body="x", lot=LOT_B, customer=CUSTOMER_B, actor=CUSTOMER_ACTOR, store=store)


def test_real_pages_are_wired_to_the_inline_map_discussion():
    """The shipped map surfaces own the thread; no Streamlit form sits above it."""
    import inspect

    from views import customer_dashboard, logi_view_model, shipment, web_app

    portal_view = inspect.getsource(customer_dashboard.render_customer_dashboard)
    assert "journey_inline.build_customer_discussion(" in portal_view
    assert "discussion=discussion" in portal_view
    assert "render_customer_discussion(" not in portal_view

    shell = inspect.getsource(logi_view_model)
    assert "journey_inline.build_staff_discussion(" in shell
    assert '"journeyDiscussion"' in shell or "journeyDiscussion" in shell

    web = inspect.getsource(web_app)
    assert "_render_journey_focus_pane" not in web

    # The lot-detail page keeps its own stage pane: a different surface, never
    # part of the Journey Map path.
    detail = inspect.getsource(shipment.ui_shipment_detail_tabs)
    assert "render_internal_discussion(" in detail

    component = (ROOT / "component/src/components/JourneyMap.tsx").read_text()
    assert "JourneyDiscussionPanel" in component
    panel = (ROOT / "component/src/components/JourneyDiscussionPanel.tsx").read_text()
    assert "journey-discussion-body" in panel and "journey-discussion-send" in panel

    portal_js = (ROOT / "assets/customer_portal/hexa-portal.js").read_text()
    assert "journey-discussion" in portal_js
    assert "journey_note_create" in portal_js and "journey_note_download" in portal_js


def test_ui_customer_with_two_lots_posts_into_the_lot_it_selected(db, store):
    lot_two = "G1-LG-002"
    db.shipments.insert_one({"id": lot_two, "customer_id": CUSTOMER_A})
    _seed_public_event(db, shipment=LOT_A, event="EV-A", stage="pickup")
    _seed_public_event(db, shipment=lot_two, event="EV-B", stage="pickup")
    _write(db, body="TRAO ĐỔI LÔ MỘT", stage="pickup", store=store)

    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, lot_two, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert discussion["shipmentId"] == lot_two
        assert "TRAO ĐỔI LÔ MỘT" not in json.dumps(discussion, ensure_ascii=False)
        # The other lot stays in the dashboard payload, but its thread is absent.
        assert discussion["notes"] == []

        _trigger(state, "journey_note_create", {
            "shipmentId": lot_two, "stageId": "pickup",
            "body": "KHÁCH GỬI Ở LÔ HAI", "visibility": "CUSTOMER",
            "replyToId": "", "files": [], "requestId": "REQ-LOT2-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        state["result"] = None
        app.run()
        assert [note["body"] for note in state["model"]["discussion"]["notes"]] == [
            "KHÁCH GỬI Ở LÔ HAI",
        ]

        # Returning to the first lot shows only the first lot's thread.
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        bodies = [note["body"] for note in state["model"]["discussion"]["notes"]]
        assert bodies == ["TRAO ĐỔI LÔ MỘT"]
    rows_one = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id="pickup",
        actor=CUSTOMER_ACTOR, db=db)
    rows_two = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=lot_two, stage_id="pickup",
        actor=CUSTOMER_ACTOR, db=db)
    assert [row["body"] for row in rows_one] == ["TRAO ĐỔI LÔ MỘT"]
    assert [row["body"] for row in rows_two] == ["KHÁCH GỬI Ở LÔ HAI"]




# --------------------------------------------------------------------------
# Trả lời (reply): một cấp, đúng phạm vi, không lộ cha INTERNAL
# --------------------------------------------------------------------------

def _reply(db, parent_id, *, body="Phản hồi", actor=SALE, stage="pickup",
           visibility=notes.VISIBILITY_CUSTOMER, lot=LOT_A, customer=CUSTOMER_A):
    return notes.create_stage_note(
        customer_id=customer, shipment_id=lot, stage_id=stage, body=body,
        visibility=visibility, actor=actor, reply_to_id=parent_id, db=db,
    )


def test_reply_attaches_to_its_root_and_a_reply_to_a_reply_stays_at_one_level(db):
    root = _write(db, body="Bình luận gốc", stage="pickup")["note"]
    first = _reply(db, root["id"], body="Trả lời lần một")["note"]
    assert first["reply_to_id"] == root["id"]
    # Replying to a reply is folded back to the same root — no chain can grow.
    second = _reply(db, first["id"], body="Trả lời lần hai")["note"]
    assert second["reply_to_id"] == root["id"]

    thread = notes.build_thread(_customer(db, stage="pickup"))
    assert [note["body"] for note in thread] == ["Bình luận gốc"]
    assert [reply["body"] for reply in thread[0]["replies"]] == [
        "Trả lời lần một", "Trả lời lần hai",
    ]
    assert all(reply["replies"] == [] for reply in thread[0]["replies"])


def test_reply_parent_must_belong_to_the_same_lot_and_stage(db):
    root = _write(db, body="Gốc ở lấy hàng", stage="pickup")["note"]
    with pytest.raises(notes.JourneyNoteDenied):
        _reply(db, root["id"], stage="customs")
    db.shipments.insert_one({"id": "G1-LG-999", "customer_id": CUSTOMER_A})
    with pytest.raises(notes.JourneyNoteDenied):
        _reply(db, root["id"], lot="G1-LG-999")
    with pytest.raises(notes.JourneyNoteDenied):
        _reply(db, "jn-does-not-exist")


def test_customer_can_never_reply_to_an_internal_parent(db):
    root = _write(db, body="NỘI BỘ", stage="pickup",
                  visibility=notes.VISIBILITY_INTERNAL)["note"]
    with pytest.raises(notes.JourneyNoteDenied):
        _reply(db, root["id"], actor=CUSTOMER_ACTOR)
    # Staff may reply internally under it…
    staff_reply = _reply(db, root["id"], visibility=notes.VISIBILITY_INTERNAL)
    assert staff_reply["note"]["reply_to_id"] == root["id"]
    # …but must not publish a CUSTOMER-visible reply under an INTERNAL parent.
    with pytest.raises(notes.JourneyNoteDenied):
        _reply(db, root["id"], visibility=notes.VISIBILITY_CUSTOMER)
    thread = notes.build_thread(_customer(db, stage="pickup"))
    assert thread == []


def test_legacy_reply_with_an_invisible_parent_is_never_delivered(db):
    internal_parent = _write(db, body="NỘI BỘ CŨ", stage="pickup",
                             visibility=notes.VISIBILITY_INTERNAL)["note"]
    # A row written before the reply rules existed (or by a bad migration).
    db.quick_notes.insert_one({
        "id": "jn-orphan-reply", "kind": notes.JOURNEY_NOTE_KIND,
        "customer_id": CUSTOMER_A, "shipment_id": LOT_A, "stage_id": "pickup",
        "visibility": notes.VISIBILITY_CUSTOMER, "reply_to_id": internal_parent["id"],
        "body": "PHẢN HỒI MỒ CÔI", "author_kind": "customer",
        "author_name": "Lục Giác", "author_role": "customer",
        "created_at": "2026-10-30T09:00:00+00:00",
    })
    thread = notes.build_thread(_customer(db, stage="pickup"))
    assert "PHẢN HỒI MỒ CÔI" not in json.dumps(thread, ensure_ascii=False)


def test_inline_download_of_a_revoked_file_is_refused(db, store):
    """A file revoked after the thread loaded can never be re-downloaded."""
    _seed_public_event(db)
    outcome = _write(db, body="Ảnh đã thu hồi", stage="pickup", files=[_png()], store=store)
    note_id = outcome["note"]["id"]
    attachment_id = outcome["note"]["attachments"][0]["id"]
    db.quick_notes.update_one(
        {"id": note_id}, {"$set": {"attachments.0.status": "REVOKED"}},
    )
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert discussion["notes"][0]["attachments"] == []
        _trigger(state, "journey_note_download", {
            "shipmentId": LOT_A, "stageId": "pickup", "noteId": note_id,
            "attachmentId": attachment_id, "requestId": "REQ-REVOKED-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert discussion["download"] is None
        assert discussion["downloadOutcome"]["ok"] is False
    assert notes.read_note_attachment(
        note_id=note_id, attachment_id=attachment_id,
        actor=CUSTOMER_ACTOR, db=db, gridfs=store,
    )["ok"] is False


def test_a_comment_never_changes_the_published_progress(db, store):
    """Commenting is not an evidence write: the published stage state is untouched."""
    _seed_public_event(db)
    published = db.public_events.find_one({"id": "EV-1"})
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        stages_before = [node["state"] for node in state["model"]["lots"][0]["journey"]["nodes"]]
        _trigger(state, "journey_note_create", {
            "shipmentId": LOT_A, "stageId": "pickup", "body": "Ý kiến, không phải bằng chứng",
            "visibility": "CUSTOMER", "replyToId": "", "files": [],
            "requestId": "REQ-NO-EVIDENCE-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        state["result"] = None
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        stages_after = [node["state"] for node in state["model"]["lots"][0]["journey"]["nodes"]]
    assert stages_after == stages_before
    assert db.public_events.find_one({"id": "EV-1"}) == published
    assert db.quick_notes.count_documents({"kind": notes.JOURNEY_NOTE_KIND}) == 1


# --------------------------------------------------------------------------
# Issue #236 blocker: a download must prove the OPEN lot + stage
# --------------------------------------------------------------------------

def test_attachment_read_is_bound_to_the_expected_lot_and_stage(db, store):
    outcome = _write(db, body="Tệp của lô A · lấy hàng", stage="pickup",
                     files=[_png()], store=store)
    note_id = outcome["note"]["id"]
    attachment_id = outcome["note"]["attachments"][0]["id"]
    scope = {"customer_id": CUSTOMER_A, "shipment_id": LOT_A, "stage_id": "pickup"}

    # 1. The right scope reads the real bytes.
    good = notes.read_note_attachment(
        note_id=note_id, attachment_id=attachment_id, actor=CUSTOMER_ACTOR,
        db=db, gridfs=store, expected_scope=scope,
    )
    assert good["ok"] is True and good["data"] == PNG_1PX
    assert store.reads == 1

    # 2. Every mismatch is refused BEFORE storage is touched.
    for bad in (
        {**scope, "shipment_id": LOT_B},
        {**scope, "customer_id": CUSTOMER_B},
        {**scope, "stage_id": "customs"},
        {"customer_id": CUSTOMER_A, "shipment_id": LOT_A},          # no stage
        {"shipment_id": LOT_A, "stage_id": "pickup"},               # no customer
        {},                                                         # fail closed
    ):
        refused = notes.read_note_attachment(
            note_id=note_id, attachment_id=attachment_id, actor=SALE,
            db=db, gridfs=store, expected_scope=bad,
        )
        assert refused["ok"] is False
        assert "data" not in refused
        assert refused["error"] == "Không tìm thấy chứng từ."
    assert store.reads == 1, "a refused scope must never read bytes"

    # 3. Omitting the parameter keeps the previous contract for other callers.
    legacy = notes.read_note_attachment(
        note_id=note_id, attachment_id=attachment_id, actor=SALE, db=db, gridfs=store,
    )
    assert legacy["ok"] is True and store.reads == 2


def _second_lot_for_customer_a(db, lot="G1-LG-002"):
    db.shipments.insert_one({"id": lot, "customer_id": CUSTOMER_A, "transport_mode": "SEA"})
    return lot


def test_inline_download_refuses_a_note_from_another_lot_even_with_its_ids(db, store):
    """Knowing the note/file ids of another lot must not fetch its bytes."""
    _seed_public_event(db)
    other_lot = _second_lot_for_customer_a(db)
    other = _write(db, body="TỆP CỦA LÔ KHÁC", stage="pickup", lot=other_lot,
                   files=[_png()], store=store)
    reads_after_upload = store.reads
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        _trigger(state, "journey_note_download", {
            "shipmentId": LOT_A, "stageId": "pickup",
            "noteId": other["note"]["id"],
            "attachmentId": other["note"]["attachments"][0]["id"],
            "requestId": "REQ-CROSS-LOT-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert discussion["download"] is None, "no bytes may reach the payload"
        assert discussion["downloadOutcome"]["ok"] is False
        state["result"] = None
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert state["model"]["discussion"]["download"] is None
    assert store.reads == reads_after_upload, "a cross-lot download must not read storage"


def test_inline_download_refuses_a_note_from_another_stage_of_the_same_lot(db, store):
    _seed_public_event(db)
    other_stage = _write(db, body="TỆP CỦA CÔNG ĐOẠN KHÁC", stage="customs",
                         files=[_png()], store=store)
    reads_after_upload = store.reads
    app, state, stack = _portal_inline(db, store)
    with stack:
        _focus(app, LOT_A, "pickup")
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        _trigger(state, "journey_note_download", {
            "shipmentId": LOT_A, "stageId": "pickup",
            "noteId": other_stage["note"]["id"],
            "attachmentId": other_stage["note"]["attachments"][0]["id"],
            "requestId": "REQ-CROSS-STAGE-1",
        })
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        discussion = state["model"]["discussion"]
        assert discussion["download"] is None
        assert discussion["downloadOutcome"]["ok"] is False
        state["result"] = None
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        assert state["model"]["discussion"]["download"] is None
    assert store.reads == reads_after_upload


_STAFF_INLINE_EVENT_SCRIPT = (
    "import streamlit as st\n"
    "from views import journey_inline\n"
    "user = {'username': 'sale.thanh', 'role': 'sale'}\n"
    "st.session_state['out'] = journey_inline.consume_staff_triggers(\n"
    "    {'seq': 0}, st.session_state['event'], user=user,\n"
    "    shipments=st.session_state['rows'],\n"
    ")\n"
    "slot = st.session_state.get(journey_inline.STAFF_DOWNLOAD_KEY)\n"
    "st.session_state['slot'] = bool(slot)\n"
    "st.session_state['slot_len'] = len(str((slot or {}).get('base64') or ''))\n"
)


def _staff_inline_event(db, store, event, payload, rows):
    with _internal_stack(db, store):
        app = AppTest.from_string(_STAFF_INLINE_EVENT_SCRIPT, default_timeout=120)
        app.session_state["rows"] = rows
        app.session_state["event"] = {
            event: {"seq": 1, "event": event, "payload": payload},
        }
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        return (
            app.session_state["out"], app.session_state["slot"],
            app.session_state["slot_len"],
        )


def test_staff_inline_download_refuses_a_lot_outside_the_projection(db, store):
    """A staff download cannot cross into a lot the operator's projection lacks."""
    outside = "G1-LG-900"
    db.shipments.insert_one({"id": outside, "customer_id": CUSTOMER_A})
    hidden = _write(db, body="TỆP LÔ NGOÀI PROJECTION", stage="pickup", lot=outside,
                    files=[_png()], store=store)
    reads_after_upload = store.reads
    rows = [{"id": LOT_A, "customerId": CUSTOMER_A,
             "journey": {"nodes": [{"id": "pickup-1", "label": "Lấy hàng"}]}}]

    # The forged focus for the hidden lot is itself refused: it is not in rows.
    outcomes, slot, slot_len = _staff_inline_event(db, store, "journey_note_download", {
        "shipmentId": outside, "stageId": "pickup",
        "noteId": hidden["note"]["id"],
        "attachmentId": hidden["note"]["attachments"][0]["id"],
        "requestId": "REQ-HIDDEN-FOCUS-1",
    }, rows)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is False
    assert outcomes[0]["gate"] == "INVALID_SCOPE"
    assert slot is False and slot_len == 0

    # Even with a VALID focus (lot A), the hidden lot's ids are refused.
    outcomes, slot, slot_len = _staff_inline_event(db, store, "journey_note_download", {
        "shipmentId": LOT_A, "stageId": "pickup", "nodeId": "pickup-1",
        "noteId": hidden["note"]["id"],
        "attachmentId": hidden["note"]["attachments"][0]["id"],
        "requestId": "REQ-HIDDEN-IDS-1",
    }, rows)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is False
    assert outcomes[0]["gate"] == "NOT_FOUND"
    assert slot is False and slot_len == 0, "no byte may be queued for the browser"
    assert store.reads == reads_after_upload


def test_staff_inline_download_matches_a_note_in_the_same_open_scope(db, store):
    _seed_public_event(db)
    note = _write(db, body="TỆP ĐÚNG PHẠM VI", stage="pickup", files=[_png()], store=store)
    rows = [{"id": LOT_A, "customerId": CUSTOMER_A,
             "journey": {"nodes": [{"id": "pickup-1", "label": "Lấy hàng"}]}}]
    outcomes, slot, slot_len = _staff_inline_event(db, store, "journey_note_download", {
        "shipmentId": LOT_A, "stageId": "pickup", "nodeId": "pickup-1",
        "noteId": note["note"]["id"],
        "attachmentId": note["note"]["attachments"][0]["id"],
        "requestId": "REQ-MATCH-1",
    }, rows)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is True
    assert slot is True and slot_len > 0
    assert store.reads >= 1


def test_inline_download_bytes_are_one_shot_tenant_bound_and_repeatable():
    """A repeated click on the SAME attachment must get a new sequence number."""
    fake = FakeStreamlit()
    session_key = journey_inline.STAFF_DOWNLOAD_KEY
    saved = {"data": PNG_1PX, "name": "repeat.png", "mime": "image/png"}
    kwargs = {
        "shipment_id": LOT_A, "stage_id": "pickup", "customer_id": CUSTOMER_A,
        "note_id": "jn-repeat", "attachment_id": "att-repeat", "outcome": saved,
    }
    with patch.object(journey_inline, "st", fake):
        seq_1 = journey_inline._store_download(session_key, **kwargs)
        first = journey_inline._take_download(session_key, LOT_A, "pickup", CUSTOMER_A)
        assert seq_1 == 1 and first["seq"] == 1
        assert base64.b64decode(first["base64"]) == PNG_1PX
        assert session_key not in fake.session_state

        # This was broken: the consumed slot made each click start again at 1,
        # so the React/jsdom download dedupe ignored subsequent clicks.
        seq_2 = journey_inline._store_download(session_key, **kwargs)
        second = journey_inline._take_download(session_key, LOT_A, "pickup", CUSTOMER_A)
        assert seq_2 == 2 and second["seq"] == 2
        assert base64.b64decode(second["base64"]) == PNG_1PX

        # Even a matching lot+stage is not enough if ownership has changed.
        seq_3 = journey_inline._store_download(session_key, **kwargs)
        assert seq_3 == 3
        assert journey_inline._take_download(session_key, LOT_A, "pickup", CUSTOMER_B) is None
        assert session_key not in fake.session_state


def test_denied_download_clears_previously_queued_bytes_even_with_known_ids(db):
    """A denied request may not accidentally emit a pending prior file."""
    fake = FakeStreamlit()
    session_key = journey_inline.STAFF_DOWNLOAD_KEY
    kwargs = {
        "shipment_id": LOT_A, "stage_id": "pickup", "customer_id": CUSTOMER_A,
        "note_id": "jn-old", "attachment_id": "att-old",
        "outcome": {"data": PNG_1PX, "name": "old.png", "mime": "image/png"},
    }
    rows = [{"id": LOT_A, "customerId": CUSTOMER_A}]
    user = {"username": "sale.thanh", "role": "sale"}
    with patch.object(journey_inline, "st", fake):
        journey_inline._store_download(session_key, **kwargs)
        refused = journey_inline.consume_staff_triggers(
            {"seq": 0},
            {"journey_note_download": {
                "seq": 1, "payload": {
                    "shipmentId": LOT_A, "stageId": "pickup",
                    "noteId": "jn-nonexistent", "attachmentId": "att-old",
                    "requestId": "REQ-DENIED-QUEUED",
                },
            }},
            user=user, shipments=rows, db=db,
        )
        assert len(refused) == 1 and refused[0]["ok"] is False
        assert session_key not in fake.session_state
        assert journey_inline._take_download(session_key, LOT_A, "pickup", CUSTOMER_A) is None

        # A forged focus outside the current staff projection also clears it.
        journey_inline._store_download(session_key, **kwargs)
        refused_focus = journey_inline.consume_staff_triggers(
            {"seq": 0},
            {"journey_note_download": {
                "seq": 2, "payload": {
                    "shipmentId": "LOT-HIDDEN", "stageId": "pickup",
                    "noteId": "jn-old", "attachmentId": "att-old",
                    "requestId": "REQ-DENIED-FOCUS",
                },
            }},
            user=user, shipments=rows, db=db,
        )
        assert len(refused_focus) == 1
        assert refused_focus[0]["gate"] == "INVALID_SCOPE"
        assert session_key not in fake.session_state


@pytest.mark.parametrize("change", ["revoked", "reassigned"])
def test_queued_file_is_rechecked_before_component_payload(db, store, change):
    """File bytes queued before a permission change must never reach the UI."""
    original = _write(db, body="Đính kèm", stage="pickup", files=[_png()], store=store)
    note_id = original["note"]["id"]
    attachment_id = original["note"]["attachments"][0]["id"]
    fake = FakeStreamlit()
    key = journey_inline.STAFF_DOWNLOAD_KEY
    kwargs = dict(
        shipment_id=LOT_A, stage_id="pickup", customer_id=CUSTOMER_A,
        note_id=note_id, attachment_id=attachment_id,
        outcome={"data": PNG_1PX, "name": "bang-ke.png", "mime": "image/png"},
    )
    focus = {"customer_id": CUSTOMER_A, "shipment_id": LOT_A, "stage_id": "pickup"}
    rows = [{"id": LOT_A, "customerId": CUSTOMER_A}]
    def payload():
        return journey_inline._discussion_payload(
            actor=SALE, focus=focus, rows=rows, session_key=key,
            can_see_internal=True, db=db,
        )
    with patch.object(journey_inline, "st", fake):
        # Prove the positive path still delivers exactly the queued file.
        journey_inline._store_download(key, **kwargs)
        allowed = payload()
        assert base64.b64decode(allowed["download"]["base64"]) == PNG_1PX
        assert key not in fake.session_state

        # Then queue the same attachment and revoke it BEFORE model emission.
        journey_inline._store_download(key, **kwargs)
        if change == "revoked":
            db.quick_notes.update_one(
                {"id": note_id}, {"$set": {"attachments.0.status": "REVOKED"}},
            )
        else:
            db.shipments.update_one(
                {"id": LOT_A}, {"$set": {"customer_id": CUSTOMER_B}},
            )
        denied = payload()
        assert denied["download"] is None
        assert key not in fake.session_state
        assert "base64" not in json.dumps(denied, ensure_ascii=False)
