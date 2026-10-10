"""LOGI-193 — persistence for Admin-uploaded Office templates.

This module adds **no new storage plane**:

  * registry metadata (label, kind, status, immutable version rows, confirmed
    mappings) lives in the app's EXISTING ``app_settings`` collection through
    the EXISTING ``core.database.load_app_setting`` / ``save_app_setting``;
  * template BYTES live in the app's EXISTING GridFS byte store
    (``core.gridfs_client.GridFSAttachmentStore``), only under its own bucket
    namespace so a template can never be mistaken for a shipment attachment
    row.  Same provider, same connection, same failure surface.

Version rows are immutable once published: republishing a changed mapping or
a new file appends ``version + 1`` and moves the active pointer; nothing is
rewritten in place and nothing is deleted (retire only flips ``status``).
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from core.docgen.uploaded_template import (
    KIND_DOCX,
    KIND_XLSX,
    MAX_LABEL_TEXT,
    MAX_TEMPLATE_BYTES,
    UploadedTemplateError,
    UPLOADED_ADAPTER,
)

SETTING_ID = "docgen_uploaded_templates"
#: Same GridFS provider/connection as shipment attachments, separate bucket.
TEMPLATE_GRIDFS_BUCKET = "docgen_template_files"

STATUS_DRAFT = "DRAFT"
STATUS_ACTIVE = "ACTIVE"
STATUS_RETIRED = "RETIRED"

MAX_TEMPLATES = 50
MAX_TEMPLATE_ID = 40
_ID_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class TemplateStoreError(RuntimeError):
    """A registry/storage failure that is safe to surface at the boundary."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def new_template_id(label: str) -> str:
    """Stable, filesystem-safe, human-recognizable template id."""
    slug = _ID_SLUG_PATTERN.sub("-", _text(label).lower()).strip("-")[:24] or "bieu-mau"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"UT-{slug}-{stamp}"[:MAX_TEMPLATE_ID]


def _store(db: Any = None) -> Any:
    from core.gridfs_client import GridFSAttachmentStore

    resolved = db
    if resolved is None:
        from core.database import get_db

        resolved = get_db()
    if resolved is None:
        raise TemplateStoreError("MongoDB chưa sẵn sàng để lưu biểu mẫu tải lên.")
    return GridFSAttachmentStore(resolved, bucket_name=TEMPLATE_GRIDFS_BUCKET)


def load_registry(db: Any = None) -> list[dict[str, Any]]:
    """The template registry (never bytes; GridFS ids stay backend-only).

    ``core.database.save_app_setting`` stores the payload under ``value``, so
    the registry lives at ``app_settings[id=...].value.templates``.
    """
    from core.database import load_app_setting

    stored = load_app_setting(SETTING_ID, db=db)
    if not isinstance(stored, Mapping):
        return []
    payload = stored.get("value")
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("templates")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _save_registry(rows: list[Mapping[str, Any]]) -> None:
    from core.database import get_last_db_error, save_app_setting

    payload = {"templates": [dict(row) for row in rows], "updated_at": _now()}
    if not save_app_setting(SETTING_ID, payload):
        raise TemplateStoreError(get_last_db_error() or "Không lưu được danh mục biểu mẫu.")


def get_template(template_id: str, db: Any = None) -> dict[str, Any] | None:
    target = _text(template_id)
    return next((row for row in load_registry(db=db) if _text(row.get("id")) == target), None)


def active_templates(db: Any = None) -> list[dict[str, Any]]:
    """Published templates the shipment picker may offer (stable order)."""
    return sorted(
        (
            row
            for row in load_registry(db=db)
            if _text(row.get("status")).upper() == STATUS_ACTIVE and row.get("activeVersion")
        ),
        key=lambda row: (_text(row.get("label")).lower(), _text(row.get("id"))),
    )


def active_version(template: Mapping[str, Any]) -> dict[str, Any] | None:
    """The immutable version row the active pointer names."""
    pointer = template.get("activeVersion")
    if not isinstance(pointer, int) or pointer < 1:
        return None
    versions = template.get("versions") if isinstance(template.get("versions"), list) else []
    return next(
        (
            dict(row)
            for row in versions
            if isinstance(row, Mapping) and int(row.get("version") or 0) == pointer
        ),
        None,
    )


def catalog_templates(db: Any = None) -> tuple[Any, ...]:
    """Active templates as rows of the EXISTING shipment document catalog.

    Returns ``ShipmentDocumentTemplate`` instances (not a parallel shape), so
    ``core.shipment_document_catalog.with_uploaded_templates`` can append them
    to the code-owned V1 entries and every existing projection/validation path
    keeps working unchanged.
    """
    from core.shipment_document_catalog import ShipmentDocumentTemplate

    entries: list[Any] = []
    for template in active_templates(db=db):
        version = active_version(template)
        if not version:
            continue
        kind = _text(template.get("kind")).upper()
        label = _text(template.get("label")) or _text(template.get("id"))
        entries.append(
            ShipmentDocumentTemplate(
                id=_text(template.get("id")),
                label=f"{label} ({'DOCX' if kind == KIND_DOCX else 'XLSX'} · v{int(version.get('version') or 1)})",
                category=_text(template.get("category")) or "Biểu mẫu tải lên",
                adapter=UPLOADED_ADAPTER,
                document_type=_text(template.get("id")),
                active=True,
            )
        )
    return tuple(entries)


def load_bytes(template: Mapping[str, Any], db: Any = None) -> bytes:
    """Read the pinned bytes of the template's active version."""
    version = active_version(template)
    if not version:
        raise TemplateStoreError("Biểu mẫu chưa có phiên bản đã phát hành.")
    file_id = _text(version.get("fileId"))
    if not file_id:
        raise TemplateStoreError("Biểu mẫu thiếu tham chiếu tệp trong kho.")
    try:
        return bytes(_store(db).download_file(file_id))
    except TemplateStoreError:
        raise
    except Exception as exc:  # noqa: BLE001 - provider failure boundary
        raise TemplateStoreError(f"Không đọc được tệp biểu mẫu ({type(exc).__name__}).") from exc


def create_draft(
    *,
    label: str,
    category: str,
    kind: str,
    mime: str,
    data: bytes,
    sha256: str,
    positions: list[Mapping[str, Any]],
    uploaded_by: str,
    db: Any = None,
) -> dict[str, Any]:
    """Store bytes + detected positions as ONE new draft template."""
    from core.docgen.uploaded_template import MAX_POSITIONS

    name = _text(label)[:MAX_LABEL_TEXT]
    if not name:
        raise UploadedTemplateError("Thiếu tên biểu mẫu.")
    if kind not in (KIND_DOCX, KIND_XLSX):
        raise UploadedTemplateError(f"Loại biểu mẫu không hỗ trợ: {kind!r}")
    if len(data) > MAX_TEMPLATE_BYTES:
        raise UploadedTemplateError("Tệp biểu mẫu vượt quá giới hạn dung lượng.")

    rows = load_registry(db=db)
    if len(rows) >= MAX_TEMPLATES:
        raise UploadedTemplateError(f"Đã đạt giới hạn {MAX_TEMPLATES} biểu mẫu tải lên.")

    template_id = new_template_id(name)
    file_identity = _store(db).upload_file(
        name=f"{template_id}.{'docx' if kind == KIND_DOCX else 'xlsx'}",
        mime=_text(mime),
        data=data,
        metadata={
            "purpose": "docgen_uploaded_template",
            "templateId": template_id,
            "sha256": _text(sha256),
            "uploadedBy": _text(uploaded_by),
        },
    )

    row = {
        "id": template_id,
        "label": name,
        "category": _text(category)[:MAX_LABEL_TEXT] or "Biểu mẫu tải lên",
        "kind": kind,
        "status": STATUS_DRAFT,
        "activeVersion": None,
        "createdAt": _now(),
        "updatedAt": _now(),
        "uploadedBy": _text(uploaded_by),
        # Detected positions are a bounded REVIEW AID, never a final mapping.
        "detected": [dict(item) for item in (positions or [])[:MAX_POSITIONS]],
        "mapping": [],
        "draftFileId": _text(file_identity.get("storage_file_id")),
        "draftSha256": _text(sha256),
        "draftSizeBytes": int(len(data)),
        "versions": [],
    }
    rows.append(row)
    _save_registry(rows)
    return row


def save_mapping(
    *,
    template_id: str,
    mapping: list[Mapping[str, Any]],
    actor: str,
    db: Any = None,
) -> dict[str, Any]:
    """Persist ONE confirmed mapping on a DRAFT (never on a published version)."""
    rows = load_registry(db=db)
    row = next((item for item in rows if _text(item.get("id")) == _text(template_id)), None)
    if row is None:
        raise UploadedTemplateError("Không tìm thấy biểu mẫu.")
    if _text(row.get("status")).upper() != STATUS_DRAFT:
        raise UploadedTemplateError(
            "Chỉ bản nháp mới sửa được mapping; hãy tải tệp mới để tạo bản nháp khác."
        )
    row["mapping"] = [dict(item) for item in mapping]
    row["updatedAt"] = _now()
    row["mappingBy"] = _text(actor)
    _save_registry(rows)
    return row


def publish(
    *,
    template_id: str,
    actor: str,
    db: Any = None,
) -> dict[str, Any]:
    """Freeze the current draft (bytes + mapping) into an immutable version."""
    rows = load_registry(db=db)
    row = next((item for item in rows if _text(item.get("id")) == _text(template_id)), None)
    if row is None:
        raise UploadedTemplateError("Không tìm thấy biểu mẫu.")
    if _text(row.get("status")).upper() == STATUS_RETIRED:
        raise UploadedTemplateError("Biểu mẫu đã ngừng dùng; không phát hành lại.")
    mapping = row.get("mapping") if isinstance(row.get("mapping"), list) else []
    if not mapping:
        raise UploadedTemplateError("Chưa có mapping nào được xác nhận — không phát hành.")
    file_id = _text(row.get("draftFileId"))
    sha256 = _text(row.get("draftSha256"))
    if not file_id or not sha256:
        raise UploadedTemplateError("Bản nháp thiếu tệp hoặc SHA-256 đã ghim.")

    versions = list(row.get("versions") or [])
    version_number = len(versions) + 1
    versions.append(
        {
            "version": version_number,
            "fileId": file_id,
            "sha256": sha256,
            "sizeBytes": int(row.get("draftSizeBytes") or 0),
            "mapping": copy.deepcopy(mapping),
            "publishedAt": _now(),
            "publishedBy": _text(actor),
        }
    )
    row["versions"] = versions
    row["activeVersion"] = version_number
    row["status"] = STATUS_ACTIVE
    row["updatedAt"] = _now()
    _save_registry(rows)
    return row


def set_active(*, template_id: str, active: bool, actor: str, db: Any = None) -> dict[str, Any]:
    """Activate/retire a template. Retire never deletes bytes or history."""
    rows = load_registry(db=db)
    row = next((item for item in rows if _text(item.get("id")) == _text(template_id)), None)
    if row is None:
        raise UploadedTemplateError("Không tìm thấy biểu mẫu.")
    if active and not row.get("activeVersion"):
        raise UploadedTemplateError("Biểu mẫu chưa có phiên bản đã phát hành để kích hoạt.")
    row["status"] = STATUS_ACTIVE if active else STATUS_RETIRED
    row["updatedAt"] = _now()
    row["statusBy"] = _text(actor)
    _save_registry(rows)
    return row


def project_template(row: Mapping[str, Any], *, include_detected: bool = False) -> dict[str, Any]:
    """Password-free, path-free projection for the UI (no GridFS id leaks)."""
    version = active_version(row)
    projection = {
        "id": _text(row.get("id")),
        "label": _text(row.get("label")),
        "category": _text(row.get("category")),
        "kind": _text(row.get("kind")),
        "status": _text(row.get("status")).upper(),
        "activeVersion": version.get("version") if version else None,
        "versionCount": len(row.get("versions") or []),
        "mappingCount": len(row.get("mapping") or []),
        "publishedMappingCount": len((version or {}).get("mapping") or []),
        "uploadedBy": _text(row.get("uploadedBy")),
        "updatedAt": _text(row.get("updatedAt")),
        "publishedBy": _text((version or {}).get("publishedBy")),
        "publishedAt": _text((version or {}).get("publishedAt")),
        "sizeBytes": int(row.get("draftSizeBytes") or 0),
        "sha256": _text(row.get("draftSha256")),
    }
    if include_detected:
        projection["detected"] = [dict(item) for item in (row.get("detected") or [])]
        projection["mapping"] = [dict(item) for item in (row.get("mapping") or [])]
    return projection


def project_registry(db: Any = None, *, include_detected: bool = False) -> list[dict[str, Any]]:
    return [project_template(row, include_detected=include_detected) for row in load_registry(db=db)]
