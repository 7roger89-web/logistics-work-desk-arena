# Notes and decisions — 2026-08-29

- LOG-SKILL01 resumed from fresh GitHub canonical source
  `7roger89-web/logistics-work-desk`, `main` at
  `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`; the deleted
  `D:/Logistics_App_Copy` checkout was not recovered.
- One task-scoped sparse/shallow/blob:none workspace was retained at
  `D:/tmp/log-skill01-github-canonical-20260829`; no duplicate workspace or
  permanent full checkout was created.
- Added only the five requested host-neutral logistics skill contracts, a
  small JSON index/provenance record, pure reference behavior, four fixtures,
  focused tests, and evidence documents. No runtime loader, app wiring, P2P
  change, database write, production access, or upstream vendoring was added.
- Upstream `ai-business-skills` was inspected at master commit
  `958bd43b03afbc5afc42dfdb3fb2c087b23309e4`; reuse is classified per source
  path in `skills/logistics/skill-pack.json`, with no source text copied.
- Focused validation passed: 14 tests, affected-module compile, frontmatter/
  JSON parsing, deterministic USD/RMB traces, missing-input quote behavior,
  compliance fail-closed behavior, sales output contract, and diff checks.
- Coder report: `reports/coder/rp_coder_260829_190813_by_gpt-5-codex_log-skill01-github-canonical.md`.
- Supervisor report: `reports/supervisor/rp_supervisor_260829_191047_by_gpt-5-codex_log-skill01-github-canonical.md` — `PASS` for technical candidate readiness.
- The single local candidate commit is the remaining terminal action; Owner
  gate is required before any push, merge, release, deployment, or production
  action.
