"""Journey Map node → đúng pane trao đổi/chứng từ **đang có**.

Cả hai cổng giao diện (shell nội bộ Trường Thành và cổng khách Lục Giác) chỉ
gửi lên một **ý định**: người dùng vừa bấm node nào của lô nào. Không byte nào
trong ý định đó được tin là dữ liệu:

* ``stage_id`` chỉ được chấp nhận khi nằm trong ``core.journey_notes.STAGE_IDS``
  (bảy công đoạn chuẩn) — một stage lạ không mở pane nào;
* ``shipment_id`` chỉ được chấp nhận khi khớp với projection **do server dựng
  cho chính danh tính hiện tại** (``cards`` của khách đã xác thực, hoặc danh
  sách lô đã qua RBAC của shell nội bộ);
* ``customer_id`` **không bao giờ** được đọc từ trình duyệt: pane khách dùng
  ``CustomerPrincipal`` đã chứng minh, pane nội bộ dùng ``customer_id`` của
  chính lô trong projection của server.

Module này không tạo kho dữ liệu, không ghi gì xuống DB: nó chỉ ghi nhớ một ý
định UI đã được xác minh trong ``st.session_state`` để pane
(:mod:`views.journey_discussion`) mở đúng lô + đúng công đoạn.
"""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

from core import journey_notes as notes

#: Session slot holding the ONE verified focus intent (UI state only).
FOCUS_KEY = "logi_journey_focus"
#: Replay guard: a replayed trigger ``seq`` never re-opens a closed pane.
SEQ_KEY = "logi_journey_focus_seq"

MAX_LOT = 120
MAX_STAGE = 40
MAX_ACTOR = 120

#: INTERNAL shell node id → ONE of the seven discussion stages that
#: ``core.journey_notes`` already owns.
#:
#: The shell's Journey Map is richer than the discussion model: it renders the
#: eleven base nodes built by ``core.shipment_journey.build_journey``
#: (booking / pickup / customs-export / si-vgm / gate-in / etd / on-board /
#: transit / arrival / customs-import / delivery) plus service-scope nodes such
#: as ``MAIN_CARRIAGE``. The discussion backend stays a SEVEN-stage contract, so
#: the map below states explicitly which lifecycle bucket each real node belongs
#: to. Nodes that share a bucket share ONE thread — they are never turned into
#: fake separate threads. Anything not listed here (e.g. a Work Module node id)
#: keeps failing closed, exactly as before.
#:
#: Keys are lower-case because every incoming intent is lower-cased first.
STAFF_NODE_STAGES: dict[str, str] = {
    # 00 Kế hoạch — booking/planning happens before anything moves.
    "booking": "plan",
    # 01 Lấy hàng — origin pickup at the factory/warehouse.
    "pickup": "pickup",
    # 02 Gom hàng — export handling, equipment, SI/VGM, gate-in and origin
    # hand-off all happen BEFORE the main carriage departs.
    "si-vgm": "consolidate",
    "gate-in": "consolidate",
    "sea_equipment": "consolidate",
    "sea_consolidation": "consolidate",
    "road_truck_profile": "consolidate",
    "road_consolidation": "consolidate",
    "origin_handoff": "consolidate",
    "origin_terminal_or_border": "consolidate",
    "sea_documents": "consolidate",
    "air_documents": "consolidate",
    # 03 Vận chuyển — the main carriage itself, including ETD/ATD, sailing,
    # arrival and cross-border/transhipment coordination.
    "main_carriage": "transit",
    "etd": "transit",
    "on-board": "transit",
    "transit": "transit",
    "arrival": "transit",
    "rail_carriage": "transit",
    "cross_border": "transit",
    # 04 Thông quan — export AND import declarations.
    "customs-export": "customs",
    "customs-import": "customs",
    "export_customs": "customs",
    # 05 Giao hàng — destination trucking and final delivery.
    "delivery": "delivery",
    "destination_trucking": "delivery",
    "final_delivery": "delivery",
    # 06 Thanh toán — cargo insurance is an arrangement with a cost, so it is
    # discussed where money is discussed.
    "insurance_evidence": "finance",
    "cargo_insurance_arrangement": "finance",
}

#: The seven canonical ids are accepted unchanged on both portals.
for _stage_id in notes.STAGE_IDS:  # pragma: no branch - fixed tuple
    STAFF_NODE_STAGES.setdefault(_stage_id, _stage_id)
del _stage_id


def _text(value: Any, limit: int = 0) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    cleaned = str(value).replace("\r", " ").strip()
    return cleaned[:limit] if limit else cleaned


def resolve_node_stage(node_id: Any, node_stages: Mapping[str, str] | None = None) -> str:
    """Canonical discussion stage for ONE journey node id (``""`` = unknown).

    A canonical id is accepted as-is; otherwise only an EXPLICIT entry in
    ``node_stages`` counts. There is no fuzzy/prefix/ordering inference, so an
    unmapped id can never silently borrow another stage's thread.
    """
    candidate = _text(node_id, MAX_STAGE).lower()
    if not candidate:
        return ""
    if candidate in notes.STAGE_IDS:
        return candidate
    mapped = _text((node_stages or {}).get(candidate), MAX_STAGE).lower()
    return mapped if mapped in notes.STAGE_IDS else ""


def normalize(intent: Any,
              *,
              node_stages: Mapping[str, str] | None = None) -> dict[str, str] | None:
    """Shrink one browser intent to ``{shipment_id, stage_id}`` or ``None``.

    ``node_stages`` is only supplied for the INTERNAL shell, whose Journey Map
    renders richer node ids (``MAIN_CARRIAGE``, ``si-vgm``…). The customer
    portal keeps its own seven canonical ids and is never mapped.
    """
    if not isinstance(intent, Mapping):
        return None
    lot = _text(intent.get("shipment_id"), MAX_LOT)
    stage = resolve_node_stage(intent.get("stage_id"), node_stages)
    if not lot or not stage:
        return None
    return {"shipment_id": lot, "stage_id": stage}


def capture(
    session: MutableMapping[str, Any],
    intent: Any,
    *,
    scope: Mapping[str, str] | None = None,
    node_stages: Mapping[str, str] | None = None,
) -> bool:
    """Remember ONE verified-shape intent; ``True`` only when it was new.

    The ``seq`` replay guard is the same one-shot contract every other v2
    trigger uses: a trigger value that is still visible in component state can
    never re-open the pane after the user closed it. A malformed or replayed
    intent changes nothing.
    """
    if not isinstance(session, MutableMapping):
        return False
    if not isinstance(intent, Mapping):
        return False
    seq = intent.get("seq")
    if isinstance(seq, bool) or not isinstance(seq, int):
        return False
    last = session.get(SEQ_KEY, 0)
    if isinstance(last, bool) or not isinstance(last, int):
        last = 0
    if seq <= last:
        return False
    session[SEQ_KEY] = seq
    normalized = normalize(intent, node_stages=node_stages)
    if normalized is None:
        return False
    stored: dict[str, str] = dict(normalized)
    # Keep the raw node id the operator clicked (display/debug only). It is
    # never used as a discussion scope on its own.
    raw_node = _text(intent.get("stage_id"), MAX_STAGE)
    if raw_node:
        stored["node_id"] = raw_node
    for key, value in (scope or {}).items():
        cleaned = _text(value, MAX_ACTOR)
        if cleaned:
            stored[str(key)[:40]] = cleaned
    session[FOCUS_KEY] = stored
    return True


def capture_from_result(session: MutableMapping[str, Any], result: Any,
                        *, event: str = "journey_focus",
                        scope: Mapping[str, str] | None = None,
                        node_stages: Mapping[str, str] | None = None) -> bool:
    """Read the v2 trigger payload for ``event`` (same shape as the shell)."""
    if not hasattr(result, "get"):
        return False
    payload = result.get(event)
    if not isinstance(payload, Mapping):
        return False
    data = payload.get("payload")
    if not isinstance(data, Mapping):
        data = {}
    return capture(
        session,
        {"seq": payload.get("seq"), "shipment_id": data.get("shipment_id"),
         "stage_id": data.get("stage_id")},
        scope=scope,
        node_stages=node_stages,
    )


def current(session: MutableMapping[str, Any]) -> dict[str, str] | None:
    """The stored intent, or ``None`` when no pane is focused."""
    if not isinstance(session, MutableMapping):
        return None
    stored = session.get(FOCUS_KEY)
    if not isinstance(stored, Mapping):
        return None
    normalized = normalize(stored)
    if normalized is None:
        return None
    return {**{key: _text(value, MAX_ACTOR) for key, value in stored.items()}, **normalized}


def clear(session: MutableMapping[str, Any]) -> None:
    """Close the focused pane. The replay guard is intentionally kept."""
    if isinstance(session, MutableMapping):
        session.pop(FOCUS_KEY, None)


def for_customer(request: Mapping[str, Any] | None, customer_id: str,
                 cards: Sequence[Any]) -> dict[str, str] | None:
    """Resolve ONE intent against the customer's OWN server-built lots."""
    normalized = normalize(request)
    principal = _text(customer_id, MAX_ACTOR)
    if normalized is None or not principal:
        return None
    stored_scope = _text((request or {}).get("customer_id"), MAX_ACTOR)
    if stored_scope and stored_scope != principal:
        return None
    for card in cards or ():
        if _text(getattr(card, "reference", ""), MAX_LOT) == normalized["shipment_id"]:
            return normalized
    return None


def for_staff(request: Mapping[str, Any] | None, username: str,
              shipments: Sequence[Any]) -> dict[str, str] | None:
    """Resolve ONE intent against the RBAC-filtered shipment projection.

    ``customer_id`` comes from that projection (server truth), never from the
    browser intent, so a forged lot/customer pair can only ever fail closed.
    """
    normalized = normalize(request, node_stages=STAFF_NODE_STAGES)
    actor = _text(username, MAX_ACTOR)
    if normalized is None or not actor:
        return None
    stored_scope = _text((request or {}).get("username"), MAX_ACTOR)
    if stored_scope and stored_scope != actor:
        return None
    for row in shipments or ():
        if not isinstance(row, Mapping):
            continue
        if _text(row.get("id"), MAX_LOT) != normalized["shipment_id"]:
            continue
        customer = _text(row.get("customerId"), MAX_ACTOR)
        if not customer:
            return None
        resolved = {**normalized, "customer_id": customer}
        raw_node = _text((request or {}).get("node_id"), MAX_STAGE)
        if raw_node:
            resolved["node_id"] = raw_node
        return resolved
    return None
