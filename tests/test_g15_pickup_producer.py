"""Issue #263 — the staff pickup update is the ONLY producer of the customer
milestone source, and Admin verifies/publishes it through the existing workflow.

WRONG_PASS guarded here: inserting ``public_events`` fixtures and then calling
the publisher proves nothing. Every positive test below starts from the REAL
staff write (``shipment_transport_save`` through the production dispatcher,
RBAC and atomic writer) and inspects the record THAT ACTION created, before any
Admin verification.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

import mongomock
import pytest

from core import customer_journey, customer_portal
from core import customer_portal_publish as publisher
from core.customer_portal_milestones import (
    content_digest,
    public_source_content,
    record_pickup_source,
    source_event_id,
)

CUSTOMER_A = "CUST-263-A"
CUSTOMER_B = "CUST-263-B"
EMAIL_A = "khach-a-263@example.test"
EMAIL_B = "khach-b-263@example.test"
LOT_A = "LO-263-A"
LOT_B = "LO-263-B"
INTERNAL_SECRET = "SECRET_INTERNAL_MARGIN_987654321"


def _truck_leg(*, atd: str = "", origin: str = "Nam Ninh", plate: str = "桂A-26301") -> dict:
    return {
        "id": "leg-pickup", "sequence": 1, "mode": "Truck",
        "origin": origin, "destination": "Hữu Nghị", "carrier": "CN Road Partner",
        "etd": "2026-11-01", "eta": "2026-11-02", "atd": atd, "ata": "",
        "units": [{
            "id": "truck-1", "kind": "truck", "number": plate,
            "type_size": "Container 40", "driver_name": INTERNAL_SECRET,
            "driver_phone": "0900263263",
        }],
    }


def _shipment(lot: str, customer_id: str, *, atd: str = "", **extra) -> dict:
    return {
        "id": lot, "shipment_id": lot, "customer_id": customer_id,
        "customer": "An Phát JSC", "transport_mode": "ROAD",
        "status": "pending", "version": 0, "is_deleted": False,
        "internal_notes": INTERNAL_SECRET,
        "data": {
            "0.0": {"st": "pending", "mode": "Truck", "incoterm": "DAP"},
            "1.2": {"transport_legs": [_truck_leg(atd=atd)]},
            "2.4": {}, "2.6": {}, "2.7": {},
            "3.4": {"details": [{"amount": 987654321}], "payments": []},
        },
        **extra,
    }


@pytest.fixture()
def db():
    database = mongomock.MongoClient()["g15_pickup_producer"]
    database.customers.insert_many([
        {"id": CUSTOMER_A, "name": "An Phát JSC", "portal_access_email": EMAIL_A,
         "is_deleted": False},
        {"id": CUSTOMER_B, "name": "Khách B", "portal_access_email": EMAIL_B,
         "is_deleted": False},
    ])
    database.shipments.insert_many([
        _shipment(LOT_A, CUSTOMER_A), _shipment(LOT_B, CUSTOMER_B),
    ])
    return database


def _rows(database) -> list[dict]:
    return list(database.public_events.find({"shipment_id": LOT_A}))


def _verify(database, *, role: str = "admin", lot: str = LOT_A, customer: str = CUSTOMER_A,
            event_id: str | None = None, version: str | None = None):
    row = database.public_events.find_one({"shipment_id": lot})
    return publisher.verify_source(
        event_id or row["id"], version or row["version"],
        customer_id=customer, shipment_id=lot,
        actor_role=role, actor_username="staging-admin", db=database,
    )


def _publish(database, *, customer: str = CUSTOMER_A, lot: str = LOT_A,
             versions: dict | None = None, current: str = ""):
    row = database.public_events.find_one({"shipment_id": lot})
    return publisher.publish_verified_sources(
        customer, lot,
        event_versions={row["id"]: row["version"]} if versions is None else versions,
        document_versions={}, expected_current_version=current,
        actor_role="admin", actor_username="staging-admin", db=database,
    )


# --------------------------------------------------------------------------- #
# Producer
# --------------------------------------------------------------------------- #

def test_staff_fact_produces_exactly_one_unverified_source(db):
    """A stored pickup fact becomes ONE pending source — never a publication."""
    assert _rows(db) == []
    receipt = record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"),
                                   actor_username="thuhang")
    assert receipt == {
        "id": source_event_id(CUSTOMER_A, LOT_A), "version": receipt["version"],
        "state": "PENDING", "changed": True,
    }
    rows = _rows(db)
    assert len(rows) == 1
    row = rows[0]
    assert row["customer_id"] == CUSTOMER_A and row["shipment_id"] == LOT_A
    assert row["stage_id"] == "pickup" and row["occurred_at"] == "2026-11-02"
    assert row["public_title"] == "Đã lấy hàng" and row["visibility"] == "CUSTOMER"
    assert row["verified"] is False and row["verified_at"] == ""
    assert row["recorded_by"] == "thuhang"
    assert row["version"] == content_digest(public_source_content(
        customer_id=CUSTOMER_A, shipment_id=LOT_A, stage_id="pickup",
        public_title="Đã lấy hàng", occurred_at="2026-11-02"))[:16]
    # No internal field is projected into the public source.
    assert INTERNAL_SECRET not in str(row)
    assert "0900263263" not in str(row) and "桂A-26301" not in str(row)


def test_no_pickup_fact_means_no_source(db):
    """ETD is a plan, not a pickup: only an actual ATD creates the milestone."""
    assert record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A), actor_username="thuhang") is None
    assert _rows(db) == []


def test_resaving_identical_facts_keeps_verification_and_new_facts_clear_it(db):
    before = record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"),
                                  actor_username="thuhang")
    assert _verify(db)[0] is True
    same = record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"),
                                actor_username="thuhang")
    assert same["changed"] is False and same["version"] == before["version"]
    assert _rows(db)[0]["verified"] is True                      # unchanged facts keep approval
    moved = record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-03"),
                                 actor_username="minhtu")
    assert moved["changed"] is True and moved["version"] != before["version"]
    row = _rows(db)[0]
    assert row["verified"] is False and row["verified_at"] == "" and row["occurred_at"] == "2026-11-03"


def test_withdrawn_pickup_is_unverified_and_unpublishable(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    assert _verify(db)[0] is True
    receipt = record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd=""), actor_username="thuhang")
    assert receipt["state"] == "WITHDRAWN"
    row = _rows(db)[0]
    assert row["verified"] is False and row["occurred_at"] == ""
    with pytest.raises(publisher.PublicationWriteDenied):
        _verify(db)
    with pytest.raises(publisher.PublicationWriteDenied):
        _publish(db)


# --------------------------------------------------------------------------- #
# Admin verification
# --------------------------------------------------------------------------- #

def test_verify_requires_admin_exact_version_and_intact_content(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    row = _rows(db)[0]
    pending = publisher.list_pending_sources(CUSTOMER_A, LOT_A, actor_role="admin", db=db)
    assert [(p["id"], p["version"], p["state"]) for p in pending] == [
        (row["id"], row["version"], "PENDING")
    ]
    with pytest.raises(publisher.PublicationWriteDenied):
        publisher.list_pending_sources(CUSTOMER_A, LOT_A, actor_role="support", db=db)

    # Non-Admin actor can never verify.
    with pytest.raises(publisher.PublicationWriteDenied):
        _verify(db, role="support")

    # A stale version from an older screen is refused without writing.
    ok, message = _verify(db, version="0000000000000000")
    assert ok is False and "thay đổi" in message
    assert _rows(db)[0]["verified"] is False

    # Out-of-band content edit with the old version kept is refused by the hash.
    db.public_events.update_one({"id": row["id"]}, {"$set": {"public_title": "Đã lấy hàng (sửa tay)"}})
    with pytest.raises(publisher.PublicationWriteDenied):
        _verify(db)
    assert _rows(db)[0]["verified"] is False

    # Foreign tenant can never verify another customer's lot.
    with pytest.raises(publisher.PublicationWriteDenied):
        _verify(db, customer=CUSTOMER_B, version=row["version"])
    assert _rows(db)[0]["verified"] is False


def test_verified_source_appears_in_the_existing_publication_list(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    assert publisher.list_verified_sources(CUSTOMER_A, LOT_A, actor_role="admin", db=db)["events"] == []
    ok, message = _verify(db)
    assert ok is True, message
    row = _rows(db)[0]
    assert row["verified"] is True and row["verified_by"] == "staging-admin" and row["verified_at"]
    options = publisher.list_verified_sources(CUSTOMER_A, LOT_A, actor_role="admin", db=db)
    assert [(e["id"], e["version"]) for e in options["events"]] == [(row["id"], row["version"])]
    assert publisher.list_pending_sources(CUSTOMER_A, LOT_A, actor_role="admin", db=db) == []
    # Idempotent: verifying the same version twice is not a new approval.
    again, message = _verify(db)
    assert again is True and "đã được xác minh" in message


# --------------------------------------------------------------------------- #
# Customer read boundary
# --------------------------------------------------------------------------- #

def _dashboard(database, email: str):
    principal = customer_portal.build_customer_principal(verified_email=email, db=database)
    return customer_portal.load_customer_dashboard(principal, db=database)


def test_customer_a_sees_the_published_milestone_only_after_publication(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")

    # BEFORE verification/publication: nothing reaches the customer.
    view = _dashboard(db, EMAIL_A)
    assert [c.reference for c in view.cards] == []
    assert view.denied_lots == 1

    assert _verify(db)[0] is True
    # Verified but not published is still invisible.
    assert [c.reference for c in _dashboard(db, EMAIL_A).cards] == []

    ok, message = _publish(db)
    assert ok is True, message
    card = _dashboard(db, EMAIL_A).cards[0]
    assert card.reference == LOT_A
    assert [(e["stage"], e["title"], e["occurred_at"]) for e in card.timeline] == [
        ("pickup", "Đã lấy hàng", "2026-11-02")
    ]
    # The published payload carries nothing internal.
    payload = str(asdict(card))
    for secret in (INTERNAL_SECRET, "987654321", "0900263263", "桂A-26301", "_id"):
        assert secret not in payload

    # Customer B never sees customer A's lot or milestone.
    view_b = _dashboard(db, EMAIL_B)
    assert [c.reference for c in view_b.cards] == []
    assert "Đã lấy hàng" not in str([asdict(c) for c in view_b.cards])


def test_customer_journey_marks_pickup_completed_from_the_published_source(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    assert _verify(db)[0] is True
    assert _publish(db)[0] is True
    card = _dashboard(db, EMAIL_A).cards[0]
    model = customer_journey.build_lot_model(card)
    nodes = {node["id"]: node for node in model["journey"]["nodes"]}
    assert nodes["pickup"]["state"] == "COMPLETED"
    assert nodes["pickup"]["evidence"] == "Đã lấy hàng"
    assert nodes["pickup"]["occurred_at"] == "2026-11-02"
    assert nodes["plan"]["state"] == "UNKNOWN"      # no neighbouring stage is inferred


def test_old_version_cannot_be_published_after_the_staff_fact_changes(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    assert _verify(db)[0] is True
    first = _rows(db)[0]
    old_version = first["version"]
    # Staff corrects the actual pickup date -> a NEW version, verified cleared.
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-05"), actor_username="thuhang")
    with pytest.raises(publisher.PublicationWriteDenied):
        _publish(db, versions={first["id"]: old_version})
    assert db.shipments.find_one({"id": LOT_A}).get("customer_publication_version") in (None, "")


def test_published_source_edited_after_approval_fails_closed(db):
    record_pickup_source(db, _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02"), actor_username="thuhang")
    assert _verify(db)[0] is True
    assert _publish(db)[0] is True
    assert len(_dashboard(db, EMAIL_A).cards) == 1
    # Same id + version, edited content: the customer reader must refuse the lot.
    db.public_events.update_one({"shipment_id": LOT_A}, {"$set": {"occurred_at": "2026-01-01"}})
    view = _dashboard(db, EMAIL_A)
    assert view.cards == () and view.denied_lots == 1


# --------------------------------------------------------------------------- #
# End-to-end through the REAL staff handler (production dispatcher + RBAC)
# --------------------------------------------------------------------------- #

@pytest.fixture()
def staging():
    import streamlit as st

    from views import logi_sandbox

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = {
        "username": "thuhang", "full_name": "Thu Hằng", "role": "SUPPORT",
        "user_id": "STAGING-SUPPORT",
    }
    yield logi_sandbox
    st.session_state.clear()
    logi_sandbox.reset_backend()


def _dispatch(name: str, payload: dict) -> dict:
    from views import logi_view_model as vm

    outcomes = vm.consume_phase_b_triggers(
        {"seq": 0}, {name: {"seq": 1, "event": name, "payload": payload}},
    )
    assert len(outcomes) == 1
    return outcomes[0]


def test_staff_handler_writes_the_pending_source_and_admin_publishes_it(staging):
    """A→G on the real dispatcher; no fixture public_events anywhere."""

    from core.database import get_db

    database = get_db()
    lot = database.shipments.find_one({"id": "LO-0306"})
    assert lot is not None
    customer_id = lot["customer_id"]
    database.customers.update_one(
        {"id": customer_id}, {"$set": {"portal_access_email": EMAIL_A}},
    )
    assert database.public_events.count_documents({"shipment_id": "LO-0306"}) == 0
    row_id = source_event_id(customer_id, "LO-0306")

    legs = [_truck_leg(atd="2026-11-02", plate="桂A-26399")]
    out = _dispatch("shipment_transport_save", {"shipmentId": "LO-0306", "transportLegs": legs})
    assert out["ok"] is True, out["error"]
    assert out["readback"]["transportLegs"][0]["atd"] == "2026-11-02"
    assert out["sourceError"] == ""

    # The record inspected here was created by THAT staff action, not a fixture.
    rows = list(database.public_events.find({"shipment_id": "LO-0306"}))
    assert len(rows) == 1
    source = rows[0]
    assert source["customer_id"] == customer_id
    assert source["verified"] is False and source["state"] == "PENDING"
    assert source["occurred_at"] == "2026-11-02"
    assert out["pendingSource"]["id"] == source["id"] == row_id
    assert out["pendingSource"]["version"] == source["version"]

    # B — customer sees nothing before publication.
    assert [c.reference for c in _dashboard(database, EMAIL_A).cards] == []

    # C — Admin sees exactly this source/version, then verifies it.
    pending = publisher.list_pending_sources(customer_id, "LO-0306", actor_role="admin", db=database)
    assert [(p["id"], p["version"]) for p in pending] == [(source["id"], source["version"])]
    ok, message = publisher.verify_source(
        source["id"], source["version"], customer_id=customer_id, shipment_id="LO-0306",
        actor_role="admin", actor_username="admin", db=database,
    )
    assert ok is True, message

    # D — the EXISTING publication workflow publishes that exact version.
    ok, message = publisher.publish_verified_sources(
        customer_id, "LO-0306",
        event_versions={source["id"]: source["version"]}, document_versions={},
        expected_current_version="", actor_role="admin", actor_username="admin", db=database,
    )
    assert ok is True, message

    # E — customer A reloads and sees the approved milestone.
    card = _dashboard(database, EMAIL_A).cards[0]
    assert card.reference == "LO-0306"
    assert [(e["title"], e["occurred_at"]) for e in card.timeline] == [("Đã lấy hàng", "2026-11-02")]
    assert customer_journey.build_lot_model(card)["journey"]["nodes"][1]["state"] == "COMPLETED"

    # F — another customer's session never receives this lot, even when that
    # customer has its own published lot of the same shape.
    database.customers.insert_one(
        {"id": CUSTOMER_B, "name": "Khách B", "portal_access_email": EMAIL_B, "is_deleted": False},
    )
    b_lot = database.shipments.find_one({}) or {}
    database.shipments.insert_one({
        **{k: v for k, v in b_lot.items() if k != "_id"},
        "id": "LO-263-B-E2E", "shipment_id": "LO-263-B-E2E",
        "customer_id": CUSTOMER_B, "version": 0,
    })
    view_b = _dashboard(database, EMAIL_B)
    assert all(card.reference != "LO-0306" for card in view_b.cards)
    assert "Đã lấy hàng" not in str([asdict(c) for c in view_b.cards])
    assert "LO-0306" not in str(view_b)


def test_non_staff_role_cannot_produce_a_source(staging):
    from core.database import get_db

    database = get_db()
    import streamlit as st

    st.session_state["current_user"] = {
        "username": "viewer-263", "full_name": "Viewer", "role": "VIEWER", "user_id": "V-263",
    }
    out = _dispatch("shipment_transport_save", {
        "shipmentId": "LO-0306",
        "transportLegs": [_truck_leg(atd="2026-11-02")],
    })
    assert out["ok"] is False
    assert database.public_events.count_documents({"shipment_id": "LO-0306"}) == 0


def test_cargo_only_save_does_not_invent_a_pickup_source(staging):
    from core.database import get_db

    database = get_db()
    out = _dispatch("shipment_transport_save", {
        "shipmentId": "LO-0306",
        "cargoSummary": {"goods_description": "Thép cuộn", "package_count": "12"},
    })
    assert out["ok"] is True and out["pendingSource"] is None
    assert database.public_events.count_documents({"shipment_id": "LO-0306"}) == 0


def test_saved_document_copy_is_not_mutated_by_the_producer(db):
    """Defensive: the producer must never write into the shipment document."""
    shipment = _shipment(LOT_A, CUSTOMER_A, atd="2026-11-02")
    snapshot = deepcopy(shipment)
    record_pickup_source(db, shipment, actor_username="thuhang")
    assert shipment == snapshot
