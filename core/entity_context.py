"""Read-only Customer, Factory/Supplier, and Partner/Agent context projections.

The app does not currently have approved master stores for factories or generic
partners.  Those entities are therefore indexed from existing shipment data,
and every shipment/lot fact stays explicitly in its source-specific section.
No function in this module writes, mutates an input mapping, or aggregates
financial amounts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from core.shipment_360 import UNKNOWN
from core.shipment_dashboard import build_shipment_dashboard_view
from core.shipment_workspace import build_shipment_workspace_view


_FACTORY_ALIASES = ("factories", "factory_lots", "factory_items")
_PARTNER_ALIASES = ("partner", "partner_name", "agent", "agent_name", "agency")


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _text(value: Any, default: str = UNKNOWN) -> str:
    if value is None or value == "":
        return default
    return str(value).strip() or default


def _key(value: Any) -> str:
    return _text(value, "").casefold()


def _data(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(shipment.get("data")) or {}


def _sections(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    data = _data(shipment)
    sections: list[Mapping[str, Any]] = [shipment, data]
    sections.extend(
        section
        for key in ("0.0", "1.2", "2.6", "2.7", "3.4")
        for section in [_mapping(data.get(key))]
        if section is not None
    )
    return sections


def _first(shipment: Mapping[str, Any], aliases: Iterable[str], default: str = UNKNOWN) -> str:
    for section in _sections(shipment):
        for alias in aliases:
            value = section.get(alias)
            if value not in (None, ""):
                return _text(value, default)
    return default


def _records(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if any(key in value for key in ("id", "name", "label", "type", "status", "state", "factory_name")):
            return [value]
        return [item for item in value.values() if isinstance(item, Mapping)]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _collection(shipment: Mapping[str, Any], aliases: Iterable[str]) -> Any:
    for section in _sections(shipment):
        for alias in aliases:
            if alias in section:
                return section.get(alias)
    return None


def _shipment_id(shipment: Mapping[str, Any]) -> str:
    context_key = shipment.get("__context_shipment_key")
    if context_key not in (None, ""):
        # Keep legacy whitespace/tab characters intact: this is the exact
        # dictionary key used by Dashboard when opening the shipment.
        return str(context_key)
    return _text(_first(shipment, ("shipment_id", "id", "_id", "shipment_code", "code")), UNKNOWN)


def _shipment_rows(shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if isinstance(shipments, Mapping):
        # Dashboard navigation uses the current mapping key. Legacy payloads
        # can retain an older id/code, so keep the key in a copied read model
        # without mutating the source shipment document.
        return [
            {**item, "__context_shipment_key": str(key)}
            for key, item in shipments.items()
            if isinstance(item, Mapping)
        ]
    else:
        values = shipments
    return [item for item in values if isinstance(item, Mapping)]


def _related_row(shipment: Mapping[str, Any], dashboard: Mapping[str, Any] | None = None) -> dict[str, Any]:
    dashboard = dashboard or build_shipment_dashboard_view(shipment)
    return {
        "shipment_id": _shipment_id(shipment),
        "status": dashboard.get("operational_status_label") or UNKNOWN,
        "status_code": dashboard.get("operational_status") or UNKNOWN,
        "required_date": dashboard.get("required_date_label") or UNKNOWN,
        "planned_date": dashboard.get("planned_date_label") or UNKNOWN,
        "attention": (dashboard.get("next_action") or {}).get("label") or UNKNOWN,
        "attention_detail": (dashboard.get("next_action") or {}).get("detail") or UNKNOWN,
        "source": "shipment document + core.shipment_dashboard",
    }


def _master_fields(record: Mapping[str, Any] | None) -> dict[str, str]:
    record = record or {}
    return {
        "contact": _text(record.get("contact_person") or record.get("contact") or record.get("phone")),
        "phone": _text(record.get("phone") or record.get("phone_number")),
        "email": _text(record.get("email")),
        "address": _text(record.get("address")),
        "tax_code": _text(record.get("tax_code") or record.get("tax")),
    }


def _customer_match(shipment: Mapping[str, Any], customer_id: str, customer_name: str) -> bool:
    if customer_id and _key(shipment.get("customer_id")) == _key(customer_id):
        return True
    shipment_name = _first(shipment, ("customer", "customer_name", "client", "client_name"), "")
    return bool(customer_name) and _key(shipment_name) == _key(customer_name)


def build_customer_context(
    customer_id: str,
    customer: Mapping[str, Any] | None,
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one customer workspace without changing customer or shipment data."""

    customer = customer if isinstance(customer, Mapping) else {}
    customer_name = _text(customer.get("name") or customer.get("customer_name"), customer_id or UNKNOWN)
    related = [
        _related_row(shipment)
        for shipment in _shipment_rows(shipments)
        if _customer_match(shipment, customer_id, customer_name)
    ]
    related.sort(key=lambda row: str(row.get("shipment_id")))
    active = [row for row in related if row.get("status_code") not in {"done", "cancel"}]
    attention = [row for row in related if row.get("attention") not in (None, UNKNOWN)]
    gaps = [label for label, value in {
        "contact": customer.get("contact_person") or customer.get("phone"),
        "email": customer.get("email"),
        "address": customer.get("address"),
    }.items() if value in (None, "")]
    return {
        "entity_type": "customer",
        "entity_key": customer_id or customer_name,
        "identity": {
            "name": customer_name,
            "id": _text(customer.get("id") or customer_id),
            "source": "customer master" if customer else UNKNOWN,
        },
        "master": {
            "fields": _master_fields(customer),
            "source": "db_customers / customer master" if customer else UNKNOWN,
            "status": "KNOWN" if customer else UNKNOWN,
        },
        "requirements": [
            {"label": "Contact person", "value": _text(customer.get("contact_person"))},
            {"label": "Delivery expectation", "value": "See shipment-specific required dates" if related else UNKNOWN},
            {"label": "Commercial context", "value": "Existing shipment records only; no balance is derived" if related else UNKNOWN},
        ],
        "shipments": related,
        "active_shipments": active,
        "attention_shipments": attention,
        "history_shipments": [row for row in related if row not in active],
        "gaps": gaps or ["No known customer master gaps"],
        "read_only": True,
    }


def _factory_name(item: Mapping[str, Any]) -> str:
    return _text(item.get("factory") or item.get("factory_name") or item.get("supplier") or item.get("supplier_name"), "")


def _factory_row(shipment: Mapping[str, Any], item: Mapping[str, Any], index: int) -> dict[str, Any]:
    return {
        "shipment_id": _shipment_id(shipment),
        "lot": _text(item.get("lot") or item.get("lot_id") or item.get("factory_lot"), f"Lot {index}"),
        "product": _text(item.get("product") or item.get("product_name")),
        "quantity": _text(item.get("quantity") or item.get("packages")),
        "weight": _text(item.get("weight") or item.get("weight_kg")),
        "cbm": _text(item.get("cbm") or item.get("volume_cbm")),
        "ready_date": _text(item.get("factory_ready_date") or item.get("ready_date")),
        "readiness": (
            "READY" if item.get("ready") is True or item.get("is_ready") is True
            else "NOT READY" if item.get("ready") is False or item.get("is_ready") is False
            else UNKNOWN
        ),
        "pickup_contact": _text(item.get("pickup_contact") or item.get("contact")),
        "source": "shipment/lot-specific data",
        "completeness": (
            "COMPLETE" if item.get("required_information_complete") is True
            else "NEEDS DATA" if item.get("required_information_complete") is False
            else UNKNOWN
        ),
    }


def build_factory_context(
    factory_name: str,
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a multi-factory workspace with lot facts kept shipment-specific."""

    lots: list[dict[str, Any]] = []
    related: dict[str, dict[str, Any]] = {}
    for shipment in _shipment_rows(shipments):
        dashboard = build_shipment_dashboard_view(shipment)
        found = False
        for index, item in enumerate(_records(_collection(shipment, _FACTORY_ALIASES)), start=1):
            if _key(_factory_name(item)) != _key(factory_name):
                continue
            found = True
            lots.append(_factory_row(shipment, item, index))
        if found:
            related[_shipment_id(shipment)] = _related_row(shipment, dashboard)
    lots.sort(key=lambda row: (str(row["shipment_id"]), str(row["lot"])))
    related_rows = sorted(related.values(), key=lambda row: str(row["shipment_id"]))
    master_status = UNKNOWN
    gaps = ["Factory master record is not available"]
    if lots:
        gaps = [
            "Factory address/contact master data UNKNOWN",
            "Confirm next ready/pickup coordination from lot rows",
        ]
    return {
        "entity_type": "factory",
        "entity_key": factory_name or UNKNOWN,
        "identity": {"name": factory_name or UNKNOWN, "id": UNKNOWN, "source": "shipment/lot index"},
        "master": {
            "fields": {"contact": UNKNOWN, "phone": UNKNOWN, "email": UNKNOWN, "address": UNKNOWN, "tax_code": UNKNOWN},
            "source": "No approved factory master store in current scope",
            "status": master_status,
        },
        "lots": lots,
        "shipments": related_rows,
        "gaps": gaps,
        "next_coordination": "Confirm ready date, pickup contact, and missing lot fields" if lots else UNKNOWN,
        "read_only": True,
    }


def _partner_record(shipment: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for section in _sections(shipment):
        for alias in _PARTNER_ALIASES:
            value = section.get(alias)
            if isinstance(value, Mapping):
                return value
    return None


def _partner_name(shipment: Mapping[str, Any]) -> str:
    record = _partner_record(shipment)
    if record:
        return _text(record.get("name") or record.get("partner_name") or record.get("agent_name"), "")
    return _first(shipment, ("partner", "partner_name", "agent", "agent_name"), "")


def build_partner_context(
    partner_name: str,
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a generic partner/agent context without creating an aggregate balance."""

    related: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    finance: list[dict[str, Any]] = []
    roles: set[str] = set()
    for shipment in _shipment_rows(shipments):
        if _key(_partner_name(shipment)) != _key(partner_name):
            continue
        dashboard = build_shipment_dashboard_view(shipment)
        workspace = build_shipment_workspace_view(shipment, financial_view=dashboard.get("financial_projection"))
        record = _partner_record(shipment) or {}
        role = _text(record.get("role") or record.get("type") or _first(shipment, ("partner_role", "agent_role")), UNKNOWN)
        roles.add(role)
        row = _related_row(shipment, dashboard)
        row.update({
            "role": role,
            "operational_context": _text((workspace.get("context") or {}).get("pickup_contact")),
            "route": f"{_text((workspace.get('route') or {}).get('pol'))} -> {_text((workspace.get('route') or {}).get('pod'))}",
        })
        related.append(row)
        for document in workspace.get("documents", []):
            documents.append({"shipment_id": row["shipment_id"], **dict(document)})
        finance.append({
            "shipment_id": row["shipment_id"],
            "status": dashboard.get("financial_status") or UNKNOWN,
            "label": dashboard.get("financial_label") or UNKNOWN,
            "source": "canonical per-shipment financial projection",
        })
    related.sort(key=lambda row: str(row["shipment_id"]))
    documents.sort(key=lambda row: (str(row["shipment_id"]), str(row.get("document"))))
    finance.sort(key=lambda row: str(row["shipment_id"]))
    return {
        "entity_type": "partner",
        "entity_key": partner_name or UNKNOWN,
        "identity": {"name": partner_name or UNKNOWN, "id": UNKNOWN, "source": "shipment partner/agent records"},
        "master": {
            "fields": {"contact": UNKNOWN, "phone": UNKNOWN, "email": UNKNOWN, "address": UNKNOWN, "tax_code": UNKNOWN},
            "source": "No approved generic partner master store in current scope",
            "status": UNKNOWN,
        },
        "roles": sorted(roles) or [UNKNOWN],
        "shipments": related,
        "documents": documents,
        "financial_projection": finance,
        "financial_note": "Per-shipment canonical projection only; no partner balance or debt is derived here.",
        "gaps": ["Partner master contact data UNKNOWN", "Confirm role/contact evidence when source is available"],
        "read_only": True,
    }


def list_context_entities(
    customers: Mapping[str, Mapping[str, Any]],
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Return lightweight entity options for the workspace selector."""

    options = [
        {"entity_type": "customer", "entity_key": str(key), "label": _text(value.get("name"), str(key))}
        for key, value in customers.items()
        if isinstance(value, Mapping)
    ]
    factory_names: set[str] = set()
    partner_names: set[str] = set()
    for shipment in _shipment_rows(shipments):
        for item in _records(_collection(shipment, _FACTORY_ALIASES)):
            name = _factory_name(item)
            if name:
                factory_names.add(name)
        partner = _partner_name(shipment)
        if partner:
            partner_names.add(partner)
    options.extend({"entity_type": "factory", "entity_key": name, "label": name} for name in sorted(factory_names, key=str.casefold))
    options.extend({"entity_type": "partner", "entity_key": name, "label": name} for name in sorted(partner_names, key=str.casefold))
    return options


def build_entity_context(
    entity_type: str,
    entity_key: str,
    *,
    customers: Mapping[str, Mapping[str, Any]],
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Dispatch the public entity context contract."""

    normalized = str(entity_type or "").casefold()
    if normalized == "customer":
        customer = customers.get(entity_key) if isinstance(customers, Mapping) else None
        return build_customer_context(entity_key, customer, shipments)
    if normalized == "factory":
        return build_factory_context(entity_key, shipments)
    if normalized == "partner":
        return build_partner_context(entity_key, shipments)
    raise ValueError(f"Unsupported entity type: {entity_type}")


__all__ = [
    "build_customer_context",
    "build_entity_context",
    "build_factory_context",
    "build_partner_context",
    "list_context_entities",
]
