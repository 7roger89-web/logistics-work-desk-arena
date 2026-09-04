# Supervisor Report: Local Support Preview Gate

Verdict: PASS

## Metadata
- Report file: `reports/supervisor/rp_supervisor_260904_122800_by_gpt-5-codex_log-rbac-support-01-preview-gate.md`
- Review time: 2026-09-04 12:28 Asia/Ho_Chi_Minh
- Reviewer: gpt-5-codex
- Repo/project: Logistics Work Desk
- Scope reviewed: local MongoDB setup, branch-local Preview configuration, bounded runtime repair, and Support browser mount
- Claim reviewed: the isolated local Support preview is ready for Owner visual inspection at `http://localhost:9501`
- Authority used: latest Owner request, repository `AGENTS.md`, existing Support RBAC contract, current source, current runtime, and local database state
- Related artifacts: commit `2ce4c16`; coder blocker report; current browser screenshot outside the repository

## Executive Summary
- Problem: the approved local preview had no safe MongoDB runtime, and the first real Support-user creation attempt exposed a `NameError` in the existing admin flow.
- Decision: the bounded preview-preparation claim passes. MongoDB is a loopback-only local service, the app is restricted to `logistics_dev`, the runtime blocker is closed, and a real headed browser is mounted as Support.
- Required outcome: accepted for the Owner visual gate. This is not a declaration that the Owner has completed the six-surface visual acceptance.

## Source-Level Clearance Notes
- `views/web_app.py:20`: `current_user` is now imported from the existing `core.auth` module. The existing `_create_user_from_admin` path at `views/web_app.py:540-560` uses that callable, closing the observed runtime `NameError` without adding a new authorization layer.
- `views/web_app.py`: the current commit changes only that import in production source; no other implementation file is changed by the preview repair.

## Evidence Checked
Passed:
- `git rev-parse HEAD`: current HEAD is `2ce4c16e8f641e774bcfa729676187cb72129461`.
- `git merge-base f25347daac3d53c07f005ca49c3d9521de59351d HEAD`: the implementation candidate resolves as an ancestor; two commits follow it, including the documented closure/evidence work and the bounded blocker repair.
- `git status --porcelain=v1`: clean before this report was written; the report is documentation-only and will be committed separately.
- `python -m compileall -q views/web_app.py`: passed after the source repair.
- `python -c "from views import web_app; ..."`: the imported `current_user` is callable.
- `python scripts/check_config.py`: passed; the app connected to the configured local MongoDB database without printing secret values.
- Branch-local `.streamlit/secrets.toml`: validated without exposing values: Preview identity, authentication required, loopback Mongo URI, database `logistics_dev`, exact allowlist `['logistics_dev']`, and non-release mode.
- Windows MongoDB service: `MongoDB` is Running/Automatic; `mongod` is version 6.0.27; listener is `127.0.0.1:27017`.
- Streamlit listener: `127.0.0.1:9501` is active.
- Real headed browser: current URL is `http://127.0.0.1:9501/`; visible identity is `Codex Local Support · support`; visible banner is Preview/Staging; the Support dashboard renders without an error or login modal.
- Anvien `detect-changes files --scope all`: current worktree reports `changed_files: []` and `risk_level: none`.

Failed:
- None for the bounded preview-preparation claim.

Not run:
- Broad automated tests and the full six-surface interaction sweep were not run, per Owner instruction. Those are part of the Owner visual gate, not prerequisites for leaving the prepared preview running.

## Invariant Closure
- affected invariant: safe non-production runtime isolation and Support authentication/mount.
- sibling surfaces checked: existing auth import/call path, admin user-creation trigger, local config validation, MongoDB listener, Streamlit listener, and real browser login state.
- residual unverified same-invariant surfaces: none for preview preparation. The six business/admin surfaces remain explicitly pending Owner visual inspection and are not represented as accepted by this report.

## Overall Evaluation
The approved local preview is operationally prepared with an isolated `logistics_dev` database and no Production connection. The only implementation change was the real runtime blocker required to create the local Support account. MongoDB, Streamlit, and the headed Support browser are intentionally left running for the Owner visual gate.
