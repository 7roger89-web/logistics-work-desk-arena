# LOGI-199 G5 — Integrated Visual & Functional Verification Summary

## 1. Visual Comparison vs Owner HTML Oracle (`reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`)
- **Journey Map-First Canvas (`evidence/logi-199-g2/`)**:
  - Uses exact Owner-selected `component/src/assets/journey/vietnam-east-sea-chart.webp` (SHA-256 `f83d42167dffcb1ac629f261923408a2c6d5d6d7564cf63083aa869bababdef9`).
  - Full-bleed viewport (`ensureHostBleedStyle()` removes outer Streamlit header/padding).
  - Symmetric vertical centering (`ROW_MAIN` at 50% between `ROW_UPPER` and `ROW_LOWER`) matching `ref-01`.
  - Default `95%` fit zoom on desktop shows all 11 route nodes unclipped while keeping `Quần đảo Hoàng Sa (Việt Nam)`, `BIỂN ĐÔNG`, and `Quần đảo Trường Sa (Việt Nam)` legible above and below the main route row.
  - Bottom-left `CHÚ GIẢI TRẠNG THÁI` legend and top-right floating `▤ HỒ SƠ & TÀI CHÍNH` trigger + utility bubble + whole-lot overlay (`ref-05`).
  - Mobile (`390×844`): `background-size: 100% auto` in upper half shows the full Vietnam / Biển Đông / Hoàng Sa / Trường Sa chart without aspect distortion or side cropping; active route nodes in lower half; task bubble (`z-30`) and bottom sheet (`0px` overflow) verified.
- **Shared Visual System (`evidence/logi-199-g1/`, `evidence/logi-199-g3/`, `evidence/logi-199-g4/`)**:
  - Unified Mimo–Sonnet palette (`#10263C`, `#123A5E`, `#1D6FA8`, `#EDF1F5`, `#D6DEE7`, `#FFFFFF`) and semantic status tokens across all 24 routes.

## 2. Runtime & Regression Verification
- **FontFace Runtime Check**: `Be Vietnam Pro` (400–800) and `IBM Plex Mono` (400–700) locally bundled and `loaded` (`beLoaded: true`, `plexLoaded: true`).
- **Write/Readback Check**:
  - Desktop (`1440×900`): `T6-FCL` node `07 ON BOARD / ATD` -> bubble -> modal -> write `2026-10-03` -> reload/reopen readback `2026-10-03` (`PASS`).
  - Mobile (`390×844`): `T6-FCL` node `07 ON BOARD / ATD` -> bubble -> bottom sheet -> Save button clicked -> reload/reopen readback `2026-10-04` (`PASS`).
- **Automated Regression Suites**:
  - `pytest` (14 LOGI-199 test modules): `281 passed`.
  - `node tests/component/dom_acceptance_logi197_journey_clarity.mjs`: `PASS`.
  - `node tests/component/dom_hook_transition_197.mjs`: `PASS`.
  - `node tests/component/browser_logi199_real_streamlit.mjs`: `RUNTIME_BROWSER=PASS`.
  - `node tests/component/browser_logi199_t6_modes.mjs`: `T6_BROWSER=PASS` (all 6 SEA FCL/LCL, AIR direct/consolidated, ROAD FTL/LTL modes at 1440×900 & 390×844).
  - `node tests/component/browser_logi199_t5_route_audit.mjs`: `T5_AUDIT_PASS []` (`0` failures across 21 audited routes × 2 viewports).
  - `cd component && npm run typecheck && npm run build && npm run scan`: `PASS` (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`).
