"""Real Streamlit-runtime UI tests for the G1 customer branch (AppTest).

These are not source-review claims: each test boots the existing ``app.py``
entrypoint in Streamlit's AppTest runtime and inspects the produced element
tree.  OIDC claims are synthetic and injected only inside the test harness;
there is no identity-emulation control in the shipped UI.
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest

from core import customer_portal as portal
from core import customer_portal_oidc as oidc
from views import web_app

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
SEED_PATH = ROOT / "scripts" / "seed_customer_portal_staging.py"

FAKE_AUTH = {
    "required": True,
    "redirect_uri": "http://localhost:8501/oauth2callback",
    "cookie_secret": "S" * 48,
    "google": {
        "client_id": "staging-client-id.apps.googleusercontent.com",
        "client_secret": "STAGING_TEST_ONLY_CLIENT_SECRET",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    },
}


@pytest.fixture(scope="module")
def seed_module():
    spec = importlib.util.spec_from_file_location("seed_customer_portal_staging_runtime", SEED_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _db(seed_module, *, negative_cases=False):
    database = mongomock.MongoClient()["g1_customer_portal_runtime"]
    seed_module.seed_staging(database, include_negative_cases=negative_cases)
    return database


def _claims(email: str):
    return {
        "is_logged_in": True,
        "provider": "google",
        # Real st.user shape: Streamlit strips the cookie "origin" claim (G1.5).
        "aud": FAKE_AUTH["google"]["client_id"],
        "iss": "https://accounts.google.com",
        "email": email,
        "email_verified": True,
        "exp": int(time.time()) + 600,
        "sub": "staging-google-subject",
    }


def _portal_payload(app: AppTest) -> dict:
    """Payload of the ONE mounted HEXA reference portal (G1.5)."""
    import json

    components = app.get("bidi_component")
    assert len(components) == 1, f"expected exactly one portal mount, got {len(components)}"
    return json.loads(components[0].proto.json)


def _portal_text(app: AppTest) -> str:
    """Every customer-visible string the reference portal is about to render."""
    import json

    return json.dumps(_portal_payload(app)["model"], ensure_ascii=False)


def _visible_text(app: AppTest) -> str:
    values: list[str] = []
    for name in (
        "title", "header", "subheader", "markdown", "caption", "info",
        "warning", "error", "success", "button", "text",
    ):
        for element in getattr(app, name, []):
            label = getattr(element, "label", None)
            if label:
                values.append(str(label))
            values.append(str(getattr(element, "value", "")))
    for name in ("table", "dataframe", "arrow_table", "arrow_data_frame"):
        for element in app.get(name):
            values.append(str(getattr(element, "value", "")))
    return "\n".join(values)


def _assert_no_exceptions(app: AppTest) -> None:
    assert not app.exception, [str(element.value) for element in app.exception]


def _click(app: AppTest, key: str) -> AppTest:
    button = next((element for element in app.button if element.key == key), None)
    assert button is not None, f"button {key} not rendered"
    button.click()
    return app.run()


@pytest.mark.parametrize("role,should_see_control", [("admin", True), ("support", False)])
def test_owner_portal_email_control_is_admin_only(seed_module, role, should_see_control):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    with (
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch(
            "views.web_app.require_login",
            return_value={"username": f"{role}.one", "display_name": role, "role": role},
        ),
        patch("views.logi_view_model.build_view_model", return_value={"ok": True}),
        patch("views.logi_shell.render"),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)
    selectbox_keys = {element.key for element in app.selectbox}
    assert ("shell_portal_access_customer" in selectbox_keys) is should_see_control
    # The owner control must not introduce a second app form.
    assert not app.get("form")


@pytest.mark.parametrize("role", ["admin", "support"])
def test_internal_admin_and_support_shell_are_unchanged(role):
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    db = mongomock.MongoClient()["g1_internal_regression"]
    with (
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch(
            "views.web_app.require_login",
            return_value={"username": f"{role}.one", "display_name": role, "role": role},
        ),
        patch("views.logi_view_model.build_view_model", return_value={"ok": True}) as build,
        patch("views.logi_shell.render") as render,
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)
    assert build.call_count == 1
    assert render.call_count == 1
    visible = _visible_text(app)
    assert "Dashboard khách hàng" not in visible
    assert "Đăng nhập khách hàng bằng Google" not in visible


def test_unauthenticated_customer_login_with_bad_oidc_config_fails_closed():
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {}
    bad_status = oidc.OidcConfigStatus(
        ready=False, missing=("auth.google.client_id", "auth.cookie_secret.invalid")
    )
    with (
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch("views.web_app.require_login", return_value=None),
        patch("views.customer_dashboard.oidc.inspect_oidc_config", return_value=bad_status),
        patch("views.customer_dashboard.oidc.start_customer_login") as start_login,
    ):
        app.run()
        assert any(button.key == "customer_portal_google_login" for button in app.button)
        _click(app, "customer_portal_google_login")
    _assert_no_exceptions(app)
    start_login.assert_not_called()
    assert "Lỗi cấu hình OIDC" in _visible_text(app)


@pytest.mark.parametrize(
    "portal,app_url,expected",
    [
        (None, "https://thu-log-g1-test.streamlit.app/", True),
        (None, "https://thu-log-g1-test.streamlit.app/oauth2callback", True),
        ("customer", "https://thu-log.streamlit.app/", True),
        ("internal", "https://thu-log-g1-test.streamlit.app/", False),
        (None, "https://thu-log.streamlit.app/", False),
        (None, "http://localhost:8501/", False),
        (None, "https://thu-log-g1-test.streamlit.app.evil.net/", False),
        (None, "https://[invalid", False),
    ],
)
def test_customer_entry_mode_after_google_callback(portal, app_url, expected):
    assert web_app._customer_entry_mode(portal, app_url) is expected


def test_staging_home_after_google_redirect_is_customer_only():
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    with (
        patch("views.web_app._current_app_url", return_value="https://thu-log-g1-test.streamlit.app/"),
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch("views.web_app.require_login") as internal_login,
        patch("views.logi_view_model.build_view_model") as internal_vm,
        patch("views.logi_shell.render") as internal_shell,
    ):
        app.run()
    _assert_no_exceptions(app)
    assert "Cổng khách hàng" in _visible_text(app)
    assert "Đăng nhập khách hàng bằng Google" in _visible_text(app)
    assert not app.get("form")
    internal_login.assert_not_called()
    internal_vm.assert_not_called()
    internal_shell.assert_not_called()


def test_staging_explicit_internal_url_keeps_password_login():
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.query_params = {"portal": "internal"}
    with (
        patch("views.web_app._current_app_url", return_value="https://thu-log-g1-test.streamlit.app/"),
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch("views.web_app.require_login", return_value=None) as internal_login,
    ):
        app.run()
    _assert_no_exceptions(app)
    internal_login.assert_called_once()


def test_customer_only_url_never_mounts_internal_login_or_shell():
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.query_params = {"portal": "customer"}
    with (
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch("views.web_app.require_login") as internal_login,
        patch("views.logi_view_model.build_view_model") as internal_vm,
        patch("views.logi_shell.render") as internal_shell,
    ):
        app.run()
    _assert_no_exceptions(app)
    assert "Cổng khách hàng" in _visible_text(app)
    assert "Đăng nhập khách hàng bằng Google" in _visible_text(app)
    assert not app.get("form")
    internal_login.assert_not_called()
    internal_vm.assert_not_called()
    internal_shell.assert_not_called()


def test_customer_login_button_starts_google_oidc_only_when_clicked():
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}
    ready = oidc.OidcConfigStatus(ready=True, missing=())
    with (
        patch(
            "views.web_app.customer_portal_oidc.current_oidc_session",
            return_value=oidc.OidcSessionState(oidc.STATE_NONE),
        ),
        patch("views.web_app.require_login", return_value=None),
        patch("views.customer_dashboard.oidc.inspect_oidc_config", return_value=ready),
        patch(
            "views.customer_dashboard.oidc.start_customer_login",
            return_value=True,
        ) as start_login,
    ):
        app.run()
        start_login.assert_not_called()
        _click(app, "customer_portal_google_login")
    _assert_no_exceptions(app)
    assert start_login.call_count == 1
    assert "Đang chuyển đến Google" in _visible_text(app)


def test_oauth_return_renders_only_own_publication_cards(seed_module):
    db = _db(seed_module, negative_cases=True)
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}
    # Browser-supplied ids must have zero effect on the server-side scope.
    app.query_params = {
        "portal": "customer",
        "customer_id": seed_module.CUSTOMER_B_ID,
        "shipment_id": seed_module.LOT_B1,
        "lot": seed_module.LOT_A2,
        "version": "v9",
    }
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        _assert_no_exceptions(app)
        model = _portal_payload(app)["model"]
        lots = model["lots"]
        assert [lot["shipment_id"] for lot in lots] == [seed_module.LOT_A1, seed_module.LOT_A2]
        assert model["notice"] and "chưa có bản duyệt hợp lệ" in model["notice"]["text"]
        visible = _portal_text(app)
        assert seed_module.LOT_B1 not in visible
        assert seed_module.LOT_A_DRAFT not in visible
        assert seed_module.LOT_MISSING_CUSTOMER not in visible
        assert seed_module.FOREIGN_SENTINEL not in visible
        for sentinel in seed_module.INTERNAL_SENTINELS:
            assert sentinel not in visible
        # The published version is what the reference detail panel shows.
        assert lots[0]["publication"]["version"] == "v1"
        # ... and an approved publication still carries no invented stage/amount.
        assert lots[0]["debt_summary"]["status"] == "UNKNOWN"
        assert all(node["state"] == "UNKNOWN" for node in lots[0]["journey"]["nodes"])


def test_db_unavailable_none_logs_safe_reason_without_email(caplog):
    with patch.object(portal, "get_db", return_value=None):
        with caplog.at_level("WARNING", logger="logistics.customer_portal"):
            with pytest.raises(portal.PortalDataError):
                portal.build_customer_principal(verified_email="demo@example.com")
    assert "CUSTOMER_PORTAL_DB_UNAVAILABLE type=None" in caplog.text
    assert "demo@example.com" not in caplog.text


def test_unauthorised_oidc_email_shows_no_customer_data(seed_module):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}
    app.query_params = {"portal": "customer"}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims("not-allowed@example.com")),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)
    visible = _visible_text(app)
    assert "chưa được cấp quyền" in visible
    assert seed_module.LOT_A1 not in visible
    assert seed_module.LOT_B1 not in visible
    assert seed_module.FOREIGN_SENTINEL not in visible


def test_no_lots_state_is_safe_on_refresh(seed_module):
    db = _db(seed_module, negative_cases=False)
    db.customers.insert_one({
        "id": "CUST-EMPTY",
        "name": "Khách không có lô",
        portal.PORTAL_ACCESS_EMAIL_FIELD: "portal.empty@example.com",
    })
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims("portal.empty@example.com")),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        _assert_no_exceptions(app)
        assert "Chưa có lô hàng nào được công bố" in _visible_text(app)
        # A rerun/refresh rebuilds the principal from OIDC + MongoDB.
        app.run()
    _assert_no_exceptions(app)
    assert seed_module.LOT_A1 not in _visible_text(app)


@pytest.mark.parametrize(
    "state",
    [
        oidc.OidcSessionState(oidc.STATE_CONFIG_ERROR, reason="oidc_config_incomplete"),
        oidc.OidcSessionState(oidc.STATE_EXPIRED, reason="identity_expired"),
        oidc.OidcSessionState(oidc.STATE_DENIED, reason="audience_mismatch"),
    ],
)
def test_bad_oauth_return_states_have_no_data(seed_module, state):
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}
    with patch("views.web_app.customer_portal_oidc.current_oidc_session", return_value=state):
        app.run()
    _assert_no_exceptions(app)
    visible = _visible_text(app)
    assert seed_module.LOT_A1 not in visible
    assert seed_module.FOREIGN_SENTINEL not in visible
    assert "Đăng xuất" in visible


def test_logout_clears_dashboard_before_next_run(seed_module):
    db = _db(seed_module, negative_cases=False)
    claims_state = {"claims": _claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)}
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.secrets = {"auth": FAKE_AUTH}

    def _clear_claims():
        claims_state["claims"] = {}

    with (
        patch("streamlit.user_info._get_user_info", side_effect=lambda: claims_state["claims"]),
        patch.object(portal, "get_db", return_value=db),
        patch("views.customer_dashboard.oidc.logout_customer", side_effect=_clear_claims),
        patch("views.web_app.require_login", return_value=None),
    ):
        app.run()
        assert seed_module.LOT_A1 in _portal_text(app)
        _click(app, "customer_portal_logout")
    _assert_no_exceptions(app)
    visible = _visible_text(app)
    assert app.get("bidi_component") == []
    assert seed_module.LOT_A1 not in json.dumps(visible)
    assert seed_module.LOT_A2 not in json.dumps(visible)
    assert "Phiên đăng nhập đã kết thúc" in visible or "Đăng nhập khách hàng bằng Google" in visible
