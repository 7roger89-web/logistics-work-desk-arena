# FILE: views/sales.py
import streamlit as st
import pandas as pd
from datetime import date
from core.database import load_customers, load_rate_cards, save_rate_card
from core.config import GETFLY_SERVICES_LIST
from core.utils import safe_float

def ui_sales_module():
    st.title("🤝 QUẢN LÝ SALES & BÁO GIÁ KHUNG (RATE CARD)")
    st.caption("Quản lý báo giá cố định cho Khách hàng VIP, theo dõi biến động giá cước theo từng tháng.")
    
    if 'db_customers' not in st.session_state: 
        st.session_state.db_customers = load_customers()
    if 'db_rate_cards' not in st.session_state:
        st.session_state.db_rate_cards = load_rate_cards()

    t1, t2 = st.tabs(["👑 TẠO/CẬP NHẬT BÁO GIÁ KHUNG", "📈 LỊCH SỬ & BIẾN ĐỘNG GIÁ (%)"])

    # ====================================================================
    # TAB 1: TẠO VÀ CẬP NHẬT BÁO GIÁ CỐ ĐỊNH CHO THÁNG MỚI
    # ====================================================================
    with t1:
        with st.container(border=True):
            st.subheader("1. Thông tin Tuyến đường & Khách hàng")
            c1, c2, c3 = st.columns([1.5, 2, 1])
            
            cust_list = ["--Chọn Khách--"] + [v.get('name') for v in st.session_state.db_customers.values()]
            sel_cust = c1.selectbox("Khách hàng", cust_list)
            
            # Tên báo giá khung (Ví dụ: Tuyến nhập TQ - HP - Hưng Yên)
            rc_name = c2.text_input("Tên Báo Giá / Tuyến đường", placeholder="VD: Hàng Nhập TQ - Hưng Yên (Cont 40)")
            
            # Chọn tháng áp dụng
            rc_month = c3.text_input("Tháng áp dụng", value=date.today().strftime("%m/%Y"), help="Định dạng: MM/YYYY")

            if sel_cust != "--Chọn Khách--" and rc_name:
                st.divider()
                st.subheader(f"2. Cập nhật chi phí cho tháng {rc_month}")
                st.caption("Chỉ cần cập nhật những mục bị thay đổi giá (như Cước biển), các phí cố định cứ giữ nguyên.")
                
                # Tạo ID duy nhất cho Báo giá khung của khách này
                rc_id = f"RC_{sel_cust}_{rc_name}".replace(" ", "").upper()
                
                # Load dữ liệu tháng gần nhất (nếu có) để Sales không phải gõ lại
                existing_data = st.session_state.db_rate_cards.get(rc_id, {})
                history = existing_data.get('history', [])
                last_details = history[-1]['details'] if history else [
                    {"name": "Cước vận tải biển (O/F)", "cost": 0, "price": 0},
                    {"name": "Phí Local Charges", "cost": 0, "price": 0},
                    {"name": "Thủ tục Hải Quan", "cost": 0, "price": 0},
                    {"name": "Trucking nội địa", "cost": 0, "price": 0}
                ]

                # Giao diện nhập liệu dạng bảng (Data Editor)
                df_input = pd.DataFrame(last_details)
                edited_df = st.data_editor(
                    df_input, 
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "name": st.column_config.TextColumn("Tên Chi phí / Dịch vụ", width="large", required=True),
                        "cost": st.column_config.NumberColumn("Giá Vốn (NET)", format="%d ₫", step=10000),
                        "price": st.column_config.NumberColumn("Giá Bán (ALL IN)", format="%d ₫", step=10000)
                    }
                )

                # Tính tổng
                total_cost = edited_df['cost'].sum()
                total_price = edited_df['price'].sum()
                expected_profit = total_price - total_cost

                c_sum1, c_sum2, c_sum3 = st.columns(3)
                c_sum1.metric("💰 Tổng Giá Vốn", f"{total_cost:,.0f} ₫")
                c_sum2.metric("🎯 TỔNG BÁO GIÁ KHÁCH", f"{total_price:,.0f} ₫")
                c_sum3.metric("📈 Lợi nhuận dự kiến / Lô", f"{expected_profit:,.0f} ₫")

                if st.button(f"💾 LƯU BÁO GIÁ THÁNG {rc_month}", type="primary"):
                    new_month_data = {
                        "month": rc_month,
                        "total_cost": total_cost,
                        "total_price": total_price,
                        "profit": expected_profit,
                        "details": edited_df.to_dict('records'),
                        "updated_at": str(date.today())
                    }
                    
                    # Cập nhật lịch sử
                    is_updated = False
                    for h in history:
                        if h['month'] == rc_month:
                            h.update(new_month_data)
                            is_updated = True
                            break
                    if not is_updated:
                        history.append(new_month_data)
                        
                    # Sắp xếp lại history theo tháng
                    history = sorted(history, key=lambda x: x['month'][3:] + x['month'][:2])

                    rate_card_obj = {
                        "id": rc_id,
                        "customer": sel_cust,
                        "route_name": rc_name,
                        "history": history
                    }
                    
                    if save_rate_card(rate_card_obj):
                        st.session_state.db_rate_cards[rc_id] = rate_card_obj
                        st.success(f"✅ Đã chốt thành công báo giá khung tháng {rc_month} cho {sel_cust}!")
                    else:
                        st.error("Lỗi lưu dữ liệu!")

    # ====================================================================
    # TAB 2: LỊCH SỬ & BIẾN ĐỘNG GIÁ
    # ====================================================================
    with t2:
        st.subheader("📈 Lịch sử & Phân tích Biến động giá")
        
        all_rc = list(st.session_state.db_rate_cards.values())
        if not all_rc:
            st.info("Chưa có Báo giá khung nào được tạo.")
        else:
            # Chọn Báo giá khung để xem lịch sử
            rc_options = {rc['id']: f"{rc['customer']} - {rc['route_name']}" for rc in all_rc}
            sel_rc_id = st.selectbox("📌 Chọn Tuyến Báo Giá để phân tích:", list(rc_options.keys()), format_func=lambda x: rc_options[x])
            
            selected_rc = st.session_state.db_rate_cards[sel_rc_id]
            history = selected_rc.get('history', [])
            
            if len(history) > 0:
                # Tạo DataFrame lịch sử
                df_hist = pd.DataFrame(history)
                
                # Thuật toán tính Biến động (Tính chênh lệch % so với tháng liền trước)
                df_hist['Chênh lệch tiền'] = df_hist['total_price'].diff().fillna(0)
                df_hist['% Biến động'] = (df_hist['Chênh lệch tiền'] / df_hist['total_price'].shift(1) * 100).fillna(0)
                
                # Hiển thị Metric Trực quan cho tháng mới nhất
                latest = df_hist.iloc[-1]
                prev_price = df_hist.iloc[-2]['total_price'] if len(df_hist) > 1 else latest['total_price']
                
                st.markdown(f"#### Báo giá áp dụng hiện tại: Tháng **{latest['month']}**")
                m1, m2, m3 = st.columns(3)
                
                m1.metric(
                    "💵 Giá ALL-IN Tháng Này", 
                    f"{latest['total_price']:,.0f} ₫", 
                    f"{latest['Chênh lệch tiền']:,.0f} ₫ so với tháng trước",
                    delta_color="inverse" # Cước tăng thì màu đỏ (báo động), cước giảm màu xanh
                )
                
                pct_change = latest['% Biến động']
                m2.metric(
                    "📊 Tỷ lệ tăng/giảm cước", 
                    f"{pct_change:+.1f} %",
                    "Cước tăng mạnh" if pct_change > 5 else ("Cước giảm" if pct_change < 0 else "Ổn định"),
                    delta_color="inverse"
                )
                
                m3.metric("🎯 Lợi Nhuận Gộp (Margin)", f"{latest['profit']:,.0f} ₫")

                # Biểu đồ xu hướng giá
                st.divider()
                st.markdown("**📉 Biểu đồ xu hướng giá (Price Trend)**")
                chart_data = df_hist.set_index('month')[['total_price', 'total_cost']]
                st.line_chart(chart_data)

                # Bảng chi tiết Lịch sử
                st.markdown("**📋 Lịch sử chốt giá các tháng**")
                display_df = df_hist[['month', 'total_cost', 'total_price', 'profit', 'Chênh lệch tiền', '% Biến động']].copy()
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "month": "Tháng",
                        "total_cost": st.column_config.NumberColumn("Giá Vốn", format="%d ₫"),
                        "total_price": st.column_config.NumberColumn("Giá Bán Khách", format="%d ₫"),
                        "profit": st.column_config.NumberColumn("Lợi Nhuận", format="%d ₫"),
                        "Chênh lệch tiền": st.column_config.NumberColumn("Tăng/Giảm (+/-)", format="%d ₫"),
                        "% Biến động": st.column_config.NumberColumn("% Biến động", format="%.1f %%")
                    }
                )