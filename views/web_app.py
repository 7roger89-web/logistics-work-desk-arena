"""Logistics Work Desk — Logi-good shell entry (Phase B).

The entire visible shell + active page is ONE Streamlit Components v2
component root running the literal Logi-good React UI. Inner data is the
presentation view-model over the CURRENT Logistics readers and writers
(``views.logi_real_data`` + ``views.logi_view_model``). The visible donor UI is
frozen; Phase B changed the data and the business actions, not the design.
"""

from __future__ import annotations

import streamlit as st

from views import logi_shell, logi_view_model


def main() -> None:
    st.set_page_config(
        page_title="Phú Anh Logistics · Nội bộ",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Real Logistics view-model. With no MONGO_URI configured the app runs on
    # an isolated staging transport; a real URI always takes precedence.
    vm = logi_view_model.build_view_model()
    logi_shell.render(vm)
