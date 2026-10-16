"""Navigation projection for canonical manual-task destination metadata.

No text heuristics, route field, or second workflow registry is consulted:
shipment targets come from the task's explicit optional metadata and the
shipment's current authoritative Journey projection.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

from views import logi_route

_STAGE_TABS = frozenset({"lay-hang", "van-tai", "nhap"})


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()


def task_destination(
    task: Mapping[str, Any], shipment: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Return one existing route and honest navigation status for a task.

    ``task_scope`` is optional for backward compatibility. A shipment-linked
    task with no recognized scope/stage stays on the shipment workspace and is
    explicitly marked ``UNKNOWN_STAGE``; content text never supplies a route.
    """
    sid = _text(task.get("shipment_id"))
    if not sid:
        return {"route": "/lo-hang", "navigationStatus": "GENERAL", "notice": ""}

    lot_path = logi_route.shipment_path(sid)
    scope = _text(task.get("task_scope")).upper()
    stage_id = _text(task.get("stage_id"))
    if scope == "FINANCE" and not stage_id:
        return {
            "route": f"{lot_path}?tab=tai-chinh",
            "navigationStatus": "FINANCE",
            "notice": "Tài chính toàn lô.",
        }
    if scope == "SHIPMENT" and not stage_id:
        return {
            "route": lot_path,
            "navigationStatus": "SHIPMENT",
            "notice": "Workspace toàn lô.",
        }

    # A stage_id is explicit navigation metadata; it is not inferred from task
    # wording. Require an exact match to a current base Journey node and its
    # existing owning tab, otherwise retain the honest shipment fallback.
    if scope == "STAGE" or (not scope and stage_id):
        if stage_id and isinstance(shipment, Mapping) and _text(shipment.get("id")) == sid:
            journey = shipment.get("journey") if isinstance(shipment.get("journey"), Mapping) else {}
            nodes = journey.get("nodes") if isinstance(journey.get("nodes"), list) else []
            node = next((candidate for candidate in nodes
                         if isinstance(candidate, Mapping)
                         and _text(candidate.get("id")) == stage_id
                         and not candidate.get("moduleId")
                         and _text(candidate.get("targetTab")) in _STAGE_TABS), None)
            if node is not None:
                query = urlencode({
                    "tab": _text(node.get("targetTab")),
                    "stage": stage_id,
                    "work": "info",
                })
                label = _text(node.get("label")) or stage_id
                return {
                    "route": f"{lot_path}?{query}",
                    "navigationStatus": "STAGE",
                    "notice": f"Đã gắn công đoạn: {label}.",
                }
        return {
            "route": lot_path,
            "navigationStatus": "UNKNOWN_STAGE",
            "notice": "Công đoạn đã gắn chưa hợp lệ với hành trình hiện tại; mở lô để kiểm tra.",
        }

    if scope not in {"", "FINANCE", "SHIPMENT"}:
        return {
            "route": lot_path,
            "navigationStatus": "UNKNOWN_STAGE",
            "notice": "Nơi xử lý chưa xác định; mở lô để kiểm tra, không suy đoán từ nội dung.",
        }

    return {
        "route": lot_path,
        "navigationStatus": "UNKNOWN_STAGE",
        "notice": "Chưa gắn công đoạn; mở workspace lô để xác định nơi xử lý.",
    }
