"""Owner-facing DeepL text translation view.

Two surfaces live in this ONE module (no second translation service):

1. ``ui_translation`` — the original Streamlit page (unchanged).
2. ``translation_capability`` / ``run_translation`` / ``translation_view`` —
   the bounded presentation layer (LOGI_TRANSLATION_WORKSPACE_01) that exposes
   the SAME existing capability to the Logi-good component route
   ``/dich-thuat``. It adds no provider, no engine and no configuration
   mechanism: it wraps ``core.deepl_translation.DeepLClient`` and shapes its
   answer for the view-model.

PRIVACY BOUNDARY (truthful by construction): the text IS sent to DeepL, an
external third-party provider. Nothing here is a local/private translator, so
the view-model always carries that disclosure and the UI must show it.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import streamlit as st

from core.config import DEEPL_API_KEYS
from core.deepl_translation import (
    AUTO_DETECT_SOURCE,
    DEFAULT_LOGISTICS_CONTEXT,
    DeepLClient,
    DeepLTranslationError,
    EMPTY_TEXT_MESSAGE,
    INVALID_LANGUAGE_MESSAGE,
    MAX_TEXT_BYTES,
    NO_API_KEYS_MESSAGE,
    OVERSIZED_TEXT_MESSAGE,
    PROVIDER_REQUEST_ERROR_MESSAGE,
    SUPPORTED_SOURCE_LANGUAGES,
    SUPPORTED_TARGET_LANGUAGES,
    TranslationResult,
    UsageRow,
)


LOGGER = logging.getLogger("logistics_pro.ui.translation")

SOURCE_LANGUAGE_LABELS: dict[str, str] = {
    "AUTO": "Tự động phát hiện",
    "ZH": "中文",
    "VI": "Tiếng Việt",
    "EN": "English",
}
TARGET_LANGUAGE_LABELS: dict[str, str] = {
    "VI": "Tiếng Việt",
    "ZH-HANS": "简体中文",
    "ZH-HANT": "繁體中文",
    "EN": "English",
}

_TARGET_TO_SOURCE = {
    "VI": "VI",
    "ZH-HANS": "ZH",
    "ZH-HANT": "ZH",
    "EN": "EN",
}
_SOURCE_TO_TARGET = {
    "ZH": "ZH-HANS",
    "VI": "VI",
    "EN": "EN",
}


def _get_client(api_keys: Sequence[str] | None = None) -> DeepLClient:
    """The ONE session-cached DeepL client (key material never leaves it)."""
    keys = DEEPL_API_KEYS if api_keys is None else [str(key) for key in api_keys]
    try:
        client = st.session_state.get("deepl_client")
    except Exception:  # noqa: BLE001 - outside a Streamlit script run
        client = None
    if client is None or getattr(client, "api_count", None) != len(keys):
        client = DeepLClient(keys)
        try:
            st.session_state.deepl_client = client
        except Exception:  # noqa: BLE001 - non-Streamlit context (tests/scripts)
            pass
    return client


def _swap_languages() -> None:
    source_code = str(st.session_state.get("deepl_source_language", "AUTO"))
    target_code = str(st.session_state.get("deepl_target_language", "VI"))
    st.session_state.deepl_source_language = _TARGET_TO_SOURCE.get(target_code, "VI")
    st.session_state.deepl_target_language = _SOURCE_TO_TARGET.get(
        source_code,
        "ZH-HANS",
    )


def _format_count(value: int | None) -> str:
    return f"{value:,}" if value is not None else "—"


def _render_result(result: TranslationResult) -> None:
    st.markdown("### Kết quả dịch")
    st.text_area(
        "Bản dịch",
        key="deepl_result_text",
        height=230,
        label_visibility="collapsed",
    )
    detected = result.detected_source_language or "—"
    billed = _format_count(result.billed_characters)
    st.caption(
        f"Ngôn ngữ nguồn phát hiện: {detected} · "
        f"Ký tự tính phí: {billed} · "
        f"Đang dùng API {result.api_index}/{result.api_count}"
    )


def _render_usage(rows: list[UsageRow]) -> None:
    if not rows:
        return
    st.markdown("### Hạn mức API")
    st.dataframe(
        [row.to_display_dict() for row in rows],
        use_container_width=True,
        hide_index=True,
    )


def ui_translation() -> None:
    """Render the bounded DeepL text-only workflow."""
    st.title("🌐 Dịch Thuật DeepL")
    st.caption(
        "Dịch văn bản nghiệp vụ logistics qua DeepL. API key chỉ được dùng "
        "ở backend và không hiển thị trên giao diện."
    )
    st.markdown(
        """
        <style>
        [data-testid="stTextArea"] textarea { min-height: 160px; }
        @media (max-width: 720px) {
            [data-testid="stHorizontalBlock"] { gap: 0.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    client = _get_client()
    if client.api_count == 0:
        st.warning(NO_API_KEYS_MESSAGE)
        st.info("Cấu hình key local rồi khởi động lại Streamlit để sử dụng công cụ.")
        return

    if "deepl_source_language" not in st.session_state:
        st.session_state.deepl_source_language = "AUTO"
    if "deepl_target_language" not in st.session_state:
        st.session_state.deepl_target_language = "VI"
    if "deepl_context_enabled" not in st.session_state:
        st.session_state.deepl_context_enabled = True
    if "deepl_context" not in st.session_state:
        st.session_state.deepl_context = DEFAULT_LOGISTICS_CONTEXT

    source_col, swap_col, target_col = st.columns([4, 1, 4])
    with source_col:
        st.selectbox(
            "Ngôn ngữ nguồn",
            options=list(SOURCE_LANGUAGE_LABELS),
            format_func=SOURCE_LANGUAGE_LABELS.__getitem__,
            key="deepl_source_language",
        )
    with swap_col:
        st.write("")
        st.button(
            "⇄",
            key="deepl_swap_button",
            help="Đổi chiều dịch",
            use_container_width=True,
            on_click=_swap_languages,
        )
    with target_col:
        st.selectbox(
            "Ngôn ngữ đích",
            options=list(TARGET_LANGUAGE_LABELS),
            format_func=TARGET_LANGUAGE_LABELS.__getitem__,
            key="deepl_target_language",
        )

    source_text = st.text_area(
        "Văn bản nguồn",
        placeholder="Dán nội dung cần dịch tại đây...",
        height=230,
        key="deepl_source_text",
    )
    source_bytes = len(str(source_text or "").encode("utf-8"))
    st.caption(f"Kích thước văn bản: {source_bytes:,} / {MAX_TEXT_BYTES:,} bytes")

    use_context = st.checkbox(
        "Thêm ngữ cảnh logistics",
        key="deepl_context_enabled",
    )
    context = st.text_area(
        "Ngữ cảnh tùy chọn",
        height=105,
        key="deepl_context",
        disabled=not use_context,
    )

    translate_clicked = st.button(
        "DỊCH",
        type="primary",
        use_container_width=True,
        key="deepl_translate_button",
    )
    if translate_clicked:
        try:
            with st.spinner("Đang dịch qua DeepL..."):
                result = client.translate(
                    source_text,
                    source_lang=st.session_state.deepl_source_language,
                    target_lang=st.session_state.deepl_target_language,
                    context=context if use_context else "",
                )
            st.session_state.deepl_translation_result = result
            st.session_state.deepl_result_text = result.translated_text
        except DeepLTranslationError as exc:
            st.session_state.pop("deepl_translation_result", None)
            st.error(str(exc))
        except Exception:  # noqa: BLE001
            # Never render or log arbitrary provider/request exception text.
            st.session_state.pop("deepl_translation_result", None)
            LOGGER.error("DeepL translation view failed")
            st.error("Không thể dịch nội dung lúc này. Vui lòng thử lại.")

    result = st.session_state.get("deepl_translation_result")
    if isinstance(result, TranslationResult):
        _render_result(result)

    st.divider()
    usage_clicked = st.button(
        "Kiểm tra hạn mức API",
        use_container_width=True,
        key="deepl_usage_button",
    )
    if usage_clicked:
        try:
            with st.spinner("Đang kiểm tra hạn mức từng API..."):
                st.session_state.deepl_usage_rows = client.check_usage()
        except DeepLTranslationError as exc:
            st.error(str(exc))
        except Exception:  # noqa: BLE001
            LOGGER.error("DeepL usage view failed")
            st.error("Không thể kiểm tra hạn mức lúc này. Vui lòng thử lại.")

    rows = st.session_state.get("deepl_usage_rows", [])
    if isinstance(rows, list):
        _render_usage([row for row in rows if isinstance(row, UsageRow)])


# ---------------------------------------------------------------------------
# LOGI_TRANSLATION_WORKSPACE_01 — bounded view-model slice for /dich-thuat
#
# Presentation adapter ONLY. The translation itself is performed by the
# EXISTING canonical client (``core.deepl_translation.DeepLClient``) with the
# EXISTING configuration mechanism (``core.config.DEEPL_API_KEYS``). No new
# provider, engine, secret manager, store or API is introduced here.
# ---------------------------------------------------------------------------

PROVIDER_LABEL = "DeepL"

#: What this capability actually is: an external third-party API. The UI must
#: say so — this workspace is never a local/private translator.
PRIVACY_NOTICE = (
    "Văn bản bạn nhập được gửi tới DeepL (nhà cung cấp dịch vụ bên thứ ba) để "
    "dịch, kèm ngữ cảnh nghiệp vụ logistics mặc định của hệ thống. Đây KHÔNG "
    "phải bộ dịch chạy cục bộ: đừng dán nội dung mật hoặc nội dung chưa được "
    "phép chia sẻ ra ngoài. API key chỉ nằm ở backend và không bao giờ được "
    "đưa xuống trình duyệt."
)

#: Honest PARTIAL_BACKED state when the existing configuration carries no key.
CONFIG_REQUIRED_NOTICE = "Translation service chưa được cấu hình"

#: Shown when one intent already has an authoritative translation.
DUPLICATE_TRANSLATION_MESSAGE = (
    "Nội dung và cặp ngôn ngữ giống hệt lần dịch trước — bản dịch đang hiển "
    "thị vẫn đúng, nên hệ thống không gọi lại DeepL."
)

#: The only status that carries translated text.
STATUS_TRANSLATED = "translated"
STATUS_INVALID = "invalid"
STATUS_ERROR = "error"
STATUS_CONFIG_REQUIRED = "config_required"

_VALIDATION_MESSAGES = frozenset({
    EMPTY_TEXT_MESSAGE,
    INVALID_LANGUAGE_MESSAGE,
    OVERSIZED_TEXT_MESSAGE,
})


def _permission_allowed() -> bool:
    """The EXISTING RBAC answer for the translation capability (never raises)."""
    try:
        from core.auth import has_permission

        return bool(has_permission("translation"))
    except Exception:  # noqa: BLE001 - outside a Streamlit script run
        return False


def translation_capability(
    api_keys: Sequence[str] | None = None,
    allowed: bool | None = None,
) -> dict[str, Any]:
    """What /dich-thuat may truthfully offer — derived from the backend only.

    Language choices are filtered by ``core.deepl_translation``'s own supported
    sets, so the UI can never offer a pair the provider does not accept. No
    credential material is included: only WHETHER keys exist and HOW MANY.
    """
    keys = DEEPL_API_KEYS if api_keys is None else [str(key) for key in api_keys]
    configured = len(keys) > 0
    return {
        "provider": PROVIDER_LABEL,
        "configured": configured,
        "apiCount": len(keys),
        "allowed": bool(_permission_allowed() if allowed is None else allowed),
        # DeepL detects the source language itself (the existing AUTO source).
        "autoDetectSupported": AUTO_DETECT_SOURCE in SUPPORTED_SOURCE_LANGUAGES,
        "sourceLanguages": [
            {"code": code, "label": SOURCE_LANGUAGE_LABELS[code]}
            for code in SOURCE_LANGUAGE_LABELS
            if code in SUPPORTED_SOURCE_LANGUAGES
        ],
        "targetLanguages": [
            {"code": code, "label": TARGET_LANGUAGE_LABELS[code]}
            for code in TARGET_LANGUAGE_LABELS
            if code in SUPPORTED_TARGET_LANGUAGES
        ],
        "maxTextBytes": MAX_TEXT_BYTES,
        "logisticsContext": bool(DEFAULT_LOGISTICS_CONTEXT),
        "externalProvider": True,
        "privacyNotice": PRIVACY_NOTICE,
        "configNotice": (
            None if configured else f"{CONFIG_REQUIRED_NOTICE}. {NO_API_KEYS_MESSAGE}"
        ),
        # Direction-swap maps are the EXISTING Streamlit view's own mapping,
        # served as data so the component does not invent a second one.
        "swapSource": dict(_TARGET_TO_SOURCE),
        "swapTarget": {**_SOURCE_TO_TARGET, AUTO_DETECT_SOURCE: "ZH-HANS"},
    }


def run_translation(
    text: Any,
    *,
    source_lang: Any,
    target_lang: Any,
    client: DeepLClient | None = None,
    api_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """ONE bounded translation through the EXISTING DeepL client.

    Returns a JSON-safe result dict; it never raises and never leaks a key or a
    raw provider body. The translated text is passed through VERBATIM — line
    breaks, numbers, HS codes, shipment IDs and invoice references stay exactly
    as the provider returned them (no cosmetic reformatting, no identifier
    rewriting).
    """
    base_error: dict[str, Any] = {
        "text": None,
        "detectedSourceLanguage": None,
        "billedCharacters": None,
        "apiLabel": None,
        "provider": PROVIDER_LABEL,
    }
    try:
        active = client if client is not None else _get_client(api_keys)
        result = active.translate(
            str(text or ""),
            source_lang=str(source_lang or AUTO_DETECT_SOURCE),
            target_lang=str(target_lang or ""),
            context=DEFAULT_LOGISTICS_CONTEXT,
        )
    except DeepLTranslationError as exc:
        message = str(exc)
        if message == NO_API_KEYS_MESSAGE:
            status = STATUS_CONFIG_REQUIRED
        elif message in _VALIDATION_MESSAGES:
            status = STATUS_INVALID
        else:
            status = STATUS_ERROR
        return {"status": status, "error": message, **base_error}
    except Exception:  # noqa: BLE001 - one provider failure must not break the app
        # Never render or log arbitrary provider/request exception text.
        LOGGER.error("DeepL translation failed")
        return {
            "status": STATUS_ERROR,
            "error": PROVIDER_REQUEST_ERROR_MESSAGE,
            **base_error,
        }
    return {
        "status": STATUS_TRANSLATED,
        "text": result.translated_text,
        "error": None,
        "detectedSourceLanguage": result.detected_source_language,
        "billedCharacters": result.billed_characters,
        "apiLabel": result.api_label,
        "provider": PROVIDER_LABEL,
    }


def translation_view(
    request: Any = None,
    result: Any = None,
    api_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """The bounded ``/dich-thuat`` slice: capability + last request + result.

    ``request``/``result`` are the session readback stored by the ONE bounded
    dispatcher (``views.logi_view_model.consume_translation_triggers``); both
    stay ``None`` until the user actually asks for a translation, so the UI has
    an honest idle state instead of a fabricated one.
    """
    return {
        "capability": translation_capability(api_keys),
        "request": request if isinstance(request, dict) else None,
        "result": result if isinstance(result, dict) else None,
    }


__all__ = [
    "CONFIG_REQUIRED_NOTICE",
    "DUPLICATE_TRANSLATION_MESSAGE",
    "PRIVACY_NOTICE",
    "PROVIDER_LABEL",
    "SOURCE_LANGUAGE_LABELS",
    "STATUS_CONFIG_REQUIRED",
    "STATUS_ERROR",
    "STATUS_INVALID",
    "STATUS_TRANSLATED",
    "TARGET_LANGUAGE_LABELS",
    "run_translation",
    "translation_capability",
    "translation_view",
    "ui_translation",
]
