from __future__ import annotations

from contextlib import ExitStack
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.deepl_translation import TranslationResult, UsageRow
from views import translation as translation_view


FAKE_KEY_ONE = "fake-ui-key-one"
FAKE_KEY_TWO = "fake-ui-key-two"


class FakeClient:
    def __init__(self) -> None:
        self.api_count = 2
        self.translate_calls: list[dict[str, object]] = []
        self.usage_calls = 0

    def translate(
        self,
        text: str,
        *,
        source_lang: str | None,
        target_lang: str,
        context: str,
    ) -> TranslationResult:
        self.translate_calls.append(
            {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "context": context,
            }
        )
        return TranslationResult(
            translated_text="Bản dịch giả lập an toàn",
            detected_source_language="ZH",
            billed_characters=24,
            api_index=2,
            api_count=self.api_count,
        )

    def check_usage(self) -> list[UsageRow]:
        self.usage_calls += 1
        return [
            UsageRow(
                api_index=1,
                api_count=self.api_count,
                status="Sẵn sàng",
                character_count=10,
                character_limit=100,
                characters_remaining=90,
            ),
            UsageRow(
                api_index=2,
                api_count=self.api_count,
                status="Hết quota",
            ),
        ]


def _element(app: AppTest, collection: str, key: str):
    return next(element for element in getattr(app, collection) if element.key == key)


def _assert_no_exceptions(test_case: unittest.TestCase, app: AppTest) -> None:
    exceptions = [str(element.value) for element in app.exception]
    test_case.assertEqual(exceptions, [], msg=f"Streamlit exceptions: {exceptions}")


def _visible_text(app: AppTest) -> str:
    values: list[str] = []
    for collection_name in (
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "info",
        "warning",
        "error",
        "success",
        "button",
        "text_area",
    ):
        for element in getattr(app, collection_name):
            value = getattr(element, "value", "")
            if value is not None:
                values.append(str(value))
    return "\n".join(values)


def _run_translation_view() -> None:
    from views.translation import ui_translation

    ui_translation()


class DeepLTranslationViewTests(unittest.TestCase):
    def test_no_keys_render_clean_configuration_gate(self) -> None:
        with patch.object(translation_view, "DEEPL_API_KEYS", []):
            app = AppTest.from_function(_run_translation_view, default_timeout=60)
            app.run()

        _assert_no_exceptions(self, app)
        rendered = _visible_text(app)
        self.assertIn("Chưa cấu hình API DeepL", rendered)
        self.assertNotIn(FAKE_KEY_ONE, rendered)
        self.assertNotIn(FAKE_KEY_TWO, rendered)
        self.assertEqual([button.key for button in app.button], [])

    def test_support_view_can_translate_swap_and_check_usage(self) -> None:
        fake_client = FakeClient()
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(translation_view, "DEEPL_API_KEYS", [FAKE_KEY_ONE, FAKE_KEY_TWO])
            )
            stack.enter_context(
                patch.object(translation_view, "DeepLClient", return_value=fake_client)
            )
            app = AppTest.from_function(_run_translation_view, default_timeout=60)
            app.run()
            _assert_no_exceptions(self, app)

            _element(app, "selectbox", "deepl_source_language").set_value("ZH")
            _element(app, "selectbox", "deepl_target_language").set_value("VI")
            _element(app, "text_area", "deepl_source_text").set_value("装货地址：广西凭祥")
            app.run()
            _assert_no_exceptions(self, app)

            _element(app, "button", "deepl_translate_button").click()
            app.run()
            _assert_no_exceptions(self, app)
            self.assertEqual(len(fake_client.translate_calls), 1)
            self.assertEqual(fake_client.translate_calls[0]["source_lang"], "ZH")
            self.assertEqual(fake_client.translate_calls[0]["target_lang"], "VI")
            self.assertEqual(_element(app, "text_area", "deepl_result_text").value, "Bản dịch giả lập an toàn")
            self.assertTrue(any("Đang dùng API 2/2" in str(element.value) for element in app.caption))
            self.assertNotIn(FAKE_KEY_ONE, _visible_text(app))
            self.assertNotIn(FAKE_KEY_TWO, _visible_text(app))

            _element(app, "selectbox", "deepl_source_language").set_value("VI")
            _element(app, "selectbox", "deepl_target_language").set_value("ZH-HANS")
            app.run()
            _element(app, "button", "deepl_translate_button").click()
            app.run()
            self.assertEqual(len(fake_client.translate_calls), 2)
            self.assertEqual(fake_client.translate_calls[-1]["source_lang"], "VI")
            self.assertEqual(fake_client.translate_calls[-1]["target_lang"], "ZH-HANS")
            _element(app, "button", "deepl_swap_button").click()
            app.run()
            self.assertEqual(_element(app, "selectbox", "deepl_source_language").value, "ZH")
            self.assertEqual(_element(app, "selectbox", "deepl_target_language").value, "VI")

            _element(app, "button", "deepl_usage_button").click()
            app.run()
            _assert_no_exceptions(self, app)
            self.assertEqual(fake_client.usage_calls, 1)
            self.assertTrue(app.dataframe)
            self.assertIn("Hết quota", str(app.dataframe[0].value))


class DeepLSupportAccessTests(unittest.TestCase):
    """LOGI_TRANSLATION_RUNTIME_UI_PARITY_01 — repaired for the React shell.

    The old variant mounted the dead multi-page Streamlit shell
    (``views.web_app.refresh_core_data`` / sidebar page buttons no longer
    exist since PR #44), so it could only fail. The CURRENT equivalent of
    "support can reach translation without touching the database": the
    capability adapter answers ``allowed`` from the EXISTING RBAC matrix for a
    support session, stays configured-state honest, and never exposes key
    material.
    """

    def test_support_capability_is_allowed_and_never_exposes_keys(self) -> None:
        from views import translation as translation_view

        support_user = {
            "username": "support-user",
            "display_name": "Support User",
            "role": "support",
        }
        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {"current_user": support_user}
            capability = translation_view.translation_capability(
                api_keys=[FAKE_KEY_ONE, FAKE_KEY_TWO]
            )

        self.assertTrue(capability["allowed"])
        self.assertTrue(capability["configured"])
        self.assertEqual(capability["apiCount"], 2)
        rendered = _render_capability_text(capability)
        self.assertNotIn(FAKE_KEY_ONE, rendered)
        self.assertNotIn(FAKE_KEY_TWO, rendered)

    def test_viewer_capability_is_denied(self) -> None:
        from views import translation as translation_view

        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {
                "current_user": {"username": "viewer-user", "role": "viewer"}
            }
            capability = translation_view.translation_capability(
                api_keys=[FAKE_KEY_ONE]
            )

        self.assertFalse(capability["allowed"])
        self.assertNotIn(FAKE_KEY_ONE, _render_capability_text(capability))


def _render_capability_text(capability: dict) -> str:
    import json

    return json.dumps(capability, ensure_ascii=False, default=str)


if __name__ == "__main__":
    unittest.main()
