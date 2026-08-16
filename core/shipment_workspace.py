"""Read-only operational workspace projection for Shipment 360.

The projection composes fields already present in a shipment document with the
existing deterministic dashboard and financial read models.  It deliberately
does not import repositories or write helpers: missing operational evidence is
returned as ``UNKNOWN`` rather than inferred or replaced with a zero value.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

from core.shipment_dashboard import UNKNOWN, build_shipment_dashboard_view
from core.utils import parse_date_optional


_DATA_SECTIONS = ("0.0", "1.2", "2.4", "2.6", "2.7", "3.4")
_FACTORY_ALIASES = ("factories", "factory_lots", "factory_items")
_DOCUMENT_ALIASES = ("documents", "shipment_documents", "document_registry", "docs")


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _data(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(shipment.get("data")) or {}


def _sections(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    data = _data(shipment)
    result: list[Mapping[str, Any]] = [shipment, data]
    result.extend(
        section
        for key in _DATA_SECTIONS
        for section in [_as_mapping(data.get(key))]
        if section is not None
    )
    return result


def _first_value(shipment: Mapping[str, Any], aliases: Iterable[str]) -> Any:
    aliases_tuple = tuple(aliases)
    for section in _sections(shipment):
        for alias in aliases_tuple:
            value = section.get(alias)
            if value is not None and value != "":
                return value
    return None


def _text(value: Any, default: str = UNKNOWN) -> str:
    if value is None or value == "":
        return default
    return str(value).strip()


def _date_label(value: Any) -> str:
    parsed = parse_date_optional(value)
    return parsed.strftime("%d/%m/%Y") if parsed else UNKNOWN


def _records(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if any(key in value for key in ("id", "name", "label", "type", "status", "state")):
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


def _factory_lots(shipment: Mapping[str, Any]) -> tuple[list[dict[str, Any]], str]:
    raw = _collection(shipment, _FACTORY_ALIASES)
    if raw is None:
        return [], UNKNOWN

    lots: list[dict[str, Any]] = []
    for index, item in enumerate(_records(raw), start=1):
        lots.append(
            {
                "lot": item.get("lot") or item.get("lot_id") or item.get("factory_lot") or f"Lot {index}",
                "factory": _text(item.get("factory") or item.get("factory_name")),
                "product": _text(item.get("product") or item.get("product_name")),
                "quantity": item.get("quantity") or item.get("packages") or UNKNOWN,
                "ready_date": _date_label(item.get("factory_ready_date") or item.get("ready_date")),
                "pickup_contact": _text(item.get("pickup_contact") or item.get("contact")),
                "completeness": (
                    "ĐỦ DỮ LIỆU"
                    if item.get("required_information_complete") is True
                    else "CẦN BỔ SUNG"
                    if item.get("required_information_complete") is False
                    else "UNKNOWN"
                ),
                "source": "shipment.factories[*]",
            }
        )
    return lots, "KNOWN" if lots else UNKNOWN


def _document_state(value: Any) -> str:
    if isinstance(value, bool):
        return "CÓ DỮ LIỆU" if value else "CHƯA CÓ DỮ LIỆU"
    if value is None or value == "":
        return UNKNOWN
    return "CÓ DỮ LIỆU"


def _document_rows(shipment: Mapping[str, Any]) -> tuple[list[dict[str, Any]], str]:
    explicit = _collection(shipment, _DOCUMENT_ALIASES)
    if explicit is not None:
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(_records(explicit), start=1):
            present = item.get("present")
            if present is None:
                present = item.get("uploaded")
            status = _text(item.get("status") or item.get("state"), "")
            if not status:
                status = _document_state(present)
            rows.append(
                {
                    "document": _text(item.get("name") or item.get("label") or item.get("type"), f"Chứng từ {index}"),
                    "status": status,
                    "step": _text(item.get("step") or item.get("stage")),
                    "source": _text(item.get("source") or item.get("evidence") or item.get("uri")),
                    "required": _text(item.get("required")),
                }
            )
        return rows, "KNOWN" if rows else UNKNOWN

    data = _data(shipment)
    route = _as_mapping(data.get("1.2")) or {}
    customs = _as_mapping(data.get("2.4")) or {}
    gnt = _as_mapping(customs.get("gnt")) or {}
    finance = _as_mapping(data.get("3.4")) or {}
    known_rows = [
        ("Booking / vận đơn", route.get("booking_no") or route.get("mbl") or route.get("hbl"), "Xuất khẩu"),
        ("Tờ khai hải quan", customs.get("tk_no"), "Thông quan"),
        ("Giấy nộp thuế (GNT)", gnt.get("ds_thue") or gnt.get("so_tk"), "Thuế nhập khẩu"),
        ("Invoice", route.get("invoice_no") or finance.get("invoice_no"), "Hồ sơ thương mại"),
    ]
    rows = [
        {
            "document": label,
            "status": _document_state(value),
            "step": step,
            "source": "shipment.data",
            "required": UNKNOWN,
        }
        for label, value, step in known_rows
    ]
    has_known = any(row["status"] == "CÓ DỮ LIỆU" for row in rows)
    rows.append(
        {
            "document": "Registry chứng từ chuẩn",
            "status": UNKNOWN,
            "step": "Completeness",
            "source": "Chưa có trường documents/document_registry chuẩn",
            "required": UNKNOWN,
        }
    )
    return rows, "PARTIAL" if has_known else UNKNOWN


def _timeline(shipment: Mapping[str, Any]) -> list[dict[str, Any]]:
    data = _data(shipment)
    event_specs = (
        ("Tạo lô", _first_value(shipment, ("created_at", "assigned_date")), "shipment.created_at/assigned_date"),
        ("Sẵn sàng nhà máy", _first_value(shipment, ("factory_ready_date", "ready_date")), "shipment.factory_ready_date/ready_date"),
        ("ETD", (_as_mapping(data.get("1.2")) or {}).get("etd"), "shipment.data.1.2.etd"),
        ("ETA", (_as_mapping(data.get("2.6")) or {}).get("arrival_date"), "shipment.data.2.6.arrival_date"),
        ("Thông quan", _first_value(shipment, ("customs_date", "cleared_at")), "shipment.customs_date/cleared_at"),
        ("Giao hàng", (_as_mapping(data.get("2.7")) or {}).get("delivery_date"), "shipment.data.2.7.delivery_date"),
    )
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for label, raw_value, source in event_specs:
        parsed = parse_date_optional(raw_value)
        if parsed is None:
            continue
        key = (label, parsed.isoformat())
        if key in seen:
            continue
        seen.add(key)
        rows.append({"event": label, "date": parsed.strftime("%d/%m/%Y"), "source": source, "status": "KNOWN"})
    return rows


def build_shipment_workspace_view(
    shipment: Mapping[str, Any],
    *,
    today: date | None = None,
    financial_view: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only Shipment 360 workspace view without mutating input."""

    if not isinstance(shipment, Mapping):
        raise TypeError("shipment must be a mapping")

    dashboard = build_shipment_dashboard_view(shipment, today=today, financial_view=financial_view)
    lots, lots_status = _factory_lots(shipment)
    documents, documents_status = _document_rows(shipment)
    timeline = _timeline(shipment)
    data = _data(shipment)
    route = _as_mapping(data.get("1.2")) or {}
    pickup = _as_mapping(_first_value(shipment, ("pickup", "pickup_info")))
    delivery = _as_mapping(data.get("2.7")) or {}
    agency = _as_mapping((_as_mapping(data.get("3.4")) or {}).get("agency"))

    next_action = dashboard.get("next_action")
    if not next_action:
        if dashboard.get("is_complete"):
            next_action = {
                "code": "COMPLETE_REVIEW",
                "severity": "normal",
                "label": "Lô đã hoàn tất",
                "detail": "Không có cảnh báo vận hành hiện tại; kiểm tra các mục UNKNOWN hoặc đối soát nếu còn mở.",
                "source": "deterministic completion state",
            }
        else:
            next_action = {
                "code": "DATA_REVIEW",
                "severity": "info",
                "label": "Kiểm tra dữ liệu vận hành",
                "detail": "Chưa có cảnh báo ưu tiên hoặc bước tiếp theo được lưu trong shipment.",
                "source": "shipment dashboard projection",
            }

    return {
        "shipment_id": dashboard.get("shipment_id", UNKNOWN),
        "customer": dashboard.get("customer", UNKNOWN),
        "customer_id": _text(shipment.get("customer_id")),
        "owner": dashboard.get("owner", UNKNOWN),
        "operational_status": dashboard.get("operational_status", UNKNOWN),
        "operational_status_label": dashboard.get("operational_status_label", UNKNOWN),
        "financial_status": dashboard.get("financial_status", UNKNOWN),
        "financial_label": dashboard.get("financial_label", UNKNOWN),
        "stage": dashboard.get("operational_status_label", UNKNOWN),
        "next_action": next_action,
        "alerts": list(dashboard.get("alerts") or []),
        "required_date": dashboard.get("required_date_label", UNKNOWN),
        "planned_date": dashboard.get("planned_date_label", UNKNOWN),
        "arrival_date": dashboard.get("arrival_date_label", UNKNOWN),
        "free_time_expiry": dashboard.get("free_time_expiry_label", UNKNOWN),
        "free_time_remaining": dashboard.get("days_remaining", UNKNOWN),
        "route": {
            "pol": _text(route.get("pol")),
            "pod": _text(route.get("pod")),
            "mode": _text((_as_mapping(data.get("0.0")) or {}).get("mode")),
            "incoterm": _text((_as_mapping(data.get("0.0")) or {}).get("incoterm")),
            "booking": _text(route.get("booking_no")),
            "carrier": _text(route.get("carrier")),
            "vessel": _text(route.get("vessel")),
            "container": _text(route.get("container_no")),
        },
        "context": {
            "supplier": _text(_first_value(shipment, ("supplier", "supplier_name", "factory_supplier"))),
            "agent": _text((agency or {}).get("name") or _first_value(shipment, ("agent", "agent_name", "partner"))),
            "pickup_contact": _text((pickup or {}).get("contact") or _first_value(shipment, ("pickup_contact",))),
            "pickup_address": _text((pickup or {}).get("address") or _first_value(shipment, ("pickup_address",))),
            "delivery_address": _text(delivery.get("addr") or _first_value(shipment, ("delivery_address",))),
            "receiver": _text(delivery.get("phone_receiver") or _first_value(shipment, ("receiver", "receiver_name"))),
        },
        "factory_lots": lots,
        "factory_lots_status": lots_status,
        "documents": documents,
        "documents_status": documents_status,
        "timeline": timeline,
        "history_status": "KNOWN" if timeline else UNKNOWN,
        "source": "shipment document + core.shipment_dashboard + core.shipment_360",
        "read_only": True,
    }
