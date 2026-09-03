# Notes & Decisions Log — 2026-09-03

## LOG-RBAC-SUPPORT-01 — Full operational access for Support

- Owner decision: Support receives full employee-facing operational access, while Admin-only security/destructive authority and Sale's effective permissions remain unchanged.
- Fresh authority: isolated candidate worktree started from `origin/main` `c1c9468a814a2c0e56cefcf2851a2cadf46df436`.
- Root cause: the predecessor Support matrix lacked `sales_write`, which disabled the Contract UI's existing write gate; the current main matrix-only fix did not close sibling service/repository and actor/audit boundaries.
- Implementation: Contract semantic/service gate, operational writer/control gates, canonical Finance Ledger and reconciliation gates, actor metadata, Admin user-service guards, and focused fixture/mounted tests.
- Candidate: `f25347daac3d53c07f005ca49c3d9521de59351d` on `codex/log-rbac-support-01`.
- Validation: focused Support/RBAC/Contract/financial-safety/mounted suites pass; full-suite residuals are baseline/environment issues; safe Preview browser proof remains pending because no safe staging credentials were supplied.
- Safety: `PRODUCTION_MUTATIONS=0`, `PRODUCTION_DATA_MUTATIONS=0`; no push, merge, deployment, promotion, or Production/app-database access.
- Supervisor: `PASS` — `reports/supervisor/rp_supervisor_260903_184101_by_gpt-5-codex_log-rbac-support-01.md`.
- Coder report: `reports/coder/rp_coder_260903_184215_by_gpt-5-codex_log-rbac-support-01.md`.
