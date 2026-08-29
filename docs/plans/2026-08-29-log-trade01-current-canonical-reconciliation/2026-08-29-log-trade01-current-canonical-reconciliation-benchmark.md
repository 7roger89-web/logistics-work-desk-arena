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
| P0 | Old trade delta paths | paths | 24 | 24 | pending | preserve | 0 | `E0-P0A-DIFF1` |
| P0 | Current-main delta paths | paths | 27 | 27 | pending | preserve | 0 | `E0-P0A-DIFF1` |
| P0 | Exact overlapping paths | paths | 1 | 1 | pending | docs-only | 0 | `E0-P0A-DIFF1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Final candidate commits ahead of current main | commits | pending | pending | pending | 1 local candidate | pending | closure evidence |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused LOG-TRADE01 tests | tests | 16 | pending | pending | 16 pass | pending | validation evidence |
| P2 | Focused LOG-SKILL01 tests | tests | 14 | pending | pending | 14 pass | pending | validation evidence |
| P2 | Non-writing affected-module compile | files | 9 | pending | pending | 9 pass | pending | validation evidence |

## Non-Benchmarkable Notes

No performance target, live source fetch, database, UI, or deployment is in
scope.

