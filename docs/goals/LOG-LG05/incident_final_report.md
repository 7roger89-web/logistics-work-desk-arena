# LOG-LG05 — GETFLY Import Incident: Final Evidence Report

**Date:** 2026-08-19
**Branch:** `log-lg05-excel-round-trip-gnt`
**PR:** #4 (draft, not merged)
**Fix SHA:** `9629f33` (incident fix in `59d77ef`, state update in `9629f33`)
**Branch HEAD:** `9629f33`

---

## 1. GETFLY IMPORT ROOT CAUSE

**Primary root cause:** The dashboard period filter uses `created_at` (Ngày tạo) instead of `order_date` (Ngày đặt hàng) in `get_shipment_business_date()`. Of the Owner's 14 orders, all have "Ngày đặt hàng" in August 2026, but only 6 have "Ngày tạo" in August 2026. Therefore, 8 orders are invisible under the "Tháng này" filter.

**Secondary issue (non-blocking):** The Owner's Excel file (`danhsachdonhang-.xlsx`) has malformed `styles.xml` containing `rgb="#ccc"` (invalid aRGB hex format). However, the importer already uses the `calamine` engine which is values-oriented and ignores `styles.xml`, so this defect does NOT block the import.

## 2. ORIGINAL FILE PARSE RESULT

| Metric | Value |
|--------|-------|
| File | `danhsachdonhang-.xlsx` |
| Engine | python-calamine (values-oriented) |
| Total rows | 41 (1 header + 40 data) |
| Total columns | 52 |
| Non-empty Mã ĐH (orders) | 14 |
| Continuation rows (service lines) | 26 |
| Parse errors | 0 |

## 3. STYLE DEFECT RESULT

| Check | Result |
|-------|--------|
| openpyxl can read Owner file? | **FAIL** — `ValueError: Colors must be aRGB hex values` (due to `rgb="#ccc"` in `xl/styles.xml`) |
| calamine can read Owner file? | **OK** — 41 rows × 52 cols |
| Is the styles defect blocking import? | **NO** — importer uses calamine engine |

## 4. 52-COLUMN RESULT

| Check | Result |
|-------|--------|
| HEADERS_52 count | 52 ✓ |
| Col A = "Ngày đặt hàng" | ✓ |
| Col B = "Ngày tạo" | ✓ |
| Col C = "Mã ĐH" | ✓ |
| Col F = "Tên KH" | ✓ |
| Col AZ = "CẤP ĐỘ RỦI RO" | ✓ |

## 5. ORDER GROUP COUNT

| Check | Result |
|-------|--------|
| Total orders (non-empty Mã ĐH) | **14** |
| Total service continuation rows | 26 |
| Grouping rule | Master row (has Mã ĐH) starts new group; continuation rows belong to current group |

## 6. DATE MAPPING

| Order | order_date (Ngày đặt hàng) | created_at (Ngày tạo) | Visible under "Tháng này" using order_date? | Visible using created_at? |
|-------|---------------------------|----------------------|--------------------------------------------|--------------------------|
| 1 | 25/08/2026 | 17/12/2025 | ✓ | ✗ |
| 2 | 20/08/2026 | 14/08/2026 | ✓ | ✓ |
| 3 | 17/08/2026 | 17/08/2026 | ✓ | ✓ |
| 4 | 15/08/2026 | 29/07/2026 | ✓ | ✗ |
| 5 | 15/08/2026 | 29/07/2026 | ✓ | ✗ |
| 6 | 15/08/2026 | 15/07/2026 | ✓ | ✗ |
| 7 | 15/08/2026 | 15/07/2026 | ✓ | ✗ |
| 8 | 14/08/2026 | 17/08/2026 | ✓ | ✓ |
| 9 | 14/08/2026 | 17/08/2026 | ✓ | ✓ |
| 10 | 13/08/2026 | 17/08/2026 | ✓ | ✓ |
| 11 | 10/08/2026 | 15/07/2026 | ✓ | ✗ |
| 12 | 05/08/2026 | 06/11/2025 | ✓ | ✗ |
| 13 | 04/08/2026 | 04/08/2026 | ✓ | ✓ |
| 14 | 01/08/2026 | 22/07/2026 | ✓ | ✗ |
| **TOTAL** | **14/14 ✓** | **6/14** | **14 visible** | **8 invisible** |

**CONFIRMED:** 8 orders are invisible under "Tháng này" when using `created_at`, but all 14 are visible when using `order_date`.

## 7. WRITE PATH

| Step | Component | Status |
|------|-----------|--------|
| FILE → PARSE | `core/excel_roundtrip.py` → `parse_excel_bytes()` (calamine engine) | ✓ |
| PARSE → GROUP | `group_rows()` — master row starts group, continuation rows appended | ✓ |
| GROUP → VALIDATE | `validate_groups()` — checks against existing IDs, no DB mutation | ✓ |
| VALIDATE → MAP | `group_to_shipment_doc()` — produces canonical shipment document | ✓ |
| MAP → WRITE | `db.shipments.update_one({"id": sid}, {"$set": doc}, upsert=True)` | ✓ |
| Write to DB | MongoDB `logistics_db.shipments` (canonical collection) | ✓ |

## 8. CANONICAL COLLECTION

| Check | Result |
|-------|--------|
| Collection name | `logistics_db.shipments` |
| Document ID field | `id` (from Mã ĐH) |
| Upsert behavior | New orders inserted, existing orders merged (details appended, financial not overwritten) |

## 9. DB READ-BACK

| Check | Result |
|-------|--------|
| After write, `db.shipments.find_one({"id": sid})` returns the document? | ✓ (verified via `load_data()` in session_state refresh) |
| Document structure preserved? | ✓ (id, data.0.0, data.3.4, etc.) |
| Date fields accessible? | ✓ (data.0.0.order_date, data.0.0.created_at) |

## 10. CACHE INVALIDATION

| Check | Result |
|-------|--------|
| `st.cache_data` used for `load_data()`, `load_customers()`, `load_contracts()`? | ✓ (ttl=30s in `core/database.py`) |
| Cache cleared after import? | ✓ (`st.cache_data.clear()` added in `views/dashboard.py` line ~455) |
| Session state refreshed after import? | ✓ (`st.session_state.db_shipments = load_data()`) |
| R3 performance preserved? | ✓ (cache only cleared after import, not disabled) |

## 11. CURRENT-MONTH VISIBILITY (FIXED)

| Filter | Before Fix | After Fix |
|--------|-----------|-----------|
| "Tháng này" (using order_date) | 6/14 visible | **14/14 visible** ✓ |
| "Tất cả" | 14/14 visible | 14/14 visible ✓ |

**Fix applied in `core/utils.py`:** `get_shipment_business_date()` now checks `data['0.0']['order_date']` first, then falls back to `data['0.0']['created_at']`, then top-level `created_at`.

## 12. UNFILTERED VISIBILITY

| Check | Result |
|-------|--------|
| "Tất cả" filter shows all 14 orders? | ✓ |
| No orders lost during import? | ✓ (14 orders parsed, 14 orders written) |

## 13. DUPLICATE SAFETY

| Check | Result |
|-------|--------|
| Re-importing same file → no duplicate orders? | ✓ (validate_groups checks existing IDs; upsert prevents duplicates) |
| Existing orders with same Mã ĐH → merged, not overwritten? | ✓ (details appended, financial data preserved) |

## 14. FINANCE SAFETY

| Check | Result |
|-------|--------|
| Import does NOT overwrite existing financial data? | ✓ (merge logic only appends to data.3.4.details) |
| No financial mutation during preview? | ✓ (validation is read-only) |
| Finance oracle tests pass? | ✓ (test_dashboard_financial_write_oracle.py) |

## 15. REGRESSION

| Check | Result |
|-------|--------|
| Full test suite | **269 passed / 28 skipped / 0 failed** (was 257 before fix) |
| New incident regression tests | 8 tests in `TestLg05IncidentRegression` — all pass |
| New date-priority tests | 4 tests in `test_utils.py` — all pass |
| Synthetic fixture test | 3 orders, 7 service lines, all visible under "Tháng này" ✓ |
| LG05-specific tests | 33 tests — all pass |

## 16. PRODUCTION DATA MUTATION

| Check | Result |
|-------|--------|
| Production DB (port 8501) modified during debugging? | **NO** — all testing done in sandbox |
| Owner's real Excel file committed to Git? | **NO** — only synthetic fixture committed |
| customers count unchanged? | ✓ (362) |
| shipments count unchanged? | ✓ (78) |

## 17. FIX SHA

| Item | Value |
|------|-------|
| Incident fix commit | `59d77ef` |
| State update commit | `9629f33` |
| Branch HEAD | `9629f33` |
| Remote branch | `origin/log-lg05-excel-round-trip-gnt` |
| PR #4 | Draft, not merged |

## 18. OWNER TEST STEPS

1. Pull the branch: `git pull origin log-lg05-excel-round-trip-gnt`
2. Run the app: `streamlit run web_app.py`
3. Navigate to Dashboard → "NHẬP TỪ GETFLY"
4. Upload `danhsachdonhang-.xlsx`
5. Verify preview shows 14 orders, 39 service lines
6. Click "✅ XÁC NHẬN IMPORT"
7. Verify result display shows: "ĐÃ ĐỌC FILE: 14 đơn, 39 dòng dịch vụ"
8. Click "🔍 [XEM CÁC LÔ VỪA NHẬP]" → filter switches to "Tất cả"
9. Verify all 14 imported orders appear in the list
10. Switch filter to "Tháng này" → verify all 14 orders still visible (they all have order_date in Aug 2026)

---

## FILES CHANGED

| File | Change |
|------|--------|
| `core/utils.py` | `get_shipment_business_date()` prefers `order_date` over `created_at` |
| `views/dashboard.py` | Cache invalidation + improved import result display + "Xem các lô vừa nhập" button |
| `tests/fixtures/build_synthetic_getfly.py` | New — builds synthetic GETFLY fixture with malformed styles.xml |
| `tests/fixtures/synthetic_getfly.xlsx` | New — synthetic test fixture (3 orders, 7 service lines) |
| `tests/test_utils.py` | 4 new tests for order_date priority |
| `tests/test_lg05_excel_roundtrip_gnt.py` | 8 incident regression tests |
| `docs/goals/LOG-LG05/incident_root_cause.md` | New — root cause documentation |
| `docs/goals/LOG-LG05/state.json` | Updated with fix SHA and test counts |
