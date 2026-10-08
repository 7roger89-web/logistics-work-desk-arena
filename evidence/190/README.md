# Evidence — Issue #190 visual fidelity recovery (real Chromium)

Head: `944ddae5e2d48f8e0edabd11ff12417af252cc22` on `arena/12974a76-logistics-work-desk-arena`
(PR #191 head; product source delta from Writer head `18cbf9a` = NONE).
Generated: 2026-10-08. Executor: Arena visual-evidence lane (this session).

## 1. Verdict summary

| Item | Result |
|---|---|
| Known-good populated host reproduced | **YES** — `scripts/verify_visual_shipment_workspace.py`, SANDBOX_STAGING/mongomock, `/model` carries SEA-160 (11 journey nodes, 9 Attention items) |
| Shipments store delivery | **YES** — 11 detailed nodes rendered straight from the host view model; no manual store/CDP injection |
| Prior custom CDP failure class | **HARNESS DEFECT (closed)** — the earlier failure was the Writer's custom CDP/store pipeline, not the product runtime; the canonical hosts work at this exact head |
| Real Chromium rendered | **YES** — Chromium 110.0.5478.0 (headless), see §4 environment disclosure |
| Populated geometry vs approved donor | **IDENTICAL** on every geometry axis (§3) |
| Populated visual vs Owner original sample | **PENDING** — `reference-original.png` (1536×1466) was NOT delivered into this workspace; see §6 |
| Product source edits this session | **NONE** — only acceptance scripts / verification glue / evidence (§5) |
| Regressions (#190/#188/#186/#184, oracle, typecheck, build, scan) | **PASS** (§7) |
| Overall | **INCOMPLETE** — blocked on the missing Owner sample for the final 100%-fidelity adjudication; NOT ready for independent Supervisor sign-off on the pixel axis |

## 2. Artifacts in this directory

| File | Meaning |
|---|---|
| `candidate-populated-desktop.png` | Populated SEA-160 default state, viewport 1536×1466, scrollTop=0 |
| `candidate-populated-fullpage.png` | Same capture; the app shell is its own scrollport so full-page == viewport height |
| `candidate-populated-journey.png` | Journey section element shot (1224×1127) |
| `candidate-populated-390.png` | Populated at 390×844 |
| `fresh-desktop.png`, `fresh-desktop-cockpit.png`, `fresh-390.png` | Truthful zero-node SEA-188 lane |
| `completion-collapsed.png`, `completion-expanded.png` | Completion Goals default + expanded |
| `global-workspace-expanded.png` | Global Workspace after automatic map auto-collapse |
| `shipment-list-alerts.png` (+fullpage) | List with canonical Attention-band alerts and owner/updated_by responsibility |
| `reference-donor-reconstruction.png` (+fullpage, journey crop) | Approved PR177/Prototype-B donor commit `70fd361` rendered in the SAME browser/viewport — the "exact approved donor reconstruction" authority |
| `side-by-side-populated.png`, `overlay-populated.png`, `diff-populated.png` (+json) | Reference(donor) vs candidate at page level |
| `side-by-side-journey.png`, `overlay-journey.png`, `diff-journey.png` (+json) | Same, cropped to the Journey section |
| `geometry-190.json` | All machine measurements (blocks, nodes, cards, gaps, first-screen order, per-lane metrics, comparison table) |

## 3. Reference(donor) vs candidate measurements (1536×1466, shell scrollport coords)

| Metric | Reference (donor 70fd361) | Candidate (this head) | Δ |
|---|---|---|---|
| Journey outer bbox | 1224×904 @(288,687) | 1224×1127.5 @(288,687) | +223.5h = #190 five-card rail + compact modules row (intended) |
| Map bbox | 802×760 @(289,830) | 802×760 @(289,810.2) | same size; −19.8y (donor map toolbar removed per mandate) |
| Right Quick Panel bbox | 420×760 @(1091,830) | 420×760 @(1091,810.2) | same |
| Map / panel width ratio | 1.91 | 1.91 | 0 |
| Journey split height | 760 | 760 | 0 |
| Node logical W/H | 164×136 | 164×136 | 0 (oracle-exact, 11/11 nodes incl. positions) |
| Node rendered W/H | 114×94.5 | 114×94.5 | 0 |
| Fit scale | 0.694946 | 0.694946 | 0 |
| Map→panel gap | 0 | 0 | 0 |
| Attention→Journey gap | 15.9 | 15.9 | 0 |
| Lower work cards | absent (donor predates them) | exactly 5, one row: 230×218.3 each, gaps 12/12/12/12 | #190 mandate addition |
| Six-phase strip above populated map | no | no | 0 |
| Populated map toolbar | yes (donor) | no | #190 mandate removal |
| Default right panel | generic overview | factual Quick Panel (problem node) | #190 mandate change |
| Completion Goals default | collapsed | collapsed | 0 |
| First-screen order | attention → journey → toolbar → map → side/overview/quick | attention → journey → map → side/quick → cards(below fold) → goals(below fold) | intended |

Pixel diff of the Journey crops shows non-zero bands **only below y≈896**, i.e. exactly where the donor has no content and the candidate adds the five-card rail; the map/panel region is pixel-stable.

Composition facts verified in the candidate at 1536×1466:
- Attention strip directly above the Journey workspace (y 501 → 687), one strip only.
- Large left map + fixed right 420px factual Quick Panel; no generic overview, no Global Workspace open by default.
- No six-phase strip, no populated map toolbar.
- Five lower work cards (BOOKING – ĐẦU ĐI / TÀU ĐẾN – CHẶNG CHÍNH / NHẬP KHẨU – ỦY THÁC / GIAO HÀNG / HỒ SƠ & PHẠM VI), one desktop row, 4 compact tabs each, read-only facts.
- Completion Goals collapsed by default; collapsed copy states the derived-guidance truth ("không phải trường bắt buộc khi tạo lô" class wording); expands on demand to 7 goal cards.
- Global Workspace auto-collapses the map to the 208px rail and gives the workspace 1014px; operator can reopen the map.
- 390px: stacked split, no horizontal overflow (page 0px, scrollport 0px).
- List: urgency markers exist ONLY on rows carrying a canonical Attention band (LO-0306/LO-0308/LO-0295 = OVERDUE); rows without a band show none; responsibility renders `Phụ trách` (canonical owner) with `Cập nhật bởi` (updated_by) secondary.
- Fresh SEA-188: HỒ SƠ actionable, five downstream phases UNKNOWN + inert, zero fabricated nodes, compact 500px split, right onboarding panel, profile CTA reaches the existing Execution Profile inside Global Workspace, no overflow at 1536 or 390.

## 4. Environment disclosure (read before trusting pixels)

- Browser: **Chromium 110.0.5478.0** headless (`--no-sandbox --disable-gpu`), obtained as the npm package `@sparticuz/chromium@110` (registry.npmjs.org is allow-listed; the Playwright/Google browser CDNs are NOT reachable from this sandbox). Bundled AL2 NSS/NSPR libs used via `LD_LIBRARY_PATH`. Newer Chromium builds crash in this sandbox's VM; 110 is the newest build that runs here. Consequence: CSS `color-mix()` (Chrome 111+) is unsupported — Tailwind v4 emits an equivalent static hex-alpha fallback *before* each `@supports (color:color-mix(...))` block, so rendered colours stay correct; layout is unaffected. Disclosed, not hidden.
- Fonts: the shipped CSS `@import`s **Be Vietnam Pro** from fonts.googleapis.com (unreachable here). The harness fulfils that request from the vendored fixture `tests/component/fixtures/fonts/be-vietnam-pro` (npm `@fontsource/be-vietnam-pro@5.3.0`, OFL) so text metrics match production. The Journey surface names **Inter** first but production never fetches it (it resolves to the operator's OS UI font); the harness injects `@fontsource/inter@5.2.x` as the closest deterministic proxy. Both are EVIDENCE-HARNESS substitutions, documented in `tests/component/fixtures/fonts/*/README.md`; product source and `component/dist/*` are untouched.
- Harness: `tests/component/browser_journey_visual_fidelity_190.mjs` + `scripts/compare_journey_visual_190.py` (Pillow arithmetic only, **no OCR**). Hosts reused verbatim from the #160/#188 lanes; no new data-delivery stack.
- Scope honesty: cloud-sandbox render, NOT Owner-device certification.

## 5. Changes made (acceptance scripts / glue / evidence only)

- `tests/component/browser_journey_visual_fidelity_190.mjs` (new) — populated/fresh/list/donor lanes, geometry measurement, screenshots, oracle assertions.
- `scripts/compare_journey_visual_190.py` (new) — side-by-side / overlay / heat-diff / numeric summary.
- `tests/component/fixtures/fonts/**` (new) — vendored Be Vietnam Pro + Inter with provenance READMEs and MANIFESTs.
- `tests/component/browser_journey_fresh_parity_188.mjs` — reveal step added before the B8 finance assertion because #190 made Completion Goals collapsed by default (mandate M5); assertion content unchanged.
- `tests/component/dom_acceptance_journey_demo_fidelity.mjs` — panel/collapse expectations updated to the #190 contract (factual Quick Panel default; map auto-collapse via Global Workspace + rail reopen). Geometry assertions (11 positions, edge paths, fit/zoom/pan/reset, drag guard, zero writes) untouched and still PASS.
- Product source (`component/src/*`, `views/*`, `core/*`): **no edits**.

## 6. Owner original sample — MISSING (blocking the 100% claim)

The task packet declares `reference-original.png` (1536×1466) as the visible UI
authority, but the file was not delivered into this workspace (no attachment
block arrived; no such file exists in the repo, PR #191, or issue #190).
Everything measurable against the approved donor is done (§3). The remaining
adjudication — does the candidate's above-the-fold density (identity card +
Attention + Journey + five-card rail within 1466px) match the Owner sample —
requires that image. Until it is provided: `POPULATED_VISUAL_VS_OWNER_SAMPLE =
NEEDS_EVIDENCE`, verdict INCOMPLETE.

## 7. Regression battery at this head

| Check | Command | Result |
|---|---|---|
| TEST_190 | `pytest tests/test_journey_visual_fidelity_190.py` | 7/7 PASS |
| TEST_188 (pure) | `pytest tests/test_journey_fresh_parity_188.py` | 7/7 PASS |
| TEST_188 (real Chromium) | `node tests/component/browser_journey_fresh_parity_188.mjs /tmp/out188 all` | 31/31 checks PASS (fresh desktop+390, populated desktop+390, B7 neutral, B8 finance UNKNOWN, customs truth) |
| TEST_188 (DOM) | `node tests/component/dom_acceptance_journey_fresh_188.mjs` | PASS |
| TEST_186 | `pytest tests/test_journey_super_goal_186.py` | 9/9 PASS |
| TEST_184 | `pytest tests/test_journey_v3_customs_import_184.py` | 16/16 PASS |
| Prototype-B oracle | `verify_visual_shipment_workspace.py --fixture` + `dom_acceptance_journey_demo_fidelity.mjs` | PASS (11 exact positions, parallel group, fit/zoom/reset/pan, drag guard, selections, collapse/expand, zero writes) |
| Typecheck | `npm run typecheck` | PASS (exit 0) |
| Build | `npm run build` | PASS; rebuilt dist byte-identical to committed dist (`668ec16f…`, `426998c2…`) |
| Scan | `npm run scan` | FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0 |
| Full python suite | `pytest tests -q` | 1686 passed / 31 failed / 24 errors — ALL pre-existing at head 944ddae in unrelated areas (perf/latency harnesses, RBAC, finance parity, `views.web_app.ROUTES` collection error); zero of them touch journey/visual surfaces and this session changed no Python/product file |

Truth invariants re-proven in the browser lane: declaration ≠ clearance, GNT ≠ paid, UNKNOWN ≠ 0, suggested partner ≠ payable, no fake FX, upload ≠ completion, B7 neutral terminal, B8 finance UNKNOWN, B1 profile CTA, zero-node cockpit.

## 8. Stop rules honoured

NO MERGE · NO DEPLOY · NO PRODUCTION WRITES · NO REAL MONGO (mongomock SANDBOX_STAGING only) · NO SECRETS · tienthanhlog untouched · no human-UAT claim.
