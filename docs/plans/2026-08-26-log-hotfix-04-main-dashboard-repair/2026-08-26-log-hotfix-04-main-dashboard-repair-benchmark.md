# LOG-HOTFIX-04 Main Dashboard Repair Benchmark Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-actual-status.md`

## Benchmark Rules

This ledger records measured counts and timings only. Pass/fail narratives and
root-cause reasoning belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P0 | Anvien files scanned | files | 418 | 418 | 418 | 418 | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code | files | 205 | 205 | 205 | 205 | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien failed parses | files | 0 | 0 | 0 | 0 | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph nodes | nodes | 33153 | 33153 | 33153 | 33153 | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien graph relationships | relationships | 37674 | 37674 | 37674 | 37674 | 0 | E0-P0A-GRAPH1 |
| P0 | Baseline focused smoke failures | failures | 1 | 1 | pending | 0 | pending | E0-P0A-REPRO1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1 | `build_shipment_summary` definitions | definitions | 0 | 1 | 1 | 1 | +1 | E1-P1A-SRC1 |
| P1 | Dashboard mounted exceptions after alias/import repair | exceptions | 1 | 0 | 0 | 0 | -1 | E1-P1A-CHECK1 |
| P1 | Dashboard mounted exceptions after date-boundary repair | exceptions | 1 | 0 | 0 | 0 | -1 | E1-P1A-CHECK2 |
| P1 | Dashboard Next Action label assertion failures | failures | 1 | 0 | 0 | 0 | -1 | E1-P1A-CHECK2 |
| P1 | Shipment workspace mounted exceptions | exceptions | 1 | 0 | 0 | 0 | -1 | E1-P1B-TEST2 |
| P1 | Focused regression test failures | failures | 4 | 0 | 0 | 0 | -4 | E1-P1B-TEST4 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2 | Focused regression test failures | failures | 1 | pending | pending | 0 | pending | E2-P2A-TEST1 |
| P2 | Compile failures | failures | pending | pending | pending | 0 | pending | E2-P2A-TEST2 |
| P2 | Production mutations | mutations | 0 | 0 | pending | 0 | 0 | E2-P2A-BOUNDARY1 |
| P2 | Database mutations | mutations | 0 | 0 | pending | 0 | 0 | E2-P2A-BOUNDARY2 |

## Non-Benchmarkable Notes

- Docker availability and Supervisor verdict are categorical evidence, not
  numeric performance benchmarks.
- No live Streamlit Cloud smoke is authorized by this task.
