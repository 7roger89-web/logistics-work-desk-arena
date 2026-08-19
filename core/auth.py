"""LOG-C15 — Xác thực và phân quyền tập trung.

Cấu trúc:
- Hàm băm/giải mã mật khẩu PBKDF2-SHA256 (giữ nguyên cơ chế đã có, không tự
  invent cryptography).
- Đăng nhập/đăng xuất qua session Streamlit. Khi AUTH_REQUIRED bật, danh sách
  người dùng được lấy từ MongoDB qua core.database (không còn đọc từ
  st.secrets auth.users).
- Mô hình quyền duy nhất: ROLE_PERMISSIONS mở rộng từ hệ cũ; mọi kiểm tra đều
  qua has_permission() hoặc assert_permission().

Bảo mật:
- Thất bại đăng nhập không tiết lộ tài khoản tồn tại hay trạng thái active.
- Hash mật khẩu không bao giờ xuất hiện trong UI hay log.
- Không hard-code username/password trong source.
"""
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


def current_user() -> dict[str, Any]:
    user = st.session_state.get("current_user")
    if isinstance(user, dict):
        return user
    return {}


def is_authenticated() -> bool:
    user = current_user()
    return bool(user.get("username"))


# ---------------------------------------------------------------- permissions

# Mô hình quyền duy nhất của ứng dụng. "*" = toàn quyền (chỉ admin).
# Key là route permission (mức màn hình) hoặc action permission (mức thao tác).
# Mở rộng tối thiểu từ ROLE_PERMISSIONS có sẵn (LOG-C07) để giữ các kiểm tra
# hiện có hoạt động (shipment_edit, customer_delete, knowledge_delete...).
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "sale": {
        "dashboard",
        "shipment_create",
        "shipment_edit",
        "customers",
        "sales",
        "sales_write",
        "contracts",
        "tariff",
        "tracking",
        "knowledge",
        "shipment_360_read",
        "entity_context",
        "commercial_view",
        "commercial_write",
    },
    "support": {
        "dashboard",
        "shipment_edit",
        "customers",
        "shipment_360_read",
        "entity_context",
        "contracts",
        "tariff",
        "tracking",
        "knowledge",
        "commercial_view",
        "finance_view",
        "finance_write",  # Owner-approved (2026-08-18): shipment-level finance work (actual costs, payment confirmation, receivable/payable updates, reconciliation)
        "operations_write",
    },
    # Legacy role names giữ tương thích ngược với entries secrets.toml cũ
    # và test fixtures cũ.
    "accounting": {"dashboard", "shipment_edit", "customers", "contracts", "proxy_payment", "receivables", "entrustment", "reports", "knowledge", "finance_view"},
    "operations": {"dashboard", "shipment_create", "shipment_edit", "customers", "contracts", "tariff", "tracking", "knowledge", "operations_write"},
    "sales": {"dashboard", "shipment_create", "shipment_edit", "customers", "sales", "contracts", "tracking", "knowledge", "commercial_view", "sales_write"},
    "viewer": {"dashboard", "reports", "tracking", "knowledge", "commercial_view", "finance_view"},
}


def _role_permissions(role: str) -> set[str]:
    normalized = str(role or "viewer").lower()
    return ROLE_PERMISSIONS.get(normalized, ROLE_PERMISSIONS["viewer"])


def has_permission(permission: str) -> bool:
    """Kiểm tra quyền của người dùng hiện tại trong session."""
    user = current_user()
    role = str(user.get("role", "viewer")).lower()
    permissions = _role_permissions(role)
    if "*" in permissions:
        return True
    if permission in permissions:
        return True
    if not user.get("username"):
        return permission in _role_permissions("anonymous")
    return False


def has_write_permission(permission: str) -> bool:
    """Chỉ đúng khi user đã đăng nhập VÀ có quyền thao tác này."""
    if not is_authenticated():
        return False
    return has_permission(permission)


def assert_permission(permission: str) -> None:
    """Nâng PermissionDeniedError khi boundary thao tác bị vi phạm."""
    if not has_permission(permission):
        raise PermissionDeniedError(permission)


class PermissionDeniedError(RuntimeError):
    """Người dùng không được phép thực hiện thao tác này."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(
            "Bạn không có quyền thực hiện thao tác này. "
            "Nếu cần quyền, hãy liên hệ Quản trị viên (Admin)."
        )


def current_actor() -> str:
    """Định danh kiểm toán cho material write.

    Luôn trả về authenticated identity khi có; chỉ fall back về 'system' khi
    ứng dụng chạy ở chế độ đơn người dùng không xác thực (AUTH_REQUIRED tắt).
    Không bao giờ fall back về 'admin' hay tên tự do.
    """
    user = current_user()
    username = user.get("username")
    if username:
        return str(username)
    return "system"


# ------------------------------------------------------------------ login UI

def require_login() -> dict[str, str] | None:
    if not AUTH_REQUIRED:
        user = {"username": "local-admin", "display_name": "Local Admin", "role": "admin"}
        st.session_state.current_user = user
        return user

    session_user = current_user()
    if session_user:
        return session_user

    user_count = 0
    try:
        from core.database import load_users  # noqa: PLC0415
        user_count = len(load_users())
    except Exception:  # noqa: BLE001
        pass

    if user_count == 0:
        _render_bootstrap_setup()
        return None

    # LOG-LG04 Final UX: compact centered login
    st.markdown(
        """
        <style>
        .lg04-login-container {
            max-width: 320px;
            margin: 3rem auto;
            padding: 1.5rem;
            border: 1px solid #E4E7EC;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="lg04-login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Đăng nhập")
        username = st.text_input("Tài khoản", key="login_username").strip()
        password = st.text_input("Mật khẩu", type="password", key="login_password")
        submitted = st.button("Đăng nhập", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    if submitted:
        identity = _authenticate(username, password)
        if identity:
            st.session_state.current_user = identity
            st.rerun()
        st.error("Tài khoản hoặc mật khẩu không đúng.")
    return None


def _authenticate(username: str, password: str) -> dict[str, str] | None:
    from core.database import load_users  # noqa: PLC0415
    from core.users import authenticate  # noqa: PLC0415

    safe_name = str(username or "").strip().lower()
    if not safe_name or not password:
        return None
    try:
        users = load_users()
    except Exception:  # noqa: BLE001
        return None
    for document in users.values():
        if str(document.get("username", "")).lower() == safe_name:
            identity = authenticate(document, password)
            return identity
    return None


def _render_bootstrap_setup() -> None:
    st.warning(
        "Chưa có tài khoản quản trị nào. Hãy tạo tài khoản Admin đầu tiên để bắt đầu."
    )
    with st.form("bootstrap_form"):
        username = st.text_input("Tên đăng nhập (3-30 ký tự, chữ thường)", key="bootstrap_username").strip().lower()
        display_name = st.text_input("Tên hiển thị", key="bootstrap_display").strip()
        email = st.text_input("Email (không bắt buộc)", key="bootstrap_email").strip().lower()
        password = st.text_input("Mật khẩu (tối thiểu 8 ký tự)", type="password", key="bootstrap_password")
        confirm = st.text_input("Nhập lại mật khẩu", type="password", key="bootstrap_confirm")
        submitted = st.form_submit_button("Tạo tài khoản Admin đầu tiên", type="primary", use_container_width=True)
    if submitted:
        _complete_bootstrap(username, display_name, email, password, confirm)


def _complete_bootstrap(
    username: str,
    display_name: str,
    email: str,
    password: str,
    confirm: str,
) -> bool:
    from core.database import save_user  # noqa: PLC0415
    from core.users import build_user_document, UserError  # noqa: PLC0415

    if password != confirm:
        st.error("Mật khẩu xác nhận không khớp.")
        return False
    try:
        document = build_user_document(
            username=username,
            password=password,
            display_name=display_name,
            role="admin",
            created_by="bootstrap",
        )
    except UserError as exc:
        st.error(str(exc))
        return False
    if not save_user(document):
        st.error("Không lưu được tài khoản. Kiểm tra kết nối database.")
        return False
    st.success("Đã tạo tài khoản Admin đầu tiên. Đăng nhập để tiếp tục.")
    st.rerun()
    return True


def logout() -> None:
    for key in ("current_user",):
        st.session_state.pop(key, None)
    st.rerun()


def session_identity_summary(user: dict[str, str]) -> str:
    return f"{user.get('display_name', user.get('username', ''))} · {user.get('role', '')}"
