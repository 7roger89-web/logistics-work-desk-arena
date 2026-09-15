# LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — practical Finance Actual service-line entry: acceptance evidence

TASK `LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01` · ROLE `IMPLEMENTER`
Branch `arena/01a0a341-logistics-work-desk-arena` (Arena-pinned; base = `main` @ `7883144`)
Existing shipment proven: **`LO-0308` — Minh Đức JSC**, currency **VND** (read-only)
Throwaway lot used for writes: `LO-PARITY-0001`, inside the isolated staging database
`logistics_staging` (mongomock). `logistics_db` / `logistics_pilot` were never connected.

Owner outcome: Lô Hàng → **Tài chính / Công nợ** regains the operational
"DỊCH VỤ & CHI PHÍ THỰC TẾ" entry of the previous app — service picker from the
ONE existing catalog, full line fields, and correction of the SAME row — without
a new finance model, table, collection, API, ledger or service layer.

## Canonical source actually reused

| Layer | Source | Reused as |
| --- | --- | --- |
| Service catalog | `core.config.GETFLY_SERVICES_LIST` (27 entries `{code,name,unit,group}`) | `views.logi_real_data.finance_service_catalog()` → `ViewModel.financeServiceCatalog` → one `<select>` with `<optgroup>` by `group`. **No service list exists in React** |
| Actual lines | `shipments.data["3.4"].details` | `views.logi_real_data.finance_projection()` → `shipment.finance.actual` |
| Write path | event `finance_actual_save` | `views.logi_view_model._handle_finance_actual_save` → `finance_write` RBAC → fresh `read_shipment` → `apply_financial_snapshot` → `save_shipment_atomic` → audit → fresh readback → forced fresh view-model |
| Money parsing | `core.utils.to_decimal` / `smart_money_parse` | unchanged; `parseAmountVN` in `component/src/lib/format.ts` is the browser mirror used only to refuse blanks and drive the display preview |

## Journey actually run (staging, real writers, real readbacks)

| # | Step | Result |
| --- | --- | --- |
| 1 | Open Finance Actual on `LO-0308` | 1 booked line read back with `id 79d373a8-…`, `code DV-VC-TQ`, `unit Lần`, `qty 1`, `cost 57.000.000`, `price 62.000.000`, `VAT 8%`, `note ""` |
| 2 | Catalog projection reaches the component | `financeServiceCatalog` = 27 entries, first `DVK · Phí dịch vụ khác · Lần · DỊCH VỤ XNK`, last `CO · Xin C/O` |
| 3 | Create a lot + book one service line | `finance_actual_save` `qty 2 · cost 1.100.000 · price 1.500.000 · VAT 8 · note "2 bộ chứng từ lô CAN-HAN"` → `lineId PAY-LINE-7138BE871883`, `lineCount 1`, `receivable 3.240.000`, `cost 2.200.000`, audit `[create, update]` |
| 4 | Edit the SAME `line.id` | values `cost 1.200.000 · price 1.800.000 · VAT 10 · new note` → same id kept, `lineCount 1`, receivable `3.960.000`, payable `2.400.000`, profit `1.200.000`, margin `33.33%`, audit `[create, update, update]` |
| 5 | UNKNOWN ≠ ZERO | blank cost/price/VAT → `ok=false`, message `Chưa nhập: Giá bán, Giá vốn, VAT % — dòng thực tế phải nêu rõ số tiền (0 là giá trị hợp lệ; để trống không phải là 0).`, `requestId` echoed, `data.3.4` byte-identical before/after |
| 6 | Explicit `0` is an answer | `cost 0 · price 0 · VAT 0` accepted → booked as `0.0`, row appears with `0,00 VND` |
| 7 | Quantity guard | `0` and `-2` → `Số lượng phải lớn hơn 0.`; `abc` → `Số lượng không hợp lệ — nhập số lớn hơn 0, ví dụ 1 hoặc 2.`; omitted → canonical default 1 |
| 8 | RBAC | same payload as `VIEWER` → `RBAC: không có quyền finance_write.`, row count unchanged |
| 9 | Legacy imported rows (`price_out/price_in/name`, no id/unit) | `repair_data` mints the id, mirrors the legacy amount spellings, keeps `qty 2` / `VAT 8`, leaves the missing unit blank — and the row stays editable in place (React shows its own name instead of forcing a catalog match) |
| 10 | Neighbours untouched | Quote Estimate `finance.quote` unchanged; `payment_record` still books a receipt (received `+500.000`, outstanding `3.959.500`); partner ledger still `AGT-PHUANH · status UNKNOWN · payable null` |

## Acceptance matrix

| | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| A | catalog reused, never duplicated in React | **PASS** | `test_service_catalog_is_projected_from_core_config`, `test_view_model_carries_the_catalog_slice_to_the_component`, `test_service_catalog_is_not_hardcoded_in_react` (strips comments, compares string literals, and rejects any inline catalog array); DOM step 3 of `dom_acceptance_finance_actual_entry.mjs` proves the `<select>` options are exactly `financeServiceCatalog` (27 options, label `name (code)`, grouped by `group`), and step 4 proves code + unit arrive from that entry |
| B | read model carries the line fields | **PASS** | `test_existing_actual_row_projects_the_canonical_fields`, `test_legacy_row_lacking_fields_renders_honestly`, `test_legacy_imported_row_survives_the_canonical_reader_for_editing`; DOM step 2 asserts every field per row |
| C | create round-trip is exact | **PASS** | `test_create_actual_line_round_trips_exactly` — typed Vietnamese amounts become the booked canonical keys `qty/price/price_out/cost/price_in/vat_line/vat` |
| D | edit updates the SAME row, no duplicate | **PASS** | `test_edit_same_line_id_updates_that_row_and_never_duplicates`, `test_edit_with_an_unknown_line_id_is_refused`; DOM step 6 asserts one event carrying `line.id` |
| E | UNKNOWN ≠ ZERO on this writer path | **PASS** | `test_blank_actual_money_is_refused` (per field), `test_missing_actual_money_is_refused_too`, `test_explicit_zero_is_accepted_and_stays_zero`, `test_unparsable_amount_is_refused_with_a_clear_message`, `test_non_positive_qty_is_rejected`; DOM step 5 refuses locally before any event |
| F | RBAC `finance_write` enforced | **PASS** | `test_finance_write_rbac_is_enforced_on_entry_and_on_edit` (viewer refused on create AND on edit, nothing persisted) |
| G | fresh view-model shows line + backend totals | **PASS** | `test_fresh_view_model_shows_the_saved_line_and_backend_totals` — assertions re-read through `vm.read_shipment`, never from component state |
| H | Quote Estimate and the money neighbours unchanged | **PASS** | `test_quote_estimate_and_partner_ledger_are_untouched_by_an_actual_save`, `test_receipt_flow_still_works_next_to_the_new_entry`; DOM step 9 keeps `Doanh thu dự kiến`, Phải thu, partner C2B block and the đối soát link on screen |
| I | mobile, no horizontal scroll, no delete | **PASS** | rows/cards use `grid-cols-2 md:grid-cols-12` inside `#finance-actual-lines` (no `overflow-x-auto`), asserted by DOM step 10; DOM step 8 asserts no delete control exists in the section |
| J | no new database / collection / event / API | **PASS** | `test_no_new_database_or_collection_is_introduced` — `PHASE_B_EVENTS` still holds the same event set and the writer still targets `data["3.4"].details` |

## Semantics used (from code, not from UI labels)

* one service line = one row of `data["3.4"].details`; `id` is the canonical
  identity the editor targets, minted as `PAY-LINE-<hex>` for a new row
* revenue actual = `Σ qty × price` · receivable = revenue + output VAT
* cost actual = `Σ qty × cost` · profit/margin stay backend-owned (`core.logic`)
* `amount` in the read model keeps meaning *sell-side figure* — existing summary
  rows and the C2A DOM acceptance needed no change
* blank ≠ zero **on this writer**; `repair_data` still normalises a genuinely
  absent amount to `0` on the read path (existing canonical behaviour, not
  modified by this slice — honesty is enforced where data is booked)
* no FX: every amount keeps the lot's own currency (`shipment.finance.currency`)

## Verification commands and results

```
cd component && npx tsc --noEmit                                  -> clean
cd component && npm run build                                     -> dist/logi-shell.js 843.25 kB · logi-shell.css 59.69 kB
cd component && npm run scan                                      -> FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0
node tests/component/dom_acceptance_finance_actual_entry.mjs      -> FINANCE ACTUAL ENTRY DOM ACCEPTANCE PASS — 12 checks
node tests/component/dom_acceptance_c2a.mjs                       -> C2A DOM ACCEPTANCE PASS — 9 checks
node tests/component/dom_acceptance_{c2b,c2c,c2d,phase_a,handbook,reconciliation,
   partner_context,consolidation,ceo_report,tariff,translation,user_access}.mjs -> all PASS
python scripts/gen_c2a_fixture.py                                 -> fixture regenerated from the real staging backend
.venv/bin/python -m pytest tests/test_logi_finance_actual_entry_parity_01.py -q -> 30 passed
.venv/bin/python -m pytest tests/test_logi_c2a_finance_actual.py tests/test_phase_b_real_data.py -q -> passed
.venv/bin/python -m pytest tests -q (2 modules that fail to collect at base excluded)
   -> with this slice: 13 failed, 792 passed, 38 skipped, 6 errors
   -> at base 7883144:  13 failed, 763 passed, 38 skipped, 6 errors   (identical FAILED set)
node tests/component/dom_acceptance_create_shipment.mjs            -> FAIL "bounded waiting state missing" — PRE-EXISTING
```

The 13 failures / 6 errors are pre-existing at `7883144` (missing
`/home/ubuntu/upload/danhsachdonhang-.xlsx`, and `views.web_app` no longer
exposing `ROUTES` / `NAVIGATION_GROUPS` / `refresh_core_data`); the FAILED set is
byte-identical before and after this work, and `+29 passed` is exactly the new
suite. `dom_acceptance_create_shipment.mjs` expects the string
`ĐANG CHỜ BACKEND XÁC NHẬN…` while `CreateShipment.tsx:232` has rendered
`ĐANG TẠO LÔ…` since PR #34 — reported to Control Tower, not touched here.

## What changed

| File | Change |
| --- | --- |
| `views/logi_real_data.py` | `finance_service_catalog()` (read-only projection of `GETFLY_SERVICES_LIST`); `finance_projection` actual rows gain `id`, `name`, `code`, `unit`, `note`, `price` |
| `views/logi_view_model.py` | `build_view_model` exposes `financeServiceCatalog`; `_handle_finance_actual_save` requires cost/price/VAT to be stated (blank refused, explicit 0 kept, `qty > 0`), updates the row whose `line.id` matches, refuses an unknown id, echoes `requestId`, and returns `persisted` + fresh `readback` + `audit`; `FINANCE_ACTUAL_REQUIRED_FIELDS`, `_actual_amount`, `_is_blank_amount` |
| `component/src/components/FinanceActualEntry.tsx` | NEW — `#finance-actual-lines` cards + `#finance-actual-form` editor (catalog `<select>`, readonly auto-filled code, unit, qty 1 default, cost/price/VAT/note **all blank until typed — no VAT rate is pre-filled**, live preview, `SỬA` prefills the same canonical id and its stored rate, backend refusal shown, local blank refusal, no delete) |
| `component/src/pages/ShipmentDetail.tsx` | the tiny "Ghi nhận dòng thực tế" form and its `saveActualLine` handler removed; `<FinanceActualEntry/>` mounted under the actual summary |
| `component/src/lib/viewmodel.ts`, `lib/store.tsx` | `FinanceServiceCatalogEntry`, `ViewModel.financeServiceCatalog`, `financeServices` slice |
| `component/src/lib/format.ts` | `parseAmountVN` — browser mirror of `to_decimal`, `null` for blanks (blank never becomes 0) |
| `tests/test_logi_finance_actual_entry_parity_01.py` | NEW — 30 cases (A–J above) |
| `tests/component/dom_acceptance_finance_actual_entry.mjs` | NEW — 12 DOM checks against the built bundle |
| `tests/component/dom_acceptance_c2a.mjs`, `scripts/gen_c2a_fixture.py`, `tests/component/fixtures/view_model_c2a.json` | step 5 drives the service picker; fixture regenerated and extended (catalog slice, second catalog line with a note, a real writer `refused` variant) |
| `component/dist/logi-shell.js`, `component/dist/logi-shell.css` | rebuilt production bundle committed with the sources |

## Deferred on purpose (not in this slice)

delete of a booked line (a wrong row is corrected by editing it, audit history
stays); gross-up commission; payment correction modal; multi-currency/FX;
agent→shipment assignment; user admin; Excel export changes; payment writer
parsing of thousands-separated text (see the note above).

## CONTROL_TOWER_REPAIR_01 — a new line carries no VAT rate

Reviewed head `1b6ab2b` shipped `BLANK_DRAFT.vat = "8"`. A new row therefore
booked VAT 8% if the operator picked a service, typed cost and price, and saved
without touching VAT — an invented financial fact. The invariant is
`UNKNOWN != ZERO` **and** `UNKNOWN != 8`, so:

| Change | Surface |
| --- | --- |
| `BLANK_DRAFT.vat` is `""`; the caption reads `Phải tự nhập — 0 là giá trị hợp lệ (không VAT)` and `VD: 8` survives only as a placeholder example | `component/src/components/FinanceActualEntry.tsx` |
| Nothing else moved: backend validation, the `finance_actual_save` writer, cost/price semantics, catalog, finance model, currency logic, RBAC and the surrounding finance UI are untouched; EDIT still prefills the stored rate verbatim | — |

Proof (re-run at this head):

```
node tests/component/dom_acceptance_finance_actual_entry.mjs  STEP 5   -> PASS
  new form: VAT value == ""            (picking a service does not fill it)
  cost + price typed, VAT untouched, Save:
    FINANCE_ACTUAL_SAVE_EVENT_COUNT=0
    VALIDATION_MENTIONS_VAT=YES  ("VAT % chưa nhập" + "để trống thì không" + "0 là giá trị hợp lệ")
    FORM_REMAINS_OPEN=YES        (draft kept: Giá bán still "900000")
  then VAT="0", Save: FINANCE_ACTUAL_SAVE_EVENT_COUNT=1 and line.vat == "0"
  STEP 5B: blank cost refused the same way; a typed 8 and a typed 10 are booked
  STEP 6 : editing the row whose stored VAT is 0 prefills "0" (never blank)
.venv/bin/python -m pytest tests/test_logi_finance_actual_entry_parity_01.py -q -> 30 passed
  incl. test_a_new_line_starts_with_no_vat_rate (blank default, VAT still in the
  required-money check, edit prefills the stored rate) and the unchanged
  writer-level tests test_blank_actual_money_is_refused / test_explicit_zero_is_accepted_and_stays_zero
Mutation check: restoring vat "8" in BLANK_DRAFT fails BOTH the Python guard and
DOM STEP 5 — the invariant is pinned, not asserted by prose.
```

`SalesQuotes.tsx` still keeps its own `taxPct: "8"` default — that is Quote
*Estimate*, explicitly out of this contract, and was not touched.
