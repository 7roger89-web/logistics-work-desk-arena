#!/usr/bin/env python3
"""Generate the LOGI-193 uploaded-template DOM acceptance fixture.

The payload is never hand-written: it is produced by the SAME staging stack the
app runs (logi_sandbox mongomock + GridFS, the real dispatcher, the real
persistence and the real bounded projections), exactly like
``scripts/gen_form07_dom_fixture.py`` does for Issue #168.

Sequence baked into the fixture:
  1. the seeded HDMB-0295 contract gains its canonical party + one goods line;
  2. an ADMIN uploads ONE ordinary DOCX and ONE ordinary XLSX through the real
     ``docgen_template_upload`` event (validation + detection + storage);
  3. the Admin confirms each detected mapping and publishes both through the
     real ``docgen_template_mapping_save`` / ``docgen_template_publish`` events;
  4. a SUPPORT actor selects both through the EXISTING
     ``shipment_document_selection_save`` event on delivered LO-0295;
  5. ``uploaded_template_generate`` renders + stores one revision of each
     through the real non-destructive pipeline (durable attachment + immutable
     docgen metadata);
  6. the full ``build_view_model()`` output plus the real picker policy are
     dumped, so the DOM test renders the ACTUAL component bundle against REAL
     server projections.

Run:  python3 scripts/gen_logi193_dom_fixture.py --fixture /tmp/logi193-dom.json
Then: node tests/component/dom_acceptance_logi193_uploaded_templates.mjs /tmp/logi193-dom.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="/tmp/logi193-dom.json")
    args = parser.parse_args()

    import streamlit as st

    from core import database
    from core.shipment_attachments import fetch_attachment_bytes
    from tests.test_logi_193_uploaded_office_templates import (
        SHIPMENT_ID,
        _dispatch_generate,
        _dispatch_template,
        _prepare_source_contract,
        _support,
        build_pilot_docx,
        build_pilot_xlsx,
    )
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = {"username": "staging.admin", "full_name": "Admin (Preview)",
                                        "role": "ADMIN", "user_id": "STAGING-ADMIN"}
    _prepare_source_contract()

    published = {}
    generated = {}
    for key, raw, name in (
        ("docx", build_pilot_docx(), "BB ĐỐI CHIẾU GIAO NHẬN.docx"),
        ("xlsx", build_pilot_xlsx(), "BẢNG KÊ LÔ HÀNG.xlsx"),
    ):
        uploaded = _dispatch_template("docgen_template_upload", {
            "label": pathlib.Path(name).stem,
            "fileName": name,
            "base64": base64.b64encode(raw).decode("ascii"),
            "requestId": f"193-DOM-UP-{key}",
        }, seq=1)
        assert uploaded["ok"], uploaded
        template_id = uploaded["readback"]["id"]
        detected = uploaded["readback"]["detected"]

        mapping = [
            {"position": item["id"], "mode": "field", "value": item["suggestion"]}
            for item in detected
            if item["suggestion"]
        ]
        saved = _dispatch_template("docgen_template_mapping_save", {
            "templateId": template_id, "mapping": mapping, "requestId": f"193-DOM-MAP-{key}",
        }, seq=2)
        assert saved["ok"], saved

        released = _dispatch_template("docgen_template_publish", {
            "templateId": template_id, "requestId": f"193-DOM-PUB-{key}",
        }, seq=3)
        assert released["ok"], released
        published[key] = {"row": released["readback"], "detectedCount": len(detected),
                          "mappingCount": len(mapping)}

    # A SUPPORT actor now uses both through the EXISTING picker event.
    _support()
    template_ids = [published["docx"]["row"]["id"], published["xlsx"]["row"]["id"]]
    fresh = vm.read_shipment(SHIPMENT_ID)
    saved = vm._handle_shipment_document_selection_save({
        "shipmentId": SHIPMENT_ID,
        "requestId": "193-DOM-SELECT",
        "expectedVersion": int(fresh.get("version") or 0),
        "selectedTemplateIds": template_ids,
    })
    assert saved["ok"], saved

    for key in ("docx", "xlsx"):
        outcome = _dispatch_generate({
            "shipmentId": SHIPMENT_ID, "templateId": published[key]["row"]["id"],
        }, seq=4 if key == "docx" else 5)
        assert outcome["ok"], outcome
        generated[key] = outcome

    # The FULL view model: what the component really receives.
    _admin_model_user()
    model = vm.build_view_model()
    picker = vm._shipment_document_picker_policy()
    workspace = vm.logi_templates.template_workspace_projection(include_detected=True)

    db = database.get_db()
    stored = {}
    for key in ("docx", "xlsx"):
        attachment_id = generated[key]["persisted"]["attachmentId"]
        record = database.load_shipment_attachment(attachment_id)
        outcome = fetch_attachment_bytes(record, shipment_id=SHIPMENT_ID)
        assert outcome["ok"], outcome
        raw = bytes(outcome["data"])
        assert raw[:2] == b"PK", "the stored bytes must be a real OOXML package"
        stored[key] = {
            "attachmentId": attachment_id,
            "fileName": generated[key]["persisted"]["fileName"],
            "revision": generated[key]["persisted"]["revision"],
            "templateId": published[key]["row"]["id"],
            "templateVersion": generated[key]["persisted"]["templateVersion"],
            "outputHash": generated[key]["persisted"]["outputHash"],
            "bytesSha256": hashlib.sha256(raw).hexdigest(),
            "bytesBase64": base64.b64encode(raw).decode("ascii"),
        }
        assert stored[key]["bytesSha256"] == stored[key]["outputHash"]

    payload = {
        "shipmentId": SHIPMENT_ID,
        "viewModel": model,
        "picker": picker,
        "workspace": workspace,
        "docgenDocuments": db["docgen_documents"].count_documents({}),
        "expected": {
            "templateIds": template_ids,
            "docx": stored["docx"],
            "xlsx": stored["xlsx"],
        },
    }
    out = pathlib.Path(args.fixture)
    out.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    print(
        f"Wrote LOGI-193 DOM fixture: {out}\n"
        f"  shipment {SHIPMENT_ID}\n"
        f"  DOCX template {published['docx']['row']['id']} "
        f"({published['docx']['detectedCount']} detected / "
        f"{published['docx']['mappingCount']} mapped) -> {stored['docx']['fileName']}\n"
        f"  XLSX template {published['xlsx']['row']['id']} "
        f"({published['xlsx']['detectedCount']} detected / "
        f"{published['xlsx']['mappingCount']} mapped) -> {stored['xlsx']['fileName']}\n"
        f"  sha256 docx={stored['docx']['bytesSha256'][:16]}… "
        f"xlsx={stored['xlsx']['bytesSha256'][:16]}…"
    )
    logi_sandbox.reset_backend()
    return 0


def _admin_model_user() -> None:
    import streamlit as st

    st.session_state["current_user"] = {"username": "staging.admin", "full_name": "Admin (Preview)",
                                        "role": "ADMIN", "user_id": "STAGING-ADMIN"}


if __name__ == "__main__":
    raise SystemExit(main())
