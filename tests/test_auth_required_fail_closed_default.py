"""LOGI_AUTH_FAIL_CLOSED_DEFAULT_01 — authentication defaults fail closed."""
from __future__ import annotations

from unittest.mock import patch

import core.config as config


def test_missing_auth_setting_defaults_to_required() -> None:
    with patch.object(config, "get_setting", return_value="true") as get_setting:
        assert config._load_auth_required() is True
    get_setting.assert_called_once_with(
        "AUTH_REQUIRED",
        ("auth", "required"),
        "AUTH_REQUIRED",
        default="true",
    )


def test_explicit_false_keeps_local_dev_escape_hatch() -> None:
    with patch.object(config, "get_setting", return_value="false"):
        assert config._load_auth_required() is False


def test_explicit_true_requires_login() -> None:
    with patch.object(config, "get_setting", return_value="true"):
        assert config._load_auth_required() is True
