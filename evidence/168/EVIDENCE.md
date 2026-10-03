# Issue #168 — FORM_07 "Biên bản giao nhận hàng hóa" pilot evidence

Branch: `arena/01a0ffb4-logistics-work-desk-arena` (based on main `cec617ace5f6b7f74d34bb5118b61922a0e36713`).
Date: 2026-10-03. Production mutations: **0** — every run below happened on the
isolated mongomock/GridFS staging sandbox (`views/logi_sandbox.py`) and local git.

## 1. Owner source receipt (input only — never merged, never modified)

| Field | Value |
| --- | --- |
| Transport branch | `owner-input/form07-source-168` (HEAD `51eaaed93cadbc4772959866dce04cf35ffd3e43`) |
| Path on branch | `owner_inputs/form07/Mau-Bien-ban-giao-nhan-hang-hoa.docx` |
| SHA-256 (computed) | `cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5` — **matches the Issue #168 receipt** |
| Size | 18,997 bytes — matches |
| Git blob | `e2c3dea169bff006f4073f7fae2b2c285c912f3f` — matches |
| Status | `VERIFIED_EXACT_BINARY` (pinned in `assets/templates/form07/FORM07.template.json`) |

## 2. Sanitized production derivative (the template that actually renders)

| Field | Value |
| --- | --- |
| Asset | `assets/templates/form07/FORM07-bien-ban-giao-nhan-v1.docx` |
| SHA-256 | `568a89bfe5b2ff84bd295ecc6e378ae9520d4a5d24a84b6a813ac591174d5c56` |
| Size | 16,946 bytes |
| Rebuild | `python3 scripts/form07_build_sanitized_template.py` — deterministic, byte-identical output |
| Bind slots | single-run Jinja tokens (`{{ … }}`, `{%tr for line in goods_lines %}`) |

Sanitization record (full list in `FORM07.template.json → sanitization`):
personal metadata replaced (`cp:lastModifiedBy`, `dc:creator`, `app.xml`
Company, revision/TotalTime/timestamps pinned); source verified free of
transaction data, signatures/stamps, comments, tracked changes, macros,
OLE/ActiveX/DDE, external relationships, remote templates, images and
header/footer parts. Two inert decorative VML underline shapes under the
national motto are intentionally kept (no image, no OLE).
`core/docgen/form07.scan_package_safety` re-checks the banned-artifact list on
**every generation** and on catalog availability (drift ⇒ fail closed).

## 3. Visual comparison (original vs sanitized vs generated sample)

No LibreOffice/pandoc is installable in this sandbox (apt repositories
unreachable) and there is no headless browser, so PNG renders are not
possible. `scripts/form07_render_preview.py` renders the body of
`word/document.xml` structurally (paragraph order, bold/underline, alignment,
table geometry) — an evidence aid, not a Word layout engine:

| File | Rendered from | SHA-256 of the DOCX | Bytes |
| --- | --- | --- | --- |
| `form07-original.html` | Owner original (git blob `e2c3dea…`) | `cd2a1df5…` | 18,997 |
| `form07-sanitized.html` | Git-resident sanitized template | `568a89bf…` | 16,946 |
| `form07-sample.html` | Real `core.docgen.form07` render (staging-shaped facts) | `a0393fef0311ca6322d4a776fd14b9f496faecf745d83e2387c5c3ec2e40eb12` | 16,917 |

Cross-check: the sample SHA-256 is **byte-identical to the R1 attachment the
staging dispatcher really stored** during the end-to-end test and the DOM
fixture generation (`ATT-LO-0295-9857a3c3a299`), proving the deterministic
render path end to end.

## 4. Acceptance test matrix

Python (`tests/test_form07_delivery_receipt.py` — 11/11 passed):

1. `test_source_receipt_and_sanitized_asset_are_pinned_and_safe`
2. `test_template_availability_fails_closed_on_asset_drift`
3. `test_catalog_carries_exactly_one_new_owner_sample`
4. `test_catalog_availability_is_server_gated`
5. `test_no_hardcoded_form07_checkbox_in_shipment_detail`
6. `test_readiness_fail_closed_matrix`
7. `test_render_is_real_deterministic_docx_with_repeating_goods`
8. `test_selection_persistence_and_deselect_keeps_form07_history`
9. `test_viewer_cannot_generate_form07`
10. `test_generate_fails_closed_without_delivery_and_manual_identity`
11. `test_generate_persist_history_and_remount_download_end_to_end`

Full-suite regression: `python3 -m pytest tests -q` on this branch vs a
pristine `git worktree` of main `cec617a` produced **identical** FAILED/ERROR
sets (25 failed / 24 errors, all pre-existing environment failures on main,
e.g. `test_partner_reconciliation_desk_write_oracle.py` importing a `ROUTES`
symbol that never existed in `views/web_app.py`); the branch adds exactly the
11 new passing tests (1655 vs 1644 passed).

Node/TS (after `npm ci` in `component/`):

- `npm run typecheck` — clean.
- `npm run build` — dist rebuilt from source (never hand-edited); `npm run scan` → `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- `node tests/component/unit_shipment_document_picker.mjs` — PASS.
- `dom_acceptance_shipment_document_picker_v1.mjs` — PASS; `dom_acceptance_shipment_attachments.mjs` — PASSED checks=13; `dom_acceptance_shipment_document_review.mjs` — PASSED checks=17; `dom_acceptance_work_module_library_162.mjs` (with `scripts/verify_work_module_library_162.py --fixture`) — PASS.
- **New** `dom_acceptance_form07_delivery_receipt.mjs` — PASS (6 steps). Protocol:

```
python3 scripts/gen_form07_dom_fixture.py --fixture /tmp/form07-dom.json
node tests/component/dom_acceptance_form07_delivery_receipt.mjs /tmp/form07-dom.json
```

The fixture is produced by the REAL staging stack (selection save →
`form07_generate` R1 through `core.docgen.form07` → durable attachment +
immutable history → `shipment_projection` readback + real picker policy). The
DOM test then proves against the production bundle: server-catalog-only
checkbox with durable selection readback; GENERATED card with real provenance;
panel identity fields pre-filled from the server snapshot; exact-bytes download
(SHA-256 match) plus the metadata-only fallback through the existing
`attachment_download` event; R+1 dispatch with the server identity snapshot;
client-side refusal when the typed number is cleared (no invented defaults);
deselection hides the card while history survives; and a blocked
`BLOCKED_NOT_DELIVERED` gate renders the server's own reason/missing facts with
the delivery action.

## 5. Reused surfaces (no parallel stacks)

`document_template_ids` selection field + `shipment_document_selection_save`
event; `core.shipment_document_catalog` (one new row, adapter
`FORM07_DOCGEN`); `core.shipment_attachments` durable store (GridFS in
staging); `docgen_documents` immutable revision history; `attachment_download`
event; existing RBAC (`sales_write`) and Phase-B audit trail. No second
document DB, no template upload UI, no rules DSL, no workflow engine.
