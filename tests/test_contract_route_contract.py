"""Bounded source contract backing the real-bundle route acceptance test."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_active_contract_path_builders_use_single_encoded_segment():
    expected = {
        'pages/NewContract.tsx': 1,
        'pages/Contracts.tsx': 3,
        'components/Layout.tsx': 2,
        # 3 since LOGI_UAT_APPROVED_REPAIRS_INTEGRATE_DEPLOY_01: the linked-contract
        # "Hợp đồng" row, "MỞ HỢP ĐỒNG", and the P1-B "MỞ CHỨNG TỪ" document handoff
        # all route through the shared helper. The raw-concat ban below is unchanged.
        'pages/ShipmentDetail.tsx': 3,
    }
    for relative, count in expected.items():
        source = (ROOT / 'component/src' / relative).read_text()
        assert source.count('contractPath(') == count, relative
        assert not re.search(r'["`]\/hop-dong/[^"`]*(?:\$\{|["`]\s*\+)', source), relative
    helper = (ROOT / 'component/src/lib/contractRoute.ts').read_text()
    assert 'encodeURIComponent(id)' in helper


def test_current_nav_has_no_deferred_or_nonexistent_target():
    app = (ROOT / 'component/src/App.tsx').read_text()
    nav = (ROOT / 'component/src/lib/data.ts').read_text().split('const live =')[0]
    targets = re.findall(r'to: "([^"]+)"', nav)
    routes = re.findall(r'<Route path="([^"]+)"', app)
    assert targets and all(target in routes for target in targets)
    assert 'soon: true' not in nav
    assert '<Route path="*" element={<NotFound />} />' in app
    assert 'PhaseBPlaceholder' not in app
