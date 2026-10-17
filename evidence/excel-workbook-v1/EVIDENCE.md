# LOGI — Generic Excel Upload & Editable Workbook V1

**State:** `INCOMPLETE` for final owner/visual acceptance. The requested functional slice is proven through the existing C1 runtime handlers and the real compiled React bundle in the repository's isolated staging lanes. No customer workbook or production data was used.

## Scope and invariants

- A valid `.xlsx` is safety-checked and stored in the existing GridFS bucket before optional Lục Giác extraction. A parser miss is a successful workbook-only import, not an upload failure.
- Original upload bytes are immutable and SHA256-verified. Workbook changes are separate, owner/customer/source-bound GridFS drafts; reopening loads the latest saved draft. Restore writes a new draft copied from the original.
- The current Python quotation calculation and export allowlist stay authoritative. Source sheets, internal cost, notes and workbook bytes are not copied to the customer quotation. Formula expressions are never executed; missing formula cache is `UNKNOWN`.
- No spreadsheet server, AI extraction, database, or package dependency was added. Formula calculation, FX and tax authority were not moved to the browser.

## Functional runtime proof (isolated staging)

- `tests/test_excel_workbook_edit_v1.py::test_non_template_workbook_without_quote_columns_uploads_views_edits_saves_and_reopens` drives the actual `views.logi_c1.consume_c1_triggers` dispatcher, `quote_import_excel`, workbook view/save handlers, openpyxl and the existing GridFS adapter against isolated mongomock staging.
- The 5,597-byte synthetic XLSX has sheets `Ocean Freight` and `Port charges`. It contains `Route`, `Equipment`, `Rate USD`, a formula, and **no** `Kích thước` / `Size`, `Số lượng` / `Quantity`, or `Đơn giá RMB` / `Price RMB` header. Fixture SHA256: `638f2b0e64535ed9c021f46e20d2bf215d59863b885e632230c17ffabda22bdb`.
- Observed through the dispatcher: workbook-only success message; exact sheet names/order; original values at B4 and D4; formula at D5 remains formula/UNKNOWN. One save changes B4 text to `Ningbo → Hai Phong · checked` and D4 number to `1900`; a fresh view returns both values from draft version 1. Re-reading GridFS returns the byte-identical original and the same SHA256. The separate edited XLSX reopens with both changes and the source formula intact.
- The same focused integration file also covers restore, optimistic version rejection, ownership/RBAC, distant cell ranges and service-only quote/export without fabricated goods or customer leakage.

## Interface / mapping proof

- `tests/component/dom_acceptance_excel_inline_text_edit.mjs` mounts the **built production component bundle** in jsdom. Its synthetic UI readback verifies sheet order, actual grid cell positions, merged-cell display, formula/UNKNOWN display, editable text and number cells in one bounded draft save, parent dirty status, both close/leave confirmation paths, save readback and distant-range navigation. **38 checks pass.**
- `tests/component/dom_excel_workbook_mapping.mjs` verifies explicit range/column/currency and price-role choices, no implicit service quantity, and separate cost-vs-sale semantics. It passes.
- DOM evidence is behavioral, not pixel-based. No screenshot or 1440×900 / 390×844 layout result is claimed.
- A safe Preview/Staging Streamlit process was started with `MONGO_URI` blank and `ENV_IDENTITY=PREVIEW`; its root request returned HTTP 200. The process is local to Arena Preview and does not connect to production. It is not a deployment.

## Test results (2026-10-17)

- Focused Excel/backend suites (`test_excel_workbook_edit_v1`, `test_excel_quote_import_v1`, `test_quote_workbook_view_v1`, `test_excel_fidelity_repair_v1`, `test_excel_text_edit_v1`): **87 passed**.
- Excel inline-workbook DOM acceptance: **38 checks passed**.
- Explicit mapping DOM acceptance: **passed**.
- TypeScript typecheck, production Vite build, process scan and `git diff --check`: **passed**.
- Full-suite baseline comparison on the same Python environment: `origin/main` (`51422c94ddac7d47e67bd87b11a6d6ac55b196d8`) had **31 failed, 1,905 passed, 45 skipped, 10 subtests passed**; the PR branch after this follow-up had **31 failed, 1,913 passed, 44 skipped, 10 subtests passed**. The 31 failing test IDs are exactly identical (`current_only=[]`, `baseline_only=[]`); no new full-suite failures were introduced. The additional passes come from tests already present on the PR branch and this follow-up.
- The excluded `tests/test_partner_reconciliation_desk_write_oracle.py` collection error was also reproduced on both base and branch: `ImportError: cannot import name 'ROUTES' from views.web_app`; it was skipped in both full-suite comparison commands. `tests/test_phase_a_component.py::test_view_model_shape_via_app` remains one of the identical baseline failures; its bare AppTest reaches the unauthenticated bootstrap screen rather than a built view-model.

## Multi-sheet mapping follow-up (2026-10-17)

- `ExcelQuoteWorkspace` now merges an applied mapping into the current quote draft instead of replacing it. Same-source rows are upserted by an opaque stable identity derived from workbook SHA + sheet + source row; overlapping reapplications update rows in place, rows outside the selected range and other options are retained, and a row mapped to the other item type replaces its prior type. A different workbook requires confirmation and starts a replacement draft, avoiding cross-workbook provenance under one source record.
- Removed only the `!currentQuote` visibility guard from the mapping section. A saved quote with an unlocked `unmapped/1` workbook and `commercial_write` can use the existing `quote_edit` path; no new quote flow or backend writer was added.
- `tests/test_excel_workbook_edit_v1.py::test_multisheet_mapping_upserts_through_c1_staging_save_reopen_preview_and_xlsx` uses the actual C1 dispatcher and isolated `SANDBOX_STAGING` mongomock/GridFS backend. It imports a synthetic three-sheet source, fetches each source page through the dispatcher, then constructs explicit mapping payloads in the fixture (the Python fixture mirrors the UI upsert contract; the separate DOM test exercises the actual React mapper and TypeScript merge helper). It maps one Ocean Freight row, a partial then extended Port charges range, reapplies an overlapping row with an updated value, and maps a goods row from a third sheet. Saved quote reads prove **three service lines in one option**, then `SERVICE_ONLY` becomes `GOODS` when goods are added. Reopening retains them; GridFS still returns the original bytes.
- The integration test verifies unknowns stay unknown: mapped service selling prices are unconfirmed until explicitly supplied later; goods quantity and sale price remain `None`; tax stays `None`; FX has only the VND base and no USD/CNY rate. The customer preview and exported XLSX contain only the three explicitly confirmed service prices and no `cost_unit`, `cost_source`, internal notes, sheet names, source filename, or unique cost sentinels.
- Follow-up results: workbook staging tests **7 passed**; multi-sheet DOM mapping/merge **passed** (partial overlap, row upsert, opaque IDs, GOODS/SERVICE_ONLY, alternate-option retention and blank fields); TypeScript typecheck **passed**; Vite production build **passed**; process scan **0 executable hits**; `git diff --check` **passed**. `npm audit` reports one high-severity transitive `source-map-js` advisory (GHSA-68fv-2mgg-jv7q; fix available); no dependency manifest or lockfile was changed, and no audit fix was applied.
- Full-suite baseline failure IDs are identical on `main` and this branch; by test file: `tests/test_agreements_api.py` (1), `test_all_tabs_smoke.py` (1), `test_dashboard_financial_write_oracle.py` (1), `test_entity_context_ui.py` (2), `test_handbook.py` (1), `test_intl_payment_comparator.py` (1), `test_lg08_1_safety.py` (2), `test_log_hotfix_04_dashboard_regression.py` (1), `test_log_rbac_support_01.py` (2), `test_logc12_host_native_runtime.py` (1), `test_logc15_auth_rbac.py` (1), `test_logi_cn_truck_type_persist_01.py` (1), `test_logi_finance_actual_entry_parity_01.py` (2), `test_logi_interaction_latency_repair_01.py` (2), `test_logi_render_performance_01.py` (1), `test_logi_shipment_operational_data_v1.py` (1), `test_logi_shipment_primary_action_unify_01.py` (5), `test_login_visual_compact.py` (1), `test_phase_a_component.py` (1), `test_phase_b_real_data.py` (1), `test_session_truth_repair.py` (1), `test_shipment_slash_route_repair_01.py` (1). Total: **31 baseline failures; zero current-only failures**. The only collection error, `test_partner_reconciliation_desk_write_oracle.py`, also reproduces on both branches. None was changed in this scoped follow-up.
- Browser capability check: **`UNAVAILABLE`** (no browser binary and no Playwright browser API). **`RUNTIME_REVIEWED=NO`; `VISUAL_VERDICT=NEEDS_EVIDENCE`**. jsdom is interaction/DOM evidence only; no screenshots or 1440×900 / 390×844 visual claim.

## Limits and release boundary

- No real customer workbook was available; all workbook bytes above are synthetic and do not certify an unknown customer template.
- `RUNTIME_REVIEWED=NO`; `VISUAL_VERDICT=NEEDS_EVIDENCE` because this environment has no browser/layout engine. The live Preview is available for owner visual review, but that review has not been recorded as pass.
- No changes to Journey. `main` and production were not merged or deployed. The required release boundary is a separate **Draft PR** from the session branch only.
