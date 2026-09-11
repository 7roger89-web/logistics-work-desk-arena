#!/usr/bin/env python3
"""Generate the LOGI_TRANSLATION_WORKSPACE_01 DOM-acceptance fixture.

Same contract as gen_tariff_fixture.py: boot the ISOLATED mongomock staging
transport (never production), dump the real ``build_view_model()`` payload
verbatim. This generator additionally:

  1. configures ONE fake DeepL key for the dump only (never committed as a
     credential — it is an obvious placeholder inside a test fixture),
  2. MOCKS the provider boundary (``requests.request``) with a canned DeepL
     answer, so generating this fixture makes ZERO real paid API calls,
  3. drives the REAL bounded dispatcher (``logi_view_model.dispatch``) with one
     ``translate_text`` intent, so the fixture carries exactly the readback the
     live rerun would deliver.

Run:  python scripts/gen_translation_fixture.py
Out:  tests/component/fixtures/view_model_translation.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_translation.json"

FAKE_KEY = "fixture-fake-deepl-key-not-a-secret"

SOURCE_TEXT = (
    "Lô hàng SHP-2026-0147, mã HS 9401.61.00.\n"
    "Invoice INV-2026-0042 · 320 kiện · 12.480 kg\n"
    "请安排明天上午提货，司机电话 138 0000 0000。"
)
TRANSLATED_TEXT = (
    "Lô hàng SHP-2026-0147, mã HS 9401.61.00.\n"
    "Invoice INV-2026-0042 · 320 kiện · 12.480 kg\n"
    "Vui lòng sắp xếp lấy hàng vào sáng mai, số điện thoại tài xế 138 0000 0000."
)


class _FakeResponse:
    status_code = 200

    def json(self) -> dict:
        return {"translations": [{
            "text": TRANSLATED_TEXT,
            "detected_source_language": "ZH",
            "billed_characters": 173,
        }]}


def _fake_request(method: str, url: str, **kwargs) -> _FakeResponse:
    """The mocked provider boundary — no network, no paid call."""
    assert url.endswith("/v2/translate"), f"unexpected provider call: {url}"
    return _FakeResponse()


def main() -> None:
    import requests
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm
    from views import translation as tr

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    real_request = requests.request
    real_keys = tr.DEEPL_API_KEYS
    requests.request = _fake_request
    tr.DEEPL_API_KEYS = [FAKE_KEY]
    try:
        # The real dispatcher path: ONE translate_text intent → ONE provider
        # call → session readback → fresh view-model.
        st.rerun = lambda: None  # the one-shot rerun is a no-op for the dump
        vm.dispatch({"translate_text": {
            "seq": 1,
            "event": "translate_text",
            "payload": {"text": SOURCE_TEXT, "sourceLang": "ZH", "targetLang": "VI"},
        }})
        model = vm.build_view_model()
    finally:
        requests.request = real_request
        tr.DEEPL_API_KEYS = real_keys

    translation = model["translation"]
    assert translation["result"]["status"] == "translated", translation["result"]
    assert translation["result"]["text"] == TRANSLATED_TEXT, "provider text was mutated"
    assert FAKE_KEY not in json.dumps(model, ensure_ascii=False, default=str), \
        "credential material must never reach the view-model"

    payload = {
        "generatedFrom": (
            "scripts/gen_translation_fixture.py — isolated mongomock staging, "
            "provider boundary mocked (no real DeepL call)"
        ),
        **model,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                   encoding="utf-8")
    result = translation["result"]
    print(f"wrote {OUT}")
    print(f"  translation: configured={translation['capability']['configured']} "
          f"status={result['status']} detected={result['detectedSourceLanguage']} "
          f"billed={result['billedCharacters']} api={result['apiLabel']}")


if __name__ == "__main__":
    main()
