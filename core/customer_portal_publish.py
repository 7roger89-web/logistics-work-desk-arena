"""Admin-only, explicit G1.5 publisher over already verified public source records.

Never copy private shipment/quote data into a customer release. Approval is an
Admin action; customer read access still goes through the existing OIDC tenant
gate and its version-pinned publication reader.

Issue #263 adds exactly ONE Admin action to this same module: verifying a
pending source (written by a staff update, ``core.customer_portal_milestones``)
at an exact id + version + content hash.  It reuses the existing Admin guard,
tenant scope and collection; it never publishes and never bypasses the
publisher below.
"""
from __future__ import annotations

import logging
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime, timezone
from typing import Any
from uuid import uuid4

from core.customer_portal import PUBLICATION_COLLECTION, _resolve_db, clean_id
from core.customer_portal_milestones import (
    SOURCE_COLLECTION,
    SOURCE_STATE_VERIFIED,
    SOURCE_STATE_WITHDRAWN,
    content_digest,
    public_source_content,
)
from core.customer_portal_sources import MAX_APPROVED_PINS, read_approved_sources
from core.hexa_customer_publication import (
    ALLOWED_DOCUMENT_KINDS, PUBLICATION_SCHEMA, build_customer_publication,
    approved_content_fingerprint,
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
    if db.customers.find_one(
        {"id": customer_id, "is_deleted": {"$ne": True}}, {"_id": 0, "id": 1},
    ) is None:
        raise PublicationWriteDenied("Không tìm thấy hồ sơ khách hàng hợp lệ.")
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


_PENDING_FIELDS = {
    "_id": 0, "id": 1, "version": 1, "public_title": 1, "stage_id": 1,
    "occurred_at": 1, "recorded_at": 1, "recorded_by": 1, "state": 1,
    "verified": 1, "visibility": 1, "content_sha256": 1,
    # Needed to re-derive the approved content hash; never rendered in the UI.
    "customer_id": 1, "shipment_id": 1,
}


def list_pending_sources(
    customer_id: str, shipment_id: str, *, actor_role: str, db: Any = None,
) -> list[dict[str, str]]:
    """Admin-only view of staff-written sources that still await verification.

    Read-only and deliberately narrow: a pending source is metadata (what, when,
    which version), never internal shipment content. A source whose public
    content was withdrawn is listed as such so it can never be verified by
    accident.
    """
    _admin(actor_role)
    customer_id, shipment_id = clean_id(customer_id), clean_id(shipment_id)
    database = _resolve_db(db)
    _scope(database, customer_id, shipment_id)
    rows = list(database[SOURCE_COLLECTION].find(
        {
            "customer_id": customer_id, "shipment_id": shipment_id,
            "visibility": "CUSTOMER", "verified": {"$ne": True},
            "is_deleted": {"$ne": True},
        },
        _PENDING_FIELDS,
    ).sort("recorded_at", 1).limit(MAX_APPROVED_PINS + 1))
    if len(rows) > MAX_APPROVED_PINS:
        raise PublicationWriteDenied("Quá nhiều nguồn chờ xác minh để xử lý an toàn.")
    result: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        rid, version = clean_id(row.get("id")), clean_id(row.get("version"))
        if not rid or not version or len(rid) > 128 or len(version) > 40:
            continue
        state = clean_id(row.get("state"))
        withdrawn = (state == SOURCE_STATE_WITHDRAWN
                     or not (clean_id(row.get("public_title")) and clean_id(row.get("occurred_at"))))
        result.append({
            "id": rid, "version": version,
            "title": str(row.get("public_title") or "")[:120],
            "stage": clean_id(row.get("stage_id")),
            "occurred_at": clean_id(row.get("occurred_at")),
            "recorded_at": clean_id(row.get("recorded_at"))[:40],
            "recorded_by": clean_id(row.get("recorded_by"))[:100],
            "state": SOURCE_STATE_WITHDRAWN if withdrawn else (state or "PENDING"),
        })
    return result


def verify_source(
    event_id: str,
    version: str,
    *,
    customer_id: str,
    shipment_id: str,
    actor_role: str,
    actor_username: str,
    db: Any = None,
) -> tuple[bool, str]:
    """Mark ONE exact pending source version verified (Admin only).

    The version AND the stored content hash are re-checked here, so a source
    edited without a new staff write (same id/version, different content) is
    refused instead of being approved. Verification never publishes anything.
    """
    _admin(actor_role)
    event_id, version = clean_id(event_id), clean_id(version)
    customer_id, shipment_id = clean_id(customer_id), clean_id(shipment_id)
    username = clean_id(actor_username)
    if not username or len(username) > 100:
        raise PublicationWriteDenied("Không xác minh được tài khoản Admin.")
    if not event_id or not version:
        raise PublicationWriteDenied("Chưa chọn đúng nguồn và phiên bản cần xác minh.")
    database = _resolve_db(db)
    _scope(database, customer_id, shipment_id)
    row = database[SOURCE_COLLECTION].find_one(
        {
            "id": event_id, "customer_id": customer_id, "shipment_id": shipment_id,
            "is_deleted": {"$ne": True},
        },
        _PENDING_FIELDS,
    )
    if not isinstance(row, Mapping) or clean_id(row.get("visibility")) != "CUSTOMER":
        raise PublicationWriteDenied("Không tìm thấy nguồn chờ xác minh của đúng lô này.")
    current_version = clean_id(row.get("version"))
    if current_version != version:
        return False, "Nguồn đã thay đổi so với bản đang xem. Tải lại danh sách trước khi xác minh."
    content = public_source_content(
        customer_id=row.get("customer_id"), shipment_id=row.get("shipment_id"),
        stage_id=row.get("stage_id"), public_title=row.get("public_title"),
        occurred_at=row.get("occurred_at"),
    )
    expected_hash = str(row.get("content_sha256") or "")
    if (len(expected_hash) != 64
            or not secrets.compare_digest(expected_hash, content_digest(content))):
        raise PublicationWriteDenied("Nội dung nguồn không khớp phiên bản đã ghi. Không xác minh.")
    if not all((content["public_title"], content["occurred_at"], content["stage_id"])):
        raise PublicationWriteDenied("Nguồn chưa có đủ nội dung công khai để xác minh.")
    if row.get("verified") is True:
        return True, "Nguồn này đã được xác minh ở đúng phiên bản."
    result = database[SOURCE_COLLECTION].update_one(
        {
            "id": event_id, "customer_id": customer_id, "shipment_id": shipment_id,
            "version": current_version, "verified": {"$ne": True},
        },
        {"$set": {
            "verified": True, "verified_at": datetime.now(UTC).isoformat(),
            "verified_by": username, "state": SOURCE_STATE_VERIFIED,
        }},
    )
    if getattr(result, "matched_count", 0) != 1:
        return False, "Nguồn đã thay đổi trong lúc xác minh. Chưa ghi nhận xác minh."
    written = database[SOURCE_COLLECTION].find_one(
        {"id": event_id, "customer_id": customer_id, "shipment_id": shipment_id},
        _PENDING_FIELDS,
    )
    if (not isinstance(written, Mapping) or written.get("verified") is not True
            or clean_id(written.get("version")) != current_version):
        return False, "Chưa đọc lại được xác minh. Kiểm tra lại trước khi công bố."
    LOGGER.info("CUSTOMER_SOURCE_VERIFIED event_id=%s version=%s", event_id, current_version)
    return True, f"Đã xác minh nguồn {event_id} phiên bản {current_version}."


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
        # Any same-version source edit after approval will fail closed at read.
        "approved_content_sha256": approved_content_fingerprint(safe),
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
