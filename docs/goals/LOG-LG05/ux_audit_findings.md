# UX Audit Findings

## Phase 1: LOGIN

**OBSERVATION:** Page loads successfully. Markdown extraction shows login form with:
- Heading: "🔐 Đăng nhập"
- Fields: Tài khoản, Mật khẩu
- Password visibility toggle (visibility icon)
- Button: "Đăng nhập"
- Sidebar navigation present

The browser screenshot rendering is blank (Streamlit viewer limitation), but the app IS functional. Content is visible via markdown extraction.

**FINDING UX-001** (severity: P3)
- Screen: Login
- Category: Visual Polish / Information Density
- Observed: Login form uses st.form with 2 input fields (Tài khoản, Mật khẩu) and 1 button (Đăng nhập). Compact layout confirmed via markdown extraction.
- Expected: Compact centered login form — PASS
- Score: 2 (PASS)

**FINDING UX-002** (severity: P3)
- Screen: Login
- Category: INPUT FIELD / TOOLTIP
- Observed: Tài khoản field has hint text showing in placeholder (visible in screenshot: empty input with hint). Mật khẩu field similarly has hint. Password field shows visibility toggle button on right side.
- Expected: Password field should have show/hide toggle — PASS
- Score: 2 (PASS)

**FINDING UX-003** (severity: P2)
- Screen: Login
- Category: VISUAL POLISH
- Observed: Login form is NOT centered — it appears left-aligned with the form fields spanning most of the width. The "Đăng nhập" button spans the full form width. There's a floating empty input field above the form (likely from a previous session state or a stray element).
- Expected: Login should be compact and centered on the page.
- Evidence: Screenshot shows form starts near left edge, not centered.
- Score: 1 (PARTIAL)

**FINDING UX-004** (severity: P3)
- Screen: Login
- Category: RESPONSIVENESS
- Observed: At 1024px width, the login form spans nearly the full width. This may be acceptable for desktop but could be improved.
- Expected: Compact centered layout regardless of width.
- Score: 1 (PARTIAL)

**FINDING UX-005** (severity: P3)
- Screen: Login
- Category: FEEDBACK / LOADING
- Observed: After clicking Đăng nhập, shows "Đang đồng bộ dữ liệu hệ thống..." while processing. Takes ~15s to load dashboard. No spinner/progress indicator.
- Expected: Show a visible loading spinner during the sync process.
- Score: 1 (PARTIAL)

## Phase 2: DASHBOARD

**FINDING UX-006** (severity: P2)
- Screen: Dashboard (Phòng điều khiển lô hàng)
- Category: TABLE / FILTERING ITEMS
- Observed: Dashboard shows "13/13 lô" but each shipment row is a HUGE expandable card taking ~300px height with full detail (Khách, Sale, Nhà máy, Chứng từ, Đại lý, Vận hành, Free time, Tài chính, ETA, "Vì sao ra số này?" collapsible, 360° button, Xử lý button). Only 4-5 cards visible at once on 1024px screen.
- Expected: Compact table rows (~40-50px) with key info, expandable for details.
- Evidence: Screenshot at 1024px shows only ~2 shipment cards in viewport
- Score: 1 (PARTIAL)

**FINDING UX-007** (severity: P2)
- Screen: Dashboard
- Category: INFORMATION DENSITY
- Observed: "🔴 13 lô cần xử lý" alert box + each card shows "🟠 Việc tiếp theo: Tài chính UNKNOWN" — redundant warning repetition. The sidebar has 19 navigation items.
- Expected: Cleaner hierarchy, less visual noise.
- Score: 1 (PARTIAL)

**FINDING UX-008** (severity: P1)
- Screen: Dashboard
- Category: TABLE READABILITY
- Observed: "Vì sao ra số này?" collapsible section shows 7 bullet points of UNKNOWN status for EVERY shipment card. This creates massive vertical scrolling just to see the shipment list.
- Expected: Hide UNKNOWN details by default or show a compact summary.
- Score: 0 (FAIL)

**FINDING UX-009** (severity: P2)
- Screen: Dashboard
- Category: FILTERING ITEMS
- Observed: Filter section has: Search bar + Thời gian dropdown + Trạng thái dropdown + Khách hàng + Sale + Vận hành + Lọc nâng cao + Cảnh báo + Tài chính + 2 checkboxes. Total 10+ filter controls above the table.
- Expected: Consolidate filters, use progressive disclosure more aggressively.
- Score: 1 (PARTIAL)

**FINDING UX-010** (severity: P3)
- Screen: Dashboard sidebar
- Category: NAVIGATION
- Observed: Sidebar has 19 navigation items across 5 categories. Very long, requires scrolling.
- Expected: Compact sidebar or collapsible sections.
- Score: 1 (PARTIAL)

**FINDING UX-011** (severity: P3)
- Screen: Dashboard
- Category: BUTTON LABELING
- Observed: The button label changed from "Xử lý" to "Mở thùng nhập liệu" on the first card. Inconsistent button labels across cards.
- Expected: Consistent button labels (either all "Xử lý" or all "Mở thùng nhập liệu").
- Score: 1 (PARTIAL)

## Phase 3: XỬ LÝ LÔ / EDITABLE FORM / TABS

**FINDING UX-012** (severity: P3)
- Screen: XỬ LÝ LÔ (editable form)
- Category: FLOW / NAVIGATION
- Observed: Clicking "Mở thùng nhập liệu" on first card (LS - B&G GREEN) opens the editable form INLINE within the dashboard card. Shows: Mã Lô=LS, Ngày tạo=2026/07/29, Khách hàng=CONG TY CO PHAN B&G GREEN, Trang thai=Chua xu ly, Hop dong lien ket=--Chua lien ket--, plus 3 tabs at bottom.
- Expected: Direct editable form — PASS (no intermediate summary screen)
- Score: 2 (PASS)

**FINDING UX-013** (severity: P3)
- Screen: XỬ LÝ LÔ
- Category: TABS
- Observed: Three tabs visible: 🚛 PICKUP & XUẤT KHẨU (default/active), 🛃 IMPORT & GIAO HÀNG, 💰 FINANCE (CÔNG NỢ)
- Expected: Default to first operational tab (PICKUP & XUẤT KHẨU), not Finance — PASS
- Score: 2 (PASS)

**FINDING UX-014** (severity: P1)
- Screen: XỬ LÝ LÔ
- Category: BUTTON LABELING
- Observed: Buttons are 💾 LƯU (save), 🗑️ XÓA (delete), ❌ (close/cancel). The "XÓA" button is DANGEROUS — it's next to the save button with no confirmation dialog. One accidental click could delete a shipment.
- Expected: Delete should require confirmation dialog.
- Score: 0 (FAIL) — HIGH RISK

**FINDING UX-015** (severity: P2)
- Screen: XỬ LÝ LÔ
- Category: FORM LAYOUT
- Observed: The editable form is INLINE (within the dashboard card), not a separate page/modal. The form has many fields (Mode, Incoterm, Booking No, Carrier, MBL, HBL, Vessel, ETD, POL, POD, Số Cont/Xe, Số Lượng/GW) but at 1024px width they appear cramped. The "Lịch sử thay đổi" collapsible shows "Chưa có audit log cho lô này."
- Expected: Better spacing for inline form fields.
- Score: 1 (PARTIAL)

**FINDING UX-016** (severity: P3)
- Screen: XỬ LÝ LÔ
- Category: DATE INPUT
- Observed: Date inputs show "Press the down arrow key to interact with the calendar" — the date picker requires keyboard navigation, which is not obvious for non-technical users.
- Expected: Clickable calendar icon or simpler date input.
- Score: 1 (PARTIAL)

**FINDING UX-017** (severity: P3)
- Screen: XỬ LÝ LÔ → IMPORT & GIAO HÀNG tab
- Category: TAB CONTENT / INFORMATION ARCHITECTURE
- Observed: The IMPORT & GIAO HÀNG tab contains: Nhập khẩu section (ETA, Free Time, Số TK HQ), GNT section (Người nộp thuế, Mã số thuế, Địa chỉ, Mã cơ quan hải quan, KBNN, Cơ quan thu, Loại tài khoản, Số TK/QĐ, Nội dung khoản nộp table), Giao hàng section (Xe giao, Tài xế/SĐT, Ngày giao, SĐT Nhận, Đ/C Giao), Ủy thác & Hợp đồng section, COPY NHANH box. Very long form — requires significant scrolling.
- Expected: Grouped sections with better visual separation.
- Score: 1 (PARTIAL)

**FINDING UX-018** (severity: P3)
- Screen: XỬ LÝ LÔ → IMPORT & GIAO HÀNG
- Category: COPY NHANH FEATURE
- Observed: COPY NHANH box shows a text block with shipment info (LÔ, KH, MBL, HBL, ETD, ETA, Cont, TK HQ, Xe, Đ/C, LH). Useful feature.
- Expected: Good utility feature — PASS
- Score: 2 (PASS)

**FINDING UX-019** (severity: P3)
- Screen: XỬ LÝ LÔ → IMPORT & GIAO HÀNG
- Category: GNT SECTION
- Observed: "🧾 GIẤY NỘP THUẾ (GNT) — C1-02/NS" section is visible with "Điền thông tin để xuất file Excel GNT" and "📥 Xuất Excel GNT" button. Correctly placed in IMPORT & GIAO HÀNG tab as per LG04 feedback.
- Expected: GNT in correct tab — PASS
- Score: 2 (PASS)

## Phase 4: FINANCE (CÔNG NỢ) TAB

**FINDING UX-020** (severity: P3)
- Screen: XỬ LÝ LÔ → FINANCE (CÔNG NỢ) tab
- Category: FINANCE TABLE / DATA ENTRY
- Observed: Finance tab has: 1. Dịch Vụ & Doanh Thu table (columns: #, Tên Dịch vụ, SL, Giá Vốn, Giá Bán, VAT %, Thành tiền, 🗑), 2. Chi Hoa Hồng section, 3. Lịch sử Thu tiền section, BẢNG KÊ TÀI CHÍNH summary (PHẢI THU, CHI PHÍ, HOA HỒNG, LỢI NHUẬN, CÔNG NỢ), Xuất File Excel button.
- Expected: Comprehensive finance view — PASS
- Score: 2 (PASS)

**FINDING UX-021** (severity: P2)
- Screen: XỬ LÝ LÔ → FINANCE
- Category: HIGH-RISK DATA ENTRY
- Observed: The service line table has input fields directly editable (Tên Dịch vụ=0, SL=1, Giá Vốn=0, Giá Bán=0, VAT=0). No validation or confirmation before save. The 🗑 button deletes a row immediately.
- Expected: Validation warnings for zero/null financial fields before save.
- Score: 1 (PARTIAL)

**FINDING UX-022** (severity: P3)
- Screen: XỬ LÝ LÔ → FINANCE
- Category: GROSS-UP CALCULATOR
- Observed: "🧮 TÍNH HOA HỒNG (GROSS-UP)" section with formula Gross = Net / (1 - %Phí). Fields: Net, Phí(%), Gross result, button "💾 Áp dụng vào Chi phí Hoa hồng".
- Expected: Good utility feature — PASS
- Score: 2 (PASS)

**FINDING UX-023** (severity: P3)
- Screen: XỬ LÝ LÔ → FINANCE
- Category: PAYMENT HISTORY
- Observed: "➕ Nhập thanh toán mới" section with Ngày, Số tiền, Nội dung, Lưu thanh toán button. Simple and functional.
- Expected: Good utility — PASS
- Score: 2 (PASS)

## Phase 5: GETFLY IMPORT FLOW

**FINDING UX-024** (severity: P3)
- Screen: Dashboard
- Category: GETFLY IMPORT UI
- Observed: "📤 NHẬP TỪ GETFLY" and "📥 XUẤT CHO GETFLY" buttons are prominently displayed at the top of the dashboard, inside a yellow-bordered box. Clear and visible.
- Expected: Easy to find — PASS
- Score: 2 (PASS)

**FINDING UX-025** (severity: P2)
- Screen: Dashboard
- Category: INLINE FORM CLOSE BEHAVIOR
- Observed: Clicking ❌ (close) on the inline form triggers "Đang đồng bộ dữ liệu hệ thống..." and shows a loading spinner. The form appears to be closing but the loading indicator is confusing — it suggests data is being saved when the user only wanted to cancel.
- Expected: Closing should be instant, no "synchronizing" message for a cancel action.
- Score: 0 (FAIL) — The page remains stuck in "Đang đồng bộ dữ liệu hệ thống..." loading state, blocking further interaction. This is a significant UX issue.

**FINDING UX-026** (severity: P1)
- Screen: Dashboard
- Category: LOADING STATE
- Observed: After clicking ❌ to close the inline form, the page enters "Đang đồng bộ dữ liệu hệ thống..." loading state and REMAINS in this state indefinitely. All content appears grayed out/faded. The user cannot interact with anything until the page reloads.
- Expected: Cancel/close should be instant; loading should resolve within seconds.
- Score: 0 (FAIL) — HIGH PRIORITY

## LOGIN RE-ENTRY (for GETFLY import test)

**FINDING UX-027** (severity: P3)
- Screen: LOGIN
- Category: LAYOUT
- Observed: Login form is compact and centered with a dark blue border. Fields: Tài khoản, Mật khẩu, visibility toggle, Đăng nhập button. Clean and simple.
- Expected: Compact centered login — PASS (matches LG04 requirement)
- Score: 2 (PASS)

**FINDING UX-028** (severity: P1)
- Screen: LOGIN → DASHBOARD
- Category: LOGIN PERFORMANCE
- Observed: After clicking Đăng nhập, the page shows "Đang đồng bộ dữ liệu hệ thống..." and takes ~60 seconds to complete. The user is blocked from interacting during this entire period.
- Expected: Login should complete within 5 seconds.
- Score: 0 (FAIL) — Login takes too long (60s+)

## GETFLY IMPORT EXPANSION

**FINDING UX-029** (severity: P3)
- Screen: Dashboard → NHẬP TỪ GETFLY
- Category: IMPORT UI
- Observed: Clicking NHẬP TỪ GETFLY expands a clean section with: "Tải file Excel định dạng 52 cột (Sheet1, A:AZ). Preview trước khi import." + file upload area + Upload button. Clear instructions.
- Expected: Clear upload interface — PASS
- Score: 2 (PASS)

## Phase 6: CUSTOMERS PAGE

**FINDING UX-030** (severity: P3)
- Screen: Khách Hàng
- Category: OVERALL LAYOUT
- Observed: Clean page with "QUẢN LÝ KHÁCH HÀNG" title, subtitle, import section (collapsed), add new customer section (collapsed), data table showing 362 customers with Mã KH, Địa chỉ, Người liên hệ, Email, Tên Khách Hàng. Table has column visibility toggle, CSV download, search, fullscreen buttons. "💾 LƯU THAY ĐỔI KHÁCH HÀNG" button below table. Archive section at bottom.
- Expected: Functional customer management — PASS
- Score: 2 (PASS)

**FINDING UX-031** (severity: P3)
- Screen: Khách Hàng
- Category: IMPORT PROTECTION
- Observed: Import section clearly states: "Hệ thống sẽ đọc cột Mã KH để nhận diện. Nếu Mã KH đã tồn tại, hệ thống sẽ Bỏ qua (không ghi đè) để bảo vệ dữ liệu cũ." — Good data protection messaging.
- Expected: Clear data safety — PASS
- Score: 2 (PASS)
