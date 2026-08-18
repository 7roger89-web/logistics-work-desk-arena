# LG03 DEPLOYMENT TO OWNER MACHINE — continuation prompt (pasted_content_4.txt)

## Required steps (from Owner's continuation prompt)
1. Recover Owner machine runtime: repo path D:\Logistics_App_GitHub, local branch, local SHA, origin/main SHA, Streamlit PID, python exe, entrypoint (app.py), production DB logistics_db. Do via My Browser.
2. Update code: switch/use main, pull origin main, verify local HEAD = 90d8cef or descendant. No blind reset.
3. Clear safe runtime cache only: __pycache__, views\__pycache__, other project-local __pycache__. NEVER delete .streamlit\secrets.toml, data, backups, git history.
4. Start verified app: python -m streamlit run app.py (explicit python env). Verify CWD, python exe, entry, views.web_app.__file__, git SHA. Module must come from D:\Logistics_App_GitHub.
5. Production identity: environment PROD, database logistics_db, no TEST/DEV fallback. No printing credentials.
6. Bounded smoke (read-only, owner admin): login works; VI nav; no mojibake; 16 VI-first items; Tổng quan công việc, Khách hàng, Hồ sơ lô hàng, Việc cần xử lý, Đối soát tài chính, Quản lý người dùng all load; customers=362 shipments=78; admin active/admin; 3 rehearsal inactive.
7. Role smoke: SALE commercial visible, no finance write; SUPPORT ops visible, finance read-only, commercial/admin restricted. No new production accounts.
8. Finance safety read-only: no new obligations/transactions/allocations; UNKNOWN stays UNKNOWN; estimate separate; LG03 deployment = 0 business finance actual writes.
9. Incident record (must persist): during rehearsal cleanup an older tool hard-deleted 3 rehearsal accounts before soft-deactivation policy; restored + soft-deactivated. Users: rehearsal_admin/sale/support. No admin/customer/shipment impact. Root cause: old cleanup tool used delete_many. Prevention: tool rewritten to update_one (active=False + active_states history). Evidence: R0_release_verdict_facts.md, read-back ACCEPTANCE PASS.
10. Final closure if PASS: LOG-LG03 = RELEASED_VERIFIED. Record PRODUCTION_CODE_SHA, PRODUCTION_DB, SMOKE_RESULT, LANGUAGE_RESULT, RBAC_RESULT, FINANCE_SAFETY, USER_STATE, INCIDENT_STATUS, NEXT_SAFE_TASK. STOP. No LOG-LG04.

## Key facts
- main on GitHub = 90d8cef (merge commit) / latest main after verdict = dada01c (verdict report commit) — prompt says expected 90d8cef; verify owner pulls latest.
- Owner machine: D:\Logistics_App_GitHub, Windows cmd, git pull syntax `git pull origin <branch>`, kill streamlit via `for /f "tokens=5" %a in ('netstat -ano ^| findstr :8501') do @taskkill /PID %a /F`.
- Entry point: app.py (not views/web_app.py).
- Owner admin credentials: admin / (password known, do not print).
- My Browser: was previously used and timed out once (owner machine offline). Try again; browser tags show [Browser: My Browser].
- Production DB: logistics_db on cluster0.qvjh5ji.mongodb.net.
- state.json location: docs/goals/LOG-LG03/state.json (update to RELEASED_VERIFIED at end).
