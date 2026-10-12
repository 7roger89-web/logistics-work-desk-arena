# LOGI-195 — Evidence (Issue #195: Shipment Journey gọn và thao tác mượt)

Branch: `ct/logi195-compact-journey-smooth` · Base: `346bc36f92d1c73e61752d96b1f8636a7abe3f3d`
P2P_LAW_SOURCE=LOCAL_PORTABLE · SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
EXPERIENCE_CHECK=NO_MATCH · Skill receipts: p2p-uiux ✓, scope-reality-check ✓ (SHAs verified)

All evidence below was produced against the exact final HEAD unless noted.
Synthetic staging data only (mongomock sandbox, SEA-160/SEA-195); no
production writes. Fonts in the screenshots fall back to system fonts (the
Google Fonts @import was stripped for the isolated sandbox) — layout only.

## 1. Compact Journey (A)

- Default desktop/mobile is the operational overview: toolbar (position +
  problem) + 11-node step strip + Quick Panel + 5 summary cards. No
  718px/620px canvas is mounted by default.
  - `desktop-compact.png` — real Chromium 1536×1024, SEA-160: toolbar
    ("Đang ở", "Cần xử lý: ARRIVAL — Thiếu ETA", "🗺 Bản đồ chi tiết"),
    11 step buttons, problem Quick Panel with CẦN LÀM NGAY.
  - `desktop-detail-map.png` — after clicking "Bản đồ chi tiết": the intact
    detailed 11-node map (PR177 geometry, parallel branch, legend, zoom/fit
    controls) + Quick Panel; the toolbar control becomes "Thu gọn bản đồ".
  - `mobile-390-compact.png` — real Chromium 390×844: compact default,
    step strip in 2 columns, Quick Panel below, bottom nav. Programmatic
    check: `document.documentElement.scrollWidth === clientWidth === 390`
    (no horizontal overflow), map viewport NOT mounted.
- No duplicated journey state: the same `nodes`, `pick`, and panel JSX are
  shared between the compact and detail layouts (one render function,
  `ShipmentJourney.tsx`); the map component is untouched.
- DOM acceptance: `node tests/component/dom_acceptance_logi195_compact_journey_smooth.mjs`
  against `fixture-logi195-dom.json` (built by the real staging stack via
  `scripts/gen_logi195_dom_fixture.py`) — all assertions passed:
  compact default, 11/11 step strip, map opens/closes with 11/11 nodes,
  node picks dispatch nothing, CUSTOMER_SELF recovery path, picker checkbox
  not selection-locked, exactly one selection-save dispatch.

## 2. CUSTOMER_SELF UX (B)

- Backend identity gate UNCHANGED: `validate_flow_write` still refuses
  CUSTOMER_SELF without a canonical `customer_id` (no fuzzy name guessing).
- New guided recovery in `ShipmentDetail.tsx` (commercial-flow section): when
  CUSTOMER_SELF is chosen and the shipment lacks `customer_id`, an inline
  panel offers the EXISTING customer master + the EXISTING
  `shipment_customer_save` writer; the flow confirm stays locked until the
  authoritative readback returns the customer.
- Handler-level proof (`tests/test_shipment_document_picker_v1.py::
  test_customer_self_refused_without_customer_id_then_confirmed_after_real_customer_assigned`,
  staging sandbox): refuse (COMMERCIAL_FLOW_REFUSED) → unknown customer
  refused → assign CUST-ANPHAT via existing writer → confirm CUSTOMER_SELF
  passes with `legalImporterName == "An Phát JSC"`. PASS.
- TT_ENTRUSTED_DIRECT / TT_ENTRUSTED_SUB untouched (existing tests pass).

## 3. Template selection vs generation readiness (C)

- Client (`ShipmentDocumentPicker.tsx`): removed the `!template.available`
  coupling from the checkbox selection lock. Disabled = `!template.active`
  only. The option still shows the server's `availabilityReason` plus the
  honest note "vẫn chọn được để theo dõi; tạo bản mới vẫn bị khóa."
- Backend (`_handle_shipment_document_selection_save`): removed the
  `DOCUMENT_ACTION_UNAVAILABLE` refusal. Validation that remains: known +
  active catalog (UNKNOWN_TEMPLATE/INACTIVE_TEMPLATE), RBAC
  (`shipment_edit`), version guard, authoritative readback.
- Generation gates UNCHANGED and still fail-closed: selecting an unavailable
  template saves, but `pxk_generate` is refused by its own readiness gates
  (proven: BLOCKED_NOT_DELIVERED on an undelivered shipment;
  `evaluate_document_readiness` still gates template/storage).
- Fresh runtime checks UNCHANGED: `_shipment_document_picker_policy` still
  fresh-checks `attachmentPolicy.storageConfigured`/`storageLabel` and
  `catalog availabilityReason` on every build; nothing is assumed or
  fake-unlocked.
- Tests (`tests/test_shipment_document_picker_v1.py`): unknown/inactive/stale
  still refused with no mutation; active-but-unavailable PXK selection now
  SAVES (gate=SAVED, readback carries PXK); generation after selection stays
  refused. 8/8 PASS.

## 4. Smoothness / latency (D)

MEASURE FIRST — interaction-latency harness extended with two new intents
(`tests/test_logi_interaction_latency_finalize_02.py`), N=95 shipments,
isolated mongomock, RTT_MODEL=0:

| intent | callback (Save/Confirm) | handler | writer | readback | post-action build |
|---|---|---|---|---|---|
| shipment_commercial_flow_save | 19.3 ms | 18.7 ms | 3.7 ms (4 ops) | 9.9 ms (17 ops) | 2595.6 ms (27 ops, cold) |
| shipment_document_selection_save | 10.3 ms | 9.8 ms | 3.4 ms (4 ops) | 0.9 ms (2 ops) | 676.1 ms (27 ops) |

- Invariants hold for both: HANDLER_CALLS_PER_INTENT=1, VM_BUILDS_PER_INTENT=1,
  EXPLICIT_SECOND_RERUNS=0, authoritative readback, fresh RBAC.
- Dominant phase found: the POST-ACTION full view-model rebuild, not the
  save. Root cause: `effective_catalog()` rebuilt PER SHIPMENT row, each
  rebuild re-reading the `app_settings` template registry → 99
  `app_settings.find_one` per build (build ops 121).
- Minimal fix (no Redis/queue/cache rewrite, no long-lived cache): the
  render-stable catalog and registry rows are read ONCE per build and shared
  (`views/logi_view_model.py`, `views/logi_real_data.py`,
  `core/docgen/uploaded_template_store.py`, `views/logi_docgen_upload.py`).
  Build ops: **121 → 25**, `app_settings.find_one`: **99 → 3**, with byte-
  identical shipment projections (verified by direct comparison).
- The stale `<= 18` build-op budget (predates LOGI-193's once-per-build
  additions) was recalibrated to `<= 26` with the N+1 guards kept strict
  (`contracts.find_one == 0`, every collection `find <= 1`,
  `app_settings.find_one <= 3`, nothing per shipment).
- LATENCY_BEFORE for the two new intents: unmeasurable — the harness fixture
  was already broken on BASE_MAIN (see §6). The save paths themselves were
  not changed by the C-lane edit except removing the refusal branch; the
  new tests assert identical lifecycle invariants on both sides.
- Local interactions proven zero-dispatch in the DOM test: journey node pick,
  commercial-flow radio, document checkbox — all pure local state; only
  Save/Confirm dispatches (exactly one event per intent).

## 5. Regression

- `npx tsc --noEmit` — PASS.
- `npm run build` (component/dist rebuilt) + `npm run scan` — PASS
  (FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0).
- Focused suites (run in their file groups): latency file 18/18, picker 8/8,
  shipment_document_workflow, render_performance, DOM acceptance — all PASS.
- Full Python suite comparison, base (346bc36f) vs this branch, identical
  invocation (`pytest tests`, ignoring the pre-existing
  test_partner_reconciliation collection breakage):
  - base:   80 failed, 1217 passed, 45 skipped, 532 errors
  - branch: 80 failed, 1218 passed, 44 skipped, 536 errors
  - The per-test diff (comm on the FAILED/ERROR sets) shows the ONLY new
    entries are this change's own new/renamed tests, and they error in the
    full-suite run by the SAME mechanism as every other test in their two
    files (see §6 item 3) — all pass in their file groups. No genuine
    regression from this change.

## 6. Pre-existing issues found (not introduced here)

1. `tests/test_logi_render_performance_01.py::_real_pxk_document` was broken
   on BASE_MAIN: `pxk_generate` now requires a confirmed commercial flow
   (COMMERCIAL_FLOW_REQUIRED), but the fixture generated PXK without one.
   Fixed minimally by confirming TT_ENTRUSTED_DIRECT through the real
   `shipment_commercial_flow_save` event first. This un-breaks all four
   latency truthful_readback tests on base too.
2. `tests/test_partner_reconciliation_desk_write_oracle.py` fails collection
   on BASE_MAIN: `cannot import name 'ROUTES' from 'views.web_app'`
   (product drift, unrelated to LOGI-195). Excluded from the run; left
   untouched.
3. Full-suite test pollution (pre-existing on base, identical pattern on
   the branch): running `pytest tests` in one process produces
   80 failed / 532-536 errors on BOTH base and this branch, including every
   test in `tests/test_logi_interaction_latency_finalize_02.py` and several
   others (LibreOffice/docxtpl missing, streamlit app-execution cascade,
   cross-file state pollution). The per-test FAILED/ERROR diff between base
   and branch shows zero genuine regressions; all LOGI-195-focused tests
   pass when run in their file groups (latency 18/18, picker 8/8).

## 7. OE_GATE — “Không bị over engineering chứ?”

- SIMPLER_PATH=YES: compact overview reuses the existing panel/summary-card
  JSX (one shared render function); no new journey engine, no new store.
- MATERIAL_PROGRESS=YES: owner-visible smaller first screen + measured
  121→25 build-op cut for every Save/Confirm.
- NECESSITY=YES: each of the four owner complaints got exactly one bounded
  fix; generation gates, RBAC, and identity gates untouched.
- CORE_BEFORE_SUPPORT=YES: journey truth, selection writer, and latency
  invariants first; no new design system/workflow/router.
- SMALLER_VERIFIABLE_SLICE=YES: one branch, one draft PR, no merge/deploy.
- **OE_VERDICT=DO_IT** — the slice is the smallest that resolves all four
  findings without touching unrelated pages.

## Artifact hashes (SHA-256)

See SHA256SUMS in this directory. Fixture: `fixture-logi195-dom.json`
(real staging stack output, SEA-160 + SEA-195).
