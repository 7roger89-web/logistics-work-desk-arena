# Issue #247 — S2 staff payment UI, real Chromium

**Verdict: S2 PASS.** Product source: **NO_CODE_CHANGE**. This proves only the bounded
staff `payment_record` slice on PR #248; it does not close Issue #247, does not prove
`save_contract_intl_snapshot` has a browser editor, and does not authorize S3/merge/Cloud.

## Identity and scope

- PR: <https://github.com/7roger89-web/logistics-work-desk-arena/pull/248>
- Spec: <https://github.com/7roger89-web/logistics-work-desk-arena/issues/247#issuecomment-6538808141>
- Tested product HEAD / PR head: `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`
- Base branch: `arena/ae5f9f47-logistics-work-desk-arena`
- Session branch: `arena/5a8ce272-logistics-work-desk-arena`
- App: real `app.py` → `views.web_app.main`, existing built React bundle, Streamlit Components v2.
- Browser: **Chromium 153.0.8010.0** / `HeadlessChrome/153.0.8010.0`, binary `/tmp/chromium`,
  `LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp`, puppeteer-core 24.40.0. No jsdom.
- Transport: one OS process, one in-process `mongomock` DB `logistics_staging`,
  `ENV_IDENTITY=PREVIEW`, no `MONGO_URI`. No Cloud/Atlas/Drive/production write.
- Auth: `AUTH_REQUIRED=true` with canonical TEST users. The spec's suggested
  `AUTH_REQUIRED=false` was **not** used because `fresh_session_identity_for_action`
  would promote callbacks to `local-admin`; that would not prove Support authority.
  No auth/RBAC guard was changed.
- Actor: `qa.s2.support`, role `support`, `finance_write=true`.
- Negative actor: `qa.s2.sale`, role `sale`, `finance_write=false`.

## Fixture and pre-state

`LO-0306`, currency **VND**, version 1. Initial `data.3.4.payments`: **1**
(`SEED-REQ-0306-1`, 60,000,000 VND). Initial `financial_action_requests`: **0**.
Initial `direct_payment_created` audits: **0**. Initial payment domain events: **0**.
See `pre-state.json`.

## Commands and exits

Run from repo root at tested product HEAD:

```bash
# one test-only Streamlit process; password is ephemeral and never written to evidence
export S2_TEST_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
export S2_EVIDENCE_DIR="$PWD/evidence/issue247/s2"
export AUTH_REQUIRED=true MONGO_URI= MONGO_DB_NAME= DEPLOYMENT_ENV=staging ENV_IDENTITY=PREVIEW
export LOGISTICS_PRO_SECRETS_FILE=/path/that/does/not/exist.toml S2_WRITER_DELAY_SECONDS=5
python -m streamlit run playwright/issue247_s2_runtime.py \
  --server.address=0.0.0.0 --server.port=9501 --server.headless=true \
  --browser.gatherUsageStats=false --server.fileWatcherType=none --client.toolbarMode=minimal

curl -fsS http://127.0.0.1:9501/_stcore/health   # ok, exit 0

LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp \
node playwright/issue247_s2_browser.mjs \
  --url http://127.0.0.1:9501/ --out evidence/issue247/s2 \
  --chrome /tmp/chromium --puppeteer-core /path/to/puppeteer-core
# BROWSER_EXIT=0

python -m pytest tests/test_logi_interaction_latency_finalize_02.py -k payment_record_truthful_readback -q
# 1 passed, 17 deselected; exit 0
python -m pytest tests/test_lg08_1_rbac_boundary.py -q
# 3 passed; exit 0
```

The 5-second writer delay is a TEST-only observation window around the unchanged
canonical writer. It does not alter arguments, authorization, return value, or data.

## Positive flow — same store, two viewport intents

Each viewport navigated visibly: shipment list → `LO-0306` → Toàn bộ lô hàng →
Tài chính / Công nợ → `payment-record-sheet` → typed `137000` VND →
`payment-record-submit`. The runner issued two rapid physical clicks; the product's
synchronous pending guard produced exactly **one** canonical writer call per intent.
Success was accepted only after all three matched:

1. `lastWrites.requestId` with `ok=true`;
2. fresh `shipments[].finance.payments[].requestId`;
3. raw same-process `shipments.data.3.4.payments[].request_id`.

| Viewport | requestId | paymentId | Writer calls | Payment/request/audit/event delta |
|---|---|---|---:|---:|
| 1440×900 | `PAY-REQ-MVW0BNTH-5K18K6` | `PAY-E122EA2AF3C24F51AE86C02765C884C5` | 1 | +1 / +1 / +1 / +1 |
| 390×844 | `PAY-REQ-MVW0BYGC-ZXD34A` | `PAY-068016577A464420A8B5B3DC7F271FB7` | 1 | +1 / +1 / +1 / +1 |

Final same-store counts: payments **3** (seed + two distinct viewport intents),
`financial_action_requests` **2**, `direct_payment_created` audits **2**, domain events **2**.
Each requestId occurs exactly once in each collection and is scoped to `LO-0306`.
Both payments survived a full browser reload; Streamlit's canonical login gate was
re-authenticated as the same TEST Support user, then the lot/finance tab was reopened.

## Pending, negatives, geometry

- Pending DOM was captured while the backend call was still in flight: submit disabled,
  sheet open, no success toast, and no matching `lastWrites` outcome yet.
- Invalid `0` and non-numeric `abc` were refused in the UI with **0** writer calls on both viewports.
- Same-store canonical RBAC negative: Sale returned
  `Bạn không có quyền thực hiện giao dịch tài chính`; payment/request/audit/event state unchanged.
  Focused canonical test: `tests/test_lg08_1_rbac_boundary.py::test_rbac_sale_payment_denied`.
- Geometry before submit and after reload: submit hit-testable, inside viewport,
  no horizontal overflow. Desktop submit 215×44; mobile submit 170×48.03.
- Browser page errors: **0** on both viewports.

## Evidence files

- `browser-results.json` — full assertions, DOM events, geometry, before/after readback.
- `browser-run.txt` — final runner stdout, exit 0.
- `pre-state.json`, `writer-calls.json`, `latest-readback.json`, `readback-history.jsonl` — same-process DB/probe receipts.
- `rbac-negative.json` — canonical same-store Sale denial.
- `desktop-*.png`, `mobile-*.png` — real Chromium screenshots (finance, invalid, pending, success, reload sheet).
- `focused-backend.txt`, `focused-rbac.txt` — focused regression exits.

## Boundary

S2 PASS is executor evidence for this challenged slice only. Independent review,
customer A/B browser denial, Cloud UAT, and final Issue #247 acceptance remain separate.
No merge, no S3, no Node 06, no replacement PR.
