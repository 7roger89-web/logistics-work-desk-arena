"""LOGI_TRANSLATION_WORKSPACE_01 — focused backend acceptance for /dich-thuat.

Proves the bounded adapter (``views.translation``) and its dispatcher /
view-model wiring expose the EXISTING DeepL capability
(``core.deepl_translation.DeepLClient``) truthfully. The provider boundary is
always MOCKED (``requests.request`` is patched), so these tests never call the
real paid DeepL API.

Invariants under test:

- language choices come from the backend's own supported sets (no invented pair)
- unsupported language / empty input are refused WITHOUT a provider call
- a missing configuration is an honest ``config_required`` state, not a fake
  translation and not a crash
- success passes the provider text through VERBATIM (line breaks, HS codes,
  shipment IDs, invoice references are not mangled)
- provider errors surface as a safe message and never crash the app
- ONE user intent = at most ONE external call (same-intent duplicate guard)
- the view-model never carries credential material
"""

from __future__ import annotations

import json

import pytest

from core.deepl_translation import (
    EMPTY_TEXT_MESSAGE,
    INVALID_LANGUAGE_MESSAGE,
    NO_API_KEYS_MESSAGE,
    SUPPORTED_SOURCE_LANGUAGES,
    SUPPORTED_TARGET_LANGUAGES,
)
from views import logi_sandbox
from views import logi_view_model as vm
from views import translation as tr

FAKE_KEY = "fake-deepl-workspace-key"
FAKE_KEYS = [FAKE_KEY]

SOURCE_TEXT = (
    "Lô hàng SHP-2026-0147, mã HS 9401.61.00.\n"
    "Invoice INV-2026-0042 · 320 kiện · 12.480 kg\n"
    "请安排明天上午提货。"
)
TRANSLATED_TEXT = (
    "Lô hàng SHP-2026-0147, mã HS 9401.61.00.\n"
    "Invoice INV-2026-0042 · 320 kiện · 12.480 kg\n"
    "Vui lòng sắp xếp lấy hàng vào sáng mai."
)


# ---------------------------------------------------------------------------
# Provider-boundary mock (requests.request) — the real DeepL client runs.
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code: int, payload: object = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


class _Recorder:
    """Stand-in for ``requests.request`` that records calls and never hits net."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def __call__(self, method: str, url: str, **kwargs) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self._responses:
            raise AssertionError("provider called more times than mocked")
        return self._responses.pop(0)

    @property
    def sent_payload(self) -> dict:
        return self.calls[0]["kwargs"]["json"]

    @property
    def sent_auth_header(self) -> str:
        return self.calls[0]["kwargs"]["headers"]["Authorization"]


def _ok_response(text: str = TRANSLATED_TEXT, detected: str = "ZH",
                 billed: int = 128) -> _FakeResponse:
    return _FakeResponse(200, {"translations": [{
        "text": text, "detected_source_language": detected,
        "billed_characters": billed,
    }]})


@pytest.fixture()
def provider(monkeypatch):
    """Patch the provider boundary and configure ONE fake key."""
    import requests
    import streamlit as st

    recorder = _Recorder([_ok_response()])
    monkeypatch.setattr(requests, "request", recorder)
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", FAKE_KEYS)
    # Drop any session-cached client so this test's mocked transport is used.
    st.session_state.pop("deepl_client", None)
    return recorder


@pytest.fixture()
def staging():
    """Isolated staging transport + a clean translation session readback."""
    import streamlit as st

    logi_sandbox.reset_backend()
    logi_sandbox.ensure_backend()
    # The DeepL client is session-cached (it binds its transport at
    # construction), so each test must start from a fresh one to see its own
    # mocked provider boundary.
    for key in ("deepl_client", vm.TRANSLATION_REQUEST_KEY,
                vm.TRANSLATION_RESULT_KEY, vm.SEQ_KEY, vm.TARIFF_QUERY_KEY):
        st.session_state.pop(key, None)
    yield
    # Never leak readback state into another suite (session_state is global).
    for key in ("deepl_client", vm.TRANSLATION_REQUEST_KEY,
                vm.TRANSLATION_RESULT_KEY, vm.SEQ_KEY, vm.TARIFF_QUERY_KEY,
                "logi_last_writes"):
        st.session_state.pop(key, None)
    logi_sandbox.reset_backend()


# ---------------------------------------------------------------------------
# Capability map — what the UI may truthfully offer
# ---------------------------------------------------------------------------

def test_capability_offers_only_backend_supported_languages():
    capability = tr.translation_capability(api_keys=FAKE_KEYS)
    assert [o["code"] for o in capability["sourceLanguages"]] == sorted(
        SUPPORTED_SOURCE_LANGUAGES, key=list(tr.SOURCE_LANGUAGE_LABELS).index)
    assert [o["code"] for o in capability["targetLanguages"]] == list(
        tr.TARGET_LANGUAGE_LABELS)
    assert {o["code"] for o in capability["targetLanguages"]} == set(
        SUPPORTED_TARGET_LANGUAGES)
    # Business directions the backend really accepts are all reachable.
    assert {"ZH", "VI", "EN"} <= {o["code"] for o in capability["sourceLanguages"]}
    assert {"VI", "ZH-HANS", "EN"} <= {o["code"] for o in capability["targetLanguages"]}


def test_auto_detect_is_exposed_only_as_a_source_option():
    capability = tr.translation_capability(api_keys=FAKE_KEYS)
    assert capability["autoDetectSupported"] is True
    assert "AUTO" in {o["code"] for o in capability["sourceLanguages"]}
    assert "AUTO" not in {o["code"] for o in capability["targetLanguages"]}


def test_capability_reports_configuration_state_without_secret_material():
    configured = tr.translation_capability(api_keys=FAKE_KEYS)
    assert configured["configured"] is True and configured["apiCount"] == 1
    assert configured["configNotice"] is None

    missing = tr.translation_capability(api_keys=[])
    assert missing["configured"] is False and missing["apiCount"] == 0
    assert "chưa được cấu hình" in (missing["configNotice"] or "")
    assert NO_API_KEYS_MESSAGE in (missing["configNotice"] or "")

    for payload in (configured, missing):
        dumped = json.dumps(payload, ensure_ascii=False)
        # No credential material: only the configuration KEY NAME may appear
        # (the canonical "chưa cấu hình" notice tells the Owner where to put it).
        assert FAKE_KEY not in dumped
        assert "DeepL-Auth-Key" not in dumped
        assert "keys" not in payload


def test_privacy_boundary_is_disclosed_as_external_provider():
    capability = tr.translation_capability(api_keys=FAKE_KEYS)
    assert capability["externalProvider"] is True
    assert "DeepL" in capability["privacyNotice"]
    assert capability["provider"] == "DeepL"


# ---------------------------------------------------------------------------
# Refusals — no provider call, no fabrication
# ---------------------------------------------------------------------------

def test_unsupported_language_is_refused_without_provider_call(provider):
    result = tr.run_translation("Xin chào", source_lang="JA", target_lang="VI")
    assert result["status"] == tr.STATUS_INVALID
    assert result["error"] == INVALID_LANGUAGE_MESSAGE
    assert result["text"] is None
    assert provider.calls == []


def test_unsupported_target_language_is_refused_without_provider_call(provider):
    result = tr.run_translation("Xin chào", source_lang="VI", target_lang="TH")
    assert result["status"] == tr.STATUS_INVALID
    assert result["error"] == INVALID_LANGUAGE_MESSAGE
    assert provider.calls == []


def test_empty_input_is_refused_without_provider_call(provider):
    for empty in ("", "   ", None):
        result = tr.run_translation(empty, source_lang="VI", target_lang="EN")
        assert result["status"] == tr.STATUS_INVALID
        assert result["error"] == EMPTY_TEXT_MESSAGE
    assert provider.calls == []


def test_missing_configuration_is_honest_and_never_calls_provider(monkeypatch):
    import requests

    recorder = _Recorder([])  # raises AssertionError if the provider is called
    monkeypatch.setattr(requests, "request", recorder)
    result = tr.run_translation("Xin chào", source_lang="VI",
                                target_lang="EN", api_keys=[])
    assert result["status"] == tr.STATUS_CONFIG_REQUIRED
    assert result["error"] == NO_API_KEYS_MESSAGE
    assert result["text"] is None
    assert recorder.calls == []


# ---------------------------------------------------------------------------
# Success + provider failure through the real client
# ---------------------------------------------------------------------------

def test_successful_translation_is_verbatim_and_metadata_is_safe(provider):
    result = tr.run_translation(SOURCE_TEXT, source_lang="ZH", target_lang="VI")

    assert result["status"] == tr.STATUS_TRANSLATED
    assert result["error"] is None
    # VERBATIM: line breaks and logistics identifiers survive untouched.
    assert result["text"] == TRANSLATED_TEXT
    assert result["text"].count("\n") == TRANSLATED_TEXT.count("\n") == 2
    for identifier in ("SHP-2026-0147", "9401.61.00", "INV-2026-0042", "12.480"):
        assert identifier in result["text"]
    assert result["detectedSourceLanguage"] == "ZH"
    assert result["billedCharacters"] == 128
    assert result["apiLabel"] == "API 1/1"

    # What actually went to the provider: the existing canonical parameters.
    sent = provider.sent_payload
    assert sent["text"] == [SOURCE_TEXT]
    assert sent["source_lang"] == "ZH" and sent["target_lang"] == "VI"
    assert sent["preserve_formatting"] is True
    assert sent["context"]  # the existing logistics context is reused
    assert provider.sent_auth_header == f"DeepL-Auth-Key {FAKE_KEY}"
    assert provider.calls[0]["url"].endswith("/v2/translate")


def test_auto_detect_source_is_omitted_from_the_request(provider):
    tr.run_translation(SOURCE_TEXT, source_lang="AUTO", target_lang="VI")
    assert "source_lang" not in provider.sent_payload


def test_provider_error_is_surfaced_without_crash_or_secret(monkeypatch):
    recorder = _Recorder([_FakeResponse(500), _FakeResponse(500),
                          _FakeResponse(500)])
    import requests

    monkeypatch.setattr(requests, "request", recorder)
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", FAKE_KEYS)
    result = tr.run_translation(SOURCE_TEXT, source_lang="ZH", target_lang="VI")
    assert result["status"] == tr.STATUS_ERROR
    assert result["text"] is None
    assert result["error"]
    assert FAKE_KEY not in json.dumps(result, ensure_ascii=False)


def test_exhausted_quota_is_reported_as_an_error_state(monkeypatch):
    recorder = _Recorder([_FakeResponse(456), _FakeResponse(456)])
    import requests

    monkeypatch.setattr(requests, "request", recorder)
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", [FAKE_KEY, "fake-second-key"])
    result = tr.run_translation(SOURCE_TEXT, source_lang="ZH", target_lang="VI")
    assert result["status"] == tr.STATUS_ERROR
    assert result["text"] is None


# ---------------------------------------------------------------------------
# Dispatcher: ONE intent = ONE external call
# ---------------------------------------------------------------------------

def _trigger(seq: int, text: str = SOURCE_TEXT, source: str = "ZH",
             target: str = "VI") -> dict:
    return {"translate_text": {"seq": seq, "event": "translate_text",
                               "payload": {"text": text, "sourceLang": source,
                                           "targetLang": target}}}


def test_translation_event_is_declared_for_the_component_shell():
    assert "translate_text" in vm.TRANSLATION_EVENTS
    assert "translate_text" in vm.ALL_EVENTS


def test_dispatcher_translates_and_stores_the_readback(staging, provider):
    import streamlit as st

    outcomes = vm.consume_translation_triggers({"seq": 0}, _trigger(1))

    assert len(outcomes) == 1 and outcomes[0]["ok"] is True
    request = st.session_state[vm.TRANSLATION_REQUEST_KEY]
    assert request["sourceLang"] == "ZH" and request["targetLang"] == "VI"
    assert request["fingerprint"] == outcomes[0]["readback"]["fingerprint"]
    result = st.session_state[vm.TRANSLATION_RESULT_KEY]
    assert result["status"] == tr.STATUS_TRANSLATED
    assert result["text"] == TRANSLATED_TEXT


def test_same_intent_double_click_calls_the_provider_once(staging, provider):
    first = vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    second = vm.consume_translation_triggers({"seq": 1}, _trigger(2))

    assert first[0]["ok"] is True
    assert second[0]["ok"] is True
    assert second[0]["readback"]["duplicate"] is True
    assert second[0]["notice"] == tr.DUPLICATE_TRANSLATION_MESSAGE
    assert len(provider.calls) == 1  # ONE intent → ONE paid call


def test_changed_text_or_direction_is_a_new_intent(staging, provider):
    provider._responses.extend([_ok_response(), _ok_response()])
    vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    vm.consume_translation_triggers({"seq": 1}, _trigger(2, target="EN"))
    vm.consume_translation_triggers({"seq": 2}, _trigger(3, text="Khác"))
    assert len(provider.calls) == 3


def test_failed_translation_can_be_retried_with_the_same_text(staging, monkeypatch):
    import requests

    # The existing client retries a 5xx finitely (initial + 2 transient
    # retries), so a genuine failure needs all of them to fail.
    recorder = _Recorder([_FakeResponse(500)] * 3 + [_ok_response()] * 3)
    monkeypatch.setattr(requests, "request", recorder)
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", FAKE_KEYS)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)  # no real backoff wait

    first = vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    assert first[0]["ok"] is False and first[0]["error"]
    assert len(recorder.calls) == 3
    # A FAILED intent is not "already translated": the retry must go through.
    second = vm.consume_translation_triggers({"seq": 1}, _trigger(2))
    assert second[0]["ok"] is True
    assert len(recorder.calls) == 4


def test_replayed_seq_is_ignored(staging, provider):
    vm.consume_translation_triggers({"seq": 0}, _trigger(5))
    assert vm.consume_translation_triggers({"seq": 5}, _trigger(5)) == []
    assert len(provider.calls) == 1


def test_unknown_event_and_bad_payload_are_dropped(staging, provider):
    assert vm.consume_translation_triggers(
        {"seq": 0}, {"something_else": {"seq": 1, "payload": {}}}) == []
    outcomes = vm.consume_translation_triggers(
        {"seq": 0}, {"translate_text": {"seq": 1, "payload": "not-a-dict"}})
    assert outcomes[0]["ok"] is False and provider.calls == []


def test_empty_text_event_is_refused_without_provider_call(staging, provider):
    outcomes = vm.consume_translation_triggers(
        {"seq": 0}, _trigger(1, text="   "))
    assert outcomes[0]["ok"] is False
    assert outcomes[0]["error"] == EMPTY_TEXT_MESSAGE
    assert provider.calls == []


def test_rbac_denies_translation_event_without_provider_call(staging, provider):
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer.user", "role": "viewer"}
    try:
        outcomes = vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    finally:
        st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    assert outcomes[0]["ok"] is False and "RBAC" in outcomes[0]["error"]
    assert provider.calls == []


# ---------------------------------------------------------------------------
# View-model exposure
# ---------------------------------------------------------------------------

def test_view_model_exposes_translation_slice_without_secret(staging, provider):
    import streamlit as st

    model = vm.build_view_model()
    assert model["translation"]["capability"]["configured"] is True
    assert model["translation"]["request"] is None  # honest idle state
    assert model["translation"]["result"] is None

    vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    model = vm.build_view_model()
    assert model["translation"]["result"]["text"] == TRANSLATED_TEXT
    assert model["translation"]["request"]["sourceLang"] == "ZH"

    dumped = json.dumps(model, ensure_ascii=False, default=str)
    assert FAKE_KEY not in dumped
    assert "DeepL-Auth-Key" not in dumped


def test_unconfigured_deployment_exposes_honest_state_in_view_model(staging,
                                                                   monkeypatch):
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", [])
    model = vm.build_view_model()
    capability = model["translation"]["capability"]
    assert capability["configured"] is False
    assert "chưa được cấu hình" in capability["configNotice"]
    assert model["translation"]["result"] is None


def test_unconfigured_deployment_refuses_event_without_network(staging, monkeypatch):
    import requests

    recorder = _Recorder([])
    monkeypatch.setattr(requests, "request", recorder)
    monkeypatch.setattr(tr, "DEEPL_API_KEYS", [])

    outcomes = vm.consume_translation_triggers({"seq": 0}, _trigger(1))
    assert outcomes[0]["ok"] is False
    assert outcomes[0]["error"] == NO_API_KEYS_MESSAGE
    assert recorder.calls == []


def test_dispatch_delivers_translation_readback_with_single_rerun(staging, provider,
                                                                 monkeypatch):
    import streamlit as st

    reruns: list[int] = []
    monkeypatch.setattr(st, "rerun", lambda: reruns.append(1))
    vm.dispatch(_trigger(3))

    assert len(reruns) == 1
    assert len(provider.calls) == 1
    # The one-shot trigger is gone on the rerun → no loop, no second call.
    vm.dispatch({})
    assert len(reruns) == 1
    assert len(provider.calls) == 1


def test_tariff_path_is_undisturbed_by_the_translation_wiring(staging, provider,
                                                              monkeypatch):
    import streamlit as st

    reruns: list[int] = []
    monkeypatch.setattr(st, "rerun", lambda: reruns.append(1))
    vm.dispatch({"tariff_lookup": {"seq": 9, "event": "tariff_lookup",
                                   "payload": {"query": "9401"}}})
    assert st.session_state[vm.TARIFF_QUERY_KEY] == "9401"
    assert len(reruns) == 1
    assert provider.calls == []
