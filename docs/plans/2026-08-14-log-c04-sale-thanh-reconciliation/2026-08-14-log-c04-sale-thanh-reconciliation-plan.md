# LOG-C04 SALE Thành — Đối soát công nợ A Bò Plan

## Metadata

- Date: `2026-08-14`
- Status: `draft`
- Plan: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-actual-status.md`

## Goal

Build a read-only A Bò / SALE Thành reconciliation desk that translates the
canonical financial ledger into simple Vietnamese business language. The desk
must keep currencies separate, distinguish TT payable from money A Bò holds,
make received-on-behalf and review-required money first-class, and provide a
deterministic path from every confirmed number to record, allocation, source,
and evidence. It must remain a projection and management filter, never a new
financial account or an editable manual balance.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with browser or Playwright evidence.
- For app/runtime validation, full build must include Docker image/container build. If Docker is missing or not run, full build is incomplete; record that limitation explicitly.
- Any Playwright validation must target the real built Docker/container runtime. If the repository has no Docker runtime, use the nearest real Streamlit runtime only as a documented product smoke check and do not label it Docker evidence.
- Keep the standard planner structure. These detail rules only make phase checklist items concrete enough to implement safely.
- Every implementation phase is decomposed into narrow slices. A slice is the executable implementation unit and its own commit boundary.
- Hidden fallbacks are forbidden. Missing normalized `internal_sale_owner` must remain visible as truthful empty/incomplete state.
- Read-only desk interactions must not call financial write functions or mutate ledger collections.
- Tests use synthetic fixtures only; no workbook import and no real financial mutation.
- Preserve existing LOG-C02 canonical persistence and LOG-C03 shipment-first dashboard behavior.

## Problem

LOG-C02 already provides canonical obligations, money events, allocations,
corrections, provenance, ownership, restrictions, and durable persistence.
LOG-C03 provides a shipment-first operational dashboard. The existing partner
projection is only a small totals/bucket renderer and is not yet a desk that a
non-accountant can use to answer what TT owes A Bò, what A Bò holds, what was
received or spent on behalf, what is unallocated or unknown, why a total exists,
where the money is, and how it differs from a partner statement.

The real data also does not broadly contain normalized `internal_sale_owner`.
The feature must not guess ownership from notes, names, addresses, or arbitrary
text. Synthetic fixtures may prove the canonical owner filter; live data must
truthfully show empty/incomplete coverage.

## Scope

- Extend the existing read-only partner projection with explicit business buckets, allocation/provenance/location detail, owner-coverage metadata, and deterministic explanation inputs.
- Add pure reconciliation calculations for search, period draft, partner-reported difference, exclusion categories, and money-location traces.
- Add a dedicated Streamlit A Bò / SALE Thành desk route that uses the projection only, with progressive disclosure and no financial write controls.
- Add synthetic fixture tests for the required golden cases and write oracle.
- Add a reusable Playwright flow and QA evidence for the real visible Streamlit runtime where the environment permits it.
- Run LOG-C02 ledger regression, LOG-C03 dashboard regression, compile/build checks, and console/runtime checks.

## Non-Goals

- No workbook import or migration into the live ledger.
- No AI, external model, global search, accounting-period close/lock, GL/journal terminology, FX platform, payment execution, debit generation, manager report/export, Quick Entry, frontend rewrite, or LOG-C05.
- No automatic historical SALE-owner migration.
- No new database or separate “sổ Thành”.
- No broad financial writes. Review-state writes are not needed for this bounded slice.

## Requirements

1. UI labels use Vietnamese business language: `TT phải trả A Bò`, `A Bò đang giữ/credit`, `A Bò đã nhận hộ`, `A Bò đã chi hộ`, `Chưa phân bổ`, `Chưa xác minh`, `Bị giới hạn`, and `Cần Thành xử lý`.
2. Position totals are grouped by currency and never add VND/CNY/USD without an explicit ledger FX event.
3. Confirmed net uses the existing canonical formula (`payable_to_partner - held_credit`) and exposes its source record/allocation IDs.
4. UNKNOWN, REVIEW_REQUIRED, restricted, incompatible-currency, and incomplete-provenance items remain visible but are excluded from confirmed totals and available netting.
5. Received-on-behalf remains visible after later allocation, with total received, allocated, and remaining amounts.
6. Paid/spent-on-behalf remains a separate traceable bucket and never implies that a different leg was settled.
7. A simple lookup can surface shipment, customer/source text, amount, currency, source/reference, and transaction ID, including the synthetic `62464` case.
8. Period reconciliation is explicitly a read-only draft with confirmed and review-required sections; it does not close or lock periods.
9. Partner-reported comparison is rule-based and shows difference plus candidate unmatched categories.
10. The SALE Thành filter is exact canonical `internal_sale_owner=Thành`; missing live owner data produces truthful empty/incomplete messaging.
11. Normal desk render, filter, drill-down, explanation, search, and period selection have `financial_write_count == 0`.

## Acceptance Criteria

- A non-accountant can understand the top position without accounting terminology.
- TT payable and A Bò-held money are separate buckets in each currency.
- Received-on-behalf, paid-on-behalf, unallocated, UNKNOWN, and restricted cases are individually visible and drillable.
- Every confirmed currency total has a deterministic “Vì sao ra số này?” explanation whose source IDs reconcile to the displayed value.
- A user can drill total → bucket row → allocations → source/evidence → money location trace.
- The desk is a projection and SALE Thành remains a management dimension, not a financial party.
- Period draft and partner-reported difference are understandable and explicitly bounded.
- The read-only flow has zero financial writes and no mutation of live financial data in tests.
- LOG-C02 and LOG-C03 regression suites remain green.
- Product verdict is PASS only after source, unit, runtime, browser, and write-oracle evidence is recorded; P2P helper limitations are reported separately.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect source-of-truth files, classify each surface, record blocked or missing pieces, and update later phase status assumptions, next actions, and work steps from evidence.
  - Implementation Gate: no implementation or editing starts until `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-actual-status.md` has a final P0 decision.
  - Acceptance: actual status identifies correct, partial, missing/unbound, fake-or-stub, and blocked surfaces for this scope.

### P1: Canonical projection and deterministic reconciliation model

- Phase Goal: close the domain invariant from canonical records to explainable, currency-separated, review-safe desk data without adding a write path.
- Phase Boundary:
  - In scope: `core/financial_ledger.py`, new pure reconciliation helpers, synthetic tests, and read-only data contracts.
  - Out of scope: Streamlit rendering, live workbook ingestion, migrations, and changes to financial write functions.
  - Dependencies: P0 evidence, existing LOG-C02 ledger contracts, exact Anvien impact evidence.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P1-B`.
- Ordered Slice List:
  - P1-A: Extend partner projection buckets and trace metadata.
  - P1-B: Add deterministic reconciliation calculators and fixture matrix.

- [x] P1-A: Extend partner projection buckets and trace metadata
  - Goal: make canonical partner history expose payable, held, received-on-behalf, paid-on-behalf, unallocated, restricted, unknown, owner coverage, and allocation/provenance detail without changing persistence semantics.
  - Scope Boundary:
    - Editable: `core/financial_ledger.py` projection code and direct ledger projection tests.
    - Inspect-only: `save_obligation`, `save_transaction`, `allocate_transaction`, `reverse_allocation`, `core/database.py`, existing LOG-C02 tests.
    - Preserve-only: all financial write behavior, collection names, idempotency, ownership guards, and currency guards.
    - Out of scope: UI, period arithmetic, workbook staging, and real data migration.
  - Non-Goals: no new ledger collection, no editable balance, no owner inference, no AI.
  - Pre-flight Questions:
    - Data source: canonical obligations, transactions, allocations, and existing correction metadata only.
    - Display permission: reuse current receivables permission; projection remains read-only.
    - DB read flow: use existing `build_partner_financial_position`/pure projection boundary; no new write call.
    - DB write flow: N/A; tests must prove no write flow is reachable from projection.
    - Render location: later P2 desk consumes the contract.
    - UI behavior flow: N/A; domain slice is pure/read-only.
    - Docker runtime: N/A for this pure slice; record as N/A in evidence.
    - Playwright target: N/A for this pure slice; P2 owns browser evidence.
    - Behavior test: direct synthetic records prove bucket membership, totals, allocation remainder, owner coverage, and source IDs.
    - Cleanup/quarantine: fixture records remain in memory/pure inputs; no live DB, workbook, or file writes.
    - External side effects: none.
    - N/A notes: no UI or container is needed to prove the projection contract.
  - Work Steps:
    1. Add explicit `paid_on_behalf` and received-on-behalf history fields while preserving existing held/unallocated semantics.
       - UI flow check: N/A; verify the returned contract is UI-ready and Vietnamese labels remain a renderer concern.
       - DB/data flow check: verify only read projection fields change; canonical stored documents and write functions stay untouched.
       - Render location check: N/A; consumer contract documented in tests.
       - Mini QA for each completed implementation slice (MUST): use unit behavior tests and inspect the pure returned object.
       - Evidence target: `E1-P1A-DOM1`, `E1-P1A-TEST1`.
    2. Attach allocation history, provenance/source refs, money-leg fields, and exact owner-coverage counts to relevant rows.
       - UI flow check: N/A; row metadata must support later drill-down without raw ledger terminology at the top.
       - DB/data flow check: confirm incompatible currency, UNKNOWN, and restricted rows remain excluded from confirmed totals.
       - Render location check: N/A; confirm `views` can consume the stable mapping contract.
       - Mini QA for each completed implementation slice (MUST): run the targeted ledger fixture matrix.
       - Evidence target: `E1-P1A-DOM2`, `E1-P1A-TEST2`.
  - Implementation Gate:
    - Before editing target files, run exact Anvien file-detail and symbol-impact commands for `project_partner_financial_position`, `build_partner_financial_position`, and affected tests; record the HIGH blast-radius warning and scope it to projection reads.
    - Existing LOG-C02 tests remain the regression floor.
  - Acceptance:
    - Source: projection contains explicit bucket and trace fields with no write call.
    - Runtime/UI: N/A for this slice.
    - DB/data: pure synthetic records prove multi-currency separation and exclusion rules.
    - Behavior test: direct LOG-C02 projection tests cover received-on-behalf history after full allocation, paid-on-behalf separation, partial allocation, remainder, and owner coverage; the complete six-case desk matrix belongs to P1-B.
    - Cleanup/quarantine: all test data is in-memory and no live collection is touched.
    - Evidence IDs: `E1-P1A-DOM1..E1-P1A-TEST2`.
    - Actual-status rows refreshed: ledger projection transitions `partial -> correct`; direct test coverage transitions `partial -> correct`.
  - Evidence Targets: source diff, direct projection tests, Anvien impact, and no-write inspection.
  - Actual-status Update: append R1 with new projection fields and updated relationship/impact evidence.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-B: Add deterministic reconciliation calculators and fixture matrix
  - Goal: provide a pure desk read model for explanations, search, period draft, reported difference, review inbox, and money-location trace.
  - Scope Boundary:
    - Editable: new `core/reconciliation.py` and new direct tests.
    - Inspect-only: canonical ledger projection contract from P1-A and existing core utility date/decimal helpers.
    - Preserve-only: canonical formula, currency separation, exclusion rules, and write semantics.
    - Out of scope: UI widgets, persistence, workbook import, and report export.
  - Non-Goals: no AI guesses, no accounting close, no FX conversion, no hidden owner fallback.
  - Pre-flight Questions:
    - Data source: P1-A projection plus canonical row metadata.
    - Display permission: pure read model; no permission side effects.
    - DB read flow: caller supplies projection/raw rows; no DB dependency in pure functions.
    - DB write flow: N/A; direct tests assert zero mutation.
    - Render location: P2 desk.
    - UI behavior flow: lookup → explanation → row trace → period/report comparison.
    - Docker runtime: N/A for pure calculations.
    - Playwright target: N/A for pure calculations.
    - Behavior test: one direct test per logical requirement and fixture case.
    - Cleanup/quarantine: no persistent writes; fixture inputs are recreated per test.
    - External side effects: none.
    - N/A notes: date handling is bounded draft arithmetic, not period close.
  - Work Steps:
    1. Implement deterministic currency explanations and review-inbox classification from source IDs and formulas.
       - UI flow check: contract exposes top totals, excluded categories, and drill-down rows without requiring accounting knowledge.
       - DB/data flow check: confirmed-only explanation excludes UNKNOWN/restricted/currency mismatch rows.
       - Render location check: expose stable labels/signs/values/source IDs for Streamlit.
       - Mini QA for each completed implementation slice (MUST): run targeted reconciliation tests.
       - Evidence target: `E1-P1B-EXPL1`, `E1-P1B-TEST1`.
    2. Implement bounded search, period draft, reported-position comparison, and money-location trace.
       - UI flow check: every returned trace can be selected by ID and read as source → holder → beneficiary → allocation → remainder.
       - DB/data flow check: period/report functions consume snapshots and never call persistence.
       - Render location check: returned data supports the review inbox and progressive disclosure sections.
       - Mini QA for each completed implementation slice (MUST): run the full new core test file.
       - Evidence target: `E1-P1B-TRACE1`, `E1-P1B-TEST2`.
  - Implementation Gate:
    - P1-A projection tests pass and actual-status is refreshed before creating the calculator contract.
    - No function uses current exchange rates or text guessing to classify ownership.
  - Acceptance:
    - Source: pure functions are deterministic and source-ID backed.
    - Runtime/UI: N/A for this slice.
    - DB/data: no database calls or writes from the new module.
    - Behavior test: explanation, search `62464`, period draft, partner difference, unmatched categories, and trace tests pass.
    - Cleanup/quarantine: no persistent fixture state.
    - Evidence IDs: `E1-P1B-EXPL1..E1-P1B-TEST2`.
    - Actual-status rows refreshed: reconciliation calculator transitions `missing -> correct`.
  - Evidence Targets: new module source, pure tests, compile result, and no-write oracle.
  - Actual-status Update: append R2 with calculator contract and next UI assumptions.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: Read-only Streamlit desk and navigation

- Phase Goal: give SALE Thành a simple, exception-first desk without exposing ledger internals or adding financial writes.
- Phase Boundary:
  - In scope: new desk view, existing route registration, progressive disclosure, Vietnamese labels, and reusable browser flow.
  - Out of scope: modifying the shipment-first dashboard layout, legacy collection writes, workbook loading, and new permissions.
  - Dependencies: P1-A and P1-B stable contracts.
- Phase Implementation Rule: do not implement `P2` directly. Implement `P2-A`, verify it, record evidence, refresh actual-status, commit when required, then continue to `P2-B`.
- Ordered Slice List:
  - P2-A: Render the A Bò / SALE Thành reconciliation desk.
  - P2-B: Register navigation and add reusable visible-browser flow.

- [x] P2-A: Render the A Bò / SALE Thành reconciliation desk
  - Goal: render currency-separated position, review inbox, explanation, search, trace, period draft, and partner comparison as a read-only workspace.
  - Scope Boundary:
    - Editable: new `views/partner_reconciliation.py` only.
    - Inspect-only: P1 contracts and existing `views/partner_finance.py`.
    - Preserve-only: current finance write form and LOG-C03 dashboard.
    - Out of scope: editable manual balance, review-state writes, route registration, and global search.
  - Non-Goals: no raw ledger-first layout, no accounting terms at top, no AI.
  - Pre-flight Questions:
    - Data source: `build_partner_financial_position` plus pure `core.reconciliation` helpers.
    - Display permission: current receivables permission; no new auth policy.
    - DB read flow: one projection read per rerun; no insert/update/delete.
    - DB write flow: N/A; financial write oracle patches all known write symbols and expects zero calls.
    - Render location: dedicated Streamlit route view.
    - UI behavior flow: top simple position → attention → “Vì sao ra số này?” → bucket row → source/trace → period/report.
    - Docker runtime: target full build/container if repository runtime supports it; otherwise record unavailable.
    - Playwright target: dedicated desk route in the real app runtime.
    - Behavior test: view import/route and write-oracle tests plus browser flow.
    - Cleanup/quarantine: no write; partner-reported input is ephemeral Streamlit state only.
    - External side effects: none.
    - N/A notes: no review-state update is introduced.
  - Work Steps:
    1. Build the top position and review-inbox sections with clear Vietnamese labels and truthful owner coverage.
       - UI flow check: render each currency separately; separate payable, held, received, paid, unallocated, UNKNOWN, restricted.
       - DB/data flow check: verify no financial write function is called during render/filter/period selection.
       - Render location check: new view must be independently importable and fail visibly on missing data.
       - Mini QA for each completed implementation slice (MUST): run Streamlit smoke and direct UI contract tests.
       - Evidence target: `E2-P2A-UI1`, `E2-P2A-WRITE1`.
    2. Add progressive drill-down for explanations, source/evidence, allocation history, and money location.
       - UI flow check: user can open “Vì sao ra số này?”, select a row, and read trace without seeing raw ledger terms by default.
       - DB/data flow check: detail sections are projections of the same snapshot; no reload-time financial mutation.
       - Render location check: excluded rows appear in review inbox, not in confirmed net.
       - Mini QA for each completed implementation slice (MUST): use the reusable browser flow once route wiring is available.
       - Evidence target: `E2-P2A-TRACE1`, `E2-P2A-WRITE2`.
  - Implementation Gate:
    - Before editing the new view, run Anvien file-detail/impact for the existing finance route consumer and current `views/web_app.py` route surface.
    - Existing design system remains preserve-only; no material token/navigation redesign.
  - Acceptance:
    - Source: view imports only read projection/calculator helpers and contains no financial write call.
    - Runtime/UI: top position, review inbox, explanation, search, period, comparison, and trace render with empty/incomplete live data.
    - DB/data: read-only desk leaves canonical collections unchanged.
    - Behavior test: write oracle reports zero financial writes.
    - Cleanup/quarantine: no persistent data created.
    - Evidence IDs: `E2-P2A-UI1..E2-P2A-WRITE2`.
    - Actual-status rows refreshed: desk view transitions `missing -> correct` or `partial -> correct`.
  - Evidence Targets: source review, Streamlit smoke, write oracle, screenshot/DOM snapshot where available.
  - Actual-status Update: append R3 with UI status and runtime limitations.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-B: Register navigation and add reusable visible-browser flow
  - Goal: make the desk discoverable without replacing the shipment-first home and capture a non-accountant browser flow.
  - Scope Boundary:
    - Editable: minimal `views/web_app.py` route registration and new `playwright/log_c04_partner_reconciliation_flow.mjs`.
    - Inspect-only: existing dashboard and finance routes.
    - Preserve-only: dashboard default route, Shipment 360 navigation, and legacy finance write controls.
    - Out of scope: dashboard redesign and enterprise search.
  - Non-Goals: no new app home, no broad navigation rewrite, no financial writes.
  - Pre-flight Questions:
    - Data source: real app route with current database state; synthetic fixture checks remain in unit tests.
    - Display permission: existing `receivables` permission.
    - DB read flow: route selection only triggers projection reads.
    - DB write flow: N/A; browser flow must prove zero write oracle separately.
    - Render location: sidebar route equivalent to Dashboard → Công nợ → A Bò → SALE Thành.
    - UI behavior flow: open app → open desk → inspect top → review inbox → explanation → row trace → return → period → comparison.
    - Docker runtime: use full built runtime if available; otherwise record the real Streamlit command and limitation.
    - Playwright target: new reusable module under `playwright/`, never a temp script.
    - Behavior test: browser DOM/screenshot/console evidence and route regression.
    - Cleanup/quarantine: browser interaction only changes ephemeral UI state.
    - External side effects: none.
    - N/A notes: route does not require a new permission or collection.
  - Work Steps:
    1. Add one sidebar route pointing to the dedicated desk while preserving current route order and default Dashboard.
       - UI flow check: route label is visible for current user and opens the desk.
       - DB/data flow check: route navigation calls no write symbols.
       - Render location check: view loading errors remain visible and do not silently fall back.
       - Mini QA for each completed implementation slice (MUST): import route table and run route smoke.
       - Evidence target: `E2-P2B-ROUTE1`.
    2. Add and run the reusable Playwright flow with console/error capture and required non-accountant steps.
       - UI flow check: verify top position, review items, explanation, drill-down, return, period, and comparison.
       - DB/data flow check: pair browser run with financial write-count snapshot.
       - Render location check: write official JSON/Markdown under `Reports/qa/playwright/...`; `.tmp` is debug-only.
       - Mini QA for each completed implementation slice (MUST): real visible runtime, screenshot/trace when supported.
       - Evidence target: `E2-P2B-BROWSER1`, `E2-P2B-CONSOLE1`.
  - Implementation Gate:
    - Use exact route/file impact evidence before editing `views/web_app.py`.
    - Do not use host dev server as Docker evidence; if Docker is unavailable, state the product-smoke limitation.
  - Acceptance:
    - Source: only one bounded route and reusable Playwright flow are added.
    - Runtime/UI: browser flow reaches the desk and completes the read-only journey.
    - DB/data: financial write count is zero and live data remains unchanged.
    - Behavior test: browser evidence includes console/error status and screenshot/DOM result.
    - Cleanup/quarantine: no persistent state or live fixture import.
    - Evidence IDs: `E2-P2B-ROUTE1..E2-P2B-CONSOLE1`.
    - Actual-status rows refreshed: route/browser surfaces transition `missing -> correct` or `blocked` if the real runtime cannot be started.
  - Evidence Targets: route table, Playwright module, QA JSON/MD, console and write oracle output.
  - Actual-status Update: append R4 with browser evidence and any honest runtime blocker.
  - Commit Boundary: commit after this slice when acceptance passes.

### P3: Regression, full validation, and closure

- Phase Goal: prove product behavior and protect LOG-C02/LOG-C03 before final verdict.
- Phase Boundary:
  - In scope: complete test matrix, compile/build, runtime smoke, browser QA, Anvien change detection, reports, and closure status.
  - Out of scope: optional hardening after PASS and LOG-C05.
  - Dependencies: P1/P2 slices completed or explicitly blocked with evidence.
- Phase Implementation Rule: do not implement `P3` directly. Run `P3-A`, then `P3-B`; do not open optional work after PASS.
- Ordered Slice List:
  - P3-A: Run affected validation and regression matrix.
  - P3-B: Produce reports, supervisor review, and closure.

- [x] P3-A: Run affected validation and regression matrix
  - Goal: verify core fixtures, write oracle, Streamlit health, browser flow, compile, and LOG-C02/LOG-C03 regressions.
  - Scope Boundary:
    - Editable: validation artifacts and QA reports only; no production code unless a failed test returns to its owning slice.
    - Inspect-only: final production diff and all affected contracts.
    - Preserve-only: unrelated dirty worktree changes.
    - Out of scope: optional cleanup and unrelated failures.
  - Non-Goals: no new feature after PASS.
  - Pre-flight Questions:
    - Data source: synthetic fixtures for tests, current app runtime for smoke/browser.
    - Display permission: existing route permission.
    - DB read flow: verify read-only desk only.
    - DB write flow: write oracle and collection snapshot.
    - Render location: real Streamlit runtime and Playwright reports.
    - UI behavior flow: acceptance browser journey.
    - Docker runtime: attempt required full build/container; record missing Docker if applicable.
    - Playwright target: `playwright/log_c04_partner_reconciliation_flow.mjs`.
    - Behavior test: all affected pytest/compile/browser commands.
    - Cleanup/quarantine: stop local runtime after evidence and keep logs under repo `.tmp`.
    - External side effects: none.
    - N/A notes: no production data import.
  - Work Steps:
    1. Run targeted tests, full relevant regression tests, compileall, and write oracle.
       - UI flow check: N/A for CLI tests; browser follows in step 2.
       - DB/data flow check: synthetic and snapshot assertions pass.
       - Render location check: compile/import succeeds for new route/view.
       - Mini QA for each completed implementation slice (MUST): capture command output in evidence.
       - Evidence target: `E3-P3A-TEST1`, `E3-P3A-WRITE1`.
    2. Run full build/runtime/browser/console validation and record measurements.
       - UI flow check: browser evidence covers the complete non-accountant path.
       - DB/data flow check: no unexpected financial write.
       - Render location check: official QA files under `Reports/qa/playwright`.
       - Mini QA for each completed implementation slice (MUST): inspect screenshot/DOM and logs.
       - Evidence target: `E3-P3A-RUNTIME1`, `E3-P3A-BROWSER1`.
  - Implementation Gate:
    - Do not claim PASS if a required runtime/browser check is not run; record BLOCKED/PARTIAL honestly.
    - Run `anvien detect-changes --repo Logistics-Pro-AI --scope all` before the slice commit.
  - Acceptance:
    - Source: final diff is scoped and detected.
    - Runtime/UI: real user-visible flow is evidenced or its blocker is explicit.
    - DB/data: financial write oracle is zero for read-only flow.
    - Behavior test: all required test rows have PASS/FAIL status.
    - Cleanup/quarantine: no live financial fixture mutation.
    - Evidence IDs: `E3-P3A-TEST1..E3-P3A-BROWSER1`.
    - Actual-status rows refreshed: all affected rows reflect current evidence.
    - Limitation: local Streamlit/runtime/browser evidence passes; Docker-backed full-build acceptance is explicitly blocked because the host and repository have no Docker target.
  - Evidence Targets: test logs, build/runtime logs, QA reports, detect-changes output.
  - Actual-status Update: append R5 with final validation state.
  - Commit Boundary: commit only after all required checks for this slice pass or the plan is explicitly blocked.

- [x] P3-B: Produce reports, supervisor review, and closure
  - Goal: give the user the exact PRODUCT VERDICT, P2P helper verdict, capability map, gaps, files, and next Goal boundary requested in the attached brief.
  - Scope Boundary:
    - Editable: coder report, evidence/benchmark/actual-status updates, supervisor report, and final notes.
    - Inspect-only: accepted production diff and QA artifacts.
    - Preserve-only: all unrelated pre-existing worktree changes.
    - Out of scope: LOG-C05 implementation.
  - Non-Goals: no approval/release/deploy/merge/publish action.
  - Pre-flight Questions:
    - Data source: current repo, reports, test outputs, and current P2P state.
    - Display permission: N/A; reporting only.
    - DB read flow: report the observed read/write oracle.
    - DB write flow: no new write.
    - Render location: `reports/coder`, `reports/supervisor`, `docs/notes_decisions_log`.
    - UI behavior flow: summarize the browser evidence.
    - Docker runtime: report attempted result.
    - Playwright target: report official QA paths.
    - Behavior test: supervisor independently verifies source and evidence.
    - Cleanup/quarantine: no artifact outside scope remains.
    - External side effects: none.
    - N/A notes: no release approval requested.
  - Work Steps:
    1. Write the coder report and update evidence/benchmark/actual-status plus daily notes with exact commands, results, and scope.
       - UI flow check: report user-visible behavior and limitations.
       - DB/data flow check: report fixture-only guarantee and write oracle.
       - Render location check: link exact files and line evidence.
       - Mini QA for each completed implementation slice (MUST): verify report links and status consistency.
       - Evidence target: `E3-P3B-REPORT1`.
    2. Apply supervisor skill as an independent zero-trust acceptance review; if rejected, return only to the owning slice, re-verify, and review again.
       - UI flow check: supervisor inspects source/runtime/browser claim.
       - DB/data flow check: supervisor checks invariant closure and regressions.
       - Render location check: supervisor report is stored under `reports/supervisor`.
       - Mini QA for each completed implementation slice (MUST): inspect final status/diff and closure artifacts.
       - Evidence target: `E3-P3B-SUP1`.
  - Implementation Gate:
    - All implementation slices are complete or explicitly blocked; no optional work remains open.
  - Acceptance:
    - Source: final report maps every requested acceptance section to evidence.
    - Runtime/UI: verdict distinguishes Product PASS/PARTIAL/BLOCKED from P2P helper verdict.
    - DB/data: no broad writes were introduced.
    - Behavior test: supervisor returns PASS for the reviewed claim, or records a blocker and closure remains open.
    - Cleanup/quarantine: no plan-created dead artifact remains.
    - Evidence IDs: `E3-P3B-REPORT1..E3-P3B-SUP1`.
    - Actual-status rows refreshed: final current-state matrix and closure decision recorded.
  - Evidence Targets: coder report, supervisor report, notes log, final diff/status.
  - Actual-status Update: append R6 final status.
  - Commit Boundary: final checkpoint commit only if implementation changes were made and accepted; do not stage unrelated worktree changes.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: supervisor review passes, or the plan records a blocker with evidence and no closure is performed.
- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails the cleanup, return to the responsible implementation workflow/skill for the failed cleanup scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup.
  - Acceptance: final `git diff/status` contains no dead plan-created artifacts, supervisor passes the cleanup, and evidence records what was removed or preserved.
- [ ] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run the required final validation for the accepted scope, including full build before final runtime validation. For app/runtime scopes, attempt the full Docker/container build and record if unavailable.
    2. Start the real built runtime for app/runtime validation when available; do not substitute an unbuilt dev server as Docker evidence.
    3. Validate public runtime or UI-facing changes with browser or Playwright evidence against the real runtime. Record command, service, URL, Playwright command, and screenshot/trace/result.
    4. Regenerate generated outputs if source-of-truth changes require it.
    5. Run Anvien detect-changes before commit when implementation work was performed.
    6. Record final validation, detect-changes, benchmark, and commit evidence.
    7. Commit only scoped files and verify the worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, required commits exist when authorized by the workflow, and the worktree state is known.

## Risk Notes

- `core/financial_ledger.py` is a HIGH blast-radius projection file with many unresolved analyzer edges; keep the code change narrow and preserve all write paths.
- The worktree is intentionally dirty from previous Goals. Never reset, checkout, broad-stage, or overwrite unrelated changes.
- Live Mongo availability and Docker/browser tooling may be unavailable. Product evidence must distinguish a truthful runtime blocker from a product defect.
- Existing design artifacts are draft/owner-review-required. This plan reuses their navy utility direction and makes no material visual-token change.
- A P2P helper linter may remain BLOCKED because it treats multi-clause request text as separate objectives; report that separately from the product verdict.
