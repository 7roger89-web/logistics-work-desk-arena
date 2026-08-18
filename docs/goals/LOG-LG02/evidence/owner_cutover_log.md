# Owner Cutover Log — LOG-LG02 (running record)

Date: 2026-08-18 (UTC)

## Gate events

| Event | Time (approx) | Token |
|---|---|---|
| INTERNAL RELEASE approved by Owner | 2026-08-18 | "APPROVE INTERNAL RELEASE" (verbatim) |

## Candidate state at gate

| Item | Value |
|---|---|
| Candidate branch | `log-lg01-multi-user-internal-rc` @ `7roger89-web/logistics-work-desk` |
| Tip at approval | `4388e2f` (R4 evidence re-verification commit; base `a96ad86` hardening on LG01-T12 `ba4142c` on main `82c8134`) |
| Draft PR | #1, head = branch tip |
| Preflight | 12/12 PASS, suite 200/0 |

## Cutover plan communicated to Owner (machine: Owner's Windows PC, repo at D:\Logistics_App_GitHub)

1. `git pull origin log-lg01-multi-user-internal-rc` (Owner hit Errno2 because LG02 commits not yet on his local clone)
2. `python docs\goals\LOG-LG02\tools\export_production.py` (owner runs on his machine; prompts for Atlas URI; exports all logistics_db collections to `backups/LG02-cutover-<ts>/` read-only)
3. Edit `.streamlit\secrets.toml`: `[mongo]` uri = Atlas Cluster0 URI, database = logistics_db, allowed_databases includes logistics_db, release_mode = true; add `[env] identity = PROD_INTERNAL`; keep gemini/telegram intact
4. `streamlit run web_app.py` (Owner's usual startup)
5. First-admin bootstrap form (users collection empty in logistics_db)

## Post-cutover verification plan (Manus side, read-only via Owner's Atlas session in browser)

- Confirm app is serving candidate tip (UI shows LG02 version markers / check users collection created via Data Explorer)
- Confirm no illegitimate mutation: compare collection counts vs R1 inventory (customers 362, shipments 78, audit_logs 54 + new bootstrap user + audit entries = expected)
- Sanity: identity guard PROD_INTERNAL active; RBAC spot check (login as different role not possible pre-user-creation; smoke via public view)

## Rollback if P0

Owner restores pre-cutover secrets.toml + re-runs old app startup; data restore via `restore_production.py` (ROLLBACK CONFIRM token) against the pre-cutover export.

## Status

- Git pull succeeded on Owner's machine; export_production.py ran successfully (pre-cutover snapshot created; required new DB user `admin` with reset password in Atlas).
- Owner then opened the STREAMLIT DEPLOYED instance (NOT the local app) — screenshot shows a deployed app with mojibake Vietnamese labels, stale "Local Admin" login, and "AUTH_REQUIRED" warning. This is the legacy deployed app, not the newly configured local cutover.
- Next: verify which environment the owner should use; local localhost:8501 startup pending confirmation; asked owner for deploy URL and localhost:8501 status.
- Owner request: fix Vietnamese mojibake encoding on UI.

AWAITING_OWNER_EXECUTION.
