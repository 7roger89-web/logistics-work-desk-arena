"""Bounded QA diagnostic: real DB identity and presentation authorization."""
from unittest.mock import MagicMock

import pytest
from pymongo.database import Database

from core import config, database
from views import logi_sandbox, web_app


@pytest.fixture
def live_identity(monkeypatch):
    monkeypatch.setattr(config, "ENV_IDENTITY", "STAGING")
    monkeypatch.setattr(config, "MONGO_DB_NAME", "logistics_staging")
    monkeypatch.setattr(config, "MONGO_RELEASE_MODE", False)
    monkeypatch.setattr(logi_sandbox, "transport_name", lambda: "REAL_MONGO")
    db = MagicMock(spec=Database)
    db.name = "logistics_staging"
    monkeypatch.setattr(database, "get_db", lambda: db)
    return db


def test_real_staging_identity_and_preview_pass(live_identity, monkeypatch):
    assert all(web_app._staging_identity_checks().values())
    live_identity.command.assert_called_once_with("ping")
    monkeypatch.setattr(config, "ENV_IDENTITY", "PREVIEW")
    assert all(web_app._staging_identity_checks().values())


@pytest.mark.parametrize("setting,value", [
    ("ENV_IDENTITY", "PRODUCTION"),
    ("MONGO_DB_NAME", "logistics_db"),
    ("MONGO_RELEASE_MODE", True),
])
def test_wrong_effective_config_fails(live_identity, monkeypatch, setting, value):
    monkeypatch.setattr(config, setting, value)
    assert not all(web_app._staging_identity_checks().values())


@pytest.mark.parametrize("kind", ["mock", "wrong_database", "failed_ping", "guard_error"])
def test_transport_or_actual_database_fail_closed(live_identity, monkeypatch, kind):
    if kind == "mock":
        monkeypatch.setattr(database, "get_db", lambda: object())
    elif kind == "wrong_database":
        live_identity.name = "logistics_db"
    elif kind == "failed_ping":
        live_identity.command.side_effect = RuntimeError("SECRET_MUST_NOT_ESCAPE")
    else:
        def fail():
            raise RuntimeError("SECRET_MUST_NOT_ESCAPE")
        monkeypatch.setattr(database, "get_db", fail)
    result = web_app._staging_identity_checks()
    assert not all(result.values())
    assert all(type(v) is bool for v in result.values())
    assert "SECRET" not in str(result)


def test_sandbox_transport_cannot_pass_as_real(live_identity, monkeypatch):
    monkeypatch.setattr(logi_sandbox, "transport_name", lambda: "SANDBOX_STAGING")
    assert not all(web_app._staging_identity_checks().values())
    live_identity.command.assert_not_called()


@pytest.mark.parametrize("role,url", [
    ("support", "https://thu-log-g1-test.streamlit.app/?portal=internal"),
    ("admin", "https://production.streamlit.app/"),
    ("admin", "https://thu-log-g1-test.streamlit.app.evil.test/"),
])
def test_no_diagnostic_outside_admin_on_exact_staging_host(monkeypatch, role, url):
    ui = MagicMock()
    monkeypatch.setattr(web_app, "st", ui)
    monkeypatch.setattr(web_app, "_current_app_url", lambda: url)
    web_app._render_staging_identity_check({"role": role})
    ui.expander.assert_not_called()


def test_clicked_diagnostic_revalidates_admin_and_exposes_booleans_only(monkeypatch):
    from core import auth
    ui = MagicMock()
    ui.button.return_value = True
    monkeypatch.setattr(web_app, "st", ui)
    monkeypatch.setattr(web_app, "_current_app_url", lambda: "https://thu-log-g1-test.streamlit.app/")
    check = MagicMock(return_value={"expected condition": True})
    monkeypatch.setattr(web_app, "_staging_identity_checks", check)
    monkeypatch.setattr(auth, "fresh_session_identity_for_action", lambda: {"role": "support"})
    web_app._render_staging_identity_check({"role": "admin"})
    check.assert_not_called()
    monkeypatch.setattr(auth, "fresh_session_identity_for_action", lambda: {"role": "admin"})
    web_app._render_staging_identity_check({"role": "admin"})
    check.assert_called_once()
    ui.write.assert_called_once_with("PASS — expected condition")
    ui.success.assert_called_once_with("STAGING_RUNTIME_IDENTITY=PASS")
