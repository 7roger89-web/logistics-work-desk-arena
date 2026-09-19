"""Logistics Work Desk — Logi-good shell entry (Phase B).

The entire visible shell + active page is ONE Streamlit Components v2
component root running the literal Logi-good React UI. Inner data is the
presentation view-model over the CURRENT Logistics readers and writers
(``views.logi_real_data`` + ``views.logi_view_model``). The visible donor UI is
frozen; Phase B changed the data and the business actions, not the design.
"""

from __future__ import annotations

import streamlit as st

from core.auth import require_login
from core.config import DISPLAY_COMPANY_NAME
from views import logi_shell, logi_view_model


def main() -> None:
    st.set_page_config(
        # Display brand only (core.config.DISPLAY_COMPANY_NAME) — the legal
        # company identity for business documents stays authority_companies.
        page_title=f"{DISPLAY_COMPANY_NAME} · Nội bộ",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # AUTH GATE — must be before any business view-model is built or the
    # Logistics component is mounted.  When AUTH_REQUIRED=true and no session
    # exists, require_login() renders the existing login/bootstrap UI and
    # returns None, so we stop this Streamlit run immediately.
    user = require_login()
    if user is None:
        return

    # Real Logistics view-model. With no MONGO_URI configured the app runs on
    # an isolated staging transport; a real URI always takes precedence.
    vm = logi_view_model.build_view_model()
    logi_shell.render(vm)
