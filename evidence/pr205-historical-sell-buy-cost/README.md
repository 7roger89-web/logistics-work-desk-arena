# New evidence — PR #205 historical SELL ≠ BUY COST repair

This directory is **new repair evidence only**, not the earlier `../excel-quote-import-v1/` acceptance run.

- Reviewed parent: `2c77bee0d563c6c3481792a3b6e603cc0365a343`.
- [Repair report, scope, commands and still-open gates](../../docs/PR205_HISTORICAL_SELL_BUY_COST_REPAIR.md).
- **Current final run:** `browser.txt` / `browser-results.json`: 11 PASS on the real app with native Streamlit–React–C1, sandbox DB transport only.
- 6 current screenshots at this directory's top level: QUOTE comparison-only, ACTUAL UNKNOWN, ACTUAL 32m/new SELL blank, INPUT_RATE 31.8m/new SELL blank, expiry warning, mobile non-cost label.
- `history-integrity.json`: whole-record before/after fingerprints, original SELL 40m and actual costs UNKNOWN/32m unchanged.
- `python-regression.txt`: 73 PASS (17 new read-truth regression cases + 56 existing Excel/cost tests).
- `finance-compatibility.txt`: 31 PASS; 2 known baseline catalog checks deselected, not counted as PASS.
- `unit-regression.txt`: 7 semantic assertion groups PASS. `existing-matcher.txt` and `existing-parser.txt`: prior matcher/parser regression results.
- `existing-costcheck-dom.txt`: 13 PASS on built-bundle DOM quote/CostCheck steps 1–8c, deliberately not a Journey/full-suite result. Its synthetic actual rows now explicitly state unit.
- `typecheck.txt`, `build.txt`, `bundle-scan.txt`: PASS; no dependency change.
- `regression-before.txt`: reviewed-head ACTUAL fallback incorrectly returns SELL 40m instead of UNKNOWN.
- `real-read-before.txt` + `attempt-1/`: first real browser run discovered UNKNOWN normalized into 0; fixed by the bounded component-read opt-in. These are FAILED pre-repair evidence, **not** current PASS.
- `attempt-2/`: amount/blank-SELL assertions passed, then a test asserted a browser-only supplier note field that C1 canonically replaces. Final test checks immutable supplier/snapshot/row provenance instead; no product-authority weakening.
- `python-extended-existing-catalog-failures.txt`: exploratory 84 PASS / 2 FAIL. `baseline-existing-catalog-failures.txt`: the same two failures on an untouched archive of the reviewed head. Neither is claimed repaired or silently counted green.
- `environment.json` / `source-and-evidence-sha256.json`: runtime/source/proof provenance.

**UAT_PENDING**: the public-preview probe failed with `ERR_CONNECTION_CLOSED` (`preview-reachability.json`). No verified Owner test URL is supplied. All acceptance servers are stopped; internal loopback URLs in automation logs are not Owner instructions.

**Original Lục Giác workbook and real MongoDB staging acceptance remain NOT_RUN/unaccepted.** Historical records and workbook are explicitly synthetic. Mongomock is not proof of real Mongo durability, transactions, replication or restart behavior. No production DB, main merge or deployment.
