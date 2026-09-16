# FILE: core/getfly_reader.py
import math
import re

import pandas as pd
import streamlit as st
from core.utils import safe_float
from core.logic import calculate_from_shipment

#: GetFly's own customer-code column ("Mã KH" in the DSDH sheet). It is
#: intentionally kept beside the shared map so the real XLSX path and the
#: existing pasted-customer helper use the same identity vocabulary.
GETFLY_CUSTOMER_CODE_KEYWORDS = ["mã kh", "ma kh", "mã khách hàng"]

#: The ONE GetFly column-identity map of this repository (LOGI_CONTRACT_AND_-
#: SHIPMENT_CORE_GAPS_01). `process_getfly_excel` below reads it verbatim, and
#: `customer_rows_from_text` reuses the SAME keywords, so a pasted GetFly table
#: and an uploaded GetFly file can never drift into two different mappings.
#: Keyword matching is case-insensitive on a whitespace-stripped header cell.
GETFLY_COLUMN_KEYWORDS = {
    "order_id": ["mã đh", "mã đơn hàng"],
    "order_date": ["ngày đặt hàng", "ngày tạo"],
    "customer_name": ["tên kh", "khách hàng"],
    "customer_code": GETFLY_CUSTOMER_CODE_KEYWORDS,
    "product_code": ["mã sp", "mã sản phẩm", "mã hàng"],
    "product_name": ["tên sp", "tên sản phẩm", "tên hàng"],
    "product_note": ["mô tả"],  # ĐÃ BẮT CỘT MÔ TẢ CỦA GETFLY
    "qty": ["số lượng", "sl"],
    "cost": ["giá vốn", "đơn giá nhập", "giá nhập"],
    "price": ["đơn giá", "đơn giá bán", "giá bán"],
    "revenue": ["thành tiền", "tổng tiền"],  # Thành tiền của từng line
    "profit": ["lợi nhuận sp", "lợi nhuận"],
    "status": ["trạng thái"]
}


def _optional_getfly_number(value) -> float | None:
    """Parse a source number without collapsing UNKNOWN into zero.

    The legacy dashboard can still call ``safe_float`` on the returned frame,
    but the real import preview must distinguish an empty/invalid price from an
    explicit numeric zero before it offers Finance Actual import.
    """
    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "null", "-"} or not any(ch.isdigit() for ch in raw):
        return None
    parsed = safe_float(value)
    try:
        parsed_float = float(parsed)
    except (TypeError, ValueError):
        return None
    return parsed_float if math.isfinite(parsed_float) else None


def process_getfly_excel(file_path_or_buffer):
    """Đọc file DSDH GetFly, tự động map cột chi tiết sản phẩm và cột Mô Tả"""
    try:
        df = pd.read_excel(file_path_or_buffer, engine='openpyxl', dtype=str)
        df.columns = df.columns.str.strip()

        target_cols = GETFLY_COLUMN_KEYWORDS

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
            if c not in df.columns:
                continue
            # Do this explicitly instead of pandas ffill(): pandas 2.3 warns
            # about implicit object downcasting, and the explicit loop keeps a
            # genuinely missing leading value as UNKNOWN.
            carried = None
            filled = []
            for value in df[c].tolist():
                missing = value is None
                if not missing:
                    try:
                        missing = bool(pd.isna(value))
                    except (TypeError, ValueError):
                        missing = False
                if missing:
                    filled.append(carried)
                else:
                    carried = value
                    filled.append(value)
            df[c] = pd.Series(filled, index=df.index, dtype=object)

        numeric_cols = ['qty', 'cost', 'price', 'revenue', 'profit']
        for c in numeric_cols:
            if c in df.columns:
                # Keep an explicit 0 as 0, but retain blank/invalid source facts
                # as None so the real import can refuse a financial line instead
                # of silently booking UNKNOWN as zero.
                df[c] = df[c].map(_optional_getfly_number)

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

def _matched_key(header_cell: str, keywords) -> bool:
    """True when one header cell carries one of the GetFly keywords."""
    raw = str(header_cell or "").strip().lower()
    return bool(raw) and any(keyword in raw for keyword in keywords)


def _split_line(line: str) -> list[str]:
    """Split one pasted table row on tabs, falling back to ; / , separators.

    Copying cells out of the GetFly .xlsx yields TAB-separated text; a manually
    typed row uses "; " (the format views/../Customers.tsx import already uses).
    Tab wins whenever it is present so a name containing a comma is never cut.
    """
    if "\t" in line:
        return [cell.strip() for cell in line.split("\t")]
    return [cell.strip() for cell in re.split(r"[;,]", line)]


def _index_columns(header: list[str]) -> dict[str, int]:
    """Map the GetFly fields this extraction needs onto pasted column indexes."""
    index: dict[str, int] = {}
    for position, cell in enumerate(header):
        for target in ("customer_name", "order_id", "order_date"):
            if target not in index and _matched_key(cell, GETFLY_COLUMN_KEYWORDS[target]):
                index[target] = position
        if "customer_code" not in index and _matched_key(cell, GETFLY_CUSTOMER_CODE_KEYWORDS):
            index["customer_code"] = position
    return index


def _clean(value: str) -> str:
    raw = str(value or "").strip()
    return "" if raw.lower() in {"nan", "none", "null", "-"} else raw


def customer_rows_from_text(text: str) -> dict:
    """Extract what a GetFly DSDH table really carries about a CUSTOMER.

    GetFly's order table carries customer identity (``Tên KH`` / ``Mã KH``) and
    order facts (``Mã ĐH`` / ``Ngày đặt hàng``). It carries NO contract number,
    NO buyer-company legal record and NO MST for the counterparty — so this
    function returns ONLY the customer rows the existing canonical
    ``customer_import`` path can honestly persist, plus the order ids it saw.

    Fail-closed by design: no header line that matches a GetFly keyword means no
    guessed column positions; a row missing either the customer code or the
    customer name is reported as skipped instead of being given an invented id.
    """
    lines = [line for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
             if line.strip()]
    result = {"rows": [], "orders": [], "skipped": [], "columns": [],
              "header_found": False, "reason": ""}
    if not lines:
        result["reason"] = "Chưa có dòng nào để đọc."
        return result

    header = _split_line(lines[0])
    columns = _index_columns(header)
    if "customer_name" not in columns:
        result["columns"] = [_clean(cell) for cell in header]
        result["reason"] = (
            "Không nhận ra cột 'Tên KH' trong dòng tiêu đề. Hãy dán nguyên cả "
            "dòng tiêu đề của file GetFly (Mã ĐH, Ngày đặt hàng, Tên KH, Mã KH…)."
        )
        return result

    result["header_found"] = True
    seen: set[tuple[str, str]] = set()
    for line in lines[1:]:
        cells = _split_line(line)
        if len(cells) < len(header):
            cells = cells + [""] * (len(header) - len(cells))
        name = _clean(cells[columns["customer_name"]])
        code = _clean(cells[columns["customer_code"]]) if "customer_code" in columns else ""
        order = _clean(cells[columns["order_id"]]) if "order_id" in columns else ""
        if order and order not in result["orders"]:
            result["orders"].append(order)
        if not name or not code:
            key = name or code or _clean(cells[0])
            if key and key not in result["skipped"]:
                result["skipped"].append(key)
            continue
        identity = (code.lower(), name.lower())
        if identity in seen:
            continue
        seen.add(identity)
        row = {"id": code, "name": name}
        if "order_date" in columns:
            row["order_date"] = _clean(cells[columns["order_date"]])
        result["rows"].append(row)

    if not result["rows"] and not result["skipped"]:
        result["reason"] = "Dòng tiêu đề đúng nhưng không có dữ liệu khách hàng."
    return result
