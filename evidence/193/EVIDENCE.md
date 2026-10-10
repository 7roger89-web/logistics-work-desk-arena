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

---

# Round 2 — CONTROL_TOWER_VERDICT=REJECT: four source blockers fixed

Reviewed head: `451e015bc6001c4ab96015b30cca5f229e335a3e`. All four blockers were
first **reproduced by a failing test**, then fixed, then re-run.

## B1 — Retired template could still be generated

`_handle_uploaded_template_generate()` called `store.active_version(template)`
and only checked `if not version`. `set_active()` retires by flipping `status`
while deliberately keeping `activeVersion` and the version rows (history must
stay readable), so a retired template still had a version and a forged
`uploaded_template_generate` naming its id would produce a new file.

- `views/logi_view_model.py`: status is now checked **before** the version.
  `RETIRED` → gate `TEMPLATE_RETIRED` (`failClosed=True`); any other non-ACTIVE
  status → `TEMPLATE_NOT_PUBLISHED`, so a DRAFT still reports "not published".
- `core/docgen/uploaded_template_store.publish()`: an already-`ACTIVE` row is
  refused. `create_draft()` always mints a NEW template, so a second publish
  could only ever freeze identical bytes + mapping into a duplicate version.
- Tests: `test_a_retired_template_cannot_be_generated_by_a_direct_event`
  (refused, gate `TEMPLATE_RETIRED`, `_count_durable_writes` unchanged → zero
  attachment and zero metadata rows, and the earlier R1 file still downloads as
  a real `PK` package);
  `test_publishing_an_already_active_template_does_not_create_a_new_version`
  (refused, `len(versions) == 1`, `activeVersion == 1`).

## B2 — OOXML scan order + relationship detection

`scan_package_safety()` called `archive.testzip()` first. `testzip()` fully
decompresses every member to CRC-check it, so the part-count / uncompressed-size
/ compression-ratio limits ran *after* the bomb had already been inflated.

- Restructured into two phases. **Phase 1** reads only the ZIP central
  directory (`infolist()`) and enforces part count, total declared uncompressed
  bytes and per-member compression ratio; if any fails it returns **without
  touching a member**. **Phase 2** — reached only for a bounded package — runs
  `testzip()` and the content scans.
- Part-*name* checks (banned parts, macro-enabled names) are free, so they were
  moved next to the content scan rather than short-circuiting it: a trojan
  carrying both a macro part and an external relationship must report **both**.
- `_EXTERNAL_REL_PATTERN` (a regex matching only `TargetMode="External"` /
  `Target="scheme:`) is **deleted**. Relationships are now parsed with
  `xml.etree.ElementTree` in `_external_relationship_parts()`, which checks the
  *value*, not the spelling: single quotes, reordered attributes and odd
  whitespace all normalise away. An unparseable `.rels` is reported, never
  silently passed. An external scheme with no `TargetMode` is also refused.
- Tests: `test_uncompressed_limits_are_checked_before_any_member_is_decompressed`
  monkeypatches `ZipFile.testzip` **and** `ZipFile.read` to raise, then shrinks
  each limit in turn — the scan still refuses, proving no member was inflated.
  (The fixture is built *before* the spies are armed: python-docx itself calls
  `ZipFile.read` while assembling a package.)
  `test_external_relationships_are_refused_whatever_quote_style_is_used` is
  parametrised over double-quoted, **single-quoted**, reordered-attribute and
  single-quoted-`file:` forms — only the single-quoted ones failed before the
  fix. `test_an_internal_relationship_is_not_refused_by_the_xml_scan` and
  `test_an_ordinary_file_still_passes_the_reordered_safety_scan` guard against
  over-blocking.

## B3 — Ambiguous customer identity

`_uploaded_template_source()` fell back to `next(customer whose name matches)`.
Two customers can share a registered name with different ids and tax codes, so
this could print one company's tax code on another's document — and `next()`
over a dict is not even stable. The readiness projection meanwhile used **only**
the canonical link, so the two surfaces already disagreed.

- One shared resolver, `_resolve_uploaded_template_parties()`, now backs **both**
  the readiness projection and the generation handler.
  `_resolve_uploaded_template_customer()` accepts the canonical `customer_id`
  link, and a free-text name match **only when exactly one candidate exists**;
  zero or several resolve to `{}`, which readiness turns into `MISSING_INFO`.
- The dead `BLOCKED_AMBIGUOUS_SOURCE` return (the handler discarded it as
  `_gate`) was removed rather than kept as a second code path.
- Tests: `test_two_customers_sharing_a_name_never_resolve_to_one_of_them`
  (two same-named customers with different tax codes → generation refused with
  gate `MISSING_INFO`, resolver returns `{}`, readiness says `MISSING_INFO`);
  `test_a_unique_customer_name_match_is_still_accepted` (a provably unique name
  still resolves, with the right tax code).

## B4 — Admin could not see the result before activating

- `core/docgen/uploaded_template.py`: `preview_facts()` derives obviously-fake
  values from `CANONICAL_FIELDS` itself, every one prefixed `[DU LIEU THU]`, so
  the preview can never drift from what is bindable and never contains a real
  identity, tax code, amount or date. `render_preview()` reuses the **production**
  `resolve_mapping` + `render_uploaded`, and returns `(bytes, missing)`.
- `core/docgen/uploaded_template_store.preview_source()`: reads the DRAFT bytes
  + still-editable mapping (or the active version for a published template).
  Read-only.
- New event `docgen_template_preview` on the same dispatcher, behind the same
  `_admin_gate()`. Returns base64 + fileName (`XEM-THU_…`) + sha256 + `missing`
  + `persisted: false`. **Writes nothing.**
- `/bieu-mau` gains one `GhostBtn` per row ("Xem thử (dữ liệu giả)") on DRAFT and
  ACTIVE. On the outcome it downloads the trial file and, if positions are
  unresolved, shows them in an amber notice. No editor, no viewer framework.
- Tests: `test_admin_can_preview_a_draft_before_publishing_it` (bytes are a real
  `PK` package, sha256 matches, the marker is present, and **no** real staging
  customer name / tax code / shipment id appears);
  `test_a_preview_writes_no_attachment_metadata_or_shipment_record` (durable row
  counts unchanged, registry length unchanged, still `DRAFT`, no `activeVersion`,
  no versions, still absent from the picker catalog);
  `test_a_non_admin_cannot_preview_a_template` (`BLOCKED_PERMISSION_DENIED`);
  `test_a_preview_reports_unresolved_positions_instead_of_filling_them` (an
  operator-typed field with no value is **named** in `missing`).

## Round 2 results

- `tests/test_logi_193_uploaded_office_templates.py` — **65 passed** (was 50).
- Targeted lane (`form07|docgen|document_picker|shipment_document|gnt|attachment`)
  — **340 passed, 16 skipped, 4 errors**; `comm` against the baseline lane
  re-derived at `b80267a` in a clean worktree: **0 new, 0 fixed** (4 == 4).
- `npx tsc --noEmit` → exit 0. `npm run build` → 1915 modules, js 1,411.47 kB,
  css 81.76 kB. `npm run scan` → `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
  `component/dist` rebuilt from source and committed.
- `dom_acceptance_logi193_uploaded_templates.mjs` → **PASS** (11 groups), still
  including the download pending → resolve → next-file lifecycle.
- `dom_acceptance_form07_delivery_receipt.mjs` → **PASS**;
  `unit_shipment_document_picker.mjs` → **PASS**.
- Rendered-file sha256 values are unchanged from round 1
  (`7e163a6c8152cb3d…` / `5924121785ea597a…`) — the fixes did not alter output
  bytes for a valid generation.

Visual evidence remains **BLOCKED** (§5): still no browser binary in this
sandbox. The new preview control is covered by DOM assertions and by the Python
tests above, but its pixels have not been seen in a real browser.

---

# Round 3 — Independent Source Review R2 (REJECT): B5 / B6 fixed

Reviewed head: `19c4c26f23dedf654cdd41c3e581bb01a5c10c5e`. Both defects were
reproduced from the committed source **before** any edit.

## B5 — DOCX destroyed printed text adjacent to an inline token

Reproduced directly against the committed code:

```
run text : 'Xác nhận: {{shipment.id}} (đã kiểm)'
rendered : 'LO-0295'
```

`_MARKER_PATTERN.search(current)` detects a token **anywhere inside a run**, but
`_render_docx()` did `run.text = str(value)`, replacing the whole run. The
printed label `Xác nhận:` and the trailing note `(đã kiểm)` were silently
deleted — a legal wording change no operator can see.

**Fix** — `_replace_tokens_in_run()`: if the run contains a `{{token}}`, only the
token spans are substituted (`_MARKER_PATTERN.sub`), so every non-token
character is preserved verbatim. If the run has no token (a blank run, or a kept
label + blank tail) the whole run is the fill target exactly as before. No Jinja,
no second engine, no layout logic. One position carries one confirmed value, so
every token span in that run receives it — detection offers one position per run,
which is the limit of what an Admin can map.

**Red → green**:
| test | before | after |
|---|---|---|
| `test_an_inline_token_keeps_the_static_text_on_both_sides_of_it` | FAIL (`'LO-0295'`) | PASS — full paragraph equals `Xác nhận: LO-0295 (đã kiểm)` |
| `test_several_tokens_in_one_run_are_each_replaced_in_place` | FAIL | PASS — prefix `Lô ` and suffix `— hết` kept, no residual `{{` |
| `test_a_run_that_is_only_a_token_still_renders_as_the_bare_value` | PASS | PASS — no stray whitespace introduced |

## B6 — Template IDs collided for long names within one minute

`new_template_id()` built `f"UT-{slug[:24]}-{%Y%m%d%H%M%S}"[:40]`. At a 24-char
slug that string is **42** chars, so the slice removed the last two digits — the
**seconds** — leaving `YYYYMMDDHHMM`. Reproduced against the committed code:

```
new_template_id('Biên bản giao nhận hàng hóa') -> 'UT-bi-n-b-n-giao-nh-n-h-ng--20261010100803'[:40]
                                                -> 'UT-bi-n-b-n-giao-nh-n-h-ng--202610101008'   (seconds gone)
```

`create_draft()` appended the id with no uniqueness check and `get_template()`
returns the first match, so a later same-name upload could map and publish the
**wrong file**.

**Fix** — the budget is now sized so nothing is truncated:
`UT-` (3) + slug (16) + `-` (1) + `%y%m%d%H%M%S` (12) + 4 random base-36 chars
(`secrets.choice`) = **36** chars ≤ 40. `create_draft()` additionally refuses to
append an id already present in the registry. Existing stored ids and history are
untouched — only newly generated ids change shape.

```
UT-bi-n-b-n-giao-nh-26101008054779a7   (36 chars)
UT-bi-n-b-n-giao-nh-261010080547av33   (36 chars)  — same second, different id
```

**Red → green**:
| test | before | after |
|---|---|---|
| `test_two_same_name_uploads_in_the_same_minute_get_different_ids` | FAIL — `both uploads produced 'UT-bi-n-b-n-giao-nh-n-h-ng--202610101209'` | PASS — clock frozen, two different ids, each independently published and generating its own file (`Số hợp đồng` vs `Số booking`, different attachments and hashes) |
| `test_template_ids_never_exceed_the_declared_maximum` | PASS | PASS — 400-char, repeated, punctuation-only and empty labels all stay ≤ 40 |

## Round 3 results

- `tests/test_logi_193_uploaded_office_templates.py` — **70 passed** (was 65).
- `npx tsc --noEmit` exit 0. `npm run build` → 1915 modules, js 1,411.47 kB,
  css 81.76 kB. **The rebuilt `dist` is byte-identical to the committed one**
  (`git status --porcelain component/dist` empty), confirming B5/B6 are
  backend-only and the committed `dist` is genuinely built from source.
- `npm run scan` → `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- Targeted lane (`form07|docgen|document_picker|shipment_document|gnt|attachment`):
  **340 passed, 16 skipped, 4 errors**; baseline lane re-derived at `b80267a` in
  a clean worktree = 338 passed / 4 errors, and `comm` on the FAILED/ERROR sets
  shows **0 new, 0 fixed**.
- `dom_acceptance_logi193_uploaded_templates.mjs` **PASS**;
  `dom_acceptance_form07_delivery_receipt.mjs` **PASS**;
  `unit_shipment_document_picker.mjs` **PASS**.
- Generated-file sha256 unchanged (`7e163a6c8152cb3d…` / `5924121785ea597a…`) —
  the pilots fill blank runs, not inline tokens, so B5 correctly leaves their
  output identical.

## GNT intermittent failure — status after round 3

It recurred **once** in this round's first targeted-lane run, then did **not**
recur in 18 further identical lane runs. It has never produced a traceback
despite `--tb=long` on every attempt. Bounded findings:

- Baseline lane at `b80267a`, 6 consecutive runs: **clean every time** (338 passed / 4 errors).
- In the filtered lane the GNT test collects at position **22**; the only two
  LOGI-193 tests the `-k` filter selects collect at positions **169–170**, i.e.
  strictly *after* it, so they cannot influence it.
- The LOGI-193 source paths are gated behind uploaded templates:
  `_attach_uploaded_template_state()` returns early when no ACTIVE uploaded
  template exists, which is the case throughout that test.
- Passes in isolation and alongside the LOGI-193 module.

This is **not** claimed to be a baseline defect, and it is **not** diagnosed.
It remains an explicit residual risk. Per instruction, no endless full-suite
looping was performed.

Visual evidence remains **BLOCKED**: no browser binary in this sandbox.
