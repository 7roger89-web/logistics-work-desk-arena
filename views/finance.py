from __future__ import annotations

from datetime import date
from uuid import uuid4

import pandas as pd
import streamlit as st

from core.auth import can_operate_business
from core.payment_logic import allocate_lump_sum, apply_lump_sum_payment, get_customer_debt_overview
from core.utils import safe_float
from views.partner_finance import render_partner_financial_position


def ui_receivables_management():
    st.title("💰 THU TIỀN & PHÂN BỔ CÔNG NỢ")
    st.caption("Phân bổ khoản thu theo FIFO vào các lô cũ nhất; mỗi lần ghi có khóa chống ghi trùng.")

    render_partner_financial_position()
    st.divider()

    customers = st.session_state.get("db_customers", {})
    shipments = st.session_state.get("db_shipments", {})
    if not customers:
        st.info("Chưa có dữ liệu khách hàng.")
        return

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

    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng phải thu", f"{total_receivable:,.0f} VNĐ")
    m2.metric("Còn nợ", f"{total_debt:,.0f} VNĐ")
    m3.metric("Số lô", len(rows))

    if rows:
        display = pd.DataFrame([{k: value for k, value in row.items() if k != "original_data"} for row in rows])
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "Mã lô",
                "created_at": "Ngày tạo",
                "revenue": st.column_config.NumberColumn("Phải thu", format="%.0f VNĐ"),
                "paid": st.column_config.NumberColumn("Đã thu", format="%.0f VNĐ"),
                "debt": st.column_config.NumberColumn("Còn nợ", format="%.0f VNĐ"),
                "last_payment": "Thu gần nhất",
                "status": "Trạng thái",
            },
        )

    st.divider()
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

    if st.button(
        "Xác nhận ghi khoản thu",
        type="primary",
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
