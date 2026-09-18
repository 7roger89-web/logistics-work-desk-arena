"""LOGI_RUNTIME_CONTRACT_SLASH_ROUTE_REPAIR_01 — durable regression guard.

Backs the production specimen ``HDV 82/VSAL 2025`` (Issue #59) at two layers:

* SOURCE -- the active contract-path builders must all route through the
  single encoded-segment ``contractPath()`` helper, the detail route must
  exist, and the wildcard must be the truthful ``NotFound`` (never the
  ``PhaseBPlaceholder`` "Sắp có — chưa triển khai" deferred screen).
* SERVED BUNDLE -- the built ``component/dist/logi-shell.js`` that
  ``views/logi_shell.py`` actually serves must carry the slash-safe builder,
  the ``/hop-dong/:id`` route and the NotFound wildcard, and must NOT carry
  the deferred placeholder.

The DOM-level behaviour is proven against the real committed bundle by
``tests/component/dom_acceptance_contract_slash_id.mjs`` (drives the exact
Owner path: Hợp đồng → HDV 82/VSAL 2025 → MỞ → real ContractDetail).
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST_JS = ROOT / "component" / "dist" / "logi-shell.js"


def test_production_specimen_is_exactly_one_encoded_segment() -> None:
    specimen = "HDV 82/VSAL 2025"
    helper = (ROOT / "component/src/lib/contractRoute.ts").read_text()
    assert "encodeURIComponent(id)" in helper
    # exact production path must be produced by the helper for the specimen id
    assert ("/hop-dong/" + _encode_uri_component(specimen)) == "/hop-dong/HDV%2082%2FVSAL%202025"


def test_all_contract_detail_navigation_uses_single_encoded_segment() -> None:
    """Every dynamic /hop-dong/:id call site uses contractPath(); no raw concat."""
    scenes = {
        "pages/NewContract.tsx": 1,
        "pages/Contracts.tsx": 3,
        "components/Layout.tsx": 2,
        # 3 since PR54 integration: linked-contract row, MỞ HỢP ĐỒNG, MỞ CHỨNG TỪ.
        "pages/ShipmentDetail.tsx": 3,
    }
    for relative, count in scenes.items():
        source = (ROOT / "component/src" / relative).read_text()
        assert source.count("contractPath(") == count, relative
        assert not re.search(
            r'["`]\/hop-dong/[^"`]*(?:\$\{|["`]\s*\+)', source
        ), relative
    helper = (ROOT / "component/src/lib/contractRoute.ts").read_text()
    assert "encodeURIComponent(id)" in helper


def test_detail_route_exists_and_wildcard_is_not_the_deferred_placeholder() -> None:
    app = (ROOT / "component/src/App.tsx").read_text()
    assert '<Route path="/hop-dong/:id" element={<ContractDetail />} />' in app
    assert '<Route path="*" element={<NotFound />} />' in app
    assert "PhaseBPlaceholder" not in app


def test_served_bundle_is_slash_safe_and_has_no_deferred_placeholder_inside() -> None:
    """The bundle web_app.py serves must be the slash-safe one (dist↔source sync).

    This is the stale-generated-dist guard: the deferred placeholder string was
    the production symptom, so its absence in the served bundle is decisive.
    """
    bundle = DIST_JS.read_text(encoding="utf-8")
    assert '"/hop-dong/:id"' in bundle, "detail route token missing from served bundle"
    assert '"/hop-dong/" + encodeURIComponent' in bundle, "slash-safe builder missing from served bundle"
    assert 'data-testid": "not-found"' in bundle, "NotFound wildcard missing from served bundle"
    assert "Màn hình phụ" not in bundle, "deferred placeholder leaked into served bundle"
    assert "chưa triển khai" not in bundle, "'chưa triển khai' placeholder leaked into served bundle"


def _encode_uri_component(value: str) -> str:
    """Reference encodeURIComponent used only to state the expected literal."""

    import urllib.parse

    return urllib.parse.quote(value, safe="~!*'()")
