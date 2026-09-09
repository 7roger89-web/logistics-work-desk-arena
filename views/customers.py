# FILE: views/customers.py
import streamlit as st
import pandas as pd
from core.database import load_customers, save_customer_to_cloud, delete_customer
from core.auth import can_operate_business, has_permission
from views import ui_kit


def _customer_detail(customer: dict, customers: dict) -> None:
    """Donor-style customer detail (read-only groups built from REAL session data).

    THÔNG TIN CHÍNH · LIÊN HỆ · LÔ HÀNG · BÁO GIÁ · HỢP ĐỒNG · CÔNG NỢ · GHI CHÚ.
    Editing stays in the table below; this view only reads and navigates."""
    from core.entity_context import build_customer_context
    from core.payment_logic import get_customer_debt_overview
    from core.utils import safe_float

    cid = str(customer.get("id") or "")
    name = str(customer.get("name") or cid)
    shipments = st.session_state.get("db_shipments", {}) or {}
    quotes = st.session_state.get("db_quotes") or {}
    agreements = st.session_state.get("db_agreements") or {}
    contracts = st.session_state.get("db_contracts") or {}
    view = build_customer_context(cid, customer, shipments, quotes=quotes, agreements=agreements)
    total_debt, total_receivable, debt_rows = get_customer_debt_overview(cid, shipments)
    if not debt_rows:
        total_debt, total_receivable, debt_rows = get_customer_debt_overview(name, shipments)
    linked_contracts = [
        item for item in contracts.values()
        if isinstance(item, dict) and str(item.get("client") or "").strip().lower() == name.strip().lower()
    ]

    missing = [g for g in (view.get("gaps") or []) if g in {"contact", "email", "address"}]
    with st.container(border=True):
        ui_kit.row_head(
            name,
            f"Mã KH: {cid} · Người liên hệ: {customer.get('contact_person') or 'Chưa có'}",
            badge_items=[
                (f"{len(view.get('active_shipments') or [])} lô đang chạy", "info", "local_shipping"),
                (f"{len(view.get('attention_shipments') or [])} lô cần chú ý", "warn" if view.get("attention_shipments") else "neutral", "warning"),
                (f"Còn nợ {safe_float(total_debt):,.0f} VNĐ", "danger" if safe_float(total_debt) > 0 else "ok", "payments"),
            ],
        )
        if missing:
            labels = {"contact": "người liên hệ / điện thoại", "email": "email", "address": "địa chỉ"}
            ui_kit.callout(
                "Thiếu " + ", ".join(labels[g] for g in missing) + " — bổ sung ngay trong bảng khách hàng bên dưới (cột tương ứng) rồi bấm LƯU THAY ĐỔI.",
                "warn", title="Bổ sung thông tin",
            )

        g1, g2 = st.columns(2)
        with g1:
            ui_kit.section("THÔNG TIN CHÍNH")
            ui_kit.kv_grid([
                ("Tên khách hàng", name),
                ("Mã khách hàng", cid),
                ("Mã số thuế", customer.get("tax_code")),
                ("Địa chỉ", customer.get("address")),
            ])
        with g2:
            ui_kit.section("LIÊN HỆ")
            ui_kit.kv_grid([
                ("Người liên hệ", customer.get("contact_person")),
                ("Điện thoại", customer.get("phone")),
                ("Email", customer.get("email")),
            ])

        ui_kit.section("LÔ HÀNG", f"{len(view.get('shipments') or [])} lô liên quan · mở lô để làm việc trong Lô Hàng")
        ship_rows = list(view.get("shipments") or [])
        if ship_rows:
            ui_kit.data_table(
                [("shipment_id", "Mã lô", "strong"), ("status", "Trạng thái"), ("required_date", "Hạn khách"), ("planned_date", "Kế hoạch"), ("attention", "Cần chú ý")],
                [{k: row.get(k) for k in ("shipment_id", "status", "required_date", "planned_date", "attention")} for row in ship_rows[:12]],
            )
            open_cols = st.columns(min(4, len(ship_rows[:4])))
            for idx, row in enumerate(ship_rows[:4]):
                sid = str(row.get("shipment_id") or "")
                if open_cols[idx].button(f"Mở {sid}", key=f"customer_detail_open_{cid}_{sid}", icon=":material/arrow_forward:", use_container_width=True):
                    st.session_state.active_page = "Tổng Quan Công Việc"
                    st.session_state.active_shipment_id = sid
                    st.session_state.dashboard_active_shipment_id = sid
                    st.rerun()
        else:
            ui_kit.empty_state("Chưa có lô hàng nào gắn với khách hàng này.")

        q1, q2 = st.columns(2)
        with q1:
            ui_kit.section("BÁO GIÁ / DỰ KIẾN", "số dự kiến từ Kinh Doanh & Báo Giá — không phải số thực thu")
            quote_rows = list(view.get("quotations") or [])
            if quote_rows:
                ui_kit.data_table(
                    [("quote_id", "Báo giá", "strong"), ("status", "Trạng thái"), ("route", "Tuyến"), ("total", "Giá bán dự kiến", "num")],
                    [
                        {
                            "quote_id": r.get("quote_reference") if r.get("quote_reference") not in (None, "", "UNKNOWN") else r.get("quote_id"),
                            "status": r.get("status_code"),
                            "route": r.get("route"),
                            "total": safe_float(r.get("price_snapshot_vnd", 0)),
                        }
                        for r in quote_rows[:8]
                    ],
                    money_currency="VNĐ",
                )
            else:
                ui_kit.empty_state("Chưa có báo giá cho khách hàng này.")
        with q2:
            ui_kit.section("HỢP ĐỒNG", f"{len(linked_contracts)} hợp đồng theo tên đối tác")
            if linked_contracts:
                for item in linked_contracts[:6]:
                    contract_id = str(item.get("id") or item.get("contract_no") or "")
                    c_a, c_b = st.columns([3, 1.3], vertical_alignment="center")
                    c_a.markdown(f"**{item.get('contract_no') or contract_id}** · {ui_kit.money(item.get('value', 0), item.get('currency', 'VND'))}")
                    if c_b.button("Mở", key=f"customer_detail_contract_{cid}_{contract_id}", icon=":material/description:", use_container_width=True):
                        st.session_state.active_page = "Hợp Đồng"
                        st.session_state.selected_contract_v2 = contract_id
                        st.rerun()
            else:
                ui_kit.empty_state("Chưa có hợp đồng nào cho khách hàng này.")

        ui_kit.section("CÔNG NỢ", "số thực tế từ lô hàng · ghi nhận thanh toán tại Thu Tiền & Công Nợ")
        ui_kit.summary_cards([
            {"label": "Tổng phải thu", "value": f"{safe_float(total_receivable):,.0f} VNĐ", "icon": "request_quote"},
            {"label": "Còn nợ", "value": f"{safe_float(total_debt):,.0f} VNĐ", "icon": "error", "tone": "danger" if safe_float(total_debt) > 0 else "ok"},
            {"label": "Lô có công nợ", "value": len(debt_rows), "icon": "local_shipping"},
        ])
        if has_permission("receivables") and st.button("Ghi nhận thanh toán", key=f"customer_detail_receivables_{cid}", icon=":material/payments:"):
            st.session_state.active_page = "Thu Tiền & Công Nợ"
            st.rerun()

        ui_kit.section("GHI CHÚ")
        st.write(customer.get("note") or "—")

        if st.button("XEM NGỮ CẢNH KHÁCH HÀNG 360°", key=f"customer_detail_context_{cid}", icon=":material/hub:"):
            from views.entity_context import open_entity_context

            open_entity_context("customer", cid, return_page="Khách Hàng")


def ui_customers():
    ui_kit.page_header(
        "👥 QUẢN LÝ KHÁCH HÀNG",
        "Quản lý danh sách, thông tin liên hệ và đối tác của công ty.",
        kicker="KINH DOANH & ĐỐI TÁC",
        native_title=True,
    )

    if "db_customers" not in st.session_state:
        st.session_state.db_customers = load_customers()
    db_customers = st.session_state.db_customers
    can_edit = can_operate_business("customers")

    shipments_all = st.session_state.get("db_shipments", {}) or {}
    ui_kit.summary_cards([
        {"label": "Khách hàng", "value": len(db_customers), "icon": "group"},
        {"label": "Thiếu liên hệ", "value": sum(1 for c in db_customers.values() if not (c.get("phone") or c.get("contact_person"))), "icon": "contact_phone", "tone": "warn" if any(not (c.get("phone") or c.get("contact_person")) for c in db_customers.values()) else "neutral", "hint": "chưa có điện thoại / người liên hệ"},
        {"label": "Thiếu MST", "value": sum(1 for c in db_customers.values() if not c.get("tax_code")), "icon": "badge", "tone": "neutral"},
        {"label": "Lô hàng trong hệ thống", "value": len(shipments_all), "icon": "local_shipping"},
    ])

    # ==========================================
    # 1. TÍNH NĂNG IMPORT TỪ EXCEL/CSV (MỚI)
    # ==========================================
    with st.expander("📥 NHẬP DANH SÁCH KHÁCH HÀNG TỪ EXCEL (IMPORT)", expanded=False):
        st.info("💡 Hệ thống sẽ đọc cột **Mã KH** để nhận diện. Nếu Mã KH đã tồn tại trong phần mềm, hệ thống sẽ **Bỏ qua (không ghi đè)** để bảo vệ dữ liệu cũ.")
        
        uploaded_file = st.file_uploader("Tải lên file Excel/CSV danh sách khách hàng", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            try:
                # Đọc file tự động phân biệt định dạng
                if uploaded_file.name.endswith('.csv'):
                    df_cust = pd.read_csv(uploaded_file, dtype=str)
                else:
                    df_cust = pd.read_excel(uploaded_file, dtype=str)
                
                df_cust.columns = df_cust.columns.str.strip() # Dọn dẹp tên cột
                
                # Hiển thị Preview
                st.markdown("**Bản xem trước dữ liệu:**")
                st.dataframe(df_cust.head(5), use_container_width=True)

                if st.button("🚀 XÁC NHẬN IMPORT VÀO HỆ THỐNG", type="primary", disabled=not can_edit):
                    success_count = 0
                    skip_count = 0
                    
                    for _, row in df_cust.iterrows():
                        # Hút dữ liệu từ các cột linh hoạt
                        ma_kh = str(row.get('Mã KH', row.get('Mã khách hàng', row.get('Mã', '')))).strip()
                        ten_kh = str(row.get('Tên khách hàng', row.get('Tên KH', row.get('Tên', '')))).strip()
                        
                        if not ma_kh or ma_kh.lower() == 'nan':
                            continue # Bỏ qua dòng trống
                            
                        # KIỂM TRA TRÙNG LẶP: Nếu mã đã có trong DB -> Bỏ qua
                        if ma_kh in db_customers:
                            skip_count += 1
                            continue
                            
                        # Đóng gói dữ liệu mới
                        new_cust = {
                            "id": ma_kh,
                            "name": ten_kh,
                            "phone": str(row.get('Điện thoại', str(row.get('Số ĐT', '')))).replace('nan',''),
                            "email": str(row.get('Email', '')).replace('nan',''),
                            "contact_person": str(row.get('Người liên hệ chính', '')).replace('nan',''),
                            "note": str(row.get('Mô tả', '')).replace('nan',''),
                            "tax_code": str(row.get('Mã số thuế', '')).replace('nan',''),
                            "address": str(row.get('Địa chỉ', str(row.get('Địa chỉ giao hàng', '')))).replace('nan','')
                        }
                        
                        if save_customer_to_cloud(new_cust):
                            db_customers[ma_kh] = new_cust
                            success_count += 1
                        
                    st.success(f"🎉 Import hoàn tất! Đã thêm **{success_count}** khách hàng mới. Bỏ qua **{skip_count}** khách hàng đã tồn tại.")
                    st.session_state.needs_refresh = True
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: Vui lòng kiểm tra lại định dạng file. Chi tiết lỗi: {e}")

    with st.expander("➕ THÊM KHÁCH HÀNG MỚI", expanded=False):
        with st.form("new_customer_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Mã khách hàng").strip().upper()
            new_name = c2.text_input("Tên khách hàng").strip()
            c3, c4, c5 = st.columns(3)
            new_phone = c3.text_input("Điện thoại").strip()
            new_email = c4.text_input("Email").strip()
            new_tax_code = c5.text_input("Mã số thuế").strip()
            new_address = st.text_input("Địa chỉ").strip()
            if st.form_submit_button("Lưu khách hàng", type="primary", disabled=not can_edit):
                if not new_id or not new_name:
                    st.error("Mã và tên khách hàng là bắt buộc.")
                elif new_id in db_customers:
                    st.error("Mã khách hàng đã tồn tại.")
                else:
                    payload = {
                        "id": new_id,
                        "name": new_name,
                        "phone": new_phone,
                        "email": new_email,
                        "tax_code": new_tax_code,
                        "address": new_address,
                        "contact_person": "",
                        "note": "",
                    }
                    if save_customer_to_cloud(payload):
                        db_customers[new_id] = payload
                        st.session_state.needs_refresh = True
                        st.success("Đã thêm khách hàng.")
                        st.rerun()
                    else:
                        st.error(st.session_state.get("last_db_error") or "Không lưu được khách hàng.")

    st.divider()

    # ==========================================
    # 2. HIỂN THỊ DANH SÁCH & CHỈNH SỬA
    # ==========================================
    if db_customers:
        # ------------------------------------------------------------------
        # Donor UX: pick a customer → detail card with grouped information
        # ------------------------------------------------------------------
        ui_kit.section("HỒ SƠ KHÁCH HÀNG", "chọn khách hàng để xem lô hàng, báo giá, hợp đồng và công nợ liên quan")
        s1, s2 = st.columns([2.2, 1])
        search = s1.text_input("🔍 Tìm khách hàng", key="customer_search_box", placeholder="Tên, mã KH, người liên hệ, MST…")
        needle = str(search or "").strip().lower()
        matching_ids = [
            cid for cid, c in db_customers.items()
            if not needle or needle in " ".join(str(c.get(k) or "") for k in ("id", "name", "contact_person", "tax_code", "phone", "email")).lower()
        ]
        if matching_ids:
            picked = s2.selectbox(
                "Khách hàng",
                matching_ids,
                format_func=lambda cid: f"{db_customers.get(cid, {}).get('name', cid)} ({cid})",
                key="customer_detail_pick",
            )
            _customer_detail(db_customers[picked], db_customers)
        else:
            ui_kit.empty_state("Không tìm thấy khách hàng phù hợp.", "Thử tìm theo mã KH hoặc tên.")

        df_display = pd.DataFrame(db_customers.values())
        
        ui_kit.section("DANH SÁCH & CHỈNH SỬA", f"tổng số khách hàng: {len(df_display)} · sửa trực tiếp trong bảng rồi bấm LƯU THAY ĐỔI")
        
        # Bảng dữ liệu có thể chỉnh sửa
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("Mã KH", required=True, disabled=True),
                "name": st.column_config.TextColumn("Tên Khách Hàng", required=True),
                "phone": "Điện thoại",
                "email": "Email",
                "contact_person": "Người liên hệ",
                "tax_code": "Mã số thuế",
                "address": "Địa chỉ",
                "note": "Ghi chú"
            }
        )

        if st.button("💾 LƯU THAY ĐỔI KHÁCH HÀNG", type="primary", disabled=not can_edit):
            errors = []
            for _, row in edited_df.iterrows():
                cid = str(row.get("id", "")).strip()
                name = str(row.get("name", "")).strip()
                if not cid or not name:
                    errors.append(f"Dòng mã {cid or '(trống)'} thiếu tên khách hàng.")
                    continue
                payload = row.to_dict()
                payload["id"] = cid
                payload["name"] = name
                if not save_customer_to_cloud(payload):
                    errors.append(f"Không lưu được {cid}.")
            if errors:
                st.error("\n".join(errors))
            else:
                st.session_state.needs_refresh = True
                st.success("✅ Cập nhật dữ liệu thành công!")
                st.rerun()

        with st.expander("🗃️ Đưa khách hàng vào lưu trữ"):
            delete_id = st.selectbox(
                "Khách hàng",
                list(db_customers.keys()),
                format_func=lambda cid: f"{cid} - {db_customers.get(cid, {}).get('name', '')}",
                key="customer_delete_id",
            )
            delete_reason = st.text_input("Lý do", key="customer_delete_reason")
            if st.button(
                "Xác nhận lưu trữ",
                type="secondary",
                disabled=not has_permission("customer_delete") or not delete_reason.strip(),
                key="customer_delete_button",
            ):
                if delete_customer(delete_id, reason=delete_reason.strip()):
                    db_customers.pop(delete_id, None)
                    st.session_state.needs_refresh = True
                    st.success("Đã đưa khách hàng vào lưu trữ.")
                    st.rerun()
                else:
                    st.error("Không thể lưu trữ khách hàng.")
    else:
        st.info("Chưa có dữ liệu khách hàng. Vui lòng tải file Excel lên!")
