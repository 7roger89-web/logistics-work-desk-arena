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

    # Keep the two Owner controls together; publication is never a customer
    # action and never bypasses the server's Admin-only writer.
    _render_admin_publication_control(user, key_prefix=key_prefix, db=db)


def _render_admin_publication_control(
    user: Mapping[str, Any], *, key_prefix: str, db: Any = None,
) -> None:
    """Admin selects already verified versions and explicitly approves release."""
    from core import customer_portal_publish as publisher

    role = str(user.get("role") or "").strip().lower()
    if role != "admin":
        return
    with st.expander("Cổng khách hàng — duyệt và công bố tiến độ/chứng từ", expanded=False):
        st.caption(
            "Chỉ công bố các mốc/chứng từ đã xác minh và đúng phiên bản. "
            "Không công bố giá, chi phí hay nội dung tệp. "
            "Không tự tạo mốc hoàn thành khi thiếu nguồn."
        )
        try:
            database = portal._resolve_db(db)
            customers = portal.list_customer_portal_access(db=database)
            if not customers:
                st.info("Chưa có hồ sơ khách hàng để công bố.")
                return
            by_customer = {r["id"]: r for r in customers}
            customer_id = st.selectbox(
                "Khách hàng nhận bản công bố",
                options=list(by_customer),
                format_func=lambda key: f"{key} — {by_customer[key]['name']}",
                key=f"{key_prefix}_publish_customer",
            )
            shipments = publisher.list_customer_shipments(
                customer_id, actor_role=role, db=database,
            )
            if not shipments:
                st.info("Khách hàng này chưa có lô được liên kết bằng mã chính xác.")
                return
            by_shipment = {r["id"]: r for r in shipments}
            shipment_id = st.selectbox(
                "Lô hàng",
                options=list(by_shipment),
                key=f"{key_prefix}_publish_shipment_{customer_id}",
            )
            previous = by_shipment[shipment_id]["published_version"]
            st.caption(f"Bản đang công bố: {previous or 'Chưa có'}")
            candidates = publisher.list_verified_sources(
                customer_id, shipment_id, actor_role=role, db=database,
            )
        except (portal.PortalDataError, publisher.PublicationWriteDenied):
            st.error("Không đọc được danh sách công bố hợp lệ. Chưa có dữ liệu nào được thay đổi.")
            return
        except Exception:  # noqa: BLE001 - no internal source detail in UI
            st.error("Không tải được nguồn công bố. Vui lòng thử lại.")
            return

        event_options = {str(i): item for i, item in enumerate(candidates["events"])}
        document_options = {str(i): item for i, item in enumerate(candidates["documents"])}
        if not event_options and not document_options:
            st.info(
                "Chưa có mốc/chứng từ đã xác minh trong nguồn công bố cho lô này. "
                "Không thể công bố một bước chưa có chứng cứ."
            )
            return
        event_ids = st.multiselect(
            "Mốc tiến độ được duyệt",
            options=list(event_options),
            format_func=lambda key: (
                f"{event_options[key]['title']} — "
                f"{event_options[key]['id']} / {event_options[key]['version']}"
            ),
            key=f"{key_prefix}_publish_events_{customer_id}_{shipment_id}",
        )
        document_ids = st.multiselect(
            "Chứng từ được duyệt (chỉ metadata, không tải tệp)",
            options=list(document_options),
            format_func=lambda key: (
                f"{document_options[key]['kind']}: {document_options[key]['title']} — "
                f"{document_options[key]['id']} / {document_options[key]['version']}"
            ),
            key=f"{key_prefix}_publish_docs_{customer_id}_{shipment_id}",
        )
        event_versions = {
            event_options[key]["id"]: event_options[key]["version"] for key in event_ids
        }
        document_versions = {
            document_options[key]["id"]: document_options[key]["version"]
            for key in document_ids
        }
        conflicting_versions = (
            len(event_versions) != len(event_ids)
            or len(document_versions) != len(document_ids)
        )
        if conflicting_versions:
            st.error("Không được chọn hai phiên bản cho cùng một mã mốc/chứng từ.")
        confirmed = st.checkbox(
            "Tôi đã đối chiếu nguồn nghiệp vụ và xác nhận chỉ công bố những mục đã duyệt.",
            key=f"{key_prefix}_publish_confirmation_{customer_id}_{shipment_id}",
        )
        ready = bool(confirmed and (event_versions or document_versions) and not conflicting_versions)
        if st.button(
            "Duyệt và công bố phiên bản mới",
            type="primary",
            disabled=not ready,
            key=f"{key_prefix}_publish_submit_{customer_id}_{shipment_id}",
        ):
            try:
                success, message = publisher.publish_verified_sources(
                    customer_id, shipment_id,
                    event_versions=event_versions,
                    document_versions=document_versions,
                    expected_current_version=previous,
                    actor_role=role,
                    actor_username=str(user.get("username") or ""),
                    db=database,
                )
            except publisher.PublicationWriteDenied as exc:
                st.error(str(exc))
                return
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
