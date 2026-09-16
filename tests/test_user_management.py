"""LOGI_USER_MANAGEMENT_01 — focused acceptance for the Admin write path.

Every write goes: typed event → Admin RBAC (core.auth) → fresh load_users()
→ core.users transform → core.database writer → audit → fresh load_users()
→ password-free public readback. Transport is the isolated staging database
(mongomock) running the CURRENT canonical writers unchanged; production is
never touched.
"""

from __future__ import annotations

import pytest

from views import logi_sandbox
from views import logi_view_model as vm
from views import user_management as um

SECRET_MARKERS = ("pbkdf2_sha256$",)


@pytest.fixture()
def staging():
    """A clean isolated staging database + a deterministic Admin actor."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    _as_admin()
    yield transport
    logi_sandbox.reset_backend()


def _as_admin(username: str = "staging.admin") -> None:
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "display_name": "Staging Admin",
        "role": "admin", "user_id": f"ID-{username}",
    }


def _as(role: str, username: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "display_name": username, "role": role,
        "user_id": f"ID-{username}",
    }


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = um.consume_user_management_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _create_admin_account(seq_fn, username: str = "boss.admin") -> dict:
    """Seed ONE extra active Admin so lockout-guard tests have two to work with."""
    out = _dispatch(seq_fn, "user_create", {
        "username": username, "displayName": "Boss Admin", "role": "admin",
        "password": "admin-pass-01", "confirmPassword": "admin-pass-01",
        "requestId": f"REQ-SEED-{username}",
    })
    assert out["ok"], out["error"]
    return out


# ---------------------------------------------------------------------------
# 1–2. CREATE Sale / Support accounts
# ---------------------------------------------------------------------------

def test_admin_creates_a_sale_account(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "lan.sale", "displayName": "Lan Sale", "role": "sale",
        "email": "lan.sale@example.com",
        "password": "sale-passphrase-1", "confirmPassword": "sale-passphrase-1",
        "requestId": "REQ-CREATE-SALE-1",
    })
    assert out["ok"], out["error"]
    assert out["requestId"] == "REQ-CREATE-SALE-1"
    assert out["readback"]["username"] == "lan.sale"
    assert out["readback"]["role"] == "sale"
    assert out["readback"]["active"] is True
    assert "password_hash" not in out["readback"]
    from core.database import load_users
    assert "lan.sale" in load_users()


def test_admin_creates_a_support_account(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "minh.support", "displayName": "Minh Support", "role": "support",
        "password": "support-passphrase-1", "confirmPassword": "support-passphrase-1",
        "requestId": "REQ-CREATE-SUPPORT-1",
    })
    assert out["ok"], out["error"]
    assert out["readback"]["role"] == "support"


# ---------------------------------------------------------------------------
# 3. duplicate username CREATE is refused; existing user unchanged
# ---------------------------------------------------------------------------

def test_duplicate_create_is_refused_and_existing_user_unchanged(staging, event_seq):
    first = _dispatch(event_seq, "user_create", {
        "username": "dup.user", "displayName": "First", "role": "sale",
        "password": "first-passphrase-1", "confirmPassword": "first-passphrase-1",
        "requestId": "REQ-DUP-1",
    })
    assert first["ok"], first["error"]

    from core.database import load_users
    before = dict(load_users()["dup.user"])

    second = _dispatch(event_seq, "user_create", {
        "username": "dup.user", "displayName": "Second — should never land",
        "role": "admin",
        "password": "second-passphrase-1", "confirmPassword": "second-passphrase-1",
        "requestId": "REQ-DUP-2",
    })
    assert second["ok"] is False
    assert "đã tồn tại" in second["error"]

    after = load_users()["dup.user"]
    assert after == before, "duplicate CREATE must never overwrite the existing account"
    assert after["display_name"] == "First"
    assert after["role"] == "sale"


# ---------------------------------------------------------------------------
# 4. new account authenticates with its password
# ---------------------------------------------------------------------------

def test_new_account_authenticates_with_its_password(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "auth.check", "displayName": "Auth Check", "role": "sale",
        "password": "check-my-password-1", "confirmPassword": "check-my-password-1",
        "requestId": "REQ-AUTH-1",
    })
    assert out["ok"], out["error"]

    from core.database import load_users
    from core.users import authenticate
    doc = load_users()["auth.check"]
    identity = authenticate(doc, "check-my-password-1")
    assert identity is not None
    assert identity["role"] == "sale"
    assert authenticate(doc, "wrong-password") is None


# ---------------------------------------------------------------------------
# 5. role change reflects in canonical document + public projection
# ---------------------------------------------------------------------------

def test_admin_changes_role_and_projection_reflects_it(staging, event_seq):
    created = _dispatch(event_seq, "user_create", {
        "username": "role.change", "displayName": "Role Change", "role": "sale",
        "password": "role-change-pass-1", "confirmPassword": "role-change-pass-1",
        "requestId": "REQ-ROLE-CREATE",
    })
    assert created["ok"], created["error"]

    out = _dispatch(event_seq, "user_role_set", {
        "username": "role.change", "role": "support", "requestId": "REQ-ROLE-1",
    })
    assert out["ok"], out["error"]
    assert out["readback"]["role"] == "support"

    from core.database import load_users
    assert load_users()["role.change"]["role"] == "support"


def test_role_change_rejects_unsupported_role(staging, event_seq):
    _dispatch(event_seq, "user_create", {
        "username": "role.bad", "displayName": "Role Bad", "role": "sale",
        "password": "role-bad-pass-01", "confirmPassword": "role-bad-pass-01",
        "requestId": "REQ-ROLE-BAD-CREATE",
    })
    out = _dispatch(event_seq, "user_role_set", {
        "username": "role.bad", "role": "manager", "requestId": "REQ-ROLE-BAD",
    })
    assert out["ok"] is False
    assert "Vai trò" in out["error"]


# ---------------------------------------------------------------------------
# 6–7. deactivate / reactivate — authentication follows real state
# ---------------------------------------------------------------------------

def test_deactivate_then_reactivate_account(staging, event_seq):
    _dispatch(event_seq, "user_create", {
        "username": "toggle.me", "displayName": "Toggle Me", "role": "sale",
        "password": "toggle-pass-0001", "confirmPassword": "toggle-pass-0001",
        "requestId": "REQ-TOGGLE-CREATE",
    })
    from core.database import load_users
    from core.users import authenticate

    off = _dispatch(event_seq, "user_active_set", {
        "username": "toggle.me", "active": False, "requestId": "REQ-TOGGLE-OFF",
    })
    assert off["ok"], off["error"]
    assert off["readback"]["active"] is False
    doc = load_users()["toggle.me"]
    assert authenticate(doc, "toggle-pass-0001") is None, "deactivated account must not authenticate"

    on = _dispatch(event_seq, "user_active_set", {
        "username": "toggle.me", "active": True, "requestId": "REQ-TOGGLE-ON",
    })
    assert on["ok"], on["error"]
    assert on["readback"]["active"] is True
    doc = load_users()["toggle.me"]
    assert authenticate(doc, "toggle-pass-0001") is not None, "reactivated account must authenticate again"


# ---------------------------------------------------------------------------
# 8. set new password — old fails, new succeeds
# ---------------------------------------------------------------------------

def test_password_reset_old_fails_new_succeeds(staging, event_seq):
    _dispatch(event_seq, "user_create", {
        "username": "pwd.reset", "displayName": "Pwd Reset", "role": "sale",
        "password": "old-passphrase-01", "confirmPassword": "old-passphrase-01",
        "requestId": "REQ-PWD-CREATE",
    })
    out = _dispatch(event_seq, "user_password_reset", {
        "username": "pwd.reset", "newPassword": "new-passphrase-02",
        "confirmPassword": "new-passphrase-02", "requestId": "REQ-PWD-1",
    })
    assert out["ok"], out["error"]
    assert "password_hash" not in out["readback"]

    from core.database import load_users
    from core.users import authenticate
    doc = load_users()["pwd.reset"]
    assert authenticate(doc, "old-passphrase-01") is None
    assert authenticate(doc, "new-passphrase-02") is not None


def test_password_reset_requires_matching_confirmation(staging, event_seq):
    _dispatch(event_seq, "user_create", {
        "username": "pwd.mismatch", "displayName": "Pwd Mismatch", "role": "sale",
        "password": "abcdefgh-01", "confirmPassword": "abcdefgh-01",
        "requestId": "REQ-PWD-M-CREATE",
    })
    out = _dispatch(event_seq, "user_password_reset", {
        "username": "pwd.mismatch", "newPassword": "one-password-1",
        "confirmPassword": "different-password-2", "requestId": "REQ-PWD-M-1",
    })
    assert out["ok"] is False
    assert "khớp" in out["error"]


def test_create_requires_matching_confirmation(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "create.mismatch", "displayName": "X", "role": "sale",
        "password": "one-password-1", "confirmPassword": "different-2",
        "requestId": "REQ-CREATE-MISMATCH",
    })
    assert out["ok"] is False
    assert "khớp" in out["error"]
    from core.database import load_users
    assert "create.mismatch" not in load_users()


# ---------------------------------------------------------------------------
# 9. last-active-Admin lockout guard
# ---------------------------------------------------------------------------

def test_cannot_deactivate_the_last_active_admin(staging, event_seq):
    """Staging seeds exactly one Admin (staging.admin is the acting session,
    but the canonical seed's Admin account is 'admin' — deactivate THAT one
    while it is the sole active Admin)."""
    from core.database import load_users

    users = load_users()
    admins = [u for u, d in users.items() if str(d.get("role", "")).strip().lower() == "admin" and d.get("active", True)]
    assert len(admins) == 1, f"fixture expectation drifted: {admins}"
    sole_admin = admins[0]

    out = _dispatch(event_seq, "user_active_set", {
        "username": sole_admin, "active": False, "requestId": "REQ-LOCKOUT-1",
    })
    assert out["ok"] is False
    assert "Admin đang hoạt động cuối cùng" in out["error"]
    assert load_users()[sole_admin]["active"] is True


def test_cannot_demote_the_last_active_admin(staging, event_seq):
    from core.database import load_users

    users = load_users()
    sole_admin = next(u for u, d in users.items() if str(d.get("role", "")).strip().lower() == "admin" and d.get("active", True))

    out = _dispatch(event_seq, "user_role_set", {
        "username": sole_admin, "role": "support", "requestId": "REQ-LOCKOUT-2",
    })
    assert out["ok"] is False
    assert "Admin đang hoạt động cuối cùng" in out["error"]
    assert load_users()[sole_admin]["role"].strip().lower() == "admin"


def test_can_deactivate_an_admin_when_another_active_admin_remains(staging, event_seq):
    from core.database import load_users

    users = load_users()
    sole_admin = next(u for u, d in users.items() if str(d.get("role", "")).strip().lower() == "admin" and d.get("active", True))
    _create_admin_account(event_seq, "second.admin")

    out = _dispatch(event_seq, "user_active_set", {
        "username": sole_admin, "active": False, "requestId": "REQ-LOCKOUT-3",
    })
    assert out["ok"], out["error"]
    assert load_users()[sole_admin]["active"] is False


# ---------------------------------------------------------------------------
# 10. non-Admin mutation is refused server-side
# ---------------------------------------------------------------------------

def test_non_admin_create_is_refused(staging, event_seq):
    _as("sale", "sale.user")
    out = _dispatch(event_seq, "user_create", {
        "username": "sneaky", "displayName": "Sneaky", "role": "admin",
        "password": "sneaky-pass-001", "confirmPassword": "sneaky-pass-001",
        "requestId": "REQ-NONADMIN-CREATE",
    })
    assert out["ok"] is False
    assert "Admin" in out["error"]
    from core.database import load_users
    assert "sneaky" not in load_users()


def test_non_admin_role_set_is_refused(staging, event_seq):
    _as_admin()
    _dispatch(event_seq, "user_create", {
        "username": "target.user", "displayName": "Target", "role": "sale",
        "password": "target-pass-0001", "confirmPassword": "target-pass-0001",
        "requestId": "REQ-TARGET-CREATE",
    })
    _as("support", "support.user")
    out = _dispatch(event_seq, "user_role_set", {
        "username": "target.user", "role": "admin", "requestId": "REQ-NONADMIN-ROLE",
    })
    assert out["ok"] is False
    from core.database import load_users
    assert load_users()["target.user"]["role"] == "sale"


def test_non_admin_active_set_is_refused(staging, event_seq):
    _as_admin()
    _dispatch(event_seq, "user_create", {
        "username": "target.active", "displayName": "Target Active", "role": "sale",
        "password": "target-pass-0002", "confirmPassword": "target-pass-0002",
        "requestId": "REQ-TARGET-ACTIVE-CREATE",
    })
    _as("viewer", "viewer.user")
    out = _dispatch(event_seq, "user_active_set", {
        "username": "target.active", "active": False, "requestId": "REQ-NONADMIN-ACTIVE",
    })
    assert out["ok"] is False
    from core.database import load_users
    assert load_users()["target.active"]["active"] is True


def test_non_admin_password_reset_is_refused(staging, event_seq):
    _as_admin()
    _dispatch(event_seq, "user_create", {
        "username": "target.pwd", "displayName": "Target Pwd", "role": "sale",
        "password": "target-pass-0003", "confirmPassword": "target-pass-0003",
        "requestId": "REQ-TARGET-PWD-CREATE",
    })
    _as("sale", "sale.attacker")
    out = _dispatch(event_seq, "user_password_reset", {
        "username": "target.pwd", "newPassword": "hacked-pass-01",
        "confirmPassword": "hacked-pass-01", "requestId": "REQ-NONADMIN-PWD",
    })
    assert out["ok"] is False
    from core.database import load_users
    from core.users import authenticate
    doc = load_users()["target.pwd"]
    assert authenticate(doc, "target-pass-0003") is not None
    assert authenticate(doc, "hacked-pass-01") is None


def test_unauthenticated_mutation_is_refused(staging, event_seq):
    import streamlit as st

    st.session_state["current_user"] = {}
    out = _dispatch(event_seq, "user_create", {
        "username": "ghost", "displayName": "Ghost", "role": "sale",
        "password": "ghost-pass-0001", "confirmPassword": "ghost-pass-0001",
        "requestId": "REQ-GHOST",
    })
    assert out["ok"] is False


# ---------------------------------------------------------------------------
# 13. password/password_hash never appears in outcomes / view-model
# ---------------------------------------------------------------------------

def test_no_password_material_in_outcome_or_view_model(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "secret.check", "displayName": "Secret Check", "role": "sale",
        "password": "super-secret-passphrase", "confirmPassword": "super-secret-passphrase",
        "requestId": "REQ-SECRET-1",
    })
    assert out["ok"], out["error"]
    dump = repr(out)
    assert "super-secret-passphrase" not in dump
    for marker in SECRET_MARKERS:
        assert marker not in dump

    model = vm.build_view_model()
    model_dump = repr(model)
    for marker in SECRET_MARKERS:
        assert marker not in model_dump
    assert "super-secret-passphrase" not in model_dump

    for row in model["userAccess"]["users"]:
        assert "password_hash" not in row
        assert "password" not in row

    for write in model.get("lastWrites") or []:
        assert "password" not in write
        assert "newPassword" not in write
        assert "confirmPassword" not in write
        if isinstance(write.get("readback"), dict):
            assert "password_hash" not in write["readback"]


def test_audit_log_never_carries_password_material(staging, event_seq):
    out = _dispatch(event_seq, "user_create", {
        "username": "audit.check", "displayName": "Audit Check", "role": "sale",
        "password": "audit-secret-passphrase", "confirmPassword": "audit-secret-passphrase",
        "requestId": "REQ-AUDIT-1",
    })
    assert out["ok"], out["error"]

    from core.database import load_audit_logs
    rows = load_audit_logs("user", "audit.check", limit=10)
    assert rows
    dump = repr(rows)
    assert "audit-secret-passphrase" not in dump
    for marker in SECRET_MARKERS:
        assert marker not in dump


# ---------------------------------------------------------------------------
# 16–17. no RBAC/role widening, no delete path
# ---------------------------------------------------------------------------

def test_role_permissions_matrix_unchanged():
    from core.auth import ROLE_PERMISSIONS

    assert set(ROLE_PERMISSIONS["admin"]) == {"*"}
    assert "user_management" not in ROLE_PERMISSIONS.get("sale", set())
    assert "user_management" not in ROLE_PERMISSIONS.get("support", set())


def test_no_delete_event_exists():
    assert "user_delete" not in um.USER_MANAGEMENT_EVENTS
    assert not any("delete" in name for name in um.USER_MANAGEMENT_EVENTS)
