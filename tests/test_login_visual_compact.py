"""LOGI_LOGIN_VISUAL_COMPACT_01 — focused regression for the compact hero login.

A. AUTH behavior of ``require_login()`` is unchanged by the visual layer:
   valid credentials -> ``_authenticate`` -> session + rerun; invalid
   credentials -> generic error, no session; the first-admin bootstrap is
   still reachable when the user store is empty; an existing valid session
   is still revalidated without rendering any login screen.
B. VISUAL structure: one repo-owned asset exists locally (original SVG,
   no rendered text, no external references); the login CSS inlines it as
   a data URI; the card is compact (max-width 300px); a mobile media query
   exists; and the hero CSS is injected ONLY while logged out, so an
   authenticated run never carries it (no global restyle of the app).
"""
from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from core import auth
from core.users import build_user_document

REPO_ROOT = Path(__file__).resolve().parents[1]
HERO_ASSET = REPO_ROOT / "assets" / "login_container_ship_hero.svg"


class _FakeSessionState(dict):
    """dict that also supports the ``st.session_state.current_user`` attribute form."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value) -> None:
        self[name] = value

    def __delattr__(self, name) -> None:
        try:
            del self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def _mock_st(session_user: dict | None = None) -> MagicMock:
    mock = MagicMock()
    state = _FakeSessionState()
    if session_user:
        state["current_user"] = dict(session_user)
    mock.session_state = state
    return mock


def _users_db() -> dict:
    return {
        "sale.one": build_user_document(
            username="sale.one",
            password="sale-passphrase-1",
            display_name="Sale One",
            role="sale",
            created_by="admin",
        ),
    }


def _rendered_htmls(mock_st: MagicMock) -> list[str]:
    return [c.args[0] for c in mock_st.markdown.call_args_list if c.args]


# ----------------------------------------------------------------- B. asset


def test_hero_asset_is_an_original_local_svg() -> None:
    assert HERO_ASSET.is_file()
    raw = HERO_ASSET.read_bytes()
    assert len(raw) > 4096, "hero asset looks stub-sized"
    text = raw.decode("utf-8")
    assert text.lstrip().startswith("<svg")
    assert "<text" not in text, "artwork must not contain rendered text"
    # self-contained: no external fetches (the xmlns namespace literal is
    # an XML identifier, not a network reference)
    for external in ('href="http', "xlink:href", "url(http", "<image"):
        assert external not in text, f"asset must not reference {external!r}"


def test_composition_keeps_worker_tiny_and_rope_connected() -> None:
    """Static geometry proof of the visual concept: HUMAN TINY / SHIP MASSIVE.

    No browser is available in this executor, so the composition's scale
    contrast and the tow-line connection are asserted from the SVG geometry
    itself (the exact coordinates the browser would rasterize).
    """
    import re
    import xml.etree.ElementTree as ET

    ns = "{http://www.w3.org/2000/svg}"
    root = ET.parse(HERO_ASSET).getroot()

    def pairs(d: str) -> list[tuple[float, float]]:
        return [(float(a), float(b)) for a, b in re.findall(
            r"(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)", d
        )]

    def bbox(points) -> tuple[float, float, float, float]:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs), max(ys)

    hulls = [el for el in root.iter(f"{ns}path") if el.get("fill") == "url(#hull)"]
    assert hulls, "ship hull path missing"
    hx0, hy0, hx1, hy1 = bbox(pairs(hulls[0].get("d")))
    ship_width = hx1 - hx0
    assert ship_width > 700, "ship must dominate the frame"

    figures = [el for el in root.iter(f"{ns}g") if el.get("stroke") == "#04070c"]
    assert figures, "worker figure missing"
    fig_xy = []
    for el in figures[0].iter():
        d = el.get("d")
        if d:
            fig_xy += pairs(d)
        if el.tag == f"{ns}circle":
            cx, cy, r = float(el.get("cx")), float(el.get("cy")), float(el.get("r"))
            fig_xy += [(cx - r, cy - r), (cx + r, cy + r)]
    fx0, fy0, fx1, fy1 = bbox(fig_xy)
    fig_height = fy1 - fy0
    assert fig_height < 60, "worker must be tiny in the composition"
    assert fig_height < ship_width / 12, "worker must be absurdly smaller than the ship"
    assert fx1 < hx0, "worker stands apart from (left of) the vessel"

    ropes = [el for el in root.iter(f"{ns}path") if el.get("stroke") == "#c89a63"]
    assert ropes, "tow line missing"
    nums = pairs(ropes[0].get("d"))
    start, end = nums[0], nums[-1]
    center = ((fx0 + fx1) / 2, (fy0 + fy1) / 2)
    assert ((start[0] - center[0]) ** 2 + (start[1] - center[1]) ** 2) ** 0.5 < 40, (
        "tow line must start at the worker's hands"
    )
    assert hx0 - 20 <= end[0] <= hx1 and hy0 - 20 <= end[1] <= hy1, (
        "tow line must reach into the ship's hull"
    )


def test_background_data_uri_inlines_the_local_asset() -> None:
    uri = auth._login_background_uri()
    assert uri.startswith("data:image/svg+xml;base64,")
    payload = base64.b64decode(uri.split(",", 1)[1])
    assert payload == HERO_ASSET.read_bytes()


def test_login_css_is_compact_scoped_and_responsive() -> None:
    css = auth._login_hero_css()
    assert css.startswith("<style>")
    assert "data:image/svg+xml;base64," in css
    assert "max-width: 300px" in css, "card must stay compact (~300px)"
    assert "@media (max-width: 768px)" in css, "mobile rule missing"
    assert "min(300px, 88vw)" in css
    assert "stAppViewContainer" in css, "background must be scoped to the viewport"
    assert "stForm" in css, "card panel must target the real form wrapper"
    for leak in ("pbkdf2", "Tài khoản hoặc mật khẩu"):
        assert leak not in css


# ------------------------------------------------------- A. auth behavior


def test_login_screen_injects_hero_once_and_renders_the_form() -> None:
    mock_st = _mock_st()
    mock_st.text_input.side_effect = ["  sale.one  ", "sale-passphrase-1"]
    mock_st.form_submit_button.return_value = False  # render only, no submit
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
    assert result is None
    htmls = _rendered_htmls(mock_st)
    heroes = [h for h in htmls if "stAppViewContainer" in h]
    assert len(heroes) == 1, "hero CSS must be injected exactly once"
    assert "data:image/svg+xml;base64," in heroes[0]
    assert all("lg04-login-container" not in h for h in htmls), (
        "old plain-card markup must be gone"
    )
    assert mock_st.form.call_args.args[0] == "login_form"
    keys = [c.kwargs.get("key") for c in mock_st.text_input.call_args_list]
    assert keys == ["login_username", "login_password"]
    assert mock_st.form_submit_button.called
    assert "current_user" not in mock_st.session_state


def test_valid_login_still_sets_session_and_reruns() -> None:
    mock_st = _mock_st()
    mock_st.text_input.side_effect = ["sale.one", "sale-passphrase-1"]
    mock_st.form_submit_button.return_value = True
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
    assert result is None  # screen returns; the rerun continues the session
    user = mock_st.session_state["current_user"]
    assert user["username"] == "sale.one"
    assert user["role"] == "sale"
    assert mock_st.rerun.called
    assert not mock_st.error.called


def test_invalid_login_still_rejected_with_generic_error() -> None:
    mock_st = _mock_st()
    mock_st.text_input.side_effect = ["sale.one", "wrong-passphrase-1"]
    mock_st.form_submit_button.return_value = True
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
    assert result is None
    assert "current_user" not in mock_st.session_state
    assert not mock_st.rerun.called
    assert mock_st.error.called
    assert mock_st.error.call_args.args[0] == "Tài khoản hoặc mật khẩu không đúng."


def test_bootstrap_path_still_reachable_with_hero() -> None:
    mock_st = _mock_st()
    mock_st.form_submit_button.return_value = False
    with patch("core.database.load_users", return_value={}), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
    assert result is None
    htmls = _rendered_htmls(mock_st)
    assert any("stAppViewContainer" in h for h in htmls), "hero must cover bootstrap too"
    assert any("lg05-bootstrap" in h for h in htmls)
    assert mock_st.form.call_args.args[0] == "bootstrap_form"


def test_authenticated_run_does_not_carry_login_css() -> None:
    session_user = {
        "username": "sale.one",
        "display_name": "Sale One",
        "role": "sale",
        "user_id": "u1",
        "email": "",
    }
    mock_st = _mock_st(session_user)
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        result = auth.require_login()
    assert result is not None
    assert result["username"] == "sale.one"
    # No login screen rendered -> no hero CSS injection on an authenticated run.
    assert mock_st.markdown.call_count == 0
    assert mock_st.form.call_count == 0
