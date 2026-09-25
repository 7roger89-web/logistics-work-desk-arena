"""LOGI_SHIPMENT_DOCUMENTS_GRIDFS_RUNTIME_01 — bounded shipment attachments.

One vertical slice is preserved from PR65, with the deployable default changed
from the unavailable service-account Drive path to the MongoDB/PyMongo GridFS
path already owned by the application:

    validate → hash ORIGINAL → same-shipment dedupe → store bytes →
    persist ``shipment_attachments`` metadata → fresh authoritative readback.

GridFS is not transactional with the metadata collection. If metadata storage
fails, this service attempts exactly one deletion of the exact newly-created
GridFS file and reports ``orphanRisk`` when that deletion cannot be proven.
The optional ``drive_shared`` path retains PR65's Shared Drive-only rule and
never becomes a fallback for an unknown or failing backend.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from core.config import get_attachment_storage_backend
from core.drive_client import (
    AUTH_MODE_SERVICE_ACCOUNT,
    AUTH_MODE_USER_OAUTH,
    DriveError,
    build_drive_client,
    is_unsafe_drive_name,
    load_drive_settings,
    sanitize_drive_name,
)
from core.gridfs_client import (
    GRIDFS_BUCKET,
    GridFSFileNotFound,
    GridFSStorageError,
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

STORAGE_BACKEND_GRIDFS = "gridfs"
STORAGE_BACKEND_DRIVE_SHARED = "drive_shared"
STORAGE_BACKEND_DRIVE_OAUTH = "drive_oauth"
DRIVE_STORAGE_BACKENDS = frozenset({STORAGE_BACKEND_DRIVE_SHARED, STORAGE_BACKEND_DRIVE_OAUTH})
SUPPORTED_STORAGE_BACKENDS = frozenset({STORAGE_BACKEND_GRIDFS, *DRIVE_STORAGE_BACKENDS})

# GridFS bucket is deliberately fixed: it is an implementation detail, not a
# user/provider setting. Expected collections are
# ``shipment_attachment_files.files`` and ``shipment_attachment_files.chunks``.
SHIPMENT_ATTACHMENT_GRIDFS_BUCKET = GRIDFS_BUCKET

DRIVE_LOGISTICS_FOLDER = "Logistics"
DRIVE_UNKNOWN_CUSTOMER_FOLDER = "Khách hàng chưa xác định"
DRIVE_UNKNOWN_YEAR_FOLDER = "Chưa rõ năm"
DRIVE_UNKNOWN_MONTH_FOLDER = "Chưa rõ tháng"

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
CODE_STORAGE_UNSUPPORTED = "ATTACHMENT_STORAGE_BACKEND_UNSUPPORTED"
CODE_GRIDFS_UNCONFIGURED = "GRIDFS_NOT_CONFIGURED"
CODE_GRIDFS_FAILED = "GRIDFS_FAILED"
CODE_DRIVE_UNCONFIGURED = "DRIVE_NOT_CONFIGURED"  # legacy drive_shared outcome
CODE_DRIVE_FAILED = "DRIVE_FAILED"  # legacy drive_shared outcome
CODE_METADATA_FAILED = "METADATA_WRITE_FAILED"
CODE_METADATA_READBACK_UNPROVEN = "METADATA_READBACK_UNPROVEN"
CODE_DUPLICATE = "DUPLICATE"
CODE_NOT_FOUND = "ATTACHMENT_NOT_FOUND"


@dataclass(frozen=True)
class PreparedFile:
    """The bytes that will reach the selected storage backend."""

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
            f"Tệp vượt giới hạn {_mb(MAX_UPLOAD_BYTES)} — chưa gọi kho chứng từ, chưa lưu dữ liệu.",
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

def resolve_storage_backend() -> str:
    """Return the selected backend; unsupported values remain unsupported."""
    return str(get_attachment_storage_backend() or "").strip().lower()


def build_gridfs_client() -> Any:
    """Build the bounded GridFS store over the app's existing Mongo database."""
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore

    db = get_db()
    if db is None:
        return None
    return GridFSAttachmentStore(db, bucket_name=SHIPMENT_ATTACHMENT_GRIDFS_BUCKET)


def _resolve_gridfs_store(gridfs: Any = None) -> Any:
    if gridfs is not None:
        return gridfs
    return build_gridfs_client()


def _drive_auth_mode(backend: str) -> str:
    return AUTH_MODE_USER_OAUTH if backend == STORAGE_BACKEND_DRIVE_OAUTH else AUTH_MODE_SERVICE_ACCOUNT


def _resolve_drive_client(backend: str, drive: Any = None) -> Any:
    if drive is not None:
        return drive
    return build_drive_client(auth_mode=_drive_auth_mode(backend))


def _shipment_folder_name(shipment_id: str) -> str:
    return sanitize_drive_name(shipment_id, fallback="lo-hang")


def _shipment_header_date(shipment_context: Mapping[str, Any] | None) -> str:
    """Return the canonical shipment header date or blank when unavailable."""
    if not isinstance(shipment_context, Mapping):
        return ""
    data = shipment_context.get("data")
    if not isinstance(data, Mapping):
        return ""
    head = data.get("0.0")
    if not isinstance(head, Mapping):
        return ""
    return str(head.get("created_at") or "").strip()


def _drive_customer_folder(shipment_context: Mapping[str, Any] | None) -> str:
    """Stable human-readable customer folder from authoritative shipment data."""
    if not isinstance(shipment_context, Mapping):
        return DRIVE_UNKNOWN_CUSTOMER_FOLDER
    customer_id = str(shipment_context.get("customer_id") or "").strip()
    customer_name = str(shipment_context.get("customer") or shipment_context.get("client") or "").strip()
    raw = f"{customer_id} - {customer_name}" if customer_id and customer_name else customer_name or DRIVE_UNKNOWN_CUSTOMER_FOLDER
    return sanitize_drive_name(raw, fallback=DRIVE_UNKNOWN_CUSTOMER_FOLDER)


def _drive_period_folders(shipment_context: Mapping[str, Any] | None) -> tuple[str, str]:
    """Return YYYY/MM from shipment created_at; never substitute upload date."""
    raw = _shipment_header_date(shipment_context)
    if len(raw) >= 10:
        try:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
            return parsed.strftime("%Y"), parsed.strftime("%m")
        except ValueError:
            pass
    return DRIVE_UNKNOWN_YEAR_FOLDER, DRIVE_UNKNOWN_MONTH_FOLDER


def drive_folder_hierarchy(shipment_id: str, shipment_context: Mapping[str, Any] | None) -> tuple[str, str, str, str, str]:
    """Names for Logistics / Customer / YYYY / MM / Shipment."""
    year, month = _drive_period_folders(shipment_context)
    return (
        DRIVE_LOGISTICS_FOLDER,
        _drive_customer_folder(shipment_context),
        year,
        month,
        _shipment_folder_name(shipment_id),
    )


def storage_label(backend: str | None = None) -> str:
    """Operator-neutral storage wording, with the configured Drive mode explicit."""
    selected = str(backend or resolve_storage_backend()).strip().lower()
    if selected == STORAGE_BACKEND_DRIVE_SHARED:
        return "Shared Drive"
    if selected == STORAGE_BACKEND_DRIVE_OAUTH:
        return "Google Drive"
    return "Kho chứng từ"


def _storage_error_label(backend: str) -> str:
    return "Google Drive" if backend in DRIVE_STORAGE_BACKENDS else "Kho chứng từ"


def storage_is_configured(backend: str | None = None) -> bool:
    selected = str(backend or resolve_storage_backend()).strip().lower()
    if selected == STORAGE_BACKEND_GRIDFS:
        from core.database import get_db
        try:
            return get_db() is not None
        except Exception:  # noqa: BLE001 - policy must fail closed
            return False
    if selected in DRIVE_STORAGE_BACKENDS:
        return bool(load_drive_settings(_drive_auth_mode(selected)).configured)
    return False


def upload_attachment(
    *,
    shipment_id: str,
    category: Any,
    file_name: str,
    mime: str,
    data: bytes,
    uploaded_by: str = "",
    declared_size: Any = None,
    shipment_context: Mapping[str, Any] | None = None,
    drive: Any = None,
    gridfs: Any = None,
    storage_backend: str | None = None,
) -> dict[str, Any]:
    """Run the bounded upload order for GridFS or one explicit Drive backend.

    ``drive`` and ``gridfs`` are test seams only; production chooses the
    configured backend.  They do not bypass validation, RBAC, dedupe, or the
    metadata boundary.
    """
    from core.database import (
        ATTACHMENT_PROBE_ABSENT_PROVEN,
        ATTACHMENT_PROBE_FOUND_MATCHING,
        find_shipment_attachment_by_sha,
        load_shipment_attachment,
        probe_shipment_attachment_identity,
        save_shipment_attachment,
    )

    sid = str(shipment_id or "").strip()
    if not sid:
        return {"ok": False, "code": CODE_INVALID, "error": "Thiếu shipmentId."}
    resolved_category = category_of(category)
    backend = str(storage_backend or resolve_storage_backend()).strip().lower()
    if backend not in SUPPORTED_STORAGE_BACKENDS:
        return {
            "ok": False,
            "code": CODE_STORAGE_UNSUPPORTED,
            "error": "Kho chứng từ chưa được cấu hình đúng; không có tệp nào được lưu.",
        }

    # Required order: validate ORIGINAL → hash ORIGINAL → same-shipment dedupe.
    try:
        safe_name, canonical_mime, _kind = validate_upload(file_name, mime, declared_size, data)
    except UploadRefused as refusal:
        return {"ok": False, "code": refusal.code, "error": refusal.message}
    digest = sha256_hex(data)
    existing = find_shipment_attachment_by_sha(sid, digest)
    if existing:
        return {
            "ok": True,
            "code": CODE_DUPLICATE,
            "duplicate": True,
            "error": "",
            "message": "Tệp này đã có trong kho chứng từ của lô — không tải lên bản sao.",
            "record": existing,
        }

    # Optimization has no external side effect and therefore follows the
    # dedupe guard but precedes the single provider write.
    prepared = prepare_stored_bytes(data, extension_of(safe_name), canonical_mime)
    client: Any = None
    uploaded: dict[str, Any]
    try:
        if backend == STORAGE_BACKEND_GRIDFS:
            client = _resolve_gridfs_store(gridfs)
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
                metadata={"shipment_id": sid, "category": resolved_category},
            )
        else:
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
            root_id = str(client.settings.root_folder_id or "")
            logistics_name, customer_name, year_name, month_name, shipment_name = drive_folder_hierarchy(
                sid, shipment_context
            )
            logistics_folder = client.ensure_folder(logistics_name, root_id)
            customer_folder = client.ensure_folder(customer_name, logistics_folder)
            year_folder = client.ensure_folder(year_name, customer_folder)
            month_folder = client.ensure_folder(month_name, year_folder)
            shipment_folder = client.ensure_folder(shipment_name, month_folder)
            uploaded = client.upload_file(
                name=safe_name,
                mime=prepared.mime,
                data=prepared.data,
                parent_id=shipment_folder,
                description=f"{sid} · {category_label(resolved_category)}",
            )
            uploaded = {
                "storage_file_id": str(uploaded.get("fileId") or ""),
                "stored_name": str(uploaded.get("name") or safe_name),
                "stored_size": len(prepared.data),
            }
    except (DriveError, GridFSStorageError) as exc:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001 - provider faults never become success
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi ({type(exc).__name__})."}

    storage_file_id = str(uploaded.get("storage_file_id") or "").strip()
    if not storage_file_id:
        return {
            "ok": False,
            "code": CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED,
            "error": f"{_storage_error_label(backend)} không trả về mã tệp; không ghi metadata.",
        }
    record = {
        "id": f"ATT-{sid}-{uuid4().hex[:12]}",
        "storage_backend": backend,
        "storage_file_id": storage_file_id,
        "shipment_id": sid,
        "original_name": safe_name,
        "stored_name": str(uploaded.get("stored_name") or safe_name),
        "mime": prepared.mime,
        "category": resolved_category,
        "original_size": len(data),
        "stored_size": int(uploaded.get("stored_size") or len(prepared.data)),
        "sha256": digest,
        "uploaded_at": utc_now_iso(),
        "uploaded_by": str(uploaded_by or ""),
        "compression_mode": prepared.compression_mode,
        "compression_note": prepared.compression_note,
        "status": STATUS_AVAILABLE,
    }

    metadata_probe_state: str | None = None
    try:
        metadata_saved = bool(save_shipment_attachment(record))
    except Exception:  # noqa: BLE001 - save may have committed before audit failed
        # ``save_shipment_attachment`` writes the row before its audit insert.
        # A raised audit exception therefore cannot be treated as proof that
        # the metadata write was absent. The tri-state exact-id probe is the
        # only gate allowed to authorize the existing compensation delete.
        probe_state, durable = probe_shipment_attachment_identity(record)
        metadata_probe_state = probe_state
        if probe_state == ATTACHMENT_PROBE_FOUND_MATCHING:
            return {
                "ok": False,
                "code": CODE_METADATA_READBACK_UNPROVEN,
                "error": (
                    "Bước ghi metadata không hoàn tất rõ ràng nhưng đã thấy hồ sơ tệp tương ứng; "
                    "giữ nguyên metadata và nội dung tệp, không xoá bù."
                ),
                "metadata_committed": True,
                "readback_proven": False,
                "compensation_attempted": False,
                "compensated": False,
                "orphan_risk": False,
            }
        if probe_state != ATTACHMENT_PROBE_ABSENT_PROVEN:
            return {
                "ok": False,
                "code": CODE_METADATA_READBACK_UNPROVEN,
                "error": (
                    "Bước ghi metadata không hoàn tất rõ ràng và chưa chứng minh được hồ sơ tệp; "
                    "giữ nguyên metadata và nội dung tệp, không xoá bù."
                ),
                "metadata_committed": False,
                "readback_proven": False,
                "compensation_attempted": False,
                "compensated": False,
                "orphan_risk": False,
            }
        # Only a successful exact-id lookup that returned no row may enter the
        # existing one-delete compensation path below.
        metadata_saved = False

    if metadata_saved:
        # A successful metadata writer call and a failed/unproven fresh read are
        # different states. The row may already be durable, so deleting bytes
        # here could create the invalid row-without-file state. Preserve both
        # sides and let the next request's SHA dedupe reconcile it.
        try:
            fresh = load_shipment_attachment(record["id"])
        except Exception:  # noqa: BLE001 - readback proof is unavailable
            fresh = None
        if fresh is not None:
            return {"ok": True, "code": "", "error": "", "record": fresh, "duplicate": False}
        return {
            "ok": False,
            "code": CODE_METADATA_READBACK_UNPROVEN,
            "error": (
                "Đã ghi metadata nhưng chưa xác minh được readback mới; "
                "giữ nguyên metadata và nội dung tệp, không xoá bù."
            ),
            "metadata_committed": True,
            "readback_proven": False,
            "compensation_attempted": False,
            "compensated": False,
            "orphan_risk": False,
        }

    # A false metadata result is not proof of absence either: the write helper
    # may have failed after an upsert, or its state may be unavailable. Only a
    # successful exact-id probe returning ABSENT_PROVEN may authorize cleanup.
    if metadata_probe_state is None:
        metadata_probe_state, durable = probe_shipment_attachment_identity(record)
    if metadata_probe_state != ATTACHMENT_PROBE_ABSENT_PROVEN:
        matching = metadata_probe_state == ATTACHMENT_PROBE_FOUND_MATCHING
        return {
            "ok": False,
            "code": CODE_METADATA_READBACK_UNPROVEN,
            "error": (
                "Không xác minh được metadata nhưng đã thấy hồ sơ tệp tương ứng; "
                "giữ nguyên metadata và nội dung tệp, không xoá bù."
                if matching else
                "Không xác minh được metadata và cũng chưa chứng minh được hồ sơ tệp vắng mặt; "
                "giữ nguyên nội dung tệp, không xoá bù."
            ),
            "metadata_committed": matching,
            "readback_proven": False,
            "compensation_attempted": False,
            "compensated": False,
            "orphan_risk": False,
        }

    # GridFS has no multi-document transaction. Compensation is now gated by
    # authoritative absence and gets exactly ONE delete attempt for the exact
    # identity created by this call.
    compensation_attempted = True
    deleted = False
    try:
        deleted = bool(client.delete_file(storage_file_id))
    except Exception:  # noqa: BLE001 - a failed proof is orphan risk
        deleted = False
    if deleted:
        return {
            "ok": False,
            "code": CODE_METADATA_FAILED,
            "error": f"Không ghi được metadata vào MongoDB; tệp vừa tạo trong {storage_label(backend)} đã được xoá.",
            "compensation_attempted": compensation_attempted,
            "compensated": True,
            "orphan_risk": False,
        }

    LOGGER.warning(
        "ATTACHMENT_ORPHAN_RISK backend=%s shipment_id=%s storage_file_id=%s name=%s bytes=%s",
        backend, sid, storage_file_id or "(none)", record["stored_name"], record["stored_size"],
    )
    return {
        "ok": False,
        "code": CODE_METADATA_FAILED,
        "error": (
            f"Không ghi được metadata và chưa chứng minh được việc xoá tệp trong {storage_label(backend)} "
            "— đã ghi log để xử lý thủ công (orphan risk)."
        ),
        "orphan_risk": True,
        "compensation_attempted": compensation_attempted,
        "compensated": False,
    }


# ---------------------------------------------------------------------------
# Download (server-authoritative; Drive stays restricted)
# ---------------------------------------------------------------------------

def fetch_attachment_bytes(
    record: Mapping[str, Any],
    *,
    shipment_id: str | None = None,
    drive: Any = None,
    gridfs: Any = None,
    storage_backend: str | None = None,
) -> dict[str, Any]:
    """Fetch ONE file after metadata and shipment ownership checks.

    The ownership check is deliberately before backend construction/read. A
    caller that supplies a mismatched shipment therefore causes zero GridFS or
    Drive reads.
    """
    from core.database import load_shipment_attachment

    attachment_id = str((record or {}).get("id") or "").strip()
    if not attachment_id:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Thiếu mã tệp đính kèm."}
    stored = load_shipment_attachment(attachment_id)
    if not stored:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Không tìm thấy tệp đính kèm này."}
    expected_shipment = str(shipment_id or "").strip()
    if expected_shipment and str(stored.get("shipment_id") or "") != expected_shipment:
        return {"ok": False, "code": "SHIPMENT_MISMATCH", "error": "Tệp đính kèm không thuộc lô hàng này."}

    backend = str(storage_backend or stored.get("storage_backend") or "").strip().lower()
    # Backward-compatible reads for rows created by PR65 before the selector.
    if not backend and str(stored.get("drive_file_id") or "").strip():
        backend = STORAGE_BACKEND_DRIVE_SHARED
    if backend not in SUPPORTED_STORAGE_BACKENDS:
        return {"ok": False, "code": CODE_STORAGE_UNSUPPORTED, "error": "Kho chứng từ chưa được cấu hình đúng."}
    file_id = str(stored.get("storage_file_id") or stored.get("drive_file_id") or "").strip()
    if not file_id:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": "Metadata không có mã tệp trong kho chứng từ."}

    try:
        if backend == STORAGE_BACKEND_GRIDFS:
            client = _resolve_gridfs_store(gridfs)
            if client is None:
                return {
                    "ok": False,
                    "code": CODE_GRIDFS_UNCONFIGURED,
                    "error": "Kho chứng từ chưa sẵn sàng trên máy chủ — không đọc được tệp.",
                }
            data = client.download_file(file_id)
        else:
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
            data = client.download_file(file_id)
    except GridFSFileNotFound as exc:
        return {"ok": False, "code": CODE_NOT_FOUND, "error": str(exc)}
    except (DriveError, GridFSStorageError) as exc:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi: {exc}"}
    except Exception as exc:  # noqa: BLE001
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} lỗi ({type(exc).__name__})."}
    if not data:
        code = CODE_GRIDFS_FAILED if backend == STORAGE_BACKEND_GRIDFS else CODE_DRIVE_FAILED
        return {"ok": False, "code": code, "error": f"{_storage_error_label(backend)} trả về tệp rỗng."}
    return {"ok": True, "code": "", "error": "", "record": stored, "data": bytes(data)}


# ---------------------------------------------------------------------------
# UI projection — bounded metadata only, never a Drive id or token
# ---------------------------------------------------------------------------

def project_attachment(record: Mapping[str, Any], *, download: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Project ONE attachment for the shipment document list.

    Deliberately absent: ``storage_file_id``, GridFS/ObjectId internals,
    legacy ``drive_file_id``, ``drive_folder_id``, the raw SHA-256 and any
    credential. The operator sees the file, its category, its
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
            f"Tệp vượt giới hạn {_mb(MAX_UPLOAD_BYTES)} — chưa gọi kho chứng từ, chưa lưu dữ liệu.",
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
    "CODE_GRIDFS_FAILED",
    "CODE_GRIDFS_UNCONFIGURED",
    "CODE_STORAGE_UNSUPPORTED",
    "CODE_DUPLICATE",
    "CODE_INVALID",
    "CODE_METADATA_FAILED",
    "CODE_METADATA_READBACK_UNPROVEN",
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
    "build_gridfs_client",
    "category_of",
    "decode_upload_payload",
    "fetch_attachment_bytes",
    "optimize_image",
    "prepare_stored_bytes",
    "project_attachment",
    "project_attachments",
    "resolve_storage_backend",
    "sha256_hex",
    "storage_is_configured",
    "storage_label",
    "upload_attachment",
    "GRIDFS_BUCKET",
    "SHIPMENT_ATTACHMENT_GRIDFS_BUCKET",
]
