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

import streamlit as st

from core import customer_portal_oidc
from core.auth import require_login
from core.config import DISPLAY_COMPANY_NAME


def main() -> None:
    st.set_page_config(
        # Display brand only (core.config.DISPLAY_COMPANY_NAME) — the legal
        # company identity for business documents stays authority_companies.
        page_title=f"{DISPLAY_COMPANY_NAME} · Nội bộ",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",
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
        except (customer_portal.PortalAccessDenied, customer_portal.PortalDataError):
            customer_dashboard.render_customer_denied()
            return
        customer_dashboard.render_customer_dashboard(principal)
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
    # Owner/Admin-only portal email control lives on the customers profile.
    # Support sees no control and the financial RBAC matrix is unchanged.
    customer_dashboard.render_owner_portal_access_control(user)
    logi_shell.render(vm)
