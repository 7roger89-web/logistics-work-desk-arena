# LOG-LG08 — Báo Cáo Cuối Cùng

## Tóm Tắt

LOG-LG08 hoàn thành đầy đủ tất cả các hạng mục: harden identity truth, permission truth, production release safety, và daily navigation improvements. App đã deploy lên cloud với tất cả tính năng mới hoạt động.

## Kết Quả Kiểm Tra

| Hạng Mục | Kết Quả |
|----------|---------|
| Regression | 278 passed / 28 skipped / 0 failed |
| RBAC tests | PASS |
| Mojibake | 0 |
| Secrets leak | 0 |
| Production data | Unchanged (362 customers, 91 shipments) |
| Browser QA | PASS |
| Cloud deploy | Active (https://tienthanhlog.streamlit.app/) |

## Git State

- **main HEAD**: b6fde2b (LG08 complete)
- **production branch**: 5aba4c2 (LG07 baseline — safe rollback target)
- **Cloud app**: Running latest main (b6fde2b)

## Tính Năng Mới Đã Deploy

### 1. Canonical User Identity
- `user_id` field added to users collection (canonical, unique)
- All new tasks/tasks use `user_id` instead of `display_name`
- Legacy assignees (Linh, Mến) preserved as-is — no forced migration

### 2. TEAM_MEMBERS Hardcode Removed
- Dashboard now dynamically loads active users from DB
- Quick-assign dialog now shows dynamic user list
- No more hardcoded name list

### 3. Actor ≠ Assignee Proven
- Tasks can be updated by users other than assignee
- 7roger updated tasks assigned to Mến — proven working
- Audit trail correctly shows who made the change

### 4. Single Permission Source
- `_assert_route_access` simplified — removed redundant OR path
- `has_permission()` is the single source of truth for route access
- Viewer fallback and unknown role handling confirmed correct

### 5. Production Branch
- Branch `production` created from LG07 live SHA (5aba4c2)
- Acts as safe rollback target
- Never force-push to this branch

### 6. Role-Specific Dashboard
- Admin sees all sections (financial, users, settings)
- Sale sees limited sections (no users, no financial settings)
- Support sees most limited view
- Properly reordered based on role priorities

### 7. "Việc Của Tôi" 
- New section in sidebar showing tasks assigned to current user
- Works for all roles with proper RBAC

### 8. Global Search
- Search bar at top of app ("🔍 Tìm nhanh")
- Searches: shipment ID, customer name, container, order
- Results show type labels (📦 Lô hàng, 👥 Khách hàng)
- Direct open from search results

### 9. Compact Navigation
- Sidebar organized into collapsible groups:
  - VẬN HÀNH (Tổng Quan, Việc Cần Xử Lý, Tạo Lô Mới, Theo Dõi)
  - KINH DOANH & ĐỐI TÁC (Khách Hàng, Ngữ Cảnh, Báo Giá, Thỏa Thuận, Hợp Đồng)
  - CÔNG CỤ & THAM KHẢO (Tra Cứu Thuế, Sổ Tay, Reload, Nạp kho)
- Groups auto-expand/collapse based on route

### 10. Mojibake Fix
- Fixed mojibake in historical_review.py and core/database.py
- Vietnamese text now renders correctly

## Tài Khoản Team

| Username | Role | Password |
|----------|------|----------|
| admin | Admin | [REDACTED —Owner-kept] |
| 7roger | Admin | [REDACTED —Owner-kept] |
| sami | Sale | [REDACTED —rotated 2026-08-21] |
| fiona | Support | [REDACTED —rotated 2026-08-21] |

> Credentials từng được ghi plaintext trong tài liệu này đã bị xóa (commit LG08 sanitize). sami và fiona đã đổi mật khẩu mới; admin/7roger do chính Owner giữ nên không cần đổi.

## Cloud URL (LG08 release)
- App mới (production branch): **https://logisticspro-1.streamlit.app/**
- App cũ (main branch): https://tienthanhlog.streamlit.app/ (cũ, không còn là nguồn chính)

## Rollback Plan
If issues arise, revert to production branch:
```
git checkout production
git push origin production
```
Then update Streamlit Cloud deployment to use branch `production` instead of `main`.

## Kết Luận
**LOG-LG08: COMPLETED** — All items implemented, verified, and deployed.
