"""G1.5 independent acceptance challenge (reviewer != fix author).

This file is deliberately written from the acceptance contract, not from the
implementation: publish ``E/v1``, then attack the release and prove the
customer never sees unapproved content. It runs on an isolated in-memory Mongo
handle (mongomock) plus the real Streamlit AppTest entrypoint. No production,
Cloud or real customer data is touched.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest

from core import customer_portal as portal
from core import customer_portal_publish as publication
from core.hexa_customer_publication import (
    PUBLICATION_SCHEMA, build_customer_publication, approved_content_fingerprint,
)

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

CUSTOMER_A = "CUST-LUCGIAC"
CUSTOMER_B = "CUST-MINHDUC"
EMAIL_A = "portal.lucgiac@example.com"
EMAIL_B = "portal.minhduc@example.com"
LOT_A = "G1-LG-001"
LOT_B = "G1-MD-001"

EV_1_TITLE = "Đã lấy hàng tại kho Lục Giác"
DOC_1_TITLE = "Packing List đã duyệt"

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


def _claims(email: str):
    return {
        "is_logged_in": True, "provider": "google",
        "aud": FAKE_AUTH["google"]["client_id"], "iss": "https://accounts.google.com",
        "email": email, "email_verified": True,
        "exp": int(time.time()) + 600, "sub": "staging-google-subject",
    }


@pytest.fixture
def db():
    database = mongomock.MongoClient()["g15_independent_challenge"]
    database.customers.insert_many([
        {"id": CUSTOMER_A, "name": "Lục Giác", "portal_access_email": EMAIL_A},
        {"id": CUSTOMER_B, "name": "Minh Đức", "portal_access_email": EMAIL_B},
    ])
    database.shipments.insert_many([
        {"id": LOT_A, "customer_id": CUSTOMER_A, "transport_mode": "SEA",
         "internal_cost": "SECRET_INTERNAL_COST"},
        {"id": LOT_B, "customer_id": CUSTOMER_B, "transport_mode": "ROAD"},
    ])
    database.public_events.insert_many([
        {"id": "EV-1", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
         "stage_id": "pickup", "public_title": EV_1_TITLE,
         "occurred_at": "2026-10-28T01:00:00Z", "verified": True,
         "verified_at": "2026-10-28T02:00:00Z", "visibility": "CUSTOMER",
         "internal_note": "SECRET_EVENT_NOTE"},
        {"id": "EV-2", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
         "stage_id": "customs_import", "public_title": "Đã thông quan nhập",
         "occurred_at": "2026-10-29T01:00:00Z", "verified": True,
         "verified_at": "2026-10-29T02:00:00Z", "visibility": "CUSTOMER"},
    ])
    database.public_documents.insert_many([
        {"id": "DOC-1", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
         "kind": "PL", "public_title": DOC_1_TITLE, "status": "AVAILABLE",
         "verified": True, "visibility": "CUSTOMER",
         "storage_file_id": "SECRET_GRIDFS_ID"},
        {"id": "DOC-2", "version": "v1", "customer_id": CUSTOMER_A, "shipment_id": LOT_A,
         "kind": "BL", "public_title": "Vận đơn đường biển", "status": "AVAILABLE",
         "verified": True, "visibility": "CUSTOMER"},
        {"id": "DOC-9", "version": "v1", "customer_id": CUSTOMER_B, "shipment_id": LOT_B,
         "kind": "PL", "public_title": "Packing list của Minh Đức", "status": "AVAILABLE",
         "verified": True, "visibility": "CUSTOMER"},
    ])
    return database


def _publish(db, *, events=None, docs=None, current="", role="admin", lot=LOT_A,
             customer=CUSTOMER_A, username="staging-admin"):
    return publication.publish_verified_sources(
        customer, lot,
        event_versions={"EV-1": "v1", "EV-2": "v1"} if events is None else events,
        document_versions={"DOC-1": "v1", "DOC-2": "v1"} if docs is None else docs,
        expected_current_version=current, actor_role=role, actor_username=username, db=db,
    )


def _view(db, email=EMAIL_A):
    principal = portal.build_customer_principal(verified_email=email, db=db)
    return portal.load_customer_dashboard(principal, db=db)


def _released(db, lot=LOT_A):
    ok, message = _publish(db, lot=lot)
    assert ok is True, message
    return db.shipments.find_one({"id": lot})["customer_publication_version"]


# --------------------------------------------------------------------------
# 1. The reported blocker: same-version source edit after approval
# --------------------------------------------------------------------------

def test_approved_release_is_visible_and_complete(db):
    _released(db)
    card = _view(db).cards[0]
    assert card.reference == LOT_A
    assert {e["title"] for e in card.timeline} == {EV_1_TITLE, "Đã thông quan nhập"}
    assert {d["title"] for d in card.documents} == {DOC_1_TITLE, "Vận đơn đường biển"}
    payload = json.dumps([dict(e) for e in card.timeline] + [dict(d) for d in card.documents])
    assert "SECRET" not in payload


@pytest.mark.parametrize("collection, record_id, field, value", [
    ("public_events", "EV-1", "public_title", "CHANGED_WITHOUT_APPROVAL"),
    ("public_events", "EV-1", "occurred_at", "2026-11-30T01:00:00Z"),
    ("public_events", "EV-1", "stage_id", "delivered"),
    ("public_documents", "DOC-1", "public_title", "CHANGED_WITHOUT_APPROVAL"),
    ("public_documents", "DOC-1", "kind", "CUSTOMER_QUOTE"),
])
def test_same_version_source_edit_hides_the_whole_card(db, collection, record_id, field, value):
    _released(db)
    db[collection].update_one({"id": record_id}, {"$set": {field: value}})
    view = _view(db)
    assert view.cards == ()
    assert view.denied_lots == 1
    assert "CHANGED_WITHOUT_APPROVAL" not in str(view)


def test_whitespace_only_source_change_is_not_a_new_release(db):
    """Identical visible content must not be revoked by a normalised edit."""
    _released(db)
    db.public_events.update_one(
        {"id": "EV-1"}, {"$set": {"public_title": f"  {EV_1_TITLE}  "}})
    view = _view(db)
    assert len(view.cards) == 1 and view.denied_lots == 0
    assert {e["title"] for e in view.cards[0].timeline} == {EV_1_TITLE, "Đã thông quan nhập"}


def test_swapping_content_between_two_approved_events_is_detected(db):
    _released(db)
    first = db.public_events.find_one({"id": "EV-1"})["public_title"]
    second = db.public_events.find_one({"id": "EV-2"})["public_title"]
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"public_title": second}})
    db.public_events.update_one({"id": "EV-2"}, {"$set": {"public_title": first}})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_deleting_an_approved_source_denies_the_card(db):
    _released(db)
    db.public_events.delete_one({"id": "EV-2"})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_changing_transport_mode_after_approval_denies_the_card(db):
    _released(db)
    db.shipments.update_one({"id": LOT_A}, {"$set": {"transport_mode": "ROAD"}})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_revoking_source_verification_or_visibility_denies_the_card(db):
    _released(db)
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"visibility": "TT"}})
    assert _view(db).cards == ()
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"visibility": "CUSTOMER"}})
    assert len(_view(db).cards) == 1
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"status": "PENDING"}})
    assert _view(db).cards == ()
    db.public_documents.update_one({"id": "DOC-1"}, {"$set": {"status": "AVAILABLE"}})
    db.public_events.update_one({"id": "EV-1"}, {"$set": {"verified": False}})
    assert _view(db).cards == ()


def test_adding_a_new_pin_without_reapproval_denies_the_card(db):
    ok, _ = _publish(db, events={"EV-1": "v1"}, docs={"DOC-1": "v1"})
    assert ok
    manifest = db.customer_publications.find_one(
        {"shipment_id": LOT_A, "version": db.shipments.find_one({"id": LOT_A})[
            "customer_publication_version"]})
    db.customer_publications.update_one(
        {"_id": manifest["_id"]}, {"$set": {"event_versions.EV-2": "v1"}})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


# --------------------------------------------------------------------------
# 2. Hash integrity attacks
# --------------------------------------------------------------------------

def test_missing_hash_on_a_pinned_manifest_denies_the_card(db):
    _released(db)
    db.customer_publications.update_one(
        {"shipment_id": LOT_A}, {"$unset": {"approved_content_sha256": ""}})
    view = _view(db)
    assert view.cards == () and view.denied_lots == 1


def test_forged_hash_of_an_attacker_projection_is_still_denied(db):
    _released(db)
    db.public_events.update_one(
        {"id": "EV-1"}, {"$set": {"public_title": "CHANGED_WITHOUT_APPROVAL"}})
    forged = build_customer_publication(
        shipment={"id": LOT_A, "customer_id": CUSTOMER_A, "transport_mode": "SEA"},
        principal={"kind": "customer", "authenticated": True, "customer_id": CUSTOMER_A},
        publication={"schema": PUBLICATION_SCHEMA, "customer_id": CUSTOMER_A,
                     "shipment_id": LOT_A, "version": "v1", "state": "PUBLISHED",
                     "approved_by": "staging-admin", "approved_at": "now",
                     "event_versions": {"EV-1": "v1"}, "document_versions": {}},
        events=[{"id": "EV-1", "version": "v1", "customer_id": CUSTOMER_A,
                 "shipment_id": LOT_A, "stage_id": "pickup",
                 "public_title": "CHANGED_WITHOUT_APPROVAL",
                 "occurred_at": "2026-10-28T01:00:00Z", "verified": True,
                 "verified_at": "2026-10-28T02:00:00Z", "visibility": "CUSTOMER"}],
        documents=[],
    )
    db.customer_publications.update_one(
        {"shipment_id": LOT_A},
        {"$set": {"approved_content_sha256": approved_content_fingerprint(forged)}})
    view = _view(db)
    assert view.cards == ()
    assert "CHANGED_WITHOUT_APPROVAL" not in str(view)


def test_hash_copied_from_another_lot_does_not_authorise_this_lot(db):
    version_a = _released(db, lot=LOT_A)
    manifest_a = db.customer_publications.find_one({"shipment_id": LOT_A, "version": version_a})
    # Reuse the approved digest on a second lot that approved identical content.
    ok, message = _publish(db, lot=LOT_B, customer=CUSTOMER_B,
                           events={}, docs={"DOC-9": "v1"})
    assert ok, message
    version_b = db.shipments.find_one({"id": LOT_B})["customer_publication_version"]
    db.customer_publications.update_one(
        {"shipment_id": LOT_B, "version": version_b},
        {"$set": {"approved_content_sha256": manifest_a["approved_content_sha256"]}})
    view = portal.load_customer_dashboard(
        portal.build_customer_principal(verified_email=EMAIL_B, db=db), db=db)
    assert view.cards == () and view.denied_lots == 1


def test_unpinned_legacy_release_shows_nothing_and_is_not_denied(db):
    db.customer_publications.insert_one({
        "id": f"{CUSTOMER_A}:{LOT_A}:legacy", "schema": PUBLICATION_SCHEMA,
        "customer_id": CUSTOMER_A, "shipment_id": LOT_A, "version": "legacy",
        "state": "PUBLISHED", "approved_by": "staging-owner",
        "approved_at": "2026-10-24T08:00:00Z",
        "event_versions": {}, "document_versions": {},
    })
    db.shipments.update_one(
        {"id": LOT_A}, {"$set": {"customer_publication_version": "legacy"}})
    view = _view(db)
    assert len(view.cards) == 1
    assert view.cards[0].timeline == () and view.cards[0].documents == ()


def test_repeated_reads_of_an_unchanged_release_stay_visible(db):
    _released(db)
    for _ in range(3):
        view = _view(db)
        assert len(view.cards) == 1 and view.denied_lots == 0


# --------------------------------------------------------------------------
# 3. Tenant boundary, roles and writes
# --------------------------------------------------------------------------

def test_other_customer_never_sees_the_lot(db):
    _released(db)
    view = _view(db, email=EMAIL_B)
    # B's own unpublished lot is denied, but nothing of A crosses over.
    assert view.cards == ()
    assert view.denied_lots == 1  # B's lot has no approved release
    text = str(view)
    assert LOT_A not in text and EV_1_TITLE not in text and DOC_1_TITLE not in text


def test_foreign_principal_cannot_read_a_pinned_manifest_of_another_customer(db):
    _released(db)
    manifest = db.customer_publications.find_one({"shipment_id": LOT_A})
    with pytest.raises(PermissionError):
        build_customer_publication(
            shipment={"id": LOT_A, "customer_id": CUSTOMER_A},
            principal={"kind": "customer", "authenticated": True, "customer_id": CUSTOMER_B},
            publication=manifest,
        )


@pytest.mark.parametrize("role", ["viewer", "sale", "support", "operations", "", None])
def test_non_admin_backend_write_is_refused(db, role):
    with pytest.raises(publication.PublicationWriteDenied):
        _publish(db, role=role)
    assert db.customer_publications.count_documents({}) == 0
    assert db.shipments.find_one({"id": LOT_A}).get("customer_publication_version") is None


def test_viewer_cannot_overwrite_an_existing_release(db):
    current = _released(db)
    manifests_before = list(db.customer_publications.find().sort("id", 1))
    with pytest.raises(publication.PublicationWriteDenied):
        _publish(db, role="viewer", current=current, events={"EV-1": "v1"}, docs={})
    assert db.shipments.find_one({"id": LOT_A})["customer_publication_version"] == current
    assert list(db.customer_publications.find().sort("id", 1)) == manifests_before


def test_admin_cannot_publish_another_customers_lot(db):
    with pytest.raises(publication.PublicationWriteDenied):
        _publish(db, lot=LOT_B, events={}, docs={"DOC-9": "v1"})
    assert db.customer_publications.count_documents({}) == 0


# --------------------------------------------------------------------------
# 4. Runtime: reload, tenant switch and document rendering (real Streamlit)
# --------------------------------------------------------------------------

def _model(app):
    assert not app.exception, [str(element.value) for element in app.exception]
    components = app.get("bidi_component")
    assert len(components) == 1, f"expected one mounted portal, got {len(components)}"
    return json.loads(components[0].proto.json)["model"]


def _app(db, email):
    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.secrets = {"auth": FAKE_AUTH}
    return app


def test_customer_sees_approved_timeline_and_documents_then_nothing_after_mutation(db):
    _released(db)
    app = _app(db, EMAIL_A)
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(EMAIL_A)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        payload = _model(app)
        lots = payload["lots"]
        assert len(lots) == 1 and lots[0]["shipment_id"] == LOT_A
        assert EV_1_TITLE in json.dumps(lots, ensure_ascii=False)
        assert DOC_1_TITLE in json.dumps(lots, ensure_ascii=False)
        assert "SECRET" not in json.dumps(payload, ensure_ascii=False)
        # A plain reload is stable while nothing changed.
        app.run()
        assert _model(app)["lots"] == lots
        # Trường Thành edits an approved source without a new version.
        db.public_events.update_one(
            {"id": "EV-1"}, {"$set": {"public_title": "CHANGED_WITHOUT_APPROVAL"}})
        app.run()
        after = _model(app)
    assert after["lots"] == []
    text_after = json.dumps(after, ensure_ascii=False)
    assert "CHANGED_WITHOUT_APPROVAL" not in text_after
    assert EV_1_TITLE not in text_after and DOC_1_TITLE not in text_after


def test_switching_customer_on_the_same_component_resets_the_payload(db):
    _released(db)
    ok, message = _publish(db, lot=LOT_B, customer=CUSTOMER_B, events={}, docs={"DOC-9": "v1"})
    assert ok, message
    app = _app(db, EMAIL_A)
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(EMAIL_A)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        payload_a = _model(app)
    assert [lot["shipment_id"] for lot in payload_a["lots"]] == [LOT_A]
    assert payload_a["customer"]["name"] == "Lục Giác"
    # Same component instance, different principal after a session switch.
    with (
        patch("streamlit.user_info._get_user_info", return_value=_claims(EMAIL_B)),
        patch.object(portal, "get_db", return_value=db),
    ):
        app.run()
        payload_b = _model(app)
    assert [lot["shipment_id"] for lot in payload_b["lots"]] == [LOT_B]
    assert payload_b["customer"]["name"] == "Minh Đức"
    text_b = json.dumps(payload_b, ensure_ascii=False)
    assert LOT_A not in text_b and EV_1_TITLE not in text_b and DOC_1_TITLE not in text_b
