# LOG-HOTFIX-04 Main Dashboard Repair Actual Status

Title: LOG-HOTFIX-04 Main Dashboard Repair
Date: 2026-08-26
Status: P1 Complete / P2 Pending
Companion plan: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-plan.md`
Companion evidence: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-evidence.md`
Companion benchmark: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-benchmark.md`

## Purpose

This is the completed P0 baseline before implementation. It records the exact
main candidate, the reproduced lazy-import failure, the history-supported
contract, impact counts, and the protected boundaries.

## Freshness / Refresh Rules

Refresh the affected rows after each implementation slice and before the next
phase. Detailed command output remains in `evidence.md`.

## Scope

Target scope:

- Main-only Dashboard and Shipment readiness render path.
- Exact `build_shipment_summary` contract restoration.
- Focused mounted fixture tests and source validation.

Out of scope:

- Production, Streamlit Cloud coordinates, deployment, push, merge, rollback.
- `logistics_db`, all business writes, secrets, auth/RBAC, finance ledger,
  Getfly, GNT, payments, customers, quotations, schemas, and LG09 continuation.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `core/shipment_dashboard.py` | E0-P0A-GRAPH1 | 60 local; 7 linked flows | canonical projection and local helpers | high; edit only exact alias |
| `core/readiness.py` | E0-P0A-GRAPH1 | 67 local; 8 inbound; 3 linked flows | derived readiness/Next Action consumer | high; preserve-only |
| `views/dashboard.py` | E0-P0A-GRAPH1 | 18 local; 3 outbound; 6 linked flows | lazy Dashboard caller and row renderer | high; edit only missing constant import |
| `views/shipment.py` | E0-P0A-GRAPH1 | 7 outbound | lazy Shipment caller and workspace | high; preserve; test exact path |

## Status Rules

| Status | Meaning | Allowed next action |
|---|---|---|
| `correct` | Required behavior is already present. | Preserve and validate. |
| `partial` | Some required behavior exists, but a gap remains. | Change only the missing part. |
| `wrong` | Current behavior or binding is incorrect. | Repair exact cause. |
| `missing` | Required behavior or symbol is absent. | Restore only the established piece. |
| `unbound` | Surface exists but is not connected to the intended source. | Bind to the real source. |
| `fake-or-stub` | Placeholder behavior is presented as real. | Remove or replace truthfully. |
| `blocked` | Authority or required evidence is unclear. | Stop and record blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| `build_shipment_summary` | exact historical alias now delegates to canonical projection | exact historical alias delegating to canonical view | correct | 60 local file relationships | E0-P0A-SRC3, E0-P0A-HIST2, E1-P1A-SRC1, E1-P1B-TEST1 | preserve |
| Dashboard readiness binding | projection, severity constants, and explicit Next Action label resolve on mounted row path | lazy row path resolves and visibly labels the derived action | correct | 18 local / 6 flows | E0-P0A-REPRO1, E1-P1A-SRC2, E1-P1A-SRC4, E1-P1B-TEST1 | preserve |
| Shipment readiness binding | existing LG09 block resolves alias and renders readiness/card/tabs | workspace reaches derived readiness and Next Action | correct | 7 outbound | E0-P0A-REPRO1, E1-P1B-TEST2 | preserve |
| `core.readiness.py` | derived evaluators remain intact; deadline boundary normalizes existing string/date values | remain derived and accept existing string/date boundary safely | correct | 67 local / 8 inbound | E0-P0A-GRAPH1, E1-P1A-SRC3, E1-P1B-TEST3 | preserve |
| Canonical dashboard projection | `build_shipment_dashboard_view` present with mapping/date/financial view contract | remain the single projection authority | correct | 60 local | E0-P0A-SRC3, E0-P0A-HIST2 | preserve-only |
| Financial boundary | existing read-only projection exposes financial status/flag/projection | quote estimate remains separate from Finance Actual; UNKNOWN stays explicit | correct | inspect-only | E0-P0A-SRC3 | preserve-only |
| Production source | `origin/production` at owner-provided SHA | unchanged | correct | external boundary | E0-P0A-SRC2 | do not touch |
| Database / secrets | no access used in P0 | zero access/mutations for this task | correct | external boundary | E0-P0A-BOUNDARY2 | do not touch |
| Docker runtime | executable unavailable | built-runtime gate must be passed or recorded blocked | blocked | environment boundary | E0-P0A-BOUNDARY1 | validate in P2; never substitute |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-26 | `origin/main` / isolated worktree before implementation | all target rows | initial classification above | E0-P0A-SRC1..E0-P0A-BOUNDARY2 | P1-A may proceed; Docker remains a P2 gate |
| R1 | 2026-08-26 | after initial P1-A alias/import edit | alias, Dashboard binding, readiness deadline input | alias `missing -> present`; Dashboard `partial -> bound`; readiness `correct -> partial` after exact TypeError surfaced | E1-P1A-OBS1 | extend P1-A with parser boundary; keep readiness rules unchanged |
| R2 | 2026-08-26 | after date-boundary edit | Dashboard readiness copy | Dashboard `bound -> partial` because the derived action is not explicitly labeled in the visible strip | E1-P1A-OBS2 | add the smallest visible label; keep derived state unchanged |
| R3 | 2026-08-26 | after P1-A/P1-B source and focused-test slices | alias, Dashboard, Shipment, readiness | alias `missing -> correct`; Dashboard `partial -> correct`; Shipment `partial -> correct`; readiness `partial -> correct` | E1-P1A-SRC1..E1-P1B-CHECK1 | proceed to P2 validation; Docker remains a gate |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| `core/shipment_dashboard.py` | `views/dashboard.py` | source-of-truth / consumer | P1-A | edit | E0-P0A-HIST2, E0-P0A-SRC3 | exact alias only |
| `core/shipment_dashboard.py` | `views/shipment.py` | source-of-truth / consumer | P1-A/P1-B | preserve-only / validate-only | E0-P0A-REPRO1 | no caller redesign |
| `core/readiness.py` | `views/dashboard.py` | derived projection consumer | P1-A/P1-B | edit boundary / validate-only | E0-P0A-SRC4, E1-P1A-SRC3 | no persisted state; use existing parser |
| `core/readiness.py` | `views/shipment.py` | derived projection consumer | P1-B | preserve-only / validate-only | E0-P0A-SRC4 | no readiness rewrite |
| `views/dashboard.py` | `views/web_app.py` | route caller | P1-A/P1-B | edit one import / validate-only | E0-P0A-REPRO1 | preserve route behavior |
| `tests/test_all_tabs_smoke.py` | focused test | behavior-test precedent | P1-B | inspect-only | E0-P0A-REPRO1 | do not weaken broad smoke |
| Production worktree | main candidate | protected external source | all | do-not-touch | E0-P0A-SRC2 | no deployment or mutation |
| Database/secrets | test fixtures | protected external state | all | do-not-touch | E0-P0A-BOUNDARY2 | no credentials or DB |

## Detailed Findings

### Main lazy Dashboard path

Current state:

- The mounted all-tabs test reaches the Dashboard route and fails in the real
  lazy path before row rendering because the imported symbol is absent.
- The same compatibility name is required by the Shipment workspace path.

Required state:

```text
build_shipment_summary(shipment, *, today=None, financial_view=None)
    -> build_shipment_dashboard_view(shipment, today=today, financial_view=financial_view)
```

Evidence:

- E0-P0A-REPRO1: exact mounted failure.
- E0-P0A-HIST2: exact previous implementation.
- E0-P0A-SRC4: Dashboard's missing `CRITICAL` binding.

Relationship and impact:

- Related file count: 60 local source relationships plus Dashboard/Shipment
  consumers.
- Relationship summary: canonical projection feeds two LG09 lazy consumers.
- Impact note: narrow source repair; high-risk file requires focused runtime
  proof.

Classification:

`missing` for the alias; `partial` for Dashboard constant binding.

Allowed next action:

Implement P1-A exactly from history, then prove P1-B mounted behavior.

Forbidden next action:

Rollback LG09, invent fallback data, modify finance/database/auth, or deploy.

### LG09 readiness projection

Current state:

- `core/readiness.py` exists on current main with evaluators, derived results,
  and `derive_next_action`.
- Both callers invoke it after the dashboard summary is built.

Required state:

Preserve the module and render-derived readiness/Next Action surfaces without
persisting readiness or altering business data.

Evidence:

- E0-P0A-GRAPH1: file relationship and parse evidence.
- E0-P0A-HIST3: rollback history showing readiness deletion was part of the
  rejected inverse candidate.

Relationship and impact:

- Related file count: 67 local relationships and 8 inbound references.
- Relationship summary: derived readiness has multiple callers.
- Impact note: preserve-only; test through callers.

Classification:

`correct` but not yet runtime-verified under the repaired contract.

Allowed next action:

Validate through focused mounted tests; do not rewrite.

Forbidden next action:

Delete, duplicate, persist, or broaden LG09.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | alias, Dashboard import, date boundary, and visible action label are repaired | preserve all four verified surfaces and move to P2 |
| P1-B | exact Dashboard lazy path and Shipment workspace pass focused mounted tests | preserve tests and continue to P2 |
| P2-A | P1 mounted/source tests pass; Docker remains unavailable | run full available validation and record Docker as blocked if unchanged |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from file-detail.
- [x] Phase Touch Map defines touch mode for plan-relevant units.
- [x] Correct parts are marked preserve-only.
- [x] Missing/partial parts have exact next actions.
- [x] Blockers are recorded: Docker runtime unavailable.
- [x] Next phase status assumptions and work steps reflect the baseline.
- [x] Status Refresh Log has an R0 baseline row.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are defined.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Authority and source contract are sufficiently established for a narrow main-only
repair. The Docker runtime limitation is a later validation gate, not a reason
to invent a source fix or touch protected systems.
