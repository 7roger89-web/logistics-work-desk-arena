# FILE: core/gnt_utils.py
import pandas as pd
from docxtpl import DocxTemplate
from num2words import num2words
import io
import os
import streamlit as st
import re
from core.config import TREASURY_FILE_PATH, BASE_DIR

EXCEL_FILE = str(TREASURY_FILE_PATH)
WORD_TEMPLATE = str(BASE_DIR / "GNT_MAU.docx")

def clean_code(code):
    """Làm sạch mã: Chữ hoa, xóa mọi khoảng trắng"""
    if not code: return ""
    # Chuyển thành chuỗi, viết hoa
    s = str(code).upper()
    # Xóa toàn bộ khoảng trắng, xuống dòng
    s = re.sub(r'\s+', '', s)
    return s

def get_treasury_info(ma_hq_input):
    """
    Tra cứu thông tin Kho bạc dựa trên Mã HQ (Cột F)
    Lấy dữ liệu Tên CQ Thu (Cột D) và Tên KBNN (Cột K)
    """
    if not os.path.exists(EXCEL_FILE):
        return "", ""

    try:
        # 1. Đọc file Excel không cần Header (để kiểm soát chính xác vị trí)
        # dtype=str để đảm bảo mọi mã như 01E1 không bị hiểu nhầm
        df = pd.read_excel(EXCEL_FILE, header=None, dtype=str)
        
        # 2. Chuẩn hóa mã đầu vào
        target_code = clean_code(ma_hq_input)
        if not target_code: return "", ""

        # 3. Quét cột F (Index 5) từ dòng 7 trở đi (Dữ liệu bắt đầu từ dòng 7)
        # Cấu trúc file anh gửi: 
        # Cột D (Index 3): Tên CQ Thu
        # Cột F (Index 5): Mã HQ
        # Cột K (Index 10): Tên KBNN
        
        # Lấy vùng dữ liệu cần thiết
        col_hq_codes = df.iloc[6:, 5].astype(str) # Cột F, từ dòng 7 (index 6)
        
        # Tìm vị trí (Index) của mã HQ
        match_rows = col_hq_codes[col_hq_codes.apply(clean_code) == target_code]
        
        if not match_rows.empty:
            # Lấy index của dòng đầu tiên tìm thấy
            idx = match_rows.index[0]
            
            # Lấy dữ liệu từ các cột tương ứng tại dòng đó
            ten_cq = str(df.iloc[idx, 3]).strip()  # Cột D
            ten_kb = str(df.iloc[idx, 10]).strip() # Cột K
            
            # Xử lý nếu dữ liệu là nan
            if ten_cq.lower() == 'nan': ten_cq = ""
            if ten_kb.lower() == 'nan': ten_kb = ""
            
            return ten_cq, ten_kb
            
        return "", ""

    except Exception as e:
        # st.error(f"Lỗi đọc file Excel: {e}")
        return "", ""

def amount_to_text_vi(amount):
    """Đổi số sang chữ Tiếng Việt."""
    try:
        if float(amount or 0) == 0:
            return "Không đồng"
        text = num2words(amount, lang="vi")
        return text.capitalize() + " đồng./."
    except (ValueError, TypeError, NotImplementedError):
        from core.excel_gnt import doc_so_thanh_chu_vi
        return doc_so_thanh_chu_vi(amount)


def generate_gnt_doc(data):
    """Tạo Giấy Nộp Thuế Word từ template GNT_MAU.docx."""
    if not os.path.exists(WORD_TEMPLATE):
        raise FileNotFoundError(f"Không tìm thấy template Word: {WORD_TEMPLATE}")
    template = DocxTemplate(WORD_TEMPLATE)
    context = dict(data)
    tax_lines = list(context.get("ds_thue", []))
    total = sum(float(item.get("tien", 0) or 0) for item in tax_lines)
    context["tong_tien"] = total
    context["tong_tien_chu"] = amount_to_text_vi(total)
    context["ds_thue"] = tax_lines
    template.render(context)
    output = io.BytesIO()
    template.save(output)
    output.seek(0)
    return output
