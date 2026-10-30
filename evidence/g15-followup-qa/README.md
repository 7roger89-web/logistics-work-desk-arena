# G1.5 isolated follow-up — 2026-10-30

## Provenance and limits

- PR #232 snapshot: `b67f306d44650c4f039e2b1275941e0e7e597c48`; draft, targeting staging. The correction is **not** on that PR: the Arena session is bound to `arena/a1cadc10-logistics-work-desk-arena`.
- Repair commit on the session branch: `c2ba70b74c6a4506137084c23b7fb4f75cbe928f` (imports PR through merge parent; no change to PR or staging). No deployment and no production data.
- Python 3.11.2, pytest 9.2.0, Streamlit 1.66.1, PyMongo 4.19.0, mongomock 4.3.0; Node 22.22.3, puppeteer-core 25.16.0, Chromium 153.0.0. Disposable in-process MongoMock only, with Mongo environment variables unset. This is not a real Mongo server, nor a Google login or an actual user-device test.

## Security regression and browser evidence

`before-cross-tenant.png`: Chromium at PR snapshot b67f306; a test-only identity switch from the Lục Giác fixture to a different customer causes the previously opened modal to remain visible, showing `QA-LOT`, `QA-EVENT` and `QA-DOC`. This reproduces same-page model replacement; it does **not** prove that a real Google logout/login preserves the same page or that a fresh browser session receives foreign data.

The fix clears old lot, modal, node/bubble, toolbar and utility state on every model repaint. `after-cross-tenant.png`, `after-approved-document.png`, and `browser-results.json`: same synthetic flow with patched application assets; this browser run used the source tree corresponding to code commit `41f6335b1f5816dfd29d5ad2bf645f1fae5edecd` (before formatting the test scripts; application source is identical to c2ba70b). Admin selects approved versions, checks consent, publishes, reads the same pointer after reload; customer sees the event and approved document metadata; private/foreign sentinel strings and internal amount absent; another test customer gets no LG data. Viewer UI shows no publication control. Direct backend denial and unchanged shipment+manifest after a forged viewer attempt are separately exercised by `tests/test_customer_portal_publish_g15.py` with mongomock; this is a direct Python invocation, not a network endpoint.

`tests/component/dom_acceptance_g15_tenant_reset.mjs` tests rerenders with 0, 1, and 2 replacement lots. Negative control against b67f306, with only the unrelated `root` reference fixed, fails because the old modal stays open; patched component passes. Fixed an undefined DOM `root` reference for standalone JS rendering. The previously failing static query-parameter test was narrowed to permit **only** the existing `portal` presentation selector; existing forged parameter/OIDC tests remain. It no longer incorrectly equates a presentation switch with customer identity.

## Test observations

- Focused G1/G1.5 suite plus new regression tests at the pre-format code tree 41f6335: **143 passed, 0 failed**; includes AppTest with synthetic OIDC and mongomock.
- Full suite with identical Python/Node dependencies and PREVIEW environment: b67f306 **2108 passed, 35 failed, 44 skipped**; repair tree 41f6335 **2110 passed, 35 failed, 44 skipped**, both plus 10 passing subtests. Failure set changed: the overbroad `test_customer_modules_have_no_browser_identity_or_url_id_path` was resolved; `test_inbox_snippets.py::test_search_finds_note_beyond_page` newly failed in the full run but passed when rerun alone on both trees. The identical failure count is not an identical failure set; the intermittent ordering failure remains unclassified and is outside this G1.5 change.
- Cloud QA `BLOCKED`: deployed SHA and runtime DB identity unverified, no Cloud writes attempted. Google OIDC live round-trip, actual Lục Giác business provenance and independent challenge remain unverified.

## Reproduction

Install repository Python requirements and pytest in a disposable venv, `npm ci` in `component/`, and provide `puppeteer-core` plus a compatible Chromium outside the app dependencies. With no Mongo credentials in the environment:

```
ENV_IDENTITY=PREVIEW streamlit run tests/component/g15_isolated_runtime.py --server.address 0.0.0.0 --server.port 9501
PUPPETEER_CORE_PATH=/path/to/puppeteer-core node playwright/g15_publication_isolated_qa.mjs --url http://127.0.0.1:9501/ --chrome /path/to/chromium --out /tmp/g15-results
python -m pytest -q tests/test_customer_portal_publish_g15.py tests/test_customer_portal_sources_g15.py tests/test_customer_portal_hexa_publication_v0.py tests/test_customer_portal_hexa_reference_ui_g15.py tests/test_customer_portal_core_g1.py tests/test_customer_portal_oidc_g1.py tests/test_customer_dashboard_g1_runtime.py tests/test_customer_portal_tenant_reset_g15.py
```

The QA-only Streamlit harness explicitly simulates identities; it is not a login implementation and must not be deployed.

## After PR #232 branch fast-forward (2026-10-30)

The first paragraph above records the **original Arena session constraint** at the time the QA was produced. Subsequently, Control Tower verified `arena/a1cadc10-logistics-work-desk-arena@dd1c63d` is a direct descendant of `PR #232@b67f306` (`ahead=3, behind=0`), then fast-forwarded PR #232's branch ref with `force=false`. The security fix and regression tests are **now included in PR #232**. The branch checkpoint `docs/NEXT.md` was updated afterward; do not use the historical `b67f306` as current HEAD. This does **not** constitute a staging merge, production deployment or independent test run on the new documentation-only HEAD.
