# LOGI #199 — Independent bounded review of A/B and Owner paper chart

**Review date:** 2026-10-16
**Reviewer actor:** ChatGPT Control Tower (GPT-6), separate from the Arena implementation writer.
**GitHub authentication note:** This review file is written through the Owner's connected GitHub integration. The Git commit identity is not a distinct human reviewer's identity.
**Reviewed immutable app SHA:** `8932fcb4aa2e7705b1e0963a830758bd3d9849ae`
**Implementation baseline:** `abf3c0edca0e0c24e7cba840ca2923623454653e`
**Scope:** mobile initial-camera fix A; meaningful save/reload/readback proof B; preserve Owner paper-chart artwork.
**Verdict:** `INDEPENDENT_REVIEW=PASS_BOUNDED_A_B_PAPER`
**Evidence level:** independent source/diff review + independent SHA-256 recalculation + archived Chromium screenshot/metrics review; reviewer did **not** launch a new live browser.

## Actor-own preflight
- `P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED`
- `LAW_CHECK=PASS | SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`
- `TARGET_LAW_FRESHNESS=CURRENT` at frozen app SHA (portable header matches canonical SHA).
- `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb` (advisory only).
- `REQUIRED_SKILL=p2p-uiux` read at `.agents/skills/p2p-uiux/SKILL.md`. Portable manifest records SHA-256 `98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2`. Scope = bounded UI/interaction.
- Owner visual authority: `docs/goals/LOGI-APP-RENEWAL-01/OWNER_VISUAL_FIDELITY_OVERRIDE.md`; HTML donor is visual/interaction oracle only, not business fixture data.

## Independent challenge and observations

1. **Frozen content-to-capture identity:** Fetched the four actual GitHub files from immutable `8932fcb`, including the large JS via its Git blob endpoint, and independently computed SHA-256:
   - `component/src/components/JourneyMap.tsx` = `f3b3d51be38afa623fd649bb91aa3f57e4e28b130e907ac9fa9c857d717b3a88` — MATCH.
   - `component/dist/logi-shell.js` = `121bbc3c6090b4cdd0aa576a6e9b29a0976f0bf6f6c35360512b5ee6cac5ca9b` — MATCH.
   - `component/dist/logi-shell.css` = `cd690366fbc18ed63db3b4af8ffe0b75b971e0bcfffac3c03cc0729cfa43a4ab` — MATCH.
   - `evidence/logi-199-final-fix/capture_fix_ab.py` = `cf57703e0d4c7b89680d3eafa16b9576ebf65c16b7b4341ddd34637b336ecca5` — MATCH.
   All equal the recorded raw metrics at this exact app SHA. This binds the archived browser evidence to the shipped content, not to a guessed Git commit.

2. **A mobile initial view:** independently inspected source diff and archived screenshot `mobile-before-vs-after.png`. A fresh, unselected mobile view now anchors the first real node, showing BOOKING / PICKUP / partially visible CUSTOMS EXPORT at 390x844; 11 nodes, 20 edges, 100%. `Đọc rõ` still focuses the actual problem ARRIVAL; selecting DELIVERY focuses DELIVERY. Raw capture records touch-pan +240px and zoom/Fit; no invented nodes/states. `A=PASS` for T6-FCL; not a claim of full AIR/ROAD route certification.

3. **B meaningful persistence:** independently inspected the capture harness, fail-closed predicate (`OLD != NEW && readback == NEW`), raw metrics and screenshot `save-old-to-new.png`. On isolated Mongomock, source capture measured OLD `2026-10-11`, entered NEW `2026-10-04`, tapped Save, navigated/reloaded, and read back `2026-10-04`. Writer's supplementary clean-ZIP smoke independently documented the reverse `2026-10-04 -> 2026-10-11`; that supplementary smoke is author evidence, not this reviewer's replay. `B=PASS` scoped to isolated staging, not production DB.

4. **Owner paper unchanged:** actual `chart-paper.jpg` Git blob is identical at `abf3c0e` and `8932fcb` (`f9307466428099b1e98c1104bf9ba4032bc458d7`). Independently compared the base64 asset to the JPEG embedded inside the exact Owner HTML; MATCH. CSS Git blob identical between base and candidate. No redesign or asset regression observed.

5. **Scope isolation:** GitHub diff `abf3c0e..8932fcb` changes only JourneyMap camera, its rebuilt JS, one regression test, and A/B evidence. No product API, auth, finance, Mongo settings, schema, or production release scripts changed.

## Honest limits and next action

- `SCREENSHOT_REVIEW=PASS`; `SOURCE_HASH_REVIEW=PASS`; `REVIEWER_LIVE_BROWSER=NOT_RUN`. The screenshots were captured by the executor's Chromium, not by this reviewer.
- `WINDOWS_RUNTIME=NOT_RUN`; cannot certify Python installation, Windows launcher, or Owner machine from Linux smoke.
- `OWNER_UAT_READY=YES_FOR_ISOLATED_WINDOWS_STARTUP_AND_UAT` **for the exact frozen app SHA only**. This is approval to begin an isolated local trial, NOT a claim that Windows already works or that Owner approved UX.
- `OWNER_UAT=NOT_RUN`; `FULL_VISUAL_PARITY=NOT_CLAIMED` beyond A/B/paper; `PRODUCTION_READY=NO`; `MERGE_MAIN=NO`; `DEPLOY_PRODUCTION=NO`.
- Do not use the old `logi199-owner-trial` tag, pinned to older commit `3533144`.
- Windows user download: https://github.com/7roger89-web/logistics-work-desk-arena/archive/8932fcb4aa2e7705b1e0963a830758bd3d9849ae.zip
- Owner must use test-only fixtures (Mongomock on `127.0.0.1`, no real data), start `scripts\\logi199_uat.cmd`, and only after the isolation proof open `http://localhost:9501`. If Windows start fails, record the exact error, do not disable security guard or claim UAT PASS.

`OE_VERDICT=DO_IT` for this bounded independent review; `SKIP_IT` for another G0-G5 campaign or redoing known-good visuals.
