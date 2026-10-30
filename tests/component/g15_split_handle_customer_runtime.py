"""QA-ONLY split-handle customer harness (capability probe, not product code).

Reproduces the runtime precondition of the historical defect:

* the customer portal is rendered from an INJECTED database handle
  (``render_customer_dashboard(..., db=DB)``), exactly like the QA/staging
  fixture and any host that injects the portal database;
* ``core.database.get_db()`` is NOT configured here (no MONGO_URI), so the
  write path that resolves its own handle lands on nothing.

Under that split, a comment written through the *own* handle is either refused
or stored where the reload never reads it.  Both the PRE worktree (4dd3cb9) and
the FIX worktree (6b95af3) run THIS SAME FILE; only the application code
differs, so a different browser outcome is attributable to the app.

This file lives outside the repository and is loaded with APP_ROOT pointing at
the worktree under test.  No application file is modified.
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

APP_ROOT = Path(os.environ["APP_ROOT"]).resolve()
sys.path.insert(0, str(APP_ROOT))

import mongomock  # noqa: E402
import streamlit as st  # noqa: E402

from core import customer_portal as portal  # noqa: E402
from views import customer_dashboard  # noqa: E402

QA_CUSTOMER = "QA-LG"
QA_OTHER = "QA-OTHER"
QA_EMAIL = "lg@example.test"
QA_OTHER_EMAIL = "other@example.test"
QA_LOT = "QA-LOT"
QA_OTHER_LOT = "QA-FOREIGN"
QA_EVENT_ID = "QA-EVENT-PICKUP"


def _seed(db) -> None:
    db.customers.insert_many([
        {"id": QA_CUSTOMER, "name": "Lục Giác QA", "portal_access_email": QA_EMAIL, "is_deleted": False},
        {"id": QA_OTHER, "name": "Khách khác QA", "portal_access_email": QA_OTHER_EMAIL, "is_deleted": False},
    ])
    scope = {"service_scope": ["ORIGIN_PICKUP", "MAIN_CARRIAGE", "DELIVERY"], "service_scope_confirmed": True}
    db.shipments.insert_many([
        {
            "id": QA_LOT, "customer_id": QA_CUSTOMER, "transport_mode": "SEA",
            "internal_notes": "SECRET_INTERNAL", "cost": 987654321, "is_deleted": False,
            "data": {"0.0": {"execution_profile": copy.deepcopy(scope)}},
        },
        {
            "id": QA_OTHER_LOT, "customer_id": QA_OTHER, "transport_mode": "ROAD",
            "is_deleted": False, "data": {"0.0": {"execution_profile": copy.deepcopy(scope)}},
        },
    ])
    db.public_events.insert_many([
        {
            "id": QA_EVENT_ID, "version": "v1", "customer_id": QA_CUSTOMER, "shipment_id": QA_LOT,
            "stage_id": "pickup", "public_title": "QA Đã lấy hàng",
            "occurred_at": "2026-10-30T01:00:00Z", "verified": True,
            "verified_at": "2026-10-30T02:00:00Z", "visibility": "CUSTOMER",
            "internal_notes": "SECRET_EVENT",
        },
        {
            "id": "QA-FOREIGN-EVENT", "version": "v1", "customer_id": QA_OTHER, "shipment_id": QA_OTHER_LOT,
            "stage_id": "pickup", "public_title": "SECRET_FOREIGN_EVENT",
            "occurred_at": "2026-10-30T01:00:00Z", "verified": True,
            "verified_at": "2026-10-30T02:00:00Z", "visibility": "CUSTOMER",
        },
    ])


def _publish(db) -> None:
    """Publish through the REAL publisher so the lot passes the portal gate."""
    from core import customer_portal_publish as publisher

    if db[portal.PUBLICATION_COLLECTION].find_one(
        {"customer_id": QA_CUSTOMER, "shipment_id": QA_LOT}
    ):
        return
    publisher.publish_verified_sources(
        QA_CUSTOMER, QA_LOT,
        event_versions={QA_EVENT_ID: "v1"}, document_versions={},
        expected_current_version="", actor_role="admin",
        actor_username="qa-fixture-admin", db=db,
    )


@st.cache_resource
def fixture_db():
    db = mongomock.MongoClient()["split_handle_qa"]
    _seed(db)
    _publish(db)
    return db


st.set_page_config(layout="wide")
st.warning(
    "QA cô lập: danh tính giả lập, dữ liệu mongomock, cổng khách dùng handle được inject; "
    "không chứng minh OIDC thật."
)

db = fixture_db()
st.caption(f"SPLIT_HANDLE_QA · APP_ROOT={APP_ROOT} · get_db()={'configured' if os.getenv('MONGO_URI') else 'unconfigured'}")

role = st.radio("QA identity (test only)", ["Lục Giác", "Khách khác"], horizontal=True)

if role == "Lục Giác":
    email = QA_EMAIL
else:
    email = QA_OTHER_EMAIL

principal = portal.build_customer_principal(verified_email=email, db=db)
customer_dashboard.render_customer_dashboard(principal, db=db)
