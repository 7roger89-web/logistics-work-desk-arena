"""Staff-side public source for the LẤY HÀNG (pickup) milestone.

G1.5 already had a reader (``core.customer_portal_sources``), an Admin publisher
(``core.customer_portal_publish``) and a customer allowlist
(``core.hexa_customer_publication``), but **no application code ever wrote a
``public_events`` row**: every existing proof inserted fixtures by hand.  This
module is the missing producer for exactly ONE operational stage.

It is deliberately narrow:

* it projects ONE already-persisted staff fact — the actual pickup of the first
  ``Truck`` leg (``data["1.2"].transport_legs``), the same fact
  ``core.shipment_operations.compatibility_facts`` and the staff Journey use —
  into ONE customer-safe text record;
* the record is written **unverified** (``verified=False``) into the existing
  ``public_events`` collection, so it is a *source waiting for Admin
  verification*, not a publication;
* nothing is published here.  ``core.customer_portal_publish`` remains the one
  Admin authority, and ``read_approved_sources``/``build_customer_publication``
  remain the one customer read boundary.

Versioning is content-addressed on purpose: the public version IS the SHA-256 of
the exact customer-visible content.  Re-saving identical facts therefore keeps
the Admin's verification, while any change to the pickup fact (a new ``atd``,
or the milestone being withdrawn) produces a new version and automatically
clears ``verified``.  A publication that pinned the previous version can no
longer be read or re-published, so stale or edited content cannot be released.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any

from core.customer_portal import clean_id

PICKUP_STAGE_ID = "pickup"
PICKUP_KIND = "PICKUP"
PICKUP_PUBLIC_TITLE = "Đã lấy hàng"
PICKUP_SOURCE = "STAFF_PICKUP_ATD"
SOURCE_COLLECTION = "public_events"
SOURCE_STATE_PENDING = "PENDING"
SOURCE_STATE_VERIFIED = "VERIFIED"
SOURCE_STATE_WITHDRAWN = "WITHDRAWN"
MAX_SOURCE_ID = 128
MAX_SOURCE_TEXT = 200

#: The ONLY fields of the internal fact that may cross into a public record.
_CONTENT_FIELDS = ("stage_id", "public_title", "occurred_at", "customer_id", "shipment_id")


def _text(value: Any, limit: int = MAX_SOURCE_TEXT) -> str:
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int)):
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()[:limit]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _day(value: Any) -> str:
    """Return an ISO ``YYYY-MM-DD`` day or "" — never invent a time of day."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = _text(value, 40)[:10]
    if len(raw) != 10:
        return ""
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return ""


def public_source_content(
    *, customer_id: Any, shipment_id: Any, stage_id: Any,
    public_title: Any, occurred_at: Any,
) -> dict[str, str]:
    """The exact customer-visible content of one milestone source."""
    return {
        "stage_id": _text(stage_id, 40),
        "public_title": _text(public_title),
        "occurred_at": _text(occurred_at, 40),
        "customer_id": _text(customer_id, 128),
        "shipment_id": _text(shipment_id, 128),
    }


def content_digest(content: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical public content (no internal field participates)."""
    canonical = {key: _text(content.get(key)) for key in _CONTENT_FIELDS}
    encoded = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_version(content: Mapping[str, Any]) -> str:
    """Public version = content digest prefix (deterministic, <= 40 chars)."""
    return content_digest(content)[:16]


def source_event_id(customer_id: Any, shipment_id: Any) -> str:
    """Stable public-source id for one lot, safe for the publisher pin rules."""
    customer, shipment = _text(customer_id, 128), _text(shipment_id, 128)
    raw = f"pickup:{customer}:{shipment}"
    safe = "".join(ch if (ch.isalnum() or ch in "-_:") else "-" for ch in raw)
    if len(safe) <= MAX_SOURCE_ID and "." not in safe:
        return safe
    return "pickup:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:60]


def pickup_public_fact(shipment: Mapping[str, Any]) -> dict[str, str] | None:
    """Project the ALREADY PERSISTED pickup fact, or ``None`` when not actual.

    The rule is the existing one, not a new one: the pickup leg is the first
    ``Truck`` leg, and the milestone exists only when it carries a real ``atd``
    (``core.shipment_journey`` marks the staff node done on the same fact).
    """
    from core.shipment_operations import compatibility_facts

    if not isinstance(shipment, Mapping):
        return None
    try:
        facts = compatibility_facts(shipment)
    except Exception:  # noqa: BLE001 - malformed legacy document => no public fact
        return None
    leg = facts.get("pickup_leg") if isinstance(facts, Mapping) else None
    if not isinstance(leg, Mapping) or _text(leg.get("mode"), 20) != "Truck":
        return None
    atd = _day(leg.get("atd"))
    if not atd:
        return None
    return {"stage_id": PICKUP_STAGE_ID, "public_title": PICKUP_PUBLIC_TITLE, "occurred_at": atd}


def record_pickup_source(
    database: Any, shipment: Mapping[str, Any], *, actor_username: str,
) -> dict[str, Any] | None:
    """Create/refresh the UNVERIFIED pickup source for one lot.

    Returns a small receipt dict (id/version/state/changed) or ``None`` when
    there is nothing to record.  The caller must already be an authorised
    shipment writer; this function never grants permission and never verifies.
    """
    actor = _text(actor_username, 100)
    customer_id = clean_id(shipment.get("customer_id"))
    shipment_id = clean_id(shipment.get("id") or shipment.get("shipment_id"))
    if not customer_id or not shipment_id:
        return None
    event_id = source_event_id(customer_id, shipment_id)
    existing = database[SOURCE_COLLECTION].find_one(
        {"id": event_id, "customer_id": customer_id, "shipment_id": shipment_id},
    )
    fact = pickup_public_fact(shipment)
    now = _now()

    if fact is None:
        # Nothing actual to publish. A previously verified source must NOT stay
        # publishable after the underlying fact disappears: bump the version and
        # clear verification so any pinned publication fails closed.
        if not isinstance(existing, Mapping) or existing.get("verified") is not True:
            return None
        content = public_source_content(
            customer_id=customer_id, shipment_id=shipment_id,
            stage_id=PICKUP_STAGE_ID, public_title="", occurred_at="",
        )
        database[SOURCE_COLLECTION].update_one(
            {"_id": existing.get("_id")},
            {"$set": {
                **content,
                "version": source_version(content),
                "content_sha256": content_digest(content),
                "verified": False, "verified_at": "", "verified_by": "",
                "state": SOURCE_STATE_WITHDRAWN,
                "recorded_at": now, "recorded_by": actor, "updated_at": now,
            }},
        )
        return {
            "id": event_id, "version": source_version(content),
            "state": SOURCE_STATE_WITHDRAWN, "changed": True,
        }

    content = public_source_content(
        customer_id=customer_id, shipment_id=shipment_id, **fact,
    )
    digest = content_digest(content)
    version = digest[:16]
    if (isinstance(existing, Mapping)
            and existing.get("version") == version
            and existing.get("content_sha256") == digest):
        # Identical public content: never steal an existing verification.
        return {
            "id": event_id, "version": version,
            "state": SOURCE_STATE_VERIFIED if existing.get("verified") is True
            else SOURCE_STATE_PENDING,
            "changed": False,
        }

    document: dict[str, Any] = {
        "id": event_id,
        **content,
        "version": version,
        "content_sha256": digest,
        "kind": PICKUP_KIND,
        "visibility": "CUSTOMER",
        # A staff write is a SOURCE, never an approval.
        "verified": False, "verified_at": "", "verified_by": "",
        "state": SOURCE_STATE_PENDING,
        "source": PICKUP_SOURCE,
        "recorded_at": now, "recorded_by": actor, "updated_at": now,
        "is_deleted": False,
    }
    if isinstance(existing, Mapping):
        payload = {key: value for key, value in document.items() if key != "id"}
        database[SOURCE_COLLECTION].update_one({"_id": existing.get("_id")}, {"$set": payload})
    else:
        # Tenant integrity: the same lot may have been re-assigned to another
        # customer. Its previous owner's milestone must never stay verifiable.
        database[SOURCE_COLLECTION].update_many(
            {
                "shipment_id": shipment_id, "stage_id": PICKUP_STAGE_ID,
                "customer_id": {"$ne": customer_id}, "verified": True,
            },
            {"$set": {
                "verified": False, "verified_at": "", "verified_by": "",
                "state": SOURCE_STATE_WITHDRAWN, "updated_at": now,
            }},
        )
        database[SOURCE_COLLECTION].insert_one(dict(document))
    return {"id": event_id, "version": version, "state": SOURCE_STATE_PENDING, "changed": True}
