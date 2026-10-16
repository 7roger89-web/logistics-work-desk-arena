# LOGI #199 — khôi phục nền giấy hải đồ Owner đã duyệt

Bounded restoration evidence for the Owner request **“KHÔI PHỤC ĐÚNG SƠ ĐỒ OWNER
ĐÃ DUYỆT”**. This packet replaces the Vietnam/Biển Đông geographic chart
background of the Journey map with the exact paper-chart texture extracted from
the Owner-approved HTML oracle, using the donor's exact parameters. It does
**not** redo G0–G5, redesign any route, self-sign Supervisor PASS, or replace
Owner UAT.

## P2P preflight receipts (executor-own)

`P2P_LAW_SOURCE=LOCAL_PORTABLE`

`LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`

(bound to the recorded `SOURCE_CONTENT_SHA256` of
`.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`, projection metadata
`P2P_PORTABLE_LAW_PROJECTION=YES`; `.p2p/system` carries no installed
notebook projection; canonical was not reached in this session and was not
probed merely to force fallback).

`EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`
(advisory/non-authoritative portable ACTIVE record).

`p2p-skill-consumption-receipt/1`

```json
{"schema":"p2p-skill-consumption-receipt/1","skills":[{"id":"p2p-uiux","path":".agents/skills/p2p-uiux/SKILL.md","sha256":"98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2","consumption":"READ_AND_APPLIED"}]}
```

`INITIAL_PLANNING_CLASSIFICATION=UIUX`; `FINAL_ROUTING_CLASSIFICATION=UIUX`.
Design authority: `docs/goals/LOGI-APP-RENEWAL-01/OWNER_VISUAL_FIDELITY_OVERRIDE.md`
(OWNER_CORRECTION / DESIGN_AUTHORITY) — read and applied; runtime visual review
was performed (real Chromium screenshots + computed styles + pixel statistics),
not SOURCE_REVIEW alone.

OE gate — `Không bị over engineering chứ?`
`SIMPLER_PATH=YES` (reuse the existing map component, capture harness and test
lanes; one asset swap + layered background), `MATERIAL_PROGRESS=YES`,
`NECESSITY=YES` (Owner-corrective), `CORE_BEFORE_SUPPORT=YES`,
`SMALLER_VERIFIABLE_SLICE=YES` (background restoration only).
`OE_VERDICT=DO_IT`. Redesign/framework/G0–G5 recertification = `SKIP_IT`.

## What changed (source) and what did not

| File | Change |
|---|---|
| `component/src/components/JourneyMap.tsx` | Journey background now uses the extracted donor texture `../assets/journey/chart-paper.jpg` with the exact donor layers: base `#EDF1F5`, texture `backgroundSize: 760px`, `repeat`, overlay `opacity: 0.34` + `mix-blend-mode: multiply`, grid `52px 52px` `rgba(120,146,170,0.16)` (`journey-map-texture`, `journey-map-grid` layers, pointer-events none). |
| `component/src/index.css` | map-first canvas base is `#EDF1F5` with no CSS background image (the old `cover`-cropped chart layer is gone; `vietnam-east-sea-chart.webp` remains in the repo but is no longer the Journey default background). |
| `component/dist/logi-shell.js`, `logi-shell.css` | rebuilt from source via `npm run build` (no hand edits); a verification rebuild is byte-identical. |
| `evidence/logi-199-g2/capture_journey_flow.py` | legacy zero-node assertion updated to the approved paper texture layer (`approved_owner_chart_paper_loaded`) instead of the retired webp key. |
| `evidence/logi-199-restore/` | this packet + `capture_owner_compare.py` + `metrics.json` + 18 comparison screenshots. |

No API, auth, task/evidence, UNKNOWN handling, applicability conditions, or
save/readback code paths were touched. The demo data of the Owner HTML was not
copied into the app.

The texture asset `component/src/assets/journey/chart-paper.jpg` was extracted
**verbatim** (byte-for-byte, no AI regeneration, no redraw) from the base64
JPEG embedded in `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`
(SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`
= the Owner-declared source hash) and is already committed at the base commit.

## A — HTML demo (Owner-approved original)

`reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html` — **nguyên
bản, tự chạy offline, không rút gọn**. SHA-256 verified at capture time =
`26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.
Open it directly in a browser (file://) — no server needed.

## B — App updated (this branch)

- Branch: `arena/d657fb56-logistics-work-desk-arena` (session-fixed work branch;
  the source change set is the same restoration requested on
  `ct/logi199-owner-oracle-paper-20261016`).
- Source commit: `LOGI-199: restore Owner-approved paper chart texture for
  Journey map` (see branch log for the exact SHA).
- Dist rebuilt from source; `npm run typecheck` PASS, `npm run scan` PASS
  (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`).

## Browser comparison — real Chromium (153.0.8010.0)

Method: `evidence/logi-199-restore/capture_owner_compare.py` opens the Owner
HTML (file://) and the real Streamlit app (isolated Mongomock staging,
`scripts/logi199_t6_staging_app.py`, `STAGING_ISOLATION_PROOF=PASS
transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO
production_client=NO`) side by side at 1440×900 and 390×844. Raw values in
`metrics.json`.

### Donor parameters — Owner HTML vs app (all 16 checks PASS)

| Parameter | Owner HTML oracle | App (rendered) |
|---|---|---|
| base background | `rgb(237, 241, 245)` = `#EDF1F5` | `rgb(237, 241, 245)` = `#EDF1F5` |
| texture size | `760px auto` | `760px auto` |
| texture repeat | `repeat` | `repeat` |
| texture opacity | `0.34` | `0.34` |
| texture blend | `multiply` | `multiply` |
| texture image | `data:image/jpeg` | `data:image/jpeg` |
| grid size | `52px 52px, 52px 52px` | `52px 52px, 52px 52px` |
| grid color | `rgba(120,146,170,0.16)` | `rgba(120,146,170,0.16)` |

`DONOR_PARAMS_VERDICT=PASS`.

### Texture identity — the app uses the donor's exact bytes

| Artifact | SHA-256 |
|---|---|
| JPEG embedded in Owner HTML | `e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627` |
| `component/src/assets/journey/chart-paper.jpg` | `e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627` |
| data image rendered by the app | `e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627` |

`texture_identity.bytes_identical_to_donor=true`,
`app_matches_owner_embedded_jpeg=true`.

Pixel statistics of blank paper regions (mean RGB / gray stddev): owner desktop
`(225.5, 231.4, 237.2) / 3.89` vs app desktop `(223.1, 229.1, 234.7) / 4.78` —
the same paper + grid family on both surfaces (tile phase differs because the
layer origin differs).

### Captures (this packet)

| State | Owner HTML oracle | App (real Streamlit) |
|---|---|---|
| Desktop 1440×900 initial map | `owner-desktop-1440x900-initial.png` | `app-desktop-1440x900-initial.png` |
| Desktop node bubble | `owner-desktop-1440x900-node-bubble.png` | `app-desktop-1440x900-node-bubble.png` |
| Desktop task popup | `owner-desktop-1440x900-task-popup.png` | `app-desktop-1440x900-task-popup.png` |
| Mobile 390×844 initial map | `owner-mobile-390x844-initial.png` | `app-mobile-390x844-initial.png` |
| Mobile node bubble | `owner-mobile-390x844-node-bubble.png` | `app-mobile-390x844-node-bubble.png` |
| Mobile task bottom sheet | `owner-mobile-390x844-task-sheet.png` | `app-mobile-390x844-task-sheet.png` |
| Mobile real touch pan | `owner-mobile-390x844-touch-pan.png` | `app-mobile-390x844-touch-pan.png` |
| Zero-node SEA-188 | — (demo has no empty state) | `app-desktop-1440x900-zero-node.png`, `app-mobile-390x844-zero-node.png` |
| ON BOARD save/reload/readback | — | `app-mobile-390x844-onboard-readback.png` |

### Scenario results (real browser)

| Scenario | Verdict | Evidence |
|---|---|---|
| T6-FCL desktop 1440×900 | PASS | 11 nodes / 20 edges; map 1406×780 at y=111.19; bubble 310×252 inside map; task popup centered (center error 0.0px); 0 page errors. |
| T6-FCL mobile 390×844 | PASS | 11 nodes / 20 edges; map 374×549 at y=269.94; bubble + bottom sheet (`sheet_bottom_anchored=true`); 0 page errors. |
| Real touch pan (both surfaces) | PASS | CDP `Input.dispatchTouchEvent` touchStart + 12 touchMove + touchEnd; `pointerType=touch`; owner map transform Δx=281px, app map transform Δx=281px; no node selected; no bubble/modal left open. |
| Zero-node SEA-188 desktop + mobile | PASS | Full paper background + grid rendered (texture layers present in DOM and computed styles); 0 nodes / 0 edges — no fabricated stages; exactly 1 CTA `BỔ SUNG HỒ SƠ`; toolbar keeps `Đang ở: Chưa xác định`; truthful empty state `Chưa có sơ đồ Journey`. |
| Isolated save/reload/readback | PASS | T6-FCL ON BOARD date filled `2026-10-04`, explicitly saved, lot reloaded, value read back `2026-10-04`. Mongomock staging only; no payment flow; no real backend write. `TAP_SAVE_READBACK_VERDICT=PASS`. |
| Owner HTML functional replay | PASS | Node → bubble (OB-01…OB-04 tasks) → task popup (evidence types, `Xem thêm chi tiết` section); utility `HỒ SƠ & TÀI CHÍNH`; zoom/−/Fit controls; demo scenario switcher intact. |

`COMPARISON_VERDICT=PASS`.

### Focused regression (unchanged surfaces)

- `python3 -m pytest` focused slice (journey 184/186/188/190 + goal199 visual +
  goal199 air + t1–t5 suites): **105 passed**.
- Official-dist DOM acceptance `dom_acceptance_journey_fresh_188.mjs`
  (`nodes=[]` and `journey absent` variants): PASS (jsdom, one benign
  `scrollTo` warning).
- `dom_hook_transition_197.mjs` (real bundle, both directions): PASS.
- `npm run typecheck`: PASS. `npm run build` + `npm run scan`: PASS
  (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`); verification rebuild
  byte-identical to the committed dist.

## NOT verified / boundaries

- `INDEPENDENT_REVIEW=PENDING`; `SUPERVISOR_PASS=NOT_CLAIMED`;
  `OWNER_UAT=NOT_RUN`; `OWNER_UAT_READY=NO`; `FULL_GOAL_199=IN_PROGRESS`.
- No G0–G5 recertification, no other route redesign, no full pytest suite, no
  21-route audit in this bounded slice.
- `NO_MERGE_MAIN=YES`; `NO_DEPLOY_PRODUCTION=YES` — no Owner authorization yet.
- Windows runtime `NOT_RUN`; `GITHUB_ACTIONS_CI=NOT_TRIGGERED`.
- The capture harness runs Chromium 153.0.8010.0 with
  `--no-sandbox --disable-dev-shm-usage --disable-gpu` (this sandbox's headless
  shell SIGSEGVs with the legacy `--single-process --no-zygote` flags); the app
  DOM lives in a shadow root, so texture computed styles are read through
  Playwright locators (shadow-piercing), not `document.querySelector`.
- Prior G2-era oracles that asserted the retired
  `approved_vietnam_chart_data_image_loaded` webp key were updated to the
  paper-texture truth; their historical verdicts stay historical.

## Learning reconciliation

`LEARNING_RECONCILIATION=CANDIDATE`
(id candidate `logi199-app-shell-shadow-dom-capture-20261016`; trigger: any
future Playwright/CDP capture of this app — the shell renders in a shadow root,
so `page.evaluate(document.querySelector…)` silently returns null while
locators resolve; and multi-page/single-process Chromium in this sandbox is
unreliable). Evidence: the failed-then-corrected capture runs in this session
(metrics.json + this README). Not promoted; for reviewer disposition only.

## GOAL / PROGRESS / CURRENT / NEXT / BLOCKERS

- **GOAL:** restore the Owner-approved paper chart as the Journey background,
  identical to the approved HTML donor, with real-browser comparison proof.
- **PROGRESS:** donor texture extracted and wired with exact parameters; dist
  rebuilt from source; 18 comparison screenshots + metrics; all focused
  regressions pass; `COMPARISON_VERDICT=PASS`.
- **CURRENT:** evidence packet complete on the session work branch.
- **NEXT:** Independent Review of this packet → Owner UAT on a preview.
- **BLOCKERS:** none for this slice; release gates (merge/deploy) await Owner.
