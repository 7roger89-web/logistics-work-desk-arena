"""LOGI_USER_MANAGEMENT_01 — SESSION_TRUTH_REPAIR for ``core.auth.require_login``.

``require_login()`` used to trust ``st.session_state.current_user`` verbatim
once a session existed, so an Admin changing another operator's role, or
deactivating their account, never applied until that operator logged out and
back in. This module tests the narrow fix: on every rerun while
``AUTH_REQUIRED`` is on, the session identity is re-derived from the SAME
canonical store (``core.database.load_users``) the rest of the app reads —
no new session database, no JWT, no re-authentication.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.users import build_user_document, change_password, set_active


def _users_db():
    return {
        "sale.one": build_user_document(
            username="sale.one", password="sale-passphrase-1",
            display_name="Sale One", role="sale", created_by="admin",
        ),
        # A second account keeps ``user_count`` > 0 once sale.one is
        # deactivated/removed, so require_login() falls through to the
        # ordinary login screen rather than the (unrelated) bootstrap path.
        "admin.one": build_user_document(
            username="admin.one", password="admin-passphrase-1",
            display_name="Admin One", role="admin", created_by="admin",
        ),
    }


class _FakeSessionState(dict):
    """dict that also supports the ``st.session_state.current_user`` attribute form."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


def _session_st(current_user: dict, users: dict):
    """A minimal fake ``streamlit`` module surface require_login() touches.

    A ``MagicMock`` base means any other Streamlit call the login-screen
    fallback path might make (``st.warning``/``st.markdown``/``st.text_input``
    /…) is absorbed harmlessly instead of raising — these tests only assert
    on the SESSION identity require_login() returns, not on the rendered
    login form.
    """
    mock = MagicMock()
    mock.session_state = _FakeSessionState({"current_user": dict(current_user)} if current_user else {})
    return mock


@pytest.fixture()
def patched_load_users():
    users = _users_db()
    with patch("core.database.load_users", return_value=users):
        yield users


def test_role_change_is_picked_up_on_next_rerun(patched_load_users):
    from core import auth

    users = patched_load_users
    session_user = {"username": "sale.one", "display_name": "Sale One", "role": "sale"}
    mock_st = _session_st(session_user, users)
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        # Simulate an Admin promoting sale.one to support in the canonical store.
        users["sale.one"] = dict(users["sale.one"], role="support")
        result = auth.require_login()
        assert result is not None
        assert result["role"] == "support"
        assert mock_st.session_state["current_user"]["role"] == "support"


def test_deactivated_session_is_no_longer_trusted(patched_load_users):
    from core import auth

    users = patched_load_users
    session_user = {"username": "sale.one", "display_name": "Sale One", "role": "sale"}
    mock_st = _session_st(session_user, users)
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        users["sale.one"] = set_active(users["sale.one"], False, actor="admin")
        result = auth.require_login()
        # No password is required again; the deactivated session is simply
        # cleared so the caller falls through to the login screen.
        assert result is None
        assert "current_user" not in mock_st.session_state


def test_deleted_account_session_is_no_longer_trusted(patched_load_users):
    from core import auth

    users = patched_load_users
    session_user = {"username": "sale.one", "display_name": "Sale One", "role": "sale"}
    mock_st = _session_st(session_user, users)
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        del users["sale.one"]
        result = auth.require_login()
        assert result is None
        assert "current_user" not in mock_st.session_state


def test_password_change_alone_does_not_invalidate_the_session(patched_load_users):
    """Changing a password must not force a re-login on every rerun."""
    from core import auth

    users = patched_load_users
    session_user = {"username": "sale.one", "display_name": "Sale One", "role": "sale"}
    mock_st = _session_st(session_user, users)
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        users["sale.one"] = change_password(users["sale.one"], "new-passphrase-2", actor="admin")
        result = auth.require_login()
        assert result is not None
        assert result["username"] == "sale.one"
        assert result["role"] == "sale"


def test_unchanged_session_is_not_rewritten(patched_load_users):
    from core import auth

    users = patched_load_users
    session_user = {"username": "sale.one", "display_name": "Sale One", "role": "sale"}
    mock_st = _session_st(session_user, users)
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
        assert result is not None
        assert result["role"] == "sale"


@pytest.mark.parametrize("role", ["admin", "sale"])
def test_canonical_read_failure_fails_closed_not_open(patched_load_users, role):
    """CONTROL_TOWER_SECURITY_REPAIR_01 — a canonical read failure must never
    preserve stale session authority.

    A stale/compromised assumption ("transient read failure fails open") let
    an already-authenticated session keep acting under its OLD role/identity
    whenever ``load_users`` raised while revalidating it. That is fail-open
    authorization: if the canonical store cannot be read, the browser must
    NOT get to keep whatever role/active status it already had cached.

    This must behave exactly like a missing/inactive account: the session is
    cleared and ``require_login()`` returns ``None`` — mirroring the fresh
    login path (`_authenticate`), which already returns ``None`` on the same
    kind of failure instead of granting access.

    This test fails if ``_revalidate_session`` is reverted to
    ``except Exception: return dict(session_user)``.
    """
    from core import auth

    session_user = {"username": "sale.one", "display_name": "Sale One", "role": role}
    mock_st = _session_st(session_user, {})
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True), \
         patch("core.database.load_users", side_effect=RuntimeError("boom")), \
         patch.object(auth, "_render_bootstrap_setup"):
        result = auth.require_login()
        assert result is None
        assert "current_user" not in mock_st.session_state


def test_bootstrap_first_admin_flow_still_runs_with_no_session_and_no_users():
    """ACCEPTANCE 14 — the existing bootstrap-first-Admin flow is untouched.

    With no session identity and an empty user store, require_login() must
    still fall through to the bootstrap screen exactly as before — the
    session-truth-repair fix only activates once ``session_user`` is truthy.
    """
    from core import auth

    mock_st = _session_st({}, {})
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True), \
         patch("core.database.load_users", return_value={}), \
         patch.object(auth, "_render_bootstrap_setup") as bootstrap:
        result = auth.require_login()
        assert result is None
        bootstrap.assert_called_once()


def test_local_admin_mode_is_unaffected_by_session_revalidation(patched_load_users):
    """AUTH_REQUIRED=false keeps the historical Local Admin shortcut intact."""
    from core import auth

    mock_st = _session_st({}, {})
    with patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", False):
        result = auth.require_login()
        assert result == {"username": "local-admin", "display_name": "Local Admin", "role": "admin"}
        assert mock_st.session_state["current_user"] == result
