# LOG-C10 Documents & Review Queue Plan

## Metadata

- Date: `2026-08-16`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-actual-status.md`

## Goal

Build a compact, actionable Documents & Review Queue for Support and SALE Thành. The queue must be a deterministic read-model work surface: it shows what is missing, waiting, UNKNOWN, risky, or review-required; explains why; and opens the existing Shipment 360 / Entity Context workspaces without creating unsafe writers or changing canonical financial truth.

## Rules

- Complete P0 actual status before implementation work.
- Preserve the LOG-C07 Dashboard, LOG-C08 Shipment 360, and LOG-C09 Entity Context contracts.
- Use existing deterministic projections and source fields; do not add AI or fabricate completeness.
- Financial items are read-only signals only. Do not add debt, balance, payment, allocation, FX, or historical A Bò mutations.
- Reuse existing safe writers only; if no safe mutation exists, show a read-only item and next action.
- Update each checklist item immediately when completed and record evidence as work completes.
- Run Anvien change detection before any implementation-slice commit when implementation work was performed.
- For this local Streamlit app, validate the real visible runtime with reusable Playwright evidence. Docker is not available in the recovered environment, so no release claim may be made.
- Keep the current dirty worktree intact outside the bounded LOG-C10 files.

## Problem

The current Dashboard is shipment-first and the existing Shipment 360 / Entity Context workspaces are usable, but there is no dedicated work queue that turns deterministic operational, document, data-quality, and financial signals into a prioritized list of actionable work. A simple alert list would create noise, hide UNKNOWN semantics, and make it unclear where a Support or SALE user should act.

## Scope

- Add a pure `core/review_queue.py` projection that composes existing Dashboard, Shipment 360, Shipment Workspace, and source fields into review items.
- Add a `views/review_queue.py` compact queue workspace with search, category/status/severity and shipment/customer/factory/partner filters, reason, next action, evidence/source, and read-only state.
- Register the queue in the existing grouped navigation while preserving route permissions and session behavior.
- Wire queue items to the existing Dashboard/Shipment 360 detail flow and Entity Context flow, including a return-to-queue path.
- Show relevant review/document signals inside Shipment 360 using the existing workspace view without adding writers.
- Add focused behavior tests and reusable Playwright runtime evidence under repository conventions.
- Record critique and material corrections after real render.

## Non-Goals

- Full document-management platform, uploads, storage, approvals, or document CRUD.
- Full Finance Review redesign or any canonical financial mutation.
- Sales/Quotation, contract lifecycle, CEO reporting, or master-data CRUD redesign.
- Historical A Bò cutover/opening publication.
- AI, production deployment, Docker setup, or external communication.
- Broad legacy migration; only bounded identifier/source fixes that block queue navigation or resolution.

## Requirements

- Queue items are actionable and deduplicated by signal; every missing field is not automatically an alert.
- Deterministic priority is stable and explainable with severity, score, reason, and next action.
- Status vocabulary distinguishes `CRITICAL`, `NEEDS ATTENTION`, `WAITING`, `REVIEW`, and `INFO`.
- Document status distinguishes present, missing, waiting, UNKNOWN, and missing evidence without claiming completeness.
- UNKNOWN remains explicit and is never converted to zero or a resolved state.
- Each item carries shipment/customer/factory/partner context where source-bound, plus source/evidence references.
- Queue opening uses existing Shipment 360 / Entity Context navigation and can return without losing queue filters/context.
- No new database writer, resolve button, payment, allocation, FX, balance, debt, or historical publication path is introduced.

## Acceptance Criteria

1. Queue shows actionable work, not a duplicate Dashboard or noisy missing-field inventory.
2. Priority and status are deterministic and visually understandable without color alone.
3. Documents expose present/missing/waiting/UNKNOWN/evidence state and related entity context.
4. Queue → Shipment 360 → Review Queue and queue → Entity Context → related Shipment 360 → queue flows are reachable in the real runtime.
5. Shipment 360 exposes the same relevant review/document signals without duplicating the full queue.
6. Finance signals remain read-only, source-labelled, UNKNOWN-safe, and canonical.
7. Bounded legacy identifier issues blocking navigation are resolved without silent migration.
8. Real render evidence and a separate critique exist; material defects are corrected and re-rendered.
9. LOG-C07/C08/C09 focused regressions pass, with environment limitations reported honestly.

## Checklist

- [x] P0-A: Recover current state and complete actual status before implementation.
  - Goal: classify the existing Dashboard, Shipment 360, Entity Context, routing, data, safety boundaries, and validation environment.
  - Work Steps: inspect source and prior closure evidence; refresh Anvien; collect file-detail/impact summaries; classify queue as missing and existing surfaces as preserve-only or bounded-edit; update later phases from the evidence.
  - Implementation Gate: actual-status has evidence-backed rows and a final P0 decision.
  - Acceptance: no implementation starts before P0 is complete.

### P1: Deterministic review projection

- Phase Goal: create and test the pure actionable work model without database writes.
- Phase Boundary:
  - In scope: `core/review_queue.py`, focused tests, existing read-model imports and source aliases.
  - Out of scope: Streamlit rendering, navigation, writers, financial/history changes.
  - Dependencies: existing `core.shipment_dashboard`, `core.shipment_workspace`, and `core.shipment_360` contracts.
- Phase Implementation Rule: implement `P1-A`, verify and record it, then implement `P1-B`.
- Ordered Slice List:
  - P1-A: Build review-item projection and deterministic taxonomy.
  - P1-B: Add behavior tests for signals, priority, filtering, UNKNOWN, and immutability.

- [x] P1-A: Build review-item projection and deterministic taxonomy.
  - Goal: emit stable, source-bound actionable items for operational, document, data-quality, and financial signals.
  - Scope Boundary:
    - Editable: `core/review_queue.py`.
    - Inspect-only: `core/shipment_dashboard.py`, `core/shipment_workspace.py`, `core/shipment_360.py`, `core/database.py`.
    - Preserve-only: financial ledger and LOG-C06 historical surfaces.
    - Out of scope: Streamlit controls and mutations.
  - Non-Goals: infer document completeness, resolve legacy entities silently, or create a resolved state.
  - Pre-flight Questions:
    - Data source: shipment mappings plus existing deterministic read models.
    - Display permission: existing `dashboard` permission route; no new permission model.
    - DB read flow: existing `load_data`/session cache only.
    - DB write flow: N/A; projection is pure and read-only.
    - Render location: N/A until P2.
    - UI behavior flow: N/A until P2.
    - Docker runtime: unavailable in environment; record blocker.
    - Playwright target: N/A until P3.
    - Behavior test: pure in-memory fixture tests in P1-B.
    - Cleanup/quarantine: N/A; no persistence.
    - External side effects: none.
    - N/A notes: financial values are consumed only as status/source explanations.
  - Work Steps:
    1. Define the review-item contract, status/severity ordering, category taxonomy, and source/evidence fields.
       - UI flow check: N/A; contract must support compact table rendering and navigation targets.
       - DB/data flow check: verify no imports or calls to write helpers.
       - Render location check: N/A.
       - Evidence target: source review and Anvien impact evidence.
    2. Compose operational/document/data-quality/financial items from existing projections and explicit aliases, with stable IDs and deterministic sorting/filter helpers.
       - UI flow check: N/A; every item must expose a next action and destination target.
       - DB/data flow check: input shipments are not mutated; UNKNOWN and source provenance are preserved.
       - Render location check: N/A.
       - Evidence target: focused behavior tests and source diff.
  - Implementation Gate:
    - Before editing, Anvien file-detail/impact evidence for the existing projection consumers is recorded.
    - New module imports no repository or writer module.
  - Acceptance:
    - Source: contract and taxonomy are explicit and bounded.
    - Runtime/UI: N/A.
    - DB/data: pure input/output behavior and no writes.
    - Behavior test: covered by P1-B.
    - Cleanup/quarantine: N/A.
    - Evidence IDs: `E0-P0A-SRC1..E0-P0A-IMPACT4`, then P1 evidence.
    - Actual-status rows refreshed: review projection missing -> correct.
  - Evidence Targets: `core/review_queue.py` source, pure projection tests, diff review.
  - Actual-status Update: mark the projection `correct` only after focused tests pass.
  - Commit Boundary: commit after P1-A/P1-B acceptance if safe staging is possible; preserve unrelated dirty files.

- [x] P1-B: Add behavior tests for signals, priority, filtering, UNKNOWN, and immutability.
  - Goal: prove trigger -> projection -> observable review items for representative shipment fixtures.
  - Scope Boundary:
    - Editable: `tests/test_review_queue.py`.
    - Inspect-only: `core/review_queue.py` and existing projection tests.
    - Preserve-only: existing C07/C08/C09 tests.
    - Out of scope: UI snapshots and browser automation.
  - Non-Goals: test unsupported document or financial mutations.
  - Pre-flight Questions:
    - Data source: in-memory fixtures only.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: unittest-compatible focused tests.
    - Cleanup/quarantine: no persistent writes.
    - External side effects: none.
    - N/A notes: tests must not define fake completeness.
  - Work Steps:
    1. Create fixtures for missing factory/ready/weight, deadlines/free time, documents waiting/UNKNOWN/evidence missing, entity unresolved, and financial review/UNKNOWN.
       - UI flow check: N/A.
       - DB/data flow check: assert input fixture is unchanged.
       - Render location check: N/A.
       - Evidence target: test names and results.
    2. Assert deterministic ordering, category/status/severity filters, stable IDs, destination metadata, and empty/noise behavior.
       - UI flow check: N/A.
       - DB/data flow check: assert no financial writer or historical mutation is invoked.
       - Render location check: N/A.
       - Evidence target: focused test output.
  - Implementation Gate: P1-A source contract exists and imports cleanly.
  - Acceptance:
    - Source: tests cover the contract at behavior boundary.
    - Runtime/UI: N/A.
    - DB/data: immutability and read-only semantics proven.
    - Behavior test: focused suite passes.
    - Cleanup/quarantine: N/A.
    - Evidence IDs: `E1-P1B-TEST1..E1-P1B-SAFE1`.
    - Actual-status rows refreshed: projection and test status updated.
  - Evidence Targets: focused test output and failure-path assertions.
  - Actual-status Update: mark P1 complete and update P2 assumptions from the tested contract.
  - Commit Boundary: checkpoint after focused tests pass.

### P2: Queue workspace and integrations

- Phase Goal: expose the projection as a compact user workspace and connect it to existing contexts.
- Phase Boundary:
  - In scope: `views/review_queue.py`, `views/web_app.py`, bounded edits to `views/dashboard.py` and `views/shipment_360.py`.
  - Out of scope: changes to existing writers, core financial math, entity CRUD, or history.
  - Dependencies: P1 review-item contract and existing session navigation keys.
- Phase Implementation Rule: implement `P2-A`, then `P2-B`, and re-render after each material slice.
- Ordered Slice List:
  - P2-A: Render queue with filters, priority, reason, action, and explicit UNKNOWN/evidence semantics.
  - P2-B: Wire queue → Shipment 360 / Entity Context and return-to-queue context.

- [x] P2-A: Render queue with filters, priority, reason, action, and explicit UNKNOWN/evidence semantics.
  - Goal: provide a dense work queue instead of an alert-card wall or Dashboard duplicate.
  - Scope Boundary:
    - Editable: `views/review_queue.py`, route registration in `views/web_app.py`.
    - Inspect-only: existing read models and writers.
    - Preserve-only: Dashboard route body and financial controls unless a bounded navigation hook is required.
    - Out of scope: resolve buttons and full document management.
  - Non-Goals: add new persistence or invent uploaded evidence.
  - Pre-flight Questions:
    - Data source: session `db_shipments` loaded by existing state flow.
    - Display permission: `dashboard` permission.
    - DB read flow: session cache from `refresh_core_data`.
    - DB write flow: none.
    - Render location: grouped navigation route `Review Queue`.
    - UI behavior flow: search/filter/select/open read-only items.
    - Docker runtime: unavailable; local visible runtime evidence only.
    - Playwright target: local Streamlit app after build/start.
    - Behavior test: AppTest/import/compile support only; primary proof is visible runtime.
    - Cleanup/quarantine: no persistence.
    - External side effects: none.
    - N/A notes: use compact rows/table; no full entity duplication.
  - Work Steps:
    1. Add route metadata, queue header, summary counts, compact table/list, filters, and truthful empty state.
       - UI flow check: verify default queue, category/status/severity filters, entity filters, search, and UNKNOWN copy.
       - DB/data flow check: confirm only `load_data`/session read-model data is used.
       - Render location check: route is reachable from grouped sidebar and visually distinct from Dashboard.
       - Evidence target: real render screenshot and control ledger.
    2. Add progressive row detail for reason, next action, source/evidence, and navigation target without making each item a large card.
       - UI flow check: verify row density, no alert overload, no color-only priority, and empty/filter states.
       - DB/data flow check: finance explanation remains read-only and source-labelled.
       - Render location check: compact table remains usable at the target desktop viewport.
       - Evidence target: critique notes and corrected screenshot.
  - Implementation Gate: P1 contract is tested and no writer path is introduced.
  - Acceptance:
    - Source: route and renderer are bounded and read-only.
    - Runtime/UI: queue is reachable, understandable, and compact in visible runtime.
    - DB/data: values and status are source-bound; no mutation.
    - Behavior test: focused projection tests remain passing.
    - Cleanup/quarantine: N/A.
    - Evidence IDs: `E2-P2A-RENDER1..E2-P2A-CRIT1`.
    - Actual-status rows refreshed: route missing -> correct; queue workspace missing -> correct.
  - Evidence Targets: local runtime screenshot/JSON/MD under `reports/QA/playwright/`.
  - Actual-status Update: record visual defects before correction; do not claim PASS from source-only evidence.
  - Commit Boundary: checkpoint after route/render smoke passes.

- [x] P2-B: Wire queue → Shipment 360 / Entity Context and return-to-queue context.
  - Goal: preserve user context across queue, shipment, and entity workspaces.
  - Scope Boundary:
    - Editable: bounded navigation hooks in `views/review_queue.py`, `views/dashboard.py`, `views/entity_context.py`, `views/shipment_360.py` only if needed.
    - Inspect-only: `views/shipment.py` writer form and existing entity master route.
    - Preserve-only: `core/financial_ledger.py`, `core/database.py`, historical/A Bò.
    - Out of scope: new resolve/mutation controls.
  - Non-Goals: duplicate full entity data in each queue item.
  - Pre-flight Questions:
    - Data source: item target metadata and existing active shipment/entity session keys.
    - Display permission: existing route permissions.
    - DB read flow: existing dashboard/entity context loaders.
    - DB write flow: none.
    - Render location: existing Shipment 360 and Entity Context workspaces.
    - UI behavior flow: queue -> destination -> related shipment -> return queue.
    - Docker runtime: unavailable; report as environment limitation.
    - Playwright target: local visible app.
    - Behavior test: reusable Playwright flow and focused regression tests.
    - Cleanup/quarantine: no persistence.
    - External side effects: none.
    - N/A notes: legacy IDs are normalized only for navigation lookup, with provenance retained.
  - Work Steps:
    1. Set and consume a return context when opening shipment/entity targets; preserve search/filter selections through rerun/back.
       - UI flow check: verify queue → Shipment 360 → close/back → same queue context.
       - DB/data flow check: verify mapping-key/id lookup does not mutate source records.
       - Render location check: show a clear back affordance and relevant review/document issues in Shipment 360.
       - Evidence target: browser action ledger and screenshots.
    2. Verify entity links and related Shipment 360 navigation with UNKNOWN/legacy identifier cases.
       - UI flow check: verify customer/factory/partner targets and return path.
       - DB/data flow check: verify unresolved mapping remains UNKNOWN rather than silently inferred.
       - Render location check: entity context remains separate from queue row content.
       - Evidence target: regression test and visible flow evidence.
  - Implementation Gate: queue route renders with stable item targets and existing navigation functions are understood.
  - Acceptance:
    - Source: only bounded session/navigation edits.
    - Runtime/UI: all required flows are reachable and return context is preserved.
    - DB/data: no new writer, financial mutation, or migration.
    - Behavior test: Playwright flow covers action -> destination -> return.
    - Cleanup/quarantine: N/A.
    - Evidence IDs: `E2-P2B-NAV1..E2-P2B-SAFE1`.
    - Actual-status rows refreshed: integrations correct or blockers explicit.
  - Evidence Targets: screenshots, JSON/MD action ledger, focused regression output.
  - Actual-status Update: record legacy-ID/source-contract status and any bounded correction.
  - Commit Boundary: checkpoint after navigation flow passes.

### P3: Real render, critique, correction, regression, and closure

- Phase Goal: run the actual Streamlit app, critique the visible queue, correct material defects, and close with evidence.
- Phase Boundary:
  - In scope: local runtime build/start, Playwright screenshots/reports, focused/full tests, Anvien detect-changes, supervisor report.
  - Out of scope: Docker/deploy/release and unrelated dirty worktree cleanup.
  - Dependencies: P2 route and navigation slices.
- Phase Implementation Rule: render, critique, correct, re-render, then run final regressions.

- [x] P3-A: Execute real user flows and capture render evidence.
  - Goal: prove the visible app, not just source or tests.
  - Work Steps: run full available build/compile checks; start Streamlit; use reusable Playwright script; capture queue default/filter/empty/open/back/entity states; inspect screenshots.
  - Implementation Gate: app starts and route is visible.
  - Acceptance: evidence records runtime command, URL, controls, screenshots, and any blocked Docker/pytest limitation.

- [x] P3-B: Critique and correct material defects.
  - Goal: remove alert overload, unclear priority, excess columns, weak next action, Dashboard duplication, hidden UNKNOWN, misleading document status, unexplained finance warning, broken navigation, and confusing empty state.
  - Work Steps: record each finding with severity/classification; patch only material in-scope defects; re-render and inspect again.
  - Implementation Gate: critique is based on the real rendered screen.
  - Acceptance: material findings are corrected or explicitly blocked with evidence; corrected screenshots exist.

- [x] P3-C: Run regressions, detect changes, update ledgers, and prepare supervisor review.
  - Goal: close LOG-C10 with honest evidence and no release claim.
  - Work Steps: run compile/unittest/focused tests; run existing C07/C08/C09 tests; run `anvien detect-changes --repo Logistics-Pro-AI --scope all`; update evidence/benchmark/actual status; write coder and supervisor reports if required by the workflow.
  - Implementation Gate: no unresolved same-invariant runtime blocker remains.
  - Acceptance: evidence and status are current, release remains `NOT_RELEASED` if Docker/deploy is unavailable, and owner decision is explicit.

## Risk Notes

- `views/dashboard.py`, `views/web_app.py`, and `views/shipment_360.py` are high-risk files with existing dirty-worktree changes. Patch narrowly and do not normalize unrelated encoding or legacy UI.
- Existing data is heterogeneous and may contain `id`/`shipment_id` mismatches. Keep both source identifiers and use bounded fallback lookup only for navigation.
- Document registries are partial. Show source status and UNKNOWN; never infer “complete”.
- Financial projections can be UNKNOWN/review-required. Explain the read model and source, never write or aggregate new balances.
- Docker and pytest are known environment limitations from LOG-C07/C08/C09; local visible evidence can prove bounded product behavior but cannot become a release claim.
