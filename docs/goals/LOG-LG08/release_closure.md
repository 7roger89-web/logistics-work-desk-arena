# LOG-LG08 Release Safety Closure — Progress

## Current State (2026-08-21)
- **production branch** = b6fde2b (LG08 complete code) ✅ pushed to remote
- **main branch** = 5420058 (includes production + docs)
- **Code identical** between production and main (only docs differ) ✅
- **Old app (main branch):** https://tienthanhlog.streamlit.app/ — working
- **New app (production branch):** https://logisticspro-1.streamlit.app/ — deployed, secrets configured

## Steps Completed
1. ✅ Phase 1: Live truth verified (main=5420058, production=b6fde2b)
2. ✅ Phase 2: production branch synced to b6fde2b, Owner deployed new app from production branch
3. ✅ Phase 3: App VERIFIED — login screen appeared, admin/7roger899 logged in successfully, dashboard shows "13 lô cần xử lý" + real shipment data, sidebar "Owner · admin". Secrets correct, DB connected. CLOUD_LIVE_SHA = b6fde2b
4. ✅ Phase 4: Isolation PROVEN — pushed docs-only test commit 36c01cb to branch test/release-isolation; origin/production stayed b6fde2b (unchanged). Test branch deleted; main reset to 5420058

## Remaining Steps
- Phase 5: Real user role reconciliation
- Phase 6: Credential hygiene (sanitize final_report.md, rotate sami + fiona passwords)
- Phase 7: Final release record + report

## Credentials (for testing)
- admin / 7roger899 (admin)
- 7roger / 7roger899 (admin)
- sami / Sami2026! (sale)
- fiona / Fiona2026! (support)

## DB
- logistics_db on Atlas, 362 customers, 91 shipments, 7 users (admin, 7roger, sami, fiona, + 3 rehearsal inactive)

## Phase 5 — ROLE RECONCILIATION (2026-08-21)
admin=admin/active, 7roger=admin/active, sami=sale/active, fiona=support/active, 3 rehearsal users inactive. All have canonical user_id. Roles match Owner-approved policy — NO DRIFT.
