#!/usr/bin/env python3
"""Generate the LOGI_SHIPMENT_DOCUMENTS_GRIDFS_RUNTIME_01 DOM fixture.

The fixture comes from the real, isolated mongomock staging view-model — never
from hand-written browser data and never from production, and the byte store is
a DETERMINISTIC FAKE GRIDFS ADAPTER (no Atlas, no live provider write):

* one optimized document photo (``Tờ khai hải quan.jpg``) so the UI has to
  render an honest "Ảnh đã tối ưu" + "x MB → y KB" row;
* one PDF kept byte-identical (``Bang chung giao hang.pdf``) so the UI has to
  render "Giữ nguyên";
* the server's own ``attachmentPolicy`` (extensions, accept list, byte ceiling,
  categories, ``allowUpload``) exactly as the running app delivers it.

Run:  .venv/bin/python scripts/gen_shipment_attachments_fixture.py
Out:  tests/component/fixtures/view_model_attachments.json
"""

from __future__ import annotations

import io
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_attachments.json"

SHIPMENT_ID = "LO-0306"


def _photo_bytes(*, width: int = 2600, height: int = 1800, quality: int = 95) -> bytes:
    """Deterministic photographic-ish JPEG — large enough to be optimized.

    Seeded white noise (Mersenne Twister is stable across runs) instead of a
    per-pixel Python loop: identical test semantics in a fraction of the time.
    """
    from PIL import Image

    raw = random.Random(42).randbytes(width * height * 3)
    image = Image.frombytes("RGB", (width, height), raw)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )


class _FakeGridFS:
    """Deterministic in-memory GridFS stand-in (fixture only)."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    def upload_file(self, *, name: str, mime: str, data: bytes, metadata=None) -> dict:
        file_id = f"fixture-gridfs-{len(self._files) + 1}"
        self._files[file_id] = bytes(data)
        return {"storage_file_id": file_id, "stored_name": name, "stored_size": len(data)}

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

    gridfs = _FakeGridFS()
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
            gridfs=gridfs,
            storage_backend="gridfs",
        )
        assert outcome.get("ok") and not outcome.get("duplicate"), outcome

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
