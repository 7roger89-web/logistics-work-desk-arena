# LOG-C06 Historical A Bo Staging and Opening Position Actual Status

Title: LOG-C06 Historical A Bo Staging and Opening Position
Date: 2026-08-15
Status: PASS for bounded local LOG-C06. Cutover remains NOT_READY; owner review is required; closure evidence is complete.
Companion plan: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-plan.md`
Companion evidence: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-evidence.md`
Companion benchmark: `docs/plans/2026-08-15-log-c06-historical-staging-opening-position/2026-08-15-log-c06-historical-staging-opening-position-benchmark.md`

## Purpose

This file records the real current state and closure evidence for LOG-C06. It is a living
status matrix refreshed after each implementation slice and final acceptance check.

## Freshness / Refresh Rules

P0 records the baseline before implementation. After implementation begins, refresh only
affected rows, append a Status Refresh Log row, and update the next phase's stale status
assumptions/work steps before proceeding.

## Scope

Target scope:

- Historical `.xls` evidence staging and deterministic normalization.
- SALE Thanh review desk and staging-only review writes.
- Confirmed-only multi-currency draft opening position and cutover readiness.
- Regression and browser evidence while preserving LOG-C02 through LOG-C05.

Out of scope:

- Source workbook mutation, canonical ledger migration/publication, Quick Entry, AI,
  approval/live cutover, Dashboard redesign, Docker setup, and unrelated dirty changes.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `core/historical_staging.py` | new file; no pre-existing graph node | 0 before implementation | missing pure staging/parser/persistence/cutover seam | editable new module |
| `views/historical_review.py` | new file; no pre-existing graph node | 0 before implementation | missing bounded review surface | editable new module |
| `tests/test_historical_staging.py` | new file; no pre-existing graph node | 0 before implementation | missing direct parser/golden matrix | editable new test |
| `tests/test_historical_staging_write_oracle.py` | new file; no pre-existing graph node | 0 before implementation | missing staging-only write oracle | editable new test |
| `playwright/log_c06_historical_review_flow.mjs` | new file; no pre-existing graph node | 0 before implementation | missing reusable browser path | editable new flow |
| `views/partner_reconciliation.py` | `E0-P0A-IMPACT1` | 80 symbols; 35 local relationships; 4 inbound refs; 13 linked flows | Existing C04/C05 A Bo desk, mode navigation, canonical projection, search, report, and debit controls | high/critical scope warning; edit only the smallest Historical Review entry seam |
| `views/web_app.py` | `E0-P0A-IMPACT1` | 22 symbols; 16 local relationships; 1 linked flow | Main router, sidebar, and Dashboard-first route order | high scope warning; preserve-only; no new global route needed |
| `core/database.py` | `E0-P0A-IMPACT1` | approximately 137 symbols; 128 local relationships; 75 linked flows | Shared Mongo connection/index and all legacy/canonical writes | high scope warning; preserve-only; new staging module may use isolated collection boundary without editing this file |
| `core/financial_ledger.py` | `E0-P0A-IMPACT1` | approximately 137 symbols; 75 linked flows | Canonical obligation/transaction/allocation/correction and partner projection | high scope warning; preserve-only; no imports from staging parser |
| `core/reconciliation.py` | `E0-P0A-IMPACT1` | 73 symbols; 31 local relationships; 11 linked flows | C04 explanation/review/search/trace/period helpers | high scope warning; preserve-only; LOG-C06 opening model stays separate |
| `D:\Copy of TOYS-2025 - Copy.xls` | `E0-P0A-SRC1`, `E0-P0A-WB1` | external source | 8 sheets; Sheet2 282x14; golden rows and anomaly identified | preserve-only; read/hash only |
| C02-C05 runtime/tests/reports | `E0-P0A-FLOW1`, `E0-P0A-SAFETY1` | existing bounded surfaces | canonical ledger, dashboard, C04 desk, C05 report/debit already have local PASS evidence | preserve-only; regression gate |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Conflicts with requirement. | Replace exact offending behavior. |
| `missing` | Required behavior does not exist. | Implement missing piece. |
| `unbound` | Exists but is not wired to the required source/flow. | Bind only to the real source. |
| `fake-or-stub` | Demo/mock/fallback is used as real behavior. | Remove or make truthful. |
| `blocked` | Required authority/evidence/dependency is unavailable. | Stop and record blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Source workbook | Exact source exists at `D:\Copy of TOYS-2025 - Copy.xls`; read-only hash captured. | Readable without mutation and same hash after all validation. | correct | external | `E0-P0A-SRC1` | preserve-only; verify after each source read |
| Workbook coverage | 8 sheets; Sheet2 has 282 rows/14 columns; every non-empty source row is represented in a 289-item staging batch; golden rows and row-35/36 date anomaly are flagged. | Every non-empty row representable with provenance. | correct for staging | 289 items | `E0-P0A-WB1`, `E1-P1A-MODEL1`, `E1-P1B-GOLD1` | preserve parser; continue P2 without changing raw evidence |
| Raw/proposal staging model | `core/historical_staging.py` preserves raw cells/provenance separately from proposal, status, reason, anomaly, and review-history fields. | Separate raw evidence, proposal, status, anomaly, and review history. | correct for P1 | new pure module | `E1-P1A-MODEL1`, `E1-P1A-ORACLE1` | keep persistence/UI separate |
| Deterministic SALE normalization | 47 amount-bearing explicit SALE=Thành rows are distinct from 60 amount-bearing other-sale rows; free-text “món của Thành” stays review-only. | Explicit SALE may propose; arbitrary text never proves SALE Thanh. | correct for P1 | staging-only | `E1-P1A-RULES1`, `E1-P1B-GOLD1` | apply review actions in P2-A |
| Currency/FX normalization | Staging preserves CNY/UNKNOWN/USD buckets and records the 100,000,000 VND / 3,953 -> 25,297.2426 CNY context; no current-rate conversion is used. | Preserve CNY/USD/VND and related FX context; unknown remains review. | correct for P1; opening still missing | 102 CNY / 2 USD / 146 UNKNOWN | `E1-P1A-RULES1`, `E1-P1B-ANOMALY1` | implement confirmed-only opening model in P2-B |
| Historical persistence | `core/historical_staging_store.py` writes only `legacy_historical_staging` and `legacy_historical_review_actions`; review retries and version conflicts are explicit. | Staging/audit-only persistence; raw values immutable; retries idempotent. | correct for P2-A | 2 isolated collections | `E2-P2A-STORE1`, `E2-P2A-REVIEW1`, `E2-P2A-ORACLE1` | wire only the bounded review UI; preserve canonical writers |
| Opening position/cutover draft | `core/historical_opening.py` derives confirmed-only buckets, explicit exclusions, checkpoint outcomes, and reproducible cutover drafts without DB/ledger access. | Per-currency confirmed-only buckets, checkpoint explanation, draft hash/version/status. | correct for pure P2-B | pure model | `E2-P2B-POSITION1`, `E2-P2B-CURRENCY1`, `E2-P2B-CHECKPOINT1`, `E2-P2B-CUTOVER1` | expose through P3 UI; owner decision/live cutover remain blocked |
| Historical Review UI | Historical Review is mounted from the existing A Bò desk through one mode seam; it shows staging summary, search, raw source evidence, review actions, per-currency draft opening, and NOT_READY readiness. | Bounded review/search/source evidence/actions/draft view reachable from existing desk. | correct for P3-B local runtime | partner view high-risk seam + new view | `E3-P3A-UI1`, `E3-P3A-REVIEW1`, `E3-P3A-ORACLE1`, `E3-P3A-WRITE1`, `E3-P3B-BROWSER1`, `E3-P3B-DRAFT1` | preserve C04/C05 modes; owner approval/live remains blocked |
| Canonical financial write boundary | Existing C02-C05 write oracles and live ledger are present. | Remain unchanged; zero canonical effects during LOG-C06. | correct / preserve-only | high-risk shared surfaces | `E0-P0A-SAFETY1` | regression and write oracle only |
| LOG-C02 regression | Existing canonical ledger foundation has PASS evidence. | Remain passing. | correct | existing tests/reports | `E0-P0A-SAFETY1` | preserve; run P3-B regression |
| LOG-C03 regression | Existing shipment-first Dashboard has PASS evidence. | Remain reachable and unchanged. | correct | existing route/runtime | `E0-P0A-FLOW1` | preserve; run browser/regression |
| LOG-C04 regression | Existing A Bò reconciliation desk has PASS evidence. | Remain reachable; Historical Review is additive. | correct | partner view high risk | `E0-P0A-FLOW1`, `E0-P0A-SAFETY1` | preserve; route/write oracle |
| LOG-C05 regression | Existing manager report/Debit Draft has PASS for bounded local scope. | Remain reachable and no historical migration enters it. | correct | partner view high risk | `E0-P0A-FLOW1`, `E0-P0A-SAFETY1` | preserve; regression |
| Browser runtime | Local Streamlit `/_stcore/health` is `200/ok`; visible Chrome flow is 13/13 PASS with 0 console/page/network errors; no Docker target exists. | Use real current runtime and report Docker limitation honestly. | correct for bounded local scope; blocked for Docker | app runtime | `E0-P0A-RUNTIME1`, `E3-P3B-BROWSER1`, `E3-P3B-CONSOLE1`, `E3-P3B-BUILD1` | no container/production claim |
| Formal P2P helper | Inspection/classification passed; workflow run hit a locked `.tmp` cache permission error. | Separate helper verdict from product verdict. | blocked | helper state | `E0-P0A-P2P1` | record limitation; do not mutate cache/P2P |
| Worktree | Known dirty worktree includes prior LOG-C02-C05 and unrelated files. | Preserve all pre-existing changes and scope LOG-C06 artifacts. | correct / preserve-only | N/A | `E0-P0A-GIT1` | no reset/checkout/broad stage |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-15 | baseline before P0 | workbook, staging, UI, persistence, canonical boundaries | initial classification | `E0-P0A-REQ1`, `E0-P0A-GIT1`, `E0-P0A-P2P1`, `E0-P0A-GRAPH1`, `E0-P0A-SRC1`, `E0-P0A-WB1`, `E0-P0A-IMPACT1`, `E0-P0A-FLOW1`, `E0-P0A-SAFETY1`, `E0-P0A-RUNTIME1`, `E0-P0A-AUTH1` | P1 creates pure staging first; P2 creates isolated metadata/draft; P3 adds only bounded desk navigation/UI |
| R1 | 2026-08-15 | after P1-A/P1-B implementation and focused tests | pure parser, source coverage, SALE/currency/event rules, anomalies, golden rows | staging model and P1 evidence moved to correct; persistence/opening/UI remain missing | `E1-P1A-GRAPH1`, `E1-P1A-MODEL1`, `E1-P1A-RULES1`, `E1-P1A-ORACLE1`, `E1-P1B-GOLD1`, `E1-P1B-TRACE1`, `E1-P1B-ANOMALY1`, `E1-P1B-HASH1` | P2-A adds only staging metadata/review history; canonical boundary remains preserve-only |
| R2 | 2026-08-15 | after P2-A/P2-B pure tests | staging/audit persistence, review transitions, confirmed-only opening buckets, checkpoint reconciliation, cutover draft | persistence and pure opening model moved to correct; UI/browser/owner approval remain missing or out of scope | `E2-P2A-STORE1`, `E2-P2A-REVIEW1`, `E2-P2A-WRITE1`, `E2-P2A-ORACLE1`, `E2-P2B-POSITION1`, `E2-P2B-CURRENCY1`, `E2-P2B-CHECKPOINT1`, `E2-P2B-CUTOVER1` | P3 adds only bounded Historical Review view and local browser evidence |
| R3 | 2026-08-15 | after P3-A recorder tests | Historical Review route, session-only staging fallback, search/source evidence, staging review action | review UI moved to correct for local renderer; browser/console/full regression evidence remains pending | `E3-P3A-UI1`, `E3-P3A-REVIEW1`, `E3-P3A-ORACLE1`, `E3-P3A-WRITE1` | P3-B must validate the real Streamlit runtime and preserve C04/C05 |
| R4 | 2026-08-15 | after P3-B visible runtime and regressions | browser route, six golden searches, NOT_READY draft, validation boundary, Dashboard return, C02-C05/full tests | P3-B moved to correct for bounded local product scope; Docker/owner approval/live publication remain blocked or out of scope | `E3-P3B-DRAFT1`, `E3-P3B-TRACE1`, `E3-P3B-BROWSER1`, `E3-P3B-CONSOLE1`, `E3-P3B-REGRESSION1`, `E3-P3B-BUILD1`, `E3-P3B-WRITE1` | supervisor, final graph/detect-changes, source hash and worktree closure |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/historical_staging.py` | `tests/test_historical_staging.py` | source-of-truth model / behavior test | P1-A/P1-B/P2-A/P2-B | edit | `E0-P0A-REQ1`, `E0-P0A-WB1` | no financial imports; raw/proposal separation |
| `views/historical_review.py` | `views/partner_reconciliation.py` | new render surface / navigation consumer | P3-A/P3-B | edit | `E0-P0A-IMPACT1`, `E0-P0A-FLOW1` | bounded state route; no Dashboard rewrite |
| `views/partner_reconciliation.py` | `views/web_app.py` | existing route consumer | P3-A | edit smallest seam | `E0-P0A-IMPACT1` | high/critical blast radius; preserve C04/C05 modes |
| `views/web_app.py` | `views/partner_reconciliation.py` | router / existing desk | P3-A | preserve-only | `E0-P0A-IMPACT1`, `E0-P0A-FLOW1` | do not add global route unless required |
| `core/database.py` | `core/historical_staging.py` | existing DB provider / isolated staging consumer | P2-A | preserve-only / inspect-only | `E0-P0A-IMPACT1` | no shared writer rewrite; use isolated collection boundary |
| `core/financial_ledger.py` | `core/historical_staging.py` | canonical financial provider / forbidden importer dependency | all | do-not-touch | `E0-P0A-IMPACT1`, `E0-P0A-SAFETY1` | no live obligation/transaction/allocation mutation |
| `core/reconciliation.py` | `core/historical_staging.py` | C04 read model / separate historical model | P2-B/P3-B | preserve-only | `E0-P0A-IMPACT1` | no reuse that merges legacy with canonical truth |
| source workbook | `core/historical_staging.py` | immutable evidence / reader | P1 | validate-only | `E0-P0A-SRC1`, `E0-P0A-WB1` | hash before/after unchanged |
| `playwright/log_c06_historical_review_flow.mjs` | local Streamlit runtime | reusable browser flow / QA | P3-B | edit | `E0-P0A-RUNTIME1` | official artifacts under `reports/QA/playwright` |

## Detailed Findings

### Source workbook

Current state:

The exact workbook exists outside the repo. Read-only `xlrd` inspection identified 8
sheets and a 282-row Sheet2 with the previously reported golden values and anomaly.

Required state:

```text
Read all non-empty source rows without modifying the workbook; preserve file hash,
sheet, row, cells, raw values, raw notes, raw dates, inherited date context, and parser version.
```

Evidence:

- `E0-P0A-SRC1`: size and SHA-256 before implementation.
- `E0-P0A-WB1`: sheet dimensions, golden row locations, and date anomaly.

Relationship and impact:

- Related file count: external source; no app relationship graph.
- Relationship summary: source-of-truth evidence only; never a canonical ledger input by itself.
- Impact note: preserve-only and read-only.

Classification:

correct for availability, partial for required staging coverage.

Allowed next action:

Implement a read-only parser and compare the hash after every validation slice.

Forbidden next action:

Never save, rewrite, normalize in place, or bulk-insert rows into canonical financial collections.

### Canonical financial boundary

Current state:

LOG-C02 through LOG-C05 have canonical projection, report/debit, and write-oracle evidence.

Required state:

```text
Historical staging/review may read or write only a dedicated staging/audit metadata boundary;
canonical financial obligations, transactions, allocations, corrections, and live partner
position remain unchanged.
```

Evidence:

- `E0-P0A-SAFETY1`: existing write-oracle/regression evidence.
- `E0-P0A-IMPACT1`: high-risk shared-file counts and preserve-only touch map.

Relationship and impact:

- Related file count: `core/financial_ledger.py` approximately 137 symbols/75 linked flows; `core/database.py` approximately 137 symbols/75 linked flows.
- Relationship summary: all existing canonical writes and partner projection paths.
- Impact note: high blast-radius warning; no edit allowed.

Classification:

correct / preserve-only.

Allowed next action:

Add a write oracle that fails if any canonical collection or writer is touched.

Forbidden next action:

Do not import the workbook into canonical collections or alter live owner/partner position.

### Historical staging and review surface

Current state:

LOG-C06 parser, staging persistence, confirmed-only cutover draft, and Historical Review
view are implemented and locally validated. The existing partner desk remains a
high-risk but preserve-only C04/C05 surface with a minimal Historical Review seam.

Required state:

```text
New pure staging/cutover model plus a bounded review view, wired through the smallest
existing desk navigation seam, with explicit statuses and business labels.
```

Evidence:

- `E0-P0A-REQ1`: attached objective and boundaries.
- `E0-P0A-IMPACT1`: existing partner view/route relationship counts.
- `E0-P0A-FLOW1`: current C04/C05 route and report/debit behavior.

Relationship and impact:

- Related file count: partner view 80 symbols/13 flows; router 22 symbols/1 flow.
- Relationship summary: existing C04/C05 entrypoint and state navigation.
- Impact note: high/critical scope warning; edit only navigation and keep existing modes intact.

Classification:

correct for the bounded local scope, with existing desk correct/preserve-only.

Allowed next action:

Implement the new view and pure staging contract; add direct UI/write-oracle tests.

Forbidden next action:

Do not redesign Dashboard, add Quick Entry, or replace the canonical desk.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Pure parser/proposal contract implemented and compile/smoke checks pass; no UI/DB/canonical imports. | complete P1-A; preserve module boundary and proceed to P1-B/P2-A |
| P1-B | 11 focused tests pass; six golden rows, checkpoint separation, anomaly rules, SALE/currency rules, and source hash regression are covered. | complete P1-B; proceed to staging-only persistence without changing source/parser raw evidence |
| P2-A | Fake-DB write oracle passes import/retry, confirm/correct/not-Thành/unknown, history, actor/time/reason, and conflict tests; canonical accesses remain zero. | complete P2-A; wire only through a later bounded UI |
| P2-B | Pure opening/cutover tests pass confirmed-only inclusion, currency separation, checkpoint exact/difference/unknown, draft hash reproducibility, and no APPROVED/LIVE states. | complete pure P2-B; expose truthful NOT_READY/READY panel in P3 |
| P3-A | Recorder tests prove desk routing before canonical projection, source evidence/search, session-only staging, and confirm metadata action. | complete P3-A; keep C04/C05 preserve-only and run browser evidence in P3-B |
| P3-B | Visible Chrome flow is 13/13 PASS; six searches trace source evidence; NOT_READY and no-reason validation are visible; C02-C05/full tests and compileall pass; Docker target remains absent. | complete P3-B for bounded local scope; keep owner approval/live/Docker explicitly blocked or out of scope |
| Pn-A/Pn-B/Pn-C | Supervisor PASS; plan-created artifacts reviewed; final source fingerprint and Anvien detect-changes recorded; scoped closure commit prepared. | complete bounded local plan; keep owner review, Docker/production, canonical mutation, approval, and live cutover explicitly out of scope |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each existing target file has relationship-count evidence where applicable.
- [x] Phase Touch Map lists plan-relevant relationship files and touch modes.
- [x] Correct C02-C05 parts are marked preserve-only.
- [x] Missing/partial/blocked parts have exact next actions.
- [x] Formal P2P helper limitation is recorded without mutating cache/P2P source.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Next-phase assumptions and work steps reflect the P0 findings.
- [x] Supervisor acceptance report records the bounded local verdict and residual gates.
- [x] Final source fingerprint matches the preserved workbook baseline.
- [x] Final Anvien refresh/detect-changes and scoped worktree boundary are recorded.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete for a bounded local implementation. The workbook is available and the
current source fingerprint is captured. The formal P2P `run` helper is blocked only by a
locked prior QA cache file, and Docker acceptance is blocked because no Docker target
exists. Neither blocker authorizes changing P2P/cache/source or substituting a false
production claim. Proceed with pure staging first, preserve the canonical boundary, and
refresh this file after every slice.
