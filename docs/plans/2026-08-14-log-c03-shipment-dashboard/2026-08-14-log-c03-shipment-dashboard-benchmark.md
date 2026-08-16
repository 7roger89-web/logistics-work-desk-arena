# LOG-C03 Shipment Dashboard 2.0 Benchmark Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-actual-status.md`

## Benchmark Rules

This file records measured counts and timings only. Pass/fail narrative belongs in the evidence ledger. UI measurements are limited to declared dashboard scope and must not imply pixel-perfect redesign or general application performance.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 124 | 134 | 134 | no unexplained parse loss | 0 parse failures | E0-P0A-GRAPH1, E0-P0A-GRAPH5 |
| P0 | Anvien parsed code files | files | 62 | 65 | 65 | 0 parse failures | 0 parse failures | E0-P0A-GRAPH1, E0-P0A-GRAPH4 |
| P0 | Existing dashboard symbols | symbols | 117 | 130 | 130 | preserve bounded touch | +13 symbols including bounded helpers | E0-P0A-GRAPH2, E0-P0A-GRAPH5 |
| P0 | Existing dashboard local relationships | relationships | 7 | 8 | 8 | no unrelated graph expansion | +1 local relationship | E0-P0A-GRAPH2, E0-P0A-GRAPH5 |
| P0 | Docker build target | target | 0 | 0 | 0 | discovered/available or blocker recorded | genuine blocker: no Dockerfile/compose | E0-P0A-RUNTIME1, E3-P3A-BUILD1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Dashboard model fixture scenarios | scenarios | 0 | 16 | 16 | >= 10 bounded cases | +16 | E1-P1B-TEST1 |
| P1 | Pure projection write calls | calls | 0 | 0 | 0 | 0 | 0 | E1-P1B-FILTER1 |
| P1 | Dashboard model source files | files | 0 | 1 | 1 | 1 focused module | +1 | E1-P1A-PROJ1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Shipment row/card fields shown | fields | legacy compact route/status/debt | 10 signal groups | 10 signal groups | bounded 8-10 fields | combined identity/date/finance labels keep the row compact | E2-P2A-CARD1 |
| P2 | Independent status dimensions | dimensions | 1 mixed legacy visual | 2 | 2 | 2 | +1 separate financial dimension | E2-P2A-UI1 |
| P2 | Dashboard filter families | filters | 3 | 5 | 5 | compact owner/customer/status/finance/alert/deadline set | +2 work-desk families; existing search/time/status retained above | E2-P2B-FILTER1 |
| P2 | Dashboard -> detail -> close -> second flow steps | steps | 1 shipment path | 4 | 4 | 4 observable transitions | +3 transitions | E2-P2C-SECOND1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Focused dashboard tests | tests | 0 | 7 | 7 | all bounded scenarios pass | 7/7 manual pass | E3-P3A-BUILD1 |
| P3 | Full test suite result | tests | existing suite | 28 related unittest cases pass; pytest unavailable | 28 related unittest cases pass; full suite not claimed | no LOG-C02 regression | runner/environment limitation | E3-P3A-BUILD1, E3-P3A-REG2 |
| P3 | Browser screenshots captured | screenshots | prior C01/C02 only | 2 | 2 | before/after each key action | +2 official PNGs | E3-P3A-BROWSER1 |
| P3 | Docker-backed browser run | run | 0 | 0 | 0 | 1 or genuine blocker | genuine blocker: no Docker target | E0-P0A-RUNTIME1 |

## Non-Benchmarkable Notes

- Product correctness, alert semantics, source-of-truth behavior, and supervisor acceptance are recorded in `evidence.md`, not as invented performance numbers.
- No benchmark will be run against production financial data or by mutating a real Lục Giác record.

## B4 - Formal Closure Measurements

| Metric | Unit | Latest | Target | Result | Evidence |
|---|---:|---:|---:|---|---|
| Financial writer calls during bounded mounted flow | calls | 0 | 0 | PASS | E4-P3A-ORACLE1 |
| Financial fixture snapshot differences | differences | 0 | 0 | PASS | E4-P3A-MUT1 |
| Canonical unittest suite | tests | 49 pass / 2 skip | no unexpected failure | PASS | E4-P3A-RUN1 |
| Dashboard standalone rule/filter tests | tests | 7 pass | 7 pass | PASS | E4-P3A-DASH1 |
| LOG-C02 financial/Shipment 360 regression boundary | tests | 28 pass / 2 skip | no unexpected failure | PASS | E4-P3A-REG3 |
| Runtime SALE Thành filter result | rows | 0/78 | honest source result | PASS with known data gap | E4-P3A-BROWSER2 |
| Runtime warning filter result | rows | 28/78 | valid narrowing | PASS | E4-P3A-BROWSER2 |
| First/close/second Shipment 360 transitions | transitions | 3 | 3 | PASS | E4-P3A-BROWSER2 |
| Browser console errors/warnings | messages | 0/0 | 0/0 | PASS | E4-P3A-BROWSER2 |
