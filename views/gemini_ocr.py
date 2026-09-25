"""Presentation adapter for the bounded Gemini OCR workspace."""
from __future__ import annotations

from typing import Any

from core import gemini_ocr


PRIVACY_NOTICE = (
    "Ảnh được gửi tới Google Gemini để trích xuất chữ. Ảnh không được công cụ "
    "OCR này tự lưu vào MongoDB, GridFS hay hồ sơ lô hàng. Không dùng ảnh chứa "
    "nội dung chưa được phép chia sẻ với nhà cung cấp bên ngoài."
)
CONFIG_REQUIRED_NOTICE = "Gemini OCR chưa được cấu hình"


def ocr_capability(*, api_key: str | None = None) -> dict[str, Any]:
    key = gemini_ocr.GEMINI_API_KEY if api_key is None else str(api_key or "")
    configured = bool(str(key).strip())
    return {
        "provider": gemini_ocr.PROVIDER_LABEL,
        "model": gemini_ocr.MODEL,
        "configured": configured,
        "externalProvider": True,
        "privacyNotice": PRIVACY_NOTICE,
        "configNotice": None if configured else CONFIG_REQUIRED_NOTICE,
        "maxImageBytes": gemini_ocr.MAX_IMAGE_BYTES,
        "acceptedMimeTypes": sorted(gemini_ocr.SUPPORTED_MIME_TYPES),
    }


def run_ocr(
    image_bytes: bytes,
    *,
    mime_type: str,
    client: Any | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    return gemini_ocr.extract_markdown(
        image_bytes,
        mime_type=mime_type,
        client=client,
        api_key=api_key,
        model=model,
    )


def ocr_view(request: Any = None, result: Any = None) -> dict[str, Any]:
    return {
        "capability": ocr_capability(),
        "request": request if isinstance(request, dict) else None,
        "result": result if isinstance(result, dict) else None,
    }


__all__ = [
    "CONFIG_REQUIRED_NOTICE",
    "PRIVACY_NOTICE",
    "ocr_capability",
    "ocr_view",
    "run_ocr",
]
