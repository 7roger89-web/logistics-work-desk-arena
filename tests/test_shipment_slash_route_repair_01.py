"""LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138) — durable regression guard.

Production symptom: an existing completed shipment opened the generic invalid
path screen ("Không tìm thấy màn hình / đường dẫn không hợp lệ") instead of the
real lot detail.

Reproduced root cause (source-level, then executed against the served bundle):
the route table exposes ONE dynamic shipment segment (`/lo-hang/:id`) whose
shipped matcher compiles the parameter to ``([^\\/]+)``, while every
shipment-detail URL was built by RAW concatenation on both sides
(``"/lo-hang/" + s.id`` in the shell, ``f"/lo-hang/{sid}?tab=…"`` in the
backend projections). An identity containing ``/`` — a real identity shape in
this project, see the closed contract repair for ``HDV 82/VSAL 2025`` (Issue
#59) — therefore produced a MULTI-segment pathname that matched only the ``*``
wildcard.

The repair states ONE rule twice, in the two languages that build the link:

* ``component/src/lib/shipmentRoute.ts`` — ``shipmentPath(id)`` →
  ``"/lo-hang/" + encodeURIComponent(id)``;
* ``views/logi_route.py`` — ``shipment_path(sid)`` → the byte-identical
  escaping (``urllib.parse.quote(..., safe="~!*'()")`` == ``encodeURIComponent``).

Query strings and anchors are appended AFTER the encoded segment by the caller,
never inside it. Shipment detail reads the identity from the RAW location
segment with exactly ONE decode (the same bounded mechanism the contract detail
has used since Issue #59, because react-router's param normalisation collapses a
literal uppercase ``%2F`` into ``/``).

Served-bundle guard: ``component/dist/logi-shell.js`` is what production
actually serves (``views/logi_shell.py``), and Issue #59 proved a source-only
route repair can leave stale shipped JS — so the bundle is asserted here too.
The DOM-level behaviour (list row → real ShipmentDetail, never the wildcard;
``%2F``/``?``/``#``/unicode identity classes) is proven against that same
committed bundle by ``tests/component/dom_acceptance_shipment_slash_id.mjs``.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import urllib.parse

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "component" / "src"
DIST_JS = ROOT / "component" / "dist" / "logi-shell.js"

#: Non-sensitive specimen identities and the route segment each must produce.
#: Values are the exact ``encodeURIComponent`` output for the id.
SPECIMENS: dict[str, str] = {
    "LO-0307": "LO-0307",
    "108313713320": "108313713320",
    "LO/LEGACY/001": "LO%2FLEGACY%2F001",
    "HDV 82/VSAL 2025": "HDV%2082%2FVSAL%202025",
    "A%2FB": "A%252FB",          # literal uppercase %2F stays literal
    "A%2fB": "A%252fB",
    "A%20B": "A%2520B",          # literal %20 must not become a space
    "A%25B": "A%2525B",          # literal %25 must not become "%"
    "A?B": "A%3FB",              # no query injection
    "A#B": "A%23B",              # no anchor injection
    "LO 0307": "LO%200307",
    "LÔ-0307": "L%C3%94-0307",
}

#: LIVE files that build a shipment-detail URL (unmounted pages such as
#: pages/Tracking.tsx are deliberately NOT scanned: they are not reachable from
#: App.tsx and a route repair must not touch dead code merely for grep hygiene).
LIVE_CONSTRUCTOR_FILES = (
    "pages/Shipments.tsx",
    "pages/Receivables.tsx",
    "pages/PartnerPayables.tsx",
    "pages/PartnerContext.tsx",
    "pages/Home.tsx",
    "pages/CreateShipment.tsx",
    "components/Layout.tsx",
    "components/CostCheck.tsx",
)

#: Live backend projections that compose a shipment route for the UI.
BACKEND_PRODUCER_FILES = (
    "views/logi_real_data.py",
    "views/logi_view_model.py",
    "views/logi_c1.py",
    "views/partner_context.py",
    "views/reconciliation_desk.py",
)

RAW_TS_CONCAT = re.compile(r'["`]/lo-hang/"\s*\+')
RAW_TS_TEMPLATE = re.compile(r"`/lo-hang/\$\{")
RAW_PY_CONCAT = re.compile(r'f?["\']/lo-hang/\{')
RAW_PY_PLUS = re.compile(r'["\']/lo-hang/["\']\s*\+')


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _served_bundle() -> str:
    assert DIST_JS.exists(), "served bundle missing"
    return DIST_JS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# A — the canonical Python helper (the one rule, second language)
# ---------------------------------------------------------------------------

class TestCanonicalPythonRouteHelper:
    def test_one_encoded_segment_per_identity(self):
        from views.logi_route import shipment_path

        for shipment_id, encoded in SPECIMENS.items():
            assert shipment_path(shipment_id) == "/lo-hang/" + encoded, shipment_id

    def test_canonical_ids_are_byte_identical(self):
        from views.logi_route import shipment_path

        for plain in ("LO-0306", "LO-0308", "108313713320", "0", "00123", "SHP-20260929-001"):
            assert shipment_path(plain) == f"/lo-hang/{plain}"

    def test_query_and_anchor_are_appended_after_the_encoded_segment(self):
        from views.logi_route import shipment_path

        base = shipment_path("LO/LEGACY/001")
        assert f"{base}?tab=nhap" == "/lo-hang/LO%2FLEGACY%2F001?tab=nhap"
        assert f"{base}?tab=nhap#fld-tk" == "/lo-hang/LO%2FLEGACY%2F001?tab=nhap#fld-tk"
        # The composed URL is never handed to the encoder: "?" and "#" keep
        # their URL meaning and are never escaped into the identity.
        assert "?" in f"{base}?tab=nhap"
        assert "%3F" not in base and "%23" not in base

    def test_identity_is_encoded_exactly_once(self):
        from views.logi_route import shipment_path

        # The helper takes the RAW identity. An identity whose own text already
        # contains an escape sequence stays literal (it is text, not a URL):
        # "A%2FB" is the four characters A % 2 F B, so its route carries %252F.
        assert shipment_path("A%2FB") == "/lo-hang/A%252FB"
        assert shipment_path("A%2FB").count("%252F") == 1
        # Encoding is not applied to an already-composed route string.
        composed = "/lo-hang/LO%2FLEGACY%2F001?tab=nhap"
        assert "?" in shipment_path("LO/LEGACY/001") + "?tab=nhap"
        assert composed.endswith("?tab=nhap") and "%3F" not in composed

    def test_identity_normalisation_matches_the_ui_projection(self):
        from views.logi_route import normalize_shipment_id, shipment_path

        assert normalize_shipment_id(None) == ""
        assert normalize_shipment_id(108313713320) == "108313713320"
        assert normalize_shipment_id("  LO-0306  ") == "LO-0306"
        assert normalize_shipment_id("A/1") == "A/1"
        assert shipment_path(None) == "/lo-hang/"

    def test_escaping_is_encodeuri_component_equivalent(self):
        """Both languages must produce the SAME bytes, not merely similar ones."""
        from views.logi_route import shipment_path

        reference = {
            i: "/lo-hang/" + urllib.parse.quote(i, safe="~!*'()") for i in SPECIMENS
        }
        assert {i: shipment_path(i) for i in SPECIMENS} == reference

        node = shutil.which("node")
        if node is None:  # pragma: no cover - environment without node
            pytest.skip("node unavailable: live encodeURIComponent cross-check skipped")
        ids = list(SPECIMENS)
        script = (
            "const ids=%s; console.log(JSON.stringify(ids.map(i=>encodeURIComponent(i))));"
            % __import__("json").dumps(ids)
        )
        js = __import__("json").loads(
            subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout
        )
        assert js == [SPECIMENS[i] for i in ids], "Python helper drifted from encodeURIComponent"


# ---------------------------------------------------------------------------
# B — the canonical TypeScript helper and the live frontend call sites
# ---------------------------------------------------------------------------

class TestFrontendRouteConstruction:
    def test_helper_encodes_the_identity_not_the_url(self):
        helper = _read("component/src/lib/shipmentRoute.ts")
        assert 'return "/lo-hang/" + encodeURIComponent(id);' in helper
        # One decode, in one place, for the whole route family.
        assert helper.count("decodeURIComponent(") == 1

    def test_every_live_constructor_routes_through_the_helper(self):
        expected = {
            "pages/Shipments.tsx": 3,
            "pages/Receivables.tsx": 3,
            "pages/PartnerPayables.tsx": 3,
            "pages/PartnerContext.tsx": 1,
            "pages/Home.tsx": 1,
            "pages/CreateShipment.tsx": 1,
            "components/Layout.tsx": 2,
            "components/CostCheck.tsx": 1,
        }
        assert set(expected) == set(LIVE_CONSTRUCTOR_FILES)
        total = 0
        for relative, count in expected.items():
            source = _read(f"component/src/{relative}")
            assert source.count("shipmentPath(") == count, relative
            assert '"../lib/shipmentRoute"' in source, relative
            assert not RAW_TS_CONCAT.search(source), relative
            assert not RAW_TS_TEMPLATE.search(source), relative
            # The query/anchor is appended AFTER the helper call, never inside it.
            assert not re.search(r"shipmentPath\([^)]*[?#]", source), relative
            total += count
        assert total == 15

    def test_no_live_raw_constructor_remains_anywhere_in_the_shell(self):
        offenders = []
        for path in SRC.rglob("*.ts*"):
            if path.name == "shipmentRoute.ts":  # owns the one raw prefix concat
                continue
            if path.suffix not in {".ts", ".tsx"}:
                continue
            source = path.read_text(encoding="utf-8")
            if RAW_TS_CONCAT.search(source) or RAW_TS_TEMPLATE.search(source):
                offenders.append(str(path.relative_to(ROOT)))
        # Unmounted pages (Tracking/Tasks/Agreements) are out of scope by design.
        assert all("Tracking.tsx" in o for o in offenders), offenders

    def test_detail_reads_the_raw_segment_with_exactly_one_decode(self):
        detail = _read("component/src/pages/ShipmentDetail.tsx")
        assert "shipmentIdFromPath(pathname, paramId)" in detail
        assert "const { id: paramId } = useParams();" in detail
        assert detail.count("decodeURIComponent(") == 0, "decode lives in the route helper, once"
        helper = _read("component/src/lib/shipmentRoute.ts")
        assert helper.count("decodeURIComponent(") == 1
        # A malformed segment never becomes a guess.
        assert "catch {" in helper and "return fallback;" in helper


# ---------------------------------------------------------------------------
# C — backend route producers (AST/source guard + live behaviour)
# ---------------------------------------------------------------------------

class TestBackendRouteProducers:
    def test_no_raw_backend_shipment_route_remains(self):
        for relative in BACKEND_PRODUCER_FILES:
            source = _read(relative)
            assert not RAW_PY_CONCAT.search(source), relative
            assert not RAW_PY_PLUS.search(source), relative

    def test_each_producer_calls_the_shared_helper(self):
        for relative in BACKEND_PRODUCER_FILES:
            source = _read(relative)
            assert "shipment_path" in source, relative
            if relative != "views/logi_real_data.py":
                assert re.search(r"shipment_path\(sid\)|shipment_path\(\w", source), relative

    def test_primary_action_keeps_query_and_anchor_outside_the_encoded_segment(self):
        source = _read("views/logi_real_data.py")
        assert 'f"{shipment_path(shipment_id)}?tab={status_tab}"' in source
        assert 'f"{shipment_path(shipment_id)}?tab={tab}"' in source
        assert 'f"#{anchor}"' in source

    def test_views_import_the_helper_rather_than_redeclaring_it(self):
        for relative in BACKEND_PRODUCER_FILES:
            source = _read(relative)
            assert "from views.logi_route import shipment_path" in source or (
                "from views import logi_route" in source
            ), relative

    def test_reconciliation_open_href_encodes_a_slash_identity(self):
        desk = pytest.importorskip("views.reconciliation_desk")
        party = {"party_type": "partner", "party_id": "P-1", "name": "Đối tác A"}

        def position(shipment_id: str) -> dict:
            key = f"{party['party_type']}:{party['party_id']}"
            obligation = {
                "obligation_id": "OBL-1", "purpose": "partner_cost_payable",
                "shipment_ids": [shipment_id], "amount": 1_000.0, "currency": "VND",
                "allocated": 0.0, "outstanding": 1_000.0, "allocation_ids": [],
                "status": "CONFIRMED", "incompatible_allocation_ids": [], "overallocated": False,
                "_partner_key": key,
            }
            return {
                "shipment_id": shipment_id,
                "partners": [{"partner": dict(party), "partner_key": key, "status": "CONFIRMED",
                              "totals_by_currency": {}, "obligations": [obligation], "payments": []}],
                "obligations": [obligation], "payments": [], "status": "CONFIRMED",
                "derived": True, "read_only": True,
            }

        for shipment_id, expected in (("LO-0308", "/lo-hang/LO-0308"),
                                      ("LO/LEGACY/001", "/lo-hang/LO%2FLEGACY%2F001")):
            projection = desk.reconciliation_projection(
                [position(shipment_id)], known_shipment_ids=[shipment_id]
            )
            row = projection["rows"][0]
            assert row["shipmentId"] == shipment_id
            assert row["openHref"] == expected
            assert row["canOpen"] is True

    def test_partner_context_open_href_encodes_a_slash_identity(self):
        pc = pytest.importorskip("views.partner_context")
        agent_id = "AGT-PHUANH"
        agent_name = "CÔNG TY TNHH PHÚ ANH LOGISTICS"

        def build(shipment_id: str) -> dict:
            shipments = {
                shipment_id: {
                    "id": shipment_id, "shipment_id": shipment_id, "customer": "An Phát JSC",
                    "status": "pending", "partner": {"name": agent_name, "role": "Thủ tục hải quan"},
                    "data": {"0.0": {}, "1.2": {}, "3.4": {"details": [], "payments": []}},
                }
            }
            payables = {"rows": [{
                "id": f"{shipment_id}|{agent_id}|VND", "partnerId": agent_id, "partnerName": agent_name,
                "shipmentId": shipment_id, "currency": "VND", "payable": 1_000.0, "paid": 0.0,
                "remaining": 1_000.0, "status": "CONFIRMED", "obligationIds": ["OBL-1"],
            }]}
            agents = {agent_id: {"agent_id": agent_id, "id": agent_id, "legal_name": agent_name}}
            return pc.partner_context_projection(
                agent_id, agents=agents, customers={}, shipments=shipments, payables=payables
            )

        for shipment_id, expected in (("LO-0308", "/lo-hang/LO-0308"),
                                      ("LO/LEGACY/001", "/lo-hang/LO%2FLEGACY%2F001")):
            view = build(shipment_id)
            rows = [r for r in view.get("shipments", []) if r["shipmentId"] == shipment_id]
            assert rows, f"{shipment_id} must be linked from the partner ledger"
            assert rows[0]["openHref"] == expected
            assert rows[0]["canOpen"] is True

    def test_primary_action_composes_encoded_segment_then_query_then_anchor(self):
        rd = pytest.importorskip("views.logi_real_data")
        cases = [
            ("LO-0308", {}, "nhap", "/lo-hang/LO-0308?tab=nhap"),
            ("LO/LEGACY/001", {}, "nhap", "/lo-hang/LO%2FLEGACY%2F001?tab=nhap"),
            ("LO/LEGACY/001",
             {"nextAction": {"code": "IMPORT_CUSTOMS", "label": "Khai báo", "detail": "d", "tone": "amber"}},
             "nhap", "/lo-hang/LO%2FLEGACY%2F001?tab=nhap#fld-tk"),
            ("LO/LEGACY/001",
             {"nextAction": {"code": "PROFILE_INCOMPLETE", "label": "Bổ sung hồ sơ", "detail": "d", "tone": "red"}},
             # Issue #188 B1 — the profile editor lives in the van-tai tab.
             "nhap", "/lo-hang/LO%2FLEGACY%2F001?tab=van-tai#shipment-execution-profile"),
        ]
        for shipment_id, profile, status_tab, expected in cases:
            action = rd.compose_primary_action(
                shipment_id=shipment_id, dashboard={}, execution_profile=profile, status_tab=status_tab
            )
            assert action["route"] == expected, shipment_id


# ---------------------------------------------------------------------------
# D — the SERVED bundle is part of the repair (Issue #59 lesson)
# ---------------------------------------------------------------------------

class TestServedBundleGuard:
    def test_served_bundle_carries_the_encoded_shipment_builder(self):
        bundle = _served_bundle()
        assert '"/lo-hang/" + encodeURIComponent' in bundle, (
            "slash-safe shipment builder missing from the served bundle — "
            "rebuild component/dist (npm run build) after a source route repair"
        )

    def test_served_bundle_has_no_raw_shipment_constructor(self):
        bundle = _served_bundle()
        leftovers = [
            token for token in re.findall(r'"/lo-hang/"\s*\+\s*[A-Za-z_$][\w$.]*', bundle)
            if "encodeURIComponent" not in token
        ]
        assert leftovers == [], leftovers
        assert "`/lo-hang/${" not in bundle, "raw template shipment path leaked into the bundle"

    def test_served_bundle_still_serves_the_single_segment_route(self):
        bundle = _served_bundle()
        assert '"/lo-hang/:id"' in bundle, "detail route token missing from the served bundle"
        assert 'data-testid": "not-found"' in bundle or 'data-testid="not-found"' in bundle
        # WHY a raw slash identity can never match: the compiled parameter class
        # excludes "/" by construction.
        assert "([^\\\\/]+)" in bundle


# ---------------------------------------------------------------------------
# E — ordinary identities stay byte-identical (no regression by "fixing")
# ---------------------------------------------------------------------------

class TestOrdinaryRoutesUnchanged:
    def test_ordinary_shipment_links_are_unchanged(self):
        from views.logi_route import shipment_path

        assert shipment_path("LO-0308") == "/lo-hang/LO-0308"
        assert shipment_path("648eb4d2-6f52-4d0f-9b3a-3f0b1e6f9a11") == (
            "/lo-hang/648eb4d2-6f52-4d0f-9b3a-3f0b1e6f9a11"
        )

    def test_issue117_numeric_identity_is_single_segment_and_unchanged(self):
        from views.logi_route import shipment_path

        # Issue #117 (legacy numeric BSON id) is a BACKEND READ concern and stays
        # untouched: the browser identity is the canonical decimal STRING, which
        # is already one segment — routing it needed no fallback and adds none.
        assert shipment_path("108313713320") == "/lo-hang/108313713320"

    def test_contract_route_helper_is_untouched(self):
        assert _read("component/src/lib/contractRoute.ts") == (
            '/** A contract number is one route segment, even when it contains slashes. */\n'
            "export function contractPath(id: string): string {\n"
            '  return "/hop-dong/" + encodeURIComponent(id);\n'
            "}\n"
        )
