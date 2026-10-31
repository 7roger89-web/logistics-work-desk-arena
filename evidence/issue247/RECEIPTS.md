# Issue #247 — receipts

Repo: `7roger89-web/logistics-work-desk-arena`
Base (staging integration): `arena/ae5f9f47-logistics-work-desk-arena` @ `1144af5`
Branch: `arena/f1a205f4-logistics-work-desk-arena`
Code commit: `661fdfc`  ·  evidence/docs commit: `cf30b3b` (final HEAD)
PR: #248

Everything below was produced in this workspace; no number is estimated.

## 1. Full-suite runs

| # | file | environment | result |
|---|------|-------------|--------|
| 0 | `00-baseline-head-1144af5-40f.txt` | base `1144af5`, project venv, `component/node_modules` **absent** | **40 failed**, 2308 passed, 45 skipped |
| 1 | `01-baseline-after-npm-ci-34f.txt` | same base, after a clean `npm ci` in `component/` | **34 failed**, 2315 passed, 44 skipped |
| 2 | `02-mid-13f.txt` | repair cycle, mid-point | 13 failed, 2336 passed, 44 skipped |
| 3 | `03-mid-2f.txt` | repair cycle, mid-point | 2 failed, 2350 passed, 44 skipped |
| 4 | `04-clean-a-fresh-venv.txt` | brand-new venv from `requirements.txt` + pytest, fresh `npm ci` | **0 failed, 0 error**, 2352 passed, 44 skipped |
| 5 | `05-clean-b-fresh-venv-no-pycache.txt` | same venv, `__pycache__` + `.pytest_cache` purged | **0 failed, 0 error**, 2352 passed, 44 skipped |
| 6 | `06-final-clean-1.txt` | final HEAD `661fdfc`, fresh venv, `-p no:cacheprovider` | **0 failed, 0 error**, 2352 passed, 44 skipped |
| 7 | `07-final-clean-2.txt` | final HEAD `661fdfc`, project venv, `-p no:cacheprovider` | **0 failed, 0 error**, 2352 passed, 44 skipped |
| 8 | `08-final-clean-3.txt` | final HEAD `cf30b3b` (docs/evidence only), fresh venv, `-p no:cacheprovider` | **0 failed, 0 error**, 2352 passed, 44 skipped |

Baseline difference 0 vs 1 is *environment*, not code: `test_journey_map_focus`
(×3), `test_inbox_snippets::test_dom_acceptance_*` and
`test_customer_portal_tenant_reset_g15` execute the real bundle in jsdom and
`require("jsdom")` resolves from `component/node_modules` (declared in
`component/package.json` `devDependencies`). A clean environment therefore means
`pip install -r requirements.txt` **and** `npm ci` in `component/`.

## 2. Skip set

`pytest tests -q -rs` on the base (before any change) and on the final tree
produce the identical 44 skips / 18 reasons; only the venv path prefix in the
`SKIPPED` line differs. No skip, xfail or deselect was added, and no test was
deleted (test count grew 2308 → 2352 because file-level failures disappeared and
retired-surface suites were restated as mounted-shell suites).

`NO_NEW_SKIP=true`

## 3. Security / money receipts (focused)

```
tests/test_lg08_1_safety.py tests/test_intl_payment_comparator.py
tests/test_logi_interaction_latency_finalize_02.py::test_payment_record_truthful_readback
tests/test_logi_finance_actual_entry_parity_01.py      ->  81 passed
tests/test_phase_a_component.py tests/test_all_tabs_smoke.py
tests/test_login_visual_compact.py tests/test_session_truth_repair.py
tests/test_entity_context_ui.py tests/test_logc12_host_native_runtime.py
                                                      ->  46 passed
```

Security negative controls kept/added (all green):

* `test_lg08_1_safety.py::test_staging_identity_cannot_touch_the_production_database`
  — PREVIEW/STAGING + `logistics_db` → `RuntimeError` ("CÁCH LY").
* `test_lg08_1_safety.py::test_missing_uri_still_fails_closed`
  — no `MONGO_URI` → `RuntimeError` ("Chưa cấu hình MongoDB").
* `test_lg08_1_safety.py::test_identity_gate_enforcement`
  — `get_db()` applies the same guard when a client exists.
* `core/config.validate_mongo_identity` unchanged by this PR.
* `test_contract_intl_payment_comparator` immutability: the writer now refuses a
  second, tampered snapshot with the same id **even without the unique index**
  (pre-insert fingerprint guard, `core/database.py`).

## 4. Browser / DOM

`dom-proof.txt` — jsdom acceptance scripts driving the **real production
bundle** `component/dist/logi-shell.js`; the eight that pytest actually executes
(`tests/*.py` reference them) all exit 0:

```
dom_acceptance_contract_slash_id          exit 0   (wired)
dom_acceptance_g15_tenant_reset           exit 0   (wired)
dom_acceptance_g1_customer_save_outcomes  exit 0   (wired)
dom_acceptance_inbox_snippets             exit 0   (wired)
dom_acceptance_journey_focus_customer     exit 0   (wired)
dom_acceptance_journey_focus_shell        exit 0   (wired)
dom_acceptance_journey_fresh_188          exit 0   (wired)
dom_acceptance_journey_inline_shell       exit 0   (wired)
dom_acceptance_create_shipment            exit 0   (run by hand, not wired)
dom_acceptance_real_use_repair            exit 1   (referenced in a docstring only)
dom_acceptance_shipment_slash_id          exit 1   (referenced in a docstring only)
```

Live-server boot on the same tree (real `streamlit run app.py`, port 8080,
`/tmp/venv-clean`):

```
GET /             -> 200
GET /_stcore/health -> ok (200)
```

**Real-browser proof is NOT available in this sandbox** and is reported as
`BROWSER_CRITICAL_PATH=NOT_VERIFIED`: there is no Chrome/Chromium binary, the
Chromium CDN (`cdn.playwright.dev`, `storage.googleapis.com`) is blocked by
egress policy, and the binary extracted from the npm package
`@sparticuz/chromium` cannot start (`error while loading shared libraries:
libnspr4.so`; `libnss3`/`libnspr4` are absent and `apt-get` needs root).

Beyond the wired set, `dom_acceptance_execution_profile.mjs`,
`dom_acceptance_amount_integrity.mjs` and
`dom_acceptance_finance_actual_entry.mjs` are not referenced by any pytest test
and fail today against their committed view-model fixtures (stale relative to
the current bundle). They are outside the Issue #247 gate (which is
`python -m pytest tests -q`) and are listed as follow-up work, not as a pass.

## 5. Component build

```
cd component && npm run typecheck   -> exit 0
cd component && npm run build       -> exit 0
git diff --stat component/dist      -> dist/logi-shell.js | 2 +-   (only the
                                       CostIntelligence catalog default)
```

The build is reproducible from src: rebuilding after `npm ci` yields exactly the
committed bundle.
