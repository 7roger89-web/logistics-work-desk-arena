# LOG-C04 SALE Thành — Đối soát công nợ A Bò Actual Status

Title: LOG-C04 SALE Thành — Đối soát công nợ A Bò
Date: 2026-08-14
Status: Local product PASS; Docker/positive-live-data acceptance BLOCKED
Companion plan: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-plan.md`
Companion evidence: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-benchmark.md`

## Purpose

This file records the real current state before implementation and remains a
living status matrix throughout LOG-C04.

## Freshness / Refresh Rules

Refresh affected rows after each implementation slice and before the next phase.
Keep prior decisions in the Status Refresh Log; update only stale current-state
facts and next-phase actions.

## Scope

Target scope:

- Canonical partner projection and deterministic reconciliation read model.
- Read-only Streamlit A Bò / SALE Thành desk and minimal route.
- Synthetic fixture coverage, write oracle, regression, and browser evidence.

Out of scope:

- Real workbook import/migration, AI, Quick Entry, payment execution, debit/report export, accounting period close, FX platform, automatic owner migration, frontend rewrite, LOG-C05, and unrelated dirty-worktree edits.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|----------------------|----------------------|-------------|
| `core/financial_ledger.py` projection | `E0-P0A-IMPACT1` | 109 canonical symbols; 75 local / 34 outbound relationships in current file projection | Canonical projection and all existing ledger write flows share this module; 16 linked flows | high scope warning; edit projection only and preserve write functions |
| `views/partner_finance.py` | `E0-P0A-IMPACT1` | 0 resolved file relationships; 14 symbols / 80 analyzer gaps | Current read-only partner renderer dynamically calls the canonical projection | medium scope warning; preserve as compatibility surface while desk is added |
| `views/finance.py` | `E0-P0A-IMPACT1` | 0 resolved file relationships; current renderer calls partner projection and legacy write path | Receivables route mixes read projection and existing lump-sum write form | high UI boundary; do not add desk writes or remove legacy path |
| `views/web_app.py` | `E0-P0A-IMPACT1` | route table is dynamically imported; exact relationships unresolved in graph | Sidebar route registration is the minimal navigation seam | medium scope warning; preserve Dashboard as default |
| `tests/test_financial_ledger.py` | `E0-P0A-IMPACT1` | direct fixture coverage exists in the ledger test module | Existing LOG-C02 tests cover idempotency, allocations, received-on-behalf, restriction, and currency guards | preserve and extend only for new projection contract |
| `.p2p/design/MASTER_DESIGN_SYSTEM.*` | `E0-P0A-DESIGN1` | project-owned design artifacts | Draft navy utility system with no frontend rewrite/read-only constraint | preserve-only; no material visual-token change |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Conflicts with requirement. | Replace the offending behavior. |
| `missing` | Required behavior does not exist. | Implement the missing piece. |
| `unbound` | Surface exists but is not wired to the required source/flow. | Bind only to the real source. |
| `fake-or-stub` | Demo/mock/fallback is presented as real behavior. | Remove or make the state truthful. |
| `blocked` | Required authority/evidence/dependency is unavailable. | Stop and record the blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Canonical partner projection | P1-A added paid-on-behalf history, received-on-behalf total/remaining/allocation status, allocation/provenance/location fields, and owner coverage without changing persistence functions. | Complete business buckets and trace fields while preserving canonical formulas and writes. | correct | 141 symbols; 78 local / 34 outbound; 17 linked flows | `E0-P0A-IMPACT1`, `E1-P1A-DOM1`, `E1-P1A-DOM2`, `E1-P1A-TEST1` | preserve; P1-B consumes contract |
| Deterministic reconciliation model | `core/reconciliation.py` now provides pure explanations, review inbox, bounded amount/ID search, money-location trace, period draft, and partner-reported comparison. It imports no database or Streamlit surface. | Pure, rule-based, source-ID-backed read model. | correct | 73 symbols; 31 local relationships; 11 linked flows; MEDIUM file impact contained to the new module | `E1-P1B-EXPL1`, `E1-P1B-TRACE1`, `E1-P1B-TEST1`, `E1-P1B-TEST2` | preserve; P2 consumes stable contract |
| Existing partner renderer | Displays basic totals, buckets, explanations, and recent allocations, but mixes raw/technical language and lacks review inbox, period, search, partner comparison, and trace selection. | Preserve compatibility and add a dedicated non-accountant desk. | partial | 0 resolved relationships; 14 symbols | `E0-P0A-IMPACT1` | preserve; new P2-A view |
| Dedicated A Bò / SALE Thành desk | `views/partner_reconciliation.py` renders currency-safe position/review/search/period/report sections from the canonical projection; visible runtime shows truthful empty/incomplete owner state when live data has no matching normalized rows. | Separate read-only desk discoverable from current navigation. | correct for local runtime; Docker acceptance blocked | 46 symbols; 17 local relationships; 8 linked flows | `E2-P2A-UI1`, `E2-P2A-TRACE1`, `E3-P3A-RUNTIME1` | preserve; supervisor reviews Docker limitation |
| SALE Thành filter truthfulness | Exact `internal_sale_owner` filter exists in canonical projection; live normalized owner coverage is known to be sparse. | Exact canonical filter plus truthful empty/incomplete state; no text guessing/migration. | partial | projection file scope above | `E0-P0A-REQ1`, `E0-P0A-DESIGN1` | add owner coverage metadata in P1-A |
| Synthetic LOG-C04 fixtures | Existing LOG-C02 tests remain green; the pure fixture module covers the six golden scenario amounts plus allocation, review, search, trace, period, reported-difference, currency, and owner boundaries. | Isolated fixture-only matrix for all required cases. | correct | `tests/test_reconciliation_desk.py`: 38 symbols; 11 direct tests passed | `E1-P1B-TEST1`, `E1-P1B-TRACE1` | preserve; P2 consumes fixture contract without live-data injection |
| Read-only financial write oracle | Dedicated render recorder exercises route, search, trace, period, and report surfaces with `financial_write_count=0`; no live fixture was inserted. | Render/filter/drill-down/period/search causes zero financial writes and no collection mutation. | correct for bounded local/fixture scope | dedicated oracle: 23 symbols; 2 tests passed | `E2-P2A-WRITE1`, `E2-P2A-WRITE2`, `E3-P3A-WRITE1` | preserve; no write controls |
| Browser QA | Reusable LOG-C04 flow reached the route in visible local Streamlit; screenshots/DOM and empty-result state were captured; positive live row/trace was absent because the current canonical projection is empty for this owner. | Reusable route flow and official QA JSON/MD with console/error capture. | correct for local empty/incomplete scope; positive live data and Docker blocked | official JSON/MD; console errors/warnings 0 | `E2-P2B-BROWSER1`, `E2-P2B-CONSOLE1`, `E3-P3A-BROWSER1` | preserve; supervisor reviews explicit blockers |
| Design system | Existing draft system directs current navy utility workspace, semantic badges, compact tables, exception-first flow, no rewrite, no new database, read-only financial flag. | Reuse without material visual-token change. | correct | project-owned design files | `E0-P0A-DESIGN1` | preserve-only |
| Live workbook staging | No LOG-C04 import is authorized. | Keep real workbook out of live ledger; future staging provenance remains a later Goal. | correct / preserve-only | no target file | `E0-P0A-REQ1` | do not touch |
| Worktree safety | Worktree has many existing modified/untracked LOG-C01/C02/C03 and infrastructure artifacts. | Preserve unrelated changes; scoped edits only. | correct / preserve-only | N/A | `E0-P0A-GIT1` | no reset/checkout/broad stage |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | baseline before P0 implementation | full LOG-C04 boundary | initial classifications recorded; P0 complete | `E0-P0A-REQ1..E0-P0A-STATUS1` | P1-A must extend projection only; P2 must add a new desk rather than rewrite current finance/dashboard |
| R1 | 2026-08-14 | after P1-A projection checkpoint | canonical projection and direct fixture coverage | `partial -> correct` for P1-A projection; `partial -> correct` for direct LOG-C02 projection coverage | `E1-P1A-DOM1..E1-P1A-TEST2` | P1-B may consume the stable row contract; UI remains missing |
| R2 | 2026-08-14 | after P1-B pure read-model checkpoint | deterministic calculator module and isolated fixture matrix | reconciliation model `missing -> correct`; LOG-C04 fixture coverage `partial -> correct`; no DB/write surface introduced | `E1-P1B-EXPL1..E1-P1B-TEST2` | P2-A may render the stable contract; route/browser remain missing |
| R3 | 2026-08-14 | after P2-A view checkpoint | dedicated Streamlit consumer | desk view `missing -> correct` for local empty/incomplete state; no financial write symbols reachable | `E2-P2A-UI1`, `E2-P2A-WRITE1`, `E2-P2A-WRITE2` | route wiring/browser evidence next |
| R4 | 2026-08-14 | after P2-B route/browser checkpoint | route, visible flow, Dashboard regression | route/browser `missing -> correct` for local visible scope; Docker/positive live states explicitly blocked | `E2-P2B-ROUTE1`, `E2-P2B-BROWSER1`, `E2-P2B-CONSOLE1` | run final regression/closure |
| R5 | 2026-08-14 | after P3-A validation checkpoint | tests, build, runtime, QA artifacts | 64 tests and compile pass; local runtime/browser pass; Docker full-build remains blocked | `E3-P3A-TEST1..E3-P3A-BROWSER1` | produce coder/supervisor reports; no optional hardening |
| R6 | 2026-08-14 | after P3-B coder/supervisor closure | reports, QA artifacts, final decision | coder report recorded; supervisor returned PASS for bounded local product scope; P2P helper and Docker/positive-live blockers remain separate | `E3-P3B-REPORT1`, `E3-P3B-SUP1` | stop at LOG-C04 boundary; LOG-C05 may be discussed, not started |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/financial_ledger.py` | `tests/test_financial_ledger.py` | source-of-truth projection / regression consumer | P1-A | edit | `E0-P0A-IMPACT1` | no write-path changes |
| `core/financial_ledger.py` | `core/database.py` | persistence dependency | P1-A | preserve-only | `E0-P0A-IMPACT1` | no collection/schema mutation |
| `core/reconciliation.py` | `core/financial_ledger.py` | new pure consumer | P1-B | edit | `E0-P0A-REQ1` | no DB import/write |
| `views/partner_reconciliation.py` | `core/reconciliation.py` | UI consumer | P2-A | edit | `E0-P0A-REQ1` | read-only widgets only |
| `views/web_app.py` | `views/partner_reconciliation.py` | route registry / view consumer | P2-B | edit | `E0-P0A-IMPACT1` | preserve Dashboard default |
| `playwright/log_c04_partner_reconciliation_flow.mjs` | real Streamlit runtime | browser evidence | P2-B | edit | `E0-P0A-REQ1` | reusable, no temp script |
| `tests/test_reconciliation_desk.py` | synthetic fixture inputs | behavior test | P1-B/P3-A | edit | `E0-P0A-REQ1` | no live financial data |
| `.p2p/design/MASTER_DESIGN_SYSTEM.*` | `views/partner_reconciliation.py` | approved/preserve-only design source | P2-A | preserve-only | `E0-P0A-DESIGN1` | no material visual-token change |

## Detailed Findings

### Canonical projection

Current state:

The existing projection is the correct source-of-truth seam and is already
read-only, currency-separated, and exclusion-aware. Its row contract is not yet
rich enough for a non-accountant reconciliation desk.

Required state:

```text
canonical records -> exact SALE owner filter -> explicit business buckets
-> confirmed/review split -> source/allocation/provenance -> deterministic desk
```

Evidence:

- `E0-P0A-GRAPH1`: graph refreshed before Anvien queries.
- `E0-P0A-IMPACT1`: projection has HIGH blast-radius warning and 16 linked flows.

Relationship and impact:

- Related file count: 109 symbols with 75 local and 34 outbound relationships in the current file projection.
- Relationship summary: projection shares a module with canonical write functions and must remain read-only.
- Impact note: HIGH is a scope warning; P1-A is allowed but must not change write functions.

Classification:

`partial`

Allowed next action:

Extend returned projection metadata and direct tests only.

Forbidden next action:

Do not create a second ledger, migrate owner data, or change persistence guards.

### Desk UI

Current state:

The current partner renderer is a partial compatibility component. The current
finance screen includes a legacy payment write form, so it is not a safe
dedicated home for the read-only desk.

Required state:

```text
dedicated route -> simple currency position -> review inbox -> explanation
-> bucket/source/trace -> period/report comparison; financial writes = 0
```

Evidence:

- `E0-P0A-REQ1`: attached brief requires a separate non-accountant workflow.
- `E0-P0A-DESIGN1`: existing design contract requires current components/styles and no frontend rewrite.

Relationship and impact:

- Related file count: current finance renderer has no resolved graph relationships because Streamlit imports are dynamic; source inspection remains authoritative.
- Relationship summary: route registry dynamically imports views and current finance contains both read and write controls.
- Impact note: add a separate view and minimal route registration.

Classification:

`missing` for the dedicated surface; `partial` for the compatibility renderer.

Allowed next action:

Implement a new read-only view and route without removing the existing finance path.

Forbidden next action:

Do not put Quick Entry or a manual balance editor into the new desk.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Existing projection is partial but canonical and safe to extend. | keep P1-A narrow; preserve writes and add direct tests first |
| P1-B | Pure deterministic helpers and the six-case fixture matrix now pass. | preserve the pure contract; P2-A may bind the view without adding persistence |
| P2-A | Dedicated view now consumes only the canonical projection/pure helpers and renders truthful empty/incomplete state. | preserve view; no financial writes or visual-token rewrite |
| P2-B | One route and reusable flow are mounted; Dashboard remains default and visible browser regression passes. | preserve route; retain explicit positive-live/Docker blockers |
| P3-A | Compile, 64-test suite, selected 40-test regression, health, visible browser, screenshots, and console evidence are recorded. | P3-B may produce closure reports; do not claim Docker acceptance |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable or a documented dynamic-import limitation.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are bounded and can proceed.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. P1-A/P1-B established the canonical projection and pure
read-model contract. P2-A/P2-B now mount the bounded desk and route; P3-A
passes local validation with explicit Docker and positive-live-data blockers.
Proceed only to P3-B supervisor closure; do not broaden into workbook staging,
LOG-C05, or unrelated worktree changes.
