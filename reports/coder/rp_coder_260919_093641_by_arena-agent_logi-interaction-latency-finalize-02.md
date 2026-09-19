# Coder Report — LOGI_INTERACTION_LATENCY_FINALIZE_02 (post-action server latency)

Status: PASS — measured, bounded repair; Step 2 (read overlap) re-implemented STREAMLIT-FREE after
the Control Tower blocked the `add_script_run_ctx` / `get_script_run_ctx` worker design.
`P2P_LAW_SOURCE=LOCAL_PORTABLE` (AGENTS.md → `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`).
Focused regression: `tests/test_logi_interaction_latency_finalize_02.py` (13 passed) + PR50 invariants
`tests/test_logi_interaction_latency_repair_01.py` (20 passed) — see §Tests.

## Git reference

- Branch: `arena/01a0b8e4-logistics-work-desk-arena` (the session branch; the packet's "fresh task
  branch" wording is superseded by the platform rule that pins this session to one branch)
- Base main: `5db3d4155a206fff84a937f30567d21341f5a63e` (= EXPECTED_MAIN)
- Previous head of this task: `b37a93584584ff0fd416cfbaf290f5270d2ea34a` (Step 1 + ctx-based Step 2)
- Issue: #73 · PR: #74 (open, not merged)

## Control Tower verdict on `b37a935` and what changed

- ACCEPTED and kept unchanged: Step 1 — render-local snapshot reuse, duplicate-read removal, C1 N+1
  removal, contract in-memory index, partner-context / docgen snapshot reuse, build reads 26 → 17,
  output parity.
- BLOCKED and REWRITTEN: Step 2. `b37a935` attached Streamlit's ScriptRunContext to
  `ThreadPoolExecutor` workers (`add_script_run_ctx` / `get_script_run_ctx`) — private, unsupported
  runtime behaviour for `streamlit>=1.51,<2`. Production correctness must not depend on it.

New Step 2 shape (required safe shape):

| Thread | What happens |
| --- | --- |
| **Script thread** | resolves the canonical db handle (`core.database.get_db()`, i.e. the cached connection + `validate_mongo_identity`) ONCE per render, resolves the session values the projections need, then builds explicit pure read jobs |
| **Workers** | short-lived; PyMongo / mongomock **reads** and pure Python normalisation/grouping only — no `add_script_run_ctx`, no `get_script_run_ctx`, no `st.session_state`, no `st.cache_data` / `st.cache_resource`, no `st.secrets`, no Streamlit command, no write/audit/auth/session mutation/provider call |
| **Join** | every worker is joined before `_read_concurrently` returns; the script thread then replays captured error messages in declaration order and raises the first failing read's exception (also in declaration order) |

Implementation, in detail:

1. `core.database._UNSET_DB` sentinel + optional `db=` on the readers the concurrent path calls
   (`_load_dict`, `_load_data_impl`, `load_shipment_ids`, `load_quotes`, `load_tasks`,
   `_load_customers_impl`, `_load_contracts_impl`, `load_knowledge_base`, `load_users`,
   `load_agreements`, `load_authority_companies`, `load_authority_agents`,
   `load_shipment_attachments`, `load_docgen_documents`, `load_audit_logs`, `load_audit_logs_bulk`,
   `core.financial_ledger.load_ledger_snapshot`). `db=` default is the sentinel, so **standalone
   callers keep the original behaviour exactly**; `None` is a real value ("no database"), which a
   worker may safely receive because it never re-resolves anything.
   `views.logi_real_data.timeline_projection / timelines_projection / attachments_by_shipment` got
   the same pass-through parameter (no second persistence source, no duplicated query semantics).
2. The render's concurrent path calls the **uncached** implementations (`_load_customers_impl`,
   `_load_contracts_impl`, `_load_data_impl`) because the public `load_customers` / `load_contracts`
   are `st.cache_data` objects — a Streamlit-free worker may not call them. Same collections, same
   query, same result. Side effect, disclosed: the render no longer serves the 30 s cached
   customers/contracts slice, so those two reads are as fresh as the shipment read already was (the
   caches themselves are untouched and the legacy screens keep using them).
3. `core.database.captured_db_errors()` / `db_errors_captured()` / `replay_db_error()` + a
   capture branch in `_set_last_error`: a worker's error report is collected per thread and never
   published, so `_LAST_DB_ERROR` and `st.session_state.last_db_error` are only ever mutated by the
   script thread.
4. `views.logi_view_model._read_concurrently` no longer imports or calls the script-run-context
   helpers at all; `_READ_WORKERS = 1` remains the operational one-after-another fallback.

## Measure first — what is actually slow (N = 95, isolated staging transport)

Instrument: a harness that replays the REAL Components v2 lifecycle
(`views.logi_shell._on_component_event()` → `views.web_app.main()`), `AUTH_REQUIRED=True` with a
seeded SUPPORT operator (so the fresh RBAC revalidation is a real `users` read), timing every phase
and counting every MongoDB operation per phase. `LOGI_PERF_RTT_MS` charges a synthetic per-operation
round trip (default 0 = pure local CPU); `LOGI_PERF_PROVIDER_MS` is injected into the MOCKED DeepL
client and reported separately. Elapsed ms, op counts and collection names only — no payload
contents, no customer or business data, no secrets. No production instrumentation was added.

### BEFORE (base main `5db3d41`), median of 3

| RTT model | Interaction | TOTAL | callback | READBACK (ops) | BUILD (ops) | POST_ACTION (ops) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 ms | translate_text | 119.6 | 2.4 | — | 116.0 (26) | 116.5 (27) |
| 0 ms | shipment_field_save | 113.6 | 7.1 | 2.6 (12) | 102.5 (26) | 106.1 (39) |
| 0 ms | payment_record | 107.8 | 5.9 | 2.5 (12) | 100.9 (26) | 103.9 (39) |
| 20 ms | translate_text | 689.5 | 24.7 | — | 644.2 (26) | 665.0 (27) |
| 20 ms | shipment_field_save | 1020.9 | 126.7 | 245.6 (12) | 627.6 (26) | 893.9 (39) |
| 20 ms | payment_record | 1049.4 | 146.3 | 245.5 (12) | 635.0 (26) | 903.1 (39) |

AUTH_REVALIDATION_MS ≈ 0.5 (RTT 0) / ≈ 41 (RTT 20) — 1 op in the callback + 1 op in the script body,
both kept. WRITER (incl. audit) ≈ 2 / 83 (field save) and ≈ 1.4 / 123 (payment) — never parallelised.

**Measured root cause:** local CPU is ~100 ms per interaction and is NOT what the Owner feels. The
post-action path issued **27 (translate) / 39 (write) sequential MongoDB round-trips**; in production
each one is a Streamlit-Cloud ↔ Atlas network wait (`round-trips × RTT`). Inside the ONE build (26
ops) nine were avoidable duplicates (`customers` ×2, `contracts` ×2 **+ one `contracts.find_one` per
contract (N+1)**, `quotes` ×2, `authority_agents` ×3, `docgen_documents` ×2); the remaining 17 reads
are mutually independent yet were awaited one after another.

`FULL_VM_BUILD_HOTSPOT` (CPU, untouched — correct, not duplicated): PER_SHIPMENT_PROJECTION ≈ 45 ms,
DASHBOARD_VIEWS ≈ 14 ms, `repair_data` ≈ 12 ms, PAYLOAD_VERSION ≈ 12 ms.

## AFTER — three configurations, same harness, same modeled RTT, median of 3 runs

`CURRENT_B37A935` = the blocked head (Step 1 + ctx-in-workers). `NEW_SAFE_CONCURRENCY` = this change.

### RTT model 20 ms

| Interaction | BEFORE post-action | CURRENT_B37A935 | NEW_SAFE_CONCURRENCY | Δ NEW vs BEFORE |
| --- | --- | --- | --- | --- |
| translate_text | 665.0 | 223.0 | **222.2** | **−66.6 %** |
| shipment_field_save | 893.9 | 372.5 | **375.0** | **−58.1 %** |
| payment_record | 903.1 | 386.3 | **376.6** | **−58.3 %** |

Supporting figures at 20 ms (NEW): TOTAL 245.8 / 502.7 / 523.4 · BUILD 201.4 / 187.6 / 189.9 (17 ops
each, was 26) · READBACK — / 166.6 / 166.0 (12 ops, was 245.6) · AUTH 41 · WRITER 0 / 83.8 / 123.7.

`NEW_SAFE_CONCURRENCY` vs `CURRENT_B37A935`: −0.4 % / +0.7 % / −2.5 % — i.e. **the safe redesign
keeps the entire gain**; the differences are inside run-to-run noise. Nothing was traded for safety.

### RTT model 0 ms (pure local CPU — mongomock, no network)

| Interaction | BEFORE post-action (ops) | CURRENT_B37A935 | NEW_SAFE_CONCURRENCY (ops) |
| --- | --- | --- | --- |
| translate_text | 116.5 (27) | 124.5 | 123.0 (18) |
| shipment_field_save | 106.1 (39) | 116.6 | 114.5 (30) |
| payment_record | 103.9 (39) | 111.8 | 112.8 (30) |

Honest note: with no network at all the overlap buys nothing and costs ≈ 5–10 ms of thread-pool
overhead per interaction (+5–9 %). The repair targets round-trips; break-even is well under 1 ms RTT,
i.e. any real database link.

### Transport-independent evidence

- Build reads at N = 95: **26 → 17** (−34.6 %); `contracts.find_one` = 0; every reference collection
  ≤ 1 read; `shipments.find` ≤ 2 (worklist + the bounded id projection the finance worklists share).
- Post-action ops: translate 27 → 18 (−33 %), writes 39 → 30 (−23 %).
- Sequential round-trip depth: build 26 → 4 waves; readback 12 → 8; post-action critical path
  translate 27 → ≈5 (−81 %), writes 39 → ≈13 (−67 %).
- Wall-clock overlap proof, asserted in the tests at a 60 ms/op model: build ≈ 350–370 ms vs a serial
  floor of 1020 ms (17 ops); readback 487 ms vs 720 ms (12 ops).
- Parity: concurrent build == sequential build byte-for-byte (`version` included) — under the harness
  **and** under a real `AppTest` runtime; C1 payload from the snapshot == standalone reads; in-memory
  contract links == `load_shipments_for_contract` per contract.

`TIMING_EVIDENCE_CLASS=LOCAL_MODELED_RTT` — real Atlas RTT is unknown here; the 20 ms model is a
conservative same-region figure. DeepL provider time is measured separately by the mocked client and
is not claimed as reduced (`TRANSLATION_PROVIDER_TIME_SEPARATED=YES`).

## Acceptance proofs the Control Tower asked for

| Item | Result | Where |
| --- | --- | --- |
| CONCURRENT_OUTPUT_EQUALS_SEQUENTIAL | PASS | `test_concurrent_reads_produce_the_identical_view_model`, `test_streamlit_free_workers_produce_the_identical_view_model` |
| VERSION_EQUALS | PASS | same tests (`model["version"]`) |
| WORKER_STREAMLIT_API_CALLS | 0 | `test_read_workers_never_touch_the_streamlit_api` |
| WORKER_SESSION_STATE_CALLS | 0 | same (delegating proxy on `st.session_state`) |
| WORKER_CACHE_CALLS | 0 | same (`st.cache_data`, `st.cache_resource`) |
| WORKER_SCRIPT_RUN_CONTEXT_CALLS | 0 | same (`add_script_run_ctx` / `get_script_run_ctx`, incl. `core.config`) |
| WRITES_PARALLELIZED | NO | same (every non-read op, and everything in AUTH/WRITER, is asserted main-thread-only) |
| AUTH_PARALLELIZED | NO | same (`users.find` in the AUTH phase is main-thread only) |
| AUDIT_PARALLELIZED | NO | same (`audit_logs.insert_one` in the WRITER phase is main-thread only) |
| BACKGROUND_WORK | NO | pool is torn down inside `_read_concurrently`; all workers joined |
| AUTHORITATIVE_READBACK_PRESERVED | YES | `read_shipment` → `_projection_for` unchanged; `shipments.find_one` in READBACK is main-thread only |
| ERROR_SEMANTICS_DETERMINISTIC | PASS | `test_worker_read_errors_are_replayed_on_the_script_thread`, `test_captured_db_errors_defer_publication_and_replay_in_order` |
| HANDLER_CALLS_PER_INTENT / VM_BUILDS_PER_INTENT / EXPLICIT_SECOND_RERUNS | 1 / 1 / 0 | PR50 invariants (20 tests) + the three interaction tests |

The hard guard is a real regression guard, not a tautology: run against `b37a935`'s views it fails
with **25+ `get_script_run_ctx` calls from `logi-read_*` threads**, and the AppTest guard fails
because the old workers *did* carry a context (`worker_ctx = [('logi-read_0', True), …]`).

Real-runtime proof (`AppTest`, actual ScriptRunContext on the script thread): the submitting thread
has a context (`submitter_has_ctx = [True, True]` — so the cached connection and the session values
are resolved there), the 16 worker executions have **none**, no exception, parity True.

Build reads 17 = EXPECTED 17.

## OE gate — "Không bị over engineering chứ?"

OE_VERDICT: NOT over-engineered. This round: 5 files, +534/−104 lines including docstrings —
one sentinel + an optional `db=` parameter on existing readers (no new query semantics), three small
error-capture primitives, and the rewritten 30-line helper. No repository layer/framework, no Redis /
Celery / queue / new API / websocket / event bus / background service / new DB / second read model /
microservice / frontend state framework; no cache introduced, no skipped read, no optimistic UI, no
RBAC/audit change, no schema change. Reversible: `_READ_WORKERS = 1`.

## Tests (focused only)

- `tests/test_logi_interaction_latency_finalize_02.py` — **13 passed**: 3 representative interactions
  (translate / shipment_field_save / payment_record) with truthful readback + deterministic op
  budgets, duplicate-translate (double-paid-call) guard, concurrent == sequential parity, overlap
  proof at a modeled RTT, C1 / partner-context / docgen snapshot parity, **+4 new guards**
  (Streamlit-free workers, error replay, capture primitives, real-runtime AppTest).
- PR50 invariants `tests/test_logi_interaction_latency_repair_01.py` — 20 passed.
- `tests/test_logi_render_performance_01.py` — 13 passed.
- Translation / paid-call guard: `test_deepl_config_shapes`, `test_deepl_route_rbac`,
  `test_deepl_translation`, `test_deepl_translation_ui`, `test_translation_workspace` — 61 passed,
  4 subtests passed.
- Representative shipment + finance/customer write truthfulness, C1/partner/docgen/session:
  `test_logi_c2a_finance_actual`, `test_logi_c2b_partner_payable`,
  `test_logi_c2d_global_partner_payables`, `test_logi_customer_payment_correction_ui_01`,
  `test_logi_finance_actual_entry_parity_01`, `test_logi_shipment_core_gaps_01`,
  `test_logi_shipment_documents_drive_02`, `test_logi_shipment_documents_gridfs_runtime`,
  `test_logi_shipment_operational_data_v1`, `test_partner_context_workspace`,
  `test_phase_c1_business_contracts`, `test_session_truth_repair` — 223 passed, 2 pre-existing
  failures (see below).
- Broad sweep `tests/test_logi_*.py` — 372 passed, 3 failed; all three failures reproduce identically
  on base main `5db3d41` with the production changes stashed (`test_logi_cn_truck_type_persist_01::
  test_whitelist_gained_exactly_the_one_approved_key`,
  `test_logi_shipment_core_gaps_01::test_created_at_is_now_in_the_write_whitelist`,
  `test_logi_shipment_operational_data_v1::test_lightweight_create_starts_one_canonical_leg_and_navigable_detail_data`).
- Frontend untouched → `TYPECHECK=N/A`, `BUILD=N/A`, `DOM_ACCEPTANCE=N/A`.
- Lint (`ruff --select E9,F` on the changed files): 6 findings, **all pre-existing** on `b37a935`,
  none introduced.

## Safety

PRODUCTION_MUTATIONS=0 · PILOT_MUTATIONS=0 · PAID_PROVIDER_CALLS_IN_TESTS=0 (DeepL mocked) ·
SECRETS_CHANGED=NO · DEPLOYED=NO · logistics_db / tienthanhlog untouched. All measurements ran on the
isolated mongomock staging transport.

## Observations for Control Tower (not changed here)

- `save_customer_to_cloud` does not clear the 30 s `load_customers` `st.cache_data` (pre-existing
  freshness gap; contracts do invalidate). The render path no longer depends on that cache.
- `core.financial_ledger.shipment_partner_position` scans every ledger row per shipment
  (O(shipments × ledger rows), `isinstance(x, typing.Iterable)` per row); ≈ 12 ms at the fixture's
  5 ledger rows, grows linearly with the ledger — a CPU follow-up if the ledger becomes large.
- The write readback still issues its ledger ×3 / agents / docgen reads inside `shipment_projection`
  (8 sequential waves); routing it through the same snapshot path the render uses would cut it to
  ≈ 4 — deliberately not done (readback code path kept identical).
- Perceived UX: the pending state reacts immediately already (PR50); no fake progress or phase text
  was added because the architecture cannot truthfully report "translating" vs "refreshing" per phase
  from a single rerun.
- If the Control Tower prefers zero extra threads, `_READ_WORKERS = 1` restores the sequential path
  and keeps every Step 1 gain (build 26 → 17 ops); the wall-clock overlap then disappears.
