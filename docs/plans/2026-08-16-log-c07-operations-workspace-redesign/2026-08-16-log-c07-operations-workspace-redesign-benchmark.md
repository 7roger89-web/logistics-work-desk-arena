# LOG-C07 Logistics Operations Workspace Redesign Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-actual-status.md`

## Benchmark Rules

This file records measured counts/size/runtime metrics only. It does not turn build/test pass into design acceptance and does not record design rationale.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Loaded active shipment rows | rows | 78 | 78 | pending | preserve | 0 | E0-P0A-RUNTIME2 |
| P0 | Rows marked needing attention | rows | 76 | 76 | pending | preserve source reality | 0 | E0-P0A-RUNTIME2 |
| P0 | Visible sidebar routes | routes | 11 | 11 | 11 | grouped, all reachable | 0 | E1-P1A-NAV3 |
| P0 | Anvien parsed code files | files | 102 | 103 | 103 | fresh index | +1 | E-CLOSE-ANV1 |
| P0 | Anvien graph nodes | nodes | 19,674 | 19,988 | 19,988 | fresh index | +314 | E-CLOSE-ANV1 |
| P0 | Anvien graph relationships | relationships | 22,759 | 23,094 | 23,094 | fresh index | +335 | E-CLOSE-ANV1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Navigation groups visible | groups | 0 | 4 | 4 | 4 | +4 | E1-P1A-NAV1 |
| P1 | Global shell screenshots | screenshots | 1 | 5 | 5 | desktop + narrow evidence where supported | +4 | E1-P1B-VIS1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Workdesk rows visible in first viewport | rows | 0 | 1 | 1 | at least 1 actionable row | +1 | E2-P2A-ORDER1 |
| P2 | Priority band counters | counters | 4 | 5 | 5 | 5 semantic counters | +1 | E2-P2B-BAND1 |
| P2 | Visible row primary actions | actions/row | 1 | 1 | 1 | 1 | 0 | E2-P2B-ROW1 |
| P2 | Financial disclosure sources | fields | 0 | 7 source rows | 7 source rows | source + reason when present | +7 | E2-P2B-FIN1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Declared visible-flow actions | actions | pending | 9 | 9 | 100% ledgered | n/a | E3-P3A-ACTION1 |
| P3 | Screenshots captured and visually inspected | screenshots | 1 | 5 local + 1 official | 5 local + 1 official | critical states evidenced | n/a | E3-P3A-SHOT1 |
| P3 | Docker runtime availability | boolean | false | false | false | not required for local bounded result; blocks release | 0 | E0-P0A-BUILD2 |

## Non-Benchmarkable Notes

- Visual quality, clarity, and product usability are evaluated in the evidence ledger and independent critique, not as invented numeric scores.
- Financial correctness is covered by source-of-truth and regression evidence; the redesign must not change canonical numbers.
