"""Bounded Shipment Document Picker V1 catalog and persistence acceptance."""

from __future__ import annotations

import pytest

from core import database
from core.shipment_document_catalog import (
    SHIPMENT_DOCUMENT_CATALOG,
    SelectionValidationError,
    ShipmentDocumentTemplate,
    project_catalog,
    project_selected_template_ids,
    validate_selected_template_ids,
)
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT_ID = "LO-0308"


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    yield
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _available_policy(*_args, **_kwargs):
    return {
        "catalog": project_catalog(
            contract_templates_available=True,
            pxk_template_available=True,
            storage_configured=True,
        ),
        "canSaveSelection": True,
        "canGenerate": True,
        "storageConfigured": True,
    }


def _dispatch(name: str, payload: dict, seq: int = 1) -> dict:
    outcomes = vm.consume_phase_b_triggers(
        {"seq": seq - 1},
        {name: {"seq": seq, "event": name, "payload": payload}},
    )
    assert len(outcomes) == 1
    return outcomes[0]


def test_catalog_is_small_stable_and_fail_closed():
    # Issue #168 adds exactly ONE Owner-sample pilot (FORM_07) to the V1 set;
    # the remaining six samples stay out until their own evidence-driven slices.
    assert [row.id for row in SHIPMENT_DOCUMENT_CATALOG] == ["HDNT", "PL", "HDMB", "PXK", "GNT", "FORM_07"]
    assert {row.adapter for row in SHIPMENT_DOCUMENT_CATALOG} == {
        "CONTRACT_DOCGEN", "PXK_DOCGEN", "GNT_BUILDER", "FORM07_DOCGEN"
    }
    assert validate_selected_template_ids(["GNT", "HDMB"]) == ["HDMB", "GNT"]
    assert project_selected_template_ids(["PXK", "NOT-IN-CATALOG", "HDNT", 7]) == ["HDNT", "PXK"]

    inactive = ShipmentDocumentTemplate("OLD", "Old", "", "UNKNOWN_ADAPTER", "OLD", active=False)
    with pytest.raises(SelectionValidationError, match="không có trong danh mục"):
        validate_selected_template_ids(["NOT-IN-CATALOG"])
    with pytest.raises(SelectionValidationError, match="bị chọn lặp"):
        validate_selected_template_ids(["PXK", "PXK"])
    with pytest.raises(SelectionValidationError, match="không hoạt động"):
        validate_selected_template_ids(["OLD"], catalog=(*SHIPMENT_DOCUMENT_CATALOG, inactive))


def test_catalog_availability_is_server_projected_and_unknown_adapter_stays_closed():
    extra = ShipmentDocumentTemplate("NEXT", "Next", "", "UNSUPPORTED", "NEXT")
    rows = project_catalog(
        contract_templates_available=False,
        pxk_template_available=True,
        storage_configured=False,
        catalog=(*SHIPMENT_DOCUMENT_CATALOG, extra),
    )
    by_id = {row["id"]: row for row in rows}
    assert by_id["HDNT"]["available"] is False
    assert by_id["PXK"]["available"] is False
    assert by_id["GNT"]["available"] is False
    assert by_id["NEXT"]["active"] is True
    assert by_id["NEXT"]["available"] is False
    assert by_id["NEXT"]["availabilityReason"]

    contract_without_attachment_storage = project_catalog(
        contract_templates_available=True,
        pxk_template_available=True,
        storage_configured=False,
    )[0]
    assert contract_without_attachment_storage["available"] is True
    assert by_id["PXK"]["available"] is False


def test_selection_save_readback_and_unselect_preserve_generated_history(staging, monkeypatch):
    monkeypatch.setattr(vm, "_shipment_document_picker_policy", _available_policy)
    shipment = vm.read_shipment(SHIPMENT_ID)
    assert shipment is not None
    version = int(shipment.get("version") or 0)

    # Existing generated output is independent history, not part of the
    # selection field; deselecting PXK must leave this canonical row untouched.
    db = database.get_db()
    history = {
        "_id": f"{SHIPMENT_ID}-PXK::R1",
        "id": f"{SHIPMENT_ID}-PXK::R1",
        "document_id": f"{SHIPMENT_ID}-PXK",
        "shipment_id": SHIPMENT_ID,
        "document_type": "PXK",
        "generation_revision": 1,
        "status": "GENERATED",
        "file_name": "PXK_LO-0308_R1.xlsx",
        "output_hash": "fixture-output-hash",
    }
    db["docgen_documents"].insert_one(dict(history))
    before_collections = set(db.list_collection_names())

    saved = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "SDOC-SAVE-1",
        "expectedVersion": version,
        "selectedTemplateIds": ["PXK", "HDNT"],
    })
    assert saved["ok"], saved
    assert saved["gate"] == "SAVED"
    assert saved["readback"]["selectedDocumentTemplateIds"] == ["HDNT", "PXK"]
    fresh = vm.read_shipment(SHIPMENT_ID)
    assert fresh is not None
    assert fresh["document_template_ids"] == ["HDNT", "PXK"]
    assert int(fresh.get("version") or 0) > version
    assert db["docgen_documents"].find_one({"id": history["id"]}, {"_id": 0})["output_hash"] == "fixture-output-hash"

    deselect = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "SDOC-SAVE-2",
        "expectedVersion": int(fresh.get("version") or 0),
        "selectedTemplateIds": ["HDNT"],
    }, seq=2)
    assert deselect["ok"], deselect
    latest = vm.read_shipment(SHIPMENT_ID)
    assert latest is not None
    assert latest["document_template_ids"] == ["HDNT"]
    assert db["docgen_documents"].find_one({"id": history["id"]}, {"_id": 0})["output_hash"] == "fixture-output-hash"
    assert set(db.list_collection_names()) == before_collections | {"audit_logs"}
    assert "shipment_document_selections" not in db.list_collection_names()


def test_selection_rejects_unknown_unavailable_and_stale_version_without_mutation(staging, monkeypatch):
    monkeypatch.setattr(vm, "_shipment_document_picker_policy", _available_policy)
    shipment = vm.read_shipment(SHIPMENT_ID)
    assert shipment is not None
    original_ids = shipment.get("document_template_ids")
    version = int(shipment.get("version") or 0)

    unknown = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "SDOC-UNKNOWN",
        "expectedVersion": version,
        "selectedTemplateIds": ["FAKE"],
    })
    assert not unknown["ok"]
    assert unknown["gate"] == "UNKNOWN_TEMPLATE"

    def pxk_unavailable(*_args, **_kwargs):
        policy = _available_policy()
        for row in policy["catalog"]:
            if row["id"] == "PXK":
                row["available"] = False
                row["availabilityReason"] = "Mẫu PXK đang khóa trong test."
        return policy

    monkeypatch.setattr(vm, "_shipment_document_picker_policy", pxk_unavailable)
    unavailable = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "SDOC-UNAVAILABLE",
        "expectedVersion": version,
        "selectedTemplateIds": ["PXK"],
    }, seq=2)
    assert not unavailable["ok"]
    assert unavailable["gate"] == "DOCUMENT_ACTION_UNAVAILABLE"
    assert "đang khóa" in unavailable["error"]

    stale = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "SDOC-STALE",
        "expectedVersion": version + 1,
        "selectedTemplateIds": ["HDNT"],
    }, seq=3)
    assert not stale["ok"]
    assert stale["gate"] == "STALE_VERSION"

    fresh = vm.read_shipment(SHIPMENT_ID)
    assert fresh is not None
    assert fresh.get("document_template_ids") == original_ids
    assert int(fresh.get("version") or 0) == version


def test_read_projection_exposes_durable_ids_existing_gates_and_generated_history(staging):
    shipment = vm.read_shipment(SHIPMENT_ID)
    assert shipment is not None
    shipment["document_template_ids"] = ["PXK", "GNT", "HDNT"]
    record_id = f"{SHIPMENT_ID}-PXK::R1"
    generated = {
        "id": record_id,
        "document_id": f"{SHIPMENT_ID}-PXK",
        "shipment_id": SHIPMENT_ID,
        "document_type": "PXK",
        "generation_revision": 1,
        "status": "GENERATED",
        "output_file_name": "PXK_LO-0308_R1.xlsx",
        "output_hash": "fixture-output-hash",
    }
    projection = rd.shipment_projection(
        shipment,
        docgen_documents={SHIPMENT_ID: {record_id: generated}},
        linked_contracts={SHIPMENT_ID.upper(): {}},
        attachments={SHIPMENT_ID: []},
    )
    assert projection["selectedDocumentTemplateIds"] == ["HDNT", "PXK", "GNT"]
    assert projection["importInfo"]["gnt"]["readiness"]["state"] == "MISSING_INFO"
    assert projection["pxk"]["readiness"]["state"] == "MISSING_INFO"
    if not bool((shipment.get("data", {}).get("2.7") or {}).get("is_delivered")):
        assert projection["pxk"]["missingDeliveryFacts"] == []
    assert projection["pxk"]["documentHistory"][0]["recordId"] == record_id
    assert projection["pxk"]["documentHistory"][0]["fileName"] == "PXK_LO-0308_R1.xlsx"


def test_selection_writer_and_single_handler_are_registered():
    assert vm.PHASE_B_EVENTS == set(vm._HANDLERS)
    assert vm._HANDLERS["shipment_document_selection_save"] is vm._handle_shipment_document_selection_save
