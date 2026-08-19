# LG05 Fix Notes

## Issue: Owner says "import file từ getfly vào, không được, không có đơn hàng nào cả"

## Root causes identified and fixed:
1. `st.data_editor` returns `list` instead of `pd.DataFrame` when input is list of dicts → Fixed in shipment.py (always convert to DataFrame)
2. `uploaded.read()` on st.file_uploader returns empty bytes on rerun → Fixed with `uploaded.seek(0)` before read() + session state persistence
3. GNT expander was collapsed → Changed to visible container

## Remaining concern:
- Owner might see 0 groups in preview. Core logic verified: 14 groups from 40 rows with Owner's Excel file.
- Possible issue: `st.session_state.db_shipments` not initialized when import UI renders.

## Current state:
- Branch: log-lg05-excel-round-trip-gnt
- HEAD before latest fixes: 494ae68
- Latest uncommitted: added seek(0) to dashboard.py import UI
- Tests: 256 passed

## Owner's Excel file: /home/ubuntu/upload/danhsachdonhang-.xlsx
- 52 columns A:AZ
- 40 data rows, 14 unique shipment IDs (Getfly order IDs)
- Columns: order_date, created_date, shipment_id, executor, customer_code, customer_name, phone, email, delivery_address, contact_person, contact_phone, province, district, customer_source, tracking_no, tracking_status, warehouse_code, product_code, product_name, description, unit, product_group, qty, cost_price, sale_price, discount_pct, discount_amt, vat_pct, line_total, line_profit, revenue, discount_vnd, revenue_after_disc, shipping_fee, install_fee, revenue_pre_tax, vat_vnd, total_revenue, paid_amount, remaining_amount, profit, payment_terms, payment_method, payment_method_each, payment_date, order_source, creator, status, customer_group, refund, referral_bonus, risk_level
