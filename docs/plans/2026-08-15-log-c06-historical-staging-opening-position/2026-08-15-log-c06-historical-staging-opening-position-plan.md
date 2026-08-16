# LOG-C06 Historical A Bo Staging and Opening Position Plan

## Metadata

- Date: `2026-08-15`
- Status: `complete-bounded-local`
- Plan: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-actual-status.md`

## Goal

Build a safe bridge from the historical A Bo workbook to a reviewable, deterministic
staging model and a draft opening position for SALE Thanh. Preserve the workbook as
evidence, keep raw values separate from proposals, require explicit confirmation before
any historical row contributes to a draft, keep currencies separate, and stop at
cutover readiness. No historical row may create a canonical financial effect.

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
- Hidden fallbacks are forbidden. Missing workbook, unavailable database, unknown currency, or ambiguous ownership must be visible and truthful.
- Raw workbook evidence is immutable in the application model. Normalized proposals and review history are separate metadata.
- Only `CONFIRMED` staging mappings may contribute to opening-position or cutover calculations.
- No AI, current-rate FX recalculation, payment execution, Quick Entry, live migration, ledger mutation, or owner inference from arbitrary text.
- Preserve all unrelated dirty-worktree changes; no reset, checkout, broad staging, or destructive cleanup.
- Every implementation phase is decomposed into narrow slices; do not implement a phase directly.

## Problem

LOG-C02 through LOG-C05 provide a canonical ledger and a read-only A Bo / SALE Thanh
desk, but the historical workbook is still a competing, unnormalized source of truth.
The workbook mixes sales, partner-held money, received-on-behalf, paid-on-behalf,
customer receipts, FX context, accumulated checkpoints, and free-form notes. A direct
migration would invent owner mappings and create two financial truths. LOG-C06 needs a
provenance-preserving staging layer, deterministic proposals, a human review queue, and
an explainable draft opening position without publishing anything live.

## Scope

- Read-only `.xls` import from the existing workbook path or a safely discovered equivalent.
- Raw source provenance for every non-empty source row, including file hash, sheet, row, cell range, raw cells, date context, parser version, and import time.
- Deterministic normalization proposals for SALE owner, party roles, customer, event type, currency, FX context, anomalies, and candidate allocation.
- Simple staging states: `RAW`, `PROPOSED`, `CONFIRMED`, `REVIEW_REQUIRED`, and `REJECTED`/`NOT_APPLICABLE`.
- Separate per-currency draft opening position and cutover-draft explanation from confirmed mappings only.
- Retry-safe staging persistence and review audit metadata in a staging-only collection boundary when a database is available.
- Bounded Historical Review UI reachable from the existing A Bo desk, with search, source evidence, review actions, draft opening position, and trace explanations.
- Isolated fixtures, golden historical-item tests, checkpoint reconciliation tests, canonical-write oracle, regression tests, and reusable browser evidence.

## Non-Goals

- Automatic insertion into `financial_obligations`, `financial_transactions`, `financial_allocations`, `financial_corrections`, shipments, payments, or any other canonical financial collection.
- Automatic publication of an opening balance, approval/live status, owner approval workflow, or cutover execution.
- Quick Entry, payment execution, bank integration, current FX conversion, accounting GL, double-entry, or full historical reconstruction.
- AI/LLM classification or external connectors.
- Redesign of Dashboard, A Bo desk, or existing LOG-C02 through LOG-C05 financial UI.
- Modification of the source workbook or creation of a replacement workbook.
- Docker setup or unrelated dirty-worktree repair.

## Requirements

- Every staged source item keeps raw values and normalized proposals in separate fields.
- Explicit `SALE=Thanh` may produce a high-confidence proposal; arbitrary text containing Thanh never proves ownership.
- A blank SALE plus `mon cua Thanh` or similar text is `REVIEW_REQUIRED`.
- Other explicit sales remain separate from SALE Thanh.
- Unknown currency remains `UNKNOWN`/review and is never silently converted.
- Documented VND/USD to CNY context preserves both source amount/currency and related conversion details without using current rates.
- Event proposals can represent payable to A Bo, payment to A Bo, held credit, received-on-behalf, paid-on-behalf, customer receipt, refund/return credit, FX context, adjustment, unallocated, and unknown without forcing every row.
- Golden items 24,576, 62,464, 1,687, 1,572, 25,025, and 134,973 remain traceable to source rows; the 134,973 checkpoint remains traceable to components rather than an opaque total.
- Date sequence, inherited/merged date context, missing currency/SALE/party, duplicate-looking rows, broken accumulation references, unclear unit, and inconsistent SALE/customer linkage are surfaced as flags.
- Review actions write only staging metadata, record actor/time/reason, preserve prior history, and retry without duplicate effects.
- Opening position buckets are currency-separated and include payable, held/credit, received-on-behalf available, paid-on-behalf/settled context, unallocated, restricted, and unresolved excluded amounts.
- Cutover drafts are reproducible, source-referenced, hash/versioned, and limited to `DRAFT`, `READY_FOR_OWNER_REVIEW`, or `SUPERSEDED`.

## Acceptance Criteria

- The source hash before and after staging is identical.
- The full workbook can be represented in staging without changing raw source evidence.
- Explicit SALE and ambiguous-note rules behave deterministically.
- Confirmed, review-required, other-sale, and anomaly counts are visible.
- Search finds 62464, 1687, 1572, and 25025 with source row/cell evidence.
- Currency buckets never combine CNY, USD, and VND.
- Confirmed mappings change the draft opening position; `PROPOSED`, `REVIEW_REQUIRED`, `UNKNOWN`, and checkpoint totals do not.
- “Why did opening position become this?” lists the exact staged source IDs/rows and calculation components.
- Review confirmation/correction changes staging metadata only and is idempotent.
- Canonical financial collections and LOG-C02 through LOG-C05 behavior remain unchanged.
- Local Streamlit runtime, browser journey, console capture, compileall, focused tests, full tests, and change detection are recorded; Docker is separately reported as unavailable if no target exists.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state for the workbook, staging boundary, review route, canonical ledger, and validation surfaces.
  - Work Steps: inspect the dirty worktree; run P2P inspection; refresh Anvien; fingerprint the source workbook; inspect existing C02-C05 routes, models, tests, and write oracles; classify each target and update later phase assumptions.
  - Implementation Gate: `2026-08-15-log-c06-historical-staging-opening-position-actual-status.md` contains evidence-backed rows and a P0 decision.
  - Acceptance: source status, relationship counts, blast-radius warnings, preserve-only boundaries, missing surfaces, and next actions are explicit.

### P1: Deterministic staging and normalization

- Phase Goal: represent the workbook as immutable raw evidence with controlled proposals and anomaly flags.
- Phase Boundary:
  - In scope: `core/historical_staging.py`, deterministic `.xls` parsing, provenance, proposals, anomaly flags, source lookup, and pure fixture behavior.
  - Out of scope: Mongo writes, Streamlit rendering, canonical ledger, Quick Entry, and owner approval.
  - Dependencies: P0 actual status and the existing `xlrd>=2.0` runtime dependency.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Raw workbook reader and deterministic proposal engine.
  - P1-B: Golden fixtures, anomalies, and source-fingerprint regression.

- [x] P1-A: Raw workbook reader and deterministic proposal engine
  - Goal: create the pure staging model that preserves raw workbook evidence and produces separate deterministic proposals.
  - Scope Boundary:
    - Editable: new `core/historical_staging.py` and its direct pure tests.
    - Inspect-only: `core/excel_utils.py`, `core/getfly_reader.py`, existing canonical ledger modules, source workbook.
    - Preserve-only: `core/financial_ledger.py`, `core/reconciliation.py`, all LOG-C02-C05 source modules.
    - Out of scope: database writes and UI.
  - Non-Goals: no AI, no arbitrary-text owner inference, no raw-value overwrite, no canonical financial calls.
  - Pre-flight Questions:
    - Data source: `D:\Copy of TOYS-2025 - Copy.xls` or a safely discovered same-named workbook; read-only.
    - Display permission: N/A for pure model; UI consumes the model in P2.
    - DB read flow: N/A; pure parser accepts a path/fixture.
    - DB write flow: N/A; persistence is P2-A.
    - Render location: N/A; review renderer is P2-B.
    - UI behavior flow: N/A; pure behavior tests prove source row -> proposal.
    - Docker runtime: no target exists in baseline; record limitation.
    - Playwright target: N/A for pure slice.
    - Behavior test: parse source rows and assert raw/proposal separation, explicit/ambiguous SALE rules, currency context, and no ledger imports.
    - Cleanup/quarantine: tests use in-memory fixtures and do not write external state.
    - External side effects: none.
    - N/A notes: no database or browser is intentionally touched by this slice.
  - Work Steps:
    1. Define serializable staging item fields, parser version, source hash, deterministic source ID, raw cell map, raw date/inherited date context, and separate proposal/review fields.
       - UI flow check: N/A; expose stable fields for the later review table.
       - DB/data flow check: source file read -> immutable item object; no canonical collection access.
       - Render location check: N/A; record field contract for P2-B.
       - Mini QA for each completed implementation slice (MUST): run pure behavior tests and compile the new module; browser is N/A because no UI changed.
       - Evidence target: `E1-P1A-MODEL1`, `E1-P1A-GRAPH1`.
    2. Implement controlled field/header/date/currency/event parsing, explicit SALE normalization, review reasons, and anomaly flags without changing raw values.
       - UI flow check: N/A; proposal state and reasons must be display-ready.
       - DB/data flow check: deterministic same source hash/row produces the same source ID and proposal.
       - Render location check: N/A; source sheet/row/cells must be traceable later.
       - Mini QA for each completed implementation slice (MUST): run golden unit tests for explicit SALE, blank SALE note, other sale, unknown currency, inherited date, and FX context.
       - Evidence target: `E1-P1A-RULES1`, `E1-P1A-ORACLE1`.
  - Implementation Gate:
    - Before editing target files, Anvien P0 evidence is recorded; new file has no prior impact surface, and preserve-only high-risk files are not edited.
    - The parser must not import Streamlit, database, financial ledger, payment, AI, or current-rate FX modules.
  - Acceptance:
    - Source: every non-empty row is representable with source file/hash/sheet/row/cells/raw values and parser version.
    - Runtime/UI: N/A for pure slice.
    - DB/data: no DB or canonical ledger call is reachable from the parser.
    - Behavior test: required SALE, currency, raw/proposal, and event-type rules pass.
    - Cleanup/quarantine: no persistent fixture data remains outside test memory.
    - Evidence IDs: `E1-P1A-MODEL1`, `E1-P1A-RULES1`, `E1-P1A-ORACLE1`.
    - Actual-status rows refreshed: staging model, parser, source boundary.
  - Evidence Targets: parser symbols, import graph, pure behavior tests, and source hash comparison.
  - Actual-status Update: mark the pure staging model `missing -> correct` for its implemented contract; keep persistence/UI `missing`.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: `core/historical_staging.py` now reads the workbook read-only,
    preserves raw cells/provenance, and emits deterministic proposals without UI,
    database, canonical-ledger, payment, AI, or current-rate imports. The focused
    smoke parse completed before the P1-B test slice.

- [x] P1-B: Golden fixtures, anomalies, and source-fingerprint regression
  - Goal: prove the historical workbook targets and anomaly semantics against isolated copies/fixtures.
  - Scope Boundary:
    - Editable: new `tests/test_historical_staging.py` and, only if needed, pure parser helpers from P1-A.
    - Inspect-only: original workbook and existing LOG-C02-C05 tests.
    - Preserve-only: canonical data and source workbook.
    - Out of scope: review action persistence and browser UI.
  - Non-Goals: no production truth hard-coded from golden examples; fixtures must retain source row/cell identity.
  - Pre-flight Questions:
    - Data source: isolated fixture rows derived from observed workbook rows; source workbook read-only hash check.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A; tests are the behavior boundary.
    - Docker runtime: N/A for pure tests; final limitation recorded.
    - Playwright target: N/A.
    - Behavior test: golden amounts, checkpoint component traceability, anomaly flags, and source unchanged.
    - Cleanup/quarantine: no external writes; copied fixture bytes remain in memory or repo-local `.tmp` only if needed.
    - External side effects: none.
    - N/A notes: source hash is measured before/after, never changed.
  - Work Steps:
    1. Add isolated rows for 24,576, 62,464, 1,687, 1,572, 25,025, 134,973, and the 134,973 component group with exact source references.
       - UI flow check: N/A.
       - DB/data flow check: fixture row -> staged item -> proposal/status; checkpoint total cannot become a component automatically.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run the direct test file and inspect failure output.
       - Evidence target: `E1-P1B-GOLD1`, `E1-P1B-TRACE1`.
    2. Add date-order, missing-date inheritance, duplicate-looking, missing currency/SALE/party, unclear amount, broken checkpoint, and inconsistent linkage assertions plus source hash before/after.
       - UI flow check: N/A.
       - DB/data flow check: anomalies are flags/review reasons; no row is deleted or auto-corrected.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): run focused matrix and compileall.
       - Evidence target: `E1-P1B-ANOMALY1`, `E1-P1B-HASH1`.
  - Implementation Gate:
    - P1-A behavior is passing and actual-status has been refreshed before fixture edits.
    - Tests must prove observable parser results, not just static field presence.
  - Acceptance:
    - Source: golden items locate exact source rows/cells and source hash remains identical.
    - Runtime/UI: N/A.
    - DB/data: no canonical collection is touched.
    - Behavior test: golden and anomaly matrix passes.
    - Cleanup/quarantine: fixture data is isolated and not loaded by the app as live data.
    - Evidence IDs: `E1-P1B-GOLD1`, `E1-P1B-TRACE1`, `E1-P1B-ANOMALY1`, `E1-P1B-HASH1`.
    - Actual-status rows refreshed: golden source coverage and anomaly coverage.
  - Evidence Targets: focused test output, source fingerprint, and deterministic source ID samples.
  - Actual-status Update: mark golden/anomaly fixture coverage `missing -> correct`; keep review/persistence/UI `missing`.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: `tests/test_historical_staging.py` passes 11 focused tests. The
    six golden Sheet2 rows, checkpoint separation, explicit/ambiguous SALE rules,
    currency/FX context, anomaly flags, and unchanged source hash are covered.

### P2: Staging persistence, review actions, and draft cutover model

- Phase Goal: persist only staging metadata/review history and derive a reproducible opening-position/cutover draft from confirmed items.
- Phase Boundary:
  - In scope: staging-only Mongo boundary or session fallback, review audit/retry semantics, pure opening-position/cutover functions.
  - Out of scope: canonical ledger writes, owner approval/live publication, and full UI rendering.
  - Dependencies: P1 parser and fixtures.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P2-B`.
- Ordered Slice List:
  - P2-A: Staging-only persistence and review action safety.
  - P2-B: Confirmed opening position, checkpoint reconciliation, and cutover draft.

- [x] P2-A: Staging-only persistence and review action safety
  - Goal: make staging/review metadata durable and retry-safe without touching financial collections.
  - Scope Boundary:
    - Editable: new `core/historical_staging_store.py` and `tests/test_historical_staging_store.py`.
    - Inspect-only: `core/database.py` and existing financial write safety modules.
    - Preserve-only: `financial_obligations`, `financial_transactions`, allocations, corrections, shipments, and C02-C05 writers.
    - Out of scope: UI action wiring and cutover calculation.
  - Non-Goals: no transaction/payment/ledger writes; no overwriting raw values or prior confirmed history.
  - Pre-flight Questions:
    - Data source: staged documents from P1.
    - Display permission: N/A; persistence contract feeds P2-B.
    - DB read flow: read only `legacy_historical_staging` and `legacy_historical_review_actions` when DB exists.
    - DB write flow: explicit staging import/review action -> staging collections only; session fallback if DB unavailable.
    - Render location: N/A; UI is P3.
    - UI behavior flow: N/A; write oracle uses fake DB and observable collection deltas.
    - Docker runtime: no target in baseline; record limitation.
    - Playwright target: N/A.
    - Behavior test: import idempotency, review confirm/correct/unknown, retry, prior-history preservation, and canonical write count zero.
    - Cleanup/quarantine: fake collections per test; optional isolated Mongo tests remain opt-in and clean their own fixture namespace.
    - External side effects: staging collection writes are the only authorized persistence side effect.
    - N/A notes: approval/live statuses are forbidden.
  - Work Steps:
    1. Add deterministic staging collection/index boundary and upsert import semantics keyed by source hash/sheet/row without replacing raw/provenance fields.
       - UI flow check: N/A; expose load/read APIs for P3.
       - DB/data flow check: import -> staging-only collection; assert financial collections unchanged.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): fake-DB import/retry test and compileall.
       - Evidence target: `E2-P2A-STORE1`, `E2-P2A-WRITE1`.
    2. Add explicit review action transitions, request identity, actor/time/reason history, correction semantics, and idempotent retries.
       - UI flow check: N/A; action result must be renderable as status/history.
       - DB/data flow check: action -> one metadata update/audit record; conflicting retry fails closed.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): confirm/retry/correct/not-Thanh/unknown tests and canonical write oracle.
       - Evidence target: `E2-P2A-REVIEW1`, `E2-P2A-ORACLE1`.
  - Implementation Gate:
    - Run Anvien impact/file-detail on any existing function touched; no financial module edits are allowed unless a proven import contract requires them.
    - The fake DB must make canonical collection writes observable and fail the test if called.
  - Acceptance:
    - Source: raw source/proposal/history fields survive import and correction.
    - Runtime/UI: N/A.
    - DB/data: only staging/audit collections change; retries do not duplicate.
    - Behavior test: all review transitions and write oracle pass.
    - Cleanup/quarantine: test DB state is isolated and cleaned/quarantined.
    - Evidence IDs: `E2-P2A-STORE1`, `E2-P2A-REVIEW1`, `E2-P2A-ORACLE1`.
    - Actual-status rows refreshed: persistence boundary, review safety, canonical write boundary.
  - Evidence Targets: collection delta snapshots, idempotency results, and status-history trace.
  - Actual-status Update: mark staging persistence/review safety `missing -> correct`; keep UI `missing`.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: staging/audit persistence is isolated in `legacy_historical_staging`
    and `legacy_historical_review_actions`; import retry, review history, actor/time/
    reason, correction allowlists, idempotent request IDs, and optimistic review-version
    conflicts are covered by the fake-DB write oracle. No canonical provider is imported.

- [x] P2-B: Confirmed opening position, checkpoint reconciliation, and cutover draft
  - Goal: derive separate per-currency opening components and a reproducible cutover draft from `CONFIRMED` staged mappings only.
  - Scope Boundary:
    - Editable: new pure `core/historical_opening.py` and `tests/test_historical_opening.py`.
    - Inspect-only: canonical ledger projections and C05 debit snapshot model.
    - Preserve-only: all live financial records and approval paths.
    - Out of scope: UI rendering and live publication.
  - Non-Goals: no single opaque plus/minus total and no sign-based debit/credit inference.
  - Pre-flight Questions:
    - Data source: confirmed staged items and preserved checkpoint evidence.
    - Display permission: N/A.
    - DB read flow: function accepts staged items; no canonical read is required.
    - DB write flow: N/A; cutover draft is pure/reproducible in this slice.
    - Render location: P3-B review desk.
    - UI behavior flow: N/A; tests prove confirmed/review exclusion and source trace.
    - Docker runtime: final runtime limitation only.
    - Playwright target: N/A.
    - Behavior test: per-currency buckets, checkpoint match/difference/unknown, hash/version reproducibility, unresolved exclusion.
    - Cleanup/quarantine: in-memory only.
    - External side effects: none.
    - N/A notes: status cannot be APPROVED or LIVE.
  - Work Steps:
    1. Implement bucket calculation and deterministic explanations for payable, held/credit, received-on-behalf available, paid-on-behalf/settled, unallocated, restricted, and unresolved excluded amounts.
       - UI flow check: N/A; return business labels and source IDs.
       - DB/data flow check: only confirmed rows enter totals; status/currency gates are explicit.
       - Render location check: N/A.
       - Mini QA for each completed implementation slice (MUST): pure arithmetic and exclusion tests across CNY/USD/VND/UNKNOWN.
       - Evidence target: `E2-P2B-POSITION1`, `E2-P2B-CURRENCY1`.
    2. Implement checkpoint reconciliation and `CUTOVER_DRAFT` with source IDs, excluded/review IDs, unresolved amount, generated metadata, snapshot hash/version, and allowed statuses.
       - UI flow check: N/A.
       - DB/data flow check: no live effect; same confirmed snapshot produces same hash.
       - Render location check: P3-B explanation panel.
       - Mini QA for each completed implementation slice (MUST): exact match, difference, unknown semantics, regeneration, and no APPROVED/LIVE tests.
       - Evidence target: `E2-P2B-CHECKPOINT1`, `E2-P2B-CUTOVER1`.
  - Implementation Gate:
    - P2-A write oracle passes and actual-status confirms canonical financial collections are untouched.
    - All arithmetic is explicit per currency; negative sign never determines business direction by itself.
  - Acceptance:
    - Source: confirmed source IDs fully explain included components; excluded/review IDs remain separate.
    - Runtime/UI: N/A.
    - DB/data: no canonical writes; cutover draft is not approval/live.
    - Behavior test: bucket, currency, checkpoint, and reproducibility matrix passes.
    - Cleanup/quarantine: no persistent live fixture.
    - Evidence IDs: `E2-P2B-POSITION1`, `E2-P2B-CURRENCY1`, `E2-P2B-CHECKPOINT1`, `E2-P2B-CUTOVER1`.
    - Actual-status rows refreshed: opening position and cutover draft.
  - Evidence Targets: calculation payloads, formulas, source references, hashes, and exclusion counts.
  - Actual-status Update: mark pure opening position/cutover model `missing -> correct`; keep owner approval/live publication `blocked/out of scope`.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: `core/historical_opening.py` and its pure test matrix now keep
    confirmed components separated by CNY/USD/VND, exclude unknown/review/checkpoint
    rows with source traces, reconcile only explicit checkpoint links/formulas, and
    produce reproducible non-live `CUTOVER_DRAFT` payloads with `READY`/`NOT_READY`.

### P3: Historical Review desk and integration

- Phase Goal: expose a bounded, beginner-friendly review UI from the existing A Bò desk without redesigning approved C02-C05 surfaces.
- Phase Boundary:
  - In scope: new `views/historical_review.py`, minimal partner-desk entry control, review/search/source evidence/draft panels, and UI write oracle.
  - Out of scope: Dashboard redesign, canonical writes, Quick Entry, and live publication.
  - Dependencies: P1/P2 contracts and local Streamlit runtime.
- Phase Implementation Rule: do not implement `P3` directly. Implement `P3-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P3-B`.
- Ordered Slice List:
  - P3-A: Mounted Historical Review states and staging/review controls.
  - P3-B: Draft opening explanation, cutover readiness, and browser journey.

- [x] P3-A: Mounted Historical Review states and staging/review controls
  - Goal: add a bounded review inbox reachable from A Bò / SALE Thanh and show truthful staged data, proposals, anomalies, and safe review actions.
  - Scope Boundary:
    - Editable: new `views/historical_review.py`, minimal `_mode_navigation`/desk wiring in `views/partner_reconciliation.py`, direct UI oracle tests.
    - Inspect-only: `views/web_app.py` route registry and Dashboard.
    - Preserve-only: existing C04/C05 report/debit modes, canonical projection, existing navigation order.
    - Out of scope: new global route and financial mutations.
  - Non-Goals: no spreadsheet clone, no accounting terminology, no arbitrary owner inference, no approval button.
  - Pre-flight Questions:
    - Data source: staged model from P1/P2; session fallback is visibly labelled when Mongo is unavailable.
    - Display permission: existing `receivables` permission through the A Bò desk.
    - DB read flow: staging collection only; no canonical financial read required for historical review.
    - DB write flow: explicit staging import/review action only.
    - Render location: existing A Bò desk state route -> Historical Review view.
    - UI behavior flow: click Historical Review -> summary -> search -> source evidence -> review action -> rerender.
    - Docker runtime: no target in baseline; host Streamlit evidence only if Docker remains unavailable.
    - Playwright target: local Streamlit built/current runtime with reusable script under `playwright/`.
    - Behavior test: recorder/fake-Streamlit proves route and write oracle.
    - Cleanup/quarantine: UI tests use in-memory staging and no external writes.
    - External side effects: only explicit staging metadata action.
    - N/A notes: no Dashboard route change.
  - Work Steps:
    1. Add Historical Review navigation and truthful summary sections for confirmed/high-confidence, needs review, other sales, and anomalies.
       - UI flow check: A Bò desk -> Historical Review; C04/C05 controls remain reachable on return.
       - DB/data flow check: read staged/session data only; empty/unavailable source is visible.
       - Render location check: new review view, no Dashboard redesign.
       - Mini QA for each completed implementation slice (MUST): fake Streamlit render oracle and local route smoke.
       - Evidence target: `E3-P3A-UI1`, `E3-P3A-ORACLE1`.
    2. Add bounded search, source-row/cell evidence display, and safe review actions with simple Vietnamese business labels.
       - UI flow check: search 62464/1572; open evidence; confirm/correct/not-Thanh/unknown; rerender status.
       - DB/data flow check: action uses staging boundary only; prior history and raw values remain.
       - Render location check: review item cards/table and evidence expander.
       - Mini QA for each completed implementation slice (MUST): recorder test observes status change and zero canonical financial calls.
       - Evidence target: `E3-P3A-REVIEW1`, `E3-P3A-WRITE1`.
  - Implementation Gate:
    - Run Anvien file-detail/impact for `views/partner_reconciliation.py`; high/critical blast radius is documented and edits remain limited to navigation.
    - UI tests must patch all financial writers and fail on any call.
  - Acceptance:
    - Source: review item displays exact source file/sheet/row/cells and raw note.
    - Runtime/UI: Historical Review is reachable from A Bò desk; C04/C05 route remains intact.
    - DB/data: review writes only staging metadata.
    - Behavior test: summary/search/source/action flow passes.
    - Cleanup/quarantine: no external DB fixture survives UI test.
    - Evidence IDs: `E3-P3A-UI1`, `E3-P3A-REVIEW1`, `E3-P3A-WRITE1`.
    - Actual-status rows refreshed: review UI, route integration, write oracle.
  - Evidence Targets: UI recorder, focused C04/C05 regression, and source evidence screenshots.
  - Actual-status Update: mark Historical Review UI `missing -> correct`; preserve C04/C05 `correct`.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: `views/historical_review.py` is mounted by the existing A Bò desk
    through one navigation seam. It shows staging provenance, summary/review inbox,
    source evidence, and staging-only actions; the session-only fallback is visible and
    no canonical projection is evaluated for the Historical Review mode.

- [x] P3-B: Draft opening explanation, cutover readiness, and browser journey
  - Goal: show the per-currency draft opening position, “Vì sao opening position ra số này?”, cutover readiness, and complete the reusable local browser flow.
  - Scope Boundary:
    - Editable: `views/historical_review.py`, `playwright/log_c06_historical_review_flow.mjs`, official QA artifacts, direct UI tests, plan evidence.
    - Inspect-only: C02-C05 views/tests and source workbook.
    - Preserve-only: canonical ledger and existing financial UI.
    - Out of scope: owner approval/live opening bridge and Quick Entry.
  - Non-Goals: do not display one opaque total or claim production/container readiness without a Docker target.
  - Pre-flight Questions:
    - Data source: confirmed staged mappings and pure cutover draft.
    - Display permission: existing A Bò desk permission.
    - DB read flow: staging metadata plus pure draft inputs; no canonical writes.
    - DB write flow: optional staging review metadata only; draft generation is read/pure.
    - Render location: Historical Review page.
    - UI behavior flow: open review -> search 62464 -> source evidence -> inspect 1572 -> confirm safe item -> draft changes only after confirmation -> explanation -> return to C04/C05 desk.
    - Docker runtime: attempt full build; if no executable/target, record blocker and do not substitute as container evidence.
    - Playwright target: actual local Streamlit runtime; record URL, command, screenshots, console/page errors, and limitation.
    - Behavior test: browser flow plus UI write oracle and regression suite.
    - Cleanup/quarantine: browser uses local/session fixture; no live canonical inserts.
    - External side effects: none beyond explicit staging review action.
    - N/A notes: owner approval remains a final user decision.
  - Work Steps:
    1. Render per-currency buckets, unresolved exclusion, checkpoint comparison, and exact source trace for the draft opening position.
       - UI flow check: confirmed item changes draft; review/unknown item does not.
       - DB/data flow check: draft snapshot hash is reproducible from confirmed staged IDs.
       - Render location check: “Vì sao opening position ra số này?” expander.
       - Mini QA for each completed implementation slice (MUST): UI oracle and focused draft tests.
       - Evidence target: `E3-P3B-DRAFT1`, `E3-P3B-TRACE1`.
    2. Add cutover readiness copy/status, reusable Playwright journey, browser screenshots/console capture, full build attempt, compileall, and LOG-C02-C05 regression.
       - UI flow check: return to A Bò desk and existing report/debit remain reachable; no Quick Entry.
       - DB/data flow check: financial write oracle remains zero and canonical fixtures are byte-for-byte unchanged.
       - Render location check: readiness panel clearly says `READY`/`NOT_READY` and owner decision needed.
       - Mini QA for each completed implementation slice (MUST): run actual browser/runtime evidence, then inspect screenshots and console/page errors.
       - Evidence target: `E3-P3B-BROWSER1`, `E3-P3B-REGRESSION1`, `E3-P3B-BUILD1`.
  - Implementation Gate:
    - P3-A review/search/actions pass and actual-status is refreshed.
    - Browser evidence must target the real current runtime; a host dev shortcut cannot be reported as Docker acceptance.
  - Acceptance:
    - Source: every included draft component has source IDs/rows/cells and excluded rows are visible.
    - Runtime/UI: full user journey reaches Historical Review, explanation, cutover readiness, and returns to C04/C05.
    - DB/data: no canonical financial mutation.
    - Behavior test: browser flow, console/page-error capture, focused/full regression, and compileall pass or are explicitly blocked with evidence.
    - Cleanup/quarantine: browser fixtures are isolated and source file hash is unchanged.
    - Evidence IDs: `E3-P3B-DRAFT1`, `E3-P3B-TRACE1`, `E3-P3B-BROWSER1`, `E3-P3B-REGRESSION1`, `E3-P3B-BUILD1`.
    - Actual-status rows refreshed: cutover readiness, browser evidence, Docker limitation, regression.
  - Evidence Targets: official QA JSON/MD, screenshots, console/page error counts, build/test logs, source fingerprint.
  - Actual-status Update: mark product-local cutover review surface correct; keep owner approval/live publication blocked/out of scope.
  - Commit Boundary: commit after this slice when acceptance passes.

  - Actual result: P3-B passed on the real local Streamlit runtime. The visible Chrome
    flow reached Historical Review from the A BÃ² desk, searched 62464/1572/1687/25025/
    24576/134973 with source evidence, observed NOT_READY opening readiness, blocked a
    confirm without owner reason, returned to Dashboard, and recorded 13/13 PASS action
    ledger rows with zero console/page/request errors. Full unittest, C02-C05 regressions,
    compileall, and the Docker limitation are recorded in the P3-B evidence artifacts.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed LOG-C06 scope against the brief, plan, actual-status, evidence, benchmark, diffs, and runtime claims.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all implementation phases are complete or explicitly blocked.
  - Acceptance: supervisor passes, or a blocker is recorded with evidence and no false closure is made.
  - Actual result: Supervisor report `reports/supervisor/rp_supervisor_260815_013536_by_gpt-5-codex_log-c06-historical-staging-opening-position.md` records `PASS` for the bounded local scope. Cutover remains `NOT_READY`.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only useful LOG-C06 artifacts remain in the final diff.
  - Work Steps:
    1. Review source, tests, browser scripts, QA artifacts, plan files, and temporary files created by this plan.
    2. Remove only dead artifacts created by this plan; preserve unrelated worktree changes.
    3. Verify no rejected approach, fake fixture, or stale placeholder remains.
    4. Call supervisor to review the cleanup.
  - Implementation Gate: only plan-created artifacts are candidates for cleanup.
  - Acceptance: final diff is scoped and cleanup evidence is recorded.
  - Actual result: Reviewed plan-created artifacts; retained the reusable Playwright script, official JSON/Markdown QA artifacts, reports, and plan evidence. Generated screenshots remain uncommitted; unrelated worktree changes were preserved.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commits, and final status.
  - Work Steps:
    1. Run final build/validation and record Docker target availability.
    2. Run real local browser/runtime evidence and inspect official artifacts.
    3. Run Anvien detect-changes after graph refresh.
    4. Record final source hash, tests, regressions, supervisor verdict, and commit references.
    5. Verify worktree state and report pre-existing changes separately.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: final evidence is complete, product verdict is bounded, and no live publication is claimed.
  - Actual result: Final source fingerprint, focused/full regressions, browser evidence, Anvien graph refresh/detect-changes, supervisor verdict, and scoped closure commit are recorded. Product verdict is bounded local PASS; opening cutover is `NOT_READY` and no live publication is claimed.

## Risk Notes

- Existing `views/partner_reconciliation.py`, `core/database.py`, `core/financial_ledger.py`, and `core/reconciliation.py` have high/critical Anvien blast-radius warnings. Keep them preserve-only except the smallest desk navigation seam.
- The source workbook is outside the repo and must remain unchanged; retain before/after SHA-256 evidence.
- Mongo credentials exist in the current local configuration. All development tests must use fake/isolated databases; never use canonical collections for fixtures.
- The historical workbook contains ambiguous currencies and manually accumulated values. Unknown semantics are valid outcomes and must not be forced into a live number.
- No Docker target was found in P0. Local Streamlit/browser evidence can support a bounded product verdict, but cannot be reported as container acceptance.
- Existing worktree changes belong to prior LOG-C01 through LOG-C05 and other user work. Never reset, broad-stage, or clean them.
