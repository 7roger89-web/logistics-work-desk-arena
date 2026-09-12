# Notes and Decisions Log — 2026-09-12

## LOGI_GNT_CANONICAL_FIELDS_01 — Owner ruling on canonical import-tax fields

Scope-proof task `LOGI_GNT_MINIMUM_RESTORE_SCOPE_01` returned
`MATERIAL_PRODUCT_CHANGE_REQUIRED` against `main@8abfff8` (PR #20). The blocking
finding was not missing capability but **ambiguity**: two live readers defined
the same fact on two different, mutually blind canonical paths, and **no writer
existed for any of them**.

- `core/gnt_builder.check_gnt_prerequisites` read `data.2.4.import_duty_amount` /
  `data.2.4.import_vat_amount` / `data.2.4.tk_date`.
- `core/shipment_360._tax_summary` read `data.2.4.gnt.ds_thue[]` and returned one
  undifferentiated total.
- `views/logi_real_data.py` read `data.2.4.reg_date`, a fourth name for the same
  declaration date, which nothing wrote either.

Verified at the time: `grep` for assignments found **zero writers** into the
shipment document for `tk_date`, `reg_date`, `clearance_date`,
`import_duty_amount`, `import_vat_amount` or `gnt.ds_thue`. `FIELD_PATHS` held 26
keys, none tax-related, and `_coerce` had no list path at all.

### Owner decision (approved 2026-09-12)

1. `data.2.4.tk_date` is the canonical customs declaration date for new data.
2. `data.2.4.import_duty_amount` is the ACTUAL import duty in VND, keyed by the
   operator from the real customs notice / GNT.
3. `data.2.4.import_vat_amount` is the ACTUAL import VAT in VND, same source.
4. Exactly those three keys join the component write whitelist `FIELD_PATHS`,
   with matching numeric / date coercion. Nothing else.
5. No calculated tax or VAT. No invented rate. No HS lookup used to derive an
   amount. (`core/trade_compliance` stays unwired; the governed tariff schema
   carries only `Mã HS` and descriptions — no rate columns.
   `core/docgen/rules.py:VAT_RATE = 0.08` is an **output** VAT for commercial
   documents and must never be reused here.)
6. `reg_date` is not writable. It survives only as a read fallback for documents
   written before this ruling; `tk_date` wins when both are present.
7. `data.2.4.gnt.ds_thue[]` stays legacy evidence. It is **not** promoted to a
   source of truth, and its total is never projected as the import tax.
8. No change to Finance Actual, the ledger, the schema, the database or
   infrastructure.

### What was implemented

`views/logi_view_model.py` (+3 whitelist keys, +2 numeric and +1 date coercion) ·
`views/logi_real_data.py` (one `_declaration_date` helper; `importInfo.tax/vat`
now read the canonical amounts) · `component/src/pages/ShipmentDetail.tsx`
(three existing read-only slots made editable) · `component/src/lib/viewmodel.ts`
(comment only) · rebuilt `component/dist`.

Reused unchanged: `save_shipment_atomic` (transaction, optimistic version,
audit), the `shipment_field_save` event, `core.logic`, `core/financial_ledger`.
No new event, schema, migration, API, service, tax engine or ledger.

Acceptance: `tests/test_logi_gnt_canonical_fields_01.py`, 16 tests, one per
clause of the ruling including the negative ones (`reg_date` and `ds_thue`
writes are rejected; a legacy `ds_thue` total is still readable as evidence but
projects `tax = None`; Finance Actual is byte-identical across a tax save).

### Addendum — CLEAR_FIX (Control Tower review, same day)

The first implementation routed the three new fields through `onlyFilled(...)`,
which drops blank strings. An operator clearing a stored `5.000.000` therefore
sent no key at all, the stale number stayed canonical, and the fresh readback
put it back on screen — contradicting both **BLANK = UNKNOWN** and the field's
own hint text *"Bỏ trống = chưa biết"*.

Fix: the three approved fields are no longer passed through `onlyFilled`. They
are driven by the existing React touched-state in `ShipmentDetail.saveImport`:

- key **absent** from `form` → untouched → omitted, so an ordinary save never
  copies the legacy `reg_date` read fallback into canonical `tk_date`;
- key **present** in `form` → the operator edited it → the trimmed value is sent
  verbatim, **including `""`**.

The backend needed no change: `_coerce` already preserves a blank, and the
projection already maps it to `None` → "—".

Pinned by `tests/component/dom_acceptance_phase_a.mjs` STEP 16 (4 new checks:
untouched omitted, cleared duty `""`, cleared VAT + date `""`, edited value
verbatim) and by 6 new backend tests in
`tests/test_logi_gnt_canonical_fields_01.py`. Do not move these three fields
back behind `onlyFilled`.
