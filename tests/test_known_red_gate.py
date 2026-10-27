"""Phase A1 — khóa hành vi scripts/check_known_red.py sau hardening.

Bề mặt cần khóa:

* NEW failure/error => exit 1, registry không che failure mới;
* DRIFT (known-red nay pass) => non-fatal exit 0, in dòng ``DRIFT_COUNT=<n>``;
* MISSING (nodeid registry vắng mặt trong junit) => mặc định FATAL exit 1;
  cờ ``--allow-missing`` hạ xuống WARNING và cho exit 0;
* lỗi hạ tầng (thiếu junit, XML hỏng, registry rỗng) => exit 2.

Junit tổng hợp cố tình dùng classname trỏ tới file test có thật trên đĩa để
hàm chuẩn hóa classname -> nodeid giải đúng như khi chạy pytest thật.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_known_red", ROOT / "scripts" / "check_known_red.py"
)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)  # type: ignore[union-attr]

# classname -> nodeid mong đợi (file test có thật trong repo).
PASSING = "tests/test_config_loader.py::ConfigLoaderTests::test_legacy_flat_secrets"
PASSING_CLASSNAME = "tests.test_config_loader.ConfigLoaderTests"
RED = "tests/test_lg08_1_safety.py::test_parse_bool"
RED_CLASSNAME = "tests.test_lg08_1_safety"
RENAMED_AWAY = "tests/test_lg08_1_safety.py::test_identity_gate_enforcement"


def _junit(cases: list[tuple[str, str, bool]], path: Path) -> Path:
    """cases: (classname, name, is_red)."""
    body = ['<testsuites><testsuite name="synthetic" tests="%d">' % len(cases)]
    for classname, name, is_red in cases:
        if is_red:
            body.append(
                f'<testcase classname="{classname}" name="{name}">'
                '<failure message="synthetic">traceback</failure></testcase>'
            )
        else:
            body.append(f'<testcase classname="{classname}" name="{name}"/>')
    body.append("</testsuite></testsuites>")
    path.write_text("".join(body), encoding="utf-8")
    return path


def _write_registry(path: Path, nodeids: list[str]) -> Path:
    path.write_text("# synthetic registry\n" + "\n".join(nodeids) + "\n", encoding="utf-8")
    return path


def _run(tmp_path: Path, registry: list[str], cases, *extra: str):
    junit = _junit(cases, tmp_path / "report.xml")
    reg = _write_registry(tmp_path / "known_red.txt", registry)
    return checker.main([
        "--junit", str(junit), "--registry", str(reg),
        "--flaky", str(tmp_path / "absent_flaky.txt"),
        *extra,
    ])


def _cases(red: bool = True):
    return [
        (PASSING_CLASSNAME, "test_legacy_flat_secrets", False),
        (RED_CLASSNAME, "test_parse_bool", red),
    ]


def test_clean_run_matches_registry(tmp_path, capsys):
    rc = _run(tmp_path, [RED], _cases())
    out = capsys.readouterr().out
    assert rc == 0
    assert "NEW_COUNT=0" in out and "MISSING_COUNT=0" in out and "DRIFT_COUNT=0" in out
    assert "GATE PASS" in out


def test_new_failure_is_fatal(tmp_path, capsys):
    # Registry không rỗng (chứa một test đang pass) nhưng không chứa nodeid đỏ,
    # nên nodeid đỏ là NEW => exit 1. Registry rỗng là lỗi hạ tầng exit 2 (test riêng).
    rc = _run(tmp_path, [PASSING], _cases())
    out = capsys.readouterr().out
    assert rc == 1
    assert "NEW_COUNT=1" in out and "NEW " in out and RED in out


def test_drift_is_non_fatal_and_machine_readable(tmp_path, capsys):
    # Registry chứa một nodeid vẫn được thu thập nhưng đã pass => DRIFT.
    rc = _run(tmp_path, [RED, PASSING], _cases(red=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRIFT_COUNT=1" in out and "DRIFT " in out and PASSING in out


def test_missing_nodeid_is_fatal_by_default(tmp_path, capsys):
    # Registry chứa nodeid không hề xuất hiện trong junit (test bị đổi tên/xóa).
    rc = _run(tmp_path, [RED, RENAMED_AWAY], _cases())
    out = capsys.readouterr().out
    assert rc == 1
    assert "MISSING_COUNT=1" in out and "FATAL" in out and RENAMED_AWAY in out
    assert "GATE FAIL" in out


def test_allow_missing_downgrades_to_warning(tmp_path, capsys):
    rc = _run(tmp_path, [RED, RENAMED_AWAY], _cases(), "--allow-missing")
    out = capsys.readouterr().out
    assert rc == 0
    assert "MISSING_COUNT=1" in out and "WARNING (--allow-missing)" in out
    assert "GATE PASS" in out


def test_tooling_failures_exit_two(tmp_path):
    junit = _junit(_cases(), tmp_path / "report.xml")
    reg = _write_registry(tmp_path / "known_red.txt", [RED])
    with pytest.raises(checker.ToolingError):
        checker.main(["--junit", str(tmp_path / "nope.xml"), "--registry", str(reg)])
    corrupt = tmp_path / "bad.xml"
    corrupt.write_text("<not-valid", encoding="utf-8")
    with pytest.raises(checker.ToolingError):
        checker.main(["--junit", str(corrupt), "--registry", str(reg)])
    empty_reg = tmp_path / "empty.txt"
    empty_reg.write_text("# only comments\n", encoding="utf-8")
    with pytest.raises(checker.ToolingError):
        checker.main(["--junit", str(junit), "--registry", str(empty_reg)])
