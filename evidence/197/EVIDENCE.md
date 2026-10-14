# LOGI-197 — exact evidence binding

PRODUCT_HEAD=`fc41beed8de13ffd34c3af1ef630d3c2536124de`
PR=#198 `ct/logi197-journey-operator-clarity`
MERGE=NO · DEPLOY=NO · HUMAN_UAT=NOT_CLAIMED

The product commit above contains the LOGI-197 branch (source + typecheck fix
7963622 + rebuilt committed dist fc41bee). This evidence commit touches only
`evidence/197/` — no source, no dist, no build reruns. Verify after checkout
with:

```bash
git diff fc41beed8de13ffd34c3af1ef630d3c2536124de..HEAD --stat -- . ':(exclude)evidence'
```

Expected output: no files. All runtime evidence below was captured against
the exact product tree above; no production data was used, no production
writes were made, and no production instance (8501/8510) was touched.

## Runtime binding

- Captured: `2026-10-12T19:00+07`
- Browser: real Chromium `152` (non-headless under Xvfb :99), driven over raw
  CDP (`Page.navigate`, `Page.captureScreenshot`, `Input.dispatchMouseEvent`
  real mouse press/release, `Emulation.setDeviceMetricsOverride`)
- Harness: `file://` page mounting the ACTUAL committed
  `component/dist/logi-shell.js` + `logi-shell.css` through the real Streamlit
  Components v2 contract (`mount({name:'logi_shell', data, parentElement,
  setTriggerValue})`); Chromium 152 hard-blocks `http://127.0.0.1`, so
  `file://` was used instead
- Backend: write events round-tripped through the REAL backend
  (`vm.consume_phase_b_triggers`) on a mongomock sandbox; the fresh view
  model was re-delivered per dispatch (Streamlit rerun semantics)
- Viewports: desktop `1440×900`, mobile `390×844`
- Product bundle SHA-256: `c1f6ce4db0531c8feaa8fabca1dc47c9f2a4e977da55ef2b81620011cbbffe70`
- Product CSS SHA-256: `eb96ae2f373255c1e1b1b6f22652bb16457bed085016bd65b5bdc4c4ab9422f6`
- Runtime result: **53/53 checks PASS, 0 FAIL** (contracts A–K; see
  `results.json` for the full machine-readable check list)

## Measured acceptance summary

- Desktop 1440: exactly 5 macro phases; journey nav 222px of 813px viewport;
  detailed 11-node map NOT mounted by default (`aria-expanded=false`, toggle
  reads "🗺 Bản đồ chi tiết"); "📍 Đang ở: Chặng chính · TRANSIT" visible;
  UNKNOWN stays "Chưa xác định", never guessed — `d1-default-five-phases.png`
- Detailed map: toggle opens the existing 11-node JourneyMap (parallel
  SI/VGM∥gate-in branch intact); "Thu gọn bản đồ" closes it —
  `d2-detail-map-open.png`
- Steps 1–4: stage tab row is exactly ["Công việc", "Chứng từ"]; no "Chi phí",
  no "Lịch sử"; phase-2 Chứng từ shows only the `transport` attachment (not
  the `booking` one); no global `shipment-document-picker` inside the phase —
  `d4-phase2-scoped-docs.png`
- Absent phase (SEA-197ABS, scope=[]): steps 3–4 read "Chưa có công đoạn",
  all four Công việc/Chứng từ buttons disabled; clicking a disabled button
  opens nothing and never falls back to the global whole-lot workspace —
  `d5-absent-phase.png`
- Step 5 owns Hồ sơ / Chi phí / Lịch sử; summary reads "Chưa xác nhận hình
  thức nhập khẩu" — no false green-complete from executionProfile
- CUSTOMER_SELF modern (SEA-160): "Người nhập khẩu · An Phát JSC · ✓ Đã xác
  định", NO second customer picker; confirm dispatches **exactly 1**
  `shipment_commercial_flow_save` and **0** `shipment_customer_save`; fresh
  readback keeps `customer_id=CUST-ANPHAT` — `d7-modern-custself-after.png`
- CUSTOMER_SELF legacy unique (SEA-195, name-only): identity auto-resolved to
  "An Phát JSC", no duplicate picker; one atomic save, zero pre-save; fresh
  readback `customer_id=CUST-ANPHAT`, name repaired to "An Phát JSC" —
  `d8-legacy-custself-after.png`
- CUSTOMER_SELF exception (SEA-197AMB, two exact matches): compact chooser
  appears, confirm disabled until an explicit choice; choosing CUST-DUP-1 →
  exactly 1 save, readback `customer_id=CUST-DUP-1`; zero matches
  (SEA-197ZERO): chooser appears, confirm stays disabled — no fuzzy matching
  anywhere — `d9-exception-AMB-resolved.png`, `d9-exception-ZERO-chooser.png`
- Mobile 390: `scrollWidth == clientWidth == 390` on default, map-open, and
  phase-docs screens; five phases reflow to 2-col grid; map toggle reachable;
  stage docs usable — `m1-mobile-default.png`, `m3-mobile-phase-docs.png`
- Copy density: normal path leads with current position / next action / needed
  documents; no backend/readback/legal-identity exposition on the normal path
  (verified on the committed screenshots)

All findings are CONFIRMED_RUNTIME_FINDING (real renders + real CDP clicks +
real backend round-trips). HUMAN_UAT was never claimed.

## Gates bound to this product tree

- TypeScript typecheck: PASS (2 errors found in-session were repaired in the
  product tree itself as commit 7963622, `!Boolean(workspaceNode)`;
  identical runtime semantics)
- Vite build: PASS (1915 modules; `dist/logi-shell.js` 1,413.88 kB,
  `dist/logi-shell.css` 82.04 kB)
- executable-process scan: PASS, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`
- pytest `tests/test_shipment_document_picker_v1.py`: PASS, 16/16
- DOM acceptance `dom_acceptance_logi197_journey_clarity.mjs`: PASS
- DOM acceptance `dom_acceptance_logi195_compact_journey_smooth.mjs`: PASS
  (delegates to the superseding acceptance)

## Artifact SHA-256 manifest

`EVIDENCE.md` intentionally omits its own hash to avoid a circular self-hash;
Git's evidence commit tree binds this file itself.

- `d1-default-five-phases.png`: `4c2cf6d629e140f6836cd902b776720b145a19a221e77490ff922db226fb57d7`
- `d2-detail-map-open.png`: `1286fd22b36d983a6985e7f4f44fef6ef97930fffe843e2407c8cdd56a18208d`
- `d4-phase2-scoped-docs.png`: `b7bb86d33b3d2fffa4c3a68c1ecdc9d2146c4887f267499d41aa7a59acb73213`
- `d5-absent-phase.png`: `14475c2c09db7c50e1a03fe90b160a8f47fae967f58c3e16d4acc5951a12de9e`
- `d7-modern-custself-after.png`: `97ffabafb19341641a729621f9a360074eed7bfa4099da38eac7a207baf5dbe7`
- `d8-legacy-custself-after.png`: `0bc89ac9a068a01d0b1031204b2c44358a65ff32918215fb1f7993f528347a4c`
- `d9-exception-AMB-resolved.png`: `5e3c1c1cd74463653a5b25020b7d4c3040e37f8e5fdaf66362b49fe5f3f06821`
- `d9-exception-ZERO-chooser.png`: `aea24e69eeb095a37076fc2d2c005ce6ec0a5201102f53d460d1256f1ad73dee`
- `m1-mobile-default.png`: `9ba3598fb460c951c782f6c83c83e58fe693b2aa63b509ab68f27d3b677b9f76`
- `m3-mobile-phase-docs.png`: `37e9e552adba2aaa6f778c1f3ce0c287edaba02da9136dfb961bdea880e555b5`
- `results.json`: `89427aedc238314a3aeff087a8f9b377e8195a57a5096a3fcd503c7f035aa6d3`

The full local working set (16 PNGs + extended QA notes) lives outside the
repo at `~/workspace/logi197-qa-evidence/`; the representative subset above
fully proves the acceptance contract.
