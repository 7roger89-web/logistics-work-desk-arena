"""Seed synthetic G1 customer-portal data into an EXPLICIT staging database.

No production MongoDB is ever selected: the CLI guard refuses PRODUCTION
identity, the production DB name, a missing URI and a non-allowlisted database.
``seed_staging(db)`` also refuses a database named ``logistics_db``.  All
identifiers and emails use the reserved ``.example`` domain; no trial account
or credential is copied from the HEXA trial server.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from core import config
from core import database
from core.customer_portal import PUBLICATION_COLLECTION
from core.hexa_customer_publication import PUBLICATION_SCHEMA

CUSTOMER_A_ID = "CUST-LUCGIAC"
CUSTOMER_B_ID = "CUST-MINHDUC"
CUSTOMER_A_PORTAL_EMAIL = "portal.lucgiac@example.com"
CUSTOMER_A_CONTACT_EMAIL = "contact.lucgiac@example.com"
CUSTOMER_B_CONTACT_EMAIL = "contact.minhduc@example.com"

LOT_A1 = "G1-LG-001"
LOT_A2 = "G1-LG-002"
LOT_B1 = "G1-MD-001"
LOT_A_DRAFT = "G1-LG-DRAFT"
LOT_MISSING_CUSTOMER = "G1-NO-CUSTOMER"
LOT_NAME_ONLY = "G1-NAME-ONLY"
LOT_UNKNOWN_CUSTOMER = "G1-UNKNOWN-CUSTOMER"

INTERNAL_SENTINELS = (
    "TT_INTERNAL_COST_8451",
    "TT_MARGIN_818",
    "TT_PRIVATE_SUPPLIER_323",
    "TT_INTERNAL_VIEW_MODEL_551",
)
FOREIGN_SENTINEL = "FOREIGN_CUSTOMER_912"

_PRODUCTION_DB_NAMES = frozenset({"logistics_db"})
_STAGING_DB_NAMES = frozenset({"logistics_staging"})


def _publication(shipment_id: str, customer_id: str, version: str, *, state: str = "PUBLISHED") -> dict[str, Any]:
    approved = state == "PUBLISHED"
    return {
        "id": f"{customer_id}:{shipment_id}:{version}",
        "schema": PUBLICATION_SCHEMA,
        "customer_id": customer_id,
        "shipment_id": shipment_id,
        "version": version,
        "state": state,
        "approved_by": "staging-owner" if approved else "",
        "approved_at": "2026-10-24T08:00:00Z" if approved else "",
        "event_versions": {},
        "document_versions": {},
        "quote": {},
        "is_deleted": False,
    }


def build_documents(*, include_negative_cases: bool = True) -> dict[str, list[dict[str, Any]]]:
    """Two published Lục Giác lots plus bounded cross-tenant/data-error fixtures."""
    customers: list[dict[str, Any]] = [
        {
            "id": CUSTOMER_A_ID,
            "name": "Lục Giác",
            "email": CUSTOMER_A_CONTACT_EMAIL,
            "portal_access_email": CUSTOMER_A_PORTAL_EMAIL,
        },
        # Contact email is NOT a portal grant: this customer has no allowlisted
        # email and must remain denied even if the contact email is guessed.
        {
            "id": CUSTOMER_B_ID,
            "name": "Minh Đức",
            "email": CUSTOMER_B_CONTACT_EMAIL,
        },
    ]
    shipments: list[dict[str, Any]] = [
        {
            "id": LOT_A1,
            "customer_id": CUSTOMER_A_ID,
            "customer_publication_version": "v1",
            "transport_mode": "ROAD",
            "internal_cost": INTERNAL_SENTINELS[0],
            "margin": INTERNAL_SENTINELS[1],
            "private_document": INTERNAL_SENTINELS[2],
            "internal_view_model": {"secret": INTERNAL_SENTINELS[3]},
        },
        {
            "id": LOT_A2,
            "customer_id": CUSTOMER_A_ID,
            "customer_publication_version": "v2",
            "transport_mode": "SEA",
            "internal_cost": INTERNAL_SENTINELS[0],
        },
        {
            "id": LOT_B1,
            "customer_id": CUSTOMER_B_ID,
            "customer_publication_version": "v1",
            "transport_mode": "ROAD",
            "private_note": FOREIGN_SENTINEL,
        },
    ]
    publications: list[dict[str, Any]] = [
        _publication(LOT_A1, CUSTOMER_A_ID, "v1"),
        _publication(LOT_A2, CUSTOMER_A_ID, "v2"),
        _publication(LOT_B1, CUSTOMER_B_ID, "v1"),
    ]
    if include_negative_cases:
        shipments.extend([
            {
                "id": LOT_A_DRAFT,
                "customer_id": CUSTOMER_A_ID,
                "customer_publication_version": "v1",
                "transport_mode": "ROAD",
                "internal_cost": INTERNAL_SENTINELS[0],
            },
            # A business name must never substitute for customers.id.
            {
                "id": LOT_MISSING_CUSTOMER,
                "customer_name": "Lục Giác",
                "customer_publication_version": "v1",
                "transport_mode": "ROAD",
                "internal_cost": INTERNAL_SENTINELS[0],
            },
            {
                "id": LOT_NAME_ONLY,
                "customer": "Lục Giác",
                "customer_id": "",
                "customer_publication_version": "v1",
                "transport_mode": "AIR",
            },
            {
                "id": LOT_UNKNOWN_CUSTOMER,
                "customer_id": "CUST-NOT-IN-MASTER",
                "customer_publication_version": "v1",
                "transport_mode": "ROAD",
            },
        ])
        publications.append(_publication(LOT_A_DRAFT, CUSTOMER_A_ID, "v1", state="DRAFT"))
    return {
        "customers": customers,
        "shipments": shipments,
        PUBLICATION_COLLECTION: publications,
    }


def seed_staging(db: Any, *, include_negative_cases: bool = True) -> dict[str, int]:
    """Idempotently replace ONLY the synthetic G1 ids in a staging DB handle."""
    if str(getattr(db, "name", "") or "") in _PRODUCTION_DB_NAMES:
        raise RuntimeError("Refusing to seed a production database.")
    all_documents = build_documents(include_negative_cases=True)
    selected = build_documents(include_negative_cases=include_negative_cases)
    for collection, rows in all_documents.items():
        db[collection].delete_many({"id": {"$in": [row["id"] for row in rows]}})
    counts: dict[str, int] = {}
    for collection, rows in selected.items():
        if rows:
            db[collection].insert_many(rows)
        counts[collection] = len(rows)
    return counts


def staging_target_error(
    *,
    env_identity: str,
    db_name: str,
    uri: str,
    allowed_databases: list[str],
) -> str | None:
    identity = str(env_identity or "").strip().upper()
    name = str(db_name or "").strip()
    if not str(uri or "").strip():
        return "Thiếu MONGO_URI."
    if not name:
        return "Thiếu MONGO_DB_NAME."
    if identity == "PRODUCTION" or name in _PRODUCTION_DB_NAMES:
        return "Từ chối ghi dữ liệu G1 vào production."
    if identity in {"STAGING", "PREVIEW"} and name not in _STAGING_DB_NAMES and name not in allowed_databases:
        return "Tên database không phải staging được phép."
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-staging",
        action="store_true",
        help="Required explicit acknowledgement that the configured DB is staging.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Seed only the two published Lục Giác lots and the foreign-tenant control.",
    )
    args = parser.parse_args(argv)
    if not args.confirm_staging:
        print("Refusing to seed without --confirm-staging.", file=sys.stderr)
        return 2
    error = staging_target_error(
        env_identity=config.ENV_IDENTITY,
        db_name=config.MONGO_DB_NAME,
        uri=config.MONGO_URI,
        allowed_databases=list(config.MONGO_ALLOWED_DB_NAMES),
    )
    if error:
        print(error, file=sys.stderr)
        return 2
    try:
        db = database.get_db()
        counts = seed_staging(db, include_negative_cases=not args.clean)
    except Exception as exc:  # noqa: BLE001 - never print URI/credentials
        print(f"Seed staging thất bại: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(json.dumps({
        "transport": "STAGING",
        "database": config.MONGO_DB_NAME,
        "counts": counts,
        "published_customer": CUSTOMER_A_ID,
        "published_lots": [LOT_A1, LOT_A2],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
