"""Pure Support Attention / Now projection for Issue #166.

This module owns no business state. It reshapes existing authoritative shipment,
task, dashboard-alert and Work Module facts into one bounded read-only list used
by both Shipment Detail and Home.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from typing import Any

from views import logi_route

BAND_ORDER = {"BLOCKING": 0, "OVERDUE": 1, "DUE_SOON": 2, "ACTION": 3, "INFO": 4}


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()


def _strict_deadline(value: Any) -> date | None:
    """Parse only task-deadline shapes with unambiguous product meaning."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = _text(value)
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None


def _attention_id(source_type: str, shipment_id: str, source_ref: str) -> str:
    raw = f"{source_type}-{shipment_id}-{source_ref}".upper()
    return "ATT-" + re.sub(r"[^A-Z0-9]+", "-", raw).strip("-")[:120]


def build_attention_projection(
    rows: Iterable[Mapping[str, Any]],
    raw_tasks: Iterable[Mapping[str, Any]],
    *,
    today: date | None = None,
    unknown_label: str = "—",
) -> list[dict[str, Any]]:
    """Build one transparent, deterministic attention list.

    Exact-source identity is the only de-duplication key. No fuzzy text merge,
    score, inferred owner, waiting-on party, or fabricated deadline exists here.
    """
    as_of = today or date.today()
    projected_rows = [row for row in rows if isinstance(row, Mapping)]
    by_shipment = {_text(row.get("id")): row for row in projected_rows if _text(row.get("id"))}
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(item: dict[str, Any]) -> None:
        key = (_text(item.get("sourceType")), _text(item.get("sourceRef")))
        if not all(key) or key in seen:
            return
        seen.add(key)
        out.append(item)

    for row in projected_rows:
        sid = _text(row.get("id"))
        if not sid:
            continue
        owner = _text(row.get("sale"))
        if owner == unknown_label:
            owner = ""

        # The ONE composed primary action remains the authority. We deliberately
        # do not reverse-map its text back to an alert/profile source because
        # text equality is not stable source identity.
        if row.get("priority") in {"Khan", "CanXuLy"} or bool(row.get("missingDocs")):
            source_ref = f"PRIMARY:{sid}"
            add({
                "id": _attention_id("PRIMARY_ACTION", sid, source_ref),
                "shipmentId": sid,
                "sourceType": "PRIMARY_ACTION",
                "sourceRef": source_ref,
                "band": "ACTION",
                "reason": _text(row.get("nextActionDetail")),
                "action": _text(row.get("nextAction")),
                "context": _text(row.get("status")),
                "route": _text(row.get("nextRoute")) or logi_route.shipment_path(sid),
                "owner": owner,
                "deadline": "",
                "blockedGate": "",
                "primary": True,
                "provenance": "shipment.primaryAction",
                "unknown": False,
                "_deadlineSort": "9999-12-31",
            })

        journey = row.get("journey") if isinstance(row.get("journey"), Mapping) else {}
        nodes = [node for node in (journey.get("nodes") or []) if isinstance(node, Mapping)]
        base_nodes = {_text(node.get("id")): node for node in nodes if not node.get("moduleId")}
        for module in journey.get("modules") or []:
            if not isinstance(module, Mapping):
                continue
            status = _text(module.get("status")).upper()
            if status == "DONE":
                continue
            instance_id = _text(module.get("instanceId"))
            if not instance_id:
                continue
            next_step_id = _text(module.get("nextStepId"))
            journey_step_id = f"wm-{instance_id}-{next_step_id}" if next_step_id else ""
            module_node = next(
                (node for node in nodes if _text(node.get("id")) == journey_step_id),
                None,
            )
            anchor_id = _text(module.get("anchorStage"))
            anchor_node = base_nodes.get(anchor_id)
            route_node = module_node or anchor_node or {}
            target_tab = _text(route_node.get("targetTab")) or "van-tai"
            route = f"{logi_route.shipment_path(sid)}?tab={target_tab}"
            if module_node is not None and journey_step_id:
                route += f"&stage={journey_step_id}&work=info"
            elif anchor_node is not None and anchor_id:
                route += f"&stage={anchor_id}&work=overview"

            gate = module.get("gate") if isinstance(module.get("gate"), Mapping) else {}
            gate_label = _text(gate.get("label") or gate.get("stage"))
            unknown = status == "UNKNOWN"
            add({
                "id": _attention_id("WORK_MODULE", sid, instance_id),
                "shipmentId": sid,
                "sourceType": "WORK_MODULE",
                "sourceRef": f"MODULE:{sid}:{instance_id}",
                "band": "BLOCKING" if status == "BLOCKING" else "ACTION",
                "reason": (
                    _text(module.get("gateText"))
                    if status == "BLOCKING"
                    else _text(module.get("blocker"))
                    if unknown
                    else " · ".join(part for part in (_text(module.get("name")), _text(module.get("summary"))) if part)
                ),
                "action": _text(module.get("nextStep")) or "Kiểm tra quy trình đã gắn",
                "context": _text(module.get("name")),
                "route": route,
                # Work Module WHO is guidance, not a canonical assignee in V1.
                "owner": "",
                # guidance.when is plain guidance, never deadline authority here.
                "deadline": "",
                "blockedGate": gate_label if status == "BLOCKING" else "",
                "primary": False,
                "provenance": f"work_module:{_text(module.get('templateId'))}@{int(module.get('templateVersion') or 0)}",
                "unknown": unknown,
                "_deadlineSort": "9999-12-31",
            })

    for task in raw_tasks or []:
        if not isinstance(task, Mapping) or bool(task.get("done")):
            continue
        sid = _text(task.get("shipment_id"))
        source_ref = _text(task.get("task_id"))
        if not sid or not source_ref or sid not in by_shipment:
            continue
        parsed = _strict_deadline(task.get("deadline"))
        if parsed is not None and parsed < as_of:
            band = "OVERDUE"
        elif parsed is not None and parsed <= as_of + timedelta(days=3):
            band = "DUE_SOON"
        else:
            band = "ACTION"
        owner = _text(task.get("assignee"))
        if owner == unknown_label:
            owner = ""
        add({
            "id": _attention_id("TASK", sid, source_ref),
            "shipmentId": sid,
            "sourceType": "TASK",
            "sourceRef": f"TASK:{source_ref}",
            "band": band,
            "reason": "Việc được giao",
            "action": _text(task.get("content")),
            "context": _text(by_shipment[sid].get("customer")),
            "route": logi_route.shipment_path(sid) + "?tab=lay-hang",
            "owner": owner,
            "deadline": parsed.strftime("%d/%m/%Y") if parsed else "",
            "blockedGate": "",
            "primary": False,
            "provenance": "core.database.load_tasks",
            "unknown": False,
            "_deadlineSort": parsed.isoformat() if parsed else "9999-12-31",
        })

    out.sort(
        key=lambda item: (
            BAND_ORDER.get(_text(item.get("band")), 9),
            _text(item.get("_deadlineSort")) or "9999-12-31",
            0 if item.get("primary") else 1,
            _text(item.get("shipmentId")),
            _text(item.get("sourceRef")),
        )
    )
    for item in out:
        item.pop("_deadlineSort", None)
    return out
