# LOG-C05 Manager Report & Debit Draft Actual Status

Title: LOG-C05 Manager Report & Debit Draft
Date: 2026-08-14
Status: P1-A Complete; P1-B in progress
Companion plan: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-plan.md`
Companion evidence: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-benchmark.md`

## Purpose

This file records the real current state before LOG-C05 implementation and
remains a living status matrix throughout the plan.

## Freshness / Refresh Rules

Refresh affected rows after each implementation slice and before the next
phase. Keep prior decisions in the Status Refresh Log; update only stale
current-state facts and next-phase actions.

## Scope

Target scope:

- Deterministic manager report and Debit Draft from the LOG-C04 canonical A Bò / SALE Thành projection.
- Metadata-only snapshot/version persistence and retry safety.
- Bounded Streamlit actions, fixture coverage, write oracle, regression, and browser evidence.

Out of scope:

- Payment execution, bank integration, Excel import/migration, AI, owner inference/migration, full FX, accounting GL, period close, frontend rewrite, Docker setup, and unrelated dirty-worktree edits.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `core/reconciliation.py` | `E0-P0A-IMPACT1` | 73 symbols; 31 local relationships; 11 linked flows | Existing pure explanation/review/trace/period helpers are the read-model seam. | high scope warning; add a separate pure LOG-C05 module rather than destabilizing C04 helpers. |
| `core/financial_ledger.py` projection | `E0-P0A-IMPACT1` | 137 symbols; 75 linked flows; high file risk | Canonical projection and financial writes share this file. | preserve-only unless a contract gap is proven; no write-path edits. |
| `core/database.py` | `E0-P0A-IMPACT1` | 137 symbols; 128 local relationships; 75 linked flows; high file risk | Shared Mongo repository and index seam. | narrow index-only edit if needed; no financial repository rewrite. |
| `views/partner_reconciliation.py` | `E0-P0A-IMPACT1` | 46 symbols; 17 local relationships; 8 linked flows; high file risk | Existing mounted A Bò / SALE Thành desk and C04 controls. | edit bounded actions/rendering; preserve route and read-only controls. |
| `views/web_app.py` | `E0-P0A-ROUTE1` | existing route registry | `Công nợ A Bò` already maps to the desk; Dashboard is default. | preserve-only; no home/navigation rewrite. |
| `tests/test_reconciliation_desk.py` | `E0-P0A-FIXTURE1` | 38 symbols; 15 local relationships | C04 fixture semantics and regression tests. | preserve; add LOG-C05 tests in a new module. |
| `playwright/log_c04_partner_reconciliation_flow.mjs` | `E0-P0A-SOURCE1` | reusable C04 route flow | Existing local browser path for desk/search/trace/period. | preserve; add a separate LOG-C05 flow. |
| existing export helpers | `E0-P0A-EXPORT1` | shipment-oriented helper only | No partner debit report export contract exists. | inspect-only; do not introduce a document subsystem. |
| live canonical owner coverage | `E0-P0A-SOURCE1` | projection metadata | `internal_sale_owner` is incomplete; live positive rows may be absent. | truthful empty/incomplete state; no migration or note inference. |
| worktree | `E0-P0A-GIT1` | N/A | Prior goals have many modified/untracked files. | preserve unrelated changes; no broad staging/reset. |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Conflicts with requirement. | Replace the offending behavior. |
| `missing` | Required behavior does not exist. | Implement the missing piece. |
| `unbound` | Surface exists but is not wired to the required source/flow. | Bind only to the real source. |
| `fake-or-stub` | Demo/mock/fallback is being used as real behavior. | Remove or make the state truthful. |
| `blocked` | Required authority/evidence/dependency is unavailable. | Stop and record the blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Canonical partner projection | LOG-C04 projection is read-only, exact-owner filtered, multi-currency, and exposes business buckets plus source/allocation traces. | Remain source of truth for LOG-C05 calculations. | correct | 137 symbols; 75 linked flows | `E0-P0A-SOURCE1`, `E0-P0A-IMPACT1` | preserve-only; P1 consumes it. |
| Existing C04 pure reconciliation helpers | Explanation, review inbox, trace, period draft, and reported comparison exist and are deterministic. | Continue to support C04 and be reused where appropriate. | correct | 73 symbols; 11 linked flows | `E0-P0A-SOURCE1`, `E0-P0A-IMPACT1` | preserve; add separate LOG-C05 pure module. |
| Manager report model | Pure LOG-C05 report contract now derives per-currency summary, deterministic explanation, shipment impact, review separation, and partner difference. | Per-currency manager summary, explanation, shipment impact, review separation, partner difference. | correct | `core/debit_draft.py`: 101 symbols; 49 local relationships; 24 linked flows | `E1-P1A-GRAPH1`, `E1-P1A-MODEL1`, `E1-P1A-TEST1` | preserve pure contract; consume from P2. |
| Debit eligibility/calculator | Pure calculator now applies source-backed eligibility, exact currency-separated arithmetic, inclusion/exclusion reasons, and no manual total. | Eligible payable/credit/settlement only, exact arithmetic, exclusions, no manual total. | correct | `core/debit_draft.py`: 101 symbols; 49 local relationships; 24 linked flows | `E1-P1A-MODEL1`, `E1-P1A-TEST1`, `E1-P1A-ORACLE1` | preserve pure contract; add snapshot metadata in P1-B. |
| Snapshot/version repository | Metadata-only `DEBIT_DRAFT_SNAPSHOT` repository now supports READY_FOR_REVIEW, immutable content hash, V1/V2 supersession, reopen/list, and request-id retry safety; collection index is ensured at the metadata boundary. | READY_FOR_REVIEW snapshot, V1/V2 trace, retry-safe request identity, metadata-only write. | correct | `core/debit_snapshot.py`: 40 symbols; 18 local relationships; 1 linked flow | `E1-P1B-GRAPH1`, `E1-P1B-SNAPSHOT1`, `E1-P1B-RETRY1` | preserve; bind only to P2 explicit snapshot/reopen action. |
| Existing A Bò / SALE Thành desk | Read-only C04 desk now also exposes Báo cáo Sếp, Debit Draft, deterministic explanations, included/excluded rows, and guarded snapshot controls; empty live data remains truthful. | Add report/debit actions while preserving current controls. | correct for bounded local scope | 80 symbols; 35 local relationships; 4 inbound references; 13 linked flows; refreshed upstream impact MEDIUM (8 direct symbols, 1 file, 1 flow) | `E2-P2A-GRAPH1`, `E2-P2A-REPORT1`, `E2-P2A-DEBIT1`, `E2-P2A-WRITE1`, `E2-P2A-WRITE2` | preserve route and C04 controls; live positive data remains unverified. |
| Route/navigation | `Công nợ A Bò` remains mounted in `views/web_app.py`; Dashboard remains first route; new actions are in-desk state navigation. | Desk -> Báo cáo Sếp -> Debit Draft without changing home. | correct for bounded local scope | route registry plus mounted view | `E0-P0A-ROUTE1`, `E2-P2B-BROWSER1` | preserve-only; no home redesign. |
| LOG-C05 fixture matrix | New isolated test module covers the required C04 semantics plus the clean 40,000 CNY debit arithmetic. | Add manager/debit exact arithmetic and clean 40,000 CNY case. | correct | 28 symbols; 11 local relationships | `E1-P1A-TEST1`, `E1-P1A-ORACLE1` | preserve; extend only if P1-B exposes a contract gap. |
| Financial write oracle | C04 read-only oracle plus LOG-C05 snapshot oracle prove zero calculation effects and canonical before/after equality; only snapshot metadata changes. | Report/debit calculation zero effects; snapshot write changes only metadata. | correct | new snapshot test: 17 symbols; 5 local relationships | `E1-P1A-ORACLE1`, `E1-P1B-ORACLE1`, `E1-P1B-TEST1` | preserve; P2 may expose metadata action only. |
| Browser QA | C05 reusable flow is present and syntax-valid; direct local Chrome evidence covers desk/report/debit screenshots and truthful empty state; console smoke is 0/0, but the separate headless sidebar probe is not used to claim a complete wrapper-flow/dashboard-return run. | Reusable report/debit journey with screenshot and console evidence. | correct for bounded local scope; production-like validation blocked | flow file plus 3 official screenshots and QA JSON/MD | `E2-P2B-BROWSER1`, `E2-P2B-CONSOLE1`, `E2-P2B-REPORT1` | preserve truthful empty state; Docker and positive-live remain separate blockers. |
| Export/print | Existing helper exports shipment debit note only; no partner report/debit export contract. | Reuse only if safe/simple; export is not acceptance-critical. | missing / preserve-only | existing helper outside target | `E0-P0A-EXPORT1` | do not build subsystem; report as gap unless a native path fits. |
| Live positive state | Owner-normalized live rows may be absent; C04 already shows truthful empty/incomplete state. | Never fake live debit data; use fixture positives. | blocked for positive-live proof | projection owner metadata | `E0-P0A-SOURCE1`, `E0-P0A-RUNTIME1` | preserve truthful empty state; classify positive-live as unverified. |
| Docker runtime | No Dockerfile/compose target in current repo. | Full container proof only if an existing target is available. | blocked | N/A | `E0-P0A-RUNTIME1` | record blocker; do not create Docker in LOG-C05. |
| Worktree safety | Known dirty worktree with previous goal artifacts; scoped LOG-C05 commits contain only the implementation/evidence files, while unrelated source and earlier debug captures remain outside the commits. | LOG-C05-only additions and preservation of unrelated files. | correct / preserve-only | N/A | `E0-P0A-GIT1`, `E3-P3A-DETECT1`, `E3-P3A-REPORT1` | no reset/checkout/broad stage; final response names the preserved boundary. |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | baseline before LOG-C05 implementation | full LOG-C05 boundary | initial classifications recorded; P0 complete | `E0-P0A-REQ1..E0-P0A-RUNTIME1` | P1-A adds a new pure model; P1-B adds metadata-only snapshots; P2 consumes them without route rewrite. |
| R1 | 2026-08-14 | post-P1-A Anvien refresh and 10 focused tests | manager report, debit calculator, fixture matrix | manager report missing -> correct; debit calculator missing -> correct; fixture matrix partial -> correct | `E1-P1A-GRAPH1`, `E1-P1A-MODEL1`, `E1-P1A-TEST1`, `E1-P1A-ORACLE1` | P1-B adds metadata-only snapshot/version persistence; canonical financial paths remain preserve-only. |
| R2 | 2026-08-14 | post-P1-B Anvien refresh and 14 focused tests | snapshot/version repository, write oracle | snapshot repository missing -> correct; financial write oracle partial -> correct | `E1-P1B-GRAPH1`, `E1-P1B-SNAPSHOT1`, `E1-P1B-TEST1`, `E1-P1B-RETRY1`, `E1-P1B-ORACLE1` | P1 is complete; P2 wires the existing desk without changing route/home or financial writes. |
| R3 | 2026-08-14 | post-P2 Anvien refresh, recorder tests, local runtime screenshots, and 80-test suite | mounted report/debit UI, browser evidence, validation | desk/report/debit UI missing -> correct for bounded local scope; browser evidence correct for local empty state; positive-live and Docker remain unverified/blocked | `E2-P2A-GRAPH1`, `E2-P2A-REPORT1`, `E2-P2A-DEBIT1`, `E2-P2A-WRITE1`, `E2-P2B-BROWSER1`, `E2-P2B-CONSOLE1`, `E2-P2B-REPORT1`, `E3-P3A-TEST1`, `E3-P3A-REG1` | finish scoped commit, detect-changes, coder report, supervisor review, and final closure; do not open LOG-C06. |
| R4 | 2026-08-14 | post-commit graph refresh, final 80-test suite, health check, final detect-changes, coder report, and supervisor review | closure evidence and acceptance | all bounded local implementation rows remain correct; supervisor verdict PASS; Docker/positive-live remain explicitly blocked/unverified; dirty-worktree preservation is documented | `E3-P3A-TEST1`, `E3-P3A-BROWSER1`, `E3-P3A-DETECT1`, `E3-P3A-REPORT1` | close LOG-C05 at bounded local PASS; no release/deploy and no LOG-C06. |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/debit_draft.py` | `core/reconciliation.py` | pure read-model sibling | P1-A/P1-B | edit | `E0-P0A-IMPACT1` | no DB/Streamlit imports in pure functions; metadata repository isolated. |
| `core/financial_ledger.py` | `core/debit_draft.py` | canonical projection source | P1-A | preserve-only | `E0-P0A-IMPACT1` | no financial write-path edits. |
| `core/database.py` | `core/debit_draft.py` | snapshot collection/index dependency | P1-B | edit only index list if required | `E0-P0A-IMPACT1` | no changes to canonical writes; metadata collection only. |
| `views/partner_reconciliation.py` | `core/debit_draft.py` | mounted UI consumer | P2-A | edit | `E0-P0A-IMPACT1` | no manual debit number, no payment control. |
| `views/web_app.py` | `views/partner_reconciliation.py` | route registry | P2-A | preserve-only | `E0-P0A-ROUTE1` | Dashboard remains default; existing route preserved. |
| `tests/test_log_c05_report_debit.py` | `core/debit_draft.py` | pure behavior/fixture test | P1-A/P3-A | add | `E0-P0A-FIXTURE1` | in-memory fixture only. |
| `tests/test_log_c05_snapshot_write_oracle.py` | `core/debit_draft.py` / memory DB | metadata/write oracle | P1-B/P3-A | add | `E0-P0A-IMPACT1` | canonical before/after equality. |
| `playwright/log_c05_manager_report_debit_flow.mjs` | local Streamlit runtime | browser evidence | P2-B | add | `E0-P0A-SOURCE1` | reusable script; no live fixture seeding. |
| `reports/QA/playwright/*log-c05*` | Playwright script/runtime | official evidence | P2-B/P3-A | add | `E0-P0A-RUNTIME1` | new artifacts only; inspect screenshots. |

## Detailed Findings

### Canonical projection

Current state:

LOG-C04's `project_partner_financial_position` is the canonical, read-only
source. It filters by exact `internal_sale_owner`, derives allocation/outstanding
values, separates confirmed/review buckets, keeps currencies separate, and
exposes source/evidence/allocation IDs.

Required state:

```text
canonical projection -> deterministic report/debit model -> UI
snapshot metadata only; underlying financial collections unchanged
```

Evidence:

- `E0-P0A-SOURCE1`: source inspection and existing C04 tests.
- `E0-P0A-IMPACT1`: high shared-file blast-radius evidence.

Relationship and impact:

- Related file count: 137 symbols and 75 linked flows in the projection file.
- Relationship summary: the same file contains financial write functions.
- Impact note: preserve-only is the safe LOG-C05 boundary.

Classification:

`correct`

Allowed next action:

Consume the returned mapping in a new pure calculator and preserve the
projection/write paths.

Forbidden next action:

Do not add a second ledger, derive owner from notes, or mutate canonical rows
to make debit match.

### Report/debit domain

Current state:

No report/debit contract exists. The current desk shows C04 buckets but does
not calculate eligible settlement items or preserve a historical debit.

Required state:

```text
canonical rows -> eligibility checks -> per-currency report/debit
-> deterministic explanation/exclusions -> optional metadata snapshot
```

Evidence:

- `E0-P0A-REQ1`: LOG-C05 acceptance requires report/debit separation and snapshots.
- `E0-P0A-FIXTURE1`: existing semantic fixtures are ready to be consumed but lack clean debit arithmetic.

Relationship and impact:

- Related file count: new module has no current relationships; it will be
  consumed by the existing high-risk desk only after pure tests pass.
- Impact note: keep the model pure and avoid expanding `core/financial_ledger.py`.

Classification:

`missing`

Allowed next action:

Implement P1-A with exact source-ID-backed outputs and fixture tests.

Forbidden next action:

Do not accept a user-entered debit total, combine currencies, or include
UNKNOWN/restricted/unallocated-not-approved rows.

### Snapshot persistence

Current state:

The repository has MongoDB/action-request/index conventions, but no debit draft
snapshot collection or version identity.

Required state:

```text
READY_FOR_REVIEW -> immutable metadata snapshot V1
regenerate -> V2 + supersedes V1; retry request -> same V1
```

Evidence:

- `E0-P0A-IMPACT1`: shared database file is high blast radius.
- `E0-P0A-REQ1`: snapshot fields and no-financial-effect rule.

Relationship and impact:

- Related file count: database has 137 symbols, 128 local relationships, and
  75 linked flows.
- Impact note: narrow snapshot collection/index edit only; no canonical schema rewrite.

Classification:

`missing`

Allowed next action:

Implement P1-B with disposable memory-DB tests, stable request identity, and
canonical before/after proof.

Forbidden next action:

Do not update obligations, transactions, allocations, corrections, or partner
position as part of snapshot creation.

### Mounted UI and runtime

Current state:

The existing desk route is mounted and truthful for empty/incomplete live owner
data, but report/debit actions are absent. There is no Docker target in the
workspace.

Required state:

```text
existing desk -> Báo cáo Sếp -> Debit Draft -> optional snapshot/reopen
```

Evidence:

- `E0-P0A-ROUTE1`: existing route registry.
- `E0-P0A-RUNTIME1`: no Docker build target.

Relationship and impact:

- Related file count: partner view has 46 symbols and 8 linked flows.
- Impact note: edit only the bounded view actions; retain C04 search/trace/period/reported controls.

Classification:

`partial`; Docker production-like validation is `blocked`.

Allowed next action:

Add the two actions and a reusable local browser flow; report positive-live and
Docker limitations explicitly.

Forbidden next action:

Do not seed live fixtures, create Docker, or turn the debit draft into payment execution.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Pure report/debit model and fixture oracle pass 10/10 focused tests; canonical source remains correct/preserve-only. | complete; preserve new pure module and do not edit financial writes. |
| P1-B | Metadata-only snapshot/version repository and memory-DB write oracle pass; shared financial modules remain preserve-only. | complete; bind only explicit metadata snapshot/reopen controls in P2. |
| P2-A | Existing desk now renders the bounded report/debit surfaces and explicit metadata-only snapshot path; route/home and C04 controls are preserved. | complete for bounded local scope; preserve financial write paths and truthful empty state. |
| P2-B | C05 flow file and official screenshots/QA artifacts exist; local runtime is healthy; Docker target and positive live rows are unavailable. | complete for local evidence with explicit Docker/positive-live limitations; do not overclaim wrapper-flow completion. |
| P3-A | Compile, focused regression, and full suite pass; health and screenshot evidence are recorded; final detect-changes and closure review remain. | finish detect-changes, scoped commit, coder report, supervisor review, and final product/P2P verdict separation. |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable or a documented dynamic/runtime limitation.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only stale next-phase assumptions/actions/work steps will be updated before the next phase.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are bounded and can proceed.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The LOG-C04 canonical projection and desk are the preserved
source/runtime boundaries. LOG-C05 may proceed with a new pure report/debit
module, a metadata-only snapshot repository, and bounded in-view actions. Docker
and positive live data are explicit validation limitations, not reasons to fake
data or broaden scope.
