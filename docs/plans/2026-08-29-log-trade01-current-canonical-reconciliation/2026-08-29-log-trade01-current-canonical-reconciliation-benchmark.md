# LOG-TRADE01 current GitHub canonical reconciliation Benchmark Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-actual-status.md`

## Benchmark Rules

Record only reconciliation counts, exact identity, and focused validation
measurements. No application-wide performance or regression claim is made.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Old trade delta paths | paths | 24 | 24 | 24 | preserve | 0 | `E0-P0A-DIFF1` |
| P0 | Current-main delta paths | paths | 27 | 27 | 27 | preserve | 0 | `E0-P0A-DIFF1` |
| P0 | Exact overlapping paths | paths | 1 | 1 | 1 | docs-only | 0 | `E0-P0A-DIFF1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Current-main-first reconciliation checkpoint commits | commits | 0 | 1 | 1+docs closure | local candidate | current-main first parent | `E1-P1A-MERGE1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused LOG-TRADE01 tests | tests | 16 | 16 | 16 | 16 pass | 0 | `E2-VAL1` |
| P2 | Focused LOG-SKILL01 tests | tests | 14 | 14 | 14 | 14 pass | 0 | `E2-VAL1` |
| P2 | Non-writing affected-module compile | files | 9 | 17 | 17 | all affected files pass | +8 scope | `E2-VAL1` |
| P2 | Anvien parse failures on refresh | files | 0 | 0 | 0 | 0 | 0 | `E2-ANV1` |

## Non-Benchmarkable Notes

No performance target, live source fetch, database, UI, or deployment is in
scope.
