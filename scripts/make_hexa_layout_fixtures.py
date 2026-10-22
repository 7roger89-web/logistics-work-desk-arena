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


# ------------------------- C2: the REAL multi-level header layout (file C) ----
# Row/column positions and header WORDING here follow the independent review of
# the Owner's real workbook C. Values are still synthetic; only the STRUCTURE is
# reproduced. This is the fixture the old parser fails on:
#
#   总清单            header row 3, goods table rows 7-16
#   托盘明细（2托）   PALLET level: header row 1, repeated at row 9
#   卫浴              CARTON level: header row 2, W/D/H axis row 3, groups repeat
#   打托指令          hidden, never a customer sheet
TOTAL_HEADER_ROW_REAL = 3
TOTAL_FIRST_ROW_REAL = 7
TOTAL_HEADERS_REAL = {
    "A": "序号",
    "B": "Name product-Description",
    "C": "数量（件数）",
    "D": "净重",
    "E": "毛重",
    "F": "体积",
}
# The ten reference codes of the summary sheet. In the real workbook this column
# (`Name product-Description`) carries the CODE, and the same code is what the
# pallet sheet repeats in its `contract` column and what the carton sheet puts in
# `REF NO` — that is the only key that ties the three levels together.
GOODS_CODES_REAL = (
    "HD-2601-001", "HD-2601-002", "HD-2601-003", "HD-2601-004", "HD-2601-005",
    "HD-2601-006", "HD-2601-007", "HD-2601-008", "HD-2601-009", "HD-2601-010",
)
# (reference code, qty pieces, net weight kg, gross weight kg, volume cbm)
TOTAL_ROWS_REAL = (
    ("HD-2601-001", 12, 240.0, 268.0, 3.20),
    ("HD-2601-002", 8, 180.0, 202.0, 2.40),
    ("HD-2601-003", 6, 96.0, 108.0, 1.10),
    ("HD-2601-004", 5, 48.0, 55.0, 0.90),
    ("HD-2601-005", 4, 32.0, 38.0, 0.64),
    ("HD-2601-006", 3, 96.0, 105.0, 0.87),
    ("HD-2601-007", 20, 30.0, 34.0, 0.40),
    ("HD-2601-008", 15, 12.0, 14.0, 0.12),
    ("HD-2601-009", 6, 108.0, 121.0, 1.44),
    ("HD-2601-010", 4, 56.0, 63.0, 0.72),
)

PALLET_HEADERS_REAL = {
    "A": "The pallet number",
    "B": "Pallet size",
    "C": "contract",
    "D": "House type",
    "E": "Room number",
    "F": "Project name",
    "G": "PC",
    "H": "Total",
}
# 10 allocation lines on 2 pallets. As in the real sheet the pallet number is
# written ONCE per group (A2, A10) and the following lines leave column A blank,
# so the reader has to carry the group context forward. The `contract` column
# carries one summary code per allocation line.
PALLET_GROUP_ONE_FIRST_ROW_REAL = 2
PALLET_GROUP_ONE_ROWS_REAL = tuple(range(PALLET_GROUP_ONE_FIRST_ROW_REAL, 9))      # 2..8  (7 lines)
PALLET_REPEAT_HEADER_ROW_REAL = 9
PALLET_GROUP_TWO_ROWS_REAL = tuple(range(10, 13))                                  # 10..12 (3 lines)
PALLET_ALLOCATION_ROWS_REAL = PALLET_GROUP_ONE_ROWS_REAL + PALLET_GROUP_TWO_ROWS_REAL

# (contract code, house type, room, project, pc, total) — one per allocation line
PALLET_LINES_REAL = (
    ("HD-2601-001", "VILLA", "R01", "Du an mau A", 6, 12),
    ("HD-2601-002", "VILLA", "R02", "Du an mau A", 4, 8),
    ("HD-2601-003", "VILLA", "R03", "Du an mau A", 2, 6),
    ("HD-2601-004", "VILLA", "R04", "Du an mau A", 3, 5),
    ("HD-2601-005", "VILLA", "R05", "Du an mau A", 1, 4),
    ("HD-2601-006", "VILLA", "R06", "Du an mau A", 2, 3),
    ("HD-2601-007", "VILLA", "R07", "Du an mau A", 5, 20),
    ("HD-2601-008", "VILLA", "R08", "Du an mau A", 4, 15),
    ("HD-2601-009", "VILLA", "R09", "Du an mau A", 3, 6),
    ("HD-2601-010", "VILLA", "R10", "Du an mau A", 2, 4),
)
PALLET_NUMBER_BY_GROUP_REAL = {"group-1": "PLT-01", "group-2": "PLT-02"}
PALLET_SIZE_REAL = {"group-1": "1200x1000x1500", "group-2": "1100x900x1450"}

CARTON_HEADER_ROW_REAL = 2
CARTON_AXIS_ROW_REAL = 3
CARTON_HEADERS_REAL = {
    "A": "REF NO",
    "B": "Package NO",
    "C": "Desc.",
    "D": "Size(mm x mm x mm)",  # merged D:F, split into W/D/H on the axis row
    "G": "NW(KG)",
    "H": "GW(KG)",
    "I": "VOL(CBM)",
    "J": "数量(箱)",
    "K": "货物中文名称",
}
CARTON_AXES_REAL = {"D": "W", "E": "D", "F": "H"}
# Three groups of 12 carton lines = 36, each group preceded by the repeated
# header + the W/D/H axis row, and closed by a source TOTAL line.
CARTON_GROUP_HEADER_ROWS_REAL = (2, 16, 30)
CARTON_GROUP_ONE_ROWS_REAL = tuple(range(4, 16))    # 4..15   (12 lines)
CARTON_GROUP_TWO_ROWS_REAL = tuple(range(18, 30))   # 18..29  (12 lines)
CARTON_GROUP_THREE_ROWS_REAL = tuple(range(32, 44))  # 32..43  (12 lines)
CARTON_ROWS_REAL_ROWS = (CARTON_GROUP_ONE_ROWS_REAL + CARTON_GROUP_TWO_ROWS_REAL
                         + CARTON_GROUP_THREE_ROWS_REAL)
CARTON_TOTAL_ROW_REAL = 45
# (ref no, package no, desc, W, D, H, NW, GW, VOL, cartons, chinese name)
_CARTON_SHAPES_REAL = (
    ("Bathroom cabinet 800", 860, 540, 900, 48.0, 54.0, 0.42, 2, "浴室柜 800"),
    ("Bathroom cabinet 1000", 1060, 540, 900, 42.0, 47.0, 0.52, 2, "浴室柜 1000"),
    ("LED mirror 600", 660, 80, 860, 8.0, 9.0, 0.09, 4, "LED 镜 600"),
    ("Basin shelf 900", 960, 560, 800, 9.0, 11.0, 0.43, 1, "浴室架 900"),
    ("Shower column 1200", 1250, 220, 240, 8.0, 10.0, 0.07, 2, "淋浴柱 1200"),
    ("Toilet 700", 760, 480, 720, 32.0, 35.0, 0.26, 1, "马桶 700"),
    ("Faucet 200", 240, 180, 160, 1.5, 2.0, 0.01, 10, "龙头 200"),
    ("Floor drain 100", 120, 120, 60, 0.8, 1.0, 0.001, 5, "地漏 100"),
    ("Bathroom cabinet 600", 660, 440, 860, 18.0, 21.0, 0.25, 3, "浴室柜 600 木纹"),
    ("Mirror cabinet 700", 760, 180, 720, 14.0, 16.0, 0.10, 2, "镜柜 700"),
)
CARTON_ROWS_REAL = tuple(
    (GOODS_CODES_REAL[i % len(GOODS_CODES_REAL)],
     "PKG-%03d" % (i + 1), *_CARTON_SHAPES_REAL[i % len(_CARTON_SHAPES_REAL)])
    for i in range(len(CARTON_ROWS_REAL_ROWS))
)


def build_multilevel_packing_real_layout() -> bytes:
    """File C as it actually is: goods list → pallet level → carton level.

    Header WORDING, row positions and DATA SHAPE follow the independent review of
    the real workbook; every value is invented (`HD-2601-00x` codes, fake rooms):

    * the pallet number is written once per group (A2, A10) and the following
      allocation lines leave column A blank;
    * the `contract` column carries one summary code per allocation line, and all
      ten summary codes are present exactly once;
    * the carton sheet has 36 carton lines whose `REF NO` is one of those codes,
      split over three groups separated by the repeated header + W/D/H axis row,
      and closed by a source TOTAL line.
    """
    wb = Workbook()

    total = wb.active
    total.title = SHEET_TOTAL
    total["A1"] = BANNER
    total["A1"].font = WARN_FONT
    total["A2"] = "TỔNG DANH SÁCH HÀNG — 2 PALLET / 10 DÒNG"
    for column, title in TOTAL_HEADERS_REAL.items():
        cell = total[f"{column}{TOTAL_HEADER_ROW_REAL}"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for offset, (code, qty, net, gross, cbm) in enumerate(TOTAL_ROWS_REAL):
        excel_row = TOTAL_FIRST_ROW_REAL + offset
        total[f"A{excel_row}"] = offset + 1
        total[f"B{excel_row}"] = code
        total[f"C{excel_row}"] = qty
        total[f"D{excel_row}"] = net
        total[f"E{excel_row}"] = gross
        total[f"F{excel_row}"] = cbm
    total.column_dimensions["B"].width = 42

    pallets = wb.create_sheet(SHEET_PALLETS)

    def pallet_header(excel_row: int) -> None:
        for column, title in PALLET_HEADERS_REAL.items():
            cell = pallets[f"{column}{excel_row}"]
            cell.value = title
            cell.font = Font(name="Arial", size=10, bold=True)
            cell.fill = HEAD_FILL

    def pallet_group(excel_row: int, group: str, lines) -> None:
        """First line names the pallet; the following lines leave A blank."""
        for offset, (contract, house, room, project, pc, total_count) in enumerate(lines):
            row = excel_row + offset
            if offset == 0:
                pallets[f"A{row}"] = PALLET_NUMBER_BY_GROUP_REAL[group]
            pallets[f"B{row}"] = PALLET_SIZE_REAL[group]
            pallets[f"C{row}"] = contract
            pallets[f"D{row}"] = house
            pallets[f"E{row}"] = room
            pallets[f"F{row}"] = project
            pallets[f"G{row}"] = pc
            pallets[f"H{row}"] = total_count

    pallet_header(1)
    pallet_group(PALLET_GROUP_ONE_FIRST_ROW_REAL, "group-1",
                 PALLET_LINES_REAL[:len(PALLET_GROUP_ONE_ROWS_REAL)])
    pallet_header(PALLET_REPEAT_HEADER_ROW_REAL)
    pallet_group(PALLET_GROUP_TWO_ROWS_REAL[0], "group-2",
                 PALLET_LINES_REAL[len(PALLET_GROUP_ONE_ROWS_REAL):])

    cartons = wb.create_sheet(SHEET_CARTONS)
    cartons["A1"] = "CHI TIẾT KIỆN THEO NHÓM — 3 NHÓM / 36 DÒNG"

    def carton_header(excel_row: int) -> None:
        for column, title in CARTON_HEADERS_REAL.items():
            cell = cartons[f"{column}{excel_row}"]
            cell.value = title
            cell.font = Font(name="Arial", size=10, bold=True)
            cell.fill = HEAD_FILL
        cartons.merge_cells(
            start_row=excel_row, start_column=4, end_row=excel_row, end_column=6)
        for column, axis in CARTON_AXES_REAL.items():
            cartons[f"{column}{excel_row + 1}"] = axis

    groups = (CARTON_GROUP_ONE_ROWS_REAL, CARTON_GROUP_TWO_ROWS_REAL,
              CARTON_GROUP_THREE_ROWS_REAL)
    cursor = 0
    for header_row, rows_of_group in zip(CARTON_GROUP_HEADER_ROWS_REAL, groups):
        carton_header(header_row)
        for excel_row in rows_of_group:
            for column, value in zip("ABCDEFGHIJK", CARTON_ROWS_REAL[cursor]):
                cartons[f"{column}{excel_row}"] = value
            cursor += 1
    cartons[f"A{CARTON_TOTAL_ROW_REAL}"] = "TOTAL"
    cartons[f"J{CARTON_TOTAL_ROW_REAL}"] = sum(row[9] for row in CARTON_ROWS_REAL)
    cartons[f"I{CARTON_TOTAL_ROW_REAL}"] = round(sum(row[8] for row in CARTON_ROWS_REAL), 3)

    instruction = wb.create_sheet(SHEET_INSTRUCTION)
    instruction["A1"] = "打托指令 — HƯỚNG DẪN ĐÓNG PALLET (nội bộ)"
    instruction["A2"] = "Pallet 1: 7 dòng phân bổ · Pallet 2: 3 dòng phân bổ"
    instruction["A3"] = SENTINEL
    instruction["B3"] = 987654321
    instruction.sheet_state = "hidden"
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ------------------- A2/B2: the REAL file A and file B HEADER wording --------
SHEET_PACKING_REAL = "Sheet1"
PACKING_HEADER_ROW_REAL = 7
PACKING_HEADERS_REAL = {
    "A": "Item number",
    "B": "Product name",
    "C": "Size",
    "D": "Quantity",
    "E": "CTN",
    "F": "NW",
    "G": "GW",
    "H": "CBM",
}
# (item number, product name, size, quantity, ctn, nw, gw, cbm) — NO unit price
PACKING_ROWS_REAL = (
    ("BC-800", "Bathroom cabinet 800", "800x480x850", 12, 6, 96.0, 108.0, 2.51),
    ("BC-1000", "Bathroom cabinet 1000", "1000x480x850", 8, 4, 84.0, 94.0, 2.06),
    ("MC-600", "LED mirror 600", "600x20x800", 6, 4, 32.0, 36.0, 0.91),
)

SHEET_PI_REAL = "PI (2)"
SHEET_PI_MONEY_REAL = "File tiền hàng"
PI_HEADER_ROW_REAL = 7
PI_HEADERS_REAL = {
    "A": "Model 型号",
    "B": "Size尺寸(MM)",
    "C": "Qt.数量",
    "D": "Unit Price 单价 (CNY)",
    "E": "Amount 金额 (CNY)",
}
# (model, size, qty, unit price CNY); the first row's amount is an UNCACHED
# formula so the price stays UNKNOWN instead of becoming 0.
PI_ROWS_REAL = (
    ("BC-800", "800x480x850", 12, 180.0),
    ("BC-1000", "1000x480x850", 8, 240.0),
    ("MC-600", "600x20x800", 6, 95.0),
)


def build_packing_list_real_headers() -> bytes:
    """File A: product photos, header row 7, exact real header wording, no price."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_PACKING_REAL
    ws["A1"] = BANNER
    ws["A1"].font = WARN_FONT
    ws["A3"] = "PACKING LIST"
    ws["A3"].font = Font(name="Arial", size=14, bold=True)
    for offset, (item, name, size, qty, ctn, nw, gw, cbm) in enumerate(PACKING_ROWS_REAL):
        excel_row = PACKING_HEADER_ROW_REAL + 1 + offset
        for column, value in zip("ABCDEFGH", (item, name, size, qty, ctn, nw, gw, cbm)):
            ws[f"{column}{excel_row}"] = value
        ws.add_image(XLImage(_picture()), f"J{excel_row}")
    for column, title in PACKING_HEADERS_REAL.items():
        cell = ws[f"{column}{PACKING_HEADER_ROW_REAL}"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def build_proforma_invoice_real_headers() -> bytes:
    """File B: ``PI (2)`` + the internal ``File tiền hàng`` money sheet."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_PI_REAL
    ws["A1"] = BANNER
    ws["A1"].font = WARN_FONT
    ws["A2"] = "PROFORMA INVOICE"
    for column, title in PI_HEADERS_REAL.items():
        cell = ws[f"{column}{PI_HEADER_ROW_REAL}"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
    for offset, (model, size, qty, price) in enumerate(PI_ROWS_REAL):
        excel_row = PI_HEADER_ROW_REAL + 1 + offset
        ws[f"A{excel_row}"] = model
        ws[f"B{excel_row}"] = size
        ws[f"C{excel_row}"] = qty
        ws[f"D{excel_row}"] = price
        ws[f"E{excel_row}"] = f"=C{excel_row}*D{excel_row}"
    # Every amount is a formula the fixture never caches: the reader must not
    # invent the value, and a missing price must stay UNKNOWN, never 0.

    money = wb.create_sheet(SHEET_PI_MONEY_REAL)
    money["A1"] = "BẢNG TÍNH TIỀN HÀNG — NỘI BỘ, KHÔNG GỬI KHÁCH"
    money["A1"].font = WARN_FONT
    for column, title in {"A": "Model", "B": "Qt.数量", "C": "Unit Price 单价 (CNY)",
                          "D": "Amount 金额 (CNY)"}.items():
        money[f"{column}3"] = title
    for offset, (model, _size, qty, price) in enumerate(PI_ROWS_REAL):
        excel_row = 4 + offset
        money[f"A{excel_row}"] = model
        money[f"B{excel_row}"] = qty
        money[f"C{excel_row}"] = price
        money[f"D{excel_row}"] = f"=B{excel_row}*C{excel_row}"
    money["A8"], money["B8"] = "Giá vốn nội bộ", SENTINEL
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --------- B3: the REAL PI identity layout (code column + name column) ------
# Workbook `PL1(1).xlsx`, sheet `PI (2)`, header row 7:
#   B `Mã` (5 distinct codes) · C `Model 型号` (product NAMES) · E `Size尺寸(MM)`
#   F `Qt.数量` · G `Unit Price 单价 (CNY)` · H `Amount 金额 (CNY)`
# Two rows carry the SAME name (`ghế`) with DIFFERENT codes: the code column is
# the identity, and collapsing the two rows by name would lose a product.
PI_IDENTITY_SHEET = "PI (2)"
PI_IDENTITY_MONEY_SHEET = "File tiền hàng"
PI_IDENTITY_HEADER_ROW = 7
PI_IDENTITY_HEADERS = {
    "A": "STT",
    "B": "Mã",
    "C": "Model 型号",
    "E": "Size尺寸(MM)",
    "F": "Qt.数量",
    "G": "Unit Price 单价 (CNY)",
    "H": "Amount 金额 (CNY)",
}
# (code, name, size, qty, unit price CNY) — rows 8..12
PI_IDENTITY_ROWS = (
    ("GH-001", "ghế", "450x450x900", 10, 120.0),
    ("GH-002", "ghế", "460x460x880", 6, 135.0),
    ("BN-100", "bàn", "1200x600x750", 4, 260.0),
    ("TU-200", "tủ", "800x400x1800", 2, 480.0),
    ("KE-300", "kệ", "900x350x1200", 3, 210.0),
)


def build_proforma_invoice_pi_identity() -> bytes:
    """File B as it really is: a `Mã` code column beside a `Model 型号` name column."""
    wb = Workbook()
    ws = wb.active
    ws.title = PI_IDENTITY_SHEET
    ws["A1"] = BANNER
    ws["A1"].font = WARN_FONT
    ws["A2"] = "PROFORMA INVOICE"
    for column, title in PI_IDENTITY_HEADERS.items():
        cell = ws[f"{column}{PI_IDENTITY_HEADER_ROW}"]
        cell.value = title
        cell.font = Font(name="Arial", size=10, bold=True)
        cell.fill = HEAD_FILL
    for offset, (code, name, size, qty, price) in enumerate(PI_IDENTITY_ROWS):
        excel_row = PI_IDENTITY_HEADER_ROW + 1 + offset
        ws[f"A{excel_row}"] = offset + 1
        ws[f"B{excel_row}"] = code
        ws[f"C{excel_row}"] = name
        ws[f"E{excel_row}"] = size
        ws[f"F{excel_row}"] = qty
        ws[f"G{excel_row}"] = price
        # Amount is a formula with no cached value: it must stay UNKNOWN.
        ws[f"H{excel_row}"] = f"=F{excel_row}*G{excel_row}"
    ws.column_dimensions["C"].width = 28

    money = wb.create_sheet(PI_IDENTITY_MONEY_SHEET)
    money["A1"] = "BẢNG TÍNH TIỀN HÀNG — NỘI BỘ, KHÔNG GỬI KHÁCH"
    money["A1"].font = WARN_FONT
    for column, title in {"A": "Mã", "B": "Qt.数量",
                          "C": "Unit Price 单价 (CNY)", "D": "Amount 金额 (CNY)"}.items():
        money[f"{column}3"] = title
    for offset, (code, _name, _size, qty, price) in enumerate(PI_IDENTITY_ROWS):
        excel_row = 4 + offset
        money[f"A{excel_row}"] = code
        money[f"B{excel_row}"] = qty
        money[f"C{excel_row}"] = price
        money[f"D{excel_row}"] = f"=B{excel_row}*C{excel_row}"
    money["A10"], money["B10"] = "Giá vốn nội bộ", SENTINEL
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


FIXTURES = {
    "packing-list-257col-SYNTHETIC.xlsx": build_packing_list_with_images,
    "proforma-invoice-SYNTHETIC.xlsx": build_proforma_invoice,
    "multilevel-packing-SYNTHETIC.xlsx": build_multilevel_packing_list,
    "multilevel-packing-REAL-LAYOUT-SYNTHETIC.xlsx": build_multilevel_packing_real_layout,
    "packing-list-REAL-HEADERS-SYNTHETIC.xlsx": build_packing_list_real_headers,
    "proforma-invoice-REAL-HEADERS-SYNTHETIC.xlsx": build_proforma_invoice_real_headers,
    "proforma-invoice-PI-IDENTITY-SYNTHETIC.xlsx": build_proforma_invoice_pi_identity,
}

if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".tmp/hexa-fixtures")
    target.mkdir(parents=True, exist_ok=True)
    for file_name, builder in FIXTURES.items():
        data = builder()
        (target / file_name).write_bytes(data)
        print(f"SYNTHETIC_FIXTURE: {file_name} ({len(data)} bytes)")
