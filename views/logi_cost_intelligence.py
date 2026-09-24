"""Bounded Cost Intelligence event handlers for the existing C1 dispatcher."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value or "").strip()


def handle_cost_rate_parse(payload: Mapping[str, Any], deps: Mapping[str, Any]) -> dict[str, Any]:
    from core.cost_intelligence import parse_cost_rate_text
    from core.database import load_cost_catalog

    request_id = _text(payload.get("requestId"))
    raw = _text(payload.get("text"))
    received_raw = _text(payload.get("receivedOn"))
    received_on = date.today()
    if received_raw:
        try:
            received_on = datetime.strptime(received_raw, "%Y-%m-%d").date()
        except ValueError:
            return deps["_result"](
                "cost_rate_parse", "", False,
                "Ngày nhận bảng giá không hợp lệ.", requestId=request_id,
            )
    try:
        parsed = parse_cost_rate_text(raw, catalog=load_cost_catalog(), received_on=received_on)
    except ValueError as exc:
        return deps["_result"]("cost_rate_parse", "", False, str(exc), requestId=request_id)
    return deps["_result"](
        "cost_rate_parse", "", True, requestId=request_id, parsed=parsed,
        persisted={"rowCount": parsed["summary"]["rowCount"], "needsReview": parsed["summary"]["needsReview"]},
    )


def handle_cost_rate_save(payload: Mapping[str, Any], deps: Mapping[str, Any]) -> dict[str, Any]:
    from core.cost_intelligence import prepare_rate_snapshot
    from core.database import get_last_db_error, load_cost_rate_snapshots, save_cost_rate_snapshot

    request_id = _text(payload.get("requestId"))
    try:
        snapshot = prepare_rate_snapshot(payload, actor=deps["_actor"]())
    except ValueError as exc:
        return deps["_result"]("cost_rate_save", "", False, str(exc), requestId=request_id)
    if not save_cost_rate_snapshot(snapshot):
        return deps["_result"](
            "cost_rate_save", _text(snapshot.get("id")), False,
            get_last_db_error() or "Không lưu được snapshot giá vốn.", requestId=request_id,
        )
    fresh = next((row for row in load_cost_rate_snapshots(limit=2000) if _text(row.get("id")) == _text(snapshot.get("id"))), None)
    if fresh is None:
        return deps["_result"](
            "cost_rate_save", _text(snapshot.get("id")), False,
            "Writer báo thành công nhưng đọc lại không thấy snapshot giá vốn.", requestId=request_id,
        )
    return deps["_result"](
        "cost_rate_save", _text(snapshot.get("id")), True, requestId=request_id,
        readback=fresh, persisted={"id": _text(snapshot.get("id")), "status": _text(snapshot.get("status"))},
        audit=deps["_audit"]("cost_rate_snapshot", _text(snapshot.get("id"))),
    )


def handle_cost_catalog_save(payload: Mapping[str, Any], deps: Mapping[str, Any]) -> dict[str, Any]:
    from core.cost_intelligence import normalize_catalog_entry
    from core.database import get_last_db_error, load_cost_catalog, save_cost_catalog_entry

    request_id = _text(payload.get("requestId"))
    try:
        normalized = normalize_catalog_entry(payload)
    except ValueError as exc:
        return deps["_result"]("cost_catalog_save", "", False, str(exc), requestId=request_id)
    if not save_cost_catalog_entry(normalized):
        return deps["_result"](
            "cost_catalog_save", _text(normalized.get("id")), False,
            get_last_db_error() or "Không lưu được danh mục giá vốn.", requestId=request_id,
        )
    fresh = load_cost_catalog().get(_text(normalized.get("id")))
    if not isinstance(fresh, Mapping):
        return deps["_result"](
            "cost_catalog_save", _text(normalized.get("id")), False,
            "Writer báo thành công nhưng đọc lại không thấy danh mục.", requestId=request_id,
        )
    return deps["_result"](
        "cost_catalog_save", _text(normalized.get("id")), True, requestId=request_id,
        readback=dict(fresh), persisted={"id": _text(normalized.get("id")), "kind": _text(normalized.get("kind"))},
        audit=deps["_audit"]("cost_catalog", _text(normalized.get("id"))),
    )
