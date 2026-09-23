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
import random
from pathlib import Path
from typing import Any

import streamlit as st

from core.config import AUTH_REQUIRED, DISPLAY_COMPANY_NAME


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
        "translation",
        "shipment_360_read",
        "entity_context",
        "commercial_view",
        "commercial_write",
    },
    # Owner-approved: support được dùng toàn bộ nghiệp vụ hiện có trong app,
    # nhưng vẫn không nhận wildcard "*" của admin để giữ các thao tác quản trị/
    # xóa phá huỷ ở boundary admin.
    "support": {
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
        "translation",
        "shipment_360_read",
        "entity_context",
        "commercial_view",
        "commercial_write",
        "finance_view",
        "finance_write",
        "operations_write",
        "proxy_payment",
        "receivables",
        "entrustment",
        "reports",
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


def can_operate_business(permission: str) -> bool:
    """Return whether the authenticated actor may perform a business action.

    The role matrix remains the only policy source.  This small semantic
    wrapper gives callers a stable name for a business write without creating
    a second authorization system.
    """
    return has_write_permission(permission)


def can_edit_contract() -> bool:
    """Contract mutations use the existing commercial write permission."""
    return can_operate_business("sales_write")


# ------------------------------------------------------------------ LOG-DOCGEN-01
# Bounded RBAC for the Shipment Document Pack Generator.  These wrappers reuse
# the single ROLE_PERMISSIONS matrix; they intentionally do NOT widen Sale.
#
#   GENERATE / DOWNLOAD  -> sales_write   (Admin YES, Support YES, Sale YES)
#   ISSUE / SUPERSEDE    -> operations_write (Admin YES, Support YES, Sale NO)
#
# The writer/service layer calls these wrappers directly so UI hiding alone is
# never the security boundary.


def can_generate_documents() -> bool:
    """Generate/download a document pack: existing sales_write."""
    return can_operate_business("sales_write")


def can_issue_documents() -> bool:
    """Issue/supersede a document pack: existing operations_write."""
    return can_operate_business("operations_write")


def assert_can_generate_documents() -> None:
    """Raise PermissionDeniedError when generation is not authorised."""
    if not can_generate_documents():
        raise PermissionDeniedError("sales_write")


def assert_can_issue_documents() -> None:
    """Raise PermissionDeniedError when issuance/supersede is not authorised."""
    if not can_issue_documents():
        raise PermissionDeniedError("operations_write")


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


def current_actor_context(actor: str | None = None) -> dict[str, str]:
    """Return the canonical identity attached to a mutation.

    ``actor`` is retained as a compatibility fallback for non-Streamlit
    callers and fixtures.  An authenticated session always wins, so a
    display name or arbitrary caller string cannot replace the canonical
    ``user_id``/role pair.
    """
    user = current_user()
    username = str(user.get("username") or actor or "system")
    return {
        "user_id": str(user.get("user_id") or username),
        "username": username,
        "role": str(user.get("role") or "system").strip().lower(),
    }


def current_actor() -> str:
    """Định danh kiểm toán cho material write.

    Luôn trả về authenticated identity khi có; chỉ fall back về 'system' khi
    ứng dụng chạy ở chế độ đơn người dùng không xác thực (AUTH_REQUIRED tắt).
    Không bao giờ fall back về 'admin' hay tên tự do.
    """
    return current_actor_context()["username"]


# ------------------------------------------------------------------ login UI

# LOG-LG05 / LOGI_LOGIN_BACKGROUND_ROTATION_01 — cinematic compact login
# with 10 rotating logistics backgrounds.
#
# Visual surface only: 10 repo-owned WebP assets (assets/login/backgrounds/)
# inlined as a single data URI plus scoped CSS, injected ONLY while the
# login / first-admin setup screen renders. A logged-in rerun never emits
# these rules, so the authenticated application is not restyled. No
# external image, CDN, asset server, scheduler or runtime image dependency;
# the auth flow below is unchanged. Rotation is per-login-visit via
# tiny session-state keys; no persistent storage.

_LOGIN_HERO_ASSET = Path(__file__).resolve().parents[1] / "assets" / "login_container_ship_hero.svg"
_LOGIN_BG_DIR = Path(__file__).resolve().parents[1] / "assets" / "login" / "backgrounds"
_LOGIN_BG_COUNT = 10
_LOGIN_BG_SESSION_KEY = "_login_bg_index"
_LOGIN_BG_PREV_KEY = "_login_bg_prev_index"

# Per-image focal positions — tiny tuning so important subjects aren't
# badly cropped or hidden behind the centered login card. Only added
# because a single fixed position crops Road/Port/Air differently.
_LOGIN_BG_POSITIONS: dict[int, tuple[str, str]] = {
    1: ("50% 38%", "32% 40%"),  # container ship at sea
    2: ("50% 35%", "30% 42%"),  # port cranes
    3: ("50% 45%", "28% 45%"),  # highway trucks / border road
    4: ("50% 42%", "35% 45%"),  # air cargo aircraft
    5: ("50% 50%", "50% 50%"),  # warehouse interior
    6: ("50% 48%", "28% 48%"),  # freight train
    7: ("50% 42%", "50% 42%"),  # collage montage
    8: ("50% 40%", "30% 42%"),  # customs border checkpoint
    9: ("50% 36%", "32% 38%"),  # container yard at dusk
    10: ("50% 50%", "50% 50%"),  # global network map
}


def _login_background_files() -> list[Path]:
    """Ordered list of the 10 normal login background assets."""
    return [_LOGIN_BG_DIR / f"login-bg-{i:02d}.webp" for i in range(1, _LOGIN_BG_COUNT + 1)]


_LOGIN_HERO_CSS_TEMPLATE = """
[data-testid="stHeader"] {
  background: transparent;
}
[data-testid="stHeader"] * {
  color: #cfe0ea !important;
}
[data-testid="stAppViewContainer"] {
  background-color: #071019;
  background-image: url("__BG__");
  background-size: cover;
  background-position: __POS_DESKTOP__;
  background-repeat: no-repeat;
}
/* Compact transparent login surface. The <form> element is the real DOM
   wrapper around the Streamlit widgets; artwork stays visible behind it. */
[data-testid="stForm"] {
  max-width: 300px;
  background: transparent;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  border: none;
  border-radius: 14px;
  box-shadow: none;
  padding: 20px 18px 16px;
  margin-top: 11vh;
}
[data-testid="stForm"]:has(.lg05-bootstrap) {
  max-width: 340px;
}
[data-testid="stForm"] [data-testid="stMarkdownContainer"] {
  margin-bottom: 6px;
}
.lg05-identity { margin: 0 0 12px; }
.lg05-identity .lg05-brand { font-size: .66rem; letter-spacing: .22em; color: #6fd3e0; font-weight: 600; text-shadow: 0 1px 8px rgba(0,0,0,0.60); }
.lg05-identity .lg05-h { font-size: 1.3rem; font-weight: 700; color: #f2f7fa; margin-top: 3px; text-shadow: 0 1px 10px rgba(0,0,0,0.60); }
.lg05-identity .lg05-sub { font-size: .72rem; color: #dce8ef; margin-top: 3px; text-shadow: 0 1px 8px rgba(0,0,0,0.55); }
[data-testid="stForm"] [data-testid="stTextInput"] { margin-top: 0; margin-bottom: 4px; }
[data-testid="stForm"] label { font-size: .78rem !important; color: #f2f7fa !important; text-shadow: 0 1px 8px rgba(0,0,0,0.60); }
[data-testid="stForm"] input {
  background: rgba(5, 12, 18, 0.32) !important;
  color: #eef5f9 !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: 8px !important;
}
[data-testid="stForm"] input::placeholder { color: #aab8c5; }
[data-testid="stForm"] [data-testid="stFormSubmitButton"] {
  width: 100%;
  background-color: #2e93a8;
  color: #f4fbfd;
  border-radius: 8px;
  font-weight: 600;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"]:hover { background-color: #37a7bd; }
/* generic credential error stays compact, centered under the card */
[data-testid="stError"] {
  max-width: 320px;
  margin: 12px auto 0;
}
@media (max-width: 768px) {
  [data-testid="stForm"] { max-width: min(300px, 88vw); margin-top: 7vh; }
  [data-testid="stForm"]:has(.lg05-bootstrap) { max-width: min(340px, 90vw); }
  [data-testid="stAppViewContainer"] { background-position: __POS_MOBILE__; }
}
"""

_LOGIN_IDENTITY_HTML = (
    '<div class="lg05-identity">'
    '<div class="lg05-brand">LOGISTICS</div>'
    '<div class="lg05-h">Đăng nhập</div>'
    # Display brand only (core.config.DISPLAY_COMPANY_NAME) — never a legal_name.
    f'<div class="lg05-sub">{DISPLAY_COMPANY_NAME} · Nội bộ</div>'
    "</div>"
)

_BOOTSTRAP_IDENTITY_HTML = (
    '<div class="lg05-identity lg05-bootstrap">'
    '<div class="lg05-brand">LOGISTICS</div>'
    '<div class="lg05-h">Thiết lập hệ thống</div>'
    '<div class="lg05-sub">Tạo tài khoản Admin đầu tiên</div>'
    "</div>"
)


def _choose_login_bg_index(prev: int | None) -> int:
    """Pick one of the 10 backgrounds, preferring a different visual from prev.

    Owner source 09 and 10 are byte-identical visuals, so a transition
    09->10 or 10->09 would not be a new background. When prev is 9 or 10,
    both indices are excluded from the next candidate set. For all other
    prev values only that single index is excluded. This is the smallest
    explicit equivalence rule — no image hashing or service.
    """
    choices = list(range(1, _LOGIN_BG_COUNT + 1))
    if isinstance(prev, int) and prev in choices and len(choices) > 1:
        if prev in (9, 10):
            choices = [c for c in choices if c not in (9, 10)]
        else:
            choices = [c for c in choices if c != prev]
    return random.choice(choices)


def _current_login_bg_index() -> int:
    """Stable per-login-visit selection stored in session_state.

    - First call in a fresh login visit picks one of the 10 and stores it.
    - Subsequent calls (reruns, typing, failed login, bootstrap) return the
      same stored index so the background never flickers.
    - Only cleared after a successful login or logout, so the next login
      visit can choose a new image (preferably different from the previous).
    """
    try:
        stored = st.session_state.get(_LOGIN_BG_SESSION_KEY)  # type: ignore[attr-defined]
    except Exception:
        stored = None
    if isinstance(stored, int) and 1 <= stored <= _LOGIN_BG_COUNT:
        candidate = _LOGIN_BG_DIR / f"login-bg-{stored:02d}.webp"
        try:
            if candidate.is_file():
                return stored
        except Exception:
            pass
    # need new selection
    try:
        prev = st.session_state.get(_LOGIN_BG_PREV_KEY)  # type: ignore[attr-defined]
    except Exception:
        prev = None
    if not isinstance(prev, int) or not (1 <= prev <= _LOGIN_BG_COUNT):
        prev = None
    idx = _choose_login_bg_index(prev)
    try:
        st.session_state[_LOGIN_BG_SESSION_KEY] = idx  # type: ignore[index]
    except Exception:
        pass
    return idx


def _login_background_uri_for_index(idx: int) -> str:
    """Data URI for a specific WebP background, fallback to SVG."""
    try:
        path = _LOGIN_BG_DIR / f"login-bg-{idx:02d}.webp"
        data = path.read_bytes()
        if data:
            return "data:image/webp;base64," + base64.b64encode(data).decode("ascii")
    except Exception:
        pass
    try:
        data = _LOGIN_HERO_ASSET.read_bytes()
        return "data:image/svg+xml;base64," + base64.b64encode(data).decode("ascii")
    except Exception:
        return ""


def _login_background_uri() -> str:
    """Data URI of the currently selected login background (self-contained, no CDN).

    Only the ONE selected image is inlined. The 10 assets are never all
    injected at once, keeping the login payload small.
    """
    idx = _current_login_bg_index()
    return _login_background_uri_for_index(idx)


def _login_hero_css() -> str:
    """Scoped CSS for the compact hero login screen (login state only).

    Uses per-image focal positions so road/port/air compositions stay
    well-framed on both desktop and mobile. Only the currently selected
    background is encoded into the CSS.
    """
    idx = _current_login_bg_index()
    desktop_pos, mobile_pos = _LOGIN_BG_POSITIONS.get(idx, ("50% 42%", "28% 45%"))
    uri = _login_background_uri_for_index(idx)
    css = (
        _LOGIN_HERO_CSS_TEMPLATE.replace("__BG__", uri)
        .replace("__POS_DESKTOP__", desktop_pos)
        .replace("__POS_MOBILE__", mobile_pos)
    )
    return f"<style>{css}</style>"


def fresh_session_identity_for_action() -> dict[str, str] | None:
    """Side-effect-free auth revalidation for action/callback execution.

    Re-checks current session identity against the canonical user store BEFORE
    dispatching business events from component callbacks. Emits zero UI (no
    login cards, no HTML/CSS injection).

    Returns:
        dict: The refreshed public user identity if active and confirmed.
        None: When AUTH_REQUIRED and the session has no user, the user is
              deactivated/missing/deleted, or load_users fails closed.
    """
    if not AUTH_REQUIRED:
        user = {
            "username": "local-admin",
            "display_name": "Local Admin",
            "role": "admin",
        }
        st.session_state.current_user = user
        return user

    session_user = current_user()
    if not session_user:
        return None

    revalidated = _revalidate_session(session_user)
    if revalidated is None:
        # The account behind this session no longer exists, or was
        # deactivated after login. A stale session must never keep
        # acting under a role/identity the canonical store no longer
        # grants — clear it immediately.
        st.session_state.pop("current_user", None)
        return None
    return revalidated


def require_login() -> dict[str, str] | None:
    fresh = fresh_session_identity_for_action()
    if fresh is not None:
        return fresh

    user_count = 0
    try:
        from core.database import load_users  # noqa: PLC0415
        user_count = len(load_users())
    except Exception:  # noqa: BLE001
        pass

    # LOG-LG05 — hero background + compact card, injected only while the
    # login / first-admin setup screen renders (a logged-in rerun never
    # emits it, so the authenticated app is not restyled).
    st.markdown(_login_hero_css(), unsafe_allow_html=True)

    if user_count == 0:
        _render_bootstrap_setup()
        return None

    # LOG-LG05 Final UX: compact transparent controls (~300px) over the hero.
    # The <form> element stays visually transparent so the Owner artwork remains
    # primary. Auth flow is unchanged: same
    # keys, _authenticate(), session + rerun on success, generic error on
    # failure.
    with st.form("login_form"):
        st.markdown(_LOGIN_IDENTITY_HTML, unsafe_allow_html=True)
        username = st.text_input("Tài khoản", key="login_username").strip()
        password = st.text_input("Mật khẩu", type="password", key="login_password")
        submitted = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)
    if submitted:
        identity = _authenticate(username, password)
        if identity:
            st.session_state.current_user = identity
            # Preserve rotation: next login visit can choose a new image,
            # preferably different from this one. Clear the per-visit key
            # and remember it as prev.
            try:
                cur_idx = st.session_state.get(_LOGIN_BG_SESSION_KEY)  # type: ignore[attr-defined]
                if isinstance(cur_idx, int) and 1 <= cur_idx <= _LOGIN_BG_COUNT:
                    st.session_state[_LOGIN_BG_PREV_KEY] = cur_idx  # type: ignore[index]
                st.session_state.pop(_LOGIN_BG_SESSION_KEY, None)  # type: ignore[attr-defined]
            except Exception:
                pass
            st.rerun()
        else:
            st.error("Tài khoản hoặc mật khẩu không đúng.")
    return None


def _revalidate_session(session_user: dict[str, Any]) -> dict[str, str] | None:
    """Re-check an existing session against the canonical user record.

    ``require_login()`` used to trust ``st.session_state.current_user``
    verbatim once it was set, so a role change or a deactivation made by an
    Admin never applied to a browser tab that was already logged in — it kept
    the OLD role/display identity for the rest of that session.

    This is a narrow correction, not a new session framework: on every rerun
    (while ``AUTH_REQUIRED`` is on) the session identity is re-derived from
    ``core.database.load_users`` — the SAME canonical store ``_authenticate``
    already reads — via ``core.users.public_identity`` — the SAME
    password-free projection the rest of the app uses. No password is asked
    again and no new session store, token or daemon is introduced.

    Returns the refreshed public identity, or ``None`` when the account no
    longer exists, is inactive, or the canonical store could not be read at
    all. Authorization must fail CLOSED: if ``load_users`` raises, the
    session is cleared exactly like a missing/inactive account rather than
    keeping the operator logged in under a role the canonical store could
    not confirm. This mirrors the existing fresh-login path, where a
    ``load_users`` failure in ``_authenticate`` already returns ``None``
    instead of granting access.
    """
    username = str(session_user.get("username") or "").strip().lower()
    if not username:
        return None
    from core.database import load_users  # noqa: PLC0415
    from core.users import public_identity  # noqa: PLC0415

    try:
        users = load_users()
    except Exception:  # noqa: BLE001 - fail closed: never keep a stale session
        return None

    document = users.get(username)
    if document is None or not document.get("active", True):
        return None

    identity = public_identity(document)
    refreshed = {
        "user_id": identity["user_id"],
        "username": identity["username"],
        "display_name": identity["display_name"],
        "email": identity["email"],
        "role": identity["role"],
    }
    if refreshed != {k: session_user.get(k) for k in refreshed}:
        st.session_state.current_user = refreshed
    return refreshed


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
        st.markdown(_BOOTSTRAP_IDENTITY_HTML, unsafe_allow_html=True)
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
        try:
            st.session_state.pop(key, None)  # type: ignore[attr-defined]
        except Exception:
            pass
    # Rotation for logout in same session: next login visit prefers a
    # different image from the one just shown.
    try:
        cur_idx = st.session_state.get(_LOGIN_BG_SESSION_KEY)  # type: ignore[attr-defined]
        if isinstance(cur_idx, int) and 1 <= cur_idx <= _LOGIN_BG_COUNT:
            st.session_state[_LOGIN_BG_PREV_KEY] = cur_idx  # type: ignore[index]
        st.session_state.pop(_LOGIN_BG_SESSION_KEY, None)  # type: ignore[attr-defined]
    except Exception:
        pass
    st.rerun()


def session_identity_summary(user: dict[str, str]) -> str:
    return f"{user.get('display_name', user.get('username', ''))} · {user.get('role', '')}"
