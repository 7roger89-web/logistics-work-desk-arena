from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

import requests

from core.deepl_translation import (
    ALL_KEYS_UNAVAILABLE_MESSAGE,
    DEEPL_API_BASE,
    DEEPL_FREE_API_BASE,
    DeepLClient,
    DeepLTranslationError,
    MAX_TEXT_BYTES,
    NO_API_KEYS_MESSAGE,
)


FAKE_KEY_ONE = "fake-deepl-key-one"
FAKE_KEY_TWO = "fake-deepl-key-two"


class FakeResponse:
    def __init__(self, status_code: int, payload: object = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


class RequestRecorder:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def __call__(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        if not isinstance(response, FakeResponse):
            raise AssertionError("test response must be FakeResponse or exception")
        return response


def translation_payload(text: str = "Translated") -> dict[str, object]:
    return {
        "translations": [
            {
                "text": text,
                "detected_source_language": "ZH",
                "billed_characters": 42,
            }
        ]
    }


class DeepLTranslationBehaviorTests(unittest.TestCase):
    def _client(
        self,
        responses: list[object],
        *,
        keys: list[str] | None = None,
        sleeps: list[float] | None = None,
        max_rate_limit_retries: int = 2,
        max_transient_retries: int = 2,
    ) -> tuple[DeepLClient, RequestRecorder, list[float]]:
        recorder = RequestRecorder(responses)
        recorded_sleeps = [] if sleeps is None else sleeps
        client = DeepLClient(
            keys or [FAKE_KEY_ONE, FAKE_KEY_TWO],
            request_fn=recorder,
            sleep_fn=recorded_sleeps.append,
            backoff_base_seconds=0.25,
            max_rate_limit_retries=max_rate_limit_retries,
            max_transient_retries=max_transient_retries,
        )
        return client, recorder, recorded_sleeps

    def test_success_uses_first_key_and_returns_safe_metadata(self) -> None:
        client, recorder, _ = self._client([FakeResponse(200, translation_payload())])

        result = client.translate(
            "装货地址：广西凭祥",
            source_lang="AUTO",
            target_lang="VI",
            context="logistics context",
        )

        self.assertEqual(result.translated_text, "Translated")
        self.assertEqual(result.detected_source_language, "ZH")
        self.assertEqual(result.billed_characters, 42)
        self.assertEqual(result.api_index, 1)
        self.assertEqual(result.api_count, 2)
        self.assertEqual(result.api_label, "API 1/2")
        self.assertEqual(recorder.calls[0]["url"], f"{DEEPL_API_BASE}/v2/translate")
        payload = recorder.calls[0]["kwargs"]["json"]
        self.assertNotIn("source_lang", payload)
        self.assertEqual(payload["target_lang"], "VI")
        self.assertEqual(payload["context"], "logistics context")

    def test_quota_456_marks_first_key_and_rotates_once_to_next(self) -> None:
        client, recorder, _ = self._client(
            [FakeResponse(456, {"message": "quota"}), FakeResponse(200, translation_payload())]
        )

        result = client.translate("装货地址", target_lang="VI")

        self.assertEqual(result.api_index, 2)
        self.assertTrue(client._pool.is_exhausted(0))
        self.assertEqual(len(recorder.calls), 2)
        self.assertIn(FAKE_KEY_TWO, recorder.calls[1]["kwargs"]["headers"]["Authorization"])

    def test_invalid_401_or_403_skips_to_next_key(self) -> None:
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                client, recorder, _ = self._client(
                    [FakeResponse(status_code), FakeResponse(200, translation_payload())]
                )

                result = client.translate("装货地址", target_lang="VI")

                self.assertEqual(result.api_index, 2)
                self.assertTrue(client._pool.is_invalid(0))
                self.assertEqual(len(recorder.calls), 2)

    def test_429_retries_on_same_key_with_bounded_backoff(self) -> None:
        client, recorder, sleeps = self._client(
            [
                FakeResponse(429),
                FakeResponse(429),
                FakeResponse(200, translation_payload()),
            ]
        )

        result = client.translate("装货地址", target_lang="VI")

        self.assertEqual(result.api_index, 1)
        self.assertEqual(len(recorder.calls), 3)
        self.assertEqual(sleeps, [0.25, 0.5])
        self.assertEqual(client.preferred_api_index, 1)

    def test_5xx_and_network_errors_have_finite_retry_then_succeed(self) -> None:
        client, recorder, sleeps = self._client(
            [
                FakeResponse(503),
                requests.Timeout("network test"),
                FakeResponse(200, translation_payload()),
            ]
        )

        result = client.translate("装货地址", target_lang="VI")

        self.assertEqual(result.api_index, 1)
        self.assertEqual(len(recorder.calls), 3)
        self.assertEqual(sleeps, [0.25, 0.5])

    def test_all_keys_unavailable_returns_exact_clean_terminal_error(self) -> None:
        client, _recorder, _ = self._client([FakeResponse(456), FakeResponse(403)])

        with self.assertRaises(DeepLTranslationError) as raised:
            client.translate("装货地址", target_lang="VI")

        self.assertEqual(str(raised.exception), ALL_KEYS_UNAVAILABLE_MESSAGE)
        self.assertNotIn(FAKE_KEY_ONE, str(raised.exception))
        self.assertNotIn(FAKE_KEY_TWO, str(raised.exception))

    def test_rate_limit_exhaustion_fails_over_without_unbounded_calls(self) -> None:
        client, recorder, sleeps = self._client(
            [FakeResponse(429), FakeResponse(429), FakeResponse(429), FakeResponse(200, translation_payload())]
        )

        result = client.translate("装货地址", target_lang="VI")

        self.assertEqual(result.api_index, 2)
        self.assertEqual(len(recorder.calls), 4)
        self.assertEqual(sleeps, [0.25, 0.5])

    def test_free_fx_key_uses_free_endpoint_and_paid_key_uses_paid_endpoint(self) -> None:
        free_client, free_recorder, _ = self._client(
            [FakeResponse(200, translation_payload())], keys=["fake-free:fx"]
        )
        paid_client, paid_recorder, _ = self._client(
            [FakeResponse(200, translation_payload())], keys=["fake-paid"]
        )

        free_client.translate("装货地址", target_lang="VI")
        paid_client.translate("装货地址", target_lang="VI")

        self.assertEqual(free_recorder.calls[0]["url"], f"{DEEPL_FREE_API_BASE}/v2/translate")
        self.assertEqual(paid_recorder.calls[0]["url"], f"{DEEPL_API_BASE}/v2/translate")

    def test_no_key_configured_fails_closed_without_http_call(self) -> None:
        recorder = RequestRecorder([])
        client = DeepLClient([], request_fn=recorder)

        with self.assertRaises(DeepLTranslationError) as raised:
            client.translate("装货地址", target_lang="VI")

        self.assertEqual(str(raised.exception), NO_API_KEYS_MESSAGE)
        self.assertEqual(recorder.calls, [])

    def test_oversized_text_is_rejected_before_http(self) -> None:
        recorder = RequestRecorder([])
        client = DeepLClient([FAKE_KEY_ONE], request_fn=recorder)

        with self.assertRaises(DeepLTranslationError) as raised:
            client.translate("x" * (MAX_TEXT_BYTES + 1), target_lang="VI")

        self.assertIn("quá lớn", str(raised.exception))
        self.assertEqual(recorder.calls, [])

    def test_key_values_are_absent_from_errors_and_logs(self) -> None:
        client, _recorder, _ = self._client([FakeResponse(401), FakeResponse(456)])

        with self.assertLogs("logistics_pro.deepl", level="WARNING") as captured:
            with self.assertRaises(DeepLTranslationError) as raised:
                client.translate("装货地址", target_lang="VI")

        joined = "\n".join(captured.output) + str(raised.exception)
        self.assertNotIn(FAKE_KEY_ONE, joined)
        self.assertNotIn(FAKE_KEY_TWO, joined)
        self.assertNotIn("Authorization", joined)

    def test_usage_rows_are_index_only_and_use_usage_fields(self) -> None:
        client, recorder, _ = self._client(
            [
                FakeResponse(200, {"character_count": 10, "character_limit": 100}),
                FakeResponse(456, {"message": "quota"}),
            ]
        )

        rows = client.check_usage()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].api_label, "API 1/2")
        self.assertEqual(rows[0].status, "Sẵn sàng")
        self.assertEqual(rows[0].character_count, 10)
        self.assertEqual(rows[0].character_limit, 100)
        self.assertEqual(rows[0].characters_remaining, 90)
        self.assertEqual(rows[1].status, "Hết quota")
        display_rows = [row.to_display_dict() for row in rows]
        self.assertEqual(display_rows[0]["API"], "1")
        self.assertEqual(display_rows[0]["Còn lại"], "90")
        self.assertNotIn("key", " ".join(str(row).lower() for row in display_rows))
        self.assertNotIn(FAKE_KEY_ONE, str(display_rows))
        self.assertNotIn(FAKE_KEY_TWO, str(display_rows))
        self.assertEqual([call["method"] for call in recorder.calls], ["GET", "GET"])


class DeepLConfigLoadingTests(unittest.TestCase):
    def _run(self, toml_text: str | None, env_value: str | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
            env.pop("DEEPL_API_KEYS", None)
            if toml_text is not None:
                secret_path = Path(temp_dir) / "secrets.toml"
                secret_path.write_text(textwrap.dedent(toml_text), encoding="utf-8")
                env["LOGISTICS_PRO_SECRETS_FILE"] = str(secret_path)
            else:
                env.pop("LOGISTICS_PRO_SECRETS_FILE", None)
            if env_value is not None:
                env["DEEPL_API_KEYS"] = env_value
            return subprocess.run(
                [sys.executable, "-c", "from core.config import DEEPL_API_KEYS; print(DEEPL_API_KEYS)"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_nested_toml_api_key_list_loads_without_logging_values(self) -> None:
        result = self._run(
            """
            [deepl]
            api_keys = ["fake-one", "fake-two"]
            """,
            None,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "['fake-one', 'fake-two']")

    def test_environment_json_list_overrides_file(self) -> None:
        result = self._run(
            """
            [deepl]
            api_keys = ["file-key"]
            """,
            '["env-one", "env-two"]',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "['env-one', 'env-two']")


if __name__ == "__main__":
    unittest.main()
