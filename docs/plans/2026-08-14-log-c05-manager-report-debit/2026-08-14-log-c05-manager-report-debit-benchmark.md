# LOG-C05 Manager Report & Debit Draft Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-actual-status.md`

## Benchmark Rules

This ledger records measured counts, timings, hashes, and before/after values
only. Pass/fail narratives belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 152 | 164 | 164 | no unexpected decrease | +12 | E0-P0A-GRAPH1, E2-P2A-GRAPH1 |
| P0 | Parsed code files | files | 71 | 77 | 77 | no unexpected decrease | +6 | E0-P0A-GRAPH1, E2-P2A-GRAPH1 |
| P0 | Graph nodes | nodes | 12,130 | 13,799 | 13,799 | baseline plus scoped artifacts | +1,669 | E0-P0A-GRAPH1, E2-P2A-GRAPH1 |
| P0 | Graph relationships | relationships | 13,833 | 15,770 | 15,770 | baseline plus scoped artifacts | +1,937 | E0-P0A-GRAPH1, E2-P2A-GRAPH1 |
| P0 | Docker build target | files | 0 | 0 | 0 | record only | 0 | E0-P0A-RUNTIME1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Pure fixture cases | cases | 0 | 10 | 10 | required matrix covered | +10 | E1-P1A-TEST1 |
| P1 | Clean debit result | CNY | 0 | 40,000 | 40,000 | 40,000 | +40,000 | E1-P1A-ORACLE1 |
| P1 | Snapshot versions preserved | versions | 0 | 2 | 2 | V1 + V2 | +2 | E1-P1B-RETRY1 |
| P1 | Financial effects from calculation | writes | 0 | 0 | 0 | 0 | 0 | E1-P1A-ORACLE1, E2-P2A-WRITE1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Mounted LOG-C05 actions | actions | 0 | 2 | 2 | report + debit reachable | +2 | E2-P2A-REPORT1, E2-P2A-DEBIT1, E2-P2B-BROWSER1 |
| P2 | Browser console errors attributable to LOG-C05 | errors | 0 | 0 | 0 | 0 | 0 | E2-P2B-CONSOLE1 |
| P2 | Screenshot checkpoints | images | 0 | 3 | 3 | desk + report + debit | +3 | E2-P2B-REPORT1 |
| P2 | Local Streamlit health checks | checks | 0 | 1 | 1 | `/_stcore/health` = `ok` | +1 | E2-P2B-BROWSER1, E3-P3A-BROWSER1 |

## Non-Benchmarkable Notes

- Product correctness, review separation, source traceability, and blocker classification are recorded in the evidence ledger rather than reduced to subjective scores.
- Positive live data is not a benchmark target because owner-normalized real rows may be absent and must not be fabricated.
