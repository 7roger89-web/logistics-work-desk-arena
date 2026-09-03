# FILE: views/proxy_payment.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from uuid import uuid4
import calendar
from core.database import load_customers, load_data, load_contracts, load_proxy_payments, save_proxy_payment, delete_proxy_payment
from core.utils import safe_float, parse_date_optional
from core.auth import can_operate_business, has_permission

# --- GIAO DIỆN CHÍNH ---
def ui_proxy_payment_management():
    st.title("💸 QUẢN LÝ THANH TOÁN HỘ / ỦY THÁC TIỀN TỆ")
    st.caption("Phân hệ chuyên quản lý dòng tiền Khách gửi VNĐ -> Đổi Tỷ giá -> Chuyển Tệ (CNY)/USD cho Nhà máy.")

    # Tải dữ liệu vào bộ nhớ tạm
    if 'db_proxy' not in st.session_state: st.session_state.db_proxy = load_proxy_payments()
    if 'db_customers' not in st.session_state: st.session_state.db_customers = load_customers()
    if 'db_shipments' not in st.session_state: st.session_state.db_shipments = load_data()
    if 'db_contracts' not in st.session_state: st.session_state.db_contracts = load_contracts()

    t_new, t_list = st.tabs(["➕ TẠO/SỬA GIAO DỊCH", "📊 BỨC TRANH TỔNG THỂ & DANH SÁCH"])

    with t_new:
        with st.container(border=True):
            st.subheader("1. Thông tin dòng tiền nhận từ Khách")
            
            # HÀNG 1: MÃ GD + NGÀY + KHÁCH HÀNG (CÓ THỂ GÕ TAY)
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 2, 2])
            p_id_default = f"TT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:4].upper()}"
            
            # 🔥 ĐÃ SỬA 1: Mã GD cho phép nhập liệu, và ghi chú cách cập nhật dữ liệu
            p_id = c1.text_input("Mã GD (Cho phép sửa)", value=p_id_default, help="Mẹo: Để sửa giao dịch cũ, hãy nhập lại đúng Mã GD đó và bấm Lưu.")
            p_date = c2.date_input("Ngày Giao Dịch", date.today())
            
            # 🔥 ĐÃ SỬA 2: Vừa cho phép Chọn khách, Vừa cho phép Gõ tay người chuyển tiền tạm
            customer_options = [""] + list(st.session_state.db_customers.keys())
            selected_customer_id = c3.selectbox(
                "1. Khách hàng (Có sẵn)",
                customer_options,
                format_func=lambda cid: "--Chọn Khách Có Sẵn--" if not cid else st.session_state.db_customers.get(cid, {}).get("name", cid),
            )
            txt_cust = c4.text_input("2. Hoặc ghi tạm tên người gửi:", placeholder="VD: Cô Lan Kế toán...")

            selected_customer_name = st.session_state.db_customers.get(selected_customer_id, {}).get("name", "")
            # Ưu tiên tên nhập tay cho giao dịch vãng lai; vẫn lưu customer_id khi chọn master data.
            p_cust = txt_cust.strip() or selected_customer_name

            # HÀNG 2: TIỀN VÀ TỶ GIÁ
            c5, c6, c7 = st.columns(3)
            p_vnd = c5.number_input("Số tiền đã nhận từ khách (VNĐ)", min_value=0.0, step=100000.0, format="%.0f")
            p_rate = c6.number_input("Tỷ giá báo khách", min_value=0.0, step=1.0, format="%.0f", help="Tỷ giá chốt với khách (Đã bao gồm lợi nhuận)")
            p_curr = c7.selectbox("Loại Ngoại Tệ", ["CNY (¥)", "USD ($)", "EUR (€)", "JPY (¥)"])
            curr_sym = p_curr.split(" ")[1].replace("(","").replace(")","")
            
            st.markdown("---")
            st.subheader("2. Thông tin thực tế chuyển khoản ra nước ngoài")
            
            m1, m2, m3 = st.columns(3)
            p_fc_needed = m1.number_input(f"🎯 Số {curr_sym} CẦN NHẬN BÊN TQ", min_value=0.0, step=100.0, format="%.2f", help="Số ngoại tệ chính xác cần chuyển cho nhà máy (Nhập tay)")
            p_paid_fc = m2.number_input(f"💸 Số {curr_sym} THỰC TẾ ĐÃ CHUYỂN", min_value=0.0, step=100.0, format="%.2f")
            
            fc_remain = p_fc_needed - p_paid_fc
            if fc_remain > 0:
                m3.metric("⏳ Còn lại cần chuyển", f"{fc_remain:,.2f} {curr_sym}", delta="Chưa chuyển đủ", delta_color="inverse")
            elif fc_remain < 0:
                m3.metric("💸 Đã chuyển thừa / Ứng trước", f"{abs(fc_remain):,.2f} {curr_sym}", delta="Đại lý/Xưởng đang dư tiền", delta_color="normal")
            else:
                m3.metric("✅ Trạng thái dòng tiền", "Đã tất toán xong", delta_color="normal")

            st.markdown("---")
            c8, c9 = st.columns(2)
            p_beneficiary = c8.text_input("Người nhận bên Trung Quốc (Tên Xưởng / Đại Lý)", placeholder="Ví dụ: Đại lý A, Fuchunshin Factory...")
            p_status = c9.selectbox("Trạng thái lệnh chi", ["✅ Đã tất toán xong" if fc_remain <= 0 and p_fc_needed > 0 else "⏳ Đang xử lý / Chờ chuyển thêm"])

            st.markdown("---")
            st.subheader("3. Liên kết Vận hành (Chủ động móc nối dữ liệu)")
            c10, c11 = st.columns(2)
            p_link_type = c10.selectbox("Loại liên kết", ["Không liên kết", "Hợp Đồng", "Lô Hàng"])
            
            link_id = ""
            if p_link_type == "Hợp Đồng":
                contract_list = ["--Chọn HĐ--"] + list(st.session_state.db_contracts.keys())
                link_id = c11.selectbox("Chọn Số Hợp Đồng", contract_list)
            elif p_link_type == "Lô Hàng":
                ship_list = ["--Chọn Lô--"] + list(st.session_state.db_shipments.keys())
                link_id = c11.selectbox("Chọn Mã Lô Hàng", ship_list)
            else:
                c11.text_input("Mã liên kết", "Trống", disabled=True)
                
            p_note = st.text_input("Ghi chú điều khoản bổ sung")

            if st.button(
                "💾 LƯU GIAO DỊCH THANH TOÁN HỘ",
                type="primary",
                use_container_width=True,
                disabled=not can_operate_business("proxy_payment"),
            ):
                if p_cust != "" and p_vnd > 0:
                    new_item = {
                        "id": p_id.strip().upper(), "date": str(p_date), "customer": p_cust,
                        "customer_id": selected_customer_id,
                        "amount_vnd": p_vnd, "exchange_rate": p_rate, "currency": p_curr,
                        "amount_fc_needed": p_fc_needed, "amount_fc_paid": p_paid_fc, "amount_fc_remain": fc_remain,
                        "beneficiary": p_beneficiary, "status": p_status, "linked_type": p_link_type,
                        "linked_id": link_id if link_id not in ["--Chọn HĐ--", "--Chọn Lô--"] else "",
                        "note": p_note, "created_at": str(datetime.now())
                    }
                    if p_link_type == "Hợp Đồng" and link_id not in ["", "--Chọn HĐ--"]:
                        new_item["contract_id"] = link_id
                    if save_proxy_payment(new_item):
                        st.session_state.db_proxy[p_id] = new_item
                        st.success(f"🎉 Đã lưu thành công giao dịch {p_id}!")
                        st.rerun()
                    else: st.error("❌ Lỗi kết nối database.")
                else: st.error("⚠️ Vui lòng điền đủ Tên người gửi tiền (hoặc chọn Khách Hàng) và Số tiền VNĐ!")

    with t_list:
        proxy_list = list(st.session_state.db_proxy.values()) if st.session_state.db_proxy else []
        
        # --- BỘ LỌC THỜI GIAN ---
        c_f1, c_f2 = st.columns([1, 3])
        time_mode = c_f1.selectbox("🔎 Khoảng thời gian báo cáo:", ["Tháng này", "Tháng trước", "Năm nay", "Tất cả"], index=0)
        
        today = date.today()
        start_date, end_date = None, None
        if time_mode == "Tháng này":
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        elif time_mode == "Tháng trước":
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
            start_date = date(end_date.year, end_date.month, 1)
        elif time_mode == "Năm nay":
            start_date, end_date = date(today.year, 1, 1), date(today.year, 12, 31)

        filtered_list = []
        for payment in proxy_list:
            payment_date = parse_date_optional(payment.get("date"))
            if time_mode == "Tất cả" or (payment_date and start_date and end_date and start_date <= payment_date <= end_date):
                filtered_list.append(payment)

        if not filtered_list:
            st.info(f"ℹ️ Không có giao dịch thanh toán hộ nào trong [{time_mode}].")
        else:
            df_proxy = pd.DataFrame(filtered_list)
            
            # =========================================================================
            # BỨC TRANH TỔNG THỂ (OVERVIEW)
            # =========================================================================
            st.markdown(f"### 📈 BỨC TRANH TỔNG THỂ ({time_mode.upper()})")
            
            # Tính tổng VNĐ thu vào
            total_vnd = sum([safe_float(p.get("amount_vnd", 0)) for p in filtered_list])
            st.metric("💰 TỔNG VNĐ ĐÃ THU", f"{total_vnd:,.0f} VNĐ")
            
            # Gom nhóm tổng hợp dòng tiền ra (Theo từng loại ngoại tệ)
            st.markdown("##### 🌐 Cân đối Ngoại tệ (Chuyển đi)")
            curr_summary = []
            for curr in df_proxy['currency'].unique():
                df_c = df_proxy[df_proxy['currency'] == curr]
                needed = df_c['amount_fc_needed'].map(safe_float).sum()
                paid = df_c['amount_fc_paid'].map(safe_float).sum()
                remain = needed - paid
                curr_summary.append({
                    "Loại Ngoại Tệ": curr,
                    "🎯 Tổng Cần Chuyển": needed,
                    "💸 Đã Đi Lệnh": paid,
                    "⏳ Còn Nợ Lại": remain
                })
            
            df_summ = pd.DataFrame(curr_summary)
            st.dataframe(
                df_summ, use_container_width=True, hide_index=True,
                column_config={
                    "🎯 Tổng Cần Chuyển": st.column_config.NumberColumn(format="%.2f"),
                    "💸 Đã Đi Lệnh": st.column_config.NumberColumn(format="%.2f"),
                    "⏳ Còn Nợ Lại": st.column_config.NumberColumn(format="%.2f")
                }
            )
            
            st.divider()
            
            # =========================================================================
            # DANH SÁCH CHI TIẾT
            # =========================================================================
            st.markdown("### 📋 SỔ QUỸ CHI TIẾT")
            table_rows = []
            for p in filtered_list:
                table_rows.append({
                    "Mã GD": p.get("id"), "Ngày": p.get("date"), "Khách Hàng/Người Gửi": p.get("customer"),
                    "Đã Nhận (VND)": safe_float(p.get("amount_vnd")), "Tỷ giá": safe_float(p.get("exchange_rate")),
                    "Tiền": p.get("currency", "CNY (¥)").split(" ")[0],
                    "Cần Chuyển": safe_float(p.get("amount_fc_needed", 0)),
                    "Đã Chuyển": safe_float(p.get("amount_fc_paid", 0)),
                    "Còn Nợ": safe_float(p.get("amount_fc_remain", 0)),
                    "Người Nhận (Nước ngoài)": p.get("beneficiary"), "Trạng Thái": p.get("status")
                })
            
            st.dataframe(
                pd.DataFrame(table_rows), use_container_width=True, hide_index=True,
                column_config={
                    "Đã Nhận (VND)": st.column_config.NumberColumn(format="%d ₫"),
                    "Tỷ giá": st.column_config.NumberColumn(format="%d"),
                    "Cần Chuyển": st.column_config.NumberColumn(format="%.2f"),
                    "Đã Chuyển": st.column_config.NumberColumn(format="%.2f"),
                    "Còn Nợ": st.column_config.NumberColumn(format="%.2f")
                }
            )
            
            with st.expander("🗃️ Lưu trữ giao dịch nhập sai"):
                del_id = st.selectbox("Chọn Mã Giao Dịch để xóa:", [p['id'] for p in proxy_list], key="del_proxy_select")
                delete_reason = st.text_input("Lý do", key="del_proxy_reason")
                if st.button("Đưa vào thùng lưu trữ", type="secondary", key="btn_del_proxy_action", disabled=not has_permission("proxy_payment_delete") or not delete_reason.strip()):
                    if delete_proxy_payment(del_id, reason=delete_reason.strip()):
                        st.session_state.db_proxy.pop(del_id, None)
                        st.success("Đã xóa!"); st.rerun()
