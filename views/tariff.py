# FILE: views/tariff.py
import streamlit as st
import pandas as pd

from core.auth import can_operate_business
# Tắt giới hạn render khổng lồ của Pandas (Tiết kiệm RAM)
pd.set_option("styler.render.max_elements", 262144)

# Import trực tiếp để lỗi cấu trúc được phát hiện ngay khi khởi động.
from core.utils import fast_search_tariff, get_ai_response_hs_batch, safe_float

# =====================================================================
# WORKSPACE CBPG LƯU TẬP TRUNG TRÊN MONGODB
# =====================================================================
from core.database import load_cbpg_workspace, save_cbpg_workspace


CBPG_EXCLUSION_OPTIONS = {
    "Khác": ["Không"],
    "Ghế": [
        "Không",
        "Gỗ tự nhiên (hoàn toàn)",
        "Nhựa (hoàn toàn)",
        "Mây/Tre/Nứa (bộ phận chính)",
        "Chân nhôm (Ghế)",
        "Hàng rời (không đồng bộ)",
    ],
    "Bàn": [
        "Không",
        "Mặt bàn hình tròn",
        "Gỗ tự nhiên (hoàn toàn)",
        "Nhựa (hoàn toàn)",
        "Mây/Tre/Nứa (bộ phận chính)",
        "Hàng rời (không đồng bộ)",
    ],
}


def cbpg_exclusion_options(category: object) -> list[str]:
    """Return only exception criteria that apply to the selected category."""
    return CBPG_EXCLUSION_OPTIONS.get(str(category or "Khác").strip(), ["Không"])


def normalize_cbpg_items(items: object) -> tuple[list[dict], list[str]]:
    """Normalize dynamic editor rows and report repaired category values."""
    if not isinstance(items, list):
        return [], []
    normalized: list[dict] = []
    repairs: list[str] = []
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        category = str(row.get("Loại Hàng") or "Khác").strip()
        if category not in CBPG_EXCLUSION_OPTIONS:
            category = "Khác"
        row["ID"] = index
        row["Loại Hàng"] = category
        allowed = cbpg_exclusion_options(category)
        current = str(row.get("Ngoại trừ") or "Không").strip()
        if current not in allowed:
            if current not in {"", "Không"}:
                repairs.append(f"Dòng {index}: tiêu chí '{current}' không áp dụng cho {category} và đã chuyển về 'Không'.")
            current = "Không"
        row["Ngoại trừ"] = current
        row.setdefault("Tên Hàng", "")
        row.setdefault("Bằng chứng/Ghi chú", "")
        normalized.append(row)
    return normalized, repairs

def load_cbpg_data():
    return load_cbpg_workspace()

def save_cbpg_data(unit, invoice_total, items):
    return save_cbpg_workspace(unit, float(invoice_total), items)

# =====================================================================
# HÀM KIỂM TRA THUẾ CBPG (ÉP KIỂM DỮ LIỆU AN TOÀN 100%)
# =====================================================================
def check_cbpg_tax(row, unit):
    loai = str(row.get("Loại Hàng", "Khác")).strip()
    exclusion = str(row.get("Ngoại trừ", "Không")).strip()

    # 1. Nếu không phải bàn/ghế thì an toàn
    if loai not in ["Bàn", "Ghế"]:
        return False, 0.0, "0% (Không thuộc diện)"

    # 2. Ngoại trừ chỉ được chấp nhận khi có bằng chứng/chú thích kiểm tra.
    evidence = str(row.get("Bằng chứng/Ghi chú", "")).strip()
    if exclusion not in {"Không", ""} and evidence:
        return False, 0.0, f"0% sơ bộ (Ngoại trừ: {exclusion}; cần lưu chứng từ)"

    # 3. Đọc và ép kiểu an toàn tránh lỗi string so với float
    raw_dai = safe_float(row.get("Dài", 0))
    raw_rong = safe_float(row.get("Rộng", 0))
    raw_cao_min = safe_float(row.get("Cao Min", row.get("Cao", 0)))
    raw_cao_max = safe_float(row.get("Cao Max", 0))
    raw_day = safe_float(row.get("Dày mặt", 0))
    
    # Quy đổi tất cả về chuẩn mm để so sánh chính xác theo văn bản luật
    if unit == "cm":
        dai = raw_dai * 10
        rong = raw_rong * 10
        cao_min = raw_cao_min * 10
        cao_max = raw_cao_max * 10
        day = raw_day * 10
    elif unit == "m":
        dai = raw_dai * 1000
        rong = raw_rong * 1000
        cao_min = raw_cao_min * 1000
        cao_max = raw_cao_max * 1000
        day = raw_day * 1000
    else: # Mặc định là mm
        dai = raw_dai
        rong = raw_rong
        cao_min = raw_cao_min
        cao_max = raw_cao_max
        day = raw_day
    
    # 4. Logic cho sản phẩm BÀN (Thuế 35.20%)
    if loai == "Bàn":
        if cao_max > 0 and (cao_max - cao_min >= 95):
            return False, 0.0, "0% (Ngoại trừ: Đ/C độ cao >= 95mm)"

        cond_dai = 990 <= dai <= 3210
        cond_rong = 590 <= rong <= 1410
        cond_cao = 675 <= cao_min <= 770
        cond_day = 12 <= day <= 85
        
        if cond_dai and cond_rong and cond_cao and cond_day:
            return True, 0.352, "35.20% (CBPG Bàn)"
        return False, 0.0, "0% (Kích thước an toàn)"
        
    # 5. Logic cho sản phẩm GHẾ (Thuế 21.40%)
    elif loai == "Ghế":
        if cao_max >= 600:
            return False, 0.0, "0% (Ngoại trừ: Max độ cao >= 600mm)"
            
        if 450 < cao_min < 600:
            return True, 0.214, "21.40% (CBPG Ghế)"
        return False, 0.0, "0% (Kích thước an toàn)"
        
    return False, 0.0, "0% (Lỗi phân loại)"

# =====================================================================
# GIAO DIỆN CHÍNH
# =====================================================================
def ui_super_tariff_hub():
    can_edit = can_operate_business("tariff")
    st.title("🌏 TRA CỨU THUẾ & TỐI ƯU CBPG")
    st.caption("Công cụ hỗ trợ tra cứu và kiểm tra sơ bộ; kết quả phải được chuyên viên hải quan xác nhận trước khi khai báo.")
    
    st.markdown("""
    <style>
        .stTextArea textarea { font-size: 14px; font-family: monospace; }
        div[data-testid="stDataEditor"] table { font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

    t_cbpg, t_sql, t_ai = st.tabs([
        "⚖️ Tối Ưu Thuế CBPG (Auto-Balance)", 
        "⚡ Tra Cứu Thuế Nhanh (SQL)", 
        "🤖 AI Phân Tích HS"
    ])
    
    # -----------------------------------------------------------------
    # TAB 1: TỐI ƯU CBPG VÀ TỰ ĐỘNG CÂN BẰNG GIÁ
    # -----------------------------------------------------------------
    with t_cbpg:
        st.markdown("### 🛠️ CÔNG CỤ ĐIỀU CHỈNH GIÁ KHAI BÁO HẢI QUAN")
        st.warning("Bộ quy tắc hiện tại là công cụ sàng lọc nội bộ. Phải đối chiếu văn bản đang có hiệu lực và hồ sơ kỹ thuật trước khi khai báo.")
        
        saved_data = load_cbpg_data()
        
        if 'cbpg_items' not in st.session_state:
            if saved_data:
                st.session_state.cbpg_unit = saved_data.get("unit", "mm")
                st.session_state.cbpg_total_inv = saved_data.get("invoice_total", 0.0)
                st.session_state.cbpg_items = saved_data.get("items", [])
            else:
                st.session_state.cbpg_unit = "mm"
                st.session_state.cbpg_total_inv = 0.0
                st.session_state.cbpg_items = [
                    {"ID": 1, "Loại Hàng": "Khác", "Tên Hàng": "", "Ngoại trừ": "Không", "Bằng chứng/Ghi chú": "", "Dài": 0, "Rộng": 0, "Cao Min": 0, "Cao Max": 0, "Dày mặt": 0, "Giá Khai Báo ($)": 0.0}
                ]

        c1, c2 = st.columns([1.5, 3])
        unit_choice = c1.selectbox("📏 Chọn đơn vị đo chung:", ["mm", "cm", "m"], index=["mm", "cm", "m"].index(st.session_state.cbpg_unit))
        st.session_state.cbpg_unit = unit_choice
        
        total_invoice_input = c2.number_input("💰 TỔNG TRỊ GIÁ INVOICE GỐC ($)", value=st.session_state.cbpg_total_inv, step=100.0, format="%.2f")
        st.session_state.cbpg_total_inv = total_invoice_input
        
        # 1. Chuẩn hóa dữ liệu thô từ session state trước khi dựng editor.
        normalized_items, initial_repairs = normalize_cbpg_items(st.session_state.cbpg_items)
        st.session_state.cbpg_items = normalized_items
        df = pd.DataFrame(normalized_items)
        if df.empty:
            df = pd.DataFrame(columns=[
                "ID", "Loại Hàng", "Tên Hàng", "Ngoại trừ", "Bằng chứng/Ghi chú",
                "Dài", "Rộng", "Cao Min", "Cao Max", "Dày mặt", "Giá Khai Báo ($)",
            ])
        if initial_repairs:
            for repair in initial_repairs:
                st.warning(repair)
        
        # 2. Tự động tính toán trước kết quả kiểm tra thuế cho từng dòng để đưa vào DataFrame hiển thị trực tiếp
        status_list = []
        is_taxed_list = []
        for _, row in df.iterrows():
            is_taxed, rate, desc = check_cbpg_tax(row, unit_choice)
            status_list.append("❌ BỊ THUẾ " + desc if is_taxed else "✅ " + desc)
            is_taxed_list.append(is_taxed)
            
        if not df.empty:
            df["ID"] = range(1, len(df) + 1)
        df["Kết Quả Check Thuế"] = status_list

        st.markdown("#### 📝 CHI TIẾT DÒNG HÀNG & KẾT QUẢ QUÉT CBPG")
        
        # 3. Hiển thị bảng dòng hàng. Ngoại trừ được khóa trong bảng và chọn
        # bằng control theo từng dòng để danh sách lựa chọn phụ thuộc Loại Hàng.
        edited_df = st.data_editor(
            df,
            column_config={
                "ID": st.column_config.NumberColumn("STT", width="small", format="%d", disabled=True),
                "Loại Hàng": st.column_config.SelectboxColumn("Loại", options=["Ghế", "Bàn", "Khác"], required=True),
                "Tên Hàng": st.column_config.TextColumn("Tên chi tiết"),
                "Ngoại trừ": st.column_config.TextColumn("Tiêu chí Ngoại trừ", disabled=True, help="Chọn ở phần tiêu chí theo dòng bên dưới; danh sách phụ thuộc Loại Hàng."),
                "Bằng chứng/Ghi chú": st.column_config.TextColumn("Bằng chứng ngoại trừ", help="Số catalogue, ảnh, thông số hoặc tài liệu dùng để xác minh"),
                "Dài": st.column_config.NumberColumn(f"Dài ({unit_choice})"),
                "Rộng": st.column_config.NumberColumn(f"Rộng ({unit_choice})"),
                "Cao Min": st.column_config.NumberColumn(f"Cao Min/Cao ({unit_choice})", help="Bàn: Cao mặt bàn. Ghế: Mức ghế thấp nhất."),
                "Cao Max": st.column_config.NumberColumn(f"Cao Max ({unit_choice})", help="Dùng nếu có Đ/C độ cao. Mức vươn cao nhất."),
                "Dày mặt": st.column_config.NumberColumn(f"Dày mặt ({unit_choice})", help="Chỉ dùng cho Bàn"),
                "Giá Khai Báo ($)": st.column_config.NumberColumn("Giá Khai Báo ($) ✏️", format="%.2f", required=True),
                "Kết Quả Check Thuế": st.column_config.TextColumn("🛡️ Trạng thái CBPG", disabled=True, width="medium")
            },
            num_rows="dynamic", use_container_width=True, hide_index=True, key="cbpg_items_editor_v2"
        )

        edited_items, editor_repairs = normalize_cbpg_items(edited_df.to_dict("records"))
        for repair in editor_repairs:
            st.warning(repair)
        edited_df = pd.DataFrame(edited_items)
        required_columns = [
            "ID", "Loại Hàng", "Tên Hàng", "Ngoại trừ", "Bằng chứng/Ghi chú",
            "Dài", "Rộng", "Cao Min", "Cao Max", "Dày mặt", "Giá Khai Báo ($)",
        ]
        defaults = {
            "ID": 0,
            "Loại Hàng": "Khác",
            "Tên Hàng": "",
            "Ngoại trừ": "Không",
            "Bằng chứng/Ghi chú": "",
            "Dài": 0,
            "Rộng": 0,
            "Cao Min": 0,
            "Cao Max": 0,
            "Dày mặt": 0,
            "Giá Khai Báo ($)": 0.0,
        }
        for column in required_columns:
            if column not in edited_df:
                edited_df[column] = defaults[column]

        st.markdown("**Tiêu chí Ngoại trừ theo từng dòng**")
        if edited_df.empty:
            st.caption("Chưa có dòng hàng. Hãy thêm dòng trong bảng phía trên.")
        else:
            for row_index, row in edited_df.iterrows():
                category = str(row.get("Loại Hàng") or "Khác")
                options = cbpg_exclusion_options(category)
                current = str(row.get("Ngoại trừ") or "Không")
                selected_index = options.index(current) if current in options else 0
                selected = st.selectbox(
                    f"STT {int(row.get('ID') or row_index + 1)} — {category}",
                    options,
                    index=selected_index,
                    key=f"cbpg_exclusion_{row_index}_{int(row.get('ID') or row_index + 1)}",
                    help="Chỉ hiển thị các tiêu chí phù hợp với loại hàng đang chọn.",
                )
                edited_df.at[row_index, "Ngoại trừ"] = selected

        edited_items, post_editor_repairs = normalize_cbpg_items(edited_df.to_dict("records"))
        for repair in post_editor_repairs:
            st.warning(repair)
        edited_df = pd.DataFrame(edited_items)
        st.session_state.cbpg_items = edited_items
        if not edited_df.empty:
            current_status = []
            current_taxed = []
            for _, row in edited_df.iterrows():
                is_taxed, _, desc = check_cbpg_tax(row, unit_choice)
                current_status.append("❌ BỊ THUẾ " + desc if is_taxed else "✅ " + desc)
                current_taxed.append(is_taxed)
            edited_df["Kết Quả Check Thuế"] = current_status
            st.dataframe(
                edited_df[["ID", "Loại Hàng", "Ngoại trừ", "Kết Quả Check Thuế"]],
                use_container_width=True,
                hide_index=True,
            )

        # Cập nhật lại danh sách is_taxed dựa trên dữ liệu mới nhất người dùng vừa sửa trên bảng
        final_is_taxed_list = []
        for _, row in edited_df.iterrows():
            is_taxed, _, _ = check_cbpg_tax(row, unit_choice)
            final_is_taxed_list.append(is_taxed)

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
        
        if col_btn1.button(
            "💾 LƯU DỮ LIỆU ĐANG NHẬP",
            use_container_width=True,
            disabled=not can_edit,
        ):
            items_to_save = edited_df.drop(columns=["Kết Quả Check Thuế"], errors="ignore").to_dict('records')
            st.session_state.cbpg_items = items_to_save
            if save_cbpg_data(unit_choice, total_invoice_input, items_to_save):
                st.success("✅ Đã lưu thành công dữ liệu!")
            else:
                st.error("Lỗi lưu file.")

        if col_btn2.button(
            "🔄 TỰ ĐỘNG PHÂN BỔ (AUTO-BALANCE)",
            type="primary",
            use_container_width=True,
            disabled=edited_df.empty or not can_edit,
        ):
            new_prices = edited_df["Giá Khai Báo ($)"].tolist()
            safe_indices = [i for i, taxed in enumerate(final_is_taxed_list) if not taxed]
            taxed_indices = [i for i, taxed in enumerate(final_is_taxed_list) if taxed]
            
            if not safe_indices:
                st.error("⚠️ Toàn bộ các dòng hàng đều dính thuế CBPG! Không tìm thấy dòng an toàn để dồn giá trị.")
            else:
                sum_taxed = sum([new_prices[i] for i in taxed_indices])
                target_safe_sum = total_invoice_input - sum_taxed
                
                if target_safe_sum <= 0:
                    st.error(f"❌ VÔ LÝ: Tổng giá trị các dòng BỊ THUẾ ({sum_taxed:,.2f}$) đang lớn hơn hoặc bằng Tổng Invoice ({total_invoice_input:,.2f}$). Hãy điều chỉnh giảm giá trị dòng bị thuế!")
                else:
                    current_safe_sum = sum([new_prices[i] for i in safe_indices])
                    for idx in safe_indices:
                        weight = (new_prices[idx] / current_safe_sum) if current_safe_sum > 0 else (1.0 / len(safe_indices))
                        new_prices[idx] = target_safe_sum * weight
                    
                    updated_items = edited_df.drop(columns=["Kết Quả Check Thuế"], errors="ignore").to_dict('records')
                    for i, item in enumerate(updated_items):
                        item["Giá Khai Báo ($)"] = new_prices[i]
                    
                    st.session_state.cbpg_items = updated_items
                    save_cbpg_data(unit_choice, total_invoice_input, updated_items)
                    st.success("Đã phân bổ lại giá trị và giữ tổng Invoice trong sai số làm tròn.")
                    st.rerun()

        if col_btn3.button(
            "🗑️ XÓA DỮ LIỆU (TẠO LÔ MỚI)",
            use_container_width=True,
            disabled=not can_edit,
        ):
            default_items = [{"ID": 1, "Loại Hàng": "Khác", "Tên Hàng": "", "Ngoại trừ": "Không", "Bằng chứng/Ghi chú": "", "Dài": 0, "Rộng": 0, "Cao Min": 0, "Cao Max": 0, "Dày mặt": 0, "Giá Khai Báo ($)": 0.0}]
            st.session_state.cbpg_items = default_items
            save_cbpg_data(unit_choice, 0.0, default_items)
            st.rerun()

        st.divider()
        current_prices = edited_df["Giá Khai Báo ($)"].tolist()
        sum_val = sum(current_prices)
        
        total_tax_amount = sum([safe_float(row["Giá Khai Báo ($)"]) * check_cbpg_tax(row, unit_choice)[1] for _, row in edited_df.iterrows() if check_cbpg_tax(row, unit_choice)[0]])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng đang khai báo", f"{sum_val:,.2f} $", delta=f"Lệch: {sum_val - total_invoice_input:,.2f} $" if abs(sum_val - total_invoice_input) > 0.01 else "Khớp 100%", delta_color="inverse" if abs(sum_val - total_invoice_input) > 0.01 else "normal")
        m2.metric("Thuế CBPG phải nộp", f"{total_tax_amount:,.2f} $")
        with m3:
            if total_tax_amount > 0:
                st.error("⚠️ Có dấu hiệu phát sinh CBPG theo bộ quy tắc hiện tại")
            else:
                st.info("Không phát hiện theo bộ quy tắc hiện tại; vẫn cần chuyên viên xác nhận")

    # -----------------------------------------------------------------
    # TAB 2: TRA CỨU SQL SIÊU TỐC
    # -----------------------------------------------------------------
    with t_sql:
        st.markdown("### ⚡ Động cơ Tra Cứu Biểu Thuế 2026")
        st.info("💡 Hệ thống sử dụng kiến trúc **Search-First**. Rất nhẹ và không tốn RAM.")
        
        search_term = st.text_input("🔍 Nhập Mã HS hoặc Tên hàng hóa (Ví dụ: 9401, ghế gỗ...):", placeholder="Gõ từ khóa vào đây...")
        
        if search_term and len(search_term.strip()) >= 2:
            with st.spinner("Đang chọc vào DB lấy dữ liệu..."):
                display_df = fast_search_tariff(search_term, limit=100)
            
            if not display_df.empty:
                display_df = display_df.fillna("").astype(str).replace(["None", "nan", "NaN", "null", "<NA>"], "")
                bold_columns = [col for col in display_df.columns if col.lower() in ['thuế nk', 'acfta', 'import_tax', 'thuế nhập khẩu']]
                
                if bold_columns:
                    styled_df = display_df.style.set_properties(
                        subset=bold_columns, 
                        **{'font-weight': 'bold', 'color': '#0F2C59', 'background-color': '#F4F6F9'}
                    )
                else:
                    styled_df = display_df

                st.dataframe(styled_df, use_container_width=True, hide_index=True, height=500)
                st.caption(f"⚡ Đã tìm thấy {len(display_df)} kết quả liên quan nhất.")
            else:
                st.warning("📭 Không tìm thấy kết quả nào phù hợp. Hãy thử từ khóa khác ngắn gọn hơn!")
                
        elif search_term:
            st.warning("⚠️ Vui lòng gõ ít nhất 2 ký tự để hệ thống bắt đầu quét.")
        else:
            st.markdown("""
            <div style='text-align:center; padding: 50px 20px; border: 2px dashed var(--border-color); border-radius: 10px; margin-top: 20px;'>
                <h2 style='color: var(--text-color); opacity:0.3;'>BẢNG DỮ LIỆU ĐANG TRỐNG</h2>
                <p style='color: var(--text-color); opacity:0.5;'>Hãy gõ mã HS hoặc tên hàng hóa vào ô tìm kiếm bên trên.</p>
            </div>
            """, unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # TAB 3: TRỢ LÝ AI (HÀNG LOẠT)
    # -----------------------------------------------------------------
    with t_ai:
        st.markdown("### 🕵️ Trợ lý HS Code (Nhập liệu dạng bảng)")
        
        if 'hs_input_df' not in st.session_state:
            st.session_state.hs_input_df = pd.DataFrame([{"Tên hàng (Paste vào đây)": ""} for _ in range(10)])

        st.info("💡 Mẹo: Copy cột tên hàng từ Excel bên ngoài, click vào ô đầu tiên bên dưới và ấn `Ctrl+V`.")
        
        edited_input = st.data_editor(
            st.session_state.hs_input_df, num_rows="dynamic", use_container_width=True,
            key="editor_hs_input", height=300,
            column_config={
                "Tên hàng (Paste vào đây)": st.column_config.TextColumn("Mô tả hàng hóa (Input)", width="large", required=True)
            }
        )

        c_act, c_res = st.columns([1, 4])
        with c_act:
            if st.button("🚀 Phân Tích Ngay", type="primary", use_container_width=True):
                input_list = [str(row.get("Tên hàng (Paste vào đây)", "")).strip() for index, row in edited_input.iterrows() if str(row.get("Tên hàng (Paste vào đây)", "")).strip()]
                
                if input_list:
                    final_input_str = "\n".join([f"{i+1}. {item}" for i, item in enumerate(input_list)])
                    with st.spinner("Đang phân tích và kiểm tra structured output..."):
                        try:
                            json_data = get_ai_response_hs_batch(final_input_str)
                            st.session_state.ai_hs_result = pd.DataFrame(json_data)
                        except RuntimeError as exc:
                            st.error(str(exc))
                else:
                    st.warning("⚠️ Bảng dữ liệu đang trống.")

            if st.button("🗑️ Xóa dữ liệu", use_container_width=True):
                st.session_state.hs_input_df = pd.DataFrame([{"Tên hàng (Paste vào đây)": ""} for _ in range(10)])
                st.session_state.ai_hs_result = pd.DataFrame()
                st.rerun()

        if 'ai_hs_result' not in st.session_state:
            st.session_state.ai_hs_result = pd.DataFrame()

        if not st.session_state.ai_hs_result.empty:
            st.divider()
            st.markdown("### 🏁 Kết quả Phân tích")
            res_editor = st.data_editor(
                st.session_state.ai_hs_result, use_container_width=True, num_rows="dynamic", height=500,
                column_config={
                    "stt": st.column_config.NumberColumn("STT", width="small"),
                    "input_name": st.column_config.TextColumn("Tên hàng Input", width="medium"),
                    "hs_code": st.column_config.TextColumn("Mã HS", width="small"),
                    "vnaccs_name": st.column_config.TextColumn("Tên VNACCS", width="large"),
                    "english_name": st.column_config.TextColumn("Tên Tiếng Anh", width="large"),
                    "rule": st.column_config.TextColumn("Quy tắc", width="small"),
                    "reasoning": st.column_config.TextColumn("Giải trình", width="large"),
                    "note": st.column_config.TextColumn("Ghi chú", width="medium"),
                    "confidence": st.column_config.NumberColumn("Độ tin cậy", min_value=0.0, max_value=1.0, format="%.2f"),
                    "requires_human_review": st.column_config.CheckboxColumn("Cần chuyên viên duyệt"),
                    "missing_information": st.column_config.TextColumn("Thông tin còn thiếu", width="large"),
                }
            )
            csv = res_editor.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Xuất kết quả (Excel/CSV)", csv, "HS_Code_Result.csv", "text/csv", type="primary")
