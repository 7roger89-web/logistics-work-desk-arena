"""Owner-facing DeepL text translation view."""
from __future__ import annotations

import logging

import streamlit as st

from core.config import DEEPL_API_KEYS
from core.deepl_translation import (
    DEFAULT_LOGISTICS_CONTEXT,
    DeepLClient,
    DeepLTranslationError,
    MAX_TEXT_BYTES,
    NO_API_KEYS_MESSAGE,
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


def _get_client() -> DeepLClient:
    client = st.session_state.get("deepl_client")
    configured_count = len(DEEPL_API_KEYS)
    if client is None or getattr(client, "api_count", None) != configured_count:
        client = DeepLClient(DEEPL_API_KEYS)
        st.session_state.deepl_client = client
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


__all__ = [
    "SOURCE_LANGUAGE_LABELS",
    "TARGET_LANGUAGE_LABELS",
    "ui_translation",
]
