# LOG-C10 Documents & Review Queue Actual Status

Title: LOG-C10 Documents & Review Queue
Date: 2026-08-16
Status: P0 Complete / P1 Complete / P2 Complete / P3 Complete / Local PASS / Release NOT_RELEASED
Companion plan: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-plan.md`
Companion evidence: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-evidence.md`
Companion benchmark: `docs/plans/2026-08-16-log-c10-documents-review-queue/2026-08-16-log-c10-documents-review-queue-benchmark.md`

## Purpose

This is the living baseline for LOG-C10. It separates the correct LOG-C07/C08/C09 read-first foundations from the missing review/document queue before implementation.

## Scope

Target scope:

- deterministic review-item projection;
- Documents & Review Queue route and filters;
- queue-to-Shipment 360/Entity Context navigation and return context;
- relevant review/document signals in Shipment 360;
- real local render, critique, correction, and bounded regression evidence.

Out of scope:

- canonical financial ledger, payment/allocation/FX, historical A Bò, entity CRUD, full document management, deploy/release, AI, and broad legacy migration.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `core/shipment_dashboard.py` | `E0-P0A-DETAIL1` | 60 local / 12 flows | existing deterministic status, deadline, factory, finance alert projection | high hotspot; preserve-only |
| `views/dashboard.py` | `E0-P0A-DETAIL2` | 11 local / 4 flows | shipment-first queue, existing open Shipment 360 and writers | high file risk; narrow integration only |
| `views/web_app.py` | `E0-P0A-DETAIL3` | 17 local / 2 flows | grouped navigation and route loader | high file risk; add route metadata only |
| `views/shipment_360.py` | `E0-P0A-DETAIL4` | 9 local / 2 flows | read-only operational/financial renderers | high file risk; narrow display/navigation only |
| `core/shipment_workspace.py` | `E0-P0A-SRC1` | existing pure projection | document/lots/timeline/next-action context | inspect-only dependency |
| `core/financial_ledger.py` / LOG-C06 history | `E0-P0A-SAFE1` | governed prior scope | canonical truth and unpublished historical boundary | do-not-touch |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| LOG-C07 Dashboard shell/queue | shipment-first Dashboard is present and supervisor-reviewed | preserve, add only a distinct queue route/integration | correct / preserve-only | 11 local | `E0-P0A-REC1` | no Dashboard redesign |
| LOG-C08 Shipment 360 | operations-first read-only workspace with deterministic next action, docs/lots/timeline, finance source semantics | preserve and surface relevant review signals | correct / narrow integration | 9 local | `E0-P0A-REC2` | edit only if required for return/review context |
| LOG-C09 Entity Context | customer/factory/partner read-only workspaces and cross-links | preserve and reuse queue targets | correct / preserve | existing prior evidence | `E0-P0A-REC3` | no entity CRUD changes |
| Review-item projection | no dedicated review queue model; Dashboard alerts are shipment-oriented | actionable, deduplicated, deterministic items | missing | new | `E0-P0A-SRC2` | implement P1-A |
| Review Queue route | no `Review Queue` route in `views/web_app.py` | compact searchable/filterable queue | missing | 17 in shell | `E0-P0A-SRC2` | implement P2-A |
| Document review experience | Shipment 360 exposes partial/UNKNOWN document facts, but no work queue | status, reason, evidence, owner/next action in queue | partial | workspace dependency | `E0-P0A-SRC1` | implement P1-A/P2-A |
| Legacy identifier/source contract | existing C09 bounded mapping-key fallback supports entity/shipment navigation | queue targets must retain provenance and avoid silent inference | partial / bounded risk | route consumers | `E0-P0A-REC3` | inspect and fix only if queue flow is blocked |
| Financial review signals | existing canonical/source-labelled read model and Dashboard financial alerts | queue signals only, no new financial truth | correct / preserve-only | governed | `E0-P0A-SAFE1` | consume status/source only |
| Docker full build | Docker unavailable in recovered environment | release-grade container evidence | blocked | n/a | `E0-P0A-ENV1` | local evidence only; no release claim |
| pytest | pytest unavailable in prior baseline | use unittest/compileall if still unavailable | blocked tooling | n/a | `E0-P0A-ENV1` | report limitation honestly |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-16 | current source, prior LOG-C07/C08/C09 closure, fresh Anvien analyze/file-detail/impact | full LOG-C10 baseline | review projection/route missing; C07/C08/C09 correct and protected | `E0-P0A-REC1..E0-P0A-ENV1` | P1 creates pure projection; P2 adds route/integration; protected cores remain preserve-only |
| R1 | 2026-08-16 | P1 projection implementation plus focused unittest/compileall | `core/review_queue.py`, `tests/test_review_queue.py` | review projection missing -> correct; route remains missing | `E1-P1A-SRC1..E1-P1B-METRIC1` | P2 can render from tested contract; critique must assess 205-item local dataset |
| R2 | 2026-08-16 | route, navigation, visible Chrome rerender, focused/full regression | `views/review_queue.py`, shell registration, bounded return context, QA artifacts | route missing -> correct; queue navigation and return -> correct; first-render filter density -> corrected | `E2-P2A-RENDER1..E3-P3C-ENV1` | local bounded slice is ready for supervisor acceptance; no release claim |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| new `core/review_queue.py` | `core/shipment_dashboard.py`, `core/shipment_workspace.py` | read-model consumer | P1-A | edit | `E1-P1A-SRC1` | pure, no DB/writer imports |
| new `tests/test_review_queue.py` | `core/review_queue.py` | behavior proof | P1-B | edit | `E1-P1B-TEST1` | in-memory fixtures only |
| new `views/review_queue.py` | `core/review_queue.py`, `core/database.py` | route renderer/read consumer | P2-A | edit | `E0-P0A-SRC2` | no writers; compact rows |
| `views/web_app.py` | route modules/auth | navigation consumer | P2-A | narrow edit | `E0-P0A-DETAIL3` | preserve permissions/session keys |
| `views/dashboard.py` | existing detail and close flow | navigation sibling | P2-B | narrow edit | `E0-P0A-DETAIL2` | preserve writer behavior |
| `views/entity_context.py` | existing entity request state | navigation sibling | P2-B | inspect/narrow edit | `E0-P0A-REC3` | no CRUD changes |
| `views/shipment_360.py` | existing read-only renderer | review/document display sibling | P2-B | inspect/narrow edit | `E0-P0A-DETAIL4` | preserve finance semantics |
| financial ledger/history | governed prior surfaces | protected truth | all | do-not-touch | `E0-P0A-SAFE1` | no mutation/publication |

## Detailed Findings

### Review Queue

Current state: missing as a dedicated route and projection. Existing Dashboard alerts are useful source signals but are not a work-item model and do not cover document/data-quality context in a queue-friendly shape.

Required state: deterministic review items with category, status, severity, reason, next action, entity/shipment context, source/evidence, and navigation targets.

Classification: `missing`.

Allowed next action: implement pure projection and bounded read-only route.

Forbidden next action: add resolve writers, fabricate document completeness, or change financial/history truth.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | pure projection implemented and tested for read-only contract | complete; preserve projection boundary |
| P1-B | focused behavior tests pass for signals, priority, filters, UNKNOWN, and immutability | complete; P2 may render |
| P2-A | route renders with compact filters, stable queue fields, metrics, and selected-item detail | complete; preserve read-only route boundary |
| P2-B | queue opens Shipment 360, exposes bounded Entity Context target, and returns to queue | complete; preserve existing destination workspaces |
| P3 | visible runtime was critiqued and corrected; focused/full regressions pass; Docker/pytest remain environment blockers | complete for local scope; release remains `NOT_RELEASED` |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Existing target files have current relationship counts from Anvien file-detail.
- [x] Correct C07/C08/C09 surfaces are preserve-only where applicable.
- [x] Missing/partial queue/document surfaces have exact next actions.
- [x] Protected financial and historical boundaries are explicit.
- [x] P0 baseline evidence and downstream phase updates are recorded.
- [x] P1 projection and focused behavior tests are complete; P2 assumptions are refreshed.

## Final Phase Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are updated from evidence.
- [x] P1 complete. Queue route/render work may proceed from the tested projection.
- [x] P2 complete. Queue and bounded destination/return flows are implemented and evidenced.
- [x] P3 complete. Local render, critique, correction, regression, and closure evidence are recorded.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The owner request defines a bounded, read-first Documents & Review Queue. LOG-C07/C08/C09 remain preserve-only foundations. LOG-C10 now has a deterministic projection, a read-only route, bounded Shipment 360/Entity Context navigation, a visible local render, a material viewport correction, and passing local regressions. Docker/deploy evidence is not available, so this is a local PASS and not a release claim.
