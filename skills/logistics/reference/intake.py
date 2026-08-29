"""Source-preserving customer-intake normalization for logistics requests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .common import (
    NEEDS_CUSTOMER_INPUT,
    READY,
    UNKNOWN,
    append_unique,
    clone_mapping,
    first_present,
    is_known,
    is_present,
)


def _section(request: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        candidate = request.get(key)
        if isinstance(candidate, Mapping):
            return clone_mapping(candidate)
    return {}


def _field(
    section: Mapping[str, Any], aliases: tuple[str, ...], missing_path: str, missing: list[str]
) -> Any:
    value = first_present(section, *aliases)
    if not is_known(value):
        append_unique(missing, missing_path)
        return UNKNOWN
    return value


def _optional(section: Mapping[str, Any], aliases: tuple[str, ...]) -> Any:
    value = first_present(section, *aliases)
    return value if is_present(value) else UNKNOWN


def _normalize_factory_lots(request: Mapping[str, Any], missing: list[str]) -> list[dict[str, Any]]:
    raw_lots = request.get("factory_lots")
    if isinstance(raw_lots, list):
        lots = [clone_mapping(item) for item in raw_lots if isinstance(item, Mapping)]
    elif isinstance(raw_lots, Mapping):
        lots = [clone_mapping(raw_lots)]
    else:
        singular = request.get("factory")
        lots = [clone_mapping(singular)] if isinstance(singular, Mapping) else [{}]

    if not lots:
        lots = [{}]

    normalized: list[dict[str, Any]] = []
    for index, lot in enumerate(lots, start=1):
        prefix = f"factory_lots[{index - 1}]"
        normalized.append(
            {
                "factory_name": _field(lot, ("factory_name", "name", "factory"), f"{prefix}.factory_name", missing),
                "pickup_address": _field(
                    lot, ("pickup_address", "pickup", "address"), f"{prefix}.pickup_address", missing
                ),
                "contact": _field(lot, ("contact", "contact_person", "contact_name"), f"{prefix}.contact", missing),
                "phone": _field(lot, ("phone", "contact_phone"), f"{prefix}.phone", missing),
                "cargo_ready_date": _field(
                    lot, ("cargo_ready_date", "ready_date", "cargo_ready"), f"{prefix}.cargo_ready_date", missing
                ),
                "export_capability": _optional(lot, ("export_capability", "can_export")),
                "invoice_payment_currency": _optional(
                    lot, ("invoice_payment_currency", "payment_currency", "currency_requirement")
                ),
                "notes": _optional(lot, ("notes", "factory_notes")),
            }
        )
    return normalized


def normalize_customer_intake(request: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize an explicit customer request into a next-step checklist.

    The function copies values only.  It does not infer CBM, Incoterms, route,
    goods classification, export capability, or verified shipment facts.
    """

    source = clone_mapping(request)
    missing: list[str] = []

    customer = _section(source, "customer", "customer_info", "client")
    shipment = _section(source, "shipment", "shipment_requirements")
    cargo = _section(source, "cargo", "cargo_details", "goods")
    commercial = _section(source, "commercial_requirements", "commercial", "requirements")

    result = {
        "status": READY,
        "customer": {
            "company": _field(customer, ("company", "customer", "customer_company"), "customer.company", missing),
            "contact_person": _field(
                customer, ("contact_person", "contact", "name"), "customer.contact_person", missing
            ),
            "phone": _field(customer, ("phone", "telephone", "mobile"), "customer.phone", missing),
            "sales_owner": _field(customer, ("sales_owner", "owner", "sales"), "customer.sales_owner", missing),
        },
        "shipment": {
            "origin": _field(shipment, ("origin", "origin_city", "from"), "shipment.origin", missing),
            "destination": _field(
                shipment, ("destination", "destination_city", "to"), "shipment.destination", missing
            ),
            "incoterm": _field(shipment, ("incoterm", "incoterms"), "shipment.incoterm", missing),
            "transport_mode": _field(
                shipment, ("transport_mode", "mode", "transport"), "shipment.transport_mode", missing
            ),
            "requested_delivery_date": _field(
                shipment,
                ("requested_delivery_date", "delivery_date", "requested_date"),
                "shipment.requested_delivery_date",
                missing,
            ),
            "goods_description": _field(
                shipment, ("goods_description", "goods", "description"), "shipment.goods_description", missing
            ),
        },
        "cargo": {
            "package_count": _field(
                cargo, ("package_count", "packages", "pieces"), "cargo.package_count", missing
            ),
            "package_type": _field(cargo, ("package_type", "packing", "packaging"), "cargo.package_type", missing),
            "dimensions": _field(cargo, ("dimensions", "size"), "cargo.dimensions", missing),
            "cbm": _field(cargo, ("cbm", "volume"), "cargo.cbm", missing),
            "gross_weight": _field(
                cargo, ("gross_weight", "weight", "gross_kg"), "cargo.gross_weight", missing
            ),
            "chargeable_basis": _optional(cargo, ("chargeable_basis", "charge_basis", "billable_basis")),
            "special_handling": _optional(cargo, ("special_handling", "handling")),
            "dangerous_or_restricted_goods": _optional(
                cargo, ("dangerous_or_restricted_goods", "dangerous_goods", "restricted_goods", "dg")
            ),
        },
        "factory_lots": _normalize_factory_lots(source, missing),
        "commercial_requirements": {
            "importer_entity": _field(
                commercial, ("importer_entity", "importer", "importing_entity"), "commercial_requirements.importer_entity", missing
            ),
            "customs_requirement": _field(
                commercial, ("customs_requirement", "customs", "customs_service"), "commercial_requirements.customs_requirement", missing
            ),
            "entrusted_import_requirement": _field(
                commercial,
                ("entrusted_import_requirement", "entrusted_import", "ủy_thác_nhập_khẩu"),
                "commercial_requirements.entrusted_import_requirement",
                missing,
            ),
            "payment_requirement": _field(
                commercial, ("payment_requirement", "payment", "factory_payment"), "commercial_requirements.payment_requirement", missing
            ),
            "requested_quotation_currency": _field(
                commercial,
                ("requested_quotation_currency", "quotation_currency", "quote_currency"),
                "commercial_requirements.requested_quotation_currency",
                missing,
            ),
            "customer_specific_notes": _optional(
                commercial, ("customer_specific_notes", "notes", "customer_notes")
            ),
        },
        "missing_information": missing,
        "authority": {
            "customer_message_verified": False,
            "values_are": "customer-provided-or-UNKNOWN",
            "shipment_creation": False,
        },
    }

    if missing:
        result["status"] = NEEDS_CUSTOMER_INPUT
    return result
