# LOG-C01 Dashboard Detail Plan

## Metadata

- Date: `2026-08-14`
- Status: `blocked` (P1-A local PASS; overall closure REJECT)
- Plan: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-actual-status.md`

## Goal

Close the current Dashboard list-to-detail state transition so a non-technical operator can select a shipment with one click and immediately see its detail panel, while preserving the selected date filter and the explicit close action.

## Rules

- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes.
- Record benchmarkable counts or measurements when they are taken.
- Update later phase status assumptions, next actions, and work steps when actual-status evidence changes the repo state.
- Run Anvien detect-changes before every implementation-slice commit when implementation work was performed.
- Preserve the existing dirty worktree; do not reset, overwrite, or absorb unrelated user changes.
- Do not touch P2P source, credentials, authentication policy, worker packaging, business data, release, or deployment.
- For this Streamlit project, the real local runtime is evidence for diagnosis. Docker acceptance remains a separate gate because no Dockerfile or Docker command was found in the current project.

## Problem

Current runtime evidence shows that the dashboard reads `active_sid` before rendering the shipment list. The row button assigns the selected shipment after that read and omits a rerun, so the first click only highlights the row; a second click is required to render the detail panel.

## Scope

- `views/dashboard.py` shipment selection handler and its immediate dashboard state transition.
- A reusable browser-flow script under `playwright/` only if the available browser harness can execute it without installing new dependencies.
- Focused source, runtime, and regression evidence for previous-month filter -> one click -> detail -> close.

## Non-Goals

- No credential rotation, secret-file removal, auth-policy change, worker/dependency redesign, database migration, payment rewrite, production-data write, release, or deployment.
- No visual redesign, navigation change, or refactor of the dashboard.
- No claim that DB write -> reload persistence is proven by this phase.

## Requirements

- The existing shipment list remains visible after selecting `Tháng trước`.
- One click on a visible shipment row must render its detail heading in the same user flow.
- Closing the detail must clear the active selection and preserve the chosen filter.
- The source change must be minimal and must not introduce a hidden fallback.
- Tests/evidence must prove trigger -> state transition -> observable detail render, not only static source shape.
- No business-data mutation is allowed during verification.

## Acceptance Criteria

- P0 actual status is complete and identifies preserve-only, partial, blocked, and out-of-scope surfaces.
- The one-click flow passes in the real local Streamlit runtime from a fresh session.
- The close flow returns to the same filtered list without a second click.
- Focused regression and full available Python test/compile checks pass.
- Anvien change detection is recorded before any commit; if the dirty worktree prevents a safe isolated commit, the plan records that fact instead of committing unrelated user changes.
- Docker/container acceptance is explicitly `BLOCKED` unless a valid Docker build/runtime becomes available.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state and the exact dashboard defect.
  - Work Steps: inspect P2P installation, project state, current source, Anvien graph, existing reports, and the live local runtime; classify the target and preserve-only boundaries in `2026-08-14-log-c01-dashboard-detail-actual-status.md`.
  - Implementation Gate: the actual-status file contains current evidence IDs, relationship/impact counts, and a final P0 decision.
  - Acceptance: the dashboard target is classified `partial`/`wrong`, correct sibling surfaces are preserve-only, and non-scope blockers are recorded.

### P1: Dashboard one-click detail

- Phase Goal: repair and verify the single user-visible state transition without changing business data or the dashboard's visual direction.
- Phase Boundary:
  - In scope: the row selection handler in `views/dashboard.py`, focused runtime regression evidence, and a reusable browser-flow artifact if executable without new dependencies.
  - Out of scope: all security, worker, payment, persistence, deployment, and P2P changes.
  - Dependencies: P0 status, local Streamlit runtime, current read-only Mongo-backed dataset.
- Phase Implementation Rule: do not implement `P1` directly. Implement `P1-A`, verify it, record evidence, refresh actual-status, and stop at the phase terminal condition.
- Ordered Slice List:
  - P1-A: Repair the row selection rerun and verify one-click detail/close behavior.

- [x] P1-A: Repair the row selection rerun and verify one-click detail/close behavior
  - Goal: make the selected shipment state available to the detail branch immediately after one row click.
  - Scope Boundary:
    - Editable: the smallest necessary selection-handler lines in `views/dashboard.py`; a reusable browser-flow script only when the existing browser harness supports it.
    - Inspect-only: `views/shipment.py`, `core/state.py`, `core/database.py`, route registry, secrets/auth/worker files, and all business-data collections.
    - Preserve-only: current dashboard layout, date-filter logic, detail renderer, close handler, and unrelated dirty worktree changes.
    - Out of scope: any write path, auth change, dependency install, Dockerfile, or deployment.
  - Non-Goals: no database mutation, no new UI component, no redesign, and no attempt to close the unrelated security or persistence blockers.
  - Pre-flight Questions:
    - Data source: current read-only `db_shipments` session state loaded from Mongo.
    - Display permission: current local-admin read/edit surface; no permission policy change.
    - DB read flow: `refresh_core_data`/dashboard read -> `ships_filtered` -> row render.
    - DB write flow: N/A; verification must not submit save/delete/payment controls.
    - Render location: `views/dashboard.py` detail branch and `views/shipment.py` detail tabs.
    - UI behavior flow: choose `Tháng trước` -> expand client -> click one shipment -> heading appears -> click close -> filtered list returns.
    - Docker runtime: not available in current project inventory; record as acceptance blocker if still absent.
    - Playwright target: `http://127.0.0.1:8516` local Streamlit runtime through the installed browser harness.
    - Behavior test: fresh-session one-click heading assertion plus close/filter assertion.
    - Cleanup/quarantine: no rows created or changed; stop the local runtime after evidence collection.
    - External side effects: none intended; do not submit forms or deploy.
    - N/A notes: persistence and security are deliberately outside this slice.
  - Work Steps:
    1. Apply the minimal state-transition fix after confirming the current source and Anvien impact evidence.
       - UI flow check: confirm the selected row is the same shipment whose heading must render.
       - DB/data flow check: confirm no write control is triggered and the source dataset is read-only.
       - Render location check: confirm the existing detail branch consumes the selected session-state key.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: use the in-app Browser/Playwright surface for the real local runtime; do not substitute a mocked page.
       - Evidence target: `E1-P1A-SRC1` and `E1-P1A-IMPACT1`.
    2. Run the fresh browser flow, focused regression, full available Python tests, compile check, and change detection; refresh actual-status.
       - UI flow check: one click opens detail; close returns to the same `Tháng trước` window.
       - DB/data flow check: read-only counts remain unchanged and no mutation action is submitted.
       - Render location check: the detail heading and existing form controls are visible after the first click.
       - Mini QA for each completed implementation slice (MUST)
          For Codex: retain browser DOM/screenshot evidence and record the exact runtime URL.
       - Evidence target: `E1-P1A-UI1`, `E1-P1A-TEST1`, `E1-P1A-TEST2`, and `E1-P1A-DETECT1`.
  - Implementation Gate:
    - Before editing target files, `anvien file-detail views/dashboard.py --repo Logistics-Pro-AI --json` and dashboard impact analysis must be recorded.
    - The current file is already dirty; the edit must be reviewed against its current content and must not reset other hunks.
    - The local runtime must be healthy before and after the change.
  - Acceptance:
    - Source: the selection handler schedules the state transition consumed by the detail branch.
    - Runtime/UI: one click from a fresh session renders the detail heading and close preserves the filter.
    - DB/data: no business-data writes; read-only counts and configured source remain unchanged.
    - Behavior test: the fresh browser flow passes; available Python tests and compile checks pass.
    - Cleanup/quarantine: local runtime is stopped; no fixture/business rows remain.
    - Evidence IDs: `E1-P1A-SRC1`, `E1-P1A-IMPACT1`, `E1-P1A-UI1`, `E1-P1A-TEST1`, `E1-P1A-TEST2`, `E1-P1A-DETECT1`.
    - Actual-status rows refreshed: dashboard one-click detail `partial/wrong -> correct` only if fresh runtime evidence proves it; Docker gate remains `blocked` if unavailable.
  - Evidence Targets: current diff, Anvien file/impact output, local runtime DOM/screenshot, test output, compile output, change detection, and clean-up status.
  - Actual-status Update: append an R1 row with the observed transition and any remaining Docker/dirty-worktree boundary.
  - Commit Boundary: commit only an isolated slice when safe; otherwise do not commit unrelated pre-existing changes and record the exact reason.

  - Completion Note: the source fix, real local Browser flow, compile, unit tests, runtime health, and post-edit Anvien detection completed. The target file was already a broad dirty user rewrite, so no isolated commit was created; Docker remains unavailable.

### Pn: Supervisor and closure

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the one-click fix against the plan, current source, runtime evidence, and changed-file boundary.
  - Work Steps: inspect the final source/diff, rerun the affected evidence, and write a supervisor report; if Docker or isolated commit evidence is required and unavailable, record REJECT/BLOCKED rather than claiming completion.
  - Implementation Gate: P1-A is complete or explicitly blocked.
  - Acceptance: supervisor returns PASS for the bounded local fix or records a concrete blocker with evidence.
  - Completion Note: supervisor review completed; bounded P1-A evidence passed, but the overall claim was `REJECT` because final P2P governance drift is FAIL and Docker/commit/safety boundaries remain unresolved.
- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only useful plan artifacts remain.
  - Work Steps: review plan-created files and temporary runtime logs, remove only artifacts created by this plan that are no longer required, and verify no unrelated user file was touched.
  - Implementation Gate: no unrelated cleanup is included.
  - Acceptance: plan-created dead artifacts are removed or justified and the final status is known.
  - Completion Note: stopped only the verified local Streamlit process and removed the two exact temporary LOG-C01 runtime logs; retained plan, QA, coder, and supervisor artifacts as required evidence.
- [x] Pn-C: Close the plan.
  - Goal: finish evidence, benchmark, detect-changes, commit boundary, and final status.
  - Work Steps: record final validation and unresolved risks, update all four plan files, and stop at PASS, BLOCKED, or REJECT.
  - Implementation Gate: supervisor review and blocker accounting are complete.
  - Acceptance: the final report does not exceed current evidence and names the next owner decision if one remains.
  - Completion Note: all four plan files and evidence reports are refreshed; terminal status is `BLOCKED`, no commit or deployment was performed.

## Risk Notes

- `views/dashboard.py` is a high-risk graph file with 117 symbols, 7 local relationships, and 434 unresolved references in the current Anvien projection; keep the edit surgical.
- The current worktree contains broad user changes, including the target file. A safe isolated commit may be impossible without committing pre-existing changes; do not silently do that.
- No Dockerfile/Docker command is present in the current project inventory, so planner-required container acceptance may remain blocked even if the local Streamlit fix passes.
- Credential exposure, unauthenticated Local Admin mode, worker dependency mismatch, non-atomic Contract proxy writes, and missing durable write->reload proof remain outside this phase and must not be reported as resolved.
- Final governance boundary: the last doctor and governance-drift checks report FAIL for unlocked `.agents/skills` runtime files and protected `P2P_INSTRUCTIONS_BLOCK` drift. Do not repair or overwrite those P2P-managed files inside this dashboard task; record the blocker and request a separate governance review.
