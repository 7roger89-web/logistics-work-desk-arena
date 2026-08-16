# FILE: core/excel_utils.py
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from datetime import date
from core.config import GETFLY_SERVICES_LIST
from core.utils import safe_float, parse_date
from core.logic import calculate_from_shipment

# --- STYLES ---
BORDER_THIN = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
FONT_BOLD = Font(name='Arial', bold=True, size=10)
FONT_HEADER = Font(name='Arial', bold=True, color='FFFFFF')
FILL_HEADER = PatternFill(start_color="0F2C59", end_color="0F2C59", fill_type="solid")
ALIGN_CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal='right', vertical='center')

def apply_header_style(cell):
    cell.font = FONT_HEADER
    cell.fill = FILL_HEADER
    cell.alignment = ALIGN_CENTER
    cell.border = BORDER_THIN

def auto_fit_columns(ws):
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
            except (TypeError, ValueError):
                continue
        adjusted_width = (max_length + 2) * 1.1
        ws.column_dimensions[column_letter].width = min(adjusted_width, 50)

def find_best_match_code(input_name):
    if not input_name: return "DVK"
    clean_input = input_name.lower().strip()
    for s in GETFLY_SERVICES_LIST:
        if s['name'].lower().strip() == clean_input: return s['code']
    for s in GETFLY_SERVICES_LIST:
        s_name = s['name'].lower().strip()
        if clean_input in s_name or s_name in clean_input: return s['code']
    return "DVK"

def generate_mini_export_excel(shipment):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Debit Note"

    ws['A1'] = "LOGISTICS PRO SYSTEM"; ws['A1'].font = Font(size=16, bold=True, color="0F2C59")
    ws['A2'] = "BẢNG KÊ CHI TIẾT DỊCH VỤ (DEBIT NOTE)"; ws['A2'].font = Font(size=14, bold=True)
    
    d = shipment.get('data', {})
    sid = shipment.get('id')
    cust = shipment.get('customer')
    
    ws['A4'] = f"Mã Lô: {sid}"; ws['A4'].font = FONT_BOLD
    ws['D4'] = f"Khách hàng: {cust}"; ws['D4'].font = FONT_BOLD
    ws['A5'] = f"Ngày tàu: {d.get('1.2',{}).get('etd')}"; 
    ws['D5'] = f"Số Bill: {d.get('1.2',{}).get('mbl')}"

    headers = ["STT", "Tên Dịch vụ", "Mã", "ĐVT", "SL", "Đơn giá (Vốn)", "Đơn giá (Bán)", "Thành tiền (Trước VAT)", "VAT", "Tổng Tiền", "Ghi chú"]
    start_row = 7
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=col_idx, value=h)
        apply_header_style(cell)

    details = d.get('3.4', {}).get('details', [])
    curr_row = start_row + 1
    total_final = 0

    for i, item in enumerate(details, 1):
        qty = safe_float(item.get('qty', 1))
        p_in = safe_float(item.get('cost', item.get('price_in', 0)))
        p_out = safe_float(item.get('price', item.get('price_out', 0)))
        vat_pct = safe_float(item.get('vat_line', item.get('vat', 0)))
        
        pre_tax = qty * p_out
        vat_val = pre_tax * vat_pct / 100
        line_total = pre_tax + vat_val
        total_final += line_total
        
        code = item.get('code', '')
        name = item.get('name_full', item.get('name',''))
        if not code or code == "DV": code = find_best_match_code(name)

        row_data = [
            i, name, code, "Lần", 
            qty, p_in, p_out, pre_tax, f"{vat_pct}%", line_total, item.get('note', '')
        ]
        
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=curr_row, column=col_idx, value=val)
            cell.border = BORDER_THIN
            if col_idx in [6, 7, 8, 10]: cell.number_format = '#,##0'
            if col_idx == 1: cell.alignment = ALIGN_CENTER
        curr_row += 1

    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=9)
    total_label = ws.cell(row=curr_row, column=1, value="TỔNG CỘNG PHẢI THU:")
    total_label.font = FONT_BOLD; total_label.alignment = ALIGN_RIGHT
    
    total_val = ws.cell(row=curr_row, column=10, value=total_final)
    total_val.font = Font(bold=True, color="C62828"); total_val.number_format = '#,##0'
    total_val.border = BORDER_THIN

    auto_fit_columns(ws)
    wb.save(output)
    output.seek(0)
    return output

def generate_commission_excel(target_list):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Commission Report"

    headers = ["Mã Lô", "Khách Hàng", "Ngày Tạo", "Doanh Thu", "Chi Phí", "Lợi Nhuận Gộp", "Hoa Hồng (Chi)", "Thực Lãi Net", "Ghi Chú"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        apply_header_style(cell)

    curr_row = 2
    for sid, s in target_list:
        d = s.get('data', {})
        summary = calculate_from_shipment(s)
        revenue_net = safe_float(summary.get('revenue_net', 0))
        cost = safe_float(summary.get('cost', 0))
        comm_info = d.get('3.4', {}).get('commission', {})
        comm_val = safe_float(summary.get('commission', 0))
        profit_before_commission = revenue_net - cost
        net_profit = safe_float(summary.get('profit', 0))

        row = [
            sid, s.get('client_short') or s.get('customer') or s.get('client', ''), d.get('0.0', {}).get('created_at', ''),
            revenue_net, cost, profit_before_commission, comm_val, net_profit, comm_info.get('note', '')
        ]
        
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row=curr_row, column=col_idx, value=val)
            cell.border = BORDER_THIN
            if col_idx in [4, 5, 6, 7, 8]: cell.number_format = '#,##0'
        curr_row += 1

    auto_fit_columns(ws)
    wb.save(output)
    output.seek(0)
    return output

# --- 3. XUẤT FILE IMPORT GETFLY (Fix Lỗi Tên Cột & Thêm Tên NV) ---
def generate_getfly_excel(shipments_dict, assignee_name="", customers_dict=None):
    if customers_dict is None:
        from core.database import load_customers
        customers_dict = load_customers()
    db_cust = customers_dict
    
    # ĐÃ SỬA: "Địa chỉ giao hàng" -> "Địa chỉ", "CẤP ĐỘ RỦI RO " -> "CẤP ĐỘ RỦI RO"
    ALL_COLUMNS = [
        "Ngày đặt hàng", "Ngày tạo", "Mã ĐH", "Người thực hiện", 
        "Mã KH", "Tên KH", "Số ĐT", "Email", "Địa chỉ", 
        "Người liên hệ", "Điện thoại người liên hệ", "Tỉnh/ TP", "Quận/ Huyện", 
        "Nguồn khách hàng", "Mã vận đơn", "Trạng thái vận đơn", "Mã kho", 
        "Mã SP", "Tên sản phẩm", "Mô tả", "Đơn vị", "Nhóm sản phẩm", 
        "Số lượng", "Giá vốn", "Giá bán", "CK(%)", "CK(Đ)", "VAT(%)", 
        "Thành tiền", "Lợi nhuận SP", "Doanh số", "Chiết khấu (đ)", 
        "Doanh thu sau CK", "Phí vận chuyển (đ)", "Phí lắp đặt (đ)", 
        "Doanh thu trước thuế", "VAT (đ)", "Doanh thu", "Đã thanh toán", 
        "Còn lại", "Lợi nhuận", "Điều khoản đơn hàng", "Hình thức thanh toán", 
        "Hình thức thanh toán từng lần", "Ngày thanh toán", "Nguồn đơn hàng", 
        "Người tạo", "Trạng thái", "Nhóm khách hàng", "REFUN", 
        "HOA HỒNG KH GỬI", "CẤP ĐỘ RỦI RO"
    ]

    CODE_TO_OFFICIAL = {s['code']: s for s in GETFLY_SERVICES_LIST}
    data_rows = []
    
    c_map = {v.get('name', '').strip(): v for v in db_cust.values()} if db_cust else {}

    for sid, s in shipments_dict.items():
        d = s.get('data', {})
        cust_name = (s.get('customer') or s.get('client') or '').strip()
        c_info = db_cust.get(str(s.get('customer_id', '')), {}) or c_map.get(cust_name, {})
        
        ma_kh_chuan = c_info.get('id', '')
        
        created_at = parse_date(d.get('0.0', {}).get('created_at'))
        date_str = created_at.strftime('%d/%m/%Y') if created_at else ""
        
        details = d.get('3.4', {}).get('details', [])
        summary = calculate_from_shipment(s)
        paid_amt = safe_float(summary.get('paid', 0))
        total_rev = safe_float(summary.get('receivable', 0))
        total_profit = safe_float(summary.get('profit', 0))
        total_debt = safe_float(summary.get('debt', 0))
        
        base_row = {k: "" for k in ALL_COLUMNS}
        
        if not details: 
            h_row = base_row.copy()
            h_row.update({
                "Mã ĐH": sid, "Ngày đặt hàng": date_str, "Ngày tạo": date_str,
                "Người thực hiện": assignee_name, # Gắn tên Người thực hiện
                "Mã KH": ma_kh_chuan, "Tên KH": cust_name, 
                "Số ĐT": c_info.get('phone', ''), "Email": c_info.get('email', ''),
                "Địa chỉ": c_info.get('address', ''),
                "Doanh thu": total_rev, "Lợi nhuận": total_profit, "Đã thanh toán": paid_amt,
                "Trạng thái": "Hoàn thành" if s.get('status') in ['done', 'Done'] else "Mới",
                "Còn lại": total_debt,
                "Tên sản phẩm": "Dịch vụ Logistics", "Mã SP": "DVK", 
                "Số lượng": 1, "Thành tiền": total_rev
            })
            data_rows.append(h_row)
        else:
            for i, item in enumerate(details):
                row = base_row.copy()
                
                qty = safe_float(item.get('qty', 1))
                p_out = safe_float(item.get('price', item.get('price_out', 0)))
                p_in = safe_float(item.get('cost', item.get('price_in', 0)))
                vat_pct = safe_float(item.get('vat_line', item.get('vat', 0)))
                line_rev = qty * p_out
                line_profit = (p_out - p_in) * qty
                
                current_code = str(item.get('code', '')).strip()
                current_name = str(item.get('name_full', item.get('name', ''))).strip()
                
                if "(" in current_name and ")" in current_name:
                    extracted_code = current_name.split("(")[-1].replace(")", "").strip()
                    current_name = current_name.split("(")[0].strip()
                    if not current_code or current_code in ["None", ""]:
                        current_code = extracted_code
                
                if not current_code or current_code in ["DV", "DV-KHAC", "None"]:
                    current_code = find_best_match_code(current_name)
                
                unit_val, group_val = "Lần", "DỊCH VỤ XNK"
                if current_code in CODE_TO_OFFICIAL:
                    current_name = CODE_TO_OFFICIAL[current_code]['name']
                    unit_val = CODE_TO_OFFICIAL[current_code]['unit']
                    group_val = CODE_TO_OFFICIAL[current_code]['group']

                row.update({
                    "Mã SP": current_code,
                    "Tên sản phẩm": current_name,
                    "Mô tả": item.get('note', ''),
                    "Đơn vị": unit_val, 
                    "Nhóm sản phẩm": group_val,
                    "Số lượng": qty,
                    "Giá vốn": p_in, "Giá bán": p_out, "VAT(%)": vat_pct,
                    "Thành tiền": line_rev, "Doanh số": line_rev, "Lợi nhuận SP": line_profit,
                })

                if i == 0:
                    row.update({
                        "Mã ĐH": sid, "Ngày đặt hàng": date_str, "Ngày tạo": date_str,
                        "Người thực hiện": assignee_name, # Gắn tên Người thực hiện
                        "Mã KH": ma_kh_chuan, "Tên KH": cust_name, 
                        "Số ĐT": c_info.get('phone', ''), "Email": c_info.get('email', ''),
                        "Địa chỉ": c_info.get('address', ''),
                        "Doanh thu": total_rev, "Lợi nhuận": total_profit, "Đã thanh toán": paid_amt,
                        "Trạng thái": "Hoàn thành" if s.get('status') in ['done', 'Done'] else "Mới",
                        "Còn lại": total_debt
                    })
                
                data_rows.append(row)

    if not data_rows: return None
    df = pd.DataFrame(data_rows)
    df = df.reindex(columns=ALL_COLUMNS)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        ws = writer.sheets['Sheet1']
        auto_fit_columns(ws)
        
    output.seek(0)
    return output

def _write_key_value_sheet(title, sections):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws["A1"] = title
    ws["A1"].font = Font(size=16, bold=True, color="0F2C59")
    row = 3
    for heading, values in sections:
        ws.cell(row=row, column=1, value=heading).font = Font(bold=True, color="FFFFFF")
        ws.cell(row=row, column=1).fill = FILL_HEADER
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        row += 1
        for key, value in values:
            ws.cell(row=row, column=1, value=str(key)).font = FONT_BOLD
            ws.cell(row=row, column=2, value=value)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
            row += 1
        row += 1
    auto_fit_columns(ws)
    wb.save(output)
    output.seek(0)
    return output


def generate_quote_excel(quote):
    quote = quote or {}
    details = quote.get("details", quote.get("items", []))
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Quotation"
    ws["A1"] = "LOGISTICS PRO - BÁO GIÁ"
    ws["A1"].font = Font(size=16, bold=True, color="0F2C59")
    ws["A3"] = f"Mã báo giá: {quote.get('id', quote.get('quote_no', ''))}"
    ws["A4"] = f"Khách hàng: {quote.get('customer', quote.get('client', ''))}"
    ws["A5"] = f"Ngày: {quote.get('date', date.today())}"
    headers = ["STT", "Dịch vụ", "Đơn vị", "Số lượng", "Đơn giá", "VAT (%)", "Thành tiền", "Ghi chú"]
    for idx, header in enumerate(headers, 1):
        apply_header_style(ws.cell(row=7, column=idx, value=header))
    total = 0.0
    for row_idx, item in enumerate(details, 8):
        qty = safe_float(item.get("qty", 1))
        price = safe_float(item.get("price", item.get("price_out", 0)))
        vat = safe_float(item.get("vat", item.get("vat_line", 0)))
        amount = qty * price * (1 + vat / 100)
        total += amount
        values = [row_idx - 7, item.get("name", item.get("name_full", "")), item.get("unit", "Lần"), qty, price, vat, amount, item.get("note", "")]
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = BORDER_THIN
            if col_idx in {5, 7}:
                cell.number_format = "#,##0"
    total_row = 8 + len(details)
    ws.cell(row=total_row, column=6, value="TỔNG").font = FONT_BOLD
    ws.cell(row=total_row, column=7, value=total).number_format = "#,##0"
    ws.cell(row=total_row, column=7).font = FONT_BOLD
    auto_fit_columns(ws)
    wb.save(output)
    output.seek(0)
    return output


def generate_sales_contract_excel(contract):
    contract = contract or {}
    return _write_key_value_sheet("HỢP ĐỒNG / SALES CONTRACT", [
        ("THÔNG TIN HỢP ĐỒNG", [
            ("Số hợp đồng", contract.get("contract_no", contract.get("id", ""))),
            ("Ngày ký", contract.get("date", "")),
            ("Đối tác", contract.get("client", "")),
            ("Giá trị", contract.get("value", 0)),
            ("Tiền tệ", contract.get("currency", "USD")),
            ("Điều khoản", contract.get("note", "")),
        ])
    ])


def generate_debit_note_excel(shipment):
    return generate_mini_export_excel(shipment)