"""Single Streamlit Components v2 component root for the Logi-good shell.

Architecture (Phase B — unchanged shape, real inner data):
    Python Logistics view-model
      → ONE st.components.v2.component (logi_shell)
      → literal Logi-good React UI (component/dist build)
      → typed v2 trigger events (setTriggerValue)
      → ONE bounded Python dispatcher (views.logi_view_model.dispatch)

No components.v1, no iframe, no postMessage bridge, no query-param bridge.
The component is mounted inside Streamlit's DOM with style isolation
(shadow root); the built bundle is a browser-only ES module with zero
Node-global references (verified by scripts/scan_process.py).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from views import logi_view_model

_DIST = Path(__file__).resolve().parent.parent / "component" / "dist"
JS_FILE = _DIST / "logi-shell.js"
CSS_FILE = _DIST / "logi-shell.css"


@st.cache_resource(show_spinner=False)
def _load_bundle() -> tuple[str, str]:
    if not JS_FILE.exists() or not CSS_FILE.exists():
        raise RuntimeError(
            "Logi-good component build not found. Run: cd component && npm ci && npm run build"
        )
    js = JS_FILE.read_text(encoding="utf-8")
    css = CSS_FILE.read_text(encoding="utf-8")
    return js, css


_js, _css = _load_bundle()

# The component registry is per-Runtime (streamlit run vs. AppTest), so the
# one-time registration is deferred to the first render inside a runtime.
_state: dict = {"renderer": None, "runtime": None}


def _renderer():
    from streamlit.runtime import Runtime

    try:
        runtime = Runtime.instance()
    except RuntimeError:
        runtime = None
    if _state["renderer"] is None or _state["runtime"] is not runtime:
        _state["renderer"] = st.components.v2.component(
            "logi_shell",
            css=_css,
            js=_js,
            isolate_styles=True,
        )
        _state["runtime"] = runtime
    return _state["renderer"]


COMPONENT_KEY = "logi-shell"
CALLBACK_DISPATCHED_FLAG = "_logi_callback_dispatched"


def _on_component_event() -> None:
    """Streamlit Components v2 trigger callback.

    Executes as a prefix BEFORE the main script rerun starts. Reads the
    component trigger state from ``st.session_state[COMPONENT_KEY]`` and
    dispatches the business action in CALLBACK MODE (no explicit st.rerun).
    The pending normal rerun then builds ONE fresh view-model carrying the
    updated data and authoritative readback.
    """
    if st.session_state.get(CALLBACK_DISPATCHED_FLAG):
        return
    raw = st.session_state.get(COMPONENT_KEY)
    if raw is None:
        return
    logi_view_model.dispatch(raw, is_callback=True)
    st.session_state[CALLBACK_DISPATCHED_FLAG] = True


def render(view_model: dict) -> None:
    """Mount the ONE component root and run the bounded event dispatcher.

    Each declared event gets its own ``on_<event>_change`` trigger callback so
    the v2 runtime surfaces it as a typed trigger value and executes
    ``_on_component_event`` as a prefix before the main script rerun. The set
    below is exactly ``logi_view_model.ALL_EVENTS`` — nothing else can reach
    Python.
    """
    kwargs: dict = {
        "key": COMPONENT_KEY,
        "data": view_model,
        "width": "stretch",
        "height": "content",
    }
    for event_name in sorted(logi_view_model.ALL_EVENTS):
        kwargs[f"on_{event_name}_change"] = _on_component_event
    result = _renderer()(**kwargs)
    # Post-mount guard: if the trigger was already dispatched in prefix
    # callback mode, do NOT dispatch the same trigger a second time.
    # Seq guard remains a safety net, not the primary architecture.
    if not st.session_state.pop(CALLBACK_DISPATCHED_FLAG, False):
        logi_view_model.dispatch(result)

