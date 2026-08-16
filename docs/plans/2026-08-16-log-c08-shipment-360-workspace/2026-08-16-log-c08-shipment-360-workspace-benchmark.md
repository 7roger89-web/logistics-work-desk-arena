# LOG-C08 Shipment 360 Workspace Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c08-shipment-360-workspace/2026-08-16-log-c08-shipment-360-workspace-actual-status.md`

## Benchmark Rules

Record measured counts/timings/layout evidence only. Pass/fail narrative belongs in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 234 | 243 | 243 | current graph | +9 | E0-P0A-ANV1,E-CLOSE-ANV1 |
| P0 | Anvien parsed code files | files | 103 | 106 | 106 | 0 failed parses | +3 | E0-P0A-ANV1,E-CLOSE-ANV1 |
| P0 | Existing Shipment 360 renderer symbols | symbols | 22 | 41 | 41 | preserve contract + workspace helpers | +19 | E0-P0A-DETAIL1,E-CLOSE-ANV1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Projection focused test count | tests | 0 | 7 | 7 | >= 4 | +7 | E1-P1B-TEST1 |
| P1 | Projection source mutation cases | cases | 0 | 1 | 1 | >= 1 | +1 | E1-P1B-SAFE1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | First viewport primary work signals | signals | 0 | 5 | 5 | shipment/customer/stage/next action/deadline visible | +5 | E2-P2A-RENDER1,E2-P2B-RENDER2 |
| P2 | Dashboard -> Shipment 360 -> close actions | actions | 0 | 4 | 4 | 3+ | +4 | E2-P2B-REG1 |
| P2 | Responsive viewport checks | widths | 0 | 1 | 1 | desktop + narrow | NEEDS_EVIDENCE | E2-P2B-RENDER2 |

## Non-Benchmarkable Notes

- Docker/full-build evidence is currently expected to remain blocked because the recovered project has no Docker target/executable; record the exact final command result rather than substituting it with a benchmark.
- WCAG certification is out of scope; accessibility checks are evidence obligations only.
