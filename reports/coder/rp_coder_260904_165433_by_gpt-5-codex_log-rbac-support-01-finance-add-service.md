# Coder Report — LOG-RBAC-SUPPORT-01 Finance Add Service

Status: PASS for the bounded Support Finance service-entry flow.

## Git reference

- Worktree: `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`
- Branch: `codex/log-rbac-support-01`
- Pre-fix HEAD: `921bf119db255b7a8ad61fc6712b1802c96b6e50`
- The implementation was changed only after the headed local reproduction exposed concrete runtime blockers.

## Invariant Family Map

- Family: Support employee-facing Finance service entry for a shipment.
- Authority / SSOT: `core/auth.py::ROLE_PERMISSIONS`; the existing Finance tab in `views/shipment.py`; the existing `save_shipment_atomic` writer in `core/database.py`.
- Sibling surfaces checked: Support route visibility, Support operational writers, canonical actual-finance writer, admin-user writer, destructive shipment/customer/knowledge/payment writers, and Sale receivables visibility.
- Forbidden fallback: no new permission layer, no admin wildcard for Support, no transaction fallback, no local mock persistence, and no alternate Finance subsystem.
- Verification matrix: headed Support UI trigger; Add Service rerun retention; existing writer fixture; real local Mongo transaction-backed save and reload; focused RBAC/admin-boundary tests.

## Reproduced root causes

1. The `🎯 GIAO VIỆC MỚI` dialog decorator was attached to `_get_current_user_id`, a helper called during every dashboard render. The modal therefore opened over the shipment Finance tab and intercepted the visible `➕ Thêm Dịch vụ` button. The button was enabled, so this was a UI-state/overlay defect, not an RBAC denial.
2. The Add Service handler appended to the repaired deep-copy of the shipment and immediately reran. Without updating the existing session shipment map, the new row disappeared on rerun.
3. The existing writer sent creation-provenance fields in both `$set` and `$setOnInsert`. MongoDB rejected the real Save with `ConflictingUpdateOperators`. This was a concrete runtime writer defect on the same flow.

## Surgical repair

- `views/dashboard.py`: move the existing dialog decorator from `_get_current_user_id` to `quick_assign_task_dialog`.
- `views/shipment.py`: retain the newly added service row in the existing `st.session_state.db_shipments` map before rerun.
- `core/database.py`: exclude immutable `created_by`, `created_by_user_id`, and `created_by_role` from `$set`; retain them in `$setOnInsert`.
- `tests/test_log_rbac_support_finance_service.py`: focused regression for the dialog binding and Support Add Service row retention.

No permission file was changed. No new framework or fallback was added.

## Verification evidence

- `python -m compileall -q core/database.py views/dashboard.py views/shipment.py tests/test_log_rbac_support_finance_service.py` -> PASS.
- `python -m pytest -q --disable-warnings tests/test_log_rbac_support_finance_service.py tests/test_financial_write_safety.py::ShipmentOperationalFixtureTests::test_support_can_create_edit_and_reload_export_import_fields tests/test_log_rbac_support_01.py::SupportContractPersistenceTests::test_support_route_visibility_keeps_admin_only_user_route_hidden tests/test_log_rbac_support_01.py::SupportOperationalWriterTests::test_support_cannot_use_admin_only_destructive_writers tests/test_log_rbac_support_01.py::SupportOperationalWriterTests::test_support_can_write_canonical_finance_actual_but_viewer_cannot` -> `6 passed`.
- `python scripts/check_config.py` -> PASS; configured database reported as `logistics_dev`, local Mongo connection OK; no secret values recorded.
- Mongo local runtime -> service Running, loopback listener on `127.0.0.1:27017`, replica set `logistics-rs`, one member `127.0.0.1:27017`, state `PRIMARY`, writable primary true.
- Streamlit health -> `http://127.0.0.1:9501/_stcore/health` returned HTTP 200; listener remains loopback-only.
- Headed Support flow -> Finance tab opened; Add Service was visible and enabled with no dialog overlay; one fake service was added to shipment `SHP-20260904-011` using note `TEST LOCAL SERVICE`, cost `100000`, price `150000`; Save completed without the transaction or update-conflict error.
- Real local readback -> the same `logistics_dev` shipment contains one matching service row with the expected service, cost, price, note, and Support updater role. After `Reload Data`, the Finance inputs still show the saved values.
- Support boundary -> Support has `finance_view`, `finance_write`, and `shipment_edit`; Support has no wildcard/admin route; the shipment delete control is disabled. Sale retains no `receivables` permission.
- Anvien -> refreshed graph on the exact worktree; changed-flow detection remained limited to the three implementation files plus the focused test/evidence artifacts. Anvien reported medium aggregate change risk and existing unresolved graph bindings; no additional scope was inferred from those gaps.

Evidence screenshots:

- `reports/supervisor/evidence_support_finance_service_readback.png`
- `reports/supervisor/evidence_support_finance_service_row.png`

## E2E Verification

  [PASS] Compiled: focused `compileall` -> completed successfully.
  [PASS] Runtime: local Streamlit + local Mongo replica-set health -> service/health checks passed.
  [PASS] Happy path: Support → shipment → Finance → Add Service → edit → Save → Reload Data → readback -> passed.
  [PASS] Edge case: Support admin route/destructive boundaries and Sale receivables boundary -> focused tests passed.

## Scope limits

- The user explicitly prohibited broad repository testing; the broad suite was not run.
- The normal CUA/agent-browser kernels were unavailable on this Windows host, so the existing visible Chrome session was verified through an attached headed Selenium driver. No new preview framework was created.
- This report closes only the exact Finance Add Service path. It does not claim acceptance of the separate six-surface Owner visual gate.

Residual unverified surfaces for this exact scope: none.

Production connection: NO. Production data mutations: 0. Push/PR/merge/deploy: none.
