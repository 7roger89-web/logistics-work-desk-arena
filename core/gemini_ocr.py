"""Bounded Gemini image-to-Markdown OCR client for the Logistics work desk.

The capability is deliberately narrow:

    image bytes -> Gemini multimodal generate_content -> verbatim Markdown text

It is NOT a document store, search engine, translator, normalization layer or
business-data importer. Image bytes are validated in memory and are never
persisted by this module. Credentials stay server-side through core.config.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from google import genai
from google.genai import types

from core.config import GEMINI_API_KEY, get_setting

LOGGER = logging.getLogger("logistics_pro.gemini_ocr")

PROVIDER_LABEL = "Google Gemini"
DEFAULT_MODEL = "gemini-3.8-flash"
MODEL = get_setting(
    "GEMINI_OCR_MODEL",
    ("gemini", "ocr_model"),
    "GEMINI_OCR_MODEL",
    default=DEFAULT_MODEL,
).strip() or DEFAULT_MODEL

# Deliberately below Google's current inline-request ceiling. One screenshot or
# document photo is enough for the V1 workflow; multi-image batching is deferred.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_MIME_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})

OCR_PROMPT = """Trích xuất 100% nguyên văn toàn bộ nội dung chữ nhìn thấy trong ảnh.
Không giải thích gì thêm.
Không tóm tắt.
Không dịch.
Không sửa chính tả.
Không suy luận hoặc bổ sung nội dung không nhìn thấy.
Giữ thứ tự đọc, xuống dòng, tiêu đề, danh sách và bảng sát ảnh gốc nhất có thể.
Chỉ trả về Markdown có thể copy trực tiếp, không thêm lời mở đầu hoặc kết luận."""

NO_API_KEY_MESSAGE = (
    "Gemini OCR chưa được cấu hình. Thêm GEMINI_API_KEY hoặc [gemini].api_key "
    "vào secrets của ứng dụng."
)
EMPTY_IMAGE_MESSAGE = "Chưa có ảnh để trích xuất."
UNSUPPORTED_IMAGE_MESSAGE = "Định dạng ảnh chưa hỗ trợ. Hãy dùng PNG, JPEG hoặc WEBP."
OVERSIZED_IMAGE_MESSAGE = "Ảnh vượt quá giới hạn 10 MB của công cụ OCR."
EMPTY_RESPONSE_MESSAGE = "Gemini không trả về nội dung chữ cho ảnh này."
PROVIDER_ERROR_MESSAGE = "Gemini OCR không thể xử lý ảnh lúc này."

STATUS_EXTRACTED = "extracted"
STATUS_INVALID = "invalid"
STATUS_CONFIG_REQUIRED = "config_required"
STATUS_ERROR = "error"


@dataclass(frozen=True)
class OcrResult:
    status: str
    text: str | None
    error: str | None
    provider: str
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "text": self.text,
            "error": self.error,
            "provider": self.provider,
            "model": self.model,
        }


def _strip_outer_markdown_fence(text: str) -> str:
    """Remove only one whole-response Markdown fence; preserve inner content."""
    value = str(text or "").strip()
    lines = value.splitlines()
    if len(lines) >= 2 and lines[0].strip().casefold() in {"```markdown", "```md", "```"}:
        if lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return value


def _invalid(message: str, *, model: str) -> OcrResult:
    return OcrResult(
        status=STATUS_INVALID,
        text=None,
        error=message,
        provider=PROVIDER_LABEL,
        model=model,
    )


def extract_markdown(
    image_bytes: bytes,
    *,
    mime_type: str,
    api_key: str | None = None,
    model: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Extract visible image text as Markdown with no semantic rewriting."""
    active_model = str(model or MODEL).strip() or DEFAULT_MODEL
    raw = bytes(image_bytes or b"")
    mime = str(mime_type or "").strip().lower()

    if not raw:
        return _invalid(EMPTY_IMAGE_MESSAGE, model=active_model).to_dict()
    if mime not in SUPPORTED_MIME_TYPES:
        return _invalid(UNSUPPORTED_IMAGE_MESSAGE, model=active_model).to_dict()
    if len(raw) > MAX_IMAGE_BYTES:
        return _invalid(OVERSIZED_IMAGE_MESSAGE, model=active_model).to_dict()

    key = str(GEMINI_API_KEY if api_key is None else api_key).strip()
    if client is None and not key:
        return OcrResult(
            status=STATUS_CONFIG_REQUIRED,
            text=None,
            error=NO_API_KEY_MESSAGE,
            provider=PROVIDER_LABEL,
            model=active_model,
        ).to_dict()

    active = client if client is not None else genai.Client(api_key=key)
    try:
        response = active.models.generate_content(
            model=active_model,
            contents=[
                OCR_PROMPT,
                types.Part.from_bytes(data=raw, mime_type=mime),
            ],
            config=types.GenerateContentConfig(temperature=0),
        )
        text = _strip_outer_markdown_fence(getattr(response, "text", "") or "")
        if not text:
            return OcrResult(
                status=STATUS_ERROR,
                text=None,
                error=EMPTY_RESPONSE_MESSAGE,
                provider=PROVIDER_LABEL,
                model=active_model,
            ).to_dict()
        return OcrResult(
            status=STATUS_EXTRACTED,
            text=text,
            error=None,
            provider=PROVIDER_LABEL,
            model=active_model,
        ).to_dict()
    except Exception:  # noqa: BLE001 - provider details/key must never reach UI
        LOGGER.warning("Gemini OCR provider request failed", exc_info=False)
        return OcrResult(
            status=STATUS_ERROR,
            text=None,
            error=PROVIDER_ERROR_MESSAGE,
            provider=PROVIDER_LABEL,
            model=active_model,
        ).to_dict()


__all__ = [
    "DEFAULT_MODEL",
    "EMPTY_IMAGE_MESSAGE",
    "MAX_IMAGE_BYTES",
    "MODEL",
    "NO_API_KEY_MESSAGE",
    "OCR_PROMPT",
    "OVERSIZED_IMAGE_MESSAGE",
    "PROVIDER_ERROR_MESSAGE",
    "PROVIDER_LABEL",
    "STATUS_CONFIG_REQUIRED",
    "STATUS_ERROR",
    "STATUS_EXTRACTED",
    "STATUS_INVALID",
    "SUPPORTED_MIME_TYPES",
    "UNSUPPORTED_IMAGE_MESSAGE",
    "extract_markdown",
]
