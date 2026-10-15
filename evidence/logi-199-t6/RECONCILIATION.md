# GOAL #199 / #198 integration — acceptance reconciliation

> **Current repair checkpoint (2026-10-15):** work is on fixed branch `arena/bb243332-logistics-work-desk-arena`; current source commit `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7`; source-built dist JS SHA-256 `19674586f24fa2f66484c26640519a489e94b8656dcccdc21faa9f96b30909a3`, CSS SHA-256 `6973bae48887aefea59f09557f35922feafda5118a9a4875ae676c3ca86c7c4f`. The only visual oracle is `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html` SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`. Evidence/dist commit `754a619f30affd1c18753b50f78d917bb2db5944` is committed; post-commit typecheck/build/scan and clean dist-sync pass. Focused DOM receipts are in `evidence/logi-199-g2/metrics.json`. No matching push-workflow includes this branch, so current Actions CI is `NOT_TRIGGERED`. `FULL_GOAL_199=IN_PROGRESS`; no Independent Review PASS, Supervisor PASS, Owner UAT, main merge, or production deploy is claimed.

## Current review repair — LOGI-199 G2 (bounded; no G0–G5 redo)

- **A — desktop G2:** the previous successful browser capture (source `d77446e7…`) measured 1440×900 map height `635px` → `780px` (`+145px`), top `208.63px` → `106.62px`, zero horizontal overflow, 11 nodes/20 edges, visible business warning/primary CTA, contained node bubble, centered popup, and retained/collapsed completion review below the map. These screenshots/geometry are historical capture evidence; no fresh 1440×900 browser replay was completed on current source `2bcbf90`.
- **B — Receivables:** the previous capture at 390×844 showed the Wallet/Lucide icon instead of the broken emoji; one-line “LƯU KHOẢN THU”; `44px` Save/Cancel; visible Cancel; `828px` sheet; empty validation held the form open and Cancel closed it. No payment intent or real transaction. Runtime `payPending` was not entered; the C2C DOM flow previously covered visible pending, identity, duplicate protection and readback. This is historical prior-source evidence, not a new capture on `2bcbf90`.
- **C — mobile targets:** previous capture measured primary attention CTA `40px`; secondary controls `36–40px`; zoom/Fit/Readable `40px`; bubble close `36px`; stage task `58.48px`; no adjacent hitbox overlap. Historical only; no new current-source geometry capture.
- **D — separate verdicts:** previous successful run used CDP `touchStart` + 12 touch moves + `touchEnd`, observed `pointerType=touch`, map transform and ON BOARD node moved `+269px`, no accidental selection (`TOUCH_PAN_VERDICT=PASS`). Separate isolated Mongomock blank→`2026-10-04`→reload/readback was `TAP_SAVE_READBACK_VERDICT=PASS`. Both previous PASS results are retained as historical. **Current verdicts are `TOUCH_PAN_VERDICT=NOT_VERIFIED` and `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`**: after workspace resume the fresh staging app rendered the auth gate before the shell; the earlier venv/Chromium runtime was not present. No current replay/write occurred; no auth fixture or product auth bypass was added.
- **E — evidence reconciliation:** `state.json`, `metrics.json`, README and this reconciliation now identify the current source/dist, separate historical capture outcomes from current verification, and retain independent release blockers. The original raw metrics JSON was truncated during the failed workspace-resume restore attempt; the current metrics explicitly labels its previous-successful-run measurements as transcribed from the preserved capture summary/screenshots, not a fresh raw trace.
- **Current focused verification:** after evidence/dist commit `754a619f…`, `npm run typecheck`, Vite build (1936 modules), executable-process scan and clean `git diff --exit-code -- component/dist` all passed. Hook transition and zero-node DOM passed. C2C Steps 1–3 pass; Step 4 finance-tab assertion fails identically on pre-repair dist. Payment-trust/amount tests fail before payment on missing `LO-0308` preconditions, likewise reproduced on pre-repair dist. The LOGI-197 clarity fixture generator did not run because system Python lacks Streamlit. No full pytest or 21-route audit. Current Actions CI is `NOT_TRIGGERED`; historical run `38683678222` at `1889d2a…` is not current-source CI.

**Release/gate disposition:** current independent reviewer handoff is pending. Do not self-sign Supervisor PASS. Owner visual UAT follows only after Independent Review PASS. Preserve the independent auth/bootstrap/finance-coverage gaps and reproduced snapshot retry-idempotency defect documented below; this visual repair does not waive or repair them. `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`; `FULL_GOAL_199=IN_PROGRESS`.

## Scope and provenance

- Original baseline: `main@5c6642a339ec53fe4cc300b15f665e2cd5384bca`.
- Fresh worktree was clean on the fixed Arena branch. No previous uncommitted mobile patch existed here.
- Restored pushed preview `d96d951`, merged integration `f0aec79`. The merge's **only conflicts were evidence files**, retained preview side temporarily and regenerated by Chromium. No blanket ours/theirs source resolution. Source build/typecheck/scan verified; T1–T4 not reimplemented.
- Product merge commit: `246d199fb9c7ced8b2ce03811f541279b2213ca4`. Only the session's `arena/d8927583-logistics-work-desk-arena` may be pushed. Legacy `ct/logi199-int198-preview` intentionally remains at `d96d951`.
- Authority: [#197](https://github.com/7roger89-web/logistics-work-desk-arena/issues/197), later Owner persistent-split correction dated 13/10 carried in #198, and [fresh independent review](https://github.com/7roger89-web/logistics-work-desk-arena/pull/198#issuecomment-6184306764). The later correction supersedes **both** old six-step #186 and compact default/old summary cards; it does not remove backend truth or stage-scoped document contracts.

## Exactly five prior baseline-new failures

Original test IDs are retained for traceability; each replacement has explicit rationale in source. No tests deleted or skipped to pass CI.

| Test ID | Old requirement disposition | Repair and meaningful proof |
|---|---|---|
| `test_journey_super_goal_186.py::SixPhaseContract::test_exact_beginner_phase_labels_exist` | **SUPERSEDED** — six stages conflict with #197 and later persistent-map correction | Tests persistent split, always-mounted map, absence of obsolete phase/summary cards, retained mode-neutral region scope and Công việc/Chứng từ. Runtime #197 DOM tests stage docs/customer scope. |
| `test_journey_visual_fidelity_190.py::JourneyDensity::test_focus_shell_geometry_is_bound_to_scrollbar_free_reference_width` | **REPAIRED** — pinning old 451px summary composition/add-module marker is stale; responsive business workspace and module access remain valid | Tests small-map/flexible side constraints, responsive rule, existing modules + attachment disclosure. Browser measures real overflow/clipped controls at 1440/390. |
| `...JourneyDensity::test_fresh_zero_node_shell_is_compact` | **SUPERSEDED** — old fixed 500/430 canvas is not zero-node acceptance authority | Tests truthful empty placeholder, unknown position, exactly one primary CTA, no fabricated map/phase nodes, retained profile children; same-instance zero↔populated hook DOM regression. |
| `...JourneyDensity::test_global_workspace_reuses_collapsed_map_rail` | **SUPERSEDED** — Owner explicitly rejected replacing visible map with rail | Tests global open leaves persistent map mounted and hosts original children/tabs; #197 DOM verifies map after opening global workspace. |
| `...JourneyDensity::test_populated_default_restores_original_composition` | **SUPERSEDED** — five old summary cards/auto-quick default no longer approved | Tests overview + persistent map, quick/stage transitions, canonical problem/primaryAction, no old cards. T6 real node click→workspace→writer→readback. |

**Retained unchanged:** customs declaration≠clearance, GNT≠paid, unknown finance≠0, completion review not CLOSED/scoring, canonical Attention/owner responsibility, detailed nodes, RBAC writer/version guard, existing module and stage document interactions.

## Map readability proof (not an overflow waiver)

- Reuses existing transform/pointer/wheel controls, geometry and canonical node/edge payload. No library/router/store added.
- Initial scale **100%**, node titles **16px**; focus is a real selected/problem/current/first node. Position/status is never invented. Manual pan/zoom is preserved across ordinary rerenders.
- Explicit **Fit Journey** is an overview (~27% for FCL in 340px), **Đọc rõ** returns to reading scale. Legend folds into existing native details; controls wrap within the narrow column. Desktop retains map-left/business-right; mobile uses the existing vertical arrangement, width corrected to 100%.
- T6 challenges initial scale *before* invoking reset, real drag, no accidental selection, Fit entire canvas inside viewport, zoom increase, reading-scale restore. Screenshots:
  - `desktop-map-A-fit.png`, `desktop-map-B-readable.png`
  - `mobile-map-A-fit.png`, `mobile-map-B-readable.png`
- Fit is intentionally unsuitable for reading all labels; it is not the default and is not relabelled a legibility PASS.

## T5 / T6 boundaries

- Policy title wraps fully (including “Bộ Thông Tin Truyền Thông”), external icon remains inside card. Browser asserts title fits/not nowrap/icon bounds, not just page width.
- Be Vietnam Pro / IBM Plex Mono normal Latin+Vietnamese WOFF2 subsets bundled with SIL licenses. Existing remote-only font CSS was not sufficient in isolated shadow-root staging. Document FontFace registration gives actual loaded font receipts without network dependency; no npm/runtime dependency or legal-export font change. Audit normalizes browser-quoted family names before checking loaded status.
- Audit **21 distinct screens × 2 viewports**, fails on small visible normal body text <12px, clipped controls, page/shell overflow, route-not-reached/digest and page errors. Three legacy redirects are explicitly source-tested to separately audited destinations, not counted as screens. Not a claim to cover every detail-record/modal subroute.
- Primary fact popup 1–5 existing fields (never invent a field to reach two); CFS extras stay editable behind Chi tiết phụ. Pure projection test plus real browser expand/input-enabled checks. No removal of business evidence.
- Six variants at **both** 1440×900 and 390×844: SEA FCL/LCL, AIR direct/consolidated, ROAD FTL/LTL; UI on-board write and reopen readback date `2026-10-03`, actual canonical writer in isolated mongomock. Not external carrier/GPS/EDI proof.
- Local focused suite: **281 passed**; current-bundle DOM #197 and hook transition PASS; official typecheck/Vite/scan PASS. Local Python 3.11, Chromium 153 via temporary npm-provided binary; final Actions supplies independent environment Python 3.12 / its Playwright Chromium, not an independent human reviewer.

## Existing release risk — baseline failures are NOT waived

Same-runner local full suite: main **31 failed / 1807 passed / 45 skipped / 1 collection error**, integrated **31 failed / 1873 passed / 44 skipped / 1 collection error**; **zero new failed IDs**. Actions parity receipt and both ID lists are authoritative for its exact SHA. Skips differ because mode runtime coverage now executes an existing case.

| Area | Observed failure and bounded diagnosis | Release disposition |
|---|---|---|
| Auth/RBAC | Whole-suite unknown-role test fails; identical single test passes in clean process. Focused auth/default-fail-closed + role matrix + financial-write-safety/comparator: 86 pass, 6 skip, 1 snapshot failure. Old mounted support tests import removed `_visible_routes`, `has_permission` / `refresh_core_data` surface. | **INCOMPLETE** runtime authenticated-role coverage; ordering/fixture contamination and stale oracles likely, not proof of authorization bypass. No AUTH_REQUIRED/permission production changes in this continuation. Reviewer must not infer release safety from parity. |
| First-admin/bootstrap | Existing tests see login rather than bootstrap, including `test_session_truth_repair`; baseline-identical. | **BLOCKED for release certification** until bootstrap fixture/real authenticated path independently checked. No live user store/prod accounts touched. |
| Finance dashboard/reconciliation | Missing `ROUTES` collection import and `refresh_core_data` patches prevent old zero-write UI oracles from running. | **COVERAGE GAP**, not a financial-mutation PASS. Finance authority unchanged. |
| International payment snapshot | Existing full-suite mock accepts tampered second insert because mock lacks required unique index; alone it fails earlier on missing writer permission. Bounded authorized+indexed probe in `risk-probes/snapshot_indexed_authorized.py` rejects tamper, stores exactly one row, but same-payload retry returns false. **Exactly reproduced on baseline and branch** (`snapshot_main.json`, `snapshot_branch.json`). Probe intentionally exits 1 for failed idempotency assertion. | **PRE-EXISTING REPRODUCED DEFECT / release risk**, not repaired in UI goal. Investigate idempotency/fingerprint handling separately; do not waive or claim live indexes certified. Required index definition is `core/database.py` `uq_contract_intl_snapshot_id`; no production index command run. |
| Other baseline | Old anchor targets expect lay-hang/nhap instead of current van-tai; service catalog and exact field whitelist pins; ZIP byte comparison depends on timestamp; legacy screen smoke/projection differences. | Retained failed IDs, no broad deletion/refactor. May require separate acceptance reconciliation, not presumed harmless. |

Probe reproduction (isolated only): `PYTHONPATH=<checkout> <venv-python> evidence/logi-199-t6/risk-probes/snapshot_indexed_authorized.py`. No credential/real URI required or accepted by this probe.

## Gates / learning

`FINAL_VERDICT=INCOMPLETE` for full GOAL/release; bounded source/browser checks do not grant acceptance. Independent reviewer gate remains **PENDING**, Owner UAT **NOT_CLAIMED**, main/production untouched, no merge/deploy/closing review. Final exact CI/HEAD receipt is in existing `docs/goals/LOGI-APP-RENEWAL-01/state.json`.

`LEARNING_RECONCILIATION=CANDIDATE`: trigger = font acceptance in shadow-root/offline UI. Correction = challenge actual loaded FontFaceSet and rendered layout, not only font-family strings or overflow. Evidence = prior remote-only CSS vs local loaded-font audit and screenshots. Non-authoritative candidate only, no promotion into law/skill.
