"""Focused Issue #143 evidence for durable generated PXK/GNT files.

These tests keep the generator and attachment service seams injectable. They do
not require production Mongo, Google Drive, OAuth, or secrets.
"""

from __future__ import annotations

import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from pymongo.errors import DuplicateKeyError

from views import logi_c1
from views import logi_view_model as vm


SHIPMENT = {
    "id": "SHP-143",
    "customer_id": "CUS-143",
    "data": {
        "0.0": {
            "commercial_flow": {
                "mode": "CUSTOMER_SELF",
                "confirmed": True,
                "company_id": "",
                "sub_agent_id": "",
            },
        },
        "2.4": {},
    },
}

GNT_DATA = {
    "shipment_id": "SHP-143",
    "tk_no": "TK-143",
    "tk_date": "15/09/2026",
    "import_duty_amount": 5000000.0,
    "import_vat_amount": 800000.0,
    "taxpayer_name": "CÔNG TY 143",
    "taxpayer_tax_code": "0101430143",
    "taxpayer_address": "Hà Nội",
}


class FakeDocgenCollection:
    def __init__(self, rows=None, insert_barrier=None):
        self.rows = [copy.deepcopy(row) for row in (rows or [])]
        self.lock = threading.Lock()
        self.insert_barrier = insert_barrier

    def find_one(self, query, projection=None):
        with self.lock:
            for row in self.rows:
                if all(row.get(key) == value for key, value in query.items()):
                    result = copy.deepcopy(row)
                    if projection and projection.get("_id") == 0:
                        result.pop("_id", None)
                    return result
        return None

    def insert_one(self, document):
        if self.insert_barrier is not None:
            self.insert_barrier.wait(timeout=5)
        with self.lock:
            if any(row.get("_id") == document.get("_id") for row in self.rows):
                raise DuplicateKeyError("duplicate _id")
            self.rows.append(copy.deepcopy(document))
        return type("InsertResult", (), {"inserted_id": document.get("_id")})()


class FakeDatabase:
    def __init__(self, collection):
        self.collection = collection

    def __getitem__(self, name):
        assert name == "docgen_documents"
        return self.collection


def _gnt_metadata(*, output_hash="hash-1", revision=1):
    logical = "GNT::SHP-143"
    return {
        "id": f"{logical}::R{revision}",
        "document_id": logical,
        "document_type": "GNT",
        "shipment_id": "SHP-143",
        "contract_id": "",
        "parent_contract_id": None,
        "counterparty_id": "",
        "template_hash": "",
        "generation_revision": revision,
        "revision": revision,
        "status": "GENERATED",
        "source_snapshot": {"tk_no": "TK-143"},
        "source_reference": "GNT:SHP-143",
        "output_file_name": "GNT_SHP-143_TK-143.xlsx",
        "output_hash": output_hash,
        "supersedes_document_id": None,
        "superseded_by_document_id": None,
    }


def _install_fake_docgen_db(monkeypatch, collection):
    database = FakeDatabase(collection)
    monkeypatch.setattr("core.database.get_db", lambda: database)
    monkeypatch.setattr("core.database._actor_context", lambda: {
        "username": "writer-143",
        "user_id": "USER-143",
        "role": "admin",
    })
    monkeypatch.setattr("core.database._audit", lambda *args, **kwargs: None)
    return database


@pytest.fixture()
def ready_gnt(monkeypatch):
    """Patch only the business/generator seams; storage remains observable."""
    monkeypatch.setattr("core.auth.can_generate_documents", lambda: True)
    monkeypatch.setattr("core.auth.current_user", lambda: {"username": "writer-143"})
    monkeypatch.setattr(vm, "read_shipment", lambda shipment_id: copy.deepcopy(SHIPMENT))
    monkeypatch.setattr(
        "core.database.load_customers",
        lambda: {
            "CUS-143": {
                "customer_id": "CUS-143",
                "name": "CÔNG TY 143",
                "tax_code": "0101430143",
            },
        },
    )
    monkeypatch.setattr(
        "core.gnt_builder.check_gnt_prerequisites",
        lambda shipment: {"data": dict(GNT_DATA), "missing": [], "no_payable": False},
    )
    monkeypatch.setattr("core.gnt_builder.build_gnt_workbook", lambda data: b"PK-gnt-xlsx")
    monkeypatch.setattr("core.database.load_docgen_documents", lambda shipment_id: {})
    monkeypatch.setattr(vm, "_attachment_result_extras", lambda shipment_id: {})
    monkeypatch.setattr(vm, "_project_generated_attachment", lambda outcome: {"id": "ATT-143"})
    return monkeypatch


def _attachment_outcome(*, duplicate: bool = False):
    return {
        "ok": True,
        "code": "DUPLICATE" if duplicate else "",
        "duplicate": duplicate,
        "record": {
            "id": "ATT-143",
            "shipment_id": "SHP-143",
            "original_name": "GNT_SHP-143_TK-143.xlsx",
        },
    }


def test_session_output_store_gap_is_reproducible():
    """The old byte authority disappears when the Streamlit session is cleared."""
    import streamlit as st

    key = logi_c1._outputs_key("SHP-143")
    st.session_state[key] = {"GNT::SHP-143::R1": {"bytes": b"PK-only-session"}}
    assert logi_c1.stored_outputs("SHP-143")

    st.session_state[key] = {}
    assert logi_c1.stored_outputs("SHP-143") == {}


def test_gnt_revision_reads_durable_docgen_metadata_not_session_cache(monkeypatch):
    monkeypatch.setattr(
        "core.database.load_docgen_documents",
        lambda shipment_id: {
            "GNT::SHP-143::R1": {
                "id": "GNT::SHP-143::R1",
                "document_id": "GNT::SHP-143",
                "document_type": "GNT",
                "shipment_id": "SHP-143",
                "revision": 1,
                "generation_revision": 1,
            },
            "GNT::SHP-143::R3": {
                "id": "GNT::SHP-143::R3",
                "document_id": "GNT::SHP-143",
                "document_type": "GNT",
                "shipment_id": "SHP-143",
                "revision": 3,
                "generation_revision": 3,
            },
        },
    )
    monkeypatch.setattr(
        vm.logi_c1,
        "stored_outputs",
        lambda shipment_id: pytest.fail("session cache must not own GNT revision"),
    )

    result = vm._next_gnt_revision("SHP-143")

    assert result == {"ok": True, "document_id": "GNT::SHP-143", "revision": 4}


def test_gnt_attachment_failure_does_not_create_session_success(ready_gnt, monkeypatch):
    upload = Mock(return_value={"ok": False, "code": "GRIDFS_FAILED", "error": "write failed"})
    store = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    monkeypatch.setattr(vm.logi_c1, "store_output", store)

    result = vm._handle_gnt_generate({"shipmentId": "SHP-143"})

    assert result["ok"] is False
    assert result["gate"] == "GRIDFS_FAILED"
    assert result["attachmentPersisted"] is False
    store.assert_not_called()
    upload.assert_called_once()
    assert upload.call_args.kwargs["category"] == "customs"
    assert upload.call_args.kwargs["shipment_id"] == "SHP-143"
    assert upload.call_args.kwargs["declared_size"] == len(b"PK-gnt-xlsx")


def test_gnt_duplicate_is_success_and_metadata_then_cache_are_allowed(ready_gnt, monkeypatch):
    upload = Mock(return_value=_attachment_outcome(duplicate=True))
    persist = Mock(return_value={"ok": True})
    store = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    monkeypatch.setattr(vm, "_persist_generated_docgen_metadata", persist)
    monkeypatch.setattr(vm.logi_c1, "store_output", store)

    result = vm._handle_gnt_generate({"shipmentId": "SHP-143"})

    assert result["ok"] is True
    assert result["persisted"]["attachmentDuplicate"] is True
    assert result["persisted"]["revision"] == 1
    persist.assert_called_once()
    store.assert_called_once()
    assert upload.call_args.kwargs["category"] == "customs"


def test_metadata_failure_preserves_proven_attachment_and_skips_cache(ready_gnt, monkeypatch):
    upload = Mock(return_value=_attachment_outcome())
    persist = Mock(return_value={
        "ok": False,
        "collision": True,
        "error": "revision collision",
        "metadata_committed": False,
    })
    store = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    monkeypatch.setattr(vm, "_persist_generated_docgen_metadata", persist)
    monkeypatch.setattr(vm.logi_c1, "store_output", store)

    result = vm._handle_gnt_generate({"shipmentId": "SHP-143"})

    assert result["ok"] is False
    assert result["gate"] == "GNT_REVISION_COLLISION"
    assert result["attachmentPersisted"] is True
    assert result["partialDurable"] is True
    assert result["attachment"]["id"] == "ATT-143"
    store.assert_not_called()


def test_atomic_create_returns_created_and_fresh_read_matches(monkeypatch):
    from core import database as db

    collection = FakeDocgenCollection()
    _install_fake_docgen_db(monkeypatch, collection)
    candidate = _gnt_metadata()

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["ok"] is True
    assert result["status"] == db.DOCGEN_REVISION_CREATED
    stored = collection.find_one({"_id": candidate["id"]})
    assert stored["id"] == candidate["id"]
    assert stored["output_hash"] == candidate["output_hash"]


def test_atomic_same_identity_same_content_is_already_matching(monkeypatch):
    from core import database as db

    candidate = _gnt_metadata()
    collection = FakeDocgenCollection([dict(candidate, _id="ordinary-object-id")])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["ok"] is True
    assert result["status"] == db.DOCGEN_REVISION_ALREADY_MATCHING
    assert len(collection.rows) == 1
    assert collection.rows[0]["_id"] == "ordinary-object-id"


def test_atomic_same_identity_different_content_is_collision(monkeypatch):
    from core import database as db

    winner = _gnt_metadata(output_hash="winner")
    collection = FakeDocgenCollection([dict(winner, _id="ordinary-object-id")])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(_gnt_metadata(output_hash="loser"))

    assert result["ok"] is False
    assert result["status"] == db.DOCGEN_REVISION_COLLISION
    assert len(collection.rows) == 1
    assert collection.rows[0]["output_hash"] == "winner"


def test_atomic_absent_same_revision_race_settles_without_pre_read_authority(monkeypatch):
    from core import database as db

    barrier = threading.Barrier(2)
    collection = FakeDocgenCollection(insert_barrier=barrier)
    _install_fake_docgen_db(monkeypatch, collection)
    candidate = _gnt_metadata()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(db.create_or_observe_docgen_revision, [candidate, dict(candidate)]))

    assert sorted(result["status"] for result in results) == [
        db.DOCGEN_REVISION_ALREADY_MATCHING,
        db.DOCGEN_REVISION_CREATED,
    ]
    assert len(collection.rows) == 1


def test_atomic_absent_same_revision_different_content_has_one_winner(monkeypatch):
    from core import database as db

    barrier = threading.Barrier(2)
    collection = FakeDocgenCollection(insert_barrier=barrier)
    _install_fake_docgen_db(monkeypatch, collection)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            db.create_or_observe_docgen_revision,
            [_gnt_metadata(output_hash="left"), _gnt_metadata(output_hash="right")],
        ))

    statuses = sorted(result["status"] for result in results)
    assert statuses == [db.DOCGEN_REVISION_COLLISION, db.DOCGEN_REVISION_CREATED]
    assert len(collection.rows) == 1
    stored = collection.rows[0]
    stored_hash = stored["output_hash"]
    assert stored_hash in {"left", "right"}
    created = next(result for result in results if result["status"] == db.DOCGEN_REVISION_CREATED)
    collision = next(result for result in results if result["status"] == db.DOCGEN_REVISION_COLLISION)
    assert created["record"]["output_hash"] == stored_hash
    assert collision["record"]["output_hash"] == stored_hash


def test_issued_revision_rejects_generated_observation_without_rewrite(monkeypatch):
    from core import database as db

    candidate = _gnt_metadata()
    existing = dict(candidate, _id="ordinary-object-id", status="ISSUED")
    collection = FakeDocgenCollection([existing])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["ok"] is False
    assert result["status"] == db.DOCGEN_REVISION_COLLISION
    assert result["collision"] is True
    assert "ISSUED" in result["error"]
    assert "GENERATED" in result["error"]
    assert len(collection.rows) == 1
    assert collection.rows[0]["status"] == "ISSUED"
    assert collection.rows[0]["output_hash"] == candidate["output_hash"]


def test_generated_revision_matches_generated_observation(monkeypatch):
    from core import database as db

    candidate = _gnt_metadata()
    collection = FakeDocgenCollection([dict(candidate, _id="ordinary-object-id")])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["ok"] is True
    assert result["status"] == db.DOCGEN_REVISION_ALREADY_MATCHING


def test_issued_revision_matches_issued_observation(monkeypatch):
    from core import database as db

    candidate = dict(_gnt_metadata(), status="ISSUED")
    collection = FakeDocgenCollection([dict(candidate, _id="ordinary-object-id")])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["ok"] is True
    assert result["status"] == db.DOCGEN_REVISION_ALREADY_MATCHING
    assert collection.rows[0]["status"] == "ISSUED"


def test_historical_object_id_record_is_detected_without_duplicate(monkeypatch):
    from core import database as db

    candidate = _gnt_metadata()
    collection = FakeDocgenCollection([dict(candidate, _id="507f1f77bcf86cd799439011")])
    _install_fake_docgen_db(monkeypatch, collection)

    result = db.create_or_observe_docgen_revision(candidate)

    assert result["status"] == db.DOCGEN_REVISION_ALREADY_MATCHING
    assert len(collection.rows) == 1
    assert collection.rows[0]["_id"] == "507f1f77bcf86cd799439011"


def test_gnt_handler_collision_preserves_attachment_and_skips_session_cache(ready_gnt, monkeypatch):
    upload = Mock(return_value=_attachment_outcome())
    persist = Mock(return_value={
        "ok": False,
        "collision": True,
        "error": "revision collision",
        "metadata_committed": False,
    })
    store = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    monkeypatch.setattr(vm, "_persist_generated_docgen_metadata", persist)
    monkeypatch.setattr(vm.logi_c1, "store_output", store)

    result = vm._handle_gnt_generate({"shipmentId": "SHP-143"})

    assert result["ok"] is False
    assert result["attachmentPersisted"] is True
    assert result["partialDurable"] is True
    store.assert_not_called()


# ===========================================================================
# Delivery-note durable generation (#156)
# ===========================================================================

def _delivery_note_shipment():
    row = copy.deepcopy(SHIPMENT)
    row["customer"] = "CÔNG TY 143"
    row["data"]["1.2"] = {
        "cargo_summary": {
            "goods_description": "Máy móc công nghiệp",
            "package_count": 2,
            "package_type": "Kiện",
            "gross_weight_kg": 500,
            "cbm": 3.5,
            "dimensions": "",
            "note": "",
        }
    }
    row["data"]["2.7"] = {
        "is_delivered": True,
        "delivered_at": "2026-09-30",
        "delivery_date": "2026-09-30",
        "delivery_location": "Kho khách hàng",
        "receiver_name": "Nguyễn Văn Nhận",
        "receiver_title": "Thủ kho",
        "phone_receiver": "0902000000",
    }
    return row


def test_delivery_note_revision_reads_durable_docgen_metadata(monkeypatch):
    monkeypatch.setattr(
        "core.database.load_docgen_documents",
        lambda shipment_id: {
            "DELIVERY_NOTE::SHP-143::R1": {
                "id": "DELIVERY_NOTE::SHP-143::R1",
                "document_id": "DELIVERY_NOTE::SHP-143",
                "document_type": "DELIVERY_NOTE",
                "shipment_id": "SHP-143",
                "revision": 1,
                "generation_revision": 1,
            },
            "DELIVERY_NOTE::SHP-143::R2": {
                "id": "DELIVERY_NOTE::SHP-143::R2",
                "document_id": "DELIVERY_NOTE::SHP-143",
                "document_type": "DELIVERY_NOTE",
                "shipment_id": "SHP-143",
                "revision": 2,
                "generation_revision": 2,
            },
        },
    )

    result = vm._next_delivery_note_revision("SHP-143")

    assert result == {
        "ok": True,
        "document_id": "DELIVERY_NOTE::SHP-143",
        "revision": 3,
    }


def test_delivery_note_handler_persists_attachment_and_metadata(monkeypatch):
    monkeypatch.setattr("core.auth.can_generate_documents", lambda: True)
    monkeypatch.setattr("core.auth.current_user", lambda: {"username": "writer-143"})
    monkeypatch.setattr(vm, "read_shipment", lambda shipment_id: _delivery_note_shipment())
    monkeypatch.setattr(
        "core.database.load_customers",
        lambda: {
            "CUS-143": {
                "customer_id": "CUS-143",
                "name": "CÔNG TY 143",
                "tax_code": "0101430143",
            }
        },
    )
    monkeypatch.setattr(
        vm,
        "_next_delivery_note_revision",
        lambda shipment_id: {
            "ok": True,
            "document_id": "DELIVERY_NOTE::SHP-143",
            "revision": 2,
        },
    )
    monkeypatch.setattr(
        "core.delivery_note.generate_delivery_note_xlsx",
        lambda *args, **kwargs: {
            "bytes": b"PK-delivery-note",
            "output_file_name": "PHIEU_GIAO_HANG_PGH-143.xlsx",
            "output_hash": "out-hash",
            "template_hash": "tpl-hash",
            "source_snapshot": {
                "delivery_note_no": "PGH-143",
                "delivery_note_date": "2026-09-30",
            },
            "source_reference": "shipment:SHP-143:data.2.7+cargo_summary",
        },
    )
    monkeypatch.setattr(vm.logi_c1, "_resolve_template_paths", lambda: ("/owner.xlsx", None))
    monkeypatch.setattr(vm, "_attachment_result_extras", lambda shipment_id: {})
    monkeypatch.setattr(vm, "_project_generated_attachment", lambda outcome: {"id": "ATT-DN-143"})
    upload = Mock(return_value={
        "ok": True,
        "duplicate": False,
        "record": {
            "id": "ATT-DN-143",
            "shipment_id": "SHP-143",
            "original_name": "PHIEU_GIAO_HANG_PGH-143.xlsx",
        },
    })
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    metadata = Mock(return_value={
        "ok": True,
        "already_present": False,
        "collision": False,
        "metadata_committed": True,
        "error": "",
        "record": {},
        "status": "CREATED",
    })
    monkeypatch.setattr(vm, "_persist_generated_docgen_metadata", metadata)
    store = Mock()
    monkeypatch.setattr(vm.logi_c1, "store_output", store)
    monkeypatch.setattr(vm, "_projection_for", lambda shipment: {"id": "SHP-143"})
    monkeypatch.setattr(vm, "_audit_trail", lambda shipment_id: [])

    result = vm._handle_delivery_note_generate({
        "shipmentId": "SHP-143",
        "deliveryNoteNo": "PGH-143",
        "deliveryNoteDate": "2026-09-30",
    })

    assert result["ok"] is True
    assert result["persisted"]["revision"] == 2
    assert result["persisted"]["attachmentId"] == "ATT-DN-143"
    assert result["persisted"]["isOfficeFile"] is True

    upload.assert_called_once()
    assert upload.call_args.kwargs["category"] == "other"
    assert upload.call_args.kwargs["shipment_id"] == "SHP-143"

    metadata.assert_called_once()
    saved = metadata.call_args.args[0]
    assert saved["document_id"] == "DELIVERY_NOTE::SHP-143"
    assert saved["document_type"] == "DELIVERY_NOTE"
    assert saved["revision"] == 2
    assert saved["source_snapshot"]["delivery_note_no"] == "PGH-143"

    store.assert_called_once()
    assert store.call_args.args[2]["document_type"] == "DELIVERY_NOTE"


def test_delivery_note_handler_fails_before_attachment_when_identity_missing(monkeypatch):
    monkeypatch.setattr("core.auth.can_generate_documents", lambda: True)
    monkeypatch.setattr(vm, "read_shipment", lambda shipment_id: _delivery_note_shipment())
    upload = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)

    result = vm._handle_delivery_note_generate({
        "shipmentId": "SHP-143",
        "deliveryNoteNo": "",
        "deliveryNoteDate": "",
    })

    assert result["ok"] is False
    assert result["gate"] == "MISSING_DOCUMENT_IDENTITY"
    upload.assert_not_called()


def test_delivery_note_attachment_failure_stops_before_metadata_and_session_success(monkeypatch):
    monkeypatch.setattr("core.auth.can_generate_documents", lambda: True)
    monkeypatch.setattr("core.auth.current_user", lambda: {"username": "writer-143"})
    monkeypatch.setattr(vm, "read_shipment", lambda shipment_id: _delivery_note_shipment())
    monkeypatch.setattr(
        "core.database.load_customers",
        lambda: {"CUS-143": {"customer_id": "CUS-143", "name": "CÔNG TY 143"}},
    )
    monkeypatch.setattr(
        vm,
        "_next_delivery_note_revision",
        lambda shipment_id: {
            "ok": True,
            "document_id": "DELIVERY_NOTE::SHP-143",
            "revision": 1,
        },
    )
    monkeypatch.setattr(
        "core.delivery_note.generate_delivery_note_xlsx",
        lambda *args, **kwargs: {
            "bytes": b"PK-delivery-note",
            "output_file_name": "PHIEU_GIAO_HANG_PGH-143.xlsx",
            "output_hash": "out-hash",
            "template_hash": "tpl-hash",
            "source_snapshot": {
                "delivery_note_no": "PGH-143",
                "delivery_note_date": "2026-09-30",
            },
            "source_reference": "shipment:SHP-143:data.2.7+cargo_summary",
        },
    )
    monkeypatch.setattr(vm.logi_c1, "_resolve_template_paths", lambda: ("/owner.xlsx", None))
    monkeypatch.setattr(vm, "_attachment_result_extras", lambda shipment_id: {})
    upload = Mock(return_value={"ok": False, "code": "STORE_FAILED", "error": "write failed"})
    metadata = Mock()
    store = Mock()
    monkeypatch.setattr("core.shipment_attachments.upload_attachment", upload)
    monkeypatch.setattr(vm, "_persist_generated_docgen_metadata", metadata)
    monkeypatch.setattr(vm.logi_c1, "store_output", store)

    result = vm._handle_delivery_note_generate({
        "shipmentId": "SHP-143",
        "deliveryNoteNo": "PGH-143",
        "deliveryNoteDate": "2026-09-30",
    })

    assert result["ok"] is False
    assert result["gate"] == "STORE_FAILED"
    assert result["attachmentPersisted"] is False
    metadata.assert_not_called()
    store.assert_not_called()
