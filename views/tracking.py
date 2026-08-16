import streamlit as st
from core.config import CARRIER_LINKS
from core.utils import get_tracking_url

def ui_tracking_tool():
    st.title("🌐 TRA CỨU HÀNH TRÌNH (TRACKING)")
    with st.container(border=True):
        track_type = st.radio("Loại hình:", ["Đường Biển (Container)", "Chuyển Phát Nhanh (Express)", "Hàng Không (Air)"], horizontal=True)
        c_tr1, c_tr2 = st.columns([3, 1])
        if track_type == "Đường Biển (Container)":
            carrier = c_tr1.selectbox("Hãng tàu:", ["Maersk", "MSC", "CMA CGM", "COSCO", "Evergreen", "ONE", "Hapag-Lloyd", "Wan Hai", "SITC"])
            ref_no = c_tr2.text_input("Số Bill / Cont:")
        elif track_type == "Chuyển Phát Nhanh (Express)":
            carrier = c_tr1.selectbox("Hãng CPN:", ["DHL", "FedEx", "UPS"])
            ref_no = c_tr2.text_input("Tracking Number:")
        else:
            carrier = c_tr1.text_input("Hãng hàng không (VD: Vietnam Airlines):", "Vietnam Airlines")
            ref_no = c_tr2.text_input("Số AWB (Mawb):")
            
        if st.button("🔎 Tra cứu ngay", type="primary"):
            if ref_no:
                url = get_tracking_url(carrier, ref_no)
                st.success(f"Đang mở trang tracking của {carrier}...")
                st.markdown(f"**[Click vào đây để mở liên kết Tracking]({url})**", unsafe_allow_html=True)
            else: st.warning("Vui lòng nhập số vận đơn/container.")