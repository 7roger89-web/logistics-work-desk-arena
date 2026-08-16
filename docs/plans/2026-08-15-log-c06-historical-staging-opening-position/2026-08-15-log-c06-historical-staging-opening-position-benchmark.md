# LOG-C06 Historical A Bo Staging and Opening Position Benchmark Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-actual-status.md`

## Benchmark Rules

This ledger records measured counts, timings, hashes, and before/after values only.
Pass/fail narratives belong in the evidence ledger. Source workbook fingerprint is a
required integrity metric. Currency totals must never be reduced to a cross-currency
single number.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Workbook size | bytes | 316,416 | 316,416 | 316,416 | unchanged | 0 | E0-P0A-SRC1, E4-CLOSE-SHA1 |
| P0 | Workbook SHA-256 | hash | 857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70 | same | same | unchanged | 0 | E0-P0A-SRC1, E4-CLOSE-SHA1 |
| P0 | Workbook sheets | sheets | 8 | 8 | 8 | no source mutation | 0 | E0-P0A-WB1, E4-CLOSE-SHA1 |
| P0 | Sheet2 source rows | rows | 282 | 282 | 282 | all non-empty rows representable | 0 | E0-P0A-WB1, E4-CLOSE-SHA1 |
| P0 | Anvien scanned files | files | 166 | 166 | 183 | no parse failures | +17 | E0-P0A-GRAPH1, E4-CLOSE-DETECT1 |
| P0 | Anvien parsed code files | files | 77 | 77 | 86 | no parse failures | +9 | E0-P0A-GRAPH1, E4-CLOSE-DETECT1 |
| P0 | Docker build targets | files | 0 | 0 | 0 | record limitation | 0 | E0-P0A-RUNTIME1, E4-CLOSE-DETECT1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Staged non-empty source items | items | 0 | 289 | 289 | all source sheets/rows | +289 | E1-P1A-MODEL1 |
| P1 | Explicit SALE Thanh rows | items | 0 | 47 | 47 | measured, not inferred | +47 | E1-P1A-RULES1 |
| P1 | High-confidence PROPOSED rows | items | 0 | 5 | 5 | ambiguous rows remain review | +5 | E1-P1A-RULES1 |
| P1 | REVIEW_REQUIRED proposals | items | 0 | 185 | 185 | ambiguous rows visible | +185 | E1-P1A-RULES1 |
| P1 | Other-sale items | items | 0 | 60 | 60 | remain separate | +60 | E1-P1A-RULES1 |
| P1 | Items with anomaly flags | items | 0 | 231 | 231 | deterministic flags | +231 | E1-P1B-ANOMALY1 |
| P1 | Individual anomaly flags | flags | 0 | 483 | 483 | deterministic flags | +483 | E1-P1B-ANOMALY1 |
| P1 | Golden source items traced | items | 0 | 6 | 6 | 6 | +6 | E1-P1B-GOLD1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Staging import writes | writes | 0 | 4 (2 inserts + 2 retry updates) | 4 (2 inserts + 2 retry updates) | staging only | +4 | E2-P2A-WRITE1 |
| P2 | Canonical financial effects | writes | 0 | 0 | 0 | 0 | 0 | E2-P2A-ORACLE1 |
| P2 | Currency buckets | currencies | 0 | 3 + UNKNOWN excluded | 3 + UNKNOWN excluded | CNY/USD/VND/UNKNOWN separate | measured | E2-P2B-CURRENCY1 |
| P2 | Confirmed source IDs in draft | IDs | 0 | 2 clean fixture IDs | 2 clean fixture IDs | traceable | +2 | E2-P2B-POSITION1 |
| P2 | Cutover draft status values | statuses | 0 | DRAFT / READY_FOR_OWNER_REVIEW | DRAFT / READY_FOR_OWNER_REVIEW | DRAFT/READY_FOR_OWNER_REVIEW/SUPERSEDED only | measured | E2-P2B-CUTOVER1 |

## B3 - P3 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P3 | Historical Review entry actions | actions | 0 | 1 | 1 | reachable from A Bò desk | +1 | E3-P3A-UI1 |
| P3 | Search/review fixture hits | hits | 0 | 2 (62464, 1687) | 6 (62464, 1572, 1687, 25025, 24576, 134973) | six golden values | +6 | E3-P3B-BROWSER1 |
| P3 | Screenshots | images | 0 | pending | 18 captured | review + evidence + draft | +18 | E3-P3B-BROWSER1 |
| P3 | LOG-C06 console errors | errors | 0 | pending | 0 errors / 0 warnings / 0 page errors / 0 failed requests | 0 attributable | 0 | E3-P3B-CONSOLE1 |
| P3 | Regression tests | tests | 0 | pending | 107 full + focused/regression subsets | C02/C03/C04/C05 plus full suite | measured | E3-P3B-REGRESSION1 |

### B4 - P3-B measured final results

| Metric | Result | Evidence |
|---|---:|---|
| Visible browser action-ledger rows | 13/13 PASS | `reports/QA/playwright/2026-08-15-log-c06-historical-review.json` |
| Historical source searches rendered with evidence | 6/6 | same QA JSON; 62464, 1572, 1687, 25025, 24576, 134973 |
| Browser console errors / warnings | 0 / 0 | same QA JSON |
| Browser page errors / failed requests | 0 / 0 | same QA JSON |
| Review confirm without owner reason | blocked with validation copy | same QA JSON/MD |
| Compileall build | PASS | `.tmp/log-c06-tests/full-unittest.log` and build command output |
| LOG-C02 regression | 14 PASS, 1 skip | `.tmp/log-c06-tests/log-c02-regression.log` |
| LOG-C03 regression | 7 PASS | `.tmp/log-c06-tests/log-c03-regression.log` |
| LOG-C04 regression | 13 PASS | `.tmp/log-c06-tests/log-c04-regression.log` |
| LOG-C05 regression | 16 PASS | `.tmp/log-c06-tests/log-c05-regression.log` |
| LOG-C06 focused suite | 27 PASS | `.tmp/log-c06-tests/log-c06-focused.log` |
| Full unittest discovery | 107 PASS, 2 skips | `.tmp/log-c06-tests/full-unittest.log` |
| Docker target | unavailable | E3-P3B-BUILD1 |

## Non-Benchmarkable Notes

- Product correctness, provenance quality, review clarity, and cutover readiness are recorded in the evidence ledger.
- A historical total across CNY, USD, and VND is intentionally not a benchmark and must not be calculated.
- Positive live canonical data is not a benchmark target; fixtures must remain isolated.
