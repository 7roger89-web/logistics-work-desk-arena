# LOG-C09 Entity Context Workspaces Plan

## Metadata

- Date: `2026-08-16`
- Status: `complete`
- Plan: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-actual-status.md`

## Goal

Complete LOG-C09 as a read-first context layer around the existing Shipment 360: Customer 360, Factory/Supplier 360, and generic Partner/Agent 360, with truthful UNKNOWN states, master-vs-shipment separation, relevant shipment cross-navigation, and no new financial or document-management architecture.

## Rules

- Complete P0 actual status before implementation work.
- Preserve LOG-C02 through LOG-C08, including the A Bò historical boundary and canonical financial ledger.
- Keep projections read-only; reuse existing shipment/customer data and writers only where already present.
- Do not add CRUD, financial mutation, historical opening publication, deployment, or P2P development.
- Update each checklist item immediately when it is completed.
- Record evidence and benchmarkable counts as work completes.
- Run Anvien impact/file-detail before editing code and detect-changes before implementation commits.
- Validate the real Streamlit runtime with reusable Playwright evidence; Docker remains an explicit environment gate if unavailable.

## Problem

Shipment 360 currently exposes supplier/agent text and factory lots as context, but Support and Sales cannot open a focused entity workspace, inspect related shipments, distinguish master identity from shipment/lot facts, or return to the originating shipment without dead ends. The existing Customer CRUD and A Bò finance surfaces do not satisfy a generic context workflow.

## Scope

- Add pure read-only projections for customer, factory/supplier, and partner/agent context.
- Add one context workspace route with Customer / Factory-Supplier / Partner-Agent modes.
- Add Shipment 360 entity entry points and context workspace shipment links.
- Show document state only from currently supported evidence and keep UNKNOWN visible.
- Keep canonical financial information as source-labelled per-shipment projection only.
- Add focused behavior tests and real local render evidence for all four required journeys.

## Non-Goals

- Full customer/factory/partner CRUD or master-data administration.
- Full document management or document review.
- Finance review, new balance/debt calculations, FX conversion, or ledger mutation.
- Sales/quotation redesign, contract lifecycle, CEO reporting, AI, deployment, or release.
- Reopening LOG-C06 or publishing A Bò historical opening.

## Requirements

- Customer context: identity/contact, important requirements, delivery expectations, active/attention/history shipments, existing commercial context, and missing data.
- Factory/Supplier context: multi-factory/job-lot rows with quantity/weight/CBM, ready date, readiness, pickup context, missing data, and next coordination need; never infer from free text.
- Partner/Agent context: generic identity/contact, role by shipment, related shipments, operational context, evidence/documents, and canonical financial projection where present; never make it an A Bò page.
- Master entity fields and shipment/lot-specific fields are visibly separated and never overwrite one another.
- Entity workspace and Shipment 360 provide working links in both directions.
- No new write path is introduced by the context layer.

## Acceptance Criteria

1. Customer context is useful from a shipment workflow.
2. Factory/Supplier context supports multiple factories/lots and truthful UNKNOWN values.
3. Partner/Agent context is generic and preserves A Bò as a separate historical/finance surface.
4. Master vs shipment facts are explicitly separated.
5. Cross-navigation works in both directions without dead ends.
6. Documents and missing data are evidence-labelled and UNKNOWN remains visible.
7. Financial projections remain canonical/read-safe and do not dominate Partner 360.
8. LOG-C07 Dashboard and LOG-C08 Shipment 360 regressions pass.
9. Real local render evidence covers Shipment -> Customer, Factory, Partner, and Entity -> Shipment 360.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real LOG-C09 baseline and protect prior slices.
  - Work Steps: recover request, inspect current projections/routes/renderers/tests, refresh Anvien graph, classify each target, and update downstream slices from evidence.
  - Implementation Gate: actual-status has evidence-backed classifications and no code edit starts before the P0 decision.
  - Acceptance: all entity surfaces, protected financial/history surfaces, runtime limitations, and touch modes are recorded.

### P1: Read-only context projections

- Phase Goal: create deterministic entity context data without new persistence or writers.
- Phase Boundary:
  - In scope: `core/entity_context.py` and focused projection tests.
  - Out of scope: Streamlit rendering, navigation mutation, CRUD, finance ledger changes.
  - Dependencies: existing shipment dashboard/workspace and session-loaded shipments/customers.
- Phase Implementation Rule: implement and verify P1-A, refresh actual-status, then implement P1-B.

- [x] P1-A: Build customer, factory/supplier, and partner/agent context projections.
  - Goal: provide one stable read model that preserves master and shipment/lot boundaries.
  - Scope Boundary:
    - Editable: new pure projection module only.
    - Inspect-only: `core/shipment_dashboard.py`, `core/shipment_workspace.py`, `core/shipment_360.py`, database loaders.
    - Preserve-only: financial ledger, A Bò historical state, existing writers.
    - Out of scope: writes, inferred entity records, cross-tenant discovery.
  - Non-Goals: no CRUD and no aggregate financial balance.
  - Pre-flight Questions:
    - Data source: loaded customer master plus shipment documents and existing read models.
    - Display permission: consumer route uses existing dashboard permission.
    - DB read flow: N/A in projection; caller passes already-loaded mappings.
    - DB write flow: none.
    - Render location: consumed by the context workspace and Shipment 360 links.
    - UI behavior flow: entity selection -> projection -> workspace.
    - Docker runtime: check and record availability; do not substitute it silently.
    - Playwright target: N/A for pure projection; focused unittest is required.
    - Behavior test: pure in-memory fixtures for all entity types and UNKNOWN.
    - Cleanup/quarantine: no persistent writes.
    - External side effects: none.
    - N/A notes: permissions are existing app permissions; no new role is added.
  - Work Steps:
    1. Add stable helpers for entity identity, related shipment rows, factory lots, partner roles, document context, and missing-data labels.
       - UI flow check: N/A; projection contract is consumed by the renderer.
       - DB/data flow check: input mappings are not mutated and finance is not recomputed.
       - Render location check: output includes explicit `master` and `shipment`/`lot` groups.
       - Evidence target: source review and focused tests.
    2. Add customer/factory/partner builders and preserve UNKNOWN when source fields are absent.
       - UI flow check: N/A; all display states are renderable by the later workspace.
       - DB/data flow check: no new writer/import of database or ledger modules.
       - Render location check: each entity includes related shipment IDs for navigation.
       - Evidence target: focused behavior tests and Anvien impact evidence.
  - Implementation Gate: Anvien file-detail and impact evidence exists for touched projection dependencies; P0 status is complete.
  - Acceptance:
    - Source: projection is pure and read-only.
    - Runtime/UI: N/A until P2.
    - DB/data: input fixtures remain unchanged; no persistence call exists.
    - Behavior test: customer, multi-factory, generic partner, and UNKNOWN cases pass.
    - Cleanup/quarantine: no persistent test artifacts.
    - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-TEST1`, `E1-P1A-SAFE1`.
    - Actual-status rows refreshed: projection surfaces.
  - Evidence Targets: source, graph impact, unittest output.
  - Actual-status Update: transition context projections `missing -> correct` for the pure contract.
  - Commit Boundary: checkpoint after slice verification when worktree policy permits.

- [x] P1-B: Lock projection behavior with focused tests.
  - Goal: prove trigger -> projection -> observable entity rows and boundary safety.
  - Scope Boundary:
    - Editable: `tests/test_entity_context.py` only.
    - Inspect-only: projection source and existing C07/C08 tests.
    - Preserve-only: all existing regression tests.
    - Out of scope: UI selectors and browser reports.
  - Non-Goals: no static-only assertions without observable output.
  - Pre-flight Questions:
    - Data source: in-memory fixtures.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: none.
    - Render location: projection dictionaries.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A; this slice is pure data behavior.
    - Behavior test: unittest trigger -> builder -> rows/statuses.
    - Cleanup/quarantine: no persistent state.
    - External side effects: none.
    - N/A notes: full app runtime is P2/P3.
  - Work Steps:
    1. Add fixtures covering two factories, two customers/related shipments, and two partners with different roles.
       - UI flow check: N/A.
       - DB/data flow check: deep-copy input and assert unchanged.
       - Render location check: assert master vs shipment fields remain separate.
       - Evidence target: unittest output.
    2. Run focused and regression tests, then refresh actual-status before UI work.
       - UI flow check: N/A.
       - DB/data flow check: financial projection remains untouched.
       - Render location check: all required statuses are explicit.
       - Evidence target: test output and status refresh.
  - Implementation Gate: P1-A source and safety evidence pass.
  - Acceptance:
    - Source: tests exercise public builder outputs.
    - Runtime/UI: N/A.
    - DB/data: immutability and no financial aggregation are proven.
    - Behavior test: focused suite passes.
    - Cleanup/quarantine: no persistent writes.
    - Evidence IDs: `E1-P1B-TEST1`, `E1-P1B-SAFE1`.
    - Actual-status rows refreshed: projection behavior.
  - Evidence Targets: tests and command output.
  - Actual-status Update: mark projection contract behavior-bound-correct.
  - Commit Boundary: checkpoint after focused tests pass.

### P2: Context workspace and entity navigation

- Phase Goal: render a dense read-only context workspace and wire it into the existing app without a dead end.
- Phase Boundary:
  - In scope: `views/entity_context.py`, `views/web_app.py`, `views/shipment_360.py`, `views/shipment.py`, session-state navigation.
  - Out of scope: existing Customer CRUD internals, partner reconciliation internals, financial ledger, A Bò route.
  - Dependencies: P1 projection contract and existing C08 Shipment 360 renderer.
- [x] P2-A: Add the generic entity workspace route.
  - Goal: support Customer / Factory-Supplier / Partner-Agent modes with compact sections and explicit empty states.
  - Scope Boundary:
    - Editable: new renderer and route registration only.
    - Inspect-only: existing CRUD/finance routes.
    - Preserve-only: A Bò route and current sidebar group semantics.
    - Out of scope: new master-data editors.
  - Non-Goals: no catalog redesign.
  - Pre-flight Questions:
    - Data source: session-loaded `db_shipments` and `db_customers`.
    - Display permission: `dashboard`.
    - DB read flow: session cache only; existing refresh populates it.
    - DB write flow: none.
    - Render location: `Entity Context` route.
    - UI behavior flow: choose context -> inspect sections -> open relevant shipment.
    - Docker runtime: record unavailable if missing.
    - Playwright target: route from direct session navigation after P2-B.
    - Behavior test: mounted AppTest or browser flow.
    - Cleanup/quarantine: no writes.
    - External side effects: none.
    - N/A notes: no new route-level persistence.
  - Work Steps:
    1. Render identity/master fields separately from shipment/lot-specific rows, with missing/UNKNOWN labels and finance subordinate.
       - UI flow check: compact tables/expanders remain scannable and entity type is obvious.
       - DB/data flow check: renderer consumes projection only.
       - Render location check: route is reachable from existing app navigation.
       - Evidence target: mounted render and screenshot.
    2. Add explicit back/context controls and relevant shipment buttons.
       - UI flow check: entity workspace opens Shipment 360 without dead end.
       - DB/data flow check: active shipment is session navigation only.
       - Render location check: button labels identify the target shipment.
       - Evidence target: Playwright action ledger.
  - Implementation Gate: P1 tests pass and Anvien impact is refreshed for route/render files.
  - Acceptance:
    - Source: no writer calls in the context renderer.
    - Runtime/UI: each mode renders identity, related shipments, gaps, and next action.
    - DB/data: no state is persisted by navigation.
    - Behavior test: direct route and return controls work.
    - Cleanup/quarantine: QA artifacts use approved paths.
    - Evidence IDs: `E2-P2A-SRC1`, `E2-P2A-RENDER1`.
    - Actual-status rows refreshed: entity workspace route.
  - Evidence Targets: source inspection, runtime render, screenshot.
  - Actual-status Update: context workspace `missing -> partial` pending cross-links.
  - Commit Boundary: checkpoint after route render is verified.

- [x] P2-B: Wire Shipment 360 to entity workspaces and back.
  - Goal: make Customer, Factory/Supplier, and Partner/Agent entry points actionable from the shipment workflow.
  - Scope Boundary:
    - Editable: `views/shipment_360.py` and narrow call-site/session wiring.
    - Inspect-only: financial summary and existing edit controls.
    - Preserve-only: C08 layout/design language and writers.
    - Out of scope: changing shipment data when opening context.
  - Non-Goals: no entity editing.
  - Pre-flight Questions:
    - Data source: current workspace view plus all loaded shipments/customers.
    - Display permission: existing dashboard route.
    - DB read flow: session cache.
    - DB write flow: none.
    - Render location: context section of Shipment 360.
    - UI behavior flow: click entity -> route -> click shipment -> Shipment 360.
    - Docker runtime: record availability.
    - Playwright target: reusable LOG-C09 flow.
    - Behavior test: browser action ledger plus regression.
    - Cleanup/quarantine: screenshots/reports only under `reports/QA/playwright/`.
    - External side effects: none.
    - N/A notes: entity master selection is derived from current in-memory data.
  - Work Steps:
    1. Add entity entry buttons using stable state payloads and preserve the source shipment ID.
       - UI flow check: each button has an explicit entity type and target.
       - DB/data flow check: no mutation or recalculation.
       - Render location check: buttons sit beside context facts, not inside finance.
       - Evidence target: browser action ledger.
    2. Add Entity -> Shipment 360 return/open behavior and handle missing entities visibly.
       - UI flow check: no dead-end and previous shipment remains reachable.
       - DB/data flow check: active page/shipment state only.
       - Render location check: entity workspace row opens the existing C08 surface.
       - Evidence target: Playwright checks and screenshot.
  - Implementation Gate: P2-A route is renderable and C08 regression remains green.
  - Acceptance:
    - Source: cross-links do not import writers or finance mutation.
    - Runtime/UI: all four required flows pass.
    - DB/data: state is unchanged after navigation.
    - Behavior test: Playwright flow passes.
    - Cleanup/quarantine: reusable script and JSON/MD evidence are present.
    - Evidence IDs: `E2-P2B-NAV1`, `E2-P2B-RENDER1`, `E2-P2B-SAFE1`.
    - Actual-status rows refreshed: cross-navigation.
  - Evidence Targets: runtime screenshots, DOM/action ledger, source review.
  - Actual-status Update: cross-navigation `missing -> correct` if all paths pass.
  - Commit Boundary: checkpoint after browser flow pass.

### P3: Real render, critique, correction, and regression

- Phase Goal: inspect the real local app, correct only material LOG-C09 issues, and prove LOG-C07/C08 are preserved.
- Phase Boundary:
  - In scope: reusable Playwright flow/report, screenshots, focused/full tests, final ledgers.
  - Out of scope: Docker deployment, release, production, and new feature expansion.
- [x] P3-A: Run four journeys, critique, re-render, and regression.
  - Goal: prove the user-visible flows and correct duplicate context, poor scanability, mixed master/shipment facts, hidden UNKNOWN, or finance dominance.
  - Scope Boundary:
    - Editable: Playwright evidence and material UI corrections only.
    - Inspect-only: prior C07/C08 reports for regression targets.
    - Preserve-only: all protected finance/history boundaries.
    - Out of scope: deferred accessibility certification and deploy.
  - Non-Goals: no cosmetic rewrite after the material issues are closed.
  - Pre-flight Questions:
    - Data source: real local Streamlit runtime.
    - Display permission: local admin/default runtime.
    - DB read flow: current runtime source mode recorded.
    - DB write flow: none attempted.
    - Render location: Dashboard, Shipment 360, Entity Context.
    - UI behavior flow: four required flows plus C07/C08 regression.
    - Docker runtime: build/run checked and limitation recorded.
    - Playwright target: `playwright/log_c09_entity_context_flow.cjs`.
    - Behavior test: full unittest and reusable browser script.
    - Cleanup/quarantine: official JSON/MD/screenshots in `reports/QA/playwright/`; debug only in `.tmp/`.
    - External side effects: none.
    - N/A notes: no release approval requested.
  - Work Steps:
    1. Run the real runtime and capture all four journeys plus screenshots.
       - UI flow check: action ledger records expected and actual states.
       - DB/data flow check: no writes are attempted.
       - Render location check: entity facts are in the correct workspace sections.
       - Evidence target: JSON/MD/screenshot.
    2. Critique and correct material defects, then re-render and run full regression.
       - UI flow check: navigation and scanability remain intact after correction.
       - DB/data flow check: C08 finance and history remain unchanged.
       - Render location check: UNKNOWN and finance explanations remain visible.
       - Evidence target: final browser report, tests, detect-changes.
  - Implementation Gate: P2 slices are complete and the real app is running.
  - Acceptance:
    - Source: final diff is scoped to LOG-C09.
    - Runtime/UI: all declared journeys pass after correction.
    - DB/data: full regression passes and no new writer exists.
    - Behavior test: focused and full suites pass where environment supports them.
    - Cleanup/quarantine: approved evidence paths only.
    - Evidence IDs: `E3-P3A-RENDER1`, `E3-P3A-CRITIQUE1`, `E3-P3A-REG1`.
    - Actual-status rows refreshed: complete LOG-C09 scope.
  - Evidence Targets: browser report, screenshot, test output, detect-changes.
  - Actual-status Update: mark bounded local product state PASS or record blocker.
  - Commit Boundary: final implementation checkpoint before supervisor review.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review source, runtime, evidence, and protected boundaries.
  - Work Steps: inspect changed files and reports, run current validation, write the supervisor report, and fix only if the user-authorized implementation loop requires it.
  - Implementation Gate: P1-P3 are complete or explicitly blocked.
  - Acceptance: supervisor records PASS or a concrete blocker.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: leave only useful LOG-C09 artifacts.
  - Work Steps: review plan-created files, remove obsolete debug output only, and verify status/evidence.
  - Implementation Gate: supervisor findings are known.
  - Acceptance: no dead plan-created artifact remains.
- [x] Pn-C: Close the plan.
  - Goal: record final validation, benchmark, detect-changes, worktree state, and NOT_RELEASED status.
  - Work Steps: update all four ledgers, run required commands, record limitations, and stop at bounded terminal state.
  - Implementation Gate: supervisor PASS or explicit blocker.
  - Acceptance: final report follows the owner-requested headings and no deploy/release occurs.

## Risk Notes

- The shared worktree is materially dirty; preserve prior LOG-C02 through LOG-C08 changes and do not reset unrelated files.
- `views/shipment.py` and `views/shipment_360.py` are high-risk hotspots; keep changes narrow and presentation/read-navigation only.
- Entity records are derived from existing loaded data because no approved factory/partner master store is present; label shipment/lot facts as such rather than inventing master data.
- Docker and pytest may be unavailable; record evidence honestly and do not claim release readiness from local-only evidence.
- Existing source contains encoding artifacts in some terminal views; avoid broad rewrites and use stable visible labels/selectors for new flows.
