# Independent Review handoff — LOGI-APP-RENEWAL-01 / G2 repair

**Status:** request independent review of this exact source/dist checkpoint and evidence limitations. This is not a review verdict, Supervisor PASS, Owner UAT, or release approval.

- Fixed branch: `arena/bb243332-logistics-work-desk-arena`
- Current product-source commit: `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7`
- Current dist JS SHA-256: `19674586f24fa2f66484c26640519a489e94b8656dcccdc21faa9f96b30909a3`
- Current dist CSS SHA-256: `6973bae48887aefea59f09557f35922feafda5118a9a4875ae676c3ca86c7c4f`
- Sole visual authority: `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`, SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.
- Main evidence: `evidence/logi-199-g2/README.md`, `metrics.json`, `capture_journey_flow.py`, screenshots under this directory, and `evidence/logi-199-t6/RECONCILIATION.md`.

## A–C — visual evidence (historical capture)

The before/after screenshots and measurements were captured in the previous workspace snapshot at source `d77446e7b5ff03cfde9c79c6013d12a4b0a9c3ba`, JS `19674586…`, CSS `1b87f972…`. The current source commit is `2bcbf90…`; a fresh replay was not completed. Current source-built JS is byte-identical to that capture. The stable CSS is now `6973bae4…`; the rebuild removed a generated `.sm:space-y-2.5` rule absent from the current source, and not used on Journey/Receivables. Treat visual measurements below as previous-capture evidence, not a new current-source browser verdict.

- **Desktop G2, 1440×900:** old map `635px` → `780px` (`+145px`); top `208.63px` → `106.62px`; zero horizontal overflow; 11 nodes/20 edges; warning and primary CTA visible; bubble inside map; popup centered; completion review retained, collapsed below map.
- **Mobile, 390×844:** map `549px`, zero overflow; primary attention CTA `40px`; secondary controls `36–40px`; zoom/Fit/Readable `40px`; bubble close `36px`; task action `58.48px`; measured adjacent targets did not overlap.
- **Receivables:** prior capture showed no emoji, “LƯU KHOẢN THU” on one line, Save/Cancel `44px`, sheet `828px`; blank validation kept the sheet open and Cancel closed it. No `payment_record` or real transaction was created.

## D — touch pan and isolated ON BOARD write/readback

The previous successful capture used CDP `touchStart` + 12 multi-step `touchMove` + `touchEnd`; it observed `pointerType="touch"`, transform and ON BOARD node each moved `+269px`, and no node selection. It separately used isolated Mongomock to write a blank ON BOARD date as `2026-10-04`, reload, then read back the exact date. Historical results: `TOUCH_PAN_VERDICT=PASS`; `TAP_SAVE_READBACK_VERDICT=PASS`.

**Current verdicts:** `TOUCH_PAN_VERDICT=NOT_VERIFIED`; `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. After workspace resume, the fresh staging app showed the auth/login gate before the component rendered. The prior venv/Chromium executable was absent after the snapshot resumed. No auth fixture, auth bypass in product code, new framework, fresh write, or real payment was added. The original raw metrics JSON was lost during the snapshot restore attempt; `metrics.json` explicitly marks the previous run transcribed from its preserved summary and screenshots. Do not promote the prior PASS to current-source proof.

## Verification and limits

- Evidence/dist commit `754a619f30affd1c18753b50f78d917bb2db5944`; post-commit `npm run typecheck`, Vite build (1936 modules), scan and clean dist sync all PASS. Exact hashes are above.
- Current-bundle hook transition and zero-node DOM regressions PASS. C2C steps 1–3 PASS; its Step 4 finance-tab assertion fails as on pre-repair dist. Payment-trust/amount-integrity fail before payment at missing `LO-0308` fixture/navigation preconditions, likewise reproduced on pre-repair dist. The LOGI-197 clarity fixture did not run because the generator requires missing system-Python Streamlit. No payment logic changed. Exact outcomes are in `metrics.json`.
- `GITHUB_ACTIONS_CI=NOT_TRIGGERED`: no checked-in push-workflow filter includes the fixed Arena branch. Historical run `38683678222` at source `1889d2a…` is not current CI.
- Preserve the separate auth/bootstrap/finance-coverage gaps and reproduced snapshot retry-idempotency defect; this visual repair does not waive or repair them.
- No full pytest or 21-route audit was run. `FULL_GOAL_199=IN_PROGRESS`.

**Requested reviewer action:** assess A–E against the Owner oracle and exact current source/dist. Explicitly decide whether historical visual/runtime evidence is sufficient or current touch/save evidence must be recaptured. State any remaining failure. Do not treat this handoff as Owner UAT. `INDEPENDENT_REVIEW=PENDING`; `SUPERVISOR_PASS=NOT_CLAIMED`; `OWNER_UAT=NOT_RUN`; `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`.
