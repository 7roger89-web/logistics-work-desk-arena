# LOG-SKILL01 Logistics Skill Pack v0.1 Foundation Benchmark Ledger

## Metadata

- Date: 2026-08-29
- Plan: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-plan.md
- Evidence: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-evidence.md
- Benchmark: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-benchmark.md
- Actual status: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-actual-status.md

## Benchmark Rules

This ledger records measured inventory and workspace size only. Test pass/fail
belongs in evidence. No product/runtime performance benchmark is required for
this static, pure-reference tranche.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Tracked files in canonical tree | files | 437 | 437 | pending | 437 | 0 | E0-P0A-REPO1 |
| P0 | Workspace files after bounded sparse checkout | files | 15 | 1416 | pending | bounded | pending | E0-P0A-WORK1 |
| P0 | Workspace size | MiB | 0.167 | 76.826 | pending | bounded | pending | E0-P0A-WORK1 |
| P0 | Duplicate task workspaces | workspaces | 0 | 1 | pending | 1 | pending | E0-P0A-WORK1 |
| P0 | Existing runtime skill loaders | loaders | 0 | 0 | pending | 0 | 0 | E0-P0A-REPO1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | Skill IDs in pack index | IDs | 0 | 5 | pending | 5 unique | pending | E1-P1A-TEST1 |
| P1 | Intake fixtures | fixtures | 0 | 2 | pending | 2 | pending | E1-P1B-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Payment scenarios with trace | scenarios | 0 | 2 | pending | 2 | pending | E2-P2A-TEST1 |
| P2 | Quote cost classes | classes | 0 | 5 | pending | 5 | pending | E2-P2B-TEST1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3 | Required objection keys | keys | 0 | 8 | pending | 8 | pending | E3-P3A-TEST1 |

## Non-Benchmarkable Notes

- No UI, API, database, deployment, or production runtime is in scope; Docker/Playwright and broad regression are not required unless the implementation unexpectedly touches those surfaces.
- No live FX/freight/customs performance measurement is authorized.
