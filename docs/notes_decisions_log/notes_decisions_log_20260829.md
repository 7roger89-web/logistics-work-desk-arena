# Notes and decisions — 2026-08-29

## LOG-SKILL01 canonical foundation — historical entry

- LOG-SKILL01 was initially prepared from GitHub canonical `main` at
  `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`; the deleted
  `D:/Logistics_App_Copy` checkout was not recovered.
- The skill work used one task-scoped sparse/shallow/blob:none workspace at
  `D:/tmp/log-skill01-github-canonical-20260829`; no duplicate workspace or
  permanent full checkout was created.
- The five host-neutral logistics skill contracts, small JSON index,
  provenance record, pure reference behavior, fixtures, focused tests, and
  evidence documents were added. No runtime loader, app wiring, P2P change,
  database write, production access, or upstream vendoring was added.
- Upstream `ai-business-skills` was inspected at pinned commit
  `958bd43b03afbc5afc42dfdb3fb2c087b23309e4`; reuse is classified in
  `skills/logistics/skill-pack.json` and no source text was copied.
- Focused validation passed: 14 tests, affected-module compile,
  frontmatter/JSON parsing, deterministic USD/RMB traces, missing-input quote
  behavior, compliance fail-closed behavior, sales output contract, and diff
  checks.
- Coder report:
  `reports/coder/rp_coder_260829_190813_by_gpt-5-codex_log-skill01-github-canonical.md`.
- Supervisor report:
  `reports/supervisor/rp_supervisor_260829_191047_by_gpt-5-codex_log-skill01-github-canonical.md`
  — `PASS` for technical candidate readiness.

## LOG-TRADE01 old candidate — historical entry

- The old trade candidate was built against `bddcf24e...` in the same
  task-scoped worktree. The trade source/test blobs were later Supervisor
  reviewed and the post-review candidate amendments were documentation and
  evidence only.
- The trade boundary intentionally stayed independent of LOG-SKILL01 because
  the then-current base did not contain the skill pack. The old statement is
  historical; current reconciliation inspects the now-present skill pack.
- Boundary: no UI wiring, crawler, database, production access, push, deploy,
  or P2P core changes.

## 2026-08-29 current canonical reconciliation

- Fresh GitHub `main` is `f99bec21baae08cbbcf6f350ab2f3f76eec87b3f` with tree
  `bddd208c13e1e6d685fc5f9744298d698fdbd3ae`; it is the reconciliation
  authority for this worktree.
- The old trade delta has 24 paths and current main's delta from the old base
  has 27 paths. The exact overlap is only this notes file, classified as
  `DOCUMENTATION_ONLY`; no production or focused-test path overlaps.
- LOG-SKILL01 canonical paths are preserved. Its customer-intake contract is
  a shipment checklist and does not replace the trade ProductIdentity,
  regulatory, provenance, or tariff contracts; no forced direct reuse is made.
- The current-main-first reconciliation is local only. Owner approval remains
  required before push, merge, release, deployment, or production action.
