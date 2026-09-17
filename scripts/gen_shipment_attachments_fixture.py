#!/usr/bin/env python3
"""Generate the LOGI_SHIPMENT_DOCUMENTS_DRIVE_01 DOM-acceptance fixture.

The fixture comes from the real, isolated mongomock staging view-model — never
from hand-written browser data and never from production, and the Drive side is
a DETERMINISTIC FAKE ADAPTER (no service account, no real folder, no live Drive
write):

* one optimized document photo (``Tờ khai hải quan.jpg``) so the UI has to
  render an honest "Ảnh đã tối ưu" + "1.x MB → yyy KB" row;
* one PDF kept byte-identical (``Bang chung giao hang.pdf``) so the UI has to
  render "Giữ nguyên";
* the server's own ``attachmentPolicy`` (extensions, accept list, byte ceiling,
  categories, ``allowUpload``) exactly as the running app delivers it.

Run:  .venv/bin/python scripts/gen_shipment_attachments_fixture.py
Out:  tests/component/fixtures/view_model_attachments.json
"""

from __future__ import annotations

import base64
import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_attachments.json"

SHIPMENT_ID = "LO-0306"


def _photo_bytes() -> bytes:
    """Deterministic photographic-ish JPEG — large enough to be optimized."""
    from PIL import Image

    image = Image.new("RGB", (2600, 1800))
    pixels = image.load()
    for y in range(1800):
        for x in range(2600):
            pixels[x, y] = ((x * 7 + y * 3) % 256, (x * 5 + y * 11) % 256, (x * 13 + y * 2) % 256)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )


class _FakeDrive:
    """Deterministic in-memory Drive stand-in (staging fixture only)."""

    def __init__(self) -> None:
        from core.drive_client import DriveSettings

        self.settings = DriveSettings(
            root_folder_id="ROOT-FOLDER-FIXTURE",
            service_account={
                "client_email": "fixture@example.iam.gserviceaccount.com",
                "private_key": "-----BEGIN PRIVATE KEY-----fixture-----END PRIVATE KEY-----",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
        )
        self._folders: dict[tuple[str, str], str] = {}
        self._files: dict[str, bytes] = {}

    def ensure_folder(self, name: str, parent_id: str) -> str:
        key = (parent_id, name)
        if key not in self._folders:
            self._folders[key] = f"folder-{len(self._folders) + 1}"
        return self._folders[key]

    def upload_file(self, *, name: str, mime: str, data: bytes, parent_id: str,
                    description: str = "") -> dict:
        file_id = f"drive-file-{len(self._files) + 1}"
        self._files[file_id] = bytes(data)
        return {"fileId": file_id, "name": name, "mime": mime, "size": len(data),
                "parents": [parent_id], "webViewLink": ""}

    def download_file(self, file_id: str) -> bytes:
        return self._files.get(file_id, b"")

    def delete_file(self, file_id: str) -> bool:
        return self._files.pop(file_id, None) is not None


def main() -> None:
    import streamlit as st

    from core.shipment_attachments import upload_attachment
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    drive = _FakeDrive()
    photo = _photo_bytes()
    pdf = _pdf_bytes()
    for name, mime, payload, category in (
        ("Tờ khai hải quan.jpg", "image/jpeg", photo, "customs"),
        ("Bang chung giao hang.pdf", "application/pdf", pdf, "contract"),
    ):
        outcome = upload_attachment(
            shipment_id=SHIPMENT_ID,
            category=category,
            file_name=name,
            mime=mime,
            data=payload,
            uploaded_by="staging.support",
            drive=drive,
        )
        assert outcome.get("ok") and not outcome.get("duplicate"), outcome
        assert base64.b64encode(payload).decode("ascii")  # sanity: bytes were provided by this script

    model = vm.build_view_model()
    row = next(item for item in model["shipments"] if item["id"] == SHIPMENT_ID)
    assert len(row["attachments"]) == 2, row["attachments"]
    # The fixture must prove BOTH honesty states are reachable in the real UI.
    assert {item["compressionLabel"] for item in row["attachments"]} == {"Ảnh đã tối ưu", "Giữ nguyên"}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    print("attachments:", [(item["name"], item["sizeLabel"], item["compressionLabel"])
                           for item in row["attachments"]])
    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
