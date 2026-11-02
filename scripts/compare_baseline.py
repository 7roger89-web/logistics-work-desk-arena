#!/usr/bin/env python3
"""So kết quả pytest với tests/BASELINE_FAILED.txt.

Baseline là danh sách node id đang đỏ có chủ ý (nợ cũ). Chỉ node MỚI làm fail.
Node trong baseline mà nay xanh được in ra để dọn khỏi file.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASELINE = Path("tests/BASELINE_FAILED.txt")


def load_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def node_id(case: ET.Element) -> str:
    parts = [p for p in (case.get("classname") or "").split(".") if p]
    name = case.get("name") or ""
    if parts and parts[-1][:1].isupper():
        klass = parts.pop()
        return "/".join(parts) + ".py::" + klass + "::" + name
    return "/".join(parts) + ".py::" + name


def failed_nodes(xml_path: Path) -> set[str]:
    root = ET.parse(xml_path).getroot()
    return {
        node_id(case)
        for case in root.iter("testcase")
        if case.find("failure") is not None or case.find("error") is not None
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("junit", type=Path)
    ap.add_argument("--update", action="store_true", help="ghi lại baseline từ lần chạy này")
    args = ap.parse_args()

    if not args.junit.exists():
        print(f"Không thấy file kết quả: {args.junit}")
        return 1

    baseline = load_baseline(BASELINE)
    failed = failed_nodes(args.junit)

    if args.update:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            "# Lỗi đã biết. Chỉ dòng ở đây mới được phép đỏ.\n"
            "# Dọn được lỗi nào thì xoá dòng đó.\n"
            + "".join(f"{n}\n" for n in sorted(failed)),
            encoding="utf-8",
        )
        print(f"Đã ghi baseline: {len(failed)} lỗi.")
        return 0

    new = sorted(failed - baseline)
    fixed = sorted(baseline - failed)

    if fixed:
        print(f"\nĐã sửa được {len(fixed)} lỗi cũ — xoá khỏi baseline:")
        for node in fixed:
            print(f"  + {node}")

    if new:
        print(f"\nLỖI MỚI: {len(new)}")
        for node in new:
            print(f"  - {node}")
        return 1

    print(f"\nKhông có lỗi mới. Còn {len(failed)} lỗi cũ trong baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
