# LOG-C02 Shipment 360 — Actual Status

Title: LOG-C02 Shipment 360 — Công nợ & đối soát lô hàng  
Date: 2026-08-14  
Status: BLOCKED overall; P0 complete; bounded P1 locally PASS  
Companion plan: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-plan.md`  
Companion evidence: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-evidence.md`  
Companion benchmark: `docs/plans/2026-08-14-log-c02-shipment-360-finance/2026-08-14-log-c02-shipment-360-finance-benchmark.md`

## Purpose

This is the current-source map for the first LOG-C02 vertical slice. It
separates what the project already knows from what it cannot yet prove. It is
not a claim that the application has a complete financial ledger.

## Worktree and safety boundary

- Root: `D:\Logistics_App_Copy`.
- P2P version observed from the existing project state: `8.4.7-C-codex.15`.
- P2P development checkout and its source were not opened for editing.
- The worktree contains broad pre-existing modifications and untracked files,
  including the main finance/database/detail files. No reset, checkout, or
  destructive cleanup is allowed.
- No real business-data write, migration, deploy, credential change, or
  persistence experiment was performed for P0.

## Fresh graph / impact evidence

`E0-P0A-ANV1`: `anvien analyze --force` completed against the project. It
reported 87 scanned files, 53 parsed code files, 0 parse failures, 6,531
nodes, 7,246 relationships, and a high-risk file projection for
`views/shipment.py`, `core/database.py`, and related large views.

`E0-P0A-ANV2`: file-detail and exact-symbol impact were obtained for the
current source/calculation/detail boundaries before editing. The projection
has many unresolved references, so the high-risk classification is a scope
warning: keep the patch additive and surgical.

`E0-P0A-WORKTREE`: the target detail file and finance/database files are
already dirty. Any eventual commit must be isolated or omitted; pre-existing
changes must not be bundled accidentally.

## Current status matrix

| Unit | Current state | Required state for this slice | Status | Evidence | Decision |
|---|---|---|---|---|---|
| Shipment ID/detail | Mongo `shipments`, `load_data`, `db_shipments`, existing detail renderer | One shipment is the read-model anchor | correct/reusable | `E0-P0A-SHIPMENT` | reuse |
| Shipment 360 projection | No prior unified first-view projection | Source-labelled in-memory composition | implemented/reusable for Slice A | `E1-P1A-SRC`, `E1-P1A-TEST` | preserve as read model only |
| Shipment 360 renderer/wiring | Existing detail had finance tab but no first-view summary | Summary before operational tabs, no new writes | implemented/correct for bounded scope | `E1-P1B-UI`, `E1-P1B-NOWRITE` | preserve; no write expansion |
| Customer | Customer collection/load path and shipment customer fields exist | Customer identity available from shipment | correct/reusable | `E0-P0A-SHIPMENT`, `E0-P0A-LOGIC` | reuse |
| Customer receivable | `calculate_from_shipment` derives revenue/paid/debt from detail rows/payments | Read-only source-labelled summary | correct/reusable | `E0-P0A-LOGIC` | reuse exactly |
| Customer payment transaction | Shipment payment rows plus lump-sum receipt/idempotency path exist | Keep transaction distinct from obligation/allocation | partial/needs extension | `E0-P0A-PAYMENT` | display existing rows only |
| Cost | Detail-line cost and finance summary cost exist | Show known cost, not payable | correct for estimate | `E0-P0A-LOGIC`, `E0-P0A-SHIPMENT` | label carefully |
| Agency payable | Reports calculates agency fee minus collected/paid from explicit fields | Agency-only payable summary where data exists | partial/needs extension | `E0-P0A-REPORTS` | reuse formula; otherwise UNKNOWN |
| Global payable obligation | No unified obligation source found; proxy/contract/wallet stores are separate | Complete payable map | missing | `E0-P0A-PAYMENT`, `E0-P0A-PROXY`, `E0-P0A-ENTRUST` | do not infer |
| Contract link | Direct and legacy contract identifiers exist | Show related contract IDs | partial/needs extension | `E0-P0A-CONTRACT`, `E0-P0A-SHIPMENT` | display links only |
| Proxy payment | `proxy_payments` stores amount, currency, rates, beneficiary, links | Preserve relationship and FX fields | partial/reusable relation | `E0-P0A-PROXY` | read-only relation |
| Entrustment/received-on-behalf | Wallet deposits/payment legs and link fields exist | Preserve relationship, do not fake netting | partial/needs extension | `E0-P0A-ENTRUST` | read-only relation |
| Debit | Export helper/labels exist; persisted linked debit source not found | Trace debit from shipment | missing/unknown | `E0-P0A-SHIPMENT`, `E0-P0A-GETFLY` | mark UNKNOWN |
| Tax | GNT `ds_thue` rows and tariff checks exist | Show explicit tax rows only | partial/needs extension | `E0-P0A-TAX` | no tax obligation inference |
| FX | Rates/currencies exist in different stores | Preserve original amount/currency/rate fields | partial/needs extension | `E0-P0A-PROXY`, `E0-P0A-ENTRUST`, `E0-P0A-CONTRACT` | no recalculation |
| Evidence | Audit logs and scattered proof/note fields exist | Evidence location/completeness per financial item | partial/needs extension | `E0-P0A-PERSIST`, `E0-P0A-SHIPMENT` | source/unknown only |
| Unallocated money | No canonical allocation projection found | Derived/verified unallocated balance | missing/unknown | `E0-P0A-PAYMENT` | UNKNOWN |
| Reconciliation/variance | No complete read model found | Settled/open/unreconciled per counterparty | missing/unknown | all P0 sources | UNKNOWN; never close |
| Actual profit | Current logic produces gross/provisional profit from detail lines | Evidence-supported actual margin | partial/unknown | `E0-P0A-LOGIC` | show current estimate only |
| Persistence safety | Mongo writes and idempotency code exist; proxy pair is two independent saves | Durable write/read-back proof | unsafe/unknown | `E0-P0A-PERSIST` | inspect-only |
| P2P/governance | Existing LOG-C01 evidence reports drift; P2P must remain untouched | No P2P change in this goal | preserve-only | `E0-P0A-P2P` | out of scope |

## Source-of-truth map

| Number / label | Source | Trust level for read-only view |
|---|---|---|
| Total receivable | `core.logic.calculate_from_shipment` → `revenue_net + output_vat` | verified current app calculation |
| Collected | Same calculation → sum of `data.3.4.payments` | verified current app calculation |
| Outstanding receivable | Same calculation → receivable minus paid | verified derived value; not editable |
| Agency fee/paid/collected | Existing `views.reports` rule over `data.3.4.agency` | verified only when explicit agency fields exist |
| Known cost | Same current calculation over detail-line `cost` | verified as cost/estimate, not payable |
| Tax | Explicit `data.2.4.gnt.ds_thue[*].tien` | verified row total only; obligation unknown |
| Proxy/entrustment/contract relations | Existing linked records and shipment identifiers | verified relationship; financial settlement meaning may be unknown |
| Unallocated/unreconciled/evidence/actual settlement | No trustworthy current canonical source | `UNKNOWN` |

## Read-model design decision

P0 evidence supports a small additive read model. It may compose existing
shipment math and related records in memory, but it must not persist a second
balance source. It must expose source labels and `UNKNOWN` states and must not
call a save, payment, contract, proxy, wallet, or snapshot-mutation function.

## Phase touch map

| File/surface | Mode | Constraint |
|---|---|---|
| `core/shipment_360.py` | add | pure projection, no persistence |
| `views/shipment_360.py` | add | read-only Streamlit renderer, no write controls |
| `views/shipment.py` | minimal edit | import/cache/read-only call only; preserve existing tabs and save path |
| `tests/test_shipment_360.py` | add | fixture-only pure tests |
| `playwright/log_c02_shipment_360_flow.mjs` | add if harness works | reusable, read-only, no dependency install |
| `core/logic.py`, `core/database.py`, `core/payment_logic.py` | inspect-only | no change to current math/persistence in Slice A |
| `views/contracts.py`, `views/proxy_payment.py`, `views/entrustment.py` | inspect-only | no atomicity/netting changes |
| `.p2p`, P2P checkout, secrets/auth/deploy files | do-not-touch | separate protected boundaries |

## R2 - Slice B0 current-state refresh

Status: **B0 in progress; Quick Entry not authorized; overall not ready**.

### B0 status matrix

| Unit / write surface | Current state | Required state | Status | Relationship / graph evidence | Next plan decision |
|---|---|---|---|---|---|
| `core/payment_logic.py:apply_lump_sum_payment` | Session transaction, unique idempotency receipt, version filter, derived snapshot exist in source | Fixture-proven durable rollback/retry/read-back | partial | `E0-P2A-FD2`, `E0-P2A-SRC1` | run P2-B before enabling any new entry |
| Direct shipment payment in `views/shipment.py` | Payment row is appended in memory and saved through shipment document; no per-payment idempotency key | Duplicate/retry-safe material event write | partial/unsafe | `E0-P2A-SRC2` | keep existing path; no Quick Entry |
| `save_shipment_atomic` | Single-document optimistic update; audit/outbox saves are separate | Durable proof and failure semantics documented | partial | `E0-P2A-FD1`, `E0-P2A-SRC2` | fixture read-back; do not broaden |
| Contract proxy pair | Proxy save and contract transaction save are independent | One transaction or explicit fail-closed boundary | unsafe | `E0-P2A-FD3`, `E0-P2A-SRC3` | P2-B reproduce, then P2-C only if bounded |
| Standalone proxy payment | One upsert plus audit; no request idempotency | Traceable retry/correction behavior | partial/unsafe | `E0-P2A-SRC3` | preserve; no new use case |
| Entrustment wallet book | Multiple sequential document saves through loop | Batch failure semantics and held/allocated traceability | unsafe for batch | `E0-P2A-SRC4` | no auto-netting; model only after gate |
| Customer receivable | Derived from detail rows minus shipment payment rows | No editable balance; fixture equation holds after reload | correct source / proof pending | `E0-P2A-SRC5` | preserve source; test derived result |
| Agency payable | Explicit fee-collected-paid formula only | No inference outside explicit agency source | correct as bounded read | `E0-P2A-SRC5` | preserve; mark unknown when missing |
| GetFly financial update | Import creates shipment details via per-order save; no batch idempotency | Context-only or explicitly safe import semantics | partial | `E0-P2A-SRC6` | inspect-only; no redesign |
| Tariff/tax workspace | Separate fixed workspace upsert and tax checks | Tax obligation/evidence not guessed | partial/context | `E0-P2A-SRC6` | preserve; no ledger claim |
| Minimum ledger foundation | No formal obligation/transaction/allocation/adjustment/evidence projection | Small reusable boundary with held/unallocated non-shipment support | missing/blocked pending gate | B0 invariant family map | P2-D only after P2-B PASS |
| Isolated Mongo fixture | Mongo reachable via replica-set topology; no write yet | Fresh write/read-back and cleanup proof | ready to test | `E0-P2A-MONGO1` | execute P2-B |

### B0 touch map

| Unit | Plan-relevant relationship | Plan item | Touch mode | Constraint |
|---|---|---|---|---|
| `core/database.py` | repository for all Mongo writes | P2-C only | inspect; edit only bounded atomic helper | no schema migration; preserve dirty rewrite |
| `core/payment_logic.py` | lump-sum payment transaction | P2-B | inspect/test | no change before failure proof |
| `views/contracts.py` | contract proxy pair caller | P2-C only | edit only if atomic helper passes fixture gate | no independent pair save after fix |
| `views/shipment.py` | direct payment and snapshot caller | P2-B | inspect/test | do not refactor broad dirty file |
| `views/finance.py` | lump-sum entrypoint | P2-B | inspect-only | Quick Entry stays closed |
| `views/entrustment.py` | wallet batch writer | P2-B/P2-D | inspect/test | no auto-netting or mandatory shipment ID |
| `views/reports.py` | agency derived formula | P2-A/P2-D | inspect-only | explicit source only |
| `views/dashboard.py`, `core/getfly_reader.py` | GetFly import/context | P2-A | inspect-only | no batch import redesign |
| `views/tariff.py` | tax workspace | P2-A | inspect-only | no tax obligation inference |
| `.p2p`, P2P checkout, secrets/auth/deploy | protected unrelated boundary | all | do-not-touch | user explicitly forbids |

### B0 decision before fixture execution

- P0/B0 source map is complete enough to execute fixture-only safety tests.
- Quick Entry is **not authorized**.
- Production business database is **not** a fixture target.
- P2-C production edit is conditional on a reproducible second-save failure
  and a supported Mongo transaction boundary.
- P2-D minimum ledger work is conditional on the write-safety gate PASS.

### Refresh log addition

| Refresh | Date | Scope | Result |
|---|---|---|---|
| R2 | 2026-08-14 | B0 write map, Anvien refresh, Mongo topology, sibling financial writes | P2-A complete; P2-B ready; Quick Entry remains closed; P2-C conditional |

## R3 - B0 checkpoint after fixture execution

Overall status: **PARTIAL**. The bounded Contract proxy fix is safe on the
tested transaction boundary; the whole financial write family is not yet
safe. Quick Entry remains **NO**.

| Unit / write surface | R3 result | Evidence | Consequence |
|---|---|---|---|
| Contract proxy pair | transaction rollback and commit proven; fresh Mongo read-back proven | `E0-P2B-TEST1..TEST4` | bounded P2-C PASS |
| Lump-sum customer payment | durable, derived balance consistent, same-key retry idempotent | `E0-P2B-TEST5..TEST6` | safe only for this existing route |
| Direct shipment payment | stale version rejected, but new payment identity on retry is accepted | `E0-P2B-TEST7..TEST9` | unsafe for opening a new entry action |
| Entrustment book | sequential loop leaves first write after injected second failure | `E0-P2B-TEST10` | unsafe for batch/held-money foundation |
| Fixture persistence/cleanup | fresh-client read-back and exact teardown passed | `E0-P2B-TEST4..TEST7`, `E0-P2B-TEST11` | bounded durability evidence only |
| Regression/compile | 30 tests pass, 1 opt-in Mongo class skipped by default; compileall passes | `E0-P2B-TEST12..TEST13` | no regression found in available suite |
| Minimum ledger | not implemented; no formal obligation/allocation/adjustment/evidence source | `E0-P2B-TEST14` and reports | P2-D blocked |

### R3 safety interpretation

The lump-sum transaction/idempotency behavior must not be generalized to
direct shipment editing, standalone proxy payment, entrustment batch writes,
GetFly import, or tariff/tax context. `save_shipment_atomic` still saves its
audit/outbox after the shipment document rather than under one transaction.
The current data model still cannot represent held/unallocated money,
received-on-behalf, later allocation, overpayment, correction, and
reconciliation as first-class derived records. These remain UNKNOWN/BLOCKED;
no manual balance field was introduced.

### R3 decision

- B0: **PARTIAL**, not PASS.
- Quick Entry: **NO**.
- Next smallest slice: close direct payment request identity and entrustment
  batch atomicity/failure semantics with fixture-only proof.
- User action now: none required for the current safe stop; an owner decision
  is needed before choosing the semantics of duplicate external payment
  identity and batch correction/rollback.

## R4 - B1 pre-implementation status refresh

Owner decisions are now explicit and active: stable request identity,
traceable correction/reversal, and all-or-nothing entrustment batch. The
following is the current status before B1 implementation.

| Surface | Current status | Fresh evidence | B1 consequence |
|---|---|---|---|
| Direct payment form | wrong/unsafe for retry | `views/shipment.py:489-499` generates a new UUID and only appends in memory | move payment write to a domain/persistence helper with stable request identity |
| `save_shipment_atomic` | partial | `core/database.py:298-364`; optimistic version exists but financial history is not guarded against silent add/delete/edit | add payment-history safety guard; preserve non-financial save behavior |
| `calculate_shipment_financials` | correct source, missing reversal semantics | `core/logic.py:50-91` sums every payment row | exclude explicitly reversed/cancelled rows while preserving originals |
| Entrustment UI wrapper | partial/unsafe | `views/entrustment.py:15-16,58,174,187,207,232,282` calls one batch wrapper repeatedly | stable UI request identity and rollback-safe reload on failure |
| `save_entrustment_book` | unsafe | `core/database.py:707-713` sequential `_save_document` loop | one session/transaction, request registry, audit rows |
| Financial action identity | missing | no current `financial_action_requests` registry/index | add minimal optional-shipment registry |
| Correction foundation | missing | no reversal/correction collection or effective-history marker | add direct-payment reversal record only; no full correction UI |
| B0 Contract proxy | bounded-correct | B0 helper and fixture proof | regression only; no broad refactor |
| B0 lump-sum payment | bounded-correct | transaction/idempotency proof | regression only; do not generalize implicitly |
| Ledger/Quick Entry | blocked | no obligation/allocation/held model | remain out of scope until B1 PASS |

### R4 Anvien boundary

Fresh graph: 105 scanned / 58 parsed / 0 failures / 7,594 nodes / 8,466
relationships. `core/database.py` and `views/shipment.py` each remain high
risk with 476 unresolved references; `views/entrustment.py` has 178. Explicit
impact for `calculate_shipment_financials` was HIGH with two direct affected
nodes and three processes; other targets were resolver-gapped, so file-level
risk remains authoritative and is not interpreted as zero blast radius.

### R4 decision

B1 may edit only the direct payment, entrustment batch, correction foundation,
and their focused tests. No real business database is a fixture target.

## P0 decision

- [x] Actual implementation map is complete enough to begin a bounded
  read-only projection.
- [x] Existing customer receivable calculation is reusable and identified.
- [x] Missing/unsafe concepts are explicitly marked and will remain UNKNOWN.
- [x] No write path, migration, deployment, or P2P change is authorized by
  this slice.
- [x] P1 implementation and runtime evidence complete for bounded read-only Slice A.

Decision: **P0 PASS for bounded Slice A; P1 locally PASS; overall BLOCKED after
supervisor review.** This is not a claim that the application is financially
reconciled or persistence-safe.

## R5 - B1 post-implementation status

Overall B1 status: **PASS for the assigned direct-payment, correction, and
entrustment-batch boundary**. The Supervisor report independently accepted
the boundary. This does not promote the broader application to financially
closed and does not authorize Quick Entry.

| Surface | B1 result | Current evidence | Consequence |
|---|---|---|---|
| Direct payment request identity | PASS | stable `request_id`, unique action registry, same-request retry and mismatch rejection | no direct duplicate in the new path |
| Legitimate equal payment | PASS | distinct request identities with equal amount/date/customer context are both accepted | amount/date/customer is not used as canonical dedupe |
| Direct failure/retry/concurrency | PASS | transaction rollback fixture; disposable Mongo same-identity concurrency read-back has one effect | a transient contention failure remains safely retryable |
| Correction/reversal | PASS | original payment retained; linked correction/audit/evidence/reason/actor/time; effective balance recomputed | no silent material delete/overwrite in the B1 path |
| Entrustment batch | PASS | second/middle failure rollback, retry, duplicate retry, no-transaction fail-closed | all-or-nothing batch boundary is proven |
| Fresh persistence | PASS | fresh Mongo client reads direct payment, correction, entrustment, proxy, lump-sum, and derived balances | B1 fixture durability proven without real data |
| Regression/compile | PASS | 37 tests pass, 1 opt-in Mongo class skip without flag; 6/6 Mongo fixture pass with flag; compileall pass | no available-suite regression observed |
| Ledger / Quick Entry | CLOSED | no held/unallocated ledger added; no Quick Entry added | defer to bounded B2 |

### R5 evidence and boundary

Fresh Anvien after the final test additions: 108 scanned / 58 parsed / 0
failures / 8,404 nodes / 9,421 relationships. The graph still reports HIGH
containing-file risk and resolver gaps for dirty core/UI files; this remains a
blast-radius warning and is recorded in the Supervisor report. A local
Streamlit health check returned `200 ok`; visible browser interaction could
not be independently driven because browser-control capability was unavailable.

No business database, credential, migration, deployment, P2P source, or real
money was touched. The opt-in Mongo fixture used a generated `l02b0_*` database,
fresh-client read-back, exact teardown, and a post-run inventory with no
remaining fixture database.

### R5 decision

- B1 bounded financial write safety: **PASS**.
- Quick Entry: **NO**; keep closed.
- Ledger foundation: **YES for a separate, bounded B2**, not a broad build.
- Owner decision needed: **NO**; the current B1 Owner decisions are already
  fixed and no new choice is required to hand off the B2 boundary.

## R1 — Post-implementation refresh

- Pure read model: `core/shipment_360.py` composes current receivable math,
  agency-scoped payable, explicit tax, linked records, and source/UNKNOWN
  states without persistence.
- UI: `views/shipment_360.py` renders the summary before the existing shipment
  tabs; `views/shipment.py` adds only read-only related-cache loading and the
  renderer call. A runtime check caught and fixed the total-receivable metric
  binding before final evidence.
- Runtime: `http://127.0.0.1:8516/_stcore/health` returned `200/ok`; reusable
  Browser result is PASS for detail open, financial-first order, valued total
  receivable, source/UNKNOWN/money map, close/list/filter, and no write click.
- Regression: 3 focused and 27 full unittest cases pass; `compileall` pass.
- Graph: final refreshed Anvien graph is 99 scanned / 57 parsed / 0 failures;
  target dirty `views/shipment.py` remains high-risk with 476 unresolved
  references. Detect-changes reports 17 pre-existing changed files, 3,620
  changed symbols, 74 affected nodes, and critical aggregate risk.
- Boundary: no real business write, migration, deployment, P2P edit, or
  isolated commit. Global payable, allocation, reconciliation, evidence,
  actual profit, and durable write/reload remain UNKNOWN or out of scope.
- Cleanup: Browser QA tab finalized, local Streamlit process stopped, port
  `8516` closed, and exact temporary LOG-C02 runtime logs removed; plan, QA,
  coder, supervisor, and source evidence were retained.

## Refresh log

| Refresh | Date | Scope | Result |
|---|---|---|---|
| R0 | 2026-08-14 | Current repo, graph, worktree, finance/payment/contract/proxy/wallet/tax/GetFly sources | P0 map complete; read-only vertical slice allowed |
| R1 | 2026-08-14 | New projection/renderer, local runtime, full tests, refreshed graph, Browser flow, detect-changes | bounded Slice A `partial/missing -> correct`; overall remains BLOCKED for dirty/persistence/governance/Docker boundaries | `E1-P1A-SRC`..`E2-SUPERVISOR` |
