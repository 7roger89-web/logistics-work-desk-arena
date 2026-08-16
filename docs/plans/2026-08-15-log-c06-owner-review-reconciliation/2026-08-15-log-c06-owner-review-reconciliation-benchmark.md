# LOG-C06 Owner Review and Reconciliation Phase Benchmark Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-actual-status.md`

## Benchmark Rules

This file records measured counts, sums, hashes, coverage, and runtime metrics only.
Business decisions and pass/fail narratives belong in the evidence ledger. Currency totals
remain separated by currency; no cross-currency total is allowed.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P0 | Source workbook size | bytes | 316,416 | 316,416 | 316,416 | unchanged | 0 | E0-P0A-SRC1 |
| P0 | Source workbook SHA-256 | hash | 857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70 | same | same | unchanged | 0 | E0-P0A-SRC1 |
| P0 | Staged items | items | 289 | 289 | 289 | preserve source coverage | 0 | E0-P0A-BASELINE1 |
| P0 | Review-required items | items | 185 | 185 | 185 | cluster all 185 | 0 | E0-P0A-BASELINE1 |
| P0 | Anvien scanned files | files | 183 | 183 | 183 | no parse failures | 0 | E0-P0A-GRAPH1 |
| P0 | Anvien parsed code files | files | 86 | 86 | 86 | no parse failures | 0 | E0-P0A-GRAPH1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P1 | Golden values reconstructed | items | 0 | 6 | 6 | 6 | 6 | E1-P1A-GOLD1 |
| P1 | Checkpoint candidate components | items | 0 | 11 | 11 | exact arithmetic set | 11 | E1-P1A-CHECKPOINT1 |
| P1 | Checkpoint candidate sum | CNY | 0 | 134,973.0 | 134,973.0 | 134,973 | 134,973 | E1-P1A-ORACLE1 |
| P1 | Review rows assigned to one cluster | items | 0 | 185 | 185 | 185 | 185 | E1-P1B-CLUSTER1 |
| P1 | Ready-for-owner-confirmation rows | items | 0 | 13 | 13 | derived only | 13 | E1-P1B-READY1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P2 | Owner-facing review panels | panels | 0 | 4 | 4 | golden/cluster/decision pack/checkpoint | 4 | E2-P2A-UI1 |
| P2 | Canonical financial writes | writes | 0 | 0 | 0 | 0 | 0 | E2-P2A-ORACLE1 |
| P2 | Browser action coverage | actions | 0 | 6 | 6 | declared flow | 6 | E2-P2A-BROWSER1 |
| P2 | Focused unittest result | tests | 0 | 27 passed | 27 passed | no failure | 27 passed | E2-P2B-REGRESSION1 |
| P2 | Full unittest result | tests | 107 | 113 passed + 2 skipped | 113 passed + 2 skipped | no regression | +6 passed | E2-P2B-REGRESSION1 |
| P2 | Local runtime health | HTTP | n/a | 200 | 200 | 200 | 0 | E2-P2B-BUILD1 |
| P2 | Source workbook SHA-256 | hash | baseline | unchanged | unchanged | unchanged | 0 | E2-P2B-BUILD1 |

## Non-Benchmarkable Notes

- Owner semantic choices are not benchmarkable until explicitly decided.
- Exact arithmetic is measured separately from ownership/allocation meaning.
- Cutover remains locked and is not a benchmark target.

## B3 - P3 Owner-decision staging metrics

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P3 | Owner batch target rows | rows | 0 | 20 | 20 | 20 | 20 | E4-P3-BATCH1 |
| P3 | Owner batch applied writes | actions | 0 | 20 | 20 | 20 | 20 | E4-P3-BATCH1 |
| P3 | Deterministic replay idempotent actions | actions | 0 | 20 | 20 | 20 | 20 | E4-P3-BATCH1 |
| P3 | Staged items | items | 289 | 289 | 289 | unchanged | 0 | E4-P3-BATCH1 |
| P3 | Stored CONFIRMED items | items | 0 | 20 | 20 | Owner batch only | 20 | E4-P3-STATUS1 |
| P3 | Stored REVIEW_REQUIRED items | items | 185 | 170 | 170 | row 96 remains review | -15 | E4-P3-STATUS1 |
| P3 | Stored RAW items | items | 39 | 39 | 39 | preserve raw coverage | 0 | E4-P3-STATUS1 |
| P3 | 134,973 checkpoint components | CNY | 0 | 134,973.0 | 134,973.0 | exact | 134,973.0 | E4-P3-CHECKPOINT1 |
| P3 | Full paid-on-behalf group | CNY | 0 | 159,998.0 | 159,998.0 | exact | 159,998.0 | E4-P3-CHECKPOINT1 |
| P3 | Received source group | CNY | 0 | 349,448.3929340609 | 349,448.3929340609 | checkpoint expectation | 349,448.3929340609 | E4-P3-RECEIVED1 |
| P3 | Received group expectation difference | CNY | 0 | -67,033.84966649559 | -67,033.84966649559 | 0 only after Owner evidence | -67,033.84966649559 | E4-P3-HISTORICAL1 |
| P3 | Confirmed opening components | items | 0 | 18 | 18 | exclude embedded/summary | 18 | E4-P3-OPENING1 |
| P3 | Canonical financial writes | writes | 0 | 0 | 0 | 0 | 0 | E4-P3-ORACLE1 |
| P3 | Browser actions passed | actions | 0 | 5 | 5 | declared flow | 5 | E4-P3-QA1 |
| P3 | Full unittest result | tests | 113 passed + 2 skipped | 117 passed + 2 skipped | 117 passed + 2 skipped | no regression | +4 passed | E4-P3-REGRESSION1 |

P3 arithmetic is CNY-only and deliberately keeps the historical received-group
expectation separate from the six currently sourced money events. The
`67,033.84966649559 CNY` difference is a measured reconciliation metric, not an
opening adjustment.

## B4 - P4 technical lineage reconciliation metrics

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P4 | Six received source oracles | rows | 6 | 6 | 6 | 6 | 0 | E4-P4A-REPRO1 |
| P4 | Pre-fix received staging total | CNY | 349,448.3929340609 | 349,448.3929340609 | 349,448.3929340609 | diagnostic only | 0 | E4-P4A-GAP1 |
| P4 | Pre-fix row delta sum | CNY | 67,033.84966649563 | 67,033.84966649563 | 67,033.84966649563 | source defect identified | 0 | E4-P4A-GAP1 |
| P4 | Reconciled received group | CNY | 349,448.3929340609 | 416,482.2426005565 | 416,482.2426005565 | exact/tolerant match | +67,033.8496664956 | E4-P4-RECON1 |
| P4 | C190/C197/C198 source subgroup | CNY | n/a (wrong physical rows) | 327,034.0 | 327,034.0 | exact | source mapping corrected | E4-P4A-REPRO1 |
| P4 | Row 86 parser proposal | CNY | 7,683.0 | 99,824.43 | 99,824.43 | E86 authoritative value | +92,141.43 | E4-P4A-E861 / E4-P4B-ROOT1 |
| P4 | Full paid-on-behalf group | CNY | 159,998.0 | 159,998.0 | 159,998.0 | exact | 0 | E4-P4-RECON1 |
| P4 | Historical position checkpoint | CNY | 228,610.3970659391 | 161,576.5473994435 | 161,576.5473994435 | checkpoint formula | corrected | E4-P4-OPEN1 |
| P4 | Confirmed staging items | items | 20 | 20 | 20 | Owner decisions only | 0 | E4-P4-COUNT1 |
| P4 | Review-required staging items | items | 170 | 170 | 170 | unresolved review remains | 0 | E4-P4-COUNT1 |
| P4 | Canonical financial writes | writes | 0 | 0 | 0 | 0 | 0 | E4-P4-QA1 / E4-P4-DI1 |
| P4 | Full unittest discovery | tests | 117 passed + 2 skipped | 120 passed + 2 skipped | 120 passed + 2 skipped | no regression | +3 passed | E4-P4-REGRESSION1 |
| P4 | Source workbook SHA-256 | hash | unchanged | unchanged | unchanged | unchanged | 0 | E4-P4-DI1 |

The `79,?` baseline is intentionally not used as a numeric benchmark: the pre-fix
staging values were three wrong physical rows and were not a valid C190/C197/C198
subgroup. The authoritative source subgroup is `327,034 CNY` after row mapping is
corrected.

## B5 - P5 cutover sufficiency metrics

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P5 | Staging items classified exactly once | items | 0 | 289 | 289 | 289 | +289 | E5-P5-CLASSIFY1 |
| P5 | Embedded-in-base items | items | 0 | 19 | 19 | derived | +19 | E5-P5-CLASSIFY1 |
| P5 | Post-base confirmed events | items | 0 | 0 | 0 | no unverified inclusion | 0 | E5-P5-CLASSIFY1 |
| P5 | Post-base review-required events | items | 0 | 7 | 7 | exact material list | +7 | E5-P5-POST1 |
| P5 | Reference-only items | items | 0 | 74 | 74 | no event double count | +74 | E5-P5-CLASSIFY1 |
| P5 | Not-applicable items | items | 0 | 122 | 122 | excluded from opening | +122 | E5-P5-CLASSIFY1 |
| P5 | Unresolved non-material items | items | 0 | 60 | 60 | no opening blocker | +60 | E5-P5-CLASSIFY1 |
| P5 | Unresolved material items | items | 0 | 7 | 7 | Owner decision required | +7 | E5-P5-MATERIAL1 |
| P5 | Opening-material blocker count | items | 0 | 14 | 14 | exact material pack | +14 | E5-P5-REDUCE1 |
| P5 | Review-required subset reduced | items | 170 | 170 | 170 | classify without blanket block | 0 | E5-P5-REDUCE1 |
| P5 | Known-CNY post-base review amount | CNY | 0 | 392,796.30579784507 | 392,796.30579784507 | currency-separated | +392,796.30579784507 | E5-P5-REDUCE1 |
| P5 | Candidate opening | CNY | 0 | 161,576.5473994435 | 161,576.5473994435 | reproducible base formula | +161,576.5473994435 | E5-P5-CANDIDATE1 |
| P5 | Checkpoint events counted | events | 0 | 0 | 0 | 0 | 0 | E5-P5-GRAPH1 |
| P5 | Canonical financial writes | writes | 0 | 0 | 0 | 0 | 0 | E5-P5-ORACLE1 |
| P5 | Focused sufficiency tests | tests | 0 | 16 passed | 16 passed | no failure | +16 | E5-P5-TEST1 |
| P5 | Full unittest discovery | tests | 120 passed + 2 skipped | 130 passed + 2 skipped | 130 passed + 2 skipped | no regression | +10 passed | E5-P5-TEST1 |
| P5 | Historical Review smoke exceptions | exceptions | n/a | 0 | 0 | 0 | 0 | E5-P5-QA1 |
| P5 | Source workbook SHA-256 | hash | unchanged | unchanged | unchanged | unchanged | 0 | E5-P5-SCOPE1 |

P5 metrics are staging/review evidence only. Currency totals are not combined
across CNY, USD, and UNKNOWN. The candidate is not a published opening.

## B6 - P6 blocker reconstruction metrics

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|---|---|---:|---:|---:|---:|---|---:|---|
| P6 | Staging items classified exactly once | items | 289 | 289 | 289 | 289 | 0 | E6-P6-CLASSIFY1 |
| P6 | Reference-only rows after goods-detail proof | items | 74 | 81 | 81 | derived | +7 | E6-P6-2132191 |
| P6 | Unresolved material rows | items | 7 | 0 | 0 | 0 after deterministic evidence | -7 | E6-P6-2132191 |
| P6 | Opening-material blocker rows | items | 14 | 7 | 7 | genuine unresolved only | -7 | E6-P6-CLASSIFY1 |
| P6 | Beginner Owner decisions | decisions | 7 row-level material rows | 2 grouped | 2 grouped | minimum genuine questions | reduction | E6-P6-2012051 / E6-P6-2292301 |
| P6 | Goods-detail subtotal match | CNY | n/a | 16,929.56 | 16,929.56 | exact within source precision | n/a | E6-P6-2132191 |
| P6 | June freight subtotal match | source currency unknown | n/a | 7,060 | 7,060 | exact | n/a | E6-P6-2292301 |
| P6 | Exact 418,060.79 source cells | cells | unknown | 0 | 0 | source-grounded or Owner-gated | 0 | E6-P6-4181 |
| P6 | Candidate opening | CNY | 161,576.5473994435 | 161,576.5473994435 | 161,576.5473994435 | unchanged until Owner confirmation | 0 | E6-P6-SCENARIO1 |
| P6 | Canonical financial writes | writes | 0 | 0 | 0 | 0 | 0 | E6-P6-ORACLE1 |
| P6 | Focused P6 tests | tests | 0 | 14 passed | 14 passed | no failure | +14 | E6-P6-TEST1 |

P6 metrics are read-only staging/review evidence. The 392,796.30579784507 CNY
and 392,790 CNY columns in rows 201–205 are kept as separate source legs, and
no VND/USD conversion or cross-currency net total is benchmarked.
