# LOG-C06 Historical A Bo Staging and Opening Position Evidence Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-actual-status.md`

## Evidence Rules

The evidence ledger explains why LOG-C06 behavior is known to be correct.

- Evidence IDs are exact and phase-scoped.
- Workbook evidence is read-only and must include source fingerprint/provenance.
- Tests prove trigger -> processing -> observable result; static/source-reading checks are supporting evidence only.
- Staging/review writes must be distinguished from canonical financial effects.
- Unknown, review-required, checkpoint, and unresolved values are evidence, not defects to hide.
- Docker and positive live data limitations are reported explicitly.
- No evidence may claim AI classification, live migration, opening approval, or canonical ledger publication.

### Evidence ID Naming

Use `E<phase>-<item>-<kind><n>`; examples include `E0-P0A-WB1`,
`E1-P1A-RULES1`, `E2-P2A-ORACLE1`, and `E3-P3B-BROWSER1`.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REQ1`: attached LOG-C06 brief defines raw Excel -> staging -> deterministic normalization -> review -> confirmed mapping -> draft opening -> cutover readiness, and forbids live migration, AI, Quick Entry, arbitrary SALE inference, and canonical financial mutation.
- `E0-P0A-GIT1`: `git status --short --branch` shows `main` ahead of origin with a known dirty worktree containing LOG-C01 through LOG-C05 source, tests, reports, archives, and P2P state; no reset/checkout/broad stage is permitted.
- `E0-P0A-P2P1`: `p2p_workflow.py inspect --json` classified the request as a bounded direct task with existing project profile/policy/eval; `run --json` was attempted and stopped on a permission error reading a locked prior QA cache file under `.tmp\log-c05-browser-profile-7`, so no formal PASS is claimed.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed for `D:\Logistics_App_Copy`; graph reported 166 files scanned, 77 parsed code files, 0 parse failures, 13,814 nodes, 15,787 relationships, and a built 166-file projection.
- `E0-P0A-SRC1`: `D:\Copy of TOYS-2025 - Copy.xls` exists, is 316,416 bytes, and had SHA-256 `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70` before implementation.
- `E0-P0A-WB1`: read-only `xlrd` inspection found 8 sheets; `Sheet2` has 282 rows and 14 columns. Golden source evidence includes workbook rows 17/103/110/97/100/130 for 24,576/62,464/1,687/1,572/25,025/134,973, plus row 36 date `2026-12-18` in a surrounding 2025/early-2026 sequence.
- `E0-P0A-IMPACT1`: Anvien file-detail/impact evidence shows `views/partner_reconciliation.py` has 80 symbols, 35 local relationships, 4 inbound references, 13 linked flows, and high file risk; `views/web_app.py` has 22 symbols, 16 local relationships, 1 linked flow, and high file risk; `core/database.py` and `core/financial_ledger.py` are high-risk shared financial surfaces with approximately 137 symbols and 75 linked flows; `core/reconciliation.py` has 73 symbols, 31 local relationships, 11 linked flows, and high risk.
- `E0-P0A-FLOW1`: current route registry mounts `Công nợ A Bò` to `views.partner_reconciliation.ui_partner_reconciliation_desk`; Dashboard remains first. Existing LOG-C04/C05 plans and supervisor reports record read-only canonical projection, report/debit modes, and no financial effects.
- `E0-P0A-SAFETY1`: existing C02-C05 tests/reports contain canonical ledger write oracles, C04 desk write oracle, C05 report/debit write oracle, and full-suite evidence; these surfaces are preserve-only regression boundaries for LOG-C06.
- `E0-P0A-RUNTIME1`: no Dockerfile or docker-compose target was found in the project root; local Streamlit is the available runtime and any Docker acceptance must remain explicitly blocked/unclaimed.
- `E0-P0A-AUTH1`: no `Docs/SPEC` cluster or `SPEC-MAP.md` exists in this application; the attached LOG-C06 brief plus `AGENTS.md` and existing C02-C05 contracts are the current scope authority.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-GRAPH1`: record refreshed Anvien graph counts after the pure staging module is added.
- `E1-P1A-MODEL1`: record the staging item contract, raw/proposal separation, source ID/hash behavior, and import boundary.
- `E1-P1A-RULES1`: record deterministic SALE, currency, event-type, and anomaly rule tests.
- `E1-P1A-ORACLE1`: record pure parser output and zero imports/calls to canonical financial modules.
- `E1-P1B-GOLD1`: record isolated golden source rows for 24,576, 62,464, 1,687, 1,572, 25,025, and 134,973.
- `E1-P1B-TRACE1`: record 134,973 component source IDs and checkpoint row separation.
- `E1-P1B-ANOMALY1`: record date sequence, missing/inherited date, missing currency/SALE/party, duplicate-looking, unclear amount, and linkage anomaly results.
- `E1-P1B-HASH1`: record identical source SHA-256 before and after parser/fixture validation.

### E1 - P1 implementation results

- `E1-P1A-GRAPH1`: after adding the pure staging module, `anvien analyze --force`
  completed with 171 files scanned, 78 parsed code files, 0 parse failures, 14,476
  graph nodes, 16,582 relationships, and a built 171-file projection. The new module
  is isolated from the existing high-risk canonical files.
- `E1-P1A-MODEL1`: `stage_workbook()` produced 289 deterministic items across the
  workbook's 8 sheets. Each item carries `source_file`, source SHA-256, sheet, source
  row, cell range/reference, raw cell map/types/text, date/inherited-date context,
  parser version, proposal, review status/reason, anomaly flags, and review history.
  Raw values remain separate from the proposal object.
- `E1-P1A-RULES1`: the focused behavior matrix proved 47 amount-bearing explicit
  `SALE=Thành` rows, 5 high-confidence `PROPOSED` rows, 185 `REVIEW_REQUIRED` rows,
  and 60 amount-bearing other-sale rows. Free-text `món của Thành` remains a
  review-only candidate and does not set `internal_sale_owner`.
- `E1-P1A-ORACLE1`: static import-boundary test and module inspection show no
  Streamlit, Mongo/DB, canonical financial-ledger, or `get_db` dependency in the pure
  parser. The focused test run completed without a canonical write path.
- `E1-P1B-GOLD1`: exact Sheet2 source rows are staged for 24,576 (row 16), 1,572
  (row 96), 25,025 (row 99), 62,464 (row 102), 1,687 (row 109), and 134,973 (row
  129). Each retains a `Sheet2!<cells>` source reference and the source SHA-256.
- `E1-P1B-TRACE1`: the 134,973 row is classified as `adjustment` with checkpoint key
  `THANH_ACCUMULATED`, `CHECKPOINT_EVIDENCE`, and no candidate opening bucket; it is
  not treated as a confirmed component or opaque canonical balance.
- `E1-P1B-ANOMALY1`: the parser flags 231 items with anomalies (483 individual flags),
  including the 2026-12-18 out-of-sequence date, inherited dates, unknown currency,
  missing SALE/party, duplicate-looking rows, and checkpoint review. No raw date or
  amount is auto-corrected.
- `E1-P1B-HASH1`: `tests.test_historical_staging` ran 11 tests and passed. The source
  remained SHA-256 `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`
  before and after parsing/validation. The FX row retains 100,000,000 VND, rate 3,953,
  and 25,297.24260055654 CNY as separate related context.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-STORE1`: record staging-only collection names/indexes, import upsert behavior, and source/proposal preservation.
- `E2-P2A-REVIEW1`: record confirm, correct, not-Thanh, unknown, prior-history, actor/time/reason, and conflicting retry behavior.
- `E2-P2A-WRITE1`: record staging/audit collection deltas for a fake DB import/review flow.
- `E2-P2A-ORACLE1`: record canonical financial collections and financial writer call count remain zero.
- `E2-P2B-POSITION1`: record currency-separated opening buckets and confirmed-only inclusion/exclusion arithmetic.
- `E2-P2B-CURRENCY1`: record CNY/USD/VND/UNKNOWN separation, documented FX context preservation, and no current-rate recalculation.
- `E2-P2B-CHECKPOINT1`: record exact-match, difference, and unknown-semantics checkpoint outcomes.
- `E2-P2B-CUTOVER1`: record reproducible `CUTOVER_DRAFT` hash/version, source IDs, excluded IDs, unresolved amount, and allowed status set.

### E2 - P2 implementation results

- `E2-P2A-STORE1`: `core/historical_staging_store.py` defines the isolated collection
  boundary `legacy_historical_staging` and `legacy_historical_review_actions`, with
  unique source-item/request indexes and a source-hash/sheet/row lookup index. The
  store accepts a database-like dependency and does not import the canonical DB provider.
- `E2-P2A-REVIEW1`: actions `confirm`, `correct`, `not_thanh`, and `unknown` record
  request ID, actor, timestamp, reason, before/after status, proposal hashes, and
  review version. Corrections are allowlisted to proposal fields; raw source fields
  cannot be patched. Stale review versions and request reuse conflicts fail closed.
- `E2-P2A-WRITE1`: the fake-DB oracle observed two staging inserts, retry-safe staging
  replacements, and staging/audit updates only. Raw values and source provenance
  survived import retries and review corrections; no canonical collection was created
  or changed.
- `E2-P2A-ORACLE1`: `tests.test_historical_staging_store` passed with zero recorded
  canonical accesses/writes. Static inspection confirms no `core.database`,
  `financial_ledger`, or canonical financial collection dependency in the store.
- `E2-P2B-POSITION1`: `core/historical_opening.py` includes only `CONFIRMED`,
  known-currency, non-checkpoint components. It returns explicit buckets for payable,
  payment-to-A-Bò settled, held credit, received-on-behalf available,
  paid-on-behalf settled, unallocated confirmed, and restricted confirmed. Review,
  proposed, unknown-event, checkpoint, and unresolved rows remain in exclusions with
  source traces. `cross_currency_total` is always `None`.
- `E2-P2B-CURRENCY1`: pure tests prove CNY/USD/VND remain separate and an FX context
  retains related amount/currency/rate metadata without recalculating with a current rate.
  Negative amounts remain signed inside their explicitly classified bucket; sign alone
  is not treated as a debit/credit instruction.
- `E2-P2B-CHECKPOINT1`: explicit component IDs plus a declared `sum`/`difference`
  formula can produce `EXACT_MATCH` or `DIFFERENCE`; the workbook's 134,973 checkpoint
  has no explicit component linkage and therefore remains `UNKNOWN_SEMANTICS`, excluded
  from the opening position rather than treated as an opaque component.
- `E2-P2B-CUTOVER1`: `tests.test_historical_opening` passed reproducible snapshot
  hash/draft ID checks. Clean confirmed fixtures produce `READY_FOR_OWNER_REVIEW`,
  while review/unknown/checkpoint gaps produce `DRAFT` + `NOT_READY`. Drafts carry
  source IDs, exclusions, per-currency position, readiness reasons, version/hash,
  `canonical_mutations=0`, `approval_status=NOT_APPROVED`, and `live_status=NOT_LIVE`.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-UI1`: record the mounted path from existing A Bò desk to Historical Review and summary sections.
- `E3-P3A-REVIEW1`: record bounded search/source evidence/review action UI behavior for 62464 and 1572.
- `E3-P3A-ORACLE1`: record UI render behavior with in-memory staging and no canonical data mutation.
- `E3-P3A-WRITE1`: record review confirmation/correction updates only staging metadata and preserves raw evidence/history.
- `E3-P3B-DRAFT1`: record per-currency opening position, unresolved exclusion, and cutover readiness panel.
- `E3-P3B-TRACE1`: record “Vì sao opening position ra số này?” source row/cell trace.
- `E3-P3B-BROWSER1`: record actual Streamlit runtime URL, health result, Playwright command, screenshots, and user journey result.
- `E3-P3B-CONSOLE1`: record browser console/page error and warning counts attributable to LOG-C06.
- `E3-P3B-REGRESSION1`: record LOG-C02, LOG-C03, LOG-C04, LOG-C05 focused regression and full-suite results.
- `E3-P3B-BUILD1`: record full build attempt, compileall, and Docker target availability/blocker.

### E3 - P3-A implementation results

- `E3-P3A-UI1`: `views/partner_reconciliation.py` adds one `Historical Review` mode
  button and one early mode branch. The branch runs before the canonical partner
  projection; existing desk/report/debit modes remain in their original order and the
  global route registry is unchanged.
- `E3-P3A-REVIEW1`: recorder UI tests search the golden `62464` row, render its
  `Sheet2!D62464` source evidence, and render the staging proposal/status/anomaly
  fields. The review inbox also includes the `1572`/`1687` paths in the fixture matrix.
- `E3-P3A-ORACLE1`: the Historical Review route test patches canonical projection to
  raise if called; the route completes without evaluating it. The UI module has no
  financial-ledger or canonical writer import.
- `E3-P3A-WRITE1`: session-only confirm action changes only the session staging document,
  appends one review audit record, preserves raw evidence, and requests a rerender.
  The staging DB path uses the isolated collection names from P2-A; DB failure is
  visible as `session-only` rather than silently treated as durable.

### E3 - P3-B implementation and runtime results

- `E3-P3B-DRAFT1`: the mounted page renders per-currency CNY buckets, confirmed-only
  opening inputs, excluded unresolved rows, checkpoint reconciliation, deterministic
  draft ID/snapshot, and `NOT_READY` reasons. The current source has zero confirmed
  staging rows, remaining review/unknown-currency work, and an unreconciled 134,973
  checkpoint, so no opening amount is presented as live.
- `E3-P3B-TRACE1`: the visible source-evidence path retains source sheet/row/cell
  references. Searches for 24,576, 62,464, 1,687, 1,572, 25,025, and 134,973 all
  returned the matching staged evidence in the browser.
- `E3-P3B-BROWSER1`: `playwright/log_c06_historical_review_flow.mjs` ran against
  `http://127.0.0.1:8520/` using visible Chrome and a repo-local profile. The official
  result is `reports/QA/playwright/2026-08-15-log-c06-historical-review.json` plus
  `.md`; the action ledger is 13/13 PASS, including root Dashboard, A Bò desk,
  Historical Review, six searches, NOT_READY panel, no-reason validation, and return
  to Dashboard. Screenshots were captured at each declared action checkpoint and
  visually inspected.
- `E3-P3B-CONSOLE1`: browser console errors `0`, warnings `0`, page errors `0`, and
  failed requests `0` in the final visible run.
- `E3-P3B-REGRESSION1`: LOG-C02 regression passed 14 tests with 1 Mongo-gated skip;
  LOG-C03 passed 7 module-level dashboard tests; LOG-C04 passed 13 tests; LOG-C05
  passed 16 tests; LOG-C06 focused staging/opening/UI suite passed 27 tests; full
  unittest discovery passed 107 tests with 2 Mongo-gated skips. The 7 module-level
  dashboard tests were invoked directly because pytest is not installed locally.
- `E3-P3B-BUILD1`: `python -m compileall -q core views tests` passed; reusable flow
  syntax check passed with bundled Node; Streamlit `/_stcore/health` returned `200/ok`.
  No Dockerfile or compose target exists, so Docker/production acceptance remains
  explicitly blocked and unclaimed.
- `E3-P3B-WRITE1`: the visible review test clicked `Xác nhận` without a reason and
  observed `Nhập lý do review trước khi ghi metadata staging.`; no review mutation,
  canonical ledger write, approval, or live/cutover control was executed.

## Closure Evidence

- `E4-CLOSE-DETECT1`: fresh Anvien graph refresh completed with 183 files scanned, 86 code files parsed, and 0 parse failures. `anvien detect-changes --repo Logistics-Pro-AI --scope all` completed successfully after refresh. The output is intentionally noisy because the worktree contains pre-existing user/C01-C05 changes; it was not presented as a LOG-C06-only diff.
- `E4-CLOSE-SHA1`: final source workbook size is 316,416 bytes and SHA-256 is `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`, unchanged from `E0-P0A-SRC1`.
- `E4-CLOSE-SUPERVISOR1`: `reports/supervisor/rp_supervisor_260815_013536_by_gpt-5-codex_log-c06-historical-staging-opening-position.md` records `PASS` for the bounded local scope, while explicitly retaining `NOT_READY` for cutover and owner approval/live publication as future gates.
- `E4-CLOSE-GIT1`: implementation commits are `9792bad`, `b1c5a34`, `33016fe`, and `1b6d54e`; the closure commit is recorded after scoped staging. Pre-existing dirty files, including the deleted `Logistics_App.rar`, were not reset, cleaned, or staged.
