# LOGI-193 — Admin upload and auto-fill Office shipment templates

Issue: [#193](https://github.com/7roger89-web/logistics-work-desk-arena/issues/193)
Branch: `arena/a5762bf9-logistics-work-desk-arena`
Base: `b80267a1e5de5ea5cbbeadc51455369c47ebf346`
Status: **draft — NOT merged, NOT deployed, no production write.**

## 1. Law / preflight receipts

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE (.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md)
PORTABLE_FILE_SHA256=75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e
PORTABLE_HEADER_SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
CANONICAL_PROBE=UNREACHABLE_HTTP_403 (gh api repos/7roger89-web/P2P-upgrade-github-1/contents/docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md)
INSTALLED_PROJECTION=ABSENT (.p2p/system holds only p2p_capabilities/review_extension_activation.py, no law projection)
TARGET_LAW_FRESHNESS=CURRENT (portable header SHA == required canonical SHA)
EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb | AUTHORITY=NON_AUTHORITATIVE_VERIFIED_EXPERIENCE | SOURCE=PORTABLE_CAPSULE
```

## 2. What was built (reuse, not a second system)

| File | Role |
|---|---|
| `core/docgen/uploaded_template.py` | Detection, mapping normalisation, fail-closed readiness, deterministic OOXML render. Owns no storage. |
| `core/docgen/uploaded_template_store.py` | Registry in `app_settings` + bytes in GridFS bucket `docgen_template_files` (same storage plane). Draft → publish (immutable version) → retire. |
| `views/logi_docgen_upload.py` | 4 Admin events through the EXISTING dispatcher; `can_operate_business("*")` gate. |
| `core/shipment_document_catalog.py` | `effective_catalog()` = the ONE authority for picker + validator + row projection. |
| `views/logi_view_model.py` | Per-shipment readiness/history projection, selection validation, generation handler. |
| `component/src/pages/DocgenTemplates.tsx` | `/bieu-mau` Admin workspace. |
| `component/src/pages/ShipmentDetail.tsx` | Template panel + generate/download actions. |

No Jinja/docxtpl, no expression evaluator, no per-template code module, no new
storage plane, no new workflow framework.

## 3. Tests

### Python — `tests/test_logi_193_uploaded_office_templates.py`: **50 passed**

Covers detection (DOCX/XLSX/marker/label-neighbour), upload safety (legacy
`.doc`/`.xls`, `.docm`/`.xlsm`, non-OOXML, oversized, missing core part, macro
part, external relationship, zip-bomb ratio, ordinary theme-colour false
positive), forged mappings (`shipment.data.2.7.receiver_name`,
`__import__('os').system('id')`, `{{ 7*7 }}`, `; DROP`, `db.shipments.find()`),
the structural absence of any money/payment/VAT/currency field, fail-closed
readiness, verbatim quantity printing, deterministic render, SHA pin, RBAC,
DOCX + XLSX end-to-end, immutable re-publish, retire-keeps-history, replay
safety, and FORM_07 regression.

### Targeted regression lane: **340 passed, 16 skipped, 3 errors**

`-k "form07 or docgen or document_picker or shipment_document or gnt or attachment"`.
All 3 errors are pre-existing and present in the baseline list
(`test_logi_render_performance_01.py` ×2, `test_logi_interaction_latency_finalize_02.py` ×1).

### Full suite vs TRUE BASELINE (same venv, both re-run this session)

| | failed | passed | skipped | errors |
|---|---|---|---|---|
| baseline `b80267a` | 30 | 1699 | 45 | 25 |
| this branch | 29 | 1751 | 44 | 25 |

`comm` on the sorted FAILED/ERROR id lists: **0 new, 0 fixed** (54 lines each,
exact set match).

### Frontend

- `npx tsc --noEmit` → exit 0.
- `npm run build` → ✓ 1915 modules, `dist/logi-shell.js` 1,409.96 kB, `dist/logi-shell.css` 81.76 kB. **`component/dist` is committed and rebuilt from source.**
- `npm run scan` → `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- `node tests/component/dom_acceptance_logi193_uploaded_templates.mjs /tmp/logi193-dom.json` → **PASS** (10 assertions groups).
- `node tests/component/dom_acceptance_form07_delivery_receipt.mjs /tmp/form07-dom.json` → **PASS** (FORM_07 regression).
- `node tests/component/unit_shipment_document_picker.mjs` → **PASS**.

## 4. Runtime DOM acceptance

```
.venv/bin/python scripts/gen_logi193_dom_fixture.py --fixture /tmp/logi193-dom.json
node tests/component/dom_acceptance_logi193_uploaded_templates.mjs /tmp/logi193-dom.json
```

The fixture is produced by the REAL staging stack (logi_sandbox mongomock +
GridFS, the real dispatcher, the real projections): Admin upload → mapping
confirm → publish (DOCX + XLSX) → the EXISTING selection event →
`uploaded_template_generate` → durable attachment → `build_view_model()`
readback + real picker policy. Shipment `LO-0295`.

| Template | Detected / mapped | Output | sha256 |
|---|---|---|---|
| DOCX `UT-bb-i-chi-u-giao-nh-n-…` | 6 / 6 | `BB-I-CHI-U-GIAO-NH-N_LO-0295.docx` | `7e163a6c8152cb3d…` |
| XLSX `UT-b-ng-k-l-h-ng-…` | 11 / 11 | `B-NG-K-L-H-NG_LO-0295.xlsx` | `5924121785ea597a…` |

Reproducible: the pilot builders pin `docProps/core.xml` timestamps and ZIP
entry mtimes (openpyxl's writer unconditionally resets `dcterms:modified` to
`now()` at `openpyxl/writer/excel.py:292`), so two independent runs of the
generator produced identical SHA-256 values.

Proven in the DOM against the production bundle:

1. Both Admin-published templates render with real version + author binding.
2. The upload surface takes its accept list and size limit from the server projection.
3. The safety-boundary wording is server-owned.
4. A published version has no in-place mapping editor (immutable); it can only be retired.
5. A non-Admin gets the same list and zero write controls.
6. Both templates reach the picker as cards with real revisions.
7. **Download lifecycle**: first download dispatches exactly one bounded
   `attachment_download` carrying only `{attachmentId, requestId, shipmentId}`;
   a second click while it is in flight is ignored (guard intact); after the
   backend echoes the same `requestId` through `lastWrites`, a **different**
   file downloads. Stored bytes match the pinned SHA-256 and start with `PK`.
8. An unresolved operator-typed field renders the server's own wording, exposes
   "Bổ sung thông tin biểu mẫu", invents no output block and never dispatches a
   generation.

**Mutation check**: disabling `setDocumentDownloadPending("")` in
`ShipmentDetail.tsx` and rebuilding makes the harness fail at *"after the
backend resolves the first request, a different file downloads"* (`1 !== 2`).
The assertion is not vacuous. The source was restored and rebuilt afterwards
(`grep -c MUTATION-TEST` → 0).

## 5. Visual evidence — **BLOCKED**

This sandbox has **no browser binary**: no `chromium`/`firefox`/`webkit` on
`PATH`, none in `dpkg -l`, no `~/.cache/ms-playwright`, and the Playwright CDN
is unreachable (`curl https://cdn.playwright.dev/` → `000`, while
`registry.npmjs.org` → `200`). No real-browser screenshot at 1440x900 or
390x844 could be produced, and **no visual PASS is claimed**.

A render harness exists so a human can complete this step in a real browser:

```
.venv/bin/python scripts/gen_logi193_dom_fixture.py --fixture /tmp/logi193-dom.json
.venv/bin/python scripts/preview_logi193_dom.py --fixture /tmp/logi193-dom.json --port 8600
```

It serves the ACTUAL `component/dist/logi-shell.js` + the real staging payload
inside a true-viewport iframe (buttons switch 1440x900 / 390x844) and touches no
database. Handoff checklist for the reviewer:

- [ ] `/bieu-mau` — Admin list, upload surface, publish/retire controls.
- [ ] Mapping dialog — detected positions + field whitelist grouped by section.
- [ ] Shipment `LO-0295` → Chứng từ — both uploaded templates as picker cards.
- [ ] Generate → download → the returned file opens and matches the sha256 above.
- [ ] 390x844 — no horizontal page overflow; cards and CTAs remain tappable.

## 6. Known limitation (accepted, not hidden)

Arbitrary unmarked Office files do **not** map perfectly without one-time Admin
review. XLSX label-neighbour detection prefers right-then-below, so a
*suggestion* can point at the wrong cell; suggestions are review aids and the
Admin confirms the mapping once. Nothing is auto-published from a suggestion.

## 7. Residual risk — the intermittent GNT failure

During earlier full-suite runs on this branch (under a previous venv),
`tests/test_gnt_and_docgen_reality_check.py::test_gnt_revision_comes_from_durable_docgen_metadata_after_session_clear`
failed **once in 4 runs**; the baseline was clean 5/5 at that time. This is
**not** claimed to be a baseline defect.

Investigation and its limits:

- Passes in isolation (`14 passed`) and when run together with the LOGI-193 module (`63 passed`).
- The 29 test files that execute *before* it ran clean 3/3.
- Collection order puts that file at position 29 and the LOGI-193 module at 66, so the new test module cannot influence it.
- `logi_c1.stored_outputs()` (reached by the new history projection) is a pure read with no session write, so the new code path cannot mutate the state that test manipulates.
- 9 further full-suite runs on the branch did not reproduce it.
- Under the current venv, the final branch run and the re-derived baseline run produce **identical** FAILED/ERROR sets, and that test is in neither.

Residual risk: a real ordering/timing-sensitive interaction cannot be fully
excluded, because the one observed failure was never captured with a traceback.
Recommended supervisor action: if it recurs, capture `--tb=long` for that single
test and treat it as a branch defect until disproved.
