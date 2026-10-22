"""Issue #212 — Bể thông tin / ghi nhanh.

Capture independent snippets first, link them later. This module is only a
presentation adapter + the bounded dispatcher surface:

    typed event → current RBAC → core.database writers on quick_notes
      → audit → fresh readback

It does not create a second collection, ledger, FX engine, OCR path, or
payment posting. A pasted snippet is unverified source evidence.
"""

from __future__ import annotations

from typing import Any, Mapping

from views import logi_real_data as rd

INBOX_EVENTS = {
    "inbox_snippet_create",
    "inbox_snippet_link",
}

_UNKNOWN = rd.UNKNOWN_LABEL


def _text(value: Any) -> str:
    return rd.text(value)


def _when(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        try:
            return str(value.isoformat())
        except Exception:  # noqa: BLE001 - display fallback
            return str(value)
    text = str(value).strip()
    return "" if text in {"None", "nan"} else text


def _id_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _text(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _result(event: str, entity_id: str, ok: bool, error: str = "",
            readback: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"event": event, "id": entity_id, "ok": ok, "error": error, "readback": readback, **extra}


def snippet_projection(doc: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Public inbox card. Amounts stay UNKNOWN (null); this is not a payment."""
    if not isinstance(doc, Mapping):
        return None
    snippet_id = _text(doc.get("id"))
    if not snippet_id or snippet_id == "team_note":
        return None
    contract_ids = _id_list(doc.get("contract_ids"))
    linked_ids = _id_list(doc.get("linked_snippet_ids"))
    occurred = _text(doc.get("occurred_at"))
    return {
        "id": snippet_id,
        "rawText": _text(doc.get("raw_text")),
        "source": _text(doc.get("source")),
        "title": _text(doc.get("title")),
        "sourceRef": _text(doc.get("source_ref")),
        "occurredAt": occurred,
        "createdAt": _when(doc.get("created_at")),
        "createdBy": _text(doc.get("created_by")),
        "requestId": _text(doc.get("request_id")),
        "contractIds": contract_ids,
        "linkedSnippetIds": linked_ids,
        "linked": bool(contract_ids or linked_ids),
        "unverified": True,
        # UNKNOWN != ZERO: a snippet never invents an amount, currency or FX.
        "amount": None,
        "currency": "",
        "fxRate": None,
        "unknownLabel": _UNKNOWN,
    }


def inbox_projection(*, db: Any = None, user: Mapping[str, Any] | None = None) -> dict[str, Any]:  # noqa: ARG001 — user reserved for display hints only
    from core.auth import can_operate_business
    from core.database import load_inbox_snippets

    try:
        rows = load_inbox_snippets(db=db) if db is not None else load_inbox_snippets()
    except Exception:  # noqa: BLE001 - a missing inbox must not blank the desk
        rows = []
    snippets = [row for row in (snippet_projection(item) for item in rows) if row]
    return {
        "canWrite": bool(can_operate_business("shipment_edit")),
        "unverified": True,
        "snippets": snippets,
        "count": len(snippets),
        "linkedCount": sum(1 for row in snippets if row["linked"]),
        "unlinkedCount": sum(1 for row in snippets if not row["linked"]),
    }


def _audit(entity_id: str, limit: int = 8) -> list[dict[str, Any]]:
    from core.database import load_audit_logs

    return [
        {
            "action": _text(row.get("action")),
            "actor": _text(row.get("actor")),
            "createdAt": str(row.get("created_at") or ""),
        }
        for row in (load_audit_logs("inbox_snippet", entity_id, limit=limit) or [])
        if isinstance(row, Mapping)
    ]


def _handle_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import create_inbox_snippet

    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", snippet_id: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_create", snippet_id, ok, error, requestId=request_id, **extra)

    if not request_id:
        return _res(False, "Thiếu mã yêu cầu.")
    outcome = create_inbox_snippet(
        raw_text=_text(payload.get("rawText") or payload.get("raw_text")),
        request_id=request_id,
        source=_text(payload.get("source")),
        title=_text(payload.get("title")),
        source_ref=_text(payload.get("sourceRef") or payload.get("source_ref")),
        occurred_at=_text(payload.get("occurredAt") or payload.get("occurred_at")),
    )
    snippet = snippet_projection(outcome.get("snippet") if isinstance(outcome, Mapping) else None)
    snippet_id = _text((snippet or {}).get("id"))
    if not outcome.get("ok"):
        return _res(False, _text(outcome.get("error")) or "Không lưu được mẩu tin.", snippet_id)
    if snippet is None:
        return _res(False, "Writer báo thành công nhưng đọc lại không thấy mẩu tin.")
    return _res(
        True,
        snippet_id=snippet_id,
        readback=snippet,
        duplicate=bool(outcome.get("duplicate")),
        persisted={"id": snippet_id},
        audit=_audit(snippet_id),
        unverified=True,
    )


def _handle_link(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import relate_inbox_snippets

    request_id = _text(payload.get("requestId"))
    raw_ids = payload.get("snippetIds") or payload.get("snippet_ids") or []
    if not isinstance(raw_ids, list):
        raw_ids = [raw_ids] if raw_ids else []
    snippet_ids = [_text(item) for item in raw_ids if _text(item)]
    action = _text(payload.get("action")).lower() or "link"
    target_type = _text(payload.get("targetType") or payload.get("target_type")).lower()
    target_id = _text(payload.get("targetId") or payload.get("target_id"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_link", target_id, ok, error, requestId=request_id, **extra)

    if not request_id:
        return _res(False, "Thiếu mã yêu cầu.")
    outcome = relate_inbox_snippets(
        snippet_ids=snippet_ids,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
    )
    rows = [
        projected
        for projected in (
            snippet_projection(item)
            for item in (outcome.get("snippets") or [])
            if isinstance(item, Mapping)
        )
        if projected
    ]
    if not outcome.get("ok"):
        return _res(False, _text(outcome.get("error")) or "Không ghép được mẩu tin.")
    return _res(
        True,
        readback={"snippets": rows, "targetType": target_type, "targetId": target_id, "action": action},
        duplicate=bool(outcome.get("duplicate")),
        unverified=True,
        audit=_audit(snippet_ids[0]) if snippet_ids else [],
    )


_HANDLERS = {
    "inbox_snippet_create": _handle_create,
    "inbox_snippet_link": _handle_link,
}


def consume_inbox_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """Bounded inbox dispatcher. A replayed seq never double-writes."""
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(INBOX_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        handler = _HANDLERS.get(event_name)
        if handler is None:  # pragma: no cover - set and map stay aligned
            continue
        try:
            outcomes.append(handler(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            request_id = _text(data.get("requestId"))
            extra = {"requestId": request_id} if request_id else {}
            outcomes.append(_result(
                event_name, _text(data.get("id")), False,
                f"{type(exc).__name__}: {exc}", **extra,
            ))
    if outcomes:
        session["writes"] = outcomes
    return outcomes
