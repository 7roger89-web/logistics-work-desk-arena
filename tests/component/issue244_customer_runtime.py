"""Issue #244 customer-side QA runtime — "Hồ sơ Kế hoạch đã công bố".

Isolated QA only: synthetic identities + in-memory ``mongomock`` data. This is
NOT an authentication test and it never touches production.

It publishes ONE lot to customer ``QA-LG`` through the EXISTING publication
allowlist (``core.hexa_customer_publication``) so the browser can prove:

* node 00 shows exactly the published plan documents
  (``CUSTOMER_QUOTE`` / ``CUSTOMER_CONTRACT`` / ``PAYMENT_REQUEST``), metadata
  only: no amount, no storage id, no internal field;
* a published document does NOT complete stage 00 (a published file is not a
  verified event);
* a NON-plan published kind (``BL``), an unpublished PRIVATE contract, a stale
  version and a foreign lot can never appear.

A second lot ``QA-LOT-EMPTY`` is published with no plan document at all, so the
explicit empty wording can be checked too.

Run:
  streamlit run tests/component/issue244_customer_runtime.py --server.port 9502
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import mongomock  # noqa: E402
import streamlit as st  # noqa: E402

from core import customer_portal as portal  # noqa: E402
from core import hexa_customer_publication as publication  # noqa: E402
from views import customer_dashboard  # noqa: E402

LOT = "QA-244-LOT"
EMPTY_LOT = "QA-244-EMPTY"
FOREIGN_LOT = "QA-244-FOREIGN"
CUSTOMER = "QA-244-LG"
OTHER_CUSTOMER = "QA-244-OTHER"
EMAIL = "luagiak244@example.test"
OTHER_EMAIL = "other244@example.test"
VERSION = "v1"
APPROVED_AT = "2026-10-30T08:00:00+00:00"


def _document(doc_id: str, kind: str, title: str, *, shipment_id: str = LOT,
              customer_id: str = CUSTOMER, version: str = VERSION,
              visibility: str = "CUSTOMER", status: str = "AVAILABLE",
              verified: bool = True, **extra) -> dict:
    row = {
        "id": doc_id, "version": version, "customer_id": customer_id,
        "shipment_id": shipment_id, "kind": kind, "public_title": title,
        "status": status, "verified": verified, "visibility": visibility,
    }
    row.update(extra)
    return row


@st.cache_resource
def synthetic_db():
    db = mongomock.MongoClient()["disposable_issue244_qa"]
    db.customers.insert_many([
        {"id": CUSTOMER, "name": "Lục Giác QA 244", "portal_access_email": EMAIL},
        {"id": OTHER_CUSTOMER, "name": "Khách khác QA 244", "portal_access_email": OTHER_EMAIL},
    ])
    db.shipments.insert_many([
        {"id": LOT, "customer_id": CUSTOMER, "transport_mode": "SEA",
         "customer_publication_version": VERSION, "quote_id": "BG-QA-244",
         "internal_cost": 987654321, "internal_notes": "SECRET_INTERNAL_LOT"},
        {"id": EMPTY_LOT, "customer_id": CUSTOMER, "transport_mode": "SEA",
         "customer_publication_version": VERSION},
        {"id": FOREIGN_LOT, "customer_id": OTHER_CUSTOMER, "transport_mode": "SEA",
         "customer_publication_version": VERSION},
    ])
    db.public_events.insert_many([
        # Stage 01 is verified; stage 00 (Kế hoạch) deliberately has NO event:
        # publishing a document must never complete a stage.
        {"id": "QA-244-EV-PICKUP", "version": VERSION, "customer_id": CUSTOMER,
         "shipment_id": LOT, "stage_id": "pickup", "public_title": "Đã lấy hàng tại nhà máy",
         "occurred_at": "2026-10-29T02:00:00Z", "verified": True,
         "verified_at": "2026-10-29T03:00:00Z", "visibility": "CUSTOMER",
         "internal_note": "SECRET_EVENT"},
        {"id": "QA-244-EV-FOREIGN", "version": VERSION, "customer_id": OTHER_CUSTOMER,
         "shipment_id": FOREIGN_LOT, "stage_id": "pickup",
         "public_title": "SECRET_FOREIGN_EVENT", "occurred_at": "2026-10-29T02:00:00Z",
         "verified": True, "verified_at": "2026-10-29T03:00:00Z", "visibility": "CUSTOMER"},
    ])
    documents = [
        # The three allowed plan kinds.
        _document("QA-244-QUOTE", "CUSTOMER_QUOTE", "Báo giá LOGI 0306",
                  amount=385000000, internal_cost=300000000,
                  storage_file_id="SECRET_DRIVE_QUOTE"),
        _document("QA-244-CONTRACT", "CUSTOMER_CONTRACT", "Hợp đồng ủy thác nhập khẩu",
                  margin=85000000, storage_file_id="SECRET_DRIVE_CONTRACT"),
        _document("QA-244-PAYREQ", "PAYMENT_REQUEST", "Đề nghị tạm ứng 50%",
                  amount=192_500_000),
        # Published, but NOT a plan kind.
        _document("QA-244-BL", "BL", "Bill of lading QA"),
        _document("QA-244-BL-EMPTY", "BL", "Bill of lading QA (lô không có hồ sơ kế hoạch)",
                  shipment_id=EMPTY_LOT),
        # Present in the collection but NOT published (private / stale).
        _document("QA-244-PRIVATE", "CUSTOMER_CONTRACT", "SECRET_PRIVATE_CONTRACT",
                  visibility="TT"),
        _document("QA-244-STALE", "CUSTOMER_QUOTE", "SECRET_STALE_QUOTE",
                  version="v0"),
        _document("QA-244-FOREIGN", "CUSTOMER_QUOTE", "SECRET_FOREIGN_QUOTE",
                  shipment_id=FOREIGN_LOT, customer_id=OTHER_CUSTOMER),
    ]
    db.public_documents.insert_many(documents)

    def publish(shipment_id: str, docs: list[dict], events: list[dict]) -> None:
        # The fingerprinted public content includes the published transport mode,
        # so the approval must be computed over the SAME row the portal reads.
        shipment = {"id": shipment_id, "customer_id": CUSTOMER, "transport_mode": "SEA"}
        principal = {"authenticated": True, "kind": "customer", "customer_id": CUSTOMER}
        manifest = {
            "schema": publication.PUBLICATION_SCHEMA,
            "customer_id": CUSTOMER, "shipment_id": shipment_id,
            "version": VERSION, "state": "PUBLISHED",
            "approved_by": "qa.owner", "approved_at": APPROVED_AT,
            "event_versions": {row["id"]: row["version"] for row in events},
            "document_versions": {row["id"]: row["version"] for row in docs},
        }
        public = publication.build_customer_publication(
            shipment=shipment, principal=principal, publication=manifest,
            events=events, documents=docs,
        )
        manifest["approved_content_sha256"] = publication.approved_content_fingerprint(public)
        db[portal.PUBLICATION_COLLECTION].insert_one(manifest)

    publish(
        LOT,
        [row for row in documents if row["shipment_id"] == LOT and row["id"] != "QA-244-STALE"],
        [row for row in db.public_events.find({"shipment_id": LOT}, {"_id": 0})],
    )
    # A published lot carrying ONLY a non-plan document: proves the three-kind
    # filter instead of merely proving an empty list.
    publish(EMPTY_LOT, [row for row in documents if row["id"] == "QA-244-BL-EMPTY"], [])
    return db


st.set_page_config(layout="wide")
st.warning(
    "QA cô lập Issue #244 (khách): danh tính giả lập, dữ liệu mongomock, "
    "không chứng minh OIDC thật và không phải production."
)
db = synthetic_db()
role = st.radio("QA identity (test only)", ["Lục Giác", "Khách khác"], horizontal=True)
email = EMAIL if role == "Lục Giác" else OTHER_EMAIL
principal = portal.build_customer_principal(verified_email=email, db=db)
customer_dashboard.render_customer_dashboard(principal, db=db)
