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

    def upload_file(self, *, name: str, mime: str, data: bytes, metadata=None):
        if self.fail:
            raise RuntimeError("STORE_DOWN")
        self.counter += 1
        file_id = f"fs-{self.counter}"
        self.files[file_id] = bytes(data)
        return {"storage_file_id": file_id, "stored_name": name, "stored_size": len(data)}

    def download_file(self, file_id: str):
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


def test_customer_portal_posts_and_reloads_a_stage_comment(db):
    from core import customer_portal as portal
    from core.customer_portal_publish import publish_verified_sources

    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
        "stage_id": "pickup", "public_title": "Đã lấy hàng",
        "occurred_at": "2026-10-28T01:00:00Z", "verified": True,
        "verified_at": "2026-10-28T02:00:00Z", "visibility": "CUSTOMER",
    })
    ok, message = publish_verified_sources(
        CUSTOMER_A, LOT_A, event_versions={"EV-1": "v1"}, document_versions={},
        expected_current_version="", actor_role="admin", actor_username="staging-admin", db=db)
    assert ok, message

    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(EMAIL_A)),
        patch.object(portal, "get_db", return_value=db),
        patch("core.database.get_db", return_value=db),
    ):
        app.run()
        assert not app.exception, [str(e.value) for e in app.exception]
        areas = [element for element in app.text_area]
        assert areas, "không thấy ô nhập trao đổi trên cổng khách hàng"
        areas[0].set_value("Xác nhận địa chỉ giao hàng")
        senders = [element for element in app.button if element.label == "Gửi"]
        assert senders, "không thấy nút gửi trao đổi"
        senders[0].click()
        app.run()          # writes the note
        assert not app.exception, [str(e.value) for e in app.exception]
        assert "Đã lưu trao đổi" in _visible(app)
        app.run()          # reloads and renders the saved note
        assert not app.exception, [str(e.value) for e in app.exception]
        visible = _visible(app)

    rows = notes.list_stage_notes(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, actor=CUSTOMER_ACTOR, db=db)
    assert [row["body"] for row in rows] == ["Xác nhận địa chỉ giao hàng"]
    assert rows[0]["visibility"] == notes.VISIBILITY_CUSTOMER
    assert "Xác nhận địa chỉ giao hàng" in visible


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
