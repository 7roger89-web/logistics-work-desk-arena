"""Logistics Work Desk — Logi-good shell entry (Phase B).

The entire visible shell + active page is ONE Streamlit Components v2
component root running the literal Logi-good React UI. Inner data is the
presentation view-model over the CURRENT Logistics readers and writers
(``views.logi_real_data`` + ``views.logi_view_model``). The visible donor UI is
frozen; Phase B changed the data and the business actions, not the design.

G1 adds a read-only customer branch to this SAME entrypoint.  Internal
Admin/Support authentication and the React shell are untouched; the customer
branch renders native Streamlit only and never builds the internal view-model.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import streamlit as st

from core import customer_portal_oidc
from core.auth import require_login
from core.config import DISPLAY_COMPANY_NAME

LOGGER = logging.getLogger("logistics.customer_portal_router")
_STAGING_CUSTOMER_HOST = "thu-log-g1-test.streamlit.app"


def _customer_entry_mode(portal_mode: str | None, app_url: str) -> bool:
    """Route staging HOME to Google after the Streamlit OAuth callback.

    st.login() redirects to the app homepage, dropping ?portal=customer.
    This switch affects presentation only, never identity or permissions.
    """
    if portal_mode == "internal":
        return False
    if portal_mode == "customer":
        return True
    try:
        return urlparse(app_url).hostname == _STAGING_CUSTOMER_HOST
    except ValueError:
        return False


def _current_app_url() -> str:
    try:
        return str(st.context.url or "")
    except Exception:  # noqa: BLE001 - older/bare Streamlit runtime
        return ""


def _staging_identity_checks() -> dict[str, bool]:
    """Read effective process config and the live DB handle; expose booleans only."""
    from core import config, database
    from views import logi_sandbox

    checks = {
        "ENV_IDENTITY is STAGING/PREVIEW": config.ENV_IDENTITY in {"STAGING", "PREVIEW"},
        "MONGO_DB_NAME is logistics_staging": config.MONGO_DB_NAME == "logistics_staging",
        "MONGO_RELEASE_MODE is false": config.MONGO_RELEASE_MODE is False,
        "REAL_MONGO connected to logistics_staging": False,
    }
    try:
        from pymongo.database import Database

        db = database.get_db()  # Includes the existing validate_mongo_identity guard.
        if (
            logi_sandbox.transport_name() == logi_sandbox.REAL_TRANSPORT
            and isinstance(db, Database)
            and db.name == "logistics_staging"
        ):
            db.command("ping")  # No business reads or writes.
            checks["REAL_MONGO connected to logistics_staging"] = True
    except Exception:
        # Never expose exception text: drivers may include connection details.
        pass
    return checks


def _render_staging_identity_check(user: dict) -> None:
    """Temporary bounded QA diagnostic: authenticated Admin, staging host only."""
    if (
        user.get("role") != "admin"
        or urlparse(_current_app_url()).hostname != _STAGING_CUSTOMER_HOST
    ):
        return
    with st.expander("Staging QA — runtime identity", expanded=False):
        if not st.button("Kiểm tra runtime staging", key="staging-qa-identity"):
            return
        from core.auth import fresh_session_identity_for_action

        fresh = fresh_session_identity_for_action()
        if fresh is None or fresh.get("role") != "admin":
            st.error("Runtime identity: FAIL (Admin session required)")
            return
        checks = _staging_identity_checks()
        for label, passed in checks.items():
            st.write(f"{'PASS' if passed else 'FAIL'} — {label}")
        if all(checks.values()):
            st.success("STAGING_RUNTIME_IDENTITY=PASS")
        else:
            st.error("STAGING_RUNTIME_IDENTITY=FAIL — chưa được lưu dữ liệu QA")


def main() -> None:
    st.set_page_config(
        # Display brand only (core.config.DISPLAY_COMPANY_NAME) — the legal
        # company identity for business documents stays authority_companies.
        page_title=f"{DISPLAY_COMPANY_NAME} · Nội bộ",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Google always returns to HOME: make staging HOME customer-first.
    # Internal Admin remains available via ?portal=internal + password login.
    customer_only_entry = _customer_entry_mode(
        st.query_params.get("portal"), _current_app_url()
    )

    # OAuth return lands on this SAME app URL after Streamlit's own
    # /oauth2callback route.  A verified Google session is detected here before
    # the internal password gate; no query parameter carries a customer_id.
    oidc_state = customer_portal_oidc.current_oidc_session()
    if oidc_state.kind != customer_portal_oidc.STATE_NONE:
        from views import customer_dashboard

        customer_portal_oidc.activate_customer_session()
        if oidc_state.kind != customer_portal_oidc.STATE_AUTHENTICATED:
            customer_dashboard.render_oidc_problem(oidc_state)
            return
        from core import customer_portal

        try:
            # THE principal path: OIDC-verified email -> customers.id in MongoDB.
            principal = customer_portal.build_customer_principal(
                verified_email=oidc_state.email
            )
        except customer_portal.PortalAccessDenied:
            LOGGER.warning("CUSTOMER_PORTAL_ACCESS kind=denied")
            customer_dashboard.render_customer_denied()
            return
        except customer_portal.PortalDataError:
            LOGGER.warning("CUSTOMER_PORTAL_ACCESS kind=data_unavailable")
            customer_dashboard.render_customer_denied()
            return
        customer_dashboard.render_customer_dashboard(principal)
        return

    if customer_only_entry:
        # Customers never see the internal password/first-admin form or shell.
        # Successful Google callbacks use the OIDC branch above.
        from views import customer_dashboard

        customer_dashboard.render_customer_login_choice(standalone=True)
        return

    # AUTH GATE — must be before any business view-model is built or the
    # Logistics component is mounted.  When AUTH_REQUIRED=true and no session
    # exists, require_login() renders the existing login/bootstrap UI and
    # returns None, so we stop this Streamlit run immediately.
    user = require_login()
    if user is None:
        from views import customer_dashboard

        customer_dashboard.render_customer_login_choice()
        return

    # Authenticated-only imports stay OUT of the login critical path.  The
    # login screen does not need the large Logistics view-model graph or the
    # component bundle, so importing them before require_login() only adds
    # cold-session work without changing any authentication semantics.
    from views import customer_dashboard, logi_shell, logi_view_model

    # Real Logistics view-model. With no MONGO_URI configured the app runs on
    # an isolated staging transport; a real URI always takes precedence.
    vm = logi_view_model.build_view_model()
    _render_staging_identity_check(user)
    # Owner/Admin-only portal email control lives on the customers profile.
    # Support sees no control and the financial RBAC matrix is unchanged.
    customer_dashboard.render_owner_portal_access_control(user)
    logi_shell.render(vm)
