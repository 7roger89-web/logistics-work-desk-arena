"""Bounded GridFS byte store for shipment attachments.

GridFS is the app's existing MongoDB/PyMongo byte-storage path for this
runtime.  This module intentionally exposes only the three operations the
shipment attachment service needs: upload, download, and delete.  Business
metadata remains in ``shipment_attachments``; GridFS ids are backend-only.

No new SDK or object-storage abstraction is introduced here.  The bucket name
is fixed so deployment configuration cannot accidentally route attachments to
an unrelated collection.
"""

from __future__ import annotations

from typing import Any, Mapping

from bson import ObjectId
from bson.errors import InvalidId

GRIDFS_BUCKET = "shipment_attachment_files"


class GridFSStorageError(RuntimeError):
    """A provider failure that is safe to surface at the service boundary."""


class GridFSFileNotFound(GridFSStorageError):
    """The requested GridFS file id does not exist."""


class GridFSAttachmentStore:
    """Small, injectable GridFS adapter used by the shipment service.

    ``bucket`` is injectable for isolated tests.  Production constructs a
    normal :class:`gridfs.GridFS` bucket over the already-configured Mongo
    database; no second Mongo connection is created here.
    """

    def __init__(self, db: Any, *, bucket_name: str = GRIDFS_BUCKET, bucket: Any = None) -> None:
        if db is None and bucket is None:
            raise GridFSStorageError("MongoDB chưa sẵn sàng cho kho chứng từ.")
        self.bucket_name = bucket_name
        if bucket is not None:
            self._bucket = bucket
            return
        try:
            from gridfs import GridFS

            self._bucket = GridFS(db, collection=bucket_name)
        except Exception as exc:  # noqa: BLE001 - provider construction boundary
            raise GridFSStorageError(
                f"Không khởi tạo được kho chứng từ ({type(exc).__name__})."
            ) from exc

    @property
    def bucket(self) -> Any:
        """The injected/constructed bucket, exposed only for focused tests."""
        return self._bucket

    def upload_file(
        self,
        *,
        name: str,
        mime: str,
        data: bytes,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store exactly ``data`` and return a backend-only file identity."""
        if not isinstance(data, (bytes, bytearray, memoryview)) or not data:
            raise GridFSStorageError("Không có dữ liệu để lưu vào kho chứng từ.")
        try:
            file_id = self._bucket.put(
                bytes(data),
                filename=str(name or ""),
                contentType=str(mime or "application/octet-stream"),
                metadata=dict(metadata or {}),
            )
        except Exception as exc:  # noqa: BLE001 - provider failure boundary
            raise GridFSStorageError(
                f"Kho chứng từ lỗi khi ghi ({type(exc).__name__})."
            ) from exc
        identity = str(file_id or "")
        if not identity:
            raise GridFSStorageError("Kho chứng từ không trả về mã tệp.")
        return {
            "storage_file_id": identity,
            "stored_name": str(name or ""),
            "stored_size": len(data),
        }

    def download_file(self, storage_file_id: str) -> bytes:
        """Read exactly one GridFS file, or fail closed when it is missing."""
        object_id = self._object_id(storage_file_id)
        try:
            grid_out = self._bucket.get(object_id)
            data = grid_out.read()
        except GridFSFileNotFound:
            raise
        except Exception as exc:  # noqa: BLE001 - NoFile differs by PyMongo version
            from gridfs.errors import NoFile

            if isinstance(exc, NoFile):
                raise GridFSFileNotFound("Không tìm thấy tệp trong kho chứng từ.") from exc
            raise GridFSStorageError(
                f"Kho chứng từ lỗi khi đọc ({type(exc).__name__})."
            ) from exc
        if data is None:
            raise GridFSStorageError("Kho chứng từ không trả về nội dung tệp.")
        return bytes(data)

    def delete_file(self, storage_file_id: str) -> bool:
        """Delete exactly one known file; callers decide whether to retry (never)."""
        object_id = self._object_id(storage_file_id)
        try:
            self._bucket.delete(object_id)
            return True
        except Exception as exc:  # noqa: BLE001 - compensation is fail-closed
            return False

    @staticmethod
    def _object_id(storage_file_id: str) -> ObjectId:
        value = str(storage_file_id or "").strip()
        try:
            return ObjectId(value)
        except (InvalidId, TypeError) as exc:
            raise GridFSFileNotFound("Mã tệp trong kho chứng từ không hợp lệ.") from exc


# A concise alias keeps focused tests and callers readable without introducing
# another provider abstraction.
GridFSStore = GridFSAttachmentStore


__all__ = [
    "GRIDFS_BUCKET",
    "GridFSAttachmentStore",
    "GridFSFileNotFound",
    "GridFSStorageError",
    "GridFSStore",
]
