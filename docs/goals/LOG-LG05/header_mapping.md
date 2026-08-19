# Root Cause: Excel Header Mismatch

The Owner's Excel file `danhsachdonhang-.xlsx` has **Vietnamese headers**, NOT English field names.

## Actual headers (52 columns):
```
0: 'Ngày đặt hàng'
1: 'Ngày tạo'
2: 'Mã ĐH'
3: 'Người thực hiện'
4: 'Mã KH'
5: 'Tên KH'
6: 'Số ĐT'
7: 'Email'
8: 'Địa chỉ giao hàng'
9: 'Người liên hệ'
10: 'Điện thoại người liên hệ'
11: 'Tỉnh/ TP'
12: 'Quận/ Huyện'
13: 'Nguồn khách hàng'
14: 'Mã vận đơn'
15: 'Trạng thái vận đơn'
16: 'Mã kho'
17: 'Mã SP'
18: 'Tên sản phẩm'
19: 'Mô tả'
20: 'Đơn vị'
21: 'Nhóm sản phẩm'
22: 'Số lượng'
23: 'Giá vốn'
24: 'Giá bán'
25: 'CK(%)'
26: 'CK(Đ)'
27: 'VAT(%)'
28: 'Thành tiền'
29: 'Lợi nhuận SP'
30: 'Doanh số'
31: 'Chiết khấu (đ)'
32: 'Doanh thu sau CK'
33: 'Phí vận chuyển (đ)'
34: 'Phí lắp đặt (đ)'
35: 'Doanh thu trước thuế'
36: 'VAT (đ)'
37: 'Doanh thu'
38: 'Đã thanh toán'
39: 'Còn lại'
40: 'Lợi nhuận'
41: 'Điều khoản đơn hàng'
42: 'Hình thức thanh toán'
43: 'Hình thức thanh toán từng lần'
44: 'Ngày thanh toán'
45: 'Nguồn đơn hàng'
46: 'Người tạo'
47: 'Trạng thái'
48: 'Nhóm khách hàng'
49: 'REFUN'
50: 'HOA HỒNG KH GỬI'
51: 'CẤP ĐỘ RỦI RO'
```

## Current code issue:
`excel_roundtrip.py` uses `ALL_FIELD_NAMES` with English internal field names (shipment_id, customer_name, product_code, etc.) but the actual Excel headers are Vietnamese. The parse function maps by column INDEX, not by header name, so the VALUES are correct. BUT the `has_master` / `has_service` checks use field names like "shipment_id" and "product_code" which ARE the internal names used in the values dict. So the grouping should work.

Wait — actually the parse uses column INDEX to map to internal field names. So column index 2 → "shipment_id", index 17 → "product_code", etc. The VALUES dict uses internal names. So the grouping SHOULD work.

Let me re-verify: earlier test showed 14 groups from 40 rows. So the core logic IS correct. The issue must be in the UI — specifically the `st.session_state.db_shipments` not being loaded, or the file bytes being lost on rerun.

The fixes I already applied:
1. `uploaded.seek(0)` before `.read()`
2. Store bytes in `st.session_state["lg05_excel_bytes"]`
3. Ensure `db_shipments` is loaded before validate

These should fix the issue. But I also need to make sure the EXPORT uses Vietnamese headers to match the Owner's format.
