"""Phase E — shim tương thích ngược cho tên cấu hình cũ.

Bề mặt cần khóa:

* env cũ ``MONGODB_URI`` và section cũ ``[mongodb]`` / ``[google]`` vẫn đọc được;
* tên mới luôn thắng trên mọi kênh, thứ tự ưu tiên env > st.secrets > secrets.toml
  không đổi;
* mỗi alias phát cảnh báo DeprecationWarning đúng MỘT lần/process;
* không có cấu hình tên cũ thì không cảnh báo âm thầm (negative).
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import warnings
from pathlib import Path

import pytest

import core.config as cfg

ROOT = Path(__file__).resolve().parents[1]

_LEGACY_ENV_VARS = ("MONGO_URI", "MONGODB_URI", "MONGO_DB_NAME", "GEMINI_API_KEY", "GEMINI_KEYS")


@pytest.fixture(autouse=True)
def _isolate_config(monkeypatch, tmp_path):
    for name in _LEGACY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    secrets = tmp_path / "secrets.toml"
    monkeypatch.setenv("LOGISTICS_PRO_SECRETS_FILE", str(secrets))
    cfg._load_file_secrets.cache_clear()
    saved = cfg._WARNED_LEGACY_ALIASES.copy()
    cfg._WARNED_LEGACY_ALIASES.clear()
    yield secrets
    cfg._WARNED_LEGACY_ALIASES.clear()
    cfg._WARNED_LEGACY_ALIASES.update(saved)
    cfg._load_file_secrets.cache_clear()


def _write(secrets: Path, content: str) -> None:
    secrets.write_text(textwrap.dedent(content), encoding="utf-8")
    cfg._load_file_secrets.cache_clear()


def _deprecation_warnings(record: list[warnings.WarningMessage]) -> list[str]:
    return [str(w.message) for w in record if issubclass(w.category, DeprecationWarning)]


# ---------------------------------------------------------------- env legacy

def test_legacy_env_mongodb_uri_is_accepted_and_warns_once(monkeypatch, _isolate_config):
    monkeypatch.setenv("MONGODB_URI", "mongodb://legacy-env.invalid:27017")
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        first = cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
        second = cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
    assert first == second == "mongodb://legacy-env.invalid:27017"
    messages = _deprecation_warnings(record)
    assert len(messages) == 1
    assert "MONGODB_URI" in messages[0] and "MONGO_URI" in messages[0]


def test_new_env_wins_over_legacy_env_without_warning(monkeypatch, _isolate_config):
    monkeypatch.setenv("MONGO_URI", "mongodb://new.invalid:27017")
    monkeypatch.setenv("MONGODB_URI", "mongodb://old.invalid:27017")
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        value = cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
    assert value == "mongodb://new.invalid:27017"
    assert _deprecation_warnings(record) == []


# ----------------------------------------------------------- sections legacy

def test_legacy_mongodb_section_resolves_with_one_warning(_isolate_config):
    _write(_isolate_config, """
        [mongodb]
        uri = "mongodb://legacy-section.invalid:27017"
        database = "legacy_db"
    """)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        uri = cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
        db_name = cfg.get_setting(
            "MONGO_DB_NAME", ("mongo", "database"), "MONGO_DB_NAME",
            default="", legacy_secret_paths=(("mongodb", "database"),),
        )
        # Lần gọi lặp lại cùng alias không được cảnh báo lại.
        cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
    assert uri == "mongodb://legacy-section.invalid:27017"
    assert db_name == "legacy_db"
    messages = _deprecation_warnings(record)
    # Hai alias khác nhau ([mongodb].uri, [mongodb].database) mỗi alias cảnh báo một lần;
    # lần gọi lặp lại uri ở trên không được thêm warning thứ ba.
    assert len(messages) == 2
    assert any("[mongodb].uri" in m and "[mongo].uri" in m for m in messages)
    assert any("[mongodb].database" in m and "[mongo].database" in m for m in messages)


def test_new_mongo_section_wins_over_legacy_section(_isolate_config):
    _write(_isolate_config, """
        [mongo]
        uri = "mongodb://new-section.invalid:27017"
        database = "new_db"
        [mongodb]
        uri = "mongodb://old-section.invalid:27017"
        database = "old_db"
    """)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        uri = cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
        db_name = cfg.get_setting(
            "MONGO_DB_NAME", ("mongo", "database"), "MONGO_DB_NAME",
            default="", legacy_secret_paths=(("mongodb", "database"),),
        )
    assert uri == "mongodb://new-section.invalid:27017"
    assert db_name == "new_db"
    assert _deprecation_warnings(record) == []


def test_legacy_google_section_resolves_and_new_gemini_wins(_isolate_config):
    _write(_isolate_config, """
        [google]
        api_key = "legacy-google-key"
        api_keys = ["legacy-google-1", "legacy-google-2"]
        model = "legacy-model"
    """)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        single = cfg.get_setting(
            "GEMINI_API_KEY", ("gemini", "api_key"), "GEMINI_API_KEY",
            legacy_secret_paths=(("google", "api_key"),),
        )
        keys = cfg.get_list_setting(
            "GEMINI_KEYS", ("gemini", "api_keys"), "GEMINI_KEYS",
            legacy_secret_paths=(("google", "api_keys"),),
        )
        model = cfg.get_setting(
            "GEMINI_MODEL", ("gemini", "model"), "GEMINI_MODEL",
            default="gemini-3.6-flash",
            legacy_secret_paths=(("google", "model"),),
        )
    assert single == "legacy-google-key"
    assert keys == ["legacy-google-1", "legacy-google-2"]
    assert model == "legacy-model"
    assert len(_deprecation_warnings(record)) == 3  # mỗi alias một lần

    _write(_isolate_config, """
        [gemini]
        api_key = "new-gemini-key"
        api_keys = ["new-1"]
        model = "new-model"
        [google]
        api_key = "legacy-google-key"
    """)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        single = cfg.get_setting(
            "GEMINI_API_KEY", ("gemini", "api_key"), "GEMINI_API_KEY",
            legacy_secret_paths=(("google", "api_key"),),
        )
        keys = cfg.get_list_setting(
            "GEMINI_KEYS", ("gemini", "api_keys"), "GEMINI_KEYS",
            legacy_secret_paths=(("google", "api_keys"),),
        )
        model = cfg.get_setting(
            "GEMINI_MODEL", ("gemini", "model"), "GEMINI_MODEL",
            default="gemini-3.6-flash",
            legacy_secret_paths=(("google", "model"),),
        )
    assert single == "new-gemini-key"
    assert keys == ["new-1"]
    assert model == "new-model"
    assert _deprecation_warnings(record) == []


def test_no_legacy_config_means_no_warning(_isolate_config):
    _write(_isolate_config, """
        [mongo]
        uri = "mongodb://only-new.invalid:27017"
    """)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        cfg.get_setting(
            "MONGO_URI", ("mongo", "uri"), "MONGO_URI",
            legacy_env="MONGODB_URI",
            legacy_secret_paths=(("mongodb", "uri"),),
        )
    assert _deprecation_warnings(record) == []


# ------------------------------------------------------- end-to-end subprocess

def test_module_constants_load_from_legacy_names_in_fresh_process(tmp_path):
    """Resolution lúc import module với secrets CHỈ dùng tên cũ + cảnh báo."""
    secret_path = tmp_path / "secrets.toml"
    secret_path.write_text(textwrap.dedent("""
        [mongodb]
        uri = "mongodb://e2e-legacy.invalid:27017"
        database = "e2e_legacy_db"
        [google]
        api_keys = ["e2e-google-1"]
        model = "e2e-model"
    """), encoding="utf-8")
    env = os.environ.copy()
    env["LOGISTICS_PRO_SECRETS_FILE"] = str(secret_path)
    env["PYTHONPATH"] = str(ROOT)
    for name in _LEGACY_ENV_VARS:
        env.pop(name, None)
    snippet = (
        "import warnings, core.config as c\n"
        "with warnings.catch_warnings(record=True) as rec:\n"
        "    warnings.simplefilter('always')\n"
        "    import importlib; importlib.reload(c)\n"
        "msgs=[str(w.message) for w in rec if issubclass(w.category, DeprecationWarning)]\n"
        "assert c.MONGO_URI == 'mongodb://e2e-legacy.invalid:27017', c.MONGO_URI\n"
        "assert c.MONGO_DB_NAME == 'e2e_legacy_db', c.MONGO_DB_NAME\n"
        "assert c.GEMINI_API_KEYS == ['e2e-google-1'], c.GEMINI_API_KEYS\n"
        "assert c.GEMINI_MODEL == 'e2e-model', c.GEMINI_MODEL\n"
        "assert any('MONGODB_URI' in m or '[mongodb]' in m for m in msgs), msgs\n"
        "assert any('[google]' in m for m in msgs), msgs\n"
        "print('E2E_LEGACY_OK', len(msgs))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", snippet], cwd=ROOT, env=env,
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "E2E_LEGACY_OK" in result.stdout
