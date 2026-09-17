# FILE: core/gnt_builder.py
"""
LOG-LG05 / LOGI_GNT_DOC_EXPORT_REALITY_CHECK_01 — GNT Generation (Giấy Nộp Thuế)

Builds a 2-sheet Excel workbook:
  Sheet 1: NHẬP THÔNG TIN (editable input form with auto-filled values)
  Sheet 2: GIẤY NỘP THUẾ (C1-02/NS official form, print-friendly)

Legal basis:
  - Mẫu số C1-02/NS ban hành kèm theo Thông tư 84/2016/TT-BTC.
    (Theo Điều 14 khoản 3 Thông tư 328/2016/TT-BTC, mẫu C1-02/NS sử dụng theo mẫu ban hành tại TT 84/2016/TT-BTC;
     được sửa đổi/bổ sung bởi TT 72/2021/TT-BTC và TT 23/2025/TT-BTC).
  - Mã Mục lục NSNN theo Thông tư 324/2016/TT-BTC:
      + Tiểu mục 1901: Thuế nhập khẩu (Mục 1900)
      + Tiểu mục 1702: Thuế giá trị gia tăng hàng nhập khẩu (Mục 1700)
      (Tiểu mục 1701 là Thuế GTGT hàng SXKD trong nước - KHÔNG dùng cho hàng NK)

Prerequisites (all must be KNOWN, not guessed):
  - tk_no: customs declaration number
  - tk_date: customs declaration date
  - import_duty_amount: import duty (Thuế nhập khẩu) — known numeric >= 0
  - import_vat_amount: import VAT (Thuế GTGT hàng nhập khẩu) — known numeric >= 0
  - taxpayer_name: importer name (legally responsible entity from explicit customs/GNT record)
  - taxpayer_tax_code: importer MST (from explicit customs/GNT record)

DO NOT GUESS:
  - Bank name, account number
  - KBNN (Kho bạc NN)
  - Collecting authority (Cơ quan thu)
  - Sub-item code (Mã tiểu mục), Chapter code (Mã chương)
"""

import io
from datetime import date
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def doc_so_thanh_chu_vi(amount: float) -> str:
    """Convert number to Vietnamese words for financial documents."""
    if amount == 0:
        return "Không đồng"

    units = [
        "", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"
    ]
    digits = [
        "không", "một", "hai", "ba", "bốn", "năm",
        "sáu", "bảy", "tám", "chín"
    ]

    def group_to_words(n: int) -> str:
        """Convert a 3-digit group to words."""
        if n == 0:
            return ""
        parts = []
        hundreds = n // 100
        tens = (n % 100) // 10
        ones = n % 10

        if hundreds > 0:
            parts.append(f"{digits[hundreds]} trăm")

        if tens > 0:
            if tens == 1:
                parts.append("mười")
            else:
                parts.append(f"{digits[tens]} mươi")
        elif ones > 0 and hundreds > 0:
            parts.append("lẻ")

        if ones > 0:
            if tens == 1 or (tens == 0 and hundreds > 0):
                if ones == 5:
                    parts.append("lăm")
                elif ones == 1:
                    parts.append("mốt")
                else:
                    parts.append(digits[ones])
            else:
                if ones == 1:
                    parts.append("mốt")
                elif ones == 5 and tens > 0:
                    parts.append("lăm")
                else:
                    parts.append(digits[ones])

        return " ".join(parts)

    # Split into groups of 3 from right
    int_amount = int(amount)
    groups = []
    while int_amount > 0:
        groups.append(int_amount % 1000)
        int_amount //= 1000

    if not groups:
        groups = [0]

    # Build words from highest group
    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        gw = group_to_words(groups[i])
        if gw:
            if i > 0:
                result_parts.append(f"{gw} {units[i]}")
            else:
                result_parts.append(gw)

    if not result_parts:
        return "Không đồng"

    text = " ".join(result_parts).strip()
    # Capitalize first letter
    text = text[0].upper() + text[1:] if text else text
    return f"{text} đồng./."


def build_gnt_workbook(data: Dict[str, Any]) -> bytes:
    """
    Build a 2-sheet GNT workbook.

    Required data keys:
      shipment_id: str - Mã ĐH / shipment code
      tk_no: str - customs declaration number (Số tờ khai)
      tk_date: str - customs declaration date (Ngày tờ khai, format DD/MM/YYYY)
      import_duty_amount: float - Thuế nhập khẩu
      import_vat_amount: float - Thuế GTGT hàng NK
      taxpayer_name: str - importer name
      taxpayer_tax_code: str - importer MST
      taxpayer_address: str - importer address (optional)
      taxpayer_province: str - importer province (optional)
      taxpayer_district: str - importer district (optional)
      payer_on_behalf: str - optional, if logistics pays on behalf
      shipment_ref: str - optional reference to shipment

    Returns: bytes of xlsx file
    """
    wb = openpyxl.Workbook()

    # ─── Sheet 1: NHẬP THÔNG TIN ───
    ws1 = wb.active
    ws1.title = "NHẬP THÔNG TIN"

    # Styles
    title_font = Font(bold=True, size=14)
    section_font = Font(bold=True, size=11, color="FFFFFF")
    section_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    autofill_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    editable_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    label_font = Font(bold=True, size=10)
    value_font = Font(size=10)
    note_font = Font(italic=True, size=9, color="666666")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

    # Title
    ws1.cell(row=1, column=1, value="GIẤY NỘP THUẾ (GNT) — THÔNG TIN NHẬP LIỆU").font = title_font
    ws1.cell(row=2, column=1, value=f"Lô: {data.get('shipment_id', '')} | Mẫu C1-02/NS ban hành kèm theo Thông tư 84/2016/TT-BTC").font = note_font

    row = 4
    # Section: Thông tin Tờ khai
    ws1.cell(row=row, column=1, value="A. THÔNG TIN TỜ KHAI HẢI QUAN").font = section_font
    for col in range(1, 4):
        ws1.cell(row=row, column=col).fill = section_fill
    row += 1

    autofill_data = [
        ("Số tờ khai (TK)", data.get("tk_no", ""), "Tự động từ hồ sơ lô"),
        ("Ngày tờ khai", data.get("tk_date", ""), "Tự động từ hồ sơ lô"),
        ("Mã ĐH (Shipment)", data.get("shipment_id", ""), "Mã lô hàng"),
    ]
    for label, value, note in autofill_data:
        ws1.cell(row=row, column=1, value=label).font = label_font
        c = ws1.cell(row=row, column=2, value=value)
        c.fill = autofill_fill
        c.font = value_font
        c.border = thin_border
        ws1.cell(row=row, column=3, value=note).font = note_font
        row += 1

    row += 1
    # Section: Người nộp thuế
    ws1.cell(row=row, column=1, value="B. NGƯỜI NỘP THUẾ (TỔ CHỨC CHỊU TRÁCH NHIỆM PHÁP LÝ)").font = section_font
    for col in range(1, 4):
        ws1.cell(row=row, column=col).fill = section_fill
    row += 1

    autofill_data2 = [
        ("Tên tổ chức/cá nhân", data.get("taxpayer_name", ""), "Tự động — chủ hàng/importer"),
        ("Mã số thuế (MST)", data.get("taxpayer_tax_code", ""), "Tự động từ hồ sơ hải quan"),
        ("Địa chỉ", data.get("taxpayer_address", ""), "Tự động từ hồ sơ hải quan"),
        ("Quận/Huyện", data.get("taxpayer_district", ""), "Tự động"),
        ("Tỉnh/TP", data.get("taxpayer_province", ""), "Tự động"),
    ]
    for label, value, note in autofill_data2:
        ws1.cell(row=row, column=1, value=label).font = label_font
        c = ws1.cell(row=row, column=2, value=value)
        c.fill = autofill_fill
        c.font = value_font
        c.border = thin_border
        ws1.cell(row=row, column=3, value=note).font = note_font
        row += 1

    if data.get("payer_on_behalf"):
        row += 1
        ws1.cell(row=row, column=1, value="(Nộp thay bởi)").font = label_font
        c = ws1.cell(row=row, column=2, value=data["payer_on_behalf"])
        c.fill = editable_fill
        c.border = thin_border
        row += 1

    row += 1
    # Section: Số thuế
    ws1.cell(row=row, column=1, value="C. SỐ THUẾ PHẢI NỘP").font = section_font
    for col in range(1, 4):
        ws1.cell(row=row, column=col).fill = section_fill
    row += 1

    # LOG-LG08.1 / LOGI_GNT_DOC_EXPORT_REALITY_CHECK_01: Support dynamic tax list from UI
    tax_list = data.get("ds_thue", [])
    if not tax_list:
        duty = float(data.get("import_duty_amount", 0) or 0)
        vat = float(data.get("import_vat_amount", 0) or 0)
        tax_list = [
            {"ten": "Thuế nhập khẩu", "ndkt": "1901", "tien": duty},
            {"ten": "Thuế GTGT hàng nhập khẩu", "ndkt": "1702", "tien": vat}
        ]
    else:
        # Validate known canonical tax concepts in custom tax_list (fail closed on invalid NDKT)
        for t in tax_list:
            ten_norm = str(t.get("ten") or "").strip().lower()
            ndkt_val = str(t.get("ndkt") or "").strip()
            # Guard Import Duty (Thuế nhập khẩu) -> 1901
            if ("thuế nhập khẩu" in ten_norm or ten_norm == "thuế nk") and ndkt_val and ndkt_val != "1901":
                raise ValueError(
                    f"Mã NDKT không hợp lệ cho Thuế nhập khẩu: '{ndkt_val}'. Yêu cầu bắt buộc: 1901 theo MLNS TT 324/2016/TT-BTC."
                )
            # Guard Import VAT (Thuế GTGT hàng nhập khẩu) -> 1702
            is_import_vat = (
                "thuế gtgt hàng nhập" in ten_norm
                or "thuế gtgt hàng nk" in ten_norm
                or "thuế vat hàng nhập" in ten_norm
                or "thuế vat hàng nk" in ten_norm
                or ("gtgt" in ten_norm and "nhập" in ten_norm)
                or ("vat" in ten_norm and "nhập" in ten_norm)
            )
            if is_import_vat and ndkt_val and ndkt_val != "1702":
                raise ValueError(
                    f"Mã NDKT không hợp lệ cho Thuế GTGT hàng nhập khẩu: '{ndkt_val}'. Yêu cầu bắt buộc: 1702 theo MLNS TT 324/2016/TT-BTC (Mã 1701 là thuế GTGT nội địa, tuyệt đối không dùng cho hàng NK)."
                )
    
    total = sum(t.get("tien", 0) for t in tax_list)

    autofill_data3 = []
    for t in tax_list:
        autofill_data3.append((t.get("ten", "Thuế"), t.get("tien", 0), f"Mã NDKT: {t.get('ndkt', '')}"))
    
    autofill_data3.append(("TỔNG CỘNG (đ)", total, "Tổng cộng các khoản thuế"))
    autofill_data3.append(("Tổng bằng chữ", doc_so_thanh_chu_vi(total), "Tự động chuyển số thành chữ"))
    for label, value, note in autofill_data3:
        ws1.cell(row=row, column=1, value=label).font = label_font
        c = ws1.cell(row=row, column=2, value=value)
        c.fill = autofill_fill
        c.font = value_font
        c.border = thin_border
        if isinstance(value, (int, float)):
            c.number_format = "#,##0"
        ws1.cell(row=row, column=3, value=note).font = note_font
        row += 1

    row += 1
    # Section: KHÔNG TỰ ĐIỀN (must be filled manually)
    ws1.cell(row=row, column=1, value="D. THÔNG TIN CẦN ĐIỀN THỦ CÔNG (KHÔNG TỰ ĐỘNG)").font = section_font
    for col in range(1, 4):
        ws1.cell(row=row, column=col).fill = section_fill
    row += 1

    manual_data = [
        ("NH (Ngân hàng)", "", "Kho bạc NN nơi nộp — DO NOT GUESS"),
        ("Số tài khoản KBNN", "", "Tài khoản thu NSNN — DO NOT GUESS"),
        ("KBNN nơi thu", "", "Kho bạc NN — DO NOT GUESS"),
        ("Cơ quan quản lý thu", "", "Cơ quan hải quan — DO NOT GUESS"),
        ("Mã tiểu mục (Thuế NK)", "", "Theo danh mục NSNN — DO NOT GUESS"),
        ("Mã chương (Thuế NK)", "", "Theo danh mục NSNN — DO NOT GUESS"),
        ("Mã tiểu mục (Thuế GTGT)", "", "Theo danh mục NSNN — DO NOT GUESS"),
        ("Mã chương (Thuế GTGT)", "", "Theo danh mục NSNN — DO NOT GUESS"),
    ]
    for label, value, note in manual_data:
        ws1.cell(row=row, column=1, value=label).font = label_font
        c = ws1.cell(row=row, column=2, value=value)
        c.fill = editable_fill
        c.font = value_font
        c.border = thin_border
        ws1.cell(row=row, column=3, value=note).font = note_font
        row += 1

    # Column widths for sheet 1
    widths1 = [32, 38, 45]
    for i, w in enumerate(widths1, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # ─── Sheet 2: GIẤY NỘP THUẾ (C1-02/NS) ───
    ws2 = wb.create_sheet("GIẤY NỘP THUẾ")

    # Page setup for printing
    ws2.page_setup.orientation = "portrait"
    ws2.page_setup.paperSize = 5  # A4
    ws2.page_setup.fitToWidth = 1
    ws2.page_setup.fitToHeight = 0
    ws2.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(fitToPage=True)
    ws2.print_area = "A1:G50"

    # Title
    ws2.cell(row=1, column=1, value="GIẤY NỘP TIỀN VÀO NGÂN SÁCH NHÀ NƯỚC").font = Font(bold=True, size=12)
    ws2.cell(row=2, column=1, value="Mẫu số: C1-02/NS").font = Font(size=10)
    ws2.cell(row=2, column=3, value="(Ban hành kèm theo Thông tư số 84/2016/TT-BTC)").font = Font(italic=True, size=9)
    ws2.cell(row=3, column=1, value="Ngày ... tháng ... năm .......").font = Font(size=10)

    # Taxpayer info
    row = 5
    ws2.cell(row=row, column=1, value="Người nộp thuế:").font = label_font
    ws2.cell(row=row, column=2, value=data.get("taxpayer_name", "")).font = value_font
    ws2.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    ws2.cell(row=row, column=6, value="Mã số thuế:").font = label_font
    ws2.cell(row=row, column=7, value=data.get("taxpayer_tax_code", "")).font = value_font
    row += 1

    ws2.cell(row=row, column=1, value="Địa chỉ (nhà, số đường):").font = label_font
    ws2.cell(row=row, column=2, value=data.get("taxpayer_address", "")).font = value_font
    ws2.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    ws2.cell(row=row, column=6, value="Điện thoại:").font = label_font
    ws2.cell(row=row, column=7, value=data.get("taxpayer_phone", "")).font = value_font
    row += 1

    ws2.cell(row=row, column=1, value="Quận/Huyện:").font = label_font
    ws2.cell(row=row, column=2, value=data.get("taxpayer_district", "")).font = value_font
    ws2.cell(row=row, column=3, value="Tỉnh/TP:").font = label_font
    ws2.cell(row=row, column=4, value=data.get("taxpayer_province", "")).font = value_font
    row += 2

    # Payment method (checkbox style)
    ws2.cell(row=row, column=1, value="Nộp bằng tiền mặt tại:").font = label_font
    ws2.cell(row=row, column=3, value="[ ] KBNN").font = value_font
    ws2.cell(row=row, column=5, value="[ ] NH ủy nhiệm thu").font = value_font
    row += 1
    ws2.cell(row=row, column=1, value="Chuyển khoản từ tài khoản:").font = label_font
    ws2.cell(row=row, column=3, value="...........................").font = value_font
    ws2.cell(row=row, column=5, value="NH: ...........................").font = value_font
    row += 2

    # Tax table
    ws2.cell(row=row, column=1, value="Các khoản nộp vào NSNN:").font = label_font
    row += 1

    # Table header
    table_headers = ["STT", "Số tờ khai / Số quyết định", "Kỳ thuế / Ngày tờ khai", "Nội dung khoản nộp", "Số tiền (đ)", "Mã tiểu mục", "Mã chương"]
    header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
    for col_idx, h in enumerate(table_headers, 1):
        c = ws2.cell(row=row, column=col_idx, value=h)
        c.font = Font(bold=True, size=9)
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = thin_border
    row += 1

    # Tax rows
    tk_no = data.get("tk_no", "")
    tk_date = data.get("tk_date", "")

    tax_rows = []
    for i, t in enumerate(tax_list, 1):
        tax_rows.append((str(i), tk_no, tk_date, t.get("ten", ""), t.get("tien", 0), t.get("ndkt", ""), ""))
        
    first_tax_row = row
    for tax_row_data in tax_rows:
        for col_idx, val in enumerate(tax_row_data, 1):
            c = ws2.cell(row=row, column=col_idx, value=val)
            c.border = thin_border
            c.font = value_font
            if col_idx == 5:
                c.number_format = "#,##0"
            if col_idx in (1, 5):
                c.alignment = center
        row += 1

    # Total row
    total_row = row
    ws2.cell(row=row, column=1, value="").border = thin_border
    ws2.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    ws2.cell(row=row, column=2, value="TỔNG CỘNG").font = Font(bold=True, size=9)
    ws2.cell(row=row, column=2).border = thin_border
    ws2.cell(row=row, column=3).border = thin_border
    ws2.cell(row=row, column=4).border = thin_border
    c = ws2.cell(row=row, column=5, value=f"=SUM(E{first_tax_row}:E{row-1})")
    c.font = Font(bold=True, size=9)
    c.border = thin_border
    c.number_format = "#,##0"
    c.alignment = center
    ws2.cell(row=row, column=6).border = thin_border
    ws2.cell(row=row, column=7).border = thin_border
    row += 2

    # Total in words
    ws2.cell(row=row, column=1, value="Tổng số tiền ghi bằng chữ:").font = label_font
    ws2.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    ws2.cell(row=row, column=2, value=doc_so_thanh_chu_vi(total)).font = value_font
    ws2.cell(row=row, column=2).border = thin_border
    for col in range(3, 8):
        ws2.cell(row=row, column=col).border = thin_border
    row += 2

    # Shipment reference
    ws2.cell(row=row, column=1, value="Tham chiếu lô hàng:").font = note_font
    ws2.cell(row=row, column=2, value=f"{data.get('shipment_id', '')}").font = note_font
    row += 2

    # Signature section
    sig_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    ws2.cell(row=row, column=1, value="NGƯỜI NỘP TIỀN").font = Font(bold=True, size=9)
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws2.cell(row=row, column=1).fill = sig_fill
    ws2.cell(row=row, column=2).fill = sig_fill
    ws2.cell(row=row, column=4, value="KẾ TOÁN TRƯỞNG").font = Font(bold=True, size=9)
    ws2.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws2.cell(row=row, column=4).fill = sig_fill
    ws2.cell(row=row, column=5).fill = sig_fill
    ws2.cell(row=row, column=7, value="THỦ TRƯỞNG ĐV").font = Font(bold=True, size=9)
    ws2.merge_cells(start_row=row, start_column=7, end_row=row, end_column=7)
    ws2.cell(row=row, column=7).fill = sig_fill
    row += 1

    for _ in range(4):
        for col in [1, 4, 7]:
            ws2.cell(row=row, column=col).fill = sig_fill
        row += 1

    # Column widths for sheet 2
    widths2 = [18, 20, 16, 28, 14, 10, 10]
    for i, w in enumerate(widths2, 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def check_gnt_prerequisites(ship_data: Dict[str, Any], customer_doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Check if a shipment has all prerequisites for GNT generation.

    Returns dict with:
      ready: bool - all prerequisites met
      no_payable: bool - tax amounts are known but sum to 0
      missing: List[str] - list of missing fields
      reason: str - reason when not ready
      data: Dict - extracted values for GNT (if available)
    """
    customs = ship_data.get("data", {}).get("2.4", {}) if isinstance(ship_data.get("data"), dict) else {}
    gnt_section = customs.get("gnt", {}) if isinstance(customs.get("gnt"), dict) else {}
    missing = []
    result_data = {}

    # Check tk_no
    tk_no = customs.get("tk_no", "")
    if not tk_no or str(tk_no).strip() == "" or str(tk_no) == "None":
        missing.append("Số tờ khai (TK)")
    else:
        result_data["tk_no"] = str(tk_no).strip()

    # Check tk_date
    tk_date = customs.get("tk_date", "") or customs.get("reg_date", "")
    if not tk_date or str(tk_date).strip() == "" or str(tk_date) == "None":
        missing.append("Ngày tờ khai")
    else:
        tk_date_str = str(tk_date).strip()
        if "-" in tk_date_str and len(tk_date_str.split("-")) == 3:
            parts = tk_date_str.split("-")
            if len(parts[0]) == 4:
                tk_date_str = f"{parts[2]}/{parts[1]}/{parts[0]}"
        result_data["tk_date"] = tk_date_str

    # Check import duty amount (UNKNOWN != ZERO semantics)
    raw_duty = customs.get("import_duty_amount")
    duty = None
    if raw_duty is None or str(raw_duty).strip() == "" or str(raw_duty).strip() == "None":
        missing.append("Thuế nhập khẩu (số tiền)")
    else:
        try:
            duty_val = float(raw_duty)
            if duty_val < 0:
                missing.append("Thuế nhập khẩu không hợp lệ (âm)")
            else:
                duty = duty_val
                result_data["import_duty_amount"] = duty
        except (ValueError, TypeError):
            missing.append("Thuế nhập khẩu (số tiền không hợp lệ)")

    # Check import VAT amount (UNKNOWN != ZERO semantics)
    raw_vat = customs.get("import_vat_amount")
    vat = None
    if raw_vat is None or str(raw_vat).strip() == "" or str(raw_vat).strip() == "None":
        missing.append("Thuế GTGT hàng NK (số tiền)")
    else:
        try:
            vat_val = float(raw_vat)
            if vat_val < 0:
                missing.append("Thuế GTGT hàng NK không hợp lệ (âm)")
            else:
                vat = vat_val
                result_data["import_vat_amount"] = vat
        except (ValueError, TypeError):
            missing.append("Thuế GTGT hàng NK (số tiền không hợp lệ)")

    # Taxpayer info: ONLY from explicit customs / GNT fields
    taxpayer_name = (
        gnt_section.get("nguoi_nop")
        or customs.get("taxpayer_name")
        or customs.get("nguoi_nop")
        or ""
    )
    if not taxpayer_name or str(taxpayer_name).strip() == "":
        missing.append("Tên người nộp thuế")
    result_data["taxpayer_name"] = str(taxpayer_name).strip()

    taxpayer_tax_code = (
        gnt_section.get("mst")
        or customs.get("taxpayer_tax_code")
        or customs.get("mst")
        or ""
    )
    if not taxpayer_tax_code or str(taxpayer_tax_code).strip() == "":
        missing.append("Mã số thuế (MST)")
    result_data["taxpayer_tax_code"] = str(taxpayer_tax_code).strip()

    result_data["taxpayer_address"] = str(
        gnt_section.get("dia_chi")
        or customs.get("taxpayer_address")
        or customs.get("dia_chi")
        or ""
    ).strip()
    result_data["taxpayer_province"] = str(
        gnt_section.get("tinh_tp")
        or customs.get("taxpayer_province")
        or ""
    ).strip()
    result_data["taxpayer_district"] = str(
        gnt_section.get("quan_huyen")
        or customs.get("taxpayer_district")
        or ""
    ).strip()
    result_data["payer_on_behalf"] = str(customs.get("payer_on_behalf") or "").strip()

    result_data["shipment_id"] = str(ship_data.get("id", "")).strip()

    # Total tax obligation check: both known zero is not missing, but no payable amount
    no_payable = False
    if duty is not None and vat is not None and duty == 0 and vat == 0 and len(missing) == 0:
        no_payable = True

    ready = (len(missing) == 0) and not no_payable

    reason = ""
    if no_payable:
        reason = "NO_PAYABLE_AMOUNT"
    elif not ready:
        reason = f"Thiếu: {', '.join(missing)}"

    return {
        "ready": ready,
        "no_payable": no_payable,
        "missing": missing,
        "reason": reason,
        "data": result_data,
    }
