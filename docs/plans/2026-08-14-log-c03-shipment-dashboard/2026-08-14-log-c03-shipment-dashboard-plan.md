# LOG-C03 Shipment Dashboard 2.0 Plan

## Metadata

- Date: `2026-08-14`
- Status: `P3 Complete / formal closure BLOCKED`
- Plan: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-actual-status.md`

## Goal

Make the existing Streamlit home screen a shipment-first support work desk. A support user must see actionable shipments, separate operational and read-only financial status, deterministic date/data warnings, a compact attention summary, useful filters including SALE Thanh, and a reliable one-click path into the existing Shipment 360/detail surface.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- For app/runtime validation, full build must include Docker image/container build. If Docker is missing or not run, full build is incomplete and the final result cannot claim Docker-backed acceptance.
- Any Playwright validation must target the real built Docker/container runtime. If the repository has no Docker target or Docker cannot be built/started, record the genuine blocker and classify local Streamlit evidence as supporting evidence only.
- Playwright evidence must record the runtime command, exposed URL, Playwright command, screenshot/trace/result, and any host capability blocker.
- Keep the standard planner structure. These detail rules make each slice concrete and independently verifiable.
- Every implementation phase is decomposed into narrow slices. Work starts from a slice ID, not a broad phase.
- Hidden fallback is forbidden. Missing business data must be visible as `CẦN BỔ SUNG`, `UNKNOWN`, or an equivalent truthful state.
- Dashboard navigation and projection reads must not call financial write APIs. Existing writes inside the existing Shipment detail/Finance surface remain preserve-only and out of this slice.
- Do not add AI, a workflow engine, a new database, a new frontend stack, or LOG-C04 reconciliation behavior.

## Problem

The current main dashboard is a legacy customer-group view with task and analytics sections ahead of the shipment work queue. It has a free-time badge using local UI math, a compact debt badge using the legacy financial calculator, and a working detail transition, but it lacks a single bounded read model for operational attention, customer deadlines, missing data, separate financial status, owner/customer/attention filters, and a deterministic next action. The current project is also dirty with LOG-C01/LOG-C02 work and unrelated user changes, so the slice must preserve those changes and avoid broad staging.

## Scope

- Inspect and reuse current shipment schema, status vocabulary, customer linkage, ETA/free-time, delivery fields, Shipment 360 projection, navigation/session state, current Streamlit styles, tests, and Playwright harness.
- Add a pure, non-mutating dashboard projection/rule module using existing shipment fields and the existing Shipment 360 financial read model.
- Add deterministic rules for free-time warning/overdue, customer required-date warning/at-risk, explicit promised/next-action dates when present, missing critical data, compact financial attention, and evidence-backed next attention.
- Render a shipment-first dashboard work queue with a compact `HÔM NAY CẦN CHÚ Ý` summary, separate operational/financial signals, bounded cards/rows, and compact filters.
- Support safe synthetic Golden Lục Giác fixture tests only; no real data mutation.
- Preserve the existing Shipment 360/detail renderer and navigation state, including first click, close/back, and second shipment flows.
- Add unit tests and a reusable Playwright flow/report for the bounded behavior.

## Non-Goals

- No AI, LLM, Gemini/OpenAI/Claude integration, AI classification, or AI next action.
- No A Bò reconciliation desk, ledger write, allocation write, debit generator, Quick Entry, payment write, or LOG-C04 work.
- No full Factory Lot domain, project scheduling/CPM/SLA engine, task graph, capacity planning, auto-assignment, GPS, portal, React/Next rewrite, new DB, Redis, Elasticsearch, RabbitMQ, GraphQL, or microservices.
- No redesign of the existing Shipment 360 financial view or existing finance/detail write controls.
- No mutation of production Lục Giác or other real financial data for tests.
- No reset/checkout/broad cleanup of the dirty worktree.

## Requirements

1. Dashboard is shipment-first and answers which shipment needs attention without opening every shipment.
2. Operational status and financial status are independent display fields.
3. Financial status is read-only from `build_shipment_360_summary`/existing financial projection; dashboard does not duplicate ledger balance math or call financial write APIs.
4. Free-time days remaining are derived from existing `data.2.6.arrival_date` + `free_time`; warning is `<= 2` days and critical is expired, using the current date convention and a testable `today` parameter.
5. Customer required-date and planned/ETA comparisons are deterministic and visible when supported by existing/fixture fields; absent fields stay truthful.
6. Missing critical information is bounded to explicit supported fields, at minimum customer and the relevant active-shipment milestone/date signals; no universal checklist is invented.
7. Next attention is ranked critical/overdue, missing prerequisite, financial review, deadline soon, then normal pending evidence; no fake action when no evidence exists.
8. Filters include all, mine/SALE Thanh, owner, customer/search, operational status, financial status, has alert, and deadline soon where data supports them.
9. Dashboard open -> Shipment 360/detail -> close/back -> second shipment works without losing shipment identity or filter state.
10. No AI and no new financial write path.

## Acceptance Criteria

- The main dashboard renders a shipment-first work queue and top attention summary.
- Operational and financial status are visibly separate on each row/card.
- Unit fixtures cover normal, free-time warning/critical, customer deadline warning/at-risk, operational complete + financial open, operational active + financial settled, UNKNOWN/review finance, missing data, Golden Lục Giác, SALE Thanh, financial/alert filters, and no-mutation safety.
- The existing browser runtime can open the dashboard and the first and second shipment reliably; screenshots and machine-readable evidence are captured.
- `pytest`/unittest, `compileall`, Streamlit health, and existing LOG-C02 finance/payment regressions are checked.
- Docker-backed full-build/browser acceptance is either PASS with evidence or explicitly BLOCKED by the host/repository capability; no dev-server evidence is mislabeled as Docker acceptance.
- Real data is not mutated for fixture/testing.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state and protect the dirty worktree boundary.
  - Work Steps: inspect Git status, current dashboard/detail/router/source-of-truth paths, prior LOG-C01/LOG-C02 evidence, Anvien graph/impact, existing tests, and browser tooling; classify each surface and write the current-status matrix.
  - Implementation Gate: no product code editing starts until the actual-status file has the baseline rows, evidence IDs, touch modes, and a final P0 decision.
  - Acceptance: current dashboard is classified partial/wrong for LOG-C03, existing Shipment 360/detail and one-click navigation are classified preserve/partial, ledger/database are preserve-only, and Docker/P2P blockers are recorded.

### P1: Projection and deterministic rules

- Phase Goal: create the single pure read model that turns existing shipment data plus the existing financial projection into compact dashboard signals without persistence side effects.
- Phase Boundary:
  - In scope: `core/shipment_dashboard.py` and its direct unit-test contract.
  - Out of scope: Streamlit layout, database schema, financial ledger changes, and detail-page writes.
  - Dependencies: P0 actual status; existing `core.utils` date parsing, `core.config` status vocabulary, and `core.shipment_360` read model.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: Add dashboard read model and rule functions.
  - P1-B: Add focused behavior fixtures/tests and no-write proof.

- [x] P1-A: Add dashboard read model and deterministic rule functions.
  - Goal: expose a stable `build_shipment_dashboard_view` plus filtering/sorting helpers that derive all card fields and alert signals from existing data.
  - Scope Boundary:
    - Editable: new `core/shipment_dashboard.py` only.
    - Inspect-only: `core/shipment_360.py`, `core/logic.py`, `core/utils.py`, `core/config.py`, `core/financial_ledger.py`.
    - Preserve-only: all existing DB and financial write functions.
    - Out of scope: UI rendering and production fixture insertion.
  - Non-Goals: no persisted `days_remaining`, no duplicate receivable/debt math, no AI, no task graph, no new taxonomy beyond mapping current `wait/pending/done/cancel`.
  - Pre-flight Questions:
    - Data source: shipment mapping plus `build_shipment_360_summary` read model.
    - Display permission: caller's existing dashboard permission; projection itself is permission-neutral.
    - DB read flow: caller supplies current shipment documents; no DB call in pure helpers.
    - DB write flow: none; prove the module has no write imports/calls.
    - Render location: later `views/dashboard.py` shipment queue.
    - UI behavior flow: none in this slice; pure model only.
    - Docker runtime: N/A for pure module; final runtime gate remains pending.
    - Playwright target: N/A; use unit behavior evidence.
    - Behavior test: next slice `tests/test_shipment_dashboard.py`.
    - Cleanup/quarantine: no persistent fixture; all data is in-memory.
    - External side effects: none.
    - N/A notes: no factory-lot persistence exists in current schema; expose bounded factory/missing-data counts only when explicit fixture fields exist.
  - Work Steps:
    1. Implement date/owner/status extraction, free-time expiry and customer deadline rule helpers with injectable `today`.
       - UI flow check: N/A; return render-ready labels/severity only.
       - DB/data flow check: read nested `data.2.6`, `data.2.7`, `data.0.0`, and supported explicit aliases without mutation.
       - Render location check: define stable fields for status, deadline, warning list, next attention, and financial projection.
       - Mini QA for each completed implementation slice (MUST): run `python -m py_compile core/shipment_dashboard.py` and direct fixture probes.
       - Evidence target: `E1-P1A-RULE1..E1-P1A-RULE3`.
    2. Implement `build_dashboard_summary`/`filter_dashboard_views`/attention ranking with stable severity ordering and truthful empty/unknown states.
       - UI flow check: N/A; verify no fake next action is generated.
       - DB/data flow check: call only the existing read-only financial projection; never call `save_*`, `allocate_*`, `reverse_*`, payment, or link write functions.
       - Render location check: ensure all later UI fields are bounded to the shipment row/card contract.
       - Mini QA for each completed implementation slice (MUST): compile and run a read-only counter/probe over synthetic mappings.
       - Evidence target: `E1-P1A-PROJ1..E1-P1A-PROJ3`.
  - Implementation Gate:
    - Before editing the new module, Anvien file-detail/impact evidence for `core/shipment_360.py`, `core/utils.py`, and `core/config.py` is recorded; no existing high-risk ledger file is edited.
    - P0 is complete and the only write target for this slice is the new pure module.
  - Acceptance:
    - Source: pure helpers are importable and do not import persistence/write APIs.
    - Runtime/UI: N/A; render contract is covered by unit tests in P1-B.
    - DB/data: source inspection proves projection calls are read-only and inputs are not mutated.
    - Behavior test: direct probes cover free-time boundary `2/1/0`, expired, and missing dates.
    - Cleanup/quarantine: no persisted data created.
    - Evidence IDs: `E1-P1A-RULE1..E1-P1A-PROJ3`.
    - Actual-status rows refreshed: `core/shipment_dashboard.py` missing -> partial/correct for pure model after verification.
  - Evidence Targets: module source, compile output, direct probe output, import/write-safety inspection.
  - Actual-status Update: append R1 with the new module classification and update P1-B assumptions from actual field aliases found during implementation.
  - Commit Boundary: commit after this slice when acceptance passes, unless dirty-file overlap prevents an isolated safe commit; record the reason.

- [x] P1-B: Add focused behavior fixtures/tests and no-write proof.
  - Goal: prove the projection/rules for all bounded LOG-C03 scenarios before wiring UI.
  - Scope Boundary:
    - Editable: new `tests/test_shipment_dashboard.py` only.
    - Inspect-only: `core/shipment_dashboard.py` and existing finance/ledger tests.
    - Preserve-only: existing LOG-C02 tests and real DB data.
    - Out of scope: browser interaction and Streamlit monkeypatch-heavy tests.
  - Non-Goals: no Mongo writes, no production fixture insertion, no tests that assert only static source shape.
  - Pre-flight Questions:
    - Data source: in-memory shipment dictionaries with Golden Lục Giác fixture.
    - Display permission: N/A; pure projection.
    - DB read flow: N/A; inject read-only summary or use the pure projection seam.
    - DB write flow: assert no write helper is called; no DB fixture enabled.
    - Render location: later UI contract fields.
    - UI behavior flow: model-level trigger -> rule -> observable row state.
    - Docker runtime: N/A; final runtime remains separate.
    - Playwright target: N/A.
    - Behavior test: `pytest -q tests/test_shipment_dashboard.py`.
    - Cleanup/quarantine: all fixtures local and discarded by test process.
    - External side effects: none.
    - N/A notes: Mongo opt-in tests remain unchanged and are not required for pure rule proof.
  - Work Steps:
    1. Add fixture builders for normal, warning, critical, deadline, finance, missing-data, and Golden Lục Giác shipments.
       - UI flow check: prove each fixture yields the intended render-ready state.
       - DB/data flow check: assert input fixture is unchanged after projection.
       - Render location check: assert separate `operational_status` and `financial_status` fields.
       - Mini QA for each completed implementation slice (MUST): run the focused test file.
       - Evidence target: `E1-P1B-TEST1..E1-P1B-TEST5`.
    2. Add filter/ranking and no-financial-write assertions, including SALE Thanh and unknown/review states.
       - UI flow check: assert filtered view IDs and ranked attention labels.
       - DB/data flow check: patch/read-only seam and assert no write call occurs.
       - Render location check: assert no fake next action when evidence is absent.
       - Mini QA for each completed implementation slice (MUST): focused tests plus existing `tests/test_shipment_360.py`.
       - Evidence target: `E1-P1B-FILTER1..E1-P1B-SAFETY2`.
  - Implementation Gate:
    - P1-A module behavior exists and compile/direct probes pass.
    - Test fixtures do not write production paths or require Mongo.
  - Acceptance:
    - Source: tests use observable model behavior, not implementation-only assertions.
    - Runtime/UI: model contract is complete for later renderer.
    - DB/data: no-write test passes and fixture deep-copy equality holds.
    - Behavior test: focused file and adjacent LOG-C02 projection tests pass.
    - Cleanup/quarantine: no persistent data remains.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-SAFETY2`.
    - Actual-status rows refreshed: P1 model status correct; P2 UI assumptions updated from test field coverage.
  - Evidence Targets: focused test output, fixture matrix, source-of-truth/no-write assertions.
  - Actual-status Update: append R2 with scenario coverage and any unsupported current data fields.
  - Commit Boundary: commit after this slice when acceptance passes, unless safe staging is impossible because of pre-existing overlap.

### P2: Shipment-first Streamlit work desk

- Phase Goal: render the model in the existing dashboard without replacing Streamlit or breaking detail navigation.
- Phase Boundary:
  - In scope: bounded `views/dashboard.py` dashboard tab/row/filter rendering and related style additions.
  - Out of scope: existing GetFly import/export, Top Customer, commission, task/note tools, Shipment 360 renderer, and finance writes except preserving their current reachability.
  - Dependencies: P1 model/tests; current dashboard session aliases; existing status/config/style vocabulary.
- Phase Implementation Rule: implement P2-A, verify and refresh status, then P2-B, then P2-C. Do not combine unrelated UI behaviors in one patch.
- Ordered Slice List:
  - P2-A: Render attention summary and shipment rows with two status dimensions.
  - P2-B: Add compact shipment filters and deterministic ordering.
  - P2-C: Preserve/verify Shipment 360 first-click, close/back, and second-shipment navigation.

- [x] P2-A: Render attention summary and shipment rows with two status dimensions.
  - Goal: replace the customer-group-first dashboard body with a readable support queue while keeping existing tabs below/alongside as preserve-only functionality.
  - Scope Boundary:
    - Editable: `views/dashboard.py` only within `ui_dashboard` dashboard tab and local style/helpers; new dashboard model imports.
    - Inspect-only: `views/shipment.py`, `views/shipment_360.py`, `core/shipment_360.py`.
    - Preserve-only: existing detail renderer, save/delete controls, GetFly, Top Customer, commission, task/note behavior.
    - Out of scope: new UI framework or a full visual rewrite.
  - Non-Goals: no balance calculations in row renderer, no new write control, no dashboard finance editing.
  - Pre-flight Questions:
    - Data source: normalized `all_ships` plus P1 projection.
    - Display permission: existing dashboard route permission; detail edit permission remains as-is.
    - DB read flow: current session data loaded by `load_data`; financial view read-only.
    - DB write flow: none from new row/card path.
    - Render location: top of `t_board` after compact header/filter context.
    - UI behavior flow: dashboard load -> attention summary -> shipment row -> open button.
    - Docker runtime: pending/no Docker target found in P0.
    - Playwright target: local Streamlit only as supporting evidence until Docker availability is known.
    - Behavior test: P1 focused model tests; later Playwright.
    - Cleanup/quarantine: no test data write.
    - External side effects: none.
    - N/A notes: existing analytics tabs stay unchanged to avoid scope drift.
  - Work Steps:
    1. Add summary counts and status/alert style tokens with accessible text labels, not color-only meaning.
       - UI flow check: load dashboard and inspect summary states at normal desktop viewport.
       - DB/data flow check: projection is invoked read-only per shipment; no snapshot write.
       - Render location check: summary precedes the queue and does not bury shipment rows under KPI charts.
       - Mini QA for each completed implementation slice (MUST): run Streamlit health and visible screenshot/DOM snapshot.
       - Evidence target: `E2-P2A-UI1..E2-P2A-UI3`.
    2. Render compact row/card fields: shipment ID, customer, owner when present, operational status, deadline, top warning/next attention, financial status, last update, and open button.
       - UI flow check: verify warning/critical/financial flags are readable without opening the row.
       - DB/data flow check: missing data remains `CẦN BỔ SUNG`/`UNKNOWN`; no fake values.
       - Render location check: preserve existing `active_shipment_id` and `dashboard_active_shipment_id` aliases for open behavior.
       - Mini QA for each completed implementation slice (MUST): compile, focused tests, and local browser screenshot.
       - Evidence target: `E2-P2A-CARD1..E2-P2A-NAV1`.
  - Implementation Gate:
    - Run Anvien file-detail/impact for `views/dashboard.py` and symbol-level impact for `ui_dashboard`; record high/critical warnings and keep edits surgical.
    - Confirm the new renderer imports only read model functions and does not add financial write imports.
  - Acceptance:
    - Source: dashboard composes model fields and does not duplicate ledger math.
    - Runtime/UI: shipment-first summary and rows are visible/readable; operational/financial statuses are separate.
    - DB/data: dashboard navigation does not call write APIs.
    - Behavior test: P1 tests remain green.
    - Cleanup/quarantine: no persistent fixture.
    - Evidence IDs: `E2-P2A-UI1..E2-P2A-NAV1`.
    - Actual-status rows refreshed: dashboard partial/wrong -> partial/correct for shipment-first render.
  - Evidence Targets: source diff, local runtime screenshot, DOM snapshot, compile/test output.
  - Actual-status Update: append R3 and update P2-B filter assumptions.
  - Commit Boundary: commit after slice when safe; otherwise keep targeted diff and record mixed-worktree reason.

- [x] P2-B: Add compact shipment filters and deterministic ordering.
  - Goal: let support/SALE Thanh narrow the queue without an advanced search engine.
  - Scope Boundary:
    - Editable: `views/dashboard.py` filter controls/selection logic only.
    - Inspect-only: P1 filter helpers, auth current-user identity, existing time/status filters.
    - Preserve-only: current search and date filters unless safely composed.
    - Out of scope: saved views, server-side query system, auto assignment.
  - Non-Goals: no editable owner/status duplication in storage; filter state stays session UI state.
  - Pre-flight Questions:
    - Data source: P1 projection list.
    - Display permission: current user display name for `Của tôi`; fixture owner `Thành` for Golden path.
    - DB read flow: same loaded session data.
    - DB write flow: none.
    - Render location: compact filter row immediately above queue.
    - UI behavior flow: choose filter -> rerun -> list/count/summary update.
    - Docker runtime: same pending blocker.
    - Playwright target: reusable LOG-C03 flow against real runtime where available.
    - Behavior test: P1 filter tests plus browser filter interaction.
    - Cleanup/quarantine: no persistent data.
    - External side effects: none.
    - N/A notes: customer/owner option values derive from current rows; no new master-data writes.
  - Work Steps:
    1. Add all/owned/owner/customer/operational/financial/alert/deadline-soon filters with stable Streamlit keys.
       - UI flow check: each enabled filter can be selected and visibly changes the queue.
       - DB/data flow check: filter is applied to in-memory read model only.
       - Render location check: no hidden advanced search or duplicate finance control.
       - Mini QA for each completed implementation slice (MUST): visible browser interaction and screenshot for SALE Thanh, financial, and alert filters.
       - Evidence target: `E2-P2B-FILTER1..E2-P2B-FILTER4`.
    2. Sort attention first, then deadline, then last update; retain truthful empty state.
       - UI flow check: critical/overdue shipment appears before normal shipment and empty filter explains no results.
       - DB/data flow check: sorting does not mutate `db_shipments` documents.
       - Render location check: filter state is retained through detail close/back when current Streamlit behavior supports it.
       - Mini QA for each completed implementation slice (MUST): focused tests and browser DOM snapshot.
       - Evidence target: `E2-P2B-SORT1..E2-P2B-EMPTY1`.
  - Implementation Gate:
    - Run Anvien impact for the relevant `ui_dashboard` filter region and confirm the edit does not touch core database or ledger files.
  - Acceptance:
    - Source: filters map to model fields and current session only.
    - Runtime/UI: SALE Thanh, financial, and alert filter paths are observable.
    - DB/data: no filter writes or fixture persistence.
    - Behavior test: model filter tests pass.
    - Cleanup/quarantine: none required.
    - Evidence IDs: `E2-P2B-FILTER1..E2-P2B-EMPTY1`.
    - Actual-status rows refreshed: filter capability partial -> correct for supported fields; unsupported fields documented as gaps.
  - Evidence Targets: filter inventory, browser screenshots, model test output, no-write inspection.
  - Actual-status Update: append R4 with supported owner/deadline field findings.
  - Commit Boundary: commit after slice when safe; do not broad-stage pre-existing work.

- [x] P2-C: Preserve/verify Shipment 360, back, and second-shipment navigation.
  - Goal: close the existing dashboard -> detail invariant after the new row renderer is mounted.
  - Scope Boundary:
    - Editable: only `views/dashboard.py` navigation wiring if the new row needs a surgical key/rerun fix.
    - Inspect-only: `views/shipment.py`, `views/shipment_360.py`, `views/web_app.py`.
    - Preserve-only: current first-click fix and detail close state aliases unless a direct regression is reproduced.
    - Out of scope: new routing system and detail-page redesign.
  - Non-Goals: no changes to finance/detail save/payment semantics.
  - Pre-flight Questions:
    - Data source: session `db_shipments`/`all_ships` and active ID aliases.
    - Display permission: existing route/detail permissions.
    - DB read flow: current session/loaded DB data.
    - DB write flow: no click in QA on save/delete/payment.
    - Render location: row open button and existing detail container.
    - UI behavior flow: dashboard -> first shipment -> close/back -> second shipment.
    - Docker runtime: required for final full QA if available; otherwise blocker.
    - Playwright target: `playwright/log_c03_shipment_dashboard_flow.mjs`.
    - Behavior test: existing LOG-C01/LOG-C02 flow plus LOG-C03 flow.
    - Cleanup/quarantine: no persistent writes.
    - External side effects: none.
    - N/A notes: browser history route is not a separate URL in current Streamlit architecture.
  - Work Steps:
    1. Run existing C01/C02 browser flows after UI integration and compare detail heading/financial projection evidence.
       - UI flow check: first click opens correct ID; Shipment 360 appears; close returns to queue.
       - DB/data flow check: no save/delete/payment control submitted.
       - Render location check: filter state/customer context remains visible after close.
       - Mini QA for each completed implementation slice (MUST): screenshots before click, after open, after close.
       - Evidence target: `E2-P2C-REG1..E2-P2C-REG3`.
    2. Run the second-shipment path from the new queue and record any host/runtime blocker.
       - UI flow check: opening a second row after returning renders the second ID, not stale detail.
       - DB/data flow check: source counts and financial action request counts remain unchanged.
       - Render location check: no console/runtime error attributable to LOG-C03.
       - Mini QA for each completed implementation slice (MUST): reusable Playwright output plus screenshot inspection.
       - Evidence target: `E2-P2C-SECOND1..E2-P2C-SAFETY1`.
  - Implementation Gate:
    - Run Anvien impact on `ui_dashboard`; only edit if a direct regression is reproduced.
  - Acceptance:
    - Source: active ID aliases remain consistent.
    - Runtime/UI: first/close/second flow passes on the real available runtime or is explicitly blocked by the host capability.
    - DB/data: read-only flow leaves financial write collections/counters unchanged.
    - Behavior test: existing and new browser scripts produce machine-readable evidence.
    - Cleanup/quarantine: no real data mutation; stop any runtime process after QA.
    - Evidence IDs: `E2-P2C-REG1..E2-P2C-SAFETY1`.
    - Actual-status rows refreshed: navigation stays correct/preserve-only or records reproduced regression.
  - Evidence Targets: browser screenshots/JSON/MD, console/runtime logs, source diff, no-write readback.
  - Actual-status Update: append R5 with runtime verdict and Docker blocker.
  - Commit Boundary: separate fix commit only if a regression required a code change; otherwise no new product commit.

### P3: Regression, browser evidence, and closure

- Phase Goal: validate the bounded slice proportionally, record evidence/benchmarks, and obtain independent supervisor acceptance or a precise blocker.
- Phase Boundary:
  - In scope: full compile/test, existing finance/payment regression, Streamlit health, Playwright QA, reports, detect-changes, and safe worktree handoff.
  - Out of scope: optional hardening, Docker infrastructure creation, LOG-C04, and unrelated dirty files.
  - Dependencies: P1/P2 slices.
- Phase Implementation Rule: verification slices do not change product behavior; any fix returns to the responsible implementation slice with a separate review cycle.
- Ordered Slice List:
  - P3-A: Run full local validation and browser QA/reporting.
  - P3-B: Run Anvien detect-changes, supervisor review, and closure classification.

- [x] P3-A: Run full local validation and browser QA/reporting.
  - Goal: produce current source, test, runtime, screenshot, and regression evidence for all bounded acceptance criteria.
  - Scope Boundary:
    - Editable: new report artifacts under `reports/QA/`, `.tmp/` logs, and plan evidence/benchmark/status files.
    - Inspect-only: product code after P2.
    - Preserve-only: production data and prior reports.
    - Out of scope: fixing code while acting as QA; code fixes require a new implementation slice.
  - Non-Goals: do not claim Docker acceptance when Docker is unavailable.
  - Pre-flight Questions:
    - Data source: current local runtime plus in-memory test fixtures.
    - Display permission: local admin/current existing session.
    - DB read flow: real app read path; no writes.
    - DB write flow: no business action submitted.
    - Render location: real dashboard and Shipment 360.
    - UI behavior flow: load -> filter -> open -> close -> open second.
    - Docker runtime: attempt/record exact capability; no Dockerfile currently exists.
    - Playwright target: latest real runtime available; classify host-only evidence honestly.
    - Behavior test: `pytest -q`, `python -m compileall core views tests`, existing and new Playwright flows.
    - Cleanup/quarantine: stop runtime, retain official reports, keep debug output under `.tmp` only.
    - External side effects: none.
    - N/A notes: Mongo opt-in tests only run when explicitly configured and isolated.
  - Work Steps:
    1. Run compile/tests and current LOG-C02 projection/write-safety regressions, recording exact pass/skip/fail outputs.
       - UI flow check: N/A; source/runtime checks support the later browser verdict.
       - DB/data flow check: ensure no opt-in production Mongo test is enabled accidentally.
       - Render location check: compile includes changed `views/dashboard.py` and new module/tests.
       - Mini QA for each completed implementation slice (MUST): save logs under `.tmp` and link evidence IDs.
       - Evidence target: `E3-P3A-BUILD1..E3-P3A-REG2`.
    2. Run reusable Playwright flows with screenshots, inspect screenshots visually, and write QA JSON/MD.
       - UI flow check: cover summary, cards, filters, warning/critical distinction, first/second navigation.
       - DB/data flow check: compare read-only financial action/write counts before/after where observable.
       - Render location check: no console errors attributable to LOG-C03; document unsupported host capability.
       - Mini QA for each completed implementation slice (MUST): official evidence under `Reports/qa/playwright/...` if the project’s existing convention is used, with debug only in `.tmp`.
       - Evidence target: `E3-P3A-BROWSER1..E3-P3A-BROWSER5`.
  - Implementation Gate:
    - Product code is frozen for QA; any failure is reported and routed back to coder rather than patched in QA.
  - Acceptance:
    - Source: changed files compile.
    - Runtime/UI: browser evidence covers declared scope or marks downstream scope blocked.
    - DB/data: no real fixture mutation; financial projection remains read-only.
    - Behavior test: exact commands and results recorded.
    - Cleanup/quarantine: runtime stopped and official artifacts separated from `.tmp`.
    - Evidence IDs: `E3-P3A-BUILD1..E3-P3A-BROWSER5`.
    - Actual-status rows refreshed: final runtime/test statuses and blockers recorded.
  - Evidence Targets: test logs, health output, screenshots, QA report, JSON flow result, console/runtime logs.
  - Actual-status Update: append R6 with final validation classifications.
  - Commit Boundary: report/evidence-only artifacts are not broad-staged; follow worktree safety.

- [x] P3-B: Run Anvien detect-changes, supervisor review, and closure classification.
  - Goal: independently verify the complete LOG-C03 claim and stop at PASS/PARTIAL/BLOCKED with no hidden unresolved same-invariant surface.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/actual-status and required supervisor/coder/QA reports.
    - Inspect-only: final product diff and runtime artifacts.
    - Preserve-only: all unrelated pre-existing changes.
    - Out of scope: implementation fixes during supervisor review.
  - Non-Goals: no release/deploy/publish and no user approval request for a failed technical gate.
  - Pre-flight Questions:
    - Data source: current worktree, Anvien graph, validation artifacts.
    - Display permission: N/A.
    - DB read flow: N/A beyond evidence review.
    - DB write flow: no release/publish write.
    - Render location: final dashboard runtime.
    - UI behavior flow: review full trigger -> process -> observable result chain.
    - Docker runtime: record not run/blocked if unavailable.
    - Playwright target: review latest official artifacts.
    - Behavior test: detect-changes plus supervisor source/runtime review.
    - Cleanup/quarantine: no deletion outside plan-created debug artifacts.
    - External side effects: none.
    - N/A notes: no commit if safe isolated staging cannot be guaranteed.
  - Work Steps:
    1. Refresh Anvien graph if source changed and run `anvien detect-changes --repo Logistics-Pro-AI --scope all`; record affected files/flows and blast-radius warnings.
       - UI flow check: map changed dashboard -> projection -> detail path.
       - DB/data flow check: confirm ledger/database write surfaces were not newly affected.
       - Render location check: confirm source diff is within LOG-C03 boundary.
       - Mini QA for each completed implementation slice (MUST): evidence ledger entry.
       - Evidence target: `E3-P3B-DETECT1..E3-P3B-DETECT3`.
    2. Call supervisor skill for zero-trust acceptance review and write the report before final handoff.
       - UI flow check: supervisor verifies visible runtime evidence rather than source-only claims.
       - DB/data flow check: supervisor verifies no new financial write path and no real fixture mutation.
       - Render location check: supervisor verifies same-invariant surfaces and residual unverified scope.
       - Mini QA for each completed implementation slice (MUST): review package includes plan/status/evidence/benchmark/report links.
       - Evidence target: supervisor report and final status `E3-P3B-SUP1`.
  - Implementation Gate:
    - P3-A evidence exists; all known failures are classified; no unresolved same-invariant surface is silently omitted.
  - Acceptance:
    - Source: supervisor report inspects touched production files.
    - Runtime/UI: final verdict is exactly PASS, PARTIAL, or BLOCKED with evidence.
    - DB/data: write-safety boundary is explicitly cleared or blocked.
    - Behavior test: detect-changes and supervisor review are fresh.
    - Cleanup/quarantine: final worktree status is known.
    - Evidence IDs: `E3-P3B-DETECT1..E3-P3B-SUP1`.
    - Actual-status rows refreshed: final plan decision recorded.
  - Evidence Targets: detect-changes, supervisor report, final worktree status, plan closure.
  - Actual-status Update: append R7 final closure row.
  - Commit Boundary: only targeted safe commits; never broad-stage or reset unrelated changes.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify completed LOG-C03 work against the accepted plan, evidence, benchmark, changed files, generated output, and validation results.
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
    2. Remove or rewrite only plan-created dead artifacts; never delete unrelated dirty work.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails cleanup, return to the responsible workflow and re-run review.
  - Implementation Gate: only plan-created artifacts are candidates for cleanup.
  - Acceptance: final status contains no dead plan-created artifacts, or a blocker is recorded.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit decision, and final status.
  - Work Steps:
    1. Run required final validation including full build; record Docker absence if no Docker target/runtime exists.
    2. Start the real built container runtime if available; otherwise mark visible Docker QA blocked and retain local runtime evidence as supporting only.
    3. Validate UI with browser/Playwright evidence and screenshots.
    4. Regenerate only required generated outputs.
    5. Run Anvien detect-changes before any implementation commit.
    6. Record final validation, detect-changes, benchmark, and commit/worktree evidence.
    7. Commit only safe targeted files and verify worktree state; otherwise explain why no isolated commit was created.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: final evidence is current, the worktree boundary is known, and the final result is classified honestly.

## Risk Notes

- `views/dashboard.py` is already dirty and high-symbol-count; a safe isolated commit may be impossible without staging unrelated pre-existing hunks. Do not broad-stage or reset it.
- Anvien reports high unresolved-reference counts in legacy Streamlit modules; these are blast-radius/scope warnings, not reasons to edit unrelated code.
- The current repository has no Dockerfile/compose target, so planner-required Docker full-build/browser evidence may remain genuinely blocked.
- Current data may not contain customer required dates, owner, factory, or last-meaningful-update fields. The projection must expose missing data honestly and document unsupported fields instead of inventing values.
- The existing detail page still contains write-capable save/payment controls. LOG-C03 must not add new dashboard write paths or click those controls in QA; preserve LOG-C02 behavior.
- P2P workflow state is currently blocked by an active/uncertified Goal Contract requiring objective/oracle resolution. Do not modify P2P source; record this as governance evidence and do not claim P2P PASS.

## Final Plan Closure — 2026-08-14

- P1-A/P1-B, P2-A/P2-B/P2-C, and P3-A/P3-B were executed and their evidence is recorded in the linked evidence ledger, benchmark ledger, actual-status refresh, and official QA report.
- Pn-A supervisor review completed with verdict `REJECT`; the fresh re-review report is `reports/supervisor/rp_supervisor_260814_190347_by_gpt-5-codex_log_c03_shipment_dashboard.md`.
- Pn-B reviewed plan-created artifacts. No rejected implementation approach was retained; debug material remains under `.tmp/` per the QA convention, and unrelated dirty work was not removed.
- Pn-C is closed as `BLOCKED`, not as product PASS: local implementation/browser evidence is complete, while the P2P Goal Contract, Docker build target, pytest oracle, and numeric financial-write-count oracle remain unresolved.

## Formal Closure Reconciliation — 2026-08-14

The latest LOG-C03 closure request is the controlling acceptance authority for
this bounded product slice. The earlier Pn-C note above is historical and is
superseded for the product/helper split below; no product feature was added.

| Reported item | Classification | Closure result | Evidence / interpretation |
|---|---|---|---|
| Docker target absent | `NOT_APPLICABLE` | Closed as not applicable to LOG-C03 | No Dockerfile/compose target or canonical Docker workflow exists. `README_UPGRADE.md` and `start.sh` define the existing Streamlit runtime. The inherited plan wording is not an executable project target and is not part of the latest product acceptance list. |
| pytest unavailable | `NOT_APPLICABLE` | Closed as not applicable to LOG-C03 | `requirements.txt` does not declare pytest; the project documents `python -m unittest discover -s tests -v`. Canonical unittest execution and the bounded dashboard runner both pass. |
| Numeric financial-write-count oracle | `GOAL_ACCEPTANCE_REQUIREMENT` | Closed | `tests/test_dashboard_financial_write_oracle.py` mounts the real app entry point with an in-memory fixture, spies all bounded financial writer families, exercises filters and two navigation transitions, and proves `financial_write_count == 0` plus zero financial snapshot differences. |
| P2P Goal Contract / acceptance marker | `P2P_INFRASTRUCTURE_REQUIREMENT` | Product-independent helper remains blocked | The existing P2P run is `BLOCKED` because its goal linter requires independent objectives to be split before a Goal starts; `goal_created` is false and C1/C4 remain blocked. No P2P source/state/marker was changed. |

### Two-layer closure verdict

- Product/project acceptance: `PASS` for the LOG-C03 criteria A-K in the latest user request.
- P2P formal helper: `BLOCKED` by the existing P2P infrastructure workflow state.
- Fresh Supervisor review `reports/supervisor/rp_supervisor_260814_193944_by_gpt-5-codex_log_c03_formal_closure.md` returned `PASS` for the bounded product/project layer; the P2P formal helper remains separately `BLOCKED`.
- Known data-model gap: real runtime `SALE Thành` remains `0/78` because no
  normalized owner source exists. The filter semantics pass on a bounded
  fixture; no owner was inferred and no schema migration was opened.
- No LOG-C04 work was started.
