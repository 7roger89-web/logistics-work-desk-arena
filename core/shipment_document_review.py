"""LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — read-only shipment review.

Run 3 connects the two capabilities already merged into ``main`` to the
EXISTING shipment **Chứng từ / Tệp đính kèm** surface:

* Run 2 — ``core.located_text_reader.read_document_text`` turns real bounded
  XLSX / born-digital PDF bytes into located text;
* Run 1 — ``core.trade_document_crosscheck.run_trade_document_crosscheck``
  compares those documents over the frozen 19 canonical facts.

This module is an ORCHESTRATION + PROJECTION layer only. It deliberately does
not create a second attachment store, a second reader, an OCR router, a
provider abstraction, a workflow engine or a review database:

* attachment bytes are read through the ONE existing seam
  ``core.shipment_attachments.fetch_attachment_bytes(..., shipment_id=...)``,
  which re-loads canonical metadata and proves shipment ownership BEFORE any
  backend byte read;
* document text comes from the ONE Run 2 reader;
* the cross-check is the ONE Run 1 engine, unchanged;
* the result is a bounded dict the caller keeps in Streamlit session state.

It never writes to Mongo, GridFS, Drive or an audit collection, never calls a
network provider, never OCRs, and never selects a winner for a conflict.
Unreadable documents stay visible with their honest state and contribute ZERO
fabricated trade facts.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from core.document_extraction import DocumentSecurityError
from core.located_text_reader import (
    TEXT_NOT_AVAILABLE_NO_OCR,
    TextReaderLimits,
    read_document_text,
)
from core.shipment_attachments import extension_of
from core.trade_document_crosscheck import (
    FIELD_SPECS,
    FactStatus,
    run_trade_document_crosscheck,
)

#: Run 3 is a review surface, not a bulk document processor.
MAX_REVIEW_FILES = 6
#: Aggregate metadata preflight bound for ONE operator request.
MAX_REVIEW_TOTAL_BYTES = 30 * 1024 * 1024

#: Extensions the operator may select for this run.
REVIEW_EXTENSIONS: tuple[str, ...] = ("pdf", "xlsx")

# --- bounded document states ------------------------------------------------

STATE_READABLE = "READABLE"
STATE_NEEDS_OCR_NOT_RUN = "NEEDS_OCR_NOT_RUN"
STATE_UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
STATE_TOO_LARGE_FOR_REVIEW = "TOO_LARGE_FOR_REVIEW"
STATE_READ_FAILED = "READ_FAILED"

DOCUMENT_STATES: tuple[str, ...] = (
    STATE_READABLE,
    STATE_NEEDS_OCR_NOT_RUN,
    STATE_UNSUPPORTED_FORMAT,
    STATE_TOO_LARGE_FOR_REVIEW,
    STATE_READ_FAILED,
)

STATE_LABELS: dict[str, str] = {
    STATE_READABLE: "Đọc được",
    STATE_NEEDS_OCR_NOT_RUN: "Cần OCR — bước này chưa chạy OCR",
    STATE_UNSUPPORTED_FORMAT: "Chưa kiểm tra tự động được ở bước này",
    STATE_TOO_LARGE_FOR_REVIEW: "Quá lớn để kiểm tra ở bước này",
    STATE_READ_FAILED: "Không đọc được tệp",
}

# --- bounded request-level refusal codes ------------------------------------

CODE_INVALID_REQUEST = "INVALID_REQUEST"
CODE_SELECTION_EMPTY = "SELECTION_EMPTY"
CODE_SELECTION_LIMIT_EXCEEDED = "SELECTION_LIMIT_EXCEEDED"
CODE_DUPLICATE_SELECTION = "DUPLICATE_SELECTION"
CODE_ATTACHMENT_NOT_FOUND = "ATTACHMENT_NOT_FOUND"
CODE_SHIPMENT_MISMATCH = "SHIPMENT_MISMATCH"
CODE_REVIEW_BUDGET_EXCEEDED = "REVIEW_BUDGET_EXCEEDED"
CODE_CROSSCHECK_FAILED = "CROSSCHECK_FAILED"

# --- Vietnamese operator labels ---------------------------------------------

#: Vietnamese display labels for the 19 canonical Run 1 field keys. Canonical
#: keys stay authoritative in code/data; the label is operator wording only.
VIETNAMESE_FACT_LABELS: dict[str, str] = {
    "shipper": "Người gửi",
    "consignee": "Người nhận",
    "invoice_number": "Số hóa đơn",
    "invoice_date": "Ngày hóa đơn",
    "incoterm": "Điều kiện Incoterms",
    "total": "Tổng tiền",
    "package_count": "Số kiện",
    "net_weight": "Khối lượng tịnh",
    "gross_weight": "Khối lượng cả bì",
    "cbm": "Thể tích",
    "origin": "Xuất xứ",
    "pol": "Cảng xếp",
    "pod": "Cảng dỡ",
    "vessel": "Tàu",
    "voyage": "Chuyến",
    "container": "Số container",
    "seal": "Số seal",
    "bl_number": "Số vận đơn",
    "hs_code": "Mã HS",
}

VIETNAMESE_STATUS_LABELS: dict[str, str] = {
    FactStatus.CONFLICT.value: "Lệch",
    FactStatus.UNKNOWN.value: "Chưa xác định",
    FactStatus.MISSING.value: "Thiếu",
    FactStatus.SINGLE_SOURCE.value: "Chỉ một nguồn",
    FactStatus.SAME.value: "Khớp",
}

VIETNAMESE_DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "INVOICE": "Hóa đơn thương mại",
    "PACKING_LIST": "Packing List",
    "BILL_OF_LADING": "Vận đơn đường biển",
    "UNKNOWN_DOCUMENT": "Chưa phân loại được",
}

#: Deterministic CẦN XEM ordering: CONFLICT → UNKNOWN → MISSING, then
#: SINGLE_SOURCE (THAM KHẢO), then SAME (ĐÃ KHỚP).
STATUS_ORDER: dict[str, int] = {
    FactStatus.CONFLICT.value: 0,
    FactStatus.UNKNOWN.value: 1,
    FactStatus.MISSING.value: 2,
    FactStatus.SINGLE_SOURCE.value: 3,
    FactStatus.SAME.value: 4,
}

#: Every CONFLICT keeps all of its source sides and never selects a winner.
CONFLICT_OPERATOR_NOTE = "Chưa chọn giá trị đúng — cần người kiểm tra."

#: Honest Vietnamese reason for an extension this run does not select.
#: The wording must not imply the file is damaged.
UNSUPPORTED_REASON_IMAGE = "Cần OCR — bước này chưa chạy OCR"
UNSUPPORTED_REASON_OFFICE_LEGACY = "Chưa hỗ trợ kiểm tra tự động ở bước này"
UNSUPPORTED_REASON_OTHER = "Không hỗ trợ ở bước này"

#: Bounded evidence: one fact keeps at most this many source sides.
MAX_FACT_SIDES = 8
#: Bounded evidence: a projected raw/normalized value is trimmed to this.
MAX_EVIDENCE_CHARS = 160
#: Canonical document types whose three-way presence means a complete review.
CANONICAL_REVIEW_TYPES: tuple[str, ...] = ("INVOICE", "PACKING_LIST", "BILL_OF_LADING")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounded_text(value: Any, limit: int = MAX_EVIDENCE_CHARS) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def display_name_of(record: Mapping[str, Any]) -> str:
    """The operator-visible filename of ONE canonical attachment record."""

    return str(record.get("original_name") or record.get("stored_name") or "").strip()


def metadata_size_of(record: Mapping[str, Any]) -> int:
    """Bytes the store says this attachment occupies (0 = metadata silent).

    ``stored_size`` is what a byte read will actually return; ``original_size``
    is the honest fallback for rows written before the optimizer. When metadata
    carries no usable number the preflight cannot bound it and the real-bytes
    check after the read remains the authority.
    """

    for key in ("stored_size", "original_size"):
        raw = record.get(key)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return 0


def unsupported_reason(extension: str) -> str:
    """Honest Vietnamese wording for an extension this run cannot review."""

    lowered = str(extension or "").strip().lower()
    if lowered in {"jpg", "jpeg", "png"}:
        return UNSUPPORTED_REASON_IMAGE
    if lowered in {"doc", "docx", "xls"}:
        return UNSUPPORTED_REASON_OFFICE_LEGACY
    return UNSUPPORTED_REASON_OTHER


def _document_outcome(
    attachment_id: str,
    file_name: str,
    state: str,
    reason: str,
    *,
    document_type: str = "",
    reader_method: str = "",
    size_bytes: int = 0,
    warning: str = "",
) -> dict[str, Any]:
    """ONE bounded document outcome. Never carries bytes, text or storage ids."""

    return {
        "attachmentId": attachment_id,
        "fileName": file_name,
        "state": state,
        "stateLabel": STATE_LABELS.get(state, state),
        "reason": reason,
        "documentType": document_type,
        "documentTypeLabel": VIETNAMESE_DOCUMENT_TYPE_LABELS.get(document_type, ""),
        "readerMethod": reader_method,
        "sizeBytes": int(size_bytes or 0),
        "warning": warning,
    }


def _refusal(code: str, message: str, *, attachment_id: str = "") -> dict[str, Any]:
    return {"code": code, "message": message, "attachmentId": attachment_id}


# ---------------------------------------------------------------------------
# Preflight — every refusal below happens BEFORE any storage byte is read
# ---------------------------------------------------------------------------


def preflight_selection(
    shipment_id: str,
    attachment_ids: Sequence[Any],
    metadata_rows: Mapping[str, Mapping[str, Any]],
    *,
    limits: TextReaderLimits | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    """Validate the selection from canonical metadata alone.

    Returns ``(documents, eligible, refusal)`` where ``documents`` is the
    honest per-attachment outcome list in the operator's selection order,
    ``eligible`` the canonical records that may be read, and ``refusal`` a
    request-level refusal (``None`` when the request may proceed).

    Order is the contract: count → uniqueness → metadata existence →
    shipment ownership → supported extension → per-file byte budget →
    aggregate review budget. ZERO storage bytes are read here.
    """

    active_limits = limits or TextReaderLimits()
    sid = str(shipment_id or "").strip()
    ids = [str(item).strip() for item in (attachment_ids or [])]
    ids = [item for item in ids if item]

    if not ids:
        return [], [], _refusal(CODE_SELECTION_EMPTY, "Chưa chọn tệp nào để kiểm tra.")
    if len(ids) > MAX_REVIEW_FILES:
        return [], [], _refusal(
            CODE_SELECTION_LIMIT_EXCEEDED,
            f"Chỉ kiểm tra tối đa {MAX_REVIEW_FILES} tệp một lần — đã chọn {len(ids)} tệp. "
            "Chưa đọc bất kỳ tệp nào.",
        )
    if len(set(ids)) != len(ids):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        return [], [], _refusal(
            CODE_DUPLICATE_SELECTION,
            "Danh sách tệp bị trùng — mỗi tệp chỉ được chọn một lần. Chưa đọc bất kỳ tệp nào.",
            attachment_id=duplicates[0],
        )

    documents: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    eligible_bytes = 0

    for attachment_id in ids:
        record = metadata_rows.get(attachment_id)
        if not isinstance(record, Mapping):
            return documents, [], _refusal(
                CODE_ATTACHMENT_NOT_FOUND,
                "Không tìm thấy tệp đính kèm này trong lô hàng. Chưa đọc bất kỳ tệp nào.",
                attachment_id=attachment_id,
            )
        if str(record.get("shipment_id") or "").strip() != sid:
            # Ownership is proven from canonical metadata BEFORE any byte read,
            # so a mismatched attachment costs zero storage reads.
            return documents, [], _refusal(
                CODE_SHIPMENT_MISMATCH,
                "Có tệp đính kèm không thuộc lô hàng này. Chưa đọc bất kỳ tệp nào.",
                attachment_id=attachment_id,
            )

        name = display_name_of(record)
        size = metadata_size_of(record)
        extension = extension_of(name)
        if extension not in REVIEW_EXTENSIONS:
            documents.append(
                _document_outcome(
                    attachment_id, name, STATE_UNSUPPORTED_FORMAT,
                    unsupported_reason(extension), size_bytes=size,
                )
            )
            continue
        if size and size > active_limits.max_file_bytes:
            documents.append(
                _document_outcome(
                    attachment_id, name, STATE_TOO_LARGE_FOR_REVIEW,
                    f"Tệp lớn hơn giới hạn đọc {_mb(active_limits.max_file_bytes)} của bộ đọc chứng từ.",
                    size_bytes=size,
                )
            )
            continue

        documents.append(
            _document_outcome(attachment_id, name, STATE_READABLE, "Đang chờ đọc.", size_bytes=size)
        )
        eligible.append(
            {
                "attachmentId": attachment_id,
                "fileName": name,
                "record": dict(record),
                "metadataBytes": size,
                # ``documents`` also holds unsupported / over-budget rows, so an
                # eligible item must carry the slot it owns rather than assume
                # the two lists stay index-aligned.
                "documentIndex": len(documents) - 1,
            }
        )
        eligible_bytes += size

    if eligible_bytes > MAX_REVIEW_TOTAL_BYTES:
        return [], [], _refusal(
            CODE_REVIEW_BUDGET_EXCEEDED,
            f"Tổng dung lượng {len(eligible)} tệp đã chọn là {_mb(eligible_bytes)} — vượt giới hạn "
            f"{_mb(MAX_REVIEW_TOTAL_BYTES)} cho một lần kiểm tra. Chưa đọc bất kỳ tệp nào.",
        )

    return documents, eligible, None


def _mb(size: int) -> str:
    return f"{size / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Projection helpers
# ---------------------------------------------------------------------------


def _location_label(provenance: Mapping[str, Any] | None) -> str:
    """Bounded Vietnamese page OR sheet/cell provenance — never full text."""

    if not isinstance(provenance, Mapping):
        return ""
    page = provenance.get("page_number")
    sheet = str(provenance.get("sheet_name") or "")
    cell = str(provenance.get("cell_coordinate") or "")
    if page is not None:
        return f"Trang {page}"
    if sheet and cell:
        return f"Sheet {sheet} · ô {cell}"
    if sheet:
        return f"Sheet {sheet}"
    line = provenance.get("line_number")
    return f"Dòng {line}" if line is not None else ""


def _unique_artifact_label(base_name: str, taken: set[str]) -> str:
    """A label the Run 1 engine accepts: it refuses duplicate document labels.

    Two attachments may share a filename, so the second copy gets a bounded
    deterministic suffix. The operator always sees the real display name; this
    label only disambiguates the cross-check sides.
    """

    candidate = base_name or "document"
    if candidate not in taken:
        return candidate
    index = 2
    while f"{candidate}-{index}" in taken:
        index += 1
    return f"{candidate}-{index}"


def _fact_projection(fact: Any, sides_identity: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    """ONE bounded fact for the operator — Vietnamese label, canonical key,
    status, source sides with page OR sheet/cell location, reason, decision.

    ``sides_identity`` maps a Run 1 document label back to the attachment it
    came from, so a side carries the operator-visible filename and its
    attachment id — never a storage id.

    No confidence score, no percentage, no quality score: the engine is
    rule-based and this projection invents nothing it did not compute.
    """

    status = fact.status.value
    sides: list[dict[str, Any]] = []
    for observation in fact.observations[:MAX_FACT_SIDES]:
        raw = observation.raw_value
        if raw is None or str(raw).strip() == "":
            # NOT_FOUND carries no evidence; surfacing an empty side would read
            # as "the document said nothing" when it said no such field exists.
            continue
        identity = sides_identity.get(observation.document_label) or {}
        sides.append(
            {
                "attachmentId": identity.get("attachmentId", ""),
                "fileName": identity.get("fileName") or observation.document_label,
                "documentLabel": observation.document_label,
                "documentType": observation.document_type.value,
                "documentTypeLabel": VIETNAMESE_DOCUMENT_TYPE_LABELS.get(
                    observation.document_type.value, ""
                ),
                "observationStatus": observation.status.value,
                "rawValue": _bounded_text(raw),
                "normalizedValue": _bounded_text(observation.normalized_key or observation.normalized_value),
                "unit": str(observation.unit or ""),
                "location": _location_label(observation.source_provenance),
                "reason": str(observation.reason or ""),
            }
        )
    return {
        "fieldKey": fact.field_key,
        "label": VIETNAMESE_FACT_LABELS.get(fact.field_key, fact.field_key),
        "status": status,
        "statusLabel": VIETNAMESE_STATUS_LABELS.get(status, status),
        "reason": str(fact.reason or ""),
        "operatorDecision": str(fact.operator_decision or "NONE"),
        "operatorNote": CONFLICT_OPERATOR_NOTE if status == FactStatus.CONFLICT.value else "",
        "sides": sides,
    }


def _sorted_facts(facts: Sequence[Any]) -> list[Any]:
    """CẦN XEM first (CONFLICT → UNKNOWN → MISSING), then SINGLE_SOURCE, SAME."""

    field_order = {spec.field_key: index for index, spec in enumerate(FIELD_SPECS)}
    return sorted(
        facts,
        key=lambda fact: (STATUS_ORDER.get(fact.status.value, 9), field_order.get(fact.field_key, 99)),
    )


# ---------------------------------------------------------------------------
# The ONE read-only review
# ---------------------------------------------------------------------------


def run_shipment_document_review(
    shipment_id: str,
    attachment_ids: Sequence[Any],
    *,
    metadata_rows: Mapping[str, Mapping[str, Any]],
    fetch_bytes: Callable[..., Mapping[str, Any]] | None = None,
    limits: TextReaderLimits | None = None,
) -> dict[str, Any]:
    """Run ONE bounded read-only review over already-ownership-checked metadata.

    The caller (the dispatcher) owns RBAC and fresh shipment existence; this
    function owns the remaining server order: bounded selection → metadata
    preflight → sequential storage reads through the EXISTING
    ``core.shipment_attachments.fetch_attachment_bytes`` → Run 2 reader →
    Run 1 cross-check → bounded projection.

    It writes nothing, calls no provider, and never OCRs. Any request-level
    refusal returns before the first storage byte is read.
    """

    sid = str(shipment_id or "").strip()
    active_limits = limits or TextReaderLimits()
    if fetch_bytes is None:
        from core.shipment_attachments import fetch_attachment_bytes as fetch_bytes  # noqa: PLC0415

    documents, eligible, refusal = preflight_selection(
        sid, attachment_ids, metadata_rows, limits=active_limits
    )
    if refusal is not None:
        return _projection(
            sid,
            selected_count=len([item for item in (attachment_ids or []) if str(item).strip()]),
            documents=documents,
            facts=[],
            status_counts=_empty_status_counts(),
            refusal=refusal,
            storage_byte_reads=0,
        )

    # Documents are read SEQUENTIALLY: one container is decompressed at a time.
    artifacts = []
    taken_labels: set[str] = set()
    #: Run 1 document label -> bounded identity of the attachment it came from.
    sides_identity: dict[str, dict[str, str]] = {}
    label_by_attachment: dict[str, str] = {}
    readable_slots: list[int] = []

    for item in eligible:
        slot = int(item["documentIndex"])
        attachment_id = item["attachmentId"]
        name = item["fileName"]
        outcome = fetch_bytes({"id": attachment_id}, shipment_id=sid)
        if not outcome.get("ok"):
            documents[slot] = _document_outcome(
                attachment_id, name, STATE_READ_FAILED,
                str(outcome.get("error") or "Không đọc được tệp từ kho chứng từ."),
                size_bytes=item["metadataBytes"],
            )
            continue

        data = bytes(outcome.get("data") or b"")
        if len(data) > active_limits.max_file_bytes:
            documents[slot] = _document_outcome(
                attachment_id, name, STATE_TOO_LARGE_FOR_REVIEW,
                f"Tệp thật lớn hơn giới hạn đọc {_mb(active_limits.max_file_bytes)} của bộ đọc chứng từ.",
                size_bytes=len(data),
            )
            continue

        try:
            located = read_document_text(data, name, limits=active_limits)
        except DocumentSecurityError as exc:
            message = str(exc)
            state = STATE_TOO_LARGE_FOR_REVIEW if "exceeds the bounded" in message else STATE_READ_FAILED
            reason = (
                f"Tệp vượt giới hạn đọc chứng từ ({message})."
                if state == STATE_TOO_LARGE_FOR_REVIEW
                else f"Không đọc được nội dung tệp ({message})."
            )
            documents[slot] = _document_outcome(
                attachment_id, name, state, reason, size_bytes=len(data)
            )
            continue
        except Exception as exc:  # noqa: BLE001 - per-document containment
            documents[slot] = _document_outcome(
                attachment_id, name, STATE_READ_FAILED,
                f"Không đọc được nội dung tệp ({type(exc).__name__}).", size_bytes=len(data),
            )
            continue

        if located.unsupported_state == TEXT_NOT_AVAILABLE_NO_OCR:
            # Image-only PDF: honest no-OCR state, zero fabricated trade facts.
            documents[slot] = _document_outcome(
                attachment_id, name, STATE_NEEDS_OCR_NOT_RUN,
                UNSUPPORTED_REASON_IMAGE,
                reader_method=located.reader_method, size_bytes=len(data),
                warning="; ".join(located.warnings[:3]),
            )
            continue

        label = _unique_artifact_label(located.source_filename or name, taken_labels)
        taken_labels.add(label)
        label_by_attachment[attachment_id] = label
        sides_identity[label] = {"attachmentId": attachment_id, "fileName": name}
        artifacts.append(replace(located.to_document_artifact(), filename=label))
        readable_slots.append(slot)

    readable_count = len(artifacts)
    facts: list[Any] = []
    status_counts = _empty_status_counts()
    classified_types: dict[str, str] = {}
    crosscheck_refusal: dict[str, Any] | None = None

    if artifacts:
        try:
            crosscheck = run_trade_document_crosscheck(artifacts)
        except Exception as exc:  # noqa: BLE001 - honest containment, never a fake result
            crosscheck_refusal = _refusal(
                CODE_CROSSCHECK_FAILED,
                f"Không đối chiếu được chứng từ đã đọc ({type(exc).__name__}). "
                "Chưa ghi gì vào hồ sơ lô hàng.",
            )
        else:
            facts = _sorted_facts(crosscheck.facts)
            status_counts = dict(crosscheck.status_counts())
            for summary in crosscheck.documents:
                classified_types[summary.document_label] = summary.document_type.value

    # Fill the classified document type back onto the readable outcomes.
    slot_by_label = {
        label: slot
        for label, slot in zip(
            (label_by_attachment[documents[slot]["attachmentId"]] for slot in readable_slots),
            readable_slots,
        )
    }
    for label, document_type in classified_types.items():
        slot = slot_by_label.get(label)
        if slot is None:
            continue
        documents[slot]["documentType"] = document_type
        documents[slot]["documentTypeLabel"] = VIETNAMESE_DOCUMENT_TYPE_LABELS.get(document_type, "")
        documents[slot]["reason"] = "Đã đọc lớp chữ trong tệp."

    return _projection(
        sid,
        selected_count=len(documents),
        documents=documents,
        facts=[_fact_projection(fact, sides_identity) for fact in facts],
        status_counts=status_counts,
        readable_count=readable_count,
        classified_types=classified_types,
        refusal=crosscheck_refusal,
        storage_byte_reads=len(eligible),
    )


def _empty_status_counts() -> dict[str, int]:
    return {status.value: 0 for status in FactStatus}


def _projection(
    shipment_id: str,
    *,
    selected_count: int,
    documents: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    status_counts: dict[str, int],
    readable_count: int | None = None,
    classified_types: Mapping[str, str] | None = None,
    refusal: dict[str, Any] | None = None,
    storage_byte_reads: int = 0,
) -> dict[str, Any]:
    """The bounded ephemeral review result the session keeps and the UI shows.

    Deliberately absent: PDF/XLSX bytes, base64, the full extracted text, the
    whole ``LocatedTextDocument``, any GridFS/Drive/storage id, the raw
    SHA-256, and any credential.
    """

    readable = readable_count if readable_count is not None else sum(
        1 for item in documents if item["state"] == STATE_READABLE
    )
    types_present = {
        value for value in (classified_types or {}).values() if value in CANONICAL_REVIEW_TYPES
    }
    complete = all(name in types_present for name in CANONICAL_REVIEW_TYPES)
    return {
        "shipmentId": shipment_id,
        "reviewedAt": _utc_now_iso(),
        "selectedCount": int(selected_count),
        "readableCount": int(readable),
        "storageByteReads": int(storage_byte_reads),
        "statusCounts": {key: int(status_counts.get(key, 0)) for key in _empty_status_counts()},
        "documents": documents,
        "facts": facts,
        "crossConfirmationComplete": bool(complete),
        "partialNote": _partial_note(readable, complete),
        "refusal": refusal,
        "savedToShipment": False,
    }


def _partial_note(readable_count: int, complete: bool) -> str:
    if readable_count <= 0:
        return "Chưa đọc được tệp nào — chỉ có trạng thái tệp, chưa đối chiếu."
    if complete:
        return "Đã có đủ ba loại chứng từ chính để đối chiếu."
    return "Chưa đủ ba loại chứng từ chính — đối chiếu chéo chưa đầy đủ."


__all__ = [
    "CANONICAL_REVIEW_TYPES",
    "CODE_ATTACHMENT_NOT_FOUND",
    "CODE_CROSSCHECK_FAILED",
    "CODE_DUPLICATE_SELECTION",
    "CODE_INVALID_REQUEST",
    "CODE_REVIEW_BUDGET_EXCEEDED",
    "CODE_SELECTION_EMPTY",
    "CODE_SELECTION_LIMIT_EXCEEDED",
    "CODE_SHIPMENT_MISMATCH",
    "CONFLICT_OPERATOR_NOTE",
    "DOCUMENT_STATES",
    "MAX_FACT_SIDES",
    "MAX_REVIEW_FILES",
    "MAX_REVIEW_TOTAL_BYTES",
    "REVIEW_EXTENSIONS",
    "STATE_LABELS",
    "STATE_NEEDS_OCR_NOT_RUN",
    "STATE_READABLE",
    "STATE_READ_FAILED",
    "STATE_TOO_LARGE_FOR_REVIEW",
    "STATE_UNSUPPORTED_FORMAT",
    "STATUS_ORDER",
    "UNSUPPORTED_REASON_IMAGE",
    "UNSUPPORTED_REASON_OFFICE_LEGACY",
    "UNSUPPORTED_REASON_OTHER",
    "VIETNAMESE_DOCUMENT_TYPE_LABELS",
    "VIETNAMESE_FACT_LABELS",
    "VIETNAMESE_STATUS_LABELS",
    "display_name_of",
    "metadata_size_of",
    "preflight_selection",
    "run_shipment_document_review",
    "unsupported_reason",
]
