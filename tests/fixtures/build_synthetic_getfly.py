"""Build a synthetic GETFLY Excel fixture for regression testing.

Creates a 52-column GETFLY-format workbook matching HEADERS_52:
- Col A: "Ngày đặt hàng" (order date)
- Col B: "Ngày tạo" (created date)  
- Col C: "Mã ĐH" (shipment ID)
- Col F: "Tên KH" (customer name)
- Col R/S/Y: product/service fields

Corrupts styles.xml with rgb="#ccc" (matching the GETFLY defect) to prove
calamine handles it while openpyxl fails.

3 orders, 7 service lines total, all order_dates in Aug 2026.
"""
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
import zipfile
import shutil
import os


HEADERS_52 = [
    "Ngày đặt hàng",          # A
    "Ngày tạo",               # B
    "Mã ĐH",                  # C
    "Người thực hiện",        # D
    "Mã KH",                  # E
    "Tên KH",                 # F
    "Số ĐT",                  # G
    "Email",                  # H
    "Địa chỉ giao hàng",      # I
    "Người liên hệ",          # J
    "Điện thoại người liên hệ",  # K
    "Tỉnh/ TP",               # L
    "Quận/ Huyện",            # M
    "Nguồn khách hàng",       # N
    "Mã vận đơn",             # O
    "Trạng thái vận đơn",     # P
    "Mã kho",                 # Q
    "Mã SP",                  # R
    "Tên sản phẩm",           # S
    "Mô tả",                  # T
    "Đơn vị",                 # U
    "Nhóm sản phẩm",          # V
    "Số lượng",               # W
    "Giá vốn",                # X
    "Giá bán",                # Y
    "CK(%)",                  # Z
    "CK(Đ)",                  # AA
    "VAT(%)",                 # AB
    "Thành tiền",             # AC
    "Lợi nhuận SP",           # AD
    "Doanh số",               # AE
    "Chiết khấu (đ)",         # AF
    "Doanh thu sau CK",       # AG
    "Phí vận chuyển (đ)",     # AH
    "Phí lắp đặt (đ)",        # AI
    "Doanh thu trước thuế",   # AJ
    "VAT (đ)",                # AK
    "Doanh thu",              # AL
    "Đã thanh toán",          # AM
    "Còn lại",                # AN
    "Lợi nhuận",              # AO
    "Điều khoản đơn hàng",    # AP
    "Hình thức thanh toán",   # AQ
    "Hình thức thanh toán từng lần",  # AR
    "Ngày thanh toán",        # AS
    "Nguồn đơn hàng",        # AT
    "Người tạo",              # AU
    "Trạng thái",             # AV
    "Nhóm khách hàng",        # AW
    "REFUN",                  # AX
    "HOA HỒNG KH GỬI",        # AY
    "CẤP ĐỘ RỦI RO",         # AZ
]

ORDERS = [
    {
        "order_date": "01/08/2026",
        "created_at": "15/07/2026",
        "order_no": "SYN-2026-001",
        "customer": "CÔNG TY TNHH SYNTHETIC ALPHA",
        "services": [
            {"name": "Vận chuyển tiêu chuẩn", "price": "150000", "code": "VC-001"},
            {"name": "Đóng gói gỗ", "price": "50000", "code": "DG-002"},
            {"name": "Bốc xếp", "price": "30000", "code": "BX-003"},
        ],
    },
    {
        "order_date": "10/08/2026",
        "created_at": "20/06/2026",
        "order_no": "SYN-2026-002",
        "customer": "CÔNG TY TNHH SYNTHETIC BETA",
        "services": [
            {"name": "Vận chuyển nhanh", "price": "250000", "code": "VN-004"},
            {"name": "Bảo hiểm hàng hóa", "price": "20000", "code": "BH-005"},
        ],
    },
    {
        "order_date": "25/08/2026",
        "created_at": "01/09/2026",
        "order_no": "SYN-2026-003",
        "customer": "CÔNG TY TNHH SYNTHETIC GAMMA",
        "services": [
            {"name": "Vận chuyển hàng nặng", "price": "500000", "code": "VH-006"},
            {"name": "Cẩu hàng", "price": "100000", "code": "CH-007"},
        ],
    },
]


def build_fixture(output_path: str) -> None:
    """Build the synthetic GETFLY Excel file with corrupted styles.xml."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    # Add dashed border to trigger border color elements in styles.xml
    dashed = Side(style='dashed', color='CCCCCC')
    border = Border(left=dashed, right=dashed, top=dashed, bottom=dashed)

    # Write headers
    for col_idx, header in enumerate(HEADERS_52, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    # Write data rows
    row = 2
    for order in ORDERS:
        first_row_in_group = True
        for svc in order["services"]:
            if first_row_in_group:
                ws.cell(row=row, column=1, value=order["order_date"]).border = border
                ws.cell(row=row, column=2, value=order["created_at"]).border = border
                ws.cell(row=row, column=3, value=order["order_no"]).border = border
                ws.cell(row=row, column=6, value=order["customer"]).border = border
                first_row_in_group = False
            ws.cell(row=row, column=18, value=svc["code"]).border = border
            ws.cell(row=row, column=19, value=svc["name"]).border = border
            ws.cell(row=row, column=25, value=svc["price"]).border = border
            row += 1

    wb.save(output_path)

    # Corrupt styles.xml: replace <color rgb="00CCCCCC"/> with <color rgb="#ccc"/>
    tmp_path = output_path + ".tmp"
    shutil.copy(output_path, tmp_path)

    with zipfile.ZipFile(tmp_path, 'r') as zin:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.namelist():
                data = zin.read(item)
                if item == 'xl/styles.xml':
                    xml_str = data.decode('utf-8')
                    xml_str = xml_str.replace('<color rgb="00CCCCCC"/>', '<color rgb="#ccc"/>')
                    data = xml_str.encode('utf-8')
                zout.writestr(item, data)

    os.remove(tmp_path)


if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures/synthetic_getfly.xlsx"
    build_fixture(output)
    print(f"Built: {output}")
