#!/usr/bin/env python3
"""Known-red gate for the intentionally-red pytest suite.

Đọc junit XML do pytest sinh (``--junitxml``) và so tập FAILED/ERROR thực tế với
registry ``tests/known_red.txt`` (và tùy chọn ``tests/known_flaky.txt``).

Quy tắc thoát:
  * Có FAILED/ERROR mới không nằm trong registry (và không phải flaky đã đăng ký)
    => in rõ nodeid mới, exit 1. Registry không bao giờ "che" failure mới.
  * Nodeid trong registry nay không còn đỏ => in khối DRIFT (liệt kê nodeid, kèm
    dòng máy-đọc-được ``DRIFT_COUNT=<n>``), exit 0. Drift là tín hiệu cập nhật
    registry trong chính PR sửa được test, không phải lỗi chặn cứng.
  * Nodeid registry vắng mặt hoàn toàn trong junit (bị đổi tên/xóa?) => mặc định
    là FATAL: registry đã không còn mô tả sự thật run, exit 1. Chỉ khi truyền
    ``--allow-missing`` cho một ngoại lệ có chủ ý thì hạ xuống WARNING và exit 0.
  * Lỗi hạ tầng (thiếu file, XML hỏng, registry rỗng) => exit 2 (fail-closed).

Chỉ dùng thư viện chuẩn. Không deselect/xfail test nào: script đọc báo cáo,
không can thiệp vào quá trình pytest chạy.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXIT_OK = 0
EXIT_NEW_FAILURE = 1
EXIT_TOOLING = 2


class ToolingError(RuntimeError):
    """Lỗi hạ tầng của chính checker (thiếu file, XML hỏng...): fail-closed."""


def _load_nodeid_list(path: Path, *, allow_missing: bool = False) -> set[str]:
    if not path.is_file():
        if allow_missing:
            return set()
        raise ToolingError(f"required file not found: {path}")
    nodeids: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        nodeids.add(line)
    if not nodeids and not allow_missing:
        raise ToolingError(f"registry contains no nodeid: {path}")
    return nodeids


def _classname_to_nodeid(classname: str, name: str) -> str:
    """Chuyển classname junit ('pkg.mod.Class'/'pkg.mod') về nodeid pytest.

    pytest junit không kèm thuộc tính file, nên tách phần module bằng cách kiểm
    tra đường dẫn file thật trên đĩa (script chạy tại gốc repo đã checkout).
    Fallback: segment cuối viết hoa được coi là tên class.
    """
    parts = classname.split(".") if classname else []
    for k in range(len(parts), 0, -1):
        candidate = Path(*parts[:k]).with_suffix(".py")
        if candidate.exists():
            module = str(candidate)
            classes = parts[k:]
            if classes:
                return f"{module}::{'::'.join(classes)}::{name}"
            return f"{module}::{name}"
    if len(parts) > 1:
        module = str(Path(*parts[:-1]).with_suffix(".py"))
        return f"{module}::{parts[-1]}::{name}"
    return f"{classname}::{name}"


def _parse_junit(junit_path: Path) -> tuple[set[str], set[str]]:
    """Trả về (tập nodeid đỏ, tập mọi nodeid đã thu thập trong lần chạy)."""
    if not junit_path.is_file():
        raise ToolingError(f"junit report not found: {junit_path}")
    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError as exc:
        raise ToolingError(f"cannot parse junit XML {junit_path}: {exc}") from exc

    red: set[str] = set()
    collected: set[str] = set()
    for testcase in root.iter("testcase"):
        nodeid = _classname_to_nodeid(
            testcase.get("classname", ""), testcase.get("name", "")
        )
        collected.add(nodeid)
        if any(child.tag in ("failure", "error") for child in testcase):
            red.add(nodeid)
    return red, collected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Known-red gate cho bộ test đỏ có chủ ý.")
    parser.add_argument("--junit", required=True, type=Path, help="Đường dẫn junit XML.")
    parser.add_argument("--registry", required=True, type=Path, help="tests/known_red.txt.")
    parser.add_argument(
        "--flaky",
        type=Path,
        default=Path("tests/known_flaky.txt"),
        help="Danh sách flaky tùy chọn; vắng mặt được coi là rỗng.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Cố ý chấp nhận nodeid registry vắng mặt trong junit: hạ MISSING từ "
             "FATAL (exit 1) xuống WARNING (exit 0). Chỉ dùng cho ngoại lệ có chủ ý.",
    )
    args = parser.parse_args(argv)

    registered = _load_nodeid_list(args.registry)
    flaky = _load_nodeid_list(args.flaky, allow_missing=True)

    current_red, collected = _parse_junit(args.junit)

    new_failures = sorted(current_red - registered - flaky)
    drifted = sorted(nodeid for nodeid in registered if nodeid in collected and nodeid not in current_red)
    missing_from_run = sorted(nodeid for nodeid in registered if nodeid not in collected)
    flaky_red_now = sorted(current_red & flaky)

    print("=" * 72)
    print("KNOWN-RED GATE SUMMARY")
    print(f"  junit red (FAILED/ERROR) : {len(current_red)}")
    print(f"  registry known-red       : {len(registered)}")
    print(f"  registered flaky         : {len(flaky)}")
    print(f"  new failures/errors      : {len(new_failures)}")
    print(f"  drift (now passing)      : {len(drifted)}")
    print(f"  registry missing in run  : {len(missing_from_run)}"
          + ("" if args.allow_missing else " (FATAL; --allow-missing để hạ xuống WARNING)"))
    print("-" * 72)
    # Các dòng máy-đọc-được dưới đây giữ ổn định định dạng để CI/grep bám vào.
    print(f"NEW_COUNT={len(new_failures)}")
    print(f"DRIFT_COUNT={len(drifted)}")
    print(f"MISSING_COUNT={len(missing_from_run)}")
    print("=" * 72)

    if flaky_red_now:
        print("INFO: flaky nodeid đỏ ở lần chạy này (đã đăng ký, không tính là new):")
        for nodeid in flaky_red_now:
            print(f"  FLAKY-RED {nodeid}")

    if missing_from_run:
        if args.allow_missing:
            print("WARNING (--allow-missing): nodeid registry vắng mặt trong junit — "
                  "chấp nhận có chủ ý, hãy xác nhận đây không phải registry rot:")
        else:
            print("FATAL: nodeid registry vắng mặt trong junit (test bị đổi tên/xóa hoặc "
                  "sai id?). Registry không còn mô tả sự thật run — cập nhật registry hoặc "
                  "dùng --allow-missing cho ngoại lệ có chủ ý:")
        for nodeid in missing_from_run:
            print(f"  MISSING  {nodeid}")

    if drifted:
        print("DRIFT: các known-red sau đã pass/không còn đỏ — cập nhật registry trong PR này:")
        for nodeid in drifted:
            print(f"  DRIFT    {nodeid}")

    if new_failures:
        print("NEW FAILURES/ERRORS (không có trong known_red.txt) — gate FAIL:")
        for nodeid in new_failures:
            print(f"  NEW      {nodeid}")
        return EXIT_NEW_FAILURE

    if missing_from_run and not args.allow_missing:
        print("GATE FAIL: registry lệch sự thật do có MISSING (mặc định FATAL).")
        return EXIT_NEW_FAILURE

    print("GATE PASS: không có failure/error mới ngoài tập known-red đã đăng ký.")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ToolingError as exc:
        print(f"TOOLING ERROR: {exc}", file=sys.stderr)
        sys.exit(EXIT_TOOLING)
