# LOGI-APP-RENEWAL-01 — current G2 repair reviewer handoff

**Status:** prepared for Independent Review; not a verdict, Supervisor PASS, Owner UAT, or release approval. Historical integration preview notes are preserved at `evidence/logi-199-t6/historical/REVIEWER_UPDATE-pre-G2-repair-20261015.md`; their old branch/source/CI must not be treated as current.

- Fixed branch: `arena/bb243332-logistics-work-desk-arena`
- Current source commit: `2bcbf90f9ef1ff665c8f1bfe2d09f1706cce51f7`
- Evidence/dist checkpoint commit: `754a619f30affd1c18753b50f78d917bb2db5944`
- Current dist JS SHA-256: `19674586f24fa2f66484c26640519a489e94b8656dcccdc21faa9f96b30909a3`
- Current dist CSS SHA-256: `6973bae48887aefea59f09557f35922feafda5118a9a4875ae676c3ca86c7c4f`
- Sole visual authority: `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`, SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.

## Evidence and provenance

- `evidence/logi-199-g2/REVIEWER_HANDOFF.md` — concise A–E review request and explicit limits.
- `evidence/logi-199-g2/README.md` — before/after desktop and mobile summary.
- `evidence/logi-199-g2/metrics.json` — current source/dist hashes, historical geometry and capture verdicts, current verification and blockers.
- `evidence/logi-199-g2/before/` — pre-repair images and baseline metrics. `before/legacy-g2/` and `before/legacy-metrics-pre-199-repair.json` are historical.
- `evidence/logi-199-t6/RECONCILIATION.md` — current repair receipt followed by historical T0–T6 receipts and separate release blockers.

The last successful browser capture is from the previous snapshot/source `d77446e7…` (JS hash `19674586…`, CSS hash `1b87f972…`). It measured the desktop map at `780px` (`+145px` vs pre-repair), mobile targets/Receivables one-line Save, CDP touch pan `+269px` without selection, and isolated Mongomock ON BOARD date save/reload/readback as `2026-10-04`. Those runtime results are historical, not current-source verification. The current source-built JS is byte-identical; stable rebuilt CSS is `6973bae4…` and differs from the prior CSS by a generated utility absent from the current Journey/Receivables source.

**Current verdicts:** `TOUCH_PAN_VERDICT=NOT_VERIFIED`; `TAP_SAVE_READBACK_VERDICT=NOT_VERIFIED`. After the workspace resumed on the pinned branch, a fresh staging run stopped at the auth/login gate before the component rendered. The earlier temporary Python/Chromium runtime was not present; no auth fixture/bypass or new framework was added. No fresh mock write or real payment occurred. The previous raw metrics JSON was truncated while restoring the workspace snapshot; `metrics.json` transparently distinguishes transcribed historical values from current verification.

Evidence/dist commit `754a619f30affd1c18753b50f78d917bb2db5944` is verified: post-commit typecheck/build/scan and clean dist sync PASS; hook transition and zero-node DOM PASS. C2C steps 1–3 pass with the same pre-repair Step 4 finance-tab failure; payment-trust/amount-integrity stop before payment on missing LO-0308 fixtures, reproduced against old dist. The LOGI-197 clarity fixture did not run because its generator needs system-Python streamlit. Exact outcomes are in `metrics.json`. `GITHUB_ACTIONS_CI=NOT_TRIGGERED` because no workflow filter includes the fixed branch. Historical Actions run `38683678222` at source `1889d2a…` is not current CI. No full pytest or 21-route run.

Preserve independent auth/bootstrap/finance-coverage gaps and the reproduced snapshot retry-idempotency defect. `INDEPENDENT_REVIEW=PENDING`; `SUPERVISOR_PASS=NOT_CLAIMED`; `OWNER_UAT=NOT_RUN`; `FULL_GOAL_199=IN_PROGRESS`; `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES`.

**Requested:** review A–E against the Owner oracle and exact current source/dist; state whether the historical visual/runtime proof is sufficient or must be recaptured, and list remaining failures. Owner visual UAT follows only after Independent Review PASS.
