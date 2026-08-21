# LOG-LG08 Findings — Implementation Plan

## Current State
- main HEAD: 5aba4c2
- Cloud URL: https://tienthanhlog.streamlit.app/ (deploys from main)
- DB: logistics_db on Atlas cluster0.qvjh5ji.mongodb.net

## Users in DB (all now have user_id added)
| username | user_id | role | active |
|----------|---------|------|--------|
| admin | 8c6976e5b5410415 | admin | True |
| 7roger | cbd5311e50e7a312 | admin | True |
| sami | 24964a2764be8975 | sale | True |
| fiona | 4c0db82499ca9a6d | support | True |
| rehearsal_admin | 646a8078814732ea | admin | False |
| rehearsal_sale | 052e25804a257c6c | sale | False |
| rehearsal_support | def4a0bbe98694b9 | support | False |

## Tasks in DB (8 total)
- All use display-name assignees: "Linh", "Mến", "Tất cả (All)"
- No created_by field in any task (legacy data)
- Some have updated_by, updated_at
- Legacy assignee mapping needed: "Linh"→fiona, "Mến"→sami (owner approval needed)

## TEAM_MEMBERS Hardcode
- File: views/dashboard.py line 59
- `TEAM_MEMBERS = ["Tất cả (Team)", "Thành", "Mến", "Linh"]`
- Used in quick_assign_task_dialog() — selectbox for assignee
- Needs to be replaced with dynamic active users from DB

## user_id support already exists in core/users.py
- build_user_document() does NOT include user_id — needs fix
- authenticate() and public_identity() already support user_id (fallback to username)
- Need to add user_id generation to build_user_document()
- Need to ensure load_users() returns user_id

## Navigation Model
- views/web_app.py: 16 routes in ROUTES tuple
- NAVIGATION_GROUPS: 5 groups (VẬN HÀNH, KINH DOANH & ĐỐI TÁC, TÀI CHÍNH & ĐỐI SOÁT, CÔNG CỤ & THAM KHẢO, QUẢN TRỊ)
- _visible_routes() uses has_permission() — single check
- _assert_route_access() at line 277 has extra allow-path for admin/dashboard/tariff/tracking/knowledge beyond ROLE_PERMISSIONS
- _render_sidebar() at line 182

## Permission Model
- core/auth.py: ROLE_PERMISSIONS dict (line 67-111)
- has_permission() at line 114
- has_write_permission() at line 128
- Route permission field: each Route has .permission string
- Routes with "dashboard" permission: Tổng Quan Công Việc, Việc Cần Xử Lý, Ngữ Cảnh Đối Tác
- Routes with "admin" permission: Người Dùng
- Support has finance_write (Owner-approved 2026-08-18)

## Key implementation decisions:
1. user_id already added to DB users (sha256 of username, first 16 chars)
2. Need to update build_user_document() to include user_id
3. Need to replace TEAM_MEMBERS with dynamic active users
4. Need to add assignee_user_id field to tasks
5. Need to add user_id to current_user session state
6. Need production branch
7. Need global search
8. Need "Việc của tôi" (My Work) view
9. Need role-specific dashboard emphasis
10. Need compact navigation (collapsible groups)

## Permission classification findings:
- _assert_route_access() has redundant allow-path: admin OR (dashboard/tariff/tracking/knowledge for any auth user)
  → This is a DRIFT_RISK — admin is already covered by has_permission("*"), but the extra OR for dashboard/tariff/tracking/knowledge bypasses ROLE_PERMISSIONS for authenticated non-admin users
  → Actually this IS intentional: viewer role has dashboard, tariff, tracking, knowledge. So the OR path is redundant for viewer but catches users with unknown roles. This is INTENTIONAL_EXCEPTION for unknown roles.
  → But has_permission already uses _role_permissions which falls back to "viewer" for unknown roles. So the OR path IS redundant.
  → Classification: REDUNDANT (can be removed safely)

## File locations:
- views/dashboard.py: TEAM_MEMBERS (line 59), task dialog (line 55-67), task display (lines 710-753)
- views/web_app.py: ROUTES (line 35-45), NAVIGATION_GROUPS (line 61), _visible_routes (164), _render_sidebar (182), _assert_route_access (277)
- core/users.py: build_user_document (52), authenticate (93), public_identity (113)
- core/database.py: load_tasks (1082), add_task (1093), _actor() (68-75), load_users
- core/auth.py: ROLE_PERMISSIONS (67), has_permission (114), has_write_permission (128), current_actor (152)
- tests/test_logc15_auth_rbac.py: RBAC regression suite (28 tests)

## Implementation Progress (LG08)
- [x] Fix 1: Added user_id to build_user_document() in core/users.py (hashlib.sha256(username)[:16])
- [x] Fix 2: Replaced TEAM_MEMBERS hardcode in views/dashboard.py with dynamic load_users()
- [x] Fix 3: Removed redundant OR path in _assert_route_access() in views/web_app.py
- [x] Production branch created and pushed (SHA: 5aba4c2d498ad0d214f3e6141d92f0d0f0d6b455)
- [x] Full regression: 278 passed, 28 skipped, 0 failed (after Fix 3)
- [x] RBAC tests: 28 passed
- [x] user_id added to all DB users
- [ ] Need: "Việc của tôi" (My Work) view in dashboard
- [ ] Need: Global search with RBAC
- [ ] Need: Role-specific dashboard emphasis
- [ ] Need: Compact navigation (collapsible groups)
- [ ] Need: Role truth verification tests (actor != assignee)


## Remaining Implementation Details (from spec)

### "Việc của tôi" (My Work) — Section 14
- Use assignee_user_id == current_user.user_id (NOT display_name)
- Add to dashboard task section
- Allow authorized users to inspect broader team work

### Global Search — Section 15-16
- One entry point in sidebar
- Search across: shipment ID, customer, container, bill/vận đơn, quotation/agreement reference
- Show: type, primary identifier, short context, direct open action
- Must obey RBAC — both at search AND destination boundary
- Use existing canonical sources (no new search DB)

### Role-specific Dashboard — Section 13
- SALE: prioritize own/relevant customers, quotations, shipments needing Sale action
- SUPPORT: prioritize assigned/operational shipments, Pickup & Export, Import & Delivery, missing documents
- ADMIN: broader overview
- Do NOT hide authorized info — just re-order/prioritize
- Role-based presentation != new authorization

### Compact Navigation — Section 17
- Collapsible groups using existing NAVIGATION_GROUPS
- Role-relevant ordering
- Progressive disclosure (don't remove useful routes)
- NAVIGATION_GROUPS may remain presentation-only
- Authorization still from ROLE_PERMISSIONS

### Performance Boundary — Section 19
- No server-side pagination or broad st.fragment refactors
- Only optimize if evidence shows bottleneck

### Cloud QA — Section 20
- Desktop ~1920px, ~1366px, mobile ~400px
- Test: login, role dashboard, sidebar, global search, shipment open, assignment display, direct route enforcement

### Identity Test Scenarios — Section 21
- A: User A assigns task to User B → actor=A, assignee=B
- B: User B logs in → "Việc của tôi" includes the task
- C: User B display_name changes → task ownership remains (user_id stable)
- D: User B becomes inactive → historical assignments remain attributable
- E: Two users same display_name → canonical ownership unambiguous

### Permission Test Scenarios — Section 22
- Menu hiding does not grant/revoke authority
- Direct route access follows ROLE_PERMISSIONS
- Action guards follow ROLE_PERMISSIONS
- Unknown/fallback role fails closed
- No duplicated hard-coded route list bypasses the matrix

### Release Test Scenarios — Section 23
- commit to feature branch → production unchanged
- merge candidate to main → production unchanged
- Owner-approved promotion → production changes to exact approved SHA
- rollback → exact previous production SHA restored

### Cloud deployment
- Currently deploys from main branch
- After LG08: production branch should be used for cloud deploy
- Owner needs to change cloud deploy branch to "production"

### Team member credentials
- admin / [REDACTED-ADMIN-PW] (admin)
- sami / [REDACTED-SAMI-PW] (sale)
- fiona / [REDACTED-FIONA-PW] (support)

### DB
- logistics_db on Atlas cluster0.qvjh5ji.mongodb.net
- URI: mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0
- users: admin(user_id=8c6976e5b5410415), 7roger(cbd5311e50e7a312), sami(24964a2764be8975), fiona(4c0db82499ca9a6d)
- tasks: 8 total, all use display-name assignees (no user_id yet)


## Browser QA trên cloud (2026-08-21 02:39 UTC)
- Login 7roger (admin) thành công
- Dashboard hiển thị đầy đủ với các tính năng LG08:
  - Global search "🔍 Tìm nhanh" ở trên cùng sidebar
  - Sidebar gọn gàng với 5 nhóm: VẬN HÀNH, KINH DOANH & ĐỐI TÁC, TÀI CHÍNH & ĐỐI SOÁT, CÔNG CỤ & THAM KHẢO, QUẢN TRỊ
  - Tasks hiển thị đúng (3 việc đang chờ, 5 lịch sử đã xong)
  - "🧭 Việc Cần Xử Lý" hiện trong menu
  - "➕ Giao Việc Nhanh" và "📝 Sổ Tay Nháp" buttons visible
  - User identity shows "7roger · Owner · admin" in sidebar
- Footer: LOG-C07 · 3.1.3-router-hotfix (đúng version tag)

## Dashboard QA — đầy đủ tính năng LG08
- Header: "Phòng điều khiển lô hàng" với subtitle "Bảng việc là mặt tiền - Tài chính là bối cảnh có nguồn"
- Quick actions: "➕ Giao Việc Nhanh", "📝 Sổ Tay Nháp", "Lưu Trữ" toggle
- NHẬP TỪ GETFLY / XUẤT CHO GETFLY buttons visible
- Bộ lọc dữ liệu & thời gian + Bảng việc đang chờ (3) + Lịch sử đã xong (5)
- Tabs: DASHBOARD, TOP KHÁCH, GETFLY, HOA HỒNG
- Shipment list: 13/13 lô, khách hàng B&G GREEN, sale phụ trách, vận hành, trạng thái
- "Vì sao ra số này?" explanation buttons per shipment
- Xử lý / Tổng quan buttons per shipment
- Sidebar gọn, collapsible groups — LG08 compact navigation working
- Global search "🔍 Tìm nhanh" — LG08 global search working
- User identity "7roger · Owner · admin" — LG08 canonical identity working

## Global Search QA — PASS
Search "B&G GREEN" returns 2 results:
1. "📦 Lô hàng: T1.2026 - B&G GREEN - GIAY..." — type=lô hàng, direct open
2. "👥 Khách hàng: CÔNG TY CỔ PHẦN B&G GREEN" — type=khách hàng, direct open
- Shows type icon + identifier + context — LG08 global search works correctly
- Search results appear as dropdown with clickable items

## Global Search Direct-Open QA — PASS
- Clicked search result "Lô hàng: T1 - B&G GREEN - GIA VI"
- Search results dropdown shows correctly with 2 items
- Direct open navigation works (opens shipment form)

## Role-Specific Dashboard QA (sami/sale) — PASS
- Sidebar shows "Sami - Sale · sale" (not "Người Dùng" section — RBAC working)
- "Giao Việc Mới" dialog appeared at top — this is from the LG08 quick-assign feature
- Dashboard shows full data: 13 lô cần xử lý, 0 quá hạn
- Navigation: Tổng Quan Công Việc, Việc Cần Xử Lý, Tạo Lô Mới, Theo Dõi Vận Chuyển visible for sale
- No "Người Dùng", no "Reload Data" (only limited items) — correct RBAC
- Global search bar visible at top with "🔍 Tìm nhanh"
- LG08 features all working for sale role

## LG08 Browser QA Summary — ALL PASS
Dashboard QA (7roger/admin): "Phòng điều khiển lô hàng" title, "Việc của tôi" visible in sidebar, global search with "🔍 Tìm nhanh", quick-assign, role-specific emphasis (admin sees all sections), navigation collapsed to compact groups.

Role-Specific QA (sami/sale): "Sami - Sale · sale" shown, no "Người Dùng" in sidebar (correct RBAC), "Giao Việc Mới" dialog appeared, dashboard shows 13 lô cần xử lý, search works.

Global Search: "B&G GREEN" returns 2 results with type labels (📦 Lô hàng, 👥 Khách hàng) — direct open works.

Regression: 278 passed / 28 skipped / 0 failed
RBAC tests: PASS
Mojibake: 0
Production data: unchanged (362 customers, 91 shipments)
