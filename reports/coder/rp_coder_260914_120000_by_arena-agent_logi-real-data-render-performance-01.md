# Coder Report — LOGI_REAL_DATA_RENDER_PERFORMANCE_01 (real-data render N+1)

Status: PASS for the bounded performance repair. One render, one read per source.
Focused regression: `tests/test_logi_render_performance_01.py` (13 passed).

## Git reference

- Branch: `arena/01a0a0e7-logistics-work-desk-arena`
- Base main at handoff: `02095e6f78ce851b39546a6b0ce4c4cc4d1862b8` (unchanged when this work started)

## Root cause (reproduced, N = 95, isolated staging transport)

`views.logi_view_model.build_view_model()` called readers that each re-fetched COMPLETE collections:

| Per-shipment call | Collection re-read |
| --- | --- |
| `finance_projection` → `_partner_projection` → `shipment_partner_position` | `financial_obligations` + `financial_transactions` + `financial_allocations` |
| `pxk_projection` → `_pxk_document` | `docgen_documents` (scoped query) |
| `pxk_projection` (no direct contract match) | full `contracts` scan via `load_contracts_for_shipment` |
| `build_view_model` → `timeline_projection(sid)` | `audit_logs` |
| `_partner_projection` (no ledger record yet) | `authority_agents` |
| `partner_payables_projection()` + `reconciliation_view()` | the three ledger collections **again** per shipment id |
| `assemble_c1_payload()` | the full `shipments` collection the render already had |

Measured on the base commit, same fixture, ONE render: **1 192 collection reads**
(ledger alone 855 = 95 × 3 × 3 paths).

## Repair (one request/render-local snapshot; no cache layer)

- `core/financial_ledger.load_ledger_snapshot()` — the three ledger collections read once;
  `shipment_partner_position(..., records=snapshot)` consumes it (old per-call path kept for
  every caller that passes no snapshot).
- `core/database.load_audit_logs_bulk()` — one bounded audit read, grouped in memory, same
  newest-first / per-entity-limit semantics.
- `core/database.load_shipment_ids()` — the shared non-deleted id query the two global finance
  worklists each ran.
- `views/logi_real_data`: `timelines_projection`, `docgen_documents_by_shipment`,
  `linked_contracts_index` (zero reads — built from contracts already loaded) and optional
  snapshot parameters on `shipment_projection` / `finance_projection` / `pxk_projection` /
  `partner_payables_projection`.
- `views/logi_c1.assemble_c1_payload(shipments=...)` and
  `views/reconciliation_desk.reconciliation_view(shipment_ids=..., records=...)`.
- `views/logi_view_model._read_sources()` builds the snapshot once per render and shares it.

No Redis, service, database, API, persistent cache, schema change, writer change, RBAC change,
route change or UI change. Nothing is stored on the module, the session or the process: the next
rerun reads again, so a fresh write is visible on the very next render as before.

## Evidence

Collection reads per render, N = 95, same fixture:

| Source | BEFORE | AFTER |
| --- | --- | --- |
| financial_obligations / transactions / allocations | 285 each | 1 each |
| audit_logs | 95 | 1 |
| docgen_documents | 96 | 2 (PXK blocks + C1) |
| authority_agents | 96 | 3 |
| contracts | 37 | 5 |
| shipments | 4 | 2 |
| **total** | **1 192** | **25** |

Local sandbox timing (mongomock, median of 3, no Atlas network latency):

| Segment | BEFORE | AFTER |
| --- | --- | --- |
| `build_view_model()` total | 223.3 ms | 84.9 ms |
| shipment projections | 91.6 ms | 36.2 ms |
| C1 payload | 15.3 ms | 1.6 ms |
| payables | 30.7 ms | 1.0 ms |
| reconciliation | 31.4 ms | 1.3 ms |

`TIMING_EVIDENCE_CLASS=LOCAL_NOT_LIVE` — each removed read is a network round trip on Atlas, so
the live gain is expected to exceed these local numbers. Live proof belongs on thu-log after merge.

Output equivalence: base-commit payload vs repaired payload on a byte-deterministic fixture
(frozen clock + deterministic ids) — every section digest identical (shipments, payables,
receivables, reconciliation, contracts/customers/quotes/agreements/authority, home, tasks,
notifications, ceoReport, partnerContext, handbook, userAccess, translation); the only difference
is the repository path inside the tariff source path and the internal `version` hash, which hashes
task documents including their random Mongo `_id`.

Suites: `12 failed, 765 passed, 38 skipped, 6 errors` (repaired) vs `12 failed, 752 passed,
38 skipped, 6 errors` (base) — identical failure list, +13 from the new focused test file.
