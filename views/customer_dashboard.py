"""G1 read-only customer dashboard, rendered with native Streamlit only.

This is NOT a second app or HTTP server.  It is imported by the existing
``views.web_app.main`` entrypoint after the one trusted principal has been
built.  It deliberately has no URL/query-parameter shipment selector: all
publication cards are preloaded server-side for that principal, and the detail
button only reveals an already-allowlisted card.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

import streamlit as st

from core import customer_portal as portal
from core import customer_portal_oidc as oidc

_MODE_LABELS = {
    "ROAD": "Đường bộ",
    "SEA": "Đường biển",
    "AIR": "Đường hàng không",
    "RAIL": "Đường sắt",
}


def _mode_label(mode: str | None) -> str:
    return _MODE_LABELS.get(str(mode or "").upper(), "Chưa xác định")


def _logout_button(*, key: str, on_logout: Callable[[], None] | None = None) -> bool:
    if st.button("Đăng xuất", key=key):
        (on_logout or oidc.logout_customer)()
        st.info("Phiên đăng nhập đã kết thúc. Bạn có thể đóng trang này.")
        return True
    return False


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


def render_customer_dashboard(
    principal: portal.CustomerPrincipal,
    *,
    db: Any = None,
    on_logout: Callable[[], None] | None = None,
) -> None:
    """Render only the preloaded, allowlisted cards for one verified customer."""
    st.title("Dashboard khách hàng")
    st.caption("Thông tin lô hàng đã được Trường Thành Logistics xác nhận công bố.")
    st.text(f"Khách hàng: {principal.display_name}")
    st.text(f"Tài khoản: {principal.email}")
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

    if view.data_issues:
        st.error(
            "Phát hiện lỗi dữ liệu công bố. Nội bộ đang rà soát; "
            "không có thông tin lô lỗi nào được hiển thị."
        )
    if view.denied_lots:
        st.warning(
            "Một số lô bị từ chối công bố hoặc chưa có bản duyệt hợp lệ; "
            "hệ thống không hiển thị nội dung đó."
        )
    if view.no_lots and not view.denied_lots:
        st.info("Chưa có lô hàng nào được công bố cho tài khoản này.")

    for index, card in enumerate(view.cards):
        with st.container(border=True):
            st.subheader(f"Lô {card.reference}")
            st.success(card.status_label)
            st.caption("Trạng thái bản công bố đã được duyệt.")
            if st.button(
                "Xem thông tin được công bố",
                key=f"customer_portal_detail_{index}",
            ):
                st.session_state[f"customer_portal_open_{index}"] = True
            if st.session_state.get(f"customer_portal_open_{index}"):
                st.table(
                    [
                        {"Thông tin": "Mã lô", "Giá trị": card.reference},
                        {"Thông tin": "Trạng thái", "Giá trị": card.status_label},
                        {"Thông tin": "Phiên bản công bố", "Giá trị": card.publication_version},
                        {"Thông tin": "Phương thức vận chuyển", "Giá trị": _mode_label(card.transport_mode)},
                        {"Thông tin": "Thời điểm duyệt", "Giá trị": card.approved_at},
                    ]
                )
                st.caption("Chỉ các trường trong allowlist công bố được hiển thị.")


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
            rows = portal.list_customer_portal_access(db=db)
        except portal.PortalDataError:
            st.caption("Không tải được danh sách khách hàng.")
            return
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
