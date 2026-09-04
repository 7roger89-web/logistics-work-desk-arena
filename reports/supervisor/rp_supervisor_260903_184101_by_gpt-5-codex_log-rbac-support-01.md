# Supervisor Report: LOG-RBAC-SUPPORT-01 full operational access

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260903_184101_by_gpt-5-codex_log-rbac-support-01.md`
- Review time: `260903 184101 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`
- Scope reviewed: `origin/main` `c1c9468` through candidate `f25347daac3d53c07f005ca49c3d9521de59351d`; commits `b831a6d` and `f25347d`
- Claim reviewed: authenticated Support can use the existing employee-facing operational workflows, including Contract create/edit/save/reopen, while Admin-only security/destructive boundaries and Sale's effective permissions remain intact.
- Authority used: latest Owner request `LOG-RBAC-SUPPORT-01`, repository `AGENTS.md`, active plan/evidence/benchmark/actual-status files, source, tests, and Anvien graph evidence.
- Related artifacts: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/`; candidate commits `b831a6d`, `f25347d`.

## Executive Summary

- Problem: the original Support Contract block came from the `sales_write` permission missing from the predecessor Support matrix; the fresh `origin/main` matrix-only merge had removed the visible denial but left sibling service gates, actor stamping, and focused proof incomplete.
- Decision: PASS. The reviewed candidate closes the mapped route/control/service/repository authorization family, preserves audit/idempotency/correction behavior, and has fresh source, graph, fixture, and mounted AppTest evidence.
- Required outcome: accepted as a development candidate only. Browser Preview remains pending without safe staging credentials; no Production promotion is authorized.

## Source-Level Clearance Notes

- `core/auth.py`: clear. `can_operate_business()` and `can_edit_contract()` are semantic wrappers over the existing `ROLE_PERMISSIONS` authority; `current_actor_context()` binds user ID, username, and role. `git diff c1c9468 HEAD -- core/auth.py` shows no Sale permission-matrix change.
- `core/database.py`: clear. `_require_business_permission()` is the existing central repository guard (`core/database.py:78-84`); `_audit()` records canonical actor fields and UTC time (`core/database.py:403-423`); Shipment, Customer, Quote, Agreement, Task, proxy, entrustment, and Admin user writers are guarded and/or audited (`core/database.py:438-1682`). Unauthorized Support/Admin tests prove no mutation before access.
- `core/debit_snapshot.py`: clear. Reconciliation snapshot persistence checks `receivables` and stamps `prepared_by_user_id`/role plus supersede metadata (`core/debit_snapshot.py:297-379`).
- `core/financial_ledger.py`: clear. Canonical obligation/transaction/allocation/link/reversal writers fail closed through `_require_finance_write()` (`core/financial_ledger.py:64-72`, `504-976`) and retain request identity, transaction boundaries, corrections, provenance, and actor fields.
- `core/payment_logic.py`: clear. Lump-sum Finance Actual is permission-gated before DB access and retains transaction/idempotency plus actor metadata (`core/payment_logic.py:78-201`).
- `views/contracts.py`: clear. Contract shipment links, contract finance rows, proxy payment, create/save, and terms controls use `can_edit_contract()` (`views/contracts.py:198-405`).
- `views/customers.py`: clear. Import/create/edit controls use the existing `customers` permission; storage remains separate (`views/customers.py:14-169`).
- `views/dashboard.py`: clear for the changed invariant. Task/note controls use `shipment_edit`; Getfly import reaches guarded Shipment persistence; destructive delete remains separately permissioned (`views/dashboard.py:52-123`, `511-575`, `718-727`, `898-927`).
- `views/entrustment.py`: clear. Existing Support entrustment controls are enabled from the `entrustment` permission and persist through the guarded batch writer (`views/entrustment.py:49-51`, `76-312`).
- `views/finance.py`: clear. Finance Actual receipt action uses `finance_write` and stops before the handler when unauthorized (`views/finance.py:91-117`).
- `views/partner_reconciliation.py`: clear. Debit snapshot save/regenerate controls use `receivables` (`views/partner_reconciliation.py:292-390`).
- `views/proxy_payment.py`: clear. Ordinary proxy payment save uses `proxy_payment`; archive remains separate (`views/proxy_payment.py:93-213`).
- `views/quotations.py` / `views/agreements.py`: clear. Existing Sales/commercial permissions are reused for quote and agreement controls; quotation remains an estimate and does not post Finance Actual (`views/quotations.py:191-295`, `views/agreements.py:204-435`).
- `views/sales.py` / `views/tariff.py`: clear. Existing Sales rate-card and tariff/CBPG writers are enabled for roles already carrying the corresponding route token, including Support (`views/sales.py:78-113`, `views/tariff.py:149-362`).
- Tests/docs: clear as acceptance evidence. Focused fixtures were updated only where the new service guards require authenticated actors; no Production fixture or application DB was used.

## Evidence Checked

Passed:

- Fresh source/commit inspection: candidate `f25347d` is clean, has 27 intended files in its commit, and contains no Anvien-generated `AGENTS.md`, `CLAUDE.md`, or `.gitignore` changes.
- Anvien current graph: 478 scanned files, 228 parsed code files, 37,656 nodes, 43,333 relationships; final compare detect reports 27 changed files, 76 affected items, risk `critical`. `_audit` upstream impact is 35, risk `CRITICAL`; this was covered by focused regression.
- `python -m pytest tests/test_log_rbac_support_01.py -q` → `10 passed`.
- `python -m pytest tests/test_logc15_auth_rbac.py -q` → `27 passed`.
- `python -m pytest tests/test_financial_write_safety.py -q` → `12 passed, 6 skipped, 2 subtests passed`.
- `python -m pytest tests/test_financial_ledger.py -q` → `13 passed, 1 skipped`.
- `python -m pytest tests/test_users_persistence.py -q` → `6 passed`.
- `python -m pytest tests/test_contracts.py tests/test_quotations.py tests/test_agreements_api.py tests/test_commercial_agreements.py -q` → `38 passed, 4 subtests passed`.
- `python -m pytest tests/test_all_tabs_smoke.py tests/test_logc12_host_native_runtime.py -q` → `2 passed`.
- `python -m pytest tests/test_log_c05_snapshot_write_oracle.py tests/test_log_c05_partner_desk_write_oracle.py tests/test_partner_reconciliation_desk_write_oracle.py tests/test_historical_review_ui.py tests/test_tariff.py -q` → `16 passed`.
- `python -m compileall -q core views app.py tests` → pass.
- Contract AppTest mounted the real `Hợp Đồng` route as Support, reported no Streamlit exceptions, and found `🚀 Lưu hợp đồng` enabled. Fixture readback proved Contract create/update/reopen, Shipment Pickup/Export and Import/Delivery field persistence, canonical Finance transaction, customer/quote/agreement/proxy/entrustment/tariff writers, and actor metadata.

Failed:

- Full `python -m pytest tests -q` → `347 passed, 7 skipped, 27 failed, 6 errors, 12 subtests passed`. Fresh failure review identifies missing `/home/ubuntu/upload/danhsachdonhang-.xlsx`, missing `python-calamine`, historical source-hash drift, cp1252 reads of UTF-8 source, missing Mongo configuration, and pre-existing dashboard/entity/runtime assertions. These are outside the changed Support writer invariant; the affected focused suites above pass.
- Dashboard financial oracle still has its known environment/UI-text mismatch; it does not record a financial write. LG08 source-safety failures are cp1252 decode failures before assertions, not authorization or mutation failures.

Not run:

- Safe Preview/browser verification: no staging Preview credentials were supplied. The Owner contract explicitly permits source and mounted-runtime verification with this gate reported pending.
- Production, `logistics_workdesk_logc14`, `logistics_db`, deployment, promotion, merge, and Docker runtime: not run and not authorized.

## Invariant Closure

- affected invariant: Support permission must flow from route visibility through UI control, validation, service/repository writer, actor/audit metadata, and protected-finance rules.
- sibling surfaces checked: `ROUTES`/route guard; Contract forms and linking; Customer; Shipment/Pickup/Export/Import/Delivery/GNT/Getfly entrypoints; quotations/agreements/factory payload; tasks/quick note; Finance Actual; payment/correction; proxy/entrustment; Debit reconciliation; canonical Finance Ledger; Admin user service; focused fixtures and mounted AppTest.
- residual unverified same-invariant surfaces: none within the changed writer family. Historical staging remains a separate metadata-only subsystem and was not refactored; no canonical Finance writer is reached by it. Browser presentation proof is the explicitly reported pending gate, not a claimed PASS.

## Overall Evaluation

The candidate is acceptable as a development implementation candidate. It addresses the original Support Contract authority mismatch and the same-invariant service/UI gaps without widening Sale, adding an RBAC subsystem, changing schema/migrating data, or touching Production. The full suite is not globally green because of independently reproduced repository/environment residuals, but all affected Support/RBAC/Contract/financial-safety/mounted checks pass. This is a technical PASS only; it is not Owner approval, merge, deployment, or Production promotion.
