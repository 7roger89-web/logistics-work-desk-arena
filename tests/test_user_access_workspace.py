"""LOGI_USER_ACCESS_WORKSPACE_01 — focused tests for the read-only /nguoi-dung page.

The workspace is a *presentation* slice over capability that already exists
(core.database.load_users, core.users public view, core.auth ROLE_PERMISSIONS,
core.config.AUTH_REQUIRED).  These tests therefore assert passthrough and
absence-of-invention rather than new behaviour:

* every displayed account row equals the canonical ``public_identity`` fields
  and never carries credential material — even when the source document has
  one;
* an empty user store renders an honest empty state, never a sample user;
* roles and permissions come verbatim from the single canonical matrix;
* the current-auth-mode statement matches the real ``AUTH_REQUIRED`` value;
* the staging view-model exposes the slice and no user-management event was
  added with the page.

Production database is never used.
"""

from __future__ import annotations

import pytest

from views import user_access as ua

SECRET_KEY_MARKERS = ("password", "passwd", "hash", "token", "secret", "apikey", "api_key")
SECRET_VALUE_MARKERS = ("pbkdf2_sha256$", "sha256:")


def _admin() -> dict[str, str]:
    return {
        "user_id": "admin-fixture-01",
        "username": "admin.fixture",
        "display_name": "Admin Fixture",
        "role": "admin",
    }


def _real_document(username: str = "anh.sale", role: str = "sale") -> dict:
    """A user document built by the CANONICAL builder — it carries a real hash."""
    from core.users import build_user_document

    return build_user_document(
        username=username,
        password="super-secret-passphrase",
        display_name="Anh Sale",
        role=role,
        email="anh.sale@example.com",
        created_by="fixture",
    )


# ---------------------------------------------------------------------------
# passthrough, never paraphrase — and never credential material
# ---------------------------------------------------------------------------


def test_user_rows_equal_the_canonical_public_identity_verbatim():
    from core.users import public_identity, public_summary

    docs = [_real_document("anh.sale", "sale"), _real_document("ba.support", "support")]
    projection = ua.user_access_projection(users=docs)

    assert projection["users"] == public_summary(docs)
    # Canonical order: role first ("sale" < "support"), then display name.
    assert projection["users"][0]["username"] == "anh.sale"
    assert projection["users"][1]["username"] == "ba.support"
    for row, doc in zip(projection["users"], public_summary(docs)):
        assert row == public_identity(doc)
        assert set(row) == set(ua.USER_FIELDS)


def test_credential_material_never_reaches_the_payload():
    docs = [_real_document("anh.sale", "sale")]
    projection = ua.user_access_projection(users=docs, current_user=_admin())

    raw = repr(projection)
    for marker in SECRET_VALUE_MARKERS:
        assert marker not in raw, f"secret material {marker!r} leaked into the payload"


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_keys(item)


def test_no_secret_named_field_is_delivered_anywhere():
    projection = ua.user_access_projection(
        users=[_real_document("anh.sale", "sale")],
        current_user=_admin(),
        auth_required=True,
    )
    for key in _walk_keys(projection):
        lowered = key.lower()
        assert not any(marker in lowered for marker in SECRET_KEY_MARKERS), (
            f"secret-named field {key!r} delivered to the frontend"
        )


def test_unknown_source_fields_are_not_invented_or_forwarded():
    doc = _real_document("anh.sale", "sale")
    doc["internal_security_note"] = "rotate after offboarding"
    doc["login_attempts"] = 42
    projection = ua.user_access_projection(users=[doc])

    row = projection["users"][0]
    assert "internal_security_note" not in row
    assert "login_attempts" not in row
    assert set(row) == set(ua.USER_FIELDS)


# ---------------------------------------------------------------------------
# honest empty state and bounded payload
# ---------------------------------------------------------------------------


def test_empty_user_store_is_honest_not_fabricated():
    projection = ua.user_access_projection(users=[], current_user=_admin())

    assert projection["users"] == []
    assert projection["counts"]["userCount"] == 0
    assert projection["counts"]["userShown"] == 0
    assert projection["counts"]["activeCount"] == 0
    # The canonical roles/permissions still exist even with no account yet.
    assert projection["roles"]["assignable"]
    assert projection["permissionMatrix"]


def test_payload_is_bounded_and_truncation_is_stated():
    docs = [_real_document(f"user.{index:03d}", "sale") for index in range(ua.MAX_USERS + 7)]
    projection = ua.user_access_projection(users=docs)

    assert projection["counts"]["userCount"] == len(docs)
    assert projection["counts"]["userShown"] == ua.MAX_USERS
    assert len(projection["users"]) == ua.MAX_USERS


# ---------------------------------------------------------------------------
# canonical RBAC truth — unchanged, unmerged, unrenamed
# ---------------------------------------------------------------------------


def test_assignable_roles_are_exactly_the_canonical_supported_roles():
    from core.users import SUPPORTED_ROLES

    projection = ua.user_access_projection(users=[])
    assert projection["roles"]["assignable"] == [str(role) for role in SUPPORTED_ROLES]


def test_permission_matrix_is_the_canonical_role_permissions_verbatim():
    from core.auth import ROLE_PERMISSIONS

    projection = ua.user_access_projection(users=[])
    delivered = {row["role"]: row["permissions"] for row in projection["permissionMatrix"]}

    assert set(delivered) == set(ROLE_PERMISSIONS)
    for role, permissions in ROLE_PERMISSIONS.items():
        assert delivered[role] == sorted(str(permission) for permission in permissions)
        row = next(r for r in projection["permissionMatrix"] if r["role"] == role)
        assert row["wildcard"] == ("*" in permissions)
        assert row["permissionCount"] == len(permissions)


def test_legacy_roles_are_reported_separately_not_merged():
    from core.auth import ROLE_PERMISSIONS
    from core.users import SUPPORTED_ROLES

    projection = ua.user_access_projection(users=[])
    supported = {str(role) for role in SUPPORTED_ROLES}
    expected_legacy = sorted(set(ROLE_PERMISSIONS) - supported)

    assert projection["roles"]["legacy"] == expected_legacy
    assert "viewer" in projection["roles"]["legacy"]


# ---------------------------------------------------------------------------
# current user indicator + auth-mode honesty
# ---------------------------------------------------------------------------


def test_current_user_indicator_matches_the_session_identity():
    from core.auth import ROLE_PERMISSIONS

    projection = ua.user_access_projection(users=[], current_user=_admin())
    current = projection["currentUser"]

    assert current["present"] is True
    assert current["username"] == "admin.fixture"
    assert current["role"] == "admin"
    assert current["wildcard"] is True
    assert current["permissions"] == sorted(str(p) for p in ROLE_PERMISSIONS["admin"])


def test_anonymous_session_reports_no_current_user():
    projection = ua.user_access_projection(users=[], current_user={})
    assert projection["currentUser"]["present"] is False


def test_local_admin_mode_is_named_honestly():
    projection = ua.user_access_projection(users=[], auth_required=False)
    mode = projection["authMode"]

    assert mode["required"] is False
    assert mode["mode"] == "local_admin"
    assert "local-admin" in mode["note"]
    assert "KHÔNG phải đăng nhập đa người dùng" in mode["note"]


def test_multi_user_mode_is_named_honestly():
    projection = ua.user_access_projection(users=[], auth_required=True)
    mode = projection["authMode"]

    assert mode["required"] is True
    assert mode["mode"] == "multi_user"


# ---------------------------------------------------------------------------
# scope honesty
# ---------------------------------------------------------------------------


def test_projection_declares_read_only_scope_limits():
    projection = ua.user_access_projection(users=[])

    assert projection["classification"] == "READ_ONLY_READY"
    assert projection["readOnly"] is True
    assert any("CHỈ ĐỌC" in line for line in projection["unavailable"])
    assert any("hash" in line for line in projection["unavailable"])


def test_no_user_management_event_was_added():
    from views import logi_view_model as vm

    # The page needs no server-side action: no event, no writer bridge.
    assert not any(
        token in name
        for name in vm.ALL_EVENTS
        for token in ("user_create", "user_update", "user_delete", "user_disable",
                      "user_role", "password_reset", "invite_user")
    )


# ---------------------------------------------------------------------------
# the bridge that activates the route
# ---------------------------------------------------------------------------


@pytest.fixture()
def staging():
    """Clean, isolated mongomock staging database with the deterministic actor."""
    import streamlit as st

    from views import logi_sandbox

    previous = st.session_state.get("current_user")
    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    logi_sandbox.reset_backend()
    if previous is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = previous


def test_view_model_exposes_the_user_access_slice_on_staging(staging):
    from views import logi_view_model as vm

    model = vm.build_view_model()
    user_access = model["userAccess"]

    assert user_access["readOnly"] is True
    assert user_access["classification"] == "READ_ONLY_READY"
    # Staging seeds three real reference accounts (admin/thuhang/minhtu): the
    # canonical rows must pass through, not be replaced by samples.
    assert user_access["counts"]["userCount"] == 3
    assert {row["username"] for row in user_access["users"]} == {"admin", "thuhang", "minhtu"}
    # The canonical matrix still arrives, verbatim.
    assert user_access["counts"]["roleCount"] > 0
    # The current-user indicator reflects the staging actor.
    assert user_access["currentUser"]["present"] is True
    assert user_access["currentUser"]["username"] == "staging.support"
    # No credential material anywhere in the delivered slice.
    for marker in SECRET_VALUE_MARKERS:
        assert marker not in repr(user_access)
    for key in _walk_keys(user_access):
        lowered = key.lower()
        assert not any(marker in lowered for marker in SECRET_KEY_MARKERS), (
            f"secret-named field {key!r} delivered to the frontend"
        )
