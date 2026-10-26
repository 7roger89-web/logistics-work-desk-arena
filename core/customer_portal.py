"""G1 customer portal: the single server-side principal and read boundary.

There is intentionally no browser-controlled ``customer_id``, shipment code,
publication version, or identity-emulation input here.  The ONLY way to obtain a
customer principal is :func:`build_customer_principal`, which resolves a
verified email against the Owner-allowlisted field on the existing
``customers`` collection.  Staging tests may call that same function with a
test-granted verified email and an explicit in-memory database handle; the
production path obtains the email from Streamlit's verified OIDC session.

Reads use narrow MongoDB projections and the trial's tested HEXA allowlist.
The internal Logistics view-model is never built for a customer.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Mapping

from core.database import get_db
from core.hexa_customer_publication import (
    PUBLICATION_SCHEMA,
    PublicationDenied,
    build_customer_publication,
)

LOGGER = logging.getLogger("logistics.customer_portal")

PORTAL_ACCESS_EMAIL_FIELD = "portal_access_email"
PUBLICATION_COLLECTION = "customer_publications"
MAX_CUSTOMER_LOTS = 20
MAX_INTEGRITY_SCAN = 200

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CUSTOMER_PROJECTION = {"_id": 0, "id": 1, "name": 1, PORTAL_ACCESS_EMAIL_FIELD: 1}
_CUSTOMER_ID_PROJECTION = {"_id": 0, "id": 1}
# Deliberately narrow: internal cost, margin, private documents, notes and the
# full Logistics view-model never cross this boundary.
_SHIPMENT_PROJECTION = {
    "_id": 0,
    "id": 1,
    "customer_id": 1,
    "transport_mode": 1,
    "customer_publication_version": 1,
}
_MANIFEST_PROJECTION = {
    "_id": 0,
    "schema": 1,
    "customer_id": 1,
    "shipment_id": 1,
    "version": 1,
    "state": 1,
    "approved_by": 1,
    "approved_at": 1,
    "event_versions": 1,
    "document_versions": 1,
    "quote": 1,
}


class PortalAccessDenied(PermissionError):
    """Generic denial; never distinguish unknown email from a foreign tenant."""

    def __init__(self) -> None:
        super().__init__("CUSTOMER_RESOURCE_UNAVAILABLE")


class PortalDataError(RuntimeError):
    """Trusted data is unavailable or inconsistent; fail closed without detail."""

    def __init__(self) -> None:
        super().__init__("CUSTOMER_PORTAL_DATA_UNAVAILABLE")


@dataclass(frozen=True)
class CustomerPrincipal:
    customer_id: str
    email: str
    display_name: str

    def publication_principal(self) -> dict[str, Any]:
        """The minimal principal shape the HEXA allowlist expects."""
        return {
            "authenticated": True,
            "kind": "customer",
            "customer_id": self.customer_id,
        }


@dataclass(frozen=True)
class PublicationCard:
    """A customer-safe card; no raw shipment, manifest or view-model object."""

    reference: str
    status_label: str
    transport_mode: str | None
    publication_version: str
    approved_at: str


@dataclass(frozen=True)
class CustomerDashboardView:
    principal: CustomerPrincipal
    cards: tuple[PublicationCard, ...]
    denied_lots: int = 0
    data_issues: int = 0

    @property
    def no_lots(self) -> bool:
        return not self.cards


def clean_id(value: Any) -> str:
    if isinstance(value, bool):
        return ""
    if isinstance(value, (str, int)):
        return str(value).strip()
    return ""


def safe_text(value: Any, limit: int = 80) -> str:
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text[:limit]


def normalize_email(value: Any) -> str:
    """Canonical, exact-match email form. Invalid values are never queried."""
    if not isinstance(value, str):
        return ""
    email = value.strip().lower()
    if not email or len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        return ""
    return email


def _resolve_db(db: Any) -> Any:
    if db is not None:
        return db
    try:
        resolved = get_db()
    except Exception as exc:  # noqa: BLE001 - identity/config errors fail closed
        LOGGER.warning("CUSTOMER_PORTAL_DB_UNAVAILABLE type=%s", type(exc).__name__)
        raise PortalDataError() from None
    if resolved is None:
        raise PortalDataError()
    return resolved


def _active_email_matches(db: Any, email: str) -> list[Mapping[str, Any]]:
    query = {PORTAL_ACCESS_EMAIL_FIELD: email, "is_deleted": {"$ne": True}}
    rows = list(db.customers.find(query, _CUSTOMER_PROJECTION).limit(2))
    return [row for row in rows if isinstance(row, Mapping)]


def build_customer_principal(*, verified_email: str, db: Any = None) -> CustomerPrincipal:
    """Build THE customer principal from a verified email, never from a browser id.

    The email must already have been verified by the caller: Streamlit OIDC in
    the real path, or the staging test harness granting a test identity.  The
    canonical ``customers.id`` is looked up server-side using the Owner's
    explicit ``portal_access_email`` allowlist.  Contact ``email`` is ignored.
    """
    email = normalize_email(verified_email)
    if not email:
        raise PortalAccessDenied()
    database = _resolve_db(db)
    try:
        matches = _active_email_matches(database, email)
    except Exception as exc:  # noqa: BLE001 - keep the message generic
        LOGGER.warning("CUSTOMER_PORTAL_PRINCIPAL_READ_FAILED type=%s", type(exc).__name__)
        raise PortalDataError() from None
    if len(matches) != 1:
        LOGGER.warning("CUSTOMER_PORTAL_PRINCIPAL_DENIED reason=email_not_unique_or_not_allowed")
        raise PortalAccessDenied()
    row = matches[0]
    if normalize_email(row.get(PORTAL_ACCESS_EMAIL_FIELD)) != email:
        LOGGER.warning("CUSTOMER_PORTAL_PRINCIPAL_DENIED reason=noncanonical_allowed_email")
        raise PortalDataError()
    customer_id = clean_id(row.get("id"))
    if not customer_id:
        LOGGER.warning("CUSTOMER_PORTAL_PRINCIPAL_DENIED reason=missing_customers_id")
        raise PortalDataError()
    return CustomerPrincipal(
        customer_id=customer_id,
        email=email,
        display_name=safe_text(row.get("name")) or "Khách hàng",
    )


def _assert_principal_still_allowed(db: Any, principal: CustomerPrincipal) -> None:
    """Re-check on every render/refresh so Owner revocation takes effect."""
    try:
        matches = _active_email_matches(db, principal.email)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_REVALIDATION_FAILED type=%s", type(exc).__name__)
        raise PortalDataError() from None
    if len(matches) != 1 or clean_id(matches[0].get("id")) != principal.customer_id:
        LOGGER.warning("CUSTOMER_PORTAL_REVALIDATION_DENIED")
        raise PortalAccessDenied()


def _known_customer_ids(db: Any) -> set[str]:
    try:
        rows = db.customers.find({"is_deleted": {"$ne": True}}, _CUSTOMER_ID_PROJECTION).limit(500)
        return {cid for cid in (clean_id(row.get("id")) for row in rows if isinstance(row, Mapping)) if cid}
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_CUSTOMER_SCAN_FAILED type=%s", type(exc).__name__)
        raise PortalDataError() from None


def _scan_data_integrity(db: Any, known_customer_ids: set[str]) -> int:
    """Record missing/unknown shipment.customer_id for INTERNAL review only.

    The projection contains no name, cost, notes or documents.  A broken lot is
    never attached by business name and never rendered to any customer; only a
    generic data-error notice reaches the UI.
    """
    try:
        rows = db.shipments.find(
            {"is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "customer_id": 1},
        ).limit(MAX_INTEGRITY_SCAN)
        suspects: list[tuple[str, str]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                suspects.append(("(unreadable)", "invalid_row"))
                continue
            customer_id = clean_id(row.get("customer_id"))
            shipment_id = clean_id(row.get("id")) or "(no-id)"
            if not customer_id:
                suspects.append((shipment_id, "missing_customer_id"))
            elif customer_id not in known_customer_ids:
                suspects.append((shipment_id, "unknown_customer_id"))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_DATA_SCAN_FAILED type=%s", type(exc).__name__)
        return 1
    if suspects:
        LOGGER.warning(
            "CUSTOMER_PORTAL_INTERNAL_REVIEW count=%s sample=%s",
            len(suspects), suspects[:5],
        )
    return len(suspects)


def load_customer_dashboard(principal: CustomerPrincipal, *, db: Any = None) -> CustomerDashboardView:
    """Load only PUBLISHED, approved, version-pinned cards for this customer."""
    if (not isinstance(principal, CustomerPrincipal)
            or not clean_id(principal.customer_id)
            or not normalize_email(principal.email)):
        raise PortalAccessDenied()
    database = _resolve_db(db)
    _assert_principal_still_allowed(database, principal)
    known_customer_ids = _known_customer_ids(database)
    data_issues = _scan_data_integrity(database, known_customer_ids)
    denied_lots = 0
    cards: list[PublicationCard] = []

    try:
        shipment_rows = list(database.shipments.find(
            {"customer_id": principal.customer_id, "is_deleted": {"$ne": True}},
            _SHIPMENT_PROJECTION,
        ).limit(MAX_CUSTOMER_LOTS))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_SHIPMENT_READ_FAILED type=%s", type(exc).__name__)
        raise PortalDataError() from None

    for row in shipment_rows:
        if not isinstance(row, Mapping):
            data_issues += 1
            continue
        shipment_id = clean_id(row.get("id"))
        shipment_customer_id = clean_id(row.get("customer_id"))
        if (not shipment_id or shipment_customer_id != principal.customer_id
                or shipment_customer_id not in known_customer_ids):
            data_issues += 1
            LOGGER.warning(
                "CUSTOMER_PORTAL_SHIPMENT_REJECTED shipment_id=%s reason=customer_id_invalid",
                shipment_id or "(no-id)",
            )
            continue
        expected_version = clean_id(row.get("customer_publication_version"))
        if not expected_version:
            denied_lots += 1
            LOGGER.warning(
                "CUSTOMER_PORTAL_PUBLICATION_DENIED shipment_id=%s reason=missing_pinned_version",
                shipment_id,
            )
            continue
        try:
            manifest = database[PUBLICATION_COLLECTION].find_one(
                {
                    "customer_id": principal.customer_id,
                    "shipment_id": shipment_id,
                    "version": expected_version,
                    "state": "PUBLISHED",
                    "is_deleted": {"$ne": True},
                },
                _MANIFEST_PROJECTION,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("CUSTOMER_PORTAL_MANIFEST_READ_FAILED type=%s", type(exc).__name__)
            raise PortalDataError() from None
        if not isinstance(manifest, Mapping):
            denied_lots += 1
            LOGGER.warning(
                "CUSTOMER_PORTAL_PUBLICATION_DENIED shipment_id=%s reason=no_approved_manifest",
                shipment_id,
            )
            continue
        if (clean_id(manifest.get("schema")) != PUBLICATION_SCHEMA
                or clean_id(manifest.get("version")) != expected_version):
            denied_lots += 1
            LOGGER.warning(
                "CUSTOMER_PORTAL_PUBLICATION_DENIED shipment_id=%s reason=schema_or_version_mismatch",
                shipment_id,
            )
            continue
        shipment = {
            "id": shipment_id,
            "customer_id": principal.customer_id,
            "transport_mode": row.get("transport_mode"),
        }
        try:
            public = build_customer_publication(
                shipment=shipment,
                principal=principal.publication_principal(),
                publication=dict(manifest),
                events=(),
                documents=(),
                quote=None,
            )
        except PublicationDenied:
            denied_lots += 1
            LOGGER.warning(
                "CUSTOMER_PORTAL_PUBLICATION_DENIED shipment_id=%s reason=hexa_allowlist",
                shipment_id,
            )
            continue
        if (public.get("schema") != PUBLICATION_SCHEMA
                or clean_id(public.get("reference")) != shipment_id):
            data_issues += 1
            continue
        cards.append(PublicationCard(
            reference=shipment_id,
            status_label="ĐÃ XÁC NHẬN",
            transport_mode=safe_text(public.get("transport_mode"), 8).upper() or None,
            publication_version=expected_version,
            approved_at=safe_text(manifest.get("approved_at"), 40) or "Không rõ",
        ))
    return CustomerDashboardView(
        principal=principal,
        cards=tuple(cards),
        denied_lots=denied_lots,
        data_issues=data_issues,
    )


def list_customer_portal_access(*, db: Any = None) -> list[dict[str, str]]:
    """Internal Owner control only; returns a tiny customer-profile projection."""
    database = _resolve_db(db)
    try:
        rows = database.customers.find(
            {"is_deleted": {"$ne": True}}, _CUSTOMER_PROJECTION
        ).sort("id", 1).limit(200)
        return [
            {
                "id": clean_id(row.get("id")),
                "name": safe_text(row.get("name")) or "Khách hàng",
                "portal_access_email": safe_text(row.get(PORTAL_ACCESS_EMAIL_FIELD), 254),
            }
            for row in rows
            if isinstance(row, Mapping) and clean_id(row.get("id"))
        ]
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_OWNER_LIST_FAILED type=%s", type(exc).__name__)
        raise PortalDataError() from None


def set_customer_portal_access_email(
    customer_id: str,
    email: str,
    *,
    actor_role: str,
    db: Any = None,
) -> tuple[bool, str]:
    """Owner/Admin grants or revokes ONE email on the existing customer profile.

    This does not create a second customer collection or an independent mapping
    table.  An empty email removes the field: the default is NO portal access.
    """
    if str(actor_role or "").strip().lower() != "admin":
        return False, "Chỉ Owner/Admin được thay đổi quyền truy cập cổng khách hàng."
    canonical_id = clean_id(customer_id)
    if not canonical_id:
        return False, "Mã khách hàng không hợp lệ."
    raw_email = "" if email is None else str(email).strip()
    granted_email = normalize_email(raw_email) if raw_email else ""
    if raw_email and not granted_email:
        return False, "Email không hợp lệ."
    try:
        database = _resolve_db(db)
        if granted_email:
            duplicate = database.customers.find_one(
                {
                    PORTAL_ACCESS_EMAIL_FIELD: granted_email,
                    "id": {"$ne": canonical_id},
                    "is_deleted": {"$ne": True},
                },
                _CUSTOMER_ID_PROJECTION,
            )
            if duplicate:
                return False, "Email này đã được cấp cho một hồ sơ khách hàng khác."
        update = (
            {"$set": {PORTAL_ACCESS_EMAIL_FIELD: granted_email}}
            if granted_email
            else {"$unset": {PORTAL_ACCESS_EMAIL_FIELD: ""}}
        )
        result = database.customers.update_one(
            {"id": canonical_id, "is_deleted": {"$ne": True}}, update
        )
        if getattr(result, "matched_count", 0) != 1:
            return False, "Không tìm thấy hồ sơ khách hàng."
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("CUSTOMER_PORTAL_OWNER_UPDATE_FAILED type=%s", type(exc).__name__)
        return False, "Không cập nhật được hồ sơ khách hàng."
    LOGGER.info(
        "CUSTOMER_PORTAL_ACCESS_CHANGED customer_id=%s granted=%s",
        canonical_id, bool(granted_email),
    )
    return True, "Đã cập nhật email truy cập portal." if granted_email else "Đã thu hồi quyền truy cập portal."
