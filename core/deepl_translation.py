"""Small server-side DeepL text translation client.

The client deliberately owns only the V1 text-translation boundary.  It keeps
authorized key state in memory, retries finitely, and exposes API indices and
usage metadata without exposing credential material.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import logging
import time
from typing import Any

import requests

from core.config import DEEPL_API_KEYS


LOGGER = logging.getLogger("logistics_pro.deepl")

DEEPL_FREE_API_BASE = "https://api-free.deepl.com"
DEEPL_API_BASE = "https://api.deepl.com"
DEEPL_TRANSLATE_PATH = "/v2/translate"
DEEPL_USAGE_PATH = "/v2/usage"

MAX_TEXT_BYTES = 100_000
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RATE_LIMIT_RETRIES = 2
DEFAULT_MAX_TRANSIENT_RETRIES = 2
DEFAULT_BACKOFF_BASE_SECONDS = 0.5

NO_API_KEYS_MESSAGE = (
    "Chưa cấu hình API DeepL. Thêm [deepl].api_keys hoặc DEEPL_API_KEYS "
    "vào secrets local."
)
ALL_KEYS_UNAVAILABLE_MESSAGE = "Tất cả API DeepL hiện đã hết hạn mức hoặc không khả dụng."
EMPTY_TEXT_MESSAGE = "Vui lòng nhập nội dung cần dịch."
OVERSIZED_TEXT_MESSAGE = (
    "Nội dung quá lớn cho một yêu cầu DeepL. Hãy rút gọn văn bản rồi thử lại."
)
INVALID_TRANSLATION_RESPONSE_MESSAGE = "DeepL trả về phản hồi dịch không hợp lệ."
INVALID_LANGUAGE_MESSAGE = "Ngôn ngữ dịch chưa được hỗ trợ trong phiên bản V1."
PROVIDER_REQUEST_ERROR_MESSAGE = "DeepL không thể xử lý yêu cầu lúc này."

AUTO_DETECT_SOURCE = "AUTO"
SUPPORTED_SOURCE_LANGUAGES = frozenset({AUTO_DETECT_SOURCE, "ZH", "VI", "EN"})
SUPPORTED_TARGET_LANGUAGES = frozenset({"VI", "ZH-HANS", "ZH-HANT", "EN"})

DEFAULT_LOGISTICS_CONTEXT = (
    "International logistics, freight forwarding, customs clearance, "
    "China–Vietnam road transport, import-export documentation, commercial contracts."
)

RequestFn = Callable[..., requests.Response]
SleepFn = Callable[[float], None]


class DeepLTranslationError(RuntimeError):
    """Safe user-facing error that never contains a credential or raw body."""


@dataclass(frozen=True)
class TranslationResult:
    """A translated text plus safe provider metadata."""

    translated_text: str
    detected_source_language: str | None
    billed_characters: int | None
    api_index: int
    api_count: int

    @property
    def api_label(self) -> str:
        return f"API {self.api_index}/{self.api_count}"


@dataclass(frozen=True)
class UsageRow:
    """Index-only usage status for one configured key."""

    api_index: int
    api_count: int
    status: str
    character_count: int | None = None
    character_limit: int | None = None
    characters_remaining: int | None = None

    @property
    def api_label(self) -> str:
        return f"API {self.api_index}/{self.api_count}"

    def to_display_dict(self) -> dict[str, str]:
        """Return a UI-safe row with no credential field."""
        return {
            "API": str(self.api_index),
            "Trạng thái": self.status,
            "Đã dùng": _display_number(self.character_count),
            "Giới hạn": _display_number(self.character_limit),
            "Còn lại": _display_number(self.characters_remaining),
        }


@dataclass
class _KeyState:
    # repr=False is an additional guard against accidental debug output.
    key: str = field(repr=False)
    exhausted: bool = False
    invalid: bool = False


class DeepLKeyPool:
    """Deterministic in-memory state for the configured DeepL key order."""

    def __init__(self, api_keys: Sequence[str], preferred_index: int = 0) -> None:
        cleaned: list[str] = []
        for raw_key in api_keys:
            key = str(raw_key or "").strip()
            if key and key not in cleaned:
                cleaned.append(key)
        self._states = [_KeyState(key=key) for key in cleaned]
        self.preferred_index = (
            preferred_index % len(self._states) if self._states else 0
        )

    def __repr__(self) -> str:
        return (
            f"DeepLKeyPool(api_count={self.api_count}, "
            f"preferred_index={self.preferred_index + 1 if self._states else 0})"
        )

    @property
    def api_count(self) -> int:
        return len(self._states)

    def available_indices(self) -> tuple[int, ...]:
        if not self._states:
            return ()
        ordered = [
            (self.preferred_index + offset) % len(self._states)
            for offset in range(len(self._states))
        ]
        return tuple(
            index
            for index in ordered
            if not self._states[index].exhausted and not self._states[index].invalid
        )

    def key_for(self, index: int) -> str:
        """Return a key only to the internal request boundary."""
        return self._states[index].key

    def endpoint_for(self, index: int) -> str:
        return endpoint_for_key(self.key_for(index))

    def mark_exhausted(self, index: int) -> None:
        self._states[index].exhausted = True

    def mark_invalid(self, index: int) -> None:
        self._states[index].invalid = True

    def mark_success(self, index: int) -> None:
        self.preferred_index = index

    def is_exhausted(self, index: int) -> bool:
        return self._states[index].exhausted

    def is_invalid(self, index: int) -> bool:
        return self._states[index].invalid


def endpoint_for_key(api_key: str) -> str:
    """Infer the DeepL endpoint without returning or logging the key."""
    if str(api_key or "").casefold().endswith(":fx"):
        return DEEPL_FREE_API_BASE
    return DEEPL_API_BASE


class DeepLClient:
    """Bounded DeepL V2 client for text translation and explicit usage checks."""

    def __init__(
        self,
        api_keys: Sequence[str] | None = None,
        *,
        request_fn: RequestFn | None = None,
        sleep_fn: SleepFn | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_rate_limit_retries: int = DEFAULT_MAX_RATE_LIMIT_RETRIES,
        max_transient_retries: int = DEFAULT_MAX_TRANSIENT_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_rate_limit_retries < 0 or max_transient_retries < 0:
            raise ValueError("retry counts must not be negative")
        if backoff_base_seconds < 0:
            raise ValueError("backoff_base_seconds must not be negative")

        self._pool = DeepLKeyPool(DEEPL_API_KEYS if api_keys is None else api_keys)
        self._request_fn = request_fn or requests.request
        self._sleep_fn = sleep_fn or time.sleep
        self._timeout_seconds = float(timeout_seconds)
        self._max_rate_limit_retries = int(max_rate_limit_retries)
        self._max_transient_retries = int(max_transient_retries)
        self._backoff_base_seconds = float(backoff_base_seconds)

    @property
    def api_count(self) -> int:
        return self._pool.api_count

    @property
    def preferred_api_index(self) -> int | None:
        if not self.api_count:
            return None
        return self._pool.preferred_index + 1

    def translate(
        self,
        text: str,
        *,
        source_lang: str | None = None,
        target_lang: str,
        context: str = "",
        preserve_formatting: bool = True,
        show_billed_characters: bool = True,
    ) -> TranslationResult:
        """Translate one text with finite retries and deterministic failover."""
        self._require_keys()
        clean_text = _validate_text(text, context)
        source_code = _normalize_source_language(source_lang)
        target_code = _normalize_target_language(target_lang)
        clean_context = str(context or "").strip()

        payload: dict[str, Any] = {
            "text": [clean_text],
            "target_lang": target_code,
            "preserve_formatting": bool(preserve_formatting),
        }
        if source_code is not None:
            payload["source_lang"] = source_code
        if clean_context:
            payload["context"] = clean_context
        if show_billed_characters:
            payload["show_billed_characters"] = True

        for index in self._pool.available_indices():
            response = self._request_with_retries(
                index,
                method="POST",
                path=DEEPL_TRANSLATE_PATH,
                payload=payload,
            )
            if response is None:
                continue

            status_code = _status_code(response)
            if status_code == 200:
                result = _parse_translation_response(
                    response,
                    api_index=index + 1,
                    api_count=self.api_count,
                )
                self._pool.mark_success(index)
                return result
            if status_code == 456:
                self._pool.mark_exhausted(index)
                LOGGER.warning("DeepL API %s/%s exhausted", index + 1, self.api_count)
                continue
            if status_code in {401, 403}:
                self._pool.mark_invalid(index)
                LOGGER.warning("DeepL API %s/%s unavailable", index + 1, self.api_count)
                continue
            if status_code == 429 or _is_server_error(status_code):
                LOGGER.warning(
                    "DeepL API %s/%s remained unavailable after bounded retry",
                    index + 1,
                    self.api_count,
                )
                continue
            raise DeepLTranslationError(_safe_translation_status_message(status_code))

        raise DeepLTranslationError(ALL_KEYS_UNAVAILABLE_MESSAGE)

    def check_usage(self) -> list[UsageRow]:
        """Query each configured key only when the caller explicitly asks."""
        self._require_keys()
        rows: list[UsageRow] = []
        for index in range(self.api_count):
            response = self._request_with_retries(
                index,
                method="GET",
                path=DEEPL_USAGE_PATH,
            )
            rows.append(self._usage_row_from_response(index, response))
        return rows

    def _usage_row_from_response(
        self,
        index: int,
        response: requests.Response | None,
    ) -> UsageRow:
        base = {"api_index": index + 1, "api_count": self.api_count}
        if response is None:
            return UsageRow(**base, status="Không khả dụng")

        status_code = _status_code(response)
        if status_code == 200:
            payload = _json_object(response)
            if payload is None:
                return UsageRow(**base, status="Không rõ")
            character_count = _usage_number(payload, "character_count")
            character_limit = _usage_number(payload, "character_limit")
            remaining = (
                max(character_limit - character_count, 0)
                if character_count is not None and character_limit is not None
                else None
            )
            status = (
                "Hết quota"
                if remaining == 0 and character_limit is not None
                else "Sẵn sàng"
            )
            return UsageRow(
                **base,
                status=status,
                character_count=character_count,
                character_limit=character_limit,
                characters_remaining=remaining,
            )
        if status_code == 456:
            self._pool.mark_exhausted(index)
            return UsageRow(**base, status="Hết quota")
        if status_code in {401, 403}:
            self._pool.mark_invalid(index)
            return UsageRow(**base, status="Không khả dụng")
        if status_code == 429:
            return UsageRow(**base, status="Đang giới hạn")
        return UsageRow(**base, status="Không khả dụng")

    def _request_with_retries(
        self,
        index: int,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> requests.Response | None:
        rate_limit_retries = 0
        transient_retries = 0
        while True:
            try:
                response = self._send_request(index, method, path, payload)
            except requests.RequestException:
                if transient_retries >= self._max_transient_retries:
                    LOGGER.warning(
                        "DeepL API %s/%s network failure after bounded retry",
                        index + 1,
                        self.api_count,
                    )
                    return None
                self._wait(transient_retries)
                transient_retries += 1
                continue

            status_code = _status_code(response)
            if status_code == 429 and rate_limit_retries < self._max_rate_limit_retries:
                self._wait(rate_limit_retries)
                rate_limit_retries += 1
                continue
            if _is_server_error(status_code) and transient_retries < self._max_transient_retries:
                self._wait(transient_retries)
                transient_retries += 1
                continue
            return response

    def _send_request(
        self,
        index: int,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
    ) -> requests.Response:
        kwargs: dict[str, Any] = {
            "headers": {
                "Authorization": f"DeepL-Auth-Key {self._pool.key_for(index)}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            "timeout": self._timeout_seconds,
        }
        if payload is not None:
            kwargs["json"] = payload
        return self._request_fn(
            method,
            f"{self._pool.endpoint_for(index)}{path}",
            **kwargs,
        )

    def _wait(self, retry_number: int) -> None:
        self._sleep_fn(self._backoff_base_seconds * (2**retry_number))

    def _require_keys(self) -> None:
        if not self.api_count:
            raise DeepLTranslationError(NO_API_KEYS_MESSAGE)


def _validate_text(text: str, context: str) -> str:
    clean_text = str(text or "").strip()
    if not clean_text:
        raise DeepLTranslationError(EMPTY_TEXT_MESSAGE)
    clean_context = str(context or "").strip()
    request_bytes = len(clean_text.encode("utf-8")) + len(clean_context.encode("utf-8"))
    if request_bytes > MAX_TEXT_BYTES:
        raise DeepLTranslationError(OVERSIZED_TEXT_MESSAGE)
    return clean_text


def _normalize_source_language(source_lang: str | None) -> str | None:
    code = str(source_lang or AUTO_DETECT_SOURCE).strip().upper()
    if code in {"", AUTO_DETECT_SOURCE}:
        return None
    if code not in SUPPORTED_SOURCE_LANGUAGES:
        raise DeepLTranslationError(INVALID_LANGUAGE_MESSAGE)
    return code


def _normalize_target_language(target_lang: str) -> str:
    code = str(target_lang or "").strip().upper()
    if code not in SUPPORTED_TARGET_LANGUAGES:
        raise DeepLTranslationError(INVALID_LANGUAGE_MESSAGE)
    return code


def _status_code(response: requests.Response) -> int | None:
    try:
        return int(getattr(response, "status_code", 0))
    except (TypeError, ValueError):
        return None


def _is_server_error(status_code: int | None) -> bool:
    return status_code is not None and 500 <= status_code <= 599


def _parse_translation_response(
    response: requests.Response,
    *,
    api_index: int,
    api_count: int,
) -> TranslationResult:
    payload = _json_object(response)
    translations = payload.get("translations") if payload else None
    if not isinstance(translations, list) or not translations or not isinstance(translations[0], dict):
        raise DeepLTranslationError(INVALID_TRANSLATION_RESPONSE_MESSAGE)
    item = translations[0]
    translated_text = item.get("text")
    if not isinstance(translated_text, str):
        raise DeepLTranslationError(INVALID_TRANSLATION_RESPONSE_MESSAGE)
    detected = item.get("detected_source_language")
    detected_language = str(detected).upper() if detected not in (None, "") else None
    billed_characters = _optional_int(item.get("billed_characters"))
    return TranslationResult(
        translated_text=translated_text,
        detected_source_language=detected_language,
        billed_characters=billed_characters,
        api_index=api_index,
        api_count=api_count,
    )


def _json_object(response: requests.Response) -> dict[str, Any] | None:
    try:
        payload = response.json()
    except (TypeError, ValueError, AttributeError):
        return None
    return payload if isinstance(payload, dict) else None


def _usage_number(payload: dict[str, Any], name: str) -> int | None:
    candidate_maps: list[dict[str, Any]] = [payload]
    for nested_name in ("usage", "subscription", "api_usage"):
        nested = payload.get(nested_name)
        if isinstance(nested, dict):
            candidate_maps.append(nested)
    for candidate in candidate_maps:
        if name in candidate:
            return _optional_int(candidate.get(name))
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _display_number(value: int | None) -> str:
    return f"{value:,}" if value is not None else "—"


def _safe_translation_status_message(status_code: int | None) -> str:
    if status_code in {400, 413, 414}:
        return "DeepL từ chối nội dung hoặc tham số của yêu cầu."
    if status_code is None:
        return PROVIDER_REQUEST_ERROR_MESSAGE
    return PROVIDER_REQUEST_ERROR_MESSAGE


__all__ = [
    "ALL_KEYS_UNAVAILABLE_MESSAGE",
    "AUTO_DETECT_SOURCE",
    "DEFAULT_LOGISTICS_CONTEXT",
    "DEEPL_API_BASE",
    "DEEPL_FREE_API_BASE",
    "DEEPL_TRANSLATE_PATH",
    "DEEPL_USAGE_PATH",
    "DeepLClient",
    "DeepLKeyPool",
    "DeepLTranslationError",
    "MAX_TEXT_BYTES",
    "NO_API_KEYS_MESSAGE",
    "SUPPORTED_SOURCE_LANGUAGES",
    "SUPPORTED_TARGET_LANGUAGES",
    "TranslationResult",
    "UsageRow",
    "endpoint_for_key",
]
