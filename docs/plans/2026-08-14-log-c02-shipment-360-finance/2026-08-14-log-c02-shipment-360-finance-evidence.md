# LOG-C02 Shipment 360 — Evidence

## Metadata

- Date: `2026-08-14`
- Status: `bounded PASS` locally; overall `BLOCKED` after supervisor review
- Plan: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-plan.md`

## Evidence rules

- Evidence is tied to the current `D:\Logistics_App_Copy` worktree and the
  current implementation, not to the P2P checkout.
- Read-only inspection may use current data sources; implementation and
  verification must not write real business data.
- A source-level presence of a write mechanism is not durable persistence
  proof. Runtime claims require runtime evidence.
- Unknown means the current code does not provide a trustworthy source in this
  slice; it is not a guessed zero.

## P0 actual-status evidence

| ID | Evidence | What it proves | Result |
|---|---|---|---|
| `E0-P0A-ANV1` | `anvien analyze --force`; current graph: 87 scanned files, 53 parsed code files, 0 parse failures, 6,531 nodes, 7,246 relationships | Graph was refreshed before graph queries | PASS; high-risk hotspots include shipment/database/dashboard |
| `E0-P0A-ANV2` | Anvien file-detail and impact for `views/shipment.py`, `core/logic.py`, `core/payment_logic.py`, and exact `ui_shipment_detail_tabs` / `calculate_from_shipment` symbols | Target and source blast-radius evidence exists before edit | PASS with high-risk/unresolved-reference warnings |
| `E0-P0A-WORKTREE` | `git status --short` and diff stat | Existing user changes are broad and must be preserved | PASS; no reset/checkout/cleanup performed |
| `E0-P0A-LOGIC` | `core/logic.py` source inspection | Current receivable/paid/debt calculation and legacy snapshot fields | PASS; reusable for read-only projection |
| `E0-P0A-PAYMENT` | `core/payment_logic.py` and `core/database.py` source inspection | Customer overview/FIFO/idempotency paths exist but are not a unified ledger | PARTIAL; runtime durability remains unproven |
| `E0-P0A-SHIPMENT` | `views/shipment.py` source inspection | Shipment detail, current finance tab, GNT fields, payments, contract link, and operational status exist | PARTIAL; first-view Shipment 360 is missing |
| `E0-P0A-REPORTS` | `views/reports.py` source inspection | Existing agency fee/collected/paid payable rule | PARTIAL; only agency-specific and not a global payable model |
| `E0-P0A-CONTRACT` | `views/contracts.py` source inspection | Contract links and contract transaction/proxy relation reads exist | PARTIAL; proxy pair has two independent saves |
| `E0-P0A-PROXY` | `views/proxy_payment.py` source inspection | Proxy payment store and stored FX/beneficiary/link fields exist | PARTIAL; distinct store, no allocation ledger |
| `E0-P0A-ENTRUST` | `views/entrustment.py` source inspection | Entrustment wallet links, deposits, payment legs, and stored rates exist | PARTIAL; no unified obligation/settlement source |
| `E0-P0A-TAX` | `views/shipment.py` and `views/tariff.py` source inspection | GNT/tax rows and tariff checks exist | PARTIAL; tax obligation/evidence ledger is missing |
| `E0-P0A-GETFLY` | `core/getfly_reader.py` source inspection | GetFly import/export/cross-check is reusable context | PASS for context; not a finance ledger |
| `E0-P0A-PERSIST` | `core/database.py` and `core/payment_logic.py` source inspection plus C01 evidence | Mongo persistence and safer-looking transaction/idempotency code exist | UNKNOWN for write→reload durable proof; no real write attempted |
| `E0-P0A-P2P` | Existing LOG-C01 P2P/bootstrap/governance evidence | P2P version/scope and governance drift boundary | Preserve-only; no P2P edits |

## Capability map

| Capability | Classification | Current evidence / source | Slice A decision |
|---|---|---|---|
| Shipment identifier/detail | `EXISTS_AND_REUSABLE` | Mongo `shipments`, `load_data`, `db_shipments`, `ui_shipment_detail_tabs` | Compose read model from current shipment ID |
| Customer | `EXISTS_AND_REUSABLE` | `customers` collection, `load_customers`, shipment customer fields, payment overview | Use existing customer label/id only |
| Contract linkage | `EXISTS_NEEDS_EXTENSION` | Direct `contract_id` plus legacy entrustment contract number and contract transaction reads | Show links; do not normalize into a new ledger |
| Cost entries | `EXISTS_AND_REUSABLE` | `data.3.4.details.cost`, `calculate_shipment_financials.cost` | Show as known cost/estimate, explicitly not payable |
| Customer payment transactions | `EXISTS_NEEDS_EXTENSION` | `data.3.4.payments`, `payment_receipts`, FIFO allocator | Show existing shipment payment rows; no new allocation writes |
| Payable | `EXISTS_NEEDS_EXTENSION` | Explicit agency fields, proxy payments, contract transactions, wallet records | Show agency payable only when source fields exist; otherwise UNKNOWN |
| Receivable | `EXISTS_AND_REUSABLE` | `core.logic.calculate_from_shipment` | Reuse as the single current source for this view |
| Debit | `MISSING` / `UNKNOWN` | Debit export helper exists, but no persisted debit collection/link was found | Do not infer or display a debit balance |
| Agent/partner master | `EXISTS_NEEDS_EXTENSION` | Agency fields and beneficiary/link values exist in multiple stores | Show related records only; no new party model |
| FX | `EXISTS_NEEDS_EXTENSION` | Proxy, contract, and entrustment records preserve different rate fields | Preserve raw amount/currency/rate/date-like fields; no recalc |
| Tax | `EXISTS_NEEDS_EXTENSION` | GNT `ds_thue`, tariff/CBPG checks | Show explicit tax rows only; tax payable remains UNKNOWN |
| GetFly | `EXISTS_AND_REUSABLE` | Import/export/cross-check and finance line inputs | Context only; no new source of truth |
| Balance calculation | `EXISTS_NEEDS_EXTENSION` | Customer debt, agency formula, wallet balance, proxy remaining | Mark duplicated semantics; do not merge into one balance |
| Finance summary | `EXISTS_AND_REUSABLE` | `core.logic`, `views/finance.py`, `views/reports.py` | Add a composed read-only Shipment 360 projection |
| Evidence/audit | `EXISTS_NEEDS_EXTENSION` | `audit_logs`, payment proof/note fields, scattered documents | Show source/unknown; no evidence mutation or completeness claim |
| Persistence | `UNSAFE` / `UNKNOWN` for this slice | Mongo save/idempotency code exists; proxy pair is non-atomic; durable proof absent | Inspect only; add no writes |

## Implementation evidence ledger

| ID | Planned observation | Status | Artifact |
|---|---|---|---|
| `E1-P1A-SRC` | Pure projection uses existing calculation and preserves unknowns | PASS | source + Anvien file-detail/impact |
| `E1-P1A-TEST` | Projection and existing unit tests pass | PASS | 3 focused + 27 full unittest cases |
| `E1-P1B-UI` | Real shipment detail renders read-only Shipment 360 first | PASS | `Reports/qa/playwright/2026-08-14-log-c02-shipment-360.md` |
| `E1-P1B-NOWRITE` | No new summary control or DB mutation is triggered | PASS | new read-model scan + Browser `readOnly=true` |
| `E1-P1C-BUILD` | Full available build/compile boundary passes | PASS | `compileall`, `py_compile`, local health `200/ok` |
| `E1-P1C-DETECT` | Anvien change detection is recorded before commit decision | PASS WITH DIRTY BOUNDARY | 17 pre-existing changed files; aggregate risk `critical` |
| `E2-SUPERVISOR` | Independent supervisor verdict | REJECT overall / PASS bounded slice | `reports/supervisor/rp_supervisor_260814_log_c02_shipment_360.md` |

## P1 verification detail

- `E1-P1A-SRC`: projection calls the current customer financial calculation,
  keeps agency payable scoped, and contains no persistence call.
- `E1-P1A-TEST`: focused 3/3 and full 27/27 unittest cases pass.
- `E1-P1B-UI`: Browser observed detail open, financial-first order, total
  receivable with a value, source/UNKNOWN/money map, and close/list/filter.
- `E1-P1B-NOWRITE`: source scan found no save/delete/payment/input reference in
  the new read model; no business control was clicked.
- `E1-P1C-BUILD`: `python -m compileall -q .` and runtime health pass.
- `E1-P1C-DETECT`: Anvien saw the full pre-existing dirty worktree; no isolated
  commit was made.
- Final Anvien refresh after the last metric fix: 99 files scanned, 57 parsed,
  0 parse failures, 7,249 nodes, and 8,063 relationships; detect-changes still
  reports 17 dirty paths, 3,620 changed symbols, 74 affected nodes, and
  critical aggregate risk.
- Cleanup: Browser QA tab was finalized, port `8516` was closed, and the exact
  temporary LOG-C02 runtime logs were removed after the evidence artifacts were
  retained.

## Explicit unknowns

- A global payable obligation/allocation balance per shipment.
- A persisted debit-note source linked to the shipment.
- Unallocated payment amount from a canonical allocation store.
- Reconciliation state, dispute/variance state, and evidence completeness.
- Actual profit supported by settlement evidence rather than current estimate.
- Durable write/reload proof for any real payment boundary.

## E0 - P2-A B0 actual-status and write-map evidence

| ID | Evidence | What it proves | Result |
|---|---|---|---|
| `E0-P2A-ANV1` | Fresh `anvien analyze --force` on `D:\Logistics_App_Copy`; 99 scanned, 57 parsed, 0 failures, 7,249 nodes, 8,063 relationships | Graph was refreshed before B0 graph queries | PASS; high-risk database/payment/contract files remain |
| `E0-P2A-FD1` | `anvien file-detail core/database.py --repo Logistics-Pro-AI --json` | Repository has 93 symbols, 56 linked flows, 439 unresolved references, and high risk | PASS WITH GRAPH-GAP WARNING |
| `E0-P2A-FD2` | `anvien file-detail core/payment_logic.py --repo Logistics-Pro-AI --json` | Lump-sum payment path has 29 symbols, one linked flow, 134 unresolved references, and high risk | PASS WITH GRAPH-GAP WARNING |
| `E0-P2A-FD3` | `anvien file-detail views/contracts.py --repo Logistics-Pro-AI --json` | Contract finance UI is a sibling caller of proxy and contract transaction persistence | PASS; dirty/high-risk boundary preserved |
| `E0-P2A-IMP1` | Exact Anvien symbol impact for `save_proxy_payment`, `save_contract_transaction`, and `apply_lump_sum_payment` using explicit UIDs | Direct impact is not resolved reliably; file-level risk and source call sites remain authoritative | UNKNOWN direct graph impact; do not interpret as zero blast radius |
| `E0-P2A-MONGO1` | Read-only topology probe: configured URI present, `logistics_db` selected, Mongo reachable, replica-set name and logical sessions present | Isolated Mongo transaction fixture is technically available without touching business collections | PASS; no business write was performed |
| `E0-P2A-SRC1` | `core/payment_logic.py:78-186` | Lump-sum customer payment uses Mongo session/transaction, idempotency key lookup, optimistic shipment version, receipt record, and audit rows | PARTIAL/SAFE INTENT; durable behavior still needs fixture proof |
| `E0-P2A-SRC2` | `core/database.py:298-364`, `views/shipment.py:489-499,553-572`, `views/dashboard.py:292-298` | Direct shipment payment/finance edits use single shipment update with optimistic version but audit/outbox are separate and no idempotency key is attached to direct payment form | PARTIAL; duplicate/retry safety not proven |
| `E0-P2A-SRC3` | `core/database.py:527-548`, `core/database.py:673-681`, `views/contracts.py:290-300` | Contract proxy payment and contract transaction are two independent save calls; each is an upsert plus separate audit | UNSAFE for pair atomicity until fixed/proven |
| `E0-P2A-SRC4` | `core/database.py:621-627`, `views/entrustment.py:179-233` | Entrustment wallet book loops multiple document saves; auto-save can partially persist a multi-document update | PARTIAL/UNSAFE for batch atomicity; no forced shipment_id |
| `E0-P2A-SRC5` | `views/reports.py:76-88`, `core/logic.py:50-112` | Customer receivable and agency formula are derived legacy balances; no formal obligation/allocation ledger exists | PARTIAL; no editable balance source should be added |
| `E0-P2A-SRC6` | `views/dashboard.py:405-490`, `core/getfly_reader.py:7-121`, `views/tariff.py:70-74,314-350` | GetFly import may create shipments and tariff workspace persists a separate workspace; neither is a financial allocation ledger | CONTEXT ONLY; inspect sibling writes, do not merge semantics |

## E0 - P2-A financial write map

| Write path | Classification | File/function | Collections/docs written | Save count | Session/transaction | Idempotency/version | Failure behavior | Balance impact |
|---|---|---|---|---:|---|---|---|---|
| Direct shipment customer payment | PARTIAL/UNSAFE | `views/shipment.py` -> `save_shipment_atomic` | `shipments`, then audit/outbox | 1 primary + separate logs | no Mongo transaction in repository function | optimistic shipment version; no payment idempotency key | primary failure returns false; later log failure can be partial | `apply_financial_snapshot` derives paid/debt from shipment payment rows |
| Lump-sum customer receipt | PARTIAL pending proof | `core/payment_logic.py:apply_lump_sum_payment` | `shipments`, `audit_logs`, `payment_receipts` | 1 per allocation + receipt + audits | Mongo session transaction | unique `payment_receipts.idempotency_key` + shipment version filter | exception aborts transaction; must prove via fixture | appends transaction rows, derives shipment legacy balance |
| Contract bank transfer | PARTIAL | `views/contracts.py` -> `save_contract_transaction` | `contract_transactions`, `audit_logs` | 1 + audit | no transaction | document id upsert; no request idempotency | false return can leave no document, audit can be separate | contract transaction only; no shipment balance source |
| Contract-linked proxy payment pair | UNSAFE | `views/contracts.py:294` -> `save_proxy_payment` then `save_contract_transaction` | `proxy_payments`, `contract_transactions`, audits | 2 independent saves + audits | no shared transaction | document id only; no request idempotency | first can succeed when second fails | proxy remaining fields and contract row can diverge |
| Standalone proxy payment | PARTIAL | `views/proxy_payment.py` -> `save_proxy_payment` | `proxy_payments`, `audit_logs` | 1 + audit | no transaction | document id upsert; no request idempotency | false return reports error; retry may overwrite/duplicate by new id | stored `amount_fc_remain`; no obligation allocation |
| Entrustment wallet/batch | UNSAFE for batch | `views/entrustment.py` -> `save_entrustment_book` | multiple `entrustments` docs, each via `_save_document` | N documents + no batch audit | no transaction | document id only | later failure leaves earlier docs persisted | wallet deposit/payment arithmetic is local projection, not canonical obligation |
| Agency payable report | SAFE as read-only calculation | `views/reports.py` | none | 0 | N/A | N/A | N/A | `fee - collected - paid`, only when explicit fields exist |
| GetFly import | PARTIAL | `views/dashboard.py` -> `save_shipment_atomic` per new order | `shipments` and separate audit/outbox | 1 per order, loop | no batch transaction | shipment id/unique index; no import idempotency token | loop can partially import orders | creates shipment revenue/cost details and derived legacy snapshot |
| Tariff/CBPG workspace | PARTIAL/context | `views/tariff.py` -> `save_cbpg_workspace` | `cbpg_workspaces` | 1 + no audit | no transaction | fixed workspace id upsert | false return; no tax obligation ledger | workspace/tax estimate only, not payable balance |

## E0 - P2-A invariant family map

- Family: financial write and derived-balance integrity.
- Authority: current LOG-C02 B0 request, current repository functions, Mongo
  schema/index setup, and existing `core.logic` calculation.
- Sibling surfaces: direct shipment payment, lump-sum payment, contract bank
  and proxy forms, standalone proxy, entrustment wallet, agency report,
  GetFly import, and tariff workspace.
- Forbidden fallback: editable stored balance, manual note pretending to be
  allocation/netting, compensating two-save sequence described as atomic, or
  a mandatory `shipment_id` on a payment that is not yet allocated.
- Verify matrix: happy path, partial payment, multi-payment, one payment to
  several obligations, adjustment/received-on-behalf, held/unallocated, later
  allocation, overpayment, unallocated remainder, duplicate/retry, second-save
  failure, correction/cancel, and fresh derived-balance read-back.

## E0 - P2-B pre-test boundary

The isolated fixture boundary is authorized for execution: a newly generated
database name outside `logistics_db` will be used, the exact name will be
checked before any write, fresh-client reads will be used for proof, and the
fixture database will be dropped only after the name is revalidated. No
business collection, migration, or application credential will be changed.

## E0 - P2-B1 pre-implementation evidence

| Evidence ID | Evidence | Result |
|---|---|---|
| `E0-P2B1-GRAPH1` | Fresh `anvien analyze --force` | PASS: 105 scanned / 58 parsed / 0 failures / 7,594 nodes / 8,466 relationships |
| `E0-P2B1-FD1` | Anvien context/file detail for `save_shipment_atomic`, `save_entrustment_book`, `calculate_shipment_financials`, `ui_shipment_detail_tabs`, `save_entrust_db`, and `ensure_indexes` | PASS WITH HIGH-RISK DIRTY-FILE WARNING |
| `E0-P2B1-IMP1` | Explicit symbol impact for the selected production functions | HIGH for `calculate_shipment_financials`; resolver-gapped/zero direct counts for database/UI symbols; never interpreted as zero blast radius |
| `E0-P2B1-SRC1` | `views/shipment.py:489-499` | CONFIRMED source of new UUID/in-memory direct payment behavior |
| `E0-P2B1-SRC2` | `core/database.py:298-364,707-713` | CONFIRMED source of version-only shipment save and sequential entrustment batch |
| `E0-P2B1-SRC3` | `core/logic.py:50-91` | CONFIRMED current balance source sums payment rows without reversal semantics |
| `E0-P2B1-OWNER1` | Owner decisions supplied in the current user attachment | PASS: stable request identity, traceable correction, all-or-nothing batch are fixed authority |
| `E0-P2B1-SPEC1` | `Docs/SPEC` and `SPEC-MAP.md` inventory | UNKNOWN/NOT PRESENT in this Logistics project; no alternate spec authority inferred |

### B1 invariant map recorded before implementation

The B1 map covers direct payment identity, shipment payment-history guards,
entrustment batch transaction/idempotency, minimum correction/reversal
linkage, derived effective history, and regression of B0 transaction paths.
It explicitly leaves shipment_id optional on the shared request registry and
does not create a held/unallocated ledger.

## R5 - B1 implementation and acceptance evidence

| Evidence ID | Evidence | What it proves | Result |
|---|---|---|---|
| `E0-P2B1-IMPL1` | `core/database.py:454-604`; `views/shipment.py` direct payment form | Stable direct request identity, transaction write, unique registry result reuse, and UI retry identity | PASS |
| `E0-P2B1-IMPL2` | `core/database.py:608-732`; `core/logic.py` effective payment filter | Traceable reversal/correction preserves original history and excludes inactive payment from derived paid/debt | PASS |
| `E0-P2B1-IMPL3` | `core/database.py:1076-1152`; `views/entrustment.py:18-43` | Entrustment batch transaction, stable request identity, fail-closed capability, and failed-state reload | PASS |
| `E0-P2B1-TEST1` | Direct fixture matrix: normal, same-request retry, payload mismatch, equal legitimate payment, failure/retry, correction, no-transaction | No duplicate; legitimate equal action accepted; rollback/correction/fail-closed behavior | PASS |
| `E0-P2B1-TEST2` | Entrustment fixture matrix: second failure, middle failure, retry, duplicate success, no-transaction | All-or-nothing batch with zero partial state and safe retry | PASS |
| `E0-P2B1-TEST3` | `python -m unittest discover -s tests -p 'test_*.py' -v` | Full available repository regression | PASS: 37 tests; 1 opt-in class skipped without flag |
| `E0-P2B1-TEST4` | `LOG_C02_RUN_MONGO_FIXTURES=1 python -m unittest tests.test_financial_write_safety.MongoPersistenceFixtureTests -v` | Disposable Mongo transaction, durable persistence, fresh-client read-back, same-identity concurrency, and B0 regression | PASS: 6/6 |
| `E0-P2B1-TEST5` | `python -m compileall -q core views tests scripts app.py web_app.py` | Python source compiles after B1 changes | PASS |
| `E0-P2B1-TEST6` | Streamlit on `127.0.0.1:8509`, `/_stcore/health` | Current app runtime starts and is healthy; process stopped after check | PASS: `200 ok` |
| `E0-P2B1-CLEAN` | Post-fixture Mongo database inventory | No generated fixture database remains; business database was not target | PASS |
| `E0-P2B1-GRAPH2` | Final `anvien analyze --force` and `detect-changes --scope all` | Current graph is fresh and dirty/high-risk scope is explicitly recorded | PASS WITH HIGH-RISK DIRTY BOUNDARY |
| `E0-P2B1-REVIEW1` | New Data-Integrity, Edge-Case, Coder, and Supervisor reports | Independent safety and acceptance review | PASS; Supervisor verdict PASS |

### B1 acceptance interpretation

All ten Owner acceptance points are evidenced within the assigned boundary.
The B1 result does not certify standalone legacy writers, broad ledger
semantics, or visible-browser interaction. The latter could not be driven in
this session because no browser-control capability was available; source
compile and Streamlit health were still checked.

## R3 - Slice B0 fixture and bounded-fix evidence

| Evidence ID | Evidence | Result |
|---|---|---|
| `E0-P2B-TEST1` | Contract proxy second-write failure injection | PASS: transaction fixture removed proxy, transaction, and audits |
| `E0-P2B-TEST2` | Unsupported transaction topology | PASS: failed closed before writes |
| `E0-P2B-TEST3` | Contract proxy success fixture | PASS: pair plus two audit rows |
| `E0-P2B-TEST4` | Isolated Mongo fresh-client contract proxy read-back | PASS |
| `E0-P2B-TEST5` | Isolated Mongo lump-sum write/read-back | PASS: derived paid 40,000; debt 60,000 |
| `E0-P2B-TEST6` | Same lump-sum idempotency key retry | PASS: one receipt/payment |
| `E0-P2B-TEST7` | Isolated Mongo direct shipment save/read-back | PASS: derived paid/debt consistent |
| `E0-P2B-TEST8` | Stale version fixture | PASS: stale save rejected |
| `E0-P2B-TEST9` | Direct payment retry with new payment identity | CONFIRMED GAP: two rows accepted; derived paid 80,000 |
| `E0-P2B-TEST10` | Entrustment second-write failure injection | CONFIRMED GAP: first document remained; exception escaped |
| `E0-P2B-TEST11` | Exact fixture database teardown/recheck | PASS: no leftover generated database |
| `E0-P2B-TEST12` | Full regression suite | PASS: 30 tests; 1 opt-in Mongo class skipped without flag |
| `E0-P2B-TEST13` | Python compileall | PASS |
| `E0-P2B-TEST14` | No real business mutation | PASS: only synthetic/in-memory and isolated fixture boundary |

### B0 implementation evidence

- `core/database.py` now exposes `save_contract_proxy_payment_atomic` and
  `_save_document(..., db=..., session=...)`; both writes and audit rows use
  the same session. `views/contracts.py` calls the helper for the proxy pair.
- The actual Mongo fixture used a newly generated `l02b0_*` database and a
  fresh independent client for read-back. The configured business database
  name was not a target and the fixture name was absent after cleanup.
- Fresh Anvien post-edit result: 101 scanned / 58 parsed / 0 failures / 7,553
  nodes / 8,425 relationships. `anvien detect-changes` still reports a
  critical aggregate because the repository contains broad pre-existing
  changes; this is a scope warning, not evidence of isolated impact.
- No `Docs/SPEC` or `SPEC-MAP.md` exists in the project; the review used the
  user B0 contract, AGENTS rules, source, and executable fixture evidence.

### B0 gate result

Bounded Contract proxy atomicity: **PASS**. Overall write-safety gate:
**PARTIAL**. Direct payment identity and entrustment batch semantics remain
unsafe/unfinished. Minimum ledger and Quick Entry remain blocked.
