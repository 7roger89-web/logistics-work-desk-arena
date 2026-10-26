# FILE: views/customers.py
import streamlit as st
import pandas as pd
from core.database import load_customers, save_customer_to_cloud, delete_customer
from core.auth import can_operate_business, has_permission

def ui_customers():
    st.title("👥 QUẢN LÝ KHÁCH HÀNG")
    st.caption("Quản lý danh sách, thông tin liên hệ và đối tác của công ty.")

    if "db_customers" not in st.session_state:
        st.session_state.db_customers = load_customers()
    db_customers = st.session_state.db_customers
    can_edit = can_operate_business("customers")

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
        df_display = pd.DataFrame(db_customers.values())
        # G1: email portal là cấu hình Owner cho phép trên chính hồ sơ
        # customers. Email liên hệ KHÔNG tự động cấp quyền. Cột này chỉ đọc
        # trong bảng cũ; Owner/Admin cấp/thu hồi qua control riêng.
        if "portal_access_email" not in df_display.columns:
            df_display["portal_access_email"] = ""
        else:
            df_display["portal_access_email"] = df_display["portal_access_email"].fillna("")
        st.caption("Email portal do Owner/Admin cấp riêng; mặc định không có quyền truy cập.")
        
        st.markdown(f"**Tổng số khách hàng:** {len(df_display)}")
        
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
                "portal_access_email": st.column_config.TextColumn("Email portal (Owner)", disabled=True),
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
                # Không cho bảng chỉnh sửa hàng loạt ghi đè cấu hình portal.
                # Owner/Admin thay đổi field này qua core.customer_portal.
                payload.pop("portal_access_email", None)
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
