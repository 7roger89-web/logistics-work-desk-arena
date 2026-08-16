# LOG-C01 Dashboard Detail Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-actual-status.md`

## Evidence Rules

Evidence is current, source-backed, and specific to LOG-C01. Historical reports are leads only; current source/runtime checks determine classification. No secret value, customer row, payment value, or raw browser credential is stored in this ledger. Browser evidence is read-only and must not be confused with DB write persistence proof.

### Evidence ID Naming

Evidence IDs use the required phase/item/kind format. `E0` is baseline/recovery and `E1` is the selected dashboard phase.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-P2P1`: `python .p2p/system/scripts/doctor.py --root .` returned `RESULT: PASS`; skills, eight custom profiles, optional Aesthetica independence, agent limit 8, governance drift, release readiness, installed foundation, and Decision Trace checks passed.
- `E0-P0A-P2P2`: `.p2p/system/VERSION` and `.p2p/system/release.json` identify installed P2P `8.4.7-C-codex.15`; the release metadata records a project-scoped legacy-system upgrade and protected state hash.
- `E0-P0A-P2P3`: local `.codex/agents` contains exactly eight canonical profiles plus separate `p2p-aesthetica.toml`; no full quorum was spawned for this task.
- `E0-P0A-ANV1`: `anvien analyze --force` completed with 76 files scanned, 52 parsed code files, 0 parse failures, and a current graph at `.anvien/graph.json`; `anvien status` reports the Logistics repository up-to-date at commit `b01fceb`.
- `E0-P0A-ANV2`: `anvien file-detail views/dashboard.py --repo Logistics-Pro-AI --json` reports 117 symbols, 7 local relationships, 434 unresolved references, high risk, and current/non-stale graph evidence; file impact reports 1 affected file and 2 direct file relationships, while downstream symbol impact reports 6 direct references and 1 affected module.
- `E0-P0A-STATE1`: `p2p_workflow.py inspect` found the project root, 2,826 files, P2P installed, project policy/eval present, and RAG not applicable; `bootstrap` created only missing project profile/status/trusted-evidence/execution-ledger state and reused the existing policy/eval suite with 18 cases and validation PASS.
- `E0-P0A-RUN1`: local Streamlit runtime at `http://127.0.0.1:8516` returned health `200` with body `ok`; the dashboard rendered in the connected in-app Browser as Local Admin.
- `E0-P0A-UI1`: fresh current runtime flow selected `Tháng trước` and showed `01/07/2026`–`31/07/2026`; after one click on the visible July shipment the button became active but no detail heading appeared; after a second click the detail heading rendered. This is a current reproduction of the historical first-click finding.
- `E0-P0A-SRC1`: current `views/dashboard.py` reads `active_sid` before the list button and assigns `active_shipment_id`/`dashboard_active_shipment_id` inside the row handler without a rerun; the existing comment explicitly says nested rerun is avoided.
- `E0-P0A-PAY1`: current `core/payment_logic.py` uses Mongo session/transaction, idempotency key, version checks, receipt and audit writes for lump-sum customer payment; this is source evidence of a safer bounded path, not durable runtime proof.
- `E0-P0A-PAY2`: current `views/contracts.py` saves a proxy payment and contract transaction through two separate calls (`save_proxy_payment(payment) and save_contract_transaction(tx)`), so the Contract proxy flow remains partial/non-atomic if the second write fails.
- `E0-P0A-SEC1`: current configuration inspection found secret-bearing `.streamlit/secrets.toml` and tracked `google_key.json`; values are intentionally not recorded here.
- `E0-P0A-OPS1`: current source still has `AUTH_REQUIRED` default/secret path set to false in the local configuration and `core/auth.py` grants Local Admin when auth is not required; current `start.sh` launches `bot_service.py` and passes `$PORT`, while `requirements.txt` does not declare the imported `telebot`/`google.generativeai` modules.
- `E0-P0A-PERSIST1`: current reports and source show Mongo read/ping success and 24 historical unit tests, but no current safe durable write -> reload -> read-back evidence; this remains `UNKNOWN`/unproven.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`

- `E1-P1A-SRC1`: current `views/dashboard.py:366-371` preserves both existing selection aliases and calls `st.rerun()` immediately after assigning the clicked shipment. No detail renderer, filter, save, delete, or database code changed in this slice.
- `E1-P1A-IMPACT1`: after the source edit, `anvien analyze --force` completed with 81 files scanned, 53 parsed code files, 0 parse failures, 6,506 graph nodes, and 7,215 relationships. Refreshed file-detail remains current/non-stale with 117 symbols, 7 local relationships, 435 unresolved references, and high risk; the pre-edit impact scope remains one directly affected file plus six downstream symbol references.
- `E1-P1A-UI1`: after restarting the verified local Streamlit process, the read-only in-app Browser flow at `http://127.0.0.1:8516/` selected `Tháng trước`, expanded the visible July shipment, and observed the `📂` detail heading after one click; clicking `❌` returned to the filtered list with no detail heading. Result: `detailAfterOneClick=true`, `detailAfterClose=false`, `readOnly=true`. No save/delete/payment control was submitted.
- `E1-P1A-TEST1`: reusable flow `playwright/log_c01_dashboard_detail_flow.mjs` executed through the installed Browser/Playwright surface. It asserts the real Streamlit DOM state rather than a mock page and records the shipment label, one-click detail state, close state, and read-only boundary.
- `E1-P1A-TEST2`: `python -m compileall -q core views tests` exited 0; `python -m unittest discover -s tests -v` ran 24 tests and completed `OK` in 3.609 seconds. Runtime health remained HTTP 200 with body `ok`.
- `E1-P1A-DETECT1`: `anvien detect-changes --repo Logistics-Pro-AI --scope all` ran after the slice. The graph is current, but the worktree contains broad pre-existing user changes and the target dashboard file is already a large dirty rewrite; no isolated commit was made and no unrelated hunk was staged.
- `E1-P1A-P2P1`: final `python .p2p/system/scripts/doctor.py --root .` returned `RESULT: FAIL` because its governance-drift check reports unlocked runtime files under `.agents/skills` and a changed protected `P2P_INSTRUCTIONS_BLOCK`; the canonical eight profiles, optional Aesthetica separation, agent limit 8, helpers, foundation 8/8, and decision-trace checks still passed. The separate `p2p_governance.py drift` command reports the same FAIL. No P2P source or checkout was modified by this task.

## E2 - P2 Evidence

Matching plan item(s): `Pn-A`, `Pn-B`, `Pn-C`

- `E2-PnA-SUP1`: independent supervisor report [rp_supervisor_260814_log_c01_dashboard_detail.md](../../../reports/supervisor/rp_supervisor_260814_log_c01_dashboard_detail.md) returned `REJECT` for overall closure while confirming the bounded P1-A local behavior.
- `E2-PnB-CLEAN1`: the verified local Streamlit process on port 8516 was stopped; the two exact temporary LOG-C01 runtime logs were removed; the plan, QA, coder, and supervisor artifacts were retained as evidence.
- `E2-PnC-CLOSE1`: all four plan files were refreshed, no file was staged or committed, no release/deployment ran, and the terminal state is `BLOCKED`.

## Closure Evidence

The bounded local dashboard behavior is evidenced as complete. Overall Logistics readiness is blocked: final P2P governance drift is FAIL, Docker acceptance is unavailable, the dirty worktree prevents a safe isolated commit, and the credential/auth, worker, Contract proxy atomicity, and durable persistence findings remain outside this slice. Supervisor verdict: `REJECT`.
