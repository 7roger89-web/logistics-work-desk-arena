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
