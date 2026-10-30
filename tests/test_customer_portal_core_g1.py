"""G1 customer portal server-side trust boundary tests (staging fixtures)."""
from __future__ import annotations

import importlib.util
import inspect
import json
import logging
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest

from core import customer_portal as cp
from core.hexa_customer_publication import PUBLICATION_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "scripts" / "seed_customer_portal_staging.py"


@pytest.fixture(scope="module")
def seed_module():
    spec = importlib.util.spec_from_file_location("seed_customer_portal_staging", SEED_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def db(seed_module):
    database = mongomock.MongoClient()["g1_customer_portal_test"]
    seed_module.seed_staging(database)
    return database


def _refs(database, email, seed_module):
    principal = cp.build_customer_principal(verified_email=email, db=database)
    return [card.reference for card in cp.load_customer_dashboard(principal, db=database).cards]


def test_single_principal_path_has_no_browser_customer_id(seed_module, db):
    signature = inspect.signature(cp.build_customer_principal)
    assert set(signature.parameters) == {"verified_email", "db"}
    assert "customer_id" not in signature.parameters
    principal = cp.build_customer_principal(
        verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
    )
    assert principal.customer_id == seed_module.CUSTOMER_A_ID
    assert principal.publication_principal() == {
        "authenticated": True,
        "kind": "customer",
        "customer_id": seed_module.CUSTOMER_A_ID,
    }


def test_contact_and_unknown_email_are_not_portal_grants(seed_module, db):
    for email in (
        seed_module.CUSTOMER_A_CONTACT_EMAIL,
        seed_module.CUSTOMER_B_CONTACT_EMAIL,
        "nobody@example.com",
        "not-an-email",
        "",
    ):
        with pytest.raises(cp.PortalAccessDenied):
            cp.build_customer_principal(verified_email=email, db=db)


def test_duplicate_allowlisted_email_fails_closed(seed_module, db, caplog):
    db.customers.update_one(
        {"id": seed_module.CUSTOMER_B_ID},
        {"$set": {cp.PORTAL_ACCESS_EMAIL_FIELD: seed_module.CUSTOMER_A_PORTAL_EMAIL}},
    )
    with caplog.at_level(logging.WARNING, logger="logistics.customer_portal"):
        with pytest.raises(cp.PortalAccessDenied):
            cp.build_customer_principal(
                verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
            )
    assert "email_not_unique_or_not_allowed" in caplog.text


def test_dashboard_returns_only_own_published_lots(seed_module, db):
    principal = cp.build_customer_principal(
        verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
    )
    view = cp.load_customer_dashboard(principal, db=db)
    rendered = json.dumps(asdict(view), ensure_ascii=False)
    assert [card.reference for card in view.cards] == [seed_module.LOT_A1, seed_module.LOT_A2]
    assert view.denied_lots == 1  # DRAFT lot is rejected without showing its content
    assert view.data_issues == 0  # foreign or unowned lots cannot affect this customer
    for sentinel in seed_module.INTERNAL_SENTINELS + (seed_module.FOREIGN_SENTINEL,):
        assert sentinel not in rendered
    assert seed_module.LOT_B1 not in rendered
    assert seed_module.LOT_A_DRAFT not in rendered
    assert "internal_view_model" not in rendered
    assert "cost" not in {field for card in view.cards for field in asdict(card)}
    assert "margin" not in {field for card in view.cards for field in asdict(card)}


def test_unowned_shipment_is_not_matched_by_customer_name(seed_module, db):
    principal = cp.build_customer_principal(
        verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
    )
    view = cp.load_customer_dashboard(principal, db=db)
    references = {card.reference for card in view.cards}
    assert seed_module.LOT_MISSING_CUSTOMER not in references
    assert seed_module.LOT_NAME_ONLY not in references
    assert seed_module.LOT_UNKNOWN_CUSTOMER not in references
    assert view.data_issues == 0


def test_foreign_data_errors_do_not_change_customer_dashboard(seed_module, db):
    principal = cp.build_customer_principal(
        verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
    )
    before = cp.load_customer_dashboard(principal, db=db)
    assert before.data_issues == 0
    # Another client's invalid ownership must not trigger this client's warning.
    db.shipments.insert_many([
        {"id": "G1-FOREIGN-UNKNOWN", "customer_id": "MISSING-CUSTOMER"},
        {"id": "G1-UNOWNED-OTHER", "client": seed_module.CUSTOMER_A_ID},
    ])
    after = cp.load_customer_dashboard(principal, db=db)
    assert after == before
    assert after.data_issues == 0


@pytest.mark.parametrize(
    "mutation",
    [
        {"state": "DRAFT"},
        {"customer_id": "CUST-MINHDUC"},
        {"shipment_id": "G1-GUESSED"},
        {"version": "v9"},
        {"approved_by": ""},
        {"approved_at": ""},
        {"schema": "wrong-schema/v0"},
    ],
)
def test_manifest_must_be_published_approved_pinned_and_same_tenant(
    seed_module, db, mutation
):
    db[cp.PUBLICATION_COLLECTION].update_one(
        {"shipment_id": seed_module.LOT_A1, "schema": PUBLICATION_SCHEMA},
        {"$set": mutation},
    )
    refs = _refs(db, seed_module.CUSTOMER_A_PORTAL_EMAIL, seed_module)
    assert seed_module.LOT_A1 not in refs
    assert seed_module.LOT_A2 in refs


def test_shipment_pinned_version_mismatch_is_rejected(seed_module, db):
    db.shipments.update_one(
        {"id": seed_module.LOT_A1},
        {"$set": {"customer_publication_version": "v9"}},
    )
    refs = _refs(db, seed_module.CUSTOMER_A_PORTAL_EMAIL, seed_module)
    assert seed_module.LOT_A1 not in refs
    assert seed_module.LOT_A2 in refs


def test_customer_b_principal_cannot_see_customer_a_data(seed_module, db):
    ok, _ = cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_B_ID,
        "portal.minhduc@example.com",
        actor_role="admin",
        db=db,
    )
    assert ok is True
    principal = cp.build_customer_principal(
        verified_email="portal.minhduc@example.com", db=db
    )
    view = cp.load_customer_dashboard(principal, db=db)
    rendered = json.dumps(asdict(view), ensure_ascii=False)
    assert [card.reference for card in view.cards] == [seed_module.LOT_B1]
    assert seed_module.LOT_A1 not in rendered
    assert seed_module.LOT_A2 not in rendered
    for sentinel in seed_module.INTERNAL_SENTINELS:
        assert sentinel not in rendered


def test_owner_setter_is_admin_only_default_deny_and_revocable(seed_module, db):
    ok, message = cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_B_ID,
        "portal.minhduc@example.com",
        actor_role="support",
        db=db,
    )
    assert ok is False and "Owner/Admin" in message
    customer_b = db.customers.find_one({"id": seed_module.CUSTOMER_B_ID})
    assert cp.PORTAL_ACCESS_EMAIL_FIELD not in customer_b

    ok, _ = cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_B_ID,
        "  PORTAL.MinhDuc@Example.com  ",
        actor_role="admin",
        db=db,
    )
    assert ok is True
    customer_b = db.customers.find_one({"id": seed_module.CUSTOMER_B_ID})
    assert customer_b[cp.PORTAL_ACCESS_EMAIL_FIELD] == "portal.minhduc@example.com"

    ok, _ = cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_A_ID,
        "portal.minhduc@example.com",
        actor_role="admin",
        db=db,
    )
    assert ok is False  # duplicate allowlist is rejected

    ok, _ = cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_B_ID, "", actor_role="admin", db=db
    )
    assert ok is True
    assert cp.PORTAL_ACCESS_EMAIL_FIELD not in db.customers.find_one(
        {"id": seed_module.CUSTOMER_B_ID}
    )
    with pytest.raises(cp.PortalAccessDenied):
        cp.build_customer_principal(
            verified_email="portal.minhduc@example.com", db=db
        )


def test_refresh_after_owner_revocation_denies_principal(seed_module, db):
    principal = cp.build_customer_principal(
        verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL, db=db
    )
    cp.set_customer_portal_access_email(
        seed_module.CUSTOMER_A_ID, "", actor_role="admin", db=db
    )
    with pytest.raises(cp.PortalAccessDenied):
        cp.load_customer_dashboard(principal, db=db)


def test_no_lots_state(seed_module, db):
    db.customers.insert_one({
        "id": "CUST-EMPTY",
        "name": "Khách không có lô",
        cp.PORTAL_ACCESS_EMAIL_FIELD: "portal.empty@example.com",
    })
    principal = cp.build_customer_principal(
        verified_email="portal.empty@example.com", db=db
    )
    view = cp.load_customer_dashboard(principal, db=db)
    assert view.no_lots is True
    assert view.cards == ()


def test_database_failure_fails_closed(seed_module):
    with patch.object(cp, "get_db", side_effect=RuntimeError("identity failure")):
        with pytest.raises(cp.PortalDataError):
            cp.build_customer_principal(
                verified_email=seed_module.CUSTOMER_A_PORTAL_EMAIL
            )


def test_staging_seed_refuses_production(seed_module):
    assert seed_module.staging_target_error(
        env_identity="PRODUCTION",
        db_name="logistics_db",
        uri="mongodb://example.invalid/db",
        allowed_databases=["logistics_db"],
    )
    assert seed_module.staging_target_error(
        env_identity="STAGING",
        db_name="logistics_workdesk_logc14",
        uri="",
        allowed_databases=["logistics_workdesk_logc14"],
    )
    assert seed_module.staging_target_error(
        env_identity="STAGING",
        db_name="logistics_staging",
        uri="mongodb://example.invalid/logistics_staging",
        allowed_databases=[],
    ) is None
    with pytest.raises(RuntimeError):
        seed_module.seed_staging(mongomock.MongoClient()["logistics_db"])


def test_customer_modules_have_no_browser_identity_or_url_id_path():
    sources = [
        ROOT / "core" / "customer_portal.py",
        ROOT / "core" / "customer_portal_oidc.py",
        ROOT / "views" / "customer_dashboard.py",
        ROOT / "views" / "web_app.py",
    ]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert "st.query_params" not in text
        assert "get_query_params" not in text
        assert "experimental_get_query_params" not in text
        assert 'session_state.get("customer_id")' not in text
        assert 'session_state["customer_id"]' not in text
