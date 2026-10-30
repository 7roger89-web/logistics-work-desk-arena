"""G1.5 Admin publication: real write/readback on a synthetic isolated Mongo."""
from __future__ import annotations

from dataclasses import asdict

import mongomock
import pytest

from core import customer_portal
from core import customer_portal_publish as publication

CUSTOMER = "CUST-LG-PUBLISH"
LOT = "G1-LG-PUB-01"
EMAIL = "lucgiac-publish@example.com"


@pytest.fixture
def db():
    database = mongomock.MongoClient()["g15_publish_isolated"]
    database.customers.insert_one({
        "id": CUSTOMER, "name": "Lục Giác", "portal_access_email": EMAIL,
    })
    database.shipments.insert_one({
        "id": LOT, "customer_id": CUSTOMER, "transport_mode": "SEA",
    })
    database.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": CUSTOMER,
        "shipment_id": LOT, "stage_id": "pickup",
        "public_title": "Đã lấy hàng", "occurred_at": "2026-10-30T01:00:00Z",
        "verified": True, "verified_at": "2026-10-30T02:00:00Z",
        "visibility": "CUSTOMER", "internal_notes": "SECRET_NOTE",
    })
    database.public_documents.insert_one({
        "id": "DOC-1", "version": "v2", "customer_id": CUSTOMER,
        "shipment_id": LOT, "kind": "PL",
        "public_title": "Packing list", "status": "AVAILABLE",
        "verified": True, "visibility": "CUSTOMER",
        "storage_file_id": "SECRET_GRIDFS_ID",
    })
    database.quotes.insert_one({
        "id": "QT-1", "customer_id": CUSTOMER,
        "selling_total_vnd": 987654321, "margin": "SECRET_MARGIN",
    })
    return database


def _release(db, *, event_versions=None, document_versions=None, current="",
             role="admin", lot=LOT):
    return publication.publish_verified_sources(
        CUSTOMER, lot,
        event_versions=event_versions if event_versions is not None else {"EV-1": "v1"},
        document_versions=document_versions if document_versions is not None else {"DOC-1": "v2"},
        expected_current_version=current,
        actor_role=role, actor_username="staging-admin",
        db=db,
    )


def test_admin_can_select_and_publish_existing_verified_versions(db):
    options = publication.list_verified_sources(CUSTOMER, LOT, actor_role="admin", db=db)
    assert [(r["id"], r["version"]) for r in options["events"]] == [("EV-1", "v1")]
    assert [(r["id"], r["version"]) for r in options["documents"]] == [("DOC-1", "v2")]
    assert "SECRET" not in str(options)
    ok, message = _release(db)
    assert ok is True, message
    shipment = db.shipments.find_one({"id": LOT})
    version = shipment["customer_publication_version"]
    assert version.startswith("g15-")
    manifest = db.customer_publications.find_one({"shipment_id": LOT, "version": version})
    assert manifest["state"] == "PUBLISHED"
    assert manifest["approved_by"] == "staging-admin"
    assert manifest["event_versions"] == {"EV-1": "v1"}
    assert manifest["document_versions"] == {"DOC-1": "v2"}
    principal = customer_portal.build_customer_principal(verified_email=EMAIL, db=db)
    card = customer_portal.load_customer_dashboard(principal, db=db).cards[0]
    assert [(e["id"], e["title"]) for e in card.timeline] == [("EV-1", "Đã lấy hàng")]
    assert [(d["id"], d["version"]) for d in card.documents] == [("DOC-1", "v2")]
    assert card.quote is None
    payload = str(asdict(card))
    assert "SECRET" not in payload and "987654321" not in payload


def test_backend_rejects_viewer_even_if_ui_were_bypassed(db):
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db, role="viewer")
    assert db.customer_publications.count_documents({}) == 0
    assert "customer_publication_version" not in db.shipments.find_one({"id": LOT})
    with pytest.raises(publication.PublicationWriteDenied):
        publication.list_verified_sources(CUSTOMER, LOT, actor_role="viewer", db=db)


def test_cross_tenant_or_unknown_lot_cannot_be_published(db):
    db.shipments.insert_one({"id": "FOREIGN-1", "customer_id": "OTHER"})
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db, lot="FOREIGN-1")
    assert db.customer_publications.count_documents({}) == 0


@pytest.mark.parametrize("events,docs", [
    ({"EV-1": "v999"}, {"DOC-1": "v2"}),
    ({"EV-1": "v1"}, {"DOC-1": "v999"}),
    ({"UNKNOWN": "v1"}, {}),
    ({}, {"UNKNOWN": "v2"}),
    ({}, {}),
])
def test_missing_stale_or_unselected_versions_never_publish(db, events, docs):
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db, event_versions=events, document_versions=docs)
    assert db.customer_publications.count_documents({}) == 0


def test_revoked_source_verification_fails_closed(db):
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"verified": False}})
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db)
    assert db.customer_publications.count_documents({}) == 0


def test_private_document_is_never_eligible(db):
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"visibility": "TT"}})
    options = publication.list_verified_sources(CUSTOMER, LOT, actor_role="admin", db=db)
    assert options["documents"] == []
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db)
    assert db.customer_publications.count_documents({}) == 0


def test_concurrent_or_stale_version_is_refused_without_wiping_release(db):
    first, _ = _release(db)
    assert first
    stable_version = db.shipments.find_one({"id": LOT})["customer_publication_version"]
    result, message = _release(db, current="")
    assert result is False and "thay đổi" in message
    assert db.shipments.find_one({"id": LOT})["customer_publication_version"] == stable_version
    assert db.customer_publications.count_documents({}) == 1
    success, _ = _release(db, current=stable_version, event_versions={"EV-1": "v1"},
                          document_versions={})
    assert success
    current_version = db.shipments.find_one({"id": LOT})["customer_publication_version"]
    assert current_version != stable_version
    assert db.customer_publications.count_documents({}) == 2


def test_invalid_or_unsafe_ids_are_denied_before_write(db):
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db, event_versions={"injected.key": "v1"}, document_versions={})
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db, event_versions={"EV-1": "v1"}, document_versions={"$bad": "v1"})
    assert db.customer_publications.count_documents({}) == 0


def test_unapproved_customer_cannot_read_after_admin_publishes(db):
    ok, _ = _release(db)
    assert ok
    db.customers.update_one({"id": CUSTOMER}, {"$unset": {"portal_access_email": ""}})
    with pytest.raises(customer_portal.PortalAccessDenied):
        customer_portal.build_customer_principal(verified_email=EMAIL, db=db)


def test_orphan_customer_id_cannot_create_publication(db):
    db.customers.delete_one({"id": CUSTOMER})
    with pytest.raises(publication.PublicationWriteDenied):
        _release(db)
    assert db.customer_publications.count_documents({}) == 0


def test_viewer_has_no_admin_publication_ui(monkeypatch):
    import streamlit as st
    from views.customer_dashboard import render_owner_portal_access_control

    def should_not_open(*_args, **_kwargs):
        raise AssertionError("Viewer reached Admin-only publishing widgets")

    monkeypatch.setattr(st, "expander", should_not_open)
    render_owner_portal_access_control({"username": "readonly", "role": "viewer"})
