"""LOGI_LOGIN_BACKGROUND_ROTATION_01 — focused regression for 10-image rotation.

Covers:
- 10 local WebP assets registered, exist, readable
- selection returns one of 10, stable within login visit, not flickering on failed login
- successful login preserves auth, next visit can rotate
- bootstrap still uses visual layer
- authenticated run emits no CSS
- CSS contains only selected background, compact card, mobile rule, no CDN
"""
from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from core import auth
from core.users import build_user_document

REPO_ROOT = Path(__file__).resolve().parents[1]
HERO_SVG_FALLBACK = REPO_ROOT / "assets" / "login_container_ship_hero.svg"
BG_DIR = REPO_ROOT / "assets" / "login" / "backgrounds"


class _FakeSessionState(dict):
    """dict that also supports the st.session_state.current_user attribute form."""

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


# ----------------------------------------------------------------- assets: 10 WebP

def test_ten_login_backgrounds_registered() -> None:
    files = auth._login_background_files()
    assert len(files) == 10, f"expected 10, got {len(files)}"
    assert auth._LOGIN_BG_COUNT == 10
    # exact naming 01..10 webp in backgrounds dir
    expected = [BG_DIR / f"login-bg-{i:02d}.webp" for i in range(1, 11)]
    assert files == expected


def test_every_registered_asset_exists_and_readable() -> None:
    files = auth._login_background_files()
    for p in files:
        assert p.is_file(), f"missing {p}"
        data = p.read_bytes()
        assert len(data) > 20_000, f"{p.name} stub-sized {len(data)}"
        # WebP magic: RIFF....WEBP or at least readable by pillow fallback check
        assert data[:4] == b"RIFF", f"{p.name} not WebP RIFF"
        assert b"WEBP" in data[:16], f"{p.name} missing WEBP header"


def test_fallback_svg_still_exists_for_graceful_degradation() -> None:
    # SVG may remain only as fallback, not as active background
    assert HERO_SVG_FALLBACK.is_file()
    raw = HERO_SVG_FALLBACK.read_bytes()
    assert len(raw) > 4096


def test_selection_returns_one_of_ten() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        # fresh visit, no prev
        idx = auth._current_login_bg_index()
        assert 1 <= idx <= 10
        # second call same visit returns same
        idx2 = auth._current_login_bg_index()
        assert idx2 == idx
        # uri corresponds to that idx
        uri = auth._login_background_uri()
        assert uri.startswith("data:image/webp;base64,")
        payload = base64.b64decode(uri.split(",", 1)[1])
        expected = (BG_DIR / f"login-bg-{idx:02d}.webp").read_bytes()
        assert payload == expected


def test_selected_background_stable_through_repeated_reruns() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        idx1 = auth._current_login_bg_index()
        # simulate several reruns (typing, etc.)
        for _ in range(5):
            idx = auth._current_login_bg_index()
            assert idx == idx1
        # css also stable
        css1 = auth._login_hero_css()
        css2 = auth._login_hero_css()
        assert css1 == css2


def test_failed_login_does_not_switch_background() -> None:
    mock_st = _mock_st()
    # first render: pick background
    mock_st.text_input.side_effect = ["sale.one", "wrong-passphrase-1"]
    mock_st.form_submit_button.return_value = False
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        auth.require_login()
        idx_before = mock_st.session_state.get(auth._LOGIN_BG_SESSION_KEY)

    # now failed submit: should keep same idx, not rotate
    mock_st.text_input.side_effect = ["sale.one", "wrong-passphrase-1"]
    mock_st.form_submit_button.return_value = True
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        auth.require_login()
        idx_after_fail = mock_st.session_state.get(auth._LOGIN_BG_SESSION_KEY)
        # failed login keeps per-visit key (does not clear to prev)
        assert idx_after_fail == idx_before
        assert mock_st.error.called
        assert mock_st.error.call_args.args[0] == "Tài khoản hoặc mật khẩu không đúng."
        assert "current_user" not in mock_st.session_state


def test_successful_login_preserves_auth_and_clears_per_visit_key() -> None:
    mock_st = _mock_st()
    mock_st.text_input.side_effect = ["sale.one", "sale-passphrase-1"]
    mock_st.form_submit_button.return_value = True
    with patch("core.database.load_users", return_value=_users_db()), \
         patch.object(auth, "st", mock_st), patch.object(auth, "AUTH_REQUIRED", True):
        # first pick idx
        mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = 3
        result = auth.require_login()
    assert result is None
    user = mock_st.session_state["current_user"]
    assert user["username"] == "sale.one"
    assert mock_st.rerun.called
    # per-visit cleared, prev stored
    assert auth._LOGIN_BG_SESSION_KEY not in mock_st.session_state
    assert mock_st.session_state.get(auth._LOGIN_BG_PREV_KEY) == 3


def test_next_login_after_logout_can_select_different_image() -> None:
    # simulate previous visit was idx=5
    mock_st = _mock_st()
    mock_st.session_state[auth._LOGIN_BG_PREV_KEY] = 5
    # mock random to be deterministic we just check it prefers different
    with patch.object(auth, "st", mock_st):
        # force choice to verify not stuck on 5 forever: call many times with same prev,
        # it should never return 5 (since choices exclude prev)
        picks = set()
        for _ in range(20):
            # clear per-visit to force new pick each iteration, but keep prev=5
            mock_st.session_state.pop(auth._LOGIN_BG_SESSION_KEY, None)
            # we temporarily reset prev to 5 each loop
            mock_st.session_state[auth._LOGIN_BG_PREV_KEY] = 5
            idx = auth._current_login_bg_index()
            picks.add(idx)
            assert idx != 5, "rotation should prefer different image from prev when 10 available"
        # at least we exercised randomness: picks subset of 1..10 excluding 5
        assert picks.issubset(set(range(1, 11)) - {5})
        # logout also stores prev and clears
        mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = 7
        with patch.object(auth, "st", mock_st):
            auth.logout()
        assert mock_st.session_state.get(auth._LOGIN_BG_PREV_KEY) == 7
        assert auth._LOGIN_BG_SESSION_KEY not in mock_st.session_state
        assert "current_user" not in mock_st.session_state


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
    assert "data:image/webp;base64," in heroes[0]
    assert "stAppViewContainer" in heroes[0]
    assert all("lg04-login-container" not in h for h in htmls)
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
    assert result is None
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
    assert mock_st.markdown.call_count == 0
    assert mock_st.form.call_count == 0


def test_css_contains_only_selected_background_not_all_ten() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        # pick idx 2 deterministically
        mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = 2
        css = auth._login_hero_css()
        assert css.startswith("<style>")
        assert "data:image/webp;base64," in css
        # count occurrences: should be exactly one data URI
        assert css.count("data:image/webp;base64,") == 1
        # ensure not embedding other assets: decode and compare to idx2
        import re as _re
        uris = _re.findall(r"data:image/webp;base64,[A-Za-z0-9+/=]+", css)
        assert len(uris) == 1
        payload = base64.b64decode(uris[0].split(",", 1)[1])
        assert payload == (BG_DIR / "login-bg-02.webp").read_bytes()
        # ensure other bg not in css (by not containing their payload tail)
        # check compact and responsive
        assert "max-width: 300px" in css
        assert "@media (max-width: 768px)" in css
        assert "min(300px, 88vw)" in css
        assert "stAppViewContainer" in css
        assert "stForm" in css
        for leak in ("pbkdf2", "Tài khoản hoặc mật khẩu"):
            assert leak not in css


def test_css_has_background_cover_and_per_image_position() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        for idx in (1, 3, 7):
            mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = idx
            css = auth._login_hero_css()
            assert "background-size: cover" in css
            desktop, mobile = auth._LOGIN_BG_POSITIONS[idx]
            assert f"background-position: {desktop};" in css
            assert f"background-position: {mobile};" in css


def test_no_external_cdn_dependency() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        css = auth._login_hero_css()
        # no http, no external url — check outside base64 payload to avoid false positives
        # strip data URIs before checking for cdn/external
        import re as _re
        css_without_data = _re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "", css)
        lowered = css_without_data.lower()
        for banned in ("http://", "https://", "cdn.", "cdn/", "url(http", "url('http", 'url("http'):
            assert banned not in lowered, f"CSS must not contain {banned!r}"
        # also ensure backgrounds dir is local
        assert "assets/login/backgrounds" not in css  # CSS should be data-uri, not file path
        # but the repo-owned files exist local
        for p in auth._login_background_files():
            assert "http" not in str(p)


def test_mobile_responsive_rule_remains() -> None:
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        css = auth._login_hero_css()
        assert "@media (max-width: 768px)" in css
        assert "88vw" in css or "90vw" in css


def test_transparent_glass_form_is_near_transparent_no_dark_veil() -> None:
    """Owner artwork stays primary; readability is handled locally by controls."""
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        for idx in (1, 2, 3, 4):
            mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = idx
            css = auth._login_hero_css()
            assert "background: rgba(8, 17, 26, 0.58)" not in css
            assert "blur(16px)" not in css
            assert "linear-gradient" not in css
        assert "background: transparent;" in css
        assert "-webkit-backdrop-filter: none;" in css
        assert "backdrop-filter: none;" in css
        assert "box-shadow: none;" in css
        assert "0 22px 55px" not in css
        assert "rgba(151, 197, 216, 0.16)" not in css
        assert 'background-image: url("data:image/webp;base64,' in css
        assert "background-size: cover;" in css
        desktop, mobile = auth._LOGIN_BG_POSITIONS[idx]
        assert f"background-position: {desktop};" in css
        assert f"background-position: {mobile};" in css
        assert "rgba(5, 12, 18, 0.62)" in css
        assert "rgba(255, 255, 255, 0.22)" in css
        assert "text-shadow:" in css
        assert css.count("data:image/webp;base64,") == 1
        assert "88vw" in css


def test_text_input_shell_stays_transparent_so_artwork_shows_through() -> None:
    """Regression guard for LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY.

    Streamlit's text-input shell (``stTextInputRootElement``) paints the theme's
    light ``secondaryBackgroundColor``. With only the ``<input>`` tinted, that
    shell showed through as an OPAQUE grey plate over the Owner artwork and the
    light typed ink on it measured ~2.2:1. The shell must be neutralised and the
    focus cue must be local to the field, not a page-level veil.
    """
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        for idx in (1, 2, 3, 4, 5):
            mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = idx
            css = auth._login_hero_css()
            assert '[data-testid="stForm"] [data-testid="stTextInputRootElement"] {' in css
            shell = css.split('[data-testid="stForm"] [data-testid="stTextInputRootElement"] {')[1].split("}")[0]
            assert "background: transparent !important;" in shell
            assert "border: none !important;" in shell
            assert "box-shadow: none !important;" in shell
            # typed ink is lighter than the field tint it sits on
            assert "color: #eef5f9 !important;" in css
            # focus is a local cue on the field, not a full-screen overlay
            assert "[data-testid=\"stForm\"] input:focus" in css
            # nothing that darkens the whole artwork is reintroduced
            assert "linear-gradient" not in css
            assert "backdrop-filter: blur" not in css
            assert "stAppViewContainer\"], [data-testid" not in css
            # reveal icon + keyboard hint inside the field stay visible on the tint
            assert '[data-testid="stTextInputRootElement"] span' in css


def test_duplicate_visual_pair_09_10_never_consecutive() -> None:
    """Visual-equivalence: 09 and 10 are byte-identical Owner visuals.

    The selector must exclude BOTH 9 and 10 when prev is either 9 or 10,
    so 09->10 and 10->09 never occur as a visual change. For all other
    prev values only that single index is excluded. Result stays in 1..10
    and same-login stability is unchanged.
    """
    # direct selector
    for prev in (9, 10):
        for _ in range(30):
            nxt = auth._choose_login_bg_index(prev)
            assert 1 <= nxt <= 10, f"out of range {nxt}"
            assert nxt not in (9, 10), f"prev={prev} must not pick 9 or 10, got {nxt}"
    # normal prev still excludes only itself
    for prev in (1, 3, 5, 7):
        for _ in range(20):
            nxt = auth._choose_login_bg_index(prev)
            assert 1 <= nxt <= 10
            assert nxt != prev, f"prev={prev} picked itself {nxt}"
            # but 9/10 remain pickable for normal prev
    # via session mechanism
    mock_st = _mock_st()
    with patch.object(auth, "st", mock_st):
        mock_st.session_state[auth._LOGIN_BG_PREV_KEY] = 9
        mock_st.session_state.pop(auth._LOGIN_BG_SESSION_KEY, None)
        idx = auth._current_login_bg_index()
        assert idx not in (9, 10), f"prev 9 via session picked {idx}"
        mock_st.session_state[auth._LOGIN_BG_PREV_KEY] = 10
        mock_st.session_state.pop(auth._LOGIN_BG_SESSION_KEY, None)
        idx = auth._current_login_bg_index()
        assert idx not in (9, 10), f"prev 10 via session picked {idx}"
        # stability: same visit keeps same idx even when prev was 9/10
        mock_st.session_state[auth._LOGIN_BG_SESSION_KEY] = 8
        assert auth._current_login_bg_index() == 8
        assert auth._current_login_bg_index() == 8

