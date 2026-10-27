"""Streamlit Components v2 mount for the HEXA customer-portal reference UI.

The visual layer is the Owner's ``HEXA_LucGiac_DEMO.html`` reference (826,336
bytes, SHA-256 ``b91c878e44256e741c533f75e62fdcc89507413d609b0b3d365af85810fbb40a``)
ported into three static assets under ``assets/customer_portal``:

* ``hexa-portal.html`` — the reference markup (demo copy and inline handlers
  removed; behaviour is bound by id in JS).
* ``hexa-portal.css``  — the reference stylesheet, re-scoped to the component
  root because a v2 mount lives in a shadow root.
* ``hexa-portal.js``   — the reference layout/interaction engine with every
  fabricated-data path deleted (no ``window.__DEMO_DATA__``, no canvas/PDF
  voucher generator, no fake download buttons, no demo comment form).
* ``sea-chart.webp``   — the reference sea chart, byte-identical to the copy
  embedded in the reference file.

This is the SAME existing entrypoint (``views.web_app`` → this module), the SAME
single component technology already used by ``views.logi_shell``. It does not
start a server, add a framework bridge, or widen the read boundary: every byte
of data comes from ``core.customer_portal`` via ``core.customer_journey``.
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "customer_portal"
HTML_FILE = ASSET_DIR / "hexa-portal.html"
CSS_FILE = ASSET_DIR / "hexa-portal.css"
JS_FILE = ASSET_DIR / "hexa-portal.js"
SEA_CHART_FILE = ASSET_DIR / "sea-chart.webp"

#: SHA-256 of the reference file these assets were ported from. Recorded so a
#: later reader can re-derive provenance instead of trusting this docstring.
REFERENCE_SHA256 = "b91c878e44256e741c533f75e62fdcc89507413d609b0b3d365af85810fbb40a"
REFERENCE_BYTES = 826336
SEA_CHART_SHA256 = "f83d42167dffcb1ac629f261923408a2c6d5d6d7564cf63083aa869bababdef9"

COMPONENT_KEY = "hexa-customer-portal"


class PortalAssetError(RuntimeError):
    """The reference-derived assets are missing or unreadable; fail closed."""


@st.cache_resource(show_spinner=False)
def load_assets() -> tuple[str, str, str, str]:
    """Read the ported reference assets once per runtime.

    Returns ``(html, css, js, sea_chart_data_url)``. Missing assets raise so the
    caller can render a truthful error instead of a blank or a fake dashboard.
    """
    try:
        html = HTML_FILE.read_text(encoding="utf-8")
        css = CSS_FILE.read_text(encoding="utf-8")
        js = JS_FILE.read_text(encoding="utf-8")
        sea_chart = SEA_CHART_FILE.read_bytes()
    except OSError as exc:  # pragma: no cover - packaging guard
        raise PortalAssetError("HEXA portal assets unavailable") from exc
    data_url = "data:image/webp;base64," + base64.b64encode(sea_chart).decode("ascii")
    return html, css, js, data_url


_state: dict = {"renderer": None, "runtime": None}


def _renderer():
    """Register the component once per Streamlit runtime (AppTest-safe)."""
    from streamlit.runtime import Runtime

    try:
        runtime = Runtime.instance()
    except RuntimeError:  # pragma: no cover - bare runtime
        runtime = None
    if _state["renderer"] is None or _state["runtime"] is not runtime:
        html, css, js, _chart = load_assets()
        _state["renderer"] = st.components.v2.component(
            "hexa_customer_portal",
            html=html,
            css=css,
            js=js,
            isolate_styles=True,
        )
        _state["runtime"] = runtime
    return _state["renderer"]


def render(model: dict, *, height: str | int = "content") -> None:
    """Mount the reference UI for one server-built model.

    The component is intentionally presentational: lot selection, node bubbles,
    modals and zoom are local UI state (the acceptance contract allows that) and
    nothing is written back to the server. A Python rerun rebuilds the payload
    from the trusted principal, so a forged browser state cannot change tenancy.
    """
    _html, _css, _js, sea_chart = load_assets()
    payload = {"model": model, "assets": {"sea_chart": sea_chart}}
    _renderer()(
        key=COMPONENT_KEY,
        data=payload,
        width="stretch",
        height=height,
    )
