# LOG-C06 Owner Review and Reconciliation Phase Actual Status

Title: LOG-C06 Owner Review and Reconciliation Phase
Date: 2026-08-15
Status: PRODUCT_PASS — LOG-C06 terminal closure; cutover publication deferred
Companion plan: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-plan.md`
Companion evidence: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-evidence.md`
Companion benchmark: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-benchmark.md`

## Purpose

This is the current-state gate for the Owner-authorized LOG-C06 staging/review continuation.
It records what is already correct, what is partial, what is missing, and what the next
slice may safely edit. It does not authorize live publication.

## Freshness / Refresh Rules

P0 records the continuation baseline. Refresh affected rows after every implementation slice,
append a status-refresh row, and update the next slice before proceeding when reality changes.

## Scope

Target scope:

- Six golden-item source reconstruction.
- Checkpoint component arithmetic and double-count protection.
- Deterministic 185-row clustering and derived Owner readiness.
- Business-language Historical Review panels and decision pack.
- Confirmed-only non-live draft regeneration and regression evidence.

Out of scope:

- Canonical ledger, payment writes, migration, publish/live cutover, approval, AI, Quick Entry,
  Docker deployment, workbook mutation, and unrelated dirty worktree changes.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `core/historical_staging.py` | E0-P0A-BASELINE1 | existing preserve-only module | source parser/provenance/status contract | preserve-only |
| `core/historical_opening.py` | E0-P0A-BASELINE1 | existing preserve-only module | confirmed-only draft/checkpoint contract | preserve-only |
| `views/historical_review.py` | E0-P0A-IMPACT1 | 3 inbound; 40 local; 6 flows | mounted staging DB/session review route and draft | high risk; minimal edit only |
| `views/partner_reconciliation.py` | prior LOG-C06 E0-P0A-IMPACT1 | existing C04/C05 surface | entry seam into Historical Review | preserve-only |
| `core/database.py`, `core/financial_ledger.py` | prior LOG-C06 E0-P0A-IMPACT1 | high-risk canonical surfaces | live/canonical writes | do-not-touch |
| `D:\Copy of TOYS-2025 - Copy.xls` | E0-P0A-SRC1 | external source | 8 sheets, Sheet2 282x14, source evidence | read/hash only |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | already satisfies the continuation contract | preserve and verify |
| `partial` | exists but misses business-review evidence | edit only missing seam |
| `missing` | required analysis/panel does not exist | implement bounded slice |
| `blocked` | source/authority/evidence unavailable | stop and record blocker |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Source workbook | present/read-only; hash known | unchanged source evidence | correct | external | E0-P0A-SRC1 | preserve |
| Staging parser/store | 289 staged rows; raw/proposal/history separated | provide stable input to analysis | correct | existing | E0-P0A-BASELINE1 | preserve |
| Opening model | confirmed-only, known-currency, non-checkpoint | remain confirmed-only and non-live | correct | existing | E0-P0A-BASELINE1 | preserve |
| Golden analysis | pure analysis contract now returns six values, source traces, business meaning, and checkpoint arithmetic | preserve read-only contract and expose it in UI | correct | new module | E1-P1A-GOLD1, E1-P1A-CHECKPOINT1, E1-P1A-ORACLE1 | proceed P2-A |
| Review clustering | all 185 review rows are deterministically assigned to 10 clusters with currency-separated totals and derived readiness | render cluster workload and bounded decision pack | correct | new module | E1-P1B-CLUSTER1, E1-P1B-READY1 | proceed P2-A |
| Historical Review UI | golden/cluster/decision pack, checkpoint explanation, review inbox, and draft panels render | preserve business-review surface and staging-only controls | correct | 4 inbound; 44 local; 6 flows | E2-P2A-UI1, E2-P2A-BROWSER1 | preserve |
| Canonical ledger/payment | untouched by LOG-C06 | remain untouched | correct/preserve-only | high risk | E0-P0A-BASELINE1 | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-15 | Owner continuation request and current repo/source | all continuation scope | initial classification | E0-P0A-OWNER1..E0-P0A-IMPACT1 | proceed to P1-A only after plan creation |
| R1 | 2026-08-15 | P1 pure analysis module + 22-test bounded regression | golden/checkpoint/cluster/readiness scope | P1-A and P1-B complete; no status or source mutation | E1-P1A-GOLD1..E1-P1B-READY1 | implement minimal P2-A render seam |
| R2 | 2026-08-15 | P2-A UI seam + visible browser + full regression + source hash | business panels, safety oracle, build and runtime evidence | P2-A and P2-B complete; no status/source/canonical mutation | E2-P2A-UI1..E2-P2B-BUILD1 | supervisor closure and scoped commit |
| R3 | 2026-08-15 | Anvien final refresh/detect + coder/supervisor review + scoped commit | closure and preservation boundary | PASS for staging/review; no live approval or canonical write | E3-CLOSE1 | stop; await Owner's six business decisions |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| Pure review analysis | none; new module | source consumer of staged items | P1-A/P1-B | edit | E0-P0A-GOLD1 | no DB/UI/canonical imports |
| `views/historical_review.py` | `tests/test_historical_review_ui.py` | UI consumer and direct test | P2-A | edit | E0-P0A-IMPACT1 | minimal import/render seam |
| `views/partner_reconciliation.py` | existing C04/C05 routes | entrypoint consumer | P2-A | preserve-only | prior LOG-C06 evidence | no route redesign |
| `core/historical_staging.py` | `core/historical_staging_store.py` | source contract | P1/P2 | inspect-only | E0-P0A-BASELINE1 | no raw/status mutation |
| `core/historical_opening.py` | `views/historical_review.py` | draft consumer | P2-A | preserve-only | E0-P0A-BASELINE1 | confirmed-only remains |
| `core/database.py`, `core/financial_ledger.py` | canonical consumers | forbidden write boundary | all | do-not-touch | E0-P0A-BASELINE1 | zero canonical effects |

## Detailed Findings

### Pure analysis contract

Current state:

The staging data is now consumed by a pure deterministic analysis contract. It reconstructs
six golden values, finds one exact 11-row candidate set for 134,973 CNY, clusters all 185
review rows, and derives Owner-readiness labels without changing the staged items.

Required state:

```text
Pure deterministic analysis returns golden evidence, candidate checkpoint arithmetic,
review clusters, derived readiness, and an Owner Decision Pack without mutation.
```

Evidence:

- E0-P0A-GOLD1: six requested source rows and surrounding rows were read.
- E0-P0A-CHECKPOINT1: candidate source rows sum exactly to 134,973 CNY.

Relationship and impact:

- Related file count: new module; no existing symbol impact.
- Relationship summary: consumes staged item dictionaries only.
- Impact note: low for new pure module; canonical boundary unaffected.

Classification:

correct for P1; the remaining implementation work is the P2-A render seam.

Allowed next action:

Render the analysis output in Historical Review, keeping the checkpoint and cutover locks
visible.

Forbidden next action:

Do not alter `review_status`, write DB rows, or include derived-ready rows in opening.

### Historical Review business surface

Current state:

The view now renders the six business evidence cards, deterministic cluster workload,
Owner Decision Pack, checkpoint arithmetic, review controls, and the confirmed-only draft.

Required state:

```text
Historical Review visibly explains the six golden items, clusters the 185-row workload,
shows only material Owner questions, and keeps DRAFT/NOT_READY cutover lock.
```

Evidence:

- E0-P0A-IMPACT1: view has 71 symbols, 3 inbound references, 6 flows, and high risk.
- E0-P0A-BASELINE1: existing UI has staging-only write oracle and confirmed-only draft.

Relationship and impact:

- Related file count: 3 inbound files; 40 local relationships; 6 flows.
- Relationship summary: direct Historical Review route and existing A Bò desk seam.
- Impact note: high risk; add only pure analysis import and bounded render helpers.

Classification:

correct for the staging/review scope; the browser evidence confirms the business-review
surface is mounted and the cutover remains locked.

Allowed next action:

Preserve the surface and complete supervisor/commit closure; Owner decisions remain
outside this implementation slice.

Forbidden next action:

Do not redesign the desk or add approve/live controls.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | Pure analysis returns all six golden rows and a unique exact checkpoint candidate set; tests pass. | complete; preserve arithmetic-only boundary |
| P1-B | 185 rows are assigned once to 10 deterministic clusters; readiness is derived and status remains unchanged. | complete; render decision reductions |
| P2-A | UI consumes pure analysis and renders golden evidence, clusters, decision pack, and checkpoint guard. | complete; preserve staging-only boundary |
| P2-B | Official browser, regression, build, health, source-hash, and Anvien evidence are current. | complete; close with supervisor and scoped commit |
| Pn | Supervisor PASS, dead-artifact review, final evidence, and scoped implementation commit are complete. | complete; stop until Owner supplies six decisions | complete | E3-CLOSE1 | no further implementation in this scope |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Existing target file relationship evidence is recorded.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct/preserve-only parts are marked.
- [x] Missing/partial parts have exact next actions.
- [x] Owner boundary and forbidden actions are recorded.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next phase status assumptions and work steps reflect current evidence.

## P1 Implementation Decision

- [x] P1-A complete: golden and checkpoint analysis verified.
- [x] P1-B complete: cluster and readiness analysis verified.
- [x] No Owner decision has been executed; zero `CONFIRMED` rows and zero canonical writes remain.
- [x] P2-A complete: business review surface verified in the real Historical Review route.
- [x] P2-B complete: browser/regression/build/source-fingerprint closure verified.

Decision note:

The pure P1 contract is ready for UI consumption. The exact checkpoint is an arithmetic
candidate only; row 129 remains excluded from opening and rows 109/115 remain separate
money legs. Proceed to P2-A with the same staging-only boundary.

P2 closure note:

The six golden items are review-ready evidence, not confirmations. The draft remains
`DRAFT / NOT_APPROVED / NOT_LIVE`, with zero confirmed opening components. The only
remaining business work is the Owner's six explicit decisions; no workbook edit or live
write is needed for this closure.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Owner authorization is sufficient for staging/review analysis and business decision-pack
preparation. The missing pure analysis and UI panels are bounded. The source workbook,
staging boundary, confirmed-only opening model, and canonical preserve-only boundary are
available and must remain unchanged while P1 proceeds.

## P3 Actual Status — Owner decisions applied to staging review

### Current status matrix

| Unit | Status | Evidence | Next action |
|---|---|---|---|
| Owner decision batch | COMPLETE | E4-P3-BATCH1 | Preserve deterministic request IDs and audit records |
| 24,576 CNY credit | CONFIRMED / EMBEDDED_IN_SNAPSHOT | E4-P3-24576 | Do not reapply to opening |
| 62,464 CNY | CONFIRMED / RECEIVED_ON_BEHALF | E4-P3-RECEIVED1 | Keep shipment unallocated unless separately proven |
| 1,687 CNY | CONFIRMED / RECEIVED_ON_BEHALF | E4-P3-RECEIVED1 | Keep separate from 62,464 and unallocated if unproven |
| 1,572 CNY | REVIEW_REQUIRED | E4-P3-1572 | Owner evidence still required; exclude from opening/debit |
| 25,025 CNY B&G Green | CONFIRMED / PAID_ON_BEHALF | E4-P3-BG1 | Preserve receipt and beneficiary legs separately |
| 134,973 CNY | CONFIRMED / SUMMARY_CHECKPOINT | E4-P3-CHECKPOINT1 | Exclude summary row from event sum |
| 159,998 CNY | DERIVED / EXACT_MATCH | E4-P3-CHECKPOINT1 | Use as one derived group only |
| 416,482.2426005565 CNY | EXPECTATION / DIFFERENCE | E4-P3-RECEIVED1 | Resolve 67,033.84966649559 CNY source gap |
| Draft opening | NOT_READY / DRAFT | E4-P3-OPENING1 | No publication; preserve lineage |
| Canonical boundary | LOCKED | E4-P3-ORACLE1 | No ledger, migration, Quick Entry, payment, or AI action |

### Post-batch counts

Stored review statuses are `CONFIRMED=20`, `REVIEW_REQUIRED=170`, `RAW=39`,
`NOT_APPLICABLE=60`, `PROPOSED=0` (289 total). Analysis-level Owner states are
`CONFIRMED=20`, `REVIEW_REQUIRED=77`, `UNKNOWN=132`, and `NOT_APPLICABLE=60`.
The two views are intentionally distinct: `UNKNOWN` is a derived analysis state,
not a new persisted review status.

### Draft opening position

The opening draft uses one traceable lineage:

```text
BASE / SOURCE COMPONENTS
  paid-on-behalf group: 159,998.0 CNY
  received-on-behalf source events: 349,448.3929340609 CNY
POST-BASE EVENTS
  none
OPENING PUBLICATION
  forbidden; DRAFT / NOT_APPROVED / NOT_LIVE
```

The 24,576 CNY credit is embedded in the 99,824.43 CNY snapshot and contributes
zero as a standalone opening event. The 134,973 CNY summary is excluded because
its 11 confirmed components already contribute to the derived 159,998 CNY group.

### Remaining material difference

The six Owner-named received rows sum to `349,448.3929340609 CNY`, while the
historical expectation is `416,482.2426005565 CNY`; the difference is
`67,033.84966649559 CNY`. Using the source sum in the historical formula produces
`228,610.3970659391 CNY`, versus the checkpoint expectation
`161,576.5473994435 CNY`. This is not auto-filled.

Other legacy checkpoint rows remain unresolved by source semantics, so the draft
also retains `CHECKPOINT_NOT_RECONCILED`, `REVIEW_REQUIRED_ITEMS_REMAIN`, and
`UNKNOWN_CURRENCY_REMAINS` gates.

### Closure evidence

- Full compile/build passed.
- Focused LOG-C06 tests passed `26/26`.
- Full unittest discovery passed `117` with `2` guarded skips.
- Visible browser QA passed `5/5`; health `200`; no browser errors; zero
  canonical controls; zero canonical writes.
- Source workbook SHA-256 remains
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
- Anvien graph was refreshed before the final change-detection pass; the dirty
  worktree contains unrelated user files that remain preserved and unstaged.
- Supervisor accepted the bounded staging/review scope; no live cutover is
  claimed.

## P4 Actual Status — technical source-lineage reconciliation baseline

### Current status matrix

| Unit | Current state | Required state | Status | Evidence | Next action |
|---|---|---|---|---|---|
| Six-source received group | Current staging total is `349,448.3929340609 CNY` versus verified historical expectation `416,482.2426005565 CNY`; row-level deltas not yet proven | Cell-by-cell source/staging table with exact delta sum | partial | E4-P4A-BASELINE1 | inspect C102/C109/C115/C190/C197/C198 before any Owner question |
| C190/C197/C198 | Historical source oracle is `183,549 + 19,000 + 124,485 = 327,034 CNY`; staging preservation is not yet independently proven in this slice | exact source/staging match or deterministic lineage defect | partial | E4-P4A-BASELINE1 | trace physical rows, selected cells, normalized fields |
| C115 FX item | Historical reference is `100,000,000 VND / 3,953 = 25,297.24260055654 CNY`; staging conversion path is not yet independently proven | preserve historical conversion with no current FX | partial | E4-P4A-BASELINE1 | compare raw VND, rate, CNY reference, and inclusion |
| Row 86 / E86 | Parser proposal is `7,683 CNY`; raw source reconstruction is `99,824.43 CNY`; exact parser-selected cell is not yet traced | source formula/cached value and parser origin fully explained | partial | E4-P4A-BASELINE1 | trace E77, E85, E86, merged context, and parser amount field |
| Historical checkpoints | Old M89 `170,374.18739944347` and updated position `161,576.5473994435` are known but their explicit supersession graph is not yet rendered for P4 | checkpoints relate by scope/time without double counting | partial | E4-P4A-BASELINE1 | add supersession lineage to reconciliation output |
| Staging/canonical boundary | Prior Owner batch is staging-only and cutover remains locked | no balancing event or canonical write | correct | E4-P3-ORACLE1 | preserve and regression-test |

### P4 baseline facts

- Owner instruction changes the next action: the 67,033.8497 CNY difference is a
  technical reconciliation target, not an Owner question at this stage.
- Source workbook remains read-only and must retain SHA-256
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
- No source/staging correction has been made yet in P4.
- The six verified received values are C102 `62,464`, C109 `1,687`, C115
  `25,297.24260055654`, C190 `183,549`, C197 `19,000`, and C198 `124,485` CNY.
- The P4 implementation gate is open only for deterministic parser/normalization
  defects proven by source-level evidence; business meaning and confirmed Owner
  classifications remain preserve-only.

### P4 status refresh log

### P4 completion update

Final P4 status: complete for staging/review reconciliation; cutover remains locked.

- Six-source received group: `RECONCILED`, `416,482.2426005565 CNY`, row delta sum `0.0`.
- Physical source mapping: `C190 -> Sheet2!C192`, `C197 -> Sheet2!C199`, `C198 -> Sheet2!C200`.
- Row 86: parser/reference text `D86` no longer supplies an amount; corrected proposal lineage is `Sheet2!E86 = 99,824.43 CNY`; old raw staging artifact remains immutable.
- Old M89 is `SUPERSEDED_CHECKPOINT`; the updated historical position is `161,576.5473994435 CNY` with zero material difference.
- Durable counts: `20 CONFIRMED`, `170 REVIEW_REQUIRED`, `60 NOT_APPLICABLE`, `39 RAW`, `0 REJECTED`; audit records `27`.
- Draft remains `DRAFT / NOT_APPROVED / NOT_LIVE`; canonical writes `0`; opening publication `false`.
- Final Anvien refresh: `208` files scanned, `94` parsed code files, `0` parse failures; detect-changes shows `30` changed files and `27` affected files at critical aggregate risk due to unrelated dirty worktree changes, which remain preserved and unstaged.

| Refresh | Date | Repo basis | Changed scope | Status change | Evidence | Next action |
|---|---|---|---|---|---|---|
| R4 | 2026-08-15 | New Owner follow-up request plus fresh Anvien graph refresh | six-source received group and E86 parser mismatch | prior P3 closure reopened only for technical reconciliation; no cutover state change | E4-P4A-BASELINE1 | reproduce source/staging rows before editing |

## P5 Actual Status — final opening-impact sufficiency

P5 is complete for the Owner-authorized staging/review scope. The former
technical reconciliation is treated as resolved evidence and is not reopened
here. No canonical mutation, publication, approval, Quick Entry, payment, AI,
deployment, or LOG-C07 implementation occurred.

### Current status matrix

| Unit | Current state | Required state | Status | Evidence | Next action |
|---|---|---|---|---|---|
| Verified base | `161,576.5473994435 CNY`; source boundary reaches physical received row 200 / `2026-05-28` | one traceable base only | correct but temporal confidence LOW | E5-P5-SCOPE1 | Owner may clarify shipment-cost checkpoint date/scope |
| Supersession graph | 24,576 embedded; 99,824.43 snapshot; 134,973 summary; 159,998 derived; old M89 superseded; zero checkpoint events counted | no checkpoint double count | correct | E5-P5-GRAPH1 | preserve graph |
| Opening-impact classification | 289/289 items classified once | seven exclusive categories; count sum 289 | correct | E5-P5-CLASSIFY1 | preserve pure classifier |
| Opening-material blockers | 14 total: 7 post-base review + 7 unresolved material | Owner pack only material blockers | partial / blocking | E5-P5-REDUCE1, E5-P5-POST1, E5-P5-MATERIAL1 | resolve only listed rows/semantics |
| 1,572 CNY | dated 2026-01-22; NOT_APPLICABLE/excluded | no automatic opening inclusion | correct | E5-P5-1572 | keep excluded unless Owner supplies direct ownership evidence |
| Shipment linkage | 62,464 and 1,687 remain unallocated by shipment ID | metadata debt must not block confirmed opening | correct | E5-P5-SHIPMENT1 | no action unless allocation changes amount/owner |
| Candidate opening | `161,576.5473994435 CNY`; 0 confirmed post-base increases/reductions | reproducible base + post-base formula | correct / provisional | E5-P5-CANDIDATE1 | do not publish |
| Readiness | `NOT_READY` with four material/scope reasons | READY only after blockers and scope are resolved | blocked for cutover, not implementation | E5-P5-READINESS1 | Owner decision pack only |
| Canonical boundary | 0 writes; publication false | remain untouched | correct | E5-P5-ORACLE1 | preserve lock |

### P5 category counts

All staged items: `EMBEDDED_IN_VERIFIED_BASE=19`, `POST_BASE_CONFIRMED=0`,
`POST_BASE_REVIEW_REQUIRED=7`, `REFERENCE_ONLY=74`, `NOT_APPLICABLE=122`,
`UNRESOLVED_NON_MATERIAL=60`, `UNRESOLVED_MATERIAL=7`.

The 170 stored review-required items are not a blanket blocker. Within that
subset, 62 are not applicable, 57 are reference-only, 46 are unresolved but
non-material, and 5 are post-base review candidates. The seven material
shipment rows are currently stored as NOT_APPLICABLE but have explicit
post-base SALE Thành evidence and are therefore retained in the opening
material pack rather than silently discarded.

### P5 candidate and cutover state

```text
VERIFIED BASE                         161,576.5473994435 CNY
+ POST_BASE_CONFIRMED INCREASES                 0.0 CNY
- POST_BASE_CONFIRMED REDUCTIONS                 0.0 CNY
= CANDIDATE OPENING                   161,576.5473994435 CNY

OPENING SUFFICIENCY                   NOT_READY
DRAFT STATUS                          DRAFT
APPROVAL                              NOT_APPROVED
LIVE                                  NOT_LIVE
CANONICAL WRITES                      0
```

### P5 status refresh log

| Refresh | Date | Repo basis | Changed scope | Status change | Evidence | Next action |
|---|---|---|---|---|---|---|
| R5 | 2026-08-15 | fresh Anvien graph, source hash, 289 staging rows, independent verifier | temporal scope, supersession, opening-impact categories, candidate formula, QA | P5 complete for staging/review; cutover remains NOT_READY and locked | E5-P5-SCOPE1..E5-P5-SUPERVISOR1 | await only opening-material Owner decisions; do not open LOG-C07 |

### Closure evidence

- Focused sufficiency/opening tests: `16/16` passed.
- Full unittest discovery: `130` passed, `2` existing guarded skips.
- Compileall and independent verifier: passed.
- Historical Review smoke QA: 0 exceptions, required labels present.
- Fresh Data-Integrity report: PASS for staging-only integrity.
- Fresh Supervisor report: PASS for bounded staging/review scope.
- Final Anvien refresh before change detection: 215 scanned, 99 parsed code,
  0 parse failures; critical aggregate risk is due to unrelated dirty files
  preserved outside this LOG-C06 scope.

## P6 Actual Status — deterministic blocker reconstruction

P6 is complete for the current Owner-authorized staging/review scope. The
source workbook is unchanged and read-only. The implementation adds a pure
P6 reconstruction projection and an independent verifier; it does not mutate
staging status or call any canonical writer.

### Current status matrix

| Unit | Current state | Required state | Status | Evidence | Next action |
|---|---|---|---|---|---|
| Rows 201–205 | C total `392,796.30579784507 CNY`; D total `392,790 CNY`; VND input `1,531,120,000`; no explicit A Bò/Thành relation | one Owner decision about relationship and selected leg | review-required, grouped | E6-P6-2012051 | Owner selects C or D meaning, direction, and currency |
| Rows 213–219 | goods detail; H sum `16,929.56` matches H224; no freight total | no opening impact from goods fields | correct / reference-only | E6-P6-2132191 | no Owner question unless separate freight evidence appears |
| Rows 229–230 | freight totals M229=`5,610`, M230=`1,450`, M235=`7,060`; SALE Thanh explicit; currency/direction unknown | one Owner decision for paid-on-behalf meaning and currency | review-required, grouped | E6-P6-2292301 | Owner confirms currency and A Bò payment direction |
| 418,060.79 | no exact source cell or unique provenance found | source-grounded date/range or Owner checkpoint confirmation | material evidence gap | E6-P6-4181 | keep checkpoint-only; do not infer rows |
| 1,572 vs 1,578.5474 | row 96 source E97=`1,572`; exact 1,578.5474 absent | preserve exclusion | correct / no opening effect | E6-P6-1572 | leave REVIEW_REQUIRED and excluded |
| Temporal boundary | last embedded `2026-05-28`; first non-embedded `2026-05-29`; proposed as-of `2026-05-28`, LOW | defensible base scope | not ready | E6-P6-TIME1 | resolve shipment-cost checkpoint date/scope |
| Candidate opening | `161,576.5473994435 CNY`; no confirmed post-base events | base + proven post-base events only | provisional | E6-P6-SCENARIO1 | do not publish |
| Canonical boundary | writes `0`; publication false; `DRAFT / NOT_APPROVED / NOT_LIVE` | preserve lock | correct | E6-P6-ORACLE1 | no cutover, no LOG-C07 |

### P6 classification and review counts

Category counts across all 289 rows are `19 EMBEDDED_IN_VERIFIED_BASE`, `0
POST_BASE_CONFIRMED`, `7 POST_BASE_REVIEW_REQUIRED`, `81 REFERENCE_ONLY`,
`122 NOT_APPLICABLE`, `60 UNRESOLVED_NON_MATERIAL`, and `0
UNRESOLVED_MATERIAL`. Stored statuses remain `20 CONFIRMED`, `170
REVIEW_REQUIRED`, `60 NOT_APPLICABLE`, `39 RAW`, and `0 REJECTED`; derived
proposal classification is `UNKNOWN=231`. The opening-material blocker count
is 7, but the beginner-first Owner pack has only 2 independent questions.

### P6 status refresh log

| Refresh | Date | Repo basis | Changed scope | Status change | Evidence | Next action |
|---|---|---|---|---|---|---|
| R6 | 2026-08-15 | fresh Anvien graph, direct workbook scan, staging projection, P6 verifier | blocker source context, grouped semantics, temporal boundary, scenarios | unresolved material rows reduced 7→0; row-level blockers 14→7; cutover remains locked | E6-P6-SCOPE1..E6-P6-ORACLE1 | wait for the two grouped Owner decisions and shipment-cost checkpoint evidence |

### P6 closure evidence

- Focused P6 tests passed `14/14`; compatibility sufficiency verifier passed.
- Independent P6 verifier passed source hash, source-cell absence, exact subtotal,
  temporal, scenario, draft-lock, and canonical-zero assertions.
- Compileall passed; full regression passed `134` tests with `2` guarded
  skips; visible historical-review smoke QA passed with `0` exceptions.
- Fresh Data-Integrity report: PASS for the P6 staging-only contract, with a
  separate MEDIUM concurrency advisory outside the P6 pure-analysis path.
- Fresh Supervisor report: PASS for the bounded P6 implementation; it does not
  authorize live publication or canonical mutation.

## Terminal product closure

Owner roadmap decision: `PRODUCT_PASS`.

- Historical staging: `PASS`
- Historical provenance mechanism: `PASS`
- Owner review mechanism: `PASS`
- Checkpoint reconstruction: `PASS`
- Double-count protection: `PASS`
- Cutover sufficiency mechanism: `PASS`
- Canonical financial mutation: `0`
- Historical A Bò live opening: `NOT_PUBLISHED`
- Cutover publication: `DEFERRED_OWNER_GATED`
- Remaining historical ambiguity: `PRESERVED / DEFERRED`
- Deferred backlog: `.p2p/state/deferred-historical-reconciliation.json`

`161,576.5473994435 CNY` remains historical reconciled candidate/checkpoint
evidence only. No further A Bò historical investigation is part of LOG-C06.
LOG-C07 is a separate new-chat product goal.
