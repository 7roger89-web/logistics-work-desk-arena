"""Đăng nhập tùy chọn bằng Streamlit secrets, hỗ trợ PBKDF2-SHA256."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any

import streamlit as st

from core.config import AUTH_REQUIRED


def hash_password(password: str, iterations: int = 390000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(raw_salt)
        expected = base64.b64decode(raw_digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(raw_iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _users() -> dict[str, Any]:
    try:
        return dict(st.secrets["auth"]["users"])
    except (KeyError, TypeError, FileNotFoundError):
        return {}


def require_login() -> dict[str, str] | None:
    if not AUTH_REQUIRED:
        user = {"username": "local-admin", "display_name": "Local Admin", "role": "admin"}
        st.session_state.current_user = user
        return user

    if st.session_state.get("current_user"):
        return st.session_state.current_user

    st.title("🔐 LOGISTICS PRO")
    st.caption("Đăng nhập để truy cập hệ thống.")
    with st.form("login_form"):
        username = st.text_input("Tài khoản").strip()
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)
    if submitted:
        users = _users()
        profile = users.get(username)
        if profile and verify_password(password, str(profile.get("password_hash", ""))):
            user = {
                "username": username,
                "display_name": str(profile.get("display_name", username)),
                "role": str(profile.get("role", "viewer")),
            }
            st.session_state.current_user = user
            st.rerun()
        st.error("Tài khoản hoặc mật khẩu không đúng.")
    return None


def logout() -> None:
    st.session_state.pop("current_user", None)
    st.rerun()

ROLE_PERMISSIONS = {
    "admin": {"*"},
    "accounting": {"dashboard", "shipment_edit", "customers", "contracts", "proxy_payment", "receivables", "entrustment", "reports", "knowledge"},
    "operations": {"dashboard", "shipment_create", "shipment_edit", "customers", "contracts", "tariff", "tracking", "knowledge"},
    "sales": {"dashboard", "shipment_create", "shipment_edit", "customers", "sales", "contracts", "tracking", "knowledge"},
    "viewer": {"dashboard", "reports", "tracking", "knowledge"},
}


def has_permission(permission: str) -> bool:
    user = st.session_state.get("current_user", {})
    role = str(user.get("role", "viewer")).lower()
    permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])
    return "*" in permissions or permission in permissions
