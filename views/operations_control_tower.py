"""Issue #170 — pure read-only Operations Control Tower projection.

The Tower aggregates the SAME Support Attention truth introduced by #166.
It owns no workflow/task/business state, opens no database, dispatches no event,
and never infers responsibility from a last-writer field.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from typing import Any

MANAGER_BANDS = frozenset({"BLOCKING", "OVERDUE", "DUE_SOON"})
UNASSIGNED_KEY = "UNASSIGNED"
UNASSIGNED_LABEL = "Chưa phân công / Chưa xác định"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()


def _rows(value: Any) -> list[Mapping[str, Any]]:
    return [row for row in (value or []) if isinstance(row, Mapping)]


def _is_manager_grade(item: Mapping[str, Any]) -> bool:
    """Only facts with real current intervention value enter the manager queue."""
    return (
        _text(item.get("band")).upper() in MANAGER_BANDS
        or bool(item.get("unknown"))
        or _text(item.get("sourcePriority")) == "Khan"
    )


def _deadline_date(item: Mapping[str, Any]) -> date | None:
    raw = _text(item.get("deadlineDate"))
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        # Manager projection never reparses display/free-text deadline strings.
        return None


def _enrich(
    item: Mapping[str, Any],
    shipments: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    sid = _text(item.get("shipmentId"))
    shipment = shipments.get(sid, {})
    result = dict(item)
    # core.shipment_dashboard deliberately emits this Vietnamese sentinel when
    # no canonical shipment owner exists. It is not a person's identity.
    if _text(result.get("owner")).casefold() == "chưa phân công":
        result["owner"] = ""
    result.update(
        {
            "customer": _text(shipment.get("customer")) or "Chưa xác định",
            "shipmentStatus": _text(shipment.get("status")) or "Chưa xác định",
        }
    )
    return result


def _horizon(
    manager_items: list[dict[str, Any]],
    *,
    as_of: date,
) -> dict[str, Any]:
    buckets = {"OVERDUE": [], "TODAY": [], "NEXT_3_DAYS": []}
    for item in manager_items:
        due = _deadline_date(item)
        if due is None:
            continue
        if due < as_of:
            buckets["OVERDUE"].append(item)
        elif due == as_of:
            buckets["TODAY"].append(item)
        elif due <= as_of + timedelta(days=3):
            buckets["NEXT_3_DAYS"].append(item)

    return {
        "asOf": as_of.isoformat(),
        "precision": "DATE_ONLY",
        "labels": {
            "OVERDUE": "Quá hạn",
            "TODAY": "Hôm nay",
            "NEXT_3_DAYS": "1–3 ngày tới",
        },
        "buckets": [
            {"id": key, "label": {
                "OVERDUE": "Quá hạn",
                "TODAY": "Hôm nay",
                "NEXT_3_DAYS": "1–3 ngày tới",
            }[key], "items": buckets[key], "count": len(buckets[key])}
            for key in ("OVERDUE", "TODAY", "NEXT_3_DAYS")
        ],
    }


def _workload(manager_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for item in manager_items:
        owner = _text(item.get("owner"))
        key = owner or UNASSIGNED_KEY
        row = grouped.setdefault(
            key,
            {
                "ownerKey": key,
                "owner": owner or UNASSIGNED_LABEL,
                "blocking": 0,
                "overdue": 0,
                "dueSoon": 0,
                "action": 0,
                "unknown": 0,
                "itemIds": [],
            },
        )
        band = _text(item.get("band")).upper()
        if band == "BLOCKING":
            row["blocking"] += 1
        elif band == "OVERDUE":
            row["overdue"] += 1
        elif band == "DUE_SOON":
            row["dueSoon"] += 1
        else:
            row["action"] += 1
        if item.get("unknown"):
            row["unknown"] += 1
        row["itemIds"].append(_text(item.get("id")))

    # UNASSIGNED is a control gap, so keep it visibly first. Everyone else is
    # alphabetical — never ranked by workload or performance.
    return sorted(
        grouped.values(),
        key=lambda row: (0 if row["ownerKey"] == UNASSIGNED_KEY else 1, row["owner"].casefold()),
    )


def _concentration_rows(
    manager_items: list[dict[str, Any]],
    *,
    key_fn,
    label_fn,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in manager_items:
        key = _text(key_fn(item))
        if not key:
            continue
        label = _text(label_fn(item)) or key
        row = grouped.setdefault(
            key,
            {
                "key": key,
                "label": label,
                "count": 0,
                "blocking": 0,
                "overdue": 0,
                "dueSoon": 0,
                "unknown": 0,
                "itemIds": [],
            },
        )
        row["count"] += 1
        band = _text(item.get("band")).upper()
        if band == "BLOCKING":
            row["blocking"] += 1
        elif band == "OVERDUE":
            row["overdue"] += 1
        elif band == "DUE_SOON":
            row["dueSoon"] += 1
        if item.get("unknown"):
            row["unknown"] += 1
        row["itemIds"].append(_text(item.get("id")))

    # This is concentration, not a risk/performance ranking. Count-desc makes
    # clusters scannable; the UI must label them neutrally.
    return sorted(grouped.values(), key=lambda row: (-row["count"], row["label"].casefold()))


def build_operations_control_tower(
    shipments: Iterable[Mapping[str, Any]],
    attention: Iterable[Mapping[str, Any]],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Build the bounded manager surface over existing read-only truth."""
    as_of = today or date.today()
    shipment_rows = _rows(list(shipments or []))
    attention_rows = _rows(list(attention or []))
    shipment_by_id = {
        _text(row.get("id")): row
        for row in shipment_rows
        if _text(row.get("id"))
    }

    attention_shipments = {
        _text(item.get("shipmentId"))
        for item in attention_rows
        if _text(item.get("shipmentId")) in shipment_by_id
    }
    unknown_shipments = {
        _text(item.get("shipmentId"))
        for item in attention_rows
        if bool(item.get("unknown")) and _text(item.get("shipmentId")) in shipment_by_id
    }

    # Preserve shared Attention ordering. Do not create a manager score.
    manager_items = [
        _enrich(item, shipment_by_id)
        for item in attention_rows
        if _text(item.get("shipmentId")) in shipment_by_id and _is_manager_grade(item)
    ]

    customer_rows = _concentration_rows(
        manager_items,
        key_fn=lambda item: item.get("customer"),
        label_fn=lambda item: item.get("customer"),
    )
    gate_rows = _concentration_rows(
        [item for item in manager_items if _text(item.get("blockedGate"))],
        key_fn=lambda item: item.get("blockedGate"),
        label_fn=lambda item: item.get("blockedGate"),
    )
    module_rows = _concentration_rows(
        [
            item
            for item in manager_items
            if _text(item.get("sourceType")) == "WORK_MODULE"
            and _text(item.get("moduleTemplateId"))
        ],
        key_fn=lambda item: item.get("moduleTemplateId"),
        label_fn=lambda item: item.get("moduleName") or item.get("moduleTemplateId"),
    )

    return {
        "classification": "READ_ONLY_ATTENTION_AGGREGATE_V1",
        "readOnly": True,
        "scope": {
            "shipmentCount": len(shipment_rows),
            "attentionShipmentCount": len(attention_shipments),
            "noSignalShipmentCount": max(len(shipment_rows) - len(attention_shipments), 0),
            "unknownShipmentCount": len(unknown_shipments),
            "managerItemCount": len(manager_items),
        },
        "interventionQueue": manager_items,
        "horizon": _horizon(manager_items, as_of=as_of),
        "workload": _workload(manager_items),
        "concentration": {
            "customers": customer_rows,
            "gates": gate_rows,
            "modules": module_rows,
        },
        "unavailable": [
            "Chưa có nguồn canonical cho waiting-on party / chase age.",
            "Deadline hiện tại là theo ngày, không suy diễn thành đồng hồ <24h.",
            "Không có workload score, employee score, health score hoặc risk score.",
        ],
    }


__all__ = [
    "MANAGER_BANDS",
    "UNASSIGNED_KEY",
    "UNASSIGNED_LABEL",
    "build_operations_control_tower",
]
