"""Bounded read-only adapters for Owner-approved customer publication sources.

Manifest pins candidate ids; core.hexa_customer_publication independently
checks tenant, verification, visibility and approved document kinds. This adapter never reads raw attachments, internal ledger, margin
or shipment notes. Missing public collections simply yield no approved data.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

MAX_APPROVED_PINS = 100

_EVENT_PROJECTION = {
    "_id": 0, "id": 1, "version": 1, "customer_id": 1, "shipment_id": 1,
    "stage_id": 1, "public_title": 1, "occurred_at": 1,
    "verified": 1, "verified_at": 1, "visibility": 1,
}
_DOCUMENT_PROJECTION = {
    "_id": 0, "id": 1, "version": 1, "customer_id": 1, "shipment_id": 1,
    "kind": 1, "public_title": 1, "status": 1, "visibility": 1, "verified": 1,
}
class PublicSourceUnavailable(RuntimeError):
    """Invalid or ambiguous published source: never reveal partial data."""


def _id(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return ""
    return str(value).strip()


def _versions(value: str) -> list[str | int]:
    """Accept a canonical numeric version stored as an int by the quote engine."""
    versions: list[str | int] = [value]
    if value.isascii() and value.isdecimal() and str(int(value)) == value:
        versions.append(int(value))
    return versions


def _pins(publication: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    raw = publication.get(key, {})
    if not isinstance(raw, Mapping) or len(raw) > MAX_APPROVED_PINS:
        raise PublicSourceUnavailable("invalid publication pin map")
    pins: list[dict[str, Any]] = []
    for raw_id, raw_version in raw.items():
        item_id, version = _id(raw_id), _id(raw_version)
        if not item_id or not version or len(item_id) > 128 or len(version) > 40:
            raise PublicSourceUnavailable("invalid publication pin")
        pins.append({"id": item_id, "version": {"$in": _versions(version)}})
    return pins


def _read_pinned(
    database: Any,
    collection: str,
    projection: dict[str, int],
    customer_id: str,
    shipment_id: str,
    pins: list[dict[str, Any]],
) -> list[Mapping[str, Any]]:
    if not pins:
        return []
    rows = list(database[collection].find(
        {"customer_id": customer_id, "shipment_id": shipment_id, "$or": pins},
        projection,
    ).limit(MAX_APPROVED_PINS + 1))
    if len(rows) > MAX_APPROVED_PINS:
        raise PublicSourceUnavailable("too many published source rows")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise PublicSourceUnavailable("invalid published source row")
        key = (_id(row.get("id")), _id(row.get("version")))
        if not all(key) or key in seen:
            raise PublicSourceUnavailable("ambiguous published source version")
        seen.add(key)
    return rows


def read_approved_sources(
    database: Any,
    *,
    customer_id: str,
    shipment_id: str,
    shipment_quote_id: Any,
    publication: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], Mapping[str, Any] | None]:
    """Read only exact approved candidates; never search without a release pin."""
    events = _read_pinned(
        database, "public_events", _EVENT_PROJECTION, customer_id, shipment_id,
        _pins(publication, "event_versions"),
    )
    documents = _read_pinned(
        database, "public_documents", _DOCUMENT_PROJECTION, customer_id,
        shipment_id, _pins(publication, "document_versions"),
    )
    # Owner policy 5C: no internal quote reads for customer UI.
    # Approved quote file metadata is in public_documents/CUSTOMER_QUOTE.
    return events, documents, None
