"""Issue #212 — Bể thông tin / ghi nhanh.

Capture independent snippets first (text and/or files), link them later.
This module is only a presentation adapter + the bounded dispatcher surface:

    typed event → current RBAC → core.database writers on quick_notes
      → existing GridFS/Drive adapters for note-owned bytes → audit → readback

It does not create a second collection, ledger, FX engine, OCR path, or
payment posting. A pasted snippet is unverified source evidence.
"""

from __future__ import annotations

from typing import Any, Mapping

from views import logi_real_data as rd

INBOX_EVENTS = {
    "inbox_snippet_create",
    "inbox_snippet_link",
    "inbox_snippet_attach",
    "inbox_snippet_download",
    "inbox_snippet_search",
}

INBOX_QUERY_KEY = "logi_inbox_query"
INBOX_DOWNLOAD_KEY = "logi_inbox_attachment_download"

_UNKNOWN = rd.UNKNOWN_LABEL

try:
    import streamlit as st
except ImportError:  # pragma: no cover - tests still import streamlit
    st = None  # type: ignore[assignment]


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


def _session_map(key: str) -> dict[str, Any]:
    if st is None:
        return {}
    state = st.session_state.get(key)
    return dict(state) if isinstance(state, Mapping) else {}


def _set_session(key: str, value: Mapping[str, Any]) -> None:
    if st is None:
        return
    st.session_state[key] = dict(value)


def _query_state() -> dict[str, str]:
    state = _session_map(INBOX_QUERY_KEY)
    filt = _text(state.get("filter")).lower()
    if filt not in {"all", "linked", "unlinked"}:
        filt = "all"
    return {
        "query": _text(state.get("query")),
        "filter": filt,
        "before": _text(state.get("before")),
    }


def _download_state() -> dict[str, Any]:
    return _session_map(INBOX_DOWNLOAD_KEY)


def _can_access_inbox() -> bool:
    from core.auth import can_operate_business

    return bool(can_operate_business("shipment_edit"))


def snippet_projection(
    doc: Mapping[str, Any] | None,
    *,
    download: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Public inbox card. Amounts stay UNKNOWN (null); this is not a payment."""
    from core.inbox_attachments import project_inbox_attachment

    if not isinstance(doc, Mapping):
        return None
    snippet_id = _text(doc.get("id"))
    if not snippet_id or snippet_id == "team_note":
        return None
    contract_ids = _id_list(doc.get("contract_ids"))
    shipment_ids = _id_list(doc.get("shipment_ids"))
    linked_ids = _id_list(doc.get("linked_snippet_ids"))
    occurred = _text(doc.get("occurred_at"))
    download_for = download if _text((download or {}).get("snippetId")) == snippet_id else None
    attachments = [
        projected
        for projected in (
            project_inbox_attachment(item, download=download_for)
            for item in (doc.get("attachments") or [])
            if isinstance(item, Mapping)
        )
        if projected
    ]
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
        "shipmentIds": shipment_ids,
        "linkedSnippetIds": linked_ids,
        "linked": bool(contract_ids or shipment_ids or linked_ids),
        "attachments": attachments,
        "unverified": True,
        # UNKNOWN != ZERO: a snippet never invents an amount, currency or FX.
        "amount": None,
        "currency": "",
        "fxRate": None,
        "unknownLabel": _UNKNOWN,
    }


def _project_linked_map(
    grouped: Mapping[str, list[Mapping[str, Any]]] | None,
    *,
    download: Mapping[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for key, rows in (grouped or {}).items():
        projected = [
            item
            for item in (snippet_projection(row, download=download) for row in rows)
            if item
        ]
        if projected:
            out[str(key)] = projected
    return out


def inbox_projection(
    *,
    db: Any = None,
    user: Mapping[str, Any] | None = None,  # noqa: ARG001 — display reserved
    contract_ids: list[str] | None = None,
    shipment_ids: list[str] | None = None,
) -> dict[str, Any]:
    from core.database import load_inbox_snippets_linked_to, query_inbox_snippets

    can_access = _can_access_inbox()
    empty = {
        "canRead": can_access,
        "canWrite": can_access,
        "unverified": True,
        "snippets": [],
        "count": 0,
        "linkedCount": 0,
        "unlinkedCount": 0,
        "hasMore": False,
        "query": "",
        "filter": "all",
        "byContractId": {},
        "byShipmentId": {},
    }
    if not can_access:
        return empty

    state = _query_state()
    download = _download_state()
    try:
        page = query_inbox_snippets(
            db=db,
            query=state["query"],
            link_filter=state["filter"],
            before=state["before"],
        ) if db is not None else query_inbox_snippets(
            query=state["query"],
            link_filter=state["filter"],
            before=state["before"],
        )
    except Exception:  # noqa: BLE001 - a missing inbox must not blank the desk
        page = {
            "rows": [],
            "count": 0,
            "linked_count": 0,
            "unlinked_count": 0,
            "has_more": False,
            "query": state["query"],
            "filter": state["filter"],
        }
    snippets = [
        row for row in (
            snippet_projection(item, download=download) for item in (page.get("rows") or [])
        ) if row
    ]
    try:
        linked_maps = load_inbox_snippets_linked_to(
            contract_ids=contract_ids or [],
            shipment_ids=shipment_ids or [],
            db=db,
        ) if db is not None else load_inbox_snippets_linked_to(
            contract_ids=contract_ids or [],
            shipment_ids=shipment_ids or [],
        )
    except Exception:  # noqa: BLE001
        linked_maps = {"by_contract": {}, "by_shipment": {}}
    by_contract = _project_linked_map((linked_maps or {}).get("by_contract"), download=download)
    by_shipment = _project_linked_map((linked_maps or {}).get("by_shipment"), download=download)
    return {
        "canRead": True,
        "canWrite": True,
        "unverified": True,
        "snippets": snippets,
        "count": int(page.get("count") or 0),
        "linkedCount": int(page.get("linked_count") or 0),
        "unlinkedCount": int(page.get("unlinked_count") or 0),
        "hasMore": bool(page.get("has_more")),
        "query": _text(page.get("query")),
        "filter": _text(page.get("filter")) or "all",
        "byContractId": by_contract,
        "byShipmentId": by_shipment,
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


def _file_sig(name: str, size: int, digest: str) -> str:
    return f"{name}:{size}:{digest}"


def _prepare_files(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Decode and validate files BEFORE any byte-store call. RBAC already passed."""
    from core.inbox_attachments import (
        CODE_INVALID,
        CODE_SIZE,
        CODE_TOO_MANY_FILES,
        INBOX_MAX_FILES,
        MAX_UPLOAD_BYTES,
        UploadRefused,
        decode_upload_payload,
        sha256_hex,
        validate_upload,
    )

    raw = payload.get("files") if "files" in payload else payload.get("attachments")
    if raw in (None, ""):
        raw = []
    if not isinstance(raw, list):
        return [], {"code": CODE_INVALID, "error": "Danh sách tệp không hợp lệ."}
    if len(raw) > INBOX_MAX_FILES:
        return [], {
            "code": CODE_TOO_MANY_FILES,
            "error": f"Mỗi mẩu tin tối đa {INBOX_MAX_FILES} tệp.",
        }
    prepared: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            return [], {"code": CODE_INVALID, "error": "Tệp gửi lên không hợp lệ."}
        declared_raw = item.get("size")
        declared_size: int | None = None
        if declared_raw is not None:
            try:
                declared_size = int(declared_raw)
            except (TypeError, ValueError):
                return [], {"code": CODE_INVALID, "error": "Kích thước tệp không hợp lệ."}
            if declared_size > MAX_UPLOAD_BYTES:
                return [], {
                    "code": CODE_SIZE,
                    "error": (
                        f"Tệp vượt giới hạn {MAX_UPLOAD_BYTES // (1024 * 1024)} MB — "
                        "chưa gọi kho chứng từ, chưa lưu dữ liệu."
                    ),
                }
        try:
            data, size = decode_upload_payload(item)
            safe_name, canonical_mime, _kind = validate_upload(
                _text(item.get("fileName") or item.get("name")),
                _text(item.get("mime")),
                declared_size if declared_size is not None else size,
                data,
            )
        except UploadRefused as refusal:
            return [], {"code": refusal.code, "error": refusal.message}
        digest = sha256_hex(data)
        prepared.append(
            {
                "file_name": safe_name,
                "mime": canonical_mime,
                "data": data,
                "size": size,
                "digest": digest,
                "sig": _file_sig(safe_name, size, digest),
            }
        )
    return prepared, None


def _persist_prepared_files(
    snippet_id: str,
    prepared: list[dict[str, Any]],
    *,
    uploaded_by: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Store bytes then metadata. Partial failure does not roll back the note.

    Compensation deletes the just-written bytes only when metadata absence is
    proven. A committed-but-unproven readback keeps both sides.
    """
    from core.database import (
        ATTACHMENT_PROBE_ABSENT_PROVEN,
        append_inbox_attachment,
        probe_inbox_attachment_identity,
    )
    from core.inbox_attachments import compensate_stored_bytes, store_inbox_bytes

    failed: list[dict[str, Any]] = []
    stored: list[dict[str, Any]] = []
    orphan_risk = False
    for item in prepared:
        outcome = store_inbox_bytes(
            snippet_id=snippet_id,
            file_name=item["file_name"],
            mime=item["mime"],
            data=item["data"],
            declared_size=item["size"],
            uploaded_by=uploaded_by,
        )
        if not outcome.get("ok"):
            failed.append(
                {
                    "fileName": item["file_name"],
                    "error": _text(outcome.get("error")) or "Không lưu được tệp.",
                    "code": _text(outcome.get("code")),
                }
            )
            continue
        record = dict(outcome.get("record") or {})
        saved = append_inbox_attachment(snippet_id, record)
        if saved.get("ok"):
            if saved.get("duplicate"):
                compensate_stored_bytes(
                    client=outcome.get("client"),
                    storage_file_id=_text(record.get("storage_file_id")),
                )
            stored.append(dict(saved.get("record") or record))
            continue
        probe_state = _text(saved.get("probe_state"))
        if not probe_state:
            probe_state, _durable = probe_inbox_attachment_identity(snippet_id, record)
        if probe_state != ATTACHMENT_PROBE_ABSENT_PROVEN:
            failed.append(
                {
                    "fileName": item["file_name"],
                    "error": _text(saved.get("error"))
                    or "Chưa xác minh được metadata; giữ nguyên tệp, không xoá bù.",
                    "code": _text(saved.get("code")) or "METADATA_READBACK_UNPROVEN",
                    "orphanRisk": False,
                    "compensationAttempted": False,
                }
            )
            continue
        deleted = compensate_stored_bytes(
            client=outcome.get("client"),
            storage_file_id=_text(record.get("storage_file_id")),
        )
        if not deleted:
            orphan_risk = True
        failed.append(
            {
                "fileName": item["file_name"],
                "error": _text(saved.get("error")) or "Không ghi được metadata tệp.",
                "code": _text(saved.get("code")) or "METADATA_WRITE_FAILED",
                "orphanRisk": not deleted,
                "compensationAttempted": True,
            }
        )
    return stored, failed, orphan_risk


def _handle_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import current_user
    from core.database import create_inbox_snippet, inbox_request_fingerprint, load_inbox_snippet

    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", snippet_id: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_create", snippet_id, ok, error, requestId=request_id, **extra)

    if not request_id:
        return _res(False, "Thiếu mã yêu cầu.")
    if not _can_access_inbox():
        return _res(False, "RBAC: không có quyền ghi nhanh.", gate="BLOCKED_PERMISSION_DENIED")

    prepared, file_error = _prepare_files(payload)
    if file_error is not None:
        return _res(False, file_error["error"], gate=file_error["code"])

    raw = _text(payload.get("rawText") or payload.get("raw_text"))
    source = _text(payload.get("source"))
    title = _text(payload.get("title"))
    source_ref = _text(payload.get("sourceRef") or payload.get("source_ref"))
    occurred_at = _text(payload.get("occurredAt") or payload.get("occurred_at"))
    fingerprint = inbox_request_fingerprint(
        raw_text=raw,
        source=source,
        title=title,
        source_ref=source_ref,
        occurred_at=occurred_at,
        file_sigs=[item["sig"] for item in prepared],
    )
    outcome = create_inbox_snippet(
        raw_text=raw,
        request_id=request_id,
        source=source,
        title=title,
        source_ref=source_ref,
        occurred_at=occurred_at,
        has_files=bool(prepared),
        fingerprint=fingerprint,
    )
    snippet = snippet_projection(outcome.get("snippet") if isinstance(outcome, Mapping) else None)
    snippet_id = _text((snippet or {}).get("id"))
    if not outcome.get("ok"):
        return _res(False, _text(outcome.get("error")) or "Không lưu được mẩu tin.", snippet_id)
    if snippet is None:
        return _res(False, "Writer báo thành công nhưng đọc lại không thấy mẩu tin.")
    if outcome.get("duplicate"):
        return _res(
            True,
            snippet_id=snippet_id,
            readback=snippet,
            duplicate=True,
            persisted={"id": snippet_id},
            audit=_audit(snippet_id),
            unverified=True,
        )

    actor = _text((current_user() or {}).get("username"))
    stored, failed, orphan_risk = _persist_prepared_files(snippet_id, prepared, uploaded_by=actor)
    fresh = snippet_projection(load_inbox_snippet(snippet_id)) or snippet
    partial = bool(failed)
    return _res(
        True,
        snippet_id=snippet_id,
        readback=fresh,
        duplicate=False,
        partial=partial,
        failedFiles=failed,
        persisted={"id": snippet_id, "attachmentCount": len(stored)},
        audit=_audit(snippet_id),
        unverified=True,
        orphanRisk=orphan_risk,
        message=(
            "Đã lưu mẩu tin nhưng một số tệp chưa vào kho — thử lại các tệp lỗi, không tạo mẩu mới."
            if partial
            else ""
        ),
    )


def _handle_attach(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import current_user
    from core.database import load_inbox_snippet

    request_id = _text(payload.get("requestId"))
    snippet_id = _text(payload.get("snippetId") or payload.get("id"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_attach", snippet_id, ok, error, requestId=request_id, **extra)

    if not request_id:
        return _res(False, "Thiếu mã yêu cầu.")
    if not snippet_id:
        return _res(False, "Thiếu mã mẩu tin.")
    if not _can_access_inbox():
        return _res(False, "RBAC: không có quyền ghi nhanh.", gate="BLOCKED_PERMISSION_DENIED")
    existing = load_inbox_snippet(snippet_id)
    if existing is None:
        return _res(False, f"Không tìm thấy mẩu tin {snippet_id}.")
    prepared, file_error = _prepare_files(payload)
    if file_error is not None:
        return _res(False, file_error["error"], gate=file_error["code"])
    if not prepared:
        return _res(False, "Chưa có tệp để đính kèm.")
    actor = _text((current_user() or {}).get("username"))
    stored, failed, orphan_risk = _persist_prepared_files(snippet_id, prepared, uploaded_by=actor)
    fresh = snippet_projection(load_inbox_snippet(snippet_id))
    partial = bool(failed)
    if fresh is None:
        return _res(False, "Không đọc lại được mẩu tin sau khi đính kèm.")
    return _res(
        True,
        readback=fresh,
        partial=partial,
        failedFiles=failed,
        persisted={"id": snippet_id, "attachmentCount": len((fresh or {}).get("attachments") or [])},
        audit=_audit(snippet_id),
        unverified=True,
        orphanRisk=orphan_risk,
        message=(
            "Một số tệp chưa vào kho — thử lại các tệp lỗi, không tạo mẩu mới."
            if partial
            else ""
        ),
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
    if not _can_access_inbox():
        return _res(False, "RBAC: không có quyền ghép thông tin.", gate="BLOCKED_PERMISSION_DENIED")
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


def _handle_search(payload: Mapping[str, Any]) -> dict[str, Any]:
    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_search", "", ok, error, requestId=request_id, **extra)

    if not _can_access_inbox():
        return _res(False, "RBAC: không có quyền xem bể thông tin.", gate="BLOCKED_PERMISSION_DENIED")
    filt = _text(payload.get("filter")).lower() or "all"
    if filt not in {"all", "linked", "unlinked"}:
        filt = "all"
    state = {
        "query": _text(payload.get("query"))[:120],
        "filter": filt,
        "before": _text(payload.get("before")),
    }
    _set_session(INBOX_QUERY_KEY, state)
    return _res(True, readback=state, unverified=True)


def _handle_download(payload: Mapping[str, Any]) -> dict[str, Any]:
    import base64 as _base64

    from core.database import find_inbox_attachment, load_inbox_snippet
    from core.inbox_attachments import CODE_NOT_FOUND, fetch_inbox_bytes, storage_label

    request_id = _text(payload.get("requestId"))
    snippet_id = _text(payload.get("snippetId"))
    attachment_id = _text(payload.get("attachmentId"))
    shipment_id = _text(payload.get("shipmentId"))
    contract_id = _text(payload.get("contractId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("inbox_snippet_download", snippet_id, ok, error, requestId=request_id, **extra)

    if not snippet_id or not attachment_id:
        return _res(False, "Thiếu mã mẩu tin hoặc mã tệp.", gate="INVALID_REQUEST")
    if not _can_access_inbox():
        return _res(False, "RBAC: không có quyền đọc tệp bể thông tin.", gate="BLOCKED_PERMISSION_DENIED")

    snippet = load_inbox_snippet(snippet_id)
    if snippet is None:
        return _res(False, "Không tìm thấy mẩu tin.", gate=CODE_NOT_FOUND)
    if shipment_id:
        if shipment_id not in _id_list(snippet.get("shipment_ids")):
            return _res(
                False,
                "Tệp bể thông tin không thuộc lô hàng này.",
                gate="INBOX_TARGET_MISMATCH",
            )
    if contract_id:
        if contract_id not in _id_list(snippet.get("contract_ids")):
            return _res(
                False,
                "Tệp bể thông tin không thuộc hợp đồng này.",
                gate="INBOX_TARGET_MISMATCH",
            )

    stored = find_inbox_attachment(snippet_id, attachment_id)
    if stored is None:
        return _res(False, "Không tìm thấy tệp đính kèm này.", gate=CODE_NOT_FOUND)

    outcome = fetch_inbox_bytes(stored)
    if not outcome.get("ok"):
        return _res(
            False,
            _text(outcome.get("error")) or f"Không đọc được tệp từ {storage_label()}.",
            gate=_text(outcome.get("code")) or "DOWNLOAD_FAILED",
        )
    data = bytes(outcome.get("data") or b"")
    previous = _download_state()
    seq = int(previous.get("seq") or 0) + 1
    _set_session(
        INBOX_DOWNLOAD_KEY,
        {
            "attachmentId": attachment_id,
            "snippetId": snippet_id,
            "fileName": _text(stored.get("original_name")) or _text(stored.get("stored_name")),
            "mime": _text(stored.get("mime")),
            "bytes": len(data),
            "seq": seq,
            "base64": _base64.b64encode(data).decode("ascii"),
        },
    )
    return _res(
        True,
        readback={"snippetId": snippet_id, "attachmentId": attachment_id, "seq": seq},
        persisted={
            "attachmentId": attachment_id,
            "fileName": _text(stored.get("original_name")),
            "size": len(data),
            "seq": seq,
        },
        gate="DOWNLOADED",
    )


_HANDLERS = {
    "inbox_snippet_create": _handle_create,
    "inbox_snippet_link": _handle_link,
    "inbox_snippet_attach": _handle_attach,
    "inbox_snippet_download": _handle_download,
    "inbox_snippet_search": _handle_search,
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
                event_name, _text(data.get("id") or data.get("snippetId")), False,
                f"{type(exc).__name__}: {exc}", **extra,
            ))
    if outcomes:
        session["writes"] = outcomes
    return outcomes
