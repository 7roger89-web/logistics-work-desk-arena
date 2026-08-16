# LOG-C03 Shipment Dashboard 2.0 Actual Status

Title: LOG-C03 Shipment Dashboard 2.0
Date: 2026-08-14
Status: P0 Complete / implementation in progress
Companion plan: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-plan.md`
Companion evidence: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-benchmark.md`

## Purpose

This living file records the real current state for LOG-C03. The P0 baseline below was completed before product-code implementation. Later refresh rows must be added after each implementation slice.

## Freshness / Refresh Rules

- P0 records the baseline before LOG-C03 product implementation.
- R1+ records status transitions only when current source/runtime/evidence proves them.
- Preserve unrelated user changes and do not infer correctness from the presence of a file or a green stale test.

## Scope

Target scope:

- Existing Streamlit main dashboard as shipment-first support work desk.
- Pure read-only dashboard projection/rules.
- Deterministic warnings, filters, attention ranking, fixture tests, and navigation/browser proof.

Out of scope:

- P2P source/governance repair, release/deploy, LOG-C04, ledger writes, allocation/reconciliation writes, AI, new DB/frontend stack, full factory-lot domain, and unrelated dirty worktree files.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `views/dashboard.py` / `ui_dashboard` | `E0-P0A-GRAPH2` | 1 direct affected file in impact projection; 117 symbols; 7 local relationships | Current route owns customer-group list, filters, task summary, legacy badges, and active-shipment/detail branch | high source complexity warning; edit only bounded dashboard body |
| `core/shipment_dashboard.py` | new file; no baseline graph node | 0 baseline related files | Missing pure dashboard read model/rule seam | edit P1-A only |
| `tests/test_shipment_dashboard.py` | no baseline file | 0 baseline related files | Missing direct behavior test surface | edit P1-B only |
| `views/shipment.py` / `ui_shipment_detail_tabs` | `E0-P0A-GRAPH3` | 0 direct impact files; 99 symbols | Existing detail renderer includes Shipment 360 and existing writes | preserve/inspect-only; do not redesign |
| `core/shipment_360.py` / `build_shipment_360_summary` | `E0-P0A-GRAPH3` | 1 direct impact file; 71 symbols; 38 local relationships | Existing source-labelled, non-mutating financial projection | preserve-only read source |
| `core/financial_ledger.py` | `E0-P0A-GRAPH3` | 1 direct impact file; 133 symbols; 34 local relationships | Canonical ledger write/projection family | do-not-touch in LOG-C03 |
| `core/database.py` | source inspection and prior C02 evidence | high fan-in; existing load/write family | Current DB loading and writes shared by many surfaces | inspect-only; no schema or new writes |
| `views/web_app.py` | source inspection | route caller; preserve | Main route mounts Dashboard | preserve-only |
| `playwright/*.mjs` | `E0-P0A-BROWSER1` | existing reusable flows | C01/C02 browser evidence exists; LOG-C03 flow missing | add one reusable flow only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current behavior conflicts with required outcome. | Replace only failed behavior. |
| `missing` | Required behavior does not exist. | Implement missing piece only. |
| `unbound` | Surface exists but is not wired to the real source/flow. | Bind only to real source. |
| `fake-or-stub` | Prototype/placeholder used as real behavior. | Remove or make truthful. |
| `blocked` | Required evidence/authority/capability is unavailable. | Stop or record bounded blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Main dashboard work queue | Customer-group-first list with task/history and analytics ahead of actionable shipments | Shipment-first actionable queue with top attention summary | wrong/partial | 1 affected file; 117 symbols | E0-P0A-SRC1, E0-P0A-GRAPH2 | edit P2-A |
| Operational status | Existing `wait/pending/done/cancel` values and labels | Reuse current vocabulary as independent operational field | correct/partial | config relationship preserved | E0-P0A-SRC5 | preserve; map in P1-A |
| Financial status | Legacy UI debt badge and finance calculator in dashboard; Shipment 360 has read-only projection | Compact read-only financial status sourced from existing projection | partial/wrong | Shipment 360 71 symbols; ledger 133 symbols | E0-P0A-SRC3, E0-P0A-GRAPH3 | edit P1-A/P2-A; do not touch ledger |
| Free-time rule | Existing UI computes warning at <=3 days and does not expose a model | Derived warning at <=2 and critical when expired, testable by date | partial/wrong | dashboard file | E0-P0A-SRC1, E0-P0A-SRC6 | edit P1-A |
| Customer deadline | Existing normalized field/rule absent | Deterministic at-risk/warning only when explicit date data exists | missing/unknown data capability | dashboard/detail fields inspected | E0-P0A-SRC6 | implement supported aliases in P1-A; document gaps |
| Promised/next-action dates | No bounded dashboard rule seam | Use explicit known fields only; no fake task | missing | no baseline owner | E0-P0A-SRC6 | implement bounded extraction in P1-A |
| Missing critical data | Customer validation exists only at save; dashboard does not show `CẦN BỔ SUNG` | Visible bounded warnings for supported missing fields | partial | validator separate from dashboard | E0-P0A-SRC6 | edit P1-A/P2-A |
| Next attention ranking | Existing tasks are separate user-entered work records; no shipment-specific deterministic ranking | Evidence-backed deterministic attention | missing | dashboard task path preserve-only | E0-P0A-SRC1 | implement P1-A; do not create task graph |
| Owner/SALE Thanh data | Ledger has `internal_sale_owner`; shipment UI has no normalized owner field | Filter when owner evidence exists; no fabricated owner | partial/unknown | ledger preserve-only | E0-P0A-SRC6 and ledger tests | model aliases/fixture in P1-A, filter P2-B |
| Customer/search/status/date filters | Search, time range, Active/Done exist | Keep useful filters and add compact owner/customer/finance/alert/deadline filters | partial | dashboard file | E0-P0A-SRC1 | edit P2-B |
| Shipment 360/detail | Existing read-only Shipment 360 plus operational/finance tabs | Reliable dashboard open/close/second shipment | correct for existing path; needs regression after UI change | shipment/detail preserved | E0-P0A-SRC3, E0-P0A-SRC4, E0-P0A-BROWSER1 | preserve/verify P2-C |
| Financial ledger writes | Existing LOG-C02 write paths outside dashboard | No new dashboard financial write path | correct/preserve-only | ledger medium impact; many symbols | E0-P0A-GRAPH3 | do-not-touch; safety test P1-B/P3-A |
| Factory lot/Golden Lục Giác | No normalized factory-lot domain in current app | Synthetic fixture/read-only summary only | missing/unknown | no baseline model | E0-P0A-SRC6 | fixture-only P1-B; no domain build |
| Tests | Existing finance/Shipment 360/write-safety tests, no dashboard rule tests | Direct behavior tests for LOG-C03 model and regressions | partial | tests separate from production | E0-P0A-TEST1 | add P1-B |
| Browser QA | Existing local C01/C02 reusable flows; no LOG-C03 flow | Summary/filter/first/second flow with screenshots and console evidence | partial | Playwright files existing | E0-P0A-BROWSER1 | add P3-A |
| Docker full-build | No Dockerfile/compose target discovered | Docker evidence or genuine blocker | blocked | no runtime target | E0-P0A-RUNTIME1 | attempt once in P3-A; do not substitute silently |
| P2P workflow | Active Goal Contract workflow run is BLOCKED on split/oracle compilation | Do not modify P2P; record governance blocker | blocked | state/report paths | E0-P0A-P2P1 | keep out of implementation; report final blocker |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | baseline before P0 implementation | LOG-C03 target surfaces | initial matrix above | E0-P0A-WT1..E0-P0A-P2P1 | P0 complete; proceed with P1-A pure model, then update assumptions |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `views/dashboard.py` | `views/shipment.py` | detail renderer consumer | P2-A/B/C | edit bounded region | E0-P0A-GRAPH2 | preserve active ID aliases and unrelated tabs |
| `core/shipment_dashboard.py` | `core/shipment_360.py` | read-model dependency | P1-A | edit new file; preserve dependency | E0-P0A-GRAPH3 | no write imports/calls |
| `core/shipment_dashboard.py` | `core/utils.py` | date parser dependency | P1-A | preserve/use | E0-P0A-SRC5 | follow current date parsing semantics |
| `core/shipment_dashboard.py` | `core/config.py` | status vocabulary dependency | P1-A | preserve/use | E0-P0A-SRC5 | no new status taxonomy |
| `core/financial_ledger.py` | `views/dashboard.py` | protected finance source family | all | do-not-touch | E0-P0A-GRAPH3 | read-only projection only |
| `core/database.py` | `views/dashboard.py` | loaded shipment source | P2-A/B | inspect-only/preserve | E0-P0A-SRC5 | no schema or write expansion |
| `views/web_app.py` | `views/dashboard.py` | route caller | P2-A/C | preserve-only | E0-P0A-SRC5 | Dashboard remains main route |
| `tests/test_shipment_dashboard.py` | `core/shipment_dashboard.py` | behavior test consumer | P1-B | edit new file | E0-P0A-TEST1 | fixture-only/no Mongo |
| `playwright/log_c03_shipment_dashboard_flow.mjs` | real Streamlit runtime | browser evidence | P3-A | edit new file | E0-P0A-BROWSER1 | reusable script; official QA report outputs |
| `.p2p/design/*` | current dashboard styles | UI contract/evidence | P0/P2 | create only if generated by p2p-uiux contract tooling | none baseline | no unapproved visual-system replacement |

## Detailed Findings

### Main dashboard and model boundary

Current state:

`views/dashboard.py` contains 117 symbols and 435 unresolved references in the current graph. It already owns filters, customer grouping, status/debt badges, task tools, GetFly import/export, and the active detail branch. It is a high-complexity legacy surface with a narrow safe edit region.

Required state:

```text
Shipment-first queue -> pure read model -> deterministic alerts -> existing detail/Shipment 360.
```

Evidence:

- `E0-P0A-SRC1`: current customer-group-first behavior and legacy filters.
- `E0-P0A-SRC2`: current first-click active-ID/rerun path.
- `E0-P0A-SRC3`: existing read-only financial projection.

Relationship and impact:

- Related file count: 1 directly affected file in dashboard impact projection; preserve sibling surfaces.
- Relationship summary: dashboard calls local status helpers/detail renderer and reads session state/data.
- Impact note: high source complexity warning; proceed surgically.

Classification:

`partial/wrong` for LOG-C03.

Allowed next action:

Add a pure model, then replace only the main queue/filters while preserving detail and legacy secondary tabs.

Forbidden next action:

Do not rewrite the app, ledger, database, or existing detail page.

### Financial source boundary

Current state:

`core/shipment_360.py` exposes a read-only, source-labelled projection with separate operational/financial status and attention/UNKNOWN states. The canonical ledger contains write functions and must remain untouched.

Required state:

Dashboard financial flag must consume the existing projection and never calculate a second ledger balance or invoke writes.

Evidence:

- `E0-P0A-SRC3`, `E0-P0A-SRC4`, `E0-P0A-GRAPH3`.

Classification:

Projection `correct/preserve-only`; dashboard consumption `partial`.

Allowed next action:

Import/read the projection from the new pure dashboard model and render a compact status label.

Forbidden next action:

Do not edit `core/financial_ledger.py`, add payment/allocation calls, or persist a duplicate financial status field.

### Runtime capability boundary

Current state:

Local Streamlit and prior browser flows exist; no Dockerfile/compose target is present. P2P workflow state is blocked by objective/oracle compilation.

Required state:

Final report must distinguish local visible runtime evidence from Docker-backed acceptance and record the P2P blocker without changing P2P.

Evidence:

- `E0-P0A-RUNTIME1`, `E0-P0A-P2P1`.

Classification:

`blocked` for Docker-backed full-build/browser; product implementation is not blocked by the missing target, but final PASS cannot claim that evidence.

Allowed next action:

Implement/verify locally, attempt the required capability once, and classify final result honestly.

Forbidden next action:

Do not invent Docker evidence or modify P2P governance files to clear the blocker.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | pure dashboard model missing; existing read-only Shipment 360 is usable | proceed with new pure model using existing date/status/projection seams |
| P1-B | direct dashboard behavior tests missing | add focused fixture tests after P1-A; no Mongo |
| P2-A | dashboard queue is wrong/partial but detail is preserve-worthy | edit only dashboard body; keep detail aliases and secondary tabs |
| P2-B | current filters are search/time/status only | compose compact owner/customer/finance/alert/deadline filters from model |
| P2-C | first-click path already proven locally | preserve and rerun after UI change; only patch if regression reproduced |
| P3-A | existing local Playwright harness; Docker unavailable at baseline | add LOG-C03 reusable flow, attempt runtime gate, mark host blocker if unchanged |
| P3-B | no LOG-C03 detect/review evidence yet | refresh graph/detect-changes and call supervisor before closure |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status and exact evidence IDs.
- [x] Target file relationship/impact evidence is recorded.
- [x] Phase Touch Map defines edit/preserve/inspect/do-not-touch modes.
- [x] Correct parts are marked preserve-only.
- [x] Partial/missing/blocked parts have exact next actions.
- [x] Status Refresh Log has an R0 baseline row.
- [x] P0 decision is complete before product implementation.
- [x] Affected rows and R1+ refreshes are recorded after implementation slices.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete for the bounded LOG-C03 product slice. The next phase must create the missing pure projection and direct tests before touching the legacy Streamlit renderer. Existing Shipment 360/detail/ledger/database surfaces remain preserve/inspect-only. Docker and P2P workflow blockers are recorded and cannot be silently bypassed for final acceptance.

## R1 Refresh — Projection and Fixture Rules

- `E1-P1A-PROJ1`: complete. `core/shipment_dashboard.py` is a pure, read-only projection boundary with separate operational and financial fields, deterministic alert ordering, explicit UNKNOWN financial state, and no database/write imports.
- `E1-P1A-RULE1`: complete. Free time is derived from the existing arrival/free-time fields; warning threshold is `<=2` days and expiry is critical for active shipments.
- `E1-P1A-RULE2`: complete. Customer-required, planned, promised, and factory-information aliases are bounded to explicit source fields; absent evidence does not create a fake alert.
- `E1-P1B-TEST1`: complete. Seven focused test functions cover 16 fixture scenarios and pass through the available manual Python runner.
- `E1-P1B-FILTER1`: complete. Owner, customer, operational, financial, alert, deadline, search, and severity ordering paths are covered without loading real Lục Giác data.

## R2 Refresh — Dashboard Integration

- `E2-P2A-UI1` / `E2-P2A-CARD1`: complete on the local visible Streamlit runtime. The primary queue is one shipment per row and exposes owner/update/route/date, operational status, free time, financial flag/raw status, and next action.
- `E2-P2B-FILTER1` / `E2-P2B-SORT1`: complete. The work desk exposes compact owner/customer/attention/operational/financial filters and keeps existing search/time/status filters above it; `SALE Thành` remains selectable without inventing assignments.
- `E2-P2C-REG1` / `E2-P2C-SECOND1`: complete. The existing active-detail session/rerun path was preserved and the visible browser flow opened T7, closed, then opened LO-0306.

## R3 Refresh — Validation and Closure

- `E3-P3A-BUILD1`: targeted compile and regression evidence passes; `pytest` is unavailable and no Dockerfile/compose target exists, so those environment-level checks remain unavailable.
- `E3-P3A-BROWSER1`: complete on `http://127.0.0.1:8517/`; final flow result is recorded in `Reports/QA/playwright/2026-08-14-log-c03-shipment-dashboard.json`, with dashboard/detail PNG evidence and zero browser console errors/warnings.
- `E3-P3B-DETECT1`: complete. Final Anvien refresh parsed all 65 code files without parse failure; `detect-changes --scope all` is noisy because the worktree contains 17 tracked dirty files and many unrelated user additions.
- `E3-P3B-SUP1`: complete. Supervisor report `reports/supervisor/rp_supervisor_260814_190347_by_gpt-5-codex_log_c03_shipment_dashboard.md` returned `REJECT` for formal closure while clearing the corrected local product slice as technically coherent.

## Current Closure Classification

`BLOCKED` for formal LOG-C03 closure, with the bounded product slice implemented and locally browser-verified. The remaining blockers are external to the slice: the required P2P workflow remains blocked by its active objective/oracle compilation state, and the repository has no Docker build target. No user data or financial ledger write was used to bypass either gate.

## R4 Refresh — Formal Closure Reconciliation — 2026-08-14

The prior classification above is historical pre-oracle status. The latest
closure authority requires separate product and helper verdicts.

| Boundary | Current evidence | Classification | Current status |
|---|---|---|---|
| LOG-C03 product behavior | Dashboard, deterministic rules, separate statuses, valid fixture owner filter, navigation, browser/runtime, write oracle, and LOG-C02 regressions all pass | `PROJECT_REQUIREMENT` | PASS |
| Docker | No Dockerfile, compose target, or documented project Docker workflow; app docs/start script use Streamlit | `NOT_APPLICABLE` | Not a LOG-C03 product gate |
| pytest | Not declared in requirements; unittest is the documented canonical runner and passes | `NOT_APPLICABLE` | Not a LOG-C03 product gate |
| Financial write oracle | Mounted fixture-only AppTest with writer spies and before/after snapshot | `GOAL_ACCEPTANCE_REQUIREMENT` | PASS; count `0` |
| P2P Goal Contract/acceptance marker | Existing run remains BLOCKED at goal linter/objective split; no valid marker generated and no P2P state changed | `P2P_INFRASTRUCTURE_REQUIREMENT` | Helper BLOCKED; product independent |
| SALE Thành owner source | Runtime has no normalized owner source; observed `0/78`; fixture semantics pass | `KNOWN_DATA_MODEL_GAP` | Not a closure blocker; no migration in LOG-C03 |

### Final two-layer status

- Product/project acceptance: `PASS`.
- P2P formal helper: `BLOCKED`.
- Worktree: known dirty and uncommitted; no broad staging, reset, or commit was
  performed.
- No LOG-C04 implementation started.
- Fresh Supervisor review `reports/supervisor/rp_supervisor_260814_193944_by_gpt-5-codex_log_c03_formal_closure.md` returned `PASS` for the product/project layer; the P2P formal helper remains separately `BLOCKED`.
