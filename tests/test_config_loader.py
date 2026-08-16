from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConfigLoaderTests(unittest.TestCase):
    def _run(self, toml_text: str, assertions: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_path = Path(temp_dir) / "secrets.toml"
            secret_path.write_text(textwrap.dedent(toml_text), encoding="utf-8")
            env = os.environ.copy()
            env["LOGISTICS_PRO_SECRETS_FILE"] = str(secret_path)
            env["PYTHONPATH"] = str(ROOT)
            return subprocess.run(
                [sys.executable, "-c", assertions],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_legacy_flat_secrets(self):
        result = self._run(
            """
            MONGO_URI = "mongodb://legacy.invalid:27017"
            MONGO_DB_NAME = "legacy_db"
            TELEGRAM_TOKEN = "dummy-token"
            TELEGRAM_CHAT_ID = "123"
            GEMINI_KEYS = ["dummy-1", "dummy-2"]
            [gcp_service_account]
            type = "service_account"
            """,
            """
from core.config import GEMINI_API_KEYS, MONGO_DB_NAME, MONGO_URI, TELEGRAM_TOKEN
assert MONGO_URI == 'mongodb://legacy.invalid:27017'
assert MONGO_DB_NAME == 'legacy_db'
assert TELEGRAM_TOKEN == 'dummy-token'
assert GEMINI_API_KEYS == ['dummy-1', 'dummy-2']
""",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("missing ScriptRunContext", result.stderr)

    def test_nested_secrets(self):
        result = self._run(
            """
            [mongo]
            uri = "mongodb://nested.invalid:27017"
            database = "nested_db"
            [telegram]
            token = "dummy-token"
            chat_id = "456"
            [gemini]
            api_keys = ["nested-1", "nested-2"]
            model = "test-model"
            """,
            """
from core.config import GEMINI_API_KEYS, GEMINI_MODEL, MONGO_DB_NAME, MONGO_URI
assert MONGO_URI == 'mongodb://nested.invalid:27017'
assert MONGO_DB_NAME == 'nested_db'
assert GEMINI_API_KEYS == ['nested-1', 'nested-2']
assert GEMINI_MODEL == 'test-model'
""",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("missing ScriptRunContext", result.stderr)


if __name__ == "__main__":
    unittest.main()
