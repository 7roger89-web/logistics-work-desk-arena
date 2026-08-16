# LOG-C02 B2 Financial Ledger Foundation + A Bò Golden Financial Case Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-actual-status.md`

## Benchmark Rules

This ledger records measured counts and timings only. Pass/fail narratives,
design decisions, and detailed command logs belong in `evidence.md`. All
financial measurements are from synthetic fixtures or source inventories; no
real business amount is queried or changed.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 109 | 116 | 116 | no unexpected scope expansion | +7 | E2-P1C-REVIEW5-R2 |
| P0 | Anvien parsed code files | files | 58 | 61 | 61 | 0 parse failures | +3 | E2-P1C-REVIEW5-R2 |
| P0 | Anvien graph nodes | nodes | 8,419 | 9,930 | 9,930 | inventory recorded | +1,511 | E2-P1C-REVIEW5-R2 |
| P0 | Anvien graph relationships | relationships | 9,436 | 11,246 | 11,246 | inventory recorded | +1,810 | E2-P1C-REVIEW5-R2 |
| P0 | B2 canonical ledger collections | collections | 0 | 3 | 3 | minimum 3 canonical collections | +3 | E2-P1C-TEST2-R2 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Obligation fixture records | records | 0 | 1+ | pending | create/read-back proven | proven | E1-P1A-RUN1 |
| P1 | Transaction fixture records | records | 0 | 1+ | pending | create/read-back proven | proven | E1-P1A-RUN1 |
| P1 | Effective allocation fixture records | records | 0 | 3+ | pending | cardinalities proven | proven | E1-P1A-RUN1 |
| P1 | A Bò held-money balance | VND fixture units | 30,000,000 | 0 | pending | 0 after valid 30M allocation | -30,000,000 | E1-P1A-SVC5 |
| P1 | L-001 payable outstanding | VND fixture units | 80,000,000 | 50,000,000 | pending | 50,000,000 after allocation | -30,000,000 | E1-P1A-SVC5 |
| P1 | Multi-allocation transaction amount | VND fixture units | 300,000,000 | 300,000,000 | pending | 300,000,000 preserved | 0 | E1-P1A-SVC3 |
| P1 | Multi-allocation effective total | VND fixture units | 0 | 280,000,000 | pending | 280,000,000 | +280,000,000 | E1-P1A-SVC3 |
| P1 | Multi-allocation unallocated | VND fixture units | 300,000,000 | 20,000,000 | pending | 20,000,000 | -280,000,000 | E1-P1A-SVC4 |
| P1 | Multiple-payment obligation outstanding | CNY fixture units | 100,000 | 0 | pending | 0 | -100,000 | E1-P1A-SVC3 |
| P1 | Same-request ledger effects | effects | 0 | 1 | pending | exactly 1 | +1 | E1-P1A-SVC9 |
| P1 | Restricted/unknown allocations accepted | allocations | 0 | 0 | pending | 0 | 0 | E1-P1A-SVC7 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Focused B2 tests passed | tests | 0 | 11 | 11 | all affected pass | +11 | E2-P1C-TEST1-R2 |
| P2 | Full unittest tests passed | tests | 37 | 48 | 48 | no regression | +11 | E2-P1C-TEST5-R2 |
| P2 | Full unittest skipped/failed | tests | 1/0 | 2/0 | 2/0 | no unexpected fail | +1/0 | E2-P1C-TEST5-R2 |
| P2 | Compileall errors | errors | 0 | 0 | 0 | 0 | 0 | E2-P1C-TEST4-R2 |
| P2 | Fixture databases remaining after teardown | databases | 0 | 0 | 0 | 0 | 0 | E2-P1C-TEST8-R2 |
| P2 | B2-owned implementation files | files | 0 | 5 | 5 | scope recorded | +5 | E2-P1C-REVIEW5-R2 |

## Non-Benchmarkable Notes

- No production traffic, real business data, or live financial totals are
  benchmark targets in B2.
- Docker/browser runtime performance is not benchmarkable because no Docker
  artifact is present in the current repository; this remains a validation
  limitation, not a fabricated measurement.
