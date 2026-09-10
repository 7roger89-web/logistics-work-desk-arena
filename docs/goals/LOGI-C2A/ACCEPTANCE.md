# LOGI-GOOD C2A — single shipment Finance Actual: acceptance evidence

TASK `LOGI_GOOD_C2A_SINGLE_SHIPMENT_FINANCE_ACTUAL`
Branch `arena/01a08ac3-logistics-work-desk-arena` (Arena-pinned; base = `main` @ `72e55d6`)
Shipment proven: **`LO-0308` — Minh Đức JSC**, currency **VND**

## Journey actually run (staging, real writers, real readbacks)

| # | Step | Result |
| --- | --- | --- |
| 1 | Open Finance Actual | `views/logi_real_data.finance_projection` over `shipments.data["3.4"]` |
| 2 | Read current authoritative state | receivable 66,960,000 · net 62,000,000 · VAT 4,960,000 · cost 57,000,000 · profit 5,000,000 · debt 66,960,000 VND |
| 3 | Enter supported actual amounts | `finance_actual_save` → 2 × 1,500,000 sell / 1,100,000 cost / VAT 8 |
| 4 | Save through the current writer | `apply_financial_snapshot` + `save_shipment_atomic` |
| 5 | Fresh readback | receivable 70,200,000 · cost 59,200,000 · profit 5,800,000 · margin 8.92% |
| 6 | Record ONE receipt | `payment_record` → `save_direct_shipment_payment`, 40,000,000 VND |
| 7 | Fresh readback | received 40,000,000 · outstanding 30,200,000 VND |
| 8 | Retry the same payment intent | same `request_id` → one payment row, one registry row |
| 9 | Prove idempotency | `received` unchanged at 40,000,000 after the replay |
| 10 | Outstanding from backend truth | `summary["debt"]` = receivable − paid, re-read from the DB |
| 11 | Actual profit / margin | `net − cost − commission`, output VAT excluded; UNKNOWN when nothing is booked |
| 12 | Reopen in fresh app state | `build_view_model()` re-projects identical values |
| 13 | Persisted values + transactions | unchanged after the fresh rebuild |

## Acceptance matrix

| | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| A | real Finance Actual read | **PASS** | `test_c2a_finance_actual_read_is_authoritative` |
| B | supported Finance Actual write | **PASS** | `test_c2a_finance_actual_write_and_fresh_readback`, `..._update_existing_line_not_duplicated`; DOM step 5 emits `finance_actual_save` |
| C | fresh readback | **PASS** | every test re-reads via `vm.read_shipment` (uncached `find_one`) |
| D | actual cost/revenue semantics preserved | **PASS** | `test_c2a_revenue_and_cost_semantics_are_preserved` — receivable = net + output VAT; payable = accrued cost; cash-to-partner = UNKNOWN |
| E | currencies explicit / separate | **PASS** | `test_c2a_currency_is_explicit_and_never_converted`; DOM step 8 renders a USD lot as USD with no conversion. **No FX engine exists** in the backend, so actuals are one currency per shipment and are never summed across currencies |
| F | UNKNOWN != ZERO | **PASS** | `test_c2a_unknown_never_becomes_zero`; DOM step 7 shows `— VND` for profit/margin on an empty book and asserts `0 VND` is absent. Mutation check: restoring the old line fails 2 tests |
| G | one real supported payment recorded | **PASS** | `test_c2a_receipt_recorded_and_outstanding_from_backend_truth` |
| H | duplicate submission idempotent | **PASS** | `test_c2a_duplicate_submission_has_no_duplicate_financial_effect`; DOM step 6 double-click replays ONE `request_id` |
| I | outstanding from backend truth | **PASS** | `fin["outstanding"] == out["persisted"]["derivedDebt"]` (core.logic, re-read) |
| J | actual profit does not borrow Quote Estimate | **PASS** | `test_c2a_actual_profit_never_borrows_quote_estimate` — profit with a quote present but no actual line is UNKNOWN |
| K | allowed-role write works | **PASS** | `test_c2a_allowed_role_can_write_finance_actual` (SUPPORT + `finance_write`) |
| L | denied-role direct event fails | **PASS** | `test_c2a_denied_role_cannot_bypass_the_backend_with_a_typed_event` — VIEWER typed event refused by the **writer boundary** (`core/database.py:568`), nothing written, no audit row |
| M | audit evidence exists | **PASS** | `test_c2a_audit_trail_for_finance_mutations` — `update` + `direct_payment_created` with a real actor |
| N | reopen in fresh app state retains truth | **PASS** | `test_c2a_fresh_app_state_shows_the_same_business_truth` after `st.cache_data.clear()` |

## Semantics used (from code, not from UI labels)

* revenue actual = `Σ qty × price` (booked, not cash)
* receivable = revenue actual **+ output VAT**
* received = `Σ` non-reversed `payments[].amount` (cash)
* cost actual = `Σ qty × cost` (accrued)
* paid-to-partner = **UNKNOWN** — the shipment carries no supplier-payment ledger
* profit = revenue actual − cost − commission, **output VAT excluded**
* Quote Estimate (`quotes`) ≠ Finance Actual (`data["3.4"]`) — never merged

## Verification commands and results

```
python -m pytest tests/test_logi_c2a_finance_actual.py -q        -> 15 passed
python -m pytest tests/test_phase_b_real_data.py \
                 tests/test_logi_c2a_finance_actual.py \
                 tests/test_phase_a_component.py -q              -> 55 passed
python -m pytest tests -q (2 modules excluded that also fail to
  collect at the base commit)                                    -> 13 failed, 501 passed, 38 skipped, 6 errors
  same command at base 72e55d6                                   -> 13 failed, 486 passed, 38 skipped, 6 errors
cd component && npx tsc --noEmit                                 -> clean
cd component && npm run build && npm run scan                    -> FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0
node tests/component/dom_acceptance_phase_a.mjs                  -> DOM ACCEPTANCE PASS - 21 checks (frozen shell unchanged)
node tests/component/dom_acceptance_c2a.mjs                      -> C2A DOM ACCEPTANCE PASS - 9 checks
python scripts/gen_c2a_fixture.py                                -> fixture regenerated from the real staging backend
streamlit run app.py --server.address 0.0.0.0                    -> /_stcore/health 200, / 200
```

The 13 failures / 6 errors are pre-existing at `72e55d6` and untouched by this
work (`+15 passed` is exactly the new C2A suite).

## What changed

| File | Change |
| --- | --- |
| `views/logi_real_data.py` | `finance_projection` gains `hasActualLines`, `profitMargin`; `profit` is UNKNOWN when no actual line is booked |
| `component/src/lib/viewmodel.ts` | `Finance` gains `hasActualLines?`, `profitMargin?` |
| `component/src/lib/format.ts` | adds `fmtCcy`, `fmtMillionsCcy`, `fmtPct` — currency-explicit, never converting |
| `component/src/pages/ShipmentDetail.tsx` | Finance tab wired: actual lines with sell+cost+VAT, actual profit/margin block, one-line actual editor → `finance_actual_save`, currency-explicit AR/AP headings and tiles, payment sheet currency + per-intent request identity |
| `scripts/gen_c2a_fixture.py` | generates the DOM fixture from the real backend |
| `tests/test_logi_c2a_finance_actual.py` | 15 backend acceptance tests |
| `tests/component/dom_acceptance_c2a.mjs` | 9 DOM acceptance checks on the real bundle |
| `component/dist/logi-shell.{js,css}` | rebuilt browser bundle (process gate 0) |

## UI freeze respected

Header, sidebar, mobile nav, colours, typography, global layout and donor
interaction patterns are untouched — `dom_acceptance_phase_a.mjs` still passes
all 21 checks against the rebuilt bundle. The new controls live **inside the
existing Finance tab cards** (`Thực tế — đã phát sinh` and `Phải thu khách
hàng`), reuse the donor primitives (`StateRow`, `Field`, `inputCls`,
`PrimaryBtn`, the tile grid) and add **no new top-level page**.

## Not built (deferred, as instructed)

No FX engine, no second ledger, no `finance_v2`, no reconciliation database,
no duplicate transaction collection, no generic accounting engine, no global
reconciliation, no partner-debt system, no company-wide accounting, no global
P&L, no CEO dashboard, no Admin, no new storage/database/service, no Phase
C2B work.

`PRODUCTION_DB_USED=NO` — every write ran against the isolated mongomock
staging database (`logistics_staging`); `logi_sandbox` never touches a real
`MONGO_URI` and the fixture generator asserts the staging transport.

---

## Addendum — live app evidence through the real entry point

The Arena Preview control plane returned a generic "Something went wrong"
while the application itself was healthy, so the C2A Finance path was verified
through the real entry point instead: `AppTest.from_file("app.py")`, which runs
`app.py` → `views.web_app.main()` → `build_view_model()` → the single
Components v2 root.

Preview diagnosis (in order):

| Check | Result |
| --- | --- |
| Streamlit already running? | Yes — the intended `streamlit run app.py` process |
| Port 8501 occupied? | Yes, by that process (`0.0.0.0:8501`) |
| Is it the intended app? | Yes |
| Latest stdout/stderr | Clean boot, no exception, no traceback |
| `GET /_stcore/health` | `200`, body `ok` |
| `GET /` | `200`, 7459 bytes |
| `GET /` with an external preview `Host` header | `200` |
| → classification | **Arena preview/control-plane problem, not a Logistics code failure** |

Live run on the one existing shipment `LO-0308`:

```
1) app.py boots via real entry point - no exception
   transport=SANDBOX_STAGING  db=logistics_staging
   BEFORE  receivable=66,960,000 net=62,000,000 vat=4,960,000 cost=57,000,000
           paid_to_partner=None outstanding=66,960,000
           profit=5,000,000 margin=8.06 ccy=VND
   hasActualLines=True actual_lines=1 quote_lines=0
   component data channel JSON-serializable: OK

2) finance_actual_save OK  lineId=PAY-LINE-3AA8B61BD4A2
   payment_record   OK  paymentId=PAY-A17EED6F...
   SAME intent replay -> ok=True samePaymentId=True
   NEW intent (same amount+kind) -> distinctPaymentId=True

3) FRESH app.py run (reopen). payload version a4f5342a -> 581595fb
   AFTER   receivable=70,200,000 net=65,000,000 cost=59,200,000
           received=80,000,000 outstanding=-9,800,000
           profit=5,800,000 margin=8.92
   payments retained = [REQ-LIVE-1 40,000,000 ; REQ-LIVE-2 40,000,000]
   outstanding == receivable - received : True
   paid-to-partner still UNKNOWN (None) : True
   actual lines retained = 2

4) audit actions = ['create', 'direct_payment_created', 'update']
```

Notes on that run:

* Step 3 intentionally posts **two** receipts (the second with a genuinely new
  request identity) to prove a new intent is not swallowed as a replay, so
  `received` is 80,000,000 against a 70,200,000 receivable and `outstanding`
  is the correct **negative** 9,800,000 credit. The committed acceptance test
  posts one receipt and asserts the ordinary positive balance
  (outstanding 30,200,000).
* `margin` moves 8.06 → 8.92 because the extra booked line changes the
  revenue/cost mix. Both values come from `core.logic`, never from the quote.
* `db=logistics_staging` confirms the isolated mongomock staging database;
  production was never contacted.
