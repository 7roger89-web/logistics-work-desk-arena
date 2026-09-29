"""Focused Issue #143 evidence for durable generated PXK/GNT files.

These tests keep the generator and attachment service seams injectable. They do
not require production Mongo, Google Drive, OAuth, or secrets.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from views import logi_c1
from views import logi_view_model as vm


SHIPMENT = {
    "id": "SHP-143",
    "customer_id": "CUS-143",
    "data": {"2.4": {}},
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


@pytest.fixture()
def ready_gnt(monkeypatch):
    """Patch only the business/generator seams; storage remains observable."""
    monkeypatch.setattr("core.auth.can_generate_documents", lambda: True)
    monkeypatch.setattr("core.auth.current_user", lambda: {"username": "writer-143"})
    monkeypatch.setattr(vm, "read_shipment", lambda shipment_id: dict(SHIPMENT))
    monkeypatch.setattr("core.database.load_customers", lambda: {})
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


def test_docgen_revision_collision_fails_before_overwrite(monkeypatch):
    existing = {
        "id": "GNT::SHP-143::R1",
        "document_id": "GNT::SHP-143",
        "document_type": "GNT",
        "shipment_id": "SHP-143",
        "revision": 1,
        "generation_revision": 1,
        "output_file_name": "GNT_SHP-143_TK-143.xlsx",
        "output_hash": "old-hash",
    }
    candidate = dict(existing)
    candidate["output_hash"] = "new-hash"
    save = Mock()
    monkeypatch.setattr("core.database.load_docgen_document", lambda record_id: existing)
    monkeypatch.setattr("core.database.save_docgen_document", save)

    result = vm._persist_generated_docgen_metadata(candidate)

    assert result["ok"] is False
    assert result["collision"] is True
    save.assert_not_called()
