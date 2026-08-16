# LOG-C04 SALE Thành — Đối soát công nợ A Bò Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c04-sale-thanh-reconciliation/2026-08-14-log-c04-sale-thanh-reconciliation-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

- Evidence is current for the reviewed worktree and references exact commands, source files, runtime artifacts, or test results.
- Synthetic fixtures are isolated and never imported into live financial collections.
- Anvien evidence is refreshed before graph-based work and detect-changes is run before implementation commits.
- Product behavior, not static source presence alone, is the primary proof for new surfaces.
- P2P helper status is recorded separately from Product Verdict.

### Evidence ID Naming

Use stable, phase-scoped evidence IDs so `plan.md`, `actual-status.md`,
`benchmark.md`, and later agents can reference exact proof without ambiguity.

Format: `E<phase>-<item>-<kind><n>`.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REQ1`: Attached LOG-C04 brief defines the product outcome, persona, canonical-ledger boundary, golden fixtures, read-only financial write oracle, browser flow, acceptance criteria, and explicit non-goals.
- `E0-P0A-GIT1`: `git status --short` captured a known dirty worktree with existing LOG-C01/C02/C03 changes; no reset/checkout/broad staging is authorized.
- `E0-P0A-P2P1`: `p2p_workflow.py inspect/classify` identified a long-running Goal and `bootstrap` reused existing project profile/policy/eval/status; existing project eval contains 18 cases and validates PASS.
- `E0-P0A-P2P2`: Goal helper created a LOG-C04 contract but its linter returned BLOCKED because the request text was interpreted as separate objectives; this is a formal-helper limitation to report separately, not a product acceptance result.
- `E0-P0A-GRAPH1`: `anvien analyze --force` refreshed the graph: 139 files scanned, 66 parsed code files, 10,912 nodes, 12,427 relationships, 63 unresolved file-projection edges; `core/financial_ledger.py` and related projection surfaces are high-risk warnings, not edit prohibitions.
- `E0-P0A-IMPACT1`: Anvien `file-detail`/`impact` inspection identified the existing canonical projection in `core/financial_ledger.py`, the current partner renderer in `views/partner_finance.py`, the finance route in `views/finance.py`, and the router in `views/web_app.py`; the projection impact is HIGH with 16 linked flows and must remain scoped to read projection fields.
- `E0-P0A-DESIGN1`: Existing `.p2p/design/MASTER_DESIGN_SYSTEM.{md,json}` and `DESIGN_CONTRACT.json` are draft/owner-review-required and constrain this Goal to current components/styles, no frontend rewrite, read-only financial flag, and no new database. They are preserve-only.
- `E0-P0A-STATUS1`: Current-state classifications are recorded in the companion actual-status file; P0 is complete and implementation may begin only within the listed slice boundaries.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-DOM1`: `core/financial_ledger.py` now exposes `paid_on_behalf`, keeps received-on-behalf rows after full allocation, and returns `owner_coverage`; existing payable/held/unallocated/review/currency formula remains intact.
- `E1-P1A-DOM2`: Projection rows now carry `record_type`, `record_id`, timestamps, evidence/source refs, provenance, allocation history, and allocation IDs for later drill-down.
- `E1-P1A-TEST1`: `python -m unittest tests.test_financial_ledger -q` passed 13 tests with 1 opt-in Mongo test skipped; the forced rollback log is expected fixture output and the suite result is OK.
- `E1-P1A-TEST2`: `python -m unittest tests.test_financial_ledger -q` passed 13 tests with the new projection regression cases; the tests prove received-on-behalf history remains visible after full allocation, paid-on-behalf stays separate from held credit, and owner coverage is exposed.
- `E1-P1B-EXPL1`: `build_currency_explanation` and `build_review_inbox` produce deterministic confirmed/review-separated formulas, labels, and source IDs; the fixture asserts the confirmed total excludes UNKNOWN/restricted rows.
- `E1-P1B-TRACE1`: `search_partner_position("62464")`, `build_money_location_trace`, `build_period_reconciliation`, and `compare_reported_position` pass the synthetic CNY/VND fixture; allocation IDs are deduplicated in the period draft.
- `E1-P1B-TEST1`: `python -m unittest tests.test_reconciliation_desk -q` passed 11 tests covering the six golden amounts, currency separation, owner truthfulness, review categories, explanation, search, trace, period draft, and reported difference.
- `E1-P1B-TEST2`: `python -m compileall -q core/reconciliation.py tests/test_reconciliation_desk.py` passed; the new module imports no database/Streamlit/write surface and the fixture is in-memory only. Anvien file-detail parsed `core/reconciliation.py` (73 symbols, 31 local relationships, 11 linked flows, stale=false); file impact is MEDIUM and contained to the new module.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-UI1`: `views/partner_reconciliation.py` renders the dedicated Vietnamese read-only desk; visible runtime shows truthful empty/incomplete owner state and period draft when live canonical data has no matching A Bò/SALE Thành rows.
- `E2-P2A-TRACE1`: Positive explanation/trace states pass the pure fixture tests; the visible runtime correctly leaves trace/review rows unmounted when no live row exists, rather than injecting fixture data.
- `E2-P2A-WRITE1`: `python -m unittest tests.test_partner_reconciliation_desk_write_oracle -q` passed 2 tests; render/search/trace/period inputs produced `financial_write_count=0`.
- `E2-P2A-WRITE2`: Source inspection and the render oracle show no `save/allocate/insert/update/delete/bulk_write` path in the desk; browser route interaction produced no financial write control or write error. No live fixture was inserted.
- `E2-P2B-ROUTE1`: Route table import contains one `receivables` route to `views.partner_reconciliation.ui_partner_reconciliation_desk`; Dashboard remains the first/default route.
- `E2-P2B-BROWSER1`: Reusable flow `playwright/log_c04_partner_reconciliation_flow.mjs` passed on the visible local runtime; official JSON/Markdown are under `Reports/qa/playwright/2026-08-14-log-c04-partner-reconciliation.*`.
- `E2-P2B-CONSOLE1`: Final visible browser flow recorded `console_errors=[]` and `console_warnings=[]`.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-TEST1`: `python -m compileall -q core views tests` passed; full `python -m unittest discover -s tests -p "test*.py" -q` passed 64 tests with 2 opt-in skips; affected LOG-C02/LOG-C03/regression selection passed 40 tests with 2 opt-in skips.
- `E3-P3A-WRITE1`: Dedicated render oracle passed 2 tests with zero financial writes; the 64-test suite also kept existing write-safety tests green.
- `E3-P3A-RUNTIME1`: Local Streamlit health returned `ok` at `http://127.0.0.1:8520/`; Docker attempt is explicitly blocked because `docker` is unavailable and no Dockerfile/compose target exists.
- `E3-P3A-BROWSER1`: Visible browser screenshots were captured/inspected for initial Dashboard, desk empty state, search no-result, date picker, settled draft, and Dashboard regression; final console errors/warnings were empty. Positive live trace remains unverified because live projection is empty.
- `E3-P3B-REPORT1`: Coder report `reports/coder/rp_coder_260814_210500_by_gpt-5-codex_log-c04-reconciliation.md`, daily decision-log entry, official QA artifacts, and final plan/evidence/benchmark/status refresh are recorded.
- `E3-P3B-SUP1`: Supervisor report `reports/supervisor/rp_supervisor_260814_211500_by_gpt-5-codex_log-c04-reconciliation.md` independently reviewed source/runtime/tests/artifacts and returned `PASS` for the bounded local product scope; Docker/positive-live blockers remain explicit.

## Closure Evidence

- Final detect-changes: `anvien detect-changes --repo Logistics-Pro-AI --scope all --json` was run before the implementation/report checkpoints; full-worktree output remains high/critical because unrelated dirty files are present, while scoped commits contain only the LOG-C04 files listed in the coder/supervisor reports.
- Commit hash(es): `e117e1d`, `215a9ad`, `8cfea84`, `f08f60e`, `440c5f8`, `8d7dfa0`, `d96acea`, `04f5a03`.
- Product verdict: `PASS` for bounded local Streamlit/read-only product scope; Docker-built runtime and positive live-data states are `BLOCKED` and not relabeled as pass.
- P2P formal helper verdict: `BLOCKED` by the helper linter's separate-objective interpretation; reported separately from the product verdict.
