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


def _text(value: Any, limit: int = 0) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    cleaned = str(value).replace("\r", " ").strip()
    return cleaned[:limit] if limit else cleaned


def normalize(intent: Any) -> dict[str, str] | None:
    """Shrink one browser intent to ``{shipment_id, stage_id}`` or ``None``."""
    if not isinstance(intent, Mapping):
        return None
    lot = _text(intent.get("shipment_id"), MAX_LOT)
    stage = _text(intent.get("stage_id"), MAX_STAGE).lower()
    if not lot or stage not in notes.STAGE_IDS:
        return None
    return {"shipment_id": lot, "stage_id": stage}


def capture(
    session: MutableMapping[str, Any],
    intent: Any,
    *,
    scope: Mapping[str, str] | None = None,
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
    normalized = normalize(intent)
    if normalized is None:
        return False
    stored: dict[str, str] = dict(normalized)
    for key, value in (scope or {}).items():
        cleaned = _text(value, MAX_ACTOR)
        if cleaned:
            stored[str(key)[:40]] = cleaned
    session[FOCUS_KEY] = stored
    return True


def capture_from_result(session: MutableMapping[str, Any], result: Any,
                        *, event: str = "journey_focus",
                        scope: Mapping[str, str] | None = None) -> bool:
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
    normalized = normalize(request)
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
        return {**normalized, "customer_id": customer}
    return None
