# FILE: views/reports.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from core.database import load_data, load_customers, load_tasks, load_proxy_payments
from core.utils import safe_float, parse_date_optional, get_shipment_business_date
from core.logic import calculate_from_shipment

def clean_client_name(name):
    if not name or name == "Unknown": return "Khách Lẻ"
    return str(name).upper().strip()

def ui_reports_dashboard():
    st.title("📊 BÁO CÁO QUẢN TRỊ (CEO DASHBOARD)")
    st.caption("Bức tranh toàn cảnh về Sức khỏe Tài chính, Lợi nhuận và Hiệu suất Vận hành của Doanh nghiệp.")

    # 1. Tải toàn bộ dữ liệu
    if 'db_reporting_shipments' not in st.session_state:
        st.session_state.db_reporting_shipments = load_data(limit=100000, include_archived=True)
    if 'db_customers' not in st.session_state: st.session_state.db_customers = load_customers()
    if 'db_proxy' not in st.session_state: st.session_state.db_proxy = load_proxy_payments()
    
    shipments = st.session_state.db_reporting_shipments
    proxies = st.session_state.db_proxy
    tasks = load_tasks()

    # 2. BỘ LỌC THỜI GIAN GLOBAL
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        time_mode = c1.selectbox("⏳ Chọn kỳ báo cáo:", ["Tháng này", "Tháng trước", "Quý này", "Năm nay", "Tất cả"], index=0)
        
        today = date.today()
        start_date, end_date = None, None
        
        if time_mode == "Tháng này":
            start_date, end_date = date(today.year, today.month, 1), date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        elif time_mode == "Tháng trước":
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
            start_date = date(end_date.year, end_date.month, 1)
        elif time_mode == "Quý này":
            curr_quarter = (today.month - 1) // 3 + 1
            start_date = date(today.year, 3 * curr_quarter - 2, 1)
            end_month = 3 * curr_quarter
            end_date = date(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
        elif time_mode == "Năm nay":
            start_date, end_date = date(today.year, 1, 1), date(today.year, 12, 31)

        # Hiển thị ngày cụ thể để Giám đốc nắm rõ
        if start_date and end_date:
            c2.info(f"Từ: **{start_date.strftime('%d/%m/%Y')}** ➔ Đến: **{end_date.strftime('%d/%m/%Y')}**")
        else:
            c2.info("Hiển thị dữ liệu Toàn thời gian")

    # 3. LỌC VÀ XỬ LÝ DỮ LIỆU TÀI CHÍNH
    filtered_ships = []
    for sid, s in shipments.items():
        dt = get_shipment_business_date(s)
        if time_mode == "Tất cả" or (dt and start_date <= dt <= end_date):
            filtered_ships.append((sid, s))

    total_revenue, total_cost, total_profit, total_debt_kh, total_debt_agent_vnd = 0, 0, 0, 0, 0
    client_stats = {}

    for sid, s in filtered_ships:
        d = s.get('data', {})
        client = clean_client_name(s.get('customer', s.get('client')))
        
        # Tính theo FinanceService duy nhất; lợi nhuận không cộng VAT đầu ra.
        summary = calculate_from_shipment(s)
        rev = safe_float(summary.get("revenue_net", 0))
        cost = safe_float(summary.get("cost", 0))
        profit = safe_float(summary.get("profit", 0))
        debt_kh = safe_float(summary.get("debt", 0))
        
        # Công nợ đại lý
        ag = d.get('3.4', {}).get('agency', {})
        ag_fee_vnd = safe_float(ag.get('fee_vnd', ag.get('fee', 0)))
        ag_col_vnd = safe_float(ag.get('collected_vnd', ag.get('collected', 0)))
        ag_paid_vnd = safe_float(ag.get('paid_vnd', 0))
        debt_agent = ag_fee_vnd - ag_col_vnd - ag_paid_vnd

        # Cộng dồn
        total_revenue += rev
        total_cost += cost
        total_profit += profit
        if debt_kh > 1000: total_debt_kh += debt_kh
        if debt_agent > 0: total_debt_agent_vnd += debt_agent

        # Cập nhật thống kê Khách hàng
        if client not in client_stats:
            client_stats[client] = {'Doanh Thu': 0, 'Lợi Nhuận': 0, 'Đang Nợ': 0, 'Số Lô': 0}
        client_stats[client]['Doanh Thu'] += rev
        client_stats[client]['Lợi Nhuận'] += profit
        if debt_kh > 1000: client_stats[client]['Đang Nợ'] += debt_kh
        client_stats[client]['Số Lô'] += 1

    # 4. KHỐI METRIC "SỨC KHỎE TÀI CHÍNH"
    st.markdown("### 💎 SỨC KHỎE TÀI CHÍNH")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 TỔNG LỢI NHUẬN", f"{total_profit:,.0f} ₫", help="Doanh thu - Chi Phí - Hoa hồng")
    m2.metric("💰 DOANH THU TRƯỚC VAT", f"{total_revenue:,.0f} ₫")
    m3.metric("🚨 NỢ PHẢI THU (KHÁCH)", f"{total_debt_kh:,.0f} ₫", delta="Cần đôn đốc đòi nợ", delta_color="inverse")
    m4.metric("💸 NỢ PHẢI TRẢ (ĐẠI LÝ VNĐ)", f"{total_debt_agent_vnd:,.0f} ₫", delta="Mình đang nợ", delta_color="inverse")

    st.markdown("---")

    # 5. BẢNG PHONG THẦN KHÁCH HÀNG (BIỂU ĐỒ)
    st.markdown("### 🏆 BẢNG PHONG THẦN KHÁCH HÀNG")
    if client_stats:
        df_clients = pd.DataFrame.from_dict(client_stats, orient='index').reset_index().rename(columns={'index': 'Khách Hàng'})
        
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.markdown("##### 🥇 TOP 5 LỢI NHUẬN CAO NHẤT")
            top_profit = df_clients.sort_values('Lợi Nhuận', ascending=False).head(5)
            st.bar_chart(top_profit.set_index('Khách Hàng')['Lợi Nhuận'], color="#2E7D32")
            
        with c_chart2:
            st.markdown("##### 🚨 TOP 5 NỢ ĐỌNG LỚN NHẤT")
            top_debt = df_clients[df_clients['Đang Nợ'] > 0].sort_values('Đang Nợ', ascending=False).head(5)
            if not top_debt.empty:
                st.bar_chart(top_debt.set_index('Khách Hàng')['Đang Nợ'], color="#C62828")
            else:
                st.success("Tuyệt vời! Không có khách hàng nào nợ đọng đáng kể trong kỳ này.")
    else:
        st.info("Chưa có dữ liệu khách hàng trong kỳ này.")

    st.markdown("---")

    # 6. HIỆU SUẤT VẬN HÀNH & ỦY THÁC
    st.markdown("### ⚙️ HIỆU SUẤT VẬN HÀNH & ỦY THÁC")
    
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        st.markdown("##### 📦 Tổng quan Lô Hàng")
        status_counts = {"Hoàn thành": 0, "Đang chạy": 0}
        for _, s in filtered_ships:
            if s.get('status') in ['done', 'Done', 'Hoàn thành']: status_counts["Hoàn thành"] += 1
            else: status_counts["Đang chạy"] += 1
            
        st.write(f"- 🚀 **Lô hàng mới mở trong kỳ:** {len(filtered_ships)} lô")
        st.write(f"- 🟢 **Đã hoàn thành xong:** {status_counts['Hoàn thành']} lô")
        st.write(f"- 🟡 **Đang xử lý dở dang:** {status_counts['Đang chạy']} lô")
        
        # Thống kê Task
        pending_tasks = len([t for t in tasks if not t.get('done', False)])
        st.warning(f"📌 **Team đang có {pending_tasks} đầu việc chưa hoàn thành!**")

    with col_op2:
        st.markdown("##### 💸 Tổng quan Thanh Toán Hộ (Ủy Thác)")
        filtered_proxies = []
        for payment in proxies.values():
            payment_date = parse_date_optional(payment.get("date"))
            if time_mode == "Tất cả" or (payment_date and start_date and end_date and start_date <= payment_date <= end_date):
                filtered_proxies.append(payment)
                
        if filtered_proxies:
            total_vnd_proxy = sum([safe_float(p.get("amount_vnd", 0)) for p in filtered_proxies])
            st.write(f"- 💰 **Tổng VNĐ nhận từ khách:** {total_vnd_proxy:,.0f} ₫")
            
            # Tính nợ Tệ
            df_proxy = pd.DataFrame(filtered_proxies)
            if 'currency' in df_proxy.columns:
                cny_rows = df_proxy[df_proxy['currency'] == 'CNY (¥)']
                cny_needed = cny_rows['amount_fc_needed'].map(safe_float).sum() if 'amount_fc_needed' in cny_rows.columns else 0
                cny_paid = cny_rows['amount_fc_paid'].map(safe_float).sum() if 'amount_fc_paid' in cny_rows.columns else 0
                cny_debt = cny_needed - cny_paid
                
                st.write(f"- 🇨🇳 **Tổng Tệ (CNY) khách yêu cầu chuyển:** {cny_needed:,.2f} ¥")
                st.write(f"- 🇨🇳 **Thực tế đã chuyển đi:** {cny_paid:,.2f} ¥")
                if cny_debt > 0:
                    st.error(f"⚠️ **CÒN PHẢI ĐI LỆNH CHUYỂN:** {cny_debt:,.2f} ¥")
                else:
                    st.success("✅ Không còn nợ lệnh chuyển tiền Tệ nào!")
        else:
            st.info("Không có phát sinh giao dịch Ủy thác nào trong kỳ.")
