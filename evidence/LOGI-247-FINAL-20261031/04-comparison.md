# 04 — Collected-ID and skipped-ID comparison

All numbers below were recomputed from the raw artifacts in `02-run-a/` and `03-run-b/`; machine
readable form in `04-comparison.json`.

## 1. Full-run results

| Run | Worktree | Interpreter | Command | Exit | Result | Wall |
|---|---|---|---|---|---|---|
| A | `/tmp/wtA` @ `9012ee0` | `/tmp/venvA` (fresh) | `python -m pytest tests -q -rs -p no:cacheprovider` | **0** | 2359 passed, 44 skipped, 10 subtests passed, 0 failed, 0 error | 151.55 s |
| B | `/tmp/wtB` @ `9012ee0` | `/tmp/venvB` (fresh) | `python -m pytest tests -q -rs -p no:cacheprovider` | **0** | 2359 passed, 44 skipped, 10 subtests passed, 0 failed, 0 error | 160.48 s |

`stderr` was empty (0 bytes) in both runs. No `-k`, `--ignore`, `-x`, `--deselect` or config-based
deselection was used; no pytest config file exists at this HEAD, so no `addopts` could weaken the run.
Tokens `deselected`, `xfailed`, `xpassed` do not occur in either transcript: **0 xfail, 0 xpass,
0 deselected**.

Independence is visible inside the transcripts themselves: the aggregated skip summary names
`../venvA/lib/python3.11/site-packages/_pytest/unittest.py` in run A and
`../venvB/...` in run B — i.e. the two suites really executed under different interpreters, not twice
under one environment.

## 2. Collected IDs

| Item | Value |
|---|---|
| `--collect-only` count, run A | **2403** (`tests collected in 7.94s`, exit 0) |
| `--collect-only` count, run B | **2403** (`tests collected in 2.12s`, exit 0) |
| A set == B set | **YES** (`diff` empty) |
| sha256 of A id list | `552021c2b3c15c7ab43b8153c8123b08c698de990538fc7839317363022fd197` |
| sha256 of B id list | `552021c2b3c15c7ab43b8153c8123b08c698de990538fc7839317363022fd197` |
| passed + skipped | 2359 + 44 = **2403** ✔ (no silent disappearance) |

## 3. Collected IDs vs the S1 baseline (id-level diff, not a count claim)

Baseline source: the committed `evidence/issue247/s1/baseline-collection.json.gz` inside the PR HEAD
itself (`collected_count=2396`, `head=2941181d…`, `collected_sha256=aa581653…`).

- **Added: 7 genuine new test IDs**, all in `tests/test_intl_payment_comparator.py`:
  `test_s1_duplicate_key_replay_ignores_driver_id`,
  `test_s1_failed_lookup_never_inserts[no-index|unique-index]`,
  `test_s1_snapshot_replay_and_tamper_readback[no-index|unique-index]`,
  `test_s1_viewer_denied_with_readback[no-index|unique-index]`.
- **Lost: 0 genuine test IDs.**
- Raw diff shows one further line on each side that is *not* a real difference:
  `tests/test_excel_quote_import_v1.py::test_unsafe_or_unsupported_workbooks_rejected[…]` — the S1
  JSON recorded the parametrized payload as a long `xxxx…` placeholder, the live collector reports
  `[big.xlsx-data3]`. Same test, redacted parameter on the recorded side only.
- Arithmetic check: 2396 + 7 = **2403** ✔

## 4. Skipped IDs

| Item | Value |
|---|---|
| Skipped, run A | **44** |
| Skipped, run B | **44** |
| Skipped in S1 baseline | **44** |
| A set == B set | **YES** |
| A set == S1 set | **YES** (byte-identical after sort) |
| sha256 of the 44-id set | `12acbd9f7af86e099efc92f651eb3b2004abf0df7b871e7023441e04547a430d` |

Exact identity was obtained from xunit junit (`02-run-a/skipped-junit.xml`, `03-run-b/skipped-junit.xml`)
of a focused replica over the only seven files that contain a skip site, run separately in each env
(139 passed / 44 skipped, exit 0, 1.64 s and 1.69 s). Both full runs independently reported
`44 skipped` with identical per-site counts, so the focused replica is a projection of the same set,
not a substitute for the full runs.

Per-class distribution (identical in A, B and S1):

| Class | Skips | Reason (from `-rs`) |
|---|---:|---|
| `test_financial_ledger.MongoFinancialLedgerFixtureTests` | 1 | `set LOG_C02_RUN_MONGO_FIXTURES=1 for isolated Mongo proof` |
| `test_financial_write_safety.MongoPersistenceFixtureTests` | 6 | same |
| `test_historical_owner_decisions.HistoricalOwnerDecisionTests` | 4 | `Historical source workbook is unavailable: D:\Copy of TOYS-2025 - Copy.xls` |
| `test_historical_review_analysis.HistoricalReviewAnalysisTests` | 5 | same |
| `test_historical_staging.HistoricalStagingTests` | 12 | same |
| `test_lg05_excel_roundtrip_gnt.TestExcelExportRoundTrip` | 1 | `Owner's Excel file not present in test environment` |
| `test_lg05_excel_roundtrip_gnt.TestExcelRoundTrip` | 5 | same |
| `test_log_docgen_01.RbacTests` | 3 | `Template assets not present` / `Requires local templates` / `no assets` |
| `test_log_docgen_01.TemplateGenerationTests` | 6 | same |
| `test_log_docgen_01.VersionAndLinkageTests` | 1 | same |
| **total** | **44** | 7 mongo + 21 historical workbook + 6 excel + 10 docgen |

**`SKIP_EXPANSION=NO`** — no skip was added, and no previously skipping ID moved to a different reason
category.

## 5. What this comparison does and does not prove

Proves: on `9012ee0`, two separate interpreters executed the same 2403 collected IDs, both exited 0
with 0 FAILED / 0 ERROR, and the skipped set is unchanged versus the S1 baseline.

Does **not** prove: real Mongo/Atlas durability or concurrency (the 7 Mongo-proof tests are skipped by
design and ran under `mongomock`-free skip), Cloud runtime, Google OIDC, or Chromium UI behaviour on
this HEAD. `MONGO_PROOF=SKIPPED_BY_DESIGN`, `CLOUD_OIDC=NOT_VERIFIED`, `S2/S3_BROWSER=NOT_RERUN`.
