"""Admin-only, explicit G1.5 publisher over already verified public source records.

Never copy private shipment/quote data into a customer release. Approval is an
Admin action; customer read access still goes through the existing OIDC tenant
gate and its version-pinned publication reader.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.customer_portal import PUBLICATION_COLLECTION, _resolve_db, clean_id
from core.customer_portal_sources import MAX_APPROVED_PINS, read_approved_sources
from core.hexa_customer_publication import (
    ALLOWED_DOCUMENT_KINDS, PUBLICATION_SCHEMA, build_customer_publication,
)

LOGGER = logging.getLogger("logistics.customer_portal_publish")
_SOURCE_FIELDS = {
    "_id": 0, "id": 1, "version": 1, "public_title": 1,
    "customer_id": 1, "shipment_id": 1, "verified": 1,
    "verified_at": 1, "visibility": 1, "occurred_at": 1,
    "stage_id": 1, "status": 1, "kind": 1,
}


class PublicationWriteDenied(PermissionError):
    """Generic fail-closed refusal, including unavailable source data."""


def _admin(actor_role: Any) -> None:
    if str(actor_role or "").strip().lower() != "admin":
        raise PublicationWriteDenied("Chỉ Admin được công bố cho khách hàng.")


def _scope(db: Any, customer_id: str, shipment_id: str) -> Mapping[str, Any]:
    if not customer_id or not shipment_id:
        raise PublicationWriteDenied("Chưa chọn đúng khách hàng và lô hàng.")
    row = db.shipments.find_one(
        {"id": shipment_id, "customer_id": customer_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "customer_id": 1, "transport_mode": 1,
         "customer_publication_version": 1},
    )
    if not isinstance(row, Mapping) or clean_id(row.get("customer_id")) != customer_id:
        raise PublicationWriteDenied("Lô hàng không thuộc khách hàng đã chọn.")
    return row


def list_customer_shipments(
    customer_id: str, *, actor_role: str, db: Any = None,
) -> list[dict[str, str]]:
    """Canonical IDs only; no fuzzy matching by a customer's display name."""
    _admin(actor_role)
    customer_id = clean_id(customer_id)
    if not customer_id:
        return []
    database = _resolve_db(db)
    rows = database.shipments.find(
        {"customer_id": customer_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "customer_publication_version": 1},
    ).sort("id", 1).limit(50)
    return [
        {"id": clean_id(row.get("id")),
         "published_version": clean_id(row.get("customer_publication_version"))}
        for row in rows if isinstance(row, Mapping) and clean_id(row.get("id"))
    ]


def list_verified_sources(
    customer_id: str, shipment_id: str, *, actor_role: str, db: Any = None,
) -> dict[str, list[dict[str, str]]]:
    """Only eligible, pre-verified sources; never infer or create evidence."""
    _admin(actor_role)
    customer_id, shipment_id = clean_id(customer_id), clean_id(shipment_id)
    database = _resolve_db(db)
    _scope(database, customer_id, shipment_id)
    result: dict[str, list[dict[str, str]]] = {"events": [], "documents": []}
    for collection, output in (("public_events", "events"), ("public_documents", "documents")):
        query: dict[str, Any] = {
            "customer_id": customer_id, "shipment_id": shipment_id,
            "verified": True, "visibility": "CUSTOMER",
        }
        if collection == "public_documents":
            query["status"] = "AVAILABLE"
            query["kind"] = {"$in": sorted(ALLOWED_DOCUMENT_KINDS)}
        rows = list(database[collection].find(query, _SOURCE_FIELDS).limit(MAX_APPROVED_PINS + 1))
        if len(rows) > MAX_APPROVED_PINS:
            raise PublicationWriteDenied("Quá nhiều bản nguồn để chọn an toàn.")
        for row in rows:
            rid, version = clean_id(row.get("id")), clean_id(row.get("version"))
            if (not rid or not version or len(rid) > 128 or len(version) > 40
                    or "." in rid or rid.startswith("$")):
                continue
            if output == "events" and not all((
                clean_id(row.get("verified_at")), clean_id(row.get("occurred_at")),
                clean_id(row.get("public_title")), clean_id(row.get("stage_id")),
            )):
                continue
            result[output].append({
                "id": rid, "version": version,
                "title": str(row.get("public_title") or row.get("kind") or rid)[:120],
                "stage": clean_id(row.get("stage_id")),
                "kind": clean_id(row.get("kind")),
            })
    return result


def _pins(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or len(value) > MAX_APPROVED_PINS:
        raise PublicationWriteDenied("Danh sách công bố không hợp lệ.")
    pins: dict[str, str] = {}
    for raw_id, raw_version in value.items():
        rid, version = clean_id(raw_id), clean_id(raw_version)
        if (not rid or not version or len(rid) > 128 or len(version) > 40
                or "." in rid or rid.startswith("$")):
            raise PublicationWriteDenied("Mã hoặc phiên bản không hợp lệ.")
        pins[rid] = version
    return pins


def publish_verified_sources(
    customer_id: str,
    shipment_id: str,
    *,
    event_versions: Mapping[str, str],
    document_versions: Mapping[str, str],
    expected_current_version: str,
    actor_role: str,
    actor_username: str,
    db: Any = None,
) -> tuple[bool, str]:
    """Create an immutable release then compare-and-set the shipment's pointer.

    A failed pointer update leaves only an unreachable manifest; no partial
    customer publication is exposed and no success is reported without readback.
    """
    _admin(actor_role)
    customer_id, shipment_id = clean_id(customer_id), clean_id(shipment_id)
    username = clean_id(actor_username)
    if not username or len(username) > 100:
        raise PublicationWriteDenied("Không xác minh được tài khoản Admin.")
    events, documents = _pins(event_versions), _pins(document_versions)
    if not events and not documents:
        raise PublicationWriteDenied("Phải chọn ít nhất một mốc hoặc chứng từ đã xác minh.")
    database = _resolve_db(db)
    shipment = _scope(database, customer_id, shipment_id)
    previous = clean_id(shipment.get("customer_publication_version"))
    if previous != clean_id(expected_current_version):
        return False, "Bản công bố đã thay đổi. Tải lại trước khi duyệt tiếp."

    # Validate the exact chosen versions again at write time. The public
    # allowlist rejects private, unverified, stale, foreign or ambiguous data.
    candidate = {"event_versions": events, "document_versions": documents}
    try:
        public_events, public_documents, _ = read_approved_sources(
            database, customer_id=customer_id, shipment_id=shipment_id,
            shipment_quote_id=None, publication=candidate,
        )
        dry_manifest = {
            **candidate, "schema": PUBLICATION_SCHEMA,
            "customer_id": customer_id, "shipment_id": shipment_id,
            "version": "preflight", "state": "PUBLISHED",
            "approved_by": username, "approved_at": "preflight",
        }
        safe = build_customer_publication(
            shipment=shipment,
            principal={"kind": "customer", "authenticated": True, "customer_id": customer_id},
            publication=dry_manifest, events=public_events, documents=public_documents,
        )
        if ({e["id"]: e["version"] for e in safe["timeline"]} != events
                or {d["id"]: d["version"] for d in safe["documents"]} != documents):
            raise PublicationWriteDenied("Nguồn không khớp bản xác minh/phiên bản.")
    except PublicationWriteDenied:
        raise
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PUBLICATION_PREFLIGHT_DENIED type=%s", type(exc).__name__)
        raise PublicationWriteDenied("Không xác minh đủ nguồn để công bố.") from None

    version = "g15-" + uuid4().hex
    manifest = {
        "id": f"{customer_id}:{shipment_id}:{version}",
        "schema": PUBLICATION_SCHEMA, "customer_id": customer_id,
        "shipment_id": shipment_id, "version": version,
        "state": "PUBLISHED", "approved_by": username,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "event_versions": events, "document_versions": documents,
        "is_deleted": False,
    }
    cas: dict[str, Any] = {
        "id": shipment_id, "customer_id": customer_id,
        "is_deleted": {"$ne": True},
        "customer_publication_version": (
            previous if previous else {"$in": [None, ""]}
        ),
    }
    try:
        database[PUBLICATION_COLLECTION].insert_one(manifest)
        result = database.shipments.update_one(
            cas, {"$set": {"customer_publication_version": version}},
        )
        if getattr(result, "matched_count", 0) != 1:
            return False, "Lô hàng đã thay đổi, chưa công bố phiên bản mới."
        written = database.shipments.find_one(
            {"id": shipment_id, "customer_id": customer_id},
            {"_id": 0, "customer_publication_version": 1},
        )
        if (not isinstance(written, Mapping)
                or written.get("customer_publication_version") != version):
            return False, "Chưa xác nhận được bản lưu. Kiểm tra lại trước khi thao tác tiếp."
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PUBLICATION_SAVE_UNVERIFIED type=%s", type(exc).__name__)
        return False, "Không xác nhận được kết quả công bố. Hãy tải lại để kiểm tra."
    LOGGER.info("CUSTOMER_PUBLICATION_APPROVED shipment_id=%s version=%s", shipment_id, version)
    return True, f"Đã công bố bản {version} cho khách hàng."
