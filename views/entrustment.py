from __future__ import annotations

import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime
from uuid import uuid4

from core.database import load_entrustments, save_entrustment_book
from core.utils import safe_float


def load_all_entrust_db():
    return load_entrustments()


def save_entrust_db(db_data):
    intent_payload = {}
    for code, document in db_data.items():
        payload = dict(document)
        payload.pop("updated_at", None)
        intent_payload[str(code)] = payload
    intent = hashlib.sha256(
        json.dumps(intent_payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    request_key = "entrustment_batch_request_id"
    intent_key = "entrustment_batch_intent"
    if st.session_state.get(intent_key) != intent:
        st.session_state[intent_key] = intent
        st.session_state[request_key] = f"ENT-BATCH-{uuid4().hex.upper()}"
    user = st.session_state.get("current_user") or {}
    saved = save_entrustment_book(
        db_data,
        request_id=st.session_state[request_key],
        actor=user.get("username", "system"),
    )
    if saved:
        st.session_state.pop(request_key, None)
        st.session_state.pop(intent_key, None)
    else:
        # A failed transaction must not leave stale in-memory rows looking saved.
        st.session_state.db_entrustments = load_all_entrust_db()
    return saved

# =====================================================================
# GIAO DIỆN CHÍNH
# =====================================================================
def ui_entrustment_manager():
    st.title("💳 QUẢN LÝ THANH TOÁN HỘ (VÍ TỆ)")
    
    # 1. Tải dữ liệu một lần vào session-state
    if "db_entrustments" not in st.session_state:
        st.session_state.db_entrustments = load_all_entrust_db()
    db_total = st.session_state.db_entrustments

    # 2. Tải danh sách Lô hàng và Hợp đồng từ hệ thống lõi
    db_shipments = st.session_state.get("db_shipments", {})
    db_contracts = st.session_state.get("db_contracts", {})

    # State quản lý màn hình (Màn danh sách vs Màn chi tiết)
    if 'active_entrust_code' not in st.session_state:
        st.session_state.active_entrust_code = None

    active_code = st.session_state.active_entrust_code

    # =================================================================
    # MÀN HÌNH 1: BẢNG TỔNG HỢP (DANH SÁCH TẤT CẢ CÁC VÍ)
    # =================================================================
    if not active_code:
        st.caption("Quản lý tập trung các ví tiền ký quỹ, tự động hiển thị giao dịch mới nhất lên đầu.")
        
        # --- Form Tạo Mã Mới ---
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            new_code_input = c1.text_input("Nhập Tên/Mã giao dịch mới tinh:", placeholder="VD: CỌC-KH-MINH-ANH, LO-2026...").strip().upper()
            if c2.button("➕ TẠO VÍ THANH TOÁN MỚI", type="primary", use_container_width=True):
                if new_code_input:
                    if new_code_input not in db_total:
                        db_total[new_code_input] = {
                            "updated_at": datetime.now().strftime("%Y%m%d%H%M%S"),
                            "linked_type": "Không liên kết", "linked_id": "", "is_completed": False,
                            "deposits": [{"Ngày nạp": datetime.now().strftime("%d/%m/%Y"), "Số tiền (VND)": 0.0, "Ghi chú": "Khởi tạo"}],
                            "payments": []
                        }
                        save_entrust_db(db_total)
                    st.session_state.active_entrust_code = new_code_input
                    st.rerun()
                else:
                    st.error("⚠️ Vui lòng nhập tên mã cần tạo!")
        
        # --- Vẽ Bảng Tổng Hợp Bằng Dòng Vòng Lặp ---
        st.markdown("### 🗂️ SỔ CÁI VÍ TIỀN KÝ QUỸ")
        
        if not db_total:
            st.info("📭 Hệ thống chưa có dữ liệu thanh toán hộ nào.")
            return

        # Sắp xếp các ví theo thời gian cập nhật mới nhất (giảm dần)
        sorted_codes = sorted(
            db_total.keys(), 
            key=lambda k: db_total[k].get("updated_at", "00000000000000"), 
            reverse=True
        )

        # Vẽ Header Bảng
        header_cols = st.columns([1, 2, 2, 1.5, 1.5, 1.5, 1.5])
        header_cols[0].markdown("**Thao tác**")
        header_cols[1].markdown("**Mã Giao Dịch**")
        header_cols[2].markdown("**Liên Kết**")
        header_cols[3].markdown("**Tổng Nạp (VNĐ)**")
        header_cols[4].markdown("**Đã Chi (VNĐ)**")
        header_cols[5].markdown("**Số Dư Ví**")
        header_cols[6].markdown("**Trạng Thái**")
        st.markdown("<hr style='margin: 5px 0px; border-top: 2px solid #ddd;'>", unsafe_allow_html=True)

        # Vẽ từng dòng dữ liệu
        for code in sorted_codes:
            wallet = db_total[code]
            
            # Tính toán nhanh tài chính để hiển thị
            t_nap = sum([safe_float(d.get("Số tiền (VND)", 0)) for d in wallet.get("deposits", [])])
            t_chi = sum([(safe_float(p.get("Số Tiền Ngoại Tệ", p.get("Số Tệ (CNY)", 0))) * safe_float(p.get("Tỷ giá Báo Khách", 0))) for p in wallet.get("payments", [])])
            so_du = t_nap - t_chi
            
            is_comp = wallet.get("is_completed", False)
            link_type = wallet.get("linked_type", "Không")
            link_id = wallet.get("linked_id", "")
            
            cols = st.columns([1, 2, 2, 1.5, 1.5, 1.5, 1.5])
            
            # Nút Xem/Sửa
            if cols[0].button("👁️ Xem/Sửa", key=f"btn_view_{code}"):
                st.session_state.active_entrust_code = code
                st.rerun()
                
            cols[1].markdown(f"**{code}**")
            
            # Icon liên kết
            if link_type == "Lô Hàng (Dashboard)": cols[2].caption(f"📦 {link_id}")
            elif link_type == "Hợp Đồng": cols[2].caption(f"📄 {link_id}")
            else: cols[2].caption("⚪ Độc lập")
            
            cols[3].markdown(f"{t_nap:,.0f} ₫")
            cols[4].markdown(f"{t_chi:,.0f} ₫")
            
            if so_du >= 0: cols[5].markdown(f"<span style='color:green; font-weight:bold;'>{so_du:,.0f} ₫</span>", unsafe_allow_html=True)
            else: cols[5].markdown(f"<span style='color:red; font-weight:bold;'>{so_du:,.0f} ₫</span>", unsafe_allow_html=True)
            
            if is_comp: cols[6].markdown("🔒 *Hoàn thành*")
            else: cols[6].markdown("🟢 *Đang chạy*")
            
            st.markdown("<hr style='margin: 0px; opacity: 0.3;'>", unsafe_allow_html=True)

    # =================================================================
    # MÀN HÌNH 2: CHI TIẾT MỘT VÍ CỤ THỂ
    # =================================================================
    else:
        current_wallet = db_total[active_code]
        
        c_back, c_title = st.columns([1, 5])
        if c_back.button("⬅️ QUAY LẠI DANH SÁCH", use_container_width=True):
            st.session_state.active_entrust_code = None
            st.rerun()
            
        c_title.markdown(f"### 📂 CHI TIẾT VÍ: **{active_code}**")
        st.divider()

        # -----------------------------------------------------------------
        # KHỐI LIÊN KẾT HỒ SƠ
        # -----------------------------------------------------------------
        st.markdown("##### 🔗 Liên kết hồ sơ hệ thống")
        with st.container(border=True):
            cc1, cc2 = st.columns(2)
            curr_link_type = current_wallet.get("linked_type", "Không liên kết")
            link_type = cc1.radio("Gắn kết giao dịch thanh toán hộ này với:", ["Không liên kết", "Lô Hàng (Dashboard)", "Hợp Đồng"], index=["Không liên kết", "Lô Hàng (Dashboard)", "Hợp Đồng"].index(curr_link_type), horizontal=True)
            chosen_link_id = current_wallet.get("linked_id", "")
            
            if link_type == "Lô Hàng (Dashboard)":
                shipment_options = list(db_shipments.keys()) if db_shipments else []
                if not shipment_options: cc2.warning("⚠️ Chưa có lô hàng nào trên Dashboard.")
                else:
                    default_idx = shipment_options.index(chosen_link_id) if chosen_link_id in shipment_options else 0
                    chosen_link_id = cc2.selectbox("🎯 Chọn Mã Lô Hàng:", shipment_options, index=default_idx)
            elif link_type == "Hợp Đồng":
                contract_options = list(db_contracts.keys()) if db_contracts else []
                if not contract_options: cc2.warning("⚠️ Chưa có Hợp đồng nào.")
                else:
                    default_idx = contract_options.index(chosen_link_id) if chosen_link_id in contract_options else 0
                    chosen_link_id = cc2.selectbox("📄 Chọn Số Hợp Đồng:", contract_options, index=default_idx)
            else:
                chosen_link_id = ""

            if link_type != curr_link_type or chosen_link_id != current_wallet.get("linked_id", ""):
                db_total[active_code]["linked_type"] = link_type
                db_total[active_code]["linked_id"] = chosen_link_id
                if link_type == "Hợp Đồng" and chosen_link_id:
                    db_total[active_code]["contract_id"] = chosen_link_id
                else:
                    db_total[active_code].pop("contract_id", None)
                db_total[active_code]["updated_at"] = datetime.now().strftime("%Y%m%d%H%M%S")
                save_entrust_db(db_total)
                st.toast("🔗 Cập nhật liên kết thành công!")
                st.rerun()

        # -----------------------------------------------------------------
        # KHỐI NHẬP LIỆU BẢNG TÍNH (AUTO-SAVE)
        # -----------------------------------------------------------------
        curr_completed_status = current_wallet.get("is_completed", False)
        is_completed = st.checkbox("🔒 Khóa số liệu (Hoàn thành nhập liệu cho ví này)", value=curr_completed_status, key=f"chk_comp_{active_code}")
        
        if is_completed != curr_completed_status:
            db_total[active_code]["is_completed"] = is_completed
            db_total[active_code]["updated_at"] = datetime.now().strftime("%Y%m%d%H%M%S")
            save_entrust_db(db_total)
            st.rerun()

        with st.expander("📊 BẢNG KHÁCH NẠP & CHI TIẾT CHI HỘ (AUTO-SAVE)", expanded=not is_completed):
            st.markdown("#### 💰 Lịch sử khách nạp tiền ký quỹ (VNĐ)")
            df_dep = pd.DataFrame(current_wallet["deposits"])
            edited_dep = st.data_editor(
                df_dep,
                column_config={
                    "Ngày nạp": st.column_config.TextColumn("Ngày"),
                    "Số tiền (VND)": st.column_config.NumberColumn("Số tiền nạp (VNĐ)", format="%d ₫", step=100000),
                    "Ghi chú": st.column_config.TextColumn("Ghi chú", width="large")
                },
                num_rows="dynamic", use_container_width=True, key=f"editor_dep_{active_code}"
            )
            
            dep_dict_list = edited_dep.to_dict('records')
            if dep_dict_list != current_wallet["deposits"]:
                db_total[active_code]["deposits"] = dep_dict_list
                db_total[active_code]["updated_at"] = datetime.now().strftime("%Y%m%d%H%M%S")
                save_entrust_db(db_total)
                st.rerun()

            st.markdown("#### 🌐 Chi tiết đợt thanh toán hộ ngoại tệ")
            df_pay = pd.DataFrame(current_wallet["payments"])
            if df_pay.empty:
                df_pay = pd.DataFrame(columns=["Đợt/Lần", "Loại Tiền", "Số Tiền Ngoại Tệ", "Tỷ giá Báo Khách", "Tỷ giá Thực Tế", "Ghi chú"])
                
            edited_pay = st.data_editor(
                df_pay,
                column_config={
                    "Đợt/Lần": st.column_config.TextColumn("Lần", required=True),
                    "Loại Tiền": st.column_config.SelectboxColumn("Loại Tiền", options=["CNY", "USD", "EUR", "VND"], default="CNY", required=True),
                    "Số Tiền Ngoại Tệ": st.column_config.NumberColumn("Số Ngoại Tệ", format="%.2f", step=100.0, required=True),
                    "Tỷ giá Báo Khách": st.column_config.NumberColumn("Giá Báo Khách", format="%d", step=1, required=True),
                    "Tỷ giá Thực Tế": st.column_config.NumberColumn("Giá Thực Mua", format="%d", step=1, required=True),
                    "Ghi chú": st.column_config.TextColumn("Ghi chú", width="large")
                },
                num_rows="dynamic", use_container_width=True, key=f"editor_pay_{active_code}"
            )

            pay_dict_list = edited_pay.to_dict('records')
            if pay_dict_list != current_wallet["payments"]:
                db_total[active_code]["payments"] = pay_dict_list
                db_total[active_code]["updated_at"] = datetime.now().strftime("%Y%m%d%H%M%S")
                save_entrust_db(db_total)
                st.rerun()

        # -----------------------------------------------------------------
        # KHỐI TỔNG KẾT TÀI CHÍNH
        # -----------------------------------------------------------------
        total_nap_vnd = pd.to_numeric(edited_dep['Số tiền (VND)'], errors='coerce').fillna(0).sum()
        total_chi_baokhach_vnd = 0.0
        total_chi_thucte_vnd = 0.0
        cny_summary, usd_summary, eur_summary = 0.0, 0.0, 0.0
        
        for _, r in edited_pay.iterrows():
            currency_type = str(r.get("Loại Tiền", "CNY"))
            # Tương thích với data cũ đang dùng "Số Tệ (CNY)"
            foreign_amt = safe_float(r.get("Số Tiền Ngoại Tệ", r.get("Số Tệ (CNY)", 0)))
            tg_bao = safe_float(r.get("Tỷ giá Báo Khách", 0))
            tg_thuc = safe_float(r.get("Tỷ giá Thực Tế", 0))
            
            total_chi_baokhach_vnd += (foreign_amt * tg_bao)
            total_chi_thucte_vnd += (foreign_amt * tg_thuc)
            
            if currency_type == "CNY": cny_summary += foreign_amt
            elif currency_type == "USD": usd_summary += foreign_amt
            elif currency_type == "EUR": eur_summary += foreign_amt

        so_du_vi = total_nap_vnd - total_chi_baokhach_vnd
        lai_ty_gia = total_chi_baokhach_vnd - total_chi_thucte_vnd

        st.markdown("### 📊 TỔNG KẾT TÀI CHÍNH")
        if is_completed: st.caption("🔒 *Bảng số liệu chi tiết đang được thu gọn bảo mật.*")
            
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Tổng Khách Nạp", f"{total_nap_vnd:,.0f} ₫")
        m2.metric("💸 Tổng Chi (Giá báo)", f"{total_chi_baokhach_vnd:,.0f} ₫")
        
        if so_du_vi >= 0: m3.metric("🟢 DƯ VÍ (Đang giữ)", f"{so_du_vi:,.0f} ₫")
        else: m3.metric("🔴 KHÁCH CẦN BÙ", f"{abs(so_du_vi):,.0f} ₫", delta_color="inverse")
            
        m4.metric("📈 Lãi Tỷ Giá Tổng", f"{lai_ty_gia:,.0f} ₫")

        st.markdown("##### 📦 Ngoại tệ thực tế đã bốc đi chi hộ:")
        cc1, cc2, cc3 = st.columns(3)
        cc1.markdown(f"🇨🇳 Nhân Dân Tệ: **{cny_summary:,.2f} ¥**")
        cc2.markdown(f"🇺🇸 Đô La Mỹ: **{usd_summary:,.2f} $**")
        cc3.markdown(f"🇪🇺 Đồng Euro: **{eur_summary:,.2f} €**")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ XÓA TOÀN BỘ SỐ LIỆU MÃ NÀY", use_container_width=True):
            if active_code in db_total:
                del db_total[active_code]
                save_entrust_db(db_total)
                st.session_state.active_entrust_code = None
                st.rerun()
