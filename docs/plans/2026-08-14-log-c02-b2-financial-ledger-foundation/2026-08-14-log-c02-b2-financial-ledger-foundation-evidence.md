# LOG-C02 B2 Financial Ledger Foundation + A Bò Golden Financial Case Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-actual-status.md`

## Evidence Rules

Evidence is phase-scoped and uses exact IDs. B2 evidence must distinguish
source inspection, in-memory behavior, isolated Mongo persistence, runtime/UI
observation, and independent review. Fixture PASS is not evidence that real
business data was migrated or that legacy financial sources are reconciled.
No old Data-Integrity or Edge-Case report is used as a review source; each
specialist lane creates a fresh report for this B2 head.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: B2 request attachment confirms optional shipment linkage,
  one canonical ledger, five concepts, ownership/restriction separation,
  derived balances, golden fixtures, and no Quick Entry/AI/migration.
- `E0-P0A-SRC2`: `core/database.py` source inspection confirms B1
  `_transaction_client`, request registry, correction collection, audit/outbox
  helpers, and current `ensure_indexes` extension point.
- `E0-P0A-SRC3`: `core/logic.py`, `core/payment_logic.py`, `views/finance.py`,
  `views/entrustment.py`, `views/proxy_payment.py`, and
  `core/shipment_360.py` show existing legacy calculations/stores but no
  canonical obligation/allocation/held projection.
- `E0-P0A-SRC4`: current tests include B1 direct-payment, entrustment,
  contract-proxy, lump-sum, and shipment-360 fixtures; no B2 canonical ledger
  test module exists at baseline.
- `E0-P0A-WT1`: `git status --short` shows broad pre-existing dirty changes;
  B2 must preserve unrelated files and avoid broad staging.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed for repo
  `Logistics-Pro-AI`: 109 scanned, 58 parsed, 0 parse failures, 8,419 graph
  nodes, 9,436 relationships, 55 unresolved file-projection gaps.
- `E0-P0A-IMP1`: Anvien `file-detail` reports `core/database.py` 137 symbols,
  64 linked flows, 701 unresolved references, risk `high`; file impact is
  `MEDIUM`, 9 direct symbols, 1 affected file, and 64 linked flows.
- `E0-P0A-IMP2`: Anvien `file-detail` reports `views/finance.py` 14 symbols,
  78 unresolved references, risk `high`; file impact is `LOW` with no linked
  downstream files in the graph projection.
- `E0-P0A-IMP3`: Anvien `file-detail` reports `core/shipment_360.py` 71
  symbols, 7 linked flows, 268 unresolved references, risk `high`; file impact
  is `MEDIUM`, 12 direct symbols, 1 affected file, and 7 linked flows.
- `E0-P0A-IMP4`: Anvien `file-detail` reports `core/state.py` 3 symbols and
  38 unresolved references; no state edit is required for B2.
- `E0-P0A-CAP1`: Baseline capability map: existing B1 persistence primitives
  are `EXISTS_AND_REUSABLE`; legacy shipment/customer payment is
  `EXISTS_NEEDS_EXTENSION` for canonical mapping; obligation, allocation,
  held/unallocated, ownership buckets, and received-on-behalf projection are
  `MISSING`; legacy stores are `DUPLICATED`; real-data durability outside B1
  is `UNKNOWN` until B2 fixtures.
- `E0-P0A-DEC1`: P0 decision is complete for a bounded B2 implementation:
  new ledger module plus minimal index bootstrap is editable; legacy finance,
  shipment 360 source, and all broad UI/data paths are preserve/inspect-only.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

### P1-A canonical ledger service

- `E1-P1A-SVC1`: canonical collection/payload inspection and tests prove
  obligation creation accepts `shipment_ids=[]` and preserves parties,
  amount/currency, purpose, due date, owner, evidence, and provenance.
- `E1-P1A-SVC2`: transaction creation accepts no shipment and preserves
  source/payer, holder, beneficial owner, original money fields, occurred time,
  request identity, restrictions, and internal sale owner.
- `E1-P1A-SVC3`: allocation tests prove partial allocation, one transaction to
  many obligations, and many transactions to one obligation.
- `E1-P1A-SVC4`: allocation projection derives outstanding and unallocated
  values from effective history; no editable balance field is persisted.
- `E1-P1A-SVC5`: A Bò 30M held-money fixture exists without shipment, later
  allocates to L-001 80M, and derives held 0 / payable outstanding 50M.
- `E1-P1A-SVC6`: received-on-behalf and payment-only fixtures preserve holder,
  beneficial owner, source, currency, and optional later shipment link without
  duplicating the original transaction.
- `E1-P1A-SVC7`: ownership/restriction/UNKNOWN/currency guard tests block
  unsafe allocation and leave rows visible outside confirmed position.
- `E1-P1A-SVC8`: allocation reversal preserves original allocation and
  restores transaction available amount and obligation outstanding.
- `E1-P1A-SVC9`: stable request retry and injected failure/no-session tests
  prove one effect, rollback, and fail-closed behavior.

P1-A execution evidence:

- `E1-P1A-RUN1`: `python -m unittest tests.test_financial_ledger.FinancialLedgerMemoryFixtureTests -v` passed 10/10.
- `E1-P1A-RUN2`: opt-in `LOG_C02_RUN_MONGO_FIXTURES=1` ran the generated
  `l02b2_*` database and passed the fresh-client A Bò golden persistence test
  1/1.
- `E1-P1A-RUN3`: post-run database inventory reported
  `REMAINING_L02B2=[]`; no fixture database remained.
- `E1-P1A-RUN4`: `python -m py_compile` passed for the new ledger module,
  index bootstrap, focused test, and current Finance view before P1-B UI
  completion.

### P1-B read-only projection

- `E1-P1B-UI1`: projection output has explicit payable, held/credit,
  received-on-behalf, unallocated, restricted, unknown, and currency buckets.
- `E1-P1B-UI2`: deterministic why-number rows identify formula/source record
  and exclude UNKNOWN from confirmed totals.
- `E1-P1B-UI3`: renderer source scan proves no ledger mutation helper or write
  control is imported/called.
- `E1-P1B-UI4`: Sale Thành filter matches only `internal_sale_owner` and does
  not rewrite any party/fund-owner field.
- `E1-P1B-UI5`: Finance route health/render check is recorded; any missing
  Docker/browser vehicle remains explicit rather than replaced by a mock.
- `E1-P1B-UI6`: empty, mixed-currency, restricted, and unknown projections
  render without summing unlike currencies.

## E2 - P2 Evidence

Matching plan item(s): `P1-C`, `Pn-A`, `Pn-B`, `Pn-C`

- `E2-P1C-TEST1`: focused B2 unit/fixture test command and result.
- `E2-P1C-TEST2`: opt-in disposable Mongo command, generated database name,
  fresh-client read-back, and exact cleanup inventory.
- `E2-P1C-TEST3`: B1 direct-payment, entrustment, contract-proxy, and lump-sum
  regression result.
- `E2-P1C-TEST4`: compileall result for `core`, `views`, `tests`, `scripts`,
  `app.py`, and `web_app.py`.
- `E2-P1C-TEST5`: full affected unittest result with pass/skip/fail counts.
- `E2-P1C-TEST6`: no-real-data/no-migration/no-P2P/no-credential mutation
  verification.
- `E2-P1C-TEST7`: local runtime health and read-only Finance evidence, if
  available; Docker/browser limitation recorded if unavailable.
- `E2-P1C-TEST8`: exact generated fixture database cleanup verification.
- `E2-P1C-REVIEW1`: fresh Data-Integrity report path, findings, and required
  lane-owned commit.
- `E2-P1C-REVIEW2`: fresh Edge-Case report path, perturbations, findings, and
  required lane-owned commit.
- `E2-P1C-REVIEW3`: coder implementation review report path and result.
- `E2-P1C-REVIEW4`: supervisor acceptance report path and result.
- `E2-P1C-REVIEW5`: Anvien `detect-changes --repo Logistics-Pro-AI --scope all`
  output, changed-symbol/file scope, and risk interpretation.
- `E2-P1C-REVIEW6`: final plan/status/decision-log/worktree/commit evidence.

## Closure Evidence

To be filled as B2 closes:

- final B2 result: `PASS` / `PARTIAL` / `BLOCKED`;
- implementation files and line links;
- focused/full tests, compile, fixture cleanup, and runtime evidence;
- fresh specialist reports and supervisor verdict;
- detect-changes output and isolated commit hash if available;
- explicit remaining risks and B3 recommendation; no automatic B3 build.

## R2 Current Evidence Override — 2026-08-14

The entries below are the authoritative current evidence for the post-hardening
implementation state; earlier pending placeholders remain as schema targets.

- `E2-P1C-TEST1-R2`: `python -m unittest tests.test_financial_ledger.FinancialLedgerMemoryFixtureTests -v` passed `11/11`, including the over-allocation review fixture.
- `E2-P1C-TEST2-R2`: `LOG_C02_RUN_MONGO_FIXTURES=1 python -m unittest tests.test_financial_ledger.MongoFinancialLedgerFixtureTests -v` passed `1/1` with an isolated `l02b2_*` database and fresh-client read-back.
- `E2-P1C-TEST3-R2`: B1 Mongo regression was attempted with the opt-in fixture; 5/6 cases completed successfully and one case plus cleanup hit an Atlas `NetworkTimeout`. The local full suite remains green and no fixture namespace remained afterward.
- `E2-P1C-TEST4-R2`: `python -m compileall -q core views tests scripts app.py web_app.py` exited 0; changed ledger/test files also passed `py_compile`.
- `E2-P1C-TEST5-R2`: `python -m unittest discover -s tests -p 'test_*.py' -q` passed `48` tests with `2` expected opt-in Mongo skips and `0` failures.
- `E2-P1C-TEST6-R2`: no migration, real-business write, deployment, credential/permission change, P2P edit, or production database mutation was performed; exact fixture cleanup probes returned empty `l02b*` inventories.
- `E2-P1C-TEST7-R2`: local headless Streamlit health probe returned HTTP `200` / body `ok`; no Dockerfile/compose or real browser harness was available, so Docker/browser proof is explicitly unavailable.
- `E2-P1C-TEST8-R2`: post-B2 Mongo cleanup returned `REMAINING_L02B2=[]`.
- `E2-P1C-REVIEW1-R2`: fresh Data-Integrity report committed as `4f77b8c`, `reports/Data-Integrity/rp_data_260814_164238_by_gpt-5-codex_log_c02_b2_ledger.md`; bounded PASS with tenant/migration/general-adjustment risks explicit.
- `E2-P1C-REVIEW2-R2`: fresh Edge-Case report committed as `9695244`, `reports/Edge-Case/rp_edge_260814_164743_by_gpt-5-codex_log_c02_b2_ledger.md`; bounded PASS and over-allocation hardening recorded.
- `E2-P1C-REVIEW5-R2`: post-change Anvien refresh: 116 files scanned, 61 parsed, 0 failures, 9,930 graph nodes, 11,246 relationships; ledger file detail 132 symbols/16 flows/high hotspot; file impact 14 direct/24 impacted nodes. `detect-changes --scope all` reports 14 tracked affected files and 93 affected processes because the worktree contains broad pre-existing changes; B2 untracked files are separately recorded and not broadly staged.
- `E2-P1C-REVIEW6-R2`: scoped `git diff --check` passed; only specialist reports were isolated-committed. Production B2 files remain in the pre-existing dirty worktree and were not broadly staged.

## R3 Supervisor Closure Evidence — 2026-08-14

- `E2-P1C-REVIEW4-R3`: fresh Supervisor report
  `reports/supervisor/rp_supervisor_260814_165706_by_gpt-5-codex_log_c02_b2_ledger.md`
  verdict `REJECT` for P1-C closure. The report independently inspected
  source, current diff, current Anvien graph, tests, runtime evidence, and
  prior same-scope blockers.
- `E2-P1C-BLOCKER-R3`: closure blockers are concrete: missing Docker/browser
  vehicle for the changed Finance route; one B1 Mongo case and cleanup hit
  Atlas `NetworkTimeout`; shared `core/database.py` and `views/finance.py`
  cannot currently be committed as isolated B2 hunks without risking
  unrelated user changes.
- `E2-P1C-DECISION-R3`: overall B2 status is `PARTIAL`; do not enable real
  financial writes, migration, deployment, Quick Entry, or financial closure.
