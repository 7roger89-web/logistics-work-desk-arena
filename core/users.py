"""LOG-C15 — User identity store (pure logic, no I/O).

Authoritative user document model for the Logistics team:

- user_id: unique internal identity (never a free-text name)
- username: login identifier (lowercase, unique)
- display_name: business-facing name shown in the UI
- email: optional contact/login helper
- role: exactly one of SUPPORTED_ROLES
- active: bool; inactive users cannot authenticate
- password_hash: pbkdf2_sha256 produced by core.auth.hash_password (never plaintext)
- created_by / deactivated_by: actor provenance for admin actions

This module owns validation and in-memory transformation only. Persistence
lives in core.database (load_users / save_user / delete_user) so views keep a
single data path. No credentials, hashes, or secrets are printed anywhere.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

from core.auth import hash_password, verify_password

SUPPORTED_ROLES = ("admin", "sale", "support")

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,29}$")

MAX_DISPLAY_NAME_LENGTH = 60


class UserError(ValueError):
    """Raised for invalid user management input."""


def normalize_username(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if not USERNAME_RE.match(value):
        raise UserError(
            "Tên đăng nhập phải từ 3 đến 30 ký tự, chỉ gồm chữ thường, số, dấu chấm, gạch dưới hoặc gạch ngang."
        )
    return value


def normalize_role(raw: Any) -> str:
    role = str(raw or "").strip().lower()
    if role not in SUPPORTED_ROLES:
        raise UserError(f"Vai trò không được hỗ trợ: {role or '(trống)'}")
    return role


def build_user_document(
    username: str,
    password: str,
    display_name: str,
    role: str,
    active: bool = True,
    email: str = "",
    created_by: str = "system",
) -> dict[str, Any]:
    username = normalize_username(username)
    role = normalize_role(role)
    display = str(display_name or username).strip()[:MAX_DISPLAY_NAME_LENGTH]
    if not display:
        raise UserError("Tên hiển thị không được để trống.")
    if not password:
        raise UserError("Mật khẩu không được để trống.")
    if len(password) < 8:
        raise UserError("Mật khẩu cần ít nhất 8 ký tự.")
    email = str(email or "").strip().lower()
    return {
        "username": username,
        "display_name": display,
        "email": email,
        "role": role,
        "active": bool(active),
        "password_hash": hash_password(password),
        "active_states": [{"active": bool(active), "actor": str(created_by), "note": "user created"}],
        "created_by": str(created_by),
    }


def change_password(document: Mapping[str, Any], new_password: str, actor: str = "system") -> dict[str, Any]:
    if not new_password or len(new_password) < 8:
        raise UserError("Mật khẩu mới cần ít nhất 8 ký tự.")
    updated = dict(document)
    updated["password_hash"] = hash_password(new_password)
    updated["password_changed_by"] = str(actor)
    updated.pop("password", None)
    return updated


def authenticate(document: Mapping[str, Any], password: str) -> dict[str, Any] | None:
    """Return a public session identity when credentials and state are valid.

    Never distinguishes 'wrong password' from 'inactive' in an error message;
    both return None so failed authentication exposes no internal state.
    """
    if not verify_password(password, str(document.get("password_hash", ""))):
        return None
    if not document.get("active", True):
        return None
    username = str(document.get("username", ""))
    return {
        "user_id": str(document.get("user_id", username)),
        "username": username,
        "display_name": str(document.get("display_name", username)),
        "email": str(document.get("email", "")),
        "role": str(document.get("role", "support")),
    }


def public_identity(document: Mapping[str, Any]) -> dict[str, Any]:
    """Public view of a user document — never includes password material."""
    username = str(document.get("username", ""))
    return {
        "user_id": str(document.get("user_id", username)),
        "username": username,
        "display_name": str(document.get("display_name", username)),
        "email": str(document.get("email", "")),
        "role": str(document.get("role", "support")),
        "active": bool(document.get("active", True)),
    }


def public_summary(documents: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [public_identity(doc) for doc in documents],
        key=lambda user: (str(user.get("role")), str(user.get("display_name"))),
    )


def set_active(document: Mapping[str, Any], active: bool, actor: str = "system") -> dict[str, Any]:
    updated = dict(document)
    before = bool(updated.get("active", True))
    if before == bool(active):
        return updated
    updated["active"] = bool(active)
    states = list(updated.get("active_states", []))
    states.append({
        "active": bool(active),
        "actor": str(actor),
        "note": "user deactivated" if not active else "user reactivated",
    })
    updated["active_states"] = states
    updated["deactivated_by" if not active else "reactivated_by"] = str(actor)
    return updated


def redact_password_material(document: Mapping[str, Any]) -> dict[str, Any]:
    cleaned = dict(document)
    for key in ("password_hash", "password"):
        cleaned.pop(key, None)
    return cleaned
