"""LOGI-199 T5 — the three legacy paths are deliberate redirects, not screens.

The real-browser route audit excludes them from distinct-surface coverage; this
pins the redirect targets at source so the exclusion stays truthful.
"""
import re
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "component/src/App.tsx").read_text(encoding="utf-8")


def target(path: str) -> str:
    m = re.search(r'<Route path="%s" element={<Navigate to="([^"]+)" replace />} />' % re.escape(path), APP)
    assert m, f"{path} is no longer a plain redirect; audit it as a real screen"
    return m.group(1)


def test_legacy_paths_redirect_to_audited_screens():
    assert target("/viec-can-xu-ly") == "/lo-hang"
    assert target("/theo-doi") == "/lo-hang"
    assert target("/thoa-thuan-ban-giao") == "/kinh-doanh-bao-gia"
    for dest in ("/lo-hang", "/kinh-doanh-bao-gia"):
        assert f'<Route path="{dest}" element={{<' in APP
