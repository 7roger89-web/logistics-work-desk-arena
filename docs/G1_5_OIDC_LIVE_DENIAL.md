# G1.5 — Live Google identity denied: diagnosis

Date: 2026-10-27 (Asia/Saigon)
Scope: diagnosis of the staging symptom on `https://thu-log-g1-test.streamlit.app/`
after a real Google callback: **“Danh tính đăng nhập không hợp lệ. Không có dữ liệu
được hiển thị.”**

## 1. Symptom → code path

`views/web_app.py::main` → `core/customer_portal_oidc.py::current_oidc_session()`
→ `views/customer_dashboard.py::render_oidc_problem()`.

`render_oidc_problem()` only prints that sentence for
`STATE_DENIED` (`STATE_CONFIG_ERROR` and `STATE_EXPIRED` print their own text).
So the live session reached `STATE_DENIED` with some `reason`.

## 2. Exact reason: `origin_mismatch` (deterministic, not a guess)

Streamlit's own callback writes the identity cookie as
`dict(userinfo, origin=<redirect_uri origin>, is_logged_in=True, provider=provider)`
(`streamlit/web/server/starlette/starlette_auth_routes.py::_auth_callback`,
verified in 1.66.1). When the cookie is read for a script run, Streamlit validates
that `origin` against the live request origin and then **deletes the claim before
exposing `st.user`**:

- starlette line (≥1.63.0 through 1.66.1): `_parse_decoded_user_cookie()` →
  `payload.pop("origin", None)`
- tornado line (1.51.x): `BrowserWebSocketHandler._parse_user_cookie()` →
  `del cookie_value["origin"]`

Both supported lines are affected, so this is not a Cloud version drift.
Consequently `st.user` can never contain `origin`, and the old check

```python
if str(info.get("origin") or "") != config.redirect_origin:  # "" != "https://…"
    return OidcSessionState(STATE_DENIED, reason="origin_mismatch")
```

denied **every** real Google login while `config` was already ready.

Reproduction with Streamlit's real parser (no mocks of the buggy behaviour),
synthetic claims, nothing secret printed:

```text
STREAMLIT_ST_USER_KEYS=at_hash,aud,azp,email,email_verified,exp,iat,is_logged_in,iss,nonce,provider,sub
STREAMLIT_ST_USER_HAS_ORIGIN=False
STREAMLIT_ST_USER_HAS_PROVIDER=True
CURRENT_REASON=origin_mismatch     # before fix
CURRENT_KIND=DENIED                # before fix
CURRENT_REASON=NONE                # after fix
CURRENT_KIND=AUTHENTICATED         # after fix
```

Why the tests stayed green: `_claims()` fixtures in
`tests/test_customer_portal_oidc_g1.py` and
`tests/test_customer_dashboard_g1_runtime.py` injected an `origin` key that the
real `st.user` never has. The fixture, not the app, was wrong.

## 3. Minimal fix (security unchanged)

`core/customer_portal_oidc.py`:

- `_origin_binding_ok()`: an **absent** `origin` is the normal verified-session
  shape (Streamlit already fail-closes cross-origin cookies: a foreign-origin
  cookie yields an empty `st.user` → `STATE_NONE`, never a verified identity).
  A **present but different** `origin` is still a hard `DENIED/origin_mismatch`.
- Unchanged and still enforced: `is_logged_in`, `provider=="google"`,
  `aud == client_id`, `iss ∈ {accounts.google.com}`, `email_verified == true`,
  `exp` not expired, `email` normalised/validated.
- `_state()` logs only `CUSTOMER_PORTAL_OIDC_STATE kind=<kind> reason=<reason>`.
  No claims, email, ID token, cookie, client secret or credential is logged.
  Anonymous sessions (`STATE_NONE`) are not logged, so nothing is spammed.

`views/customer_dashboard.py::render_oidc_problem()` is unchanged: the UI stays
generic and the reason stays in the operator log.

## 4. Evidence

- Screenshot-free proof, environment: Python venv, Streamlit 1.66.1, Authlib
  1.9.x, mongomock, pytest.
- Baseline full suite **before** edit: `35 failed, 2002 passed, 45 skipped,
  10 subtests passed` (`--continue-on-collection-errors`).
- After edit: `35 failed, 2009 passed, 45 skipped, 10 subtests passed`;
  the FAILED set is byte-identical to the baseline set (+7 new passing tests).
- Regression proof that the new tests actually capture the live bug: with the
  OLD `core/customer_portal_oidc.py` restored and the real-shape claims,
  `tests/test_customer_dashboard_g1_runtime.py` → `4 failed, 9 passed`; with the
  fix → `13 passed`.
- G1 lane (`test_customer_portal_oidc_g1.py`, `test_customer_dashboard_g1_runtime.py`,
  `test_customer_portal_core_g1.py`, `test_customer_portal_hexa_publication_v0.py`):
  `78 passed`.

## 5. Not verified here (BLOCKED, not assumed)

- Live browser round-trip on `thu-log-g1-test.streamlit.app`: this executor's
  sandbox has **no egress** to `*.streamlit.app` or `accounts.google.com`
  (`curl` exit 35), no Chromium/Playwright runtime, no Streamlit Cloud log
  access and no Google test account. Live `OIDC_LIVE` therefore stays
  `BLOCKED_BY_ENVIRONMENT`, not `PASS`.
- Owner-side confirmation: after redeploy, Streamlit Cloud logs should show
  either no `CUSTOMER_PORTAL_OIDC_STATE` line (identity accepted, then the
  portal's own allowlist decides) or one safe
  `kind=DENIED reason=<code>` line, which pins any remaining cause in one line.
