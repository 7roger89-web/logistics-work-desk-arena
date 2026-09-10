# LOGI-GOOD C2A — Finance Actual capability map (pre-coding)

TASK: `LOGI_GOOD_C2A_SINGLE_SHIPMENT_FINANCE_ACTUAL`
Base: `main` @ `72e55d63887ecb1ea77c1e641ff6b7cde9499338` (fresh-check verified)

Every reader/writer/permission below was located by reading the current
repository, not assumed. Line references are from the base commit.

## Canonical finance representation (the ONLY one)

There is **no separate finance ledger for shipments**. Authoritative Finance
Actual lives on the shipment document itself:

```
shipments.data["3.4"] = {
  details:    [ {id, name_full, display_name, code, unit, qty,
                 price (=sell/price_out), cost (=price_in), vat_line, note} ]
  payments:   [ {id, request_id, date, amount, note, created_by, is_reversed?} ]
  commission: {list, total, note}
  # derived snapshot, recomputed by core.logic.apply_financial_snapshot on write
  out, out_net, output_vat, in, profit, paid, debt, currency
}
```

`core/logic.py:50 calculate_shipment_financials` is the single derivation:

| derived value | formula in current backend |
| --- | --- |
| `revenue_net` | Σ qty × price |
| `output_vat` | Σ qty × price × vat_line/100 |
| `receivable` | revenue_net + output_vat |
| `cost` | Σ qty × cost |
| `paid` | Σ payment.amount where not reversed/cancelled/void |
| `profit` | revenue_net − cost − commission.total (**excludes output VAT**) |
| `debt` | receivable − paid |

`core/logic.py:110 apply_financial_snapshot` writes that summary back onto
`data["3.4"]`. Quote Estimate is a **different collection** (`quotes`, read via
`_quote_lines`) and is never merged into the above.

## Action map

| ACTION | CURRENT READER | CURRENT WRITER/SERVICE | CANONICAL RECORD | RBAC | IDEMPOTENCY | FRESH READBACK | SUPPORTED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Read Finance Actual | `views/logi_real_data.py:195 finance_projection` ← `core.logic.calculate_from_shipment` | — (read only) | `shipments.data["3.4"]` | `finance_view` for the page; projection is read-only | n/a | `views.logi_view_model.read_shipment` | **YES** |
| Read Quote Estimate | `views/logi_real_data.py:156 _quote_lines` | — | `quotes` | read-only | n/a | same | **YES** (separate object, never summed into actual) |
| Write Finance Actual line | `read_shipment` | `views/logi_view_model.py:563 _handle_finance_actual_save` → `core.logic.apply_financial_snapshot` + `core.database.save_shipment_atomic` | `shipments.data["3.4"].details[]` | `can_operate_business("finance_write")` checked in the handler | optimistic version (`expected_version`) + line `id` reuse for updates | `_projection_for(fresh)` re-read from DB | **YES** (handler + tests existed; **no UI caller** — see gap G1) |
| Record one receipt/payment | `finance_projection["payments"]` | `views/logi_view_model.py:653 _handle_payment_record` → `core.database.save_direct_shipment_payment` (`core/database.py:546`) | `shipments.data["3.4"].payments[]` + `financial_action_requests` | `can_operate_business("finance_write")` enforced **inside the writer** (`core/database.py:568-572`), so UI hiding is not the boundary | `request_id` + `_direct_payment_fingerprint` in a real transaction; replay returns the original result and never double-posts | `_projection_for(fresh)` + `derived_paid` / `derived_debt` | **YES** |
| Correct a payment | `finance_projection["payments"]` | `_handle_payment_correction` → `core.database.save_direct_payment_correction` | payment row flagged `is_reversed`, history preserved | `finance_write` (writer boundary) | `correctionRequestId` | `_projection_for(fresh)` | **YES** (not needed for C2A acceptance) |
| Outstanding balance | `finance_projection["outstanding"]` ← `summary["debt"]` | derived by `core.logic` | `shipments.data["3.4"].debt` | read-only | n/a | re-read after write | **YES** |
| Actual profit / margin | `finance_projection["profit"]` ← `summary["profit"]` | derived by `core.logic` | `shipments.data["3.4"].profit` | read-only | n/a | re-read after write | **PARTIAL** — value existed and was exposed, but margin was not derived and profit was emitted as `0.0` when no actual line was booked (a manufactured zero). See gap G2. |
| Currencies | `finance_projection["currency"]` ← `shipment.currency` / `data["3.4"].currency`, default `"VND"` | — | `shipments.currency` | read-only | n/a | re-read | **YES** for explicit per-shipment currency. **No FX engine exists** — verified: no conversion table/rate service anywhere in `core/`. Therefore actuals are single-currency per shipment and must never be converted or summed with another currency. |
| Audit | `views/logi_view_model.py:458 _audit_trail` ← `core.database.load_audit_logs` | `core.database._audit` (same Mongo session as the write) | `audit_logs` | n/a | n/a | `load_audit_logs("shipment", sid)` | **YES** — `update` and `direct_payment_created` |
| RBAC | `core/auth.py:148 can_operate_business` → `has_write_permission` → `ROLE_PERMISSIONS` | same | `users` | single matrix | n/a | n/a | **YES** |

## Semantics established from the code (not from UI labels)

* **revenue actual** = `revenue_net` = Σ qty × price of booked `details` lines.
  It is a *booked* figure, not cash.
* **customer receivable** = `receivable` = revenue_net **+ output VAT**.
* **amount received** = `paid` = Σ non-reversed `payments[].amount`. Cash.
* **cost actual** = `cost` = Σ qty × cost of the same booked lines. Accrued.
* **amount paid to partners** = **not modelled on the shipment document**.
  `finance_projection["paid"]` is therefore `UNKNOWN` (`None`), never `0`.
* **payable** = `cost` (accrued), which is *not* the same thing as cash paid.
* **profit** = `revenue_net − cost − commission`, output VAT excluded.
* **Quote Estimate ≠ Finance Actual** — different collections, never merged.
  `finance_projection` documents this in its own docstring.

## Gaps found (the actual C2A work)

* **G1 — Finance Actual write has no UI caller.** `finance_actual_save` is in
  `PHASE_B_EVENTS` and in `component/src/lib/dispatcher.ts`, but no page ever
  dispatches it. The Finance tab rendered actual costs read-only.
* **G2 — Actual profit/margin not surfaced.** `finance_projection["profit"]`
  existed but nothing consumed it; no margin; and with zero booked lines the
  backend arithmetic yields `0.0`, which would present a manufactured profit.
* **G3 — Currency was hardcoded in the UI.** The Finance tab headings and the
  payment modal said "(VND)" literally while the authoritative currency is
  `finance.currency`.
* **G4 — Payment request identity was over-sticky.** `ShipmentDetail.tsx`
  derived the request id from `shipmentId|amount|kind`, so a *second genuine*
  receipt of the same amount and kind replayed the first request and would not
  post. Idempotency must be per payment intent, not per amount.

## Explicitly NOT built (deferred)

No FX engine, no second ledger, no `finance_v2`, no reconciliation database,
no duplicate transaction collection, no generic accounting engine, no new
top-level page, no partner-debt/global-P&L/company accounting, no new audit
system, no new storage or service.

---

## Checkpoint A evidence

Single existing shipment proven: **`LO-0308` — Minh Đức JSC** (staging seed,
currency VND, one booked actual line, no payments yet).

Authoritative read before any write (`core.logic.calculate_from_shipment`):

```
revenue_net   62,000,000 VND
output_vat     4,960,000 VND
receivable    66,960,000 VND
cost          57,000,000 VND
commission             0 VND
profit         5,000,000 VND   (net - cost - commission; output VAT excluded)
paid                   0 VND
debt          66,960,000 VND
```

Verification run:

```
python -m pytest tests/test_logi_c2a_finance_actual.py -q     -> 15 passed
python -m pytest tests -q (excluding 2 modules that fail to
  collect at the base commit as well)                          -> 13 failed, 501 passed, 38 skipped, 6 errors
  same command at base 72e55d6                                 -> 13 failed, 486 passed, 38 skipped, 6 errors
```

`+15 passed` is exactly the new C2A suite; the 13 failures and 6 errors are
pre-existing at `72e55d6` and untouched.

Mutation check: restoring the previous unconditional
`profit = num(summary["profit"])` makes
`test_c2a_unknown_never_becomes_zero` and
`test_c2a_actual_profit_never_borrows_quote_estimate` fail (`2 failed, 13
passed`), so the UNKNOWN!=ZERO assertions genuinely exercise the change.
