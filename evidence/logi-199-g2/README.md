# LOGI-APP-RENEWAL-01 — LOGI-199 G2 review repair evidence

## Current evidence boundary
This packet covers only the bounded LOGI #199 empty-map pointer correction and current-source G2 replay. It does not redo G0–G5, certify the full goal, self-sign Supervisor PASS, or replace Owner UAT. The visual authority remains `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`, SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.

- Published source candidate on the fixed branch: `1e899553cc1ad7dbd720eb805e061ec61ae0871a`.
- **Raw browser-capture SHA:** `751f64f5129637eef4fb74515afdf7fa15ca9deb` (from `current-source/metrics.json`). This commit object was absent from the resumed local clone and GitHub returned HTTP 422 “No commit found”. Preserve this raw value; do not rewrite the raw capture.
- Current official dist rebuilt from the published candidate: JS SHA-256 `3b650f8f2d7171113ddcd927f885133898d60d5cd22dece16a95dfc092089e5c`; CSS SHA-256 `412f27aa81d65b5c0a3bafadd98f3c3123ee6a2d5ec5ea4957ca3084409917fb`. Both match the raw browser metrics. The capture-harness SHA also matches (`c93ea253ad71dc6c0524bb6945e4e1e1a7a0c6cf638993db7fdac27547cfa06a`). Commit-ID identity mapping remains **NOT_VERIFIED** and is disclosed for Independent Review; no Chromium replay was repeated after the workspace restore.
- Current-source raw browser metrics and screenshots are in `current-source/`; the raw JSON SHA-256 is `8d0f8e4a0fbe8746c72e4d3f79d2d19b223d83e76415cec5eee3c65c46887193`. The raw file records `CAPTURE_VERDICT=PASS`, Chromium 153.0.8010.0, and the capture source SHA above.
- Staging proof: `STAGING_ISOLATION_PROOF=PASS transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO production_client=NO` appeared before fixture creation. Mongo URI/database/secrets inputs were empty; test-only `AUTH_REQUIRED=false` was used only by the fail-closed staging launcher. Production auth/app code, production credentials, and production data were untouched.
- Current local checks on published candidate `1e89955`: typecheck/build/scan pass; dist hashes match; focused official-dist DOM acceptance and same-instance hook-transition checks pass. A prior focused Python slice reported 27 passed; no full-suite or 21-route rerun.
- `npm ci` installed the locked dependencies and reported one high-severity audit advisory. It was not independently triaged or remediated in this bounded task.
- `INDEPENDENT_REVIEW=PENDING`; `OWNER_UAT_READY=NO`; no Owner UAT, merge, or production deploy is claimed. The previous issue-comment permission failure is not a product/release blocker; no permission repair is requested.

## P2P preflight receipts for this continuation

`P2P_LAW_SOURCE=LOCAL_PORTABLE`

`LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`

`EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb` (advisory/non-authoritative portable ACTIVE record).

`p2p-skill-consumption-receipt/1`

```json
{"schema":"p2p-skill-consumption-receipt/1","skills":[{"id":"p2p-uiux","path":".agents/skills/p2p-uiux/SKILL.md","sha256":"98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2","consumption":"READ_AND_APPLIED"}]}
```

`INITIAL_PLANNING_CLASSIFICATION=UIUX`; `FINAL_ROUTING_CLASSIFICATION=UIUX`.

## A — Desktop G2 layout (1440×900)

The pre-repair screenshot and measurements are under `before/`. In the **previous successful capture** (source `d77446e7…`), at the same 1440×900 viewport, map viewport height increased from `635px` to `780px` (`+145px`) and its top moved from `y=208.63px` to `y=106.62px` (`−102px`). The 780px height is viewport-relative CSS, not a fixed 780px rule. Identity, business attention, CTA and toolbar share compact chrome; the map reaches `y=886.62px`. “Rà soát trước khi kết thúc lô” remains present, collapsed, and below the map. Horizontal overflow is `0px`; 11 nodes and 20 edges remain. These are the earlier G2 comparison measurements; the current 2026-10-15 T6-FCL and zero-node geometry is captured separately in `current-source/metrics.json` and summarized in the final follow-up below.

| State | Screenshot |
|---|---|
| Before repair | `before/desktop-01-journey-initial.png` |
| After, full map | `desktop-01-journey-initial.png` |
| After, node-attached task bubble | `desktop-02-node-bubble.png` |
| After, centered task popup | `desktop-03-task-popup.png` |

The business warning (“Bổ sung số tờ khai nhập khẩu.”), reason, primary “XỬ LÝ” CTA, toolbar and map utilities remain rendered. Bubble stays within the map and the task popup is centered (`0px` center error).

## B/C — Mobile layout, targets, and Receivables (390×844)

The previous successful 390×844 capture measured the map at `549px` high with `0px` horizontal overflow and top `y=269.94px` (16px lower than its immediate pre-repair capture). Primary CTA height was `40px`; secondary identity/toolbar buttons `36px`; zoom and Fit/Readable controls `40px`; bubble close `36px`; stage-task action `58.48px`. Adjacent toolbar/zoom hitboxes did not overlap. Touch taps changed/restored zoom; opening/closing Global Workspace did not change zoom or select a node. The fine-grained control-target measurements above remain from the earlier G2 capture; current 390×844 map geometry, horizontal overflow, real touch-pan and save/readback are captured in the final current-source follow-up below.

Receivables at 390×844 (previous successful capture, source `d77446e7…`):

- Before: `💾 LƯU KHOẢN THU`, two text lines, `48px` Save/Cancel targets.
- After: Lucide Wallet icon (no emoji), “LƯU KHOẢN THU” on one text line, `44px` Save and Cancel targets; Cancel remains visible. Popup height is `828px`.
- Screenshots: `before/mobile-receivables-pay-sheet.png`, `mobile-receivables-pay-sheet.png`, and `mobile-receivables-validation.png`.
- Empty-amount validation remained visible, the sheet stayed open, the amount stayed blank, and Cancel closed the sheet. This validation path emitted no payment intent; no money transaction was created. Runtime `payPending` was not entered because no transaction was sent. The historical current-bundle C2C DOM flow exercised visible pending, disabled submit, stable request identity, duplicate-submit guard and authoritative readback. These facts are not a fresh browser replay on the zero-node follow-up source `1ecffa0`.

## D — Touch-pan and isolated save/readback

`capture_journey_flow.py` uses CDP `Input.dispatchTouchEvent` (`touchStart`, 12 multi-step `touchMove`s, `touchEnd`), not mouse drag. In the **previous successful capture** on source `d77446e7…`, Chromium observed touch events and pointer events with `pointerType="touch"`; transform `x` and the ON BOARD node each moved `+269px`, and selection stayed empty. That earlier run's `TOUCH_PAN_VERDICT=PASS` is historical. The later raw current-source capture at SHA `751f64f5129637eef4fb74515afdf7fa15ca9deb` separately records a fresh CDP touch-pan PASS; its metrics and screenshots are summarized in the final follow-up below. The raw commit object is not fetchable, and the published candidate's commit-ID mapping is disclosed for review.

The prior separate Mongomock run started with an empty ON BOARD date, tapped node/task/Save, reloaded, and read back `2026-10-04`. Its `TAP_SAVE_READBACK_VERDICT=PASS` is historical. The later raw current-source capture separately records an isolated Mongomock ON BOARD save/reload/readback PASS for `2026-10-04`, as summarized below. No real backend or payment write occurred. The earlier Save button did not display backend confirmation during the short post-tap window; the post-reload readback matched. The current branch did not add an auth fixture or disable auth in product code.

## Prior focused verification and known pre-existing test oracles (source 2bcbf90)

- At prior source commit `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7` and dist/evidence commit `754a619f30affd1c18753b50f78d917bb2db5944`: post-commit `npm run typecheck`, Vite 8.2.2 build (1936 modules), `npm run scan` and clean dist sync all PASS. `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`; built JS/CSS hashes match that bundle (`19674586…` / `6973bae4…`).
- `dom_hook_transition_197.mjs`: PASS on that prior source-built bundle in both zero→populated and populated→zero directions.
- `dom_acceptance_journey_fresh_188.mjs`: PASS on that prior source-built bundle's zero-node split view (one CTA, zero writes). JSDOM prints a non-fatal `scrollTo` warning. The latest full-width result is recorded in the follow-up section below.
- `dom_acceptance_c2c.mjs`: Steps 1–3 PASS (receivables/totals, request identity, duplicate absorption, visible pending, refusal/retry and authoritative readback); Step 4 fails on the legacy finance-tab assertion after “Mở lô”. The exact same assertion failed against pre-repair dist.
- `dom_acceptance_payment_trust.mjs` and `dom_acceptance_amount_integrity.mjs`: fail before payment at the `LO-0308` fixture/navigation preconditions; both were reproduced identically against pre-repair dist. These are not reported as passes; payment logic was not changed.
- `dom_acceptance_logi197_journey_clarity.mjs` did not run: its fixture generator requires `streamlit`, which is not installed in the system Python after workspace resume. No product assertion ran.
- This prior verification subsection describes the pre-restore candidate only. Its touch/save statuses were superseded by the preserved raw current-source capture below, which records `TOUCH_PAN_VERDICT=PASS` and `TAP_SAVE_READBACK_VERDICT=PASS`; those raw statuses remain tied to the unavailable recorded SHA `751f64f…`, with the published-candidate mapping disclosed for review.
- `GITHUB_ACTIONS_CI=NOT_TRIGGERED` because no checked-in push workflow includes the fixed branch. Historical T6 run `38683678222` at source `1889d2a…` is not current-source verification.
- No full pytest, 21-route run, merge to main, or production deploy. The system Python has no pytest; the user’s bounded slice excludes a full-suite rerun.

## Historical artifacts and gates

Screenshots moved under `before/legacy-g2/` and `before/legacy-metrics-pre-199-repair.json` are explicitly pre-repair. The old mobile “touch” claim is not valid proof because its script used `page.mouse`. The prior `d774…` CDP touch PASS is historical and separate from the later raw current-source CDP touch PASS documented below. The current-source raw touch/save verdicts are `PASS`; the captured commit SHA is unavailable remotely and the identity mapping is disclosed above.

`NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`; `FULL_GOAL_199=IN_PROGRESS`. Independent review remains pending; Owner visual UAT is not claimed and follows only after Independent Review PASS. Authentication/bootstrap/finance coverage gaps and the reproduced snapshot retry-idempotency blocker remain separate release blockers.

## LOGI #199 zero-node pointer repair and current-source replay — 2026-10-15

This is a bounded continuation of existing G2 work, not a redesign or G0–G5 rerun. Published source candidate: `1e899553cc1ad7dbd720eb805e061ec61ae0871a`. The current-source capture is preserved with its original recorded SHA `751f64f5129637eef4fb74515afdf7fa15ca9deb`. That old commit object is unavailable in the restored clone and GitHub; the source-equivalent changes were re-committed on top of remote HEAD `2ce7d92` and the official bundle rebuilt to the exact raw capture hashes. The raw source SHA is left unchanged, and commit-ID equivalence is **NOT_VERIFIED** for independent review. Do not claim the browser was recaptured on `1e89955`.

### Current browser evidence (real Streamlit + built component)

| Scenario | Result | Rendered/computed evidence |
|---|---|---|
| T6-FCL desktop 1440×900 | **PASS in raw capture** | 11 nodes/20 edges; map 1406×780 at y=106.62px; 0px horizontal overflow; no page errors. |
| T6-FCL mobile 390×844 | **PASS in raw capture** | 11 nodes/20 edges; map 374×549px; 0px horizontal overflow. |
| Real mobile touch-pan | **PASS in raw capture** | CDP `touchStart` + 12 `touchMove` + `touchEnd`; `pointerType=touch`; map and ON BOARD node each moved +269px; no accidental node selection/bubble. |
| T6-FCL ON BOARD save/reload/readback | **PASS in raw capture** | Tap node → task bubble → task editor; enter test date `2026-10-04`; explicitly tap Save; reload; read the date back. Post-reload stage and evidence are visible. No payment flow. Immediate backend-confirmation text was not visible in the short post-tap window; persisted readback is the proof. |
| SEA-188 zero-node desktop 1440×900 | **PASS in raw capture** | 0 nodes/edges; actual chart viewport fills 1406×780 map-first shell; chart data image loaded; computed cursor `default`, touch action `auto`; 0px overflow. Browser-observed pointerdown/move/up left transform unchanged. Exactly one truthful CTA opens the existing profile path; no non-read HTTP request. |
| SEA-188 zero-node mobile 390×844 | **PASS in raw capture** | 0 nodes/edges; viewport fills 374×549 shell; pointer transform unchanged, one CTA/editor/no-write checks pass; 0px overflow. |
| Missing-Journey property variant | **PASS official-dist DOM acceptance** | `journey.nodes=[]` and absent `journey` both pass truthful empty state, zero fabricated nodes/phases/statuses, one CTA, existing Global Workspace/Execution Profile path, no business write, and no empty-map pan. No separate real-browser screenshot for absent `journey`; browser screenshots use canonical `SEA-188` with `nodes=[]`. |

Raw values, viewport boxes, event counts, transforms, and screenshot provenance are in `current-source/metrics.json`. Current screenshots:

- Desktop: `current-source/desktop-t6-fcl-journey-initial.png`, `desktop-zero-node-initial.png`, `desktop-zero-node-execution-profile-editor.png`.
- Mobile: `current-source/mobile-t6-fcl-journey-initial.png`, `mobile-zero-node-initial.png`, `mobile-zero-node-execution-profile-editor.png`, `mobile-04-touch-pan-after.png`, `mobile-04-onboard-touch-editor.png`, `mobile-t6-fcl-onboard-touch-readback.png`.
- Node/bubble/task states: `current-source/desktop-t6-fcl-node-bubble.png`, `desktop-t6-fcl-task-popup.png`, `mobile-02-node-bubble.png`, `mobile-03-task-sheet.png`.

The selected Vietnam/Biển Đông/Hoàng Sa/Trường Sa asset was loaded as a data image in the capture. `SEA-188` was created through the canonical `shipment_create` path in isolated Mongomock with no mode, Incoterm, confirmed service scope, transport legs, or fabricated Journey stage. The UI shows the real missing-profile state and keeps current phase unconfirmed.

### Current verification and provenance

- Rebuilt the official dist from published source candidate `1e89955`; Vite 8.2.2, 1936 modules, JS/CSS hashes exactly match the raw browser capture (`3b650f8…` / `412f27a…`). Typecheck and scan pass; scan reports `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- Re-ran the two focused official-dist DOM acceptance variants (`nodes=[]`, `journey absent`) and `dom_hook_transition_197.mjs`; all pass. JSDOM emits a benign `Window.scrollTo()` not-implemented warning. The hook test passes zero→populated and populated→zero on the same mounted instance.
- Focused Python regressions previously reported **27 passed** against the raw capture candidate. Full pytest, 21-route audit, broad historic finance/payment oracles, and G0–G5 recertification were not run.
- Runtime log proved in-process Mongomock isolation before fixture creation; the only deliberate write was the disposable T6-FCL ON BOARD test date. No real DB/payment write occurred.
- Windows batch launcher was statically checked only; **Windows runtime NOT_RUN**.
- `npm ci` reported one high-severity audit advisory; no broad audit or dependency remediation was in scope.

### Review and release boundary

`INDEPENDENT_REVIEW=PENDING`; `SUPERVISOR_PASS=NOT_CLAIMED`; `OWNER_UAT=NOT_RUN`; `OWNER_UAT_READY=NO`; `FULL_GOAL_199=IN_PROGRESS`. The source candidate for review is `1e899553cc1ad7dbd720eb805e061ec61ae0871a`; reviewers should explicitly evaluate the raw-capture SHA reconciliation above. Existing auth/bootstrap/finance coverage and snapshot retry-idempotency blockers remain separate and unwaived. `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`.

OE gate: `SIMPLER_PATH=YES` (reuse existing map/launcher/tests); `MATERIAL_PROGRESS=YES`; `NECESSITY=YES`; `CORE_BEFORE_SUPPORT=YES`; `SMALLER_VERIFIABLE_SLICE=YES`; `OE_VERDICT=DO_IT` for this bounded fix. Broader redesign/framework/21-route ceremony is `SKIP_IT`.

### GOAL / PROGRESS / CURRENT / NEXT / BLOCKERS

- **GOAL:** finish the open LOGI #199 empty-map pointer and exact-source evidence handoff.
- **PROGRESS:** current raw desktop/mobile capture, rebuilt official dist, focused DOM tests and hook transitions are available and passing; the zero CTA opens the real profile path without a write.
- **CURRENT:** capture records source SHA `751f64f…`; published candidate is `1e89955…`; dist and capture-harness hashes match. Commit-ID equivalence remains **NOT_VERIFIED**, disclosed for review.
- **NEXT:** non-force push and verify the source/evidence/docs on the fixed branch; request Independent Review of only the open findings. Owner UAT stays closed until review PASS.
- **BLOCKERS:** independent review pending; GitHub remote push/readback pending; raw capture commit object unavailable (mapping disclosed); Windows runtime not run; unrelated release blockers remain unchanged.
