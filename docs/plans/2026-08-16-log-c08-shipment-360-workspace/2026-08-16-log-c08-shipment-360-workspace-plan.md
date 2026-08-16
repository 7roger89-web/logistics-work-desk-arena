# LOG-C08 Shipment 360 Workspace Plan

## Metadata

- Date: `2026-08-16`
- Status: `bounded_terminal`
- Plan: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-actual-status.md`

## Goal

Make Shipment 360 the daily operational work surface reached from the LOG-C07 shipment-first Dashboard. Support and SALE Thành must be able to identify the shipment, understand stage/owner/deadlines/risks, see factory and customer context, understand document completeness and history, choose the next action, and inspect canonical financial meaning without creating a second ledger or mutating historical A Bò state.

## Rules

- Complete P0 actual status before implementation work.
- Preserve LOG-C02 through LOG-C07 behavior and evidence.
- Use the existing Streamlit/Python stack; no React rewrite or unrelated infrastructure.
- Treat `core.financial_ledger.py`, historical staging, and existing safe writers as preserve-only.
- Use deterministic rules and explicit `UNKNOWN`; do not invent operational, document, financial, or historical facts.
- The new workspace summary is read-only. Existing save, payment, rename, and delete controls remain where they already exist and are not expanded.
- Run Anvien detect-changes before any implementation-slice commit when implementation work is performed.
- Validate the real local runtime and record Docker/pytest limitations honestly if unavailable.

## Problem

The current click-through reaches `views.shipment.ui_shipment_detail_tabs`, but the first visible surface is a large edit form followed immediately by a finance projection. Operational identity, next action, factory lots, documents, deadlines, customer/agent context, and history are not presented as one coherent hierarchy. The read models already contain enough evidence for a bounded workspace projection, so the gap is primarily composition and presentation.

## Scope

- Add a pure read-only Shipment 360 workspace projection that reuses `build_shipment_dashboard_view` and the existing financial projection.
- Render an action-first Shipment 360 overview in `views/shipment_360.py` with identity, separate statuses, deadlines/free time, alerts, context, factory lots, documents, and evidence-backed timeline.
- Move the existing finance projection into the Finance area so operations lead the page.
- Keep the existing detail fields and safe writes available below the overview.
- Add focused projection tests and reusable Playwright coverage for Dashboard -> Shipment 360 -> close/back.
- Add truthful evidence and bounded design/plan artifacts.

## Non-Goals

- No new financial mutation, allocation, balance, FX conversion, ledger, or payment semantics.
- No A Bò historical opening publication or LOG-C06 reopening.
- No generic workflow engine, document management platform, customer/partner redesign, deployment, release, or AI.
- No change to the LOG-C07 Dashboard projection or navigation contract except what is required to consume the existing click-through.

## Requirements

1. The first Shipment 360 viewport identifies shipment, customer, owner, route/stage, next action, deadline/free-time state, and operational/financial statuses separately.
2. Next action is deterministic and sourced from existing dashboard alerts; missing data remains visible.
3. Multi-factory/factory-lot collections are shown when present and `UNKNOWN` when the source is absent.
4. Documents distinguish present, waiting/missing, and `UNKNOWN` registry state without claiming completeness that the data cannot prove.
5. Finance remains a read-only projection with source/reason and `UNKNOWN` semantics, and does not dominate the operational entry surface.
6. Timeline/history uses explicit shipment dates and existing audit rows only; no inferred history or chain-of-thought.
7. Dashboard -> open -> inspect -> close/back preserves the existing queue context and does not regress existing safe writes.
8. Desktop and narrow viewport degradation, visible focus, readable labels, and color-independent statuses are checked without claiming WCAG certification.

## Acceptance Criteria

- The real local Dashboard opens a shipment and renders the new Shipment 360 overview.
- A user can scan the first viewport and answer the twelve LOG-C08 product questions or see `UNKNOWN`/gap text where evidence is absent.
- Lục Giác-style multi-factory data renders as separate lots with missing fields surfaced.
- Finance remains canonical/read-only and all financial regression tests stay green.
- Existing save/payment/rename/delete paths remain in their prior locations and no new writer is introduced.
- Render evidence includes an initial critique and a corrected re-render where material defects are found.
- Focused tests, unittest discovery, compileall, and real runtime/Playwright evidence are recorded.
- Release status remains `NOT_RELEASED`; Docker or pytest gaps are explicit rather than hidden.

## Checklist

- [x] P0-A: Recover current product state, graph evidence, and protected boundaries.
  - Goal: establish the true LOG-C07 baseline before edits.
  - Work Steps: inspect prior LOG-C07 plan/evidence; inspect Shipment 360 source, view, tests, and dashboard click-through; refresh Anvien; run file-detail and impact for touched symbols; classify preserve-only and partial surfaces.
  - Implementation Gate: actual-status file records current classifications and exact evidence IDs.
  - Acceptance: P0 status is complete and downstream work is narrowed to the workspace projection and presentation.

### P1: Read-only workspace projection

- Phase Goal: create a deterministic projection for operational context without changing existing source-of-truth modules.
- Phase Boundary:
  - In scope: new `core/shipment_workspace.py`, focused projection tests, existing dashboard/360 read-model inputs.
  - Out of scope: Streamlit rendering, database writes, financial ledger, historical staging.
  - Dependencies: `core.shipment_dashboard.build_shipment_dashboard_view`, `core.shipment_360.build_shipment_360_summary`.
- Phase Implementation Rule: implement P1-A, verify and record evidence, refresh actual status, then implement P1-B.
- Ordered Slice List:
  - P1-A: deterministic workspace view for identity, action, context, documents, lots, and timeline
  - P1-B: focused Lục Giác/UNKNOWN/no-mutation tests

- [x] P1-A: deterministic workspace view
  - Goal: expose one read-only contract for the Shipment 360 work surface.
  - Scope Boundary:
    - Editable: new `core/shipment_workspace.py` only.
    - Inspect-only: `core/shipment_dashboard.py`, `core/shipment_360.py`.
    - Preserve-only: ledger, database, historical staging, existing writers.
    - Out of scope: UI markup and runtime navigation.
  - Non-Goals: do not add a second status taxonomy or infer missing dates/documents.
  - Pre-flight Questions:
    - Data source: shipment document plus existing dashboard and financial projections.
    - Display permission: same shipment visibility as the existing detail route.
    - DB read flow: no new DB read; caller supplies the already-loaded shipment and audit rows.
    - DB write flow: none.
    - Render location: consumed by `views/shipment_360.py`.
    - UI behavior flow: pure mapping from source -> workspace view.
    - Docker runtime: unavailable in baseline; record blocker.
    - Playwright target: N/A for pure projection; covered in P2.
    - Behavior test: direct fixture tests.
    - Cleanup/quarantine: in-memory fixtures only.
    - External side effects: none.
    - N/A notes: no permission or persistence changes.
  - Work Steps:
    1. Implement source-labelled identity/context/lots/documents/timeline helpers and deterministic next-action selection from the existing dashboard alerts.
       - UI flow check: projection fields map directly to visible overview sections planned for P2.
       - DB/data flow check: source object is not mutated and no writer is imported.
       - Render location check: contract is importable by the Shipment 360 renderer only.
       - Evidence target: source diff, import scan, projection test fixture.
    2. Add stable status/severity labels and explicit UNKNOWN reasons for absent factory, document, deadline, and history evidence.
       - UI flow check: every missing fact has a readable non-color state.
       - DB/data flow check: no zero/default substitution for missing source values.
       - Render location check: values are render-ready and do not require a second lookup.
       - Evidence target: focused tests and actual-status refresh.
  - Implementation Gate:
    - Existing projection file-detail/impact evidence is current; the new module remains read-only and does not import database or ledger writers.
  - Acceptance:
    - Source: projection returns stable keys for identity, next action, status, context, lots, documents, and timeline.
    - Runtime/UI: N/A until P2.
    - DB/data: source fixture is unchanged; no writer imports.
    - Behavior test: P1-B tests pass.
    - Cleanup/quarantine: no persistent fixture changes.
    - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-SAFE1`.
    - Actual-status rows refreshed: workspace projection.
  - Evidence Targets: source inspection, import/safety scan, focused tests.
  - Actual-status Update: transition workspace projection `missing -> correct` after tests pass.
  - Commit Boundary: shared worktree has pre-existing changes; do not create a mixed commit. Record exact changed files instead.

- [x] P1-B: focused projection tests
  - Goal: prove multi-factory, next-action, document, timeline, UNKNOWN, and no-mutation behavior.
  - Scope Boundary:
    - Editable: `tests/test_shipment_workspace.py`.
    - Inspect-only: new projection and existing read models.
    - Preserve-only: financial and historical tests.
    - Out of scope: browser rendering.
  - Non-Goals: no production data access.
  - Pre-flight Questions:
    - Data source: in-memory Lục Giác fixture adapted from `tests/test_shipment_dashboard.py`.
    - Display permission: N/A; pure contract.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: source fixture -> projection assertions.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: unittest/pytest-compatible focused file.
    - Cleanup/quarantine: in-memory only.
    - External side effects: none.
    - N/A notes: no external state.
  - Work Steps:
    1. Add tests for two complete lots plus one incomplete lot, deterministic deadline alert, inferred document rows, and explicit history rows.
       - UI flow check: assertions correspond to visible overview labels.
       - DB/data flow check: deep-copy equality proves no mutation.
       - Render location check: N/A.
       - Evidence target: focused test output.
    2. Add tests for missing collections/documents and a finance view with UNKNOWN; run focused and related financial/dashboard tests.
       - UI flow check: UNKNOWN is asserted rather than a guessed zero/complete state.
       - DB/data flow check: no ledger input is changed.
       - Render location check: N/A.
       - Evidence target: test output and regression ledger.
  - Implementation Gate: P1-A source contract exists and actual-status row is refreshed.
  - Acceptance:
    - Source: tests cover the contract and protected boundaries.
    - Runtime/UI: N/A.
    - DB/data: no persistent state touched.
    - Behavior test: focused tests pass.
    - Cleanup/quarantine: no cleanup required beyond process temp state.
    - Evidence IDs: `E1-P1B-TEST1`, `E1-P1B-SAFE1`.
    - Actual-status rows refreshed: test coverage.
  - Evidence Targets: focused test output and source review.
  - Actual-status Update: mark projection and test coverage correct.
  - Commit Boundary: no isolated commit in the shared dirty worktree; record status.

### P2: Shipment 360 operational work surface

- Phase Goal: make the real Shipment 360 page answer daily operational questions before exposing the existing edit/finance detail.
- Phase Boundary:
  - In scope: `views/shipment_360.py`, bounded call-site changes in `views/shipment.py`, existing audit read.
  - Out of scope: core ledger, dashboard projection, route permissions, new writes.
  - Dependencies: P1 projection contract and existing Shipment 360 finance projection.
- Phase Implementation Rule: implement P2-A, render/critique, refresh actual status, then P2-B.
- Ordered Slice List:
  - P2-A: action-first overview and context render
  - P2-B: finance demotion, history integration, and navigation continuity

- [x] P2-A: action-first overview and context render
  - Goal: render a dense but scannable operational overview with next action, statuses, context, lots, documents, and deadlines.
  - Scope Boundary:
    - Editable: `views/shipment_360.py`, import/call site in `views/shipment.py`.
    - Inspect-only: existing save/payment controls.
    - Preserve-only: financial projection math and core modules.
    - Out of scope: new mutations.
  - Non-Goals: no card collage, no generic design-system promotion.
  - Pre-flight Questions:
    - Data source: `build_shipment_workspace_view` and existing `shipment_360` summary.
    - Display permission: existing detail route permission.
    - DB read flow: existing shipment plus already-loaded related caches.
    - DB write flow: none.
    - Render location: first body of `ui_shipment_detail_tabs`.
    - UI behavior flow: Dashboard row -> overview -> expand context/lots/docs/history -> existing detail controls.
    - Docker runtime: baseline has no Docker target; record as blocked if unchanged.
    - Playwright target: local app for visible evidence, with limitation recorded.
    - Behavior test: existing dashboard 360 flow plus new assertions.
    - Cleanup/quarantine: screenshots/reports under repo QA paths; debug only under `.tmp/log-c08`.
    - External side effects: none.
    - N/A notes: no new DB write.
  - Work Steps:
    1. Render identity/status/deadline/action band with semantic text, visible focus-compatible controls, and responsive CSS matching LOG-C07 tokens.
       - UI flow check: first viewport answers shipment/customer/stage/owner/next-action/deadline.
       - DB/data flow check: renderer consumes projection only.
       - Render location check: overview appears before edit tabs.
       - Evidence target: screenshot and critique.
    2. Add progressive disclosure for customer/factory/agent context, multi-factory rows, documents, and explicit gaps.
       - UI flow check: dense data remains scannable and narrow viewport degrades without hiding the next action.
       - DB/data flow check: no master-data duplication or new writes.
       - Render location check: expanders/tables are below the primary action band.
       - Evidence target: screenshot/DOM and focused runtime checks.
  - Implementation Gate: P1 projection tests pass; Anvien impact/file-detail is refreshed for renderer and call site.
  - Acceptance:
    - Source: overview renderer has no writer calls.
    - Runtime/UI: real Dashboard -> Shipment 360 shows action-first overview and context.
    - DB/data: financial and shipment snapshots unchanged by read-only render.
    - Behavior test: flow opens a known shipment and returns to queue.
    - Cleanup/quarantine: official evidence is in `reports/QA/playwright/`; temp images are debug-only.
    - Evidence IDs: `E2-P2A-RENDER1`, `E2-P2A-CRITIQUE1`, `E2-P2A-SAFE1`.
    - Actual-status rows refreshed: overview/context render.
  - Evidence Targets: real screenshot, source review, runtime action ledger.
  - Actual-status Update: transition Shipment 360 presentation `wrong/partial -> partial` pending P2-B.
  - Commit Boundary: no mixed commit due pre-existing dirty worktree.

- [x] P2-B: finance demotion, history, and return continuity
  - Goal: keep finance trustworthy but subordinate to operations, integrate audit timeline, and preserve close/back context.
  - Scope Boundary:
    - Editable: call order in `views/shipment.py`, finance renderer placement in `views/shipment_360.py`, reusable Playwright flow/report.
    - Inspect-only: canonical finance/read-model code and existing safe writer calls.
    - Preserve-only: A Bò historical state and dashboard filters.
    - Out of scope: new financial actions.
  - Non-Goals: no financial truth change and no historical cutover.
  - Pre-flight Questions:
    - Data source: existing `shipment_360` summary and `load_audit_logs`.
    - Display permission: existing detail route.
    - DB read flow: one existing audit read; no new repositories.
    - DB write flow: none.
    - Render location: finance tab and timeline expander.
    - UI behavior flow: inspect operations -> open finance -> close/back -> queue filter remains.
    - Docker runtime: record unavailable if no Docker target.
    - Playwright target: reusable `playwright/log_c08_shipment_360_flow.cjs`.
    - Behavior test: dashboard financial write oracle, shipment 360 tests, historical safety tests.
    - Cleanup/quarantine: no real business data mutation.
    - External side effects: none.
    - N/A notes: no release/deploy.
  - Work Steps:
    1. Move the finance projection below the operational overview and ensure its source/reason/UNKNOWN disclosure remains intact.
       - UI flow check: operations remain primary while finance is reachable and legible.
       - DB/data flow check: no duplicate balance or FX conversion.
       - Render location check: finance projection is in Finance scope, not page entry.
       - Evidence target: source diff and rendered screenshot.
    2. Reuse audit rows in the timeline, add Dashboard -> Shipment 360 -> close/back assertions, and run critique corrections.
       - UI flow check: user can return to the same operational queue context without a dead end.
       - DB/data flow check: audit is read-only; safe write controls remain count/behavior stable.
       - Render location check: timeline shows explicit events and UNKNOWN/gap when absent.
       - Evidence target: Playwright JSON/MD, screenshots, regression test output.
  - Implementation Gate: P2-A render is inspected and material defects are recorded before corrections.
  - Acceptance:
    - Source: finance/history changes remain presentation/read-only.
    - Runtime/UI: full journey works and critique defects are corrected.
    - DB/data: financial snapshot and historical status are unchanged.
    - Behavior test: focused and related regression suites pass.
    - Cleanup/quarantine: reports and screenshots are stored under approved paths.
    - Evidence IDs: `E2-P2B-REG1`, `E2-P2B-RENDER2`, `E2-P2B-SAFE1`.
    - Actual-status rows refreshed: full Shipment 360 workspace.
  - Evidence Targets: Playwright report, screenshots, test output, detect-changes.
  - Actual-status Update: mark bounded workspace correct or record concrete blocker.
  - Commit Boundary: shared worktree prevents a clean implementation commit; report exact worktree state.

### Pn: closure and supervisor review

- [x] Pn-A: Supervisor review of completed LOG-C08 scope.
  - Goal: independently verify source, runtime, evidence, financial safety, and history boundary.
  - Work Steps: inspect changed production files; inspect reports/screenshots; run current validation; write supervisor report; repair only if user-authorized implementation loop requires it.
  - Implementation Gate: P1/P2 slices completed or explicitly blocked.
  - Acceptance: supervisor PASS for bounded local scope or a documented REJECT/blocker.

- [x] Pn-B: remove dead work created by this plan.
  - Goal: keep only useful source, tests, reports, and plan artifacts.
  - Work Steps: review diff/status; remove only plan-created obsolete artifacts; re-run source/status checks.
  - Implementation Gate: supervisor review has identified no required active artifact.
  - Acceptance: no dead plan-created helper or stale evidence remains.

- [x] Pn-C: close evidence and report.
  - Goal: record final validation, benchmark, detect-changes, worktree state, and release status.
  - Work Steps: run compileall/unittest/focused tests; run real local render; run Playwright; run detect-changes; update all ledgers and final report.
  - Implementation Gate: Pn-A/Pn-B pass or blockers are explicit.
  - Acceptance: final report follows LOG-C08 requested headings, says `NOT_RELEASED`, and states whether owner action is needed.

## Risk Notes

- `views/shipment.py` is a large high-risk file in a shared dirty worktree; keep edits at the existing projection/render call site and do not reformat the file.
- Anvien currently reports many unresolved analyzer gaps; preserve the measured high file risk and use source/runtime/tests together.
- Docker is not present in the recovered LOG-C07 evidence; Playwright against the local Streamlit runtime is useful product evidence but cannot be called container/full-build evidence.
- Pytest may be unavailable; use unittest-compatible tests and record the limitation.
- The existing source text has encoding artifacts in some terminals; avoid broad text rewrites and verify actual rendered Vietnamese copy in the browser.
