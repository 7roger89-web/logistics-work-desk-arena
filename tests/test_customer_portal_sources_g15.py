"""G1.5 source-to-allowlist tests: read only approved, version-pinned data."""
from __future__ import annotations

from dataclasses import asdict
from unittest.mock import patch

import mongomock
import pytest

from core import customer_portal as portal
from core.customer_portal_sources import PublicSourceUnavailable, read_approved_sources
from core.hexa_customer_publication import (
    PUBLICATION_SCHEMA, approved_content_fingerprint, build_customer_publication,
)

CUSTOMER = "CUST-LUCGIAC"
LOT = "G1-LG-001"
EMAIL = "portal.lucgiac@example.com"


@pytest.fixture
def db():
    database = mongomock.MongoClient()["g15_source_contract"]
    database.customers.insert_one({
        "id": CUSTOMER, "name": "Lục Giác", "portal_access_email": EMAIL,
    })
    database.shipments.insert_one({
        "id": LOT, "customer_id": CUSTOMER, "transport_mode": "ROAD",
        "customer_publication_version": "v1", "quote_id": "QT-1",
    })
    database.customer_publications.insert_one({
        "schema": PUBLICATION_SCHEMA, "customer_id": CUSTOMER,
        "shipment_id": LOT, "version": "v1", "state": "PUBLISHED",
        "approved_by": "owner", "approved_at": "2026-10-27T06:00:00Z",
        "event_versions": {"EV-1": "v1"}, "document_versions": {"DOC-1": "v1"},
        "quote": {"id": "QT-1", "version": "1"},
    })
    return database


def _view(db):
    principal = portal.build_customer_principal(verified_email=EMAIL, db=db)
    return portal.load_customer_dashboard(principal, db=db)


def _approve_fixture_content(db):
    """Simulate Owner approval of the current allowlisted public snapshot."""
    manifest = db.customer_publications.find_one({"shipment_id": LOT})
    events, documents, _ = read_approved_sources(
        db, customer_id=CUSTOMER, shipment_id=LOT,
        shipment_quote_id=None, publication=manifest,
    )
    safe = build_customer_publication(
        shipment=db.shipments.find_one({"id": LOT}),
        principal={"kind": "customer", "authenticated": True, "customer_id": CUSTOMER},
        publication=manifest, events=events, documents=documents,
    )
    db.customer_publications.update_one(
        {"shipment_id": LOT},
        {"$set": {"approved_content_sha256": approved_content_fingerprint(safe)}},
    )


def _insert_sources(db):
    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": CUSTOMER,
        "shipment_id": LOT, "stage_id": "pickup",
        "public_title": "Đã lấy hàng", "occurred_at": "2026-10-27T08:00:00Z",
        "verified": True, "verified_at": "2026-10-27T08:30:00Z",
        "visibility": "CUSTOMER", "private_notes": "SECRET_INTERNAL_EVENT",
    })
    db.public_documents.insert_one({
        "id": "DOC-1", "version": "v1", "customer_id": CUSTOMER,
        "shipment_id": LOT, "kind": "PL", "public_title": "Packing List",
        "status": "AVAILABLE", "verified": True, "visibility": "CUSTOMER",
        "storage_file_id": "SECRET_GRIDFS_ID",
    })
    db.quotes.insert_one({
        "id": "QT-1", "version": 1, "customer_id": CUSTOMER, "status": "SENT",
        "calculation": {
            "selling_price_total_vnd": 250000.0, "internal_cost": "SECRET_COST",
        },
        "margin": "SECRET_MARGIN",
    })
    _approve_fixture_content(db)


def test_approved_sources_reach_only_the_customer_safe_card(db):
    _insert_sources(db)
    card = _view(db).cards[0]
    assert card.timeline == ({
        "id": "EV-1", "version": "v1", "stage": "pickup",
        "title": "Đã lấy hàng", "occurred_at": "2026-10-27T08:00:00Z",
    },)
    assert card.documents == ({
        "id": "DOC-1", "version": "v1", "kind": "PL",
        "title": "Packing List",
    },)
    assert card.quote is None  # 5C: quotation money not exposed.
    assert "250000" not in str(asdict(card))
    assert "SECRET_" not in str(asdict(card))


def test_published_quote_document_has_only_approved_metadata(db):
    _insert_sources(db)
    db.public_documents.insert_one({
        "id": "QUOTE-PDF-1", "version": "v7", "customer_id": CUSTOMER,
        "shipment_id": LOT, "kind": "CUSTOMER_QUOTE",
        "public_title": "Báo giá đã duyệt bản 7",
        "status": "AVAILABLE", "verified": True, "visibility": "CUSTOMER",
        "internal_locator": "INTERNAL_ONLY",
        "selling_total_vnd": 987654321,
    })
    db.customer_publications.update_one({"shipment_id": LOT}, {"$set": {
        "document_versions.QUOTE-PDF-1": "v7",
    }})
    _approve_fixture_content(db)  # re-approve the newly selected document
    card = _view(db).cards[0]
    assert {"id": "QUOTE-PDF-1", "version": "v7", "kind": "CUSTOMER_QUOTE",
            "title": "Báo giá đã duyệt bản 7"} in card.documents
    assert card.quote is None
    assert "INTERNAL_ONLY" not in str(asdict(card))
    assert "987654321" not in str(asdict(card))
    db.customer_publications.update_one({"shipment_id": LOT}, {"$set": {
        "document_versions.QUOTE-PDF-1": "v6",
    }})
    assert _view(db).cards == ()  # changed pin without new approval is rejected


def test_no_manifest_release_keeps_customer_data_empty(db):
    _insert_sources(db)
    db.customer_publications.update_one({"shipment_id": LOT}, {"$set": {
        "event_versions": {}, "document_versions": {}, "quote": {},
    }})
    card = _view(db).cards[0]
    assert card.timeline == () and card.documents == () and card.quote is None


def test_private_unverified_foreign_or_draft_sources_stay_hidden(db):
    _insert_sources(db)
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"verified": False}})
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"visibility": "TT"}})
    db.quotes.update_one({"id": "QT-1"}, {"$set": {"status": "DRAFT"}})
    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": "FOREIGN",
        "shipment_id": LOT, "verified": True,
        "verified_at": "now", "visibility": "CUSTOMER",
        "public_title": "FOREIGN_SECRET", "occurred_at": "now",
    })
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1
    assert "FOREIGN_SECRET" not in str(asdict(view))


def test_unpinned_versions_stay_hidden(db):
    _insert_sources(db)
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"version": "v2"}})
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"version": "v2"}})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_published_quote_pin_does_not_read_internal_quotes(db):
    _insert_sources(db)
    with patch.object(db["quotes"], "find", side_effect=AssertionError("forbidden quotation query")):
        assert _view(db).cards[0].quote is None


def test_invalid_or_duplicate_release_fails_closed(db):
    _insert_sources(db)
    db.public_events.insert_one({
        "id": "EV-1", "version": "v1", "customer_id": CUSTOMER,
        "shipment_id": LOT, "verified": True, "visibility": "CUSTOMER",
        "verified_at": "now", "public_title": "AMBIGUOUS",
        "occurred_at": "2026-10-27T08:00:00Z",
    })
    with pytest.raises(portal.PortalDataError):
        _view(db)
    db.public_events.delete_one({"public_title": "AMBIGUOUS"})
    db.customer_publications.update_one(
        {"shipment_id": LOT}, {"$set": {"event_versions": ["bad"]}},
    )
    with pytest.raises(portal.PortalDataError):
        _view(db)


def test_missing_verification_on_manifest_denies_before_source_read(db):
    _insert_sources(db)
    db.customer_publications.update_one(
        {"shipment_id": LOT}, {"$set": {"approved_at": ""}},
    )
    with patch.object(db["public_events"], "find", side_effect=AssertionError("read not permitted")):
        view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_source_database_failure_uses_generic_error(db, caplog):
    with patch.object(db["public_events"], "find", side_effect=RuntimeError("SECRET_SOURCE")):
        with pytest.raises(portal.PortalDataError):
            _view(db)
    assert "SECRET_SOURCE" not in caplog.text


def test_owner_revocation_blocks_sources(db):
    _insert_sources(db)
    db.customers.update_one({"id": CUSTOMER}, {"$unset": {"portal_access_email": ""}})
    with pytest.raises(portal.PortalAccessDenied):
        _view(db)


def test_pin_maps_are_bounded(db):
    pins = {f"EV-{i}": "v1" for i in range(101)}
    with pytest.raises(PublicSourceUnavailable):
        read_approved_sources(
            db, customer_id=CUSTOMER, shipment_id=LOT,
            shipment_quote_id=None, publication={"event_versions": pins},
        )

def test_same_version_source_mutation_is_never_released(db):
    _insert_sources(db)
    assert _view(db).cards[0].timeline[0]["title"] == "Đã lấy hàng"
    db.public_events.update_one(
        {"id": "EV-1"}, {"$set": {"public_title": "CHANGED_WITHOUT_APPROVAL"}},
    )
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1
    assert "CHANGED_WITHOUT_APPROVAL" not in str(asdict(view))


def test_legacy_source_pins_without_content_hash_fail_closed(db):
    _insert_sources(db)
    db.customer_publications.update_one(
        {"shipment_id": LOT}, {"$unset": {"approved_content_sha256": ""}},
    )
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_internal_fields_not_in_public_projection_do_not_revoke_release(db):
    _insert_sources(db)
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"private_notes": "EDITED"}})
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"storage_file_id": "EDITED"}})
    view = _view(db)
    assert len(view.cards) == 1
    assert "EDITED" not in str(asdict(view))


