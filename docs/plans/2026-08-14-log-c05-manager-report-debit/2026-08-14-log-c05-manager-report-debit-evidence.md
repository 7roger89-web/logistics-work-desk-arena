# LOG-C05 Manager Report & Debit Draft Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-plan.md`
- Evidence: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-evidence.md`
- Benchmark: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-benchmark.md`
- Actual status: `docs/plans/2026-08-14-log-c05-manager-report-debit/2026-08-14-log-c05-manager-report-debit-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

- Evidence IDs are exact and phase-scoped.
- Source inspection and Anvien output map scope; runtime/browser output proves mounted behavior.
- Tests are supporting behavior evidence and cannot override the user brief.
- Financial write oracle evidence must distinguish metadata snapshot writes from underlying financial effects.
- Docker and positive-live-data gaps are recorded as blockers, not hidden by host-only evidence.
- No evidence may claim real workbook migration, payment execution, AI, or owner inference.

### Evidence ID Naming

`E<phase>-<item>-<kind><n>`; examples used here include `E0-P0A-REQ1`,
`E1-P1A-MODEL1`, `E2-P2A-REPORT1`, and `E3-P3A-TEST1`.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REQ1`: pasted LOG-C05 brief requires report + debit draft from canonical ledger, deterministic eligibility, multi-currency separation, snapshots, no AI/payment/Excel/live mutation, and truthful empty live state.
- `E0-P0A-GIT1`: `git status --short --branch` shows a known dirty worktree with prior LOG-C01/C02/C03/C04 and infrastructure changes; no reset/checkout/broad stage is permitted.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed on `D:\Logistics_App_Copy`; 152 files scanned, 71 code files parsed, 12,130 graph nodes, 13,833 relationships, 152 file projection.
- `E0-P0A-IMPACT1`: Anvien file-detail/impact shows `core/reconciliation.py` with 73 symbols/11 linked flows/high risk, `views/partner_reconciliation.py` with 46 symbols/8 linked flows/high risk, `core/financial_ledger.py` with 137 symbols/75 linked flows/high risk, and `core/database.py` with 137 symbols/75 linked flows/high risk.
- `E0-P0A-SOURCE1`: existing projection is read-only, exact-owner filtered, currency-separated, and exposes payable/held/received/paid/review/source/allocation fields; existing C04 helpers provide explanation, review inbox, trace, period draft, and partner comparison.
- `E0-P0A-ROUTE1`: `views/web_app.py` already mounts `Công nợ A Bò` to `ui_partner_reconciliation_desk`, while Dashboard remains the first route; no new home route is required.
- `E0-P0A-FIXTURE1`: `tests/test_reconciliation_desk.py` already contains the six C04 semantic golden cases, but no manager-report/debit calculator or clean 40,000 CNY debit fixture.
- `E0-P0A-EXPORT1`: existing export helper is shipment-oriented (`generate_debit_note_excel`) and is not a safe partner debit report path; no large export subsystem is authorized.
- `E0-P0A-RUNTIME1`: no Dockerfile or docker-compose file exists in the workspace; local Streamlit is the available runtime and any Docker acceptance must be reported separately.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-GRAPH1`: refreshed `anvien analyze --force` after the pure slice; 158 files scanned, 73 code files parsed, 12,934 graph nodes, 14,810 relationships, 0 parse failures.
- `E1-P1A-MODEL1`: `core/debit_draft.py` is a pure source-derived model with no Streamlit, database, AI, payment, or workbook imports; Anvien reports 101 symbols, 49 local relationships, 24 linked flows, stale `False`, and medium upstream file impact limited to the new file.
- `E1-P1A-TEST1`: `python -m unittest tests.test_log_c05_report_debit -v` passes 10/10 tests, covering report header/summary, all required C04 golden amounts and exclusions, important shipments, partner difference, clean debit arithmetic, multi-currency separation, edge exclusions, and zero financial effects.
- `E1-P1A-ORACLE1`: clean in-memory canonical fixture derives `90,000 CNY` payable after the `10,000 CNY` allocation history, `50,000 CNY` credits (`30,000` held plus `20,000` allocated received-on-behalf), and exactly `40,000 CNY` debit-ready; the model reports `financial_effect_write_count=0` and `read_only=True`.
- `E1-P1B-GRAPH1`: refreshed `anvien analyze --force` after the snapshot slice; 160 files scanned, 75 code files parsed, 13,298 graph nodes, 15,209 relationships, 0 parse failures.
- `E1-P1B-SNAPSHOT1`: `core/debit_snapshot.py` builds `DEBIT_DRAFT_SNAPSHOT` documents with period, party/owner, currency totals, exclusions, ledger/obligation/transaction/allocation/correction/shipment IDs, correction/reversal state, generated time, preparer, version, supersession link, and content hash; Anvien reports 40 symbols, 18 local relationships, 1 linked flow, stale `False`, and medium upstream impact limited to the new module.
- `E1-P1B-TEST1`: `python -m unittest tests.test_log_c05_report_debit tests.test_log_c05_snapshot_write_oracle -q` passes 14/14; `compileall` passes for the snapshot module and oracle.
- `E1-P1B-RETRY1`: the in-memory repository proves the same `request_id` reuses one snapshot, a conflicting payload raises `DebitSnapshotConflictError`, V2 preserves V1 content and marks only metadata superseded, and next version is `3` after V1/V2.
- `E1-P1B-ORACLE1`: snapshot persistence changes only `debit_draft_snapshots`; canonical obligation, transaction, allocation documents and the derived position remain byte-for-byte equal in the fixture oracle. Retry uniqueness is enforced by `uq_debit_draft_snapshot_request` at the metadata collection boundary.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-GRAPH1`: after the mounted UI edits, `anvien analyze --force` completed with 164 files scanned, 77 parsed code files, 13,799 graph nodes, 15,770 relationships, and 0 parse failures. `views/partner_reconciliation.py` now reports 80 symbols, 35 local relationships, 4 inbound references, 13 linked flows, stale `False`; file impact is `MEDIUM` with 8 direct symbols, 1 affected file, and 1 affected flow.
- `E2-P2A-REPORT1`: `tests.test_log_c05_partner_desk_write_oracle` renders the manager-report mode from an in-memory canonical projection and asserts the exact Vietnamese title, summary/explanation, important-shipment section, partner-difference wording, and truthful report surface.
- `E2-P2A-DEBIT1`: the same recorder suite renders Debit Draft and asserts the formula, included/excluded sections, currency-safe/read-only copy, and no manual total/payment control; the no-DB path leaves snapshot persistence unavailable.
- `E2-P2A-WRITE1`: the mounted report/debit recorder suite observes `financial_write_count == 0` for both modes; the existing C04 partner-desk write oracle remains green in the focused regression run.
- `E2-P2A-WRITE2`: snapshot repository tests prove the explicit metadata path is separate from obligations, transactions, allocations, corrections, and derived partner position; UI tests patch `get_db` to `None` and verify the snapshot button is disabled/absent in the empty runtime path.
- `E2-P2B-BROWSER1`: local Streamlit runtime at `http://127.0.0.1:8520` returned `ok` from `/_stcore/health`; direct Chrome smoke evidence reached the existing A Bò desk and both new actions. The live projection was empty, so the UI truthfully showed no eligible canonical data and no positive fixture was seeded.
- `E2-P2B-CONSOLE1`: `node --check playwright/log_c05_manager_report_debit_flow.mjs` passed. A concise local page-load smoke capture recorded 0 console errors and 0 page errors; the separate headless sidebar probe was not used to overclaim full reusable-flow completion.
- `E2-P2B-REPORT1`: official QA artifacts are `reports/QA/playwright/2026-08-14-log-c05-manager-report-debit.json` and `.md`; the three inspected screenshots prove the desk, manager report, and Debit Draft empty-state surfaces. Docker is explicitly blocked because no executable, Dockerfile, or compose target is available.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`

- `E3-P3A-TEST1`: `python -m compileall -q core views tests` passed; the focused LOG-C02/C03/C04/LOG-C05 regression command passed 45/45 tests with 1 expected skip; full `python -m unittest discover -s tests -p "test*.py" -q` passed 80/80 with 2 expected skips. Forced-write-failure tracebacks are expected assertions from the safety fixtures, not failures.
- `E3-P3A-REG1`: the focused regression includes `financial_ledger`, `shipment_360`, `shipment_dashboard`, `reconciliation_desk`, both partner-desk write oracles, and all LOG-C05 model/snapshot tests; no test failure was observed.
- `E3-P3A-BROWSER1`: the latest mounted runtime health remains `ok`; direct screenshots were visually inspected with `view_image`, and the official QA JSON/MD preserves the local-only, empty-live, no-mutation boundary.
- `E3-P3A-DETECT1`: after the latest graph refresh and both scoped commits, `anvien detect-changes --repo Logistics-Pro-AI --scope all --json` completed; the current dirty worktree reports 17 changed files and 14 affected files, with no uncommitted LOG-C05 source file in the filtered result. Staged detection was also run before both implementation commits.
- `E3-P3A-REPORT1`: coder report `reports/coder/rp_coder_260814_232305_by_gpt-5-codex_log-c05-manager-report-debit.md` and supervisor report `reports/supervisor/rp_supervisor_260814_232216_by_gpt-5-codex_log-c05-manager-report-debit.md` are written; the supervisor verdict is `PASS` for the bounded local scope.

## Closure Evidence

- Supervisor review is `PASS`; final detect-changes is recorded; scoped commits are `a17f2f4`, `3c7ecdd`, `d46ee7e`, and `74e5733`; final product/P2P verdict separation remains explicit in the closure response.
