"""LOGI_TRANSLATION_RUNTIME_UI_PARITY_01 — DeepL credential shape acceptance.

The deployed failure this task repairs: the config loader only accepted the
PLURAL shapes, so a key configured as ``[deepl].api_key`` / ``DEEPL_API_KEY``
(singular) yielded an empty list and the translation capability reported
"chưa cấu hình" even though a key WAS present in Streamlit secrets.

Each case runs ``core.config`` in a FRESH subprocess (the values are read at
import time) with an isolated secrets file and/or env vars, exactly like the
existing ``tests/test_config_loader.py`` pattern. Every value used here is an
obvious placeholder — never a real credential.

Proven shapes:

- env ``DEEPL_API_KEYS`` (JSON list and comma-separated)
- env ``DEEPL_API_KEY`` (singular)
- secrets ``[deepl].api_keys``
- secrets ``[deepl].api_key`` (singular)
- legacy flat ``DEEPL_API_KEYS`` / ``DEEPL_API_KEY`` secrets
- no config -> empty list and ``configured == False``
- deterministic precedence with NO concatenation of duplicated sources
- key material never appears in the capability view-model payload
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Obvious placeholders only. These strings are assertions targets, never
# real credentials.
KEY_ONE = "cfg-shape-proof-key-one"
KEY_TWO = "cfg-shape-proof-key-two"
SINGLE_KEY = "cfg-shape-proof-single-key"

LIST_ASSERT = """
import json
from core.config import DEEPL_API_KEYS
from views.translation import translation_capability
cap = translation_capability(api_keys=DEEPL_API_KEYS)
assert DEEPL_API_KEYS == {keys!r}, DEEPL_API_KEYS
assert cap["configured"] == {configured}, cap
assert cap["apiCount"] == {count}, cap
# Key material must NEVER appear in the payload handed to the browser.
serialized = json.dumps(cap, ensure_ascii=False, default=str)
for secret in {all_keys!r}:
    assert secret not in serialized, "credential leaked into capability"
print("OK")
"""


class DeepLConfigShapeTests(unittest.TestCase):
    def _run(
        self,
        toml_text: str,
        keys: list[str],
        *,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_path = Path(temp_dir) / "secrets.toml"
            secret_path.write_text(textwrap.dedent(toml_text), encoding="utf-8")
            env = os.environ.copy()
            env.pop("DEEPL_API_KEYS", None)
            env.pop("DEEPL_API_KEY", None)
            env["LOGISTICS_PRO_SECRETS_FILE"] = str(secret_path)
            env["PYTHONPATH"] = str(ROOT)
            if extra_env:
                env.update(extra_env)
            assertions = LIST_ASSERT.format(
                keys=keys,
                configured=bool(keys),
                count=len(keys),
                all_keys=[KEY_ONE, KEY_TWO, SINGLE_KEY],
            )
            return subprocess.run(
                [sys.executable, "-c", assertions],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

    def _assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("OK", result.stdout)

    # ------------------------------------------------------------------ env
    def test_env_plural_json_list(self):
        self._assert_ok(self._run(
            "", [KEY_ONE, KEY_TWO],
            extra_env={"DEEPL_API_KEYS": f'["{KEY_ONE}", "{KEY_TWO}"]'},
        ))

    def test_env_plural_comma_separated(self):
        self._assert_ok(self._run(
            "", [KEY_ONE, KEY_TWO],
            extra_env={"DEEPL_API_KEYS": f"{KEY_ONE},{KEY_TWO}"},
        ))

    def test_env_singular(self):
        self._assert_ok(self._run(
            "", [SINGLE_KEY],
            extra_env={"DEEPL_API_KEY": SINGLE_KEY},
        ))

    # -------------------------------------------------------------- secrets
    def test_secrets_plural_table(self):
        self._assert_ok(self._run(
            f'[deepl]\napi_keys = ["{KEY_ONE}", "{KEY_TWO}"]\n',
            [KEY_ONE, KEY_TWO],
        ))

    def test_secrets_singular_table(self):
        self._assert_ok(self._run(
            f'[deepl]\napi_key = "{SINGLE_KEY}"\n',
            [SINGLE_KEY],
        ))

    def test_secrets_flat_plural_legacy(self):
        self._assert_ok(self._run(
            f'DEEPL_API_KEYS = ["{KEY_ONE}", "{KEY_TWO}"]\n',
            [KEY_ONE, KEY_TWO],
        ))

    def test_secrets_flat_singular(self):
        self._assert_ok(self._run(
            f'DEEPL_API_KEY = "{SINGLE_KEY}"\n',
            [SINGLE_KEY],
        ))

    # ------------------------------------------------------------- no config
    def test_no_config_is_empty_and_unconfigured(self):
        self._assert_ok(self._run("", []))

    # ------------------------------------------------------------ precedence
    def test_env_plural_beats_env_singular(self):
        self._assert_ok(self._run(
            "", [KEY_ONE],
            extra_env={
                "DEEPL_API_KEYS": f'["{KEY_ONE}"]',
                "DEEPL_API_KEY": SINGLE_KEY,
            },
        ))

    def test_env_singular_beats_secrets_plural(self):
        self._assert_ok(self._run(
            f'[deepl]\napi_keys = ["{KEY_ONE}", "{KEY_TWO}"]\n',
            [SINGLE_KEY],
            extra_env={"DEEPL_API_KEY": SINGLE_KEY},
        ))

    def test_secrets_plural_beats_secrets_singular(self):
        self._assert_ok(self._run(
            f'[deepl]\napi_keys = ["{KEY_ONE}", "{KEY_TWO}"]\n'
            f'api_key = "{SINGLE_KEY}"\n',
            [KEY_ONE, KEY_TWO],
        ))

    def test_duplicated_sources_are_not_concatenated(self):
        # Plural env + singular env + both secret shapes all present: ONLY the
        # highest-precedence source is used (no accidental key doubling).
        self._assert_ok(self._run(
            f'[deepl]\napi_keys = ["{KEY_TWO}"]\napi_key = "{SINGLE_KEY}"\n',
            [KEY_ONE],
            extra_env={
                "DEEPL_API_KEYS": f'["{KEY_ONE}"]',
                "DEEPL_API_KEY": SINGLE_KEY,
            },
        ))


if __name__ == "__main__":
    unittest.main()
