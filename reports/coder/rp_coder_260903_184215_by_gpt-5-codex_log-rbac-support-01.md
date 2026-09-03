# Coder Report: LOG-RBAC-SUPPORT-01 — Full operational access for Support

Date: `2026-09-03`  
Workspace: `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`  
Branch: `codex/log-rbac-support-01`  
Baseline: fresh `origin/main` `c1c9468a814a2c0e56cefcf2851a2cadf46df436`  
Implementation candidate: `f25347daac3d53c07f005ca49c3d9521de59351d`

## Scope and authority

Implemented only the Owner-approved Support operational-access scope. The existing `ROLE_PERMISSIONS` matrix remains the policy source; no new RBAC framework, authentication rewrite, schema migration, route, deployment, merge, or Production operation was added. Owner's dirty checkout at `D:\Logistics_App_GitHub` was not modified; all implementation and fixtures stayed in the isolated worktree.

## Required report

### ROOT_CAUSE_CONTRACT_SUPPORT_BLOCK

The predecessor Support matrix did not include `sales_write`, while every Contract create/edit/link/finance/terms control in `views/contracts.py` used that write gate. The current fresh `origin/main` already contains PR #8, which adds the Support operational matrix token and removes the visible denial, but it was only a matrix delta: Contract service writers and sibling operational repository writers were still not consistently protected or actor-stamped. The candidate closes the complete UI → validation → service → repository path and proves durable readback.

### RBAC_FILES_CHANGED

Production source groups changed:

- `core/database.py` — central business writer gates, actor metadata, audit calls, Admin user-service guard.
- `core/debit_snapshot.py` — `receivables` service gate and actor metadata.
- `core/financial_ledger.py` — `finance_write` gate for obligation/transaction/allocation/link/reversal writers and actor metadata.
- `core/payment_logic.py` — `finance_write` gate for lump-sum receipt/allocation and central audit/actor metadata.
- `views/contracts.py`, `views/customers.py`, `views/dashboard.py`, `views/entrustment.py`, `views/finance.py`, `views/partner_reconciliation.py`, `views/proxy_payment.py`, `views/quotations.py`, `views/sales.py`, `views/shipment.py`, `views/tariff.py` — existing controls switched to canonical business helper/disabled state where required.
- `core/auth.py` was changed in the prior candidate checkpoint `b831a6d` to add `can_operate_business`, `can_edit_contract`, and `current_actor_context`; its Sale permission matrix is unchanged versus `origin/main`.

Test/evidence groups changed:

- `tests/test_log_rbac_support_01.py`, `tests/test_financial_write_safety.py`, `tests/test_financial_ledger.py`, `tests/test_users_persistence.py`, `tests/test_log_c05_snapshot_write_oracle.py`, `tests/test_agreements_api.py`, `tests/test_commercial_agreements.py`, `tests/test_quotations.py`.
- `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/` plan, actual-status, benchmark, and evidence ledger.

Anvien-generated `AGENTS.md`, `CLAUDE.md`, and `.gitignore` changes were removed before commit.

### SUPPORT_CONTRACT_CREATE

PASS — Support fixture called `save_contract_to_cloud` with a valid Contract payload and persisted it to an isolated fake repository.

### SUPPORT_CONTRACT_EDIT

PASS — Support updated persisted Contract value/note through the same writer; UI uses `can_edit_contract()`.

### SUPPORT_CONTRACT_SAVE

PASS — `🚀 Lưu hợp đồng` is enabled in mounted Support AppTest; Contract transaction/proxy/link/terms controls use the same helper; unauthorized service call fails before repository mutation.

### SUPPORT_CONTRACT_REOPEN

PASS — `load_contracts()` readback after create/update returned the changed value/note and actor fields; proof is not session-state-only.

### SUPPORT_CUSTOMER

PASS — Customer import/create/edit controls and `save_customer_to_cloud` use the existing `customers` permission; isolated writer test succeeds for Support and Viewer is denied.

### SUPPORT_SHIPMENT

PASS — `shipment_create`/`shipment_edit` controls and `save_shipment_atomic` are guarded; fixture creates, edits, reloads, and verifies actor fields.

### SUPPORT_PICKUP_EXPORT

PASS — Existing Shipment Pickup/Export fields remain on the normal Shipment writer path; fixture readback verifies booking/pickup data.

### SUPPORT_IMPORT_DELIVERY

PASS — Existing Getfly/import and Import/Delivery fields reach guarded Shipment persistence; fixture readback verifies arrival/delivery data. No Getfly data or Production file was used.

### SUPPORT_DOCUMENTS_TASKS

PASS — Shipment document/GNT fields remain on the guarded Shipment path; Dashboard task/quick-note create/toggle writers use `shipment_edit` and task mutations are audited.

### SUPPORT_FINANCE_ACTUAL

PASS — Direct Shipment payment, correction/reversal, lump-sum receipt, and canonical Finance Ledger writes use `finance_write`. Estimate/commercial data is not promoted to Finance Actual.

### SUPPORT_PAYMENT_RECONCILIATION

PASS — Proxy/entrustment writers use their existing permissions; Debit Draft snapshot write/regenerate uses `receivables`; rollback/idempotency/correction tests remain green.

### ADMIN_FULL_ACCESS

PASS — `ROLE_PERMISSIONS["admin"] == {"*"}` and Admin helper assertions remain true.

### SALE_PERMISSION_DRIFT

PASS — `git diff c1c9468 HEAD -- core/auth.py` contains helper/actor additions only; the `ROLE_PERMISSIONS["sale"]` block is unchanged. Sale continues to lack `finance_write`, `receivables`, Admin, and destructive tokens.

### ADMIN_ONLY_FUNCTIONS_RETAINED

PASS — Support has no wildcard or user/security/destructive tokens. `Người Dùng` route requires `admin`; `save_user` permits only first-admin bootstrap without an authenticated user, while user update/delete require Admin wildcard. Shipment/customer/proxy/knowledge destructive writers reject Support before mutation. No secrets/config/deploy/promotion writer was added.

### AUDIT_TRACEABILITY

PASS — `_audit` records `actor_user_id`, `actor_username`, `actor_role`, and UTC timestamp. `_save_document`, Shipment, payment, correction, canonical ledger, entrustment, and Debit snapshot paths stamp canonical actor fields. Authenticated session identity overrides arbitrary display-name/caller strings; existing request identity/idempotency and correction/reversal semantics remain.

### TEST_RESULTS

Fresh candidate commit verification:

- `python -m pytest tests/test_log_rbac_support_01.py -q` → `10 passed`.
- `python -m pytest tests/test_logc15_auth_rbac.py -q` → `27 passed`.
- `python -m pytest tests/test_financial_write_safety.py -q` → `12 passed, 6 skipped, 2 subtests passed`.
- `python -m pytest tests/test_financial_ledger.py -q` → `13 passed, 1 skipped`.
- `python -m pytest tests/test_users_persistence.py -q` → `6 passed`.
- `python -m pytest tests/test_contracts.py tests/test_quotations.py tests/test_agreements_api.py tests/test_commercial_agreements.py -q` → `38 passed, 4 subtests passed`.
- `python -m pytest tests/test_all_tabs_smoke.py tests/test_logc12_host_native_runtime.py -q` → `2 passed`.
- `python -m pytest tests/test_log_c05_snapshot_write_oracle.py tests/test_log_c05_partner_desk_write_oracle.py tests/test_partner_reconciliation_desk_write_oracle.py tests/test_historical_review_ui.py tests/test_tariff.py -q` → `16 passed`.
- `python -m compileall -q core views app.py tests` → pass.
- Full `python -m pytest tests -q` → `347 passed, 7 skipped, 27 failed, 6 errors, 12 subtests passed`. Residuals are missing Owner workbook/dependency, historical fixture hash drift, cp1252 source reads, missing Mongo configuration, and existing dashboard/entity/runtime assertions. No affected Support focused suite fails.

### COMPILE

PASS — `python -m compileall -q core views app.py tests` returned exit code 0.

### MAIN_CANDIDATE_SHA

`f25347daac3d53c07f005ca49c3d9521de59351d` (`fix: close support operational authorization boundaries`), based on fresh `origin/main` `c1c9468`.

### PRODUCTION_MUTATIONS=0

0. No Production instance was opened, no Production API was called, and no deployment/promotion/merge/push was performed.

### PRODUCTION_DATA_MUTATIONS=0

0. No `logistics_workdesk_logc14`, `logistics_db`, or Production Mongo write was performed. Tests used in-memory fixtures; opt-in Mongo fixtures remained skipped because no safe Mongo credentials were configured.

## Runtime boundary

Mounted Streamlit/AppTest proof is available for Support Contract and the smoke/host-native flows. Safe Preview browser validation is `PENDING_SAFE_PREVIEW_CREDENTIALS`; no Production runtime was used as a substitute. This is a development candidate, not release/promotion approval.

## Terminal

`LOG_RBAC_SUPPORT_01_FULL_OPERATIONAL_ACCESS_VERIFIED_CANDIDATE`

STOP. Do not promote to Production automatically.
