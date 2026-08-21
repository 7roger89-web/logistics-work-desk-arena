# LOG-LG05 Context Notes

## Task
LOG-LG05 — Excel Round-Trip & GNT Generation
- Branch: log-lg05-excel-round-trip-gnt (created from log-lg04 branch)
- Contract file: /home/ubuntu/upload/pasted_content_2.txt (529 lines)

## Owner files received
- /home/ubuntu/upload/danhsachdonhang-.xlsx — compatibility reference (52 columns, Sheet1)
- /home/ubuntu/upload/Mau-so-C1-02-NS.docx — GNT template reference

## Key requirements from contract (pasted_content_2.txt)
1. RECOVER: baseline LG04 (production SHA 3c1e1c7 on main, current candidate 56c474d)
2. 52-column compatibility: Sheet1, A:AZ, exact header spelling/order, multi-row service structure
3. Import preview: UPLOAD→PARSE→GROUP→VALIDATE→PREVIEW→CONFIRM→WRITE
4. Dedup: UNKNOWN!=ZERO, MISSING!=SAFE_TO_GUESS, AMBIGUOUS!=RESOLVED
5. Export: "XUẤT DANH SÁCH ĐƠN HÀNG" preserves 52-col contract
6. Round-trip test required
7. GNT data model: customsDeclarationNumber, customsDeclarationDate, importDutyAmount, importVatAmount
8. GNT button: "TẠO GIẤY NỘP THUẾ (GNT)" in IMPORT & GIAO HÀNG tab, only when prerequisites met
9. GNT output: GNT_<shipment-code>_<declaration-number>.xlsx, 2 sheets (NHẬP THÔNG TIN + GIẤY NỘP THUẾ)
10. Auto-fill from Logistics: declaration number/date, duty/VAT amounts, taxpayer name/tax code/address, shipment ref
11. Do NOT guess: bank/KBNN, account, collecting authority, chapter code, sub-item code, budget code
12. Tax table: 2+ rows (Thuế nhập khẩu + Thuế GTGT hàng nhập khẩu), total in words
13. Taxpayer vs payer-on-behalf: use legally responsible entity; if ambiguous, leave unresolved
14. C1-02/NS legal template check: verify current official structure before release
15. GNT editability: editable cells distinguishable, print-friendly
16. Security: DO NOT commit Owner's real Excel/customer data into Git
17. Tests: 52-col export, grouping, dedup, conflict, UNKNOWN vs ZERO, GNT prereqs, etc.
18. Terminal: READY_FOR_OWNER_LG05_RELEASE_GATE (both workstreams must pass)

## Technical state
- Repo: /home/ubuntu/logistics_repo
- Branch: log-lg05-excel-round-trip-gnt
- DB: MongoDB Atlas (cluster0.qvjh5ji), logistics_db, shipments=78, customers=362
- Streamlit on port 8501 (production), 8502 (preview on Owner's machine)
- Owner machine: D:\Logistics_App_GitHub
- Login: admin / [REDACTED-ADMIN-PW]

## Excel file issue
- openpyxl cannot read danhsachdonhang-.xlsx (invalid stylesheet XML)
- Need to: install python-calamine, or fix XML, or use alternative approach

## Shipment data structure (from DB inspection)
- shipments collection, each doc has "id" and "data" fields
- data structure: nested dict like {"0.0": {...}, "1.0": {...}, "2.0": {...}}
- "0.0" contains created_at and other master fields
- created_at dates range from 2025-12 to 2026-06

## Production shipment months
- 2025-12: 29, 2026-01: 23, 2026-02: 9, 2026-03: 2, 2026-04: 2, 2026-06: 8
- No August 2026 shipments in production

## Excel structure analysis (danhsachdonhang-.xlsx)
- Shape: (41, 52) — 1 header row + 40 data rows, 52 columns A:AZ
- Uses python-calamine engine (openpyxl fails on invalid stylesheet XML)
- 52 column headers:
  A: 'Ngày đặt hàng', B: 'Ngày tạo', C: 'Mã ĐH', D: 'Người thực hiện', E: 'Mã KH', F: 'Tên KH',
  G: 'Số ĐT', H: 'Email', I: 'Địa chỉ giao hàng', J: 'Người liên hệ', K: 'Điện thoại người liên hệ',
  L: 'Tỉnh/ TP', M: 'Quận/ Huyện', N: 'Nguồn khách hàng', O: 'Mã vận đơn', P: 'Trạng thái vận đơn',
  Q: 'Mã kho', R: 'Mã SP', S: 'Tên sản phẩm', T: 'Mô tả', U: 'Đơn vị', V: 'Nhóm sản phẩm',
  W: 'Số lượng', X: 'Giá vốn', Y: 'Giá bán', Z: 'CK(%)',
  BA: 'CK(Đ)', BB: 'VAT(%)', BC: 'Thành tiền', BD: 'Lợi nhuận SP', BE: 'Doanh số', BF: 'Chiết khấu (đ)',
  BG: 'Doanh thu sau CK', BH: 'Phí vận chuyển (đ)', BI: 'Phí lắp đặt (đ)', BJ: 'Doanh thu trước thuế',
  BK: 'VAT (đ)', BL: 'Doanh thu', BM: 'Đã thanh toán', BN: 'Còn lại', BO: 'Lợi nhuận', BP: 'Điều khoản đơn hàng',
  BQ: 'Hình thức thanh toán', BR: 'Hình thức thanh toán từng lần', BS: 'Ngày thanh toán', BT: 'Nguồn đơn hàng',
  BU: 'Người tạo', BV: 'Trạng thái', BW: 'Nhóm khách hàng', BX: 'REFUN', BY: 'HOA HỒNG KH GỬI', BZ: 'CẤP ĐỘ RỦI RO'
- Multi-row per shipment: master fields (A-N) only on first row of each shipment;
  subsequent rows (service lines) only have R:S (service code/name), T (description), U-V, W:X:Y etc.
- 14 unique shipments (by column C 'Mã ĐH'), 40 data rows total
- Payment history in column BS: comma-separated dates like '28/07/2026 00:00,12/08/2026 00:00'
- Payment methods in column BR: comma-separated like 'Chuyển khoản,Chuyển khoản'
- Currency: VND, some have VAT 8%, some 0%
- 'Thành tiền' = qty * unit price after discount
- 'Doanh thu' = total revenue incl VAT
- 'Đã thanh toán' + 'Còn lại' = 'Doanh thu'

## LEGAL TEMPLATE CHECK (researched 2026-08-19)
- Owner's DOCX references: Thông tư số 184/2015/TT-BTC (current as of 2026)
- Nghị định 347/2025/NĐ-CP (effective 01/01/2026) replaced Nghị định 11/2020/NĐ-CP for KBNN procedures
- Nghị định 347/2025 governs the administrative procedures BUT the C1-02/NS form itself is still referenced under Thông tư 184/2015/TT-BTC (customs duty payment procedures)
- As of August 2026: Thông tư 184/2015/TT-BTC is still the governing regulation for the C1-02/NS customs duty payment form
- The form structure in Owner's DOCX matches the current official template
- Key point: for customs duty (hải quan) payments, Thông tư 184/2015/TT-BTC still applies; Nghị định 347/2025/NĐ-CP is about general KBNN procedures
- DECISION: Use Thông tư 184/2015/TT-BTC as legal reference (matches Owner's DOCX and still current)

## C1-02/NS Template structure (Mau-so-C1-02-NS.docx)
Reference: Thông tư số 184/2015/TT-BTC

### Fields needed (from DOCX):
1. Header: "GIẤY NỘP TIỀN VÀO NGÂN SÁCH NHÀ NƯỚC" + Mẫu số: C1-02/NS (Theo Thông tư số 184/2015/TT-BTC)
2. Người nộp thuế + Mã số thuế
3. Địa chỉ (line 1) + Quận/Huyện + Tỉnh TP (line 2)
4. Người nộp thay + Địa chỉ (line 1) + Quận/Huyện + Tỉnh TP (line 2)
5. NH (KBNN) + trích TK số + hoặc thu tiền mặt + TK thu NSNN/Tạm thu/Hoàn thuế GTGT checkboxes
6. KBN (KBNN nơi thu) + Tỉnh tp
7. Mở tại NH ủy nhiệm thu
8. Checkbox: Nộp theo kết luận cơ quan có thẩm quyền (Kiểm toán NN/Thanh tra TC/Thanh tra CP/Cơ quan khác)
9. Tên cơ quan quản lý thu
10. Tổng số tiền ghi bằng chữ
11. Tax table (6 cols): STT | Số tờ khai/Số quyết định/Số thông báo | Kỳ thuế/Ngày tờ khai | Nội dung các khoản nộp NSNN | Số tiền | Mã tiểu mục | Mã chương
12. Tổng cộng row
13. KBNN section: Mã CQ thu, Nợ TK, Có TK
14. Signatures: Người nộp tiền, Kế toán trưởng, Thủ trưởng đơn vị, Thủ quỹ, Kế toán, Kế toán trưởng/Trưởng phòng kế toán

### For GNT auto-fill:
- Số tờ khai = customs declaration number
- Ngày tờ khai = customs declaration date
- Nội dung = "Thuế nhập khẩu" / "Thuế GTGT hàng nhập khẩu"
- Số tiền = import duty / import VAT amounts
- Mã tiểu mục / Mã chương = leave blank (DO NOT GUESS)
- Tổng = sum of both taxes
- Tổng bằng chữ = Vietnamese number-to-words conversion
- NH/KBNN = leave blank (DO NOT GUESS)
- Người nộp thuế = importer name (from shipment data)
- Mã số thuế = importer tax code (from shipment data)
- Địa chỉ = importer address (from shipment data)
- Người nộp thay = if logistics co pays on behalf

## EXISTING GNT IMPLEMENTATION (already in codebase)
Location: views/shipment.py lines 213-330, core/excel_gnt.py

### UI (views/shipment.py):
- In IMPORT & GIAO HÀNG tab, there's an expander "🖨️ Tạo Giấy Nộp Thuế (GNT)"
- Fields: người nộp, MST, địa chỉ, mã HQ, KBNN, cơ quan thu, loại TK (7111/3511), số TK/QĐ
- Tax table: st.data_editor with columns Nội dung, Mã NDKT, Số tiền
- Default rows: "Thuế Nhập khẩu" (1901) + "Thuế GTGT hàng NK" (1701)
- GNT data saved to d['2.4']['gnt'] dict
- Button: "📥 Xuất Excel GNT" → calls create_gnt_excel() → download
- Filename: GNT_{so_tk}.xlsx

### Excel generation (core/excel_gnt.py):
- Uses openpyxl with a template file from GNT_TEMPLATE_PATH
- Single sheet approach (loads template, fills in place)
- Functions: doc_so_thanh_chu_vi(n), find_row_by_text(), copy_style(), create_gnt_excel(data)
- Fills: header (nguoi_nop, mst, dia_chi, ten_kbnn, ten_cq_thu, ma_cq_thu)
- Checkbox: TK thu NSNN [x] or TK tạm thu [x]
- Tax rows: STT, so_tk, ngay_tk, nội dung, số tiền, mã NDKT
- Total: static value (not formula)
- Total in words: Vietnamese conversion

### What LG05 needs to change/add:
1. TWO-SHEET approach: Sheet1 "NHẬP THÔNG TIN" + Sheet2 "GIẤY NỘP THUẾ" (per contract)
2. Filename: GNT_<shipment-code>_<declaration-number>.xlsx (current is GNT_{so_tk}.xlsx)
3. Auto-fill from authoritative data (declaration number, date, duty amount, VAT amount)
4. Prerequisites check: declaration number, date, import duty, import VAT must be KNOWN
5. Do NOT guess: bank/KBNN, collecting authority, chapter/sub-item codes
6. Taxpayer vs payer-on-behalf logic
7. Editable cells distinguishable
8. Print-friendly

## EXISTING DATA STRUCTURE for GNT fields:
- d['2.4']['tk_no'] = tờ khai number (currently empty in production)
- d['2.4']['tk_date'] = tờ khai date (currently 'None' in production)
- d['2.4']['tax_lines'] = [] (exists but always empty in production)
- d['2.4']['gnt'] = {} (GNT saved data)
- d['3.4'] = finance section with details, payments, out, in, vat, profit, debt, paid
- Customer info: ship['client'], ship['customer'], customer tax_code/address from customers collection

## KEY GAP ANALYSIS:
- Production data does NOT have import duty/VAT amounts stored separately from revenue
- The existing GNT UI requires manual entry of tax amounts (data_editor)
- For LG05: need to add fields for importDutyAmount and importVatAmount to the data model
- These could go in d['2.4'] alongside tk_no/tk_date

## FINAL DATA MODEL ANALYSIS (Phase 2 complete)

### Existing fields in d['2.4'] (customs/import section):
- tk_no: 74/78 shipments (mostly empty string)
- tk_date: 38/78 (mostly 'None' string)
- phan_luong: 73
- customs_status: 52
- note_ops: 31
- tax_lines: 6 (always empty list [])
- ma_hq: 6 (always empty string)

### Existing fields in d['3.4'] (finance section):
- details: 78 (list of service lines)
- commission: 78
- payments: 78
- out: 76 (revenue)
- in: 76 (cost)
- out_net: 53
- output_vat: 53
- profit: 53
- paid: 53
- debt: 53
- currency: 53
- vat: 39
- agency: 5

### KEY FINDING: No importDutyAmount or importVatAmount fields exist yet!
- tax_lines exists but is always empty
- The existing GNT UI requires MANUAL entry of tax amounts via data_editor
- For LG05: MUST add fields:
  - d['2.4']['import_duty_amount'] (Thuế nhập khẩu)
  - d['2.4']['import_vat_amount'] (Thuế GTGT hàng NK)
  - These go in the IMPORT & GIAO HÀNG tab alongside tk_no

### GNT Prerequisites (per contract):
1. tk_no (declaration number) - exists in d['2.4']['tk_no']
2. tk_date (declaration date) - exists in d['2.4']['tk_date'] (needs UI input)
3. import_duty_amount - NEW FIELD NEEDED
4. import_vat_amount - NEW FIELD NEEDED

### Current GNT UI location:
- views/shipment.py lines 213-330 (inside IMPORT & GIAO HÀNG tab t2)
- Uses expander "🖨️ Tạo Giấy Nộp Thuế (GNT)"
- Saves to d['2.4']['gnt']

### Excel GNT generation:
- core/excel_gnt.py (create_gnt_excel) - uses GNT_MAU.xlsx template (NOT in repo)
- core/gnt_utils.py - amount_to_text_vi, get_treasury_info (uses MA_NGAN_SACH.xlsx)
- GNT_MAU.xlsx template file does NOT exist in repo (needs to be created or referenced)

### LG05 Architecture Decision:
- Do NOT use the existing single-template approach (requires GNT_MAU.xlsx which doesn't exist)
- Build a PURE openpyxl approach: generate workbook from scratch with 2 sheets
- Sheet 1: NHẬP THÔNG TIN (editable form, auto-filled values highlighted)
- Sheet 2: GIẤY NỘP THUẾ (C1-02/NS form layout, print-friendly)
- Filename: GNT_<shipment-code>_<declaration-number>.xlsx

## EXACT 52-COLUMN HEADERS (verified 2026-08-19)
A: 'Ngày đặt hàng', B: 'Ngày tạo', C: 'Mã ĐH', D: 'Người thực hiện',
E: 'Mã KH', F: 'Tên KH', G: 'Số ĐT', H: 'Email', I: 'Địa chỉ giao hàng',
J: 'Người liên hệ', K: 'Điện thoại người liên hệ', L: 'Tỉnh/ TP',
M: 'Quận/ Huyện', N: 'Nguồn khách hàng', O: 'Mã vận đơn',
P: 'Trạng thái vận đơn', Q: 'Mã kho', R: 'Mã SP', S: 'Tên sản phẩm',
T: 'Mô tả', U: 'Đơn vị', V: 'Nhóm sản phẩm', W: 'Số lượng',
X: 'Giá vốn', Y: 'Giá bán', Z: 'CK(%)', AA: 'CK(Đ)', AB: 'VAT(%)',
AC: 'Thành tiền', AD: 'Lợi nhuận SP', AE: 'Doanh số', AF: 'Chiết khấu (đ)',
AG: 'Doanh thu sau CK', AH: 'Phí vận chuyển (đ)', AI: 'Phí lắp đặt (đ)',
AJ: 'Doanh thu trước thuế', AK: 'VAT (đ)', AL: 'Doanh thu',
AM: 'Đã thanh toán', AN: 'Còn lại', AO: 'Lợi nhuận',
AP: 'Điều khoản đơn hàng', AQ: 'Hình thức thanh toán',
AR: 'Hình thức thanh toán từng lần', AS: 'Ngày thanh toán',
AT: 'Nguồn đơn hàng', AU: 'Người tạo', AV: 'Trạng thái',
AW: 'Nhóm khách hàng', AX: 'REFUN', AY: 'HOA HỒNG KH GỬI',
AZ: 'CẤP ĐỘ RỦI RO'

## GROUPING SEMANTICS (verified from data)
- Master fields: A-N, C, E, F, G, H, I, J, K, L, M, N (order/customer info)
- Service line fields: R:S (product code/name), T (description), U-V, W:AO (financial)
- A row is a "master row" if it has C (Mã ĐH) non-null
- A row is a "detail row" if it has R (Mã SP) but C is null → belongs to previous master row
- Payment history: column AR (Hình thức thanh toán từng lần) = comma-separated list
- Payment dates: column AS (Ngày thanh toán) = comma-separated list like '28/07/2026 00:00,12/08/2026 00:00'
- Payment amounts: need to derive from AM (Đã thanh toán) per detail row, or flatten

## MAPPING: Excel → Canonical (shipments collection)
Master fields → ship top-level + d['0.0']:
- C (Mã ĐH) → ship['id']
- F (Tên KH) → ship['customer'] / ship['client']
- B (Ngày tạo) → ship['created_at']
- AV (Trạng thái) → ship['status']
- D (Người thực hiện) → new field or note

Detail fields → d['3.4']['details'][] (service lines):
- R (Mã SP) → detail['code']
- S (Tên sản phẩm) → detail['name']
- T (Mô tả) → detail['note']
- U (Đơn vị) → new field
- V (Nhóm sản phẩm) → new field
- W (Số lượng) → detail['qty']
- X (Giá vốn) → detail['cost'] / detail['price_in']
- Y (Giá bán) → detail['price'] / detail['price_out']
- Z (CK(%)) → detail['discount_pct']
- AA (CK(Đ)) → detail['discount_amt']
- AB (VAT(%)) → detail['vat'] / detail['vat_line']
- AC (Thành tiền) → detail['line_total']
- AD (Lợi nhuận SP) → detail['profit']

Aggregate fields → d['3.4']:
- AE (Doanh số) → d['3.4']['out']
- AL (Doanh thu) → d['3.4']['in'] (reversed? need to check)
- AM (Đã thanh toán) → d['3.4']['paid']
- AN (Còn lại) → d['3.4']['debt']
- AO (Lợi nhuận) → d['3.4']['profit']

Payments → d['3.4']['payments'][]:
- From AR (Hình thức thanh toán từng lần) + AS (Ngày thanh toán) + AM (Đã thanh toán)

## BUILD PROGRESS (as of 2026-08-19, Phase 3)
- core/excel_roundtrip.py CREATED with:
  - HEADERS_52 list (exact, verified)
  - ImportRow, ImportGroup, ExportRow, ImportParseResult classes
  - parse_excel_bytes() → groups rows
  - group_rows() → groups into shipments
  - validate_groups() → classifies new/existing/conflict
  - shipment_to_export_rows() → canonical → export rows
  - export_to_excel_bytes() → openpyxl 52-col workbook
  - group_to_shipment_doc() → import group → canonical doc
  - safe_num() helper

## TODO (Phase 3 remaining):
1. Add import UI to views (dashboard or shipment page)
2. Add export button to dashboard
3. Phase 4: core/gnt_builder.py - 2-sheet workbook
4. Phase 4: Add import_duty_amount/import_vat_amount to UI
5. Phase 4: GNT button with prerequisites check
6. Phase 5: Tests (round-trip, dedup, GNT, 52-col)
7. Phase 6: QA + pilot
8. Phase 7: Report

## GNT Module Plan (core/gnt_builder.py):
- Function: build_gnt_workbook(data) → bytes
- Sheet 1 "NHẬP THÔNG TIN":
  - Label | Value | Notes
  - Auto-filled: TK number, TK date, importer name, tax code, address
  - Editable: duty amount, VAT amount (if known), bank info
  - Highlight auto-filled cells yellow
- Sheet 2 "GIẤY NỘP THUẾ":
  - C1-02/NS form layout (header, taxpayer info, tax table, total, signatures)
  - Tax table: Thuế nhập khẩu + Thuế GTGT hàng NK
  - Total in Vietnamese words
  - Print-friendly (page setup)
- Filename: GNT_{shipment_id}_{tk_no}.xlsx
- Prerequisites: tk_no + tk_date + (duty_amount > 0 OR vat_amount > 0)
