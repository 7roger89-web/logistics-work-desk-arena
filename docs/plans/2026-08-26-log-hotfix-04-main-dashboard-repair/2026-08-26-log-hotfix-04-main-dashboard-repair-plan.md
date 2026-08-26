# LOG-HOTFIX-04 Main Dashboard Repair Plan

## Metadata

- Date: `2026-08-26`
- Status: `P1 Complete / P2 Pending`
- Plan: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-actual-status.md`

## Goal

Repair the current `main`-only Dashboard regression in an isolated development
candidate so the Dashboard work-desk row and Shipment workspace can execute the
existing LG09 readiness projection without changing Production, databases,
secrets, deployment coordinates, or unrelated business domains.

## Rules

- Complete P0 actual status before implementation; P0 is complete below.
- Preserve the owner worktree and the existing Production worktree.
- Use repository history as the contract authority before adding compatibility
  behavior.
- Keep the canonical read-only projection, readiness/Next Action derivation,
  `UNKNOWN` semantics, and finance separation unchanged.
- Do not use credentials, connect to `logistics_db`, perform business writes,
  deploy, push, merge, or resume LG09 as a broad workstream.
- Run Anvien impact/file-detail before editing and detect-changes before every
  implementation-slice commit.
- Validate the exact mounted lazy-import path, not only module import.
- Docker is a required runtime gate for public UI work under this plan. The
  preflight on 2026-08-26 reports Docker unavailable; this must remain an
  explicit validation limitation and cannot be replaced with a dev-server
  Playwright claim.

## Problem

`origin/main` at `618838427f7fc143a36f70527c27b3c13e303a92` keeps LG09 callers in
`views/dashboard.py` and `views/shipment.py`, but the required
`build_shipment_summary` symbol is absent from `core/shipment_dashboard.py`.
The mounted all-tabs smoke therefore fails at the Dashboard row's lazy import
before the row can render. The Dashboard block also references `CRITICAL`
without importing it; that latent name error must be repaired only if required
for the preserved readiness path.

## Scope

- Base: isolated worktree from `origin/main` at
  `618838427f7fc143a36f70527c27b3c13e303a92`.
- Editable source candidates: `core/shipment_dashboard.py` and
  `views/dashboard.py` only when mechanically required by the established
  contract.
- Editable regression tests: a focused LOG-HOTFIX-04 test exercising the
  mounted Dashboard lazy path and the mounted Shipment workspace path.
- Inspect/preserve only: `core/readiness.py`, `views/shipment.py`, finance
  ledger code, database code, auth/RBAC, customers, quotations, Getfly, GNT,
  payments, schemas, deployment settings, and all Production worktrees.
- Plan/report artifacts in this isolated branch are in scope.

## Non-Goals

- No rollback to `6a7517e`; no deployment or Streamlit coordinate change.
- No new compatibility layer whose behavior is not supported by history.
- No broad LG09 continuation, staging secret setup, or Production smoke.
- No database reads beyond repository/source inspection; no database writes.
- No finance ledger, quotation, payment, customer, auth, or schema changes.

## Requirements

1. Re-establish the historical per-shipment contract with the exact signature
   and delegation previously introduced by `ccdd345`.
2. Keep `build_shipment_dashboard_view` as the canonical read-only projection;
   the compatibility name must not duplicate or mutate projection behavior.
3. Keep readiness results and Next Action derived from the shipment and
   dashboard projection; do not encode readiness as persisted state.
4. Normalize the existing string/date deadline boundary with the repository's
   date parser before comparison; preserve invalid/unknown values as no known
   deadline rather than inventing a date.
5. Keep the Dashboard's derived primary action visibly labeled as the next
   action; preserve the existing compact readiness strip rather than changing
   its rules or adding a second state source.
6. Ensure Dashboard and Shipment callers resolve their imported constants and
   symbol on the actual lazy render paths.
7. Focused tests must prove Dashboard work-desk rendering, shipment workspace
   rendering, readiness projection, no `ImportError`/`TypeError`, and compile
   success with fixture/mocked data only.

## Acceptance Criteria

- Root cause is established from current reproduction plus history.
- Caller and callee agree on the exact `build_shipment_summary` contract.
- Mounted Dashboard smoke reaches `_render_workdesk_rows` and renders the
  shipment row without an exception.
- Mounted Shipment workspace smoke renders the readiness/Next Action surface
  without an exception.
- Focused regression tests and compile checks pass.
- No source outside the approved scope is changed.
- Production SHA remains `42d6fef6d7328232c19b095940e8971405908a92` and has no
  mutation; database mutations remain zero.
- The Docker runtime gate is either passed with evidence or the final result
  is explicitly blocked/rejected; no host dev server is presented as a
  substitute.

## Invariant Family Map

| Family | Authority / SSOT | Consumers | Required invariant |
|---|---|---|---|
| Shipment dashboard projection | `core.shipment_dashboard.build_shipment_dashboard_view` | Dashboard, readiness, summary helpers | deterministic read-only projection; no shipment mutation |
| LG09 readiness | `core.readiness` | Dashboard row, Shipment workspace | derived statuses and Next Action; no persisted readiness state |
| Financial boundary | existing financial projection/ledger contracts | dashboard row and readiness finance evaluation | quote estimate is not Finance Actual; `UNKNOWN` is not zero |
| Identity boundary | existing shipment fields and auth contracts | row/workspace display | actor is not silently treated as assignee |
| Runtime route | `views/web_app.py` lazy view loading | Dashboard and Shipment surfaces | exact mounted routes execute their real caller chain |
| Release boundary | `origin/main` candidate only | none in Production | no deployment, push, merge, DB mutation, or coordinate change |

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish current source, runtime failure, history, impact, and
    forbidden boundaries.
  - Acceptance: actual-status records the missing alias, latent Dashboard
    constant import, preserved readiness module, and current refs.

### P1: Restore the established contract and prove both callers

- Phase Goal: restore only the missing contract, the mechanically required
  constant import, and the existing string/date boundary, then prove the two
  mounted consumers.
- Phase Boundary:
  - In scope: the two source fixes and focused fixture tests.
  - Out of scope: all Production/deployment/database/business writes.
  - Dependencies: P0 history and impact evidence.
- Phase Implementation Rule: implement P1-A, verify and refresh actual status;
  then implement P1-B, verify and refresh actual status.
- Ordered Slice List:
  - P1-A: Restore historical read-only alias and Dashboard constant binding.
  - P1-B: Add exact mounted Dashboard/Shipment regression coverage.

- [x] P1-A: Restore historical read-only alias, Dashboard constant binding, and
  deadline boundary.
  - Goal: make both existing LG09 callers resolve the intended API without
    changing canonical projection behavior.
  - Scope Boundary:
    - Editable: `core/shipment_dashboard.py`, `core/readiness.py` for the
      deadline boundary, and the single missing constant in `views/dashboard.py`
      if required by source inspection.
    - Inspect-only: `views/shipment.py`, history,
      financial/database/auth modules.
    - Preserve-only: all existing projection and readiness logic.
    - Out of scope: wrappers, fallback data, persistence, deployment.
  - Non-Goals: no rollback and no unrelated cleanup.
  - Pre-flight Questions:
    - Data source: existing shipment mapping passed by callers; deadline values
      are stored as strings in current fixtures and may also be `date` objects.
    - Display permission: existing caller/auth permissions.
    - DB read flow: N/A; this slice operates on caller-provided mappings.
    - DB write flow: N/A; no writer is reachable or authorized.
    - Render location: Dashboard `_render_workdesk_rows`; Shipment
      `ui_shipment_detail_tabs` readiness block.
    - UI behavior flow: lazy import -> projection -> date normalization ->
      readiness -> visible row or Next Action surface.
    - Docker runtime: check availability; do not claim a substitute.
    - Playwright target: N/A until a built Docker runtime exists.
    - Behavior test: focused mounted AppTest in P1-B.
    - Cleanup/quarantine: fixtures are in-memory and discarded by the test.
    - External side effects: none.
    - N/A notes: database identity is intentionally not probed in this local
      source-only slice.
  - Work Steps:
    1. Apply the exact history-supported alias signature and delegation.
       - UI flow check: caller path remains unchanged.
       - DB/data flow check: confirm delegation is read-only and mapping-only.
       - Render location check: confirm both existing callers resolve the same
         canonical projection.
       - Evidence target: E1-P1A-SRC1..E1-P1A-SRC3.
    2. Bind `CRITICAL` in Dashboard only if the preserved branch references it
       without an import, then run syntax/static checks.
       - UI flow check: non-OK readiness action can select its icon.
       - DB/data flow check: no data source or writer changes.
       - Render location check: Dashboard readiness strip remains in its row.
       - Evidence target: E1-P1A-SRC4, E1-P1A-CHECK1.
    3. Normalize `customer_required_date` through the existing date parser
       before the overdue comparison, preserving `None` for unknown/invalid
       values and returning a date in `NextAction.due_at` when known.
       - UI flow check: string-backed fixture deadlines no longer raise a
         `TypeError` in the Dashboard or Shipment readiness path.
       - DB/data flow check: the mapping is read only and no field is rewritten.
       - Render location check: overdue Next Action remains derived at render
         time and does not become persisted state.
       - Evidence target: E1-P1A-SRC5, E1-P1A-CHECK2.
    4. Keep the compact Dashboard readiness output explicitly labeled
       `Việc tiếp theo` when a non-OK action is rendered.
       - UI flow check: the derived action is observable without inferring its
         meaning from a stage name.
       - DB/data flow check: no data or writer path changes.
       - Render location check: label remains inside the Dashboard row strip.
       - Evidence target: E1-P1A-SRC6, E1-P1A-CHECK3.
  - Implementation Gate:
    - Pre-edit Anvien file-detail evidence is recorded as E0-P0A-GRAPH1 and
      symbol/history evidence as E0-P0A-HIST1..E0-P0A-HIST3.
    - The alias must match the prior contract; no invented API is allowed.
  - Acceptance:
    - Source: exact signature/delegation present; no duplicate projection.
    - Runtime/UI: deferred to P1-B mounted tests.
    - DB/data: no DB access or mutation.
    - Behavior test: source-level contract checks are added in P1-B.
    - Cleanup/quarantine: no persistent fixture or temp DB.
    - Evidence IDs: E1-P1A-SRC1..E1-P1A-CHECK3.
    - Actual-status rows refreshed: alias, Dashboard readiness binding, date
      normalization, and visible Next Action label.
  - Evidence Targets: history diff, source diff, compile result.
  - Actual-status Update: alias `missing -> present`; Dashboard constant binding
    `partial -> bound`; readiness date boundary `partial -> correct`.
  - Commit Boundary: commit after slice acceptance and detect-changes pass.

- [x] P1-B: Add exact mounted Dashboard/Shipment regression coverage.
  - Goal: exercise the real lazy import path and the Shipment workspace render
    with deterministic in-memory fixtures.
  - Scope Boundary:
    - Editable: focused test file only.
    - Inspect-only: application source after P1-A.
    - Preserve-only: existing broad smoke tests and production code outside
      P1-A.
    - Out of scope: live credentials, real database, writes, browser deploy.
  - Non-Goals: no tests that merely import a module or assert static DOM.
  - Pre-flight Questions:
    - Data source: fixture shipment/customer mappings.
    - Display permission: patched authenticated fixture user.
    - DB read flow: app-level load functions patched to fixtures; no DB.
    - DB write flow: N/A; no click submits a business form.
    - Render location: mounted `web_app.py` Dashboard and `ui_shipment_detail_tabs`.
    - UI behavior flow: route mount -> lazy caller -> visible shipment/readiness
      output.
    - Docker runtime: record unavailable if still absent.
    - Playwright target: N/A without Docker.
    - Behavior test: exact `_render_workdesk_rows` call chain plus workspace.
    - Cleanup/quarantine: AppTest session and in-memory patches end per test.
    - External side effects: none.
    - N/A notes: no live staging credential is required or read.
  - Work Steps:
    1. Add a focused test that asserts the alias contract and mounts Dashboard
       through `web_app.py` with the existing fixture patches.
       - UI flow check: assert shipment ID and work action are rendered.
       - DB/data flow check: assert only fixture loaders are used.
       - Render location check: failure must identify the mounted Dashboard
         exception.
       - Evidence target: E1-P1B-TEST1.
    2. Add a mounted Shipment workspace test and readiness projection assertions.
       - UI flow check: assert Next Action/readiness and work-area labels.
       - DB/data flow check: assert unknown/financial projection remains derived.
       - Render location check: `ui_shipment_detail_tabs` reaches the readiness
         block without ImportError/TypeError.
       - Evidence target: E1-P1B-TEST2..E1-P1B-TEST4.
  - Implementation Gate:
    - Tests must fail on the pre-fix source due the exact missing symbol path;
      no module-only proxy is acceptable.
  - Acceptance:
    - Source: focused test is scoped and fixture-only.
    - Runtime/UI: mounted Dashboard and Shipment tests pass without exceptions.
    - DB/data: zero writes and no DB connection.
    - Behavior test: exact lazy path, workspace render, readiness projection.
    - Cleanup/quarantine: no persistent state remains.
    - Evidence IDs: E1-P1B-TEST1..E1-P1B-TEST4.
    - Actual-status rows refreshed: both caller surfaces become verified.
  - Evidence Targets: focused pytest output and test source.
  - Actual-status Update: Dashboard/Shipment mounted paths `partial -> correct`
    under fixture-only mounted tests.
  - Commit Boundary: include test slice in the same logical repair checkpoint
    only after P1-A and P1-B acceptance pass.

### P2: Validate candidate and boundary integrity

- Phase Goal: validate source, focused behavior, compile, full available test
  suite, graph impact, and Production/database non-mutation.
- Phase Boundary:
  - In scope: tests, compile, Anvien detect-changes, Git identity/status,
    Docker availability/result, reports.
  - Out of scope: deployment, source push, database access, coordinate changes.
  - Dependencies: P1 checkpoint commit.
- Ordered Slice List:
  - P2-A: Run compile/focused/full available tests and boundary checks.
  - P2-B: Record candidate and independent review inputs.

- [ ] P2-A: Run compile/focused/full available tests and boundary checks.
  - Goal: establish reproducible local acceptance and prove untouched boundaries.
  - Scope Boundary:
    - Editable: evidence, benchmark, actual-status, decision log only.
    - Inspect-only: source and all protected worktrees.
    - Preserve-only: code after P1 checkpoint.
    - Out of scope: all mutation outside the isolated branch.
  - Non-Goals: no staging setup or public deployment.
  - Pre-flight Questions:
    - Data source: fixture/mocked test data only.
    - Display permission: test fixture only.
    - DB read flow: no DB connection.
    - DB write flow: none.
    - Render location: mounted AppTest paths; Docker gate separately recorded.
    - UI behavior flow: tests only; no live Cloud assertion.
    - Docker runtime: attempt/check and record exact result.
    - Playwright target: blocked if Docker unavailable.
    - Behavior test: focused tests plus existing relevant smoke.
    - Cleanup/quarantine: inspect temp files/status; no destructive cleanup.
    - External side effects: none.
    - N/A notes: Production SHA is read-only Git verification.
  - Work Steps:
    1. Run focused tests, compile, and relevant existing smoke.
       - UI flow check: record mounted route results.
       - DB/data flow check: inspect patches and mutation oracle.
       - Render location check: record exception-free surfaces.
       - Evidence target: E2-P2A-TEST1..E2-P2A-TEST4.
    2. Run Anvien detect-changes, Git boundary checks, and Docker gate.
       - UI flow check: no live runtime claim if Docker is unavailable.
       - DB/data flow check: confirm no database tooling was invoked.
       - Render location check: report exact candidate commit and source diff.
       - Evidence target: E2-P2A-DETECT1..E2-P2A-BOUNDARY3.
  - Implementation Gate: no final acceptance claim without recorded test and
    boundary results.
  - Acceptance:
    - Source: compile passes and diff is allowlisted.
    - Runtime/UI: mounted tests pass; Docker/browser status is explicit.
    - DB/data: zero mutation evidence.
    - Behavior test: focused and relevant smoke pass.
    - Cleanup/quarantine: no unapproved plan-created artifacts.
    - Evidence IDs: E2-P2A-TEST1..E2-P2A-BOUNDARY3.
    - Actual-status rows refreshed: validation state and runtime limitation.
  - Evidence Targets: command outputs and SHA/status records.
  - Actual-status Update: validation rows updated with pass or blocked state.
  - Commit Boundary: documentation checkpoint after validation; no Production
    commit or push.

- [ ] P2-B: Record candidate and independent review inputs.
  - Goal: freeze the main-only candidate evidence for Supervisor.
  - Scope Boundary: reports and plan ledgers only; no source mutation.
  - Non-Goals: no promotion, deployment, or LG09 continuation.
  - Pre-flight Questions:
    - Data source: Git and test evidence.
    - Display permission: N/A.
    - DB read flow: N/A.
    - DB write flow: none.
    - Render location: report references only.
    - UI behavior flow: report the mounted result and any Docker block.
    - Docker runtime: report exact availability.
    - Playwright target: report N/A/blocked honestly.
    - Behavior test: link evidence IDs.
    - Cleanup/quarantine: review plan-created artifacts.
    - External side effects: none.
    - N/A notes: Supervisor is independent and no-fix.
  - Work Steps:
    1. Update ledgers, decision log, and coder report.
       - UI flow check: report actual mounted surfaces only.
       - DB/data flow check: report zero database mutation.
       - Render location check: map evidence to routes.
       - Evidence target: closure evidence.
  - Implementation Gate: all P1/P2-A evidence recorded.
  - Acceptance: Supervisor can independently reproduce or review every claim.
  - Evidence Targets: E2-P2B-REPORT1.
  - Actual-status Update: candidate evidence is ready for Supervisor.
  - Commit Boundary: documentation commit before Supervisor review.

- [ ] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify plan, diff, evidence, benchmark, and runtime
    claims.
  - Work Steps: run Supervisor; if rejected, fix only the rejected scope and
    rerun review; do not broaden scope.
  - Implementation Gate: P1 and P2 are complete or explicitly blocked.
  - Acceptance: Supervisor PASS, or a documented blocker/rejection with no
    false terminal.

- [ ] Pn-B: Remove dead work created during this plan.
  - Goal: keep only accepted source, focused tests, and durable evidence.
  - Work Steps: inspect plan-created artifacts; remove only obsolete artifacts
    created by this plan; rerun Supervisor on cleanup.
  - Implementation Gate: never delete owner or unrelated files.
  - Acceptance: final diff contains no dead plan-created artifact.

- [ ] Pn-C: Close the plan.
  - Goal: record final validation, hashes, reports, and worktree state.
  - Work Steps: satisfy available build gate, record Docker limitation if any,
    run final detect-changes, commit, and verify status.
  - Implementation Gate: Supervisor has passed or a blocker is recorded.
  - Acceptance: no terminal is emitted unless all user-required gates pass.

## Risk Notes

- Restoring the alias is low source risk because the exact implementation exists
  in repository history and delegates to the canonical projection.
- Dashboard readiness may expose the missing `CRITICAL` binding once the alias
  is restored; test this explicitly rather than hiding it with fallback logic.
- AppTest uses fixture patches and proves local mounted behavior, but it does not
  prove Streamlit Cloud deployment or live staging identity.
- Docker is not installed in the current environment; this is a known runtime
  validation gate, not permission to claim public-runtime PASS.
- Existing `.gitignore` and `AGENTS.md` modifications in the isolated worktree
  are owner changes and must remain untouched and uncommitted.
