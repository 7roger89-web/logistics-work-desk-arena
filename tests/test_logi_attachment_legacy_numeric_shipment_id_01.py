"""LOGI_ATTACHMENT_LEGACY_NUMERIC_SHIPMENT_ID_01 — Legacy numeric shipment ID compatibility.

Regression proof for Issue #117:
A legacy shipment stored in Mongo with numeric BSON id (e.g. 108313713320)
is projected to the UI as string "108313713320". Attachment upload receives
shipmentId="108313713320". Before the fix, read_shipment("108313713320") fails
exact Mongo match against numeric BSON 108313713320, returning None and halting
with SHIPMENT_NOT_FOUND and error "Không tìm thấy lô 108313713320."
"""

from __future__ import annotations

import base64
from typing import Any, Mapping
from unittest.mock import patch

import pytest

from core import database as db
from core import shipment_attachments as att
from tests.test_logi_shipment_documents_drive_02 import CountingFactory, FakeDrive
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

PRODUCTION_NUMERIC_ID = 108313713320
PRODUCTION_STRING_ID = "108313713320"


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Isolated mongomock database with deterministic staging operator."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = {
        "username": "staging.support",
        "role": "SUPPORT",
        "full_name": "Thu Hằng (Preview/Staging)",
        "user_id": "STAGING-SUPPORT",
    }
    st.session_state.pop(vm.ATTACHMENT_DOWNLOAD_KEY, None)
    yield transport
    st.session_state.pop(vm.ATTACHMENT_DOWNLOAD_KEY, None)
    logi_sandbox.reset_backend()


@pytest.fixture()
def seq():
    state = {"n": 0}

    def _next() -> int:
        state["n"] += 1
        return state["n"]

    return _next


def _upload_payload(
    file_name: str = "bang_ke.png",
    mime: str = "image/png",
    data: bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake",
    *,
    shipment_id: str = PRODUCTION_STRING_ID,
    category: str = "customs",
    request_id: str = "req-legacy-01",
) -> dict[str, Any]:
    return {
        "shipmentId": shipment_id,
        "category": category,
        "fileName": file_name,
        "mime": mime,
        "size": len(data),
        "base64": base64.b64encode(data).decode("ascii"),
        "requestId": request_id,
    }


def _dispatch(name: str, payload: Mapping[str, Any], seq_fn) -> dict[str, Any]:
    trigger = {name: {"seq": seq_fn(), "event": name, "payload": dict(payload)}}
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, trigger)
    assert len(outcomes) == 1
    return outcomes[0]


# ---------------------------------------------------------------------------
# 1. Authoritative read boundary identity semantics
# ---------------------------------------------------------------------------

class TestReadShipmentLegacyIdentityBoundary:
    def test_legacy_numeric_candidate_helper(self):
        assert vm.legacy_numeric_candidate(PRODUCTION_STRING_ID) == PRODUCTION_NUMERIC_ID
        assert vm.legacy_numeric_candidate("0") == 0
        assert vm.legacy_numeric_candidate("123") == 123
        assert vm.legacy_numeric_candidate("00123") is None
        assert vm.legacy_numeric_candidate("+123") is None
        assert vm.legacy_numeric_candidate("-123") is None
        assert vm.legacy_numeric_candidate("123.0") is None
        assert vm.legacy_numeric_candidate(" 123 ") is None
        assert vm.legacy_numeric_candidate("123 ") is None
        assert vm.legacy_numeric_candidate(" 123") is None
        assert vm.legacy_numeric_candidate("LO-0306") is None
        assert vm.legacy_numeric_candidate("") is None
        assert vm.legacy_numeric_candidate(None) is None
        assert vm.legacy_numeric_candidate(123) is None
        assert vm.legacy_numeric_candidate("9999999999999999999999999999999999999999") is None

    def test_legacy_numeric_bson_id_resolves_from_canonical_string(self, staging):
        database = db.get_db()
        database.shipments.insert_one({
            "id": PRODUCTION_NUMERIC_ID,
            "customer": "CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI TIẾN THÀNH",
            "is_deleted": False,
            "version": 1,
            "data": {},
        })

        # Exact query with string should resolve through bounded fallback
        shipment = vm.read_shipment(PRODUCTION_STRING_ID)
        assert shipment is not None, "Canonical string representation of numeric ID must resolve"
        # Mongo document must NOT be mutated merely because fallback read occurred
        stored = database.shipments.find_one({"id": PRODUCTION_NUMERIC_ID}, {"_id": 0})
        assert stored is not None
        assert stored["id"] == PRODUCTION_NUMERIC_ID
        assert isinstance(stored["id"], int)

    def test_exact_string_id_takes_precedence_over_numeric_fallback(self, staging):
        database = db.get_db()
        target_id = 998877
        string_id = "998877"

        database.shipments.insert_one({
            "id": string_id,
            "customer": "String Document (Wins)",
            "is_deleted": False,
        })
        database.shipments.insert_one({
            "id": target_id,
            "customer": "Numeric Document (Shadowed)",
            "is_deleted": False,
        })

        shipment = vm.read_shipment(string_id)
        assert shipment is not None
        assert shipment["customer"] == "String Document (Wins)", "Exact string id must win over numeric candidate"

    def test_ambiguous_numeric_looking_ids_do_not_coerce(self, staging):
        database = db.get_db()
        database.shipments.insert_one({
            "id": 123,
            "customer": "Numeric 123",
            "is_deleted": False,
        })

        ambiguous_cases = [
            "00123",       # leading zeros
            "+123",        # explicit plus
            "-123",        # negative
            "123.0",       # float format
            " 123 ",       # surrounding whitespace
            "123 ",        # trailing whitespace
            " 123",        # leading whitespace
        ]

        for amb in ambiguous_cases:
            assert vm.read_shipment(amb) is None, f"Ambiguous string {amb!r} must NOT coerce to numeric 123"

    def test_unknown_shipment_returns_none(self, staging):
        assert vm.read_shipment("999999999999") is None
        assert vm.read_shipment("NON_EXISTENT") is None
        assert vm.read_shipment("") is None
        assert vm.read_shipment(None) is None

    def test_direct_numeric_int_input_resolves(self, staging):
        database = db.get_db()
        database.shipments.insert_one({
            "id": PRODUCTION_NUMERIC_ID,
            "customer": "Direct Int Customer",
            "is_deleted": False,
        })
        shipment = vm.read_shipment(PRODUCTION_NUMERIC_ID)
        assert shipment is not None
        assert shipment["customer"] == "Direct Int Customer"


# ---------------------------------------------------------------------------
# 2. Attachment upload path with legacy numeric shipment ID
# ---------------------------------------------------------------------------

class TestAttachmentUploadLegacyNumericShipmentId:
    def test_production_legacy_numeric_shipment_upload_succeeds(self, staging, seq, monkeypatch):
        monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
        database = db.get_db()
        database.shipments.insert_one({
            "id": PRODUCTION_NUMERIC_ID,
            "customer": "Legacy Test Customer",
            "is_deleted": False,
            "version": 1,
            "data": {},
        })

        fake_drive = FakeDrive()
        factory = CountingFactory(fake_drive)

        with patch("core.shipment_attachments.build_drive_client", factory):
            outcome = _dispatch(
                "shipment_attachment_upload",
                _upload_payload(shipment_id=PRODUCTION_STRING_ID),
                seq,
            )

        assert outcome["gate"] != "SHIPMENT_NOT_FOUND", "Legacy numeric shipment must NOT fail with SHIPMENT_NOT_FOUND"
        assert outcome["ok"] is True, f"Upload must succeed, got error: {outcome.get('error')}"
        assert outcome["gate"] == "UPLOADED"
        assert len(fake_drive.uploads) == 1, "Exactly ONE Drive storage upload call must occur"
        assert factory.calls == 1

        # Verify metadata is safely keyed to canonical string UI id
        attachments = db.load_shipment_attachments(PRODUCTION_STRING_ID)
        assert len(attachments) == 1
        persisted = list(attachments.values())[0]
        assert persisted["shipment_id"] == PRODUCTION_STRING_ID

        # Verify readback exposes attachment under that shipment
        readback = outcome.get("readback") or {}
        assert readback.get("id") == PRODUCTION_STRING_ID
        readback_attachments = readback.get("attachments") or []
        assert len(readback_attachments) == 1
        assert readback_attachments[0]["id"] == persisted["id"]

    def test_standard_string_shipment_upload_preserves_behavior(self, staging, seq, monkeypatch):
        monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
        fake_drive = FakeDrive()
        factory = CountingFactory(fake_drive)

        with patch("core.shipment_attachments.build_drive_client", factory):
            outcome = _dispatch(
                "shipment_attachment_upload",
                _upload_payload(shipment_id="LO-0306"),
                seq,
            )

        assert outcome["ok"] is True
        assert outcome["gate"] == "UPLOADED"
        assert len(fake_drive.uploads) == 1
        assert factory.calls == 1
        attachments = db.load_shipment_attachments("LO-0306")
        assert len(attachments) >= 1

    def test_unknown_shipment_zero_storage_calls(self, staging, seq, monkeypatch):
        monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
        fake_drive = FakeDrive()
        factory = CountingFactory(fake_drive)

        with patch("core.shipment_attachments.build_drive_client", factory):
            outcome = _dispatch(
                "shipment_attachment_upload",
                _upload_payload(shipment_id="999999999999"),
                seq,
            )

        assert outcome["ok"] is False
        assert outcome["gate"] == "SHIPMENT_NOT_FOUND"
        assert "Không tìm thấy lô 999999999999." in outcome["error"]
        assert len(fake_drive.uploads) == 0, "Unknown shipment must produce ZERO storage calls"
        assert factory.calls == 0

    def test_ambiguous_shipment_id_zero_storage_calls(self, staging, seq, monkeypatch):
        monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "drive_shared")
        database = db.get_db()
        database.shipments.insert_one({
            "id": 123,
            "customer": "Numeric 123",
            "is_deleted": False,
        })
        fake_drive = FakeDrive()
        factory = CountingFactory(fake_drive)

        with patch("core.shipment_attachments.build_drive_client", factory):
            outcome = _dispatch(
                "shipment_attachment_upload",
                _upload_payload(shipment_id="00123"),
                seq,
            )

        assert outcome["ok"] is False
        assert outcome["gate"] == "SHIPMENT_NOT_FOUND"
        assert len(fake_drive.uploads) == 0, "Ambiguous id must produce ZERO storage calls"
        assert factory.calls == 0

    def test_gridfs_backend_legacy_numeric_shipment_upload_succeeds(self, staging, seq, monkeypatch):
        monkeypatch.setenv("ATTACHMENT_STORAGE_BACKEND", "gridfs")
        database = db.get_db()
        database.shipments.insert_one({
            "id": PRODUCTION_NUMERIC_ID,
            "customer": "Legacy Test Customer (GridFS)",
            "is_deleted": False,
            "version": 1,
            "data": {},
        })

        outcome = _dispatch(
            "shipment_attachment_upload",
            _upload_payload(shipment_id=PRODUCTION_STRING_ID),
            seq,
        )

        assert outcome["gate"] != "SHIPMENT_NOT_FOUND"
        assert outcome["ok"] is True, f"GridFS upload must succeed, got error: {outcome.get('error')}"
        assert outcome["gate"] == "UPLOADED"

        # Verify metadata is safely keyed to canonical string UI id
        attachments = db.load_shipment_attachments(PRODUCTION_STRING_ID)
        assert len(attachments) == 1
        persisted = list(attachments.values())[0]
        assert persisted["shipment_id"] == PRODUCTION_STRING_ID
        assert persisted["storage_backend"] == "gridfs"

        # Verify readback exposes attachment under that shipment
        readback = outcome.get("readback") or {}
        assert readback.get("id") == PRODUCTION_STRING_ID
        readback_attachments = readback.get("attachments") or []
        assert len(readback_attachments) == 1
        assert readback_attachments[0]["id"] == persisted["id"]
