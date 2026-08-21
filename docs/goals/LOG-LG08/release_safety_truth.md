# LOG-LG08 Release Safety Closure — Live Truth

## Phase 1: Current Live Truth (verified 2026-08-21)

- **MAIN HEAD**: 5420058 (HEAD -> main, origin/main, origin/HEAD) "LG08: final report"
- **PREVIOUS_PRODUCTION_SHA**: 5aba4c2 (origin/production) "LG07: final report"
- **b6fde2b**: "LG08: Fix mojibake" — the approved LG08 code SHA (before final report commit)
- **production is ancestor of main**: YES
- **Commits between production and main**:
  - f794325: LOG-LG08: Canonical identity, remove TEAM_MEMBERS hardcode, role-specific dashboard, global search, compact navigation, Việc của tôi
  - b6fde2b: LG08: Fix mojibake
  - 5420058: LG08: final report (docs only)

## DB State (verified)
- DB: logistics_db on cluster0.qvjh5ji.mongodb.net
- Customers: 362
- Shipments: 91
- Duplicate shipment IDs: 0
- Users:
  - admin | admin | active=True | display=Owner
  - rehearsal_admin | admin | active=False
  - rehearsal_sale | sale | active=False
  - rehearsal_support | support | active=False
  - 7roger | admin | active=True | display=7roger - Owner
  - sami | sale | active=True | display=Sami - Sale
  - fiona | support | active=True | display=Fiona - Support

## Streamlit Cloud
- App: https://tienthanhlog.streamlit.app/
- Repo: 7roger89-web/logistics-work-desk
- Current deploy branch: **main** (needs to switch to **production**)
- Owner controls the dashboard at share.streamlit.io

## Plan
1. Sync production branch to b6fde2b (the actual LG08 code, excluding final_report docs commit)
2. Owner switches Streamlit Cloud deployment branch from main to production
3. Verify cloud works on production branch
4. Prove isolation
5. Credential hygiene check
