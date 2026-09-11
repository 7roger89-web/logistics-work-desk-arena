"""LOGI_USER_ACCESS_WORKSPACE_01 — bounded, READ-ONLY user/access projection for /nguoi-dung.

This is deliberately **not** an IAM platform, SSO or a new identity store.  It
presents the authentication / user / RBAC capability that ALREADY exists in the
application, assembled for the ``/nguoi-dung`` reader:

    core.database.load_users()   → the authoritative user documents (MongoDB)
    core.users.public_identity() → the canonical password-free public view
    core.auth.ROLE_PERMISSIONS   → the single role → permission matrix
    core.users.SUPPORTED_ROLES   → the roles a user account can actually hold
    core.config.AUTH_REQUIRED    → the truth about the current auth mode
    core.auth.current_user()     → who is looking at the page

Guarantees enforced by this module:

* No credential material: rows are built ONLY from ``public_identity``, which
  is a pick-list (user_id, username, display_name, email, role, active) —
  ``password_hash`` / ``password`` never enter the payload, not even to be
  masked.
* No invented RBAC fact: every permission shown comes verbatim from the one
  canonical ``ROLE_PERMISSIONS`` matrix.  Roles that the user store can assign
  (``SUPPORTED_ROLES``) and legacy compatibility roles are reported as
  separate, labelled groups — never merged into a fake role list.
* Auth-mode honesty: when ``AUTH_REQUIRED`` is off the app runs as a single
  Local Admin account.  The page says exactly that instead of presenting the
  deployment as multi-user production auth.
* No write path: this projection takes its inputs as arguments and performs no
  I/O and no mutation.  User management (create / update / deactivate) stays
  with the existing canonical writers in ``core.database``; this page exposes
  none of them yet, and says so in ``unavailable``.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

# Explicit limit: account lists on a work desk stay small; the payload is
# bounded and any truncation is stated, never hidden.
MAX_USERS = 100

CLASSIFICATION = "READ_ONLY_READY"

# The canonical public fields of a user account, in display order.  This is
# exactly what core.users.public_identity returns — nothing else is delivered.
USER_FIELDS = ("user_id", "username", "display_name", "email", "role", "active")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _role_row(role: str, permissions: Iterable[str]) -> dict[str, Any]:
    """One canonical matrix row — verbatim passthrough, no reinterpretation."""
    perms = [str(permission) for permission in permissions]
    return {
        "role": str(role),
        "permissions": sorted(perms),
        # "*" is the canonical admin wildcard; surfaced as its own flag so the
        # UI can say "toàn quyền" without treating it as a permission name.
        "wildcard": "*" in perms,
        "permissionCount": len(perms),
    }


def _current_user_view(current_user: Mapping[str, Any] | None) -> dict[str, Any]:
    """Who is looking — the same identity the header already shows."""
    from core.auth import _role_permissions  # the single canonical lookup

    user = dict(current_user or {})
    username = _text(user.get("username"))
    role = str(user.get("role") or "viewer").strip().lower()
    permissions = _role_permissions(role)
    return {
        "present": bool(username),
        "username": username,
        "displayName": _text(user.get("display_name") or user.get("full_name")) or username,
        "role": role,
        "permissions": sorted(str(permission) for permission in permissions),
        "wildcard": "*" in permissions,
    }


def _auth_mode_view(required: bool | None) -> dict[str, Any]:
    """Honest statement of the deployment's real authentication mode.

    Local Admin (``AUTH_REQUIRED`` off, the historical default) is one shared
    local account with admin rights — it is NOT multi-user production auth,
    and the page never presents it as one.
    """
    if required:
        return {
            "required": True,
            "mode": "multi_user",
            "label": "Đa người dùng (MongoDB)",
            "note": (
                "AUTH_REQUIRED đang bật: đăng nhập bằng tài khoản trong collection "
                "users (mật khẩu băm PBKDF2-SHA256). Việc quản trị tài khoản vẫn "
                "thuộc Admin trong core.database, không phải trang này."
            ),
        }
    return {
        "required": False,
        "mode": "local_admin",
        "label": "Local Admin (một tài khoản cục bộ)",
        "note": (
            "AUTH_REQUIRED đang tắt: ứng dụng chạy với một tài khoản cục bộ "
            "(local-admin) có vai trò admin. Đây KHÔNG phải đăng nhập đa người "
            "dùng thực sự; trang này hiển thị trung thực chế độ hiện có, không "
            "tự ý nâng cấp thành hệ thống xác thực mới."
        ),
    }


def _users_rows(users: Iterable[Mapping[str, Any]] | None) -> tuple[list[dict[str, Any]], int]:
    """Canonical public view of every account — pick-list, never block-list."""
    from core.users import public_identity

    documents = [doc for doc in (users or []) if isinstance(doc, Mapping)]
    rows = [public_identity(doc) for doc in documents]
    # Same canonical ordering as core.users.public_summary.
    rows.sort(key=lambda user: (str(user.get("role")), str(user.get("display_name"))))
    total = len(rows)
    return rows[:MAX_USERS], total


def user_access_projection(
    users: Iterable[Mapping[str, Any]] | None = None,
    current_user: Mapping[str, Any] | None = None,
    auth_required: bool | None = None,
) -> dict[str, Any]:
    """Assemble the ``/nguoi-dung`` user/access slice.  Pure read, pure build.

    ``auth_required`` defaults to the canonical ``core.config.AUTH_REQUIRED``
    so callers do not have to know the setting; tests may pass it explicitly.
    """
    if auth_required is None:
        from core.config import AUTH_REQUIRED

        auth_required = bool(AUTH_REQUIRED)

    from core.auth import ROLE_PERMISSIONS
    from core.users import SUPPORTED_ROLES

    rows, user_total = _users_rows(users)
    matrix = [_role_row(role, permissions) for role, permissions in ROLE_PERMISSIONS.items()]
    supported = [str(role) for role in SUPPORTED_ROLES]
    legacy = [row["role"] for row in matrix if row["role"] not in supported]
    active_count = sum(1 for row in rows if row.get("active"))
    current = _current_user_view(current_user)

    return {
        "classification": CLASSIFICATION,
        "readOnly": True,
        "authMode": _auth_mode_view(auth_required),
        "currentUser": current,
        "users": rows,
        "roles": {
            "assignable": supported,
            "legacy": legacy,
            "source": "core.users.SUPPORTED_ROLES + core.auth.ROLE_PERMISSIONS",
        },
        # The single canonical matrix, verbatim.  No role or permission name is
        # added, renamed or removed by this page.
        "permissionMatrix": matrix,
        "counts": {
            "userCount": user_total,
            "userShown": len(rows),
            "activeCount": active_count,
            "inactiveCount": len(rows) - active_count,
            "roleCount": len(matrix),
            "assignableRoleCount": len(supported),
        },
        # What this page explicitly does NOT provide.  These are honest scope
        # statements: the canonical writers exist in core.database but no
        # proven, safe UI write path is exposed yet — the page refuses to
        # pretend otherwise.
        "unavailable": [
            "Trang này CHỈ ĐỌC: không tạo / sửa / khóa / xóa tài khoản, không "
            "đổi mật khẩu, không gán vai trò. Các thao tác ghi vẫn nằm ở tầng "
            "core.database (save_user / update_user / delete_user) và chưa có "
            "kênh UI được chứng minh an toàn để mở.",
            "Không hiện mật khẩu, hash mật khẩu, token hay bất kỳ dữ liệu bí "
            "mật nào — danh sách tài khoản dùng đúng public view chuẩn của "
            "core.users.",
            "Không thêm vai trò mới hay quyền mới: ma trận dưới đây là nguyên "
            "văn ROLE_PERMISSIONS của core.auth.",
        ],
    }
