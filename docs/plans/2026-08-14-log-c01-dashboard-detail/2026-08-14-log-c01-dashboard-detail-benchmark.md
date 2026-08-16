# LOG-C01 Dashboard Detail Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-actual-status.md`

## Benchmark Rules

This ledger records measured counts only. Pass/fail narrative belongs in the evidence ledger. No customer, payment, or secret values are recorded.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Canonical P2P agent profiles | count | 8 | 8 | 8 | 8 | 0 | E0-P0A-P2P1..P2P3 |
| P0 | Full quorum denominator | agents | 8 | 8 | 8 | 8 | 0 | E0-P0A-P2P1 |
| P0 | Project files from workflow inspection | files | n/a | 2,826 | 2,826 | inventory recorded | n/a | E0-P0A-STATE1 |
| P0 | Anvien parsed code files | files | n/a | 53 | 53 | parse failures 0 | +1 | E0-P0A-ANV1, E1-P1A-IMPACT1 |
| P0 | Dashboard detail clicks required | clicks | historical 2 | 1 | 1 | 1 | -1 | E0-P0A-UI1, E1-P1A-UI1 |
| P0 | Read-only live shipments shown in selected filter | rows | historical 1 | 1 | 1 | >=1 | 0 | E0-P0A-UI1, E1-P1A-UI1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | One-click detail render | clicks | 2 | 1 | 1 | 1 | -1 | E1-P1A-UI1 |
| P1 | Filter window retained after close | boolean | pending | true | true | true | pass | E1-P1A-UI1 |
| P1 | Python test count | tests | historical 24 | 24 | 24 | no regressions | 0 | E1-P1A-TEST2 |
| P1 | Compile errors | errors | historical 0 | 0 | 0 | 0 | 0 | E1-P1A-TEST2 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Supervisor verdict | verdict | pending | REJECT | REJECT | PASS or concrete blocker | concrete blocker recorded | E2-PnA-SUP1 |
| P2 | Isolated commit boundary | files | pending | blocked: broad dirty target/worktree | blocked | no unrelated user files | unavailable | E1-P1A-DETECT1, E2-PnC-CLOSE1 |

## Non-Benchmarkable Notes

- Credential exposure, authentication posture, worker dependency mismatch, payment atomicity, and write->reload persistence are correctness/safety classifications, not benchmark claims in this phase.
- Docker/container availability is a gate state, not a performance metric.
