# LOG-LG05 — GETFLY Real-File Owner Acceptance Gate

**Date:** 2026-08-19
**Mode:** CONTINUE_EXISTING_LOG-LG05

---

## 1. RECONCILED GIT TRUTH

| Item | SHA |
|------|-----|
| **CURRENT_LOCAL_HEAD** | `da5bb22fdfe64dc9dfd226c06262197b5878e9a6` |
| **CURRENT_REMOTE_BRANCH_HEAD** | `da5bb22fdfe64dc9dfd226c06262197b5878e9a6` (matches local) |
| **CURRENT_PR4_HEAD** | `da5bb22fdfe64dc9dfd226c06262197b5878e9a6` (matches branch) |
| **CURRENT_MAIN_SHA** | `aa5cef48b56fa151df32868512273180834ebb72` |

**Commit after 9629f33:** Only 1 commit — `da5bb22` ("LG05: add final incident evidence report"). This explains the earlier report discrepancy (it was written before the report commit was pushed).

**ONE CURRENT CANDIDATE SHA:** `da5bb22fdfe64dc9dfd226c06262197b5878e9a6`

---

## 2. RECONCILED GETFLY ROW COUNTS

| Metric | Value | Definition |
|--------|-------|------------|
| **PHYSICAL_ROWS** | 40 | All non-header data rows in the Excel file |
| **HEADER_ROWS** | 1 | Row 1 with column names |
| **BUSINESS_DATA_ROWS** | 40 | Same as PHYSICAL_ROWS (no empty filler rows counted) |
| **MASTER_ORDER_ROWS** | 14 | Rows with non-empty "Mã ĐH" (col C) |
| **CONTINUATION_SERVICE_ROWS** | 25 | Rows with service data but no "Mã ĐH" |
| **TOTAL_SERVICE_ROWS** | 39 | 14 master rows (all have service) + 25 continuation rows |
| **EMPTY/MISC_ROWS** | 1 | Row 41: summary row ("Tổng cộng") — ignored by parser |
| **TOTAL/SUMMARY_ROWS** | 1 | Ignored during import |

**UI Terminology (confirmed correct):** "14 đơn, 39 dòng dịch vụ" — Owner's count is CORRECT.

---

## 3. REAL FILE — PREVIEW ONLY (NO PRODUCTION WRITE)

**PREVIEW RESULT:**

| Preview Field | Value |
|---------------|-------|
| **TỔNG ĐƠN TRONG FILE** | 14 |
| **LÔ MỚI** | 13 |
| **LÔ ĐÃ CÓ** | 1 |
| **LÔ KHÔNG THAY ĐỔI** | 0 |
| **LÔ SẼ ĐƯỢC CẬP NHẬT** | 1 |
| **XUNG ĐỘT** | 0 |
| **DÒNG DỊCH VỤ BỔ SUNG** | 39 |
| **CẢNH BÁO TÀI CHÍNH** | 0 (financial data never overwritten) |
| **UNKNOWN / INVALID VALUES** | 0 errors |

**VALIDATION:** is_valid=True, 0 errors, 1 warning (existing order will be merged)

---

## 4. DATE PROOF

**Field Mapping (verified on real file):**

| GETFLY Column | Canonical Field | Dashboard Filter |
|---------------|-----------------|------------------|
| "Ngày đặt hàng" (col A) | `data['0.0']['order_date']` | ✅ Primary (after fix) |
| "Ngày tạo" (col B) | `data['0.0']['created_at']` | Fallback only |

**Per-Order Date Proof (14/14):**

| Order | Ngày đặt hàng | Ngày tạo | Biz Date | Tháng này? |
|-------|---------------|----------|----------|------------|
| Lô.... | 25/08/2026 | 17/12/2025 | 2026-08-25 | ✓ |
| T8. LÔ GIƯỜNG + GHẾ + BÀN TRÀ | 20/08/2026 | 14/08/2026 | 2026-08-20 | ✓ |
| 108528866500 - BO MẠCH CAO ÁP | 17/08/2026 | 17/08/2026 | 2026-08-17 | ✓ |
| T8.2026 LÔ GIƯỜNG + GHẾ HOMELAND | 15/08/2026 | 29/07/2026 | 2026-08-15 | ✓ |
| LS | 15/08/2026 | 29/07/2026 | 2026-08-15 | ✓ |
| T7.2026 - LÔ ÔNG DẪN MỀM | 15/08/2026 | 15/07/2026 | 2026-08-15 | ✓ |
| LÔ CARBON - THAN HOẠT TÍNH | 15/08/2026 | 15/07/2026 | 2026-08-15 | ✓ |
| 108530180140 - LÔ NỘI THẤT BÀN GHẾ | 14/08/2026 | 17/08/2026 | 2026-08-14 | ✓ |
| 108528272310 - LÔ GHẾ NỘI THẤT INDO | 14/08/2026 | 17/08/2026 | 2026-08-14 | ✓ |
| 108528312100 - LÔ NỘI THẤT BÀN GHẾ | 13/08/2026 | 17/08/2026 | 2026-08-13 | ✓ |
| T7.2026 LÔ NHỰA TRAO ĐỔI ION | 10/08/2026 | 15/07/2026 | 2026-08-10 | ✓ |
| 108498852450 - LÔ BỘ TRỤC VÍT | 05/08/2026 | 06/11/2025 | 2026-08-05 | ✓ |
| 107772253960 - LÔ QUANG MINH HT350 | 04/08/2026 | 04/08/2026 | 2026-08-04 | ✓ |
| LÔ..... | 01/08/2026 | 22/07/2026 | 2026-08-01 | ✓ |

**RESULT: 14/14 = ✓ PASS** — All orders have order_date in August 2026 and will be visible under "Tháng này" filter.

---

## 5. IMPORT DELTA — PER ORDER CLASSIFICATION

| # | Order | Status | Details |
|---|-------|--------|---------|
| 1 | Lô.... | **NEW** | 1 service line |
| 2 | T8. LÔ GIƯỜNG + GHẾ + BÀN TRÀ HĐ 2307 | **NEW** | 3 service lines |
| 3 | 108528866500 - BO MẠCH CAO ÁP HCM | **NEW** | 1 service line |
| 4 | T8.2026 LÔ GIƯỜNG + GHẾ HOMELAND | **NEW** | 3 service lines |
| 5 | LS | **NEW** | 1 service line |
| 6 | T7.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE | **EXISTING_MERGE** | 1 service line (existing: 1, incoming: 1, result: 2) |
| 7 | LÔ CARBON - THAN HOẠT TÍNH | **NEW** | 1 service line |
| 8 | 108530180140 - LÔ NỘI THẤT BÀN GHẾ | **NEW** | 5 service lines |
| 9 | 108528272310 - LÔ GHẾ NỘI THẤT INDO | **NEW** | 5 service lines |
| 10 | 108528312100 - LÔ NỘI THẤT BÀN GHẾ | **NEW** | 5 service lines |
| 11 | T7.2026 LÔ NHỰA TRAO ĐỔI ION | **NEW** | 1 service line |
| 12 | 108498852450 - LÔ BỘ TRỤC VÍT | **NEW** | 5 service lines |
| 13 | 107772253960 - LÔ QUANG MINH HT350 | **NEW** | 5 service lines |
| 14 | LÔ..... | **NEW** | 2 service lines |

**EXISTING_MERGE Delta (Order #6):**
- Existing: 1 service line ("Phí dịch vụ khác", qty=1, cost=941,849,572)
- Incoming: 1 service line ("Phí dịch vụ khác", qty=1, cost=941,849,572)
- Result: 2 service lines (existing preserved + new appended)
- **Financial data: NOT overwritten** ✓

**CONFLICT:** 0 orders

---

## 6. FINANCE DELTA

| Check | Result |
|-------|--------|
| Existing financial data overwritten? | **NO** — merge only appends details |
| New financial data lost? | **NO** — all incoming data preserved |
| UNKNOWN values set to zero? | **NO** — UNKNOWN kept as UNKNOWN |
| Ambiguous values auto-resolved? | **NO** — flagged for Owner review |

**Dữ liệu tài chính bị ghi đè: 0** ✓

---

## 7. VISIBILITY ACCEPTANCE

| View | Expected | Result |
|------|----------|--------|
| **IN_DATABASE** (after import) | 14 new/updated IDs | Pending Owner confirmation |
| **IN_TẤT_CẢ** | 14/14 visible | ✓ (proven via date mapping) |
| **IN_THÁNG_NÀY** | 14/14 visible | ✓ (proven via date mapping — all order_dates in Aug 2026) |

**"XEM CÁC LÔ VỪA NHẬP" button:** Currently switches to "Tất cả" filter and highlights imported IDs via `st.session_state['lg05_imported_ids']`. Bounded fix applied — accurate label.

---

## 8. REGRESSION (at SHA da5bb22)

| Test Suite | Result |
|------------|--------|
| **Full regression** | 269 passed / 28 skipped / 0 failed |
| **RBAC** | 28 passed |
| **Finance oracle** | 1 passed |
| **GETFLY incident regression** | 8 passed |
| **Date-priority tests** | 10 passed (test_utils.py) |
| **Duplicate/re-import** | Covered in incident regression |
| **Cache invalidation** | Covered in incident regression |
| **Mojibake** | Pre-existing only (3 in core/database.py from LG04, not introduced by LG05) |
| **Secret scan** | No hardcoded secrets found |

---

## 9. OWNER ACTION REQUIRED

**Preview is CLEAN — no material conflicts.**

Owner must confirm import by running:
1. Pull branch: `git pull origin log-lg05-excel-round-trip-gnt`
2. Start app: `streamlit run web_app.py`
3. Navigate to Dashboard → "NHẬP TỪ GETFLY"
4. Upload `danhsachdonhang-.xlsx`
5. Review preview (shows 13 NEW, 1 EXISTING_MERGE, 0 CONFLICT)
6. Click "✅ XÁC NHẬN IMPORT"

---

## VERDICT

```
CURRENT CANDIDATE SHA: da5bb22fdfe64dc9dfd226c06262197b5878e9a6
GETFLY FILE COUNTS: 40 data rows, 1 header, 14 orders, 39 service rows, 1 summary (ignored)
IMPORT PREVIEW: 13 NEW, 1 EXISTING_MERGE, 0 CONFLICT
FINANCE DELTA: 0 overwritten
DATE MAPPING: order_date ✓ (all 14 in Aug 2026)
EXPECTED THÁNG NÀY VISIBILITY: 14/14 ✓
REGRESSION: 269 passed / 28 skipped / 0 failed
OWNER ACTION: Confirm import via UI
```

**Terminal: READY_FOR_OWNER_GETFLY_IMPORT_CONFIRMATION**
