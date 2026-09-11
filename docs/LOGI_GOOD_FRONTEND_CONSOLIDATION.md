# LOGI_GOOD_FRONTEND_CONSOLIDATION_01 — Frontend Consolidation Sweep

Bounded frontend completion sweep on top of merged PR #11 (C2D). **No backend
change, no new architecture.** Same frozen Logi-good shell, same one
`st.components.v2` root, same typed events, same bounded Python dispatcher.

## Donor authority used

- **A** `7roger89-web/logi-good`: NOT accessible from this session.
- **B** `owner-assets/logi-good-ui` branch → `design_reference/logi-good/`
  (extracted read-only; SOURCE_SHA `974b7cf` per its manifest). Used as the
  visual reference for parity checks.
- **C** the already-frozen literal implementation in `component/src`
  (identical to B for shell/css/ui; pages carry real-data wiring).

## Route capability matrix (baseline → final; states are B-based)

Route-level capability did not need new wiring: every already-backed
destination already rendered a real page. The sweep repaired presentation,
navigation honesty and the dashboard contrast defect.

| Route | Page | Baseline | Final |
| --- | --- | --- | --- |
| `/` | Home | REAL_BACKED (hero contrast defect) | REAL_BACKED (fixed) |
| `/viec-can-xu-ly` | Tasks | REAL_BACKED | REAL_BACKED |
| `/lo-hang` | Shipments | REAL_BACKED (donor-identical) | REAL_BACKED |
| `/lo-hang/:id` | ShipmentDetail | REAL_BACKED (fake doc actions leftovers) | REAL_BACKED (cleaned) |
| `/tao-lo-moi` | CreateShipment | REAL_BACKED | REAL_BACKED |
| `/theo-doi` | Tracking | REAL_BACKED (no fake GPS — by design) | REAL_BACKED |
| `/khach-hang` | Customers | REAL_BACKED (C1 events) | REAL_BACKED |
| `/kinh-doanh-bao-gia` | SalesQuotes | REAL_BACKED (C1 events) | REAL_BACKED |
| `/thoa-thuan-ban-giao` | Agreements | REAL_BACKED (C1 events) | REAL_BACKED |
| `/hop-dong` | Contracts | REAL_BACKED (C1) | REAL_BACKED |
| `/hop-dong/moi` | NewContract | REAL_BACKED (C1) | REAL_BACKED |
| `/hop-dong/:id` | ContractDetail | REAL_BACKED (C1) | REAL_BACKED |
| `/tai-chinh/thu-tien` | Receivables | REAL_BACKED (C2C) | REAL_BACKED |
| `/tai-chinh/cong-no-doi-tac` | PartnerPayables | REAL_BACKED (C2D) | REAL_BACKED |
| `/ngu-canh-doi-tac` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked "Sắp có") |
| `/tai-chinh/doi-soat` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked, out of scope: reconciliation) |
| `/bao-cao-ceo` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked, out of scope: CEO analytics) |
| `/tra-cuu-thue` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked) |
| `/so-tay` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked) |
| `/dich-thuat` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked) |
| `/nguoi-dung` | placeholder | UNBACKED_PLACEHOLDER | UNBACKED_PLACEHOLDER (marked) → **REAL_BACKED (LOGI_USER_ACCESS_WORKSPACE_01, read-only)** |

Deferred destinations keep real backend capability in the legacy Streamlit
layer (`views/entity_context.py`, `views/translation.py`, `views/tariff.py`,
user admin in LOG-C15) but have **no** component view-model/event surface;
per the sweep rule they were not faked and not given a fabricated page.

## What changed (frontend only)

1. **Dashboard/Home contrast defect (Owner-reported).** The donor gradient
   chain resolves through `@property`-registered custom properties; inside
   the v2 shadow root, browsers whose engine ignores those registrations
   (older Chromium / Android WebView; Owner uses mobile heavily) drop
   `background-image`, leaving light text on the light shell background. Fix:
   inheritable gradient custom-property defaults in `shell.css` (the
   component-owned stylesheet; donor `index.css` untouched) so the *exact
   donor gradient values* resolve everywhere. No markup change, no new color
   system.
2. **Navigation honesty.** The seven deferred destinations are marked
   "Sắp có" in sidebar, mobile drawer and quick-add (flag lives in
   `lib/data.ts` — the reconstructed contract file, not a donor file).
   Sidebar/drawer "Việc Cần Xử Lý" badge shows the REAL open-task count
   (Khẩn + Cần xử lý) instead of the donor sample "6".
3. **Truthful chrome.** Footer no longer claims "dữ liệu minh họa
   09/09/2026" (environment-aware: staging disclosure vs real-data note).
   Global-search empty hints no longer cite sample IDs. Role-switcher menu
   now states it is display-only (real RBAC stays server-side).
4. **Shipment Detail de-faked.** The docs checklist in the Chứng từ tab no
   longer pretends file download/upload (real state chip + real "Bổ sung"
   navigation to the owning input tab, matching the Lấy hàng tab pattern).
   PXK preview fields no longer prefill the sample date "09/09/2026" or a
   sample role; unknown stays blank (UNKNOWN != ZERO).
5. **Deferred placeholder page** now renders the destination name + an
   explicit "Sắp có — chưa triển khai" + a statement that no sample data is
   shown instead, and links back to real pages.

## Verification

- `npm run typecheck` ✓; `npm run build` ✓; `npm run scan` ✓
  (FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0).
- Existing DOM acceptance (real production bundle in jsdom):
  phase_a 21 checks ✓, c2a 9 ✓, c2b 7 ✓, c2c 6 ✓, c2d 6 ✓.
- NEW `tests/component/dom_acceptance_consolidation.mjs` (fixture generated
  by `scripts/gen_consolidation_fixture.py` from the real staging backend):
  10 checks — boot, gradient safety net, sidebar honesty + real badge,
  footer truth, 11 backed destinations render real pages, 7 deferred render
  the explicit placeholder, mobile drawer + bottom-nav route correctly,
  no faked shipment-doc actions/sample PXK date, quick-add consistency,
  route/tab survive a backend rerun.
- Focused backend regression (dispatcher/view-model untouched, run anyway):
  `tests/test_phase_a_component.py`, `test_phase_b_real_data.py`,
  `test_phase_c1_business_contracts.py`, `test_logi_c2a/c2b/c2c/c2d` —
  103 passed ✓.

## Deferred capability gaps (for future backend-adjacent phases)

- `/ngu-canh-doi-tac` — partner-context surface needs a real projection.
- `/tai-chinh/doi-soat` — reconciliation desk (explicitly out of scope).
- `/bao-cao-ceo` — CEO analytics (explicitly out of scope).
- `/tra-cuu-thue` — HS/tax lookup needs component wiring to
  `core.trade_compliance`.
- `/so-tay` — handbook content (no backend source).
- `/dich-thuat` — needs component wiring to `core.deepl_translation` + RBAC.
- `/nguoi-dung` — user/role admin needs component wiring to LOG-C15 auth.
