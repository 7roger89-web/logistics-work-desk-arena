# LOGI-APP-RENEWAL-01 — Issue #199 evidence

**Snapshot:** 2026-10-16 · **Branch:** `arena/aa27a489-logistics-work-desk-arena` · **Base HEAD:** `5c6642a339ec53fe4cc300b15f665e2cd5384bca`

`P2P_LAW_SOURCE=LOCAL_PORTABLE`
`LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`
`EXPERIENCE_CHECK=NO_MATCH`

## Outcome and scope

The smallest active-app slice now mounts the existing task desk at `/viec-can-xu-ly` and links to it from Home without restoring a broad navigation item. Sale/Support task creation uses the existing `task_create` dispatcher, `core.database.add_task`, permission check, task audit, and fresh `load_tasks` readback. Optional destination metadata is explicit: stage nodes come from the selected shipment’s current mode-aware Journey; finance and whole-lot are explicit scopes; missing/stale stages fall back to that lot with a notice; unlinked tasks remain generic at `/lo-hang` with no invented shipment. Home removes the focus shipment’s `PRIMARY_ACTION` by identity before bounding Attention, so a newly due task is not sliced away. A secondary compact Attention task with an unknown stage includes the fallback explanation in its visible text and accessible name.

No workflow engine, data migration, Journey redesign, production mutation, auth bypass, merge, push, or deployment was performed. PR #207 and #208 were freshly checked and remain OPEN Draft; neither branch was changed.

## Evidence — challenged behavior only

- **Focused backend regression:**
  `.venv/bin/python -m pytest -q tests/test_logi_task_routing_199.py tests/test_support_attention_now_166.py`
  → **14 passed**. Covers mode-specific eligible stage choices; canonical writer metadata, creator/assignee, deadline and audit; dispatch/readback/replay guard; Viewer denial; stage/finance/whole-lot/unknown/stale/generic routes; unchanged legacy records. A fresh task read from the isolated database feeds both the Task desk projection and Home Attention with the same exact stage route.
- **Authenticated app path:** Streamlit `AppTest` logged in through the real login form as a synthetic Sale account with `AUTH_REQUIRED=true`, using only an isolated `mongomock` staging database and a synthetic shipment. The existing app build-view-model path and bounded dispatcher wrote one stage-bound task; the next app run reloaded it, returned correlated `lastWrites` readback, retained the audit row, and projected `/lo-hang/AUTH-199-SEA?tab=van-tai&stage=si-vgm&work=info` for both Task desk and Home. `logi_shell.render` was replaced only in this test run to capture the Python view-model; AppTest did **not** render/click the React component.
- **React DOM acceptance:**
  `node tests/component/dom_acceptance_task_routing_199.mjs`
  → **PASS** against the production bundle in JSDOM: Home → task desk → explicit stage create event → correlated success/fresh task display → Home stage CTA → exact existing SI/VGM workspace; secondary unknown-stage disclosure; generic unlinked task has no fake lot.
  `node tests/component/dom_acceptance_internal_ux_simplify.mjs` → **PASS, 8 checks**, including Home task entry, normal-nav omission, and unrelated existing search/quote/translation checks.
- **Frontend and bundle:** `npm run typecheck` → **PASS**; `npm run build` → **PASS** (JS 1,440.03 kB, CSS 82.41 kB); `npm run scan` → **PASS**, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`. Tracked `component/dist` outputs were rebuilt.

## Missing evidence and known failures

- No Chromium/Firefox/Playwright browser is available in this environment. No real layout, screenshot, or 1440×900 desktop / 390×844 mobile acceptance is claimed. JSDOM confirms text/links/events only; it has no layout engine. The compact warning is present in the DOM, but responsive fit remains unverified.
- The full suite was **not** run. `pytest --collect-only -q tests` collected 1,890 tests then stopped on the existing `tests/test_partner_reconciliation_desk_write_oracle.py` import of missing `views.web_app.ROUTES`. No test was removed or suppressed. The six unrelated baseline failures specified in the task were left untouched. Other broad DOM scripts exercised during triage stopped at pre-existing expectations outside this slice (Home deadline/hero copy, shipment-list fixture filtering, and Journey context test ID); their later task assertions therefore remain unverified.
- `npm ci` reported one high-severity audit finding; no dependency upgrade or audit fix was applied.

`EVIDENCE_VERDICT=INCOMPLETE` — the authenticated isolated write/readback, exact routing projection, focused regressions, component DOM flow, build and executable-process scan are proven; desktop/mobile browser acceptance and the full suite remain unverified.

## OE_GATE

**Không bị over engineering chứ?**

- `SIMPLER_PATH=YES` — reuses the current Journey builder, task writer, dispatcher, route model, and mounted task page.
- `MATERIAL_PROGRESS=YES` — a canonical task can now be created, read back, displayed on Home, and routed by explicit metadata.
- `NECESSITY=YES` — the active task route/create action and non-heuristic destination are the requested behavior.
- `CORE_BEFORE_SUPPORT=YES` — permission, destination validation, audit, and fresh readback are in the existing backend path before UI feedback.
- `SMALLER_VERIFIABLE_SLICE=YES` — no migration, engine, or Journey redesign; browser work is explicitly not claimed.

`OE_VERDICT=DO_IT` — this is the smallest tested active-app path that proves authoritative task routing without guessing from task wording.

`FULL_GOAL_199=IN_PROGRESS` · `PRODUCTION_READY=NO` · `LEARNING_RECONCILIATION=NONE`
