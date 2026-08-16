# LOG-C06 Owner Review and Reconciliation Phase Evidence Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-actual-status.md`

## Evidence Rules

This ledger records current source facts, deterministic analysis, implementation behavior,
runtime evidence, safety checks, and final closure. Derived readiness is never treated as
confirmation. Long metric tables belong in the benchmark ledger.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-OWNER1`: Owner authorized staging/review/correct/reconcile work and explicitly denied canonical ledger writes, publish/live cutover, migration, Quick Entry, AI, payment writes, and free-text SALE inference. No new Goal Contract is authorized.
- `E0-P0A-SRC1`: `D:\Copy of TOYS-2025 - Copy.xls` is present, read-only, 8 sheets, Sheet2 282x14, SHA-256 `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
- `E0-P0A-GOLD1`: actual Sheet2 rows 16, 96, 99, 102, 109, and 129 contain the six requested amounts and source notes; surrounding rows were read directly from the workbook.
- `E0-P0A-CHECKPOINT1`: rows 103-121 contain candidate business lines for the 134,973 checkpoint; rows 103-108, 111, 114, 116, 120, and 121 total exactly 134,973 CNY, while rows 109 and 115 are separate received/FX rows.
- `E0-P0A-GRAPH1`: fresh Anvien graph refresh reports 183 scanned files, 86 parsed code files, 0 parse failures, and a non-stale index at commit `94a7349`.
- `E0-P0A-IMPACT1`: `views/historical_review.py` file-detail reports 71 symbols, 40 local relationships, 3 inbound references, 6 linked flows, high risk; upstream impact reports 16 contained symbols and 4 affected process hits. The UI edit is restricted to a minimal import/render seam.
- `E0-P0A-BASELINE1`: prior LOG-C06 implementation is committed and bounded; staging parser, staging store, confirmed-only opening model, and no-canonical-mutation tests already exist and are preserve-only for this continuation.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-GOLD1`: `build_review_analysis()` returns the six source rows in the requested order: Sheet2 rows 16, 102, 109, 96, 99, and 129, with amounts 24,576; 62,464; 1,687; 1,572; 25,025; and 134,973 CNY. Each derived row retains its staged `source_reference` and includes business meaning, money source/location, certainty, recommendation, and an Owner question.
- `E1-P1A-CHECKPOINT1`: bounded Sheet2 context before staged row 129 yields component rows 103, 104, 105, 106, 107, 108, 111, 114, 116, 120, and 121. Rows 109 (1,687 CNY received-on-behalf) and 115 (25,297.24260055654 CNY FX context) are explicitly excluded as separate money legs.
- `E1-P1A-ORACLE1`: Decimal subset-sum result is `EXACT_MATCH_CANDIDATE`, one exact solution, component sum `134,973.0` CNY, difference `0.0`, checkpoint excluded from components, and opening inclusion locked false. This is arithmetic evidence only, not Owner confirmation.
- `E1-P1B-CLUSTER1`: all 185 current `REVIEW_REQUIRED` rows are assigned exactly once to 10 deterministic clusters. Counts are: UNKNOWN currency 75; checkpoint/summary 27; likely duplicate 4; paid-on-behalf 9; material ambiguity 15; inherited-date-only 34; customer receipt leg 1; received-on-behalf 2; explicit SALE missing event 6; FX context 12.
- `E1-P1B-READY1`: derived state counts are `READY_FOR_OWNER_CONFIRMATION=13`, `REVIEW_REQUIRED=83`, `UNKNOWN=133`, `NOT_APPLICABLE=60`; current staged statuses remain `RAW=39`, `PROPOSED=5`, `REVIEW_REQUIRED=185`, `NOT_APPLICABLE=60`, with zero `CONFIRMED` rows. The six-item Owner Decision Pack is bounded to six decisions and keeps `DRAFT / NOT_APPROVED / NOT_LIVE`.

Verification:

- `python -m unittest tests.test_historical_review_analysis tests.test_historical_staging tests.test_historical_opening -v`: 22 passed.
- `python -m compileall -q core/historical_review_analysis.py tests/test_historical_review_analysis.py`: passed.
- `git diff --check` for the P1 files and plan directory: passed.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

Completed implementation/runtime evidence:

- `E2-P2A-UI1`: `views/historical_review.py` consumes `build_review_analysis()` through
  one bounded render seam. The visible route contains six golden cards, ten cluster
  groups, the six-decision Owner Decision Pack, and the checkpoint component table.
  `tests.test_historical_review_ui` verifies the business review map exposes Owner
  decisions while canonical controls remain absent.
- `E2-P2A-ORACLE1`: analysis output reports zero canonical mutations; the pure module
  imports no database/store/ledger writer. Browser control inventory found no canonical
  controls, and attempting a confirmation without a reason was blocked by the existing
  staging review guard. No `CONFIRMED` row was created.
- `E2-P2A-BROWSER1`: official report
  `reports/QA/playwright/2026-08-15-log-c06-owner-review-phase.json` and its Markdown
  companion record a clean visible run at `http://127.0.0.1:8531/`: golden evidence,
  clusters, decision pack, checkpoint reconstruction, no-reason guard, and Dashboard
  return all passed (`6/6`, no console/page/request failures). The runtime reported
  staging DB mode; the local runtime is evidence only, not production acceptance.
- `E2-P2B-REGRESSION1`: focused analysis/UI/staging/opening suite passed `27/27`;
  full discovery passed `113`, with `2` existing environment-guarded skips. No
  LOG-C06 regression was observed.
- `E2-P2B-BUILD1`: `python -m compileall -q core views tests` passed;
  `node --check playwright/log_c06_owner_review_phase.mjs` passed; `/healthz` on the
  clean local runtime returned HTTP 200; `git diff --check` passed; the source workbook
  hash remained `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
  No repository Docker target was found, so Docker acceptance is not claimed.

## Closure Evidence

Closure evidence:

- `E3-CLOSE1`: final Anvien refresh is non-stale with 192 files scanned, 89 parsed code
  files, and 0 parse failures. `file-detail` for `views/historical_review.py` reports
  84 symbols, 44 local relationships, 4 inbound references, 6 linked flows, and high
  risk; upstream impact reports 18 contained symbols and 4 affected process hits.
  Final `detect-changes --scope all` reports 21 dirty files / 4,228 changed symbols
  and 18 affected files / 101 affected processes at critical aggregate risk because
  unrelated pre-existing worktree changes are included. The LOG-C06 scoped commit
  stages only the analysis, review UI, tests, reusable QA script, official QA report,
  and plan artifacts; unrelated changes remain unstaged. The implementation slice is
  committed as `05ebe65`; coder and supervisor reports are included in the closure
  artifact set, with no unrelated file staged.

## E4 - P3 Owner-decision staging evidence

Matching plan item(s): `P3-A`, `P3-B`, `P3-C`, `P3-D`, `P3-E`

- `E4-P3-SOURCE1`: the read-only workbook remained unchanged at SHA-256
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
  The source rows applied by the batch are 16, 99, 102, 103, 104, 105, 106,
  107, 108, 109, 111, 114, 115, 116, 120, 121, 129, 190, 197, and 198.
  Row 96 (1,572 CNY) is deliberately excluded from the batch and remains
  `REVIEW_REQUIRED`.
- `E4-P3-BATCH1`: the audited staging batch is
  `LOG-C06-OWNER-DECISIONS-2026-08-15`. It has 20 deterministic request IDs;
  the replay run returned `idempotent_count=20`, `applied_count=0`, and did not
  create duplicate review actions. Staging item count remains 289 and audit
  action count remains 20.
- `E4-P3-STATUS1`: stored review statuses after the Owner batch are
  `CONFIRMED=20`, `REVIEW_REQUIRED=170`, `RAW=39`, `NOT_APPLICABLE=60`, and
  `PROPOSED=0`. The analysis-level Owner state counts are
  `CONFIRMED=20`, `REVIEW_REQUIRED=77`, `UNKNOWN=132`, and
  `NOT_APPLICABLE=60`; `UNKNOWN` is an analysis state, not a new stored review
  status.
- `E4-P3-24576`: row 16 is `refund_return_credit`, with lineage
  `24,576 -> checkpoint 99,824.43 -> opening lineage`; its opening inclusion is
  `embedded_in_snapshot`, standalone opening amount is zero, and the batch
  guard forbids reapplying the credit or adding the snapshot as a new event.
- `E4-P3-RECEIVED1`: rows 102 (62,464 CNY) and 109 (1,687 CNY) are separate
  `received_on_behalf` events for internal sale owner Thành. Shipment linkage
  remains unresolved/unallocated where the source does not prove an ID.
  The six received-group source rows 102, 109, 115, 190, 197, and 198 total
  `349,448.3929340609 CNY` against the historical expectation
  `416,482.2426005565 CNY`.
- `E4-P3-1572`: row 96 remains visible in Owner Review and is excluded from the
  confirmed opening buckets and debit eligibility. No ownership inference was
  added from the phrase “món của Thành”.
- `E4-P3-BG1`: row 99 (25,025 CNY) preserves two money legs: customer receipt
  into Trường Thành and A Bò paid/transferred on behalf to B&G Green. The
  customer receipt is not treated as settlement of A Bò's paid-on-behalf leg.
- `E4-P3-CHECKPOINT1`: row 129 is a confirmed summary checkpoint, not an event.
  Its 11 component rows (103, 104, 105, 106, 107, 108, 111, 114, 116, 120,
  121) sum exactly to `134,973 CNY`; the summary is excluded from components.
  The derived paid-on-behalf group is `134,973 + 25,025 = 159,998 CNY`
  across 12 source components, with the derived total excluded as an additional
  event.
- `E4-P3-HISTORICAL1`: the historical formula remains a reconciliation
  checkpoint only: `418,060.79 + 159,998 - 416,482.2426005565 =
  161,576.5473994435 CNY`. Replacing the expected received group with the six
  currently identified source cells yields `228,610.3970659391 CNY`, leaving a
  material `67,033.84966649559 CNY` difference. No value is auto-filled and no
  current opening balance is published.
- `E4-P3-OPENING1`: the draft has 18 confirmed financial components (12 paid
  components and 6 received components); the embedded 24,576 credit and the
  134,973 summary are explicit exclusions. The CNY draft buckets are
  `paid_on_behalf=159,998.0`, `received_on_behalf=349,448.3929340609`, and
  `held_credit=0.0` because the credit is embedded. Readiness is `NOT_READY`
  with `OWNER_CHECKPOINT_DIFFERENCE` and unresolved legacy checkpoint/review
  gates.
- `E4-P3-ORACLE1`: `canonical_writes=0`, `canonical_collections_touched=[]`,
  `opening_published=false`, and the state remains
  `DRAFT / NOT_APPROVED / NOT_LIVE`. The staging batch only uses
  `legacy_historical_staging` and `legacy_historical_review_actions`.
- `E4-P3-QA1`: official visible-browser evidence is in
  `reports/QA/playwright/2026-08-15-log-c06-owner-decisions-phase.json` and
  `.md`: 5/5 actions passed, HTTP 200, zero console/page/request failures,
  zero canonical controls, and the 1,572 CNY row still displayed
  `REVIEW_REQUIRED`.
- `E4-P3-REGRESSION1`: `python -m compileall -q .` passed; focused LOG-C06
  tests passed 26/26; full unittest discovery passed 117 tests with 2 guarded
  skips; and `node --check playwright/log_c06_owner_decisions_phase.mjs`
  passed.
- `E4-P3-SUPERVISOR1`: the fresh supervisor report records a bounded PASS for
  staging/review only and keeps the material checkpoint difference as a real
  Owner decision item. The full-worktree Anvien risk is reported separately
  because unrelated dirty files are preserved and were not staged.

## E4 - P4 technical lineage reconciliation evidence

Matching plan item(s): `P4-A`, `P4-B`, `P4-C`

- `E4-P4A-REPRO1`: read-only source probe verified `C102=62,464`, `C109=1,687`, `C115=25,297.24260055654`, physical `C192=183,549`, physical `C199=19,000`, and physical `C200=124,485` CNY. The historical labels C190/C197/C198 are aliases for those late physical rows; the physical cells C190/C197/C198 contain `78,000`, `121,643.15033350437`, and `60,357` instead.
- `E4-P4A-GAP1`: pre-fix row deltas were `0`, `0`, `0`, `+105,549`, `-102,643.15033350437`, and `+64,128` CNY. Decimal sum is `67,033.84966649563` CNY; the Owner-provided `...559` display is the corresponding binary/rendered rounding. No balancing event was created.
- `E4-P4A-E861`: source row 86 contains `D86="cua thanh = E76 + 83"` and numeric `E86=99,824.43000000001`; `E77=96,324.43` plus `E85=3,500` reconstructs `99,824.43`. xlrd exposed no formula map/cache, so E86 is treated as a stored numeric value and D86 as reference text.
- `E4-P4B-ROOT1`: parser v1 shifted `cellname()` by one row/column and allowed arbitrary amount-labeled text through `_numeric_value`, so D86 text became `7,683`. Parser v2 uses correct zero-based `cellname()` inputs and accepts only numeric/currency text, rejecting formula/reference prose.
- `E4-P4B-REPAIR1`: durable staging was repaired through audited `lineage_repair` actions. Raw workbook/staging fields remain immutable; row 86 records corrected E86 proposal lineage; legacy rows 190/197/198 are returned to `REVIEW_REQUIRED` with superseded Owner metadata preserved. Three correct late physical rows are confirmed under their historical oracle labels.
- `E4-P4-RECON1`: `C102+C109+C115+C190+C197+C198 = 416,482.2426005565 CNY` with source-table row delta sum `0.0`; received checkpoint status is `RECONCILED`. The paid group is `134,973 + 25,025 = 159,998 CNY`; old M89 is `SUPERSEDED_CHECKPOINT` and is not combined with the updated snapshot.
- `E4-P4-OPEN1`: regenerated CNY draft buckets are paid-on-behalf `159,998.0`, received-on-behalf `416,482.2426005565`, and held credit `0.0` because `24,576` is embedded in `99,824.43`. Historical formula reconstructs `161,576.5473994435 CNY`; remaining material differences are zero.
- `E4-P4-COUNT1`: durable status counts are `20 CONFIRMED`, `170 REVIEW_REQUIRED`, `60 NOT_APPLICABLE`, `39 RAW`, `0 REJECTED`; 27 audit records exist after preserving previous history and adding corrected late-row decisions plus lineage repairs.
- `E4-P4-QA1`: official QA report `reports/QA/playwright/2026-08-15-log-c06-p4-lineage-reconciliation.json` and Markdown companion record HTTP 200, zero AppTest exceptions, visible six-source reconciliation, visible `RECONCILED`, visible `416,482`, and zero canonical mutations.
- `E4-P4-DI1`: independent data-integrity sweep `python scripts/verify_log_c06_p4_lineage.py`, recorded in `reports/Data-Integrity/rp_data_260815_105200_by_gpt-5-codex_log_c06_p4_lineage.md`, passed source hash, row mapping, double-count, raw-preservation, audit-boundary, draft, and lock invariants.
- `E4-P4-REGRESSION1`: focused LOG-C06 unittest suite passed `24/24`; full unittest discovery passed `120` with `2` environment-guarded skips; `compileall` passed.
- `E4-P4-GRAPH1`: final Anvien refresh completed before change detection with `208` files scanned, `94` parsed code files, `0` parse failures, `18,737` graph nodes, and `21,512` relationships. Final detect-changes reports `30` changed files and `27` affected files; aggregate risk is `CRITICAL` because unrelated pre-existing worktree changes are included. The LOG-C06 scope remains bounded to the files listed below and the unrelated changes are not staged.

## E5 - P5 final cutover sufficiency evidence

Matching plan item(s): `P5-A`, `P5-B`, `P5-C`, `P5-D`

- `E5-P5-SCOPE1`: the source workbook remains read-only at SHA-256
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
  The analyzed source range is `Sheet2!A1:Z282`. The verified base boundary
  is represented by the latest included received-source row 200 / physical
  source date `2026-05-28`; temporal confidence is `LOW` because the
  `418,060.79 CNY` shipment-cost checkpoint has no provable source cell/date.
- `E5-P5-GRAPH1`: the deterministic supersession graph contains the
  `24,576` source credit, `99,824.43` snapshot, `134,973` component
  checkpoint, derived `159,998` paid-on-behalf group, old M89
  `170,374.18739944347` superseded checkpoint, `416,482.2426005565` received
  expectation, and current `161,576.5473994435` verified base. It reports
  `checkpoint_events_counted=0`.
- `E5-P5-CLASSIFY1`: all `289` staging items are assigned exactly one
  category. Counts: `EMBEDDED_IN_VERIFIED_BASE=19`,
  `POST_BASE_CONFIRMED=0`, `POST_BASE_REVIEW_REQUIRED=7`,
  `REFERENCE_ONLY=74`, `NOT_APPLICABLE=122`,
  `UNRESOLVED_NON_MATERIAL=60`, `UNRESOLVED_MATERIAL=7`.
  `UNRESOLVED_MATERIAL_COUNT=7`; opening-material blocker count is `14`.
- `E5-P5-REDUCE1`: the stored `REVIEW_REQUIRED=170` rows reduce to `62
  NOT_APPLICABLE`, `57 REFERENCE_ONLY`, `46 UNRESOLVED_NON_MATERIAL`, and
  `5 POST_BASE_REVIEW_REQUIRED`; no manual review of all 170 rows is required
  to identify opening blockers. Finance-relevant known-CNY post-base review
  amounts are rows 201–205 totaling `392,796.30579784507 CNY`.
- `E5-P5-1572`: the `1,572 CNY` row is source row 96, dated `2026-01-22`,
  before the verified snapshot/base scope. Its evidence is not explicit SALE
  Thành ownership; it remains `NOT_APPLICABLE`/excluded and cannot change the
  candidate opening under the preserved treatment.
- `E5-P5-SHIPMENT1`: confirmed `62,464 CNY` and `1,687 CNY` receipt events
  retain unresolved shipment linkage without becoming opening blockers because
  amount, currency, SALE owner, A Bò relationship, and direction are confirmed.
- `E5-P5-POST1`: exact post-base review list is rows `201`, `202`, `203`,
  `204`, `205`, `229`, and `230`. Rows 201–205 are CNY review rows dated
  `2026-05-29`/`2026-05-30` with no explicit SALE/owner. Rows 229/230 are
  structured SALE Thành freight rows dated `2026-06-10`/`2026-06-22`, with
  totals `5,610` and `1,450` but unknown currency/ownership in staging.
- `E5-P5-MATERIAL1`: exact `UNRESOLVED_MATERIAL` rows are `213`–`219`,
  dated `2026-06-04` or `2026-06-18`, with explicit SALE Thành but no
  structured freight-total cell. Goods/weight fields are not treated as A Bò
  amounts; their amount basis is `no_reliable_freight_total`.
- `E5-P5-CANDIDATE1`: candidate opening is
  `161,576.5473994435 CNY + 0 confirmed increases - 0 confirmed reductions`.
  Review rows are excluded and historical components remain provenance behind
  the verified base.
- `E5-P5-READINESS1`: readiness is `NOT_READY` for
  `TEMPORAL_SCOPE_UNCERTAIN`, `POST_BASE_REVIEW_REQUIRED`,
  `UNRESOLVED_MATERIAL_ITEMS`, and `OPENING_CURRENCY_UNKNOWN`. Draft state is
  `DRAFT / NOT_APPROVED / NOT_LIVE`.
- `E5-P5-ORACLE1`: canonical mutation oracle is zero; canonical collections
  touched are empty; opening publication is false; audit records remain 27.
- `E5-P5-TEST1`: focused sufficiency/opening tests passed `16/16`; full
  unittest discovery passed `130` with `2` existing guarded skips; compileall
  passed; independent verifier passed all assertions.
- `E5-P5-QA1`: Historical Review smoke QA passed with zero exceptions,
  reconciliation/checkpoint labels present, and nine rendered dataframes.
- `E5-P5-GRAPH2`: fresh Anvien refresh before change detection reported `215`
  scanned files, `99` parsed code files, `0` parse failures, `19,211` graph
  nodes, and `22,150` relationships. Change detection reported `19` changed
  files and `16` affected files at critical aggregate risk because unrelated
  dirty worktree changes are preserved and not staged.
- `E5-P5-DI1`: fresh Data-Integrity report
  `reports/Data-Integrity/rp_data_260815_140900_by_gpt-5-codex_log_c06_p5_cutover_sufficiency.md`
  gives PASS for the staging-only integrity contract.
- `E5-P5-SUPERVISOR1`: fresh Supervisor report
  `reports/supervisor/rp_supervisor_260815_140930_by_gpt-5-codex_log_c06_p5_cutover_sufficiency.md`
  gives one bounded PASS verdict; it does not approve live publication or
  canonical mutation.

## E6 - P6 blocker reconstruction and minimal Owner pack evidence

Matching plan item(s): `P6-A`, `P6-B`, `P6-C`, `P6-D`

- `E6-P6-SCOPE1`: the read-only source workbook remains SHA-256
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`, with
  source range `Sheet2!A1:Z282`; the staging input remains 289 items.
- `E6-P6-2012051`: physical source reconstruction preserves rows 201–205 as
  the `NHAN CHUYEN TIEN USD (2026-T4+5)` conversion/transfer table. C totals
  `392,796.30579784507 CNY`, D/chuyen-ho totals `392,790 CNY`, and VND input
  totals `1,531,120,000 VND`; the `6.30579784507 CNY` column difference is
  not an opening adjustment. Three source groups are retained (201,
  202–203, 204–205) and one Owner question is generated.
- `E6-P6-2132191`: physical H213:H219 goods values sum to `16,929.56` and
  match H224 within source-display precision. No row-level freight-total
  cell exists; the seven rows are now `REFERENCE_ONLY`, not
  `UNRESOLVED_MATERIAL`, and their operational goods values are excluded from
  opening amount aggregation.
- `E6-P6-2292301`: M229=`5,610` and M230=`1,450` are row-level freight
  totals; M235=`7,060` is the exact subtotal and M236 is cumulative summary
  evidence. N229/N230 explicitly identify SALE Thanh. Currency and A Bo
  payment direction are not stated by the source, so the two rows remain one
  grouped Owner question.
- `E6-P6-4181`: an exhaustive bounded numeric scan found no exact
  `418,060.79` source cell and no unique source-component provenance; nearby
  summary values are preserved as non-matching evidence. The amount remains a
  reconciliation checkpoint only.
- `E6-P6-1572`: physical row 97 has source amount E97=`1,572` and adjacent
  conversion D97=`1,572.5800933125972`; exact `1,578.5474` is absent from the
  workbook and has no deterministic formula link. Row 96 remains
  `REVIEW_REQUIRED` and opening effect zero.
- `E6-P6-TIME1`: the last embedded source event is `2026-05-28` (C198 /
  Sheet2!C200); the first source-dated non-embedded group is `2026-05-29`
  (rows 201–205). Proposed opening as-of date is `2026-05-28`, LOW overall
  confidence because the 418,060.79 shipment-cost date remains unproven.
- `E6-P6-CLASSIFY1`: current category counts are `19 EMBEDDED`, `0
  POST_BASE_CONFIRMED`, `7 POST_BASE_REVIEW_REQUIRED`, `81 REFERENCE_ONLY`,
  `122 NOT_APPLICABLE`, `60 UNRESOLVED_NON_MATERIAL`, and `0
  UNRESOLVED_MATERIAL`; all 289 rows classify exactly once. Opening-material
  blocker count is 7 and the beginner Owner pack contains 2 grouped
  decisions.
- `E6-P6-COUNT1`: durable staging statuses remain `20 CONFIRMED`, `170
  REVIEW_REQUIRED`, `60 NOT_APPLICABLE`, `39 RAW`, `0 REJECTED`; derived
  classification count is `UNKNOWN=231`. No status mutation was performed.
- `E6-P6-SCENARIO1`: current candidate remains
  `161,576.5473994435 CNY`. Scenarios for the 7,060 freight group and for
  selecting C versus D in rows 201–205 are illustrative only, CNY-separated,
  and do not convert VND/USD or add checkpoints.
- `E6-P6-TEST1`: focused P6 tests passed `14/14`; the independent P6 verifier
  passed source hash, physical-row reconstruction, exact subtotals, source
  absence checks, temporal boundary, scenario guards, draft locks, and
  canonical-zero assertions. The compatibility sufficiency verifier also
  passed.
- `E6-P6-ORACLE1`: canonical writes remain `0`, canonical collections remain
  untouched, opening publication is false, and status remains
  `DRAFT / NOT_APPROVED / NOT_LIVE`.
- `E6-P6-DI1`: fresh Data-Integrity report
  `reports/Data-Integrity/rp_data_260815_221551_by_gpt-5-codex_log_c06_p6_blocker_reconstruction.md`
  passes the P6 staging-only integrity contract and records one separate
  MEDIUM concurrency advisory in the pre-existing review-action store.
- `E6-P6-SUPERVISOR1`: fresh Supervisor report
  `reports/supervisor/rp_supervisor_260815_222358_by_gpt-5-codex_log_c06_p6_owner_pack.md`

## E7 - LOG-C06 terminal product closure

- `E7-CLOSE-OWNER1`: Owner roadmap decision closes LOG-C06 as `PRODUCT_PASS`.
  Historical staging, historical provenance mechanism, Owner review,
  checkpoint reconstruction, double-count protection, and cutover sufficiency
  are recorded as `PASS`. This is a terminal product-state decision, not an
  instruction to continue historical investigation.
- `E7-CLOSE-STATE1`: terminal state is persisted in
  `.p2p/state/project-status.json` and
  `.p2p/state/reports/run-20260815-234441-log-c06-terminal-closure.json`.
- `E7-CLOSE-BACKLOG1`: remaining ambiguity is preserved in
  `.p2p/state/deferred-historical-reconciliation.json` under
  `DEFERRED_HISTORICAL_RECONCILIATION`, with source hash and physical-cell
  pointers for the May 29–30 conversion group, 7,060 freight group,
  418,060.79 provenance gap, and other historical unknowns.
- `E7-CLOSE-ORACLE1`: canonical financial mutation remains `0`; historical
  candidate `161,576.5473994435 CNY` remains `NOT_PUBLISHED`; no migration,
  payment, Quick Entry, AI, deployment, or Owner inference occurred.
- `E7-CLOSE-GENERIC1`: the proven capabilities are recorded as
  partner-generic. A Bò remains one partner instance and is not an architectural
  center of Logistics.
- `E7-CLOSE-NEXT1`: LOG-C07 is permitted only as a new chat with whole-Logistics
  product scope and official P2P .19 as the field test. No LOG-C07 work was
  started in this closure.
  gives a bounded PASS for the P6 implementation; it does not approve
  publication, canonical mutation, payment, Quick Entry, AI, or LOG-C07.
