"""Focused GridFS runtime proof for Issue #66.

All storage in this file is an injected fake bucket/store or isolated test
state. No Atlas, production database, deployment, or real attachment is used.
"""

from __future__ import annotations

import json
from bson import ObjectId
from unittest.mock import patch

import pytest

from core import shipment_attachments as att
from core.gridfs_client import (
    GridFSAttachmentStore,
    GridFSFileNotFound,
    GridFSStorageError,
)


PDF = b"%PDF-1.4\nexact-gridfs-bytes"


class Bucket:
    def __init__(self):
        self.files = {}
        self.put_calls = []
        self.get_calls = []
        self.delete_calls = []

    def put(self, data, **kwargs):
        file_id = ObjectId()
        self.put_calls.append((bytes(data), kwargs))
        self.files[file_id] = bytes(data)
        return file_id

    def get(self, file_id):
        self.get_calls.append(file_id)
        if file_id not in self.files:
            raise GridFSFileNotFound("missing")
        data = self.files[file_id]
        return type("GridOut", (), {"read": lambda self: data})()

    def delete(self, file_id):
        self.delete_calls.append(file_id)
        if file_id not in self.files:
            raise GridFSFileNotFound("missing")
        del self.files[file_id]


@pytest.fixture()
def bucket():
    return Bucket()


class FakeStore:
    def __init__(self, *, fail_upload=False, fail_delete=False, fail_download=False):
        self.fail_upload = fail_upload
        self.fail_delete = fail_delete
        self.fail_download = fail_download
        self.uploads = []
        self.downloads = []
        self.deletes = []
        self.files = {}

    def upload_file(self, *, name, mime, data, metadata=None):
        if self.fail_upload:
            self.uploads.append({"name": name, "mime": mime, "data": bytes(data), "metadata": metadata})
            raise GridFSStorageError("write failed")
        file_id = str(ObjectId())
        self.uploads.append({"name": name, "mime": mime, "data": bytes(data), "metadata": metadata, "storage_file_id": file_id})
        self.files[file_id] = bytes(data)
        return {"storage_file_id": file_id, "stored_name": name, "stored_size": len(data)}

    def download_file(self, file_id):
        self.downloads.append(file_id)
        if self.fail_download:
            raise GridFSStorageError("read failed")
        if file_id not in self.files:
            raise GridFSFileNotFound("missing")
        return self.files[file_id]

    def delete_file(self, file_id):
        self.deletes.append(file_id)
        if self.fail_delete:
            return False
        self.files.pop(file_id, None)
        return True


def metadata_record(*, file_id="507f1f77bcf86cd799439011", shipment_id="SHP-1"):
    return {
        "id": "ATT-SHP-1-1",
        "storage_backend": "gridfs",
        "storage_file_id": file_id,
        "shipment_id": shipment_id,
        "original_name": "chung-tu.pdf",
        "stored_name": "chung-tu.pdf",
        "mime": "application/pdf",
        "category": "customs",
        "original_size": len(PDF),
        "stored_size": len(PDF),
        "sha256": att.sha256_hex(PDF),
        "uploaded_at": att.utc_now_iso(),
        "uploaded_by": "operator",
        "compression_mode": att.COMPRESSION_KEPT,
        "compression_note": "Giữ nguyên bản gốc.",
        "status": att.STATUS_AVAILABLE,
    }


class TestGridFSAdapter:
    def test_upload_download_delete_are_exact_and_use_bounded_bucket(self, bucket):
        store = GridFSAttachmentStore(object(), bucket_name="shipment_attachment_files", bucket=bucket)
        uploaded = store.upload_file(name="a.pdf", mime="application/pdf", data=PDF, metadata={"shipment_id": "SHP-1"})
        assert uploaded["storage_file_id"]
        assert bucket.put_calls[0][0] == PDF
        assert bucket.put_calls[0][1]["filename"] == "a.pdf"
        assert bucket.put_calls[0][1]["contentType"] == "application/pdf"
        assert store.download_file(uploaded["storage_file_id"]) == PDF
        assert store.delete_file(uploaded["storage_file_id"]) is True
        assert bucket.delete_calls

    def test_pymongo_gridfs_uses_the_bounded_files_and_chunks_collections(self):
        import mongomock
        import mongomock.gridfs

        mongomock.gridfs.enable_gridfs_integration()
        client = mongomock.MongoClient()
        store = GridFSAttachmentStore(client["isolated"], bucket_name="shipment_attachment_files")
        uploaded = store.upload_file(name="a.pdf", mime="application/pdf", data=PDF)
        assert client["isolated"]["shipment_attachment_files.files"].count_documents({}) == 1
        assert client["isolated"]["shipment_attachment_files.chunks"].count_documents({}) >= 1
        assert store.download_file(uploaded["storage_file_id"]) == PDF
        assert store.delete_file(uploaded["storage_file_id"]) is True

    def test_missing_file_and_provider_failure_fail_closed(self, bucket):
        store = GridFSAttachmentStore(object(), bucket=bucket)
        with pytest.raises(GridFSFileNotFound):
            store.download_file(str(ObjectId()))

        class Broken:
            def put(self, *args, **kwargs):
                raise RuntimeError("provider")

        broken = GridFSAttachmentStore(object(), bucket=Broken())
        with pytest.raises(GridFSStorageError):
            broken.upload_file(name="a.pdf", mime="application/pdf", data=PDF)


class TestGridFSAttachmentService:
    def test_unknown_backend_fails_closed_without_provider_write(self):
        store = FakeStore()
        with patch("core.database.find_shipment_attachment_by_sha") as dedupe:
            result = att.upload_attachment(
                shipment_id="SHP-1", category="other", file_name="a.pdf",
                mime="application/pdf", data=PDF, storage_backend="s3", gridfs=store,
            )
        assert result["ok"] is False
        assert result["code"] == att.CODE_STORAGE_UNSUPPORTED
        dedupe.assert_not_called()
        assert store.uploads == []

    def test_valid_upload_uses_gridfs_then_fresh_metadata_readback(self):
        store = FakeStore()
        fresh = metadata_record(file_id=str(ObjectId()))
        with patch("core.database.find_shipment_attachment_by_sha", return_value=None), \
             patch("core.database.save_shipment_attachment", return_value=True), \
             patch("core.database.load_shipment_attachment", return_value=fresh):
            result = att.upload_attachment(
                shipment_id="SHP-1", category="customs", file_name="chung-tu.pdf",
                mime="application/pdf", data=PDF, uploaded_by="operator",
                declared_size=len(PDF), storage_backend="gridfs", gridfs=store,
            )
        assert result["ok"] is True
        assert result["record"] is fresh
        assert len(store.uploads) == 1
        assert store.uploads[0]["data"] == PDF
        assert store.uploads[0]["metadata"] == {"shipment_id": "SHP-1", "category": "customs"}

    def test_duplicate_has_zero_second_gridfs_write(self):
        store = FakeStore()
        existing = metadata_record()
        with patch("core.database.find_shipment_attachment_by_sha", return_value=existing), \
             patch("core.database.save_shipment_attachment") as save:
            result = att.upload_attachment(
                shipment_id="SHP-1", category="other", file_name="renamed.pdf",
                mime="application/pdf", data=PDF, storage_backend="gridfs", gridfs=store,
            )
        assert result["ok"] and result["duplicate"] is True
        assert store.uploads == []
        save.assert_not_called()

    @pytest.mark.parametrize("file_name,data,mime", [
        ("too.pdf", b"%PDF-1.4", "application/pdf"),
        ("bad.exe", b"not allowed", "application/octet-stream"),
    ])
    def test_invalid_input_has_zero_gridfs_writes(self, file_name, data, mime):
        store = FakeStore()
        with patch("core.database.find_shipment_attachment_by_sha") as dedupe:
            result = att.upload_attachment(
                shipment_id="SHP-1", category="other", file_name=file_name,
                mime=mime, data=(b"x" * (att.MAX_UPLOAD_BYTES + 1)) if file_name == "too.pdf" else data,
                storage_backend="gridfs", gridfs=store,
            )
        assert result["ok"] is False
        assert store.uploads == []
        dedupe.assert_not_called()

    def test_metadata_failure_deletes_exact_gridfs_file_once(self):
        store = FakeStore()
        with patch("core.database.find_shipment_attachment_by_sha", return_value=None), \
             patch("core.database.save_shipment_attachment", return_value=False), \
             patch("core.database.load_shipment_attachment", return_value=None):
            result = att.upload_attachment(
                shipment_id="SHP-1", category="other", file_name="a.pdf",
                mime="application/pdf", data=PDF, storage_backend="gridfs", gridfs=store,
            )
        assert result["ok"] is False
        assert result["compensated"] is True
        assert len(store.deletes) == 1
        assert store.deletes[0] == store.uploads[0]["storage_file_id"]

    def test_failed_compensation_reports_orphan_risk(self):
        store = FakeStore(fail_delete=True)
        with patch("core.database.find_shipment_attachment_by_sha", return_value=None), \
             patch("core.database.save_shipment_attachment", return_value=False):
            result = att.upload_attachment(
                shipment_id="SHP-1", category="other", file_name="a.pdf",
                mime="application/pdf", data=PDF, storage_backend="gridfs", gridfs=store,
            )
        assert result["ok"] is False
        assert result["orphan_risk"] is True
        assert len(store.deletes) == 1

    def test_shipment_mismatch_has_zero_gridfs_reads(self):
        store = FakeStore()
        record = metadata_record(shipment_id="SHP-1")
        with patch("core.database.load_shipment_attachment", return_value=record):
            result = att.fetch_attachment_bytes({"id": record["id"]}, shipment_id="SHP-2", gridfs=store)
        assert result["code"] == "SHIPMENT_MISMATCH"
        assert store.downloads == []

    def test_legacy_drive_identity_remains_readable_without_migration(self):
        from core.drive_client import DriveSettings

        legacy = metadata_record()
        legacy.pop("storage_backend")
        legacy.pop("storage_file_id")
        legacy["drive_file_id"] = "legacy-drive-file"
        fake_drive = FakeStore()
        fake_drive.files["legacy-drive-file"] = PDF
        fake_drive.settings = DriveSettings(root_folder_id="shared-drive-root", service_account={"client_email": "x", "private_key": "x", "token_uri": "x"})
        with patch("core.database.load_shipment_attachment", return_value=legacy), \
             patch("core.shipment_attachments.build_drive_client", return_value=fake_drive):
            result = att.fetch_attachment_bytes({"id": legacy["id"]}, shipment_id="SHP-1")
        assert result["ok"] is True
        assert result["data"] == PDF
        assert fake_drive.downloads == ["legacy-drive-file"]

    def test_unauthorized_upload_has_zero_gridfs_calls(self):
        from views import logi_view_model as vm

        store = FakeStore()
        with patch("core.auth.can_generate_documents", return_value=False), \
             patch("core.shipment_attachments.build_gridfs_client") as build:
            result = vm._handle_shipment_attachment_upload({
                "shipmentId": "SHP-1", "category": "other", "fileName": "a.pdf",
                "mime": "application/pdf", "size": len(PDF),
                "base64": "JVBERi0xLjQKZXhhY3QtZ3JpZGZzLWJ5dGVz", "requestId": "unauth",
            })
        assert result["ok"] is False
        assert result["gate"] == "BLOCKED_PERMISSION_DENIED"
        build.assert_not_called()
        assert store.uploads == []

    def test_unauthorized_download_has_zero_metadata_or_gridfs_reads(self):
        from views import logi_view_model as vm

        store = FakeStore()
        with patch("core.auth.can_operate_business", return_value=False), \
             patch("core.database.load_shipment_attachment") as lookup, \
             patch("core.shipment_attachments.build_gridfs_client") as build:
            result = vm._handle_attachment_download({
                "shipmentId": "SHP-1", "attachmentId": "ATT-1", "requestId": "unauth-download",
            })
        assert result["ok"] is False
        assert result["gate"] == "BLOCKED_PERMISSION_DENIED"
        lookup.assert_not_called()
        build.assert_not_called()
        assert store.downloads == []

    def test_projection_has_no_storage_identity_or_sha(self):
        projected = att.project_attachment(metadata_record())
        serialized = json.dumps(projected, ensure_ascii=False)
        assert "storage_file_id" not in projected
        assert att.sha256_hex(PDF) not in serialized
        assert "507f1f77bcf86cd799439011" not in serialized
        assert "drive_file_id" not in projected
