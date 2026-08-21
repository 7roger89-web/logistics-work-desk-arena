# LOG-LG08 Phase 0 — Current Truth

## Git
- main HEAD: 5aba4c2 (LG07 final report)
- All branches: main only (no feature/, no production branch yet)
- Cloud deploy: https://tienthanhlog.streamlit.app/ → deploys from main (7roger89-web/logistics-work-desk)

## DB Users (logistics_db, users collection)
| username | display_name | role | active | user_id |
|----------|-------------|------|--------|---------|
| admin | Owner | admin | True | ObjectId(6a83dfdec59a89ba3d41a321) |
| rehearsal_admin | Nguoi quan tri | admin | False | ObjectId(6a840e9c06cbdb86c14f45ce) |
| rehearsal_sale | Nhan vien Sales | sale | False | ObjectId(6a840e9c06cbdb86c14f45cf) |
| rehearsal_support | Nhan vien Ho tro | support | False | ObjectId(6a840e9c06cbdb86c14f45d0) |
| 7roger | 7roger - Owner | admin | True | ObjectId(6a86754337aa5257721474b4) |
| sami | Sami - Sale | sale | True | ObjectId(6a86754437aa5257721474b5) |
| fiona | Fiona - Support | support | True | ObjectId(6a86754537aa5257721474b6) |

- NO user_id field exists — _id is ObjectId (immutable but not a string canonical key)
- display_name used as assignee (TEAM_MEMBERS hardcode)

## TEAM_MEMBERS Hardcode — FOUND
- File: views/dashboard.py line 59
- `TEAM_MEMBERS = ["Tất cả (Team)", "Thành", "Mến", "Linh"]`
- Used at line 62: `t_assignee = c1.selectbox("👤 Giao cho ai?", TEAM_MEMBERS)`
- add_task() stores assignee as display name string
- tasks collection: {content, assignee, deadline, done, created_at, created_by}
- created_by uses _actor() from core/auth.py

## Audit Actor Model
- core/auth.py line 152: `def current_actor() -> str` — returns username string
- tasks.created_by stores actor username
- No actor_user_id field

## Permission Model
- core/auth.py line 65-111: ROLE_PERMISSIONS dict
- line 114: `def has_permission(permission: str) -> bool`
- line 128: `def has_write_permission(permission: str) -> bool`
- Need to check _assert_route_access and route definitions

## Navigation Model
- views/web_app.py line 61: NAVIGATION_GROUPS tuple
- line 182: `_render_sidebar(current_user, routes)`
- line 280: route access check comment
- NO global search exists currently

## To Do
- Remove TEAM_MEMBERS hardcode → use active users from DB
- Add user_id canonical field
- Prove actor != assignee in task model
- Legacy migration: assignee values "Thành", "Mến", "Linh" → map to user_ids
- Single permission source cleanup
- production branch from live SHA
- Role-specific dashboard
- "Việc của tôi" queue
- Global search with RBAC
- Compact navigation
