# LOG-C07 Logistics Operations Workspace Redesign Evidence Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c07-operations-workspace-redesign/2026-08-16-log-c07-operations-workspace-redesign-actual-status.md`

## Evidence Rules

This ledger records current source, runtime, graph, design, test, screenshot, critique, correction, and safety evidence for LOG-C07. P2P `.19` artifacts and LOG-C06 terminal closure are authority/evidence pointers; they do not authorize financial mutation, historical publication, or release.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-P2P1`: `.p2p/system/VERSION` reports `8.4.7-C-codex.19`.
- `E0-P0A-P2P2`: `p2p_workflow.py inspect/classify/bootstrap` reused installed project state and project eval suite; project eval contains 18 cases and validation `PASS`.
- `E0-P0A-P2P3`: `p2p_workflow.py run` returned `BLOCKED` only because bounded execution/verification had no concrete runtime oracle; it recorded the existing goal/capsule and did not authorize release.
- `E0-P0A-DI1`: official `p2p_uiux.py design-intelligence` route status `READY`; required faculties include product intent, users/tasks, IA, task flows, component states, dense data, navigation, search, trust/uncertainty, financial UI, runtime evidence, critique, rendered perception, and regression verification.
- `E0-P0A-DI2`: official route classified `p2p-uiux` as primary; optional `p2p_aesthetica` profile was resolved but not executable/identity-verified, so no simulated specialist was used.
- `E0-P0A-SAFE1`: LOG-C06 terminal closure is `PRODUCT_PASS`; historical A Bò remains `NOT_PUBLISHED`, `DEFERRED_OWNER_GATED`, canonical financial mutation `0`, ambiguity preserved/deferred.
- `E0-P0A-SRC1`: baseline source inspection found `views/web_app.py` flat sidebar route list and `views/dashboard.py` dashboard header/date/task/history blocks before the shipment workdesk.
- `E0-P0A-SRC2`: `core/shipment_dashboard.py` is a pure read-only projection with explicit alerts, filters, sorting, financial flags, source, and `read_only_financial=True`; preserve-only at P0.
- `E0-P0A-SRC3`: `core/shipment_360.py` is read-only/source-labelled and preserves `UNKNOWN`, receivable/payable/evidence explanations; preserve-only at P0.
- `E0-P0A-GRAPH1`: fresh `anvien analyze --force` indexed 225 files, 102 parsed code files, 19,674 nodes, 22,759 relationships, 0 failed parses; file projection has 99 unresolved files and reports `views/dashboard.py`/`core/shipment_dashboard.py` high-risk hotspots.
- `E0-P0A-GRAPH2`: Anvien file detail: `views/dashboard.py` 130 symbols, 8 local relationships, 2 linked flows, risk `high`; `views/web_app.py` 22 symbols, 16 local relationships, 1 linked flow, risk `high`; `core/shipment_dashboard.py` 78 symbols, 60 local relationships, 12 linked flows, risk `high`.
- `E0-P0A-IMPACT1`: Anvien file impact: dashboard `LOW` aggregate with 130 contained symbols/3 direct/1 flow; web shell `LOW` with 22 symbols/4 direct/1 flow; projection `MEDIUM` with 78 symbols/10 direct/12 linked flows. This supports editing presentation only and preserving projection/core.
- `E0-P0A-RUNTIME1`: fresh local Streamlit runtime started from `web_app.py` at `http://127.0.0.1:8520/`; visible Chrome rendered the real Dashboard.
- `E0-P0A-RUNTIME2`: baseline body/screenshot showed 78 shipments, 76 needing attention, 0 deadline-soon count, 78 financial-attention count, 11 navigation routes, task/history before queue, and a long customer-count paragraph.
- `E0-P0A-SHOT1`: baseline screenshot `.tmp/log-c07/baseline-dashboard.png` captured and visually inspected; it shows default Streamlit card metrics and filter/task chrome ahead of the operational queue.
- `E0-P0A-BUILD1`: `python -m compileall -q core views tests` passed; `python -m pytest` is unavailable because pytest is not installed. This is a validation limitation, not a product failure.
- `E0-P0A-BUILD2`: no Dockerfile/compose target and no Docker executable were found; Docker/production acceptance is blocked and will not be mislabeled as pass.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-NAV1`: `views/web_app.py:55-72` defines four presentation groups: Operations, Commercial Context, Finance & Review, and Tools & Reference; the underlying route labels and permissions remain unchanged.
- `E1-P1A-NAV2`: visible Chrome body and screenshot show one active Dashboard button and reachable Customer, Finance/A Bò, and Tools routes; no duplicate selected radio state remains after the correction to button-based grouped navigation.
- `E1-P1A-NAV3`: reusable LOG-C07 flow reached Customer context and returned to Dashboard; all 11 visible route labels remain reachable through the grouped shell.
- `E1-P1A-SAFE1`: no shell code calls database writes; reload/archive/auth/logout controls remain in `_render_sidebar`, and A Bò route implementation is untouched.
- `E1-P1B-VIS1`: corrected render `.tmp/log-c07/redesign-dashboard-corrected-viewport.png` shows the navy workspace rail, active-state contrast, compact utility chrome, and focus/reduced-motion CSS.
- `E1-P1B-VIS2`: final visible screenshot `reports/QA/playwright/2026-08-16-log-c07-operations-workspace.png` confirms the corrected shell; stable rerender observed 0 console errors, 0 page errors, and 0 failed requests.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-ORDER1`: final viewport places the primary shipment queue and first actionable row in view; the top time-range expander and task/history panels are progressively disclosed above the queue.
- `E2-P2A-FILTER1`: queue filter uses the existing `filter_dashboard_views` contract for owner, customer, operational status, financial flag, alert, deadline, and search; no new financial math was added.
- `E2-P2A-FILTER2`: visible flow searched `LO-0306`, produced `2/2` matching rows, and excluded unrelated `T1 - 107850148710`; filter state persisted after Shipment 360 close.
- `E2-P2B-BAND1`: rendered queue exposes five semantic counters: total, action required, deadline, finance attention, and missing context.
- `E2-P2B-ROW1`: row exposes shipment/customer/route, Sale owner, update/ETA/planned dates, factory/document/agency context, operational status, free time, financial status, next action, and one Shipment 360 action.
- `E2-P2B-ROW2`: missing context remains explicit (`UNKNOWN`, `chưa có trường chuẩn`, or `chưa có nguồn chuẩn`) instead of being filled with guessed values.
- `E2-P2B-ROW3`: the first row is compact enough to scan in the first viewport while the full queue remains a dense vertical work surface.
- `E2-P2B-FIN1`: “Vì sao ra số này?” reveals financial meaning, receivable/payable/expected-profit metrics, source/status/reason rows, and a read-only canonical-truth notice.
- `E2-P2B-FIN2`: `core/shipment_dashboard.py` and `core/shipment_360.py` were preserve-only; `read_only_financial=True`, source labels, UNKNOWN states, and existing Shipment 360 controls remain intact.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-RUNTIME1`: fresh local Streamlit runtime was restarted from `web_app.py`; visible Chrome rendered the current source at `http://127.0.0.1:8520/`.
- `E3-P3A-SHOT1`: baseline `.tmp/log-c07/baseline-dashboard.png`, first render `.tmp/log-c07/redesign-dashboard-first-render.png`, corrected shell `.tmp/log-c07/redesign-dashboard-corrected-viewport.png`, final viewport `.tmp/log-c07/redesign-dashboard-final-viewport.png`, and official QA screenshot were captured and inspected.
- `E3-P3A-ACTION1`: `playwright/log_c07_operations_workspace_flow.mjs` and the QA JSON/MD record navigation, search/filter, financial explanation, Shipment 360 open/close, A Bò boundary, and return path.
- `E3-P3A-CRITIQUE1`: first render critique found a material sidebar selector defect (white brand on white background) and duplicate active-looking route controls caused by multiple radio groups; the correction target was source-backed and bounded.
- `E3-P3B-FIX1`: `views/web_app.py` changed sidebar selector to the actual Streamlit `section`, then replaced grouped radios with active-state buttons; `views/dashboard.py` collapsed secondary time filters, tightened the header, and restored semantic `h1` styling.
- `E3-P3B-TEST1`: compileall passed; unittest discovery ran 134 tests with 2 skips and OK; pytest remains tooling-blocked.
- `E3-P3B-RENDER1`: final corrected viewport shows one active Dashboard nav state, navy rail, first queue row in view, five-counter band, filters, context, and “Vì sao ra số này?” disclosure.
- `E3-P3B-REG1`: visible flow passed all declared checks; existing save controls remained at count 2 when detail was opened; financial/historical unittest suite passed; no payment, migration, publish, or canonical write path was exercised.

## Closure Evidence

- `E-CLOSE-P2P1`: official P2P `.19` Design Intelligence returned `READY`; Contract is valid large scope; Design System is project-owned `DRAFT` with no WCAG claim.
- `E-CLOSE-ANV1`: fresh `anvien analyze --force`, file detail/impact, and `anvien detect-changes --scope all` were run after the final code correction; the aggregate dirty-worktree risk is recorded, not hidden.
- `E-CLOSE-SUP1`: `reports/supervisor/rp_supervisor_260816_010034_by_gpt-5-codex_log-c07-operations-workspace.md` independently reviewed the source, runtime, tests, QA report, Anvien evidence, and safety boundaries; verdict `PASS` for the bounded local UI slice.
- `E-CLOSE-GIT1`: no isolated implementation commit was created because `views/dashboard.py` and `views/web_app.py` are already modified in the shared dirty worktree and staging them would mix pre-existing user changes; worktree state is reported explicitly.
- `E-CLOSE-SAFE1`: release/deploy/publish remains forbidden and must be reported as `NOT_RELEASED`.
