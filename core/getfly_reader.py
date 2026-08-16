# FILE: core/getfly_reader.py
import pandas as pd
import streamlit as st
from core.utils import safe_float
from core.logic import calculate_from_shipment

def process_getfly_excel(file_path_or_buffer):
    """Đọc file DSDH GetFly, tự động map cột chi tiết sản phẩm và cột Mô Tả"""
    try:
        df = pd.read_excel(file_path_or_buffer, engine='openpyxl', dtype=str)
        df.columns = df.columns.str.strip()
        
        target_cols = {
            "order_id": ["mã đh", "mã đơn hàng"],
            "order_date": ["ngày đặt hàng", "ngày tạo"],
            "customer_name": ["tên kh", "khách hàng"],
            "product_code": ["mã sp", "mã sản phẩm", "mã hàng"],
            "product_name": ["tên sp", "tên sản phẩm", "tên hàng"],
            "product_note": ["mô tả"], # ĐÃ BẮT CỘT MÔ TẢ CỦA GETFLY
            "qty": ["số lượng", "sl"],
            "cost": ["giá vốn", "đơn giá nhập", "giá nhập"],
            "price": ["đơn giá", "đơn giá bán", "giá bán"],
            "revenue": ["thành tiền", "tổng tiền"], # Thành tiền của từng line
            "profit": ["lợi nhuận sp", "lợi nhuận"],
            "status": ["trạng thái"]
        }
        
        rename_dict = {}
        for target, keywords in target_cols.items():
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    rename_dict[col] = target
                    break  
                    
        df.rename(columns=rename_dict, inplace=True)
        df = df.loc[:, ~df.columns.duplicated()]
        
        if 'order_id' not in df.columns:
            return None, "⚠️ File Excel không đúng chuẩn (Thiếu cột Mã Đơn Hàng)."

        # Lấp ô trống do Merge Cell (Bản chất file GetFly là các dòng dưới bị rỗng thông tin Đơn hàng)
        fill_cols = ['order_id', 'order_date', 'customer_name']
        for c in fill_cols:
            if c in df.columns: df[c] = df[c].ffill()

        numeric_cols = ['qty', 'cost', 'price', 'revenue', 'profit']
        for c in numeric_cols:
            if c in df.columns:
                # safe_float hỗ trợ cả 1,234,567 và 1.234.567 theo định dạng Việt Nam.
                df[c] = df[c].map(safe_float)

        return df, None
    except Exception as e:
        return None, f"⚠️ Lỗi đọc file: {e}"

def get_kpi_summary(df):
    if df is None or df.empty: return 0, 0, 0
    total_rev = df['revenue'].sum() if 'revenue' in df.columns else 0
    total_profit = df['profit'].sum() if 'profit' in df.columns else 0
    total_orders = df['order_id'].nunique() if 'order_id' in df.columns else 0
    return total_rev, total_profit, total_orders

def cross_check_with_app(df_getfly, app_shipments):
    """
    Đóng gói chi tiết TỪNG DÒNG DỊCH VỤ, map 'Mô Tả' vào 'Ghi Chú'
    """
    if df_getfly is None or df_getfly.empty or 'order_id' not in df_getfly.columns: 
        return []

    discrepancies = []
    unique_orders = df_getfly['order_id'].unique()

    for oid in unique_orders:
        oid = str(oid).strip()
        order_rows = df_getfly[df_getfly['order_id'] == oid]
        
        c_name = str(order_rows.iloc[0].get('customer_name', '')).strip()
        c_date = str(order_rows.iloc[0].get('order_date', '')).strip()
        gf_rev = safe_float(order_rows['revenue'].sum() if 'revenue' in order_rows.columns else 0)
        
        details_list = []
        for _, row in order_rows.iterrows():
            p_code = str(row.get('product_code', 'DVK')).strip()
            p_name = str(row.get('product_name', 'Dịch vụ khác')).strip()
            
            # Xử lý Cột Mô tả -> Ghi chú
            p_note = str(row.get('product_note', '')).strip()
            if p_note.lower() in ['nan', 'none', 'null']: p_note = ''
            
            name_full = f"{p_name} ({p_code})" if p_code and p_code.lower() != 'nan' else p_name
            
            details_list.append({
                "name_full": name_full,
                "qty": safe_float(row.get('qty', 1)),
                "cost": safe_float(row.get('cost', 0)),
                "price": safe_float(row.get('price', 0)) if 'price' in row else safe_float(row.get('revenue',0)),
                "vat_line": 0,
                "note": p_note # MÔ TẢ ĐƯỢC MAP THÀNH GHI CHÚ
            })
            
        if oid in app_shipments:
            app_ship = app_shipments[oid]
            app_rev = safe_float(calculate_from_shipment(app_ship).get('receivable', 0))
            
            diff = abs(gf_rev - app_rev)
            if diff > 1000:
                discrepancies.append({
                    "Mã Lô (GetFly)": oid, "Khách Hàng": c_name, "Ngày Tạo": c_date,
                    "Trạng thái": "🔴 Lệch Doanh Thu", "Doanh Thu GetFly": gf_rev,
                    "Doanh Thu Trên App": app_rev, "Độ Lệch": gf_rev - app_rev,
                    "details": details_list 
                })
        else:
            discrepancies.append({
                "Mã Lô (GetFly)": oid, "Khách Hàng": c_name, "Ngày Tạo": c_date,
                "Trạng thái": "⚠️ Lọt lưới (Chưa tạo trên App)", "Doanh Thu GetFly": gf_rev,
                "Doanh Thu Trên App": 0, "Độ Lệch": gf_rev,
                "details": details_list 
            })
            
    return discrepancies