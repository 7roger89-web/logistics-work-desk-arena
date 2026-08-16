# LOG-C07 Logistics Operations Workspace Redesign Plan

## Metadata

- Date: `2026-08-16`
- Status: `BOUNDED TERMINAL / PASS / release blocked`
- Plan: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-actual-status.md`

## Goal

This plan closes at a bounded, supervisor-reviewed local UI result for the shell and Dashboard workdesk. Secondary route-body redesign remains the next recommended goal; no release, deployment, publication, payment, migration, or canonical financial mutation is included.

Turn the existing Streamlit Logistics product into a professional, shipment-first operations workspace for SALE Thành and support. The first screen must make work priority, owner, deadline, exception, customer/factory context, and next action legible before opening Shipment 360. Financial status stays a read-only, source-labelled explanation behind the operational surface; historical A Bò stays `NOT_PUBLISHED / DEFERRED_OWNER_GATED`.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For UI-facing changes, validate the real user-visible Streamlit runtime with visible-browser/Playwright evidence.
- There is no Docker target or Docker executable in this repository/host; local runtime evidence is supporting evidence only and cannot be called production/release acceptance.
- Keep edits bounded to presentation, navigation shell, read-only workdesk controls, tests, and design/evidence artifacts.
- Do not mutate canonical financial/business data, payment state, historical staging, opening balances, or the database schema.
- Do not publish historical A Bò, enable payment, migrate history, deploy, release, or communicate externally.
- Preserve LOG-C02–LOG-C06 code paths and evidence; preserve existing Shipment 360/detail write controls and permissions.
- Unknown, missing, deferred, and review states must remain explicit; no fallback zero, guessed owner, or invented factory/agent data.

## Problem

The current runtime already has a good pure shipment dashboard projection, but the visible product still behaves like a legacy collection of controls: flat navigation, date/search/tasks/history ahead of the work queue, a long customer-count paragraph, four generic metrics, dense cards with no consistent context hierarchy, and only a financial status label rather than a concise explanation of source and meaning. Support has to scan too much before finding the shipment; SALE cannot see the operational portfolio and financial review in one clear workspace. The source projection and financial read models are safer than the current presentation and should be reused rather than duplicated.

## Scope

- Rework the Streamlit application shell/sidebar in `views/web_app.py` into grouped Operations / Commercial / Finance & review navigation while preserving route labels, permissions, active-page state, reload, archive, auth, and all existing route reachability.
- Rework the dashboard first screen in `views/dashboard.py`: put shipment attention and work queue before secondary analytics; keep the legacy tabs reachable below the operational surface.
- Add an operations header with as-of/freshness context, search, archive scope, and quick actions without hiding the existing task/note functionality.
- Add a compact priority band and dense shipment rows with separate operational/financial badges, next action, owner/customer/route, deadline/free-time signals, document/factory completeness when present, and a read-only “why this financial state” disclosure sourced from `financial_projection`.
- Preserve `core/shipment_dashboard.py`, `core/shipment_360.py`, `core/financial_ledger.py`, `core/database.py`, `views/shipment.py`, and historical staging as preserve-only unless a test reveals an existing regression caused by presentation wiring.
- Add direct presentation helper tests where feasible and a reusable Playwright flow/report under `playwright/` / `reports/QA/playwright/`.
- Create/update project-owned design contract and master design system artifacts through official P2P UIUX tooling after the bounded direction is selected.

## Non-Goals

- No React/Next rewrite, new frontend stack, new database, task/workflow engine, AI, automatic assignment, GPS, portal, or production deployment.
- No change to financial calculation, canonical ledger truth, write safety, payment, reconciliation logic, historical opening, staging classification, or A Bò deferred decisions.
- No rebrand that removes the existing Logistics identity; use a restrained operations-console direction adapted to Streamlit.
- No removal of legacy dashboard tabs, import/export, commission, customer ranking, or detail write controls; only demote them behind the primary operations surface.
- No claim of WCAG conformance; accessibility evidence is bounded to visible focus/contrast/reading-order checks and remains `NEEDS_EVIDENCE` where measurement is unavailable.

## Requirements

1. Primary landing surface is `Dashboard` and answers: what is urgent, what is next, who owns it, and where to open the shipment.
2. Queue rows remain shipment-first and sorted by criticality, deadline, then stable shipment ID.
3. Search covers shipment ID, customer, owner, operational status, and financial status through the existing projection filter.
4. Filters expose owner/SALE, customer, alert, operational status, financial flag, deadline soon, archive scope, and a reset path without hiding current filter state.
5. Operational status and financial status stay separate; financial status includes read-only source/meaning disclosure and explicit UNKNOWN/review wording.
6. Customer, route, factory/document context, last update, promised/required/planned dates, and next attention fit into a scan-friendly row without inventing missing values.
7. Shipment 360 opens from the row, retains shipment identity, close/back restores the workdesk, and the existing detail save/delete permission behavior remains untouched.
8. Navigation groups daily work first and keeps A Bò visibly a partner/review instance rather than the product center.
9. Empty, stale, missing, error, and no-results states are explicit and recoverable.
10. Existing LOG-C02 financial/ledger/payment and LOG-C06 historical safety tests remain green.

## Acceptance Criteria

- Visible first viewport presents grouped navigation, operational context, priority band, search/filter entry, and first actionable shipment rows without scrolling through unrelated analytics first.
- A support user can identify a critical shipment, owner/unknown owner, next action, deadline/free-time risk, and open Shipment 360 in one scan.
- SALE Thành can see portfolio totals, attention counts, financial review/UNKNOWN counts, and the source meaning of displayed financial state without a financial write control.
- Customer/factory/document context is present only when supported by current fields; absent data remains visibly unknown/missing.
- Dashboard -> row -> Shipment 360 -> close/back works in the real runtime; second-row navigation remains deterministic.
- Presentation changes do not mutate shipment mappings or invoke financial write helpers.
- Visible runtime screenshots, a control/action ledger, source-of-truth checks, independent critique, correction screenshot, and regression output exist.
- Local build/compile and relevant tests pass. Docker/production acceptance remains explicitly blocked by host/repository capability; release status is `NOT_RELEASED`.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish current product reality and protect LOG-C02–LOG-C06 boundaries.
  - Work Steps: inspect current runtime/source, existing plans/reports, P2P `.19`, Design Intelligence route, Anvien graph/file detail/impact, baseline screenshot, tests, and Docker capability; classify every touched surface in actual-status.
  - Implementation Gate: no product code edits before actual-status contains baseline evidence IDs, relationship counts, touch modes, and the P0 decision.
  - Acceptance: current dashboard and shell are `partial`; read-only projections/financial/historical capabilities are preserve-only; local runtime is available; Docker is a known blocker.

### P1: Workspace shell and information architecture

- Phase Goal: make the product feel like one operations workspace with daily work first and secondary capabilities behind it.
- Phase Boundary:
  - In scope: `views/web_app.py` shell/sidebar/global tokens and bounded route metadata.
  - Out of scope: route business logic, financial data, historical staging, and database writes.
  - Dependencies: P0 actual-status; current permission and session-state contract.
- Phase Implementation Rule: implement `P1-A`, verify/refresh status/commit, then `P1-B`.
- Ordered Slice List:
  - P1-A: Grouped navigation and workspace chrome.
  - P1-B: Global visual tokens, focus, density, and runtime shell states.

- [x] P1-A: Grouped navigation and workspace chrome.
  - Goal: expose Operations, Commercial, Finance & review, and Tools groups without breaking route reachability.
  - Scope Boundary:
    - Editable: `views/web_app.py` route metadata and `_render_sidebar` only.
    - Inspect-only: `core.auth`, `core.state`, existing route modules, Playwright route locators.
    - Preserve-only: route permissions, `active_page`, reload/archive/auth/logout behavior, A Bò route implementation.
    - Out of scope: financial/reconciliation logic and any route body.
  - Non-Goals: no hidden routes, no new permissions, no sidebar data writes.
  - Pre-flight Questions:
    - Data source: existing `ROUTES` and `has_permission`.
    - Display permission: existing route permission contract.
    - DB read flow: none; shell only.
    - DB write flow: none.
    - Render location: visible sidebar and top page context.
    - UI behavior flow: open app -> choose grouped route -> same route function renders.
    - Docker runtime: unavailable; local Streamlit supporting evidence.
    - Playwright target: visible route switching and active state.
    - Behavior test: existing route smoke plus new helper/unit assertions where useful.
    - Cleanup/quarantine: none; session-only navigation state.
    - External side effects: none.
    - N/A notes: no API/DB contract applies.
  - Work Steps:
    1. Add explicit route group metadata and professional display copy while retaining stable route labels/keys.
       - UI flow check: every visible route remains reachable and selected route remains highlighted.
       - DB/data flow check: confirm `_visible_routes` still gates by permission and no loader/write path changes.
       - Render location check: sidebar is compact, grouped, and keeps reload/archive/auth controls below navigation.
       - Mini QA: compile `views/web_app.py` and visible route click smoke.
       - Evidence target: `E1-P1A-NAV1..E1-P1A-NAV3`.
    2. Move A Bò into a clearly labelled partner/review group and preserve its route; keep financial ledger as a secondary capability.
       - UI flow check: A Bò remains discoverable but is not the primary navigation anchor.
       - DB/data flow check: no historical read/write code is imported by the shell.
       - Render location check: grouped labels explain Operations vs Finance/review.
       - Mini QA: visible navigation inventory and route return to Dashboard.
       - Evidence target: `E1-P1A-SAFE1`.
  - Implementation Gate:
    - Anvien file-detail/impact for `views/web_app.py` and `_render_sidebar` is recorded; current relationship count is 16 local file relationships and the graph is fresh.
    - No route body or permission function is edited.
  - Acceptance:
    - Source: grouping is metadata/presentation-only.
    - Runtime/UI: visible sidebar grouping, active state, route switch, reload/archive/auth controls remain usable.
    - DB/data: no write path introduced.
    - Behavior test: route inventory covers Dashboard, finance, A Bò partner desk, and at least one tool route.
    - Cleanup/quarantine: no persistent data changed.
    - Evidence IDs: `E1-P1A-NAV1..E1-P1A-SAFE1`.
    - Actual-status rows refreshed: `views/web_app.py` partial -> correct for shell scope.
  - Evidence Targets: diff/source, route inventory, visible screenshot, Anvien impact, control ledger.
  - Actual-status Update: record shell status transition and update P2 assumptions to use grouped nav labels.
  - Commit Boundary: commit after slice acceptance.

- [x] P1-B: Global visual tokens, focus, density, and runtime shell states.
  - Goal: replace default Streamlit chrome feel with a restrained navy/ink/amber operations-console language that supports dense data and uncertainty.
  - Scope Boundary:
    - Editable: `_configure_page` style block in `views/web_app.py`.
    - Inspect-only: current dashboard local style block and Streamlit DOM selectors.
    - Preserve-only: component semantics, labels, route handlers, and colors conveying status.
    - Out of scope: dashboard row markup.
  - Non-Goals: no external font/network dependency, no decorative animation, no WCAG claim.
  - Pre-flight Questions:
    - Data source: N/A; CSS tokens only.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: app shell, sidebar, controls, focus, tables/containers.
    - UI behavior flow: app load -> visible shell -> keyboard focus/hover/resize.
    - Docker runtime: unavailable; local evidence only.
    - Playwright target: screenshot at desktop and narrow viewport; focus ring smoke.
    - Behavior test: compile plus visible render.
    - Cleanup/quarantine: none.
    - External side effects: none.
    - N/A notes: CSS changes cannot prove complete accessibility; mark NEEDS_EVIDENCE.
  - Work Steps:
    1. Introduce CSS variables, compact typography/table numeric alignment, consistent borders, focus rings, and responsive reading order.
       - UI flow check: controls remain visible and readable after styling.
       - DB/data flow check: no data path changes.
       - Render location check: shell and future queue share the same token language.
       - Mini QA: compile and screenshot at 1440px and 980px.
       - Evidence target: `E1-P1B-VIS1..E1-P1B-VIS2`.
  - Implementation Gate:
    - `views/web_app.py` source/impact evidence is current; no new dependency.
  - Acceptance:
    - Source: CSS is bounded and names tokens.
    - Runtime/UI: visible focus, readable labels, no clipped sidebar controls at supported widths.
    - DB/data: unchanged.
    - Behavior test: shell still loads after rerun.
    - Cleanup/quarantine: none.
    - Evidence IDs: `E1-P1B-VIS1..E1-P1B-VIS2`.
    - Actual-status rows refreshed: shell visual status partial -> correct for bounded scope.
  - Evidence Targets: screenshots, DOM/control inventory, compile output.
  - Actual-status Update: append R1 after P1.
  - Commit Boundary: commit after slice acceptance.

### P2: Shipment-first operations workdesk

- Phase Goal: make daily shipment work the front door and reduce scan cost without rewriting the read model.
- Phase Boundary:
  - In scope: `_render_shipment_workdesk`, dashboard header/filter placement, row presentation, read-only financial explanation, dashboard body order in `views/dashboard.py`.
  - Out of scope: projection rules, Shipment 360 internals, database writes, legacy tabs below the workdesk.
  - Dependencies: P1 shell tokens; existing `core.shipment_dashboard` contract.
- Phase Implementation Rule: implement `P2-A`, verify/refresh status/commit, then `P2-B`.
- Ordered Slice List:
  - P2-A: Operations header, priority band, and search/filter model.
  - P2-B: Dense shipment rows, context, source-labelled financial disclosure, and legacy feature demotion.

- [x] P2-A: Operations header, priority band, and search/filter model.
  - Goal: surface as-of context, urgent workload, and filters before secondary task/history/analytics content.
  - Scope Boundary:
    - Editable: `views/dashboard.py` local render helpers and dashboard body order.
    - Inspect-only: `core/shipment_dashboard.py` filter/sort/summary functions; task/note persistence.
    - Preserve-only: task/note dialogs and their database calls, legacy tabs, detail route.
    - Out of scope: core projection and finance logic.
  - Non-Goals: no dashboard-specific financial math and no persisted filter state beyond session state.
  - Pre-flight Questions:
    - Data source: `build_shipment_dashboard_view`, `build_dashboard_summary`, `filter_dashboard_views`, `sort_dashboard_views`.
    - Display permission: existing Dashboard permission.
    - DB read flow: existing `load_data`/`load_archived_data` only.
    - DB write flow: none in new workdesk path.
    - Render location: first dashboard tab viewport before task/history/legacy analytics.
    - UI behavior flow: load -> inspect band -> search/filter -> sorted queue.
    - Docker runtime: unavailable; local supporting evidence.
    - Playwright target: visible search/filter change and no-results recovery.
    - Behavior test: projection/filter tests plus visible interaction ledger.
    - Cleanup/quarantine: no writes; fixture tests remain in memory.
    - External side effects: none.
    - N/A notes: task checkbox writes stay reachable but are not part of new queue actions.
  - Work Steps:
    1. Move shipment queue ahead of task/history blocks and make date/archive scope secondary context rather than the first visual block.
       - UI flow check: first viewport shows queue entry and filter affordance.
       - DB/data flow check: same loaded `all_ships` mapping feeds projection; no mutation added.
       - Render location check: queue renders inside Dashboard tab before secondary tabs.
       - Mini QA: local runtime screenshot and body text inspection.
       - Evidence target: `E2-P2A-ORDER1`.
    2. Add a compact command/search bar with reset and explicit filter summary; wire search to `filter_dashboard_views(search=...)`.
       - UI flow check: type query -> rows narrow -> clear/reset restores list.
       - DB/data flow check: projection rows only; no DB write.
       - Render location check: search and filters are adjacent to workdesk header.
       - Mini QA: visible interaction flow with no-results state.
       - Evidence target: `E2-P2A-FILTER1..E2-P2A-FILTER2`.
  - Implementation Gate:
    - Anvien file-detail/impact for `views/dashboard.py`, `_render_shipment_workdesk`, and `ui_dashboard` is current; file summary is high-risk with 130 symbols/8 local relationships, so the change stays presentation-only.
    - Existing focused tests pass before changing behavior.
  - Acceptance:
    - Source: only render ordering/filter wiring changes.
    - Runtime/UI: queue and filters are first-class; no-results and reset are clear.
    - DB/data: no new write import/call.
    - Behavior test: current projection/filter tests pass; visible search/no-results/recovery recorded.
    - Cleanup/quarantine: no persistent fixture/data.
    - Evidence IDs: `E2-P2A-ORDER1..E2-P2A-FILTER2`.
    - Actual-status rows refreshed: dashboard partial -> partial with primary workdesk front door complete.
  - Evidence Targets: diff, compile, tests, visible screenshots, action ledger.
  - Actual-status Update: refresh P2-B assumptions from actual DOM and row density.
  - Commit Boundary: commit after slice acceptance.

- [x] P2-B: Dense shipment rows, context, source-labelled financial disclosure, and legacy feature demotion.
  - Goal: make one row explain the shipment, current work, deadline, owner, context, financial meaning, and open action without a card collage.
  - Scope Boundary:
    - Editable: `_render_shipment_workdesk`, `_desk_badge`, and related local helpers in `views/dashboard.py`.
    - Inspect-only: `core/shipment_dashboard.py` financial projection; `views/shipment_360.py` and `core/financial_ledger.py`.
    - Preserve-only: detail open/save/delete, all finance writes, legacy tabs.
    - Out of scope: new financial calculations or new business status taxonomy.
  - Non-Goals: no aggregate balances that are not already present in read projections; no guessed “paid” zero.
  - Pre-flight Questions:
    - Data source: row fields plus `row['financial_projection']` and existing shipment section fields.
    - Display permission: Dashboard read permission; detail permission unchanged.
    - DB read flow: none beyond current data load and read-only projection.
    - DB write flow: none.
    - Render location: dense queue rows with expandable “Vì sao?” detail and secondary context columns.
    - UI behavior flow: row scan -> expand explanation/context -> open Shipment 360.
    - Docker runtime: unavailable; local supporting evidence.
    - Playwright target: open first row, inspect explanation, close/back, open second row.
    - Behavior test: add helper tests for explanation labels and no mutation if direct seam is extracted.
    - Cleanup/quarantine: no writes.
    - External side effects: none.
    - N/A notes: documents/factory/agent fields are shown only when existing mapping supplies them.
  - Work Steps:
    1. Replace four generic metric cards and long customer-count paragraph with a compact priority band that counts critical, waiting/missing, deadline, financial review/UNKNOWN, and total.
       - UI flow check: numbers are labelled by meaning; clicking/filtering retains the same count semantics.
       - DB/data flow check: counts derive from `build_dashboard_summary`/rows only.
       - Render location check: band sits directly above rows.
       - Mini QA: visible screenshot and source inspection.
       - Evidence target: `E2-P2B-BAND1`.
    2. Redesign each row as a dense operations line: identity/context, owner and last update, operational status, deadline/free-time, financial status, next action, and one Shipment 360 action.
       - UI flow check: row has one obvious open action and text alternatives for color statuses.
       - DB/data flow check: no financial write helpers called from row renderer.
       - Render location check: rows remain readable at desktop and narrow viewport; no horizontal overflow for core action.
       - Mini QA: open/close/second-row visible flow and screenshot.
       - Evidence target: `E2-P2B-ROW1..E2-P2B-ROW3`.
    3. Add progressive disclosure for “Vì sao tài chính ở trạng thái này?” using existing source/reason fields; render UNKNOWN/review/missing explicitly.
       - UI flow check: disclosure opens/closes without leaving workdesk; no write button appears.
       - DB/data flow check: source strings come from `financial_projection.sources`, `receivable`, `payable`, `known_cost`, and existing projection; no recalculation.
       - Render location check: explanation stays secondary to action and does not dominate the row.
       - Mini QA: inspect a CHỜ THU, UNKNOWN, and review row in visible runtime.
       - Evidence target: `E2-P2B-FIN1..E2-P2B-FIN2`.
  - Implementation Gate:
    - `core/shipment_dashboard.py` remains preserve-only; financial regression tests are green.
    - Source inspection confirms no `save_*`, `allocate_*`, `reverse_*`, payment, or historical publish call in new renderer.
  - Acceptance:
    - Source: row markup is readable and bounded; financial display is projection-only.
    - Runtime/UI: support can identify next action and open Shipment 360; SALE can read why/status/source.
    - DB/data: no mutation; unknowns visible.
    - Behavior test: focused shipment dashboard, Shipment 360, financial write safety, historical closure tests pass.
    - Cleanup/quarantine: no persistent data changed.
    - Evidence IDs: `E2-P2B-BAND1..E2-P2B-FIN2`.
    - Actual-status rows refreshed: dashboard primary surface partial -> correct for bounded redesign.
  - Evidence Targets: source/diff, tests, screenshots, action ledger, source-of-truth table.
  - Actual-status Update: append R2 after P2.
  - Commit Boundary: commit after slice acceptance.

### P3: Render, critique, correction, and regression

- Phase Goal: prove the redesign in the real local runtime, independently critique the rendered result, correct material defects, and verify regressions.
- Phase Boundary:
  - In scope: reusable Playwright script/report, screenshots, visible runtime checks, focused/full tests, P2P design-system/a11y/drift artifacts.
  - Out of scope: Docker/production release, historical A Bò changes, data mutation.
  - Dependencies: P1/P2 implementation slices.
- Phase Implementation Rule: implement `P3-A`, record runtime critique, then `P3-B` correction; no acceptance from build-only evidence.
- Ordered Slice List:
  - P3-A: Real visible runtime verification and independent critique.
  - P3-B: Material correction and re-render/regression verification.

- [x] P3-A: Real visible runtime verification and independent critique.
  - Goal: render the latest app in visible Chrome, exercise the declared flows, capture evidence, and record critique across hierarchy, dense data, trust, accessibility, and functional completeness.
  - Scope Boundary:
    - Editable: reusable `playwright/log_c07_operations_workspace_flow.mjs` and QA report/evidence artifacts only; no product fixes in QA pass.
    - Inspect-only: latest product code and runtime.
    - Preserve-only: all data sources and real business state.
    - Out of scope: Docker, production, canonical financial mutation.
  - Non-Goals: no hidden/headless-only approval, no test patching during QA.
  - Pre-flight Questions:
    - Data source: real local runtime loaded through normal app path.
    - Display permission: local admin context as current runtime.
    - DB read flow: existing read path; record source mode.
    - DB write flow: must remain zero for declared read-only flow.
    - Render location: Dashboard shell and workdesk, plus Shipment 360 open/close.
    - UI behavior flow: load -> inspect -> search/filter -> no result/reset -> open row -> financial disclosure -> close/back -> second row.
    - Docker runtime: blocked; record exact missing capability.
    - Playwright target: visible Chrome at `http://127.0.0.1:8520/`.
    - Behavior test: reusable script and JSON/MD QA report.
    - Cleanup/quarantine: close browser/session; no data writes.
    - External side effects: none.
    - N/A notes: full product control sweep is out of scope; declare exact surfaces.
  - Work Steps:
    1. Run compile/build prerequisite and start fresh local Streamlit runtime; open visible Chrome through the user URL.
       - UI flow check: shell mounts and first viewport is captured.
       - DB/data flow check: source mode and write boundary recorded.
       - Render location check: visible Chrome, not direct source/test harness.
       - Mini QA: screenshot before any action.
       - Evidence target: `E3-P3A-RUNTIME1..E3-P3A-SHOT1`.
    2. Execute action ledger and capture screenshots after filter, no-results, reset, first row, explanation, close/back, and second row.
       - UI flow check: every declared action has expected/actual/verdict.
       - DB/data flow check: source labels/unknowns checked against projection fields.
       - Render location check: inspect layout, overflow, focus, and density in screenshots.
       - Mini QA: script output and visual inspection.
       - Evidence target: `E3-P3A-ACTION1..E3-P3A-CRITIQUE1`.
  - Implementation Gate:
    - Implementation slices are complete; fresh runtime is running; no QA code fix occurs in this slice.
  - Acceptance:
    - Source: current production source inspected.
    - Runtime/UI: declared flow is visibly exercised; screenshot evidence exists.
    - DB/data: no write observed; source-of-truth table is explicit.
    - Behavior test: report distinguishes pass/fail/blocked/unverified; Docker remains blocked.
    - Cleanup/quarantine: no persistent mutation.
    - Evidence IDs: `E3-P3A-RUNTIME1..E3-P3A-CRITIQUE1`.
    - Actual-status rows refreshed: material defects are listed before correction.
  - Evidence Targets: Playwright JSON/MD, screenshots, runtime log, action ledger, critique.
  - Actual-status Update: append R3 with critique findings and correction gates.
  - Commit Boundary: QA artifacts are not mixed into product implementation commit unless repo convention requires; product correction is a separate slice/commit.

- [x] P3-B: Material correction and re-render/regression verification.
  - Goal: fix only material defects found by the rendered critique, re-render, and verify regression paths.
  - Scope Boundary:
    - Editable: bounded product files identified by P3-A, likely `views/dashboard.py` or `views/web_app.py`; one separate correction commit.
    - Inspect-only: financial/historical core unless evidence proves an existing regression.
    - Preserve-only: ledger, database, Shipment 360 source-of-truth.
    - Out of scope: new design direction, unrelated cleanup, release.
  - Non-Goals: no endless polish loop; stop after the bounded correction loop or a genuine blocker.
  - Pre-flight Questions:
    - Data source: unchanged projection/read models.
    - Display permission: unchanged.
    - DB read flow: unchanged.
    - DB write flow: none.
    - Render location: exact defect location from screenshot/critique.
    - UI behavior flow: corrected path -> same declared action ledger.
    - Docker runtime: still unavailable.
    - Playwright target: same visible Chrome path after fresh restart.
    - Behavior test: focused tests + rerun of reusable flow.
    - Cleanup/quarantine: none.
    - External side effects: none.
    - N/A notes: if defects require data/architecture decisions, stop as BLOCKED instead of guessing.
  - Work Steps:
    1. Apply the smallest source correction tied to a critique finding, refresh Anvien, compile, and rerun focused tests.
       - UI flow check: defect is addressed without changing core action semantics.
       - DB/data flow check: write boundary remains zero.
       - Render location check: source line and screenshot finding map directly.
       - Mini QA: compile + focused tests before rerender.
       - Evidence target: `E3-P3B-FIX1..E3-P3B-TEST1`.
    2. Re-render the visible runtime and verify Dashboard -> Shipment 360 -> close/back plus financial/historical regressions.
       - UI flow check: corrected screenshot and flow output show no regression.
       - DB/data flow check: run read-only/source-of-truth and financial safety tests.
       - Render location check: compare before/after material defects and responsive viewport.
       - Mini QA: final visible screenshots and evidence report.
       - Evidence target: `E3-P3B-RENDER1..E3-P3B-REG1`.
  - Implementation Gate:
    - P3-A critique names a concrete source-backed material defect; otherwise mark P3-B N/A and do not invent a fix.
  - Acceptance:
    - Source: correction is minimal and traceable.
    - Runtime/UI: re-render closes material defect; no new visual/functional regression.
    - DB/data: financial/historical truth unchanged.
    - Behavior test: focused and regression tests pass; visible flow is rerun.
    - Cleanup/quarantine: no persistent data changed.
    - Evidence IDs: `E3-P3B-FIX1..E3-P3B-REG1`.
    - Actual-status rows refreshed: all declared bounded surfaces correct or explicitly blocked.
  - Evidence Targets: diff, Anvien detect-changes, tests, final screenshots/report.
  - Actual-status Update: append R4 and set final bounded status.
  - Commit Boundary: separate correction commit after verification.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently review source, runtime, evidence, financial/historical boundaries, and completion claim.
  - Work Steps: run supervisor review; if rejected, return only the failed scope to coder; rerun review until PASS or a genuine blocker is recorded.
  - Implementation Gate: all bounded slices are complete or explicitly blocked.
  - Acceptance: supervisor report has exactly one PASS/REJECT verdict and no unverified same-invariant surface is silently accepted.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only useful plan artifacts remain.
  - Work Steps: inspect new files/temp artifacts; preserve required screenshots/reports; remove only artifacts created by this plan that are obsolete; rerun supervisor review of cleanup.
  - Implementation Gate: no unrelated dirty-worktree files are touched.
  - Acceptance: plan artifacts are traceable and no dead product helper remains.
- [x] Pn-C: Close the plan.
  - Goal: record final evidence, benchmark, detect-changes, commit/worktree state, and release boundary.
  - Work Steps: run full local validation, record Docker blocker, run Anvien detect-changes, write coder/supervisor reports, and verify no release/deploy action occurred.
  - Implementation Gate: Pn-A/Pn-B pass or have explicit blocker evidence.
  - Acceptance: final status is bounded `PASS` or `BLOCKED` with release status `NOT_RELEASED`.

## Risk Notes

- `views/dashboard.py` is a high-risk dense file (130 symbols, 519 unresolved analyzer references); keep changes local to render helpers and preserve legacy sections.
- Streamlit reruns can reset/lose widget state; use stable keys and verify search/filter/open/close paths in the real runtime.
- Existing real data has many stale/overdue dates; surface this as operational reality, not a reason to rewrite data.
- Financial projections intentionally contain UNKNOWN/review states; do not turn them into zero or “paid”.
- Docker is unavailable; local visible runtime can prove interaction but not production artifact acceptance.
- Historical A Bò is terminally closed; any UI mention must remain partner/review context and never expose publish/cutover action.
