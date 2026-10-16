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


def handle_source_download(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore
    from core.quote_excel_import import MIME_XLSX
    from views.logi_c1 import _result, read_quote

    qid = str(payload.get("id") or "")
    if not can_operate_business("commercial_view"):
        return _result("quote_source_download", qid, False, "RBAC: không có quyền xem báo giá.")
    quote = read_quote(qid)
    source = (quote or {}).get("excel_quote", {}).get("source", {})
    if not source:
        return _result("quote_source_download", qid, False, "Không có tệp nguồn của báo giá.")
    data = GridFSAttachmentStore(get_db()).download_file(source["storage_file_id"])
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
