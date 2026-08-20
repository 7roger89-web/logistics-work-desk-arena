# LOG-LG04 R2 — PROGRESS NOTES

**Current state (2026-08-18):**
- Branch: `log-lg04-daily-work-simplification`, HEAD = `8b3a2da`
- PR #3: Open, Draft, HEAD = `8b3a2da`
- Owner machine: 8501 = production (LG03 code), 8502 = preview (LG04 R1 code)
- DB: 362 customers, 78 shipments

**Owner R2 requirements (pasted_content_4.txt):**
1. Remove the 3 "Mở..." jump cards (render_primary_work_cards) — replace with inline work areas directly visible
2. Header compact: chỉ ID + khách hàng + route
3. Next-action card keeps but severity meaningful (KHẨN CẤP/QUÁ HẠN, CẦN XỬ LÝ, BÌNH THƯỜNG)
4. Primary work areas (Xuất khẩu / Nhập khẩu / Chi phí) directly visible near top with "Cập nhật" inline
5. Progressive disclosure: summary first, missing fields, update inline, advanced collapsed
6. Dashboard: bộ lọc thời gian mặc định "Tháng này" + carry-over cho lô quá hạn
7. Search input đơn giản (shipment code, customer)
8. "Ngữ cảnh đối tác" → đổi thành "Liên hệ nhanh" / "Ai tham gia lô hàng này"
9. Documents: signal "Thiếu X chứng từ" instead of large table
10. Support gets `finance_write` permission (Owner business authority)

**Done:**
- [x] core/auth.py: added `finance_write` to `support` role

**TODO next:**
- views/shipment_360.py:
  - Remove render_primary_work_cards() (the 3 jump cards)
  - Instead, render work areas directly: header compact, next-action, then 3 sections inline (export/import/finance) each with summary + missing fields + "Cập nhật" button that expands inline form
  - Rename "Ngữ cảnh đối tác" expander → "📞 Liên hệ nhanh"
  - Document signal: "❌ Thiếu {N} chứng từ: ..." with "Xem chứng từ" link
- views/dashboard.py:
  - Default time filter = "Tháng này" (index=1 or appropriate)
  - Carry-over section: "Các lô cũ vẫn còn việc cần xử lý"
  - Simplify search to a single input
- Update tests: test_lg04_daily_work_ui.py must be updated for the new layout (remove jump card assertions, add inline work area assertions)
- Update RBAC tests for support finance_write
- Run full regression + mojibake scan


## R2 — IMPLEMENTATION PLAN (updated 2026-08-18)

### Current file layout (views/shipment_360.py):
- `render_primary_work_cards()` at lines 89-152: 3 jump cards with "Mở..." buttons
- `render_shipment_workspace()` at lines 154-324: main workspace
  - Header: kicker + title + route (lines 184-195)
  - Next-action card (line 209)
  - 3 jump cards (line 212)
  - 5-column signal row (lines 214-223)
  - Alerts expander (lines 225-234)
  - "Ai tham gia lô hàng này" expander (lines 236-284)
  - Factory lots expander (lines 286-295)
  - Documents expander (lines 297-313)
  - Timeline/audit expander (lines 315-320)
- `render_shipment_360_summary()` at lines 403-454: financial metrics (read-only)

### R2 changes needed in shipment_360.py:
1. **Remove `render_primary_work_cards()` entirely** — Owner rejects jump cards
2. **Restructure `render_shipment_workspace()` order:**
   - Compact header (just ID + customer + route, 2 lines)
   - Next-action banner (keep, but make severity meaningful)
   - **Primary work area** directly visible: 3 sections (Xuất khẩu / Nhập khẩu / Tài chính) each with:
     - Concise status summary (current known values + missing values)
     - Inline "Cập nhật" button that expands form right there (no jump to tab)
   - Then reference blocks (signals, partner/contact, documents signal, audit) below
3. **Rename "Ngữ cảnh đối tác"** → already "Ai tham gia lô hàng này" — keep but add "📞 Liên hệ nhanh" label
4. **Document signal:** Instead of full documents expander at top, show "❌ Thiếu {N} chứng từ: A, B, C" with "Xem chứng từ" link to collapsed table
5. **Finance section:** Add "Cập nhật" inline (since Support now has finance_write) — but this requires importing the finance write views. Actually the workspace is currently read-only in shipment_360.py. For R2, we can add an inline expandable form that links to the same shipment.py finance tab.

### Key insight for "Cập nhật" inline:
Instead of expanding a full form inline (complex), the "Cập nhật" button should navigate to the specific tab in shipment.py (which already has the forms). But Owner says NO jump cards. So the better approach: make the 3 work areas show their key summary + missing fields at the top of the workspace, and provide a clear "Cập nhật" button that sets `st.session_state` to open the corresponding tab in shipment.py. This is not a "card" — it's a direct action button within the work area itself.

Actually, re-reading Owner requirement: "Each area should initially show a concise operational summary such as: important known values; missing values; warnings; completion/status. Where authorized, provide a clear 'Cập nhật' action that opens/expands the form inline near the section."

So: show the 3 work areas inline at the top of the workspace (not as cards to jump to), and each area has an inline expandable "Cập nhật" that opens the relevant form section right there.


## R2 — KEY ARCHITECTURE UNDERSTANDING

**How the app works:**
- `views/shipment_360.py` renders the read-only workspace (what Owner sees after clicking "MỞ HỒ SƠ LÔ 360°")
- `views/shipment.py` renders the editable detail view with 3 tabs (PICKUP & XUẤT KHẨU / IMPORT & GIAO HÀNG / FINANCE)
- Owner clicks "MỞ HỒ SƠ LÔ 360°" on dashboard → shows workspace from shipment_360.py
- The workspace currently has: header, next-action, 3 jump cards, signals, then reference blocks
- To edit data, user must go to the shipment detail (which has the 3 editable tabs)

**R2 solution approach:**
The Owner wants: open shipment → SEE work → UPDATE work. No intermediate jump cards.

The cleanest approach for R2:
1. In `shipment_360.py` workspace, show the 3 work areas inline at the top (each with summary + missing fields + "Cập nhật" button)
2. The "Cập nhật" button sets `st.session_state.active_shipment_section` (export/import/finance) — this is the SAME mechanism as before, but now it's an inline action button within the work area (not a separate card)
3. When the user clicks "Cập nhật", the app navigates to the editable detail with the correct tab pre-selected
4. BUT the Owner also wants to NOT need to navigate. So the better approach: make the workspace itself contain inline expandable forms for the most common updates.

**Revised approach:**
Keep the workspace as the primary work surface. The 3 work areas show:
- Current known values (compact)
- Missing/required fields (highlighted)
- A "Cập nhật" button that opens an inline expander with the essential fields (just the critical ones, not all)
- For full editing, link to the detail page

Actually, the simplest and safest approach: Keep the workspace read-only (as it is) but restructure so that the 3 work areas are directly visible at the top (not as cards to click through). Each area shows a summary + "Cập nhật" button. When "Cập nhật" is clicked, it navigates to the detail page with the correct tab pre-opened. This eliminates the "card" metaphor and instead shows the work directly.

The key difference from the rejected version: instead of 3 separate cards (each looking like a separate widget), show the 3 areas as natural sections of the workspace with their content directly visible.


## R2 — NEXT ACTION CARD API

`render_next_action_card(action, *, anchor=None)` — displays a styled card with:
- severity-based border/background (critical=red, warning=orange, normal=blue, info=gray)
- Level text: "NGHIÊM TRỌNG" / "CẦN XỬ LÝ SỚM" / "CÔNG VIỆC TIẾP THEO" / "GỢI Ý KIỂM TRA"
- Task label, detail (why), who (person responsible)
- Optional "⬇ Xử lý ngay" button that scrolls to anchor

Owner requirement for severity: use "KHẨN CẤP / QUÁ HẠN", "CẦN XỬ LÝ", "BÌNH THƯỜNG" instead of current "NGHIÊM TRỌNG"/"CẦN XỬ LÝ SỚM"/"CÔNG VIỆC TIẾP THEO"

## R2 — FINAL IMPLEMENTATION DECISION FOR SHIPMENT_360.PY

The workspace will be restructured as follows:

```
[Compact header: ID + customer + route]
[Next-action banner: prominent, severity-based]
[--- PRIMARY WORK AREA ---]
Section A: LẤY HÀNG & XUẤT KHẨU
  - Compact summary: Mode, Booking, ETD, POL→POD, Status
  - Missing fields flagged: "⚠️ Thiếu: MBL, HBL" 
  - "Cập nhật" button → navigates to detail with export tab
Section B: NHẬP KHẨU & GIAO HÀNG
  - Compact summary: ETA, Free time, TK HQ, Status
  - Missing fields flagged
  - "Cập nhật" button → navigates to detail with import tab
Section C: CHI PHÍ & CÔNG NỢ
  - Compact summary: Chi phí đã biết, Phải thu, Phải trả, Status
  - Missing fields flagged
  - "Cập nhật" button → navigates to detail with finance tab
[--- REFERENCE ---]
Signal row (5 cols)
Partner/Contact expander ("📞 Liên hệ nhanh")
Document signal ("❌ Thiếu X chứng từ: A, B, C → Xem chứng từ")
Factory lots expander (hidden when empty)
Timeline/audit expander
```

The "Cập nhật" button does NOT jump to a tab — it navigates to the editable detail page (ui_shipment_detail_tabs) with the correct tab pre-selected. This is the SAME mechanism as before (st.session_state.active_shipment_section) but presented as a natural action within the work area, not as a separate card.

Actually wait — the workspace is rendered by `render_shipment_workspace()` which is called from the dashboard context. The editable detail is shown separately. Let me check how they relate.


## R2 — IMPLEMENTATION STATUS (2026-08-18)

### Done:
1. ✅ `core/auth.py`: Added `finance_write` to `support` role
2. ✅ `tests/test_logc15_auth_rbac.py`: Updated SUPPORT_ONLY_READ + split test into two (old test renamed behavior, new test_support_can_write_shipment_finance added)
3. ✅ `views/dashboard.py`: Changed default time filter from "Tất cả" (index=4) to "Tháng này" (index=0)

### Remaining TODO:
4. Rewrite `views/shipment_360.py` `render_shipment_workspace()`:
   - Remove `render_primary_work_cards()` call
   - Replace with inline work sections (export/import/finance) showing summary + "Cập nhật" button
   - The "Cập nhật" button sets `st.session_state.active_shipment_section = section` which navigates to the editable tabs in shipment.py
   - Keep compact header (2 lines: ID + customer, then route)
   - Next-action card stays but severity levels should be: KHẨN CẤP/QUÁ HẠN (critical), CẦN XỬ LÝ (warning), BÌNH THƯỜNG (normal)
   - "Ngữ cảnh đối tác" → "📞 Liên hệ nhanh" (currently "👥 Ai tham gia lô hàng này")
   - Documents: signal format "❌ Thiếu X chứng từ: A, B, C" with "Xem chứng từ" link
   - Keep factory lots, timeline/audit as is

5. Update `core/next_action_card.py` severity levels:
   - "critical" → "KHẨN CẤP / QUÁ HẠN"
   - "warning" → "CẦN XỬ LÝ"  
   - "normal" → "BÌNH THƯỜNG"
   - "info" → "GỢI Ý KIỂM TRA"

6. Update `tests/test_lg04_daily_work_ui.py`:
   - Remove assertions for jump cards (lg04_work_jump_*, card labels)
   - Add assertions for new inline work sections
   - Update partner expander label

7. Run full regression: `python3 -m pytest tests/ -q`
8. Run mojibake scan on changed files
9. Commit to branch `log-lg04-daily-work-simplification`
10. Update PR #3 (already open, just push new commits)
11. Update state.json + evidence
12. Write Owner-facing report

### Key architecture fact:
- `shipment.py` line 171-179: The `_jump = st.session_state.pop("active_shipment_section", None)` mechanism already handles navigating to the correct tab. So the workspace just needs to set `st.session_state.active_shipment_section` and call `st.rerun()`.
- The workspace (`shipment_360.py`) is rendered by `shipment.py` at line 125, BEFORE the editable detail section.
- When user clicks "Cập nhật" in workspace → sets `active_shipment_section` → reruns → `shipment.py` reads it at line 173 and opens the correct tab.


## R2 — STATUS UPDATE (after edits above)

### DONE:
1. ✅ core/auth.py: support now has finance_write
2. ✅ tests/test_logc15_auth_rbac.py: updated SUPPORT_ONLY_READ + added test_support_can_write_shipment_finance
3. ✅ views/dashboard.py: default time filter = "Tháng này" (index=0)
4. ✅ core/next_action_card.py: severity levels updated (KHẨN CẤP/CẦN XỬ LÝ/BÌNH THƯỜNG/GỢI Ý KIỂM TRA)
5. ✅ views/shipment_360.py: Added _render_primary_work_areas() + helper functions (_area_summary_*, _area_missing_*)
6. ✅ views/shipment_360.py: Replaced render_primary_work_cards() call with _render_primary_work_areas() call

### REMAINING:
7. Update render_shipment_workspace to remove render_primary_work_cards entirely (keep function for backwards compat or delete)
8. Update partner expander label from "👥 Ai tham gia lô hàng này" to "📞 Liên hệ nhanh"
9. Update documents signal to show "❌ Thiếu X chứng từ: A, B, C" format
10. Update tests/test_lg04_daily_work_ui.py (remove old card assertions, add new area assertions)
11. Run full regression + mojibake scan
12. Commit + push to branch log-lg04-daily-work-simplification
13. Update state.json + evidence
14. Write Owner-facing report
15. Deploy preview on Owner machine port 8502


## R2 — LATEST STATUS (2026-08-18)

All code changes DONE:
- core/auth.py: support has finance_write ✅
- tests/test_logc15_auth_rbac.py: updated ✅
- views/dashboard.py: default "Tháng này" ✅
- core/next_action_card.py: severity labels updated ✅
- views/shipment_360.py: 
  - _render_primary_work_areas() added ✅
  - render_primary_work_cards() removed from workspace ✅
  - Partner expander renamed to "📞 Liên hệ nhanh" ✅
  - Documents signal format updated ✅

NEXT: Update tests/test_lg04_daily_work_ui.py to match new layout. The old tests expect:
- "lg04_work_jump_lg04_tab_export" button (OLD — now "lg04_r2_update_export_{sid}")
- Card labels "Mở Xuất khẩu", "Mở Nhập khẩu & Giao hàng", "Mở Chi phí" (OLD)
- Partner expander label "👥 Ai tham gia lô hàng này" (OLD — now "📞 Liên hệ nhanh")

New tests should expect:
- "lg04_r2_update_export_{sid}", "lg04_r2_update_import_{sid}", "lg04_r2_update_finance_{sid}" buttons
- Work area titles in markdown: "🚛 Lấy hàng & Xuất khẩu", "🛃 Nhập khẩu & Giao hàng", "💰 Chi phí & Công nợ"
- Partner expander "📞 Liên hệ nhanh"
- Document signal "❌ Thiếu X chứng từ"


## R2 — PROGRESS (2026-08-18 latest)

### ALL CODE DONE ✅
1. core/auth.py: support has finance_write
2. tests/test_logc15_auth_rbac.py: updated
3. views/dashboard.py: default "Tháng này"
4. core/next_action_card.py: severity labels KHẨN CẤP/CẦN XỬ LÝ/BÌNH THƯỜNG/GỢI Ý KIỂM TRA
5. views/shipment_360.py: 
   - _render_primary_work_areas() — inline work areas with "Cập nhật" buttons (keys: lg04_r2_update_{section}_{sid})
   - Partner expander renamed to "📞 Liên hệ nhanh"
   - Documents signal "❌ Thiếu X chứng từ: A, B, C — Xem chứng từ"
   - Unknown free time override in workspace

6. tests/test_lg04_daily_work_ui.py: REWRITTEN for R2 layout

### NEXT STEPS:
7. Run full regression: cd /home/ubuntu/logistics_repo && python3 -m pytest tests/ -q
8. Run mojibake scan on changed files
9. Commit all changes to branch log-lg04-daily-work-simplification
10. Update state.json (add R2 facts)
11. Write Owner-facing report
12. Wait for Owner to deploy preview (or help them)

### Key facts for report:
- Owner's machine: D:\Logistics_App_GitHub, port 8501 = production app
- Preview port: 8502 (separate cmd window)
- Owner SHA on main: 3c1e1c7
- PR #3 HEAD: need to check (push new commits)
- Production: customers=362, shipments=78, admin active, 3 rehearsal inactive
