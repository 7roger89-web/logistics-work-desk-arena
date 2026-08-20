# LG05 Fix Notes

## Timeline of fixes:
1. `st.data_editor` list vs DataFrame → fixed in shipment.py (always convert to DataFrame)
2. GNT expander collapsed → changed to visible container in shipment.py IMPORT tab
3. GNT button removed from dashboard header (moved to IMPORT tab)
4. `timedelta` NameError → fixed: `datetime.timedelta` (line 553)
5. Import file bytes lost on rerun → fixed with seek(0) + getvalue() fallback + session state
6. `save_shipment_atomic(sid, doc)` wrong signature → fixed with db.shipments.update_one upsert
7. `db_shipments` not initialized → auto-load from DB if missing
8. Expander key added to persist expanded state across reruns

## Current state:
- Branch: log-lg05-excel-round-trip-gnt
- Last committed: dfb2c41 (timedelta + import fixes)
- Uncommitted: expander key fix, file_bytes fallback
- Tests: 256 passed

## Owner's Excel file headers (Vietnamese):
0: 'Ngày đặt hàng', 1: 'Ngày tạo', 2: 'Mã ĐH', 3: 'Người thực hiện', 4: 'Mã KH',
5: 'Tên KH', 6: 'Số ĐT', 7: 'Email', 8: 'Địa chỉ giao hàng', 9: 'Người liên hệ',
10: 'Điện thoại người liên hệ', 11: 'Tỉnh/ TP', 12: 'Quận/ Huyện', 13: 'Nguồn khách hàng',
14: 'Mã vận đơn', 15: 'Trạng thái vận đơn', 16: 'Mã kho', 17: 'Mã SP', 18: 'Tên sản phẩm',
19: 'Mô tả', 20: 'Đơn vị', 21: 'Nhóm sản phẩm', 22: 'Số lượng', 23: 'Giá vốn', 24: 'Giá bán',
25: 'CK(%)', 26: 'CK(Đ)', 27: 'VAT(%)', 28: 'Thành tiền', 29: 'Lợi nhuận SP', 30: 'Doanh số',
31: 'Chiết khấu (đ)', 32: 'Doanh thu sau CK', 33: 'Phí vận chuyển (đ)', 34: 'Phí lắp đặt (đ)',
35: 'Doanh thu trước thuế', 36: 'VAT (đ)', 37: 'Doanh thu', 38: 'Đã thanh toán', 39: 'Còn lại',
40: 'Lợi nhuận', 41: 'Điều khoản đơn hàng', 42: 'Hình thức thanh toán', 43: 'Hình thức thanh toán từng lần',
44: 'Ngày thanh toán', 45: 'Nguồn đơn hàng', 46: 'Người tạo', 47: 'Trạng thái', 48: 'Nhóm khách hàng',
49: 'REFUN', 50: 'HOA HỒNG KH GỬI', 51: 'CẤP ĐỘ RỦI RO'

## Core logic verified:
- parse_excel_bytes: 40 rows, 0 errors
- group_rows: 14 groups
- validate_groups: is_valid=True
- group_to_shipment_doc: produces correct doc structure

## Remaining issue (Owner reports "không có đơn hàng nào cả"):
- The preview shows 0 groups. Core logic produces 14 groups in sandbox test.
- Possible causes: file bytes empty after read(), expander collapsed, db_shipments empty
- All three have been addressed. Need Owner to pull and test again.
