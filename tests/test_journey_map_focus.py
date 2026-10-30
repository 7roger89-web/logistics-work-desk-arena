"""LOGI — Journey Map node → đúng pane trao đổi/chứng từ đang có.

Isolated: mongomock + the fake byte store pattern already used by
``tests/test_journey_notes.py``. No Cloud, no Drive, no production write.

What this file actually proves (and nothing more):

* one node click produces ONE read-only intent, resolved against the caller's
  OWN server-built projection; a foreign lot, an unknown stage or a replayed
  trigger opens nothing;
* the browser's ``customer_id`` never decides the tenant — the server-proven
  principal/projection does;
* the SAME existing pane opens on the clicked stage, with INTERNAL notes still
  hidden from the customer;
* the shell dispatcher keeps the one-shot ``seq`` contract and writes no
  business data.
"""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import types
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest

from core import journey_notes as notes
from core import shipment_journey as journey_catalog
from views import journey_focus

_ROOT_PATH = Path(__file__).resolve().parents[1]

CUSTOMER_A = "CUST-LUCGIAC"
CUSTOMER_B = "CUST-MINHDUC"
LOT_A = "G1-LG-001"
LOT_B = "G1-MD-001"

SALE = {"username": "sale.thanh", "role": "sale", "full_name": "Trần Thanh"}

CUSTOMER_NOTE = "Đã nhận chứng từ thông quan bản khách xem."
INTERNAL_NOTE = "Giá vốn nội bộ 12.400.000 — không công bố."
OTHER_LOT_NOTE = "Trao đổi của lô thứ hai."

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8Dw"
    "HwAFAAH/q842iQAAAABJRU5ErkJggg=="
)


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

def _note(note_id, lot, stage, body, visibility, customer=CUSTOMER_A):
    return {
        "id": note_id,
        "kind": "journey_note",
        "customer_id": customer,
        "shipment_id": lot,
        "stage_id": stage,
        "body": body,
        "visibility": visibility,
        "author_kind": "user",
        "author_name": "sale.thanh",
        "author_role": "sale",
        "created_at": "2026-10-30T08:00:00+00:00",
        "attachments": [],
        "is_deleted": False,
    }


@pytest.fixture()
def db():
    database = mongomock.MongoClient().db
    database.customers.insert_many([
        {"id": CUSTOMER_A, "name": "Lục Giác", "is_deleted": False},
        {"id": CUSTOMER_B, "name": "Minh Đức", "is_deleted": False},
    ])
    database.shipments.insert_many([
        {"id": LOT_A, "customer_id": CUSTOMER_A, "is_deleted": False},
        {"id": LOT_B, "customer_id": CUSTOMER_B, "is_deleted": False},
    ])
    database.quick_notes.insert_many([
        _note("jn-a-cust", LOT_A, "customs", CUSTOMER_NOTE, "CUSTOMER"),
        _note("jn-a-int", LOT_A, "customs", INTERNAL_NOTE, "INTERNAL"),
        _note("jn-b", LOT_B, "customs", OTHER_LOT_NOTE, "CUSTOMER", customer=CUSTOMER_B),
    ])
    return database


def _run(script: str, database) -> AppTest:
    app = AppTest.from_string(script, default_timeout=120)
    with (
        patch("core.database.get_db", return_value=database),
        patch("core.journey_notes._resolve_db", return_value=database),
    ):
        app.run()
    assert not app.exception, [str(item.value) for item in app.exception]
    return app


def _visible(app: AppTest) -> str:
    chunks = []
    for name in ("markdown", "caption", "text", "success", "error", "warning", "info"):
        for element in getattr(app, name, []):
            chunks.append(str(getattr(element, "value", "")))
            label = getattr(element, "label", None)
            if label:
                chunks.append(str(label))
    return "\n".join(chunks)


# --------------------------------------------------------------------------- #
# pure intent rules
# --------------------------------------------------------------------------- #

def test_only_a_canonical_stage_and_a_real_lot_make_a_valid_intent():
    assert journey_focus.normalize({"shipment_id": LOT_A, "stage_id": "customs"}) == {
        "shipment_id": LOT_A, "stage_id": "customs"}
    # Case-folded canonical id is accepted; junk is refused.
    assert journey_focus.normalize({"shipment_id": LOT_A, "stage_id": " CUSTOMS "}) == {
        "shipment_id": LOT_A, "stage_id": "customs"}
    assert journey_focus.normalize({"shipment_id": LOT_A, "stage_id": "warehouse-x"}) is None
    assert journey_focus.normalize({"shipment_id": "", "stage_id": "customs"}) is None
    assert journey_focus.normalize({"shipment_id": LOT_A}) is None
    assert journey_focus.normalize("journey_focus") is None
    assert journey_focus.normalize(None) is None


def test_a_replayed_trigger_never_reopens_a_closed_pane():
    session: dict = {}
    intent = {"seq": 7, "shipment_id": LOT_A, "stage_id": "customs"}
    assert journey_focus.capture(session, intent, scope={"customer_id": CUSTOMER_A}) is True
    assert journey_focus.current(session)["stage_id"] == "customs"
    journey_focus.clear(session)
    assert journey_focus.current(session) is None
    # Same seq again: the one-shot contract keeps the pane closed.
    assert journey_focus.capture(session, intent, scope={"customer_id": CUSTOMER_A}) is False
    assert journey_focus.current(session) is None
    # A malformed intent stores nothing at all.
    assert journey_focus.capture(session, {"seq": 9, "stage_id": "nope", "shipment_id": LOT_A}) is False
    assert journey_focus.current(session) is None


class _Card:
    def __init__(self, reference: str) -> None:
        self.reference = reference


def test_customer_intent_only_resolves_inside_the_customers_own_cards():
    request = {"shipment_id": LOT_A, "stage_id": "customs", "customer_id": CUSTOMER_A}
    cards = [_Card(LOT_A)]
    assert journey_focus.for_customer(request, CUSTOMER_A, cards) == {
        "shipment_id": LOT_A, "stage_id": "customs"}
    # A lot of another customer is not in this principal's cards.
    assert journey_focus.for_customer({**request, "shipment_id": LOT_B}, CUSTOMER_A, cards) is None
    # A scope that claims another customer is refused even if the lot were listed.
    assert journey_focus.for_customer(request, CUSTOMER_B, [_Card(LOT_A)]) is None
    # No principal, no pane.
    assert journey_focus.for_customer(request, "", [_Card(LOT_A)]) is None


def test_staff_intent_takes_the_customer_from_the_server_projection():
    shipments = [
        {"id": LOT_A, "customerId": CUSTOMER_A, "customer": "Lục Giác"},
        {"id": LOT_B, "customerId": CUSTOMER_B, "customer": "Minh Đức"},
    ]
    forged = {"shipment_id": LOT_A, "stage_id": "delivery", "customer_id": CUSTOMER_B}
    resolved = journey_focus.for_staff(forged, "sale.thanh", shipments)
    assert resolved == {"shipment_id": LOT_A, "stage_id": "delivery", "customer_id": CUSTOMER_A}
    # Unknown lot / stage / actor fails closed.
    assert journey_focus.for_staff({"shipment_id": "LOT-X", "stage_id": "delivery"},
                                   "sale.thanh", shipments) is None
    assert journey_focus.for_staff({"shipment_id": LOT_A, "stage_id": "not-a-stage"},
                                   "sale.thanh", shipments) is None
    assert journey_focus.for_staff(forged, "", shipments) is None
    # A projection row with no customer link can never open a note pane.
    assert journey_focus.for_staff({"shipment_id": LOT_A, "stage_id": "delivery"},
                                   "sale.thanh", [{"id": LOT_A, "customerId": ""}]) is None


# --------------------------------------------------------------------------- #
# internal Journey Map node ids → the seven existing discussion stages
# --------------------------------------------------------------------------- #

FIXTURE_188 = _ROOT_PATH / "tests" / "component" / "fixtures" / "view_model_journey_fresh_188.json"
FIXTURE_LOT = "LO-0307"
INTERNAL_TRANSIT_NOTE = "Chặng chính: hãng tàu đổi ETD — nội bộ theo dõi."
CUSTOMER_TRANSIT_NOTE = "Khách đã xác nhận chấp nhận ETD mới."
OTHER_STAGE_NOTE = "GHI CHÚ CỦA CÔNG ĐOẠN KHÁC — không được lẫn."


def _fixture_row(shipment_id: str = FIXTURE_LOT) -> dict:
    data = json.loads(FIXTURE_188.read_text(encoding="utf-8"))
    return next(row for row in data["before"]["shipments"] if row["id"] == shipment_id)


def test_every_real_internal_node_maps_to_one_of_the_seven_stages():
    """The map is explicit AND complete for the ids the shell really renders."""
    mapped = journey_focus.STAFF_NODE_STAGES
    missing = sorted(node for node in journey_catalog.JOURNEY_STAGE_IDS
                     if node.lower() not in mapped)
    assert missing == [], f"internal journey node ids without a discussion stage: {missing}"
    assert set(notes.STAGE_IDS) <= set(mapped)
    assert all(stage in notes.STAGE_IDS for stage in mapped.values())
    # The eleven base nodes build_journey() can emit, all present.
    assert {"booking", "pickup", "customs-export", "si-vgm", "gate-in", "etd",
            "on-board", "transit", "arrival", "customs-import", "delivery"} <= set(mapped)


@pytest.mark.parametrize(
    "node_id,expected",
    [
        # ROAD fixture node the shell really renders.
        ("MAIN_CARRIAGE", "transit"),
        # SEA nodes (booking → transit).
        ("booking", "plan"),
        ("si-vgm", "consolidate"),
        ("gate-in", "consolidate"),
        ("etd", "transit"),
        ("on-board", "transit"),
        ("arrival", "transit"),
        # Export/import customs.
        ("customs-export", "customs"),
        ("customs-import", "customs"),
        ("customs", "customs"),
        # Delivery.
        ("delivery", "delivery"),
        ("final_delivery", "delivery"),
        # Service-scope nodes that can become journey nodes.
        ("ORIGIN_TERMINAL_OR_BORDER", "consolidate"),
        ("CROSS_BORDER", "transit"),
        ("sea_documents", "consolidate"),
        ("insurance_evidence", "finance"),
        # The canonical seven still work unchanged.
        ("plan", "plan"),
        ("pickup", "pickup"),
        ("finance", "finance"),
    ],
)
def test_each_internal_node_lands_in_its_documented_stage(node_id, expected):
    session: dict = {}
    assert journey_focus.capture(
        session, {"seq": 1, "shipment_id": FIXTURE_LOT, "stage_id": node_id},
        node_stages=journey_focus.STAFF_NODE_STAGES,
    ) is True
    resolved = journey_focus.for_staff(
        journey_focus.current(session), "sale.thanh",
        [{"id": FIXTURE_LOT, "customerId": "CUST-DUCLONG"}],
    )
    assert resolved["stage_id"] == expected
    assert resolved["node_id"] == node_id


@pytest.mark.parametrize(
    "node_id", ["warehouse-x", "module:inst:step-1", "", "stage-99", "MAIN_CARRIAGE_X"],
)
def test_an_unmapped_internal_node_still_fails_closed(node_id):
    session: dict = {}
    assert journey_focus.capture(
        session, {"seq": 1, "shipment_id": FIXTURE_LOT, "stage_id": node_id},
        node_stages=journey_focus.STAFF_NODE_STAGES,
    ) is False
    assert journey_focus.current(session) is None
    assert journey_focus.for_staff(
        {"shipment_id": FIXTURE_LOT, "stage_id": node_id, "node_id": node_id},
        "sale.thanh", [{"id": FIXTURE_LOT, "customerId": "CUST-DUCLONG"}],
    ) is None


def test_the_customer_contract_never_accepts_internal_node_ids():
    """The customer portal keeps its own seven canonical stages only."""
    request = {"shipment_id": LOT_A, "stage_id": "MAIN_CARRIAGE", "customer_id": CUSTOMER_A}
    assert journey_focus.for_customer(request, CUSTOMER_A, [_Card(LOT_A)]) is None
    # …and a customer intent of another tenant still fails closed.
    assert journey_focus.for_customer(
        {"shipment_id": LOT_A, "stage_id": "transit", "customer_id": CUSTOMER_B},
        CUSTOMER_A, [_Card(LOT_A)],
    ) is None


def test_a_stored_internal_focus_does_not_survive_a_different_operator():
    session: dict = {}
    journey_focus.capture(
        session, {"seq": 1, "shipment_id": FIXTURE_LOT, "stage_id": "MAIN_CARRIAGE"},
        scope={"username": "sale.thanh"}, node_stages=journey_focus.STAFF_NODE_STAGES,
    )
    row = {"id": FIXTURE_LOT, "customerId": "CUST-DUCLONG"}
    assert journey_focus.for_staff(journey_focus.current(session), "sale.thanh", [row]) is not None
    assert journey_focus.for_staff(journey_focus.current(session), "nguoi.khac", [row]) is None


# --------------------------------------------------------------------------- #
# the shell dispatcher keeps the one-shot, read-only contract
# --------------------------------------------------------------------------- #

def test_shell_dispatcher_records_one_intent_and_writes_no_business_data(db):
    script = (
        "import streamlit as st\n"
        "from views import logi_view_model as model\n"
        "st.session_state['current_user'] = {'username': 'sale.thanh', 'role': 'sale'}\n"
        "result = {'journey_focus': {'seq': 4, 'event': 'journey_focus',\n"
        "          'payload': {'shipment_id': 'G1-LG-001', 'stage_id': 'customs'}}}\n"
        "first = model.consume_journey_focus_triggers({'seq': 0}, result)\n"
        "second = model.consume_journey_focus_triggers({'seq': 4}, result)\n"
        "st.session_state['first'] = first\n"
        "st.session_state['second'] = second\n"
        "st.session_state['stored'] = dict(st.session_state.get('logi_journey_focus') or {})\n"
        "st.session_state['documents'] = sorted(name for name, _ in [])\n"
    )
    app = _run(script, db)
    first = app.session_state["first"]
    assert first and first[0]["ok"] is True
    assert first[0]["readback"] == {"shipmentId": LOT_A, "stageId": "customs"}
    assert app.session_state["second"] == []
    stored = app.session_state["stored"]
    assert stored["shipment_id"] == LOT_A and stored["stage_id"] == "customs"
    assert stored["username"] == "sale.thanh"
    # Read-only: the lot truth is untouched by the intent.
    shipment = db.shipments.find_one({"id": LOT_A})
    assert shipment["customer_id"] == CUSTOMER_A


def test_shell_focus_pane_is_resolved_against_the_callers_own_lots(db):
    script = (
        "import streamlit as st\n"
        "from views import logi_view_model as model\n"
        "st.session_state['current_user'] = {'username': 'sale.thanh', 'role': 'sale'}\n"
        "model.consume_journey_focus_triggers({'seq': 0}, {'journey_focus': {\n"
        "    'seq': 1, 'payload': {'shipment_id': 'G1-MD-001', 'stage_id': 'pickup'}}})\n"
        "own = [{'id': 'G1-LG-001', 'customerId': 'CUST-LUCGIAC'}]\n"
        "st.session_state['resolved'] = model.journey_focus_pane(\n"
        "    {'username': 'sale.thanh'}, own)\n"
        "other = model.journey_focus_pane({'username': 'khac.nguoi'}, own)\n"
        "st.session_state['foreign'] = other\n"
    )
    app = _run(script, db)
    # The clicked lot is not in this operator's projection -> nothing opens.
    assert app.session_state["resolved"] is None
    assert app.session_state["foreign"] is None


# --------------------------------------------------------------------------- #
# the EXISTING pane opens on the clicked stage (customer side)
# --------------------------------------------------------------------------- #

def test_customer_pane_opens_on_the_clicked_stage_and_hides_internal_notes(db):
    script = (
        "from views.journey_discussion import render_customer_discussion\n"
        "class Card:\n"
        "    def __init__(self, ref): self.reference = ref\n"
        "class Principal:\n"
        "    customer_id = 'CUST-LUCGIAC'\n"
        "    display_name = 'Lục Giác'\n"
        "render_customer_discussion(\n"
        "    [Card('G1-LG-001'), Card('G1-MD-001')], Principal(),\n"
        "    focus={'shipment_id': 'G1-LG-001', 'stage_id': 'customs'})\n"
    )
    app = _run(script, db)
    shown = _visible(app)
    assert "Đang mở từ Journey Map" in shown
    assert "Thông quan" in shown
    # Only the focused lot is on screen.
    assert OTHER_LOT_NOTE not in shown
    # The customer still never sees INTERNAL content.
    assert INTERNAL_NOTE not in shown
    assert CUSTOMER_NOTE in shown
    selectors = list(app.selectbox)
    assert len(selectors) == 1
    assert selectors[0].value == "04 · Thông quan"
    # The ONE pane is already expanded by the node click.
    assert [e.label for e in app.expander] == ["💬 Trao đổi công đoạn · lô G1-LG-001"]


def test_foreign_or_unknown_focus_never_renders_a_customer_pane(db):
    script = (
        "from views.journey_discussion import render_customer_discussion\n"
        "class Card:\n"
        "    def __init__(self, ref): self.reference = ref\n"
        "class Principal:\n"
        "    customer_id = 'CUST-LUCGIAC'\n"
        "    display_name = 'Lục Giác'\n"
        "render_customer_discussion([Card('G1-LG-001')], Principal(),\n"
        "    focus={'shipment_id': 'G1-MD-001', 'stage_id': 'customs'})\n"
    )
    app = _run(script, db)
    assert not list(app.selectbox)
    shown = _visible(app)
    assert OTHER_LOT_NOTE not in shown and INTERNAL_NOTE not in shown


def test_customer_pane_without_focus_keeps_its_old_collapsed_behaviour(db):
    script = (
        "from views.journey_discussion import render_customer_discussion\n"
        "class Card:\n"
        "    def __init__(self, ref): self.reference = ref\n"
        "class Principal:\n"
        "    customer_id = 'CUST-LUCGIAC'\n"
        "    display_name = 'Lục Giác'\n"
        "render_customer_discussion([Card('G1-LG-001')], Principal())\n"
    )
    app = _run(script, db)
    assert "Đang mở từ Journey Map" not in _visible(app)
    assert [e.label for e in app.expander] == ["💬 Trao đổi công đoạn · lô G1-LG-001"]
    assert list(app.selectbox)[0].value == "00 · Kế hoạch"


# --------------------------------------------------------------------------- #
# the EXISTING pane opens on the clicked stage (staff side)
# --------------------------------------------------------------------------- #

def test_internal_pane_opens_on_the_clicked_stage_with_internal_notes(db):
    script = (
        "from views.journey_discussion import render_internal_discussion\n"
        "render_internal_discussion('G1-LG-001', 'CUST-LUCGIAC',\n"
        "    {'username': 'sale.thanh', 'role': 'sale'}, focus_stage='customs')\n"
    )
    app = _run(script, db)
    shown = _visible(app)
    assert "Đang mở từ Journey Map" in shown and "Thông quan" in shown
    assert INTERNAL_NOTE in shown and CUSTOMER_NOTE in shown
    assert list(app.selectbox)[0].value == "04 · Thông quan"
    assert list(app.expander)[0].label == (
        "💬 Trao đổi / Chứng từ · lô G1-LG-001 · công đoạn Thông quan"
    )


def test_internal_pane_without_focus_stays_collapsed_on_the_first_stage(db):
    script = (
        "from views.journey_discussion import render_internal_discussion\n"
        "render_internal_discussion('G1-LG-001', 'CUST-LUCGIAC',\n"
        "    {'username': 'sale.thanh', 'role': 'sale'})\n"
    )
    app = _run(script, db)
    assert "Đang mở từ Journey Map" not in _visible(app)
    assert list(app.selectbox)[0].value == "00 · Kế hoạch"


def test_unknown_focus_stage_falls_back_instead_of_crashing(db):
    script = (
        "from views.journey_discussion import render_internal_discussion\n"
        "render_internal_discussion('G1-LG-001', 'CUST-LUCGIAC',\n"
        "    {'username': 'sale.thanh', 'role': 'sale'}, focus_stage='warehouse-x')\n"
    )
    app = _run(script, db)
    assert list(app.selectbox)[0].value == "00 · Kế hoạch"
    assert "Đang mở từ Journey Map" not in _visible(app)


def test_send_then_reload_keeps_the_thread_scoped_to_lot_and_stage(db):
    """Gửi → lưu → reload: the focused pane shows the saved note immediately."""
    script = (
        "from views.journey_discussion import render_internal_discussion\n"
        "render_internal_discussion('G1-LG-001', 'CUST-LUCGIAC',\n"
        "    {'username': 'sale.thanh', 'role': 'sale'}, focus_stage='customs')\n"
    )
    app = _run(script, db)
    area = list(app.text_area)[0]
    area.set_value("Bổ sung tờ khai hải quan bản đã ký")
    senders = [element for element in app.button if element.label == "Gửi"]
    assert senders
    with (
        patch("core.database.get_db", return_value=db),
        patch("core.journey_notes._resolve_db", return_value=db),
    ):
        senders[0].click()
        app.run()
        assert not app.exception, [str(item.value) for item in app.exception]
        area = list(app.text_area)[0]
        assert area.value in ("", None)
        app.run()
    rows = list(db.quick_notes.find({"kind": "journey_note", "shipment_id": LOT_A,
                                     "stage_id": "customs"}))
    bodies = {row["body"] for row in rows}
    assert "Bổ sung tờ khai hải quan bản đã ký" in bodies
    # Every saved row still carries the exact lot + stage scope.
    assert all(row["shipment_id"] == LOT_A and row["stage_id"] == "customs" for row in rows)
    # Nothing was written to the other customer's lot.
    assert db.quick_notes.count_documents({"shipment_id": LOT_B}) == 1


# --------------------------------------------------------------------------- #
# the customer dashboard wires the intent to the pane BEFORE the map
# --------------------------------------------------------------------------- #

_DASH_SCRIPT = (
    "import types\n"
    "import streamlit as st\n"
    "from views import customer_dashboard as dash\n"
    "principal = types.SimpleNamespace(customer_id='CUST-LUCGIAC',\n"
    "    display_name='Lục Giác', email='portal.lucgiac@example.com')\n"
    "st.session_state['logi_journey_focus'] = st.session_state.get('__focus__')\n"
    "dash.render_customer_dashboard(principal)\n"
)


def _dash_app(focus, database) -> AppTest:
    """Run the REAL dashboard wiring with only the DB and portal read stubbed.

    The stubs are applied from the test process (never from inside the script)
    so no module attribute is left mutated for the rest of the suite.
    """
    from views import customer_dashboard as dash

    view = types.SimpleNamespace(
        cards=[_Card(LOT_A), _Card(LOT_B)],
        principal=types.SimpleNamespace(customer_id=CUSTOMER_A, display_name="Lục Giác",
                                        email="portal.lucgiac@example.com"),
        no_lots=False, denied_lots=[], data_issues=[],
    )
    app = AppTest.from_string(_DASH_SCRIPT, default_timeout=120)
    app.session_state["__focus__"] = focus
    with (
        patch.object(dash.portal, "load_customer_dashboard", return_value=view),
        patch.object(dash, "build_model", lambda view: {}),
        patch.object(dash.component, "render", lambda model, **kw: None),
        patch("core.database.get_db", return_value=database),
        patch("core.journey_notes._resolve_db", return_value=database),
    ):
        app.run()
    assert not app.exception, [str(item.value) for item in app.exception]
    return app


def test_dashboard_opens_the_existing_pane_for_the_clicked_node(db):
    app = _dash_app(
        {"shipment_id": LOT_A, "stage_id": "customs", "customer_id": CUSTOMER_A}, db,
    )
    shown = _visible(app)
    assert "Đang mở từ Journey Map" in shown
    assert [e.label for e in app.expander] == ["💬 Trao đổi công đoạn · lô G1-LG-001"]
    assert list(app.selectbox)[0].value == "04 · Thông quan"
    assert INTERNAL_NOTE not in shown and CUSTOMER_NOTE in shown


def test_dashboard_drops_a_focus_belonging_to_another_customer(db):
    app = _dash_app(
        # The lot exists, but the stored intent was opened for another customer:
        # after a customer switch nothing of that session may survive.
        {"shipment_id": LOT_A, "stage_id": "customs", "customer_id": CUSTOMER_B}, db,
    )
    shown = _visible(app)
    assert "Đang mở từ Journey Map" not in shown
    assert INTERNAL_NOTE not in shown and CUSTOMER_NOTE not in shown
    # The ordinary (unfocused) pane list is rendered instead.
    assert [e.label for e in app.expander] == [
        "💬 Trao đổi công đoạn · lô G1-LG-001",
        "💬 Trao đổi công đoạn · lô G1-MD-001",
    ]


# --------------------------------------------------------------------------- #
# the REAL app.py path (views.web_app → logi_shell → existing pane)
# --------------------------------------------------------------------------- #

_APP_PATH = _ROOT_PATH / "app.py"


def _run_app(database, focus, *, permission: bool = True) -> AppTest:
    from unittest.mock import patch as _patch

    app = AppTest.from_file(str(_APP_PATH), default_timeout=180)
    app.session_state["logi_journey_focus"] = focus
    with (
        _patch("core.auth.AUTH_REQUIRED", False),
        _patch("core.auth.has_permission", lambda *a, **k: permission),
        _patch("core.database.get_db", return_value=database),
        _patch("core.journey_notes._resolve_db", return_value=database),
        _patch("views.logi_sandbox.ensure_backend", return_value=None),
    ):
        app.run()
    return app


def test_real_app_opens_the_existing_internal_pane_above_the_shell(db):
    app = _run_app(
        db, {"shipment_id": LOT_A, "stage_id": "customs", "username": "local-admin"},
    )
    assert not app.exception, [str(item.value) for item in app.exception]
    labels = [element.label for element in app.expander]
    assert labels[0] == "💬 Trao đổi / Chứng từ · lô G1-LG-001 · công đoạn Thông quan"
    assert list(app.selectbox)[0].value == "04 · Thông quan"
    assert "Đang mở từ Journey Map" in _visible(app)
    assert INTERNAL_NOTE in _visible(app)


def test_real_app_never_opens_a_pane_outside_the_operators_projection(db):
    app = _run_app(
        db, {"shipment_id": "LOT-NOT-VISIBLE", "stage_id": "customs", "username": "local-admin"},
    )
    assert not app.exception, [str(item.value) for item in app.exception]
    assert not [label for label in (e.label for e in app.expander) if "Trao đổi / Chứng từ ·" in label]


def test_real_app_denies_the_pane_without_the_existing_write_permission(db):
    app = _run_app(
        db, {"shipment_id": LOT_A, "stage_id": "customs", "username": "local-admin"},
        permission=False,
    )
    assert not app.exception, [str(item.value) for item in app.exception]
    assert not [label for label in (e.label for e in app.expander) if "Trao đổi / Chứng từ ·" in label]


def test_real_app_opens_the_transit_pane_for_the_fixture_node(fixture_db):
    """Same mapping, but through the REAL app entrypoint the operator loads."""
    app = _run_app(
        fixture_db,
        {"shipment_id": "LO-0307", "stage_id": "transit", "node_id": "MAIN_CARRIAGE",
         "username": "local-admin"},
    )
    assert not app.exception, [str(item.value) for item in app.exception]
    labels = [element.label for element in app.expander]
    assert labels[0] == "💬 Trao đổi / Chứng từ · lô LO-0307 · công đoạn Vận chuyển"
    assert list(app.selectbox)[0].value == "03 · Vận chuyển"
    assert INTERNAL_TRANSIT_NOTE in _visible(app)


# --------------------------------------------------------------------------- #
# REQUIRED REPRODUCTION: real fixture node LO-0307 / MAIN_CARRIAGE
#   click intent → real dispatcher/normalizer → EXISTING transit pane
# --------------------------------------------------------------------------- #

@pytest.fixture()
def fixture_db():
    row = _fixture_row()
    database = mongomock.MongoClient().db
    database.customers.insert_one(
        {"id": row["customerId"], "name": row["customer"], "is_deleted": False})
    database.shipments.insert_one(
        {"id": row["id"], "customer_id": row["customerId"], "is_deleted": False})
    database.quick_notes.insert_many([
        _note("jn-307-int", row["id"], "transit", INTERNAL_TRANSIT_NOTE, "INTERNAL",
              customer=row["customerId"]),
        _note("jn-307-cust", row["id"], "transit", CUSTOMER_TRANSIT_NOTE, "CUSTOMER",
              customer=row["customerId"]),
        _note("jn-307-other", row["id"], "customs", OTHER_STAGE_NOTE, "INTERNAL",
              customer=row["customerId"]),
    ])
    return database


def test_real_fixture_main_carriage_click_opens_the_transit_pane(fixture_db):
    row = _fixture_row()
    node = row["journey"]["nodes"][0]
    assert (node["id"], node["label"]) == ("MAIN_CARRIAGE", "Chặng chính")
    script = (
        "import json, streamlit as st\n"
        "from views import logi_view_model as model\n"
        "from views.journey_discussion import render_internal_discussion\n"
        "row = json.loads(st.session_state['row'])\n"
        "st.session_state['current_user'] = {'username': 'sale.thanh', 'role': 'sale'}\n"
        # EXACTLY the payload component/src/components/JourneyMap.tsx sends.
        "trigger = {'journey_focus': {'seq': 1, 'event': 'journey_focus',\n"
        "    'payload': {'shipment_id': row['id'],\n"
        "                'stage_id': row['journey']['nodes'][0]['id']}}}\n"
        "outcomes = model.consume_journey_focus_triggers({'seq': 0}, trigger)\n"
        "focus = model.journey_focus_pane({'username': 'sale.thanh'}, [row])\n"
        "st.session_state['outcomes'] = outcomes\n"
        "st.session_state['focus'] = focus\n"
        "render_internal_discussion(focus['shipment_id'], focus['customer_id'],\n"
        "    {'username': 'sale.thanh', 'role': 'sale'}, focus_stage=focus['stage_id'])\n"
    )
    app = AppTest.from_string(script, default_timeout=120)
    app.session_state["row"] = json.dumps(row)
    with (
        patch("core.database.get_db", return_value=fixture_db),
        patch("core.journey_notes._resolve_db", return_value=fixture_db),
    ):
        app.run()
    assert not app.exception, [str(item.value) for item in app.exception]

    outcomes = app.session_state["outcomes"]
    assert outcomes and outcomes[0]["ok"] is True
    # The outcome still reports the RAW intent the browser sent…
    assert outcomes[0]["readback"] == {"shipmentId": "LO-0307", "stageId": "main_carriage"}
    # …while the resolved focus is the existing SEVEN-stage bucket.
    focus = app.session_state["focus"]
    assert focus["shipment_id"] == "LO-0307"
    assert focus["stage_id"] == "transit"
    assert focus["customer_id"] == "CUST-DUCLONG"  # from the projection, not the browser
    assert focus["node_id"] == "MAIN_CARRIAGE" and focus["node_label"] == "Chặng chính"

    # The EXISTING pane, opened on Vận chuyển.
    assert list(app.selectbox)[0].value == "03 · Vận chuyển"
    assert app.expander[0].label == "💬 Trao đổi / Chứng từ · lô LO-0307 · công đoạn Vận chuyển"
    shown = _visible(app)
    assert "Đang mở từ Journey Map" in shown
    # Internal data survives for staff…
    assert INTERNAL_TRANSIT_NOTE in shown
    assert CUSTOMER_TRANSIT_NOTE in shown
    # …and the neighbouring bucket is NOT mixed in.
    assert OTHER_STAGE_NOTE not in shown


def test_real_fixture_second_node_opens_its_own_bucket(fixture_db):
    """`delivery` on the same fixture lot is Giao hàng, not the transit thread."""
    row = _fixture_row()
    assert [node["id"] for node in row["journey"]["nodes"]] == ["MAIN_CARRIAGE", "delivery"]
    session: dict = {}
    assert journey_focus.capture(
        session, {"seq": 1, "shipment_id": "LO-0307", "stage_id": "delivery"},
        node_stages=journey_focus.STAFF_NODE_STAGES,
    ) is True
    focus = journey_focus.for_staff(journey_focus.current(session), "sale.thanh", [row])
    assert focus["stage_id"] == "delivery"
    assert focus["node_id"] == "delivery"


# --------------------------------------------------------------------------- #
# real front-end assets (jsdom, no browser, no network)
# --------------------------------------------------------------------------- #



@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
@pytest.mark.parametrize(
    "script,marker",
    [
        ("dom_acceptance_journey_focus_customer.mjs",
         "PASS Journey Map node → discussion intent"),
        ("dom_acceptance_journey_focus_shell.mjs",
         "PASS Journey Map node action (shell)"),
    ],
)
def test_front_end_node_action_is_exercised_on_the_real_assets(script, marker):
    result = subprocess.run(
        ["node", str(_ROOT_PATH / "tests" / "component" / script)],
        cwd=_ROOT_PATH, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker in result.stdout
