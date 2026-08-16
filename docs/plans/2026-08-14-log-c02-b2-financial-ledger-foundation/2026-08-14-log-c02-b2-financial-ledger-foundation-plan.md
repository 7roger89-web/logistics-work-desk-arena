# LOG-C02 B2 Financial Ledger Foundation + A Bò Golden Financial Case Plan

## Metadata

- Date: `2026-08-14`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-actual-status.md`

## Goal

Implement the smallest durable canonical financial ledger that can represent
obligations, money events, allocations, corrections/reversals, provenance,
ownership, held/unallocated money, received-on-behalf money, and optional
shipment linkage. Prove the model with isolated fixture data, including the
A Bò advance/held-money golden case and the Sale Thành internal-dimension
projection. Derived balances must be calculated from canonical history and
must not become editable stored fields.

## Rules

- Complete P0 actual status before implementation work.
- Preserve the existing dirty worktree; do not reset, checkout, overwrite, or
  absorb unrelated user changes.
- Do not touch P2P, credentials, permissions, deployment, migration of real
  data, or the production business database.
- Do not open Quick Entry, AI, workflow/progress redesign, GL/double-entry,
  full FX, period close, debit generation, Excel migration, portal, GPS, or
  enterprise search.
- Use the current MongoDB architecture and B1 transaction/request/correction
  semantics. The ledger must fail closed when transaction support is absent.
- A financial record may have no shipment. `shipment_ids`/shipment linkage is
  optional and must be attachable later without duplicating history.
- Keep obligation, transaction, allocation, adjustment/reversal, and evidence
  distinct. Never replace them with a manual balance field.
- Preserve original amount/currency and any explicit FX snapshot. B2 does not
  recalculate historical money using today's rate and does not add currencies.
- Keep source/payer, holder, beneficial owner, allowed use/restriction, and
  allocation target as separate concepts. UNKNOWN or RESTRICTED values cannot
  silently enter confirmed position or auto-net.
- Unknown business meanings remain visible and reviewable as UNKNOWN or
  REVIEW_REQUIRED; raw provenance is preserved.
- Synthetic fixture data only. Any isolated Mongo database must have a
  generated name, fresh-client read-back, exact cleanup, and no collision with
  `MONGO_DB_NAME`.
- Run Anvien file-detail and impact evidence before editing affected symbols,
  run change detection before any implementation commit, and record evidence
  as each slice completes.

## Problem

Current finance and payment paths calculate shipment/customer values and keep
several partner, proxy, contract, entrustment, and tax stores, but there is no
canonical obligation/transaction/allocation source. The current shape cannot
truthfully model money that exists before a shipment, money held by A Bò,
received-on-behalf money, later allocation, one-to-many allocation, or
many-to-one settlement. A derived A Bò position and Sale Thành view therefore
cannot be built without either duplicating balances or guessing ownership.

## Scope

- `core/financial_ledger.py`: canonical Mongo ledger write/read helpers,
  derived allocation/outstanding/held/partner projections, ownership and
  restriction guards, optional shipment linking, and deterministic why-number
  explanations.
- `core/database.py`: minimal ledger index registration in the existing
  `ensure_indexes` bootstrap only; preserve existing B1 write paths.
- `views/partner_finance.py`: bounded read-only A Bò / Sale Thành projection
  renderer, if the current runtime can safely render it without a write path.
- `views/finance.py`: minimal read-only projection section using the canonical
  ledger; preserve existing customer receipt flow and controls.
- `tests/test_financial_ledger.py`: fixture-only domain, failure-path, and
  optional disposable Mongo persistence tests.
- B2 plan/evidence/benchmark/actual-status and fresh specialist reports.

## Non-Goals

- No broad Quick Entry or new financial input form.
- No migration/import of existing real shipment, workbook, contract, proxy,
  or entrustment data.
- No replacement of legacy sources in existing Shipment 360 during this
  bounded slice; future projections can consume the ledger after proof.
- No accounting GL, double-entry, tax/legal policy, automatic netting,
  reconciliation inbox, period close, manager report, debit generator, or
  full FX platform.
- No editable partner balance, outstanding, settled, or unallocated field.
- No auto-resolution of unknown terms such as legacy workbook notes.
- No production database write, deployment, credential change, or P2P edit.

## Requirements

### Canonical records

1. Obligation: from party, to party, amount, currency, purpose, optional due
   date, optional shipment linkage, internal sale owner, evidence/provenance,
   and active/reversal status.
2. Transaction/money event: source/payer, holder/receiver, beneficial owner,
   amount/currency, occurred time, request identity, transaction kind,
   internal sale owner, evidence/provenance, optional shipment linkage, and
   separate restriction/allowed-use metadata.
3. Allocation: transaction/credit to obligation, exact currency/amount,
   optional shipment context, request identity, audit/provenance, and active
   or reversed status. One transaction may allocate to many obligations and
   many transactions may allocate to one obligation.
4. Adjustment/reversal: preserve the original record, use a stable request
   identity and reason/evidence/actor/time, and affect derived results only
   through an explicit effective-status transition.
5. Evidence/provenance: structured references to debit, bank proof,
   screenshot/file/reference, legacy source row, raw note, mapping status, and
   review status without creating a document-management platform.

### Derived and safety rules

- Obligation outstanding = original obligation amount - effective allocations.
- Transaction unallocated = transaction amount - effective allocations.
- Partner position is a projection by currency and explicit bucket, never a
  manually stored balance.
- Allocation is blocked when currency, ownership, allowed-use, restriction,
  source availability, target validity, or traceability is not proven.
- UNKNOWN/REVIEW_REQUIRED and RESTRICTED money is retained and visible but
  excluded from confirmed position and legal allocation.
- Sale Thành is only `internal_sale_owner`, never a party or fund owner by
  default; filtering must not change ownership or totals.

## Acceptance Criteria

- P0 actual status classifies existing finance, payment, proxy, entrustment,
  and projection surfaces and states the exact B2 touch boundary.
- Canonical obligation, transaction, and allocation documents persist through
  the current Mongo transaction boundary with optional shipment linkage.
- A held 30M fixture at A Bò can exist without shipment, later allocate into
  an L-001 80M obligation, and derive held 0 / payable outstanding 50M.
- Received-on-behalf, payment-only, multi-allocation, and multiple-payment
  cases remain first-class and do not duplicate transaction history.
- Ownership/restriction/currency checks block unsafe allocation and preserve
  UNKNOWN/REVIEW_REQUIRED rows outside confirmed totals.
- A Bò position exposes payable-to-A Bò, held/credit, received-on-behalf,
  unallocated, restricted, unknown, and derived currency-specific net detail.
- Sale Thành filtering works as an internal dimension without creating a
  party/account or changing ownership.
- Retry, rollback, correction/reversal, and fresh-client read-back satisfy the
  B1 safety standard for the new ledger writes.
- Existing B1 direct-payment, entrustment, contract-proxy, and lump-sum
  regressions remain passing; compileall passes.
- No real business data, migration, deployment, credentials, or P2P source is
  touched.
- Final status is exactly `PASS`, `PARTIAL`, or `BLOCKED`, with unresolved
  financial risks explicit; no B3 work starts automatically.

## Checklist

- [x] P0-A: Complete B2 actual status before implementation.
  - Goal: establish the real current ledger gap, reusable B1 primitives,
    related-file impact, and exact editable/preserve-only boundary.
  - Work Steps: inspect current source, Mongo bootstrap, existing finance and
    projection consumers, B1 tests, worktree, and Anvien file/impact results;
    write the capability matrix; update P1 assumptions before code edits.
  - Implementation Gate: actual-status file has a completed P0 matrix,
    evidence IDs, touch map, and explicit P0 decision.
  - Acceptance: no implementation begins from an assumed schema; all required
    current surfaces are classified as correct/partial/missing/unsafe/
    unknown with a bounded next action.

### P1: Canonical ledger foundation and bounded projection

- Phase Goal: add one source of truth for new canonical ledger records and a
  small read-only projection without changing legacy production data.
- Phase Boundary:
  - In scope: canonical Mongo collections, indexes, transaction-safe helpers,
    derived projections, deterministic explanations, bounded UI read model,
    and fixture tests.
  - Out of scope: migration, broad entry UI, legacy source replacement,
    accounting platform, full reconciliation, and real data.
  - Dependencies: P0 PASS; current Mongo transaction topology or explicit
    fail-closed result; B1 request/correction primitives remain available.
- Phase Implementation Rule: do not implement P1 directly. Complete P1-A,
  refresh status/evidence, then P1-B, then P1-C.
- Ordered Slice List:
  - P1-A: Canonical ledger persistence and derived calculation services.
  - P1-B: Read-only A Bò / Sale Thành projection and why-number surface.
  - P1-C: Fixture, fresh-client, failure-path, regression, and closure proof.

- [x] P1-A: Implement canonical ledger persistence and derived calculation services.
  - Goal: create durable optional-shipment obligation, transaction, allocation,
    link, and reversal paths with one canonical source.
  - Scope Boundary:
    - Editable: `core/financial_ledger.py`, the minimal `ensure_indexes`
      extension in `core/database.py`, and focused ledger tests.
    - Inspect-only: legacy shipment/payment/proxy/entrustment/tax data stores
      except for B1 regression calls.
    - Preserve-only: existing B1 direct payment, correction, entrustment, and
      contract proxy behavior; all unrelated dirty files.
    - Out of scope: migration/import, Quick Entry, auto-net, full FX,
      shipment 360 source replacement.
  - Non-Goals: no editable balance snapshots and no second shipment/A Bò/Sale
    Thành books.
  - Pre-flight Questions:
    - Data source: current Mongo repositories and B1 transaction/request/audit
      conventions; no legacy data import.
    - Display permission: service layer is reusable; UI display waits for
      P1-B.
    - DB read flow: canonical collections queried fresh; effective allocations
      are summed by status.
    - DB write flow: `get_db` + `_transaction_client` + request registry,
      atomic canonical write and audit/correction within one transaction.
    - Render location: N/A for the service slice.
    - UI behavior flow: N/A; tests call the real service boundary.
    - Docker runtime: no Docker artifact exists in this repo; record as
      unavailable for this non-UI slice rather than inventing one.
    - Playwright target: N/A; no UI is changed in P1-A.
    - Behavior test: optional shipment create, optional link, allocation
      cardinalities, restriction/ownership/currency guard, reversal/retry.
    - Cleanup/quarantine: memory fixtures are process-local; Mongo fixtures
      use generated `l02b2_*` databases and exact teardown.
    - External side effects: only an opt-in disposable Mongo fixture DB.
    - N/A notes: migration, legacy import, FX conversion, and real data are
      intentionally not touched.
  - Work Steps:
    1. Implement normalized party, evidence/provenance, canonical payload,
       action fingerprint, and transaction-safe obligation/transaction writes.
       - UI flow check: N/A; no input control is added.
       - DB/data flow check: document fields allow `shipment_ids=[]` and do not
         persist derived balances; request identity is unique and auditable.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: Browser/control capability is only needed when UI changes;
          this service slice uses the real caller/test boundary.
       - Evidence target: `E1-P1A-SVC1..E1-P1A-SVC4`.
    2. Implement allocation validation/derived projections, allocation
       reversal, and later shipment linking without history duplication.
       - UI flow check: N/A; confirm no Quick Entry/control is introduced.
       - DB/data flow check: effective allocation sums drive remaining amounts;
         invalid ownership/restriction/currency/unknown cases fail closed.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST)
          Use fixture perturbations for duplicate request, over-allocation,
          reversed allocation, restricted funds, unknown item, and no-session
          DB.
       - Evidence target: `E1-P1A-SVC5..E1-P1A-SVC9`.
  - Implementation Gate:
    - Before editing target symbols, run Anvien file-detail and impact for the
      chosen files/functions; record the high-risk `core/database.py` boundary
      and keep the edit to index registration only.
    - New writes must fail closed without session transaction support and must
      preserve original records on correction/reversal.
  - Acceptance:
    - Source: canonical collection/payload contracts are explicit and
      shipment-optional.
    - Runtime/UI: N/A; service boundary is tested directly.
    - DB/data: obligation/transaction/allocation and request/audit/correction
      writes are atomic and reloadable.
    - Behavior test: golden held-money, received-on-behalf, payment-only,
      multi-allocation, multiple-payment, guard, reversal, retry cases pass.
    - Cleanup/quarantine: no fixture database remains after opt-in run.
    - Evidence IDs: `E1-P1A-SVC1..E1-P1A-SVC9`.
    - Actual-status rows refreshed: canonical ledger, optional linkage,
      ownership/restriction, and derived projection rows.
  - Evidence Targets: source diff, Anvien impact, focused tests, index names,
    fixture isolation and read-back.
  - Actual-status Update: `missing/blocked -> correct for bounded new-ledger
    writes` is recorded after memory and disposable Mongo fixture proof;
    legacy sources remain partial.
  - Commit Boundary: implementation remains uncommitted until the complete
    B2 dirty-boundary/detect-changes review establishes an isolated boundary.

- [x] P1-B: Add the bounded read-only A Bò / Sale Thành projection.
  - Goal: let an owner read the derived A Bò position and why-number detail
    without entering or editing money.
  - Scope Boundary:
    - Editable: `views/partner_finance.py` and minimal `views/finance.py`
      render wiring, plus focused renderer tests if needed.
    - Inspect-only: existing receipt form and legacy customer calculations.
    - Preserve-only: existing finance controls, shipment 360 legacy read model,
      and all save flows.
    - Out of scope: Quick Entry, reconciliation inbox, manager report, or
      changes to ledger data.
  - Non-Goals: no new write buttons, no automatic netting, no AI explanation.
  - Pre-flight Questions:
    - Data source: `build_partner_financial_position` from canonical ledger.
    - Display permission: existing Finance route; read-only view only.
    - DB read flow: fresh canonical reads on each view render; no session-state
      balance cache as source of truth.
    - DB write flow: N/A; renderer must not call mutation helpers.
    - Render location: bounded section in `views/finance.py` and new renderer.
    - UI behavior flow: choose internal sale owner/partner view, see explicit
      currency buckets, recent allocations, and deterministic drilldown.
    - Docker runtime: no Docker artifact exists; local Streamlit health is the
      available runtime check and Docker gap remains explicit.
    - Playwright target: only if an existing browser/Playwright harness can
      target a real built runtime; otherwise record unavailable, not mocked.
    - Behavior test: renderer source scan plus pure projection contract tests.
    - Cleanup/quarantine: read-only; no persistent state created.
    - External side effects: none.
    - N/A notes: no new route is required; use existing Finance route.
  - Work Steps:
    1. Add explicit bucket formatting and deterministic explanation rows for
       payable, held/credit, received-on-behalf, unallocated, restricted, and
       unknown values grouped by currency.
       - UI flow check: no submit/save/delete controls in the new section.
       - DB/data flow check: each displayed value maps to a canonical record
         and formula; UNKNOWN is displayed but excluded from confirmed totals.
       - Render location check: Finance route only; legacy receipt form remains.
       - Mini QA for each completed implementation slice (MUST)
          Exercise empty ledger, one held fixture, unknown/restricted rows, and
          mixed currencies without summing unlike currencies.
       - Evidence target: `E1-P1B-UI1..E1-P1B-UI3`.
    2. Wire the bounded section with Sale Thành as a dimension and verify
       ownership labels remain source/holder/beneficial-owner values.
       - UI flow check: filter changes read projection only and cannot mutate.
       - DB/data flow check: filter applies to canonical internal owner field;
         totals do not move into a fake Thành party/account.
       - Render location check: existing Finance page renders the section after
         the current read-only summary and before any new control (none).
       - Mini QA for each completed implementation slice (MUST)
          Run local health and, where available, real browser inspection of the
          Finance route; retain limitation if browser capability is absent.
       - Evidence target: `E1-P1B-UI4..E1-P1B-UI6`.
  - Implementation Gate:
    - Run Anvien file-detail/impact for `views/finance.py` and the new renderer;
      source scan must prove no ledger write helper is imported/called.
  - Acceptance:
    - Source: read-only renderer is bounded and source-labelled.
    - Runtime/UI: Finance route remains renderable and shows explicit buckets
      when canonical fixture data is available.
    - DB/data: no new UI write or balance persistence.
    - Behavior test: Sale Thành projection filters without ownership mutation.
    - Cleanup/quarantine: no persistent fixture or session mutation.
    - Evidence IDs: `E1-P1B-UI1..E1-P1B-UI6`.
    - Actual-status rows refreshed: A Bò projection, Sale Thành dimension,
      why-number readiness.
  - Evidence Targets: source scan, projection tests, local health/browser
    evidence if available, and no-mutation check.
  - Actual-status Update: `missing -> bounded/read-only` after the local
    Streamlit health check; Docker/browser closure remains explicitly
    unavailable and there is no claim of complete reconciliation.
  - Commit Boundary: keep UI commit isolated from service commit when safe.

- [ ] P1-C: Execute fixture, fresh-client, regression, and closure proof.
  - Goal: verify all B2 matrix items that are in scope and produce a truthful
    PASS/PARTIAL/BLOCKED decision.
  - Scope Boundary:
    - Editable: focused tests, plan/evidence/benchmark/status, specialist
      reports, and no unrelated production files.
    - Inspect-only: real business database and existing dirty modifications.
    - Preserve-only: B1 artifacts and P2P source.
    - Out of scope: broad hardening after the bounded gate.
  - Non-Goals: fixture PASS cannot be promoted to production-wide safety when
    topology or dirty-boundary evidence is missing.
  - Pre-flight Questions:
    - Data source: synthetic in-memory and optional isolated Mongo fixtures.
    - Display permission: read-only runtime check only.
    - DB read flow: fresh client reads canonical rows and recomputes totals.
    - DB write flow: retry/rollback/reversal and no-session fail-closed tests.
    - Render location: existing Finance route if P1-B is complete.
    - UI behavior flow: no mutation action; inspect render only.
    - Docker runtime: no Dockerfile/compose found; report incomplete full-build
      requirement instead of substituting a host browser proof.
    - Playwright target: real built runtime only; otherwise N/A with reason.
    - Behavior test: full B2 matrix plus full affected unittest suite.
    - Cleanup/quarantine: exact generated Mongo database inventory and teardown.
    - External side effects: none beyond opt-in disposable fixture DB.
    - N/A notes: no migration or production smoke write is permitted.
  - Work Steps:
    1. Run focused ledger tests, optional Mongo tests, compileall, and the full
       affected unittest suite; record counts and failures.
       - UI flow check: N/A or read-only health only.
       - DB/data flow check: fresh-client persistence and derived equations.
       - Render location check: Finance route health if UI changed.
       - Mini QA for each completed implementation slice (MUST)
          Use only fixture data and verify cleanup before closure.
       - Evidence target: `E2-P1C-TEST1..E2-P1C-TEST8`.
    2. Run fresh Data-Integrity, Edge-Case, coder, and supervisor review; run
       Anvien detect-changes; refresh all four plan files and decision log.
       - UI flow check: supervisor validates read-only boundary and any runtime
         evidence available.
       - DB/data flow check: integrity review verifies source/derived split,
         idempotency, correction, and unknown/restricted handling.
       - Render location check: no broad UI redesign or Quick Entry.
       - Mini QA for each completed implementation slice (MUST)
          Review report hashes/paths and ensure no specialist artifact is left
          uncommitted where its skill requires a commit.
       - Evidence target: `E2-P1C-REVIEW1..E2-P1C-REVIEW6`.
  - Implementation Gate:
    - All required matrix rows have pass/fail evidence; unresolved topology,
      Docker, or dirty-boundary risk is stated rather than hidden.
  - Acceptance:
    - Source: no forbidden scope expansion or fake balance field.
    - Runtime/UI: bounded read-only route check, or explicit unavailable
      evidence when the required runtime vehicle cannot be used.
    - DB/data: fixture cleanup and fresh read-back are proven.
    - Behavior test: focused, full affected, and compileall results recorded.
    - Cleanup/quarantine: no generated business fixture remains.
    - Evidence IDs: `E2-P1C-TEST1..E2-P1C-REVIEW6`.
    - Actual-status rows refreshed: all B2 rows and final decision.
  - Evidence Targets: test outputs, cleanup inventory, graph/detect-changes,
    specialist reports, supervisor verdict, and commit/worktree state.
  - Actual-status Update: append final B2 refresh; mark only proven surfaces
    correct and leave unproven legacy/migration/runtime items partial or blocked.
  - Commit Boundary: commit only isolated B2-owned changes/reports when safe;
    never stage unrelated dirty worktree files.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed B2 work against the accepted plan, evidence,
    benchmark, changed files, generated output, and validation results.
  - Work Steps:
    1. Call the supervisor skill for the full completed-plan review.
    2. If supervisor fails, fix only the failed B2 scope and rerun review.
    3. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: implementation phases are complete or explicitly
    blocked and evidence is current.
  - Acceptance: supervisor passes or a blocker is recorded without false
    closure.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: leave only artifacts serving accepted B2 scope.
  - Work Steps:
    1. Review B2-created source, tests, reports, temporary files, and plan
       artifacts.
    2. Remove only dead artifacts created by this plan.
    3. Run supervisor review for cleanup.
  - Implementation Gate: do not delete pre-existing user files or unrelated
    dirty changes.
  - Acceptance: no stale placeholder, rejected approach, or temporary fixture
    remains in the B2-owned diff.
- [ ] Pn-C: Close the plan.
  - Goal: record final validation, detect-changes, benchmark, commit/worktree
    state, and the exact B2 result.
  - Work Steps:
    1. Run required final validation and state Docker/runtime limitation.
    2. Run detect-changes before any implementation commit.
    3. Record evidence, specialist reports, and decision log.
    4. Commit only isolated B2 outputs when possible and verify status.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: final result is PASS/PARTIAL/BLOCKED and no B3 implementation
    starts in this turn.

## Risk Notes

- `core/database.py` is a high-risk dirty file with broad unresolved graph
  references. Keep its edit to additive index registration and preserve B1
  code already present.
- Mongo transaction support and fresh-client topology are available only as
  fixture evidence; do not generalize without the opt-in proof.
- Existing legacy shipment payment, proxy, entrustment, tax, and contract
  stores remain separate and may still be partial or unsafe. B2 does not
  silently migrate them.
- Cross-currency netting, unknown ownership, and restricted money must remain
  blocked/review-required.
- The repository has no Docker artifact known at P0. The planner's full-build
  Docker requirement therefore remains an explicit environment limitation for
  UI closure, not permission to invent or install one.

## Closure Decision Override — 2026-08-14

- `Pn-A` review was executed; Supervisor verdict is `REJECT` in
  `reports/supervisor/rp_supervisor_260814_165706_by_gpt-5-codex_log_c02_b2_ledger.md`.
- `Pn-B` found no B2-created disposable database or dead temporary fixture
  artifact; pre-existing user files and dirty changes were preserved.
- `Pn-C` remains open. Overall B2 result is `PARTIAL`, not accepted closure,
  until the supervisor blockers are either evidenced closed or explicitly
  re-scoped by the Owner.
