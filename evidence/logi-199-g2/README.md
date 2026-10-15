# LOGI-APP-RENEWAL-01 — LOGI-199 G2 review repair evidence

## Current evidence boundary

This packet covers only the latest bounded repair on the fixed branch `arena/bb243332-logistics-work-desk-arena`. It does not redo G0–G5, certify the whole goal, self-sign Supervisor PASS, or replace Owner UAT. The only visual authority is `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`, SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.

- Latest zero-node follow-up source/dist commit: `1ecffa0a4dc3eff0141554a808e39e7fba109ebe`.
- Prior G2 evidence checkpoint commit (historical baseline): `754a619f30affd1c18753b50f78d917bb2db5944`.
- Latest official source-built UI: `component/dist/logi-shell.js` SHA-256 `2143711b22a9aad6aeed902457e450432902a8ce178dd561a2890e48870a4adc`; `component/dist/logi-shell.css` SHA-256 `bcf51682b4bdf799f1267364259f95d3f8417184afc3a3b90875679fa8ddb65a`.
- **Prior G2 evidence provenance:** the displayed before/after screenshots and successful touch/save-readback run are from the previous workspace snapshot at source `d77446e7b5ff03cfde9c79c6013d12a4b0a9c3ba` and CSS hash `1b87f972…`. The resumed workspace's earlier source build was `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7` with CSS `6973bae4…`. The 2026-10-15 zero-node follow-up is a separate current source/dist build at `1ecffa0a4dc3eff0141554a808e39e7fba109ebe`, documented below. The earlier fresh replay hit the login gate before the component loaded. Do not present prior runtime PASS measurements as current-source verification.
- Current capture runtime: no usable Chromium executable/venv is present after workspace resume. No fresh mock write or real payment occurred in the failed replay. No auth bypass fixture or extra framework was added.
- Full reconciled metrics and provenance: `metrics.json`; reproducible flow: `capture_journey_flow.py`; reviewer packet: `REVIEWER_HANDOFF.md`.
- The source/dist/evidence commits are pushed to the fixed branch. The attempted GitHub issue #199 handoff comment was blocked with `Resource not accessible by integration`; the Independent Reviewer has not received a posted comment.

## A — Desktop G2 layout (1440×900)

The pre-repair screenshot and measurements are under `before/`. In the **previous successful capture** (source `d77446e7…`), at the same 1440×900 viewport, map viewport height increased from `635px` to `780px` (`+145px`) and its top moved from `y=208.63px` to `y=106.62px` (`−102px`). The 780px height is viewport-relative CSS, not a fixed 780px rule. Identity, business attention, CTA and toolbar share compact chrome; the map reaches `y=886.62px`. “Rà soát trước khi kết thúc lô” remains present, collapsed, and below the map. Horizontal overflow is `0px`; 11 nodes and 20 edges remain. These geometry results are historical capture evidence, not a fresh browser measurement on the zero-node follow-up source `1ecffa0`.

| State | Screenshot |
|---|---|
| Before repair | `before/desktop-01-journey-initial.png` |
| After, full map | `desktop-01-journey-initial.png` |
| After, node-attached task bubble | `desktop-02-node-bubble.png` |
| After, centered task popup | `desktop-03-task-popup.png` |

The business warning (“Bổ sung số tờ khai nhập khẩu.”), reason, primary “XỬ LÝ” CTA, toolbar and map utilities remain rendered. Bubble stays within the map and the task popup is centered (`0px` center error).

## B/C — Mobile layout, targets, and Receivables (390×844)

The previous successful 390×844 capture measured the map at `549px` high with `0px` horizontal overflow and top `y=269.94px` (16px lower than its immediate pre-repair capture). Primary CTA height was `40px`; secondary identity/toolbar buttons `36px`; zoom and Fit/Readable controls `40px`; bubble close `36px`; stage-task action `58.48px`. Adjacent toolbar/zoom hitboxes did not overlap. Touch taps changed/restored zoom; opening/closing Global Workspace did not change zoom or select a node. These measurements are historical until replayed on current source.

Receivables at 390×844 (previous successful capture, source `d77446e7…`):

- Before: `💾 LƯU KHOẢN THU`, two text lines, `48px` Save/Cancel targets.
- After: Lucide Wallet icon (no emoji), “LƯU KHOẢN THU” on one text line, `44px` Save and Cancel targets; Cancel remains visible. Popup height is `828px`.
- Screenshots: `before/mobile-receivables-pay-sheet.png`, `mobile-receivables-pay-sheet.png`, and `mobile-receivables-validation.png`.
- Empty-amount validation remained visible, the sheet stayed open, the amount stayed blank, and Cancel closed the sheet. This validation path emitted no payment intent; no money transaction was created. Runtime `payPending` was not entered because no transaction was sent. The historical current-bundle C2C DOM flow exercised visible pending, disabled submit, stable request identity, duplicate-submit guard and authoritative readback. These facts are not a fresh browser replay on the zero-node follow-up source `1ecffa0`.

## D — Touch-pan and isolated save/readback

`capture_journey_flow.py` uses CDP `Input.dispatchTouchEvent` (`touchStart`, 12 multi-step `touchMove`s, `touchEnd`), not mouse drag. In the **previous successful capture** on source `d77446e7…`, Chromium observed touch events and pointer events with `pointerType="touch"`; transform `x` and the ON BOARD node each moved `+269px`, and selection stayed empty. That run's `TOUCH_PAN_VERDICT=PASS` is historical. On the latest source `1ecffa0`, `TOUCH_PAN_VERDICT=NOT_VERIFIED`; the earlier fresh replay stopped at the login gate before the shell rendered, and this zero-node follow-up could not start staging. No current-source touch interaction occurred.

The prior separate Mongomock run started with an empty ON BOARD date, tapped node/task/Save, reloaded, and read back `2026-10-04`. Its `TAP_SAVE_READBACK_VERDICT=PASS` is historical. On latest source `1ecffa0`, `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`; no fresh mock write happened after the workspace resumed. No real backend or payment write occurred. The earlier Save button did not display backend confirmation during the short post-tap window; the post-reload readback matched. The current branch did not add an auth fixture or disable auth in product code.

## Prior focused verification and known pre-existing test oracles (source 2bcbf90)

- At prior source commit `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7` and dist/evidence commit `754a619f30affd1c18753b50f78d917bb2db5944`: post-commit `npm run typecheck`, Vite 8.2.2 build (1936 modules), `npm run scan` and clean dist sync all PASS. `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`; built JS/CSS hashes match that bundle (`19674586…` / `6973bae4…`).
- `dom_hook_transition_197.mjs`: PASS on that prior source-built bundle in both zero→populated and populated→zero directions.
- `dom_acceptance_journey_fresh_188.mjs`: PASS on that prior source-built bundle's zero-node split view (one CTA, zero writes). JSDOM prints a non-fatal `scrollTo` warning. The latest full-width result is recorded in the follow-up section below.
- `dom_acceptance_c2c.mjs`: Steps 1–3 PASS (receivables/totals, request identity, duplicate absorption, visible pending, refusal/retry and authoritative readback); Step 4 fails on the legacy finance-tab assertion after “Mở lô”. The exact same assertion failed against pre-repair dist.
- `dom_acceptance_payment_trust.mjs` and `dom_acceptance_amount_integrity.mjs`: fail before payment at the `LO-0308` fixture/navigation preconditions; both were reproduced identically against pre-repair dist. These are not reported as passes; payment logic was not changed.
- `dom_acceptance_logi197_journey_clarity.mjs` did not run: its fixture generator requires `streamlit`, which is not installed in the system Python after workspace resume. No product assertion ran.
- Current `TOUCH_PAN_VERDICT=NOT_VERIFIED` and `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. Previous successful capture results remain explicitly historical; the fresh capture stopped at the auth gate before the shell, and no fresh touch/write occurred.
- `GITHUB_ACTIONS_CI=NOT_TRIGGERED` because no checked-in push workflow includes the fixed branch. Historical T6 run `38683678222` at source `1889d2a…` is not current-source verification.
- No full pytest, 21-route run, merge to main, or production deploy. The system Python has no pytest; the user’s bounded slice excludes a full-suite rerun.

## Historical artifacts and gates

Screenshots moved under `before/legacy-g2/` and `before/legacy-metrics-pre-199-repair.json` are explicitly pre-repair. The old mobile “touch” claim is not valid proof because its script used `page.mouse`. The prior `d774…` CDP touch PASS is separately marked historical; the current top-level `TOUCH_PAN_VERDICT` is `NOT_VERIFIED`.

`NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`; `FULL_GOAL_199=IN_PROGRESS`. Independent review remains pending; Owner visual UAT is not claimed and follows only after Independent Review PASS. Authentication/bootstrap/finance coverage gaps and the reproduced snapshot retry-idempotency blocker remain separate release blockers.

## LOGI #199 zero-node Journey split-layout follow-up — 2026-10-15

This is the **remaining zero-node exception only**, on fixed branch `arena/bb243332-logistics-work-desk-arena`. It does not roll back G0–G5, change the populated Journey layout, or re-open previously accepted G2 map-first, Vietnam chart, mobile CTA, Receivables, or gesture behavior. Product/source/dist/test commit: `1ecffa0a4dc3eff0141554a808e39e7fba109ebe`.

### Layout and acceptance status

| Required status | Result | Evidence boundary |
|---|---|---|
| `POPULATED_MAP_FIRST` | **PASS — preserved** | Existing populated branch is unchanged; same-instance hook DOM transitions into the populated map-first workspace and renders its real fixture nodes. Exact `T6-FCL` 11-node browser replay is **NOT_VERIFIED**. |
| `ZERO_NODE_FULL_WIDTH` | **PASS** | Current official-dist JSDOM acceptance passes for both `journey.nodes=[]` and a missing Journey. It asserts the full-width map-first canvas, truthful “Chưa có sơ đồ Journey” / “Chưa xác định” / missing-profile status, no fake nodes or phase cards, one “BỔ SUNG HỒ SƠ” CTA, existing editor inside Global Workspace, and zero business writes. JSDOM proves behavior/DOM contracts, not viewport geometry. |
| `OLD_SPLIT_LAYOUT_ACTIVE` | **NO** | Old small-map split CSS and zero-state right panel/root are absent; DOM acceptance asserts no old class or split root. |
| Browser desktop `1440×900` | **NOT_CAPTURED / BLOCKED** | No current-source screenshots or geometry measurements. |
| Browser mobile `390×844` | **NOT_CAPTURED / BLOCKED** | No current-source screenshots or geometry measurements. |
| `T6-FCL` (11 nodes) browser result | **NOT_VERIFIED** | Do not substitute prior G2 screenshots/captures; they are historical. |

### Current focused verification and hashes

- `npm run typecheck` — **PASS**.
- `npm run build` — **PASS**, Vite 8.2.2, 1936 modules.
- `npm run scan` — **PASS**, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- Post-commit rebuild was deterministic; `git diff --exit-code -- component/dist` was clean (**dist sync PASS**).
- `tests.test_journey_super_goal_186` + `tests.test_journey_visual_fidelity_190` — **18/18 PASS**.
- `dom_acceptance_journey_fresh_188.mjs` — **PASS** for both `nodes=[]` and `journey absent`; JSDOM emits only a benign unimplemented `scrollTo()` warning.
- Hook-test bundle build + `dom_hook_transition_197.mjs` — **PASS** for zero→populated and populated→zero on the same mounted instance; no hook-ordering error.
- No full pytest or 21-route audit was run.

| File | SHA-256 |
|---|---|
| `component/src/components/ShipmentJourney.tsx` | `86b85d344614eb5524c814f605e77fb2926f10ff962ba044f53c14ebf77acf9d` |
| `component/src/index.css` | `aa8537c64ca6ed3e55f60475cae11ac37aa2a502e57274fa18d388c0a891bdcb` |
| `tests/component/dom_acceptance_journey_fresh_188.mjs` | `8fcadbf558e6b187bd9cc38951825ce2bd29a2858bcec91fb422026bb26e2c01` |
| `tests/component/dom_hook_transition_197.mjs` | `2be31388a5acb0e692a07d3def5a64f89a469a476ce19b1c569c40176b198f61` |
| `component/dist/logi-shell.js` | `2143711b22a9aad6aeed902457e450432902a8ce178dd561a2890e48870a4adc` |
| `component/dist/logi-shell.css` | `bcf51682b4bdf799f1267364259f95d3f8417184afc3a3b90875679fa8ddb65a` |

### Browser/staging blocker

The exact T6 staging launcher was attempted with `MONGO_URI` unset. It stopped before staging seed/app start at `ModuleNotFoundError: mongomock`; system Python also lacks `streamlit` and `pymongo`. No staging write occurred. Node Playwright/Playwright Core and a Chromium/Chrome executable are not installed/present in the checked runtime paths. The existing T6 browser runner requires `AUTH_REQUIRED=false`, so it was **not used**. The real app defaults to fail-closed `AUTH_REQUIRED=true`; additionally, the launcher sets `staging.support` while the sandbox seed's users are `admin`, `thuhang`, and `minhtu`, so existing revalidation can keep the real app at its login gate. No production auth was changed, no auth bypass or new fixture/framework was added, and no production data was used. Browser screenshots were not generated.

### Gesture/readback and release gates

`TOUCH_PAN_VERDICT=NOT_VERIFIED`; `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. Neither was replayed on this source; no write occurred in the failed staging attempt. `Independent Review=PENDING`; `Owner UAT=NOT_RUN`. `NO_MERGE_MAIN=YES`; `NO_DEPLOY=YES`; unrelated auth/bootstrap/finance/snapshot-idempotency blockers remain intact.

### GOAL / PROGRESS / CURRENT / NEXT / BLOCKERS

- **GOAL:** close only the LOGI #199 zero-node Journey split-layout exception while preserving the accepted populated path and G2 work.
- **PROGRESS:** zero-node full-width map-first UI and acceptance assertions are implemented; source, official dist, typecheck, build, scan, fresh DOM, hook-transition DOM, and dist sync pass.
- **CURRENT:** `POPULATED_MAP_FIRST=PASS` (source/DOM preservation); `ZERO_NODE_FULL_WIDTH=PASS` (JSDOM); `OLD_SPLIT_LAYOUT_ACTIVE=NO`. T6-FCL and zero-node desktop/mobile browser evidence remain **NOT_VERIFIED**, not claimed.
- **NEXT:** restore an authorized isolated staging/browser runtime without weakening auth; capture `T6-FCL` 11 nodes and the zero-node state at `1440×900` and `390×844`, then request Independent Review. Owner UAT remains gated on review.
- **BLOCKERS:** missing Streamlit/Mongomock/PyMongo and Playwright/Chromium; existing staging actor/auth revalidation mismatch; Independent Review pending; Owner UAT not run. Previously tracked unrelated release blockers are unchanged.

### OE gate for this bounded slice

`SIMPLER_PATH=YES`; `MATERIAL_PROGRESS=YES`; `NECESSITY=YES`; `CORE_BEFORE_SUPPORT=YES`; `SMALLER_VERIFIABLE_SLICE=YES`; `OE_VERDICT=DO_IT` for this zero-node-specific layout/test change only. No framework, module, design system, or workflow was added.
