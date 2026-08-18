# LG03 OWNER MACHINE DEPLOYMENT — progress (18/08/2026 ~15:15)

## Confirmed so far
1. Owner's machine code: local main branch, HEAD `3c1e1c7` = merge of LG03 main (39125d0) + small commit preserving LG02 tool fix (1 file: docs/goals/LOG-LG02/tools/fix_vietnamese.py, 2 ins/2 del). Descends from main 90d8cef. PRODUCTION_CODE_SHA candidate = 3c1e1c7.
2. App runs on owner machine at http://localhost:8501 (title "LOGISTICS PRO"), started by owner with streamlit run app.py.
3. Login page renders Vietnamese correctly: "Tài khoản / Mật khẩu / Đăng nhập" — NO mojibake.
4. Session cookies lost after app restart (login form reappears) — owner logged in once, restarted app, needs re-login.
5. Owner said "đã đăng nhập" then "xong" twice — browser view shows login form again (session cleared after restart).

## Remaining smoke checks (need owner re-login)
- Navigate dashboard: verify 16 VI-first menu labels, counts (362 customers, 78 shipments), no mojibake.
- Screens: Tổng quan công việc, Khách hàng, Hồ sơ lô hàng/Theo dõi, Việc cần xử lý, Đối soát tài chính, Quản lý người dùng.
- Admin active, rehearsal inactive (check via app users page or read-only DB probe later; app users page renders roles/active status — can check visually in app).
- Role smoke: SKIP (no Sale/Support production accounts exist; prompt forbids creating accounts for smoke) — state SKIP in report.
- Finance safety: read-only, 0 writes.
- Production identity: D:\Logistics_App_GitHub + .streamlit/secrets.toml = logistics_db, release_mode=true (established LG02; not to be changed).

## Deployment steps completed
1. Recover runtime: DONE (owner ran streamlit run app.py; My Browser connected)
2. Update code: DONE (owner merged main into branch, switched main to 3c1e1c7)
3. Clear safe runtime cache: DONE (rd views__pycache__ core__pycache__ _pycache__)
4. Start app: DONE
5. Production identity: app served by D:\Logistics_App_GitHub config (inferred from LG02 verified setup; cannot read .streamlit/secrets.toml remotely without DB check)
6. Bounded smoke: IN PROGRESS (login page VI OK; dashboard pending re-login)

## Incident record (must persist in final report)
During rehearsal-user cleanup an older tool hard-deleted 3 rehearsal accounts before the soft-deactivation policy; recovered and soft-deactivated (active=False + active_states history). Affected users: rehearsal_admin/sale/support. No admin/customer/shipment impact. Evidence: R0_release_verdict_facts.md, cleanup tool rewritten to update_one.

## Final closure items
- state.json: LOG-LG03 = RELEASED_VERIFIED; PRODUCTION_CODE_SHA=3c1e1c7; SMOKE_RESULT; LANGUAGE_RESULT; RBAC_RESULT; FINANCE_SAFETY; USER_STATE; INCIDENT_STATUS; NEXT_SAFE_TASK = "Không có tác vụ tiếp theo" (no LOG-LG04).
- Report structure: LG03 RELEASE VERDICT + REHEARSAL CLEANUP RESULT + ADMIN SAFETY + FINAL PR HEAD SHA + MERGE SHA + MAIN AFTER MERGE + REGRESSION STATUS + PRODUCTION DATA SAFETY + DEPLOY STATUS + OWNER ACTION NEEDED + LOG-LG04 STATUS = NOT_STARTED.
