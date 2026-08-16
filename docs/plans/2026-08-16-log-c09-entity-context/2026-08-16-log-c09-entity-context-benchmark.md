# LOG-C09 Entity Context Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-actual-status.md`

## Benchmark Rules

Record measurements only. Build/test/e2e pass-fail belongs in the evidence ledger unless the timing, count, size, or coverage is the measured target.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | pending | 252 | 252 | record | recorded | E3-P3A-REG1 |
| P0 | Anvien parse failures | files | pending | 0 | 0 | 0 | 0 | E3-P3A-REG1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Entity projection builders | count | 0 | 3 | 3 | 3 | +3 | E1-P1A-SRC1 |
| P1 | Focused behavior tests | tests | 0 | 11 | 11 | all pass | +11 | E1-P1B-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Context workspace modes | modes | 0 | 3 | 3 | 3 | +3 | E2-P2A-RENDER1 |
| P2 | Required cross-navigation journeys | journeys | 0 | 4 | 4 | 4 | +4 | E2-P2B-NAV1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Browser checks | checks | 0 | 11 | 11 | all pass | +11 | E3-P3A-RENDER1 |
| P3 | Official screenshots | files | 0 | 2 | 2 | >= 1 | +2 | E3-P3A-RENDER1 |

## Non-Benchmarkable Notes

- Docker availability, pytest availability, and release status are evidence/constraint facts, not product performance benchmarks.
