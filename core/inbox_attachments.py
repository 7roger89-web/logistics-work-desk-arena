"""Issue #212 — note-owned file bytes on the EXISTING GridFS/Drive adapters.

Inbox snippets may carry JPEG/PNG/PDF/Office files. Bytes live in the already
configured shipment attachment store (GridFS by default, Drive when selected).
Metadata lives on the existing ``quick_notes`` row. This module is not a new
storage product: it reuses validation, the 20 MB ceiling, image optimization,
and the GridFS/Drive clients from ``core.shipment_attachments``.

Never store binary/base64 on the note. Never return Drive/GridFS ids, raw
SHA-256, or public URLs to the browser. Unlink of a shipment/contract must not
move, copy, re-upload, or delete these bytes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from core.drive_client import (
    AUTH_MODE_SERVICE_ACCOUNT,
    AUTH_MODE_USER_OAUTH,
    DriveError,
    build_drive_client,
    load_drive_settings,
)
from core.gridfs_client import GridFSFileNotFound, GridFSStorageError
from core.shipment_attachments import (
    ALLOWED_ACCEPT,
    ALLOWED_EXTENSIONS,
    CODE_DRIVE_FAILED,
    CODE_DRIVE_UNCONFIGURED,
    CODE_GRIDFS_FAILED,
    CODE_GRIDFS_UNCONFIGURED,
    CODE_INVALID,
    CODE_NOT_FOUND,
    CODE_SIZE,
    CODE_STORAGE_UNSUPPORTED,
    COMPRESSION_OPTIMIZED,
    DRIVE_STORAGE_BACKENDS,
    MAX_UPLOAD_BYTES,
    STORAGE_BACKEND_DRIVE_OAUTH,
    STORAGE_BACKEND_DRIVE_SHARED,
    STORAGE_BACKEND_GRIDFS,
    SUPPORTED_STORAGE_BACKENDS,
    UploadRefused,
    build_gridfs_client,
    decode_upload_payload,
    extension_of,
    prepare_stored_bytes,
    resolve_storage_backend,
    sha256_hex,
    storage_is_configured,
    storage_label,
    utc_now_iso,
    validate_upload,
)

LOGGER = logging.getLogger("logistics_pro.inbox_attachments")

DRIVE_INBOX_FOLDER = "Inbox"

INBOX_MAX_FILES = 8
INBOX_ATTACHMENT_PREFIX = "iatt-"

CODE_TOO_MANY_FILES = "TOO_MANY_FILES"
CODE_EMPTY_CAPTURE = "EMPTY_CAPTURE"


def inbox_drive_folder_names(when: datetime | None = None) -> tuple[str, str, str]:
    """Unassigned inbox assets sit in Inbox/YYYY/MM. Link never moves them."""
    stamp = when or datetime.now(timezone.utc)
    return DRIVE_INBOX_FOLDER, stamp.strftime("%Y"), stamp.strftime("%m")


def _drive_auth_mode(backend: str) -> str:
    return AUTH_MODE_USER_OAUTH if backend == STORAGE_BACKEND_DRIVE_OAUTH else AUTH_MODE_SERVICE_ACCOUNT


def _resolve_gridfs(gridfs: Any = None) -> Any:
    return gridfs if gridfs is not None else build_gridfs_client()


def _resolve_drive(backend: str, drive: Any = None) -> Any:
    if drive is not None:
        return drive
    return build_drive_client(auth_mode=_drive_auth_mode(backend))


def _storage_error_label(backend: str) -> str:
    return "Google Drive" if backend in DRIVE_STORAGE_BACKENDS else "Kho chứng từ"


def _human(size: int) -> str:
    value = int(size or 0)
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    if value >= 1024:
        return f"{value / 1024:.0f} KB"
    return f"{value} B"


def project_inbox_attachment(
    record: Mapping[str, Any] | None,
    *,
    download: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Public attachment card. Storage ids, hashes and URLs stay server-side."""
    if not isinstance(record, Mapping):
        return None
    attachment_id = str(record.get("id") or "").strip()
    if not attachment_id:
        return None
    original_size = int(record.get("original_size") or 0)
    stored_size = int(record.get("stored_size") or 0)
    optimized = str(record.get("compression_mode") or "") == COMPRESSION_OPTIMIZED
    ready = bool(download) and str(download.get("attachmentId") or "") == attachment_id
    if optimized and stored_size and stored_size < original_size:
        size_label = f"{_human(original_size)} → {_human(stored_size)}"
    else:
        size_label = _human(original_size or stored_size)
    return {
        "id": attachment_id,
        "name": str(record.get("original_name") or record.get("stored_name") or ""),
        "mime": str(record.get("mime") or ""),
        "originalSize": original_size,
        "storedSize": stored_size,
        "sizeLabel": size_label,
        "uploadedAt": str(record.get("uploaded_at") or ""),
        "downloadAvailable": ready,
        "downloadBase64": str(download.get("base64") or "") if ready else "",
        "downloadSeq": int(download.get("seq") or 0) if ready else 0,
    }


def compensate_stored_bytes(*, client: Any, storage_file_id: str) -> bool:
    """Exactly one delete of the bytes just written. Absence is not retried."""
    identity = str(storage_file_id or "").strip()
    if client is None or not identity:
        return False
    try:
        return bool(client.delete_file(identity))
    except Exception:  # noqa: BLE001 - compensation is fail-closed
        return False


def store_inbox_bytes(
    *,
    snippet_id: str,
    file_name: str,
    mime: str,
    data: bytes,
    declared_size: Any = None,
    uploaded_by: str = "",
    drive: Any = None,
    gridfs: Any = None,
    storage_backend: str | None = None,
) -> dict[str, Any]:
    """Validate → hash ORIGINAL → store bytes. Caller persists metadata on the note.

    Does not write ``shipment_attachments`` and does not invent a shipment id.
    """
    owner = str(snippet_id or "").strip()
    if not owner:
        return {"ok": False, "code": CODE_INVALID, "error": "Thiếu mã mẩu tin."}
    backend = str(storage_backend or resolve_storage_backend()).strip().lower()
    if backend not in SUPPORTED_STORAGE_BACKENDS:
        return {
            "ok": False,
            "code": CODE_STORAGE_UNSUPPORTED,
            "error": "Kho chứng từ chưa được cấu hình đúng; không có tệp nào được lưu.",
        }
    try:
        safe_name, canonical_mime, _kind = validate_upload(file_name, mime, declared_size, data)
    except UploadRefused as refusal:
        return {"ok": False, "code": refusal.code, "error": refusal.message}

    digest = sha256_hex(data)
    prepared = prepare_stored_bytes(data, extension_of(safe_name), canonical_mime)
    client: Any = None
    try:
        if backend == STORAGE_BACKEND_GRIDFS:
            client = _resolve_gridfs(gridfs)
            if client is None:
                return {
                    "ok": False,
                    "code": CODE_GRIDFS_UNCONFIGURED,
                    "error": "Kho chứng từ chưa sẵn sàng trên máy chủ. Không có tệp nào được lưu.",
                }
            uploaded = client.upload_file(
                name=safe_name,
                mime=prepared.mime,
                data=prepared.data,
                metadata={"owner_kind": "inbox_snippet", "snippet_id": owner},
            )
        else:
            client = _resolve_drive(backend, drive)
            if client is None:
                settings = load_drive_settings(_drive_auth_mode(backend))
                return {
                    "ok": False,
                    "code": CODE_DRIVE_UNCONFIGURED,
                    "error": (
                        "Google Drive chưa được cấu hình trên máy chủ (thiếu "
                        + ", ".join(settings.missing)
                        + "). Không có tệp nào được tải lên."
                    ),
                }
            root_id = str(getattr(getattr(client, "settings", None), "root_folder_id", "") or "")
            inbox_name, year_name, month_name = inbox_drive_folder_names()
            inbox_folder = client.ensure_folder(inbox_name, root_id)
            year_folder = client.ensure_folder(year_name, inbox_folder)
            month_folder = client.ensure_folder(month_name, year_folder)
            uploaded_drive = client.upload_file(
                name=safe_name,
                mime=prepared.mime,
                data=prepared.data,
                parent_id=month_folder,
                description=f"inbox {owner}",
            )
            uploaded = {
                "storage_file_id": str(uploaded_drive.get("fileId") or uploaded_drive.get("storage_file_id") or ""),
                "stored_name": str(uploaded_drive.get("name") or safe_name),
                "stored_size": len(prepared.data),
            }
    except (DriveError, GridFSStorageError) as exc:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001 - provider faults never become success
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {
            "ok": False,
            "code": code,
            "error": f"{_storage_error_label(backend)} lỗi ({type(exc).__name__}).",
        }

    storage_file_id = str((uploaded or {}).get("storage_file_id") or "").strip()
    if not storage_file_id:
        return {
            "ok": False,
            "code": CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED,
            "error": f"{_storage_error_label(backend)} không trả về mã tệp; không ghi metadata.",
        }
    record = {
        "id": f"{INBOX_ATTACHMENT_PREFIX}{uuid4().hex}",
        "storage_backend": backend,
        "storage_file_id": storage_file_id,
        "original_name": safe_name,
        "stored_name": str(uploaded.get("stored_name") or safe_name),
        "mime": prepared.mime,
        "original_size": len(data),
        "stored_size": int(uploaded.get("stored_size") or len(prepared.data)),
        "sha256": digest,
        "uploaded_at": utc_now_iso(),
        "uploaded_by": str(uploaded_by or ""),
        "compression_mode": prepared.compression_mode,
        "compression_note": prepared.compression_note,
        "status": "AVAILABLE",
    }
    return {
        "ok": True,
        "code": "",
        "error": "",
        "record": record,
        "client": client,
        "backend": backend,
    }


def fetch_inbox_bytes(
    record: Mapping[str, Any],
    *,
    drive: Any = None,
    gridfs: Any = None,
) -> dict[str, Any]:
    """Read ONE note-owned file. Caller must already have proven association."""
    stored = dict(record or {})
    backend = str(stored.get("storage_backend") or resolve_storage_backend()).strip().lower()
    if backend not in SUPPORTED_STORAGE_BACKENDS:
        return {"ok": False, "code": CODE_STORAGE_UNSUPPORTED, "error": "Kho chứng từ chưa được cấu hình đúng."}
    file_id = str(stored.get("storage_file_id") or "").strip()
    if not file_id:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Metadata không có mã tệp trong kho chứng từ."}
    try:
        if backend == STORAGE_BACKEND_GRIDFS:
            client = _resolve_gridfs(gridfs)
            if client is None:
                return {
                    "ok": False,
                    "code": CODE_GRIDFS_UNCONFIGURED,
                    "error": "Kho chứng từ chưa sẵn sàng trên máy chủ — không đọc được tệp.",
                }
            data = client.download_file(file_id)
        else:
            client = _resolve_drive(backend, drive)
            if client is None:
                settings = load_drive_settings(_drive_auth_mode(backend))
                return {
                    "ok": False,
                    "code": CODE_DRIVE_UNCONFIGURED,
                    "error": (
                        "Google Drive chưa được cấu hình trên máy chủ (thiếu "
                        + ", ".join(settings.missing)
                        + ") — không đọc được tệp."
                    ),
                }
            data = client.download_file(file_id)
    except GridFSFileNotFound as exc:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": str(exc)}
    except (DriveError, GridFSStorageError) as exc:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {
            "ok": False,
            "code": code,
            "error": f"{_storage_error_label(backend)} lỗi ({type(exc).__name__}).",
        }
    if not data:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} trả về tệp rỗng."}
    return {"ok": True, "code": "", "error": "", "record": stored, "data": bytes(data)}


__all__ = [
    "ALLOWED_ACCEPT",
    "ALLOWED_EXTENSIONS",
    "CODE_EMPTY_CAPTURE",
    "CODE_INVALID",
    "CODE_NOT_FOUND",
    "CODE_SIZE",
    "CODE_TOO_MANY_FILES",
    "DRIVE_INBOX_FOLDER",
    "INBOX_MAX_FILES",
    "MAX_UPLOAD_BYTES",
    "UploadRefused",
    "compensate_stored_bytes",
    "decode_upload_payload",
    "fetch_inbox_bytes",
    "inbox_drive_folder_names",
    "project_inbox_attachment",
    "sha256_hex",
    "storage_is_configured",
    "storage_label",
    "store_inbox_bytes",
    "validate_upload",
]
