"""Trao đổi theo công đoạn lô hàng (Trường Thành ↔ một khách hàng).

Một luồng trao đổi duy nhất, gắn đúng **khách hàng + lô hàng + công đoạn**:

* lưu trong **collection ``quick_notes`` đang có** (``kind="journey_note"``),
  cùng chỗ với Quick Notes/mẩu tin hộp thư đến; không tạo kho lưu trữ mới;
* tệp đính kèm đi qua **đúng adapter kho chứng từ đang dùng**
  (:mod:`core.inbox_attachments` → GridFS hoặc Drive đã cấu hình). Không giả
  định Google Drive: backend được đọc tại runtime và báo lỗi rõ ràng nếu chưa
  cấu hình;
* hai lớp nội dung: ``INTERNAL`` (chỉ Trường Thành) và ``CUSTOMER`` (khách xem
  được). Khách hàng **không bao giờ** đọc được nội dung nội bộ và **không thể**
  tự nâng quyền nội dung của mình lên nội bộ.

Danh tính luôn do server quyết định: khách hàng chỉ được phép ghi vào lô của
chính mình, đã đối chiếu ``shipments.customer_id``. Không nhận ``customer_id``
từ trình duyệt ở phía cổng khách.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

LOGGER = logging.getLogger("logistics.journey_notes")

JOURNEY_NOTE_KIND = "journey_note"
NOTE_COLLECTION = "quick_notes"

VISIBILITY_INTERNAL = "INTERNAL"
VISIBILITY_CUSTOMER = "CUSTOMER"
VISIBILITIES = (VISIBILITY_INTERNAL, VISIBILITY_CUSTOMER)

#: Write gate reuses the SINGLE existing role matrix, same permission as the
#: existing Quick Notes/inbox snippet writer.
WRITE_PERMISSION = "shipment_edit"

MAX_BODY = 4000
MAX_NOTES_READ = 200
MAX_FILES_PER_SUBMIT = 4

STAGE_IDS: tuple[str, ...] = (
    "plan", "pickup", "consolidate", "transit", "customs", "delivery", "finance",
)
STAGE_LABELS: dict[str, str] = {
    "plan": "Kế hoạch",
    "pickup": "Lấy hàng",
    "consolidate": "Gom hàng",
    "transit": "Vận chuyển",
    "customs": "Thông quan",
    "delivery": "Giao hàng",
    "finance": "Thanh toán",
}

_PROJECTION = {
    "_id": 0, "id": 1, "kind": 1, "customer_id": 1, "shipment_id": 1,
    "stage_id": 1, "body": 1, "visibility": 1, "author_kind": 1,
    "author_name": 1, "author_role": 1, "created_at": 1, "attachments": 1,
}


class JourneyNoteDenied(PermissionError):
    """Fail-closed refusal for an unauthorised or unscoped note action."""


def _clean(value: Any, limit: int = 0) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    text = str(value).replace("\r", " ").strip()
    return text[:limit] if limit else text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_db(db: Any = None) -> Any:
    if db is not None:
        return db
    from core.database import get_db

    try:
        resolved = get_db()
    except Exception:  # noqa: BLE001 - config/identity errors fail closed
        LOGGER.warning("JOURNEY_NOTE_DB_UNAVAILABLE")
        raise JourneyNoteDenied("Cơ sở dữ liệu chưa sẵn sàng.") from None
    if resolved is None:
        LOGGER.warning("JOURNEY_NOTE_DB_UNAVAILABLE reason=None")
        raise JourneyNoteDenied("Cơ sở dữ liệu chưa sẵn sàng.")
    return resolved


def _user_may_write(role: Any) -> bool:
    """Role check against the ONE existing permission matrix."""
    from core.auth import _role_permissions

    normalized = str(role or "").strip().lower()
    if not normalized:
        return False
    try:
        permissions = set(_role_permissions(normalized))
    except Exception:  # noqa: BLE001 - unknown role never writes
        return False
    return "*" in permissions or WRITE_PERMISSION in permissions


def _actor(actor: Any) -> dict[str, str]:
    """Normalise the server-side actor. A customer can never act as staff."""
    if not isinstance(actor, Mapping):
        raise JourneyNoteDenied("Không xác định được người ghi.")
    kind = _clean(actor.get("kind"), 20).lower()
    if kind == "user":
        username = _clean(actor.get("username"), 100)
        role = _clean(actor.get("role"), 40).lower()
        if not username:
            raise JourneyNoteDenied("Không xác minh được tài khoản nội bộ.")
        if not _user_may_write(role):
            raise JourneyNoteDenied("Tài khoản này không được ghi trao đổi lô hàng.")
        return {"kind": "user", "username": username, "role": role}
    if kind == "customer":
        customer_id = _clean(actor.get("customer_id"), 120)
        if not customer_id:
            raise JourneyNoteDenied("Không xác minh được khách hàng.")
        return {
            "kind": "customer",
            "customer_id": customer_id,
            "username": _clean(actor.get("name"), 100) or "Khách hàng",
            "role": "customer",
        }
    raise JourneyNoteDenied("Không xác định được người ghi.")


def _customer_read_allowed(actor: Mapping[str, str], customer_id: str) -> bool:
    return actor.get("kind") != "customer" or actor.get("customer_id") == customer_id


def _scope(database: Any, customer_id: str, shipment_id: str) -> None:
    if not customer_id or not shipment_id:
        raise JourneyNoteDenied("Thiếu khách hàng hoặc lô hàng hợp lệ.")
    try:
        customer = database.customers.find_one(
            {"id": customer_id, "is_deleted": {"$ne": True}}, {"_id": 0, "id": 1},
        )
        shipment = database.shipments.find_one(
            {"id": shipment_id, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "customer_id": 1},
        )
    except Exception:  # noqa: BLE001
        LOGGER.warning("JOURNEY_NOTE_SCOPE_READ_FAILED")
        raise JourneyNoteDenied("Không kiểm tra được lô hàng.") from None
    if customer is None:
        raise JourneyNoteDenied("Không tìm thấy hồ sơ khách hàng hợp lệ.")
    if not isinstance(shipment, Mapping) or _clean(shipment.get("customer_id")) != customer_id:
        raise JourneyNoteDenied("Lô hàng không thuộc khách hàng đã chọn.")


def _public_note(row: Mapping[str, Any]) -> dict[str, Any]:
    from core.inbox_attachments import project_inbox_attachment

    attachments = [
        projected
        for projected in (
            project_inbox_attachment(item)
            for item in (row.get("attachments") or ())
            if isinstance(item, Mapping)
            and _clean(item.get("status"), 30).upper() == "AVAILABLE"
        )
        if projected
    ]
    return {
        "id": _clean(row.get("id"), 80),
        "stage_id": _clean(row.get("stage_id"), 40),
        "body": _clean(row.get("body"), MAX_BODY),
        "visibility": (
            VISIBILITY_CUSTOMER
            if _clean(row.get("visibility"), 20).upper() == VISIBILITY_CUSTOMER
            else VISIBILITY_INTERNAL
        ),
        "author_kind": _clean(row.get("author_kind"), 20) or "user",
        "author_name": _clean(row.get("author_name"), 100),
        "author_role": _clean(row.get("author_role"), 40),
        "created_at": _clean(row.get("created_at"), 40),
        "attachments": attachments,
    }


def list_stage_notes(
    *,
    customer_id: str,
    shipment_id: str,
    stage_id: str = "",
    actor: Any = None,
    db: Any = None,
    limit: int = MAX_NOTES_READ,
) -> list[dict[str, Any]]:
    """Read one lot's stage discussion. Customers never receive internal notes."""
    customer_id, shipment_id = _clean(customer_id, 120), _clean(shipment_id, 120)
    stage = _clean(stage_id, 40).lower()
    if stage and stage not in STAGE_IDS:
        return []
    if not customer_id or not shipment_id:
        return []
    database = _resolve_db(db)
    resolved_actor = _actor(actor)
    if not _customer_read_allowed(resolved_actor, customer_id):
        LOGGER.warning("JOURNEY_NOTE_READ_DENIED reason=foreign_customer")
        return []
    # A note's original customer_id is not permanent read permission: always
    # verify the shipment still belongs to this customer before any content read.
    try:
        _scope(database, customer_id, shipment_id)
    except JourneyNoteDenied:
        LOGGER.warning("JOURNEY_NOTE_READ_DENIED reason=shipment_scope_changed")
        return []
    query: dict[str, Any] = {
        "kind": JOURNEY_NOTE_KIND,
        "customer_id": customer_id,
        "shipment_id": shipment_id,
        "is_deleted": {"$ne": True},
    }
    if stage:
        query["stage_id"] = stage
    if resolved_actor.get("kind") == "customer":
        query["visibility"] = VISIBILITY_CUSTOMER
    try:
        # Show the latest bounded messages, not the oldest 200 forever.
        rows = list(
            database[NOTE_COLLECTION].find(query, _PROJECTION)
            .sort("created_at", -1)
            .limit(max(1, min(int(limit or MAX_NOTES_READ), MAX_NOTES_READ)))
        )
        rows.reverse()  # retain chronological conversation display
    except Exception:  # noqa: BLE001
        LOGGER.warning("JOURNEY_NOTE_READ_FAILED")
        raise JourneyNoteDenied("Không đọc được trao đổi của lô hàng.") from None
    notes = []
    for row in rows:
        if not isinstance(row, Mapping) or not _clean(row.get("id")):
            continue
        if _clean(row.get("customer_id")) != customer_id or _clean(row.get("shipment_id")) != shipment_id:
            continue
        notes.append(_public_note(row))
    return notes


def create_stage_note(
    *,
    customer_id: str,
    shipment_id: str,
    stage_id: str,
    body: str,
    visibility: str = VISIBILITY_INTERNAL,
    actor: Any = None,
    files: Sequence[Mapping[str, Any]] = (),
    db: Any = None,
    gridfs: Any = None,
    drive: Any = None,
    storage_backend: str | None = None,
) -> dict[str, Any]:
    """Append ONE note (with optional files) to one lot's stage thread.

    Bytes are stored first; if the note cannot be proven written they are
    compensated (one bounded delete). Nothing is reported as saved without a
    fresh readback of the stored row.
    """
    resolved_actor = _actor(actor)
    customer_id, shipment_id = _clean(customer_id, 120), _clean(shipment_id, 120)
    stage = _clean(stage_id, 40).lower()
    if stage not in STAGE_IDS:
        raise JourneyNoteDenied("Công đoạn không hợp lệ.")
    text = _clean(body, MAX_BODY).strip()
    incoming = [item for item in (files or ()) if isinstance(item, Mapping)]
    if len(incoming) > MAX_FILES_PER_SUBMIT:
        raise JourneyNoteDenied(f"Tối đa {MAX_FILES_PER_SUBMIT} tệp mỗi lần gửi.")
    if not text and not incoming:
        raise JourneyNoteDenied("Nhập nội dung hoặc đính kèm chứng từ.")
    requested = _clean(visibility, 20).upper() or VISIBILITY_INTERNAL
    if requested not in VISIBILITIES:
        raise JourneyNoteDenied("Phạm vi nội dung không hợp lệ.")
    # A customer account can only ever publish customer-visible content.
    final_visibility = (
        VISIBILITY_CUSTOMER if resolved_actor["kind"] == "customer" else requested
    )
    database = _resolve_db(db)
    _scope(database, customer_id, shipment_id)
    if not _customer_read_allowed(resolved_actor, customer_id):
        raise JourneyNoteDenied("Khách hàng không thể ghi vào lô của người khác.")

    note_id = f"jn-{uuid4().hex}"
    stored: list[dict[str, Any]] = []
    attachments: list[dict[str, Any]] = []
    backend_label = ""
    if incoming:
        from core.inbox_attachments import compensate_stored_bytes, store_inbox_bytes
        from core.shipment_attachments import storage_label

        for item in incoming:
            outcome = store_inbox_bytes(
                snippet_id=note_id,
                file_name=_clean(item.get("name"), 255),
                mime=_clean(item.get("mime"), 255),
                data=item.get("data") or b"",
                declared_size=item.get("size"),
                uploaded_by=resolved_actor["username"],
                drive=drive,
                gridfs=gridfs,
                storage_backend=storage_backend,
            )
            record = outcome.get("record") if isinstance(outcome, Mapping) else None
            if not outcome.get("ok") or not isinstance(record, Mapping):
                for orphan in stored:
                    compensate_stored_bytes(
                        client=orphan.get("client"),
                        storage_file_id=str((orphan.get("record") or {}).get("storage_file_id") or ""),
                    )
                raise JourneyNoteDenied(
                    _clean(outcome.get("error"), 300) or "Không lưu được chứng từ đính kèm."
                )
            stored.append(outcome)
            attachments.append(dict(record))
            backend_label = storage_label(outcome.get("backend"))

    row = {
        "id": note_id,
        "kind": JOURNEY_NOTE_KIND,
        "customer_id": customer_id,
        "shipment_id": shipment_id,
        "stage_id": stage,
        "body": text,
        "visibility": final_visibility,
        "author_kind": resolved_actor["kind"],
        "author_name": resolved_actor["username"],
        "author_role": resolved_actor["role"],
        "created_at": _now(),
        "updated_at": _now(),
        "updated_by": resolved_actor["username"],
        "attachments": attachments,
        "is_deleted": False,
    }
    try:
        database[NOTE_COLLECTION].insert_one(dict(row))
        saved = database[NOTE_COLLECTION].find_one(
            {"id": note_id, "kind": JOURNEY_NOTE_KIND}, _PROJECTION,
        )
    except Exception:  # noqa: BLE001
        LOGGER.warning("JOURNEY_NOTE_WRITE_FAILED type=unknown")
        from core.inbox_attachments import compensate_stored_bytes

        for orphan in stored:
            compensate_stored_bytes(
                client=orphan.get("client"),
                storage_file_id=str((orphan.get("record") or {}).get("storage_file_id") or ""),
            )
        raise JourneyNoteDenied("Không lưu được trao đổi. Vui lòng thử lại.") from None
    if not isinstance(saved, Mapping):
        from core.inbox_attachments import compensate_stored_bytes

        for orphan in stored:
            compensate_stored_bytes(
                client=orphan.get("client"),
                storage_file_id=str((orphan.get("record") or {}).get("storage_file_id") or ""),
            )
        raise JourneyNoteDenied("Không xác nhận được trao đổi đã lưu. Vui lòng thử lại.")
    LOGGER.info(
        "JOURNEY_NOTE_SAVED shipment_id=%s stage=%s visibility=%s attachments=%s",
        shipment_id, stage, final_visibility, len(attachments),
    )
    return {
        "ok": True,
        "note": _public_note(saved),
        "storage_label": backend_label,
        "visibility": final_visibility,
    }


def read_note_attachment(
    *,
    note_id: str,
    attachment_id: str,
    actor: Any = None,
    db: Any = None,
    gridfs: Any = None,
    drive: Any = None,
) -> dict[str, Any]:
    """Read ONE attached file after re-proving the note and the exact file id.

    A customer may only read files of customer-visible notes on their own lot.
    """
    resolved_actor = _actor(actor)
    identifier, wanted = _clean(note_id, 80), _clean(attachment_id, 120)
    if not identifier or not wanted:
        return {"ok": False, "error": "Thiếu mã trao đổi hoặc mã tệp."}
    database = _resolve_db(db)
    try:
        row = database[NOTE_COLLECTION].find_one(
            {"id": identifier, "kind": JOURNEY_NOTE_KIND, "is_deleted": {"$ne": True}},
            {"_id": 0},
        )
    except Exception:  # noqa: BLE001
        LOGGER.warning("JOURNEY_NOTE_ATTACHMENT_READ_FAILED")
        return {"ok": False, "error": "Không đọc được chứng từ."}
    if not isinstance(row, Mapping):
        return {"ok": False, "error": "Không tìm thấy chứng từ."}
    if not _customer_read_allowed(resolved_actor, _clean(row.get("customer_id"), 120)):
        LOGGER.warning("JOURNEY_NOTE_ATTACHMENT_DENIED reason=foreign_customer")
        return {"ok": False, "error": "Không tìm thấy chứng từ."}
    if (resolved_actor.get("kind") == "customer"
            and _clean(row.get("visibility"), 20).upper() != VISIBILITY_CUSTOMER):
        LOGGER.warning("JOURNEY_NOTE_ATTACHMENT_DENIED reason=internal_content")
        return {"ok": False, "error": "Không tìm thấy chứng từ."}
    # Never serve previously shared bytes after reassignment/deletion of the
    # shipment.  The note's old tenant field alone is not sufficient.
    try:
        _scope(
            database,
            _clean(row.get("customer_id"), 120),
            _clean(row.get("shipment_id"), 120),
        )
    except JourneyNoteDenied:
        LOGGER.warning("JOURNEY_NOTE_ATTACHMENT_DENIED reason=shipment_scope_changed")
        return {"ok": False, "error": "Không tìm thấy chứng từ."}
    record = next(
        (
            item
            for item in (row.get("attachments") or ())
            if isinstance(item, Mapping) and _clean(item.get("id"), 120) == wanted
        ),
        None,
    )
    if (record is None
            or _clean(record.get("status"), 30).upper() != "AVAILABLE"):
        return {"ok": False, "error": "Không tìm thấy chứng từ."}
    from core.inbox_attachments import fetch_inbox_bytes

    outcome = fetch_inbox_bytes(record, drive=drive, gridfs=gridfs)
    if not outcome.get("ok"):
        return {"ok": False, "error": _clean(outcome.get("error"), 300) or "Không đọc được chứng từ."}
    return {
        "ok": True,
        "name": _clean(record.get("original_name") or record.get("stored_name"), 255),
        "mime": _clean(record.get("mime"), 255),
        "data": outcome.get("data") or b"",
    }
