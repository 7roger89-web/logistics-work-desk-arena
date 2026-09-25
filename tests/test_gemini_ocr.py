"""LOGI_GEMINI_OCR_01 — focused contracts for image -> Markdown OCR."""
from __future__ import annotations

import base64
from pathlib import Path

import pytest

from core import gemini_ocr
from views import gemini_ocr as view
from views import logi_sandbox
from views import logi_view_model as vm

IMAGE_BYTES = b"\x89PNG\r\n\x1a\nsynthetic-ocr-image"
MARKDOWN = "# OOCL\n\nNINGBO - HAIPHONG\n\nUSD 750/20GP"


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, *, text: str = MARKDOWN, error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return _FakeResponse(self.text)


class _FakeClient:
    def __init__(self, *, text: str = MARKDOWN, error: Exception | None = None) -> None:
        self.models = _FakeModels(text=text, error=error)


def _trigger(seq: int, *, data: bytes = IMAGE_BYTES, mime: str = "image/png",
             filename: str = "quote.png") -> dict:
    return {
        "ocr_image": {
            "seq": seq,
            "event": "ocr_image",
            "payload": {
                "filename": filename,
                "mimeType": mime,
                "dataBase64": base64.b64encode(data).decode("ascii"),
            },
        }
    }


def test_core_success_sends_exact_prompt_bytes_mime_and_model():
    client = _FakeClient()
    result = gemini_ocr.extract_markdown(
        IMAGE_BYTES,
        mime_type="image/png",
        api_key="fake-key",
        model="gemini-test",
        client=client,
    )
    assert result["status"] == gemini_ocr.STATUS_EXTRACTED
    assert result["text"] == MARKDOWN
    call = client.models.calls[0]
    assert call["model"] == "gemini-test"
    assert call["contents"][0] == gemini_ocr.OCR_PROMPT
    part = call["contents"][1]
    assert part.inline_data.mime_type == "image/png"
    assert part.inline_data.data == IMAGE_BYTES
    assert call["config"].temperature == 0


def test_only_outer_markdown_fence_is_removed():
    tick = chr(96) * 3
    wrapped = tick + "markdown\n# Hóa đơn\n\n\`USD 750\`\n" + tick
    result = gemini_ocr.extract_markdown(
        IMAGE_BYTES, mime_type="image/png", client=_FakeClient(text=wrapped)
    )
    assert result["text"] == "# Hóa đơn\n\n\`USD 750\`"


@pytest.mark.parametrize(
    ("data", "mime", "expected"),
    [
        (b"", "image/png", gemini_ocr.EMPTY_IMAGE_MESSAGE),
        (IMAGE_BYTES, "image/gif", gemini_ocr.UNSUPPORTED_IMAGE_MESSAGE),
        (b"x" * (gemini_ocr.MAX_IMAGE_BYTES + 1), "image/png",
         gemini_ocr.OVERSIZED_IMAGE_MESSAGE),
    ],
)
def test_invalid_input_is_refused_before_provider(data, mime, expected):
    client = _FakeClient()
    result = gemini_ocr.extract_markdown(data, mime_type=mime, client=client)
    assert result["status"] == gemini_ocr.STATUS_INVALID
    assert result["error"] == expected
    assert client.models.calls == []


def test_missing_key_is_honest_without_provider_call():
    result = gemini_ocr.extract_markdown(
        IMAGE_BYTES, mime_type="image/png", api_key=""
    )
    assert result["status"] == gemini_ocr.STATUS_CONFIG_REQUIRED
    assert result["error"] == gemini_ocr.NO_API_KEY_MESSAGE
    assert result["text"] is None


def test_provider_failure_is_safe_and_does_not_leak_detail():
    result = gemini_ocr.extract_markdown(
        IMAGE_BYTES,
        mime_type="image/png",
        client=_FakeClient(error=RuntimeError("secret provider body")),
    )
    assert result["status"] == gemini_ocr.STATUS_ERROR
    assert result["error"] == gemini_ocr.PROVIDER_ERROR_MESSAGE
    assert "secret provider body" not in str(result)


def test_capability_never_exposes_key_material():
    cap = view.ocr_capability(api_key="fake-super-secret")
    assert cap["configured"] is True
    assert cap["externalProvider"] is True
    assert "fake-super-secret" not in str(cap)
    assert cap["acceptedMimeTypes"] == ["image/jpeg", "image/png", "image/webp"]


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    logi_sandbox.ensure_backend()
    for key in (vm.OCR_REQUEST_KEY, vm.OCR_RESULT_KEY, vm.SEQ_KEY, vm.LAST_WRITES_KEY):
        st.session_state.pop(key, None)
    yield
    for key in (vm.OCR_REQUEST_KEY, vm.OCR_RESULT_KEY, vm.SEQ_KEY, vm.LAST_WRITES_KEY):
        st.session_state.pop(key, None)
    logi_sandbox.reset_backend()


def test_ocr_event_is_declared_for_component_shell():
    assert "ocr_image" in vm.OCR_EVENTS
    assert "ocr_image" in vm.ALL_EVENTS


def test_dispatcher_does_not_persist_raw_image_or_base64(staging, monkeypatch):
    import streamlit as st

    calls: list[tuple[bytes, str]] = []

    def fake_run(data: bytes, *, mime_type: str):
        calls.append((data, mime_type))
        return {
            "status": gemini_ocr.STATUS_EXTRACTED,
            "text": MARKDOWN,
            "error": None,
            "provider": gemini_ocr.PROVIDER_LABEL,
            "model": "gemini-test",
        }

    monkeypatch.setattr(view, "run_ocr", fake_run)
    outcomes = vm.consume_ocr_triggers({"seq": 0}, _trigger(1))
    assert outcomes[0]["ok"] is True
    assert calls == [(IMAGE_BYTES, "image/png")]
    request = st.session_state[vm.OCR_REQUEST_KEY]
    assert request["filename"] == "quote.png"
    assert request["mimeType"] == "image/png"
    assert request["sizeBytes"] == len(IMAGE_BYTES)
    assert request["fingerprint"]
    assert "dataBase64" not in request
    assert st.session_state[vm.OCR_RESULT_KEY]["text"] == MARKDOWN


def test_same_image_intent_calls_provider_once(staging, monkeypatch):
    calls: list[int] = []

    def fake_run(data: bytes, *, mime_type: str):
        calls.append(1)
        return {
            "status": gemini_ocr.STATUS_EXTRACTED,
            "text": MARKDOWN,
            "error": None,
            "provider": gemini_ocr.PROVIDER_LABEL,
            "model": "gemini-test",
        }

    monkeypatch.setattr(view, "run_ocr", fake_run)
    first = vm.consume_ocr_triggers({"seq": 0}, _trigger(1))
    second = vm.consume_ocr_triggers({"seq": 1}, _trigger(2))
    assert first[0]["ok"] is True
    assert second[0]["ok"] is True
    assert second[0]["readback"]["duplicate"] is True
    assert len(calls) == 1


def test_invalid_base64_is_refused_without_provider(staging, monkeypatch):
    calls: list[int] = []
    monkeypatch.setattr(view, "run_ocr", lambda *a, **k: calls.append(1))
    bad = {
        "ocr_image": {
            "seq": 1,
            "event": "ocr_image",
            "payload": {
                "filename": "bad.png",
                "mimeType": "image/png",
                "dataBase64": "%%%NOT-BASE64%%%",
            },
        }
    }
    out = vm.consume_ocr_triggers({"seq": 0}, bad)
    assert out[0]["ok"] is False
    assert calls == []


def test_dispatch_delivers_ocr_with_one_rerun(staging, monkeypatch):
    import streamlit as st

    monkeypatch.setattr(
        view,
        "run_ocr",
        lambda data, *, mime_type: {
            "status": gemini_ocr.STATUS_EXTRACTED,
            "text": MARKDOWN,
            "error": None,
            "provider": gemini_ocr.PROVIDER_LABEL,
            "model": "gemini-test",
        },
    )
    reruns: list[int] = []
    monkeypatch.setattr(st, "rerun", lambda: reruns.append(1))
    vm.dispatch(_trigger(3))
    assert reruns == [1]
    vm.dispatch({})
    assert reruns == [1]


def test_source_wiring_has_route_nav_event_and_no_inline_secret():
    root = Path(__file__).resolve().parents[1]
    app = (root / "component/src/App.tsx").read_text(encoding="utf-8")
    nav = (root / "component/src/lib/data.ts").read_text(encoding="utf-8")
    dispatcher = (root / "component/src/lib/dispatcher.ts").read_text(encoding="utf-8")
    page = (root / "component/src/pages/OcrWorkspace.tsx").read_text(encoding="utf-8")

    assert 'path="/ocr-anh"' in app
    assert 'to: "/ocr-anh"' in nav
    assert '"ocr_image"' in dispatcher
    assert 'dispatchLogiEvent("ocr_image"' in page
    assert "GEMINI_API_KEY" not in page
    assert "dataBase64" in page
    assert "Copy Markdown" in page
