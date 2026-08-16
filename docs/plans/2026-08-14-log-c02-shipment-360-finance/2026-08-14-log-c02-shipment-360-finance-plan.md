# LOG-C02 Shipment 360 — Công nợ & đối soát lô hàng

## Metadata

- Date: `2026-08-14`
- Status: `blocked` overall; bounded Slice A `PASS` locally
- Plan: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-actual-status.md`

## Goal

Deliver Slice A of LOG-C02: map the real current finance capability and add
a read-only Shipment 360 financial summary to the existing shipment detail
view. The first useful view must answer “who owes whom how much for this
shipment and why?” using only current, code-backed data; unresolved concepts
must remain `UNKNOWN`.

## Rules

- Complete and record P0 actual status before implementation work.
- Preserve the existing dirty worktree; never reset, checkout, overwrite, or
  absorb unrelated user changes.
- Do not touch the P2P development checkout, P2P source, credentials, auth
  policy, real business data, deployment, migration, or release.
- This slice is read-only. It must not create a write path, mutate Mongo
  documents, repair a shipment in place, or change the existing save flows.
- Keep the five financial concepts distinct in the read model: obligation,
  transaction, allocation, adjustment, and evidence. Do not manufacture a
  missing concept from a convenient balance field.
- A derived balance is allowed only where the current source calculation is
  identified. Never add an editable balance field.
- Preserve original FX fields when displaying existing records; never
  recalculate historical values with today’s rate.
- Use the existing Mongo architecture and current project conventions. No
  new database, collection, migration, workflow engine, or enterprise search.
- Unknown business meanings stay `UNKNOWN`; no guessed debit/tax/agent
  semantics.
- Run Anvien file-detail and impact evidence before editing target symbols,
  run change detection before any possible commit, and do not commit if the
  dirty worktree prevents an isolated commit.
- Record evidence and benchmarkable measurements as each slice completes.

## Problem

The application already calculates customer receivable, paid, and debt from
shipment detail lines and payments, but that information is shown inside the
older finance tab and is mixed with several unrelated stores. Agency payable,
proxy payments, entrustment wallets, tax records, contract transactions, and
evidence are not one unified ledger. A shipment therefore has no first-view,
read-only financial map that distinguishes verified values from missing
reconciliation data.

## Scope

- `core/shipment_360.py`: pure read-model projection over an existing shipment
  and already-loaded read-only related records.
- `views/shipment_360.py`: read-only Streamlit renderer with financial summary,
  attention items, money map, relationships, and source labels.
- `views/shipment.py`: minimal wiring before the existing operational/finance
  tabs; preserve all existing edit and save behavior.
- Focused unit tests for the pure projection and reusable browser-flow
  evidence when the existing browser harness is available without installing
  dependencies.
- Capability map, evidence, benchmark, actual-status, coder, supervisor, and
  decision-log records for this bounded slice.

## Non-Goals

- No obligation/transaction/allocation/adjustment/evidence ledger migration.
- No new payment, payable, receivable, debit, tax, FX, reconciliation, or
  correction write flow.
- No direct balance editing, workflow engine, dependency graph UI, project
  management feature, or operational timeline redesign.
- No fix of the known Contract proxy-payment two-save partial-write risk; it is
  recorded as an existing blocker and remains outside this slice.
- No claim that Mongo write → durable persistence → restart/reload → read-back
  is proven. No real-money fixture is allowed.
- No credential/auth/worker/Docker/P2P/governance repair, deployment, or data
  cleanup.

## Requirements and Invariants

### User-visible requirements

- Opening a shipment shows financial information before the large operational
  detail tabs.
- Show, when code-backed: total receivable, collected, outstanding
  receivable, agency payable, paid/offset, outstanding agency payable, known
  cost (explicitly not a payable), tax records, customer payments, proxy and
  entrustment relationships, contract links, and operational/financial status.
- Show `UNKNOWN` with a reason for unallocated money, unreconciled items,
  unconfirmed costs, evidence completeness, actual profit, and any other
  concept for which the current project has no trustworthy source.
- Every displayed material number has a source label or is explicitly marked
  inferred/unknown. The read model must not imply that cost equals payable or
  that a payment is an obligation.
- The UI has no submit/save/delete/payment/adjustment controls in the new
  summary.

### Financial invariants

| Invariant family | Current source of truth | Forbidden shortcut | Verification |
|---|---|---|---|
| Customer receivable | `core.logic.calculate_from_shipment`, using `data.3.4.details` and `data.3.4.payments` | Recompute a second balance in the UI; edit debt directly | Pure projection tests and source inspection |
| Agency payable | Existing `views.reports` rule over explicit `data.3.4.agency` fields only | Treat all shipment cost as payable; infer a payable from missing agency data | Projection tests with present/absent agency section |
| Payment vs obligation | Existing payment rows and existing agency/proxy/contract stores remain separate | Collapse every amount into one editable balance | Projection shape and UI labels |
| FX history | Existing stored exchange-rate/original-currency fields | Recalculate historical money using current rate | Preserve raw related records in projection tests |
| Tax/debit/evidence | Explicit GNT/tax rows, existing records, or unknown | Guess `giấy C`, debit, tax obligation, or evidence state | Unknown-state tests |
| Closure | No complete current reconciliation source exists | Show “đã tất toán” from customer debt alone | Always expose bounded/unknown closure state |

### Invariant family map

- Siblings: `core/logic.py`, `core/payment_logic.py`, `core/database.py`,
  `views/shipment.py`, `views/finance.py`, `views/reports.py`,
  `views/contracts.py`, `views/proxy_payment.py`, `views/entrustment.py`,
  `views/dashboard.py`, `core/getfly_reader.py`, and `views/tariff.py`.
- Read-model owner: `core/shipment_360.py`; it composes existing sources and
  must not become a new persistence source.
- UI owner: `views/shipment_360.py`; it renders verified/incomplete states and
  must not call mutation functions.
- Forbidden cross-boundary behavior: calling `apply_financial_snapshot`,
  `save_shipment_atomic`, `save_proxy_payment`, `save_contract_transaction`,
  or any payment/entrustment save from the new read-only summary.
- Test matrix: present/absent agency payable, partial customer payment,
  multiple payment rows, direct/contract related proxy records, preserved FX
  fields, explicit GNT tax rows, and unknown reconciliation/evidence states.

## Acceptance Criteria

- P0 actual status contains an evidence-backed capability map classified as
  `EXISTS_AND_REUSABLE`, `EXISTS_NEEDS_EXTENSION`, `DUPLICATED`, `MISSING`,
  `UNSAFE`, or `UNKNOWN`.
- The pure projection uses the current customer calculation and does not
  invent missing payables, allocations, adjustments, debits, or evidence.
- The shipment detail view visibly shows the read-only financial summary in a
  real local runtime without changing existing flows.
- All new projection tests, existing Python tests, compile checks, and the
  available real browser read-only flow pass.
- Browser evidence confirms no new summary control submits a mutation; no
  fixture/business data is written.
- Anvien change detection is recorded. A safe isolated commit is optional and
  must not include the pre-existing dirty worktree; otherwise status records
  “no commit — dirty boundary preserved”.
- Final status is exactly `PASS`, `BLOCKED`, or `REJECT` based on supervisor
  evidence; unresolved durability, security, governance, Docker, and dirty
  boundaries are not silently converted to PASS.

## Checklist

- [x] P0-A: Inspect current implementation and complete the actual capability map.
  - Goal: identify real sources, duplicates, unsafe boundaries, and unknowns.
  - Evidence: refreshed Anvien graph, source inspection, existing tests/reports,
    and worktree status.
  - Decision: Slice A read-only projection is safe to attempt; all writes and
    persistence proof remain out of scope.

### P1: Read-only Shipment 360

- [x] P1-A: Implement the pure read-only financial projection and focused tests.
  - Boundary: new projection module and tests; no DB writes or existing math
    changes.
  - Gate: exact Anvien file/symbol detail and impact evidence recorded before
    editing; tests prove current receivable source and unknown behavior.
  - Acceptance: projection returns source-labelled values and relations without
    mutating its inputs.
  - Completion: `core/shipment_360.py` added; focused tests pass for current
    receivable math, agency scope, tax, relations, FX preservation, input
    non-mutation, and UNKNOWN states.

- [x] P1-B: Render and wire the financial summary into shipment detail.
  - Boundary: new renderer plus minimal import/call in dirty
    `views/shipment.py`; preserve current tabs and save paths.
  - Gate: renderer contains no mutation calls; existing detail flow still
    renders.
  - Acceptance: local Streamlit runtime shows the financial summary first and
    leaves existing finance/operational controls intact.
  - Completion: read-only renderer added and wired before the existing tabs;
    the existing dirty detail file was not reset or refactored.

- [x] P1-C: Verify runtime, regression, and read-only browser behavior.
  - Work: run full available build/compile/test checks, real local browser
    flow, change detection, and evidence refresh.
  - Acceptance: no business-data mutation; browser evidence and test output
    are retained; missing Docker/isolated persistence proof remain explicit.
  - Completion: local health `200/ok`, reusable Browser flow PASS, 27 tests
    PASS, compileall PASS, and Anvien change detection recorded.

### Pn: Supervisor and closure

- [x] Pn-A: Independent supervisor review of source, diff, evidence, and scope.
  - Completion: supervisor reran the Browser flow, tests, compile, health,
    source mutation scan, and dirty-boundary review; bounded slice PASS,
    overall closure REJECT.
- [x] Pn-B: Update plan/evidence/benchmark/actual-status and append the decision
  log; stop at PASS/BLOCKED/REJECT.
  - Completion: all four plan files, coder/supervisor reports, QA artifacts,
    and the shared decision log were refreshed; terminal status BLOCKED.

### P2: Slice B0 - Financial Write Safety Gate and Minimum Ledger Readiness

- Phase Goal: verify the existing money-writing family before enabling any new
  quick-entry action, close only a bounded integrity blocker when the current
  Mongo pattern proves it is safe, and document the smallest ledger boundary
  that can follow the gate.
- Phase Boundary:
  - In scope: existing shipment payment, lump-sum allocation, shipment save,
    contract proxy/transaction pair, proxy payment, entrustment wallet, agency
    balance calculation, GetFly financial import context, tax workspace, and
    fixture-only persistence/retry tests.
  - Out of scope: Quick Entry, real business data, migration, full accounting,
    broad workflow redesign, new database, P2P, deployment, and credential or
    permission changes.
  - Dependencies: the current dirty worktree is preserved; Mongo fixture data
    must use a newly generated isolated database name and must be cleaned up.
- Phase Implementation Rule: do not implement a ledger or Quick Entry until
  P2-A and P2-B establish a safe write boundary. If a material business or
  architecture decision remains, stop with PARTIAL/BLOCKED evidence.
- Ordered Slice List:
  - P2-A: Rebuild the financial write map and B0 actual-status matrix.
  - P2-B: Execute the fixture-only atomicity, persistence, retry, and derived
    balance gate.
  - P2-C: Apply only the smallest proven contract-proxy integrity fix, if the
    gate identifies a bounded safe change.
  - P2-D: Record minimum ledger readiness, including held/unallocated money
    and non-shipment payment cases, without opening Quick Entry.
  - P2-E: Regression, change detection, reports, and supervisor acceptance.

- [ ] P2-A: Rebuild the financial write map and B0 actual-status matrix.
  - Goal: classify every current material financial write as SAFE, PARTIAL,
    UNSAFE, or UNKNOWN with exact source, collection, save count, transaction,
    idempotency, failure behavior, and balance impact.
  - Scope Boundary:
    - Editable: the existing B0 plan/evidence/benchmark/status artifacts and
      fixture-only test files if required by P2-B.
    - Inspect-only: current production write paths until Anvien file-detail and
      impact evidence is recorded.
    - Preserve-only: all pre-existing dirty business files not selected by a
      later bounded fix.
    - Out of scope: any real Mongo write, migration, or UI quick-entry.
  - Non-Goals: do not normalize existing stores into a new ledger during the
    map phase.
  - Pre-flight Questions:
    - Data source: current Mongo repository and existing legacy shipment fields.
    - Display permission: no new user-facing display in B0.
    - DB read flow: source inspection plus isolated fixture reload.
    - DB write flow: fixture-only; production business database is forbidden.
    - Render location: N/A; this slice is backend/data-safety evidence.
    - UI behavior flow: N/A; Quick Entry remains closed.
    - Docker runtime: not required for non-UI B0; project has no Docker artifact.
    - Playwright target: N/A; no UI behavior is changed in P2-A.
    - Behavior test: current source paths and the P2-B fixture matrix.
    - Cleanup/quarantine: generated fixture database is dropped only after
      exact-name verification; no business database is touched.
    - External side effects: isolated Mongo fixture database only.
    - N/A notes: GetFly and tariff are context/write-adjacent surfaces, not a
      unified financial ledger source.
  - Work Steps:
    1. Refresh Anvien and inspect current repository, payment, contract,
       proxy, entrustment, shipment, finance, reports, GetFly, and tariff paths.
       - UI flow check: N/A; confirm no UI changes are needed for the map.
       - DB/data flow check: enumerate each collection/document mutation and
         derived balance path.
       - Render location check: N/A.
       - Evidence target: E0-P2A-SRC1..E0-P2A-IMP3.
    2. Write the capability/write matrix and update downstream B0 assumptions.
       - UI flow check: Quick Entry remains explicitly blocked.
       - DB/data flow check: mark durable proof and failure behavior separately
         from source-level intent.
       - Render location check: N/A.
       - Evidence target: E0-P2A-MAP1..E0-P2A-MAP4.
  - Implementation Gate:
    - no production code edit until exact file-detail and symbol impact are
      recorded for every function selected for P2-C.
    - P2-A must state whether the current environment supports isolated Mongo
      transactions without exposing credentials or business data.
  - Acceptance:
    - Source: all named financial write siblings are mapped.
    - Runtime/UI: no UI mutation is introduced.
    - DB/data: business database remains unchanged.
    - Behavior test: map has a direct fixture/retry plan for each material path.
    - Cleanup/quarantine: fixture boundary is explicit.
    - Evidence IDs: E0-P2A-SRC1..E0-P2A-MAP4.
    - Actual-status rows refreshed: write-path rows and B0 gate state.
  - Evidence Targets: source lines, Anvien graph/impact, topology probe, and
    the B0 invariant family map.
  - Actual-status Update: replace stale Slice A persistence UNKNOWN details with
    current B0 source classifications while retaining history.
  - Commit Boundary: documentation/status refresh only; preserve dirty code
    boundary.

- [ ] P2-B: Execute the fixture-only financial write safety gate.
  - Goal: prove or disprove durable write/read-back, rollback on second-save
    failure, retry/idempotency behavior, and derived outstanding consistency.
  - Scope Boundary:
    - Editable: fixture test harness and focused tests only after P2-A gate.
    - Inspect-only: production write code unless P2-C is separately authorized
      by the test evidence.
    - Preserve-only: real business collections and all unrelated test fixtures.
    - Out of scope: real money and production data.
  - Non-Goals: do not claim that a fake transaction proves Mongo durability;
    actual isolated Mongo persistence must be separately labeled.
  - Pre-flight Questions:
    - Data source: synthetic obligations/payments/adjustments only.
    - Display permission: N/A.
    - DB read flow: new isolated fixture database and fresh client/collection
      read-back.
    - DB write flow: transaction/session or fail-closed result under injection.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A for backend-only fixture tests.
    - Playwright target: N/A.
    - Behavior test: the 14-case matrix in the user request.
    - Cleanup/quarantine: exact generated database name and final drop proof.
    - External side effects: isolated fixture database only.
    - N/A notes: no migration or history rewrite.
  - Work Steps:
    1. Run obligation/transaction/allocation/adjustment fixture cases, including
       held/unallocated and received-on-behalf semantics.
       - UI flow check: N/A.
       - DB/data flow check: derived balance equals obligation minus allocation
         plus valid adjustment after fresh reload.
       - Render location check: N/A.
       - Evidence target: E0-P2B-TEST1..E0-P2B-TEST10.
    2. Inject second-save failure and duplicate/retry timing cases, then run a
       fresh-client read-back and cleanup.
       - UI flow check: N/A.
       - DB/data flow check: no partial proxy pair and no duplicate payment.
       - Render location check: N/A.
       - Evidence target: E0-P2B-TEST11..E0-P2B-TEST14.
  - Implementation Gate: if the current production path cannot safely satisfy
    the failure case, keep Quick Entry closed and route only the smallest
    bounded integrity fix to P2-C.
  - Acceptance:
    - Source: transaction/idempotency/version behavior is evidenced.
    - Runtime/UI: no UI write path is enabled.
    - DB/data: fixture write, fresh read-back, and cleanup are proven.
    - Behavior test: all applicable 14 cases are PASS or explicitly BLOCKED
      with the exact missing boundary.
    - Cleanup/quarantine: generated fixture database is absent after teardown.
    - Evidence IDs: E0-P2B-TEST1..E0-P2B-TEST14.
    - Actual-status rows refreshed: persistence/retry/derived-balance rows.
  - Evidence Targets: test output, fresh read-back, rollback observation, and
    cleanup verification.
  - Actual-status Update: classify each write path from UNKNOWN to the proven
    SAFE/PARTIAL/UNSAFE state only.
  - Commit Boundary: no code commit unless P2-C changes production behavior.

- [ ] P2-C: Close the smallest proven contract-proxy integrity blocker.
  - Goal: if and only if P2-B proves the existing two-save path can leave a
    partial pair, route both documents through the existing Mongo transaction
    pattern and fail closed when transactions are unavailable.
  - Scope Boundary:
    - Editable: the narrow repository helper and its single contract-proxy
      caller, plus direct behavior tests.
    - Inspect-only: all other write siblings unless the matrix proves the same
      fix is required.
    - Preserve-only: existing document shapes, indexes, and UI layout.
    - Out of scope: new ledger collections, migration, compensation-based fake
      atomicity, and retry redesign for unrelated legacy forms.
  - Non-Goals: do not call a two independent-save sequence atomic.
  - Pre-flight Questions:
    - Data source: existing `proxy_payments` and `contract_transactions`.
    - DB read flow: existing load functions plus fresh fixture read-back.
    - DB write flow: one Mongo session/transaction for both documents/audits.
    - UI behavior flow: existing contract form only; no new controls.
    - Behavior test: injected second-write failure leaves neither document.
    - Cleanup/quarantine: fixture-only.
    - External side effects: none beyond isolated fixture database.
  - Work Steps:
    1. Run file-detail and symbol impact for the selected repository helper and
       contract caller, then implement the narrow transactional boundary.
       - UI flow check: form success/error behavior remains unchanged.
       - DB/data flow check: both documents and audits share the same session.
       - Render location check: existing contract finance tab only.
       - Evidence target: E1-P2C-IMPACT1..E1-P2C-TEST3.
    2. Run direct failure/retry tests and current regression suite.
       - UI flow check: no Quick Entry is enabled.
       - DB/data flow check: second-write exception aborts the fixture transaction.
       - Render location check: N/A if no UI file change is needed beyond caller.
       - Evidence target: E1-P2C-TEST4..E1-P2C-REG1.
  - Implementation Gate: actual Mongo transaction support is verified by the
    topology probe and the fixture test; otherwise this slice is blocked.
  - Acceptance:
    - Source: no independent two-save caller remains for the contract proxy
      pair.
    - DB/data: rollback and fresh read-back pass with fixture data.
    - Behavior test: direct happy/failure/retry tests pass.
    - Evidence IDs: E1-P2C-IMPACT1..E1-P2C-REG1.
  - Evidence Targets: diff, test output, and detect-changes.
  - Actual-status Update: contract proxy `UNSAFE/PARTIAL -> SAFE` only when
    rollback proof is fresh.
  - Commit Boundary: one surgical implementation commit after acceptance; no
    unrelated dirty files may be included.

- [ ] P2-D: Record minimum ledger readiness without opening Quick Entry.
  - Goal: define the smallest reusable conceptual boundary for obligation,
    transaction, allocation, adjustment, evidence, and held/unallocated money
    using existing stores where possible.
  - Scope Boundary:
    - Editable: evidence/status/plan artifacts and pure fixture/domain helpers
      only if P2-B is PASS.
    - Inspect-only: production ledger persistence until owner acceptance of any
      remaining business semantics.
    - Preserve-only: existing balances and legacy fields; no migration.
    - Out of scope: full accounting, cashflow, portal, global search, workflow,
      or automatic netting.
  - Non-Goals: no direct editable balance and no mandatory shipment_id on every
    money event.
  - Work Steps:
    1. Map shipment-linked, payment-case-linked, and unallocated/held records,
       including A Bo held 30M -> later 80M obligation -> 50M remaining.
       - UI flow check: N/A.
       - DB/data flow check: preserve source -> held -> allocation/netting ->
         target obligation -> remaining available.
       - Render location check: N/A.
       - Evidence target: E2-P2D-MODEL1..E2-P2D-MODEL3.
  - Implementation Gate: P2-B must be PASS; otherwise record readiness as
    BLOCKED/PARTIAL and do not add production ledger writes.
  - Acceptance: model does not require every money event to have shipment_id,
    does not auto-net unknown ownership, and derives outstanding values.
  - Actual-status Update: minimum ledger row is ready/blocked based on gate.
  - Commit Boundary: documentation only unless a separately proven pure helper
    is required.

- [ ] P2-E: Regression, detect-changes, reports, and supervisor acceptance.
  - Goal: close B0 at exactly PASS, PARTIAL, or BLOCKED with current evidence.
  - Work Steps: run compile/test/isolated fixture checks, refresh Anvien, run
    detect-changes, write coder/data-integrity/edge/supervisor artifacts, and
    preserve the dirty boundary.
  - Implementation Gate: no Quick Entry, migration, deploy, or real-money
    write is permitted.
  - Acceptance: supervisor independently accepts the exact B0 claim or records
    a blocker; final report names whether a user decision is required.

## Risk Notes

- The target `views/shipment.py` is already a broad dirty rewrite and has a
  high-risk Anvien projection with many unresolved references. The change must
  be a small wiring insertion, not a refactor.
- Current finance stores are duplicated: shipment payments, lump-sum payment
  receipts, proxy payments, contract transactions, entrustment wallets, and
  agency fields do not yet form one allocation ledger.
- Source code contains safer-looking payment transaction/idempotency logic,
  but durable runtime proof is still unknown. This slice does not enable it.
- The Contract proxy form still performs two independent saves. It remains an
  explicit later integrity task.
- Existing P2P governance drift and security/operations blockers remain
  preserve-only and do not affect the read-only projection unless runtime
  access is unavailable.

## R3 — B0 financial write safety checkpoint

Status: **PARTIAL**. The bounded Contract proxy pair fix is proven, but the
whole material financial write family is not yet safe enough to authorize
Quick Entry or the minimum ledger implementation.

- `P2-A`: complete. The write map covers 10 material financial write families;
  fresh Anvien evidence remains high-risk because the worktree is dirty and
  resolver gaps are large.
- `P2-B`: partial. Isolated Mongo proof passed for Contract proxy,
  lump-sum payment idempotency, and single shipment persistence/derived
  balance. Direct payment duplicate identity and entrustment batch failure
  gaps were reproduced with fixture injections.
- `P2-C`: bounded implementation complete. `save_contract_proxy_payment_atomic`
  uses one supported Mongo transaction and fails closed when the topology
  cannot start a session. No independent-save fallback remains in that path.
- `P2-D`: blocked. No new obligation/transaction/allocation/adjustment/evidence
  ledger or held/unallocated write path was added.
- `P2-E`: in review. Reports and supervisor review are required before this
  checkpoint can be closed.

Decision boundary: **Quick Entry = NO**. The next smallest slice is direct
payment request identity plus entrustment batch atomicity/failure semantics,
still fixture-only. Do not generalize the lump-sum idempotency proof to other
writers.

Evidence: `reports/coder/rp_coder_260814_150045_by_gpt-5-codex_financial-write-safety.md`,
`reports/Data-Integrity/rp_data_260814_150045_by_gpt-5-codex_financial-write-safety.md`,
`reports/Edge-Case/rp_edge_260814_150045_by_gpt-5-codex_financial-write-safety.md`.

## R4 — B1 close-financial-write-safety plan

Owner decisions are fixed for this slice: stable immutable request identity,
traceable correction/reversal without silent history mutation, and
all-or-nothing entrustment batches. No clarification is required before
implementation.

### Invariant Family Map

- Family: financial action identity, durable write atomicity, correction trace,
  and derived shipment balance.
- Authority: current LOG-C02 B1 owner decision, `AGENTS.md`, current Mongo
  repository patterns, and `core.logic` as the existing balance source. No
  Logistics `Docs/SPEC`/`SPEC-MAP.md` family exists.
- Sibling surfaces: `views/shipment.py` direct payment form,
  `core/database.py:save_shipment_atomic`,
  `views/entrustment.py:save_entrust_db`,
  `core/database.py:save_entrustment_book`,
  `core/payment_logic.py:apply_lump_sum_payment`, and the B0 Contract proxy
  helper.
- Forbidden fallback: UI-only button disabling, amount/date/customer
  duplicate inference, sequential partial batch writes, editable debt,
  silent payment deletion/overwrite, or a mandatory `shipment_id` on the
  identity registry.
- Verify matrix: direct normal/retry/failure-retry/equal-amount distinct
  identity/concurrent attempt/fresh read-back/derived debt; entrustment
  success/second and middle failure/retry/duplicate retry/fresh read-back;
  correction history/linkage/derived result/reload; Contract proxy and
  lump-sum regression.

### B1 ordered checklist

- [x] P2-B1-A: refresh current status, source map, and Anvien impact before
  editing. Gate: exact target symbols inspected and dirty/high-risk boundary
  recorded. Acceptance: B1 assumptions match current code.
- [ ] P2-B1-B: add stable direct-payment request identity at the persistence
  boundary, unique registry, UI reuse across retry, and correction-safe
  payment history guard. Gate: no new direct payment can bypass request
  identity. Acceptance: duplicate retry has one effect while equal legitimate
  payments remain distinct.
- [ ] P2-B1-C: make `save_entrustment_book` an all-or-nothing transaction
  with stable batch identity and UI retry reuse. Gate: Mongo transaction
  support or fixture fail-closed behavior is proven. Acceptance: every
  injected batch failure leaves zero partial financial state.
- [ ] P2-B1-D: add only the minimum traceable correction/reversal record and
  derived calculation behavior needed by the two paths. Gate: original event
  remains readable and correction linkage is persisted. Acceptance: no silent
  delete/overwrite and derived balance reflects effective history.
- [ ] P2-B1-E: run the complete B1 matrix, full regression, compile, fresh
  Anvien/change detection, and independent reports. Acceptance: B1 is PASS
  only when all owner acceptance points are evidenced; otherwise stop with
  exact PARTIAL/BLOCKED findings and keep ledger/Quick Entry closed.

### B1 boundary

No held/unallocated ledger, Quick Entry suite, standalone proxy fix, contract
transfer fix, GetFly redesign, or shipment audit/outbox broad refactor is
authorized. A shared request registry is allowed only as the smallest
identity/correction primitive and must leave `shipment_id` optional.

## R5 — B1 implementation and acceptance result

Status: **PASS for the bounded B1 boundary**. The implementation closes the
three Owner decisions for direct shipment payment, entrustment batch, and
minimum correction semantics. Quick Entry and the broad ledger remain closed.

- [x] P2-B1-B: direct payment request identity, unique registry, stable UI
  retry identity, and generic payment-history mutation guard are implemented
  and verified.
- [x] P2-B1-C: entrustment batch uses one transaction, stable batch identity,
  UI retry reuse, and fail-closed behavior without transaction support.
- [x] P2-B1-D: payment reversal/correction preserves the original row,
  persists linkage/reason/evidence/actor/time, and recomputes derived balance.
- [x] P2-B1-E: complete B1 matrix, full regression, compileall, fresh
  Anvien, detect-changes, Data-Integrity, Edge-Case, Coder, and Supervisor
  reports are complete.

Evidence: `reports/Data-Integrity/rp_data_260814_154742_by_gpt-5-codex_log-c02-b1-write-safety.md`,
`reports/Edge-Case/rp_edge_260814_154742_by_gpt-5-codex_log-c02-b1-write-safety.md`,
`reports/coder/rp_coder_260814_154742_by_gpt-5-codex_log-c02-b1-write-safety.md`,
and `reports/supervisor/rp_supervisor_260814_154742_by_gpt-5-codex_log-c02-b1-write-safety.md`.

Decision boundary: **CAN LEDGER FOUNDATION BEGIN? YES, but only as a bounded
B2 recommendation**. Do not immediately implement broad Quick Entry. The
smallest B2 should be a shipment-linked obligation/transaction/allocation
read/write boundary that reuses the request/correction primitive, keeps
balances derived, supports unallocated money explicitly, and proves fresh
read-back before any wider entry surface.
