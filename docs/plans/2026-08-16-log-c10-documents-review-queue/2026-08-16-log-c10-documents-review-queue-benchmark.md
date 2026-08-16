# LOG-C10 Documents & Review Queue Benchmark Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-actual-status.md`

## Benchmark Rules

Record measured counts and timings only. Do not treat pass/fail narrative as a benchmark. UI evidence may include inventory counts and screenshot dimensions, while functional conclusions belong in the evidence ledger.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P0 | Existing dedicated review queue routes | routes | 0 | 0 | 0 | 1 | +0 | `E0-P0A-SRC2` |
| P0 | Existing high-risk touched consumer relationships | relationships | 97 | 97 | 97 | preserve | 0 | `E0-P0A-DETAIL1..E0-P0A-DETAIL4` |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P1 | Review item categories | categories | 0 | 4 | 4 | 4 | +4 | `E1-P1A-SRC3` |
| P1 | Focused behavior tests | tests | 0 | 6 | 6 | >= 6 | +6 | `E1-P1B-TEST1` |
| P1 | Local dataset review items | items | 0 | 205 | 205 | measured | +205 | `E1-P1B-METRIC1` |
| P1 | Local dataset shipments represented | shipments | 0 | 78 | 78 | measured | +78 | `E1-P1B-METRIC1` |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P2 | Queue-visible columns/fields | fields | 0 | — | — | compact, <= 9 | — | pending |
| P2 | Queue navigation destinations | destinations | 0 | — | — | 2 | — | pending |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| P3 | Visible runtime action ledger rows | rows | 0 | — | — | declared scope complete | — | pending |
| P3 | Render screenshots | files | 0 | — | — | >= 2 | — | pending |

## Non-Benchmarkable Notes

Docker availability and pytest availability are environment facts, not product performance metrics; keep them in evidence/status rather than inventing a benchmark.

## Final Measurements

| Metric | Latest | Evidence |
|---|---:|---|
| Queue-visible fields | 7 | `E2-P2A-CONTRACT1` |
| Navigation destinations | 2 | `E2-P2B-NAV1`, `E2-P2B-ENTITY1` |
| Visible runtime actions | 4 | `E3-P3A-RUNTIME1` |
| Render screenshots | 4 | `E3-P3A-ARTIFACT1` |
| Full regression tests | 150 passed, 2 skipped | `E3-P3C-FULL1` |
