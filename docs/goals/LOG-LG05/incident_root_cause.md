# LG05 GETFLY IMPORT INCIDENT — ROOT CAUSE DIAGNOSIS

## Evidence Chain

### 1. ORIGINAL_GETFLY_OPENPYXL_RESULT
- `openpyxl.load_workbook()` → FAIL: `ValueError: Unable to read workbook: could not read stylesheet`
- Cause: `xl/styles.xml` contains `rgb="#ccc"` (invalid non-aRGB syntax)
- 3 invalid rgb patterns found in styles.xml

### 2. CALAMINE_READER_RESULT
- `pd.read_excel(..., engine="calamine")` → OK
- 41 physical rows (including header) = 40 data rows
- 52 columns (A:AZ)
- openpyxl cannot read the file AT ALL (both read_only and regular mode fail)
- calamine reads fine because it's values-oriented, doesn't parse styles.xml

### 3. CURRENT IMPORTER STATUS
- The current importer in `views/dashboard.py` uses `core/excel_roundtrip.py` which uses `pd.read_excel(..., engine="calamine")` — VALUES-ORIENTED reader
- So the styles.xml defect is ALREADY handled by the calamine engine
- BUT: if any code path uses openpyxl (e.g., export), it would fail

### 4. FILE FACTS
- HEADER_COUNT: 52
- DATA_ROWS: 40
- ORDER_COUNT: 14 (non-empty Mã ĐH)
- SERVICE_LINE_COUNT: 40 - 14 = 26 continuation rows

### 5. DATE SEMANTICS (CRITICAL ROOT CAUSE)
- GETFLY_ORDER_DATE_FIELD = "Ngày đặt hàng" (column A) → maps to `data['0.0']['order_date']`
- GETFLY_CREATED_DATE_FIELD = "Ngày tạo" (column B) → maps to `data['0.0']['created_at']`
- DASHBOARD_PERIOD_FIELD = `get_shipment_business_date()` → uses `created_at` only

- Evidence from actual file:
  - All 14/14 orders have "Ngày đặt hàng" in Aug 2026
  - Only 6/14 orders have "Ngày tạo" in Aug 2026
  - Dashboard filter "Tháng này" (Aug 2026) uses `created_at` → only 6 visible

### 6. ROOT CAUSE
The dashboard period filter uses `created_at` (GETFLY's "Ngày tạo" = record creation metadata)
instead of `order_date` (GETFLY's "Ngày đặt hàng" = canonical business order date).
This causes imported orders to be invisible when "Ngày tạo" differs from "Ngày đặt hàng".

### 7. FIX REQUIRED
`get_shipment_business_date()` in `core/utils.py` should:
1. Check `data['0.0']['order_date']` first (canonical business date)
2. Fall back to `data['0.0']['created_at']`
3. Fall back to top-level `created_at`

### 8. WRITE PATH
- UI handler: `views/dashboard.py` → `_handle_excel_import()` (approx line 328+)
- Parser: `core/excel_roundtrip.py` → `parse_excel_bytes()` → `group_rows()`
- Mapper: `core/excel_roundtrip.py` → `group_to_shipment_doc()`
- Writer: `db.shipments.update_one()` (via update_shipment_data in views/dashboard.py)
- Canonical collection: `logistics_db.shipments`

### 9. CACHE
- `st.cache_resource` for DB connection (core/database.py)
- `st.cache_data` for `load_data`, `load_customers`, `load_contracts` (core/database.py)
- After import: need `st.cache_data.clear()` or targeted invalidation

### 10. CURRENT STATE
- Branch: log-lg05-excel-round-trip-gnt
- HEAD: 219bd0a
- All 257 tests pass
