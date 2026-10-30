"""Trao đổi ngay trong Journey Map — cùng một backend, hai cổng.

Issue #236: a Journey Map node click must open the real stage conversation
INSIDE the map (the customer bubble / the internal node panel), not a
Streamlit form above the map. This module is the presentation adapter between
the already existing note backend (:mod:`core.journey_notes`) and those two
components:

* :func:`build_staff_discussion` / :func:`build_customer_discussion` produce a
  **bounded** discussion slice for ONE verified lot + ONE stage. Nothing is
  preloaded for other lots, and INTERNAL content never enters a customer
  payload.
* :func:`consume_staff_triggers` / :func:`consume_customer_triggers` handle the
  typed component events (write a comment/reply, read one attachment) through
  ``core.journey_notes.create_stage_note`` / ``read_note_attachment`` and the
  configured byte store in ``core.inbox_attachments``.

Trust model: the browser sends an INTENT only (lot id + node id + text + the
one chosen file). The principal, tenant, stage, visibility and permission are
always re-derived server-side. Attachment bytes travel as bounded base64
because that is the transport this app already proves for
``shipment_attachment_upload`` and ``inbox_snippet_create`` — no second upload
service, no unbounded payload, no bytes in the shared view-model.
"""
from __future__ import annotations

import base64
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

from core import journey_notes as notes
from views import journey_focus

try:  # tests import the module with a Streamlit runtime available; keep it soft
    import streamlit as st
except ImportError:  # pragma: no cover - Streamlit is a hard dependency in the app
    st = None  # type: ignore[assignment]

STAFF_EVENTS = {"journey_note_create", "journey_note_download"}
CUSTOMER_EVENTS = {"journey_note_create", "journey_note_download"}
#: The existing read-only "open this node's thread" intent (PR #235) is reused
#: unchanged: the same one-shot ``seq`` contract, the same server-side
#: re-validation. The difference is WHERE the thread is rendered.
FOCUS_EVENT = "journey_focus"

STAFF_DOWNLOAD_KEY = "logi_journey_note_download"
STAFF_REQUESTS_KEY = "logi_journey_note_requests"
CUSTOMER_DOWNLOAD_KEY = "logi_customer_journey_note_download"
CUSTOMER_REQUESTS_KEY = "logi_customer_journey_note_requests"
CUSTOMER_OUTCOME_KEY = "logi_customer_journey_note_outcome"
CUSTOMER_DOWNLOAD_OUTCOME_KEY = "logi_customer_journey_note_download_outcome"

MAX_REQUEST_MEMORY = 40


def _text(value: Any, limit: int = 0) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    text = str(value).replace("\r", " ").strip()
    return text[:limit] if limit else text


def _result(event: str, entity_id: str, ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
    return {"event": event, "id": entity_id, "ok": ok, "error": error, **extra}


# --------------------------------------------------------------------------- #
# actors / permissions
# --------------------------------------------------------------------------- #

def staff_actor(user: Mapping[str, Any] | None) -> dict[str, str] | None:
    """The server-side actor for one authenticated internal user."""
    if not isinstance(user, Mapping):
        return None
    username = _text(user.get("username"), 100)
    role = _text(user.get("role"), 40).lower()
    if not username or not role:
        return None
    return {"kind": "user", "username": username, "role": role}


def customer_actor(principal: Any) -> dict[str, str] | None:
    """The server-side actor for one OIDC-proven customer principal."""
    customer_id = _text(getattr(principal, "customer_id", ""), 120)
    if not customer_id:
        return None
    return {
        "kind": "customer",
        "customer_id": customer_id,
        "name": _text(getattr(principal, "display_name", ""), 100) or "Khách hàng",
    }


def _staff_can_use(user: Mapping[str, Any] | None) -> bool:
    """Same single RBAC matrix the existing discussion pane used."""
    actor = staff_actor(user)
    return bool(actor and notes.user_may_write(actor["role"]))


def _max_upload_bytes() -> int:
    from core.shipment_attachments import MAX_UPLOAD_BYTES

    return int(MAX_UPLOAD_BYTES)


def _remember_focus(focus: Mapping[str, str], **scope: str) -> None:
    """Pin the ONE verified focus so the next read builds THIS thread.

    Only values already proven by :mod:`views.journey_focus` are stored; the
    browser never supplies ``customer_id`` or the resolved stage here.
    """
    if st is None:
        return
    stage = _text(focus.get("stage_id"), 40).lower()
    shipment = _text(focus.get("shipment_id"), 120)
    if stage not in notes.STAGE_IDS or not shipment:
        return
    stored: dict[str, str] = {"shipment_id": shipment, "stage_id": stage}
    node_id = _text(focus.get("node_id"), 40)
    if node_id:
        stored["node_id"] = node_id
    for key, value in scope.items():
        cleaned = _text(value, 120)
        if cleaned:
            stored[key] = cleaned
    st.session_state[journey_focus.FOCUS_KEY] = stored


# --------------------------------------------------------------------------- #
# read side — ONE bounded lot + stage thread
# --------------------------------------------------------------------------- #

def _node_label(rows: Sequence[Any], shipment_id: str, node_id: str) -> str:
    wanted = _text(node_id, 40)
    if not wanted:
        return ""
    for row in rows or ():
        if not isinstance(row, Mapping) or _text(row.get("id"), 120) != shipment_id:
            continue
        journey = row.get("journey") if isinstance(row.get("journey"), Mapping) else {}
        for node in journey.get("nodes") or ():
            if isinstance(node, Mapping) and _text(node.get("id"), 40) == wanted:
                return _text(node.get("label"), 120)
        break
    return ""


def _take_download(session_key: str, shipment_id: str, stage_id: str) -> dict[str, Any] | None:
    """Return the ONE just-read file for THIS lot+stage and drop its bytes.

    Bytes are session-scoped exactly like the inbox / shipment attachment
    download channel: the browser receives them once, inside the next payload,
    and the session slot never accumulates files.
    """
    if st is None:
        return None
    stored = st.session_state.get(session_key)
    if not isinstance(stored, Mapping):
        return None
    if (
        _text(stored.get("shipmentId"), 120) != shipment_id
        or _text(stored.get("stageId"), 40).lower() != stage_id
    ):
        return None
    st.session_state.pop(session_key, None)
    encoded = _text(stored.get("base64"))
    if not encoded:
        return None
    return {
        "noteId": _text(stored.get("noteId"), 80),
        "attachmentId": _text(stored.get("attachmentId"), 120),
        "name": _text(stored.get("fileName"), 255),
        "mime": _text(stored.get("mime"), 255) or "application/octet-stream",
        "base64": encoded,
        "seq": int(stored.get("seq") or 0),
    }


def _take_outcome(key: str, shipment_id: str, stage_id: str) -> dict[str, Any] | None:
    """The ONE authoritative outcome of this lot+stage's last write, once."""
    if st is None or not key:
        return None
    stored = st.session_state.get(key)
    if not isinstance(stored, Mapping):
        return None
    if (
        _text(stored.get("shipmentId"), 120) != shipment_id
        or _text(stored.get("stageId"), 40).lower() != stage_id
    ):
        return None
    st.session_state.pop(key, None)
    return {
        "requestId": _text(stored.get("requestId"), 80),
        "ok": bool(stored.get("ok")),
        "error": _text(stored.get("error"), 300),
        "duplicate": bool(stored.get("duplicate")),
    }


def _discussion_payload(
    *,
    actor: Mapping[str, str],
    focus: Mapping[str, str],
    rows: Sequence[Any],
    session_key: str,
    can_see_internal: bool,
    db: Any = None,
    outcome_key: str = "",
) -> dict[str, Any]:
    shipment_id = _text(focus.get("shipment_id"), 120)
    stage_id = _text(focus.get("stage_id"), 40).lower()
    node_id = _text(focus.get("node_id"), 40)
    payload: dict[str, Any] = {
        "shipmentId": shipment_id,
        "stageId": stage_id,
        "nodeId": node_id,
        "nodeLabel": _node_label(rows, shipment_id, node_id),
        "stageLabel": notes.STAGE_LABELS.get(stage_id, stage_id),
        "canWrite": (
            True if actor.get("kind") == "customer"
            else notes.user_may_write(actor.get("role", ""))
        ),
        "canAttach": True,
        "canSeeInternal": can_see_internal,
        "maxFiles": notes.MAX_FILES_PER_SUBMIT,
        "maxBytes": _max_upload_bytes(),
        "notes": [],
        "count": 0,
        "download": _take_download(session_key, shipment_id, stage_id),
        "outcome": _take_outcome(outcome_key, shipment_id, stage_id),
        "downloadOutcome": _take_outcome(
            CUSTOMER_DOWNLOAD_OUTCOME_KEY if outcome_key == CUSTOMER_OUTCOME_KEY else "",
            shipment_id, stage_id,
        ),
        "error": "",
    }
    try:
        records = notes.list_stage_notes(
            customer_id=_text(focus.get("customer_id"), 120),
            shipment_id=shipment_id,
            stage_id=stage_id,
            actor=actor,
            db=db,
        )
    except notes.JourneyNoteDenied as denied:
        payload["error"] = _text(denied, 300) or "Không đọc được trao đổi."
        return payload
    # ``core.journey_notes`` already projects each attachment through the ONE
    # public card (no storage id, no hash, no URL); the view adds no second shape.
    thread = notes.build_thread(records)
    payload["notes"] = thread
    payload["count"] = sum(1 + len(row.get("replies") or ()) for row in thread)
    for key in ("customer_id", "username"):
        payload.pop(key, None)
    return payload


def build_staff_discussion(
    user: Mapping[str, Any] | None,
    shipments: Sequence[Any],
    *,
    db: Any = None,
) -> dict[str, Any] | None:
    """Thread for the node THIS operator clicked, or ``None`` when closed."""
    if st is None or not _staff_can_use(user):
        return None
    actor = staff_actor(user)
    if actor is None:
        return None
    focus = journey_focus.for_staff(
        journey_focus.current(st.session_state), actor["username"], shipments or (),
    )
    if not focus:
        return None
    return _discussion_payload(
        actor=actor,
        focus=focus,
        rows=shipments or (),
        session_key=STAFF_DOWNLOAD_KEY,
        can_see_internal=True,
        db=db,
    )


def build_customer_discussion(
    principal: Any,
    cards: Sequence[Any],
    *,
    db: Any = None,
) -> dict[str, Any] | None:
    """Thread for the node THIS customer opened on one of their OWN lots."""
    if st is None:
        return None
    actor = customer_actor(principal)
    if actor is None:
        return None
    focus = journey_focus.for_customer(
        journey_focus.current(st.session_state), actor["customer_id"], cards or (),
    )
    if not focus:
        return None
    # ``for_customer`` returns the validated lot + stage only; the tenant is the
    # server-proven principal, never the stored request.
    focus = {**focus, "customer_id": actor["customer_id"]}
    card_rows = [
        {"id": _text(getattr(card, "reference", ""), 120)} for card in (cards or ())
    ]
    return _discussion_payload(
        actor=actor,
        focus=focus,
        rows=card_rows,
        session_key=CUSTOMER_DOWNLOAD_KEY,
        can_see_internal=False,
        db=db,
        outcome_key=CUSTOMER_OUTCOME_KEY,
    )


# --------------------------------------------------------------------------- #
# write side — bounded files, duplicate-submit guard
# --------------------------------------------------------------------------- #

def _prepare_files(raw: Any) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
    """Validate names/MIME/size BEFORE any byte lands in the file store."""
    from core.inbox_attachments import decode_upload_payload, validate_upload
    from core.shipment_attachments import CODE_INVALID, CODE_SIZE, MAX_UPLOAD_BYTES, UploadRefused

    if raw in (None, ""):
        return [], None
    if not isinstance(raw, list):
        return [], {"code": CODE_INVALID, "error": "Danh sách tệp không hợp lệ."}
    if len(raw) > notes.MAX_FILES_PER_SUBMIT:
        return [], {
            "code": "TOO_MANY_FILES",
            "error": f"Tối đa {notes.MAX_FILES_PER_SUBMIT} tệp mỗi lần gửi.",
        }
    prepared: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            return [], {"code": CODE_INVALID, "error": "Tệp gửi lên không hợp lệ."}
        declared: int | None = None
        if item.get("size") is not None:
            try:
                declared = int(item.get("size"))
            except (TypeError, ValueError):
                return [], {"code": CODE_INVALID, "error": "Kích thước tệp không hợp lệ."}
            if declared < 0 or declared > MAX_UPLOAD_BYTES:
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
                _text(item.get("name") or item.get("fileName"), 255),
                _text(item.get("mime"), 255),
                declared if declared is not None else size,
                data,
            )
        except UploadRefused as refusal:
            return [], {"code": refusal.code, "error": refusal.message}
        if len(prepared) and any(row["name"] == safe_name and row["data"] == data for row in prepared):
            continue
        prepared.append({"name": safe_name, "mime": canonical_mime, "data": data, "size": size})
    return prepared, None


def _request_seen(key: str, request_id: str) -> bool:
    if st is None or not request_id:
        return False
    seen = st.session_state.get(key)
    if not isinstance(seen, list):
        return False
    return request_id in seen


def _remember_request(key: str, request_id: str) -> None:
    if st is None or not request_id:
        return
    seen = st.session_state.get(key)
    rows = list(seen) if isinstance(seen, list) else []
    rows.append(request_id)
    st.session_state[key] = rows[-MAX_REQUEST_MEMORY:]


def _store_download(
    session_key: str,
    *,
    shipment_id: str,
    stage_id: str,
    note_id: str,
    attachment_id: str,
    outcome: Mapping[str, Any],
) -> int:
    previous = st.session_state.get(session_key) if st is not None else None
    seq = int((previous or {}).get("seq") or 0) + 1 if isinstance(previous, Mapping) else 1
    data = bytes(outcome.get("data") or b"")
    st.session_state[session_key] = {
        "shipmentId": shipment_id,
        "stageId": stage_id,
        "noteId": note_id,
        "attachmentId": attachment_id,
        "fileName": _text(outcome.get("name"), 255),
        "mime": _text(outcome.get("mime"), 255),
        "bytes": len(data),
        "seq": seq,
        "base64": base64.b64encode(data).decode("ascii"),
    }
    return seq


def _handle_create(
    payload: Mapping[str, Any],
    *,
    actor: Mapping[str, str],
    focus: Mapping[str, str],
    requests_key: str,
    allow_internal: bool,
    db: Any = None,
) -> dict[str, Any]:
    """Append ONE comment/reply to the verified lot + stage."""
    request_id = _text(payload.get("requestId"), 80)
    event = "journey_note_create"

    def res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result(event, _text(focus.get("shipment_id"), 120), ok, error,
                       requestId=request_id, **extra)

    if not request_id:
        return res(False, "Thiếu mã yêu cầu.", gate="INVALID_REQUEST")
    if _request_seen(requests_key, request_id):
        # A replayed trigger (or a double click) is acknowledged, never written
        # twice. The caller learns it was a duplicate and refreshes from truth.
        return res(True, gate="DUPLICATE", duplicate=True,
                   persisted={"duplicate": True})
    prepared, file_error = _prepare_files(payload.get("files") or payload.get("attachments"))
    if file_error is not None:
        return res(False, file_error["error"], gate=file_error["code"])
    body = _text(payload.get("body"), notes.MAX_BODY)
    visibility = _text(payload.get("visibility"), 20).upper() or (
        notes.VISIBILITY_CUSTOMER if actor.get("kind") == "customer" else notes.VISIBILITY_INTERNAL
    )
    if not allow_internal and visibility == notes.VISIBILITY_INTERNAL:
        # A customer account can never publish internal content, even by
        # crafting the payload by hand.
        visibility = notes.VISIBILITY_CUSTOMER
    if not body and not prepared:
        return res(False, "Nhập nội dung hoặc đính kèm chứng từ.", gate="EMPTY")
    reply_to_id = _text(payload.get("replyToId"), 80)
    try:
        outcome = notes.create_stage_note(
            customer_id=_text(focus.get("customer_id"), 120),
            shipment_id=_text(focus.get("shipment_id"), 120),
            stage_id=_text(focus.get("stage_id"), 40),
            body=body,
            visibility=visibility,
            actor=actor,
            files=prepared,
            reply_to_id=reply_to_id,
            db=db,
        )
    except notes.JourneyNoteDenied as denied:
        return res(False, _text(denied, 300) or "Không gửi được trao đổi.",
                   gate="DENIED")
    except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
        return res(False, f"{type(exc).__name__}: {exc}", gate="FAILED")
    _remember_request(requests_key, request_id)
    saved = outcome.get("note") if isinstance(outcome, Mapping) else None
    saved = saved if isinstance(saved, Mapping) else {}
    return res(
        True,
        gate="SAVED",
        duplicate=False,
        persisted={
            "noteId": _text(saved.get("id"), 80),
            "replyToId": _text(saved.get("reply_to_id"), 80),
            "visibility": _text(outcome.get("visibility"), 20),
            "attachments": len(saved.get("attachments") or ()),
        },
        readback={"thread": "refresh"},
    )


def _handle_download(
    payload: Mapping[str, Any],
    *,
    actor: Mapping[str, str],
    focus: Mapping[str, str],
    session_key: str,
    db: Any = None,
) -> dict[str, Any]:
    """Read ONE attachment after proving the note, tenant and visibility."""
    request_id = _text(payload.get("requestId"), 80)
    note_id = _text(payload.get("noteId"), 80)
    attachment_id = _text(payload.get("attachmentId"), 120)
    event = "journey_note_download"
    shipment_id = _text(focus.get("shipment_id"), 120)
    stage_id = _text(focus.get("stage_id"), 40)

    if not note_id or not attachment_id:
        return _result(event, shipment_id, False, "Thiếu mã trao đổi hoặc mã tệp.",
                       requestId=request_id, gate="INVALID_REQUEST")
    # The note MUST belong to the lot + stage the server resolved for this
    # panel. Without this binding a crafted trigger could name a note of
    # another lot/stage (or a lot outside the staff projection) and receive
    # its bytes; the check runs before storage is touched.
    outcome = notes.read_note_attachment(
        note_id=note_id, attachment_id=attachment_id, actor=actor, db=db,
        expected_scope={
            "customer_id": _text(focus.get("customer_id"), 120),
            "shipment_id": shipment_id,
            "stage_id": stage_id,
        },
    )
    if not outcome.get("ok"):
        return _result(event, shipment_id, False,
                       _text(outcome.get("error"), 300) or "Không đọc được chứng từ.",
                       requestId=request_id, gate="NOT_FOUND")
    seq = _store_download(
        session_key,
        shipment_id=shipment_id,
        stage_id=stage_id,
        note_id=note_id,
        attachment_id=attachment_id,
        outcome=outcome,
    )
    return _result(
        event, shipment_id, True,
        gate="DOWNLOADED", requestId=request_id,
        persisted={
            "noteId": note_id,
            "attachmentId": attachment_id,
            "fileName": _text(outcome.get("name"), 255),
            "seq": seq,
        },
    )


def _consume(
    session: MutableMapping[str, Any] | dict,
    result: Any,
    *,
    actor: Mapping[str, str] | None,
    resolve_focus: Any,
    requests_key: str,
    download_key: str,
    allow_internal: bool,
    db: Any = None,
) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    if actor is None:
        return outcomes
    for event_name in sorted(STAFF_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, Mapping):
            continue
        seq = payload.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, Mapping):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        focus = resolve_focus(data)
        if not focus:
            outcomes.append(_result(
                event_name, _text(data.get("shipmentId") or data.get("shipment_id"), 120),
                False, "Không xác minh được lô và công đoạn của trao đổi.",
                requestId=_text(data.get("requestId"), 80), gate="INVALID_SCOPE",
            ))
            continue
        try:
            if event_name == "journey_note_create":
                outcomes.append(_handle_create(
                    data, actor=actor, focus=focus, requests_key=requests_key,
                    allow_internal=allow_internal, db=db,
                ))
            else:
                outcomes.append(_handle_download(
                    data, actor=actor, focus=focus, session_key=download_key, db=db,
                ))
        except Exception as exc:  # noqa: BLE001
            outcomes.append(_result(
                event_name, _text(focus.get("shipment_id"), 120), False,
                f"{type(exc).__name__}: {exc}",
                requestId=_text(data.get("requestId"), 80), gate="FAILED",
            ))
    return outcomes


def _staff_focus_resolver(user: Mapping[str, Any] | None, shipments: Sequence[Any]):
    actor = staff_actor(user)
    if actor is None or not _staff_can_use(user):
        return lambda data: None

    def resolve(data: Mapping[str, Any]) -> dict[str, str] | None:
        focus = journey_focus.for_staff(
            {
                "shipment_id": data.get("shipmentId") or data.get("shipment_id"),
                "stage_id": (data.get("stageId") or data.get("stage_id")
                             or data.get("nodeId") or data.get("node_id")),
                "node_id": data.get("nodeId") or data.get("node_id"),
                "username": actor["username"],
            },
            actor["username"],
            shipments or (),
        )
        if not focus:
            return None
        # Remember the verified node so the next payload opens THAT thread.
        # The browser's replay guard belongs to the focus event itself; this
        # write path must not advance it or a later intentional click would be
        # rejected as a replay.
        _remember_focus(focus, username=actor["username"])
        return focus

    return resolve


def _customer_focus_resolver(principal: Any, cards: Sequence[Any]):
    actor = customer_actor(principal)
    if actor is None:
        return lambda data: None

    def resolve(data: Mapping[str, Any]) -> dict[str, str] | None:
        focus = journey_focus.for_customer(
            {
                "shipment_id": data.get("shipmentId") or data.get("shipment_id"),
                "stage_id": data.get("stageId") or data.get("stage_id"),
                "customer_id": actor["customer_id"],
            },
            actor["customer_id"],
            cards or (),
        )
        if not focus:
            return None
        focus["customer_id"] = actor["customer_id"]
        _remember_focus(focus, customer_id=actor["customer_id"])
        return focus

    return resolve


def consume_staff_triggers(
    session: MutableMapping[str, Any] | dict,
    result: Any,
    *,
    user: Mapping[str, Any] | None,
    shipments: Sequence[Any],
    db: Any = None,
) -> list[dict[str, Any]]:
    """Bounded internal write/download dispatcher (same ``seq`` contract)."""
    return _consume(
        session, result,
        actor=staff_actor(user) if _staff_can_use(user) else None,
        resolve_focus=_staff_focus_resolver(user, shipments),
        requests_key=STAFF_REQUESTS_KEY,
        download_key=STAFF_DOWNLOAD_KEY,
        allow_internal=True,
        db=db,
    )


def consume_customer_triggers(
    session: MutableMapping[str, Any] | dict,
    result: Any,
    *,
    principal: Any,
    cards: Sequence[Any],
    db: Any = None,
) -> list[dict[str, Any]]:
    """Bounded customer write/download dispatcher. INTERNAL is impossible."""
    outcomes = _consume(
        session, result,
        actor=customer_actor(principal),
        resolve_focus=_customer_focus_resolver(principal, cards),
        requests_key=CUSTOMER_REQUESTS_KEY,
        download_key=CUSTOMER_DOWNLOAD_KEY,
        allow_internal=False,
        db=db,
    )
    if st is not None:
        focus = journey_focus.current(st.session_state) or {}
        for event_name, key in (
            ("journey_note_create", CUSTOMER_OUTCOME_KEY),
            ("journey_note_download", CUSTOMER_DOWNLOAD_OUTCOME_KEY),
        ):
            rows = [row for row in outcomes if row.get("event") == event_name]
            if not rows:
                continue
            last = rows[-1]
            st.session_state[key] = {
                "shipmentId": _text(focus.get("shipment_id"), 120),
                "stageId": _text(focus.get("stage_id"), 40),
                "requestId": _text(last.get("requestId"), 80),
                "ok": bool(last.get("ok")),
                "error": _text(last.get("error"), 300),
                "duplicate": bool(last.get("duplicate")),
            }
    return outcomes
