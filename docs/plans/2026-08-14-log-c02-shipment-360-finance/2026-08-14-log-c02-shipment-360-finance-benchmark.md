# LOG-C02 Shipment 360 — Benchmark and Measurements

## Metadata

- Date: `2026-08-14`
- Status: `bounded PASS` locally; overall `BLOCKED`
- Plan: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-plan.md`

## Measurement policy

This slice is a read-only projection. Measurements must describe source
inventory, test/build/runtime evidence, and graph scope; they must not require
writing a business fixture or measuring a production-money operation.

## Baseline measurements

| ID | Measurement | Value | Method / interpretation |
|---|---|---:|---|
| `B0-ANALYZE` | Files scanned | 87 | `anvien analyze --force` |
| `B0-PARSED` | Parsed code files | 53 | Anvien graph output |
| `B0-PARSE-FAIL` | Parse failures | 0 | Anvien graph output |
| `B0-NODES` | Graph nodes | 6,531 | Anvien graph output |
| `B0-EDGES` | Graph relationships | 7,246 | Anvien graph output |
| `B0-TESTS` | Existing test count | 24 tests / 9 files | Current repository test inventory |
| `B0-DOCKER` | Docker artifacts | 0 found | No Dockerfile/compose/runtime command in current project |

## Implementation measurements

| ID | Measurement | Value | Method | Status |
|---|---|---:|---|---|
| `B1-PROJECTION` | Shipment 360 projection runtime | 3/3 focused tests | Focused unittest with fixture mappings | PASS |
| `B1-UNIT` | Full Python test result | 27/27 | `python -m unittest discover -s tests -p "test_*.py"` | PASS |
| `B1-COMPILE` | Compile result | exit `0` | `python -m compileall -q .` | PASS |
| `B1-UI` | First-view browser render | PASS | Real local Streamlit/browser harness; health `200/ok` | PASS |
| `B1-NOWRITE` | Summary-triggered business writes | 0 observed | Source review + read-only browser flow | PASS |
| `B1-CHANGES` | Anvien change detection | 17 dirty files / 3,620 changed symbols / 74 affected nodes | `anvien detect-changes --repo Logistics-Pro-AI --scope all` | PASS WITH DIRTY BOUNDARY |

## B2 - P2 B0 measurements

| ID | Measurement | Value | Method | Status |
|---|---|---:|---|---|
| `B2-ANALYZE` | Current graph inventory | 99 scanned / 57 parsed / 0 failed / 7,249 nodes / 8,063 relationships | Fresh `anvien analyze --force` | PASS |
| `B2-DB-TOPOLOGY` | Isolated transaction capability | reachable / replica set / logical sessions | Read-only `hello` topology probe; no business write | PASS |
| `B2-BUSINESS-WRITES` | Business database writes during preflight | 0 | Source inspection and topology probe only | PASS |
| `B2-WRITE-PATHS` | Material financial write families mapped | 10 | B0 source matrix in evidence ledger | PASS |
| `B2-DOCKER` | Docker artifacts for B0 backend slice | 0 found | Repository inventory | BLOCKED/NOT APPLICABLE |

## B3 - P2 B0 fixture measurements

| ID | Measurement | Value | Method | Status |
|---|---|---:|---|---|
| `B3-MATRIX` | Required financial fixture cases | 14 | User-provided B0 matrix; 10 directly exercised in this checkpoint and the remaining ledger cases remain blocked by missing model support | PARTIAL |
| `B3-TESTS` | B0 safety test module | 6/6 targeted tests | `python -m unittest discover -s tests -p "test_financial_write_safety.py" -v` with isolated Mongo enabled; 4.339s | PASS |
| `B3-READBACK` | Fresh-client durable read-back | 3 bounded paths | Contract proxy pair, lump-sum payment, and shipment save | PASS |
| `B3-RETRY` | Retry/duplicate evidence | lump-sum PASS; direct payment GAP | Same-key lump-sum retry is idempotent; direct retry with new ID doubled fixture payment | PARTIAL |
| `B3-FAILURE` | Failure injection | proxy rollback PASS; entrustment batch GAP | Second-write failure tests | PARTIAL |
| `B3-FULL` | Full Python regression | 30 PASS / 1 opt-in skip | `python -m unittest discover -s tests -p "test_*.py" -v`; 2.714s | PASS |
| `B3-COMPILE` | Compile result | exit `0` | `python -m compileall -q .` | PASS |
| `B3-CLEANUP` | Fixture database cleanup | `fixture_database_leftovers=[]` | Exact-name revalidation after teardown | PASS |

## Interpretation rules

- A passing pure test proves deterministic projection behavior only; it does
  not prove Mongo durability.
- A passing browser flow proves visible read-only rendering only; it does not
  prove that the existing save/payment flows are safe.
- Runtime duration is useful as a record but is not a financial correctness
  claim.
- No benchmark result authorizes deployment or use with real money.
- `pytest` is not installed in the current project environment; the available
  unittest suite was used instead. No dependency was installed.
- B0 fixture measurements must never be interpreted as business-money evidence;
  they only prove the bounded repository boundary against synthetic data.

## B4 - Interpretation

The measured PASS applies only to the tested Contract proxy transaction,
lump-sum receipt idempotency, and single shipment persistence paths. The
material write family remains PARTIAL because direct payment request identity
and entrustment batch atomicity are not safe. No measurement authorizes Quick
Entry, ledger migration, or real-money operation.

## B5 - B1 pre-implementation measurements

| ID | Measurement | Value | Method | Status |
|---|---|---:|---|---|
| `B5-ANALYZE` | Fresh graph inventory | 105 scanned / 58 parsed / 0 failed / 7,594 nodes / 8,466 relationships | `anvien analyze --force` | PASS |
| `B5-HOTSPOT` | Selected dirty-file risk | `core/database.py` 476 unresolved; `views/shipment.py` 476; `views/entrustment.py` 178 | Anvien file projection | HIGH RISK |
| `B5-DIRECT-REPRO` | Direct duplicate baseline | 40,000 → 80,000 in B0 fixture attack | Runtime-authentic persistence fixture | CONFIRMED FAILURE |
| `B5-ENTRUST-REPRO` | Entrustment partial-write baseline | first document survives forced second failure | Runtime-authentic injected writer fixture | CONFIRMED FAILURE |
| `B5-SPEC` | Logistics SPEC family | 0 `Docs/SPEC` / `SPEC-MAP.md` found | Repository inventory | NOT PRESENT |

B1 implementation measurements will be appended after each verified batch;
the values above are the pre-change baseline and do not authorize Quick Entry.

## B6 - B1 final measurements

| ID | Measurement | Value | Method | Status |
|---|---|---:|---|---|
| `B6-ANALYZE` | Final graph inventory | 108 scanned / 58 parsed / 0 failed / 8,404 nodes / 9,421 relationships | `anvien analyze --force` | PASS |
| `B6-HOTSPOT` | Selected dirty-file risk | `core/database.py` 701 unresolved; `views/shipment.py` 506; financial tests 539 | Anvien file projection | HIGH RISK / DIRTY BOUNDARY |
| `B6-B1-FIXTURE` | Direct and entrustment B1 fixture tests | 7/7 pass in targeted run | `python -m unittest ...DirectFinancialWriteFixtureTests ...EntrustmentBatchFixtureTests` | PASS |
| `B6-FULL` | Full Python regression | 37 pass / 1 opt-in Mongo class skipped by default | `python -m unittest discover -s tests -p 'test_*.py' -v` | PASS |
| `B6-MONGO` | Disposable Mongo financial fixture | 6/6 pass | `LOG_C02_RUN_MONGO_FIXTURES=1 ...MongoPersistenceFixtureTests` | PASS |
| `B6-COMPILE` | Compile result | exit `0` | `python -m compileall -q core views tests scripts app.py web_app.py` | PASS |
| `B6-RUNTIME` | Streamlit health | `200 ok` | Local runtime `127.0.0.1:8509/_stcore/health`; stopped after check | PASS |
| `B6-CLEANUP` | Fixture database leftovers | `[]` | Read-only Mongo inventory after fixture teardown | PASS |

### B6 interpretation

These measurements prove the bounded B1 write-safety boundary only. They do
not authorize real-money operation, deployment, migration, Quick Entry, or a
broad obligation/allocation ledger. The concurrent Mongo test observed one
safe transient write-conflict return but one durable financial effect; retry
with the same request identity remains the required caller behavior.
