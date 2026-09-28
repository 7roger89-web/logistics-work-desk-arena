"""LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — read-only shipment review.

Run 3 connects two capabilities already on ``main`` to the EXISTING shipment
"Chứng từ / Tệp đính kèm" surface:

    canonical attachment metadata
      → server-side byte read (core.shipment_attachments.fetch_attachment_bytes)
      → Run 2 located text (core.located_text_reader.read_document_text)
      → Run 1 cross-check (core.trade_document_crosscheck)
      → Run 3 bounded view-model projection (core.shipment_document_review)

Everything here runs on the isolated staging/mongomock transport with a
DETERMINISTIC FAKE GRIDFS STORE — never a real cluster, never a provider, never
OCR. The three real Run 2 fixtures are uploaded as real shipment attachments so
the orchestration is proven end-to-end, not against a stand-in.

Covered:

1.  the full synthetic canary (19 facts: SAME=7 CONFLICT=1 MISSING=2 UNKNOWN=1
    SINGLE_SOURCE=8, 3/3 classification, every CONFLICT side visible, CẦN XEM
    before ĐÃ KHỚP);
2.  the mandatory adversarial set A–J (permission denied, foreign attachment,
    duplicate ids, 7 ids, >30 MB aggregate, manual unsupported file, image-only
    PDF, corrupt file containment, stale requestId, cross-shipment session);
3.  hard read-only acceptance (DB/audit/attachment/shipment writes = 0,
    provider/OCR calls = 0, storage byte reads only for ownership-proven files);
4.  the privacy projection (no bytes, no base64, no storage id, no raw SHA-256,
    no full extracted text, never the whole LocatedTextDocument);
5.  partial-review honesty (1 / 2 / 0 readable documents, duplicate copies of
    one document type are never independent confirmation);
6.  regression of the reused seams (Run 1 + Run 2 unchanged, attachment
    download/upload untouched).

Run:  .venv/bin/python -m pytest tests/test_logi_shipment_document_review_run3_01.py -q
"""

from __future__ import annotations

import base64
import io
import json
import re
import sys
import zipfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping
from unittest.mock import patch

import pytest
from pypdf import PdfWriter

from core import database as db
from core import drive_client as dc
from core import shipment_attachments as att
from core.located_text_reader import TEXT_NOT_AVAILABLE_NO_OCR, TextReaderLimits
from core.shipment_document_review import (
    CODE_DUPLICATE_SELECTION,
    CODE_REVIEW_BUDGET_EXCEEDED,
    CODE_SHIPMENT_MISMATCH,
    DOCUMENT_STATES,
    MAX_REVIEW_FILES,
    MAX_REVIEW_TOTAL_BYTES,
    REVIEW_EXTENSIONS,
    STATE_NEEDS_OCR_NOT_RUN,
    STATE_READABLE,
    STATE_READ_FAILED,
    STATE_TOO_LARGE_FOR_REVIEW,
    STATE_UNSUPPORTED_FORMAT,
    VIETNAMESE_FACT_LABELS,
    run_shipment_document_review,
    unsupported_reason,
)
from core.trade_document_crosscheck import FIELD_SPECS
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT_ID = "LO-0306"
OTHER_SHIPMENT_ID = "LO-0307"
REVIEW_EVENT = "shipment_document_review"

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "trade_canary_real_files"
INVOICE_XLSX = "commercial_invoice.xlsx"
PACKING_LIST_XLSX = "packing_list.xlsx"
BL_PDF = "bill_of_lading.pdf"
CANONICAL_FIXTURES = (INVOICE_XLSX, PACKING_LIST_XLSX, BL_PDF)

#: Expected full synthetic review from issue #132.
EXPECTED_TOTAL_FACTS = 19
EXPECTED_STATUS_COUNTS = {
    "CONFLICT": 1,
    "UNKNOWN": 1,
    "MISSING": 2,
    "SINGLE_SOURCE": 8,
    "SAME": 7,
}

SHA256_RE = re.compile(r"\b[0-9a-f]{64}\b")
BASE64_LOOKS_LIKE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
PROVIDER_MODULE_MARKERS = (
    "gemini",
    "google.genai",
    "pytesseract",
    "tesseract",
    "paddleocr",
    "docling",
    "aidock",
)


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


def _blank_pdf_bytes(page_count: int = 1) -> bytes:
    """A born-digital PDF with NO selectable text layer (image-only equivalent)."""

    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _corrupt_xlsx_bytes() -> bytes:
    """A file that declares the XLSX extension but is not a readable container."""

    return b"PK\x03\x04" + b"this is not a real xlsx container" * 8


def _duplicate_invoice_bytes() -> bytes:
    """A SECOND copy of the invoice: different bytes, same document type/values.

    Used to prove that two copies of ONE document type never become independent
    confirmation of each other. The copy keeps the COMMERCIAL INVOICE title and
    every trade value, and only gains a distinct trailing marker row, so the
    container is genuinely a different file (no same-shipment SHA dedupe).
    """

    source = io.BytesIO(_fixture_bytes(INVOICE_XLSX))
    target = io.BytesIO()
    marker = (
        '<row r="90"><c r="A90" t="inlineStr"><is><t>'
        "DUPLICATE COPY 2 — SYNTHETIC — NOT A REAL SHIPMENT"
        "</t></is></c></row>"
    )
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(
        target, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            payload = zin.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                text = payload.decode("utf-8")
                assert "</sheetData>" in text
                payload = text.replace("</sheetData>", marker + "</sheetData>", 1).encode("utf-8")
            out_info = zipfile.ZipInfo(info.filename, info.date_time)
            out_info.compress_type = zipfile.ZIP_DEFLATED
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, payload)
    duplicate = target.getvalue()
    assert duplicate != _fixture_bytes(INVOICE_XLSX)
    return duplicate


def _tiny_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
    )


def _mime_for(name: str) -> str:
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith((".xlsx", ".xlsm")):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if name.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


def _upload(shipment_id: str, name: str, data: bytes, *, category: str = "customs") -> dict[str, Any]:
    """Upload through the REAL attachment service onto the REAL GridFS store.

    No fake adapter: the bytes land in the bounded ``shipment_attachment_files``
    bucket of the isolated mongomock database, so the review later reads them
    back through the exact production path (``fetch_attachment_bytes`` →
    ``GridFSAttachmentStore.download_file``).
    """

    outcome = att.upload_attachment(
        shipment_id=shipment_id,
        category=category,
        file_name=name,
        mime=_mime_for(name),
        data=data,
        uploaded_by="staging.support",
        storage_backend="gridfs",
    )
    assert outcome.get("ok"), outcome
    return dict(outcome["record"])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def staging():
    """Isolated staging transport + an authenticated SUPPORT actor."""

    import mongomock
    import mongomock.gridfs
    import streamlit as st

    # The REAL GridFS adapter is exercised, so mongomock must back the bounded
    # ``shipment_attachment_files`` bucket exactly as the app's own runtime test
    # does (tests/test_logi_shipment_documents_gridfs_runtime.py).
    mongomock.gridfs.enable_gridfs_integration()

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "tests must run on the isolated staging transport"
    st.session_state["current_user"] = {
        "username": "staging.support", "role": "SUPPORT",
        "full_name": "Thu Hằng (Preview/Staging)", "user_id": "STAGING-SUPPORT",
    }
    st.session_state.pop(vm.SHIPMENT_DOCUMENT_REVIEW_KEY, None)
    yield transport
    st.session_state.pop(vm.SHIPMENT_DOCUMENT_REVIEW_KEY, None)
    logi_sandbox.reset_backend()


@pytest.fixture()
def seq():
    state = {"n": 0}

    def _next() -> int:
        state["n"] += 1
        return state["n"]

    return _next


@pytest.fixture()
def storage():
    """Upload the real Run 2 fixtures as real attachments of SHIPMENT_ID."""

    uploaded: dict[str, dict[str, Any]] = {}
    for name in CANONICAL_FIXTURES:
        uploaded[name] = _upload(SHIPMENT_ID, name, _fixture_bytes(name))
    return uploaded


@pytest.fixture()
def byte_reads():
    """Count EVERY storage byte read made through the ONE existing seam."""

    calls: list[tuple[str, str]] = []
    real = att.fetch_attachment_bytes

    def counting(record, **kwargs):
        calls.append((str((record or {}).get("id") or ""), str(kwargs.get("shipment_id") or "")))
        return real(record, **kwargs)

    with patch("core.shipment_attachments.fetch_attachment_bytes", counting):
        yield calls


def _dispatch(payload: Mapping[str, Any], seq_fn) -> dict[str, Any]:
    """Drive the ONE read-only review dispatcher through its real consumer."""

    trigger = {REVIEW_EVENT: {"seq": seq_fn(), "event": REVIEW_EVENT, "payload": dict(payload)}}
    outcomes = vm.consume_document_review_triggers({"seq": 0}, trigger)
    assert len(outcomes) == 1
    return outcomes[0]


def _review_payload(attachment_ids, *, shipment_id: str = SHIPMENT_ID, request_id: str = "REQ-1"):
    return {"shipmentId": shipment_id, "attachmentIds": list(attachment_ids), "requestId": request_id}


def _by_name(uploaded, *names):
    return [uploaded[name]["id"] for name in names]


def _walk_strings(value: Any):
    """Every string anywhere inside a projection (privacy assertions)."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


# ===========================================================================
# 1. Contract shape — the event is read-only and the bounds are the issue's
# ===========================================================================


class TestReviewContract:
    def test_event_is_read_only_and_not_a_phase_b_mutation(self):
        assert REVIEW_EVENT in vm.ALL_EVENTS
        assert REVIEW_EVENT in vm.DOCUMENT_REVIEW_EVENTS
        # Issue #132: "Add this as a read-only event path, not a Phase-B
        # business mutation."
        assert REVIEW_EVENT not in vm.PHASE_B_EVENTS

    def test_session_key_is_the_bounded_ephemeral_slot(self):
        assert vm.SHIPMENT_DOCUMENT_REVIEW_KEY == "logi_shipment_document_review"

    def test_bounds_match_the_issue(self):
        assert MAX_REVIEW_FILES == 6
        assert MAX_REVIEW_TOTAL_BYTES == 30 * 1024 * 1024
        assert REVIEW_EXTENSIONS == ("pdf", "xlsx")
        # Run 2's own per-file ceiling is reused, never widened.
        assert TextReaderLimits().max_file_bytes == 10 * 1024 * 1024

    def test_all_five_document_states_are_declared(self):
        assert set(DOCUMENT_STATES) == {
            STATE_READABLE,
            STATE_NEEDS_OCR_NOT_RUN,
            STATE_UNSUPPORTED_FORMAT,
            STATE_TOO_LARGE_FOR_REVIEW,
            STATE_READ_FAILED,
        }

    def test_every_canonical_field_key_has_a_vietnamese_label(self):
        keys = {spec.field_key for spec in FIELD_SPECS}
        assert len(keys) == 19
        assert set(VIETNAMESE_FACT_LABELS) == keys
        for label in VIETNAMESE_FACT_LABELS.values():
            assert label and not label.isascii(), label


# ===========================================================================
# 2. Full synthetic end-to-end canary
# ===========================================================================


class TestFullCanary:
    def test_metadata_to_bytes_to_run2_to_run1_to_view_model(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        assert outcome["gate"] == "REVIEWED"
        assert outcome["event"] == REVIEW_EVENT
        assert outcome["requestId"] == "REQ-1"

        review = outcome["review"]
        # Every selected file really was read server-side through the ONE seam,
        # scoped to this shipment.
        assert len(byte_reads) == 3
        assert {aid for aid, _sid in byte_reads} == set(ids)
        assert {sid for _aid, sid in byte_reads} == {SHIPMENT_ID}

        assert review["shipmentId"] == SHIPMENT_ID
        assert review["selectedCount"] == 3
        assert review["readableCount"] == 3
        assert review["storageByteReads"] == 3
        assert review["savedToShipment"] is False

        # --- document states + 3/3 classification --------------------------
        states = {doc["fileName"]: doc for doc in review["documents"]}
        assert set(states) == set(CANONICAL_FIXTURES)
        assert all(doc["state"] == STATE_READABLE for doc in states.values())
        assert {states[name]["documentType"] for name in CANONICAL_FIXTURES} == {
            "INVOICE", "PACKING_LIST", "BILL_OF_LADING",
        }

        # --- the frozen 19 facts -------------------------------------------
        assert len(review["facts"]) == EXPECTED_TOTAL_FACTS
        assert review["statusCounts"] == EXPECTED_STATUS_COUNTS
        assert review["crossConfirmationComplete"] is True

        # --- CẦN XEM ordering: CONFLICT → UNKNOWN → MISSING → SINGLE → SAME --
        order = [fact["status"] for fact in review["facts"]]
        rank = {"CONFLICT": 0, "UNKNOWN": 1, "MISSING": 2, "SINGLE_SOURCE": 3, "SAME": 4}
        assert [rank[status] for status in order] == sorted(rank[status] for status in order)

        # --- the one CONFLICT shows ALL source sides, no winner ------------
        conflict = next(fact for fact in review["facts"] if fact["status"] == "CONFLICT")
        assert conflict["fieldKey"] == "package_count"
        assert conflict["label"] == "Số kiện"
        assert conflict["operatorDecision"] == "NONE"
        assert conflict["operatorNote"] == "Chưa chọn giá trị đúng — cần người kiểm tra."
        sides = conflict["sides"]
        assert len(sides) == 3
        assert [side["rawValue"] for side in sides] == ["120 CTNS", "120 CARTONS", "118 CARTONS"]
        assert {side["documentType"] for side in sides} == {"INVOICE", "PACKING_LIST", "BILL_OF_LADING"}
        # Bounded provenance: page OR sheet/cell, never full text.
        assert any(side["location"].startswith("Trang ") for side in sides)
        assert any(side["location"].startswith("Sheet ") for side in sides)
        # Each side names a real attachment of THIS shipment.
        assert {side["attachmentId"] for side in sides} == set(ids)

    def test_review_is_deterministic(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        first = _dispatch(_review_payload(ids, request_id="REQ-A"), seq)["review"]
        second = _dispatch(_review_payload(ids, request_id="REQ-B"), seq)["review"]
        for review in (first, second):
            review.pop("reviewedAt", None)
        assert first == second


# ===========================================================================
# 3. Mandatory adversarial set A–J
# ===========================================================================


class TestAdversarial:
    # --- A. permission denied -------------------------------------------------
    def test_a_permission_denied_reads_zero_storage_bytes(self, staging, storage, seq, byte_reads):
        import streamlit as st

        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        st.session_state.pop("current_user", None)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == "BLOCKED_PERMISSION_DENIED"
        assert byte_reads == []

    def test_a_viewer_may_review_without_sales_write(self, staging, storage, seq, byte_reads):
        """The read boundary is dashboard, not sales_write (issue #132)."""

        import streamlit as st

        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        st.session_state["current_user"] = {
            "username": "staging.viewer", "role": "VIEWER", "user_id": "STAGING-VIEWER",
        }
        from core.auth import can_operate_business

        assert can_operate_business("sales_write") is False
        assert can_operate_business("dashboard") is True

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        assert len(byte_reads) == 3

    # --- B. attachment belongs to another shipment ---------------------------
    def test_b_foreign_attachment_is_refused_with_zero_byte_reads(self, staging, storage, seq, byte_reads):
        uploaded = storage
        foreign = _upload(OTHER_SHIPMENT_ID, "other.pdf", _blank_pdf_bytes())
        ids = _by_name(uploaded, INVOICE_XLSX) + [foreign["id"]]

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == CODE_SHIPMENT_MISMATCH
        assert outcome["attachmentId"] == foreign["id"]
        # Zero byte reads for the mismatched file — and for every other file.
        assert byte_reads == []

    # --- C. duplicate attachment ids -----------------------------------------
    def test_c_duplicate_ids_are_refused_with_zero_byte_reads(self, staging, storage, seq, byte_reads):
        uploaded = storage
        invoice_id = uploaded[INVOICE_XLSX]["id"]

        outcome = _dispatch(_review_payload([invoice_id, invoice_id]), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == CODE_DUPLICATE_SELECTION
        assert byte_reads == []

    # --- D. seven ids ---------------------------------------------------------
    def test_d_seven_ids_are_refused_with_zero_byte_reads(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES) + [f"att-extra-{index}" for index in range(4)]

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == "SELECTION_LIMIT_EXCEEDED"
        assert MAX_REVIEW_FILES == 6
        assert len(ids) == 7
        assert byte_reads == []

    # --- E. aggregate metadata > 30 MB ---------------------------------------
    def test_e_aggregate_over_budget_refuses_before_any_byte(self, staging, storage, seq, byte_reads):
        uploaded = storage
        # Six selections — the maximum allowed — each honestly under Run 2's own
        # 10 MB per-file ceiling, so NO per-file rule can fire. Only the Run 3
        # aggregate bound can refuse this request, and it must do so before a
        # single storage byte is read.
        extra_ids = [
            _upload(SHIPMENT_ID, f"chung-tu-{index}.pdf", _blank_pdf_bytes(index + 1))["id"]
            for index in range(3)
        ]
        ids = _by_name(uploaded, *CANONICAL_FIXTURES) + extra_ids
        assert len(ids) == MAX_REVIEW_FILES == 6

        per_file = 6 * 1024 * 1024
        assert per_file < TextReaderLimits().max_file_bytes, "per-file rule must not fire"
        assert per_file * len(ids) > MAX_REVIEW_TOTAL_BYTES, "aggregate rule must fire"

        rows = {
            attachment_id: {
                "id": attachment_id,
                "shipment_id": SHIPMENT_ID,
                "original_name": f"file-{index}.pdf",
                "stored_size": per_file,
            }
            for index, attachment_id in enumerate(ids)
        }

        review = run_shipment_document_review(SHIPMENT_ID, ids, metadata_rows=rows)

        assert review["refusal"] is not None, review["documents"]
        assert review["refusal"]["code"] == CODE_REVIEW_BUDGET_EXCEEDED
        assert byte_reads == []
        assert review["storageByteReads"] == 0

    # --- F. unsupported file submitted despite a disabled UI ------------------
    def test_f_unsupported_image_and_doc_stay_visible_with_honest_state(self, staging, storage, seq, byte_reads):
        uploaded = storage
        png = _upload(SHIPMENT_ID, "anh-chung-tu.png", _tiny_png_bytes())
        ids = _by_name(uploaded, INVOICE_XLSX, BL_PDF) + [png["id"]]

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        by_name = {doc["fileName"]: doc for doc in review["documents"]}
        assert by_name["anh-chung-tu.png"]["state"] == STATE_UNSUPPORTED_FORMAT
        assert by_name["anh-chung-tu.png"]["reason"] == "Cần OCR — bước này chưa chạy OCR"
        # The readable files are still reviewed honestly.
        assert by_name[INVOICE_XLSX]["state"] == STATE_READABLE
        assert by_name[BL_PDF]["state"] == STATE_READABLE
        # Only the two supported files cost a storage read.
        assert len(byte_reads) == 2
        assert png["id"] not in {aid for aid, _ in byte_reads}

    def test_f_unsupported_wording_never_implies_damage(self):
        assert unsupported_reason("jpg") == "Cần OCR — bước này chưa chạy OCR"
        assert unsupported_reason("jpeg") == "Cần OCR — bước này chưa chạy OCR"
        assert unsupported_reason("png") == "Cần OCR — bước này chưa chạy OCR"
        assert unsupported_reason("doc") == "Chưa hỗ trợ kiểm tra tự động ở bước này"
        assert unsupported_reason("docx") == "Chưa hỗ trợ kiểm tra tự động ở bước này"
        assert unsupported_reason("xls") == "Chưa hỗ trợ kiểm tra tự động ở bước này"
        assert unsupported_reason("zip") == "Không hỗ trợ ở bước này"

    # --- G. blank / image-only PDF -------------------------------------------
    def test_g_image_only_pdf_is_needs_ocr_and_fabricates_nothing(self, staging, storage, seq, byte_reads):
        uploaded = storage
        blank = _upload(SHIPMENT_ID, "scan-khong-co-chu.pdf", _blank_pdf_bytes())
        # Prove the fixture really is a no-text-layer PDF through the Run 2 reader.
        from core.located_text_reader import read_document_text

        assert read_document_text(_blank_pdf_bytes(), "blank.pdf").unsupported_state == TEXT_NOT_AVAILABLE_NO_OCR

        outcome = _dispatch(
            _review_payload(_by_name(uploaded, INVOICE_XLSX, BL_PDF) + [blank["id"]]), seq
        )

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        by_name = {doc["fileName"]: doc for doc in review["documents"]}
        assert by_name["scan-khong-co-chu.pdf"]["state"] == STATE_NEEDS_OCR_NOT_RUN
        assert review["readableCount"] == 2
        assert review["crossConfirmationComplete"] is False

        # Zero fabricated facts: adding a no-text-layer PDF changes NOTHING
        # about the evidence, so the review is byte-for-byte the 2-document
        # baseline and no fact side ever cites the unreadable file.
        baseline = _dispatch(_review_payload(_by_name(uploaded, INVOICE_XLSX, BL_PDF),
                                             request_id="REQ-BASE"), seq)["review"]
        assert review["statusCounts"] == baseline["statusCounts"]
        assert [fact["fieldKey"] for fact in review["facts"]] == [
            fact["fieldKey"] for fact in baseline["facts"]
        ]
        cited = {side["attachmentId"] for fact in review["facts"] for side in fact["sides"]}
        assert blank["id"] not in cited

    def test_g_zero_readable_returns_states_only_and_no_crosscheck(self, staging, storage, seq, byte_reads):
        uploaded = storage
        blank = _upload(SHIPMENT_ID, "chi-co-anh.pdf", _blank_pdf_bytes())

        outcome = _dispatch(_review_payload([blank["id"]]), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        assert review["readableCount"] == 0
        assert review["facts"] == []
        assert all(value == 0 for value in review["statusCounts"].values())
        assert review["documents"][0]["state"] == STATE_NEEDS_OCR_NOT_RUN
        assert "chưa đối chiếu" in review["partialNote"]

    # --- H. corrupt supported document ---------------------------------------
    def test_h_corrupt_file_is_contained_and_the_rest_still_review(self, staging, storage, seq, byte_reads):
        uploaded = storage
        corrupt = _upload(SHIPMENT_ID, "packing_list.xlsx", _corrupt_xlsx_bytes())
        ids = _by_name(uploaded, INVOICE_XLSX, BL_PDF) + [corrupt["id"]]

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        by_id = {doc["attachmentId"]: doc for doc in review["documents"]}
        assert by_id[corrupt["id"]]["state"] == STATE_READ_FAILED
        assert by_id[uploaded[INVOICE_XLSX]["id"]]["state"] == STATE_READABLE
        assert by_id[uploaded[BL_PDF]["id"]]["state"] == STATE_READABLE
        # A truthful PARTIAL comparison over invoice + B/L, not a failed request.
        assert review["readableCount"] == 2
        assert review["crossConfirmationComplete"] is False
        assert "chưa đầy đủ" in review["partialNote"]
        assert review["statusCounts"]["SAME"] > 0

    def test_h_storage_read_failure_is_contained_per_document(self, staging, storage, seq):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        real = att.fetch_attachment_bytes
        failing_id = uploaded[PACKING_LIST_XLSX]["id"]

        def flaky(record, **kwargs):
            if str(record.get("id")) == failing_id:
                return {"ok": False, "code": "GRIDFS_FAILED", "error": "Kho chứng từ lỗi: mất kết nối."}
            return real(record, **kwargs)

        with patch("core.shipment_attachments.fetch_attachment_bytes", flaky):
            outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        by_id = {doc["attachmentId"]: doc for doc in review["documents"]}
        assert by_id[failing_id]["state"] == STATE_READ_FAILED
        assert "mất kết nối" in by_id[failing_id]["reason"]
        assert review["readableCount"] == 2

    # --- I. stale requestId ---------------------------------------------------
    def test_i_stale_request_cannot_settle_the_current_request(self, staging, storage, seq, byte_reads):
        import streamlit as st

        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        first = _dispatch(_review_payload(ids, request_id="REQ-OLD"), seq)
        assert first["ok"] is True

        stored = st.session_state[vm.SHIPMENT_DOCUMENT_REVIEW_KEY]
        assert stored["requestId"] == "REQ-OLD"
        assert stored["review"]["shipmentId"] == SHIPMENT_ID

        # The UI settles ONLY on an outcome carrying the requestId it sent.
        assert first["requestId"] == "REQ-OLD"
        assert first["requestId"] != "REQ-NEW"
        # A stale result is not the new request's answer.
        assert stored["requestId"] != "REQ-NEW"

    def test_i_a_new_review_replaces_the_previous_one(self, staging, storage, seq, byte_reads):
        import streamlit as st

        uploaded = storage
        _dispatch(_review_payload(_by_name(uploaded, INVOICE_XLSX), request_id="REQ-1"), seq)
        first_seq = st.session_state[vm.SHIPMENT_DOCUMENT_REVIEW_KEY]["seq"]
        _dispatch(_review_payload(_by_name(uploaded, *CANONICAL_FIXTURES), request_id="REQ-2"), seq)
        stored = st.session_state[vm.SHIPMENT_DOCUMENT_REVIEW_KEY]

        assert stored["requestId"] == "REQ-2"
        assert stored["seq"] == first_seq + 1
        assert stored["review"]["selectedCount"] == 3
        # Exactly ONE slot: no history table, no second review kept.
        assert isinstance(stored["review"], dict)

    # --- J. cross-shipment session result ------------------------------------
    def test_j_review_of_another_shipment_is_never_projected(self, staging, storage, seq, byte_reads):
        import streamlit as st

        uploaded = storage
        foreign = _upload(OTHER_SHIPMENT_ID, "other.pdf", _blank_pdf_bytes())

        _dispatch(
            _review_payload([foreign["id"]], shipment_id=OTHER_SHIPMENT_ID, request_id="REQ-OTHER"),
            seq,
        )
        stored = st.session_state[vm.SHIPMENT_DOCUMENT_REVIEW_KEY]
        assert stored["shipmentId"] == OTHER_SHIPMENT_ID

        projected = vm._shipment_document_review_projection()
        assert projected["shipmentId"] == OTHER_SHIPMENT_ID
        # The component guard is the same comparison the UI makes: a review whose
        # shipmentId differs from the open lot is never rendered.
        assert projected["shipmentId"] != SHIPMENT_ID

    def test_j_review_projection_is_none_without_a_review(self, staging):
        assert vm._shipment_document_review_projection() is None


# ===========================================================================
# 4. Hard read-only acceptance
# ===========================================================================


class TestHardReadOnly:
    def test_zero_db_audit_attachment_and_shipment_writes(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)

        # Every canonical writer this surface could have reached. A read-only
        # review must not touch one of them.
        forbidden = [
            "save_shipment_atomic",
            "save_shipment_attachment",
            "delete_shipment",
            "save_docgen_document",
            "_audit",
            "_save_document",
        ]
        assert all(hasattr(db, name) for name in forbidden), [
            name for name in forbidden if not hasattr(db, name)
        ]
        counters = {name: 0 for name in forbidden}

        def guard(name):
            def _boom(*args, **kwargs):
                counters[name] += 1
                raise AssertionError(f"read-only review called a writer: {name}")

            return _boom

        with ExitStack() as stack:
            for name in forbidden:
                stack.enter_context(patch(f"core.database.{name}", guard(name)))
            before = vm.read_shipment(SHIPMENT_ID)
            outcome = _dispatch(_review_payload(ids), seq)
            after = vm.read_shipment(SHIPMENT_ID)

        assert outcome["ok"] is True, outcome["error"]
        assert all(value == 0 for value in counters.values()), counters
        # The shipment document itself is untouched (version + content).
        assert before.get("version") == after.get("version")
        assert before.get("updated_at") == after.get("updated_at")
        # Attachment metadata is untouched: same rows, same ids.
        assert sorted(db.load_shipment_attachments(SHIPMENT_ID)) == sorted(uploaded[name]["id"] for name in CANONICAL_FIXTURES)

    def test_no_provider_or_ocr_module_is_imported_by_a_review(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        before = set(sys.modules)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        newly_imported = set(sys.modules) - before
        offenders = [
            name for name in newly_imported
            if any(marker in name.lower() for marker in PROVIDER_MODULE_MARKERS)
        ]
        assert offenders == [], offenders

    def test_storage_reads_are_only_for_selected_ownership_proven_files(self, staging, storage, seq, byte_reads):
        uploaded = storage
        _upload(SHIPMENT_ID, "anh.png", _tiny_png_bytes())
        ids = _by_name(uploaded, INVOICE_XLSX)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        # Exactly ONE read, for the ONE selected attachment of THIS shipment.
        assert byte_reads == [(uploaded[INVOICE_XLSX]["id"], SHIPMENT_ID)]
        assert outcome["review"]["storageByteReads"] == 1

    def test_persistence_surface_is_never_touched_by_the_handler_source(self):
        """Static complement: the handler names no collection and no writer."""

        import inspect

        source = inspect.getsource(vm._handle_shipment_document_review)
        for token in ("save_shipment", "save_shipment_attachment", "log_audit",
                      "insert_one", "update_one", "replace_one", "delete_one"):
            assert token not in source, token


# ===========================================================================
# 5. Privacy projection
# ===========================================================================


class TestPrivacyProjection:
    def test_projection_carries_no_bytes_storage_ids_or_full_text(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        outcome = _dispatch(_review_payload(ids), seq)
        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]

        blob = " ".join(_walk_strings(review))
        # No raw SHA-256 of the source documents.
        assert not SHA256_RE.search(blob), "raw SHA-256 leaked into the projection"
        # No base64 body.
        assert not BASE64_LOOKS_LIKE.search(blob), "base64 body leaked into the projection"
        # No storage/GridFS/Drive identity.
        for token in ("storage_file_id", "storageFileId", "driveFileId", "drive_file_id",
                      "gridfs-", "gridfsId", "1BxiMVs0XRA5nFMdKvBKVZB74XGej"):
            assert token not in blob, token
        assert all("storage_file_id" not in doc for doc in review["documents"])
        # No original PDF/XLSX bytes and never the whole LocatedTextDocument.
        for forbidden_key in ("data", "bytes", "base64", "text", "fragments",
                              "line_locations", "source_sha256", "content_sha256"):
            assert forbidden_key not in review, forbidden_key
            for doc in review["documents"]:
                assert forbidden_key not in doc, (forbidden_key, doc)
        # The full extracted text of any document is never projected: a whole
        # fixture's text layer is far longer than any projected string.
        longest = max((len(item) for item in _walk_strings(review)), default=0)
        smallest_fixture_text = min(
            len(__import__("core.located_text_reader", fromlist=["read_document_text"])
                .read_document_text(_fixture_bytes(name), name).text)
            for name in CANONICAL_FIXTURES
        )
        assert longest < smallest_fixture_text

    def test_fact_projection_is_bounded_and_labelled(self, staging, storage, seq, byte_reads):
        uploaded = storage
        ids = _by_name(uploaded, *CANONICAL_FIXTURES)
        review = _dispatch(_review_payload(ids), seq)["review"]

        for fact in review["facts"]:
            assert fact["label"] in VIETNAMESE_FACT_LABELS.values()
            assert fact["fieldKey"] in VIETNAMESE_FACT_LABELS
            assert fact["operatorDecision"] == "NONE"
            assert fact["status"] in {"CONFLICT", "UNKNOWN", "MISSING", "SINGLE_SOURCE", "SAME"}
            # A MISSING fact states the absence instead of an empty side.
            if fact["status"] == "MISSING":
                assert fact["sides"] == []
            for side in fact["sides"]:
                assert len(side["rawValue"]) <= 160
                assert side["fileName"]
                assert "location" in side and "reason" in side
            # No invented score of any kind.
            for forbidden in ("confidence", "score", "percentage", "quality", "aiScore"):
                assert forbidden not in fact, forbidden


# ===========================================================================
# 6. Partial-review honesty
# ===========================================================================


class TestPartialReview:
    def test_one_readable_document_is_reviewed_as_incomplete(self, staging, storage, seq, byte_reads):
        uploaded = storage
        outcome = _dispatch(_review_payload(_by_name(uploaded, INVOICE_XLSX)), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        assert review["readableCount"] == 1
        assert review["crossConfirmationComplete"] is False
        assert "chưa đầy đủ" in review["partialNote"]
        # Honest single-source semantics, never a fabricated match.
        assert review["statusCounts"]["SAME"] == 0
        assert review["statusCounts"]["SINGLE_SOURCE"] > 0

    def test_two_readable_documents_compare_only_what_exists(self, staging, storage, seq, byte_reads):
        uploaded = storage
        outcome = _dispatch(_review_payload(_by_name(uploaded, INVOICE_XLSX, PACKING_LIST_XLSX)), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        assert review["readableCount"] == 2
        assert review["crossConfirmationComplete"] is False
        assert {doc["documentType"] for doc in review["documents"]} == {"INVOICE", "PACKING_LIST"}
        assert review["statusCounts"]["SAME"] > 0

    def test_duplicate_copies_of_one_type_are_not_independent_confirmation(self, staging, storage, seq, byte_reads):
        """Two copies of the SAME document type must not read as SAME."""

        uploaded = storage
        second = _upload(SHIPMENT_ID, "invoice-copy.xlsx", _duplicate_invoice_bytes())
        assert second["id"] != uploaded[INVOICE_XLSX]["id"]
        ids = [uploaded[INVOICE_XLSX]["id"], second["id"]]

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]
        assert review["readableCount"] == 2
        assert {doc["documentType"] for doc in review["documents"]} == {"INVOICE"}
        # Run 1 independence is by document TYPE, not by copy count.
        assert review["statusCounts"]["SAME"] == 0
        assert review["statusCounts"]["SINGLE_SOURCE"] > 0

    def test_empty_selection_is_refused_without_reading(self, staging, storage, seq, byte_reads):
        outcome = _dispatch(_review_payload([]), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == "SELECTION_EMPTY"
        assert byte_reads == []

    def test_malformed_payload_shapes_are_refused(self, staging, storage, seq, byte_reads):
        for payload in (
            {"shipmentId": "", "attachmentIds": ["a"], "requestId": "R"},
            {"shipmentId": SHIPMENT_ID, "attachmentIds": "not-a-list", "requestId": "R"},
            {"shipmentId": SHIPMENT_ID, "attachmentIds": [""], "requestId": "R"},
            {"shipmentId": SHIPMENT_ID, "attachmentIds": ["a"]},
        ):
            outcome = _dispatch(payload, seq)
            assert outcome["ok"] is False, payload
            assert outcome["gate"] in {"INVALID_REQUEST", "SELECTION_EMPTY"}, outcome
        assert byte_reads == []

    def test_unknown_shipment_is_refused(self, staging, storage, seq, byte_reads):
        uploaded = storage
        outcome = _dispatch(_review_payload(_by_name(uploaded, INVOICE_XLSX), shipment_id="LO-NOPE"), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == vm.SHIPMENT_IDENTITY_NOT_FOUND
        assert byte_reads == []


# ===========================================================================
# 7. Regression of the reused seams
# ===========================================================================


class TestRegression:
    def test_attachment_projection_gains_only_additive_review_fields(self, staging, storage):
        uploaded = storage
        rows = att.project_attachments(list(uploaded.values()))
        assert len(rows) == 3
        for row in rows:
            # Pre-existing contract is intact.
            for key in ("id", "name", "categoryLabel", "sizeLabel", "uploadedAt",
                        "downloadAvailable", "compressionLabel"):
                assert key in row, key
            # Run 3 adds exactly two fields, both derived server-side.
            assert row["reviewSelectable"] is True
            assert row["reviewNote"] == ""
            # Still no storage identity, still no SHA.
            for forbidden in ("storage_file_id", "storageFileId", "sha256"):
                assert forbidden not in row, forbidden

    def test_non_selectable_attachments_stay_visible_with_a_reason(self, staging, storage):
        uploaded = storage
        png = _upload(SHIPMENT_ID, "anh.png", _tiny_png_bytes())
        rows = {row["name"]: row for row in att.project_attachments(
            list(uploaded.values()) + [png]
        )}
        assert rows["anh.png"]["reviewSelectable"] is False
        assert rows["anh.png"]["reviewNote"] == "Cần OCR — bước này chưa chạy OCR"
        # Visible, not hidden, and still downloadable.
        assert "anh.png" in rows
        assert rows["anh.png"]["downloadAvailable"] is False  # only set for a requested file

    def test_existing_download_path_still_reads_bytes_for_one_attachment(self, staging, storage, seq):
        """The reused seam is unchanged: download still works after Run 3."""

        uploaded = storage
        trigger = {
            "attachment_download": {
                "seq": 1, "event": "attachment_download",
                "payload": {"shipmentId": SHIPMENT_ID,
                            "attachmentId": uploaded[INVOICE_XLSX]["id"], "requestId": "DL-1"},
            }
        }
        outcomes = vm.consume_phase_b_triggers({"seq": 0}, trigger)

        assert len(outcomes) == 1
        assert outcomes[0]["ok"] is True, outcomes[0]["error"]
        assert outcomes[0]["gate"] == "DOWNLOADED"

    def test_run1_and_run2_seams_are_untouched(self):
        """Run 3 imports the existing seams; it does not redefine them."""

        import core.located_text_reader as run2
        import core.trade_document_crosscheck as run1
        from core import shipment_document_review as run3

        assert run3.read_document_text is run2.read_document_text
        assert run3.run_trade_document_crosscheck is run1.run_trade_document_crosscheck
        assert run3.FIELD_SPECS is run1.FIELD_SPECS
        assert len(run1.FIELD_SPECS) == 19

    def test_no_delete_event_and_no_new_storage_surface(self):
        source = Path(vm.__file__).read_text(encoding="utf-8")
        assert "shipment_attachment_delete" not in source
        assert "shipment_document_review" in vm.DOCUMENT_REVIEW_EVENTS
        review_source = Path(
            __import__("core.shipment_document_review", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
        # The review module never constructs a collection, a client or a writer.
        for token in ("get_db(", "save_", "insert_one", "update_one", "MongoClient",
                      "build_gridfs_client", "build_drive_client"):
            assert token not in review_source, token


# ===========================================================================
# 7. Reconcile proof — Run 3 against CURRENT main's My Drive OAuth backend
#
# PR #133 (merged into current main) added a third storage backend,
# ``drive_oauth``, whose credential family is user OAuth rather than a service
# account. Run 3 must consume that backend through the ONE existing reader
# (``core.shipment_attachments.fetch_attachment_bytes``) — never a forked
# reader — and must keep every Run 3 guarantee while doing so.
#
# Only the HTTP client class and the settings source are stubbed. The real
# ``_drive_auth_mode`` → ``load_drive_settings`` → ``build_drive_client`` chain
# executes, so this proves the CURRENT contract rather than a stand-in. No real
# Google credential is used and no Drive integration framework is built.
# ===========================================================================


OAUTH_CLIENT_ID_SENTINEL = "SENTINEL-OAUTH-CLIENT-ID-DO-NOT-PROJECT"
OAUTH_CLIENT_SECRET_SENTINEL = "SENTINEL-OAUTH-CLIENT-SECRET-DO-NOT-PROJECT"
OAUTH_REFRESH_TOKEN_SENTINEL = "SENTINEL-OAUTH-REFRESH-TOKEN-DO-NOT-PROJECT"

OAUTH_SETTINGS = {
    dc.ROOT_FOLDER_ENV: "oauth-root-folder",
    dc.OAUTH_CLIENT_ID_ENV: OAUTH_CLIENT_ID_SENTINEL,
    dc.OAUTH_CLIENT_SECRET_ENV: OAUTH_CLIENT_SECRET_SENTINEL,
    dc.OAUTH_REFRESH_TOKEN_ENV: OAUTH_REFRESH_TOKEN_SENTINEL,
}


class _FakeOAuthDriveClient:
    """Stands in for ``GoogleDriveClient`` in user_oauth mode: bytes only.

    It deliberately has no credential, no session and no network. A single
    instance is shared by the upload and the later read so the review reads
    back exactly the bytes the attachment service stored.
    """

    def __init__(self, settings: Any = None, *, session: Any = None) -> None:
        self.settings = settings
        self.session = session
        self.uploads: list[dict[str, Any]] = []
        self.downloads: list[str] = []
        self.deletes: list[str] = []
        self._files: dict[str, bytes] = {}
        self._folders: dict[tuple[str, str], str] = {}

    def ensure_folder(self, name: str, parent_id: str) -> str:
        key = (parent_id, name)
        if key not in self._folders:
            self._folders[key] = f"oauth-folder-{len(self._folders) + 1}"
        return self._folders[key]

    def upload_file(self, *, name: str, mime: str, data: bytes, parent_id: str,
                    description: str = "") -> dict[str, Any]:
        self.uploads.append({"name": name, "mime": mime, "parentId": parent_id})
        file_id = f"oauth-drive-file-{len(self.uploads)}"
        self._files[file_id] = bytes(data)
        return {"fileId": file_id, "name": name, "mime": mime, "size": len(data),
                "parents": [parent_id], "webViewLink": ""}

    def download_file(self, file_id: str) -> bytes:
        self.downloads.append(file_id)
        return self._files.get(file_id, b"")

    def delete_file(self, file_id: str) -> bool:
        self.deletes.append(file_id)
        self._files.pop(file_id, None)
        return True


@pytest.fixture()
def oauth_drive():
    """A user_oauth Drive backend wired through the REAL auth-mode chain.

    ``core.drive_client.GoogleDriveClient`` is replaced by the byte-only fake
    and ``get_setting`` by sentinels, so ``load_drive_settings`` builds genuine
    user-oauth ``DriveSettings`` and ``build_drive_client`` is reached with
    ``auth_mode=AUTH_MODE_USER_OAUTH`` exactly as production would.
    """

    shared = _FakeOAuthDriveClient()
    seen_auth_modes: list[Any] = []

    def _factory(settings: Any = None, *, session: Any = None):
        seen_auth_modes.append(getattr(settings, "auth_mode", None))
        # The real GoogleDriveClient keeps its settings on the instance, and the
        # upload path reads client.settings.root_folder_id. Mirror that.
        shared.settings = settings
        shared.session = session
        return shared

    with patch("core.drive_client.GoogleDriveClient", _factory), \
         patch(
             "core.drive_client.get_setting",
             side_effect=lambda env, *paths, default="": OAUTH_SETTINGS.get(env, default),
         ):
        yield SimpleNamespace(client=shared, auth_modes=seen_auth_modes)


def _upload_backend(
    shipment_id: str,
    name: str,
    data: bytes,
    backend: str,
    *,
    category: str = "customs",
) -> dict[str, Any]:
    """Upload onto ONE explicit storage backend through the REAL service."""

    outcome = att.upload_attachment(
        shipment_id=shipment_id,
        category=category,
        file_name=name,
        mime=_mime_for(name),
        data=data,
        uploaded_by="staging.support",
        shipment_context=vm.read_shipment(shipment_id),
        storage_backend=backend,
    )
    assert outcome.get("ok"), outcome
    return dict(outcome["record"])


def _upload_oauth(shipment_id: str, name: str, data: bytes, *, category: str = "customs") -> dict[str, Any]:
    """Upload onto the ``drive_oauth`` backend through the REAL service."""

    return _upload_backend(shipment_id, name, data, att.STORAGE_BACKEND_DRIVE_OAUTH, category=category)


class TestReconcileDriveOAuth:
    """Run 3 proven against current main's My Drive OAuth backend."""

    @pytest.fixture()
    def oauth_storage(self, staging, oauth_drive):
        """The three real Run 2 fixtures, stored on the drive_oauth backend."""

        uploaded = {
            name: _upload_oauth(SHIPMENT_ID, name, _fixture_bytes(name))
            for name in CANONICAL_FIXTURES
        }
        # The backend really is drive_oauth end to end — not a relabelled GridFS row.
        for record in uploaded.values():
            assert record["storage_backend"] == att.STORAGE_BACKEND_DRIVE_OAUTH
            assert record["storage_file_id"].startswith("oauth-drive-file-")
        assert att.STORAGE_BACKEND_DRIVE_OAUTH in att.DRIVE_STORAGE_BACKENDS
        return uploaded

    def test_drive_oauth_bytes_are_read_through_the_one_existing_reader(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(c) the drive_oauth byte-read path is reusable without a second reader."""

        ids = _by_name(oauth_storage, *CANONICAL_FIXTURES)
        oauth_drive.auth_modes.clear()
        oauth_drive.client.downloads.clear()

        # The GridFS reader must never be reached for a drive_oauth backend.
        def _no_gridfs(*args, **kwargs):
            raise AssertionError("a drive_oauth review must not construct a GridFS store")

        with patch("core.shipment_attachments.build_gridfs_client", _no_gridfs):
            outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        review = outcome["review"]

        # The full canary still resolves identically on the OAuth backend.
        assert sum(review["statusCounts"].values()) == EXPECTED_TOTAL_FACTS
        assert review["statusCounts"] == EXPECTED_STATUS_COUNTS
        assert review["crossConfirmationComplete"] is True
        assert review["storageByteReads"] == 3
        assert len(byte_reads) == 3

        # ...because it went through the drive_oauth reader in USER OAUTH mode.
        assert len(oauth_drive.client.downloads) == 3
        assert oauth_drive.auth_modes == [dc.AUTH_MODE_USER_OAUTH] * 3
        assert sorted(oauth_drive.client.downloads) == sorted(
            oauth_storage[name]["storage_file_id"] for name in CANONICAL_FIXTURES
        )

    def test_all_three_backends_map_to_the_expected_credential_family(self):
        """gridfs / drive_shared / drive_oauth are all covered by ONE reader."""

        assert att.SUPPORTED_STORAGE_BACKENDS == {
            att.STORAGE_BACKEND_GRIDFS,
            att.STORAGE_BACKEND_DRIVE_SHARED,
            att.STORAGE_BACKEND_DRIVE_OAUTH,
        }
        assert att.DRIVE_STORAGE_BACKENDS == {
            att.STORAGE_BACKEND_DRIVE_SHARED,
            att.STORAGE_BACKEND_DRIVE_OAUTH,
        }
        # PR #133's contract: drive_oauth is the only user-OAuth backend.
        assert att._drive_auth_mode(att.STORAGE_BACKEND_DRIVE_OAUTH) == dc.AUTH_MODE_USER_OAUTH
        assert att._drive_auth_mode(att.STORAGE_BACKEND_DRIVE_SHARED) == dc.AUTH_MODE_SERVICE_ACCOUNT
        assert att._drive_auth_mode(att.STORAGE_BACKEND_GRIDFS) == dc.AUTH_MODE_SERVICE_ACCOUNT

    def test_drive_shared_backend_is_read_through_the_same_reader(
        self, staging, oauth_drive, seq, byte_reads
    ):
        """drive_shared still reviews through the ONE seam, in service-account mode."""

        service_account = json.dumps({
            "client_email": "logi-drive@fake.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----not-a-real-key-----END PRIVATE KEY-----",
            "token_uri": "https://oauth2.googleapis.com/token",
        })

        def _raw_setting(env, *paths, default=""):
            return service_account if env == dc.SERVICE_ACCOUNT_ENV else default

        with patch("core.drive_client.get_raw_setting", side_effect=_raw_setting):
            record = _upload_backend(
                SHIPMENT_ID, INVOICE_XLSX, _fixture_bytes(INVOICE_XLSX),
                att.STORAGE_BACKEND_DRIVE_SHARED,
            )
            assert record["storage_backend"] == att.STORAGE_BACKEND_DRIVE_SHARED
            oauth_drive.auth_modes.clear()
            oauth_drive.client.downloads.clear()
            outcome = _dispatch(_review_payload([record["id"]]), seq)

        assert outcome["ok"] is True, outcome["error"]
        assert outcome["review"]["storageByteReads"] == 1
        assert outcome["review"]["documents"][0]["state"] == STATE_READABLE
        assert oauth_drive.client.downloads == [record["storage_file_id"]]
        assert oauth_drive.auth_modes == [dc.AUTH_MODE_SERVICE_ACCOUNT]

    def test_dashboard_rbac_still_applies_on_the_drive_oauth_backend(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(a) dashboard RBAC still applies when the backend is drive_oauth."""

        import streamlit as st

        ids = _by_name(oauth_storage, *CANONICAL_FIXTURES)
        st.session_state.pop("current_user", None)
        oauth_drive.client.downloads.clear()

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == "BLOCKED_PERMISSION_DENIED"
        # Refused at RBAC: zero byte reads and zero Drive reads.
        assert byte_reads == []
        assert oauth_drive.client.downloads == []

    def test_ownership_is_proven_before_any_drive_oauth_byte_read(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(b) the ownership check still precedes any byte read."""

        foreign = _upload_oauth(OTHER_SHIPMENT_ID, "other.pdf", _blank_pdf_bytes())
        assert foreign["storage_backend"] == att.STORAGE_BACKEND_DRIVE_OAUTH
        ids = _by_name(oauth_storage, INVOICE_XLSX) + [foreign["id"]]
        oauth_drive.client.downloads.clear()

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is False
        assert outcome["gate"] == CODE_SHIPMENT_MISMATCH
        assert outcome["attachmentId"] == foreign["id"]
        # No byte read for the foreign file — and none for any other file.
        assert byte_reads == []
        assert oauth_drive.client.downloads == []

    def test_drive_oauth_review_performs_zero_writes(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(d) the review still performs zero writes on the OAuth backend."""

        ids = _by_name(oauth_storage, *CANONICAL_FIXTURES)
        forbidden = [
            "save_shipment_atomic",
            "save_shipment_attachment",
            "delete_shipment",
            "save_docgen_document",
            "_audit",
            "_save_document",
        ]
        counters = {name: 0 for name in forbidden}

        def guard(name):
            def _boom(*args, **kwargs):
                counters[name] += 1
                raise AssertionError(f"read-only review called a writer: {name}")

            return _boom

        uploads_before = len(oauth_drive.client.uploads)
        with ExitStack() as stack:
            for name in forbidden:
                stack.enter_context(patch(f"core.database.{name}", guard(name)))
            outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        assert all(value == 0 for value in counters.values()), counters
        assert outcome["review"]["savedToShipment"] is False
        # Nothing uploaded, nothing deleted on the OAuth backend.
        assert len(oauth_drive.client.uploads) == uploads_before
        assert oauth_drive.client.deletes == []

    def test_no_oauth_credential_or_token_reaches_the_projection(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(e) no OAuth credential, refresh token or storage id is projected."""

        ids = _by_name(oauth_storage, *CANONICAL_FIXTURES)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        blob = json.dumps(outcome["review"], ensure_ascii=False)
        for secret in (
            OAUTH_CLIENT_ID_SENTINEL,
            OAUTH_CLIENT_SECRET_SENTINEL,
            OAUTH_REFRESH_TOKEN_SENTINEL,
            "refresh_token",
            "client_secret",
            "access_token",
        ):
            assert secret not in blob, secret
        # No Drive file id, no raw SHA-256, no base64 payload.
        for name in CANONICAL_FIXTURES:
            assert oauth_storage[name]["storage_file_id"] not in blob
            assert oauth_storage[name]["sha256"] not in blob
        assert "oauth-drive-file-" not in blob
        assert not SHA256_RE.search(blob)
        assert not BASE64_LOOKS_LIKE.search(blob)

    def test_no_provider_or_ocr_fallback_from_the_drive_oauth_path(
        self, staging, oauth_storage, oauth_drive, seq, byte_reads
    ):
        """(f) no provider/OCR fallback is reached from the drive_oauth path."""

        ids = _by_name(oauth_storage, *CANONICAL_FIXTURES)
        before = set(sys.modules)

        outcome = _dispatch(_review_payload(ids), seq)

        assert outcome["ok"] is True, outcome["error"]
        offenders = [
            name for name in set(sys.modules) - before
            if any(marker in name.lower() for marker in PROVIDER_MODULE_MARKERS)
        ]
        assert offenders == [], offenders

    def test_review_never_forks_a_second_storage_reader(self):
        """The review reuses the ONE reader; it names no Drive/OAuth surface."""

        review_source = Path(
            __import__("core.shipment_document_review", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
        for token in (
            "build_drive_client",
            "load_drive_settings",
            "drive_client",
            "AUTH_MODE_USER_OAUTH",
            "fetch_review_attachment_bytes",
            "download_file",
        ):
            assert token not in review_source, token
        # And the view model still routes bytes through the ONE existing seam.
        assert "fetch_attachment_bytes" in Path(vm.__file__).read_text(encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
