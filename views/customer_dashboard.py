"""G1 read-only customer portal: server principal + HEXA reference UI.

This is NOT a second app or HTTP server.  It is imported by the existing
``views.web_app.main`` entrypoint after the one trusted principal has been
built.  The dashboard body is the Owner's ``HEXA_LucGiac_DEMO.html`` layout
(Dashboard 8-column table → map-first Journey 00..06) mounted through the same
Streamlit Components v2 technology already used by ``views.logi_shell``.

There is deliberately no URL/query-parameter lot selector: every lot in the
payload was already resolved server-side for that principal by
``core.customer_portal.load_customer_dashboard``.  The component may change
local UI state (selected lot, node bubble, modal, zoom) but it writes nothing.
"""
from __future__ import annotations

import html as html_lib
from typing import Any, Callable, Mapping

import streamlit as st

from core import config
from core import customer_journey
from core import customer_portal as portal
from core import customer_portal_oidc as oidc
from views import customer_portal_component as component

_CUSTOMER_CSS = """
<style>
  /* Only the customer entry is affected; the internal shell is untouched. */
  section.main .block-container, div[data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem !important;
    padding-bottom: 0.6rem !important;
    max-width: 100% !important;
  }
  .g1-customer-account {
    display: flex; align-items: center; justify-content: flex-end;
    gap: 10px; flex-wrap: wrap; margin: 0 0 8px;
    font-size: 11.5px; color: #475569;
  }
</style>
"""


def _logout_button(*, key: str, on_logout: Callable[[], None] | None = None) -> bool:
    if st.button("Đăng xuất", key=key):
        (on_logout or oidc.logout_customer)()
        st.info("Phiên đăng nhập đã kết thúc. Bạn có thể đóng trang này.")
        return True
    return False


def _demo_flag() -> str | None:
    """Honest environment label; a non-production dataset is never implied to be live."""
    identity = str(getattr(config, "ENV_IDENTITY", "") or "").upper()
    if identity and identity != "PRODUCTION":
        return "DỮ LIỆU STAGING — KHÔNG PHẢI SẢN XUẤT"
    return None


def _notice_from_view(view: portal.CustomerDashboardView) -> dict[str, str] | None:
    if view.data_issues:
        return {
            "title": "LỖI DỮ LIỆU CÔNG BỐ:",
            "text": (
                "Nội bộ đang rà soát; không có thông tin lô lỗi nào được hiển thị."
            ),
        }
    if view.denied_lots:
        return {
            "title": "MỘT SỐ LÔ CHƯA ĐƯỢC CÔNG BỐ:",
            "text": (
                "Có lô bị từ chối công bố hoặc chưa có bản duyệt hợp lệ; "
                "hệ thống không hiển thị nội dung đó."
            ),
        }
    return None


def render_customer_denied(*, on_logout: Callable[[], None] | None = None) -> None:
    """Uniform screen for anonymous, unauthorised or revoked identities."""
    st.title("Cổng khách hàng")
    st.warning(
        "Tài khoản này chưa được cấp quyền xem dữ liệu. "
        "Vui lòng liên hệ bộ phận hỗ trợ của Trường Thành Logistics."
    )
    st.caption("Không có lô hàng hoặc thông tin công bố nào được hiển thị.")
    _logout_button(key="customer_portal_denied_logout", on_logout=on_logout)


def render_oidc_problem(state: oidc.OidcSessionState, *, on_logout: Callable[[], None] | None = None) -> None:
    """Safe states for OAuth-return, refresh, misconfiguration and expiry."""
    st.title("Cổng khách hàng")
    if state.kind == oidc.STATE_CONFIG_ERROR:
        st.error(
            "Lỗi cấu hình OIDC: cổng khách hàng tạm thời đóng. "
            "Dữ liệu không được hiển thị."
        )
    elif state.kind == oidc.STATE_EXPIRED:
        st.warning("Phiên đăng nhập đã hết hạn. Vui lòng đăng xuất và đăng nhập lại.")
    else:
        st.warning("Danh tính đăng nhập không hợp lệ. Không có dữ liệu được hiển thị.")
    _logout_button(key="customer_portal_problem_logout", on_logout=on_logout)


def render_customer_login_choice(*, standalone: bool = False) -> None:
    """Reuse the Google login button on a customer-only entry URL."""
    if standalone:
        st.title("Cổng khách hàng")
        st.caption(
            "Đăng nhập Google để xem các lô hàng đã được Trường Thành Logistics "
            "công bố riêng cho tài khoản của bạn."
        )
    else:
        st.caption("Khách hàng?")
    if st.button("Đăng nhập khách hàng bằng Google", key="customer_portal_google_login"):
        status = oidc.inspect_oidc_config()
        if not status.ready:
            st.error(
                "Lỗi cấu hình OIDC: cổng khách hàng chưa sẵn sàng. "
                f"Thiếu/không hợp lệ: {', '.join(status.missing)}."
            )
        elif oidc.start_customer_login():
            st.info("Đang chuyển đến Google để xác thực. Sau khi xác thực, ứng dụng sẽ quay lại đây.")
        else:
            st.error("Không khởi tạo được luồng đăng nhập Google. Không có dữ liệu được hiển thị.")


def _account_label(email: str) -> str:
    """Masked account hint: enough to recognise the session, not a data grant."""
    value = str(email or "").strip()
    if "@" not in value:
        return ""
    local, _, domain = value.partition("@")
    head = local[:2] if len(local) > 2 else local[:1]
    return f"{head}***@{domain}"


def build_model(view: portal.CustomerDashboardView) -> dict[str, Any]:
    """Build the exact component payload for one trusted dashboard view."""
    return customer_journey.build_portal_model(
        view,
        demo_flag=_demo_flag(),
        notice=_notice_from_view(view),
        account_label=_account_label(view.principal.email),
    )


def render_customer_dashboard(
    principal: portal.CustomerPrincipal,
    *,
    db: Any = None,
    on_logout: Callable[[], None] | None = None,
) -> None:
    """Render the reference dashboard + journey map for one verified customer."""
    st.markdown(_CUSTOMER_CSS, unsafe_allow_html=True)
    account_col, action_col = st.columns([3, 1])
    with account_col:
        st.markdown(
            '<div class="g1-customer-account">'
            f"Khách hàng: <b>{html_lib.escape(principal.display_name)}</b>"
            f" · Tài khoản: <b>{html_lib.escape(_account_label(principal.email))}</b>"
            "</div>",
            unsafe_allow_html=True,
        )
    with action_col:
        if _logout_button(key="customer_portal_logout", on_logout=on_logout):
            return

    try:
        view = portal.load_customer_dashboard(principal, db=db)
    except portal.PortalAccessDenied:
        render_customer_denied(on_logout=on_logout)
        return
    except portal.PortalDataError:
        st.error("Dữ liệu công bố chưa sẵn sàng. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.")
        return

    if view.no_lots and not view.denied_lots and not view.data_issues:
        st.info("Chưa có lô hàng nào được công bố cho tài khoản này.")
        st.caption("Không có lô hàng hoặc thông tin công bố nào được hiển thị.")

    try:
        component.render(build_model(view))
    except component.PortalAssetError:
        st.error(
            "Giao diện cổng khách hàng chưa sẵn sàng trên máy chủ này. "
            "Không có dữ liệu nào được hiển thị."
        )


def render_owner_portal_access_control(
    user: Mapping[str, Any],
    *,
    key_prefix: str = "shell",
    db: Any = None,
) -> None:
    """Admin-only control writing ONE allowed email onto the customers profile."""
    if str(user.get("role") or "").strip().lower() != "admin":
        return
    with st.expander("Cổng khách hàng — email được Owner cho phép", expanded=False):
        st.caption(
            "Mặc định không có email nào được phép. Email liên hệ không tự động "
            "cấp quyền portal; chỉ Owner/Admin được thay đổi cấu hình này."
        )
        try:
            active_db = portal._resolve_db(db)
            rows = portal.list_customer_portal_access(db=active_db)
        except portal.PortalDataError:
            st.caption("Kết nối dữ liệu cổng khách hàng: CHƯA SẴN SÀNG.")
            return
        oidc_status = oidc.inspect_oidc_config()
        st.caption(
            f"Database đang đọc: {str(getattr(active_db, 'name', 'UNKNOWN'))} | "
            "Google OIDC: "
            + ("ĐỦ CẤU HÌNH (chưa kiểm đăng nhập thật)" if oidc_status.ready
               else "CHƯA ĐỦ CẤU HÌNH")
        )
        if not rows:
            st.info("Chưa có hồ sơ khách hàng.")
            return
        by_id = {row["id"]: row for row in rows}
        # Intentionally plain widgets, NOT st.form(): the existing app already
        # owns login/bootstrap forms and other legacy surfaces. Avoiding a
        # nested form keeps the internal shell and its AppTest lifecycle intact.
        selected = st.selectbox(
            "Hồ sơ khách hàng",
            options=list(by_id),
            format_func=lambda cid: f"{cid} — {by_id[cid]['name']}",
            key=f"{key_prefix}_portal_access_customer",
        )
        current_email = by_id[selected]["portal_access_email"]
        email = st.text_input(
            "Email duy nhất được phép",
            value=current_email,
            key=f"{key_prefix}_portal_access_email_{selected}",
            placeholder="portal@khachhang.example",
        )
        save_col, revoke_col = st.columns(2)
        save = save_col.button(
            "Lưu email được phép",
            key=f"{key_prefix}_portal_access_save_{selected}",
            type="primary",
        )
        revoke = revoke_col.button(
            "Thu hồi quyền",
            key=f"{key_prefix}_portal_access_revoke_{selected}",
        )
        if save or revoke:
            ok, message = portal.set_customer_portal_access_email(
                selected,
                "" if revoke else email,
                actor_role=user.get("role"),
                db=db,
            )
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
