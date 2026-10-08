#!/usr/bin/env python3
"""Generate the Issue #168 FORM_07 DOM acceptance fixture — REAL staging data.

The payload is never hand-written: it is produced by the same staging stack the
app runs (logi_sandbox mongomock + GridFS, the real dispatcher, the real
persistence and the real bounded projections), exactly like
``scripts/gen_shipment_document_review_fixture.py`` does for Run 3.

Sequence baked into the fixture:
  1. the seeded HDMB-0295 contract gains its canonical parties + goods lines;
  2. ``shipment_document_selection_save`` selects FORM_07 on delivered LO-0295;
  3. ``form07_generate`` renders + stores revision R1 through the REAL
     core.docgen.form07 pipeline (durable attachment + immutable history);
  4. ``shipment_projection`` re-reads everything and the resulting shipment
     row (with ``form07``) plus the real picker policy are dumped.

Run:  python3 scripts/gen_form07_dom_fixture.py --fixture /tmp/form07-dom.json
Then: node tests/component/dom_acceptance_form07_delivery_receipt.mjs /tmp/form07-dom.json
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
    parser.add_argument("--fixture", default="/tmp/form07-dom.json")
    args = parser.parse_args()

    import streamlit as st

    from core import database
    from core.shipment_attachments import fetch_attachment_bytes
    from tests.test_form07_delivery_receipt import (
        CONTRACT_ID,
        MANUAL,
        SHIPMENT_ID,
        _dispatch,
        _prepare_source_contract,
    )
    from views import logi_real_data as rd
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    _prepare_source_contract()

    fresh = vm.read_shipment(SHIPMENT_ID)
    saved = _dispatch("shipment_document_selection_save", {
        "shipmentId": SHIPMENT_ID,
        "requestId": "F07-DOM-SAVE-1",
        "expectedVersion": int(fresh.get("version") or 0),
        "selectedTemplateIds": ["FORM_07"],
    })
    assert saved["ok"], saved

    generated = _dispatch("form07_generate", {
        "shipmentId": SHIPMENT_ID,
        "form07No": MANUAL["form07_no"],
        "orderDate": MANUAL["order_date"],
    })
    assert generated["ok"], generated

    fresh = vm.read_shipment(SHIPMENT_ID)
    db = database.get_db()
    contracts = {CONTRACT_ID: dict(db["contracts"].find_one({"id": CONTRACT_ID}, {"_id": 0}))}
    docs = rd.docgen_documents_by_shipment(
        {row["id"]: dict(row) for row in db["docgen_documents"].find({}, {"_id": 0})}
    )
    attachments: dict[str, list[dict]] = {}
    for attachment in db["shipment_attachments"].find({}, {"_id": 0}):
        attachments.setdefault(str(attachment.get("shipment_id") or ""), []).append(dict(attachment))
    row = rd.shipment_projection(
        fresh,
        contracts=contracts,
        docgen_documents=docs,
        attachments=attachments,
    )

    form07 = row.get("form07") or {}
    document = form07.get("document") or {}
    attachment_id = document.get("attachmentId") or ""
    assert attachment_id, "R1 must be stored through the durable attachment path"
    outcome = fetch_attachment_bytes({"id": attachment_id}, shipment_id=SHIPMENT_ID)
    assert outcome["ok"], outcome
    stored = bytes(outcome["data"])
    assert stored[:2] == b"PK", "the stored R1 bytes must be a real DOCX package"

    picker = vm._shipment_document_picker_policy()

    payload = {
        "shipmentId": SHIPMENT_ID,
        "shipment": row,
        "picker": picker,
        "expected": {
            "attachmentId": attachment_id,
            "fileName": document.get("fileName"),
            "revision": document.get("revision"),
            "form07No": MANUAL["form07_no"],
            "orderDate": MANUAL["order_date"],
            "bytesSha256": hashlib.sha256(stored).hexdigest(),
            "bytesBase64": base64.b64encode(stored).decode("ascii"),
        },
    }
    out = pathlib.Path(args.fixture)
    out.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    print(
        f"Wrote FORM_07 DOM fixture: {out} (shipment {SHIPMENT_ID}, "
        f"readiness {form07.get('readiness', {}).get('state')}, "
        f"R{document.get('revision')} {document.get('fileName')}, "
        f"sha256 {payload['expected']['bytesSha256'][:16]}…)"
    )
    logi_sandbox.reset_backend()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
