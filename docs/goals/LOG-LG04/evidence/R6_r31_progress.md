# LOG-LG04 R3.1 Implementation Progress

## Current Truth (as of R3.1 start)
- Branch HEAD: f06b8fd (origin/log-lg04-daily-work-simplification)
- PR #3 HEAD: f06b8fd, draft=True, merged=False
- main HEAD: aa5cef4 (LG03 terminal RELEASED_VERIFIED)
- Production 8501: Owner's local app at 3c1e1c7 (LG03 production code) — untouched
- Preview 8502: Owner runs from FETCH_HEAD on the branch

## R3.1 Goal
"📝 XỬ LÝ LÔ" must open DAILY WORK SURFACE showing all 3 primary areas:
1. 🚛 Lấy hàng & Xuất khẩu
2. 🛃 Nhập khẩu & Giao hàng
3. 💰 Chi phí & Công nợ

NOT hard-coded to finance tab. Smart focus: if next-action reliably identifies relevant area, emphasize that one.

## Current Architecture Understanding

### Dashboard flow when "Xử lý" clicked:
- `st.session_state.active_shipment_id = sid`
- `st.session_state.dashboard_active_shipment_id = sid`
- `st.session_state.lg04_open_direct_work = True`
- `st.session_state.active_shipment_section = "finance"` ← THIS IS THE R3.1 BUG

### Dashboard render flow (views/dashboard.py ~line 536):
- `active_sid = st.session_state.get('dashboard_active_shipment_id')`
- If active_sid: renders `ui_shipment_detail_tabs(active_sid, ship_data)`
- This function is in views/shipment.py line 93

### ui_shipment_detail_tabs structure:
- 3 tabs: `st.tabs(["🚛 PICKUP & XUẤT KHẨU", "🛃 IMPORT & GIAO HÀNG", "💰 FINANCE (CÔNG NỢ)"], default=_tab_label)`
- `_jump = st.session_state.pop("active_shipment_section", None)`
- `_tab_index = {"export": 0, "import": 1, "finance": 2}.get(str(_jump))`
- If _tab_index is not None, opens that tab; otherwise first tab (export)

### The Problem:
Currently "Xử lý" sets `active_shipment_section = "finance"` → always opens FINANCE tab.
Owner wants: open a "daily work surface" showing ALL 3 areas, with smart focus.

### Solution Plan:
1. Change the dashboard button to NOT set active_shipment_section = "finance"
2. Instead set `active_shipment_section = "work_surface"` (new value)
3. In ui_shipment_detail_tabs, when active_shipment_section == "work_surface":
   - Show a compact summary of all 3 areas at the top
   - Each area shows: summary, missing info, "Cập nhật" button
   - "Cập nhật" sets active_shipment_section to the specific area and reruns
   - Smart focus: use next_action.code to determine which area to expand/highlight
   - If uncertain: show all 3 equally

4. The 3 primary areas already exist as `_render_primary_work_areas` in shipment_360.py
   - But that's read-only (no writers). Need to make the "Cập nhật" button open the editable tab.

5. Alternative simpler approach:
   - When active_shipment_section = "work_surface", show the 3 work area cards (like _render_primary_work_areas)
   - Each card has "Cập nhật" button that sets active_shipment_section to the specific area
   - Tab switching works via the existing mechanism

## Files to Modify:
- views/dashboard.py: change button handler to set active_shipment_section = "work_surface"
- views/shipment.py: in ui_shipment_detail_tabs, handle "work_surface" case

## next_action classification (for smart focus):
From shipment_360.py build_shipment_workspace_view:
- FREE_TIME_EXPIRING → import area
- Various codes map to export/import/finance
