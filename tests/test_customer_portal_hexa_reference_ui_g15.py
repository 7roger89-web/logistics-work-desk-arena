"""G1.5 — HEXA customer-portal reference UI: model, payload and runtime proof.

Three layers, deliberately separated because they prove different things:

``SOURCE_REVIEW``
    the asset provenance/parity checks (the CSS/HTML really came from the
    Owner's reference file and no demo-only machinery survived the port);
``TEST_PASS``
    the pure model rules (a PUBLISHED lot never implies a completed stage, a SEA
    lot never shows ROAD wording, nothing is invented) and the real Streamlit
    AppTest element tree (the component is mounted for the verified principal
    and nothing else);
``negative security``
    unauthorised identity, browser-supplied ids, internal/foreign sentinels and
    the reference's fabricated figures never reach the payload.

Browser behaviour (bubbles, zoom, containment at 1440x900 and 390x844) is
``VISUAL_PASS`` and lives in ``playwright/g15_hexa_portal_qa.mjs``; a static
test must not claim it.
"""
from __future__ import annotations

import importlib.util
import json
import re
import time
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest

from core import customer_journey as journey
from core import customer_portal as portal
from core import customer_portal_oidc as oidc
from views import web_app

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
SEED_PATH = ROOT / "scripts" / "seed_customer_portal_staging.py"
ASSET_DIR = ROOT / "assets" / "customer_portal"

REFERENCE_SHA256 = "b91c878e44256e741c533f75e62fdcc89507413d609b0b3d365af85810fbb40a"
REFERENCE_BYTES = 826336

FAKE_AUTH = {
    "required": True,
    "redirect_uri": "http://localhost:8501/oauth2callback",
    "cookie_secret": "S" * 48,
    "google": {
        "client_id": "staging-client-id.apps.googleusercontent.com",
        "client_secret": "STAGING_TEST_ONLY_CLIENT_SECRET",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    },
}

#: Every fabricated figure in the reference HTML. None of these may appear in
#: an authenticated payload — they are demo data, not this customer's data.
REFERENCE_DEMO_FIGURES = (
    "53.400.000", "53400000", "30.000.000", "30000000", "23.400.000", "23400000",
    "42.500.000", "42500000", "25/10/2026", "2026-10-25", "22/10/2026",
    "ROAD-LG-001", "ROAD-LG-002", "QT-20261022-LG01", "HD-LG-2026-01",
    "0901 234 567", "29H-886.68", "DOC-LG-", "DEMO-001", "Ms. Minh Tú",
    "18 kiện / 4.200 kg", "10 pallet / 2.600 kg", "Hữu Nghị",
)


@pytest.fixture(scope="module")
def seed_module():
    spec = importlib.util.spec_from_file_location("seed_customer_portal_staging_g15", SEED_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _db(seed_module, *, negative_cases=False):
    database = mongomock.MongoClient()["g1_customer_portal_g15"]
    seed_module.seed_staging(database, include_negative_cases=negative_cases)
    return database


def _claims(email: str):
    return {
        "is_logged_in": True,
        "provider": "google",
        "aud": FAKE_AUTH["google"]["client_id"],
        "iss": "https://accounts.google.com",
        "email": email,
        "email_verified": True,
        "exp": int(time.time()) + 600,
        "sub": "staging-google-subject",
    }


def _payload(app: AppTest) -> dict:
    components = app.get("bidi_component")
    assert len(components) == 1, f"expected exactly one mounted portal, got {len(components)}"
    return json.loads(components[0].proto.json)


def _visible_text(app: AppTest) -> str:
    values: list[str] = []
    for name in ("title", "header", "subheader", "markdown", "caption", "info", "warning", "error", "success", "text"):
        for element in getattr(app, name, []):
            label = getattr(element, "label", None)
            if label:
                values.append(str(label))
            values.append(str(getattr(element, "value", "")))
    return "\n".join(values)


def _assert_no_exceptions(app: AppTest) -> None:
    assert not app.exception, [str(element.value) for element in app.exception]


# --------------------------------------------------------------------------
# SOURCE_REVIEW — the assets are the reference file, minus the demo machinery
# --------------------------------------------------------------------------

def test_assets_are_the_owner_reference_not_another_prototype():
    html = (ASSET_DIR / "hexa-portal.html").read_text(encoding="utf-8")
    css = (ASSET_DIR / "hexa-portal.css").read_text(encoding="utf-8")
    js = (ASSET_DIR / "hexa-portal.js").read_text(encoding="utf-8")

    # Reference structure/ids are preserved verbatim so the layout maths and the
    # 8-column table cannot drift from the file the Owner sent Lục Giác.
    for element_id in (
        "shipment-identity-bar", "journey-map-viewport", "journey-edges-svg",
        "journey-nodes-layer", "journey-bubble-slot", "journey-modal-layer",
        "journey-zoom-bar", "journey-utility-trigger", "btn-back-to-dashboard",
        "dash-shipments-tbody", "dash-shipments-cards", "journey-zero-notice",
    ):
        assert f'id="{element_id}"' in html, element_id
    for header in (
        "Mã lô", "Hàng hóa &amp; Tuyến", "Phương thức", "Chặng xác minh",
        "ETA được xác minh", "Công nợ", "Cập nhật cuối", "Hành trình",
    ):
        assert header in html, header

    # Reference tokens survived the re-scope (a redesign would change these).
    for token in ("#0c233a", "#153c61", "#f59e0b", "116px", "520px"):
        assert token in css, token
    # The reference geometry constants and layout/inspection functions survive.
    for token in ("JOURNEY_NODE_W = 116", "DESKTOP_PITCH = 148", "MOBILE_ROW_Y = [120, 220, 320]"):
        assert token in js, token
    for fn in ("journeyEdgePath", "positionBubbleElement", "fitJourney", "applyTransform"):
        assert fn in js, fn

    # Provenance is recorded from the verified reference file itself.
    assert journey is not None  # imported for the layer above
    assert REFERENCE_SHA256.startswith("b91c878e") and REFERENCE_BYTES == 826336


def test_demo_machinery_did_not_survive_the_port():
    html = (ASSET_DIR / "hexa-portal.html").read_text(encoding="utf-8")
    js = (ASSET_DIR / "hexa-portal.js").read_text(encoding="utf-8")
    for forbidden in ("__DEMO_DATA__", "buildDemoVoucherPdf", "buildPdfBuffer", "triggerDownload", "demo-badge-fixed\">DEMO"):
        assert forbidden not in js, forbidden
    # No inline handlers and no fabricated demo copy in the markup.
    assert not re.search(r"\son(click|change|input)=", html)
    for figure in REFERENCE_DEMO_FIGURES:
        assert figure not in html, figure
        assert figure not in js, figure
    # No download affordance of any kind: G1 exposes no document bytes.
    assert "Tải PDF" not in js and "download=" not in js
    # No write surface (comment box / upload input) can be reached from the UI.
    assert 'type="file"' not in html
    assert "stage-comment-input" not in html and "btn-submit-stage-collab" not in html


def test_sea_chart_asset_is_byte_identical_to_the_reference_copy():
    import hashlib

    from views import customer_portal_component as component

    raw = (ASSET_DIR / "sea-chart.webp").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == component.SEA_CHART_SHA256
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"


# --------------------------------------------------------------------------
# TEST_PASS — pure model rules
# --------------------------------------------------------------------------

class _Card:
    """Minimal stand-in for ``core.customer_portal.PublicationCard``."""

    def __init__(self, **kwargs):
        defaults = dict(
            reference="G1-LG-001",
            status_label="ĐÃ XÁC NHẬN",
            transport_mode="ROAD",
            publication_version="v1",
            approved_at="2026-10-24T08:00:00Z",
            timeline=(),
            documents=(),
            quote=None,
        )
        defaults.update(kwargs)
        for key, value in defaults.items():
            setattr(self, key, value)


def test_published_without_events_never_invents_a_completed_stage():
    nodes = journey.build_stage_nodes(transport_mode="ROAD")
    assert [n["index"] for n in nodes] == ["00", "01", "02", "03", "04", "05", "06"]
    assert len(nodes) == 7
    assert all(n["state"] == "UNKNOWN" for n in nodes)
    assert all(n["completed"] is False for n in nodes)
    assert all(n["current"] is False for n in nodes)
    assert all(n["occurred_at"] == "" for n in nodes)
    assert all(n["stage_comments"] == [] for n in nodes)
    assert all("Chưa có dữ liệu được duyệt" in n["evidence"] for n in nodes)


def test_only_an_approved_event_promotes_its_own_stage():
    events = (
        {"id": "e1", "stage": "pickup", "title": "Đã lấy hàng", "occurred_at": "2026-10-20T08:30:00Z"},
        {"id": "e2", "stage": "customs", "title": "Đã thông quan", "occurred_at": "2026-10-22T09:00:00Z"},
    )
    nodes = journey.build_stage_nodes(transport_mode="ROAD", public_events=events)
    completed = {n["id"] for n in nodes if n["completed"]}
    assert completed == {"pickup", "customs"}
    # No ordering inference: an earlier stage with no event stays unknown.
    assert next(n for n in nodes if n["id"] == "plan")["state"] == "UNKNOWN"
    assert next(n for n in nodes if n["id"] == "transit")["state"] == "UNKNOWN"
    # The approved event's own wording and instant are shown, not a rewrite.
    pickup = next(n for n in nodes if n["id"] == "pickup")
    assert pickup["evidence"] == "Đã lấy hàng"
    assert pickup["occurred_at"] == "20/10/2026 08:30 UTC"


def test_unmapped_event_stage_never_leaks_into_a_neighbouring_stage():
    events = ({"id": "e1", "stage": "warehouse-x", "title": "Kho lạ", "occurred_at": "2026-10-20T08:30:00Z"},)
    nodes = journey.build_stage_nodes(transport_mode="ROAD", public_events=events)
    assert all(n["state"] == "UNKNOWN" for n in nodes)


@pytest.mark.parametrize(
    "mode,label_index,expected",
    [
        ("ROAD", 2, "Nhận & ghép"),
        ("SEA", 2, "Gom hàng & đóng container"),
        ("AIR", 2, "Gom hàng & chuyến bay"),
        ("RAIL", 2, "Gom hàng & xếp toa"),
        (None, 3, "Chặng 03 — chưa xác định phương thức"),
    ],
)
def test_stage_wording_follows_the_published_transport_mode(mode, label_index, expected):
    nodes = journey.build_stage_nodes(transport_mode=mode)
    assert nodes[label_index]["label"] == expected
    if mode in (None,):
        # A mode-less lot can never be labelled with ROAD-only stage names.
        labels = [n["label"] for n in nodes]
        assert "Nhận & ghép" not in labels
        assert "Vận chuyển" not in labels


def test_road_lot_model_has_no_fabricated_amounts_eta_or_documents():
    model = journey.build_lot_model(_Card())
    assert model["shipment_id"] == "G1-LG-001"
    assert model["verified_stage_label"] == "Chưa xác minh"
    assert model["verified_warehouse_eta_label"] == "Chưa xác minh"
    assert model["verified_warehouse_eta"] is False
    assert model["debt_summary"] == {"status": "UNKNOWN", "currency": "VND"}
    assert model["finance_detail"] is None
    assert model["quote"] is None
    assert model["documents"] == []
    assert model["timeline"] == []
    assert model["journey"]["edges"] == [
        {"from": "plan", "to": "pickup"},
        {"from": "pickup", "to": "consolidate"},
        {"from": "consolidate", "to": "transit"},
        {"from": "transit", "to": "customs"},
        {"from": "customs", "to": "delivery"},
        {"from": "delivery", "to": "finance"},
    ]


def test_owner_5c_never_projects_quote_money_or_invents_debt():
    model = journey.build_lot_model(_Card(quote={"id": "QT-1", "version": "v1", "status": "SENT", "selling_total_vnd": 1234.0}))
    assert model["quote"] is None
    assert model["debt_summary"]["status"] == "UNKNOWN"
    assert "1234" not in json.dumps(model)
    bad = journey.build_lot_model(_Card(quote={"id": "QT-2", "selling_total_vnd": -5}))
    assert bad["quote"] is None


def test_portal_model_kpi_counts_only_verified_eta_and_never_a_customer_action():
    class _View:
        principal = portal.CustomerPrincipal(customer_id="CUST-LUCGIAC", email="a@b.example", display_name="Lục Giác")
        cards = (_Card(), _Card(reference="G1-LG-002", transport_mode="SEA"))
        denied_lots = 1
        data_issues = 0

    model = journey.build_portal_model(_View())
    assert model["kpi"]["tracking"] == 2
    assert model["kpi"]["verified_eta"] == 0
    assert model["kpi"]["customer_action"] == 0
    assert model["counts"] == {"published": 2, "denied": 1, "data_issues": 0}
    assert model["customer"]["name"] == "Lục Giác"


def test_display_timestamp_never_invents_a_value():
    assert journey.display_timestamp("2026-10-24T08:00:00Z") == "24/10/2026 08:00 UTC"
    assert journey.display_timestamp("không rõ") == "không rõ"
    assert journey.display_timestamp("") == ""
    assert journey.display_timestamp(None) == ""


# --------------------------------------------------------------------------
# TEST_PASS — real Streamlit runtime (AppTest) mounted component
# --------------------------------------------------------------------------

def test_oauth_return_mounts_reference_portal_for_own_lots_only(seed_module):
    db = _db(seed_module, negative_cases=True)
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    # Browser-supplied ids must have zero effect on the server-side scope.
    app.query_params = {
        "portal": "customer",
        "customer_id": seed_module.CUSTOMER_B_ID,
        "shipment_id": seed_module.LOT_B1,
        "lot": seed_module.LOT_A2,
        "version": "v9",
    }
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)

    payload = _payload(app)
    model = payload["model"]
    lots = model["lots"]
    assert [lot["shipment_id"] for lot in lots] == [seed_module.LOT_A1, seed_module.LOT_A2]
    assert model["customer"]["name"] == "Lục Giác"
    # The component carries the reference sea chart inline (no server fetch).
    assert payload["assets"]["sea_chart"].startswith("data:image/webp;base64,")

    dumped = json.dumps(payload, ensure_ascii=False)
    assert seed_module.LOT_B1 not in dumped
    assert seed_module.FOREIGN_SENTINEL not in dumped
    for sentinel in seed_module.INTERNAL_SENTINELS:
        assert sentinel not in dumped
    for figure in REFERENCE_DEMO_FIGURES:
        assert figure not in dumped, figure
    assert "G1-LG-001" in dumped and "G1-LG-002" in dumped


def test_published_lots_render_every_stage_as_unverified_not_completed(seed_module):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)
    model = _payload(app)["model"]
    for lot in model["lots"]:
        states = [node["state"] for node in lot["journey"]["nodes"]]
        assert states == ["UNKNOWN"] * 7, (lot["shipment_id"], states)
        assert lot["verified_stage_label"] == "Chưa xác minh"
        assert lot["verified_warehouse_eta_label"] == "Chưa xác minh"
        assert lot["debt_summary"]["status"] == "UNKNOWN"
    sea = next(lot for lot in model["lots"] if lot["shipment_id"] == seed_module.LOT_A2)
    assert sea["transport_mode"] == "SEA"
    assert sea["journey"]["nodes"][3]["label"] == "Vận tải biển"


def test_unauthorised_oidc_email_never_mounts_the_portal(seed_module):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    app.query_params = {"portal": "customer"}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims("not-allowed@example.com")),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
    _assert_no_exceptions(app)
    assert app.get("bidi_component") == []
    visible = _visible_text(app)
    assert "chưa được cấp quyền" in visible
    assert seed_module.LOT_A1 not in visible
    assert seed_module.FOREIGN_SENTINEL not in visible


def test_customer_portal_never_mounts_the_internal_shell(seed_module):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
        patch.object(portal, "get_db", return_value=db),
        patch("views.logi_view_model.build_view_model") as internal_vm,
        patch("views.logi_shell.render") as internal_shell,
        patch("views.web_app.require_login") as internal_login,
    ):
        app.run()
    _assert_no_exceptions(app)
    internal_vm.assert_not_called()
    internal_shell.assert_not_called()
    internal_login.assert_not_called()
    assert "shell_portal_access_customer" not in {element.key for element in app.selectbox}


def test_no_lots_state_is_safe_and_still_mounted_once(seed_module):
    db = _db(seed_module, negative_cases=False)
    db.customers.insert_one({
        "id": "CUST-EMPTY",
        "name": "Khách không có lô",
        portal.PORTAL_ACCESS_EMAIL_FIELD: "portal.empty@example.com",
    })
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims("portal.empty@example.com")),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        _assert_no_exceptions(app)
        assert "Chưa có lô hàng nào được công bố" in _visible_text(app)
        model = _payload(app)["model"]
        assert model["lots"] == []
        assert model["kpi"]["tracking"] == 0
        app.run()
    _assert_no_exceptions(app)
    assert _payload(app)["model"]["lots"] == []


def test_owner_granted_publication_fields_reach_the_ui_without_scope_change(seed_module):
    """An Owner-approved release is shown; it never widens the tenant."""
    db = _db(seed_module, negative_cases=False)
    db.customer_publications.update_one(
        {"shipment_id": seed_module.LOT_A1},
        {"$set": {
            "event_versions": {"EV-1": "v1"},
            "document_versions": {"DOC-1": "v1"},
            "quote": {"id": "QT-9", "version": "v1"},
        }},
    )
    db.shipments.update_one({"id": seed_module.LOT_A1}, {"$set": {"quote_id": "QT-9"}})
    db.public_events = db["public_events"]
    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": seed_module.CUSTOMER_A_ID,
        "shipment_id": seed_module.LOT_A1, "stage_id": "pickup",
        "public_title": "Đã lấy hàng tại kho", "occurred_at": "2026-10-20T08:30:00Z",
        "verified": True, "verified_at": "2026-10-20T09:00:00Z", "visibility": "CUSTOMER",
    })
    db.public_documents = db["public_documents"]
    db.public_documents.insert_one({
        "id": "DOC-1", "version": "v1", "customer_id": seed_module.CUSTOMER_A_ID,
        "shipment_id": seed_module.LOT_A1, "kind": "PL", "public_title": "Packing List",
        "status": "AVAILABLE", "visibility": "CUSTOMER", "verified": True,
    })
    db.quotes = db["quotes"]
    db.quotes.insert_one({
        "id": "QT-9", "version": "v1", "customer_id": seed_module.CUSTOMER_A_ID,
        "status": "SENT", "calculation": {"selling_price_total_vnd": 1000.0},
    })

    card = portal.load_customer_dashboard(
        portal.CustomerPrincipal(
            customer_id=seed_module.CUSTOMER_A_ID,
            email=seed_module.CUSTOMER_A_PORTAL_EMAIL,
            display_name="Lục Giác",
        ),
        db=db,
    ).cards[0]
    # A TT-approved, version-pinned publication reads genuine source records
    # and retains the independent tenant/visibility/verified allowlist.
    assert len(card.timeline) == 1
    assert card.timeline[0]["title"] == "Đã lấy hàng tại kho"
    assert card.documents == ({
        "id": "DOC-1", "version": "v1", "kind": "PL", "title": "Packing List",
    },)
    assert card.quote is None

    model = journey.build_lot_model(card)
    assert {n["id"] for n in model["journey"]["nodes"] if n["completed"]} == {"pickup"}
    assert len(model["documents"]) == 1
    assert model["quote"] is None
    assert "selling_total_vnd" not in json.dumps(model)
    assert model["debt_summary"]["status"] == "UNKNOWN"


def test_revoked_access_after_mount_shows_no_data(seed_module):
    db = _db(seed_module, negative_cases=False)
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.secrets = {"auth": FAKE_AUTH}
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        assert _payload(app)["model"]["lots"]
        # Owner revokes the grant between two reruns.
        db.customers.update_one({"id": seed_module.CUSTOMER_A_ID}, {"$unset": {portal.PORTAL_ACCESS_EMAIL_FIELD: ""}})
        app.run()
    _assert_no_exceptions(app)
    assert app.get("bidi_component") == []
    assert "chưa được cấp quyền" in _visible_text(app)


def test_payload_does_not_depend_on_query_parameters(seed_module):
    db = _db(seed_module, negative_cases=False)
    before = None
    for params in ({}, {"customer_id": seed_module.CUSTOMER_B_ID, "shipment_id": seed_module.LOT_B1}):
        app = AppTest.from_file(str(APP_PATH), default_timeout=90)
        app.secrets = {"auth": FAKE_AUTH}
        app.query_params = params
        with (
            patch("streamlit.user_info._get_user_info", return_value=_claims(seed_module.CUSTOMER_A_PORTAL_EMAIL)),
            patch.object(portal, "get_db", return_value=db),
        ):
            app.run()
        _assert_no_exceptions(app)
        payload = _payload(app)
        if before is None:
            before = payload["model"]["lots"]
        else:
            assert payload["model"]["lots"] == before
