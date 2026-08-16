# LOG-C05 Manager Report & Debit Draft Plan

## Metadata

- Date: `2026-08-14`
- Status: `complete (bounded local scope; Docker and positive-live explicitly blocked/unverified)`
- Plan: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-actual-status.md`

## Goal

Implement the bounded LOG-C05 workflow for SALE Thành and A Bò: derive a
Vietnamese manager report and a currency-separated Debit Draft from the
canonical partner ledger, show confirmed versus review-required amounts, keep
deterministic explanations and source IDs, preserve READY_FOR_REVIEW snapshot
versions with retry-safe metadata-only writes, and prove that no underlying
financial record changes.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- For app/runtime validation, record Docker as unavailable if the repository has no Docker build target; do not claim container acceptance from a host-only run.
- Any Playwright validation must record the actual runtime, URL, command, screenshot, and result. Host Streamlit evidence is explicitly labelled local when Docker is unavailable.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase is decomposed into narrow slices; do not implement a phase directly.
- Hidden fallbacks are forbidden. An empty or unavailable canonical state must be visible and truthful.
- Snapshot metadata may be written, but obligations, transactions, allocations, corrections, and partner position must remain unchanged.
- No AI, payment execution, bank integration, Excel migration, owner inference, accounting GL, or frontend rewrite.
- Preserve all unrelated dirty-worktree changes; no reset, checkout, broad staging, or forced commit.

## Problem

LOG-C04 already provides the canonical A Bò / SALE Thành projection, review
inbox, trace, period draft, and partner-reported comparison. The next business
step is missing: Thành cannot produce a manager-readable report or derive a
Debit Draft from confirmed eligible rows. There is also no preserved debit
snapshot that can answer six months later why a historical amount was X.

The current live projection may legitimately be empty because historical
`internal_sale_owner` coverage is incomplete. LOG-C05 must use isolated
fixtures for positive arithmetic and keep the live UI honest.

## Scope

- Pure deterministic manager-report summary, explanation, important-shipment aggregation, review separation, and partner-difference presentation.
- Pure deterministic debit eligibility and currency-separated Debit Draft calculation from the existing projection.
- Metadata-only snapshot document, version identity, supersession trace, and stable request-id retry behavior.
- Minimal MongoDB snapshot collection/index integration through the existing database layer.
- Existing Streamlit Reconciliation Desk actions for Báo cáo Sếp and Debit Draft, including included/excluded details and “Vì sao debit ra số này?”.
- Isolated golden fixtures, financial write oracle, snapshot immutability/reproducibility tests, regression tests, and reusable browser evidence.

## Non-Goals

- Payment execution, bank transfer, settlement write, approval workflow, or payment button.
- Real workbook import/migration or mutation of live business data.
- Manual debit total override when the canonical ledger can derive the amount.
- Automatic owner normalization or inference from notes/text.
- Full FX platform, current-rate conversion, accounting GL, double-entry, tax/policy module, or period close.
- New home-screen design, shipment redesign, customer portal, Docker setup, or unrelated dirty-worktree repair.
- Large document-generation/export subsystem; only existing safe export is reused if directly compatible.

## Requirements

- Report header contains period, generated date, SALE Thành, A Bò, currencies, and DRAFT/READY FOR REVIEW status without inventing approval.
- Report separates payable, held credit, received-on-behalf, paid-on-behalf, settled/canceled amounts, unallocated, unknown/restricted, confirmed position, and debit-eligible amount per currency.
- Report explanation is deterministic, source-ID-backed, and visibly separates confirmed from review-required rows.
- Shipment breakdown is derived and sorted from actual shipment linkage; names are never hard-coded.
- Partner-reported differences are shown and never silently included in debit.
- Debit eligibility requires known currency/owner, confirmed classification, allowed restriction, effective non-reversed record, available outstanding amount, minimum evidence, and no prior effective debit inclusion.
- Debit calculation never combines CNY/USD/VND and never uses a current FX rate to fabricate one total.
- Debit Draft contains payable lines, credit/settlement lines, included and excluded items, exact arithmetic, and a deterministic explanation.
- READY_FOR_REVIEW snapshot preserves period, all relevant ledger/obligation/transaction/allocation IDs, correction/reversal state, totals, exclusions, generated time, preparer, version, identity, and content hash.
- Regeneration creates a traceable new version and preserves V1; same request identity is retry-safe and does not duplicate a snapshot.
- Report/debit calculations have zero financial effects; metadata snapshot writes are explicitly separated and tested.
- Live empty state remains “Chưa có dữ liệu canonical đủ điều kiện” or equivalent truthful wording.

## Acceptance Criteria

- Thành can reach the existing A Bò / SALE Thành desk and open Báo cáo Sếp and Debit Draft.
- Positive fixture report and debit values reconcile exactly to canonical fixture records.
- UNKNOWN, restricted, unallocated-not-approved, missing evidence, currency mismatch, reversed, settled, and unresolved partner differences remain out of debit.
- 24,576 CNY credit, 62,464 CNY and 1,687 CNY received-on-behalf, 1,572 CNY UNKNOWN, 25,025 CNY customer-receipt-leg, and 134,973 CNY paid-on-behalf semantics are all covered.
- Clean fixture computes 40,000 CNY from 100,000 payable with 30,000 held credit, 20,000 allocated received-on-behalf, and 10,000 already settled through canonical allocation history.
- Multi-currency output remains separated.
- V1 remains reproducible after a V2 regeneration; snapshot write retry does not duplicate.
- Before/after ledger collections and position are equal for report/debit calculation and unchanged by metadata-only snapshot persistence.
- LOG-C02/C03/C04 regression tests, compileall, Streamlit health, and the reusable browser flow are recorded. Docker/positive-live limitations are explicitly separated if unavailable.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect the canonical projection, existing reconciliation helpers, partner desk route, database/index conventions, fixture semantics, worktree, and Anvien blast radius; classify every LOG-C05 surface and update downstream slice assumptions.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope with exact evidence IDs.

### P1: Deterministic report, debit, and snapshot domain

- Phase Goal: create the source-derived business model and metadata snapshot contract without changing financial records.
- Phase Boundary:
  - In scope: pure report/debit functions, eligibility rules, source IDs, versioned snapshot document, repository metadata write, and focused tests.
  - Out of scope: Streamlit rendering, browser QA, live data seeding, payment, and owner migration.
  - Dependencies: P0 actual status; LOG-C02 canonical projection; existing Mongo repository conventions.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Add pure manager-report and Debit Draft calculator.
  - P1-B: Add metadata-only snapshot/version repository and oracle.

  - [x] P1-A: Add pure manager-report and Debit Draft calculator
  - Goal: derive all report/debit amounts, inclusion/exclusion reasons, shipment impact, and exact formulas from one canonical position mapping.
  - Scope Boundary:
    - Editable: new `core/debit_draft.py` and its focused fixture test module after implementation.
    - Inspect-only: `core/financial_ledger.py` projection and existing LOG-C02/C04 tests.
    - Preserve-only: canonical financial write functions, existing `core/reconciliation.py` helpers, and current formulas.
    - Out of scope: database access, Streamlit, manual totals, payment, and live fixtures.
  - Non-Goals: no new ledger bucket persistence, no FX conversion, no AI-generated prose, and no silent fallback amount.
  - Pre-flight Questions:
    - Data source: existing `project_partner_financial_position` result and its bucket/source/allocation fields.
    - Display permission: exact canonical `internal_sale_owner = Thành`; missing owner is excluded and reported as a gap.
    - DB read flow: N/A; pure function receives a position mapping.
    - DB write flow: N/A; P1-A must have zero writes.
    - Render location: N/A; P2-A consumes the returned contract in `views/partner_reconciliation.py`.
    - UI behavior flow: N/A; tested in P2.
    - Docker runtime: N/A for pure domain slice.
    - Playwright target: N/A for pure domain slice.
    - Behavior test: fixture trigger -> calculator -> exact report/debit values and exclusions.
    - Cleanup/quarantine: fixture objects are in-memory only; no live DB or workbook access.
    - External side effects: none.
    - N/A notes: snapshot persistence is a separate P1-B slice.
  - Work Steps:
    1. Implement deterministic eligibility, per-currency summary, explanation lines, shipment aggregation, partner-difference exclusion, and debit arithmetic.
       - UI flow check: N/A; return stable presentation data for the UI.
       - DB/data flow check: verify source rows are copied/read only and no derived amount is written back.
       - Render location check: keep all presentation-ready labels in the pure contract, not raw Streamlit calls.
       - Mini QA for each completed implementation slice (MUST): use pure behavior tests and inspect the generated contract; browser is not applicable before P2.
       - Evidence target: E1-P1A-MODEL1, E1-P1A-TEST1.
    2. Add the golden LOG-C04 and clean-debit fixture matrix after the behavior is implemented.
       - UI flow check: N/A; fixture contract is consumed by P2 UI.
       - DB/data flow check: snapshot of fixture inputs before/after remains equal.
       - Render location check: assert labels and formulas are deterministic and source-ID-backed.
       - Mini QA for each completed implementation slice (MUST): run focused pytest and compileall for touched pure modules.
       - Evidence target: E1-P1A-TEST2, E1-P1A-ORACLE1.
  - Implementation Gate:
    - Before editing target files, Anvien graph is refreshed and the P0 file-detail/impact evidence is recorded.
    - The calculator has no imports of Streamlit, database, AI SDKs, or payment modules.
    - E1 tests define exact observable arithmetic before moving to UI.
  - Acceptance:
    - Source: calculator consumes canonical buckets and never accepts a user-entered total.
    - Runtime/UI: N/A for this slice.
    - DB/data: input position is unchanged after calculation.
    - Behavior test: clean fixture equals 40,000 CNY; golden exclusions and shipment aggregation pass.
    - Cleanup/quarantine: no persistent fixture data is created.
    - Evidence IDs: E1-P1A-MODEL1..E1-P1A-ORACLE1.
    - Actual-status rows refreshed: pure report/debit model missing -> correct; golden fixtures partial -> correct.
  - Evidence Targets: model source inspection, exact fixture tests, no-write oracle, compileall.
  - Actual-status Update: mark P1-A correct only after direct tests prove every required inclusion/exclusion class.
  - Commit Boundary: commit after this slice when acceptance passes.

  - [x] P1-B: Add metadata-only snapshot/version repository and oracle
  - Goal: preserve READY_FOR_REVIEW debit content with stable identity, versions, supersession trace, and retry-safe metadata write.
  - Scope Boundary:
    - Editable: `core/debit_draft.py` snapshot/repository functions and the existing `ensure_indexes` index list only if required by the repository contract; focused snapshot tests.
    - Inspect-only: existing financial action/request patterns and canonical collections.
    - Preserve-only: obligations, transactions, allocations, corrections, partner position, and financial action effects.
    - Out of scope: payment/settlement writes, schema migration/backfill, and live business data.
  - Non-Goals: no approval workflow beyond DRAFT/READY_FOR_REVIEW/SUPERSEDED.
  - Pre-flight Questions:
    - Data source: the immutable-in-memory debit contract produced by P1-A.
    - Display permission: prepared-by is current user/system identity; no approval is inferred.
    - DB read flow: optional `debit_draft_snapshots` metadata collection for version lookup/reopen.
    - DB write flow: one insert-only snapshot document keyed by stable `request_id`; no financial collection write.
    - Render location: P2-A snapshot controls in the existing partner desk.
    - UI behavior flow: create READY_FOR_REVIEW -> read back -> regenerate V2 -> reopen V1.
    - Docker runtime: N/A for repository unit tests.
    - Playwright target: N/A; P2-B covers mounted action.
    - Behavior test: same request retry returns the same snapshot; changed version preserves V1 and links V2.
    - Cleanup/quarantine: memory database only; no production DB connection in tests.
    - External side effects: metadata collection/index only when explicitly invoked.
    - N/A notes: no full close/lock.
  - Work Steps:
    1. Build a canonical snapshot document containing period, ledger/obligation/transaction/allocation IDs, correction/reversal state, totals, exclusions, generated_at, prepared_by, version, snapshot identity, and content hash.
       - UI flow check: N/A; document is the reopenable source for P2.
       - DB/data flow check: compare canonical collection snapshots before and after document construction.
       - Render location check: document contains enough fields to render V1 without current-ledger recalculation.
       - Mini QA for each completed implementation slice (MUST): run focused snapshot serialization/reproducibility tests.
       - Evidence target: E1-P1B-SNAPSHOT1, E1-P1B-TEST1.
    2. Add stable request-id insert/readback, unique index convention, version/supersession handling, and financial write oracle.
       - UI flow check: N/A; P2 invokes only the metadata operation after READY_FOR_REVIEW.
       - DB/data flow check: assert obligations/transactions/allocations/position hashes are identical before and after.
       - Render location check: snapshot status is limited to DRAFT/READY_FOR_REVIEW/SUPERSEDED.
       - Mini QA for each completed implementation slice (MUST): run retry, V1/V2, and no-financial-write tests.
       - Evidence target: E1-P1B-RETRY1, E1-P1B-ORACLE1.
  - Implementation Gate:
    - Anvien file-detail/impact evidence for `core/database.py` is reviewed before touching the shared index function.
    - The write path has stable request identity, duplicate handling, and no update to financial collections.
    - Snapshot content is immutable after insert; regeneration is a new version.
  - Acceptance:
    - Source: snapshot document contains all required reference fields and a deterministic content hash.
    - Runtime/UI: N/A for this slice.
    - DB/data: metadata-only collection changes; canonical financial collections and derived position remain equal.
    - Behavior test: retry is idempotent; V1 remains reproducible; V2 links to V1 and is not a silent overwrite.
    - Cleanup/quarantine: only disposable memory DB is used by tests.
    - Evidence IDs: E1-P1B-SNAPSHOT1..E1-P1B-ORACLE1.
    - Actual-status rows refreshed: snapshot contract missing -> correct; snapshot write oracle missing -> correct.
  - Evidence Targets: snapshot JSON shape, memory DB readback, retry/V1/V2 tests, canonical before/after hash.
  - Actual-status Update: record metadata-only write as correct while preserving explicit live DB migration/deploy as out of scope.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: Mounted manager report and Debit Draft UX

- Phase Goal: expose the pure contract from the existing Reconciliation Desk using Vietnamese progressive disclosure and truthful live empty state.
- Phase Boundary:
  - In scope: current partner desk action buttons, report surface, debit surface, snapshot/reopen controls, and reusable browser flow.
  - Out of scope: route/home redesign, payment, Excel, and real-data seeding.
  - Dependencies: P1-A/P1-B contracts and existing C04 route.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P2-B`.
- Ordered Slice List:
  - P2-A: Wire Báo cáo Sếp and Debit Draft into the existing partner desk.
  - P2-B: Add browser journey and mounted no-write/empty-state evidence.

- [x] P2-A: Wire Báo cáo Sếp and Debit Draft into the existing partner desk
  - Goal: let a non-accountant open the manager report, understand the summary, inspect explanations/exclusions, and open the Debit Draft without leaving the approved route.
  - Scope Boundary:
    - Editable: `views/partner_reconciliation.py`; add only a minimal `views` helper if the existing file cannot keep the surface bounded.
    - Inspect-only: `views/web_app.py` route registry because `Công nợ A Bò` already mounts the correct desk.
    - Preserve-only: Dashboard, Shipment 360, Finance, C04 search/trace/period/reported comparison, and all financial write routes.
    - Out of scope: new navigation home, payment button, manual debit input, and export subsystem.
  - Non-Goals: no fake positive live rows; no AI text.
  - Pre-flight Questions:
    - Data source: live `build_partner_financial_position` plus pure report/debit model.
    - Display permission: existing `receivables` route and exact SALE Thành filter.
    - DB read flow: one canonical projection read per render; no snapshot read required for DRAFT view.
    - DB write flow: only explicit READY_FOR_REVIEW metadata snapshot action.
    - Render location: existing `views/partner_reconciliation.py` with bounded surface navigation.
    - UI behavior flow: desk -> Báo cáo Sếp -> explanation/attention -> Debit Draft -> included/excluded -> snapshot/reopen -> desk.
    - Docker runtime: use local Streamlit only if Docker target is unavailable and label evidence accordingly.
    - Playwright target: `playwright/log_c05_manager_report_debit_flow.mjs` against the mounted app.
    - Behavior test: Streamlit recorder proves report/debit rendering has zero financial writes.
    - Cleanup/quarantine: snapshot UI is disabled when DB is unavailable; no fixture seeding into live app.
    - External side effects: optional metadata snapshot write only after user action.
    - N/A notes: existing report export is shipment-oriented and not reused for partner debit.
  - Work Steps:
    1. Add bounded action navigation and manager report rendering with Vietnamese summary, confirmed/review split, explanation, important shipments, and partner difference section.
       - UI flow check: action is reachable from the existing route and back navigation returns to the desk.
       - DB/data flow check: report reads the canonical projection and does not call financial writes.
       - Render location check: top summary first, details in expanders, IDs/evidence at the bottom.
       - Mini QA for each completed implementation slice (MUST): Streamlit recorder and local visible app check.
       - Evidence target: E2-P2A-REPORT1, E2-P2A-WRITE1.
    2. Add Debit Draft rendering, explicit inclusion/exclusion tables, formula explanation, multi-currency separation, and guarded snapshot/reopen controls.
       - UI flow check: debit-ready amount is derived, no number input exists, and snapshot button is absent/disabled when no eligible data or DB is unavailable.
       - DB/data flow check: save/readback is metadata-only; reopening uses snapshot content.
       - Render location check: included items above excluded items, with “Vì sao debit ra số này?” expanded on demand.
       - Mini QA for each completed implementation slice (MUST): recorder tests plus snapshot readback fixture.
       - Evidence target: E2-P2A-DEBIT1, E2-P2A-WRITE2.
  - Implementation Gate:
    - Anvien file risk remains high because the view has unresolved graph references, while the refreshed upstream impact is MEDIUM and contained to 1 affected file/1 flow; preserve C04 sibling surfaces.
    - No input field accepts or stores a debit total.
    - UI has explicit empty/error states and no fallback data.
  - Acceptance:
    - Source: view calls the pure model and existing canonical projection only.
    - Runtime/UI: report and debit actions are reachable and understandable in Vietnamese.
    - DB/data: calculations zero financial effects; snapshot action writes only snapshot metadata.
    - Behavior test: recorder sees report/debit labels, included/excluded sections, exact explanation, and zero financial writes.
    - Cleanup/quarantine: no live fixture rows are added.
    - Evidence IDs: E2-P2A-REPORT1..E2-P2A-WRITE2.
    - Actual-status rows refreshed: report/debit UI missing -> correct for local mounted scope; Docker/positive-live remain explicit blockers if applicable.
  - Evidence Targets: source/impact, recorder test, local runtime screenshot/DOM, no-write proof.
  - Actual-status Update: mark the existing desk partial -> correct for the bounded local scope without changing route/home.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-B: Add browser journey and mounted no-write/empty-state evidence
  - Goal: prove the real user journey through the existing Streamlit runtime with reusable Playwright evidence and screenshots.
  - Scope Boundary:
    - Editable: `playwright/log_c05_manager_report_debit_flow.mjs` and official LOG-C05 QA JSON/MD artifacts.
    - Inspect-only: existing C01-C04 browser flows and route wiring.
    - Preserve-only: prior QA artifacts and unrelated browser scripts.
    - Out of scope: seeding live positive data, Docker creation, and code fixes during QA.
  - Non-Goals: no approval of unverified Docker/positive-live scope.
  - Pre-flight Questions:
    - Data source: actual live canonical projection; positive arithmetic remains fixture-only.
    - Display permission: local admin/session and existing receivables permission.
    - DB read flow: canonical projection read; snapshot write only if mounted data supports it and test fixture allows it.
    - DB write flow: verify no financial write controls are reachable; metadata snapshot is not counted as financial effect.
    - Render location: visible Streamlit page opened from the app entry point.
    - UI behavior flow: open app -> desk -> report -> expand explanation -> debit -> inspect included/excluded/explanation -> back -> dashboard.
    - Docker runtime: record blocked if no Dockerfile/daemon; do not substitute silently.
    - Playwright target: current reusable local Streamlit process and visible browser tooling available in this workspace.
    - Behavior test: screenshots and structured action ledger, not DOM-only proof.
    - Cleanup/quarantine: no live data mutation; terminate only the process started by the flow if needed.
    - External side effects: none unless explicit metadata snapshot fixture action is supported.
    - N/A notes: positive live debit values remain unverified when owner-normalized live rows are absent.
  - Work Steps:
    1. Implement the reusable journey, control inventory, screenshot checkpoints, console capture, and truthful empty-state assertions.
       - UI flow check: cover every in-scope action, expander, back path, and dashboard return.
       - DB/data flow check: record live source state and confirm no fixture insertion.
       - Render location check: inspect full screenshots for overflow, mixed language, hidden fallback, and wrong money labels.
       - Mini QA for each completed implementation slice (MUST): run the flow against the latest built/local runtime and inspect screenshots.
       - Evidence target: E2-P2B-BROWSER1, E2-P2B-CONSOLE1.
    2. Record official QA report and classify local pass versus Docker/positive-live blockers.
       - UI flow check: no downstream flow is marked pass when an upstream runtime blocker prevents it.
       - DB/data flow check: source-of-truth table distinguishes live empty state from fixture-only positive state.
       - Render location check: evidence links point to exact screenshots/JSON/MD.
       - Mini QA for each completed implementation slice (MUST): re-open and visually inspect captured screenshots.
       - Evidence target: E2-P2B-REPORT1.
  - Implementation Gate:
    - Playwright script is reusable under `playwright/`, not a temp file.
    - QA does not fix code or seed live data.
    - Browser evidence identifies the runtime and any blocked production-like target.
  - Acceptance:
    - Source: journey covers existing navigation and new actions.
    - Runtime/UI: local route, report, debit, explanation, and back states are evidenced; Dashboard-first navigation remains visible, while the final direct screenshot pass did not claim a full dashboard-return journey.
    - DB/data: no financial write count increase and no live canonical mutation.
    - Behavior test: official JSON/MD and screenshots are present and inspected.
    - Cleanup/quarantine: started local process is stopped; no live rows are left behind.
    - Evidence IDs: E2-P2B-BROWSER1..E2-P2B-REPORT1.
    - Actual-status rows refreshed: browser partial -> correct for local scope; production-like blockers recorded separately.
  - Evidence Targets: browser action ledger, screenshots, console/error output, runtime health.
  - Actual-status Update: append local browser evidence and preserve explicit unverified states.
  - Commit Boundary: commit after this slice when acceptance passes.

### P3: Regression, build, and closure evidence

- Phase Goal: run affected product/regression checks, compile/build/runtime health, Anvien change detection, and closure reporting.
- Phase Boundary:
  - In scope: full available build, focused/full tests, C02/C03/C04 regression, Streamlit health, browser artifact verification, final plan evidence, and reports.
  - Out of scope: optional hardening after PASS, Docker implementation, live data migration, and next Goal implementation.
  - Dependencies: P1/P2 slices complete or explicitly blocked.
- Phase Implementation Rule: do not implement `P3` directly. Implement `P3-A`, verify it, record evidence, refresh actual-status, then run supervisor closure.
- Ordered Slice List:
  - P3-A: Run validation, update ledgers, and prepare closure reports.

- [x] P3-A: Run validation, update ledgers, and prepare closure reports
  - Goal: prove the accepted LOG-C05 scope and state remaining blockers without overstating product readiness.
  - Scope Boundary:
    - Editable: plan evidence/benchmark/actual-status, official reports, and only test/fixture corrections required by the implemented behavior.
    - Inspect-only: final source diff, git status, prior LOG-C02/C03/C04 reports.
    - Preserve-only: unrelated dirty-worktree changes and protected P2P artifacts.
    - Out of scope: new feature slices or optional hardening after terminal PASS.
  - Non-Goals: no release/deploy/merge/publish and no approval request for this local implementation task.
  - Pre-flight Questions:
    - Data source: tests, actual local runtime, fixture hashes, and canonical before/after snapshots.
    - Display permission: existing local admin runtime.
    - DB read flow: compile/test fixture DB and local runtime read path.
    - DB write flow: metadata-only oracle plus financial write oracle.
    - Render location: official reports and final task response.
    - UI behavior flow: full LOG-C05 journey plus regressions.
    - Docker runtime: check and record actual availability; no fake pass.
    - Playwright target: latest mounted runtime only.
    - Behavior test: `pytest`, `compileall`, health, browser, and Anvien detect-changes.
    - Cleanup/quarantine: remove only plan-created temp logs/processes; keep official evidence.
    - External side effects: none.
    - N/A notes: no deployment or release gate is requested.
  - Work Steps:
    1. Run focused and regression tests, compileall, health, browser evidence, and database/write oracles.
       - UI flow check: record every required state and any blocked downstream scope.
       - DB/data flow check: compare before/after hashes for canonical financial collections and position.
       - Render location check: validate official report paths and screenshot references.
       - Mini QA for each completed implementation slice (MUST): inspect test output and runtime artifacts before closure.
       - Evidence target: E3-P3A-TEST1, E3-P3A-REG1, E3-P3A-BROWSER1.
    2. Refresh plan ledgers, run Anvien detect-changes, and prepare coder/supervisor review inputs.
       - UI flow check: N/A; closure evidence records product verdict.
       - DB/data flow check: record metadata-only writes and any blockers.
       - Render location check: final status must separate PRODUCT VERDICT from P2P FORMAL HELPER VERDICT.
       - Mini QA for each completed implementation slice (MUST): inspect git status and diff scope; do not broad-stage.
       - Evidence target: E3-P3A-DETECT1, E3-P3A-REPORT1.
  - Implementation Gate:
    - All required affected checks have a command/result or explicit blocker.
    - Anvien detect-changes is run before any implementation commit.
    - Product closure does not claim unverified Docker/positive-live behavior.
  - Acceptance:
    - Source: final diff is limited to LOG-C05 plus plan/evidence artifacts.
    - Runtime/UI: local user-visible behavior and blockers are reported accurately.
    - DB/data: financial write oracle passes and canonical before/after proof is recorded.
    - Behavior test: regression suite and compileall pass or each failure is classified with evidence.
    - Cleanup/quarantine: no plan-created temporary artifact is accidentally treated as product data.
    - Evidence IDs: E3-P3A-TEST1..E3-P3A-REPORT1.
    - Actual-status rows refreshed: all affected rows have final local/blocked states.
  - Evidence Targets: tests, build, health, browser, Anvien detect-changes, worktree, and closure reports.
  - Actual-status Update: record final state and stop at PASS/PARTIAL/BLOCKED without opening LOG-C06.
  - Commit Boundary: commit only the completed LOG-C05 implementation checkpoint after detect-changes; do not commit unrelated dirty files.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the scoped cleanup/preservation boundary.
    5. If supervisor fails the cleanup boundary, return to the responsible implementation workflow/skill for the failed scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup; unrelated dirty-worktree files remain preserved.
  - Acceptance: the scoped committed diff contains only LOG-C05 implementation/evidence artifacts; earlier debug PNGs remain explicitly uncommitted in the intentionally dirty workspace and are not part of the deliverable. Evidence records this preservation boundary.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run the required final validation for the accepted scope, including full available build before final runtime validation.
    2. Check whether Docker can build/start; if not, record the production-like blocker and do not substitute it silently.
    3. Validate public runtime or UI-facing changes with browser or Playwright evidence against the latest available mounted runtime, clearly labelling local-only evidence.
    4. Regenerate generated outputs if source-of-truth changes require it.
    5. Run Anvien detect-changes before commit when implementation work was performed.
    6. Record final validation, detect-changes, benchmark, and commit evidence.
    7. Commit only scoped LOG-C05 files and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist, the supervisor is PASS for bounded local scope, and the intentionally dirty worktree state is known.

## Risk Notes

- `core/financial_ledger.py` and `core/database.py` are high-blast-radius shared modules. Prefer new pure code and a narrow snapshot index addition; do not alter financial write paths.
- Existing owner normalization is incomplete. Live positive rows may be absent; fixtures must prove arithmetic without injecting real data.
- A metadata snapshot collection is new persistence surface. It must be uniquely keyed by request identity, retain old versions, and be covered by memory-DB tests.
- The project has no Dockerfile in the current workspace. Docker acceptance may remain blocked even when the local product scope passes.
- The current worktree is intentionally dirty with prior Goal artifacts. Only LOG-C05 files are in scope for new edits.
