"""LOGI_USER_MANAGEMENT_01 — bounded Admin write path for ``/nguoi-dung``.

Turns the previously READ-ONLY ``/nguoi-dung`` workspace into a safe Admin
surface by reusing exactly the capability that already exists:

    core.users.build_user_document()   canonical normalization + PBKDF2 hash
    core.users.change_password()       canonical password rehash
    core.users.set_active()            canonical active/audit-trail toggle
    core.users.normalize_role()        canonical role validation
    core.users.public_identity()       canonical password-free public view
    core.database.load_users()         fresh canonical read (never cached)
    core.database.save_user()          canonical upsert writer (Admin-gated)
    core.database.update_user()        canonical partial/full updater (Admin-gated)
    core.auth.can_operate_business()   the SAME wildcard Admin boundary

This module invents NO identity/auth/IAM system of its own. It is the typed
event shell (RBAC pre-check → transform → writer → fresh readback) that the
existing capability was always missing; the canonical writers re-check the
same Admin boundary again, so hiding the buttons in the UI is a display
choice, never the security boundary.

Write contract (mirrors ``views/logi_c1.py`` / ``views/logi_view_model.py``):

    typed event → Admin RBAC (core.auth) → fresh load_users() →
    core.users transform → core.database writer → audit (password redacted
    by core.database._audit already) → fresh load_users() → password-free
    public readback

Scope, deliberately bounded:

* CREATE refuses a duplicate username instead of upserting over an existing
  account (``core.database.save_user`` is upsert-style and must never be
  trusted alone for that).
* ROLE / ACTIVE changes refuse an operation that would leave the system with
  zero active Admin accounts — the ONE lockout invariant this slice adds.
* No delete path: only ``active`` is toggled, history is kept.
* No password material (raw or hashed) is ever put in a handler's returned
  outcome — only ``core.users.public_identity`` fields.
"""

from __future__ import annotations

from typing import Any, Mapping

USER_MANAGEMENT_EVENTS = {
    "user_create",
    "user_role_set",
    "user_active_set",
    "user_password_reset",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _result(event: str, username: str, ok: bool, error: str = "",
            readback: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"event": event, "id": username, "username": username, "ok": ok,
            "error": error, "readback": readback, **extra}


def _actor() -> str:
    from core.auth import current_actor

    return current_actor()


def _admin_gate() -> bool:
    """The ONE Admin boundary this module reuses — never widened here.

    ``core.database.save_user`` / ``update_user`` re-check the exact same
    wildcard permission again server-side, so this pre-check only produces a
    faster, clearer refusal message; it is not itself the security boundary.
    """
    from core.auth import can_operate_business

    return can_operate_business("*")


def _fresh_users() -> dict[str, dict[str, Any]]:
    """Fresh, uncached canonical user store — never the frontend's copy."""
    from core.database import load_users

    return load_users()


def _find_user(users: Mapping[str, dict[str, Any]], username: str) -> dict[str, Any] | None:
    target = username.strip().lower()
    doc = users.get(target)
    if doc is not None:
        return doc
    return next(
        (doc for doc in users.values() if str(doc.get("username", "")).strip().lower() == target),
        None,
    )


def _active_admin_count(users: Mapping[str, dict[str, Any]], *, exclude: str = "") -> int:
    excluded = exclude.strip().lower()
    return sum(
        1
        for doc in users.values()
        if str(doc.get("role", "")).strip().lower() == "admin"
        and bool(doc.get("active", True))
        and str(doc.get("username", "")).strip().lower() != excluded
    )


def _public_readback(username: str) -> dict[str, Any] | None:
    """Fresh, password-free readback of ONE account after a write."""
    from core.users import public_identity

    fresh = _fresh_users()
    doc = _find_user(fresh, username)
    return public_identity(doc) if doc is not None else None


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _handle_user_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    """CREATE one account. Refuses a duplicate username; never upserts over one."""
    from core.database import get_last_db_error, save_user
    from core.users import UserError, build_user_document

    raw_username = _text(payload.get("username"))
    request_id = _text(payload.get("requestId"))

    def _out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("user_create", raw_username, ok, error, requestId=request_id, **extra)

    if not raw_username:
        return _out(False, "Thiếu tên đăng nhập.")
    if not _admin_gate():
        return _out(False, "RBAC: chỉ Admin mới được tạo tài khoản.")

    password = str(payload.get("password") or "")
    confirm = str(payload.get("confirmPassword") or "")
    if password != confirm:
        return _out(False, "Mật khẩu xác nhận không khớp.")

    # CREATE SAFETY: save_user is upsert-style — a fresh read of the
    # canonical store MUST happen right before the write, so a username that
    # already exists is refused instead of silently overwritten.
    existing = _fresh_users()
    if _find_user(existing, raw_username) is not None:
        return _out(False, f"Tài khoản '{raw_username}' đã tồn tại — không tạo trùng.")

    try:
        document = build_user_document(
            username=raw_username,
            password=password,
            display_name=_text(payload.get("displayName")),
            role=_text(payload.get("role")),
            active=bool(payload.get("active", True)),
            email=_text(payload.get("email")),
            created_by=_actor(),
        )
    except UserError as exc:
        return _out(False, str(exc))

    # A second race check right before the write closes the fresh-read →
    # write gap without inventing a lock: the canonical writer itself is a
    # single upsert, so this keeps the "never silently overwrite" guarantee
    # even under a near-simultaneous duplicate click.
    if _find_user(_fresh_users(), document["username"]) is not None:
        return _out(False, f"Tài khoản '{document['username']}' đã tồn tại — không tạo trùng.")

    if not save_user(document):
        return _out(False, get_last_db_error() or "Không tạo được tài khoản.")

    readback = _public_readback(document["username"])
    return _out(True, readback=readback, persisted={"username": document["username"]})


def _handle_user_role_set(payload: Mapping[str, Any]) -> dict[str, Any]:
    """CHANGE ROLE — canonical roles only; refuses the last-active-Admin demote."""
    from core.database import get_last_db_error, update_user
    from core.users import UserError, normalize_role

    username = _text(payload.get("username"))
    request_id = _text(payload.get("requestId"))

    def _out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("user_role_set", username, ok, error, requestId=request_id, **extra)

    if not username:
        return _out(False, "Thiếu tên đăng nhập.")
    if not _admin_gate():
        return _out(False, "RBAC: chỉ Admin mới được đổi vai trò.")

    try:
        new_role = normalize_role(payload.get("role"))
    except UserError as exc:
        return _out(False, str(exc))

    users = _fresh_users()
    document = _find_user(users, username)
    if document is None:
        return _out(False, f"Không tìm thấy tài khoản '{username}'.")

    current_role = str(document.get("role", "")).strip().lower()
    if current_role == new_role:
        return _out(True, readback=_public_readback(username), persisted={"role": new_role})

    # LAST_ACTIVE_ADMIN_GUARD: demoting the only active Admin would lock the
    # whole team out of user management. This is the ONE invariant this slice
    # adds — no broader policy framework.
    if current_role == "admin" and bool(document.get("active", True)):
        if _active_admin_count(users, exclude=username) == 0:
            return _out(False, "Không thể đổi vai trò của Admin đang hoạt động cuối cùng.")

    if not update_user(document["username"], payload={"role": new_role}, actor=_actor()):
        return _out(False, get_last_db_error() or "Không cập nhật được vai trò.")

    return _out(True, readback=_public_readback(username), persisted={"role": new_role})


def _handle_user_active_set(payload: Mapping[str, Any]) -> dict[str, Any]:
    """DEACTIVATE / REACTIVATE — refuses deactivating the last active Admin."""
    from core.database import get_last_db_error, update_user
    from core.users import set_active

    username = _text(payload.get("username"))
    request_id = _text(payload.get("requestId"))
    active = bool(payload.get("active"))

    def _out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("user_active_set", username, ok, error, requestId=request_id, **extra)

    if not username:
        return _out(False, "Thiếu tên đăng nhập.")
    if not _admin_gate():
        return _out(False, "RBAC: chỉ Admin mới được khóa/kích hoạt tài khoản.")

    users = _fresh_users()
    document = _find_user(users, username)
    if document is None:
        return _out(False, f"Không tìm thấy tài khoản '{username}'.")

    already = bool(document.get("active", True))
    role = str(document.get("role", "")).strip().lower()
    if already == active:
        return _out(True, readback=_public_readback(username), persisted={"active": active})

    # LAST_ACTIVE_ADMIN_GUARD: never deactivate the only active Admin.
    if not active and role == "admin" and already:
        if _active_admin_count(users, exclude=username) == 0:
            return _out(False, "Không thể vô hiệu hóa Admin đang hoạt động cuối cùng.")

    updated = set_active(document, active, actor=_actor())
    if not update_user(document["username"], document=updated, actor=_actor()):
        return _out(False, get_last_db_error() or "Không cập nhật được trạng thái tài khoản.")

    return _out(True, readback=_public_readback(username), persisted={"active": active})


def _handle_user_password_reset(payload: Mapping[str, Any]) -> dict[str, Any]:
    """SET NEW PASSWORD — Admin enters it directly; not an email reset flow."""
    from core.database import get_last_db_error, update_user
    from core.users import UserError, change_password

    username = _text(payload.get("username"))
    request_id = _text(payload.get("requestId"))

    def _out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("user_password_reset", username, ok, error, requestId=request_id, **extra)

    if not username:
        return _out(False, "Thiếu tên đăng nhập.")
    if not _admin_gate():
        return _out(False, "RBAC: chỉ Admin mới được đặt lại mật khẩu.")

    new_password = str(payload.get("newPassword") or "")
    confirm = str(payload.get("confirmPassword") or "")
    if new_password != confirm:
        return _out(False, "Mật khẩu xác nhận không khớp.")

    users = _fresh_users()
    document = _find_user(users, username)
    if document is None:
        return _out(False, f"Không tìm thấy tài khoản '{username}'.")

    try:
        updated = change_password(document, new_password, actor=_actor())
    except UserError as exc:
        return _out(False, str(exc))

    if not update_user(document["username"], document=updated, actor=_actor()):
        return _out(False, get_last_db_error() or "Không đặt lại được mật khẩu.")

    return _out(True, readback=_public_readback(username))


_HANDLERS = {
    "user_create": _handle_user_create,
    "user_role_set": _handle_user_role_set,
    "user_active_set": _handle_user_active_set,
    "user_password_reset": _handle_user_password_reset,
}


def consume_user_management_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded user-management dispatcher (pure over an explicit session).

    Mirrors ``views.logi_c1.consume_c1_triggers``: only the declared event
    names are handled, a replayed ``seq`` can never double-write, and every
    outcome (success or refusal) is returned so the caller can embed it in
    ``lastWrites`` for the frontend to match by ``requestId``.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(USER_MANAGEMENT_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        handler = _HANDLERS.get(event_name)
        if handler is None:  # pragma: no cover - sets agree by construction
            continue
        try:
            outcomes.append(handler(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            outcomes.append(_result(event_name, _text(data.get("username")), False,
                                    f"{type(exc).__name__}: {exc}"))
    if outcomes:
        session["writes"] = outcomes
    return outcomes
