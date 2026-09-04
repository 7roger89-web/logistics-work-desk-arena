# LOG-RBAC-SUPPORT-01 — Full operational access for Support Evidence Ledger

## Metadata

- Date: `2026-09-03`
- Plan: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-plan.md`
- Evidence: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-evidence.md`
- Benchmark: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-benchmark.md`
- Actual status: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct. Evidence is current to the isolated worktree `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`, whose baseline was fetched from `origin/main` at `c1c9468a814a2c0e56cefcf2851a2cadf46df436`. No Production or application database was used.

Evidence IDs are phase-scoped and stable. Source inspection and graph evidence are supporting evidence; behavior, persistence, mounted UI, security, and readback tests are the primary acceptance evidence.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: Fresh `git fetch origin main` moved `origin/main` from the stale local ref to `c1c9468`; isolated worktree was created from that ref on `codex/log-rbac-support-01`. The baseline HEAD is merge commit `c1c9468` with predecessor `78aeac3` titled `LOGISTICS: grant support full operational permissions`.
- `E0-P0A-SRC2`: `core/auth.py` is the single `ROLE_PERMISSIONS` authority. Current Support has the existing employee-facing permissions (`shipment_create`, `shipment_edit`, `customers`, `sales`, `sales_write`, `contracts`, `tariff`, `tracking`, `knowledge`, `shipment_360_read`, `entity_context`, `commercial_view`, `commercial_write`, `finance_view`, `finance_write`, `operations_write`, `proxy_payment`, `receivables`, `entrustment`, `reports`) and does not have Admin wildcard `*` or destructive/admin tokens.
- `E0-P0A-SRC3`: `views/contracts.py` routes all Contract mutation controls through `has_write_permission("sales_write")` at the UI, while `save_contract_to_cloud`, `save_contract_transaction`, and `save_contract_proxy_payment_atomic` in `core/database.py` had no service-side permission gate. The previous role matrix lacked `sales_write` for Support; the current matrix-only merge added it but did not reconcile the full writer/audit invariant.
- `E0-P0A-SRC4`: Sibling inspection found UI-only or missing writer authorization in Customer create/import/edit, Shipment detail save/actions, quotation create/persist, task/quick-note writes, lump-sum finance writes, and legacy proxy/entrustment writers. Admin-only route `Người Dùng` remains routed through permission `admin`; destructive shipment/customer/proxy actions are not Support permissions.
- `E0-P0A-ANV1`: Fresh Anvien index scanned 204 files, parsed 178 code files, and built 32,049 graph nodes / 37,412 relationships. `file-detail` relationship counts: `core/auth.py` 13 local / 3 inbound; `core/database.py` 144 local / 44 inbound; `views/contracts.py` 18 local; `views/quotations.py` 12 local; `views/customers.py` 0 local; `views/shipment.py` 0 local; `core/payment_logic.py` 3 local. File impact was MEDIUM for `core/auth.py` (10), CRITICAL for `core/database.py` (89), MEDIUM for `views/contracts.py` (7), LOW for `views/quotations.py` (5), and MEDIUM for `views/dashboard.py` (7); `_audit` symbol impact was CRITICAL across 22 upstream symbols. These are scope warnings requiring focused regression, not reasons to widen the change.
- `E0-P0A-TEST1`: Baseline `python -m pytest tests/test_logc15_auth_rbac.py tests/test_contracts.py tests/test_all_tabs_smoke.py -q` returned `30 passed, 2 failed`; both failures are stale assertions that Support cannot create shipments/quotes and is read-only on finance/admin. Baseline `python -m pytest tests/test_financial_write_safety.py tests/test_dashboard_financial_write_oracle.py tests/test_lg08_1_rbac_boundary.py -q` returned `10 passed, 6 skipped, 4 failed`; three direct-finance fixture failures lack an authenticated session after the existing backend gate, and one dashboard assertion is a pre-existing encoding/environment mismatch.
- `E0-P0A-BUILD1`: Baseline `python -m compileall -q core views app.py` completed without compiler output. Baseline worktree was clean after removing Anvien-generated metadata from the isolated worktree.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

### P1-A — Contract authorization and persistence

- `E1-P1A-SRC1`: `core/auth.py` now exposes `can_operate_business()` and the semantic `can_edit_contract()` wrapper over the existing `sales_write` matrix token. All Contract mutation controls in `views/contracts.py` use that helper. `core/database.py` now rejects unauthorized calls to `save_contract_to_cloud`, `save_contract_transaction`, and `save_contract_proxy_payment_atomic` before database mutation.
- `E1-P1A-IMPACT1`: Fresh Anvien post-edit index built 205 files / 179 parsed code files / 32,264 nodes / 37,671 relationships. Post-edit file details: `core/auth.py` 16 local / 3 inbound; `core/database.py` 146 local / 44 inbound; `views/contracts.py` 18 local; focused test files 34 and 25 local relationships. `_audit` impact remains CRITICAL across 22 symbols; Contract writer symbol impact is LOW in the current graph. `anvien detect-changes --repo ... --scope all --json` reported six changed files and 35 affected symbols in the bounded slice; no unrelated source file was edited.
- `E1-P1A-TEST1`: `python -m pytest tests/test_logc15_auth_rbac.py tests/test_log_rbac_support_01.py -q` → `31 passed`.
- `E1-P1A-DB1`: Fixture test created `CT-SUPPORT-01`, read it through `load_contracts`, updated value/note, wrote `TX-SUPPORT-01`, and read the updated Contract again. Persisted values and actor fields matched Support identity; unauthorized Viewer write left Contract and audit fixture collections empty.
- `E1-P1A-UI1`: Mounted `AppTest` opened the real `Hợp Đồng` route as Support, found no Streamlit exceptions, and verified `🚀 Lưu hợp đồng` was enabled. Route visibility test verified Support sees Contract/Customer/Shipment/Receivables permissions, does not see `admin`, Sale does not gain receivables, and Admin retains `admin` route.

### P1-B — Mounted operational writer gates and controls

- `E1-P1B-SRC1`: Fresh source sweep closed the existing operational writer gaps through the current permission layer. `core/database.py` now gates Shipment create/edit, Customer, Quotes, Agreements, rate-card/tariff workspace, Tasks/quick note, proxy/entrustment, and the Admin user APIs. `core/payment_logic.py` gates lump-sum Finance Actual; `core/debit_snapshot.py` gates reconciliation snapshot writes; `core/financial_ledger.py` gates canonical obligation/transaction/allocation/reversal/link writes. Matching UI controls in Customers, Shipment, Quotations, Agreements, Finance, Dashboard, Proxy Payment, Reconciliation, Sales/tariff, and Entrustment use existing permission helpers. Sale's matrix is unchanged from fresh `origin/main`.
- `E1-P1B-IMPACT1`: Final Anvien refresh indexed 478 files / 228 parsed code files / 37,656 graph nodes / 43,333 relationships. Final file-detail counts: `core/auth.py` 16 local / 7 inbound; `core/database.py` 185 local / 45 inbound; `core/financial_ledger.py` 84 local / 0 inbound / 35 outbound; `views/contracts.py` 18 local. Final `anvien detect-changes files --scope all` after generated-metadata cleanup reported 27 intended changed files (23 source/test + 4 plan docs), 76 affected items, risk `critical`; no generated `AGENTS.md`/`CLAUDE.md`/`.gitignore` change remains. `_audit` symbol impact is `35`, risk `CRITICAL`.
- `E1-P1B-TEST1`: `python -m pytest tests/test_log_rbac_support_01.py tests/test_logc15_auth_rbac.py -q` → `37 passed`; `python -m pytest tests/test_financial_write_safety.py -q` → `12 passed, 6 skipped, 2 subtests passed`; `python -m pytest tests/test_financial_ledger.py -q` → `13 passed, 1 skipped` independently; `python -m pytest tests/test_users_persistence.py -q` → `6 passed`; representative Customer/Quote/Agreement/Contract tests → `38 passed, 4 subtests passed`.
- `E1-P1B-UI1`: `python -m pytest tests/test_all_tabs_smoke.py -q` → `1 passed`; `python -m pytest tests/test_logc12_host_native_runtime.py -q` → `1 passed`; Support AppTest mounted the real `Hợp Đồng` route, found no exceptions, and confirmed `🚀 Lưu hợp đồng` is enabled. Shipment fixture UI/service coverage persists Pickup/Export and Import/Delivery fields through `save_shipment_atomic`.
- `E1-P1B-SEC1`: Support route visibility covers every non-admin route and excludes `admin`; Support negative tests reject Customer/Quote/Agreement/Entrustment/Proxy/Shipment destructive or unauthorized writes as applicable; Viewer is rejected before canonical Finance/Shipment writer access; Admin wildcard remains true; Sale retains its prior finance/receivables/admin exclusions.

### P1-C — Actor/audit and security

- `E1-P1C-SRC1`: `current_actor_context()` remains in `core/auth.py`; `_actor_context()`, `_audit()`, and `_save_document()` are the existing central path. Audit documents now retain `actor_user_id`, `actor_username`, `actor_role`, and UTC `created_at`; persisted business documents/action requests stamp canonical created/updated actor fields. Payment, correction, ledger, entrustment, and Debit snapshot writers retain the same identity context.
- `E1-P1C-IMPACT1`: Final Anvien `impact symbol _audit -u Function:core/database.py:_audit#8 -d upstream --include-tests` returned `impactedCount=35`, `risk=CRITICAL`; central `core/database.py` file-detail returned 185 local / 45 inbound relationships. This is a shared-boundary warning handled by focused rollback/idempotency tests.
- `E1-P1C-DB1`: Support fixture Contract create/update/reload, Shipment create/edit/reload, canonical Finance transaction, and operational collection writes read back canonical user ID/role and audit timestamps. Caller-supplied display actor is not allowed to replace authenticated Support identity.
- `E1-P1C-TEST1`: Independent `financial_write_safety` and `financial_ledger` suites pass with rollback/idempotency/reversal coverage; Support negative Admin API/destructive tests pass; focused RBAC/Contract suite passes. Existing protected-history assertions remain green in the affected suites.
- `E1-P1C-SEC1`: `ROLE_PERMISSIONS["admin"] == {"*"}`; Support has no `*`, `admin`, user-delete, shipment-delete, customer-delete, proxy-delete, or knowledge-delete token. User service `save_user` permits only first-admin bootstrap without an authenticated user; update/delete require Admin wildcard. No source path was added for secrets/deployment/configuration mutation.
- `E1-P1C-BUILD1`: `python -m compileall -q core views app.py tests` → pass. Full `python -m pytest tests -q` → `347 passed, 7 skipped, 27 failed, 6 errors, 12 subtests passed`; residual failures/errors are baseline/environment issues (missing Owner workbook, missing `python-calamine`, historical hash drift, cp1252 source reads, missing Mongo config, stale dashboard/runtime assertions), not affected Support writer gates. Safe Preview credentials were not supplied, so browser validation remains pending.

## E2 - P2 Evidence

Matching plan item(s): `Pn-A`, `Pn-B`, `Pn-C`

- `E2-Pn-A`: Supervisor review completed on the committed candidate. Report `reports/supervisor/rp_supervisor_260903_184101_by_gpt-5-codex_log-rbac-support-01.md` records exactly one verdict: `PASS`.
- `E2-Pn-B`: Dead-work cleanup completed: Anvien-generated `AGENTS.md`, `CLAUDE.md`, and `.gitignore` changes were removed; no temporary fixture or rejected approach is in the committed diff. Accepted reports/plan/evidence artifacts remain.
- `E2-Pn-C`: Closure artifacts include the coder report, Supervisor report, today's notes/decisions log, final validation results, and candidate SHA. A post-closure Anvien refresh indexed 481 files / 228 parsed code files / 37,695 nodes / 43,372 relationships; the remaining working-tree detect scope is documentation-only. No Production or application-database mutation occurred.

## Closure Evidence

- `E-CLOSE-1`: Candidate `f25347daac3d53c07f005ca49c3d9521de59351d` is committed on `codex/log-rbac-support-01`; Supervisor report is `PASS`; final Anvien compare detect found 27 intended files before closure artifacts were added, and post-closure source diff remains limited to this plan's source/tests/docs/reports. Working tree is clean after closure commit. Browser Preview remains pending by explicit credential gate. `PRODUCTION_MUTATIONS=0`; `PRODUCTION_DATA_MUTATIONS=0`; no promotion was performed.
