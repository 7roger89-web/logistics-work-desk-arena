"""Read-only projection for the Shipment Dashboard 2.0 work desk.

The dashboard is intentionally built from the shipment document and the
existing read-only Shipment 360 projection.  This module does not import
Streamlit, repositories, or write-path helpers, so it can be exercised with
small in-memory fixtures and cannot accidentally change ledger state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from typing import Any

from core.config import STATUS_LABELS
from core.shipment_360 import UNKNOWN, build_shipment_360_summary
from core.utils import parse_date_optional, safe_float


CRITICAL = "critical"
WARNING = "warning"
INFO = "info"
NORMAL = "normal"

FINANCIAL_OK = "ok"
FINANCIAL_OPEN = "open"
FINANCIAL_REVIEW = "review"
FINANCIAL_UNKNOWN = "unknown"

_STATUS_ACTIVE = {"wait", "pending"}
_STATUS_TERMINAL = {"done", "cancel"}
_STATUS_ALIASES = {
    "chờ chứng từ": "wait",
    "chưa xử lý": "wait",
    "đang thông quan/giao hàng": "pending",
    "đang xử lý": "pending",
    "hoàn thành": "done",
    "đã hủy": "cancel",
}
_OWNER_ALIASES = (
    "internal_sale_owner",
    "sale_owner",
    "sales_owner",
    "owner",
    "assigned_to",
    "assignee",
)
_CUSTOMER_REQUIRED_DATE_ALIASES = (
    "customer_required_date",
    "required_delivery_date",
    "delivery_deadline",
    "required_date",
    "customer_deadline",
)
_PROMISED_DATE_ALIASES = (
    "promised_date",
    "expected_response_date",
    "factory_ready_date",
    "next_action_due_date",
)
_LAST_UPDATE_ALIASES = ("updated_at", "last_updated_at", "modified_at", "created_at")
_FACTORY_COLLECTION_ALIASES = ("factories", "factory_lots", "factory_items")
_MISSING_INFO_FLAGS = (
    "info_pending",
    "information_pending",
    "required_information_pending",
    "waiting_for_information",
)


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _data(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(shipment.get("data")) or {}


def _sections(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return known document sections in stable precedence order."""

    data = _data(shipment)
    sections: list[Mapping[str, Any]] = [shipment, data]
    for key in ("0.0", "1.2", "2.6", "2.7", "3.4"):
        section = _as_mapping(data.get(key))
        if section is not None:
            sections.append(section)
    return sections


def _first_value(shipment: Mapping[str, Any], aliases: Iterable[str]) -> Any:
    for section in _sections(shipment):
        for alias in aliases:
            value = section.get(alias)
            if value not in (None, ""):
                return value
    return None


def _parse_value(value: Any) -> date | None:
    return parse_date_optional(value)


def _date_value(shipment: Mapping[str, Any], aliases: Iterable[str]) -> date | None:
    return _parse_value(_first_value(shipment, aliases))


def _label_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else "Chưa có"


def _text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value).strip()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).casefold() in {"1", "true", "yes", "y", "co", "có"}


def _operational_status(shipment: Mapping[str, Any]) -> str:
    value = _first_value(shipment, ("status", "operational_status"))
    normalized = _text(value, "wait").casefold()
    return _STATUS_ALIASES.get(normalized, normalized)


def _shipment_id(shipment: Mapping[str, Any]) -> str:
    return _text(
        shipment.get("shipment_id")
        or shipment.get("id")
        or shipment.get("_id")
        or _first_value(shipment, ("shipment_code", "code")),
        "UNKNOWN",
    )


def _customer(shipment: Mapping[str, Any]) -> str:
    return _text(
        shipment.get("customer")
        or shipment.get("customer_name")
        or _first_value(shipment, ("customer", "customer_name", "client_name")),
        "Chưa có khách hàng",
    )


def _owner(shipment: Mapping[str, Any]) -> str:
    return _text(_first_value(shipment, _OWNER_ALIASES), "Chưa phân công")


def _last_update(shipment: Mapping[str, Any]) -> tuple[date | None, str]:
    for alias in _LAST_UPDATE_ALIASES:
        value = _first_value(shipment, (alias,))
        parsed = _parse_value(value)
        if parsed:
            return parsed, alias
    return None, ""


def _planned_delivery_date(shipment: Mapping[str, Any]) -> date | None:
    """Use an explicit planned delivery value, then the current ETA field."""

    return _date_value(
        shipment,
        (
            "planned_delivery_date",
            "planned_delivery_at",
            "delivery_plan_date",
            "delivery_date",
            "eta",
            "arrival_date",
        ),
    )


def _arrival_date(shipment: Mapping[str, Any]) -> date | None:
    data = _data(shipment)
    arrival = _as_mapping(data.get("2.6"))
    if arrival:
        parsed = _parse_value(arrival.get("arrival_date"))
        if parsed:
            return parsed
    return _date_value(shipment, ("arrival_date", "eta"))


def _free_time_days(shipment: Mapping[str, Any]) -> int | None:
    data = _data(shipment)
    section = _as_mapping(data.get("2.6")) or {}
    raw = section.get("free_time")
    if raw in (None, ""):
        raw = _first_value(shipment, ("free_time", "free_time_days"))
    if raw in (None, ""):
        return None
    try:
        value = safe_float(raw)
    except (TypeError, ValueError, ArithmeticError):
        return None
    if value < 0:
        return None
    return int(value)


def _factory_items(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]] | None:
    for section in _sections(shipment):
        for alias in _FACTORY_COLLECTION_ALIASES:
            value = section.get(alias)
            if isinstance(value, Mapping):
                return [item for item in value.values() if isinstance(item, Mapping)]
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                return [item for item in value if isinstance(item, Mapping)]
    return None


def _missing_factory_items(items: list[Mapping[str, Any]] | None) -> int | None:
    if items is None:
        return None
    missing = 0
    for item in items:
        explicit = item.get("required_information_complete")
        if explicit is not None:
            missing += int(not _truthy(explicit))
            continue
        required_groups = (
            ("product", "product_name"),
            ("quantity", "packages"),
            ("weight",),
            ("cbm",),
            ("factory_ready_date", "ready_date"),
            ("pickup_contact", "contact"),
        )
        if any(all(item.get(field) in (None, "") for field in group) for group in required_groups):
            missing += 1
    return missing


def _is_delivered(shipment: Mapping[str, Any]) -> bool:
    data = _data(shipment)
    delivery = _as_mapping(data.get("2.7")) or {}
    return _truthy(delivery.get("is_delivered")) or _truthy(shipment.get("is_delivered"))


def _is_complete(shipment: Mapping[str, Any], status: str) -> bool:
    return status in _STATUS_TERMINAL or status == "done" or _is_delivered(shipment)


def _alert(
    code: str,
    severity: str,
    label: str,
    detail: str,
    source: str,
    priority: int,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "label": label,
        "detail": detail,
        "source": source,
        "priority": priority,
    }


def _financial_projection(
    shipment: Mapping[str, Any],
    financial_view: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if financial_view is not None:
        return financial_view
    return build_shipment_360_summary(shipment)


def _financial_state(view: Mapping[str, Any]) -> tuple[str, str]:
    status = _text(view.get("financial_status"), UNKNOWN)
    upper = status.upper()
    attention = view.get("attention")
    attention_items = list(attention) if isinstance(attention, Iterable) and not isinstance(attention, (str, bytes)) else []
    has_unknown = status == UNKNOWN or "UNKNOWN" in upper or "CHƯA ĐỦ DỮ LIỆU" in upper
    has_reconciliation = "ĐỐI SOÁT" in upper or "CẦN ĐỐI SOÁT" in upper
    has_open_balance = any(token in upper for token in ("CHỜ THU", "CHỜ TRẢ"))
    if has_unknown:
        return FINANCIAL_UNKNOWN, "UNKNOWN"
    if has_open_balance:
        return FINANCIAL_OPEN, "Đang mở"
    if has_reconciliation or attention_items:
        return FINANCIAL_REVIEW, "Cần đối soát"
    if "ĐÃ THU ĐỦ" in upper or "ĐÃ THANH TOÁN" in upper or "KHÔNG PHÁT SINH" in upper:
        return FINANCIAL_OK, "Tài chính OK"
    return FINANCIAL_REVIEW, "Cần kiểm tra"


def _next_action(
    alerts: list[dict[str, Any]],
    shipment: Mapping[str, Any],
    status: str,
) -> dict[str, Any] | None:
    if alerts:
        return alerts[0]
    explicit_action = _first_value(shipment, ("next_action", "next_step", "action_required"))
    if explicit_action not in (None, "") and status in _STATUS_ACTIVE:
        return _alert(
            "NEXT_ACTION",
            INFO,
            "Cần cập nhật bước tiếp theo",
            _text(explicit_action),
            "shipment.next_action",
            50,
        )
    return None


def build_shipment_dashboard_view(
    shipment: Mapping[str, Any],
    *,
    today: date | None = None,
    financial_view: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic dashboard row without mutating ``shipment``."""

    if not isinstance(shipment, Mapping):
        raise TypeError("shipment must be a mapping")

    as_of = today or date.today()
    status = _operational_status(shipment)
    status_label = STATUS_LABELS.get(status, status.title())
    complete = _is_complete(shipment, status)
    arrival_date = _arrival_date(shipment)
    free_time_days = _free_time_days(shipment)
    free_time_expiry = (
        arrival_date + timedelta(days=free_time_days)
        if arrival_date is not None and free_time_days is not None
        else None
    )
    days_remaining = (free_time_expiry - as_of).days if free_time_expiry else None
    required_date = _date_value(shipment, _CUSTOMER_REQUIRED_DATE_ALIASES)
    planned_date = _planned_delivery_date(shipment)
    promised_date = _date_value(shipment, _PROMISED_DATE_ALIASES)
    last_update, last_update_source = _last_update(shipment)
    factory_items = _factory_items(shipment)
    missing_factory_count = _missing_factory_items(factory_items)

    alerts: list[dict[str, Any]] = []
    if _customer(shipment) == "Chưa có khách hàng":
        alerts.append(
            _alert(
                "MISSING_CUSTOMER",
                CRITICAL,
                "Thiếu khách hàng",
                "Chưa xác định khách hàng của lô hàng.",
                "shipment.customer",
                5,
            )
        )

    if status in _STATUS_ACTIVE and arrival_date is None:
        alerts.append(
            _alert(
                "MISSING_ETA",
                WARNING,
                "Thiếu ETA",
                "Chưa có ngày ETA/arrival để Support theo dõi.",
                "data.2.6.arrival_date",
                15,
            )
        )

    if free_time_expiry is not None and not complete:
        if days_remaining is not None and days_remaining < 0:
            alerts.append(
                _alert(
                    "FREE_TIME_OVERDUE",
                    CRITICAL,
                    "Quá free time",
                    f"Hạn free time {_label_date(free_time_expiry)} đã quá {abs(days_remaining)} ngày.",
                    "data.2.6.arrival_date + free_time",
                    10,
                )
            )
        elif days_remaining is not None and days_remaining <= 2:
            alerts.append(
                _alert(
                    "FREE_TIME_SOON",
                    WARNING,
                    "Sắp hết free time",
                    f"Còn {days_remaining} ngày, hạn {_label_date(free_time_expiry)}.",
                    "data.2.6.arrival_date + free_time",
                    20,
                )
            )

    if required_date is not None and not complete:
        if planned_date is not None and planned_date > required_date:
            alerts.append(
                _alert(
                    "CUSTOMER_DEADLINE_RISK",
                    CRITICAL,
                    "Có nguy cơ trễ hạn khách",
                    f"Kế hoạch {_label_date(planned_date)} sau hạn khách {_label_date(required_date)}.",
                    "customer_required_date + planned_delivery_date",
                    8,
                )
            )
        else:
            remaining = (required_date - as_of).days
            if remaining < 0:
                alerts.append(
                    _alert(
                        "CUSTOMER_DEADLINE_OVERDUE",
                        CRITICAL,
                        "Quá hạn khách",
                        f"Hạn khách {_label_date(required_date)} đã quá {abs(remaining)} ngày.",
                        "customer_required_date",
                        7,
                    )
                )
            elif remaining <= 3:
                alerts.append(
                    _alert(
                        "CUSTOMER_DEADLINE_SOON",
                        WARNING,
                        "Sắp đến hạn khách",
                        f"Còn {remaining} ngày đến {_label_date(required_date)}.",
                        "customer_required_date",
                        18,
                    )
                )

    missing_info = any(_truthy(_first_value(shipment, (flag,))) for flag in _MISSING_INFO_FLAGS)
    if promised_date is not None and not complete and promised_date <= as_of and missing_info:
        alerts.append(
            _alert(
                "PROMISED_INFO_OVERDUE",
                WARNING,
                "Đang chờ thông tin theo hẹn",
                f"Mốc hẹn {_label_date(promised_date)} chưa có thông tin hoàn tất.",
                "promised_date + information_pending",
                25,
            )
        )

    if missing_factory_count:
        alerts.append(
            _alert(
                "FACTORY_INFO_MISSING",
                WARNING,
                "Thiếu thông tin nhà máy",
                f"Có {missing_factory_count} nhà máy/lô con chưa đủ trường bắt buộc.",
                "factories[*]",
                22,
            )
        )

    financial = _financial_projection(shipment, financial_view)
    financial_flag, financial_label = _financial_state(financial)
    if financial_flag == FINANCIAL_UNKNOWN:
        alerts.append(
            _alert(
                "FINANCE_UNKNOWN",
                WARNING,
                "Tài chính UNKNOWN",
                "Chưa đủ dữ liệu để kết luận trạng thái tài chính.",
                "Shipment 360 financial projection",
                30,
            )
        )
    elif financial_flag in {FINANCIAL_OPEN, FINANCIAL_REVIEW}:
        alerts.append(
            _alert(
                "FINANCE_ATTENTION",
                INFO if financial_flag == FINANCIAL_REVIEW else WARNING,
                "Tài chính cần theo dõi" if financial_flag == FINANCIAL_OPEN else "Cần đối soát tài chính",
                _text(financial.get("financial_status"), "Chưa có trạng thái tài chính."),
                "Shipment 360 financial projection",
                35,
            )
        )

    severity_order = {CRITICAL: 0, WARNING: 1, INFO: 2, NORMAL: 3}
    alerts.sort(key=lambda item: (severity_order.get(item["severity"], 9), item["priority"], item["code"]))
    next_action = _next_action(alerts, shipment, status)

    return {
        "shipment_id": _shipment_id(shipment),
        "customer": _customer(shipment),
        "owner": _owner(shipment),
        "operational_status": status,
        "operational_status_label": status_label,
        "is_complete": complete,
        "last_update": last_update,
        "last_update_label": _label_date(last_update),
        "last_update_source": last_update_source,
        "required_date": required_date,
        "required_date_label": _label_date(required_date),
        "planned_date": planned_date,
        "planned_date_label": _label_date(planned_date),
        "promised_date": promised_date,
        "promised_date_label": _label_date(promised_date),
        "arrival_date": arrival_date,
        "arrival_date_label": _label_date(arrival_date),
        "free_time_days": free_time_days,
        "free_time_expiry": free_time_expiry,
        "free_time_expiry_label": _label_date(free_time_expiry),
        "days_remaining": days_remaining,
        "factory_count": len(factory_items) if factory_items is not None else None,
        "missing_factory_count": missing_factory_count,
        "financial_status": _text(financial.get("financial_status"), UNKNOWN),
        "financial_flag": financial_flag,
        "financial_label": financial_label,
        "financial_projection": financial,
        "alerts": alerts,
        "top_alert": alerts[0] if alerts else None,
        "next_action": next_action,
        "has_alert": bool(alerts),
        "deadline_soon": any(item["code"].startswith("CUSTOMER_DEADLINE") for item in alerts),
        "read_only_financial": True,
        "source": "shipment document + core.shipment_360.build_shipment_360_summary",
    }


def build_dashboard_summary(views: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Return compact, deterministic counters for the work-desk summary."""

    rows = list(views)
    top_alerts = [row.get("top_alert") or {} for row in rows]
    return {
        "total": len(rows),
        "critical": sum(1 for alert in top_alerts if alert.get("severity") == CRITICAL),
        "warning": sum(1 for alert in top_alerts if alert.get("severity") == WARNING),
        "deadline_soon": sum(1 for row in rows if row.get("deadline_soon")),
        "financial_attention": sum(1 for row in rows if row.get("financial_flag") in {FINANCIAL_OPEN, FINANCIAL_REVIEW, FINANCIAL_UNKNOWN}),
        "missing_info": sum(1 for row in rows if any(alert.get("code", "").startswith(("MISSING_", "FACTORY_")) for alert in row.get("alerts", []))),
    }


def _matches_text(row: Mapping[str, Any], query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    haystack = " ".join(
        _text(row.get(key))
        for key in ("shipment_id", "customer", "owner", "operational_status_label", "financial_status")
    ).casefold()
    return needle in haystack


def filter_dashboard_views(
    views: Iterable[Mapping[str, Any]],
    *,
    owner: str | None = None,
    customer: str | None = None,
    operational_status: str | None = None,
    financial_flag: str | None = None,
    has_alert: bool | None = None,
    deadline_soon: bool | None = None,
    search: str = "",
) -> list[Mapping[str, Any]]:
    """Apply work-desk filters without changing row objects or source data."""

    def accepted(row: Mapping[str, Any]) -> bool:
        if owner and owner not in {"Tất cả", "__all__"} and _text(row.get("owner")) != owner:
            return False
        if customer and customer not in {"Tất cả", "__all__"} and _text(row.get("customer")) != customer:
            return False
        if operational_status and operational_status not in {"Tất cả", "__all__"}:
            if _text(row.get("operational_status")) != operational_status:
                return False
        if financial_flag and financial_flag not in {"Tất cả", "__all__"}:
            if _text(row.get("financial_flag")) != financial_flag:
                return False
        if has_alert is not None and bool(row.get("has_alert")) is not has_alert:
            return False
        if deadline_soon is not None and bool(row.get("deadline_soon")) is not deadline_soon:
            return False
        return _matches_text(row, search)

    return [row for row in views if accepted(row)]


def sort_dashboard_views(views: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Sort urgent work first, then nearest explicit deadline, then id."""

    severity_order = {CRITICAL: 0, WARNING: 1, INFO: 2, NORMAL: 3}

    def key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        top = row.get("top_alert") or {}
        severity = severity_order.get(_text(top.get("severity"), NORMAL), 9)
        priority = top.get("priority", 999)
        deadline = row.get("required_date") or date.max
        return severity, priority, deadline, _text(row.get("shipment_id"))

    return sorted(views, key=key)
