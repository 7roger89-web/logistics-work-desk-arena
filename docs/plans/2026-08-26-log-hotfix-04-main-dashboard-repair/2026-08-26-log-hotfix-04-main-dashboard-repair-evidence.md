# LOG-HOTFIX-04 Main Dashboard Repair Evidence Ledger

## Metadata

- Date: `2026-08-26`
- Plan: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-plan.md`
- Evidence: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-evidence.md`
- Benchmark: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-benchmark.md`
- Actual status: `docs/plans/2026-08-26-log-hotfix-04-main-dashboard-repair/2026-08-26-log-hotfix-04-main-dashboard-repair-actual-status.md`

## Evidence Rules

- Evidence records observed repository/runtime facts, commands, and outcomes.
- A source test or AppTest result is not Cloud deployment proof.
- A fixture or static import assertion is not sufficient by itself; the central
  regression proof must mount the actual lazy caller path.
- No credential, secret value, database URI, or business record is recorded.
- `BLOCKED` remains honest when Docker or live infrastructure evidence is
  unavailable.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: isolated worktree
  `D:\Logistics_App_GitHub\.tmp\log-hotfix04-main-repair` starts at
  `618838427f7fc143a36f70527c27b3c13e303a92`, equal to `origin/main`.
- `E0-P0A-SRC2`: `origin/production` resolves to
  `42d6fef6d7328232c19b095940e8971405908a92`; no Production worktree or
  deployment operation was used.
- `E0-P0A-REPRO1`: `python -m pytest tests/test_all_tabs_smoke.py -q` on the
  unmodified main candidate failed with one error in 7.53 seconds. The exact
  chain was `views/web_app.py` route load -> `views/dashboard.py`
  `_render_shipment_workdesk` -> `_render_workdesk_rows` -> lazy import of
  `build_shipment_summary`, producing the reported `ImportError`.
- `E0-P0A-HIST1`: `git log --all -S'build_shipment_summary' -- core views`
  identifies `a828a1b` (LG09 implementation), `ccdd345` (restore shipment
  summary contract), and `6a7517e` (rollback LG09 dashboard regression).
- `E0-P0A-HIST2`: `git show ccdd345 -- core/shipment_dashboard.py` shows the
  exact historical alias signature and delegation to
  `build_shipment_dashboard_view`, with an explicit read-only compatibility
  contract comment.
- `E0-P0A-HIST3`: `git show 6a7517e --` shows deletion of `core/readiness.py`
  and removal of the alias, while current main retains the LG09 callers and
  `core/readiness.py`; this supports a minimal contract repair instead of a
  rollback.
- `E0-P0A-SRC3`: current `core/shipment_dashboard.py` has
  `build_shipment_dashboard_view` with the historical mapping/date/financial
  view signature but no `build_shipment_summary` definition.
- `E0-P0A-SRC4`: current Dashboard LG09 block imports `OK`, `ACTION`, `WAITING`,
  and `INFO` but references `CRITICAL`; current Shipment block already imports
  all five readiness severity constants.
- `E0-P0A-GRAPH1`: fresh `anvien analyze --force` parsed 418 files, 205 code
  units, and 0 failed parses; graph contains 33,153 nodes and 37,674
  relationships. File-detail summaries: shipment dashboard 78 symbols/60
  local relationships/7 linked flows; readiness 46/67/3; Dashboard 222/18/6;
  Shipment 113/0/0. All four are parsed but high-risk, so edits are narrow.
- `E0-P0A-BOUNDARY1`: pre-edit `docker version` reports Docker is unavailable
  in this environment. This is recorded as a runtime validation gate, not
  replaced by a host dev-server claim.
- `E0-P0A-BOUNDARY2`: no credentials, secrets, database connection, business
  write, deployment, push, merge, or Production source mutation was performed.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-OBS1`: after restoring the historical alias and Dashboard's missing
  `CRITICAL` import, `tests/test_dashboard_financial_write_oracle.py` reached
  readiness derivation but failed with `TypeError: '<' not supported between
  instances of 'str' and 'datetime.date'` at `core/readiness.py:221`. The
  fixture and repository tests store `customer_required_date` as an ISO string,
  so the existing boundary was incomplete for actual caller data.
- `E1-P1A-OBS2`: after the date-boundary repair, mounted rendering had no
  Streamlit exception, but the existing financial write oracle failed its
  observable Next Action assertion because the Dashboard strip showed the
  derived stage/action without the explicit `Việc tiếp theo` label. The
  readiness logic was executing; the visible contract was incomplete.
- `E1-P1A-SRC1`: `core/shipment_dashboard.py` now contains the exact historical
  `build_shipment_summary(shipment, *, today=None, financial_view=None)`
  contract and delegates to `build_shipment_dashboard_view` without duplicating
  projection logic.
- `E1-P1A-SRC2`: Dashboard now imports `CRITICAL` in the existing LG09 lazy
  block; `views/shipment.py` remains unchanged and already had the full
  severity binding.
- `E1-P1A-SRC3`: `core/readiness.py` now passes
  `customer_required_date` through the existing `parse_date_optional` utility
  before comparison; invalid/unknown values remain `None` and the input mapping
  is not rewritten.
- `E1-P1A-SRC4`: Dashboard's non-OK readiness strip now visibly labels the
  derived value `Việc tiếp theo` while retaining the existing stage/action and
  status-icon projection.
- `E1-P1A-SRC5`: focused contract test confirms alias output equals the
  canonical projection, preserves the source mapping, and retains
  `read_only_financial=True`.
- `E1-P1A-CHECK1`: `python -m pytest tests/test_all_tabs_smoke.py -q` passed
  `1 passed in 9.21s` after alias/import/date repair.
- `E1-P1A-CHECK2`: `python -m pytest tests/test_dashboard_financial_write_oracle.py -q`
  passed `1 passed in 10.32s`, including zero financial writer calls and no
  financial fixture mutation.
- `E1-P1A-CHECK3`: `python -m compileall -q core/readiness.py
  core/shipment_dashboard.py views/dashboard.py views/shipment.py` passed.
- `E1-P1B-TEST1`: focused Dashboard test mounted `web_app.py`, spied on the
  actual `core.shipment_dashboard.build_shipment_summary` call, reached the
  Dashboard row, and passed its visible shipment/action assertions.
- `E1-P1B-TEST2`: focused Shipment test mounted `ui_shipment_detail_tabs`,
  reached the readiness card and all three standard tabs, and passed without an
  exception.
- `E1-P1B-TEST3`: focused readiness test proved string deadline coercion to a
  `date`, overdue `CRITICAL` Next Action derivation, `UNKNOWN` deadline
  handling, and source identity preservation.
- `E1-P1B-TEST4`: `python -m pytest tests/test_log_hotfix_04_dashboard_regression.py -q`
  passed `4 passed in 4.37s`.
- `E1-P1B-CHECK1`: relevant existing suites
  `tests/test_lg04_daily_work_ui.py tests/test_shipment_dashboard.py
  tests/test_shipment_workspace.py` passed `24 passed in 18.41s`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

Pending until implementation and validation slices are performed.

## Closure Evidence

Pending Supervisor review and final candidate status.
