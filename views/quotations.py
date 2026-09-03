"""LOG-C12 commercial quotation workspace.

The UI uses the existing customer/service/shipment writers and keeps all quote
numbers as estimates. It never posts a finance ledger entry.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from core.auth import can_operate_business
from core.config import GETFLY_SERVICES_LIST
from core.database import (
    generate_shipment_id,
    load_customers,
    load_quotes,
    save_quotes_to_cloud,
    save_shipment_atomic,
)
from core.quotations import (
    QUOTE_STATUSES,
    build_shipment_draft,
    calculate_quote,
    new_quote_document,
    prepare_quote_for_persistence,
    transition_quote,
)
from core.validators import validate_shipment
from views.sales import ui_sales_module as ui_legacy_sales_module


def _quote_store() -> dict[str, dict[str, Any]]:
    if "db_quotes" not in st.session_state:
        st.session_state.db_quotes = load_quotes()
    return st.session_state.db_quotes


def _customer_store() -> dict[str, dict[str, Any]]:
    if "db_customers" not in st.session_state:
        st.session_state.db_customers = load_customers()
    return st.session_state.db_customers


def _persist_quote(quote: dict[str, Any]) -> bool:
    actor = str(st.session_state.get("current_user", {}).get("username") or "SALE")
    try:
        stamped = prepare_quote_for_persistence(quote, actor=actor)
    except ValueError as exc:
        st.error(str(exc))
        return False
    ok = save_quotes_to_cloud({str(stamped["id"]): stamped})
    if ok:
        _quote_store()[str(stamped["id"])] = stamped
        st.session_state.quote_detail_id = str(stamped["id"])
        st.session_state.needs_refresh = True
    return ok


def _service_options() -> tuple[list[str], dict[str, dict[str, Any]]]:
    mapping = {str(item.get("code")): item for item in GETFLY_SERVICES_LIST if item.get("code")}
    return list(mapping), mapping


def _render_quote_table(quotes: dict[str, dict[str, Any]]) -> None:
    st.subheader("Báo giá đang theo dõi")
    c1, c2, c3 = st.columns(3)
    search = c1.text_input("Khách hàng / mã báo giá", key="quote_search")
    status = c2.selectbox("Trạng thái", ["Tất cả", *QUOTE_STATUSES], key="quote_status_filter")
    owner = c3.text_input("SALE phụ trách", key="quote_owner_filter")
    rows = []
    for quote in quotes.values():
        haystack = " ".join(str(quote.get(k, "")) for k in ("quote_no", "customer_name", "factory_name"))
        if search.strip().lower() not in haystack.lower():
            continue
        if status != "Tất cả" and quote.get("status") != status:
            continue
        if owner.strip().lower() not in str(quote.get("sales_owner", "")).lower():
            continue
        calc = quote.get("calculation", {})
        rows.append({
            "Mã báo giá": quote.get("quote_no", quote.get("id", "")),
            "Khách hàng": quote.get("customer_name", ""),
            "Tuyến": f"{quote.get('origin', '')} → {quote.get('destination', '')}",
            "Trạng thái": quote.get("status", "DRAFT"),
            "Giá báo khách (VND)": calc.get("selling_price_total_vnd", 0),
            "Lợi nhuận dự kiến (VND)": calc.get("estimated_margin_vnd", 0),
            "Liên kết lô": quote.get("shipment_id", "Chưa tạo"),
            "id": quote.get("id", ""),
        })
    if not rows:
        st.info("Chưa có báo giá phù hợp. Hãy tạo một báo giá mới từ thông tin Logistics thực tế.")
        return
    rows.sort(key=lambda item: item["Mã báo giá"], reverse=True)
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    selected = st.selectbox("Mở báo giá", [row["id"] for row in rows], format_func=lambda qid: next(row["Mã báo giá"] for row in rows if row["id"] == qid), key="quote_open_id")
    if st.button("Mở chi tiết báo giá", type="primary", key="quote_open_button"):
        st.session_state.quote_detail_id = selected
        st.rerun()


def _render_new_quote() -> None:
    st.subheader("Tiếp nhận nhu cầu báo giá")
    customers = _customer_store()
    customer_ids = list(customers)
    if not customer_ids:
        st.warning("Chưa có khách hàng trong Customer 360. Hãy tạo khách hàng trước khi báo giá.")
        return
    c1, c2, c3 = st.columns(3)
    customer_id = c1.selectbox("Khách hàng *", customer_ids, format_func=lambda cid: f"{customers[cid].get('name', cid)} ({cid})", key="new_quote_customer")
    sales_owner = c2.text_input("SALE phụ trách *", value="Thành", key="new_quote_owner")
    incoterm = c3.selectbox("Incoterm *", ["EXW", "FOB", "CIF", "DDP", "Khác"], key="new_quote_incoterm")
    c1, c2, c3 = st.columns(3)
    origin = c1.text_input("Điểm đi / nơi lấy hàng *", value="Trung Quốc", key="new_quote_origin")
    destination = c2.text_input("Điểm đến *", value="Việt Nam", key="new_quote_destination")
    route = c3.text_input("Biên giới / tuyến", value="Hữu Nghị", key="new_quote_route")
    c1, c2, c3 = st.columns(3)
    transport_mode = c1.selectbox("Phương thức", ["Road", "Sea", "Air", "Multimodal"], key="new_quote_mode")
    goods_description = c2.text_input("Mô tả hàng hóa *", key="new_quote_goods")
    expected_delivery_date = c3.date_input("Ngày khách cần giao", value=date.today(), key="new_quote_delivery")

    st.markdown("#### Nhà máy / lô hàng")
    lot_count = st.number_input("Số nhà máy/lô", min_value=1, max_value=10, value=1, step=1, key="new_quote_lot_count")
    factory_lots: list[dict[str, Any]] = []
    for index in range(int(lot_count)):
        with st.expander(f"Lô {index + 1}", expanded=True):
            a, b, c = st.columns(3)
            factory_name = a.text_input("Nhà máy / nhà cung cấp", key=f"quote_lot_{index}_name")
            factory_contact = b.text_input("Người liên hệ", key=f"quote_lot_{index}_contact")
            factory_phone = c.text_input("Điện thoại", key=f"quote_lot_{index}_phone")
            a, b, c, d = st.columns(4)
            ready_date = a.date_input("Ngày sẵn hàng", value=date.today(), key=f"quote_lot_{index}_ready")
            packages = b.number_input("Số kiện", min_value=0.0, value=0.0, key=f"quote_lot_{index}_packages")
            cbm = c.number_input("CBM", min_value=0.0, value=0.0, format="%.3f", key=f"quote_lot_{index}_cbm")
            gross_weight = d.number_input("Gross weight (kg)", min_value=0.0, value=0.0, key=f"quote_lot_{index}_weight")
            pickup_address = st.text_input("Địa chỉ lấy hàng", key=f"quote_lot_{index}_pickup")
            factory_lots.append({"lot_no": index + 1, "factory_name": factory_name, "factory_contact": factory_contact, "factory_phone": factory_phone, "ready_date": str(ready_date), "packages": packages, "cbm": cbm, "gross_weight_kg": gross_weight, "pickup_address": pickup_address})

    st.markdown("#### Dịch vụ và phương án giá")
    st.markdown(
        "<style>.lg04-quote-line { border: 2px solid #D0D7DE; border-radius: 10px; "
        "padding: .55rem .7rem .35rem; margin-bottom: .75rem; background: #FFFFFF; }</style>",
        unsafe_allow_html=True,
    )
    service_codes, service_map = _service_options()
    line_count = st.number_input("Số dòng dịch vụ", min_value=1, max_value=20, value=3, step=1, key="new_quote_line_count")
    service_lines: list[dict[str, Any]] = []
    for index in range(int(line_count)):
        st.markdown(f"<div class='lg04-quote-line'>", unsafe_allow_html=True)
        a, b, c, d, e, f = st.columns([2.4, 1, 1.2, 1.2, 1.2, 1])
        code = a.selectbox("Dịch vụ", service_codes, format_func=lambda code: f"{code} · {service_map[code].get('name', code)}", key=f"quote_line_{index}_code")
        currency = b.selectbox("Tiền tệ", ["VND", "USD", "CNY"], key=f"quote_line_{index}_currency")
        qty = c.number_input("SL / basis", min_value=0.0, value=1.0, key=f"quote_line_{index}_qty")
        cost_unit = d.number_input("Chi phí dự kiến", min_value=0.0, value=0.0, key=f"quote_line_{index}_cost")
        sell_unit = e.number_input("Giá báo khách", min_value=0.0, value=0.0, key=f"quote_line_{index}_sell")
        tax_pct = f.number_input("Thuế %", min_value=0.0, max_value=100.0, value=0.0, key=f"quote_line_{index}_tax")
        st.markdown("</div>", unsafe_allow_html=True)
        service_lines.append({"code": code, "service_name": service_map[code].get("name", code), "unit": service_map[code].get("unit", "Lần"), "qty": qty, "currency": currency, "cost_unit": cost_unit, "sell_unit": sell_unit, "tax_pct": tax_pct, "cost_source": "Nhập bởi SALE/Support; cần đối chiếu agent nếu là phí Trung Quốc."})

    # LOG-LG04: cài đặt nâng cao đưa vào 1 nhóm thu gọn (Ý 9)
    with st.expander("📐 Cài đặt nâng cao (tỷ giá, ủy thác, chuyển tiền)", expanded=False):
        st.caption("Các mục dưới dùng cho báo giá hàng hóa ngoại tệ hoặc có phí ủy thác/chuyển tiền. Lô nội địa thường không cần.")
        st.markdown("**Tỷ giá dùng để báo giá**")
        a, b, c = st.columns(3)
        usd_rate = a.number_input("USD → VND", min_value=0.0, value=25500.0, step=100.0, key="new_quote_usd_rate")
        cny_rate = b.number_input("CNY → VND", min_value=0.0, value=3500.0, step=10.0, key="new_quote_cny_rate")
        fx_source = c.text_input("Nguồn / ghi chú tỷ giá", value="Tỷ giá nhập khi báo giá; xác nhận lại trước khi gửi khách.", key="new_quote_fx_source")

        st.markdown("**Ủy thác nhập khẩu và chi phí chuyển tiền (ước tính)**")
        a, b, c, d = st.columns(4)
        entrusted_active = a.checkbox("Có phí ủy thác", key="new_quote_entrusted_active")
        goods_value = b.number_input("Giá trị hàng", min_value=0.0, value=0.0, key="new_quote_goods_value")
        goods_currency = c.selectbox("Tiền tệ giá trị hàng", ["USD", "CNY", "VND"], key="new_quote_goods_currency")
        entrusted_rate = d.number_input("Tỷ lệ phí ủy thác %", min_value=0.0, max_value=100.0, value=0.0, key="new_quote_entrusted_rate")
        review_requested = st.checkbox("Sale/manager yêu cầu review thương mại", key="new_quote_review_requested")
        review_reason = st.text_input("Lý do review (nếu có)", key="new_quote_review_reason") if review_requested else ""
        if entrusted_active:
            st.caption("Tỷ lệ do Sale nhập theo chính sách/duyệt thương mại. Review chỉ phát sinh khi tỷ lệ ngoài khoảng reference 2–3%, có cờ review explicit, hoặc một policy high-value được cấu hình; hiện không cấu hình ngưỡng high-value.")
        a, b, c, d, e = st.columns(5)
        remittance_amount = a.number_input("Số tiền chuyển USD", min_value=0.0, value=0.0, key="new_quote_remit_amount")
        bank_pct = b.number_input("Phí ngân hàng %", min_value=0.0, value=0.2, key="new_quote_bank_pct")
        swift = c.number_input("SWIFT USD", min_value=0.0, value=5.0, key="new_quote_swift")
        receiving = d.number_input("Receiving USD", min_value=0.0, value=0.0, key="new_quote_receiving")
        agent_fee = e.number_input("Agent conversion USD", min_value=0.0, value=0.0, key="new_quote_agent_fee")
        rmb_fee = st.number_input("RMB conversion fee CNY", min_value=0.0, value=0.0, key="new_quote_rmb_fee")
        include_remittance = st.checkbox("Tính chi phí chuyển tiền vào chi phí dự kiến", key="new_quote_include_remittance")

    if st.button(
        "Tính phương án và lưu báo giá nháp",
        type="primary",
        key="new_quote_save",
        disabled=not can_operate_business("sales_write"),
    ):
        if not sales_owner.strip() or not origin.strip() or not destination.strip() or not goods_description.strip():
            st.error("Vui lòng nhập đủ SALE, điểm đi, điểm đến và mô tả hàng hóa.")
            return
        if not any(float(line["cost_unit"]) or float(line["sell_unit"]) for line in service_lines):
            st.error("Cần có ít nhất một dòng dịch vụ có chi phí hoặc giá báo khách.")
            return
        payload = {
            "customer_id": customer_id, "customer_name": customers[customer_id].get("name", customer_id), "sales_owner": sales_owner.strip(), "origin": origin.strip(), "destination": destination.strip(), "route": route.strip(), "incoterm": incoterm, "transport_mode": transport_mode, "goods_description": goods_description.strip(), "expected_delivery_date": str(expected_delivery_date), "factory_lots": factory_lots, "service_lines": service_lines,
            "fx_snapshot": {"rates_to_vnd": {"USD": usd_rate, "CNY": cny_rate, "VND": 1}, "source": fx_source},
            "entrusted_import": {"active": entrusted_active, "goods_value": goods_value, "goods_currency": goods_currency, "rate_pct": entrusted_rate, "review_requested": review_requested, "review_reason": review_reason, "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"}, "source": "Nhập theo chính sách/duyệt thương mại; không phải bút toán tài chính."},
            "remittance_estimate": {"remitted_amount_usd": remittance_amount, "bank_fee_pct": bank_pct, "swift_fee_usd": swift, "receiving_bank_fee_usd": receiving, "agent_conversion_fee_usd": agent_fee, "rmb_conversion_fee_cny": rmb_fee}, "include_remittance_in_cost": include_remittance,
            "assumptions": ["Đây là estimate/quotation, chưa phải nghĩa vụ thanh toán.", "Giá agent/đối tác phải được đối chiếu với nguồn báo giá thực tế.", "Không tự động hóa khai báo hải quan sai lệch."],
        }
        try:
            quote = new_quote_document(payload)
        except ValueError as exc:
            st.error(str(exc)); return
        if _persist_quote(quote):
            st.success(f"Đã lưu {quote['quote_no']} ở trạng thái DRAFT. Mở tab Chi tiết để kiểm tra Vì sao ra giá này?.")
            st.rerun()
        st.error(st.session_state.get("last_db_error") or "Không lưu được báo giá vào database.")


def _render_quote_detail() -> None:
    quotes = _quote_store(); quote_id = st.session_state.get("quote_detail_id")
    if not quote_id or quote_id not in quotes:
        st.info("Chọn một báo giá từ danh sách để xem chi tiết.")
        return
    quote = quotes[quote_id]
    calc = quote.get("calculation", {})
    st.subheader(f"{quote.get('quote_no', quote_id)} · {quote.get('customer_name', '')}")
    st.caption(f"Trạng thái: {quote.get('status')} · Phiên bản: {quote.get('version', 1)} · Đây là estimate, chưa ghi Finance Ledger.")
    a, b, c, d = st.columns(4)
    a.metric("Giá báo khách", f"{calc.get('selling_price_total_vnd', 0):,.0f} VND")
    b.metric("Chi phí dự kiến", f"{calc.get('estimated_cost_vnd', 0):,.0f} VND")
    c.metric("Lợi nhuận dự kiến", f"{calc.get('estimated_margin_vnd', 0):,.0f} VND")
    d.metric("Biên lợi nhuận", f"{calc.get('estimated_margin_pct', 0):,.1f}%")
    with st.expander("Vì sao ra giá này?", expanded=True):
        st.write("Tổng báo giá được quy đổi về VND theo snapshot tỷ giá của quotation; tỷ giá này không thay thế tỷ giá giao dịch thực tế.")
        st.dataframe(pd.DataFrame(quote.get("service_lines", [])), use_container_width=True, hide_index=True)
        st.json({"calculation": calc, "fees": quote.get("fees", {}), "fx_snapshot": quote.get("fx_snapshot", {}), "assumptions": quote.get("assumptions", [])})
    with st.expander("Nhà máy / lô và thông tin Logistics", expanded=True):
        st.dataframe(pd.DataFrame(quote.get("factory_lots", [])), use_container_width=True, hide_index=True)
        st.write({"origin": quote.get("origin"), "destination": quote.get("destination"), "incoterm": quote.get("incoterm"), "route": quote.get("route"), "goods": quote.get("goods_description")})
    if quote.get("fees", {}).get("entrusted_import", {}).get("commercial_review_required"):
        st.warning("Phí ủy thác đang cần review thương mại do giá trị cao hoặc tỷ lệ ngoài khoảng thông thường.")

    current = quote.get("status", "DRAFT")
    actions: list[tuple[str, str]] = []
    if current == "DRAFT": actions.append(("Chuyển sang chờ review", "READY_FOR_REVIEW"))
    if current == "READY_FOR_REVIEW": actions.extend([("Đã gửi khách", "SENT"), ("Khách chốt", "ACCEPTED")])
    if current == "SENT": actions.append(("Khách chốt", "ACCEPTED"))
    if current == "ACCEPTED": actions.append(("Sẵn sàng tạo lô", "READY_TO_CREATE_SHIPMENT"))
    if actions:
        cols = st.columns(len(actions))
        for col, (label, target) in zip(cols, actions):
            if col.button(label, key=f"quote_transition_{target}", disabled=not can_operate_business("sales_write")):
                if not can_operate_business("sales_write"):
                    st.warning("Bạn không có quyền thay đổi báo giá.")
                    continue
                try:
                    updated = transition_quote(quote, target, actor=str(st.session_state.get("current_user", {}).get("username", "SALE")))
                except ValueError as exc:
                    st.error(str(exc)); continue
                if _persist_quote(updated): st.rerun()
    if current == "READY_TO_CREATE_SHIPMENT":
        _render_create_shipment(quote)
    st.markdown("#### Lịch sử trạng thái")
    st.dataframe(pd.DataFrame(quote.get("status_history", [])), use_container_width=True, hide_index=True)


def _render_create_shipment(quote: dict[str, Any]) -> None:
    st.markdown("#### Chuyển báo giá đã chấp nhận sang shipment draft")
    if quote.get("shipment_id"):
        st.success(f"Đã liên kết shipment {quote['shipment_id']}. Retry sẽ không tạo thêm lô.")
        return
    st.info("Hành động này chỉ tạo shipment draft, giữ quote reference và không ghi sổ tài chính.")
    if not st.button("Tạo / prefill shipment draft", type="primary", key="quote_create_shipment", disabled=not can_operate_business("sales_write")):
        return
    if not can_operate_business("sales_write"):
        st.warning("Bạn không có quyền thay đổi báo giá.")
        return
    shipments = st.session_state.get("db_shipments", {})
    existing = next((item for item in shipments.values() if item.get("quote_id") == quote.get("id") or item.get("quote_reference") == quote.get("quote_no")), None)
    if existing:
        quote["shipment_id"] = existing.get("id") or existing.get("shipment_id")
        _persist_quote(quote); st.rerun()
    shipment_id = generate_shipment_id("SHP")
    draft = build_shipment_draft(quote, shipment_id)
    validation = validate_shipment(draft)
    if not validation.is_valid:
        st.error(validation.message); return
    if save_shipment_atomic(draft):
        st.session_state.setdefault("db_shipments", {})[shipment_id] = draft
        quote["shipment_id"] = shipment_id; quote["shipment_created_at"] = str(date.today())
        if _persist_quote(quote):
            st.success(f"Đã tạo shipment draft {shipment_id}; quote reference được giữ lại.")
            st.rerun()
    st.error(st.session_state.get("last_db_error") or "Không tạo được shipment draft.")


def ui_sales_module() -> None:
    st.title("Sales & Báo giá Logistics")
    st.caption("Khách hỏi giá → thu thập thông tin → tính phương án → báo giá → khách chốt → tạo lô. Giá hiển thị là estimate, không phải Finance Ledger.")
    quotes = _quote_store()
    tabs = st.tabs(["Danh sách báo giá", "Báo giá mới", "Chi tiết", "Báo giá khung cũ"])
    with tabs[0]: _render_quote_table(quotes)
    with tabs[1]: _render_new_quote()
    with tabs[2]: _render_quote_detail()
    with tabs[3]:
        st.caption("Giữ nguyên màn hình báo giá khung hiện hữu để không mất dữ liệu lịch sử.")
        ui_legacy_sales_module()
