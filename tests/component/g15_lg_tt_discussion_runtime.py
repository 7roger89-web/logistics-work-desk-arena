"""QA cô lập: Lục Giác (khách) ↔ Trường Thành (nội bộ) trên MỘT database.

Mục đích: kiểm chứng luồng "khách gửi bình luận ngay trong node Journey Map →
server lưu đúng lô/công đoạn → reload vẫn còn → Trường Thành đọc và trả lời →
khách đọc được câu trả lời" bằng trình duyệt thật, trên dữ liệu giả lập.

Ranh giới trung thực:

* Danh tính KHÔNG phải OIDC thật: đây là fixture QA, không chứng minh đăng nhập
  Google. Mọi kiểm tra tenant/quyền phía server vẫn chạy thật.
* Database là ``mongomock`` trong tiến trình (transport staging cô lập của
  ``views.logi_sandbox``), không phải MongoDB/Drive production.
* Cả hai cổng dùng CHUNG một handle database, đúng như runtime thật nơi
  ``core.database.get_db()`` là database mà cả hai cổng đọc/ghi.

Chạy::

    streamlit run tests/component/g15_lg_tt_discussion_runtime.py --server.port 9503
"""
import copy
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from core import customer_portal as portal
from views import customer_dashboard, logi_sandbox, logi_shell, logi_view_model

QA_CUSTOMER = "QA-LG"
QA_OTHER = "QA-OTHER"
QA_EMAIL = "lg@example.test"
QA_OTHER_EMAIL = "other@example.test"
QA_LOT = "QA-LOT"
QA_OTHER_LOT = "QA-FOREIGN"
QA_EVENT_ID = "QA-EVENT-PICKUP"

#: Fixture staff identity — the internal operator who answers in this QA run.
#: This account is seeded into the canonical ``users`` store and logs in through
#: the REAL password form (AUTH_REQUIRED=true), so every callback revalidates
#: against the same store a production operator would.
TRUONG_THANH = {
    "username": "truong.thanh",
    "display_name": "Trường Thành (QA)",
    "role": "admin",
}
QA_PASSWORD = os.environ.get("QA_TEST_PASSWORD", "")


def _bootstrap() -> object:
    """ONE isolated mongomock database, seeded through the real staging seed."""
    from core.database import get_db

    logi_sandbox.ensure_backend()
    database = get_db()
    if database is None:  # pragma: no cover - registration failure is loud
        raise RuntimeError("QA database unavailable")

    database.customers.update_one(
        {"id": QA_CUSTOMER},
        {"$set": {
            "id": QA_CUSTOMER, "name": "Lục Giác QA",
            "portal_access_email": QA_EMAIL, "is_deleted": False,
        }},
        upsert=True,
    )
    database.customers.update_one(
        {"id": QA_OTHER},
        {"$set": {
            "id": QA_OTHER, "name": "Khách khác QA",
            "portal_access_email": QA_OTHER_EMAIL, "is_deleted": False,
        }},
        upsert=True,
    )

    # The QA lot inherits the real seeded shipment shape, so the Journey Map has
    # genuine nodes (pickup included) and the internal shell can project it.
    if not database.shipments.find_one({"id": QA_LOT}):
        template = database.shipments.find_one({"is_deleted": {"$ne": True}}) or {}
        lot = copy.deepcopy(template)
        lot.pop("_id", None)
        lot.update({
            "id": QA_LOT, "customer_id": QA_CUSTOMER,
            "internal_notes": "SECRET_INTERNAL_QA_LOT", "cost": 987654321,
            "is_deleted": False,
        })
        # The lot is operated by Trường Thành from pickup onwards, so the
        # internal Journey Map really renders the `pickup` node the customer
        # opens. Nothing is fabricated at render time: this IS the shipment's
        # confirmed service scope.
        data = lot.setdefault("data", {})
        head = data.setdefault("0.0", {})
        profile = head.setdefault("execution_profile", {})
        profile["service_scope"] = ["ORIGIN_PICKUP", "MAIN_CARRIAGE", "DELIVERY"]
        profile["service_scope_confirmed"] = True
        database.shipments.insert_one(lot)

    if not database.shipments.find_one({"id": QA_OTHER_LOT}):
        other = copy.deepcopy(lot)
        other.pop("_id", None)
        other.update({"id": QA_OTHER_LOT, "customer_id": QA_OTHER})
        database.shipments.insert_one(other)

    if not QA_PASSWORD:
        raise RuntimeError("QA_TEST_PASSWORD is required for the fixture staff login")
    from core.users import build_user_document

    if database.users.find_one({"username": TRUONG_THANH["username"]}) is None:
        database.users.insert_one(build_user_document(
            TRUONG_THANH["username"], QA_PASSWORD,
            TRUONG_THANH["display_name"], TRUONG_THANH["role"],
        ))

    if not database.public_events.find_one({"id": QA_EVENT_ID}):
        database.public_events.insert_one({
            "id": QA_EVENT_ID, "version": "v1",
            "customer_id": QA_CUSTOMER, "shipment_id": QA_LOT, "stage_id": "pickup",
            "public_title": "QA Đã lấy hàng",
            "occurred_at": "2026-10-30T01:00:00Z", "verified": True,
            "verified_at": "2026-10-30T02:00:00Z", "visibility": "CUSTOMER",
            "internal_notes": "SECRET_EVENT",
        })
    return database


@st.cache_resource
def qa_database():
    return _bootstrap()


def _ensure_published(database) -> None:
    """Publish the pickup milestone for QA-LOT through the REAL publisher."""
    from core import customer_portal_publish as publisher

    existing = database[portal.PUBLICATION_COLLECTION].find_one(
        {"customer_id": QA_CUSTOMER, "shipment_id": QA_LOT}
    )
    if existing:
        return
    publisher.publish_verified_sources(
        QA_CUSTOMER, QA_LOT,
        event_versions={QA_EVENT_ID: "v1"}, document_versions={},
        expected_current_version="", actor_role="admin",
        actor_username="qa-fixture-admin", db=database,
    )


st.set_page_config(layout="wide")
st.warning(
    "QA cô lập: danh tính giả lập trong fixture, dữ liệu mongomock dùng chung, "
    "không chứng minh đăng nhập OIDC thật."
)

db = qa_database()
_ensure_published(db)

role = st.radio(
    "QA identity (test only)",
    ["Trường Thành (nội bộ)", "Lục Giác", "Khách khác"],
    horizontal=True,
)

if role == "Trường Thành (nội bộ)":
    # REAL login: the fixture account exists in the canonical users store, so
    # require_login() (and every later callback revalidation) is the production
    # path — no session identity is injected by this harness.
    from core.auth import require_login

    user = require_login()
    if user is None:
        st.stop()
    st.caption(
        f"Đang đăng nhập nội bộ: {user.get('display_name')} · "
        f"{str(user.get('role', '')).upper()} (fixture QA)"
    )
    logi_shell.render(logi_view_model.build_view_model())
else:
    email = QA_EMAIL if role == "Lục Giác" else QA_OTHER_EMAIL
    principal = portal.build_customer_principal(verified_email=email, db=db)
    customer_dashboard.render_customer_dashboard(principal, db=db)
