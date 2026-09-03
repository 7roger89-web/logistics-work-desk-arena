# LOG-RBAC-SUPPORT-01 — Full operational access for Support Plan

## Metadata

- Date: `2026-09-03`
- Status: `Implementation and Supervisor acceptance complete; candidate closed without promotion`
- Plan: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-plan.md`
- Evidence: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-evidence.md`
- Benchmark: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-benchmark.md`
- Actual status: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-actual-status.md`

## Goal

Give the authenticated `support` role full employee-facing operational access across the existing Logistics workflows, with the Contract create/edit/save/reopen loop proven against durable persistence, while retaining Admin-only security/destructive boundaries, preserving Sale's effective permissions, and preserving actor/audit provenance.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- After completing a phase or implementation slice and refreshing `actual-status.md`, update the next affected phase's work steps as needed to match the latest repo reality, while preserving that phase's original goal, scope, acceptance criteria, and major phase order.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- For public runtime or UI-facing changes, validate the real user-visible runtime with AppTest/Streamlit mounted evidence; use browser evidence if a safe preview is available.
- No Production database, `logistics_db`, deployment, promotion, or merge is authorized by this plan.
- No credential, password, URI, cookie, token, or secret value may be printed or added to source.
- Keep `ROLE_PERMISSIONS` and its existing helpers as the single authorization policy; do not create a second RBAC framework.
- `QUOTE ESTIMATE != FINANCE ACTUAL`, `UNKNOWN != ZERO`, `AMBIGUOUS != RESOLVED`; protected historical finance truth remains correction/reversal/audit based.
- Support receives business-operation permissions, not `admin` wildcard or user/security/deployment/database administration.
- Preserve unrelated Owner worktree changes; implementation is confined to this isolated worktree.

## Problem

The immediate predecessor changed only `core/auth.py` to grant Support a broad permission set. The Contract view still expresses every Contract mutation through a Sales-specific write gate, while the current test contract still asserts the old Support denial. Several mounted and legacy writer boundaries are UI-only or lack a canonical service-side check. The result is an unreconciled RBAC family: the visible Contract symptom may be fixed in the matrix, but the complete UI → validation → service → repository path, actor identity, and sibling operational workflows are not yet proven together.

## Scope

- Reconcile the current Support policy against all existing employee-facing routes and action permissions.
- Add the smallest semantic helper needed for Contract operation while reusing the existing permission matrix.
- Close the Contract UI and service/repository write boundary for create, edit, save, shipment linking, Contract finance rows, and terms/reopen readback.
- Harden existing mounted business write boundaries for Customers, Shipments/Pickup/Export/Import/Delivery, Quotations/Agreements, Tasks, Finance Actual, payment/reconciliation, and existing proxy/entrustment paths without redesigning them.
- Preserve Admin-only user/role/security/configuration/destructive boundaries.
- Preserve actor `user_id`, role, username, timestamp, audit/provenance, and idempotency at central persistence/audit boundaries.
- Add focused pure, fixture-persistence, and mounted Streamlit tests for Support, Admin, Sale, and security boundaries.
- Produce a development candidate commit SHA and report `PRODUCTION_MUTATIONS=0` and `PRODUCTION_DATA_MUTATIONS=0`.

## Non-Goals

- No authentication rewrite, new role system, wildcard Support permission, schema migration, deployment, promotion, production test, or merge to `main`.
- No redesign of the Logistics UI or business rules.
- No unrelated LG09, Getfly, GNT, trade-compliance, or historical-finance refactor.
- No hard deletion of historical, audit, finance, user, customer, shipment, or proxy truth.
- No claim of staging/browser readiness if the safe preview identity/dependency gate remains unavailable.

## Requirements

1. `support` can open and operate the existing employee-facing workflows represented by the current route/action matrix.
2. Contract create/edit/save uses one canonical semantic helper at both UI and service boundaries; a saved Contract can be loaded again with persisted values.
3. Support can enter normal Contract fields, link shipments where supported, receive visible validation errors, and see Vietnamese success confirmation.
4. Admin remains full authority; Support cannot create/change/delete users, roles, secrets, deployment/configuration, or bypass protected destructive/audit rules.
5. Sale's effective permission set remains unchanged by this candidate.
6. Every Support mutation written through the audited persistence family retains canonical actor user ID, role, username, timestamp, provenance, and existing idempotency behavior.
7. Tests exercise the actual writer boundary with quarantined in-memory/disposable fixtures; no Production DB is contacted.

## Acceptance Criteria

- `SUPPORT_CONTRACT_CREATE`, `SUPPORT_CONTRACT_EDIT`, `SUPPORT_CONTRACT_SAVE`, and `SUPPORT_CONTRACT_REOPEN` are PASS against a durable fixture readback.
- Support route visibility and operational action matrix cover Customer, Contract, Shipment, Pickup/Export, Import/Delivery, Documents/Tasks, Finance Actual, payment, and reconciliation surfaces.
- Admin full access remains PASS; Sale permission drift is zero; admin-only functions remain denied to Support.
- Protected financial history still fails closed for hard-delete/silent rewrite, while supported operational finance writes remain available with audit.
- Focused tests, compile, and available full-suite evidence are recorded; any unavailable Docker/safe Preview gate is explicitly `PENDING`/`BLOCKED`, not inferred.
- An isolated commit exists with no Production mutations and no generated Anvien `AGENTS.md`/`CLAUDE.md`/`.gitignore` changes.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect current `origin/main`, source-of-truth auth matrix, Contract/UI/service/repository paths, sibling writer surfaces, Anvien graph/impact, and baseline tests; record classifications and downstream decisions in actual-status.
  - Implementation Gate: no production-code implementation starts until the actual-status file has a completed P0 decision.
  - Acceptance: the baseline identifies the matrix-only predecessor change, Contract's `sales_write` gate, stale contradictory tests, backend/UI gaps, related-file counts, and the exact bounded implementation slices.

### P1: Implement the canonical Support operational policy and writer boundaries

- Phase Goal: close the Support authorization invariant from route/control through durable writer and audit metadata.
- Phase Boundary:
  - In scope: `core/auth.py`, the existing Contract view and persistence functions, mounted operational writer guards, actor/audit metadata, and focused tests.
  - Out of scope: authentication redesign, schema migration, production/staging mutation, unrelated business logic.
  - Dependencies: P0 actual status, current `origin/main` identity, existing permission matrix and repository APIs.
- Phase Implementation Rule: do not implement `P1` directly. Implement each slice, verify it, record evidence, refresh actual-status, and commit before the next slice.
- Ordered Slice List:
  - P1-A: Canonical Contract authorization and durable Contract loop.
  - P1-B: Mounted operational writer gates and Support-facing controls.
  - P1-C: Actor/audit provenance and security regression coverage.

- [x] P1-A: Canonical Contract authorization and durable Contract loop
  - Goal: make Support's Contract create/edit/save/link/finance/terms path use one semantic permission helper and prove create → persist → reload/readback for Support.
  - Scope Boundary:
    - Editable: `core/auth.py` Contract helper/actor context, `views/contracts.py`, Contract writer functions in `core/database.py`, focused Contract tests.
    - Inspect-only: route table, legacy read projections, existing financial invariants, Production configuration.
    - Preserve-only: existing Contract fields, validation messages, legacy read fallback, transaction/idempotency behavior.
    - Out of scope: new Contract schema, UI redesign, user management.
  - Non-Goals: do not grant Support Admin wildcard or silently change Sale's effective access.
  - Pre-flight Questions:
    - Data source: existing `ROLE_PERMISSIONS` and current Contract document/transaction collections.
    - Display permission: current `contracts` route and semantic Contract write helper derived from existing `sales_write` policy.
    - DB read flow: `load_contracts`/fixture collection read after writer completion; no session-state-only proof.
    - DB write flow: `views.contracts` → `save_contract_to_cloud`/transaction writer → audited collection write.
    - Render location: `views/contracts.py::ui_contracts_management` and its existing tabs/forms.
    - UI behavior flow: Support opens Hợp Đồng, enters valid/invalid data, submits, sees Vietnamese result/error, reopens selected Contract.
    - Docker runtime: N/A unless repository exposes a safe Docker runtime; record unavailable gate explicitly.
    - Playwright target: safe mounted Streamlit/AppTest path; no Production instance.
    - Behavior test: focused Support Contract AppTest/fixture persistence test plus unauthorized service test.
    - Cleanup/quarantine: in-memory fixture or disposable prefixed DB only; no `logistics_workdesk_logc14`/`logistics_db` writes.
    - External side effects: none.
    - N/A notes: browser/Preview remains pending if staging credentials are unavailable.
  - Work Steps:
    1. Implement the smallest semantic helper over the existing matrix, replace repeated Contract UI checks, and add the service-side permission gate.
       - UI flow check: Contract save/link/finance/terms controls are enabled for authenticated Support and fail closed for unauthorized actors.
       - DB/data flow check: service rejects unauthorized writes before repository mutation; authorized writer receives the existing payload.
       - Render location check: all Contract mutation forms use the helper, not a scattered role comparison.
       - Evidence target: `E1-P1A-SRC1`, `E1-P1A-IMPACT1`.
    2. Add the durable create/edit/save/reopen fixture and mounted UI assertions, including invalid input visibility and exact persisted fields.
       - UI flow check: visible form fields, enabled submit, Vietnamese success/error, selected Contract readback.
       - DB/data flow check: create and update survive a fresh load from the fixture collection; no session-only assertion.
       - Render location check: route opens through `ROUTES` and the Contract forms are mounted.
       - Evidence target: `E1-P1A-TEST1`, `E1-P1A-DB1`, `E1-P1A-UI1`.
  - Implementation Gate:
    - Before editing, current Anvien `file-detail` and impact evidence exists for `core/auth.py`, `views/contracts.py`, and Contract writer functions in `core/database.py`.
    - P0 identifies current main and the stale predecessor tests; no hidden Production dependency is needed.
  - Acceptance:
    - Source: one semantic Contract helper; UI and service use it; Admin-only route remains separate.
    - Runtime/UI: Support can open Contract and controls do not present an authorized-save failure.
    - DB/data: Support create/edit/save/reopen readback passes on quarantined persistence.
    - Behavior test: positive Support and negative unauthorized Contract writer tests pass.
    - Cleanup/quarantine: fixture data is isolated and removed/released after the test.
    - Evidence IDs: `E1-P1A-SRC1..E1-P1A-UI1`.
    - Actual-status rows refreshed: Contract route/UI/service/repository transitions from partial to correct for the implemented boundary.
  - Evidence Targets: source diff, Anvien impact, focused tests, mounted control state, fixture collection readback, and no Production connection.
  - Actual-status Update: mark only the Contract rows proven by fresh evidence; update P1-B assumptions if shared actor/audit code changes.
  - Commit Boundary: commit `P1-A` after all listed acceptance checks pass. P1-A evidence is recorded in `E1-P1A-SRC1..E1-P1A-UI1` and the checkpoint is separate from later sibling fixes.

- [x] P1-B: Mounted operational writer gates and Support-facing controls
  - Goal: verify and close accidental Support denials or UI-only authorization across Customer, Shipment/Pickup/Export/Import/Delivery, Quotations/Agreements, Tasks, Finance Actual, payments, and reconciliation surfaces already present in the app.
  - Scope Boundary:
    - Editable: only existing UI controls and central writer permission gates in the affected family; focused role-matrix tests.
    - Inspect-only: unrelated Getfly/GNT/business calculations, historical truth, route labels not affected by permissions.
    - Preserve-only: Sale's current permissions and all admin-only destructive/security actions.
    - Out of scope: adding new routes or operational features.
  - Non-Goals: do not widen access by accepting arbitrary roles or bypassing validation/audit.
  - Pre-flight Questions:
    - Data source: existing `ROLE_PERMISSIONS`, route table, and current writer APIs.
    - Display permission: explicit existing action tokens (`customers`, `shipment_edit`, `shipment_create`, `sales_write`, `commercial_write`, `finance_write`, `operations_write`, `receivables`, `proxy_payment`, `entrustment`).
    - DB read flow: existing load functions and quarantined fixture collections.
    - DB write flow: UI → existing validation/service → existing repository/transaction boundary.
    - Render location: `views/customers.py`, `views/shipment.py`, `views/quotations.py`, `views/agreements.py`, `views/dashboard.py`, `views/finance.py`, and existing proxy/entrustment views.
    - UI behavior flow: Support control is visible/enabled for ordinary work; viewer/Support destructive controls remain disabled or hidden as policy requires.
    - Docker runtime: N/A unless a safe built runtime exists; no substitute Production browser.
    - Playwright target: mounted local safe runtime only; AppTest is the fallback for fixture-only UI evidence.
    - Behavior test: focused Support operational matrix and representative writer tests.
    - Cleanup/quarantine: fixture rows and generated files remain under `.tmp` and are removed or reset before commit.
    - External side effects: none.
    - N/A notes: documents/evidence/GNT exports are file/read operations unless an existing writer is reached; classify them explicitly.
  - Work Steps:
    1. Sweep each mounted action from route visibility through its existing writer and add only missing canonical gates/control disabled states.
       - UI flow check: support controls render as operational; true admin-only controls remain unavailable.
       - DB/data flow check: direct unauthorized service calls fail before mutation; authorized Support calls retain current validation and idempotency.
       - Render location check: Customer, Shipment work tabs, quote/agreement, task, Finance, and reconciliation entrypoints are covered.
       - Evidence target: `E1-P1B-SRC1`, `E1-P1B-IMPACT1`.
    2. Run representative Support action tests for Customer, Shipment, Pickup/Export, Import/Delivery, Tasks/Documents, Finance Actual, payment, and reconciliation, and compare Sale/Admin snapshots.
       - UI flow check: route/action visibility and button states match the matrix.
       - DB/data flow check: each selected write reaches the real fixture boundary and preserves protected-history rules.
       - Render location check: no sibling mounted path retains an accidental old Support denial.
       - Evidence target: `E1-P1B-TEST1`, `E1-P1B-UI1`, `E1-P1B-SEC1`.
  - Implementation Gate:
    - Refresh Anvien after P1-A and run file-detail/impact for every newly edited function before editing it.
    - Do not touch files outside the mapped operational family.
  - Acceptance:
    - Source: all affected mounted writer paths use the existing canonical permission layer.
    - Runtime/UI: Support operational controls are usable; admin-only controls are not confusingly editable.
    - DB/data: representative fixture writes succeed for Support and fail closed for unauthorized roles.
    - Behavior test: Support matrix passes; Sale snapshot is unchanged; Admin retains wildcard access.
    - Cleanup/quarantine: no external or Production data remains changed.
    - Evidence IDs: `E1-P1B-SRC1..E1-P1B-SEC1`.
    - Actual-status rows refreshed: every audited operational surface is marked correct or explicitly pending with reason.
  - Evidence Targets: role/action matrix, route/control sweep, writer tests, audit/idempotency assertions, and cleanup proof.
  - Actual-status Update: append transitions for each verified sibling surface and revise P1-C only for proven shared changes.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-C: Actor/audit provenance and security regression coverage
  - Goal: ensure every Support mutation in the changed writer family remains attributable to one canonical actor and protected history cannot be deleted or silently rewritten.
  - Scope Boundary:
    - Editable: central actor/audit stamping and focused tests only where necessary for the already mapped writers.
    - Inspect-only: existing Mongo schema/indexes unless a mechanical field addition is required by current document shape.
    - Preserve-only: idempotency, transaction rollback, correction/reversal, and existing audit event names.
    - Out of scope: new audit platform, schema migration, production backfill.
  - Non-Goals: do not treat display name or caller-supplied free text as the sole actor identity.
  - Pre-flight Questions:
    - Data source: authenticated session identity (`user_id`, `username`, `role`) and existing audit documents.
    - Display permission: mutation-specific existing permission token.
    - DB read flow: read audit/provenance fields from the same fixture transaction and fresh readback.
    - DB write flow: central persistence/audit helper stamps user ID, role, username, and UTC timestamp.
    - Render location: existing audit/history panels and success/error messages.
    - UI behavior flow: Support mutation reports success only after the durable writer returns success.
    - Docker runtime: N/A.
    - Playwright target: N/A unless safe preview becomes available.
    - Behavior test: actor metadata, Admin-only denial, Sale drift, hard-delete/protected-history tests.
    - Cleanup/quarantine: fixture audit collections only.
    - External side effects: none.
    - N/A notes: no Production audit read/write.
  - Work Steps:
    1. Add the smallest shared actor context and propagate it through existing central audit/write helpers without changing business payload semantics.
       - UI flow check: success is not shown for a rejected write; audit history remains readable.
       - DB/data flow check: audit and mutation metadata contain canonical actor fields and timestamp in the same transaction where one exists.
       - Render location check: existing history panels can display the actor without exposing secrets.
       - Evidence target: `E1-P1C-SRC1`, `E1-P1C-IMPACT1`, `E1-P1C-DB1`.
    2. Run security regression tests for Support/Admin/Sale, protected destructive actions, idempotency, rollback, and compile/full validation.
       - UI flow check: Support cannot reach user/role/secrets/deployment/security administration.
       - DB/data flow check: protected historical rows cannot be hard-deleted or silently overwritten; retry semantics remain stable.
       - Render location check: error messages are clear Vietnamese and do not reveal credentials.
       - Evidence target: `E1-P1C-TEST1`, `E1-P1C-SEC1`, `E1-P1C-BUILD1`.
  - Implementation Gate:
    - Refresh Anvien and run impact for central audit/actor functions before editing; treat CRITICAL fan-in as a scope warning requiring focused regression.
    - P1-A and P1-B must have refreshed actual-status rows.
  - Acceptance:
    - Source: actor stamping is centralized and no new role subsystem exists.
    - Runtime/UI: authorized Support mutations show clear success only after persistence; admin-only surfaces remain protected.
    - DB/data: actor user ID/role/time/audit/idempotency evidence is present in fixture readback.
    - Behavior test: security and historical-finance tests pass.
    - Cleanup/quarantine: all fixtures are isolated and no Production data is changed.
    - Evidence IDs: `E1-P1C-SRC1..E1-P1C-BUILD1`.
    - Actual-status rows refreshed: all plan rows have current classifications.
  - Evidence Targets: audit readback, security negative tests, idempotency/rollback results, compile, and final diff inspection.
  - Actual-status Update: append final P1 refresh before supervisor handoff.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the accepted plan, actual-status decisions, evidence, benchmark, changed files, generated output, and validation results before closure.
  - Work Steps:
    1. Call the supervisor skill to review the full completed plan work.
    2. If supervisor fails the work, return to the responsible implementation workflow/skill for the failed scope only.
    3. Re-run supervisor review after the fix.
    4. Repeat until supervisor passes or records a blocker.
  - Implementation Gate: all planned implementation phases must be completed or explicitly blocked before this review.
  - Acceptance: Supervisor report `rp_supervisor_260903_184101_by_gpt-5-codex_log-rbac-support-01.md` records `Verdict: PASS` after fresh source, graph, test, and isolation review.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure the final diff contains only artifacts that still serve the accepted plan.
  - Work Steps:
    1. Review files, sections, generated output, tests, temp files, and plan artifacts created or modified during this plan.
    2. Remove or rewrite any artifact made obsolete by actual-status findings, user corrections, failed approaches, or phase status updates.
    3. Verify no rejected approach, stale placeholder, unused generated output, or dead helper artifact remains in the final diff.
    4. Call supervisor to review the dead-work cleanup.
    5. If supervisor fails the cleanup, return to the responsible implementation workflow/skill for the failed cleanup scope only, then re-run supervisor review.
  - Implementation Gate: only remove artifacts created by this plan unless the user explicitly approves broader cleanup.
  - Acceptance: final diff contains only accepted source/tests/plan/report artifacts; generated Anvien metadata was removed and the Supervisor review passed.
- [x] Pn-C: Close the plan.
  - Goal: finish validation, evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps:
    1. Run required final validation for the accepted scope, including compile and the repository's full test command; record unavailable Docker/Preview gates honestly.
    2. If a safe built runtime is available, validate the changed Support flow with mounted browser/AppTest evidence; otherwise record browser validation pending.
    3. Run Anvien detect-changes before the final implementation commit, then remove only generated Anvien metadata from the candidate diff.
    4. Record final validation, benchmark, detect-changes, commit, and production-mutation evidence.
    5. Commit the completed scope and verify worktree state.
  - Implementation Gate: Pn-A and Pn-B must pass or record blockers.
  - Acceptance: final evidence is recorded, implementation candidate `f25347daac3d53c07f005ca49c3d9521de59351d` exists, closure docs/report are committed, and the worktree state is known clean.

## Risk Notes

- `core/database.py` has high fan-in and `_audit` has CRITICAL impact; central changes require targeted rollback/idempotency regression, not broad refactoring.
- The current `origin/main` already contains a matrix-only Support expansion and contradictory legacy tests; root cause and candidate delta must be distinguished.
- Streamlit/Mongo runtime credentials may be unavailable. No Production instance or application database may be used as a substitute.
- Existing full-suite failures outside this scope must be separated from Support evidence; stale affected tests must be updated, not ignored.
- Anvien regenerates local `AGENTS.md`/`CLAUDE.md`/`.gitignore` content in an indexed worktree; those generated changes are not part of the candidate and must be removed before commit.
