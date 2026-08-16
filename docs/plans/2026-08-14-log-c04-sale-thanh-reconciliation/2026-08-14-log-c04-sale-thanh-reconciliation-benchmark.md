# LOG-C04 SALE Thành — Đối soát công nợ A Bò Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-actual-status.md`

## Benchmark Rules

This file records measured values only. Test/build pass/fail belongs in the
evidence ledger. Measurements must be reproducible from the named command or
artifact and must not include real financial data.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 139 | 139 | 139 | current graph refreshed | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien parsed code files | files | 66 | 66 | 66 | 0 parse failures | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien graph nodes | nodes | 10,912 | 10,912 | 10,912 | current graph | 0 | `E0-P0A-GRAPH1` |
| P0 | Anvien graph relationships | relationships | 12,427 | 12,427 | 12,427 | current graph | 0 | `E0-P0A-GRAPH1` |
| P0 | Existing project eval cases | cases | 18 | 18 | 18 | >= 5 | 0 | `E0-P0A-P2P1` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Required golden fixture scenarios covered | scenarios | 0 direct LOG-C04 desk tests | 6 | 6 | >= 6 | +6 | `E1-P1B-TEST1` |
| P1 | Currency groups merged by default | groups | 0 | 0 | 0 | 0 | 0 | `E1-P1B-TEST1` |
| P1 | Pure reconciliation functions with DB writes | calls | 0 | 0 | 0 | 0 | 0 | `E1-P1B-TEST2` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Dedicated desk routes | routes | 0 | 1 | 1 | 1 | +1 | `E2-P2B-ROUTE1` |
| P2 | Read-only desk financial writes | calls | 0 baseline | 0 | 0 | 0 | 0 | `E2-P2A-WRITE1` |
| P2 | Required browser journey steps | steps | 0 | 8 | 8 | 10 | +8 | `E2-P2B-BROWSER1` |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | LOG-C02 regression tests passed | tests | pending baseline | 40 selected affected-suite tests | 40 selected affected-suite tests | all affected | pass | `E3-P3A-TEST1` |
| P3 | LOG-C03 regression tests passed | tests | pending baseline | 40 selected affected-suite tests | 40 selected affected-suite tests | all affected | pass | `E3-P3A-TEST1` |
| P3 | Browser console errors attributable to LOG-C04 | errors | 0 target | 0 | 0 | 0 | 0 | `E3-P3A-BROWSER1` |

## Non-Benchmarkable Notes

- Product comprehension, Vietnamese terminology, and progressive disclosure are acceptance qualities evidenced by source/runtime review, not a synthetic numeric score.
- Docker/container availability is an environment fact; record the exact attempt and limitation in evidence rather than inventing a pass metric.
