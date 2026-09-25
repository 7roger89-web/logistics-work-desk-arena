from __future__ import annotations

import base64
from unittest.mock import patch

import pytest

from core import database as db
from tests.test_logi_shipment_documents_drive_02 import CountingFactory, FakeDrive
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

SID = "108313713320"


@pytest.fixture()
def staging():
    import streamlit as st
    logi_sandbox.reset_backend()
    logi_sandbox.ensure_backend()
    st.session_state["current_user"] = {
        "username": "staging.support",
        "role": "SUPPORT",
        "full_name": "Thu Hằng (Preview/Staging)",
        "user_id": "STAGING-SUPPORT",
    }
    yield
    logi_sandbox.reset_backend()


@pytest.fixture()
def seq():
    state = {"n": 0}
    def _next():
        state["n"] += 1
        return state["n"]
    return _next


def payload():
    raw = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake"
    return {
        "shipmentId": SID,
        "category": "customs",
        "fileName": "anh.png",
        "mime": "image/png",
        "size": len(raw),
        "base64": base64.b64encode(raw).decode("ascii"),
        "requestId": "req-projected-id",
    }


def dispatch(seq_fn):
    trigger = {
        "shipment_attachment_upload": {
            "seq": seq_fn(),
            "event": "shipment_attachment_upload",
            "payload": payload(),
        }
    }
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, trigger)
    assert len(outcomes) == 1
    return outcomes[0]


def test_trimmed_stored_identity_matches_ui_projection(staging):
    database = db.get_db()
    stored_id = SID + " "
    database.shipments.insert_one({
        "id": stored_id,
        "customer": "Legacy",
        "is_deleted": False,
        "version": 1,
        "data": {},
    })
    stored = database.shipments.find_one({"id": stored_id}, {"_id": 0})
    assert rd.text(stored["id"]) == SID

    shipment, gate = vm._read_shipment_resolution(SID)
    assert gate == "PROJECTED_IDENTITY"
    assert shipment is not None
    assert rd.text(shipment.get("id")) == SID

    unchanged = database.shipments.find_one({"id": stored_id}, {"_id": 0})
    assert unchanged["id"] == stored_id


def test_projected_identity_upload_uses_existing_storage_path(staging, seq, monkeypatch):
    monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
    database = db.get_db()
    database.shipments.insert_one({
        "id": SID + " ",
        "customer": "Legacy",
        "is_deleted": False,
        "version": 1,
        "data": {},
    })
    fake = FakeDrive()
    factory = CountingFactory(fake)
    with patch("core.shipment_attachments.build_drive_client", factory):
        outcome = dispatch(seq)

    assert outcome["ok"] is True
    assert outcome["gate"] == "UPLOADED"
    assert factory.calls == 1
    assert len(fake.uploads) == 1
    rows = db.load_shipment_attachments(SID)
    assert len(rows) == 1
    assert next(iter(rows.values()))["shipment_id"] == SID


def test_duplicate_projected_identity_fails_closed_before_storage(staging, seq, monkeypatch):
    monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
    database = db.get_db()
    database.shipments.insert_one({
        "id": SID + " ",
        "customer": "Legacy A",
        "is_deleted": False,
        "version": 1,
        "data": {},
    })
    database.shipments.insert_one({
        "id": " " + SID,
        "customer": "Legacy B",
        "is_deleted": False,
        "version": 1,
        "data": {},
    })
    fake = FakeDrive()
    factory = CountingFactory(fake)
    with patch("core.shipment_attachments.build_drive_client", factory):
        outcome = dispatch(seq)

    assert outcome["ok"] is False
    assert outcome["gate"] == vm.SHIPMENT_IDENTITY_AMBIGUOUS
    assert factory.calls == 0
    assert len(fake.uploads) == 0
