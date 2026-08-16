# LOG-C03 Shipment Dashboard 2.0 Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c03-shipment-dashboard/2026-08-14-log-c03-shipment-dashboard-actual-status.md`

## Evidence Rules

This ledger records current source, graph, runtime, test, browser, governance, and worktree evidence for LOG-C03. Evidence is phase-scoped and must be refreshed when the changed source or runtime changes. Tests are supporting evidence; visible behavior and source-of-truth checks are required for UI claims.

### Evidence ID Naming

- `E0` = baseline/P0.
- `E1` = projection/rule model.
- `E2` = Streamlit dashboard integration.
- `E3` = regression/browser/closure.
- Use exact IDs in actual-status and benchmark files.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-WT1`: `git status --short` shows a dirty worktree with pre-existing LOG-C01/LOG-C02 source, tests, reports, `.p2p/`, `.streamlit/`, archives, and other user changes. No reset/checkout is authorized.
- `E0-P0A-WT2`: current branch is `main`; recent commits are LOG-C02 closure/checkpoint commits. New LOG-C03 work must remain bounded and must not broad-stage the worktree.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed on 2026-08-14; 124 files scanned, 62 code files parsed, 0 parse failures, graph 10,084 nodes/11,406 relationships; unresolved hotspots include `views/dashboard.py` and `core/financial_ledger.py`.
- `E0-P0A-GRAPH2`: `anvien file-detail views/dashboard.py --repo Logistics-Pro-AI --json` reports 117 symbols, 7 local relationships, 435 unresolved references, high file risk; dashboard impact is a LOW aggregate risk with 2 direct same-file relationships and 1 affected file in the current graph projection.
- `E0-P0A-GRAPH3`: `anvien file-detail views/shipment.py`, `core/shipment_360.py`, and `core/financial_ledger.py` report 99/71/133 symbols and local relationship counts 0/38/34 respectively; impact summaries are LOW/MEDIUM/MEDIUM with direct counts 0/12/14. These files are preserve/inspect-only unless a direct regression proves otherwise.
- `E0-P0A-SRC1`: `views/dashboard.py` currently groups shipments by customer and renders task history, Top Customer, GetFly, commission, and legacy compact status/debt badges; filters are search, time range, and Active/Done.
- `E0-P0A-SRC2`: `views/dashboard.py:282-375` already has a first-click session alias/rerun path to existing detail; this is preserve-first, not a reimplementation target.
- `E0-P0A-SRC3`: `core/shipment_360.py:449-634` provides a non-mutating, source-labelled Shipment 360 view with separate operational/financial fields, UNKNOWN/attention states, and `read_only=True`.
- `E0-P0A-SRC4`: `views/shipment.py:89-161` renders the Shipment 360 read model before existing operational/finance tabs. Existing detail save/payment controls remain out of scope and must not be added to dashboard rows.
- `E0-P0A-SRC5`: `core/config.py` defines the current status vocabulary `wait/pending/done/cancel` and labels; `core/utils.py` provides `parse_date_optional`, `parse_date`, and nested shipment business-date extraction.
- `E0-P0A-SRC6`: `core/validators.py` confirms existing supported shipment fields: customer, `data.1.2.etd`, `data.2.6.arrival_date`, `data.2.7.delivery_date`, and delivery completion. No normalized customer-required-date, factory-lot, owner, or CBM schema is present in current code.
- `E0-P0A-TEST1`: existing tests cover finance logic, Shipment 360, write safety, and payment/ledger regressions; no `tests/test_shipment_dashboard.py` exists at baseline.
- `E0-P0A-BROWSER1`: reusable LOG-C01/LOG-C02 Playwright flows exist under `playwright/` and prior local QA proves one-click/detail and read-only Shipment 360 behavior on the local Streamlit runtime.
- `E0-P0A-RUNTIME1`: repository root has no Dockerfile or docker-compose target; Docker-backed full-build/browser evidence is a known capability blocker unless a valid host/runtime target is discovered later.
- `E0-P0A-P2P1`: `p2p_workflow.py ... run --json` stopped `BLOCKED` because the active project workflow requires independent objectives/oracles to be split/compiled; this task does not modify P2P source and does not claim governance PASS.
- `E0-P0A-UIUX1`: `p2p_uiux.py recommend`, `design-system`, and `contract` generated a DRAFT design system and valid large-scope contract under `.p2p/design/`; implementation mapping preserves the existing Streamlit/nav/data boundaries, with accessibility evidence still marked `NEEDS_EVIDENCE`.
- `E0-P0A-GRAPH4`: final `anvien analyze --force` on 2026-08-14 scanned 133 files, parsed 65 code files, reported 0 parse failures, and produced 10,706 nodes/12,205 relationships. Final file detail reports `core/shipment_dashboard.py` as parsed with 78 symbols/60 local relationships and `views/dashboard.py` as parsed with 130 symbols/8 local relationships; the latter remains a high-risk legacy file and was edited only in the bounded queue region.
- `E0-P0A-GRAPH5`: post-Golden-fixture correction `anvien analyze --force` scanned 134 files, parsed 65 code files, reported 0 parse failures, and produced 10,724 nodes/12,223 relationships; the added file is the fresh supervisor report/artifact inventory and does not change the production graph boundary.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-RULE1`: `core/shipment_dashboard.py` derives `arrival_date + free_time`, warns at `<=2` days, and marks expired free time critical; direct probes and boundary tests pass.
- `E1-P1A-RULE2`: bounded aliases cover explicit customer-required, planned, promised, and next-action dates; no warning is created when the source date/flag is absent.
- `E1-P1A-PROJ1`: `build_shipment_dashboard_view` returns separate operational/financial fields, financial `UNKNOWN`, source-labelled projection, deterministic alerts, and `read_only_financial=True` without mutation.
- `E1-P1B-TEST1`: `tests/test_shipment_dashboard.py` contains seven focused test functions covering 16 bounded fixture scenarios; the Golden Lục Giác fixture now includes 3 factories, required delivery `30/08/2026`, assignment `01/08/2026`, `EXW`, and partial factory data. Manual execution through the available Python interpreter passed because `pytest` is not installed in PATH.
- `E1-P1B-FILTER1`: owner/customer/status/financial/alert filtering and severity/deadline ordering pass in fixture-only tests; no database or write helper is imported by the projection.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

- `E2-P2A-UI1`: local Streamlit browser snapshot at `http://127.0.0.1:8517/` shows shipment-first Support work desk, summary counters, and one row per shipment using the real loaded data.
- `E2-P2A-CARD1`: browser DOM shows shipment/customer, owner/update/route, ETA/deadline fields when available, operational badge, free-time state, financial badge/raw status, next action, and one-click row control; non-color text labels are present.
- `E2-P2B-FILTER1`: browser interaction exposes Sale phụ trách, Khách hàng, Cảnh báo, Vận hành, and Tài chính; `SALE Thành` is selectable without assigning it to rows; `Quá free time` narrowed runtime data from 78 to 28 rows.
- `E2-P2B-SORT1`: pure `sort_dashboard_views` orders critical/warning/info by severity, priority, explicit deadline, and shipment id; fixture tests pass.
- `E2-P2C-REG1`: reusable browser flow opened the existing Shipment 360/detail, observed two existing `💾 LƯU` controls unchanged, and returned to the work desk without submitting a business-data action.
- `E2-P2C-SECOND1`: the same flow opened `T7.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE + KEO`, closed it, and opened `LO-0306` successfully.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-BUILD1`: `python -m py_compile`, `python -m compileall -q core views tests`, `node --check`, seven manual dashboard tests, three `Shipment 360` unittest cases, and 25 focused finance/payment/ledger/write-safety unittest cases pass. `pytest` is unavailable and the repository has no Dockerfile/compose target, so no Docker-backed full build can be claimed.
- `E3-P3A-REG2`: `python -m unittest tests.test_finance_logic tests.test_payment_logic tests.test_financial_ledger tests.test_financial_write_safety` completed 25 tests with 2 expected skips and OK; `python -m unittest tests.test_shipment_360` completed 3 tests with OK. These are the bounded LOG-C02/Shipment 360 regression surfaces exercised for this slice, not a claim that every repository test was run.
- `E3-P3A-BROWSER1`: official JSON/MD plus dashboard and Shipment 360 PNG artifacts are under `Reports/QA/playwright/`; the final visible flow after the last source edit recorded 0 console errors and 0 warnings and completed the second-shipment transition.
- `E3-P3B-DETECT1`: final `anvien detect-changes --repo Logistics-Pro-AI --scope all --json` completed. It sees 17 tracked dirty files and 95 affected processes because the worktree was already dirty; the implementation files remain uncommitted/untracked or bounded within the existing dashboard file and were not broad-staged.
- `E3-P3B-SUP1`: `reports/supervisor/rp_supervisor_260814_190347_by_gpt-5-codex_log_c03_shipment_dashboard.md` independently re-reviewed the corrected Golden fixture and current source/runtime/evidence and returned `REJECT` for formal closure because the P2P workflow, full-build target, and declared pytest/write-count oracles remain unresolved.

## Closure Evidence

- `E3-CLOSE1`: final worktree review preserved the known dirty worktree; no files are staged or committed by LOG-C03.
- `E3-CLOSE2`: local product slice is implemented and browser-verified; formal closure remains `BLOCKED` by the repository P2P workflow state and the unavailable Docker build target.

## E4 - LOG-C03 Formal Closure Re-run

Matching user closure request: LOG-C03 bounded product acceptance and honest
blocker classification.

- `E4-P3A-ORACLE1`: `python -m unittest -v tests.test_dashboard_financial_write_oracle` passed the mounted fixture-only oracle. It ran the real `app.py` entry point through `streamlit.testing.v1.AppTest`, exercised dashboard render, financial projection read, SALE owner filter, warning filter, first-shipment open/close, and second-shipment open. All existing payment, obligation, transaction, allocation, entrustment, shipment-save, snapshot, and lump-sum writer boundaries were spied; `financial_write_count == 0`.
- `E4-P3A-MUT1`: the same oracle compared the fixture financial snapshot before and after the full bounded flow. Differences: `0`; calls recorded by the write oracle: `[]`. The test uses only an in-memory fixture and patches the app refresh path, so no real financial data or Mongo write was used.
- `E4-P3A-RUN1`: `python -m unittest discover -s tests -p 'test_*.py' -q` passed `49` tests with `2` expected skips. The canonical project runner is unittest, not pytest.
- `E4-P3A-DASH1`: the seven standalone functions in `tests/test_shipment_dashboard.py` passed through the available Python interpreter; they cover the free-time, deadline, promised-info, missing-data, financial-status, owner/filter, and deterministic ordering boundaries.
- `E4-P3A-REG3`: `python -m unittest tests.test_shipment_360 tests.test_finance_logic tests.test_payment_logic tests.test_financial_ledger tests.test_financial_write_safety` passed `28` tests with `2` expected skips. This is the LOG-C02 financial/Shipment 360 regression boundary.
- `E4-P3A-BUILD2`: `python -m compileall -q core views tests` and `python -X utf8 scripts/check_router.py` passed; router output ended with `ROUTER CHECK PASSED`.
- `E4-P3A-ENV1`: `python -m pytest --version` returned `No module named pytest`. This is an environment fact, not a product failure: pytest is not a declared dependency and the documented unittest runner passed.
- `E4-P3A-BROWSER2`: fresh visible in-app-browser recheck on `http://127.0.0.1:8517/` recorded SALE Thành `0/78`, warning filter `Quá free time` `28/78`, first open `LO-0306`, close/list restoration, second open `T1 - 107850148710 - BẢNG ĐIỀU KHIỂN KEBA HP`, Shipment 360 on both transitions, and `0` browser console errors/warnings. No save/delete/payment control was submitted. See `Reports/QA/playwright/2026-08-14-log-c03-closure.json` and `.md`.
- `E4-P3B-CLASS1`: blocker classifications are `A Docker = NOT_APPLICABLE`, `B pytest = NOT_APPLICABLE`, `C write oracle = GOAL_ACCEPTANCE_REQUIREMENT (closed)`, and `D P2P helper = P2P_INFRASTRUCTURE_REQUIREMENT (helper blocked only)`. No `REAL_PRODUCT_DEFECT` was found in the bounded LOG-C03 acceptance scope.
- `E4-P3B-P2P1`: `.p2p/state/reports/run-20260814-105256-log-c03-objective-co.json` remains the exact helper evidence: `status=BLOCKED`, `goal_created=false`, goal-linter error `independent objectives must be split before a Goal starts`, C1/C4 `BLOCKED`. It was inspected but not modified.
- `E4-P3B-SUP2`: fresh Supervisor review `reports/supervisor/rp_supervisor_260814_193944_by_gpt-5-codex_log_c03_formal_closure.md` returned `PASS` for the bounded LOG-C03 product/project claim and explicitly kept the P2P helper verdict separate as `BLOCKED`.

### Closure interpretation

`E3-CLOSE2` is retained as historical pre-oracle evidence. The current
two-layer result is product/project `PASS` and P2P formal helper `BLOCKED`.
