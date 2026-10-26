"""HEXA V0: read-only, fail-closed publication from TT to one customer.

Ported unchanged (apart from this provenance note) from trial commit
``4c4600aa52f7b24f8d1eabf9c7df4d248e9fcb52``.  This is a pure projection, not
an HTTP route, authentication provider, or file server.  The caller must
supply a server-authenticated customer principal and a TT-approved publication
manifest read from trusted storage.  Neither may be constructed from customer
query/body parameters.  Nothing here writes records.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

PUBLICATION_SCHEMA = "hexa-customer-publication/v0"
ALLOWED_DOCUMENT_KINDS = frozenset({
    "PL", "PI", "BOOKING", "SI", "BL", "AWB", "POD", "CUSTOMS",
    "CUSTOMER_INVOICE", "CUSTOMER_CONTRACT", "PAYMENT_REQUEST",
})
ALLOWED_MODES = frozenset({"ROAD", "SEA", "AIR", "RAIL"})


class PublicationDenied(PermissionError):
    """Indistinguishable denial for unknown, unpublished or foreign resources."""

    def __init__(self) -> None:
        super().__init__("CUSTOMER_RESOURCE_UNAVAILABLE")


def _id(value: Any) -> str:
    return str(value).strip() if isinstance(value, (str, int)) and not isinstance(value, bool) else ""


def _map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _approved(shipment: Mapping[str, Any], principal: Mapping[str, Any],
              publication: Mapping[str, Any]) -> tuple[str, str]:
    # A customer cannot be a Logistics 'viewer': that role has finance_view.
    cust = _id(principal.get("customer_id"))
    shipment_id = _id(shipment.get("shipment_id") or shipment.get("id"))
    if not (principal.get("authenticated") is True
            and principal.get("kind") == "customer"
            and cust and shipment_id
            and cust == _id(shipment.get("customer_id"))
            and cust == _id(publication.get("customer_id"))
            and shipment_id == _id(publication.get("shipment_id"))
            and publication.get("state") == "PUBLISHED"
            and _id(publication.get("approved_by"))
            and _id(publication.get("approved_at"))):
        raise PublicationDenied()
    return cust, shipment_id


def _belongs(row: Any, cust: str, shipment_id: str) -> bool:
    item = _map(row)
    return bool(item and _id(item.get("customer_id")) == cust
                and _id(item.get("shipment_id")) == shipment_id)


def _money_or_unknown(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    n = float(value)
    return n if math.isfinite(n) and n >= 0 else None


def _public_docs(documents: Sequence[Mapping[str, Any]], publication: Mapping[str, Any],
                 cust: str, shipment_id: str) -> list[dict[str, Any]]:
    allowed = _map(publication.get("document_versions"))
    result = []
    for d in documents:
        if not _belongs(d, cust, shipment_id):
            continue
        document_id, version, kind = _id(d.get("id")), _id(d.get("version")), _id(d.get("kind"))
        if (document_id and version and kind in ALLOWED_DOCUMENT_KINDS
                and allowed.get(document_id) == version
                and d.get("status") == "AVAILABLE"
                and d.get("visibility") == "CUSTOMER"
                and d.get("verified") is True):
            result.append({"id": document_id, "version": version, "kind": kind,
                           "title": _id(d.get("public_title")) or kind})
    return result[:100]


def _public_events(events: Sequence[Mapping[str, Any]], publication: Mapping[str, Any],
                   cust: str, shipment_id: str) -> list[dict[str, Any]]:
    allowed = _map(publication.get("event_versions"))
    result = []
    for e in events:
        if not _belongs(e, cust, shipment_id):
            continue
        event_id, version = _id(e.get("id")), _id(e.get("version"))
        if (event_id and version and allowed.get(event_id) == version
                and e.get("verified") is True
                and _id(e.get("verified_at"))
                and e.get("visibility") == "CUSTOMER"
                and _id(e.get("public_title"))
                and _id(e.get("occurred_at"))):
            result.append({"id": event_id, "version": version,
                           "stage": _id(e.get("stage_id")),
                           "title": _id(e.get("public_title")),
                           "occurred_at": _id(e.get("occurred_at"))})
    return sorted(result[:100], key=lambda x: (x["occurred_at"], x["id"]), reverse=True)


def _public_quote(quote: Mapping[str, Any] | None, shipment: Mapping[str, Any],
                  publication: Mapping[str, Any], cust: str) -> dict[str, Any] | None:
    q, released = _map(quote), _map(publication.get("quote"))
    quote_id, version = _id(q.get("id")), _id(q.get("version"))
    if not (quote_id and version and _id(shipment.get("quote_id")) == quote_id
            and _id(q.get("customer_id")) == cust
            and quote_id == _id(released.get("id"))
            and version == _id(released.get("version"))
            and q.get("status") in {"SENT", "ACCEPTED"}):
        return None
    # This is the *customer selling* total recorded by TT's quotation engine.
    # Do not include buy/cost/margin, raw Excel goods, FX, or internal ledgers.
    total = _money_or_unknown(_map(q.get("calculation")).get("selling_price_total_vnd"))
    return {"id": quote_id, "version": version, "status": q["status"],
            "selling_total_vnd": total}


def build_customer_publication(*, shipment: Mapping[str, Any],
                               principal: Mapping[str, Any],
                               publication: Mapping[str, Any],
                               events: Sequence[Mapping[str, Any]] = (),
                               documents: Sequence[Mapping[str, Any]] = (),
                               quote: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a JSON-safe public allowlist. No raw shipment/document object escapes."""
    cust, shipment_id = _approved(shipment, principal, publication)
    mode = _id(shipment.get("transport_mode")).upper()
    return {"schema": PUBLICATION_SCHEMA, "reference": shipment_id,
            "transport_mode": mode if mode in ALLOWED_MODES else None,
            "timeline": _public_events(events, publication, cust, shipment_id),
            "documents": _public_docs(documents, publication, cust, shipment_id),
            "quote": _public_quote(quote, shipment, publication, cust)}


def authorize_document_download(*, shipment: Mapping[str, Any],
                                principal: Mapping[str, Any],
                                publication: Mapping[str, Any],
                                document: Mapping[str, Any],
                                requested_id: str, requested_version: str) -> None:
    """Recheck the exact document and version before *any* storage-byte read.

    G1 does not expose downloads.  This function is retained with the trial
    business module so a later, separately approved phase cannot bypass the
    exact-version rule when it does.
    """
    cust, shipment_id = _approved(shipment, principal, publication)
    safe = _public_docs([document], publication, cust, shipment_id)
    if not (safe and safe[0]["id"] == requested_id
            and safe[0]["version"] == requested_version):
        raise PublicationDenied()
