# LOGI-APP-RENEWAL-01 — LOGI-199 G2 review repair evidence

## Current evidence boundary

This packet covers only the latest bounded repair on the fixed branch `arena/bb243332-logistics-work-desk-arena`. It does not redo G0–G5, certify the whole goal, self-sign Supervisor PASS, or replace Owner UAT. The only visual authority is `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`, SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.

- Current product source commit: `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7`.
- Evidence/dist checkpoint commit: `754a619f30affd1c18753b50f78d917bb2db5944`.
- Current source-built UI: `component/dist/logi-shell.js` SHA-256 `19674586f24fa2f66484c26640519a489e94b8656dcccdc21faa9f96b30909a3`; `component/dist/logi-shell.css` SHA-256 `6973bae48887aefea59f09557f35922feafda5118a9a4875ae676c3ca86c7c4f`.
- **Evidence provenance:** the displayed before/after screenshots and successful touch/save-readback run are from the previous workspace snapshot at source `d77446e7b5ff03cfde9c79c6013d12a4b0a9c3ba` and CSS hash `1b87f972…`. After resuming on the pinned branch, the new source commit was built and the final CSS stabilized at `6973bae4…`; its only difference from the immediately prior bundle is a generated utility selector absent from the current Journey/Receivables source. A fresh replay after workspace resume hit the login gate before the component loaded; current `TOUCH_PAN_VERDICT=NOT_VERIFIED` and `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. Do not present the previous runtime PASS as current-source verification.
- Current capture runtime: no usable Chromium executable/venv is present after workspace resume. No fresh mock write or real payment occurred in the failed replay. No auth bypass fixture or extra framework was added.
- Full reconciled metrics and provenance: `metrics.json`; reproducible flow: `capture_journey_flow.py`; reviewer packet: `REVIEWER_HANDOFF.md`.
- The source/dist/evidence commits are pushed to the fixed branch. The attempted GitHub issue #199 handoff comment was blocked with `Resource not accessible by integration`; the Independent Reviewer has not received a posted comment.

## A — Desktop G2 layout (1440×900)

The pre-repair screenshot and measurements are under `before/`. In the **previous successful capture** (source `d77446e7…`), at the same 1440×900 viewport, map viewport height increased from `635px` to `780px` (`+145px`) and its top moved from `y=208.63px` to `y=106.62px` (`−102px`). The 780px height is viewport-relative CSS, not a fixed 780px rule. Identity, business attention, CTA and toolbar share compact chrome; the map reaches `y=886.62px`. “Rà soát trước khi kết thúc lô” remains present, collapsed, and below the map. Horizontal overflow is `0px`; 11 nodes and 20 edges remain. These geometry results are historical capture evidence, not a fresh browser measurement on source `2bcbf90`.

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
- Empty-amount validation remained visible, the sheet stayed open, the amount stayed blank, and Cancel closed the sheet. This validation path emitted no payment intent; no money transaction was created. Runtime `payPending` was not entered because no transaction was sent. The historical current-bundle C2C DOM flow exercised visible pending, disabled submit, stable request identity, duplicate-submit guard and authoritative readback. These facts are not a fresh browser replay on source `2bcbf90`.

## D — Touch-pan and isolated save/readback

`capture_journey_flow.py` uses CDP `Input.dispatchTouchEvent` (`touchStart`, 12 multi-step `touchMove`s, `touchEnd`), not mouse drag. In the **previous successful capture** on source `d77446e7…`, Chromium observed touch events and pointer events with `pointerType="touch"`; transform `x` and the ON BOARD node each moved `+269px`, and selection stayed empty. That run's `TOUCH_PAN_VERDICT=PASS` is historical. On current source `2bcbf90`, `TOUCH_PAN_VERDICT=NOT_VERIFIED` because the fresh replay stopped at the login gate before the shell rendered; no touch interaction occurred.

The prior separate Mongomock run started with an empty ON BOARD date, tapped node/task/Save, reloaded, and read back `2026-10-04`. Its `TAP_SAVE_READBACK_VERDICT=PASS` is historical. Current `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`; no fresh mock write happened after the workspace resumed. No real backend or payment write occurred. The earlier Save button did not display backend confirmation during the short post-tap window; the post-reload readback matched. The current branch did not add an auth fixture or disable auth in product code.

## Focused verification and known pre-existing test oracles

- Current source commit `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7`; dist/evidence commit `754a619f30affd1c18753b50f78d917bb2db5944`: post-commit `npm run typecheck`, Vite 8.2.2 build (1936 modules), `npm run scan` and clean dist sync all PASS. `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`; built JS/CSS hashes match the committed dist exactly (`19674586…` / `6973bae4…`).
- `dom_hook_transition_197.mjs`: PASS on the current source-built bundle in both zero→populated and populated→zero directions.
- `dom_acceptance_journey_fresh_188.mjs`: PASS on the current source-built bundle (zero-node split view, one CTA, zero writes). JSDOM prints a non-fatal `scrollTo` warning.
- `dom_acceptance_c2c.mjs`: Steps 1–3 PASS (receivables/totals, request identity, duplicate absorption, visible pending, refusal/retry and authoritative readback); Step 4 fails on the legacy finance-tab assertion after “Mở lô”. The exact same assertion failed against pre-repair dist.
- `dom_acceptance_payment_trust.mjs` and `dom_acceptance_amount_integrity.mjs`: fail before payment at the `LO-0308` fixture/navigation preconditions; both were reproduced identically against pre-repair dist. These are not reported as passes; payment logic was not changed.
- `dom_acceptance_logi197_journey_clarity.mjs` did not run: its fixture generator requires `streamlit`, which is not installed in the system Python after workspace resume. No product assertion ran.
- Current `TOUCH_PAN_VERDICT=NOT_VERIFIED` and `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. Previous successful capture results remain explicitly historical; the fresh capture stopped at the auth gate before the shell, and no fresh touch/write occurred.
- `GITHUB_ACTIONS_CI=NOT_TRIGGERED` because no checked-in push workflow includes the fixed branch. Historical T6 run `38683678222` at source `1889d2a…` is not current-source verification.
- No full pytest, 21-route run, merge to main, or production deploy. The system Python has no pytest; the user’s bounded slice excludes a full-suite rerun.

## Historical artifacts and gates

Screenshots moved under `before/legacy-g2/` and `before/legacy-metrics-pre-199-repair.json` are explicitly pre-repair. The old mobile “touch” claim is not valid proof because its script used `page.mouse`. The prior `d774…` CDP touch PASS is separately marked historical; the current top-level `TOUCH_PAN_VERDICT` is `NOT_VERIFIED`.

`NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`; `FULL_GOAL_199=IN_PROGRESS`. Independent review remains pending; Owner visual UAT is not claimed and follows only after Independent Review PASS. Authentication/bootstrap/finance coverage gaps and the reproduced snapshot retry-idempotency blocker remain separate release blockers.
