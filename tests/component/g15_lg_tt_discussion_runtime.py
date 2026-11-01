"""QA cô lập: Lục Giác (khách) ↔ Trường Thành (nội bộ) trên MỘT database.

Mục đích: kiểm chứng luồng "khách gửi bình luận ngay trong node Journey Map →
server lưu đúng lô/công đoạn → reload vẫn còn → Trường Thành đọc và trả lời →
khách đọc được câu trả lời" bằng trình duyệt thật, trên dữ liệu giả lập.

Issue #247 / S3 bổ sung **ranh giới tenant A/B trong cùng một tiến trình và
cùng một handle database**: hai khách A/B đều có bản công bố RIÊNG do
``core.customer_portal_publish.publish_verified_sources`` (actor ``admin``) tạo
ra, với mốc/chứng từ đã xác minh riêng và version pin riêng. Trình duyệt đổi
A → B → A; mỗi khách chỉ được thấy lô, mốc, chứng từ, bản công bố và bình luận
của chính mình. Danh tính không được cấp quyền bị ``build_customer_principal``
từ chối ở phía server.

Ranh giới trung thực:

* Danh tính KHÔNG phải OIDC thật: đây là fixture QA, không chứng minh đăng nhập
  Google. Mọi kiểm tra tenant/quyền phía server vẫn chạy thật.
* Radio chỉ chọn một **email cố định đã được cấp trong TEST**; không có
  ``customer_id`` nào do trình duyệt gửi lên và không có principal nào được
  dựng từ dữ liệu trình duyệt.
* Database là ``mongomock`` trong tiến trình (transport staging cô lập của
  ``views.logi_sandbox``), không phải MongoDB/Drive production.
* Cả hai cổng dùng CHUNG một handle database, đúng như runtime thật nơi
  ``core.database.get_db()`` là database mà cả hai cổng đọc/ghi.
* ``S3_EVIDENCE_DIR`` (tuỳ chọn) chỉ ghi readback JSON phục vụ nghiệm thu; giá
  trị nội bộ (cost, ghi chú INTERNAL) không bao giờ được ghi ra, chỉ ghi việc
  chúng **vắng mặt** trong payload.

Chạy::

    streamlit run tests/component/g15_lg_tt_discussion_runtime.py --server.port 9503
"""
import copy
import hashlib
import json
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
#: Verified email that is NOT on the Owner allowlist (no portal_access_email).
QA_DENIED_EMAIL = "nobody@example.test"
QA_LOT = "QA-LOT"
QA_OTHER_LOT = "QA-FOREIGN"
QA_EVENT_ID = "QA-EVENT-PICKUP"
QA_OTHER_EVENT_ID = "QA-OTHER-EVENT-PICKUP"

#: Distinct, synthetic public titles so a browser text assertion can tell the two
#: customers apart without guessing from an id.
QA_EVENT_TITLE = "QA-A Đã lấy hàng tại kho Lục Giác"
QA_OTHER_EVENT_TITLE = "QA-B Đã lấy hàng tại kho khách khác"

#: Published documents: A has ONE, B has TWO, so the rendered document count is
#: itself a positive control that B's own release (not A's) produced the view.
QA_DOC_ID = "QA-DOC-PL-A"
QA_DOC_TITLE = "QA-A Packing list"
QA_OTHER_DOC_IDS = ("QA-OTHER-DOC-BL", "QA-OTHER-DOC-POD")
QA_OTHER_DOC_TITLES = ("QA-B Bill of lading", "QA-B Biên bản giao hàng")

#: Sources that must NEVER be publishable/visible: INTERNAL visibility and an
#: unverified record on the SAME lot/customer as a valid release.
QA_PRIVATE_DOC_ID = "QA-PRIVATE-DOC-A"
QA_UNVERIFIED_DOC_ID = "QA-UNVERIFIED-DOC-A"

#: Internal-only markers. They exist in the TEST database and must be absent
#: from every component payload and every browser DOM.
SECRET_LOT_NOTE = "SECRET_INTERNAL_QA_LOT"
SECRET_OTHER_LOT_NOTE = "SECRET_INTERNAL_QA_OTHER_LOT"
SECRET_EVENT_NOTE = "SECRET_EVENT_A"
SECRET_OTHER_EVENT_NOTE = "SECRET_EVENT_B"
SECRET_COST_A = 987654321
SECRET_COST_B = 123456789

QA_MODES = {QA_LOT: "SEA", QA_OTHER_LOT: "ROAD"}

READBACK: dict[str, dict] = {}

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

EVIDENCE_DIR = os.environ.get("S3_EVIDENCE_DIR", "").strip()


def _evidence_dir() -> Path | None:
    if not EVIDENCE_DIR:
        return None
    path = Path(EVIDENCE_DIR).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_evidence(name: str, payload: object) -> None:
    """Atomic evidence write; a QA page must never crash because of it."""
    directory = _evidence_dir()
    if directory is None:
        return
    try:
        text = json.dumps(payload, ensure_ascii=False, default=str, indent=2) + "\n"
        temp = directory / (name + ".tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(directory / name)
    except Exception:  # noqa: BLE001 - evidence is observability only
        pass


def _mask(email: str) -> str:
    value = str(email or "")
    if "@" not in value:
        return "***"
    local, _, domain = value.partition("@")
    head = local[:2] if len(local) > 2 else local[:1]
    return f"{head}***@{domain}"


def _digest(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:12]


def _db_identity(database) -> dict:
    from core import config

    return {
        "pid": os.getpid(),
        "database": getattr(database, "name", "UNKNOWN"),
        "client_module": type(database.client).__module__,
        "client_object_id": id(database.client),
        "database_object_id": id(database),
        "transport": logi_sandbox.transport_name(),
        "mongo_uri_env": os.environ.get("MONGO_URI", ""),
        "config_mongo_uri": str(getattr(config, "MONGO_URI", "")),
        "env_identity": str(getattr(config, "ENV_IDENTITY", "")),
        "auth_required": bool(getattr(config, "AUTH_REQUIRED", False)),
        "streamlit_version": getattr(st, "__version__", ""),
    }


# --------------------------------------------------------------------------- #
# fixture data — ONE isolated mongomock database, seeded through the real seed
# --------------------------------------------------------------------------- #

def _seed_lot(database, template, *, lot_id, customer_id, note, cost, mode):
    if database.shipments.find_one({"id": lot_id}):
        return
    lot = copy.deepcopy(template)
    lot.pop("_id", None)
    lot.update({
        "id": lot_id,
        "customer_id": customer_id,
        "internal_notes": note,
        "cost": cost,
        "transport_mode": mode,
        "is_deleted": False,
    })
    # The lot is operated by Trường Thành from pickup onwards, so the internal
    # Journey Map really renders the `pickup` node the customer opens. Nothing
    # is fabricated at render time: this IS the shipment's confirmed scope.
    data = lot.setdefault("data", {})
    head = data.setdefault("0.0", {})
    profile = head.setdefault("execution_profile", {})
    profile["service_scope"] = ["ORIGIN_PICKUP", "MAIN_CARRIAGE", "DELIVERY"]
    profile["service_scope_confirmed"] = True
    database.shipments.insert_one(lot)


def _seed_event(database, *, event_id, customer_id, shipment_id, title, note):
    if database.public_events.find_one({"id": event_id}):
        return
    database.public_events.insert_one({
        "id": event_id, "version": "v1",
        "customer_id": customer_id, "shipment_id": shipment_id, "stage_id": "pickup",
        "public_title": title,
        "occurred_at": "2026-10-30T01:00:00Z", "verified": True,
        "verified_at": "2026-10-30T02:00:00Z", "visibility": "CUSTOMER",
        "internal_notes": note,
    })


def _seed_document(database, *, document_id, customer_id, shipment_id, kind, title,
                   visibility="CUSTOMER", verified=True):
    if database.public_documents.find_one({"id": document_id}):
        return
    database.public_documents.insert_one({
        "id": document_id, "version": "v1",
        "customer_id": customer_id, "shipment_id": shipment_id,
        "kind": kind, "public_title": title, "status": "AVAILABLE",
        "verified": verified, "visibility": visibility,
        "storage_file_id": f"SECRET_GRIDFS_{document_id}",
    })


def _current_pointer(database, customer_id: str, shipment_id: str) -> str:
    row = database.shipments.find_one({"id": shipment_id, "customer_id": customer_id},
                                      {"_id": 0, "customer_publication_version": 1}) or {}
    return str(row.get("customer_publication_version") or "")


def _publish(database, *, customer_id, shipment_id, event_versions, document_versions):
    """Publish through the REAL admin publisher; verify the pointer readback."""
    from core import customer_portal_publish as publisher

    pointer = _current_pointer(database, customer_id, shipment_id)
    manifest = database[portal.PUBLICATION_COLLECTION].find_one({
        "customer_id": customer_id, "shipment_id": shipment_id,
        "version": pointer, "state": "PUBLISHED",
    }, {"_id": 0}) if pointer else None
    if pointer and manifest:
        return dict(manifest)
    ok, message = publisher.publish_verified_sources(
        customer_id, shipment_id,
        event_versions=event_versions, document_versions=document_versions,
        expected_current_version="", actor_role="admin",
        actor_username="qa-fixture-admin", db=database,
    )
    if not ok:
        raise RuntimeError(f"fixture publish failed: {message}")
    pointer = _current_pointer(database, customer_id, shipment_id)
    manifest = database[portal.PUBLICATION_COLLECTION].find_one({
        "customer_id": customer_id, "shipment_id": shipment_id,
        "version": pointer, "state": "PUBLISHED",
    }, {"_id": 0})
    if not isinstance(manifest, dict):
        raise RuntimeError("fixture publish could not be read back")
    return manifest


def _manifest_evidence(database, *, customer_id, shipment_id) -> dict:
    pointer = _current_pointer(database, customer_id, shipment_id)
    manifest = database[portal.PUBLICATION_COLLECTION].find_one({
        "customer_id": customer_id, "shipment_id": shipment_id,
        "state": "PUBLISHED", "version": pointer,
    }, {"_id": 0}) or {}
    return {
        "customer_id": customer_id,
        "shipment_id": shipment_id,
        "pointer_version": pointer,
        "manifest_version": str(manifest.get("version") or ""),
        "state": str(manifest.get("state") or ""),
        "schema": str(manifest.get("schema") or ""),
        "approved_by": str(manifest.get("approved_by") or ""),
        "approved_at": str(manifest.get("approved_at") or ""),
        "event_versions": dict(manifest.get("event_versions") or {}),
        "document_versions": dict(manifest.get("document_versions") or {}),
        "approved_content_sha256": str(manifest.get("approved_content_sha256") or ""),
    }


def _canonical_negatives(database) -> dict:
    """Server-side canonical checks on the SAME store. No browser input at all."""
    from core import customer_portal_publish as publisher
    from core.customer_portal_sources import read_approved_sources
    from core.hexa_customer_publication import (
        PublicationDenied,
        build_customer_publication,
    )

    results: dict[str, object] = {}

    # 1. A verified email that is NOT allow-listed must be denied by the server.
    try:
        portal.build_customer_principal(verified_email=QA_DENIED_EMAIL, db=database)
    except portal.PortalAccessDenied:
        results["ungranted_email"] = {
            "denied": True, "exception": "PortalAccessDenied",
            "email_masked": _mask(QA_DENIED_EMAIL),
        }
    else:
        results["ungranted_email"] = {
            "denied": False, "exception": None,
            "email_masked": _mask(QA_DENIED_EMAIL),
        }

    principal_a = portal.build_customer_principal(verified_email=QA_EMAIL, db=database)
    principal_b = portal.build_customer_principal(
        verified_email=QA_OTHER_EMAIL, db=database)
    view_a = portal.load_customer_dashboard(principal_a, db=database)
    view_b = portal.load_customer_dashboard(principal_b, db=database)
    results["tenant_split"] = {
        "a": {"customer_id": principal_a.customer_id,
              "cards": [card.reference for card in view_a.cards],
              "documents": [doc.get("id") for card in view_a.cards
                            for doc in card.documents]},
        "b": {"customer_id": principal_b.customer_id,
              "cards": [card.reference for card in view_b.cards],
              "documents": [doc.get("id") for card in view_b.cards
                            for doc in card.documents]},
    }

    manifest_a = database[portal.PUBLICATION_COLLECTION].find_one({
        "customer_id": QA_CUSTOMER, "shipment_id": QA_LOT, "state": "PUBLISHED",
        "version": _current_pointer(database, QA_CUSTOMER, QA_LOT),
    }, {"_id": 0}) or {}
    manifest_b = database[portal.PUBLICATION_COLLECTION].find_one({
        "customer_id": QA_OTHER, "shipment_id": QA_OTHER_LOT, "state": "PUBLISHED",
        "version": _current_pointer(database, QA_OTHER, QA_OTHER_LOT),
    }, {"_id": 0}) or {}

    def _attempt(call) -> str:
        try:
            call()
        except PublicationDenied:
            return "PublicationDenied"
        except Exception as exc:  # noqa: BLE001 - report the real type
            return type(exc).__name__
        return "ALLOWED"

    pub_a_principal = principal_a.publication_principal()
    # 2. A's own manifest is valid … (positive control for the negative below)
    results["own_manifest_allowed"] = _attempt(lambda: build_customer_publication(
        shipment={"id": QA_LOT, "customer_id": QA_CUSTOMER},
        principal=pub_a_principal, publication=dict(manifest_a),
    ))
    # 3. … the SAME principal + A's lot with B's manifest must be denied.
    results["cross_tenant_manifest"] = _attempt(lambda: build_customer_publication(
        shipment={"id": QA_LOT, "customer_id": QA_CUSTOMER},
        principal=pub_a_principal, publication=dict(manifest_b),
    ))
    results["foreign_shipment_manifest"] = _attempt(lambda: build_customer_publication(
        shipment={"id": QA_OTHER_LOT, "customer_id": QA_CUSTOMER},
        principal=pub_a_principal, publication=dict(manifest_b),
    ))
    # 4. B's manifest applied to A's tenant must not read one foreign row.
    events, documents, _quote = read_approved_sources(
        database, customer_id=QA_CUSTOMER, shipment_id=QA_OTHER_LOT,
        shipment_quote_id=None, publication=manifest_b,
    )
    results["cross_tenant_source_rows"] = {
        "events": len(events), "documents": len(documents),
    }
    # 5. INTERNAL / unverified sources can never be published, even by an Admin
    #    with a correct compare-and-set pointer.
    pointer_before = _current_pointer(database, QA_CUSTOMER, QA_LOT)
    manifests_before = database[portal.PUBLICATION_COLLECTION].count_documents(
        {"customer_id": QA_CUSTOMER, "shipment_id": QA_LOT})
    for label, document_id in (("private_document", QA_PRIVATE_DOC_ID),
                               ("unverified_document", QA_UNVERIFIED_DOC_ID)):
        try:
            publisher.publish_verified_sources(
                QA_CUSTOMER, QA_LOT,
                event_versions={}, document_versions={document_id: "v1"},
                expected_current_version=pointer_before, actor_role="admin",
                actor_username="qa-fixture-admin", db=database,
            )
        except publisher.PublicationWriteDenied:
            results[label] = "PublicationWriteDenied"
        else:
            results[label] = "ALLOWED"
    results["pointer_after_denials"] = _current_pointer(database, QA_CUSTOMER, QA_LOT)
    results["manifests_before_after"] = [
        manifests_before,
        database[portal.PUBLICATION_COLLECTION].count_documents(
            {"customer_id": QA_CUSTOMER, "shipment_id": QA_LOT}),
    ]
    return results


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

    # The QA lots inherit the real seeded shipment shape, so the Journey Map has
    # genuine nodes (pickup included) and the internal shell can project them.
    template = database.shipments.find_one({"is_deleted": {"$ne": True}}) or {}
    _seed_lot(database, template, lot_id=QA_LOT, customer_id=QA_CUSTOMER,
              note=SECRET_LOT_NOTE, cost=SECRET_COST_A, mode=QA_MODES[QA_LOT])
    _seed_lot(database, template, lot_id=QA_OTHER_LOT, customer_id=QA_OTHER,
              note=SECRET_OTHER_LOT_NOTE, cost=SECRET_COST_B,
              mode=QA_MODES[QA_OTHER_LOT])

    _seed_event(database, event_id=QA_EVENT_ID, customer_id=QA_CUSTOMER,
                shipment_id=QA_LOT, title=QA_EVENT_TITLE, note=SECRET_EVENT_NOTE)
    _seed_event(database, event_id=QA_OTHER_EVENT_ID, customer_id=QA_OTHER,
                shipment_id=QA_OTHER_LOT, title=QA_OTHER_EVENT_TITLE,
                note=SECRET_OTHER_EVENT_NOTE)

    _seed_document(database, document_id=QA_DOC_ID, customer_id=QA_CUSTOMER,
                   shipment_id=QA_LOT, kind="PL", title=QA_DOC_TITLE)
    for document_id, title in zip(QA_OTHER_DOC_IDS, QA_OTHER_DOC_TITLES):
        _seed_document(database, document_id=document_id, customer_id=QA_OTHER,
                       shipment_id=QA_OTHER_LOT,
                       kind="BL" if title.startswith("QA-B Bill") else "POD",
                       title=title)
    # Negative controls: INTERNAL visibility and unverified, same lot/customer.
    _seed_document(database, document_id=QA_PRIVATE_DOC_ID, customer_id=QA_CUSTOMER,
                   shipment_id=QA_LOT, kind="PL", title="SECRET_INTERNAL_DOC_A",
                   visibility="INTERNAL")
    _seed_document(database, document_id=QA_UNVERIFIED_DOC_ID,
                   customer_id=QA_CUSTOMER, shipment_id=QA_LOT, kind="PL",
                   title="SECRET_UNVERIFIED_DOC_A", verified=False)

    if not QA_PASSWORD:
        raise RuntimeError("QA_TEST_PASSWORD is required for the fixture staff login")
    from core.users import build_user_document

    if database.users.find_one({"username": TRUONG_THANH["username"]}) is None:
        database.users.insert_one(build_user_document(
            TRUONG_THANH["username"], QA_PASSWORD,
            TRUONG_THANH["display_name"], TRUONG_THANH["role"],
        ))

    # TWO independent publications, each with its OWN verified sources, pins and
    # version pointer. Neither manifest is derived from the other.
    _publish(database, customer_id=QA_CUSTOMER, shipment_id=QA_LOT,
             event_versions={QA_EVENT_ID: "v1"},
             document_versions={QA_DOC_ID: "v1"})
    _publish(database, customer_id=QA_OTHER, shipment_id=QA_OTHER_LOT,
             event_versions={QA_OTHER_EVENT_ID: "v1"},
             document_versions={doc_id: "v1" for doc_id in QA_OTHER_DOC_IDS})

    _write_evidence("server-db.json", _db_identity(database))
    _write_evidence("server-publications.json", {
        "database": getattr(database, "name", "UNKNOWN"),
        "pid": os.getpid(),
        "a": _manifest_evidence(database, customer_id=QA_CUSTOMER, shipment_id=QA_LOT),
        "b": _manifest_evidence(database, customer_id=QA_OTHER,
                                shipment_id=QA_OTHER_LOT),
        "internal_markers_present_in_db": {
            "lot_notes": [SECRET_LOT_NOTE, SECRET_OTHER_LOT_NOTE],
            "event_notes": [SECRET_EVENT_NOTE, SECRET_OTHER_EVENT_NOTE],
            "costs": [SECRET_COST_A, SECRET_COST_B],
            "private_document": QA_PRIVATE_DOC_ID,
            "unverified_document": QA_UNVERIFIED_DOC_ID,
        },
    })
    _write_evidence("server-negative.json", _canonical_negatives(database))
    return database


@st.cache_resource
def qa_database():
    return _bootstrap()


# --------------------------------------------------------------------------- #
# S3 readback: the exact payload the server hands the component for this role
# --------------------------------------------------------------------------- #

def _forbidden_for(role: str, database) -> list[str]:
    """Every string that must NOT appear in THIS role's component payload."""
    manifests = {
        "a": _manifest_evidence(database, customer_id=QA_CUSTOMER, shipment_id=QA_LOT),
        "b": _manifest_evidence(database, customer_id=QA_OTHER,
                                shipment_id=QA_OTHER_LOT),
    }
    own = manifests[role]
    other = manifests["b" if role == "a" else "a"]
    markers = [
        # Internal-only values present in the same database.
        "SECRET_INTERNAL", "SECRET_GRIDFS", "SECRET_UNVERIFIED",
        str(SECRET_COST_A), str(SECRET_COST_B),
        # Publication metadata of the OTHER customer. The portal model truncates
        # the version for display, so match the truncated form as well.
        other["manifest_version"], other["manifest_version"][:20],
        other["approved_content_sha256"], other["customer_id"],
    ]
    if role == "a":
        markers += [QA_OTHER_LOT, QA_OTHER_EVENT_ID, QA_OTHER_EVENT_TITLE,
                    *QA_OTHER_DOC_IDS, *QA_OTHER_DOC_TITLES]
    else:
        markers += [QA_LOT, QA_EVENT_ID, QA_EVENT_TITLE, QA_DOC_ID, QA_DOC_TITLE]
    # Own manifest hash is publication metadata that the portal model does not
    # deliver either. The own display version IS legitimately rendered ("Phiên
    # bản công bố" of the customer's own lot), so it is not forbidden.
    markers += [own["approved_content_sha256"]]
    return [marker for marker in markers if marker]


def _record_view(database, role: str, principal, view, payload) -> None:
    """Record the server truth for one role: cards, ids, and payload scan."""
    context = json.dumps(payload, ensure_ascii=False, default=str)
    forbidden = _forbidden_for(role, database)
    found = [marker for marker in forbidden if marker in context]
    cards = [
        {
            "reference": card.reference,
            "publication_version": card.publication_version,
            "approved_at": card.approved_at,
            "timeline": [
                {"id": event.get("id"), "version": event.get("version"),
                 "title": event.get("title"), "stage": event.get("stage")}
                for event in card.timeline
            ],
            "documents": [
                {"id": doc.get("id"), "version": doc.get("version"),
                 "kind": doc.get("kind"), "title": doc.get("title")}
                for doc in card.documents
            ],
        }
        for card in view.cards
    ]
    lots = payload.get("lots") or []
    READBACK[role] = {
        "role": role,
        "email_masked": _mask(principal.email),
        "email_sha256_12": _digest(principal.email),
        "principal_customer_id": principal.customer_id,
        "database": getattr(database, "name", "UNKNOWN"),
        "pid": os.getpid(),
        "denied_lots": int(getattr(view, "denied_lots", 0) or 0),
        "data_issues": int(getattr(view, "data_issues", 0) or 0),
        "cards": cards,
        "payload_lot_ids": [str(lot.get("shipment_id") or "") for lot in lots],
        "payload_publication_versions": [
            str((lot.get("publication") or {}).get("version") or "") for lot in lots
        ],
        "payload_document_ids": [
            str(doc.get("id") or "")
            for lot in lots for doc in (lot.get("documents") or [])
        ],
        "payload_document_titles": [
            str(doc.get("title") or "")
            for lot in lots for doc in (lot.get("documents") or [])
        ],
        "payload_has_discussion": bool(payload.get("discussion")),
        "payload_bytes": len(context.encode("utf-8")),
        "forbidden_markers": forbidden,
        "forbidden_markers_found": found,
        "payload_clean": not found,
    }
    # Streamlit re-executes this script on every rerun, so module state cannot be
    # the store. One file per role survives reruns AND independent browser
    # sessions of the SAME process, which is what a same-store A/B proof needs.
    _write_evidence(f"server-readback-{role}.json", READBACK[role])
    merged: dict[str, object] = {}
    directory = _evidence_dir()
    if directory is not None:
        for candidate in ("a", "b"):
            path = directory / f"server-readback-{candidate}.json"
            try:
                merged[candidate] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
    _write_evidence("server-readback.json", {
        "database": getattr(database, "name", "UNKNOWN"),
        "pid": os.getpid(),
        "roles": merged or READBACK,
    })


st.set_page_config(layout="wide")
st.warning(
    "QA cô lập: danh tính giả lập trong fixture, dữ liệu mongomock dùng chung, "
    "không chứng minh đăng nhập OIDC thật."
)

db = qa_database()

#: Default is customer A so a browser reload starts from a customer session
#: (never an internal login form). Each label maps to ONE fixed TEST email; the
#: principal itself is still resolved by the canonical server allowlist.
role = st.radio(
    "QA identity (test only)",
    ["Trường Thành (nội bộ)", "Lục Giác", "Khách khác", "Khách chưa được cấp quyền"],
    index=1,
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
elif role in ("Lục Giác", "Khách khác"):
    email = QA_EMAIL if role == "Lục Giác" else QA_OTHER_EMAIL
    entity_role = "a" if role == "Lục Giác" else "b"
    # Canonical server-side resolution: the email is the only input, and the
    # customer_id comes from the Owner allowlist in the database.
    principal = portal.build_customer_principal(verified_email=email, db=db)
    # Same-store readback of exactly what this principal's payload carries.
    try:
        from views import journey_inline

        view = portal.load_customer_dashboard(principal, db=db)
        discussion = journey_inline.build_customer_discussion(
            principal, view.cards, db=db)
        payload = customer_dashboard.build_model(view, discussion=discussion)
        _record_view(db, entity_role, principal, view, payload)
    except Exception as exc:  # noqa: BLE001 - readback must not break the portal
        _write_evidence("server-readback-error.json", {
            "role": entity_role, "error": type(exc).__name__,
        })
    customer_dashboard.render_customer_dashboard(principal, db=db)
else:
    # A verified email that the Owner never allow-listed: the canonical server
    # resolver must raise. The fixture renders the SAME uniform denial screen
    # the production entrypoint shows; it never falls back to another customer.
    try:
        portal.build_customer_principal(verified_email=QA_DENIED_EMAIL, db=db)
    except portal.PortalAccessDenied:
        _write_evidence("server-denied-view.json", {
            "email_masked": _mask(QA_DENIED_EMAIL),
            "exception": "PortalAccessDenied",
            "principal_created": False,
        })
        customer_dashboard.render_customer_denied()
    except portal.PortalDataError:
        _write_evidence("server-denied-view.json", {
            "email_masked": _mask(QA_DENIED_EMAIL),
            "exception": "PortalDataError",
            "principal_created": False,
        })
        customer_dashboard.render_customer_denied()
    else:  # pragma: no cover - a real fail-open bug would land here
        _write_evidence("server-denied-view.json", {
            "email_masked": _mask(QA_DENIED_EMAIL),
            "exception": None,
            "principal_created": True,
        })
        st.error("LỖI: email không được cấp quyền vẫn nhận được principal.")
