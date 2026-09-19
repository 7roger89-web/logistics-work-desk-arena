# Coder Report — LOGI_INTERACTION_LATENCY_FINALIZE_02 (post-action server latency)

Status: PASS — measured, bounded repair of the post-action (non-provider) server latency.
`P2P_LAW_SOURCE=LOCAL_PORTABLE` (AGENTS.md → `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`).
Focused regression: `tests/test_logi_interaction_latency_finalize_02.py` (new, 8 passed) +
PR50 invariants `tests/test_logi_interaction_latency_repair_01.py` (20 passed) — see §Tests.

## Git reference

- Branch: `arena/01a0b8e4-logistics-work-desk-arena` (the session's fresh branch off main)
- Base main: `5db3d4155a206fff84a937f30567d21341f5a63e` (= EXPECTED_MAIN, unchanged at start)
- Issue: #73

## Measure first — what was actually slow (N = 95, isolated staging transport)

Instrument: a harness that replays the REAL Components v2 lifecycle
(`views.logi_shell._on_component_event()` → `views.web_app.main()`), `AUTH_REQUIRED=True` with a
seeded SUPPORT operator (so the fresh RBAC revalidation is a real `users` read), and counts every
MongoDB operation per phase besides timing it. `LOGI_PERF_RTT_MS` charges a synthetic per-operation
round trip (default 0 = pure local CPU); `LOGI_PERF_PROVIDER_MS` is injected into the MOCKED DeepL
client and reported separately. Elapsed ms, op counts and collection names only — no payload
contents, no customer or business data, no secrets. No production instrumentation was added.

### BEFORE (base main), median of 3, RTT model 0 ms (mongomock ≈ no network)

| Interaction | TOTAL_SERVER_MS | callback (handler) | AUTHORITATIVE_READBACK | BUILD_VIEW_MODEL | POST_ACTION_SERVER_MS (ops) |
| --- | --- | --- | --- | --- | --- |
| translate_text | 119.1 | 2.7 (0 DB ops; provider mocked) | — | 115.6 (26 ops) | 116.0 (27) |
| shipment_field_save | 107.0 | 7.2 (pre-read 1 + writer 4 incl. audit) | 2.5 (12 ops) | 98.9 (26 ops) | 102.0 (39) |
| payment_record (finance write) | 108.2 | 6.1 (writer 6 incl. audit + outbox) | 2.5 (12 ops) | 100.5 (26 ops) | 103.6 (39) |

AUTH_REVALIDATION_MS = 0.5 (callback 0.3 / 1 op + body 0.2 / 1 op). Build phases (field-save run):
LOAD_SHIPMENTS 13.0 (1 op) · LOAD_REFERENCES 2.4 (14 ops: 4 references + 10 inside the C1 payload) ·
DASHBOARD_VIEWS 13.4 (0) · READ_SHARED_SOURCES 2.6 (8) · PER_SHIPMENT_PROJECTION 45.2 (0) ·
GLOBAL_FINANCE_PROJECTIONS 3.5 (0) · SECONDARY_WORKSPACES 2.8 (3) · PAYLOAD_VERSION 11.5 (0) ·
OTHER 2.8 · SERIALIZATION (json proxy) 10.0. Payload ≈ 767 KB.

### The measured root cause

Local CPU is ~100 ms per interaction and is NOT what the Owner feels. The post-action path issued
**27 (translate) / 39 (write) sequential MongoDB round-trips** — in production every one of them is
a Streamlit-Cloud ↔ Atlas network wait, i.e. `round-trips × RTT` (≈ 0.8–1.6 s at 20–40 ms RTT).
Inside the ONE build (26 ops) nine were avoidable duplicates of reads the same render had already
done: `customers` ×2, `contracts` ×2 **+ one `contracts.find_one` per contract (N+1)**, `quotes` ×2,
`authority_agents` ×3, `docgen_documents` ×2 — the C1 payload and the partner-context slice re-read
what `build_view_model` already held. The remaining 17 reads are all independent of one another
yet were awaited one after another.

`FULL_VM_BUILD_HOTSPOT` (CPU, local): PER_SHIPMENT_PROJECTION ≈ 45 ms, DASHBOARD_VIEWS ≈ 14 ms,
`repair_data` inside LOAD_SHIPMENTS ≈ 12 ms, PAYLOAD_VERSION ≈ 12 ms — left untouched (correct,
not duplicated; not the felt latency).

### BEFORE at a modeled 20 ms round trip (same harness, `LOGI_PERF_RTT_MS=20`), median of 3

| Interaction | TOTAL_SERVER_MS | READBACK | BUILD | POST_ACTION_SERVER_MS |
| --- | --- | --- | --- | --- |
| translate_text | 697.8 | — | 653.9 | 674.7 |
| shipment_field_save | 1044.6 | 247.9 | 642.0 | 914.3 |
| payment_record | 1073.0 | 246.6 | 655.1 | 923.8 |

## Repair (priority order of the packet; zero semantic change)

1. **Remove duplicated reads inside the ONE build / reuse what the render already loaded**
   - `views/logi_c1.assemble_c1_payload(..., customers=, quotes=, contracts=, agents=, agreements=,
     companies=, docgen_documents=)` — optional render-local snapshot parameters; `build_view_model`
     passes its own reads. Standalone callers keep every original read.
   - `views/logi_c1.contract_projection(..., contract_index=)` + `_linked_shipment_ids()` — the
     per-contract `contracts.find_one` (N+1) becomes an in-memory lookup on the contract set the
     render already read (exact stored-`id` match, same `shipment_ids` field; every contract write
     path invalidates the contracts reader, so the set is the same the per-contract read saw).
   - `views/partner_context.partner_context_view(..., agents=)` — no third `authority_agents` read.
   - `views/logi_real_data.docgen_documents_by_shipment(documents=)` — the raw docgen map is read
     once in `_read_sources` and shared with C1.
   Build reads at N = 95: **26 → 17** (`contracts.find_one` 0; every reference collection ≤ 1).
2. **Stop awaiting independent reads one after another** — `views/logi_view_model._read_concurrently`:
   the independent reads of the same render (shipments ∥ references; then ledger, agents, timelines,
   docgen, shipment ids, attachments, agreements, companies, handbook notes, users) and the write
   readback's five reference/history reads are started together on a short-lived stdlib thread
   pool and joined before anything is projected. No cache, no skipped read, no background work, no
   state: the same readers run once per render, each keeps its own error handling, an exception is
   re-raised in the script thread exactly as before, the pool is gone before the function returns.
   Streamlit's script context is attached to the workers (`add_script_run_ctx`, Streamlit ≥ 1.51
   API, verified under a real `AppTest` runtime: `is_streamlit_runtime()` is True in the workers,
   cached readers and `session_state` behave as from the script thread). `_READ_WORKERS = 1`
   restores the one-after-another behaviour (operational fallback).
   Sequential round-trip depth: build 26 → 4 waves; readback 12 → 8; post-action critical path
   translate 27 → ≈5, writes 39 → ≈13.

Untouched on purpose: RBAC fresh auth (both reads), the authoritative readback contract
(`read_shipment` after the write → `_projection_for` → same projection call), audit, the
`load_shipment_ids` read (different set than `load_shipments`: archived included), the readback's
own ledger/docgen/agents reads (same code path as before), frontend (no UI/pending change).

## Evidence — AFTER (this branch), median of 3

RTT model 0 ms (pure local CPU):

| Interaction | TOTAL_SERVER_MS | READBACK (ops) | BUILD (ops) | POST_ACTION_SERVER_MS (ops) |
| --- | --- | --- | --- | --- |
| translate_text | 123.0 | — | 119.5 (17) | 119.9 (18) |
| shipment_field_save | 117.1 | 4.0 (12) | 107.6 (17) | 111.9 (30) |
| payment_record | 115.1 | 3.6 (12) | 107.2 (17) | 111.1 (30) |

Honest note: with no network at all (mongomock) the overlap buys nothing and costs ≈ 5–10 ms of
thread-pool overhead per interaction (+5–9 %). The repair targets round-trips; break-even is well
under 1 ms RTT, i.e. any real database link.

RTT model 20 ms:

| Interaction | TOTAL_SERVER_MS | READBACK | BUILD | POST_ACTION_SERVER_MS | Δ post-action |
| --- | --- | --- | --- | --- | --- |
| translate_text | 244.8 (was 697.8) | — | 200.7 (was 653.9) | 221.3 (was 674.7) | **−67.2 %** |
| shipment_field_save | 506.1 (was 1044.6) | 166.6 (was 247.9) | 189.2 (was 642.0) | 376.5 (was 914.3) | **−58.8 %** |
| payment_record | 521.1 (was 1073.0) | 166.3 (was 246.6) | 187.7 (was 655.1) | 374.3 (was 923.8) | **−59.5 %** |

Transport-independent figures: build ops −34.6 % (26 → 17); post-action ops translate −33 %
(27 → 18), writes −23 % (39 → 30); critical-path round-trips translate −81 %, writes −67 % — the
wall-clock gain converges to the latter as the real RTT grows. Wall-clock overlap proof, asserted in
the test at a 60 ms model: build 345 ms vs a serial floor of 1020 ms (17 ops); readback 487 ms vs
720 ms (12 ops). Output parity: concurrent build == sequential build byte-for-byte (`version`
included); C1 payload from the snapshot == standalone reads; in-memory contract links ==
`load_shipments_for_contract` per contract.

Sensitivity: the removed N+1 is one round-trip per contract; the fixture carries 3 contracts, every
additional production contract removes one more sequential round-trip from BEFORE.

`TIMING_EVIDENCE_CLASS=LOCAL_MODELED_RTT` — real Atlas RTT is unknown here; the 20 ms model is a
conservative same-region figure. DeepL provider time is measured separately by the mocked client
and is not claimed as reduced (`TRANSLATION_PROVIDER_TIME_SEPARATED=YES`).

## OE gate — "Không bị over engineering chứ?"

OE_VERDICT: NOT over-engineered. 4 production files, +264/−50 lines including docstrings; every
change is an optional parameter defaulting to the original read, one in-memory index, and one
30-line stdlib helper that overlaps reads the render already had to make. No Redis/Celery/queue/
new API/websocket/event bus/background service/new DB/second read model/microservice/frontend
framework; no cache, no optimistic UI, no skipped readback, no RBAC/audit change, no schema change.

## Tests

- `tests/test_logi_interaction_latency_finalize_02.py` — 8 passed (3 representative interactions
  with truthful-readback + op budgets, duplicate-translate guard, concurrent==sequential parity,
  overlap proof at a modeled RTT, C1/partner-context/docgen snapshot parity).
- PR50 invariants `tests/test_logi_interaction_latency_repair_01.py` — 20 passed
  (HANDLER_CALLS_PER_INTENT=1, VM_BUILDS_PER_INTENT=1, EXPLICIT_SECOND_RERUNS=0, fresh RBAC,
  authoritative readback, double-paid-call guard, no stale false success).
- `tests/test_logi_render_performance_01.py` 13 passed; `tests/test_translation_workspace.py`,
  `tests/test_deepl_translation.py`, `tests/test_deepl_translation_ui.py` 45 passed;
  `tests/test_logi_c2a_finance_actual.py`, `tests/test_financial_write_safety.py`,
  `tests/test_session_truth_repair.py`, `tests/test_logi_finance_actual_entry_parity_01.py`,
  `tests/test_entity_context.py`, `tests/test_gnt_and_docgen_reality_check.py`,
  `tests/test_logi_real_use_create_agent_01.py`, `tests/test_logi_uat_real_use_repair_02.py`,
  `tests/test_partner_context_workspace.py` 128 passed, 6 skipped (need
  `LOG_C02_RUN_MONGO_FIXTURES=1`); all `tests/test_logi_*.py` 364 passed.
- Pre-existing failures on base main, unrelated and untouched (FIELD_PATHS count pins / legacy
  create flow): `test_logi_cn_truck_type_persist_01::test_whitelist_gained_exactly_the_one_approved_key`,
  `test_logi_shipment_core_gaps_01::test_created_at_is_now_in_the_write_whitelist`,
  `test_logi_shipment_operational_data_v1::test_lightweight_create_starts_one_canonical_leg_and_navigable_detail_data`.
- Frontend untouched → TYPECHECK / BUILD / DOM_ACCEPTANCE not run (N/A).
- Lint (`ruff --select E9,F`): 4 findings, all pre-existing on main, none introduced.

## Safety

PRODUCTION_MUTATIONS=0 · PILOT_MUTATIONS=0 · PAID_PROVIDER_CALLS_IN_TESTS=0 (DeepL mocked) ·
SECRETS_CHANGED=NO · DEPLOYED=NO · logistics_db / tienthanhlog untouched. All measurements ran on
the isolated mongomock staging transport.

## Observations for Control Tower (not changed here)

- `save_customer_to_cloud` does not clear the 30 s `load_customers` `st.cache_data` (pre-existing
  freshness gap; contracts do invalidate).
- `core.financial_ledger.shipment_partner_position` scans every ledger row per shipment
  (O(shipments × ledger rows), `isinstance(x, typing.Iterable)` per row); ≈ 12 ms at the fixture's
  5 ledger rows, grows linearly with the ledger — a CPU follow-up if the ledger becomes large.
- The write readback still issues its ledger ×3 / agents / docgen reads inside `shipment_projection`
  (8 sequential waves); routing it through the same snapshot path the render uses would cut it to
  ≈ 4 — deliberately not done (readback code path kept identical).
- Perceived UX: the pending state reacts immediately already (PR50); no fake progress or phase text
  was added because the architecture cannot truthfully report "translating" vs "refreshing" per phase
  from a single rerun.
