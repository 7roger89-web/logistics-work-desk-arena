# Supervisor Report: Support Finance Add Service

Verdict: PASS

## Metadata

- Report file: `rp_supervisor_260904_165753_by_gpt-5-codex_log-rbac-support-01-finance-add-service.md`
- Review time: `260904 16:57 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: Logistics worktree `D:\Logistics_App_GitHub\.tmp\log-rbac-support-01`
- Scope reviewed: commit `abe00bdd455a22192b22b98288afab3406039692` and the live local Support Finance Add Service flow.
- Claim reviewed: authenticated Support can add, save, and read back a normal shipment Finance service while Admin-only boundaries remain protected.
- Authority used: latest Owner request; repository `AGENTS.md`; canonical `core/auth.py::ROLE_PERMISSIONS`; source, focused tests, local Mongo state, and headed Streamlit runtime.
- Related artifacts: coder report `reports/coder/rp_coder_260904_165433_by_gpt-5-codex_log-rbac-support-01-finance-add-service.md`; screenshots `evidence_support_finance_service_readback.png` and `evidence_support_finance_service_row.png`.

## Executive Summary

- Problem: the visible Support Finance Add Service control was unusable in the Owner preview.
- Decision: PASS. Current source, focused tests, live headed UI, local database readback, topology, and permission boundaries all support the bounded claim.
- Required outcome: accepted for this exact Finance Add Service flow; the separate six-surface Owner visual gate remains a separate scope.

## Source-Level Clearance Notes

- `views/dashboard.py`: clear. The existing dialog decorator is on `quick_assign_task_dialog` at line 114 and no longer on `_get_current_user_id` at line 57, so dashboard rendering does not open the task dialog over Finance.
- `views/shipment.py`: clear. The existing Add Service handler at lines 539-542 retains the appended row in the existing session shipment map before rerun; no alternate UI path or permission framework was introduced.
- `core/database.py`: clear. `save_shipment_atomic` builds `update_fields` at lines 508-512 and sends it in `$set` at line 516, excluding immutable creation provenance that remains in `$setOnInsert`; this closes the observed Mongo update conflict without changing transaction logic.
- `core/auth.py`: clear and unchanged in the reviewed commit. Support retains Finance and shipment-edit permissions, has no wildcard/admin route, and Sale retains no `receivables` permission.
- `tests/test_log_rbac_support_finance_service.py`: clear. The direct regression covers decorator placement and Support Add Service rerun retention.

## Evidence Checked

Passed:

- Source diff for commit `abe00bd` -> exactly the three bounded implementation edits, the focused regression, and evidence/report bookkeeping; no permission-model change.
- `python -m pytest -q --disable-warnings tests/test_log_rbac_support_finance_service.py tests/test_financial_write_safety.py::ShipmentOperationalFixtureTests::test_support_can_create_edit_and_reload_export_import_fields tests/test_log_rbac_support_01.py::SupportContractPersistenceTests::test_support_route_visibility_keeps_admin_only_user_route_hidden tests/test_log_rbac_support_01.py::SupportOperationalWriterTests::test_support_cannot_use_admin_only_destructive_writers tests/test_log_rbac_support_01.py::SupportOperationalWriterTests::test_support_can_write_canonical_finance_actual_but_viewer_cannot` -> `6 passed`.
- `python -m compileall -q core/database.py views/dashboard.py views/shipment.py tests/test_log_rbac_support_finance_service.py` -> PASS.
- `python scripts/check_config.py` -> configured database `logistics_dev`, MongoDB connection OK; secret values were not recorded.
- Local Mongo service -> Running; `logistics-rs`; exactly one member `127.0.0.1:27017` in `PRIMARY`; writable primary true; listener loopback-only.
- Streamlit -> `http://127.0.0.1:9501/_stcore/health` returned HTTP 200; local listener is `127.0.0.1:9501`.
- Fresh headed Support browser check -> Support marker present, Finance tab selected, dialog absent, Add Service visible and enabled, saved service inputs read back as service `Phí dịch vụ khác (DVK)`, cost `100000`, price `150000`, note `TEST LOCAL SERVICE`.
- Real `logistics_dev` readback -> shipment `SHP-20260904-011` has one matching service row with the expected values, `updated_by_role=support`, and version `3`; the UI retained those values after Reload Data.
- Boundary check -> Admin user route absent in Support UI; global shipment delete control disabled; focused destructive-writer tests passed; Support Finance permissions present; Sale receivables permission absent.
- Production guard -> a guarded `logistics_db` identity check was rejected before use; no Production connection or mutation occurred.
- Anvien -> graph refreshed on the exact worktree before review; change detection identified the bounded implementation symbols and the existing analyzer gaps, with no additional same-invariant surface requiring repair.

Failed:

- None for the reviewed claim.

Not run:

- Broad repository suite and unrelated UI surfaces were not run because the Owner explicitly limited verification to this exact defect and prohibited broad testing.
- The normal CUA/agent-browser kernel was unavailable on this host; the existing visible Chrome session was independently checked through an attached headed Selenium driver.

## Invariant Closure

- affected invariant: Support employee-facing Finance service entry must be usable and persist through the existing transaction-backed shipment writer without weakening role boundaries.
- sibling surfaces checked: Finance tab trigger, dialog overlay, Add Service rerun state, existing shipment writer, local Mongo transaction topology, Support Finance permissions, Support route visibility, admin-only destructive writers, canonical actual-finance writer, and Sale receivables visibility.
- residual unverified same-invariant surfaces: none for this exact Add Service path.

## Overall Evaluation

The reviewed fix is surgical and evidence-backed. It removes the accidental modal interception, retains the new row across Streamlit reruns, and resolves the concrete Mongo update conflict observed on Save. It preserves the existing transaction model and canonical RBAC authority, does not grant Support admin wildcard access, and leaves the local preview running for Owner retest. PASS is limited to this exact Finance Add Service claim, not a blanket acceptance of every Owner visual surface.
