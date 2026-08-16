# P2P Execution Ledger Benchmark Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-actual-status.md`

## Benchmark Rules

Record measured counts and hashes only. Pass/fail explanations belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Required custom profiles resolved | count | 8 | 8 | 8 | 8 | 0 | E0-P0A-SRC2 |
| P0 | Existing project eval cases | count | 18 | 18 | 18 | >=18 | 0 | E0-P0A-BASE1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Ledger eval cases | count | 0 | 12 | 12 | 12 | +12 | E1-P1C-EVAL1..12 |
| P1 | Distinct full-quorum threads | count | 0 | 8 | 8 | 8 | +8 | E1-P1B-RUNTIME1..2 |
| P1 | Durable ledger records | count | 0 | 1 | 1 | >=1 | +1 | E1-P1B-RUNTIME2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Protected baseline hash changes | count | 0 | 0 | 0 | 0 | 0 | E2-P2A-BASELINE1 |
| P2 | Doctor/drift/eval gates passing | count | 0 | 3 | 3 | 3 | +3 | E2-P2A-DOCTOR1, E2-P2A-DRIFT1, E2-P2A-EVAL1 |

## Non-Benchmarkable Notes

Host-level automatic hook availability is a qualitative boundary; it is recorded as VERIFIED, UNAVAILABLE, or UNKNOWN in the ledger rather than converted into a fabricated metric.
