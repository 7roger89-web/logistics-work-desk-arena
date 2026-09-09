from __future__ import annotations

from datetime import date
from uuid import uuid4

import pandas as pd
import streamlit as st

from core.auth import can_operate_business
from core.payment_logic import allocate_lump_sum, apply_lump_sum_payment, get_customer_debt_overview
from core.utils import safe_float
from views.partner_finance import render_partner_financial_position
from views import ui_kit


def _receivable_status_tone(status: object) -> str:
    text = str(status or "")
    if "Đủ" in text or "✅" in text:
        return "ok"
    if "Nợ" in text or "❌" in text:
        return "danger"
    return "neutral"


def ui_receivables_management():
    ui_kit.page_header(
        "💰 THU TIỀN & PHÂN BỔ CÔNG NỢ",
        "Phân bổ khoản thu theo FIFO vào các lô cũ nhất; mỗi lần ghi có khóa chống ghi trùng.",
        kicker="TÀI CHÍNH & ĐỐI SOÁT · SỐ THỰC TẾ",
        native_title=True,
    )

    with st.expander("Vị trí tài chính đối tác (A Bò) — projection chỉ đọc", expanded=False, icon=":material/handshake:"):
        render_partner_financial_position()

    customers = st.session_state.get("db_customers", {})
    shipments = st.session_state.get("db_shipments", {})
    if not customers:
        ui_kit.empty_state("Chưa có dữ liệu khách hàng.", "Tạo khách hàng ở mục Khách Hàng trước khi ghi nhận khoản thu.")
        return

    ui_kit.section("CÔNG NỢ THEO KHÁCH HÀNG", "chọn khách hàng để xem các lô còn nợ và ghi nhận thanh toán")
    customer_ids = list(customers.keys())
    customer_id = st.selectbox(
        "Khách hàng",
        customer_ids,
        format_func=lambda cid: customers.get(cid, {}).get("name", cid),
    )
    customer_name = customers.get(customer_id, {}).get("name", customer_id)
    allocation_customer_ref = customer_id
    total_debt, total_receivable, rows = get_customer_debt_overview(allocation_customer_ref, shipments)
    if not rows:
        # Dữ liệu cũ có thể chưa có customer_id; fallback theo tên.
        allocation_customer_ref = customer_name
        total_debt, total_receivable, rows = get_customer_debt_overview(allocation_customer_ref, shipments)

    total_paid = sum(safe_float(row.get("paid", 0)) for row in rows)
    overdue_rows = [row for row in rows if _receivable_status_tone(row.get("status")) == "danger"]
    ui_kit.summary_cards([
        {"label": "Tổng phải thu", "value": f"{total_receivable:,.0f} VNĐ", "icon": "request_quote"},
        {"label": "Đã thu", "value": f"{total_paid:,.0f} VNĐ", "icon": "task_alt", "tone": "ok" if total_paid else "neutral"},
        {"label": "Còn nợ", "value": f"{total_debt:,.0f} VNĐ", "icon": "error", "tone": "danger" if safe_float(total_debt) > 0 else "ok"},
        {"label": "Lô còn nợ", "value": f"{len(overdue_rows)} / {len(rows)}", "icon": "local_shipping", "tone": "warn" if overdue_rows else "neutral", "hint": "số lô đang theo dõi"},
    ])

    if rows:
        display_rows = [
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "revenue": safe_float(row.get("revenue", 0)),
                "paid": safe_float(row.get("paid", 0)),
                "debt": safe_float(row.get("debt", 0)),
                "last_payment": row.get("last_payment"),
                "status": ui_kit.badge(row.get("status") or "—", _receivable_status_tone(row.get("status"))),
            }
            for row in rows
        ]
        ui_kit.data_table(
            [
                ("id", "Mã lô"),
                ("created_at", "Ngày tạo"),
                ("revenue", "Phải thu", "num"),
                ("paid", "Đã thu", "num"),
                ("debt", "Còn nợ", "num"),
                ("last_payment", "Thu gần nhất"),
                ("status", "Trạng thái", "html"),
            ],
            display_rows,
            money_currency="VNĐ",
        )
    else:
        ui_kit.empty_state("Khách hàng này chưa có lô nào phát sinh công nợ.", "Số liệu đọc từ lô hàng thật; không có dữ liệu mẫu.")

    st.divider()
    ui_kit.section("GHI NHẬN THANH TOÁN", "khoản thu tổng được phân bổ FIFO vào các lô cũ nhất còn nợ")
    st.subheader("Ghi nhận khoản thu tổng")
    st.session_state.setdefault("receipt_idempotency_key", str(uuid4()))
    c1, c2 = st.columns(2)
    amount = c1.number_input("Số tiền nhận (VNĐ)", min_value=0.0, step=100_000.0, format="%.0f")
    payment_date = c2.date_input("Ngày nhận", value=date.today())
    note = st.text_input("Nội dung", placeholder="VD: KH thanh toán công nợ tháng 07/2026")

    plan, remaining = allocate_lump_sum(amount, rows)
    if amount > 0:
        if plan:
            st.markdown("#### Phương án phân bổ FIFO")
            st.dataframe(
                pd.DataFrame([{k: v for k, v in item.items() if k != "original_data"} for item in plan]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "shipment_id": "Mã lô",
                    "pay_amount": st.column_config.NumberColumn("Phân bổ", format="%.0f VNĐ"),
                    "remaining_debt": st.column_config.NumberColumn("Nợ sau thu", format="%.0f VNĐ"),
                },
            )
            if remaining > 0:
                st.info(f"Tiền chưa phân bổ: {remaining:,.0f} VNĐ")
        else:
            st.warning("Không có lô còn nợ để phân bổ.")

    if amount <= 0:
        ui_kit.callout("Nhập số tiền nhận để xem phương án phân bổ trước khi ghi nhận.", "info")
    if st.button(
        "Xác nhận ghi khoản thu",
        type="primary",
        icon=":material/payments:",
        use_container_width=True,
        disabled=amount <= 0 or not plan or not can_operate_business("finance_write"),
    ):
        if not can_operate_business("finance_write"):
            st.warning("Bạn không có quyền ghi nhận khoản thu tài chính.")
            return
        user = st.session_state.get("current_user", {})
        ok, allocations, leftover, message = apply_lump_sum_payment(
            customer_ref=allocation_customer_ref,
            amount=amount,
            all_shipments=shipments,
            payment_date=str(payment_date),
            note=note.strip(),
            idempotency_key=st.session_state.receipt_idempotency_key,
            actor=user.get("username", "system"),
        )
        if ok:
            st.success(message)
            if leftover > 0:
                st.info(f"Còn {leftover:,.0f} VNĐ chưa phân bổ.")
            st.session_state.receipt_idempotency_key = str(uuid4())
            st.session_state.needs_refresh = True
            st.rerun()
        st.error(message)


def ui_invoice_screen():
    sid = st.session_state.get("invoice_sid")
    if sid:
        st.session_state.active_shipment_id = sid
        st.info("Đã chuyển lô sang màn chi tiết Shipment để chỉnh sửa tài chính.")
        st.rerun()
    st.error("Chưa chọn lô hàng.")
