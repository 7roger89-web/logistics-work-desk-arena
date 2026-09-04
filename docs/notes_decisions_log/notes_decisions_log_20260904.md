# Notes and Decisions Log — 2026-09-04

## LOG-RBAC-SUPPORT-01 local Preview gate

- Owner approved local MongoDB installation only for the isolated Support Preview; Production remained forbidden.
- MongoDB 6.0.27 was selected because the host is Windows 10 and the newer installed server binary failed to start. The local Windows service now runs on loopback.
- Branch-local config was set to Preview identity, authentication required, and the isolated `logistics_dev` database only. Secret values are not recorded.
- Real headed browser reproduction found one blocking application defect: `_create_user_from_admin` called `current_user()` without importing it.
- Surgical repair: add the existing `current_user` helper to the `core.auth` import in `views/web_app.py`.
- Verification: compile passed; local config preflight passed; Admin bootstrap and Support creation/login completed in the real browser; final Support dashboard is mounted at `http://127.0.0.1:9501`.
- No Production connection or data mutation occurred. No push, PR, merge, deploy, or promotion occurred.
- Remaining gate: Owner visually inspects the six requested Support surfaces. No broad regression run was performed.

Related coder report: `reports/coder/rp_coder_260904_122141_by_gpt-5-codex_log-rbac-support-01-preview-blocker.md`.
