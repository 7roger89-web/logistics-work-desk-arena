# LOGI-199 — Sale Home → Journey: authenticated, bounded proof

**Date:** 2026-10-16 UTC. **Repo:** `7roger89-web/logistics-work-desk-arena`.
**Session branch:** `arena/7d8e8372-logistics-work-desk-arena`.
**Verified base:** `7a73e484446bf8ab79f405125d6ba0589e8ab56a`, the unchanged Draft [#207](https://github.com/7roger89-web/logistics-work-desk-arena/pull/207) source (`arena/18ef00cf-logistics-work-desk-arena`). The new flow PR is stacked on that source, not on `main`. See the checkpoint packet for the published commit/PR identity.

`INITIAL_PLANNING_CLASSIFICATION=UIUX` · `FINAL_ROUTING_CLASSIFICATION=UIUX`
`EVIDENCE_VERDICT=PROVEN_FOR_BOUNDED_FLOW` · `VISUAL_VERDICT=BOUNDED_RENDERED_PASS`
`FULL_GOAL_199=IN_PROGRESS` · `PRODUCTION_READY=NO`

## What actually ran

The existing React/Streamlit app, real login (`AUTH_REQUIRED=true`), a canonical hashed **Sale** test user, and the existing isolated Mongomock transport. No business shell was present before login. No real Mongo URI, production secrets file/client/data, auth bypass, RBAC change, new workflow engine or product dependency was used.

1. Home at **1440×900** and **390×844**: to-do links and running statuses rendered; shell horizontal overflow **0**. #207's Home attention panel is **132.625 px**, beside a **473.171875 px** list; computed grid alignment is `flex-start`. This closes only the earlier Home rendering evidence gap, not #207's broader review or whole-app acceptance.
2. Clicked the Home action whose exact backend-generated route is `/lo-hang/FLOW199-FCL?tab=van-tai&stage=si-vgm&work=info`. It opened **that shipment, SI/VGM, work/info**, without reselecting its linked customer.
3. Closed the short popup to the map-first nautical-paper Journey, selected SI/VGM → its document bubble → its document popup; then selected on-board → its task bubble → its evidence popup. Mobile used touch taps plus the existing Fit/Đọc rõ controls.
4. Edited a distinct on-board date, clicked the actual Save button, independently read the canonical database/version/audit, fully reloaded the page, logged in again when required, navigated from Home and read the value back from both the UI and the DB.
5. Read-only cross-check of the existing full-scope `T6-FCL`: **11 nodes**, global missing-info count **3** retained in the whole-lot workspace, but **0** global missing-info disclosures/sticky actions in the on-board popup. Its unknown on-board date stays blank, not zero/completed. No write occurred to T6-FCL.

`FLOW199-FCL` intentionally confirms only pickup/export handling/export customs/origin terminal/main carriage. The existing primary-action authority then naturally links to SI/VGM; no manual-task text or unrelated shipment action was used to invent a stage. Its **9 applicable nodes**, SI/VGM ∥ gate-in branches and both merges into ETD remain intact. The separate 11-node T6 check protects the full map.

### Persistence proof (isolated data only)

| Viewport | Old → saved on-board date | Version | Audit | Reload UI + independent DB |
|---|---|---|---|---|
| Desktop 1440×900 | `2026-10-04 → 2026-10-05` | `1 → 2` | +1, `flow199.sale` / `sale` | PASS |
| Mobile 390×844 | `2026-10-05 → 2026-10-06` | `2 → 3` | +1, `flow199.sale` / `sale` | PASS |

Customer ID remains `CUST-ANPHAT`; no other sea fact changed. These dates precede the fixture's actual departure `2026-10-07`. `readback/` contains before, after-save and after-reload snapshots with audit old/new values, not credentials. This proves the unchanged canonical writer path and persistence across **page reload in the same isolated process**, not process-restart, Atlas transaction or production durability.

## Confirmed defects and the small repairs

| Before (actually observed) | Repair | Boundary |
|---|---|---|
| Raw manual tasks, including finance work, always linked to `?tab=lay-hang`; their schema has no stage binding. | `views/support_attention.py` and `views/logi_view_model.py::_task_projection` now open the task's own encoded shipment map. Home says **“Chưa gắn công đoạn; mở lô để kiểm tra”** and “Mở lô”; the explanation remains visible on mobile. | No text heuristic or invented stage/schema. Existing deadline, assignee, priority and manager UNKNOWN metrics are preserved. **Exact-stage navigation for these unbound legacy tasks remains incomplete.** |
| SI/VGM popup offered `customs/transport/booking/si/vgm` although its node declares only `si/vgm`. | `ShipmentDetail.tsx` passes the selected node's exact `documentCategories`, not a macro-region union. | Explicit `[]` remains scoped-empty; undefined remains whole-lot. Existing attachment filtering/writers unchanged. |
| On-board stage popup displayed the unrelated whole-lot “Thiếu 3 thông tin”; global sticky actions could enter node work. | Reuse the existing `showExistingWork` guard for those global sections. | Global checklist/finance/actions remain available in the whole-lot workspace; no finance repetition on nodes. |

Only **four product source files** changed, plus rebuilt `component/dist/logi-shell.js`; CSS is byte-identical. No map geometry, business writer, auth, RBAC, finance authority, shipment schema or production configuration changed.

## Evidence index

- `result.json`, `logs/after-browser.txt`: raw successful real-browser assertions for both viewports, both saves, zero page errors, and the 11-node guard.
- `readback/`: independently read canonical document/version/audit before save, after save and after full reload.
- `before/desktop-si-docs.png` → `after/desktop-si-docs.png`: same FLOW199-FCL stage, before/after document-scope repair. Baseline options are also in `logs/baseline-flow199-browser.txt`.
- `before/desktop-attention-target.png` → `after/desktop-unbound-task.png`: unbound task's old arbitrary export workspace versus honest own-shipment fallback.
- `after/{desktop,mobile}-home-fcl-target.png`: actual Home → exact stage destination.
- `after/{desktop,mobile}-fcl-initial.png`: preserved paper-map/parallel branches; `after/desktop-t6-full-scope-map.png`: all 11 full-scope nodes.
- `after/{desktop,mobile}-on-board-edited.png` and `*-on-board-reloaded.png`: actual interaction and post-reload readback.
- `logs/baseline-t6-browser.txt`: original T6 stage text including “Thiếu 3 thông tin”; `after/mobile-t6-on-board-popup.png`: repaired popup. No claim that a baseline T6 screenshot is archived here.
- `reference/`: real Chromium renders of the exact, unchanged Owner HTML at both viewports. This is a **design oracle only**, never business-data authority.
- `provenance.json` / `manifest.sha256`: exact tested source/dist/runner/reference hashes; no self-referential commit identity.
- `github-preflight-*.json`: fresh GitHub identity and Draft-state readback before publishing. #198 and #200–206 were inspected, not cherry-picked or mutated. The shared generated bundle must be rebuilt if those branches are later integrated.

Actual screenshots were opened and visually inspected (Home, map, SI documents, mobile on-board, both oracle sizes). The map-first paper design, parallel branch and short popup behavior are preserved. **Full pixel parity is not claimed**: existing header/toolbar, fit level, status vocabulary and applicable fixture nodes differ from the oracle. This is not a redesign campaign.

## Verification, including failures

Log message content is preserved; trailing horizontal whitespace in `.txt` output was normalized for Git. Browser result JSON and DB snapshots are unmodified.

- `npm run typecheck`, official `npm run build`, `npm run scan` — **PASS**; 1,936 modules; **0 executable process references**. Dist synchronized with the tested source.
- `pytest` on `test_sale_home_journey_flow_199.py`, `test_support_attention_now_166.py`, `test_operations_control_tower_170.py` — **23 PASS**. Includes adversarial task text/encoded identities/untrusted route input, authoritative stage preservation, UNKNOWN-not-completed, and a guard against turning missing stage metadata into manager intervention metrics.
- `dom_sale_home_journey_flow_199.mjs` — **PASS**, real compiled React with canonical fixture. Distinct SI/VGM/customs/booking/transport file names challenge file filtering, not only the picker; empty-category ETD, on-board scope and whole-lot finance remain covered. Metadata in this DOM lane is a fixture, not an uploaded-file persistence claim.
- Existing `dom_home_attention_layout.mjs` — **PASS**.
- New route adversarial cases and node-category assertion were **RED before repair**, then PASS; raw intermediate failure logs are retained. The final DOM harness waits for rendered conditions rather than assuming React Router transitions finish after a fixed sleep.
- Wider related Python selection — **95 PASS / 6 FAIL**. **Not an all-green suite.** The same six failures were already observed before product edits in the initial broader baseline (**131 PASS / 6 FAIL**, a different selection): five primary-action/profile route expectation mismatches (`lay-hang` versus existing canonical `van-tai`), and one existing zero-node JSDOM timing/render lane failure. Those tests were not deleted, skipped or rewritten to hide them. Commands/results are bounded; whole-app/other-mode coverage is not claimed.
- GitHub CI and independent external review are separate from these local results; see the checkpoint packet for observed status. No Owner UAT, main merge or deployment performed.

## Browser environment and reproduction (executor/CI only)

Chromium **141.0.7390.0**, temporary Playwright **1.56.1**. Missing NSS/NSPR libraries were resolved from the temporary Chromium package's bundled AL2023 archive into local test directories and passed via `LD_LIBRARY_PATH` **only to the runner**. No OS installation, product browser dependency, disabled web security, public host or new auth mode.

The Owner is **not** asked to run Python, ZIP, CMD or capture screenshots. For a later authorized executor:

1. Use existing Python/component dependencies and a verified external Playwright/Chromium runner. Create a strong random password in an ignored, mode-600 JSON file with key `password` (never publish it).
2. Start `scripts/logi199_authenticated_flow_app.py` with the process tool, `AUTH_REQUIRED=true`, no real Mongo URI/secrets, `LOGI199_TEST_CREDENTIALS_FILE` and `LOGI199_TEST_READBACK_FILE` pointing into `.tmp/`, Streamlit bound to `0.0.0.0:9501`. It reuses the existing T6 launcher, provisions hashed test-only users and emits a limited private DB snapshot. No business-shell/session login is injected.
3. Run `tests/component/browser_sale_home_journey_flow_199.mjs` with those file paths, `LOGI199_TEST_URL`, `PLAYWRIGHT_MODULE` and `CHROMIUM_EXECUTABLE`. Defaults are loopback because this is an in-sandbox test runner, not browser-facing application code. Start a **fresh isolated server process** for a complete repeat so the runner must make distinct edits again.
4. DOM fixture: `.venv/bin/python scripts/gen_logi195_dom_fixture.py --fixture .tmp/logi199-flow/dom-fixture.json`; then `node tests/component/dom_sale_home_journey_flow_199.mjs .tmp/logi199-flow/dom-fixture.json`.
5. Stop the isolated server after capture. Process-local samples disappear; credentials and temporary browser/runtime dependencies are not committed.

## Gates and unfinished work

`P2P_LAW_SOURCE=LOCAL_PORTABLE`; this actor read root AGENTS, the valid portable law, active experience and required UIUX/frontend/React skills and issued its own receipts. Exact law/skill/reference hashes are in provenance.

**Không bị over engineering chứ?**
- `SIMPLER_PATH`: existing route/component scope guards and writer; no new engine/schema/library.
- `MATERIAL_PROGRESS`: three reproduced defects repaired; two genuine saves and reload readbacks.
- `NECESSITY`: each product edit corresponds to a demonstrated route/scope leak; no CSS-only or speculative cleanup.
- `CORE_BEFORE_SUPPORT`: real flow and persistence first; this one evidence checkpoint comes after.
- `SMALLER_VERIFIABLE_SLICE`: only the Home/FCL boundaries exercised here; defer legacy stage-binding design, other modes and broad cleanup.
- `OE_VERDICT=DO_IT` for this slice; further UI refactoring is **DEFER_UNTIL_NEEDED**.

**Highest-value next step:** establish an authoritative stage binding for currently unbound manual tasks, then challenge Home → exact node for those tasks (especially finance/import), without guessing from text. Broader #199 mode coverage, existing six test gaps, independent review and Owner UAT remain open. `FULL_GOAL_199=IN_PROGRESS`, `PRODUCTION_READY=NO`.
