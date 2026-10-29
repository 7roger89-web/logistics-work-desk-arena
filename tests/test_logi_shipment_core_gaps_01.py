"""LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — shipment header editability.

Two bounded facts on a lot that the component workspace could display but not
change, repaired on the paths the app already owns:

  * ``created_at`` (``data.0.0.created_at``) — the lot's own header date. It is
    the field the legacy desk edits ("Ngày tạo" in ``views/shipment.py``), that
    the GetFly import writes, and that every reader already projects back as
    ``createdAt``; the component's ``FIELD_PATHS`` whitelist simply could not
    reach it. Now it goes through the SAME ``shipment_field_save`` →
    ``save_shipment_atomic`` → audit → fresh read round trip as every other
    scalar shipment field.
  * the customer half of the lot's name — written by the EXISTING canonical
    ``core.database.update_shipment_customer`` (its own ``shipment_edit`` gate,
    ``customer_updated`` audit row and ``$inc: version``), which until now only
    the legacy Streamlit desk could call.

Invariants asserted here, exactly as the rest of the repo defines them:
UNKNOWN != ZERO (a blank date stays blank and is never filled with today or 0),
no invented defaults (an unknown/blank customer picker is refused, and the lot
code is not treated as an editable name), audit trail, and a fresh readback that
comes from the database rather than from the handler's own echo.

Transport: the isolated mongomock staging database running the CURRENT canonical
writers unchanged; production is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_sandbox
from views import logi_view_model as vm


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _as(role: str, username: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "full_name": username, "role": role, "user_id": f"ID-{username}",
    }


def _stored(sid: str):
    return vm.read_shipment(sid) or {}


def _head(sid: str):
    return _stored(sid).get("data", {}).get("0.0", {})


# ---------------------------------------------------------------------------
# 1. Shipment header date
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", ["saved", "denied", "missing", "empty", "unknown-field", "write-failed"])
def test_header_date_outcome_keeps_request_identity(monkeypatch, case):
    """Every settlement can identify its intent, including a denied write."""
    from core import auth, database, logic

    stored = {"id": "QA-LOT", "version": 1, "data": {"0.0": {"created_at": "2026-10-21"}}}
    writes = []
    monkeypatch.setattr(auth, "can_operate_business", lambda permission: case != "denied")
    monkeypatch.setattr(vm, "read_shipment", lambda sid: None if case == "missing" else stored)
    monkeypatch.setattr(logic, "apply_financial_snapshot", lambda shipment: None)
    monkeypatch.setattr(database, "save_shipment_atomic", lambda *args, **kwargs: writes.append(args) or case != "write-failed")
    monkeypatch.setattr(database, "get_last_db_error", lambda: "QA write refused")
    monkeypatch.setattr(vm, "_projection_for", lambda shipment: {"id": shipment["id"], "createdAt": "21/10/2026"})
    monkeypatch.setattr(vm, "_audit_trail", lambda sid: [])
    monkeypatch.setattr(vm, "_actor", lambda: "qa.admin")
    fields = {} if case == "empty" else {"unapproved": "x"} if case == "unknown-field" else {"created_at": "2026-10-21"}
    outcome = vm._handle_field_save({"shipmentId": "QA-LOT", "fields": fields, "requestId": "HDRD-QA"})
    assert outcome["requestId"] == "HDRD-QA"
    assert outcome["shipmentId"] == "QA-LOT"
    assert outcome["ok"] is (case == "saved")
    assert bool(writes) is (case in {"saved", "write-failed"})
    if case == "saved":
        assert outcome["persisted"]["created_at"] == "2026-10-21"

def test_created_at_is_now_in_the_write_whitelist():
    """The whitelist is the only gate the component has — it must list the field.

    Pinned to an exact count the way LOGI_GNT_CANONICAL_FIELDS_01 and
    LOGI_CN_TRUCK_TYPE_PERSIST_01 pin theirs, so a later reader can see that
    this slice contributed exactly ONE writable key and no side fields.
    """
    assert vm.FIELD_PATHS["created_at"] == ("data", "0.0", "created_at")
    assert "created_at" in vm._DATE_FIELDS
    assert len(vm.FIELD_PATHS) == 34
    under_00 = {k for k, path in vm.FIELD_PATHS.items() if path[1:2] == ("0.0",)}
    assert under_00 == {"incoterm", "mode", "created_at"}
    # The lot CODE is an identifier, not a name field: never writable here.
    assert not {k for k in vm.FIELD_PATHS if k in {"shipment_id", "lot_code", "name", "title"}}


def test_created_at_edit_persists_and_reads_back_fresh(staging, event_seq):
    before = _stored("LO-0306").get("version")
    out = _dispatch(event_seq, "shipment_field_save",
                    {"shipmentId": "LO-0306", "fields": {"created_at": "05/09/2026"}})
    assert out["ok"], out["error"]
    # Canonical ISO form, same as every other date field on this path.
    assert _head("LO-0306")["created_at"] == "2026-09-05"
    assert out["persisted"] == {"created_at": "2026-09-05"}
    assert out["readback"]["createdAt"] == "05/09/2026", "readback is the projected fact"
    assert out["version"] == int(before or 0) + 1, "the canonical writer bumped the version"
    assert any(row["action"] in {"shipment_update", "update"} or "shipment" in row["action"]
               for row in out["audit"]), out["audit"]


def _set_root_and_head_created_at(sid, *, root, head):
    """Test-only seed: head=None removes the key; otherwise sets it verbatim.

    ``data`` stores the section under the LITERAL key "0.0", which a Mongo
    dotted update path cannot address, so the document is rewritten whole.
    """
    from core.database import get_db

    db = get_db()
    assert db is not None
    doc = db.shipments.find_one({"id": sid})
    section = dict(doc["data"]["0.0"])
    if head is None:
        section.pop("created_at", None)
    else:
        section["created_at"] = head
    data = dict(doc["data"])
    data["0.0"] = section
    res = db.shipments.update_one({"id": sid}, {"$set": {"data": data, "created_at": root}})
    assert res.matched_count == 1


def _projected_created_at(sid):
    model = vm.build_view_model()
    return next(s for s in model["shipments"] if s["id"] == sid)["createdAt"]


def test_legacy_missing_header_created_at_falls_back_to_root_timestamp(staging):
    """Legacy rows missing the business header date still sort into a real month.

    The root Mongo created_at is read-only fallback authority ONLY when the
    data.0.0 key does not exist. An explicit blank remains UNKNOWN (next test).
    """
    from datetime import datetime, timezone

    _set_root_and_head_created_at(
        "LO-0306", root=datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc), head=None
    )
    assert "created_at" not in _head("LO-0306")
    assert _projected_created_at("LO-0306") == "29/07/2026"


def test_explicit_blank_header_created_at_ignores_root_timestamp(staging):
    """An explicit blank business date stays UNKNOWN even if a root timestamp exists."""
    from datetime import datetime, timezone

    _set_root_and_head_created_at(
        "LO-0306", root=datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc), head=""
    )
    assert _head("LO-0306")["created_at"] == ""
    assert _projected_created_at("LO-0306") == ""


def test_created_at_blank_stays_unknown_and_is_never_today(staging, event_seq):
    """UNKNOWN != ZERO: clearing the date must not be filled with today or 0."""
    assert _dispatch(event_seq, "shipment_field_save",
                     {"shipmentId": "LO-0306", "fields": {"created_at": "2026-09-05"}})["ok"]

    out = _dispatch(event_seq, "shipment_field_save",
                    {"shipmentId": "LO-0306", "fields": {"created_at": ""}})
    assert out["ok"], out["error"]
    assert _head("LO-0306")["created_at"] == ""
    assert out["readback"]["createdAt"] == "", "an unknown date is blank, not 0 or today"


def test_created_at_is_untouched_when_not_sent(staging, event_seq):
    """Saving another field must never rewrite or blank the lot's date."""
    original = _head("LO-0306").get("created_at")
    out = _dispatch(event_seq, "shipment_field_save",
                    {"shipmentId": "LO-0306", "fields": {"carrier": "Vận tải Bắc Nam"}})
    assert out["ok"], out["error"]
    assert _head("LO-0306").get("created_at") == original
    assert _head("LO-0306")["created_at"], "the seeded date is still there"
    assert "created_at" not in out["persisted"]


def test_created_at_accepts_iso_and_dmy_alike(staging, event_seq):
    for typed in ("2026-09-11", "11/09/2026"):
        out = _dispatch(event_seq, "shipment_field_save",
                        {"shipmentId": "LO-0306", "fields": {"created_at": typed}})
        assert out["ok"], out["error"]
        assert _head("LO-0306")["created_at"] == "2026-09-11"


def test_date_edit_does_not_move_any_other_header_fact(staging, event_seq):
    before = dict(_head("LO-0306"))
    _dispatch(event_seq, "shipment_field_save",
              {"shipmentId": "LO-0306", "fields": {"created_at": "2026-09-12"}})
    after = dict(_head("LO-0306"))
    assert after["st"] == before["st"] and after["mode"] == before["mode"]
    assert after["incoterm"] == before["incoterm"]
    assert after["created_at"] == "2026-09-12"


# ---------------------------------------------------------------------------
# 2. Shipment name (customer half) via the existing canonical writer
# ---------------------------------------------------------------------------

def test_lot_customer_change_persists_through_the_canonical_writer(staging, event_seq):
    from core.database import load_customers

    customers = load_customers() or {}
    assert "CUST-MINHDUC" in customers

    assert _stored("LO-0306")["customer_id"] == "CUST-ANPHAT", "start from a different owner"

    out = _dispatch(event_seq, "shipment_customer_save",
                    {"shipmentId": "LO-0306", "customerId": "CUST-MINHDUC"})
    assert out["ok"], out["error"]
    assert not out.get("noop"), "a real change must not be reported as a no-op"

    fresh = _stored("LO-0306")
    # ``update_shipment_customer`` writes the SAME triple the legacy desk writes.
    assert fresh["customer"] == fresh["client"] == customers["CUST-MINHDUC"]["name"]
    assert fresh["customer_id"] == "CUST-MINHDUC"
    assert out["persisted"] == {"customer": fresh["customer"], "customerId": "CUST-MINHDUC"}
    assert out["readback"]["customer"] == fresh["customer"]
    assert any(row["action"] == "customer_updated" for row in out["audit"]), out["audit"]
    assert out["version"] == int(fresh.get("version") or 0)


def test_lot_customer_change_is_visible_in_the_next_view_model(staging, event_seq):
    assert _dispatch(event_seq, "shipment_customer_save",
                     {"shipmentId": "LO-0306", "customerId": "CUST-MINHDUC"})["ok"]
    model = vm.build_view_model()
    row = next(s for s in model["shipments"] if s["id"] == "LO-0306")
    assert row["customer"] == "Minh Đức JSC"
    assert row["customerId"] == "CUST-MINHDUC"


def test_lot_customer_noop_reports_success_without_a_version_bump(staging, event_seq):
    """Re-saving the same customer is not faked as a change in the audit trail."""
    before = _stored("LO-0308")
    same = before["customer_id"]
    out = _dispatch(event_seq, "shipment_customer_save",
                    {"shipmentId": "LO-0308", "customerId": same})
    assert out["ok"] and out.get("noop") is True
    after = _stored("LO-0308")
    assert after.get("version") == before.get("version")
    assert not any(row["action"] == "customer_updated" for row in (out.get("audit") or []))


@pytest.mark.parametrize("payload,needle", [
    ({"customerId": "CUST-KHONGCO"}, "danh bạ"),
    ({"customerId": ""}, "khách hàng"),
    ({}, "khách hàng"),
])
def test_lot_customer_refuses_unknown_and_empty_without_inventing(staging, event_seq, payload, needle):
    """No fallback name, no "--Chọn--", no first customer, no blank write."""
    before = _stored("LO-0308")
    out = _dispatch(event_seq, "shipment_customer_save", {"shipmentId": "LO-0308", **payload})
    assert not out["ok"], out
    assert needle in out["error"].lower(), out["error"]
    after = _stored("LO-0308")
    assert after.get("customer") == before.get("customer")
    assert after.get("customer_id") == before.get("customer_id")
    assert after.get("version") == before.get("version")


def test_lot_with_customer_id_refuses_free_text_rename_without_mutation_or_audit(staging, event_seq):
    """A free name may never contradict the customer ID already on the lot."""
    from core.database import get_db

    db = get_db()
    assert db is not None
    before = _stored("LO-0308")
    audits_before = db.audit_logs.count_documents({
        "entity_type": "shipment", "entity_id": "LO-0308", "action": "customer_updated",
    })

    out = _dispatch(event_seq, "shipment_customer_save",
                    {"shipmentId": "LO-0308", "customer": "Khách tự gõ"})

    assert not out["ok"]
    assert "gắn mã khách" in out["error"]
    assert _stored("LO-0308") == before
    assert db.audit_logs.count_documents({
        "entity_type": "shipment", "entity_id": "LO-0308", "action": "customer_updated",
    }) == audits_before


def test_canonical_writer_ignores_typed_name_when_valid_customer_id_is_selected(staging):
    from core.database import load_customers, update_shipment_customer

    customers = load_customers() or {}
    assert update_shipment_customer("LO-0306", "Tên giả từ browser", "CUST-MINHDUC")
    fresh = _stored("LO-0306")
    assert fresh["customer_id"] == "CUST-MINHDUC"
    assert fresh["customer"] == fresh["client"] == customers["CUST-MINHDUC"]["name"]
    assert fresh["customer"] != "Tên giả từ browser"


@pytest.mark.parametrize("customer_id,archive_first", [
    ("CUST-KHONGCO", False),
    ("CUST-HONGHA", True),
])
def test_canonical_writer_refuses_unknown_or_archived_customer_without_side_effects(
    staging, customer_id, archive_first
):
    from core.database import get_db, update_shipment_customer

    db = get_db()
    assert db is not None
    if archive_first:
        db.customers.update_one({"id": customer_id}, {"$set": {"is_deleted": True}})
    before = _stored("LO-0308")
    audits_before = db.audit_logs.count_documents({
        "entity_type": "shipment", "entity_id": "LO-0308", "action": "customer_updated",
    })

    assert not update_shipment_customer("LO-0308", "Tên không được lưu", customer_id)

    assert _stored("LO-0308") == before
    assert db.audit_logs.count_documents({
        "entity_type": "shipment", "entity_id": "LO-0308", "action": "customer_updated",
    }) == audits_before


def test_legacy_idless_lot_keeps_name_only_history_without_guessing_an_id(staging):
    from core.database import get_db, update_shipment_customer

    db = get_db()
    assert db is not None
    result = db.shipments.update_one({"id": "LO-0299"}, {"$unset": {"customer_id": ""}})
    assert result.matched_count == 1

    # Even though this exactly matches a directory name, the legacy write does
    # not infer/link an ID. Historical ID-less rows remain reviewable as-is.
    assert update_shipment_customer("LO-0299", "An Phát JSC")
    fresh = _stored("LO-0299")
    assert fresh["customer"] == fresh["client"] == "An Phát JSC"
    assert not fresh.get("customer_id")


def test_rename_of_the_lot_code_is_deliberately_not_exposed(staging):
    """Scope honesty: the code half of the name is NOT a free-edit field here.

    ``core.database.rename_shipment_id`` re-points proxy payments and
    entrustments but not ``contracts.shipment_ids``, so exposing a rename in
    this slice would silently break contract links. The claim under test is
    therefore: no rename event exists, and the code stays untouched by the two
    new write paths.
    """
    from core.database import rename_shipment_id
    import inspect

    source = inspect.getsource(rename_shipment_id)
    assert "shipment_ids" not in source, "the gap that keeps this read-only is real"
    assert not {name for name in vm.ALL_EVENTS if "rename" in name or "shipment_id" in name}


# ---------------------------------------------------------------------------
# 3. RBAC on both new surfaces
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("event,payload", [
    ("shipment_field_save", {"shipmentId": "LO-0306", "fields": {"created_at": "2026-09-05"}}),
    ("shipment_customer_save", {"shipmentId": "LO-0308", "customerId": "CUST-ANPHAT"}),
])
def test_viewer_is_refused_on_both_new_shipment_surfaces(staging, event_seq, event, payload):
    before = _stored(payload["shipmentId"])
    _as("viewer", "viewer.gap")
    out = _dispatch(event_seq, event, payload)
    assert not out["ok"] and "RBAC" in out["error"]
    assert _stored(payload["shipmentId"]).get("version") == before.get("version")


def test_sale_can_edit_both_new_surfaces(staging, event_seq):
    """The boundary is the existing role matrix, not the component's display."""
    _as("sale", "sale.gap")
    assert _dispatch(event_seq, "shipment_field_save",
                     {"shipmentId": "LO-0306", "fields": {"created_at": "2026-09-13"}})["ok"]
    assert _dispatch(event_seq, "shipment_customer_save",
                     {"shipmentId": "LO-0308", "customerId": "CUST-HONGHA"})["ok"]
    assert _head("LO-0306")["created_at"] == "2026-09-13"
    assert _stored("LO-0308")["customer_id"] == "CUST-HONGHA"


def test_new_event_reuses_the_existing_writer_and_whitelist_only(staging):
    """Reuse rule: no second shipment writer, no new collection, no new path set."""
    assert "shipment_customer_save" in vm.PHASE_B_EVENTS
    assert vm.PHASE_B_EVENTS == set(vm._HANDLERS)
    assert vm._HANDLERS["shipment_customer_save"] is vm._handle_shipment_customer_save

    from core.database import get_db

    db = get_db()
    names = set(db.list_collection_names()) if db is not None else set()
    assert not {name for name in names if "lot_name" in name or "shipment_title" in name}

    # The handler calls the canonical writer — it does not re-implement $set.
    import inspect

    body = inspect.getsource(vm._handle_shipment_customer_save)
    assert "update_shipment_customer" in body
    assert "$set" not in body
