# LOGI-GOOD C2B — Single-Partner Payable: Capability Map (Checkpoint A)

Scope: ONE existing shipment (`LO-0308`) → actual cost owed to ONE partner
(`AGT-PHUANH`, from the existing `authority_agents` master) → partner payable →
ONE real payment → remaining payable → audit / RBAC → fresh readback.

SUPREME_LAW_READ: canonical repo `7roger89-web/P2P-upgrade-github-1@main`
(docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md, P2P_SUPREME_OPERATING_LAW_V1)
is NOT reachable from this sandbox (repo unresolvable). The supplied
SUPREME_LAW_CAPSULE was used as the operating authority.

## 1. Capability map (as found on main @ 3b48141)

| ACTION | CURRENT READER | CURRENT WRITER/SERVICE | CANONICAL RECORD | SHIPMENT LINK | PARTNER LINK | RBAC | IDEMPOTENCY | FRESH READBACK | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| Partner / agent master | `core.database.load_authority_agents` | `core.database` save (db.py:1822–1842) | `authority_agents` | — | is the partner master | app-boundary role matrix | by `agent_id` | direct find | SUPPORTED |
| Shipment actual cost | `core.logic.calculate_from_shipment` over `data.3.4.details` (`cost = Σ qty×price_in`) | `finance_actual_save` typed event → `save_shipment_atomic` | shipment document | native | none on the document | `finance_write` at handler + version-checked atomic save | request registry on payments; version on shipment | `read_shipment` | SUPPORTED |
| Payable to partner | `core.financial_ledger.project_partner_financial_position` (bucket `payable_to_partner`), `derive_obligation_position` | `core.financial_ledger.save_obligation` | `financial_obligations` | `shipment_ids` on the record | `to_party` (typed party) | `_require_finance_write` → `can_operate_business("finance_write")` | `financial_action_requests` (request_id + fingerprint → "already applied") | `build_partner_financial_position` | SUPPORTED |
| Payment to partner | same projection + `recent_allocations` | `core.financial_ledger.save_transaction` + `allocate_transaction` | `financial_transactions` + `financial_allocations` | `shipment_ids` | `holder_party` (typed party) | same gate | same registry (per writer action) | same | SUPPORTED |
| Payment reversal | corrections history | `core.financial_ledger.reverse_allocation` | `financial_corrections` | via allocation | via allocation | same gate | `correction_request_id` + fingerprint | same | SUPPORTED |
| Currency separation | `_currency` mandatory on every ledger record; `allocate_transaction` hard-blocks cross-currency allocation without an explicit FX event | — | `currency` + `original_currency` on every record | — | — | — | — | — | SUPPORTED |
| Audit | `core.database.load_audit_logs(entity_type, entity_id)` | `database._audit(...)` on EVERY canonical ledger write (+ domain event outbox) | `audit_logs` | record ids | — | actor / role stamped | — | — | SUPPORTED |
| Customer receipts (proved by C2A) | `finance_projection.payments` | `payment_record` typed event → `save_direct_shipment_payment` | shipment `data.3.4.payments` | native | — | finance_write | request registry | `read_shipment` | SUPPORTED |
| **Shipment↔partner payable connector for ONE shipment** (read projection filtered by shipment + typed write events at the shell boundary) | — | — | — | — | — | — | — | — | **MISSING — this slice** |

## 2. Decision

The repository ALREADY has a canonical partner payable/payment capability
(`core/financial_ledger.py`, merged on main). Per the decision rule: **reuse it
and wire ONE shipment case.** Nothing in this slice creates a new ledger, a new
accounting subsystem, or a second store.

C2A's "paid-to-partner UNKNOWN" is explained: the canonical ledger existed, but
the shipment finance projection never read it, and no typed event at the shell
boundary could post a partner payable/payment. Both connectors are added here.

## 3. Business semantics (established from existing backend code, not invented)

- **accrued cost** = Σ qty×price_in over `data.3.4.details` (`core.logic` `cost`).
- **payable to partner** = canonical obligation (`financial_obligations`,
  `to_party` = partner) — recorded deliberately with evidence. PAYABLE ≠ COST in
  the model: the obligation is an explicit write that *references* the accrued
  cost, never an automatic equality.
- **cash paid to partner** = canonical transaction (`transaction_kind="payment"`,
  `holder_party` = partner) **allocated** to the obligation. Paid = effective
  allocation sum (reversed allocations excluded).
- **remaining payable** = obligation amount − effective allocations, derived at
  read time (`derive_obligation_position`). Never stored, never editable.
- **overpayment / advance** = a payment transaction whose unallocated remainder
  stays visible as unallocated credit (ledger-native). The C2B event handler
  pre-checks and refuses to post a payment beyond the open outstanding, and
  reports real state on any race (the ledger guard still blocks over-allocation).
- **reversed payment** = `reverse_allocation`; history preserved, sums re-derive.
- **UNKNOWN ≠ ZERO**: with no obligation/payment records for the shipment,
  payable/paid/remaining are `None` (UNKNOWN). Once an obligation exists, its
  allocation history is complete information, so a derived 0 (e.g. allocated
  before any payment) is a true zero, and a fully-paid obligation's remaining 0
  stays 0.

## 4. Case wiring (ONE shipment × ONE partner × ONE currency)

- Shipment: `LO-0308` (existing staging shipment; actual line
  "Phí xe TQ Đông Bằng → Hữu Nghị", accrued cost **57,000,000 VND**).
- Partner: `AGT-PHUANH` — CÔNG TY TNHH PHÚ ANH LOGISTICS (existing
  `authority_agents` record; no new partner module).
- Payer company party: `TT-COMPANY` — TRƯỜNG THÀNH (existing
  `authority_companies` record).
- Currency: VND only, labelled on every record and every UI figure.
- New typed events at the existing shell boundary (same pattern as
  `payment_record`): `partner_payable_record` (one obligation) and
  `partner_payment_record` (one transaction + one allocation), both
  `finance_write`-gated, request-id-idempotent, audit-logged, fresh-readback.
- New read-side helper `core.financial_ledger.shipment_partner_position`:
  derives payable/paid/remaining/payment history for ONE shipment from the
  canonical collections only. No new collection, no new store, no balances.

## 5. Proven journey (acceptance A–N — all PASS)

Suite `tests/test_logi_c2b_partner_payable.py` (11 tests) on the isolated
mongomock staging transport, plus real-bundle DOM acceptance
`node tests/component/dom_acceptance_c2b.mjs` (7 checks) against a fixture
generated from the same backend (`scripts/gen_c2b_fixture.py`):

- A partner identity: `AGT-PHUANH` resolved ONLY from the existing
  `authority_agents` master; unknown partner ids are refused.
- B shipment identity: `LO-0308`; linkage persisted on the canonical records
  (`obligation.shipment_ids`, `transaction.shipment_ids`,
  `allocation.shipment_ids`) and read back fresh.
- C accrued cost read from `core.logic.calculate_from_shipment`
  (= 57,000,000 VND, never assumed).
- D one real payment wrote through `save_transaction` + `allocate_transaction`
  via the typed `partner_payment_record` boundary event.
- E fresh readback: position re-derived from the collections, independent of
  the event result.
- F same-intent idempotency: replayed requestId returns "financial action
  already applied"; exactly 1 transaction + 1 allocation remain. The UI
  double-click replays the same request identity (DOM-proven).
- G a NEW genuine intent (new requestId, same amount) posts a DISTINCT
  transaction + allocation (DOM-proven: new request identity minted).
- H remaining payable derived = 57,000,000 − 20,000,000 − 20,000,000 =
  17,000,000 VND, exact at every step.
- I currency explicit (VND on every record/figure); a USD payment against the
  VND payable is refused before any write; no combining, no FX.
- J UNKNOWN != ZERO regression: before any ledger record, payable/paid/
  remaining are None (UI renders "— tr VND", never "0 tr VND"); a derived 0
  (allocated before any payment) is a true zero.
- K allowed role: SUPPORT (finance_write) writes successfully.
- L denied role: SALE typed event fails at the backend boundary ("RBAC:
  không có quyền finance_write") with zero canonical records created.
- M audit evidence: `audit_logs` rows exist for the obligation, transaction,
  and allocation, stamped with the acting user.
- N fresh-session reopen: projections rebuilt from brand-new database reads
  show identical business truth.

Overpay guard: a payment beyond the open outstanding is refused before any
write (advance/unallocated credit remains ledger-representable, out of slice).

## 6. UI (Checkpoint B — minimum useful, donor structures only)

No new page, no shell redesign. Inside the existing Shipment Detail →
"Tài chính / Công nợ" tab, the existing "Phải trả đối tác" card now shows:
selected partner (canonical, or the clearly-badged single catalog agent
suggestion before any ledger row), payable/paid/remaining tiles fed from the
backend partner block ("—" when UNKNOWN), partner payment history, and the two
typed-event actions (GHI NHẬN PHẢI TRẢ / TRẢ ĐỐI TÁC) with the same per-intent
request identity contract as customer receipts. Frontend visibility is not
authorization — a denied role only receives the backend refusal.

## 7. Environment note (real state at time of slice)

The full pytest suite on this sandbox shows 13 pre-existing failures + 6
errors in UI-mount/AppTest/Excel suites (Streamlit runtime + optional deps in
the sandbox). They exist unchanged on pristine main @ 3b48141 and are untouched
by this slice; every finance/ledger/RBAC/C1/C2A/C2B suite passes.

