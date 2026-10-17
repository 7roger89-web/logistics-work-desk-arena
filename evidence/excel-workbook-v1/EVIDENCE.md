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
- Full suite remains non-green: skipping the existing `tests/test_partner_reconciliation_desk_write_oracle.py` collection error yielded **1,912 passed, 44 skipped, 31 failed, 10 subtests passed**. The collection error is that the test imports missing `ROUTES` from untouched `views/web_app.py`; the 31 failures span other existing modules/tests and have not been baseline-verified or changed in this scoped branch. `tests/test_phase_a_component.py::test_view_model_shape_via_app` also fails under bare AppTest because it reaches the unauthenticated bootstrap screen rather than a built view-model; the actual safe staging server smoke returned 200.

## Limits and release boundary

- No real customer workbook was available; all workbook bytes above are synthetic and do not certify an unknown customer template.
- `RUNTIME_REVIEWED=NO`; `VISUAL_VERDICT=NEEDS_EVIDENCE` because this environment has no browser/layout engine. The live Preview is available for owner visual review, but that review has not been recorded as pass.
- No changes to Journey. `main` and production were not merged or deployed. The required release boundary is a separate **Draft PR** from the session branch only.
