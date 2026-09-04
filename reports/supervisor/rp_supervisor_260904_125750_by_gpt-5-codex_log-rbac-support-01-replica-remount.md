# Supervisor Report: Replica-Set Remount and Support Access Recovery

Verdict: PASS

## Metadata
- Report file: `reports/supervisor/rp_supervisor_260904_125750_by_gpt-5-codex_log-rbac-support-01-replica-remount.md`
- Review time: 2026-09-04 12:57 Asia/Ho_Chi_Minh
- Reviewer: gpt-5-codex
- Repo/project: Logistics Work Desk
- Scope reviewed: local MongoDB transaction capability, clean Preview restart, Support remount, and current Owner-gate state
- Claim reviewed: the local Preview remains safe and usable after correcting the standalone-MongoDB transaction blocker
- Authority used: latest Owner request, repository `AGENTS.md`, current local service state, current app source, and current browser runtime
- Related artifacts: earlier Preview-gate report; current browser screenshot outside the repository

## Executive Summary
- Problem: the first local MongoDB service was standalone, so the app displayed a stale transaction-capability error after an otherwise successful Support mount.
- Decision: the environment correction passes. The local service now runs a single-node `rs0` replica set on loopback; a transaction probe in `logistics_dev` passed and left no probe document; a fresh Preview process mounts Support without the transaction error.
- Required outcome: keep the local Preview and Support browser session running for Owner visual inspection.

## Source-Level Clearance Notes
- No application implementation file was changed for this environment correction.
- The earlier bounded source repair remains limited to the existing `current_user` import in `views/web_app.py`; this review found no further source defect.

## Evidence Checked
Passed:
- MongoDB Windows service is Running/Automatic, version 6.0.27, with a loopback-only listener.
- `hello` reports set name `rs0`, writable primary `True`, and loopback member identity.
- A focused transaction probe against `logistics_dev` using the app-compatible client pattern passed; the probe was deleted in the same transaction and the remaining count is zero.
- The Preview process at port 9501 was restarted after MongoDB configuration changed; fresh startup log contains no traceback, NameError, exception, or error line.
- Branch-local configuration remains Preview identity, authentication required, exact database allowlist `logistics_dev`, and non-release mode; values were not exposed.
- A local-only fake Support account was remounted with an in-memory generated password; the password was not printed or persisted as plaintext. Role and active state remain Support/active.
- Fresh headed-browser state shows `Codex Local Support · support`, Preview/Staging, no login form, no transaction-capability error, and no modal after cleanup. Screenshot: `C:\Users\Admin\AppData\Local\Temp\log-rbac-support-01-preview\owner-gate-clean.png`.

Failed:
- None for the bounded local Preview preparation claim.

Not run:
- Broad automated testing and the six-surface interaction sweep remain intentionally unrun; they are the Owner visual gate.
- The Codex in-app browser could not be automated because both available Computer Use kernels failed before initialization with an OS path-not-found error. The separate visible local Chrome session was verified instead.

## Invariant Closure
- affected invariant: local non-production transaction support and Support session availability.
- sibling surfaces checked: MongoDB service/config, replica-set primary state, transaction behavior, Preview restart, auth state, and browser-visible error state.
- residual unverified same-invariant surfaces: none for this bounded environment/access claim. Business-surface acceptance remains with the Owner visual gate.

## Overall Evaluation
The local Preview is now operationally usable for Support visual inspection. The standalone transaction blocker was corrected only in local service configuration; no Production connection or Production data mutation occurred, and no application framework or RBAC layer was added.
