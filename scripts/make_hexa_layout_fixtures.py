"""SYNTHETIC workbooks for the three real PL/PI layout families (HEXA V0).

These are NOT the Owner's customer files. No company name, price list, bank
account or other commercial data is copied here; every value is invented only to
reproduce the STRUCTURE the task describes:

A. `build_packing_list_with_images()` — packing list with product photos,
   13 used rows, a table starting at row 7, real data up to column T, and a
   sheet that DECLARES 257 columns because of stray formatting. No unit price.
B. `build_proforma_invoice()` — a PI sheet (`PI (2)`, table at row 7) plus a
   second money sheet that duplicates the goods table and carries tax/fee cells
   and an internal sentinel.
C. `build_multilevel_packing_list()` — goods list → two pallets → cartons, plus
   a HIDDEN loading-instruction sheet carrying an internal sentinel.

`TT_INTERNAL_SENTINEL` is a FAKE internal marker used only by the negative test
that proves the customer quotation never carries it.

Usage:
  python scripts/make_hexa_layout_fixtures.py .tmp/hexa-fixtures/
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from PIL import Image as PILImage

SENTINEL = "TT_INTERNAL_SENTINEL"

BANNER = "FIXTURE MÔ PHỎNG — KHÔNG PHẢI WORKBOOK CỦA KHÁCH"
THIN = Side(style="thin", color="B4C6E7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="E4EBF7")
WARN_FONT = Font(name="Arial", size=10, bold=True, color="9C0006")

# ---------------------------------------------------------------- A: packing list
SHEET_PACKING = "Sheet1"
SHEET_PACKING_EMPTY = "Sheet3"
PACKING_HEADERS = {
    "A": "序号",
    "B": "产品型号 Model",
    "C": "产品名称 Product name",
    "D": "中文品名",
    "E": "产品尺寸 Product size (mm)",
    "F": "数量 Qty (pcs)",
    "G": "包装方式 Packing",
    "H": "包装尺寸 Package size (mm)",
    "I": "件数 Cartons",
    "J": "净重 N.W. (kg)",
    "K": "毛重 G.W. (kg)",
    "L": "总体积 CBM",
    "M": "图片 Image",
    "N": "备注 Remark",
    "O": "材质 Material",
    "P": "生产周期 Lead time",
    "Q": "交货期",
    "R": "目的港",
    "S": "运输方式",
    "T": "数据来源",
}
# (model, english name, chinese name, product size, qty, packing, package size,
#  cartons, net weight, gross weight, cbm)
PACKING_ROWS = (
    ("BC-800", "Bathroom cabinet 800", "浴室柜 800", "800×480×850", 6, "Carton + foam", "860×540×900", 6, 96.0, 108.0, 2.51),
    ("BC-1000", "Bathroom cabinet 1000", "浴室柜 1000", "1000×480×850", 4, "Carton + foam", "1060×540×900", 4, 84.0, 94.0, 2.06),
    ("MC-600", "LED mirror 600", "LED 镜 600", "600×20×800", 8, "Carton", "660×80×860", 4, 32.0, 36.0, 0.91),
    ("SH-900", "Basin shelf 900", "浴室架 900", "900×500×750", 3, "Carton", "960×560×800", 3, 27.0, 31.0, 1.29),
)


def _picture() -> io.BytesIO:
    """A tiny synthetic photo, so the workbook really embeds an image."""
    buffer = io.BytesIO()
    PILImage.new("RGB", (24, 24), (196, 214, 235)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def build_packing_list_with_images() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_PACKING
    ws.merge_cells("A1:T1")
    ws["A1"] = BANNER
    ws["A1"].font = WARN_FONT
    ws["A1"].alignment = Alignment(horizontal="center")
    ws["A2"], ws["B2"] = "PACKING LIST", "SYNTHETIC-PL-001"
    ws["A2"].font = Font(name="Arial", size=14, bold=True)
    ws["A3"], ws["B3"] = "Nhà cung cấp", "Nhà máy mô phỏng (không có thật)"
    ws["A4"], ws["B4"] = "Ngày đóng gói", "2026-07-14"
    ws["A5"], ws["B5"] = "Số kiện", "17"
    ws["A6"], ws["B6"] = "Ghi chú", "Dữ liệu giả lập cho kiểm thử — không dùng để báo giá"
    for column, title in PACKING_HEADERS.items():
        cell = ws[f"{column}7"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for offset, row in enumerate(PACKING_ROWS):
        excel_row = 8 + offset
        model, name, name_cn, size, qty, packing, package, cartons, net, gross, cbm = row
        ws[f"A{excel_row}"] = offset + 1
        ws[f"B{excel_row}"] = model
        ws[f"C{excel_row}"] = name
        ws[f"D{excel_row}"] = name_cn
        ws[f"E{excel_row}"] = size
        ws[f"F{excel_row}"] = qty
        ws[f"G{excel_row}"] = packing
        ws[f"H{excel_row}"] = package
        ws[f"I{excel_row}"] = cartons
        ws[f"J{excel_row}"] = net
        ws[f"K{excel_row}"] = gross
        # Deliberately a formula the file never cached: CBM stays UNKNOWN.
        ws[f"L{excel_row}"] = f"=ROUND(0.86*0.54*0.9*I{excel_row},2)" if offset == 0 else cbm
        ws[f"O{excel_row}"] = "MDF + ceramic"
        ws[f"P{excel_row}"] = "25 days"
        ws[f"Q{excel_row}"] = "2026-07-14"
        ws[f"R{excel_row}"] = "Hai Phong"
        ws[f"S{excel_row}"] = "Sea"
        ws[f"T{excel_row}"] = "Nhà máy gửi"
        for column in range(1, 21):
            ws.cell(row=excel_row, column=column).border = BORDER
    ws.add_image(XLImage(_picture()), "M8")
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 30
    # The real file declares 257 columns although its data ends at T. Stray
    # formatting is the only thing that far out.
    for excel_row, column in ((1, 257), (7, 257), (13, 257)):
        ws.cell(row=excel_row, column=column).fill = PatternFill("solid", fgColor="FFFFFF")
    wb.create_sheet(SHEET_PACKING_EMPTY)
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ------------------------------------------------------------ B: proforma invoice
SHEET_PI = "PI (2)"
SHEET_PI_MONEY = "File tiền hàng"
PI_HEADERS = {
    "A": "序号 No.",
    "B": "型号 Model",
    "C": "产品名称 / Description",
    "D": "规格 Size (mm)",
    "E": "数量 Qty (pcs)",
    "F": "单位 Unit",
    "G": "单价 Unit Price (CNY)",
    "H": "金额 Amount (CNY)",
    "I": "备注 Remark",
}
# (model, bilingual description, size, qty, unit price CNY)
PI_ROWS = (
    ("BC-800", "Bathroom cabinet 800 / 浴室柜", "800×480×850", 12, 180.0),
    ("BC-1000", "Bathroom cabinet 1000 / 浴室柜", "1000×480×850", 8, 240.0),
    ("MC-600", "LED mirror 600 / LED 镜", "600×20×800", 6, 95.0),
    ("SH-900", "Basin shelf 900 / 浴室架", "900×500×750", 4, 320.0),
)


def build_proforma_invoice() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_PI
    ws.merge_cells("A1:I1")
    ws["A1"] = BANNER
    ws["A1"].font = WARN_FONT
    ws["A2"], ws["B2"] = "PROFORMA INVOICE", "SYNTHETIC-PI-001"
    ws["A2"].font = Font(name="Arial", size=14, bold=True)
    ws["A3"], ws["B3"] = "Seller", "Nhà máy mô phỏng (không có thật)"
    ws["A4"], ws["B4"] = "Buyer", "Công ty thử nghiệm (không có thật)"
    ws["A5"], ws["B5"] = "Terms", "EXW"
    ws["A6"], ws["B6"] = "Date", "2026-07-14"
    for column, title in PI_HEADERS.items():
        cell = ws[f"{column}7"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for offset, (model, description, size, qty, price) in enumerate(PI_ROWS):
        excel_row = 8 + offset
        ws[f"A{excel_row}"] = offset + 1
        ws[f"B{excel_row}"] = model
        ws[f"C{excel_row}"] = description
        ws[f"D{excel_row}"] = size
        ws[f"E{excel_row}"] = qty
        ws[f"F{excel_row}"] = "PCS"
        ws[f"G{excel_row}"] = price
        ws[f"H{excel_row}"] = f"=E{excel_row}*G{excel_row}"
        ws[f"I{excel_row}"] = "Kèm phụ kiện" if offset == 0 else None
        for column in range(1, 10):
            ws.cell(row=excel_row, column=column).border = BORDER
    ws["I12"] = "Total"
    ws["H12"] = "=SUM(H8:H11)"
    ws.add_image(XLImage(_picture()), "K2")
    ws.column_dimensions["C"].width = 38

    money = wb.create_sheet(SHEET_PI_MONEY)
    money["A1"] = "BẢNG TÍNH TIỀN HÀNG — NỘI BỘ, KHÔNG GỬI KHÁCH"
    money["A1"].font = WARN_FONT
    money["A2"] = "Bảng dưới đây TRÙNG với sheet PI; không cộng hai lần."
    for column, title in {"A": "No.", "B": "Model", "C": "Description", "E": "Qty", "G": "Unit Price (CNY)", "H": "Amount (CNY)"}.items():
        money[f"{column}3"] = title
        money[f"{column}3"].font = Font(bold=True)
    for offset, (model, description, _size, qty, price) in enumerate(PI_ROWS):
        excel_row = 4 + offset
        money[f"A{excel_row}"] = offset + 1
        money[f"B{excel_row}"] = model
        money[f"C{excel_row}"] = description
        money[f"E{excel_row}"] = qty
        money[f"G{excel_row}"] = price
        money[f"H{excel_row}"] = f"=E{excel_row}*G{excel_row}"
    money["A9"], money["B9"] = "Tổng tiền hàng", "=SUM(H4:H7)"
    money["A10"], money["B10"] = "Thuế GTGT 8%", "=B9*8%"
    money["A11"], money["B11"] = "Phí vận chuyển nội địa", 4200000
    money["A12"], money["B12"] = "Giá vốn nội bộ", SENTINEL
    money["A13"], money["B13"] = "Ghi chú nội bộ", "TT_INTERNAL_SENTINEL chỉ để kiểm thử rò rỉ"
    money.column_dimensions["C"].width = 38
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --------------------------------------------------- C: multi-level packing list
SHEET_TOTAL = "总清单"
SHEET_PALLETS = "托盘明细（2托）"
SHEET_CARTONS = "卫浴"
SHEET_INSTRUCTION = "打托指令"
TOTAL_ROWS = (
    ("BC-800", "浴室柜 800", 12, 240.0, 3.2),
    ("BC-1000", "浴室柜 1000", 8, 180.0, 2.4),
    (None, "LED 镜 600", 6, 96.0, 1.1),
)
PALLET_ROWS = (
    ("PLT-01", "BC-800", 6, 130.0, 1.7),
    ("PLT-02", "BC-1000", 4, 100.0, 1.3),
)
CARTON_ROWS = (
    ("BC-800", "浴室柜 800", 2, 860, 540, 900, 48.0, 54.0, 0.42),
    ("BC-800", "浴室柜 800", 2, 860, 540, 900, 48.0, 54.0, 0.42),
    ("BC-800", "浴室柜 800", 2, 860, 540, 900, 48.0, 54.0, 0.42),
    ("BC-1000", "浴室柜 1000", 2, 1060, 540, 900, 42.0, 47.0, 0.52),
    ("BC-1000", "浴室柜 1000", 2, 1060, 540, 900, 42.0, 47.0, 0.52),
    (None, "LED 镜 600", 4, 660, 80, 860, 8.0, 9.0, 0.09),
)


def build_multilevel_packing_list() -> bytes:
    wb = Workbook()
    total = wb.active
    total.title = SHEET_TOTAL
    total["A1"] = BANNER
    total["A1"].font = WARN_FONT
    total["A2"] = "TỔNG DANH SÁCH HÀNG — 2 PALLET"
    for column, title in {"A": "序号", "B": "型号 Model", "C": "品名", "D": "总数量 Qty",
                          "E": "毛重 G.W. (kg)", "F": "体积 CBM"}.items():
        total[f"{column}3"] = title
        total[f"{column}3"].font = Font(bold=True)
        total[f"{column}3"].fill = HEAD_FILL
    for offset, row in enumerate(TOTAL_ROWS):
        excel_row = 4 + offset
        model, description, qty, gross, cbm = row
        total[f"A{excel_row}"] = offset + 1
        total[f"B{excel_row}"] = model
        total[f"C{excel_row}"] = description
        total[f"D{excel_row}"] = qty
        total[f"E{excel_row}"] = gross
        total[f"F{excel_row}"] = cbm
    total["A7"], total["C7"] = "Tổng", "=SUM(D4:D6)"
    total["E7"] = "=SUM(E4:E6)"
    total["F7"] = "=SUM(F4:F6)"

    pallets = wb.create_sheet(SHEET_PALLETS)
    pallets["A1"] = "CHI TIẾT 2 PALLET — không cộng vào tổng danh sách"
    for column, title in {"A": "托盘号 Pallet", "B": "型号 Model", "C": "件数 Cartons",
                          "D": "毛重 G.W. (kg)", "E": "体积 CBM"}.items():
        pallets[f"{column}2"] = title
        pallets[f"{column}2"].font = Font(bold=True)
    for offset, row in enumerate(PALLET_ROWS):
        excel_row = 3 + offset
        for column, value in zip("ABCDE", row):
            pallets[f"{column}{excel_row}"] = value

    cartons = wb.create_sheet(SHEET_CARTONS)
    cartons["A1"] = "CHI TIẾT KIỆN — kích thước kiện W/D/H"
    for column, title in {"A": "型号 Model", "B": "品名", "C": "件数 Cartons", "D": "长 L (mm)",
                          "E": "宽 W (mm)", "F": "高 H (mm)", "G": "净重 N.W. (kg)",
                          "H": "毛重 G.W. (kg)", "I": "体积 CBM"}.items():
        cartons[f"{column}2"] = title
        cartons[f"{column}2"].font = Font(bold=True)
    for offset, row in enumerate(CARTON_ROWS):
        excel_row = 3 + offset
        for column, value in zip("ABCDEFGHI", row):
            cartons[f"{column}{excel_row}"] = value

    instruction = wb.create_sheet(SHEET_INSTRUCTION)
    instruction["A1"] = "打托指令 — HƯỚNG DẪN ĐÓNG PALLET (nội bộ)"
    instruction["A2"] = "Pallet 1: 6 kiện 浴室柜 800"
    instruction["A3"] = SENTINEL
    instruction["B3"] = 987654321
    instruction.sheet_state = "hidden"
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def build_oversized_width_workbook() -> bytes:
    """A genuinely oversized sheet (declared column 3000) must still be refused."""
    wb = Workbook()
    ws = wb.active
    ws["A1"] = "型号 Model"
    ws["B1"] = "数量 Qty"
    ws["A2"], ws["B2"] = "BC-800", 4
    ws.cell(row=2, column=3000).fill = PatternFill("solid", fgColor="FFFFFF")
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


FIXTURES = {
    "packing-list-257col-SYNTHETIC.xlsx": build_packing_list_with_images,
    "proforma-invoice-SYNTHETIC.xlsx": build_proforma_invoice,
    "multilevel-packing-SYNTHETIC.xlsx": build_multilevel_packing_list,
}

if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".tmp/hexa-fixtures")
    target.mkdir(parents=True, exist_ok=True)
    for file_name, builder in FIXTURES.items():
        data = builder()
        (target / file_name).write_bytes(data)
        print(f"SYNTHETIC_FIXTURE: {file_name} ({len(data)} bytes)")
