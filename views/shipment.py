# FILE: views/shipment.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from uuid import uuid4

# --- IMPORTS ---
from core.config import INCOTERMS, STATUS_OPTIONS, STATUS_MAP_INV, STATUS_MAP_FWD, GETFLY_SERVICES_LIST
from core.auth import has_write_permission
from core.utils import mark_changed, parse_date, safe_float
from core.logic import calculate_shipment_financials, apply_financial_snapshot
from core.validators import validate_shipment
# [QUAN TRỌNG] Import đủ hàm
from core.database import (
    save_shipment_atomic,
    save_direct_shipment_payment,
    repair_data,
    load_customers,
    load_contracts,
    load_proxy_payments,
    load_entrustments,
    update_shipment_customer,
    rename_shipment_id,
    generate_shipment_id,
    load_audit_logs,
)
from core.excel_utils import generate_mini_export_excel
from core.excel_gnt import create_gnt_excel
from core.gnt_utils import get_treasury_info

def ui_create_new_shipment():
    st.title("➕ TẠO LÔ HÀNG MỚI")
    if 'db_customers' not in st.session_state:
        st.session_state.db_customers = load_customers()

    with st.container(border=True):
        c1, c2 = st.columns(2)
        default_code = st.session_state.setdefault('new_shipment_code', generate_shipment_id())
        code = c1.text_input("Mã Lô (Bắt buộc)", value=default_code).strip().upper()
        
        raw_cust = st.session_state.get('db_customers', {})
        customer_options = ["--Chọn--"] + list(raw_cust.keys())
        customer_id = c2.selectbox(
            "Khách hàng (Bắt buộc)", customer_options,
            format_func=lambda cid: "--Chọn--" if cid == "--Chọn--" else raw_cust.get(cid, {}).get("name", cid),
        )
        cust = raw_cust.get(customer_id, {}).get("name", "") if customer_id != "--Chọn--" else ""
        
        c3, c4 = st.columns(2)
        create_date = c3.date_input("Ngày chứng từ", value=date.today())
        init_note = c4.text_input("Ghi chú nội bộ")

        if st.button("🚀 Khởi tạo", type="primary", disabled=not has_write_permission("shipment_create")):
            if not has_write_permission("shipment_create"):
                st.warning("Bạn không có quyền tạo lô hàng.")
            elif code and customer_id != "--Chọn--" and cust:
                if 'db_shipments' in st.session_state and code in st.session_state.db_shipments:
                    st.error("Mã lô này đã tồn tại!"); return

                new_data = {
                    "0.0": {"st": "wait", "created_at": str(create_date), "mode": "Sea", "incoterm": "EXW"},
                    "1.2": {}, 
                    "2.4": {}, 
                    "2.6": {}, 
                    "2.7": {"addr": init_note}, 
                    "3.4": {"details": [], "commission": {"list": [], "total": 0}, "payments": []},
                    "entrustment": {"active": False}
                }
                
                ship_obj = {
                    "shipment_id": code, "id": code, 
                    "client": cust, "customer": cust, "customer_id": customer_id,
                    "data": new_data, "status": "wait", "currency": "VND"
                }
                
                validation = validate_shipment(ship_obj)
                if not validation.is_valid:
                    st.error(validation.message)
                    return
                if save_shipment_atomic(ship_obj):
                    st.session_state.db_shipments[code] = ship_obj
                    st.session_state.pop('new_shipment_code', None)
                    st.success(f"Đã tạo {code}!"); 
                    st.session_state.active_shipment_id = code; 
                    st.session_state.needs_refresh = True
                    st.rerun()
                else: st.error(st.session_state.get("last_db_error") or "Lỗi lưu Database.")
            else: st.error("Thiếu Mã lô hoặc Khách hàng!")

def ui_shipment_detail_tabs(sid, ship):
    repaired_ship = repair_data({sid: ship})[sid]
    ship = repaired_ship
    d = ship['data']
    prefix = f"dt_{sid}"

    # Shipment 360 is a read-only projection. Related caches are loaded only
    # for display; no summary control can save, allocate, or mutate money.
    related_read_errors = []
    if "db_proxy" not in st.session_state:
        try:
            st.session_state.db_proxy = load_proxy_payments()
        except Exception as exc:  # fail closed for optional related records
            st.session_state.db_proxy = {}
            related_read_errors.append(f"proxy_payments ({type(exc).__name__})")
    if "db_entrustments" not in st.session_state:
        try:
            st.session_state.db_entrustments = load_entrustments()
        except Exception as exc:  # fail closed for optional related records
            st.session_state.db_entrustments = {}
            related_read_errors.append(f"entrustments ({type(exc).__name__})")

    
    audit_rows = load_audit_logs("shipment", sid, limit=30)
    # --- HEADER ---
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1.35, 1.2, 2.5, 1.5, 1])
        current_st = ship.get("status") or d['0.0'].get('st', 'wait')
        st_idx = STATUS_OPTIONS.index(current_st) if current_st in STATUS_OPTIONS else 0

        new_id = c1.text_input("Mã Lô", value=sid, key=f"{prefix}_id_ren").strip().upper()
        new_date = c2.date_input("Ngày tạo", value=parse_date(d['0.0'].get('created_at')), key=f"{prefix}_dt")

        raw_customers = st.session_state.get("db_customers", {})
        current_customer_id = ship.get("customer_id", "")
        if current_customer_id not in raw_customers:
            current_name = ship.get("customer") or ship.get("client") or ""
            current_customer_id = next((cid for cid, customer in raw_customers.items() if customer.get("name") == current_name), "")
        customer_options = [""] + list(raw_customers.keys())
        new_customer_id = c3.selectbox(
            "Khách hàng", customer_options,
            index=customer_options.index(current_customer_id) if current_customer_id in customer_options else 0,
            format_func=lambda cid: "-- Chọn khách --" if not cid else raw_customers.get(cid, {}).get("name", cid),
            key=f"{prefix}_customer_id",
        )
        new_status = c4.selectbox(
            "Trạng thái", STATUS_OPTIONS, index=st_idx,
            format_func=lambda value: STATUS_MAP_INV.get(value, value), key=f"{prefix}_status",
        )
        should_save = c5.button("💾 LƯU", type="primary", use_container_width=True, key=f"{prefix}_sv")
        curr_cust = ship.get('customer') or ship.get('client') or ""
        new_cust_name = raw_customers.get(new_customer_id, {}).get("name", curr_cust)

        # Canonical contract link. Legacy entrustment.contract_no remains a
        # read fallback, while new saves write a direct contract_id.
        contracts_db = st.session_state.get("db_contracts", {})
        current_contract_id = str(ship.get("contract_id") or d.get("entrustment", {}).get("contract_no") or "").strip().upper()
        contract_options = [""] + list(contracts_db.keys())
        if current_contract_id and current_contract_id not in contract_options:
            contract_options.append(current_contract_id)
        new_contract_id = st.selectbox(
            "Hợp đồng liên kết (một hợp đồng có thể dùng nhiều lô)",
            contract_options,
            index=contract_options.index(current_contract_id) if current_contract_id in contract_options else 0,
            format_func=lambda value: "-- Chưa liên kết --" if not value else value,
            key=f"{prefix}_contract_id",
        )

    # TRẢ LẠI ĐÚNG 3 TAB CHUẨN GỐC CỦA ANH
    # LOG-LG04: mở tab theo thẻ việc chính ở đầu trang
    _jump = st.session_state.pop("active_shipment_section", None)
    _tab_labels = ["🚛 PICKUP & XUẤT KHẨU", "🛃 IMPORT & GIAO HÀNG", "💰 FINANCE (CÔNG NỢ)"]
    if _jump in ("export", 0, None):
        _tab_label = _tab_labels[0]
    elif _jump in ("import", 1):
        _tab_label = _tab_labels[1]
    elif _jump in ("finance", 2):
        _tab_label = _tab_labels[2]
    else:
        _tab_label = _tab_labels[0]  # default: PICKUP & XUẤT KHẨU
    t1, t2, t3 = st.tabs(
        ["🚛 PICKUP & XUẤT KHẨU", "🛃 IMPORT & GIAO HÀNG", "💰 FINANCE (CÔNG NỢ)"],
        default=_tab_label,
    )
    
    with t1:
        st.markdown(f"<a id='lg04_tab_export'></a>", unsafe_allow_html=True)
        st.caption("Thông tin Vận đơn")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            d['0.0']['mode'] = c1.selectbox("Mode", ["Sea", "Air", "Truck", "Rail"], index=["Sea", "Air", "Truck", "Rail"].index(d['0.0'].get('mode', 'Sea')) if d['0.0'].get('mode') in ["Sea", "Air", "Truck", "Rail"] else 0, key=f"{prefix}_m")
            d['0.0']['incoterm'] = c2.selectbox("Incoterm", INCOTERMS, index=INCOTERMS.index(d['0.0'].get('incoterm')) if d['0.0'].get('incoterm') in INCOTERMS else 0, key=f"{prefix}_inco")
            d['1.2']['booking_no'] = c3.text_input("Booking No", d['1.2'].get('booking_no',''), key=f"{prefix}_bk")
            d['1.2']['carrier'] = c4.text_input("Carrier", d['1.2'].get('carrier',''), key=f"{prefix}_carr")
            c1, c2, c3, c4 = st.columns(4)
            d['1.2']['mbl'] = c1.text_input("MBL", d['1.2'].get('mbl',''), key=f"{prefix}_mbl")
            d['1.2']['hbl'] = c2.text_input("HBL", d['1.2'].get('hbl',''), key=f"{prefix}_hbl")
            d['1.2']['vessel'] = c3.text_input("Vessel", d['1.2'].get('vessel',''), key=f"{prefix}_ves")
            d['1.2']['etd'] = str(c4.date_input("ETD", value=parse_date(d['1.2'].get('etd')), key=f"{prefix}_etd"))
            c1, c2 = st.columns(2)
            d['1.2']['pol'] = c1.text_input("POL", d['1.2'].get('pol',''), key=f"{prefix}_pol")
            d['1.2']['pod'] = c2.text_input("POD", d['1.2'].get('pod',''), key=f"{prefix}_pod")
            c1, c2, c3 = st.columns(3)
            d['1.2']['container_no'] = c1.text_input("Số Cont/Xe", d['1.2'].get('container_no',''), key=f"{prefix}_cont")
            d['1.2']['qty_pkg'] = c2.text_input("Số Lượng/GW", d['1.2'].get('qty_pkg',''), key=f"{prefix}_pkg")

    with t2:
        st.markdown(f"<a id='lg04_tab_import'></a>", unsafe_allow_html=True)
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.caption("1. Nhập khẩu")
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                d['2.6']['arrival_date'] = str(c1.date_input("ETA", value=parse_date(d['2.6'].get('arrival_date')), key=f"{prefix}_eta"))
                d['2.6']['free_time'] = c2.number_input("Free Time", value=int(safe_float(d['2.6'].get('free_time', 14))), key=f"{prefix}_ft")
                
                d['2.4']['tk_no'] = c3.text_input("Số TK HQ", d['2.4'].get('tk_no',''), key=f"{prefix}_tk")
                
                db_cust = st.session_state.get('db_customers', {})
                cust_info = db_cust.get(ship.get('customer_id', ''), {})
                if not cust_info:
                    cust_info = next((customer for customer in db_cust.values() if customer.get('name') == curr_cust), {})
                
                with st.expander("🖨️ Tạo Giấy Nộp Thuế (GNT)", expanded=False):
                    st.caption("Điền thông tin để xuất file Excel GNT")
                    gnt_saved = d['2.4'].setdefault('gnt', {})
                    c_gnt_1, c_gnt_2 = st.columns(2)
                    gnt_nguoi_nop = c_gnt_1.text_input(
                        "Người nộp thuế",
                        value=gnt_saved.get('nguoi_nop') or new_cust_name or curr_cust,
                        key=f"gnt_name_{sid}",
                    )
                    gnt_mst = c_gnt_2.text_input(
                        "Mã số thuế",
                        value=gnt_saved.get('mst') or cust_info.get('tax_code', ''),
                        key=f"gnt_mst_{sid}",
                    )
                    gnt_dia_chi = st.text_input(
                        "Địa chỉ",
                        value=gnt_saved.get('dia_chi') or cust_info.get('address', ''),
                        key=f"gnt_addr_{sid}",
                    )

                    c_lookup_1, c_lookup_2 = st.columns([3, 1])
                    gnt_ma_hq = c_lookup_1.text_input(
                        "Mã cơ quan hải quan",
                        value=gnt_saved.get('ma_hq', ''),
                        help="Dùng để tra cứu tên cơ quan thu và KBNN từ MA_NGAN_SACH.xlsx.",
                        key=f"gnt_ma_hq_{sid}",
                    )
                    if c_lookup_2.button("Tra cứu", key=f"gnt_lookup_{sid}", use_container_width=True):
                        lookup_cq, lookup_kb = get_treasury_info(gnt_ma_hq)
                        if lookup_cq or lookup_kb:
                            st.session_state[f"gnt_cq_{sid}"] = lookup_cq
                            st.session_state[f"gnt_kbnn_{sid}"] = lookup_kb
                            st.toast("Đã tra cứu thông tin Kho bạc/Cơ quan thu.")
                        else:
                            st.warning("Không tìm thấy mã HQ hoặc chưa có file MA_NGAN_SACH.xlsx.")

                    c_gnt_3, c_gnt_4 = st.columns(2)
                    gnt_kbnn = c_gnt_3.text_input(
                        "KBNN",
                        value=gnt_saved.get('ten_kbnn', ''),
                        placeholder="Nhập tên Kho bạc Nhà nước",
                        key=f"gnt_kbnn_{sid}",
                    )
                    gnt_cq_thu = c_gnt_4.text_input(
                        "Cơ quan thu",
                        value=gnt_saved.get('ten_cq_thu', ''),
                        placeholder="Nhập tên cơ quan quản lý thu",
                        key=f"gnt_cq_{sid}",
                    )

                    c_gnt_5, c_gnt_6 = st.columns(2)
                    account_options = ["7111", "3511"]
                    saved_account = str(gnt_saved.get('tk_thu', '7111'))
                    gnt_tk_thu = c_gnt_5.selectbox(
                        "Loại tài khoản",
                        account_options,
                        index=account_options.index(saved_account) if saved_account in account_options else 0,
                        format_func=lambda x: "7111 (NSNN)" if x == '7111' else "3511 (Tạm thu)",
                        key=f"gnt_type_{sid}",
                    )
                    gnt_so_tk = c_gnt_6.text_input(
                        "Số TK/QĐ",
                        value=gnt_saved.get('so_tk') or d['2.4'].get('tk_no', ''),
                        key=f"gnt_stk_input_{sid}",
                    )
                    gnt_saved.update({
                        'nguoi_nop': gnt_nguoi_nop,
                        'mst': gnt_mst,
                        'dia_chi': gnt_dia_chi,
                        'ma_hq': gnt_ma_hq,
                        'ten_kbnn': gnt_kbnn,
                        'ten_cq_thu': gnt_cq_thu,
                        'tk_thu': gnt_tk_thu,
                        'so_tk': gnt_so_tk,
                    })

                    if f"gnt_tax_data_{sid}" not in st.session_state:
                         st.session_state[f"gnt_tax_data_{sid}"] = [
                            {"Nội dung": "Thuế Nhập khẩu", "Mã NDKT": "1901", "Số tiền": 0},
                            {"Nội dung": "Thuế GTGT hàng NK", "Mã NDKT": "1701", "Số tiền": 0},
                        ]
                    
                    edited_taxes = st.data_editor(
                        st.session_state[f"gnt_tax_data_{sid}"], num_rows="dynamic", use_container_width=True, key=f"gnt_tax_table_{sid}",
                        column_config={
                            "Nội dung": st.column_config.TextColumn("Nội dung khoản nộp", width="large", required=True),
                            "Mã NDKT": st.column_config.TextColumn("Mã NDKT", width="medium"),
                            "Số tiền": st.column_config.NumberColumn("Số tiền (VNĐ)", format="%d", min_value=0, required=True)
                        }
                    )

                    if st.button("📥 Xuất Excel GNT", key=f"btn_gnt_{sid}", use_container_width=True):
                        final_tax_list = []
                        st.session_state[f"gnt_tax_data_{sid}"] = edited_taxes.to_dict("records")
                        for _, item in edited_taxes.iterrows():
                            amt = safe_float(item.get("Số tiền", 0))
                            if amt > 0:
                                final_tax_list.append({
                                    "ten": str(item.get("Nội dung", "")).strip(),
                                    "ndkt": str(item.get("Mã NDKT", "")).strip(),
                                    "tien": amt,
                                })
                        if not final_tax_list: st.warning("Vui lòng nhập số tiền thuế lớn hơn 0.")
                        else:
                            gnt_data = {
                                'nguoi_nop': gnt_nguoi_nop, 'mst': gnt_mst, 'dia_chi': gnt_dia_chi,
                                'ten_kbnn': gnt_kbnn, 'ten_cq_thu': gnt_cq_thu,
                                'ma_cq_thu': gnt_ma_hq,
                                'tk_thu': gnt_tk_thu, 'so_tk': gnt_so_tk,
                                'ngay_tk': datetime.now().strftime("%d/%m/%Y"), 
                                'ds_thue': final_tax_list
                            }
                            excel_buffer = create_gnt_excel(gnt_data)
                            if excel_buffer:
                                st.download_button(label="📄 Tải file GNT.xlsx", data=excel_buffer, file_name=f"GNT_{gnt_so_tk}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                c4, c5 = st.columns([1,2])
                d['2.4']['customs_status'] = c4.checkbox("Đã thông quan", d['2.4'].get('customs_status', False), key=f"{prefix}_cst")
                d['2.4']['phan_luong'] = c5.selectbox("Luồng", ["Xanh", "Vàng", "Đỏ"], index=["Xanh", "Vàng", "Đỏ"].index(d['2.4'].get('phan_luong','Xanh')) if d['2.4'].get('phan_luong') in ["Xanh", "Vàng", "Đỏ"] else 1, key=f"{prefix}_pl")

            st.caption("2. Giao hàng")
            with st.container(border=True):
                c1, c2 = st.columns(2)
                d['2.7']['truck_no'] = c1.text_input("Xe giao", d['2.7'].get('truck_no',''), key=f"{prefix}_trn")
                d['2.7']['seal_no'] = c2.text_input("Tài xế/SĐT", d['2.7'].get('seal_no',''), key=f"{prefix}_seal") 
                c3, c4 = st.columns(2)
                d['2.7']['delivery_date'] = str(c3.date_input("Ngày giao", value=parse_date(d['2.7'].get('delivery_date')), key=f"{prefix}_dld"))
                d['2.7']['phone_receiver'] = c4.text_input("SĐT Nhận", d['2.7'].get('phone_receiver',''), key=f"{prefix}_phr")
                d['2.7']['addr'] = st.text_area("Đ/C Giao", d['2.7'].get('addr',''), key=f"{prefix}_add")
                d['2.7']['is_delivered'] = st.checkbox("Đã giao xong", value=d['2.7'].get('is_delivered', False), key=f"{prefix}_done")

            st.caption("3. Ủy thác & Hợp đồng")
            with st.container(border=True):
                ent = d.get('entrustment', {})
                ent['active'] = st.checkbox("Kích hoạt Ủy thác", ent.get('active', False), key=f"{prefix}_ut_act")
                
                if ent['active']:
                    if 'db_contracts' not in st.session_state: st.session_state.db_contracts = load_contracts()
                    contracts = st.session_state.db_contracts
                    c_opts = ["--Chọn HĐ--"] + list(contracts.keys())
                    curr_c = ent.get('contract_no', '--Chọn HĐ--')
                    if curr_c not in c_opts: c_opts.insert(0, curr_c)
                    
                    c1, c2 = st.columns(2)
                    ent['contract_no'] = c1.selectbox("Số Hợp Đồng", c_opts, index=c_opts.index(curr_c) if curr_c in c_opts else 0, key=f"{prefix}_ut_cn")
                    ent['invoice_no'] = c2.text_input("Số Invoice", ent.get('invoice_no', ''), key=f"{prefix}_ut_inv")
                    c3, c4 = st.columns(2)
                    ent['shipment_val'] = c3.text_input("Giá trị hàng (USD)", ent.get('shipment_val', '0'), key=f"{prefix}_ut_val")
                    ent['rate'] = c4.text_input("Tỷ giá", ent.get('rate', '24000'), key=f"{prefix}_ut_rate")
                    d['entrustment'] = ent

        with col_r:
            st.info("📋 COPY NHANH")
            info_str = f"""LÔ: {sid}\nKH: {ship.get('customer')}\nMBL: {d['1.2'].get('mbl')}\nHBL: {d['1.2'].get('hbl')}\nETD: {d['1.2'].get('etd')} | ETA: {d['2.6'].get('arrival_date')}\nCont: {d['1.2'].get('container_no')}\nTK HQ: {d['2.4'].get('tk_no')}\nXe: {d['2.7'].get('truck_no')}\nĐ/C: {d['2.7'].get('addr')}\nLH: {d['2.7'].get('phone_receiver')}"""
            st.code(info_str, language=None)

    with t3:
        st.markdown(f"<a id='lg04_tab_finance'></a>", unsafe_allow_html=True)
        st.subheader("1. Dịch Vụ & Doanh Thu — nhập chi phí và giá bán")
        st.caption("Nhập vào đây để tính doanh thu, chi phí, công nợ và lợi nhuận của lô hàng. Sau khi nhập, nhấn nút 💾 LƯU ở đầu trang.")
        details = d['3.4']['details']
        
        h = st.columns([0.5, 3, 1, 1.5, 1.5, 1, 1.5, 0.5])
        h[0].caption("#"); h[1].caption("Tên Dịch vụ"); h[2].caption("SL");
        h[3].caption("Giá Vốn"); h[4].caption("Giá Bán"); h[5].caption("VAT %"); h[6].caption("Thành tiền");
        st.markdown(
            "<style>.lg04-service-row { border: 2px solid #D0D7DE; border-radius: 10px; "
            "padding: .5rem .65rem .3rem; margin-bottom: .75rem; background: #FFFFFF; }</style>",
            unsafe_allow_html=True,
        )

        indices_to_remove = []
        base_service_options = [f"{s['name']} ({s['code']})" for s in GETFLY_SERVICES_LIST]
        service_map = {f"{s['name']} ({s['code']})": s for s in GETFLY_SERVICES_LIST}

        for i, item in enumerate(details):
            c = st.columns([0.5, 3, 1, 1.5, 1.5, 1, 1.5, 0.5])
            c[0].text(str(i + 1))
            st.markdown("<div class='lg04-service-row'>", unsafe_allow_html=True)

            current_code = str(item.get('code', '')).strip()
            current_name = str(item.get('display_name') or item.get('name_full') or item.get('name') or '').strip()
            matched_option = next(
                (label for label, meta in service_map.items() if current_code and meta['code'] == current_code),
                '',
            )
            current_option = matched_option or current_name
            service_options = list(base_service_options)
            if current_option and current_option not in service_options:
                service_options.insert(0, current_option)
            selected_index = service_options.index(current_option) if current_option in service_options else 0

            selected_service = c[1].selectbox(
                "S",
                service_options,
                index=selected_index,
                key=f"{prefix}_s_{i}",
                label_visibility="collapsed",
            )
            selected_meta = service_map.get(selected_service)
            if selected_meta:
                item['name_full'] = selected_meta['name']
                item['display_name'] = selected_meta['name']
                item['code'] = selected_meta['code']
                item['unit'] = selected_meta.get('unit', 'Lần')
            else:
                item['name_full'] = selected_service
                item['display_name'] = selected_service
                item.setdefault('code', 'DVK')

            val_qty = safe_float(item.get('qty', 1))
            val_cost = safe_float(item.get('cost', item.get('price_in', 0))) 
            val_price = safe_float(item.get('price', item.get('price_out', 0)))
            val_vat = safe_float(item.get('vat_line', item.get('vat', 0)))

            item['qty'] = c[2].number_input("Q", value=float(val_qty), step=1.0, format="%.0f", key=f"{prefix}_q_{i}", label_visibility="collapsed")
            item['cost'] = c[3].number_input("In", value=float(val_cost), step=10000.0, format="%.0f", key=f"{prefix}_pi_{i}", label_visibility="collapsed")
            item['price'] = c[4].number_input("Out", value=float(val_price), step=10000.0, format="%.0f", key=f"{prefix}_po_{i}", label_visibility="collapsed")
            item['vat_line'] = c[5].number_input("V", value=float(val_vat), step=1.0, format="%.0f", key=f"{prefix}_v_{i}", label_visibility="collapsed")

            item['price_in'] = item['cost']
            item['price_out'] = item['price']
            item['vat'] = item['vat_line']

            line_total = (item['qty'] * item['price']) * (1 + item['vat_line']/100.0)
            c[6].markdown(f"**{line_total:,.0f}**")
            
            if c[7].button("🗑", key=f"{prefix}_del_svc_{i}"):
                indices_to_remove.append(i)

            item['note'] = st.text_input("Ghi chú", value=item.get('note', ''), key=f"{prefix}_note_{i}", placeholder="Ghi chú chi tiết...", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        if indices_to_remove:
            for i in sorted(indices_to_remove, reverse=True): details.pop(i)
            st.rerun()

        if st.button("➕ Thêm Dịch vụ", key=f"{prefix}_add_svc"):
            details.append({"id": str(uuid4()), "name_full": "", "qty": 1, "cost": 0, "price": 0, "vat_line": 0, "note": ""})
            st.rerun()

        st.divider()

        with st.expander("🧮 TÍNH HOA HỒNG (GROSS-UP)", expanded=False):
            st.caption("Công thức: Gross = Net / (1 - %Phí)")
            g1, g2 = st.columns(2)
            net_amt = g1.number_input("Số tiền khách thực nhận (Net)", min_value=0.0, step=100000.0, format="%.0f", key=f"{prefix}_net")
            fee_pct = g2.number_input("Phí (%)", min_value=0.0, max_value=99.0, value=10.0, step=0.5, key=f"{prefix}_fee")
            
            if fee_pct < 100:
                gross_amt = net_amt / (1 - (fee_pct/100))
                retention = gross_amt - net_amt
                st.markdown(f"👉 **Gross cần ghi:** `{gross_amt:,.0f}` (Giữ lại: `{retention:,.0f}`)")
                
                if st.button("💾 Áp dụng vào Chi phí Hoa hồng", key=f"{prefix}_apply_com"):
                    if 'commission' not in d['3.4']: d['3.4']['commission'] = {}
                    d['3.4']['commission']['total'] = gross_amt
                    d['3.4']['commission']['details'] = {"type": "gross_up", "net": net_amt, "fee": fee_pct, "retention": retention}
                    ship["data"] = d
                    apply_financial_snapshot(ship)
                    if save_shipment_atomic(ship, expected_version=ship.get("version")):
                        st.session_state.needs_refresh = True
                        st.success("Đã cập nhật!")
                        st.rerun()
                    st.error(st.session_state.get("last_db_error") or "Không thể lưu dữ liệu.")

        fin_stats = calculate_shipment_financials(details, d['3.4'].get('commission', {}), d['3.4']['payments'])
        d['3.4']['out'] = fin_stats['receivable']
        d['3.4']['in'] = fin_stats['cost']
        
        c_fin_1, c_fin_2 = st.columns(2)
        with c_fin_1:
            st.subheader("2. Chi Hoa Hồng")
            comm_data = d['3.4']['commission']
            if 'list' not in comm_data: comm_data['list'] = []
            
            comm_total = st.number_input("Tổng Hoa Hồng (Chi ngoài)", value=float(safe_float(comm_data.get('total', 0))), step=100000.0, format="%.0f", key=f"{prefix}_comm_tot")
            comm_note = st.text_input("Ghi chú Hoa hồng", value=comm_data.get('note', ''), key=f"{prefix}_comm_note")
            comm_data['total'] = comm_total
            comm_data['note'] = comm_note

        with c_fin_2:
            st.subheader("3. Lịch sử Thu tiền")
            payments = d['3.4']['payments']
            pay_remove = []
            for idx, p in enumerate(payments):
                cc = st.columns([1.5, 2, 1.5, 0.5])
                cc[0].text(p.get('date'))
                cc[1].text(p.get('note'))
                cc[2].markdown(f"**{safe_float(p.get('amount')):,.0f}**")
                if cc[3].button("x", key=f"{prefix}_del_pay_{idx}"): pay_remove.append(idx)
            
            if pay_remove:
                st.warning("Lịch sử thanh toán không được xóa âm. Hãy dùng correction/reversal có audit.")

            with st.expander("➕ Nhập thanh toán mới"):
                pp1, pp2 = st.columns(2)
                pd_date = pp1.date_input("Ngày", date.today(), key=f"{prefix}_pd_d")
                pd_amt = pp2.number_input("Số tiền", step=100000.0, format="%.0f", key=f"{prefix}_pd_a")
                pd_note = st.text_input("Nội dung", key=f"{prefix}_pd_n")
                if st.button("Lưu thanh toán", key=f"{prefix}_pd_s"):
                    if pd_amt <= 0:
                        st.error("Số tiền thanh toán phải lớn hơn 0.")
                    else:
                        payment_request_key = f"{prefix}_payment_request_id"
                        payment_intent_key = f"{prefix}_payment_intent"
                        payment_intent = f"{pd_date}|{float(pd_amt):.2f}|{pd_note.strip()}"
                        if st.session_state.get(payment_intent_key) != payment_intent:
                            st.session_state[payment_intent_key] = payment_intent
                            st.session_state[payment_request_key] = f"PAY-REQ-{uuid4().hex.upper()}"
                        payment_request_id = st.session_state[payment_request_key]
                        payment = {
                            "id": f"PAY-{uuid4().hex.upper()}",
                            "request_id": payment_request_id,
                            "date": str(pd_date),
                            "note": pd_note.strip(),
                            "amount": float(pd_amt),
                        }
                        user = st.session_state.get("current_user") or {}
                        ok, result, message = save_direct_shipment_payment(
                            sid,
                            payment,
                            actor=user.get("username", "system"),
                        )
                        if ok:
                            payment["id"] = result.get("payment_id") or payment["id"]
                            if not any(str(row.get("request_id") or "") == payment_request_id for row in payments):
                                payments.append(payment)
                            ship["data"] = d
                            apply_financial_snapshot(ship)
                            if result.get("version") is not None:
                                ship["version"] = result["version"]
                            st.session_state.db_shipments[sid] = ship
                            st.session_state.pop(payment_request_key, None)
                            st.session_state.pop(payment_intent_key, None)
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(st.session_state.get("last_db_error") or message)

        st.markdown("---")
        st.subheader("📊 BẢNG KÊ TÀI CHÍNH")
        
        fin_stats = calculate_shipment_financials(details, comm_data, payments)
        profit = fin_stats['profit']
        debt = fin_stats['debt']
        d['3.4']['out'] = fin_stats['receivable']
        d['3.4']['out_net'] = fin_stats['revenue_net']
        d['3.4']['output_vat'] = fin_stats['output_vat']
        d['3.4']['in'] = fin_stats['cost']

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("PHẢI THU", f"{fin_stats['receivable']:,.0f}", help=f"Doanh thu trước VAT: {fin_stats['revenue_net']:,.0f}; VAT đầu ra: {fin_stats['output_vat']:,.0f}")
        m2.metric("CHI PHÍ", f"{fin_stats['cost']:,.0f}")
        m3.metric("HOA HỒNG", f"{comm_data['total']:,.0f}")
        m4.metric("LỢI NHUẬN", f"{profit:,.0f}", delta="Tạm tính")
        m5.metric("CÔNG NỢ", f"{abs(debt):,.0f}", delta_color="inverse" if debt > 0 else "normal")

        if st.button("📥 Xuất File Excel (Nội bộ)", key=f"{prefix}_xls"):
            ship['data'] = d
            st.download_button("Tải .xlsx", generate_mini_export_excel(ship), f"BangKe_{sid}.xlsx")

    with st.expander("🕒 Lịch sử thay đổi", expanded=False):
        if audit_rows:
            st.dataframe(
                pd.DataFrame([{
                    "Thời gian": str(row.get("created_at", "")),
                    "Người thực hiện": row.get("actor", ""),
                    "Hành động": row.get("action", ""),
                } for row in audit_rows]),
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("Chưa có audit log cho lô này.")

    if str(new_date) != d['0.0'].get('created_at'): d['0.0']['created_at'] = str(new_date); mark_changed()
    
    if new_id != sid:
        if rename_shipment_id(sid, new_id):
            st.session_state.active_shipment_id = new_id
            st.success(f"Đã đổi mã lô thành: {new_id}")
            st.rerun()
        else: st.error("Lỗi đổi mã lô")

    ship["status"] = new_status
    d["0.0"]["st"] = new_status
    if new_cust_name != curr_cust or new_customer_id != ship.get("customer_id"):
        ship["customer"] = new_cust_name
        ship["client"] = new_cust_name
        ship["customer_id"] = new_customer_id

    if should_save:
        ship['data'] = d
        if new_contract_id:
            ship["contract_id"] = new_contract_id
        else:
            ship.pop("contract_id", None)
        apply_financial_snapshot(ship)
        validation = validate_shipment(ship)
        for warning in validation.warnings:
            st.warning(warning.message)
        if not validation.is_valid:
            for error in validation.errors:
                st.error(error.message)
        elif save_shipment_atomic(ship, expected_version=ship.get("version")):
            st.session_state.db_shipments[sid] = ship
            st.session_state.needs_refresh = True
            st.toast("Đã lưu dữ liệu thành công!", icon="💾")
            st.rerun()
        else:
            st.error(st.session_state.get("last_db_error") or "Không lưu được vào Database.")
