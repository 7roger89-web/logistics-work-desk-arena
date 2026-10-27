"""G1 Streamlit Google OIDC adapter tests — synthetic claims, no live Google."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core import customer_portal_oidc as oidc

FAKE_AUTH = {
    "required": True,
    "redirect_uri": "http://localhost:8501/oauth2callback",
    # Synthetic, non-secret test values only.
    "cookie_secret": "S" * 48,
    "google": {
        "client_id": "staging-client-id.apps.googleusercontent.com",
        "client_secret": "STAGING_TEST_ONLY_CLIENT_SECRET",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    },
}


def _claims(**overrides):
    claims = {
        "is_logged_in": True,
        "provider": "google",
        # No "origin": Streamlit validates the cookie origin itself and deletes
        # the claim before exposing st.user (G1.5). This fixture mirrors the
        # REAL post-callback shape; adding "origin" back would re-hide the bug.
        "aud": FAKE_AUTH["google"]["client_id"],
        "iss": "https://accounts.google.com",
        "email": "PORTAL.LucGiac@Example.com",
        "email_verified": True,
        "exp": int(time.time()) + 600,
        "sub": "staging-google-subject",
    }
    claims.update(overrides)
    return claims


def test_valid_config_is_secret_free():
    status = oidc.inspect_oidc_config(FAKE_AUTH)
    assert status.ready is True
    assert status.missing == ()
    assert status.redirect_origin == "http://localhost:8501"
    text = repr(status)
    assert "STAGING_TEST_ONLY_CLIENT_SECRET" not in text
    assert status.client_id not in text


def test_authlib_requires_1_3_2_or_newer():
    with patch.object(oidc.metadata, "version", return_value="1.3"):
        assert oidc._authlib_ready() is False
    with patch.object(oidc.metadata, "version", return_value="1.3.2"):
        assert oidc._authlib_ready() is True
    with patch.object(oidc.metadata, "version", return_value="1.9.1"):
        assert oidc._authlib_ready() is True


def test_placeholders_missing_provider_and_invalid_redirect_fail_closed():
    bad = {
        "required": True,
        "redirect_uri": "YOUR_VALUE_HERE/oauth2callback",
        "cookie_secret": "YOUR_VALUE_HERE",
        "google": {
            "client_id": "YOUR_VALUE_HERE",
            "client_secret": "YOUR_VALUE_HERE",
            "server_metadata_url": "https://evil.example/.well-known/openid-configuration",
        },
    }
    status = oidc.inspect_oidc_config(bad)
    assert status.ready is False
    assert "auth.redirect_uri.invalid" in status.missing
    assert "auth.cookie_secret.invalid" in status.missing
    assert "auth.google.client_id" in status.missing
    assert "auth.google.server_metadata_url.invalid" in status.missing
    assert "YOUR_VALUE_HERE" not in repr(status)

    without_provider = dict(FAKE_AUTH)
    without_provider.pop("google")
    assert oidc.inspect_oidc_config(without_provider).ready is False


def test_no_oidc_cookie_is_none_without_touching_customer_data():
    with patch.object(oidc, "_read_user_info", return_value={}):
        state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.kind == oidc.STATE_NONE
    assert state.email == ""


def test_oauth_return_yields_only_verified_email():
    with patch.object(oidc, "_read_user_info", return_value=_claims()):
        state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.kind == oidc.STATE_AUTHENTICATED
    assert state.email == "portal.lucgiac@example.com"
    assert "customer_id" not in state.__dict__


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ({"email_verified": False}, oidc.STATE_DENIED),
        ({"email_verified": "false"}, oidc.STATE_DENIED),
        ({"exp": int(time.time()) - 10}, oidc.STATE_EXPIRED),
        ({"aud": "another-client.apps.googleusercontent.com"}, oidc.STATE_DENIED),
        ({"origin": "https://evil.example"}, oidc.STATE_DENIED),
        ({"iss": "https://evil.example"}, oidc.STATE_DENIED),
        ({"iss": ""}, oidc.STATE_DENIED),
        ({"email": "not-an-email"}, oidc.STATE_DENIED),
        ({"provider": "other"}, oidc.STATE_NONE),
        ({"is_logged_in": False}, oidc.STATE_NONE),
    ],
)
def test_invalid_or_stale_oidc_claims_fail_closed(overrides, expected):
    with patch.object(oidc, "_read_user_info", return_value=_claims(**overrides)):
        state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.kind == expected
    assert state.email == ""


def test_streamlit_strips_origin_claim_and_session_still_authenticates():
    """G1.5 regression: the REAL post-callback st.user has no "origin" claim.

    Streamlit validates the identity cookie origin itself and then pops the
    claim (`_parse_decoded_user_cookie` / `BrowserWebSocketHandler`). Requiring
    the claim made every live Google login end in DENIED/origin_mismatch.
    """
    live_shape = _claims()
    live_shape.pop("origin", None)
    assert "origin" not in live_shape
    with patch.object(oidc, "_read_user_info", return_value=live_shape):
        state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.kind == oidc.STATE_AUTHENTICATED
    assert state.reason == ""
    assert state.email == "portal.lucgiac@example.com"


def test_origin_claim_is_still_enforced_when_a_host_exposes_it():
    with patch.object(
        oidc,
        "_read_user_info",
        return_value=_claims(origin="https://evil.example"),
    ):
        state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.kind == oidc.STATE_DENIED
    assert state.reason == "origin_mismatch"
    with patch.object(oidc, "_read_user_info", return_value=_claims()):
        assert oidc.current_oidc_session(FAKE_AUTH).reason == ""


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"aud": "another-client.apps.googleusercontent.com"}, "audience_mismatch"),
        ({"iss": "https://evil.example"}, "issuer_mismatch"),
        ({"email_verified": False}, "email_not_verified"),
        ({"exp": int(time.time()) - 10}, "identity_expired"),
    ],
)
def test_denial_reason_code_is_logged_without_identity_material(overrides, reason, caplog):
    """Staging diagnosis needs the reason code only — never claims/email/tokens."""
    with patch.object(oidc, "_read_user_info", return_value=_claims(**overrides)):
        with caplog.at_level("WARNING", logger="logistics.customer_portal_oidc"):
            state = oidc.current_oidc_session(FAKE_AUTH)
    assert state.reason == reason
    text = caplog.text
    assert f"reason={reason}" in text
    for secret in (
        "portal.lucgiac@example.com",
        "staging-google-subject",
        FAKE_AUTH["google"]["client_id"],
        "STAGING_TEST_ONLY_CLIENT_SECRET",
        FAKE_AUTH["cookie_secret"],
    ):
        assert secret not in text


def test_anonymous_session_is_not_logged_as_a_denial(caplog):
    with patch.object(oidc, "_read_user_info", return_value={}):
        with caplog.at_level("WARNING", logger="logistics.customer_portal_oidc"):
            assert oidc.current_oidc_session(FAKE_AUTH).kind == oidc.STATE_NONE
    assert "CUSTOMER_PORTAL_OIDC_STATE" not in caplog.text


def test_oauth_return_with_broken_config_is_config_error():
    with patch.object(oidc, "_read_user_info", return_value=_claims()):
        state = oidc.current_oidc_session({"required": True})
    assert state.kind == oidc.STATE_CONFIG_ERROR


def test_st_login_is_called_only_for_a_ready_config():
    fake_st = MagicMock()
    with patch.object(oidc, "st", fake_st):
        with patch.object(
            oidc, "inspect_oidc_config",
            return_value=oidc.OidcConfigStatus(ready=False, missing=("auth.google.client_id",)),
        ):
            assert oidc.start_customer_login() is False
            fake_st.login.assert_not_called()
        with patch.object(
            oidc, "inspect_oidc_config",
            return_value=oidc.OidcConfigStatus(ready=True, missing=()),
        ):
            assert oidc.start_customer_login() is True
            fake_st.login.assert_called_once_with("google")


def test_logout_and_customer_activation_clear_untrusted_session_state():
    fake_st = MagicMock()
    fake_st.session_state = {
        "current_user": {"username": "internal", "role": "admin"},
        "customer_portal_open_0": True,
        "customer_portal_detail_0": False,
        "unrelated": "keep",
    }
    with patch.object(oidc, "st", fake_st):
        oidc.activate_customer_session()
        assert "current_user" not in fake_st.session_state
        assert "customer_portal_open_0" in fake_st.session_state
        fake_st.session_state["current_user"] = {"username": "internal", "role": "admin"}
        oidc.logout_customer()
    assert "current_user" not in fake_st.session_state
    assert "customer_portal_open_0" not in fake_st.session_state
    assert "customer_portal_detail_0" not in fake_st.session_state
    assert fake_st.session_state["unrelated"] == "keep"
    fake_st.logout.assert_called_once_with()
