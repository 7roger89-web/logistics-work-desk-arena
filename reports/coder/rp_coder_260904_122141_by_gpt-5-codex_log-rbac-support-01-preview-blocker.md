# Coder Report: LOG-RBAC-SUPPORT-01 local Preview blocker repair

Date: `2026-09-04`  
Workspace: `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`  
Branch: `codex/log-rbac-support-01`  
Parent candidate: `7b7fa132b8dc1d6868c45796e78f1bc3a53bffd7`

## Scope and authority

Owner approved installing a local MongoDB Community Server and preparing the existing Logistics app for a Support visual gate. The repair was allowed only because a real mounted blocker was reproduced. No Production connection, deployment, push, PR, merge, or new framework was authorized.

## Invariant Family Map

- Family: authenticated Admin user-management flow used to create the local Support preview identity.
- Authority: current `LOG-RBAC-SUPPORT-01` plan, repository `AGENTS.md`, and the Owner's local Preview request.
- Primary path: `Người Dùng` route → `_render_user_management` → `_create_user_from_admin` → existing `save_user`.
- Sibling boundary: authenticated login, Admin-only route, Support login, existing `ROLE_PERMISSIONS`, and local-only database identity.
- Forbidden fallback: no direct user collection seeding, no Local Admin bypass, no Production database, no new auth/RBAC layer.
- Result: one missing `current_user` import was the only reproduced source defect; the existing persistence and permission path remain unchanged.

## Reproduction and root cause

After local Admin bootstrap/login, the real headed browser reached `Quản lý người dùng`. Submitting the existing Support-account form failed with `NameError: name 'current_user' is not defined` at `views/web_app.py:560` inside `_create_user_from_admin`. The module imported other `core.auth` helpers but not `current_user`.

## Fix

Added `current_user` to the existing `core.auth` import in `views/web_app.py`. No other application source, permission matrix, persistence method, or UI layout was changed.

## Verification

- `[PASS]` `python -m compileall -q views\\web_app.py` — exit code 0.
- `[PASS]` Existing `python scripts/check_config.py` — local Preview identity and Mongo connection accepted; no secret value printed.
- `[PASS]` Local Mongo ping and server identity check — local service only; no Production database touched.
- `[PASS]` Headed browser at `http://127.0.0.1:9501` — Admin login, User Management route, Support creation, logout, and Support login completed. Final visible state shows `Codex Local Support · support`, Preview/Staging banner, and no exception/modal.
- `[PASS]` Local user readback contains the fake Admin and Support roles; password material was not read back or recorded.
- `[NOT RUN]` Broad/full test suite — explicitly outside this fast Owner visual-gate repair; prior focused evidence remains the test authority for the implementation candidate.

## Local runtime state

- MongoDB Community Server 6.0.27 is running as the Windows `MongoDB` service and listens only on loopback.
- Branch-local `.streamlit/secrets.toml` uses Preview identity, authentication required, and the isolated test database only. It is ignored and no values are recorded here.
- Streamlit remains running on port 9501 for Owner inspection.
- Business data was not seeded; the local database contains only app-created empty collections plus fake preview identities/audit state.

## Production and repository safety

- `PRODUCTION_CONNECTION=NO`.
- `PRODUCTION_DATA_MUTATIONS=0`.
- No `logistics_db` or `logistics_workdesk_logc14` operation was performed.
- No push, PR, merge, deploy, or promotion was performed.
- Owner worktree outside this isolated worktree was not modified.

## Handoff

Handoff to supervisor - local blocker repaired and Support visual gate is mounted; Owner must perform the six-surface visual inspection before any further action.
