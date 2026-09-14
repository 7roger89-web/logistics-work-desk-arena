# AGENTS.md — Logistics Work Desk

## P2P Supreme Law bootstrap (mandatory)

Before substantive analysis, planning, implementation, review, or merge decisions, establish exactly one valid P2P law source in this order:

1. `CANONICAL_AUTHENTICATED` — read `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` when actually reachable.
2. `LOCAL_INSTALLED` — otherwise use `.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md` only when it contains `P2P_SUPREME_OPERATING_LAW_V1` and is not known stale.
3. `LOCAL_PORTABLE` — otherwise use generated `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` only when it carries `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical-source provenance, and source-content SHA.
4. `INLINE_CAPSULE` — otherwise use only a fresh explicit `SUPREME_LAW_CAPSULE` supplied by the current P2P Control Tower prompt.

If none is available, stop before substantive work with `P2P_LAW_SOURCE=LAW_CONTEXT_BLOCKED`.

Do not treat an unauthenticated or repo-scoped 404 as proof that canonical law is absent. Do not claim a law source was read unless it actually was. `TASK_BRANCH != LAW_AUTHORITY`. Fresh reachable canonical law wins over stale local projections or chat memory.

At task start report exactly one:
`P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED|LOCAL_INSTALLED|LOCAL_PORTABLE|INLINE_CAPSULE|LAW_CONTEXT_BLOCKED`.

## Baseline hiện tại

- **Branch verified:** `log-c15-user-identity-rbac` @ `e518cae` (LOG-C13 + LOG-C14 + LOG-C15, đã kiểm chứng).
- Lineage: `main` ← `log-c13-contract-commercial-handoff` ← `log-c14-e2e-release-readiness` ← `log-c15-user-identity-rbac`.
- Merge strategy được khuyến nghị: 1 PR cumulative (C13+C14+C15) vào `main`, xem `docs/LOG_C15_HANDOFF.md` mục 37.
- KHÔNG deploy production; KHÔNG merge main cho đến khi Owner xác nhận.

## Quy ước quan trọng

- **Credential:** chỉ trong `.streamlit/secrets.toml` (gitignored). Không bao giờ in/hardcode URI/mật khẩu trong code.
- **App chạy trên máy Owner:** 2 instance production Streamlit (port 8501, 8510). Trước khi test UI, mở port khác (vd 9501), tắt sau khi xong.
- **Git credential helper:** `git config --global credential.helper manager` (helper cũ chỉ đường dẫn exe trực tiếp bị lỗi word-split trên máy này).
- **Database:** `logistics_workdesk_logc14` hiện là DB app đang dùng; `logistics_db` tồn tại trên cluster chưa dùng; DB test tạo riêng với prefix `logistics_workdesk_logc15+` và TỰ DROP sau khi chạy.
- **Quyền Atlas user hiện tại** chỉ đọc/ghi trên `logistics_workdesk_logc14` — không `dropUser`, không `listIndexes`.
- **Production untouched:** không drop/tạo database app, không thay đổi instance production.

## Testing

- Full suite: `python -m pytest tests -q` → kỳ vọng 200 passed, 28 skipped (pure tests).
- Tests runtime cần Streamlit/Mongo thực được skip theo thiết kế — không cố sửa chúng thành chạy được.
- Auth/RBAC: `tests/test_logc15_auth_rbac.py` (pure, mock streamlit).
- DB users: `scripts/logc15_db_users_test.py` + runner — chạy trên DB test riêng, tự dọn.

## Quyền (ma trận duy nhất: core/auth.py ROLE_PERMISSIONS)

admin=`*`, sale=sales_write + commercial_write + shipment_create + ops + knowledge + customers + tracking + tariff + commercial_view..., support=commercial_view + ops + finance_view + customers + tracking..., viewer=fallback read-only.

## Bootstrap

Chưa có user → app render form tạo Admin đầu tiên (không default credential). CLI: `python scripts/setup_first_user.py` (tương tác, mật khẩu không qua args).
