"""Excel quotation presentation adapter on the existing C1 event seam."""
from __future__ import annotations

import base64
from copy import deepcopy
from typing import Any, Mapping


def excel_quote_payload(customer: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.quote_excel_import import validated_source
    from core.quotations import _excel_number, normalize_fx_snapshot

    details = deepcopy(dict(payload.get("excelQuote") or {}))
    cid = str(payload.get("customerId") or customer.get("id") or "")
    trusted = validated_source(dict(details.get("source") or {}), cid)
    # Only disclosure *selections* may change; keep original source facts and
    # warnings from the stored workbook, not from the browser.
    details.update({k: v for k, v in trusted.items() if k != "disclosures"})
    _hydrate_cost_references(details)
    supplied_fx = dict(payload.get("fx") or {})
    rates = {}
    for code in ("CNY", "USD"):
        n = _excel_number(supplied_fx.get(code), f"Tỷ giá {code}")
        if n is not None:
            if n <= 0:
                raise ValueError("Tỷ giá phải lớn hơn 0; để trống nếu chưa biết.")
            rates[code] = float(n)
    cross = _excel_number(supplied_fx.get("CNY_PER_USD"), "RMB/USD")
    if cross is not None:
        if "CNY" in rates:
            raise ValueError("Chọn một cách nhập tỷ giá RMB: RMB → VND trực tiếp hoặc USD → VND + RMB/USD; không tự ghi đè tỷ giá đã nhập.")
        if cross <= 0:
            raise ValueError("RMB/USD phải lớn hơn 0.")
        if "USD" not in rates:
            raise ValueError("Cần USD → VND để dùng RMB/USD; không tự tạo tỷ giá.")
        rates["CNY"] = float(_excel_number(rates["USD"], "USD") / cross)
    return {
        "customer_id": cid, "customer_name": str(customer.get("name") or ""),
        "customer_contact": str(customer.get("contact_person") or ""),
        "customer_email": str(customer.get("email") or ""), "customer_phone": str(customer.get("phone") or ""),
        "sales_owner": str(payload.get("salesOwner") or ""),
        **{k: str(payload.get(camel) or "") for k, camel in (("origin", "origin"), ("destination", "destination"), ("route", "route"), ("incoterm", "incoterm"), ("transport_mode", "transportMode"), ("goods_description", "goodsDescription"), ("expected_delivery_date", "expectedDeliveryDate"))},
        "excel_quote": details, "service_lines": [],
        "fx_snapshot": normalize_fx_snapshot({"rates_to_vnd": rates, "source": "Tỷ giá do Sale xác nhận cho dự toán; không phải tỷ giá hải quan hoặc giao dịch thực tế."}),
        "is_estimate": True, "ledger_posted": False,
    }


def handle_import(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.quote_excel_import import MAX_BYTES, parse_luc_giac_workbook, store_source
    from views.logi_c1 import _actor, _result, read_customer

    event = "quote_import_excel"
    if not can_operate_business("sales_write"):
        return _result(event, "", False, "RBAC: không có quyền sales_write.")
    cid = str(payload.get("customerId") or "")
    if not read_customer(cid):
        return _result(event, "", False, "Chọn khách hàng có sẵn trong danh bạ trước khi nhập Excel.")
    encoded = payload.get("base64")
    if not isinstance(encoded, str) or len(encoded) > (MAX_BYTES * 4 // 3 + 8):
        return _result(event, "", False, "Tệp vượt giới hạn 5 MB.")
    try:
        data = base64.b64decode(encoded, validate=True)
        proposal = parse_luc_giac_workbook(data, str(payload.get("fileName") or ""))
        proposal["source"] = store_source(data, proposal, cid, _actor())
        # Use canonical arithmetic even on the first review, not JS products.
        from core.quotations import calculate_quote
        preview = calculate_quote({"excel_quote": proposal, "status": "DRAFT"})
        return _result(event, "", True, readback=preview["excel_quote"])
    except (ValueError, TypeError) as exc:
        return _result(event, "", False, str(exc))


def handle_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.quotations import calculate_quote, customer_quote_snapshot
    from views.logi_c1 import _result, quote_projection, read_customer

    if not can_operate_business("sales_write"):
        return _result("quote_preview", "", False, "RBAC: không có quyền sales_write.")
    customer = read_customer(str(payload.get("customerId") or ""))
    if not customer:
        return _result("quote_preview", "", False, "Khách hàng không tồn tại.")
    try:
        quote = calculate_quote({**excel_quote_payload(customer, payload), "status": "DRAFT"})
        return _result("quote_preview", "", True, readback={"quote": quote_projection(quote), "customer": customer_quote_snapshot(quote)})
    except ValueError as exc:
        return _result("quote_preview", "", False, str(exc))


def edit_excel_quote(quote: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import get_last_db_error, save_quotes_to_cloud
    from core.quotations import _now, calculate_quote, prepare_quote_for_persistence, transition_quote
    from views.logi_c1 import _actor, _result, quote_projection, read_customer, read_quote, _audit

    qid = str(quote["id"])
    version = int(quote.get("version") or 1)
    if payload.get("expectedVersion") != version:
        return _result("quote_edit", qid, False, "Báo giá đã đổi phiên bản; tải lại trước khi sửa.")
    if not isinstance(payload.get("excelQuote"), Mapping):
        return _result("quote_edit", qid, False, "Mở báo giá bằng luồng Excel để giữ nguyên thông tin nguồn.")
    customer = read_customer(str(quote.get("customer_id") or ""))
    if not customer or payload.get("customerId") != quote.get("customer_id"):
        return _result("quote_edit", qid, False, "Không đổi khách hàng của báo giá đã lưu.")
    try:
        updated = deepcopy(dict(quote))
        status = str(updated.get("status") or "DRAFT")
        if status != "DRAFT":
            updated = transition_quote(updated, "DRAFT", actor=_actor())
        updated.update(excel_quote_payload(customer, payload))
        updated["version"] = version + 1
        updated["updated_at"] = _now()
        stamped = prepare_quote_for_persistence(calculate_quote(updated), actor=_actor())
    except ValueError as exc:
        return _result("quote_edit", qid, False, str(exc))
    if not save_quotes_to_cloud({qid: stamped}, expected_versions={qid: version}):
        return _result("quote_edit", qid, False, get_last_db_error() or "Không lưu được báo giá.")
    fresh = read_quote(qid)
    if not fresh or fresh.get("version") != version + 1:
        return _result("quote_edit", qid, False, "Đã gửi lưu nhưng chưa xác minh được phiên bản mới; tải lại trước khi thử tiếp.")
    return _result("quote_edit", qid, True, readback=quote_projection(fresh), audit=_audit("quote", qid))


def handle_source_workbook(payload: Mapping[str, Any]) -> dict[str, Any]:
    """READ-ONLY: sheet tabs and ONE sheet of the ORIGINAL stored workbook.

    LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 — this is the "keep the original workbook"
    half of the task. It reads the SAME GridFS bytes that were uploaded, verifies
    their SHA256 against the recorded source, and renders one sheet with explicit
    fidelity reporting. It never writes, never re-imports into the quote, and
    never becomes an export path for the original file.

    The workbook is addressable both before the quote is saved (ownership of the
    stored source is re-validated through ``validated_source``) and afterwards
    (through the saved quote's own source reference).
    """
    import hashlib

    from core.auth import can_operate_business
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore
    from core.quote_excel_import import validated_source
    from core.quote_workbook_view import overview, sheet_page
    from views.logi_c1 import _result, read_quote

    event = "quote_source_workbook_view"
    qid = str(payload.get("id") or "")
    if not can_operate_business("commercial_view"):
        return _result(event, qid, False, "RBAC: không có quyền xem báo giá.", requestId=str(payload.get("requestId") or ""))
    details: dict[str, Any] = {}
    if qid:
        quote = read_quote(qid)
        details = dict((quote or {}).get("excel_quote") or {})
    if not details:
        cid = str(payload.get("customerId") or "")
        if not cid or not isinstance(payload.get("source"), Mapping):
            return _result(event, qid, False, "Mở báo giá hoặc nhập Excel trước khi xem workbook gốc.",
                           requestId=str(payload.get("requestId") or ""))
        try:
            details = dict(validated_source(dict(payload.get("source") or {}), cid))
        except (ValueError, TypeError) as exc:
            return _result(event, qid, False, str(exc), requestId=str(payload.get("requestId") or ""))
    source = dict(details.get("source") or {})
    if not source.get("storage_file_id"):
        return _result(event, qid, False, "Báo giá này không có tệp nguồn để đối chiếu.",
                       requestId=str(payload.get("requestId") or ""))
    data = GridFSAttachmentStore(get_db()).download_file(source["storage_file_id"])
    if hashlib.sha256(data).hexdigest() != str(source.get("sha256") or ""):
        return _result(event, qid, False, "Bytes tệp nguồn không khớp SHA256 đã lưu; không hiển thị.",
                       requestId=str(payload.get("requestId") or ""))
    proposal = {"source": source, "source_costs": details.get("source_costs") or []}
    try:
        info = overview(data, proposal)
        sheet_name = str(payload.get("sheet") or "")
        page = sheet_page(data, sheet_name, proposal=proposal,
                          can_view_internal=can_operate_business("commercial_write")) if sheet_name else None
    except ValueError as exc:
        return _result(event, qid, False, str(exc), requestId=str(payload.get("requestId") or ""))
    return _result(event, qid, True, requestId=str(payload.get("requestId") or ""),
                   readback={"read_only": True, "sha256": source["sha256"], "file_name": source.get("file_name"),
                             "overview": info, "page": page,
                             # The raw workbook carries internal data — internal sheets,
                             # and often a cost row inside the customer tab itself — so it
                             # needs the SAME grant that opens source cells. Reported here so
                             # the UI can say why the download is unavailable instead of
                             # silently hiding the button.
                             "can_download_source": can_operate_business("commercial_write"),
                             "note": "Bản xem workbook gốc chỉ để đối chiếu; số liệu nghiệp vụ vẫn sửa ở bảng Bước 1/2."})


def handle_source_download(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Download the ORIGINAL uploaded workbook — bytes and all.

    LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 Finding 1 — the original file is not a
    customer document: it is the raw workbook the customer sent, and it normally
    carries the supplier's cost sheets, internal notes and scratch tabs. Handing
    it out needs the SAME business grant the internal-sheet viewer needs
    (``commercial_write``), never the plain read permission that is enough to read
    the customer quotation. A role holding only ``commercial_view`` still reads
    every customer-facing part of the quote; it simply does not receive the
    supplier's own file. No role and no permission is added here.
    """
    import hashlib

    from core.auth import can_operate_business
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore
    from core.quote_excel_import import MIME_XLSX
    from core.quote_workbook_view import internal_rows_on_customer_sheet, protected_sheet_names
    from views.logi_c1 import _result, read_quote

    qid = str(payload.get("id") or "")
    if not can_operate_business("commercial_view"):
        return _result("quote_source_download", qid, False, "RBAC: không có quyền xem báo giá.")
    quote = read_quote(qid)
    source = (quote or {}).get("excel_quote", {}).get("source", {})
    if not source:
        return _result("quote_source_download", qid, False, "Không có tệp nguồn của báo giá.")
    # The workbook as a whole may carry internal data. The permission is decided
    # from the file's own sheet layout, using the SAME classification rule the
    # viewer uses, and the read is refused rather than silently trimmed: a
    # partial workbook would be a different document than the one on record.
    proposal = {"source": source, "source_costs": (quote or {}).get("excel_quote", {}).get("source_costs") or []}
    protected = protected_sheet_names(list(source.get("sheet_names") or []), proposal)
    # Cost figures found ON the customer sheet count too: a one-sheet workbook can
    # still carry the supplier's internal figures, so "no internal sheets" is not
    # the same thing as "nothing internal in this file".
    embedded = internal_rows_on_customer_sheet(proposal)
    if (protected or embedded) and not can_operate_business("commercial_write"):
        evidence = ", ".join(protected[:3]) if protected else f"{len(embedded)} dòng chi phí nằm ngay trong sheet khách"
        return _result("quote_source_download", qid, False,
                       "RBAC: workbook gốc chứa dữ liệu nội bộ/chưa phân loại "
                       f"({evidence}); cần quyền thao tác báo giá (commercial_write) để tải toàn bộ tệp nguồn.")
    data = GridFSAttachmentStore(get_db()).download_file(source["storage_file_id"])
    # Same integrity rule as the viewer: bytes that no longer match the recorded
    # hash are not handed out as if they were the archived file.
    if hashlib.sha256(data).hexdigest() != str(source.get("sha256") or ""):
        return _result("quote_source_download", qid, False, "Bytes tệp nguồn không khớp SHA256 đã lưu; không tải.")
    return _result("quote_source_download", qid, True, document={"fileName": source["file_name"], "mime": MIME_XLSX,
                   "downloadBase64": base64.b64encode(data).decode("ascii"), "byteSize": len(data)})


def _hydrate_cost_references(details: dict[str, Any]) -> None:
    """Re-read selected rate_cards on the existing connection; retain warnings.

    Amounts remain reference costs only. The Sale's independent selling price
    and confirmation are never populated by this function.
    """
    from datetime import date, datetime
    from core.database import get_db

    db = get_db()
    for option in (details.get("options") or {}).values():
        for line in option.get("service_lines") or []:
            sid, rid = str(line.get("rate_snapshot_id") or ""), str(line.get("rate_row_id") or "")
            if not sid:
                continue
            snapshot = db.rate_cards.find_one({"id": sid, "is_deleted": {"$ne": True}}) if db is not None else None
            row = next((r for r in (snapshot or {}).get("rows") or [] if r.get("id") == rid), None)
            if not row or snapshot.get("status") == "WITHDRAWN" or row.get("status") != "AVAILABLE" or row.get("amount") is None or row.get("kind") == "CREDIT":
                raise ValueError("Giá vốn đã chọn không còn khả dụng; kiểm tra lại Kho giá vốn.")
            expiry = str(row.get("validUntil") or "")
            validity = "UNKNOWN"
            if expiry:
                parsed = None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        parsed = datetime.strptime(expiry, fmt).date()
                        break
                    except ValueError:
                        continue
                if parsed:
                    validity = "EXPIRED" if parsed < date.today() else "SOURCE_VALID"
            if snapshot.get("status") in {"EXPIRED", "SUPERSEDED"}:
                validity = snapshot["status"]
            line.update({"cost_unit": row["amount"], "currency": row.get("currency") or "VND",
                         "unit": row.get("equipment") or row.get("unit") or "Lần", "valid_until": expiry,
                         "validity_status": validity,
                         "cost_source": f"{snapshot.get('supplier') or 'Nguồn chưa ghi'} · {sid} · {rid}",
                         "source_warning": " · ".join(str(x) for x in [row.get("reviewNote"), *row.get("conditionalAmounts", [])] if x),
                         "condition": "IF_APPLICABLE" if row.get("conditionalAmounts") else line.get("condition", "UNCONFIRMED")})
