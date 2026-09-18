"""LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the bounded shipment-attachment service.

Ported (source only) from donor PR #49 onto current main; contract unchanged:
Drive owns bytes, Mongo owns bounded metadata only.

ONE vertical slice: shipment attachment upload → safe preprocessing → Google
Drive (bytes) → Mongo (bounded metadata only) → shipment document UI readback.

Hard rules enforced here (not in the UI):

* Google Drive owns the BYTES. No raw PDF/image/DOCX/XLSX bytes and no base64
  body ever enters Mongo — :func:`core.database.save_shipment_attachment`
  refuses such a document outright.
* Authentication is the deployment's own service account; nothing here can
  return a credential, a bearer token or a signed URL to the browser.
* Size and type are checked BEFORE any Drive call, and again on the decoded
  bytes (the browser's claim is usability only, never the boundary).
* "Compression" means a REAL size reduction: JPEG/PNG are re-encoded with
  Pillow and the optimized bytes are kept only when they are materially
  smaller; PDF/DOCX/XLSX are kept byte-identical in this slice.
* Duplicate guard: within the SAME shipment the SHA-256 of the ORIGINAL upload
  identifies the attachment. A duplicate returns the existing attachment and
  performs NO second Drive upload. Cross-shipment dedupe is out of scope.
* External side-effect order: validate → hash → (dedupe) → upload Drive →
  persist metadata. If metadata persistence fails, the just-created Drive file
  is deleted ONCE using the exact file id the upload returned; when that cannot
  be proven the result says so explicitly (``orphan_risk``) and logs only
  non-sensitive repair evidence.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from core.drive_client import (
    DriveError,
    build_drive_client,
    is_unsafe_drive_name,
    load_drive_settings,
    sanitize_drive_name,
)

LOGGER = logging.getLogger("logistics_pro.attachments")

#: Conservative practical ceiling. Streamlit's own component value transport
#: handles it comfortably and a 20 MB logistics scan/photo is already large.
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
#: Pre-decode bound: base64 of MAX_UPLOAD_BYTES plus its 3-byte padding.
MAX_BASE64_CHARS = ((MAX_UPLOAD_BYTES + 2) // 3) * 4 + 8

#: Document-photo maximum edge; larger images are scaled down, never up.
IMAGE_MAX_DIMENSION = 2200
#: Document-readable JPEG quality (legible text, real byte saving).
IMAGE_JPEG_QUALITY = 82
#: Keep optimized output only when it is at least this much smaller.
IMAGE_MATERIAL_REDUCTION = 0.95

DRIVE_SHIPMENTS_FOLDER = "shipments"
DRIVE_ATTACHMENTS_FOLDER = "attachments"

CATEGORIES: tuple[dict[str, str], ...] = (
    {"id": "customs", "label": "Hải quan"},
    {"id": "contract", "label": "Hợp đồng"},
    {"id": "transport", "label": "Vận chuyển"},
    {"id": "other", "label": "Khác"},
)
DEFAULT_CATEGORY = "other"

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

#: extension → (kind, canonical mime, browser mimes accepted for it)
ALLOWED_TYPES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "pdf": ("pdf", "application/pdf", ("application/pdf",)),
    "jpg": ("image", "image/jpeg", ("image/jpeg", "image/jpg", "application/octet-stream")),
    "jpeg": ("image", "image/jpeg", ("image/jpeg", "image/jpg", "application/octet-stream")),
    "png": ("image", "image/png", ("image/png", "application/octet-stream")),
    "doc": ("ole_office", "application/msword", ("application/msword", "application/octet-stream")),
    "docx": ("zip_office", MIME_DOCX, (MIME_DOCX, "application/octet-stream")),
    "xls": ("ole_office", "application/vnd.ms-excel", ("application/vnd.ms-excel", "application/octet-stream")),
    "xlsx": ("zip_office", MIME_XLSX, (MIME_XLSX, "application/octet-stream")),
}

ALLOWED_EXTENSIONS = tuple(sorted(ALLOWED_TYPES))
ALLOWED_ACCEPT = ",".join(
    sorted({mime for _, canonical, mimes in ALLOWED_TYPES.values() for mime in (canonical, *mimes)} - {"application/octet-stream"})
)

STATUS_AVAILABLE = "AVAILABLE"
STATUS_UPLOAD_FAILED = "UPLOAD_FAILED"

COMPRESSION_OPTIMIZED = "IMAGE_OPTIMIZED"
COMPRESSION_KEPT = "KEPT_ORIGINAL"

#: Refusal codes (bounded, non-secret, stable for tests and for the UI).
CODE_INVALID = "INVALID_UPLOAD"
CODE_TYPE = "TYPE_NOT_ALLOWED"
CODE_SIZE = "SIZE_LIMIT_EXCEEDED"
CODE_MISMATCH = "CONTENT_MISMATCH"
CODE_DRIVE_UNCONFIGURED = "DRIVE_NOT_CONFIGURED"
CODE_DRIVE_FAILED = "DRIVE_FAILED"
CODE_METADATA_FAILED = "METADATA_WRITE_FAILED"
CODE_DUPLICATE = "DUPLICATE"
CODE_NOT_FOUND = "ATTACHMENT_NOT_FOUND"


@dataclass(frozen=True)
class PreparedFile:
    """The bytes that will actually reach Drive, plus how they were obtained."""

    data: bytes
    mime: str
    compression_mode: str
    compression_note: str

    @property
    def optimized(self) -> bool:
        return self.compression_mode == COMPRESSION_OPTIMIZED


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Bounded validation (server-side, independent of the browser)
# ---------------------------------------------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extension_of(file_name: str) -> str:
    name = str(file_name or "").strip().lower()
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1]


def category_of(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in {item["id"] for item in CATEGORIES} else DEFAULT_CATEGORY


def category_label(category: str) -> str:
    for item in CATEGORIES:
        if item["id"] == category:
            return item["label"]
    return "Khác"


def sniff_kind(data: bytes) -> str:
    """Magic-byte sanity check — extension/MIME alone is never trusted."""
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image_jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image_png"
    if data.startswith(b"PK\x03\x04"):
        return "zip_office"
    if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "ole_office"
    return "unknown"


_EXPECTED_SNIFF = {
    "pdf": {"pdf"},
    "image": {"image_jpeg", "image_png"},
    "zip_office": {"zip_office"},
    "ole_office": {"ole_office"},
}


def validate_upload(file_name: str, mime: str, declared_size: Any, data: bytes) -> tuple[str, str, str]:
    """Return ``(safe_name, canonical_mime, kind)`` or raise :class:`UploadRefused`.

    Order matters: cheap name/type checks, then size, then the content sniff —
    all of it BEFORE any Drive work.
    """
    if not str(file_name or "").strip():
        raise UploadRefused(CODE_INVALID, "Thiếu tên tệp.")
    if is_unsafe_drive_name(file_name):
        # A path separator, control character or traversal value is refused
        # instead of being guessed at, and no Drive name is ever built from it.
        raise UploadRefused(CODE_INVALID, "Tên tệp chứa ký tự không hợp lệ hoặc quá dài.")
    safe_name = sanitize_drive_name(file_name)

    extension = extension_of(safe_name)
    spec = ALLOWED_TYPES.get(extension)
    if spec is None:
        raise UploadRefused(
            CODE_TYPE,
            "Định dạng không được phép. Chỉ nhận: " + ", ".join(ALLOWED_EXTENSIONS).upper() + ".",
        )
    kind, canonical_mime, accepted_mimes = spec

    claimed_mime = str(mime or "").strip().lower()
    if claimed_mime and claimed_mime not in accepted_mimes:
        raise UploadRefused(
            CODE_MISMATCH,
            f"MIME '{claimed_mime}' không khớp định dạng .{extension}.",
        )

    size = len(data)
    declared: int | None = None
    if declared_size is not None:
        try:
            declared = int(declared_size)
        except (TypeError, ValueError):
            raise UploadRefused(CODE_INVALID, "Kích thước tệp không hợp lệ.") from None

    # Size ceiling FIRST (cheapest, and the boundary that must never be crossed):
    # the browser's declared number and the real byte count are both checked, so
    # a lying client cannot reach Drive either.
    if (declared is not None and declared > MAX_UPLOAD_BYTES) or size > MAX_UPLOAD_BYTES:
        raise UploadRefused(
            CODE_SIZE,
            f"Tệp vượt giới hạn {_mb(MAX_UPLOAD_BYTES)} — chưa gọi Google Drive, chưa ghi dữ liệu.",
        )
    if declared is not None and declared != size:
        # The browser's number is a convenience; the decoded bytes are the
        # authority, and a mismatch is not worth a Drive call.
        raise UploadRefused(CODE_INVALID, "Kích thước tệp không khớp nội dung gửi lên.")
    if size <= 0:
        raise UploadRefused(CODE_INVALID, "Tệp rỗng.")

    sniffed = sniff_kind(data)
    if sniffed not in _EXPECTED_SNIFF[kind]:
        raise UploadRefused(
            CODE_MISMATCH,
            "Nội dung tệp không khớp định dạng khai báo — tệp bị từ chối.",
        )
    return safe_name, canonical_mime, kind


class UploadRefused(Exception):
    """Expected refusal (never reaches Drive, never reaches Mongo)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _mb(size: int) -> str:
    return f"{size / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Compression policy — actual byte reduction, or nothing
# ---------------------------------------------------------------------------

def prepare_stored_bytes(data: bytes, extension: str, canonical_mime: str) -> PreparedFile:
    """PDF/Office stay byte-identical; images are optimized when materially smaller."""
    kind = ALLOWED_TYPES.get(extension, ("", "", ()))[0]
    if kind != "image":
        return PreparedFile(data, canonical_mime, COMPRESSION_KEPT, "Giữ nguyên bản gốc.")
    optimized = optimize_image(data, extension)
    if optimized is None:
        return PreparedFile(data, canonical_mime, COMPRESSION_KEPT, "Không tối ưu được — giữ nguyên bản gốc.")
    if len(optimized) >= len(data) * IMAGE_MATERIAL_REDUCTION:
        return PreparedFile(data, canonical_mime, COMPRESSION_KEPT, "Ảnh đã tối ưu sẵn — giữ nguyên.")
    return PreparedFile(
        optimized,
        canonical_mime,
        COMPRESSION_OPTIMIZED,
        f"Ảnh đã tối ưu (tối đa {IMAGE_MAX_DIMENSION}px, JPEG q{IMAGE_JPEG_QUALITY}).",
    )


def optimize_image(data: bytes, extension: str) -> bytes | None:
    """Return optimized image bytes, or ``None`` when optimization is not useful.

    Failures NEVER block an upload: the caller falls back to the original bytes.
    No upscaling; EXIF orientation is applied so a rotated phone photo stays
    readable; giant dimensions are capped for document photos.
    """
    try:
        from PIL import Image, ImageOps  # noqa: PLC0415 - optional, bounded dependency
    except ImportError:  # pragma: no cover - Pillow is a declared dependency
        return None
    try:
        with Image.open(io.BytesIO(data)) as opened:
            image = ImageOps.exif_transpose(opened) or opened
            if extension in {"jpg", "jpeg"} and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            width, height = image.size
            if max(width, height) > IMAGE_MAX_DIMENSION:
                image = image.copy()
                image.thumbnail((IMAGE_MAX_DIMENSION, IMAGE_MAX_DIMENSION), Image.LANCZOS)
            buffer = io.BytesIO()
            if extension == "png":
                image.save(buffer, format="PNG", optimize=True)
            else:
                image.save(buffer, format="JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True)
            return buffer.getvalue()
    except Exception as exc:  # noqa: BLE001 - optimization must never block an upload
        LOGGER.info("Image optimization skipped (%s).", type(exc).__name__)
        return None


# ---------------------------------------------------------------------------
# Upload orchestration
# ---------------------------------------------------------------------------

def _resolve_drive_client(drive: Any = None) -> Any:
    if drive is not None:
        return drive
    return build_drive_client()


def _shipment_folder_name(shipment_id: str) -> str:
    return sanitize_drive_name(shipment_id, fallback="lo-hang")


def upload_attachment(
    *,
    shipment_id: str,
    category: Any,
    file_name: str,
    mime: str,
    data: bytes,
    uploaded_by: str = "",
    declared_size: Any = None,
    drive: Any = None,
) -> dict[str, Any]:
    """The whole bounded upload contract, returning a plain outcome dict."""
    from core.database import find_shipment_attachment_by_sha, save_shipment_attachment

    sid = str(shipment_id or "").strip()
    if not sid:
        return {"ok": False, "code": CODE_INVALID, "error": "Thiếu shipmentId."}
    resolved_category = category_of(category)

    try:
        safe_name, canonical_mime, _kind = validate_upload(file_name, mime, declared_size, data)
    except UploadRefused as refusal:
        return {"ok": False, "code": refusal.code, "error": refusal.message}

    # SHA-256 of the ORIGINAL upload — the attachment's durable identity, even
    # when the stored bytes are an optimized derivative.
    digest = sha256_hex(data)

    existing = find_shipment_attachment_by_sha(sid, digest)
    if existing:
        # Same shipment + same original bytes ⇒ no second Drive copy.
        return {
            "ok": True,
            "code": CODE_DUPLICATE,
            "duplicate": True,
            "error": "",
            "message": "Tệp này đã có trên Google Drive của lô — không tải lên bản sao.",
            "record": existing,
        }

    client = _resolve_drive_client(drive)
    if client is None:
        settings = load_drive_settings()
        return {
            "ok": False,
            "code": CODE_DRIVE_UNCONFIGURED,
            "error": (
                "Google Drive chưa được cấu hình trên máy chủ (thiếu "
                + ", ".join(settings.missing)
                + "). Không có tệp nào được tải lên."
            ),
        }

    prepared = prepare_stored_bytes(data, extension_of(safe_name), canonical_mime)

    try:
        root_id = str(client.settings.root_folder_id or "")
        shipments_folder = client.ensure_folder(DRIVE_SHIPMENTS_FOLDER, root_id)
        shipment_folder = client.ensure_folder(_shipment_folder_name(sid), shipments_folder)
        attachments_folder = client.ensure_folder(DRIVE_ATTACHMENTS_FOLDER, shipment_folder)
        uploaded = client.upload_file(
            name=safe_name,
            mime=prepared.mime,
            data=prepared.data,
            parent_id=attachments_folder,
            description=f"{sid} · {category_label(resolved_category)}",
        )
    except DriveError as exc:
        return {"ok": False, "code": CODE_DRIVE_FAILED, "error": f"Google Drive lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001 - a provider fault must not blank the desk
        return {"ok": False, "code": CODE_DRIVE_FAILED, "error": f"Google Drive lỗi ({type(exc).__name__})."}

    record = {
        "id": f"ATT-{sid}-{uuid4().hex[:12]}",
        "shipment_id": sid,
        "original_name": safe_name,
        "stored_name": str(uploaded.get("name") or safe_name),
        "mime": prepared.mime,
        "category": resolved_category,
        "original_size": len(data),
        "stored_size": len(prepared.data),
        "sha256": digest,
        "drive_file_id": str(uploaded.get("fileId") or ""),
        "drive_folder_id": str(attachments_folder),
        "uploaded_at": utc_now_iso(),
        "uploaded_by": str(uploaded_by or ""),
        "compression_mode": prepared.compression_mode,
        "compression_note": prepared.compression_note,
        "status": STATUS_AVAILABLE,
    }

    if save_shipment_attachment(record):
        return {"ok": True, "code": "", "error": "", "record": record, "duplicate": False}

    # Metadata could not be persisted: compensate with exactly ONE bounded
    # delete of the file this same call created.
    drive_file_id = str(record["drive_file_id"])
    if drive_file_id and client.delete_file(drive_file_id):
        return {
            "ok": False,
            "code": CODE_METADATA_FAILED,
            "error": "Không ghi được metadata vào MongoDB; tệp vừa tạo trên Google Drive đã được xoá.",
            "compensated": True,
        }

    # Cleanup could not be proven: say so explicitly, log non-sensitive repair
    # evidence only, and never fabricate a success.
    LOGGER.warning(
        "ATTACHMENT_ORPHAN_RISK shipment_id=%s drive_file_id=%s name=%s bytes=%s",
        sid, drive_file_id or "(none)", record["stored_name"], record["stored_size"],
    )
    return {
        "ok": False,
        "code": CODE_METADATA_FAILED,
        "error": (
            "Không ghi được metadata vào MongoDB và chưa xoá được tệp vừa tạo trên Google Drive "
            "— đã ghi log để xử lý thủ công (orphan risk)."
        ),
        "orphan_risk": True,
        "compensated": False,
    }


# ---------------------------------------------------------------------------
# Download (server-authoritative; Drive stays restricted)
# ---------------------------------------------------------------------------

def fetch_attachment_bytes(record: Mapping[str, Any], *, drive: Any = None) -> dict[str, Any]:
    """Fetch ONE attachment's bytes from Drive for server-side delivery."""
    from core.database import load_shipment_attachment

    attachment_id = str((record or {}).get("id") or "").strip()
    if not attachment_id:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Thiếu mã tệp đính kèm."}
    stored = load_shipment_attachment(attachment_id)
    if not stored:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Không tìm thấy tệp đính kèm này."}
    file_id = str(stored.get("drive_file_id") or "")
    if not file_id:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Metadata không có mã tệp Google Drive."}

    client = _resolve_drive_client(drive)
    if client is None:
        settings = load_drive_settings()
        return {
            "ok": False,
            "code": CODE_DRIVE_UNCONFIGURED,
            "error": (
                "Google Drive chưa được cấu hình trên máy chủ (thiếu "
                + ", ".join(settings.missing)
                + ") — không đọc được tệp."
            ),
        }
    try:
        data = client.download_file(file_id)
    except DriveError as exc:
        return {"ok": False, "code": CODE_DRIVE_FAILED, "error": f"Google Drive lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": CODE_DRIVE_FAILED, "error": f"Google Drive lỗi ({type(exc).__name__})."}
    if not data:
        return {"ok": False, "code": CODE_DRIVE_FAILED, "error": "Google Drive trả về tệp rỗng."}
    return {"ok": True, "code": "", "error": "", "record": stored, "data": data}


# ---------------------------------------------------------------------------
# UI projection — bounded metadata only, never a Drive id or token
# ---------------------------------------------------------------------------

def project_attachment(record: Mapping[str, Any], *, download: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Project ONE attachment for the shipment document list.

    Deliberately absent: ``drive_file_id``, ``drive_folder_id``, the raw
    SHA-256 and any credential. The operator sees the file, its category, its
    honest sizes and who uploaded it.
    """
    attachment_id = str(record.get("id") or "")
    original_size = int(record.get("original_size") or 0)
    stored_size = int(record.get("stored_size") or 0)
    optimized = str(record.get("compression_mode") or "") == COMPRESSION_OPTIMIZED
    ready = bool(download) and str(download.get("attachmentId") or "") == attachment_id
    return {
        "id": attachment_id,
        "name": str(record.get("original_name") or record.get("stored_name") or ""),
        "category": str(record.get("category") or DEFAULT_CATEGORY),
        "categoryLabel": category_label(str(record.get("category") or DEFAULT_CATEGORY)),
        "mime": str(record.get("mime") or ""),
        "originalSize": original_size,
        "storedSize": stored_size,
        "sizeLabel": _size_label(original_size, stored_size, optimized),
        "compressionMode": str(record.get("compression_mode") or COMPRESSION_KEPT),
        "compressionLabel": "Ảnh đã tối ưu" if optimized else "Giữ nguyên",
        "compressionNote": str(record.get("compression_note") or ""),
        "uploadedAt": _display_time(record.get("uploaded_at")),
        "uploadedBy": str(record.get("uploaded_by") or ""),
        "status": str(record.get("status") or STATUS_AVAILABLE),
        "downloadAvailable": ready,
        "downloadBase64": str(download.get("base64") or "") if ready else "",
        "downloadSeq": int(download.get("seq") or 0) if ready else 0,
    }


def project_attachments(
    records: Mapping[str, Mapping[str, Any]] | list[Mapping[str, Any]] | None,
    *,
    download: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Project a shipment's attachments, newest first."""
    rows = list(records.values()) if isinstance(records, Mapping) else list(records or [])
    cleaned = [row for row in rows if isinstance(row, Mapping)]
    cleaned.sort(key=lambda row: str(row.get("uploaded_at") or ""), reverse=True)
    return [project_attachment(row, download=download) for row in cleaned]


def _size_label(original_size: int, stored_size: int, optimized: bool) -> str:
    if optimized and stored_size and stored_size < original_size:
        return f"{_human(original_size)} → {_human(stored_size)}"
    return _human(original_size or stored_size)


def _human(size: int) -> str:
    value = int(size or 0)
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    if value >= 1024:
        return f"{value / 1024:.0f} KB"
    return f"{value} B"


def _display_time(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return text


def decode_upload_payload(payload: Mapping[str, Any]) -> tuple[bytes, int]:
    """Strictly decode the browser's base64 body, bounded BEFORE allocating it."""
    import base64

    encoded = payload.get("base64")
    if not isinstance(encoded, str) or not encoded:
        raise UploadRefused(CODE_INVALID, "Thiếu nội dung tệp.")
    if len(encoded) > MAX_BASE64_CHARS:
        raise UploadRefused(
            CODE_SIZE,
            f"Tệp vượt giới hạn {_mb(MAX_UPLOAD_BYTES)} — chưa gọi Google Drive, chưa ghi dữ liệu.",
        )
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError, base64.binascii.Error):
        raise UploadRefused(CODE_INVALID, "Nội dung tệp không phải base64 hợp lệ.") from None
    return data, len(data)


__all__ = [
    "ALLOWED_ACCEPT",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_TYPES",
    "CATEGORIES",
    "CODE_DRIVE_FAILED",
    "CODE_DRIVE_UNCONFIGURED",
    "CODE_DUPLICATE",
    "CODE_INVALID",
    "CODE_METADATA_FAILED",
    "CODE_MISMATCH",
    "CODE_NOT_FOUND",
    "CODE_SIZE",
    "CODE_TYPE",
    "COMPRESSION_KEPT",
    "COMPRESSION_OPTIMIZED",
    "DEFAULT_CATEGORY",
    "MAX_BASE64_CHARS",
    "MAX_UPLOAD_BYTES",
    "STATUS_AVAILABLE",
    "STATUS_UPLOAD_FAILED",
    "UploadRefused",
    "category_of",
    "decode_upload_payload",
    "fetch_attachment_bytes",
    "optimize_image",
    "prepare_stored_bytes",
    "project_attachment",
    "project_attachments",
    "sha256_hex",
    "upload_attachment",
]
