#!/usr/bin/env python3
"""Generate the LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 DOM fixture.

The fixture is the REAL isolated staging view-model — never hand-written
browser data and never production. The byte store is the app's own bounded
GridFS adapter over mongomock (no Atlas, no live provider), so the review that
is baked into the fixture is produced by the REAL Run 3 orchestration:

    canonical attachment metadata
      → server-side byte read (core.shipment_attachments.fetch_attachment_bytes)
      → Run 2 located text (core.located_text_reader)
      → Run 1 cross-check (core.trade_document_crosscheck)
      → Run 3 bounded projection (core.shipment_document_review)

Attachments on the lot:

* the three real Run 2 trade fixtures (commercial_invoice.xlsx,
  packing_list.xlsx, bill_of_lading.pdf) — all review-selectable;
* one JPG and one DOCX so the UI has to render honest NON-selectable states
  ("Cần OCR — bước này chưa chạy OCR" / "Chưa hỗ trợ kiểm tra tự động ở bước
  này") without implying the files are damaged.

The full three-document review is then run through the real dispatcher and its
bounded session result is embedded as ``shipmentDocumentReview``, exactly as
``build_view_model()`` delivers it to the component.

Run:  .venv/bin/python scripts/gen_shipment_document_review_fixture.py
Out:  tests/component/fixtures/view_model_document_review.json
"""

from __future__ import annotations

import json
import pathlib
import sys

import mongomock
import mongomock.gridfs

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_document_review.json"
REAL_FILES = ROOT / "tests" / "fixtures" / "trade_canary_real_files"

SHIPMENT_ID = "LO-0306"
OTHER_SHIPMENT_ID = "LO-0307"
REQUEST_ID = "ATTREV-FIXTURE-RUN3"

#: (filename, mime, category, source bytes or inline generator)
TRADE_FIXTURES = ("commercial_invoice.xlsx", "packing_list.xlsx", "bill_of_lading.pdf")


def _mime_for(name: str) -> str:
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"


def _tiny_jpeg_bytes() -> bytes:
    """A real, valid, small JPEG so the honest "needs OCR" row is reachable."""

    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (240, 160), (226, 232, 240)).save(buffer, format="JPEG", quality=80)
    return buffer.getvalue()


def _tiny_docx_bytes() -> bytes:
    """A real, valid, minimal DOCX container (unsupported for this run)."""

    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/word/document.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/></Relationships>',
        )
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>SYNTHETIC — NOT A REAL SHIPMENT</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )
    return buffer.getvalue()


def main() -> None:
    mongomock.gridfs.enable_gridfs_integration()

    import streamlit as st

    from core.shipment_attachments import upload_attachment
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    # --- attachments on the lot under review ---------------------------------
    payload: dict[str, bytes] = {
        name: (REAL_FILES / name).read_bytes() for name in TRADE_FIXTURES
    }
    payload["To khai hai quan.jpg"] = _tiny_jpeg_bytes()
    payload["Hop dong van chuyen.docx"] = _tiny_docx_bytes()

    attachment_ids: dict[str, str] = {}
    for name, data in payload.items():
        category = "customs" if name.endswith((".xlsx", ".pdf")) else (
            "contract" if name.endswith(".docx") else "other"
        )
        outcome = upload_attachment(
            shipment_id=SHIPMENT_ID,
            category=category,
            file_name=name,
            mime=_mime_for(name),
            data=data,
            uploaded_by="staging.support",
            storage_backend="gridfs",
        )
        assert outcome.get("ok") and not outcome.get("duplicate"), outcome
        attachment_ids[name] = outcome["record"]["id"]

    # One attachment on ANOTHER lot: proves the cross-shipment guard has real
    # data to refuse, and that the fixture is not secretly single-shipment.
    foreign = upload_attachment(
        shipment_id=OTHER_SHIPMENT_ID,
        category="customs",
        file_name="lo-khac.pdf",
        mime="application/pdf",
        data=(REAL_FILES / "bill_of_lading.pdf").read_bytes(),
        uploaded_by="staging.support",
        storage_backend="gridfs",
    )
    assert foreign.get("ok"), foreign
    foreign_id = foreign["record"]["id"]

    # --- run the REAL review through the REAL dispatcher ---------------------
    selected = [attachment_ids[name] for name in TRADE_FIXTURES]
    outcome = vm._handle_shipment_document_review(
        {"shipmentId": SHIPMENT_ID, "attachmentIds": selected, "requestId": REQUEST_ID}
    )
    assert outcome.get("ok"), outcome
    review = outcome["review"]
    assert review["selectedCount"] == 3 and review["readableCount"] == 3, review
    assert len(review["facts"]) == 19, review["statusCounts"]
    assert review["statusCounts"] == {
        "CONFLICT": 1, "UNKNOWN": 1, "MISSING": 2, "SINGLE_SOURCE": 8, "SAME": 7,
    }, review["statusCounts"]
    assert review["storageByteReads"] == 3

    model = vm.build_view_model()
    row = next(item for item in model["shipments"] if item["id"] == SHIPMENT_ID)
    assert len(row["attachments"]) == 5, row["attachments"]
    selectable = [item for item in row["attachments"] if item["reviewSelectable"]]
    assert len(selectable) == 3, selectable
    notes = {item["name"]: item["reviewNote"] for item in row["attachments"] if not item["reviewSelectable"]}
    assert notes["To khai hai quan.jpg"] == "Cần OCR — bước này chưa chạy OCR", notes
    assert notes["Hop dong van chuyen.docx"] == "Chưa hỗ trợ kiểm tra tự động ở bước này", notes

    # The review the dispatcher stored in session state is what the UI receives.
    projected = model.get("shipmentDocumentReview")
    assert projected and projected["requestId"] == REQUEST_ID, projected
    assert projected["shipmentId"] == SHIPMENT_ID

    extra = {
        "fixture": {
            "task": "LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01",
            "shipmentId": SHIPMENT_ID,
            "otherShipmentId": OTHER_SHIPMENT_ID,
            "requestId": REQUEST_ID,
            "foreignAttachmentId": foreign_id,
            "attachmentIds": attachment_ids,
            "selectedIds": selected,
            "expectedFacts": len(review["facts"]),
            "expectedStatusCounts": review["statusCounts"],
        }
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({**model, "fixture": extra["fixture"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    print("attachments:", [(item["name"], item["reviewSelectable"]) for item in row["attachments"]])
    print("statusCounts:", review["statusCounts"])
    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
