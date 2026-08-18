#!/usr/bin/env python3
"""LG03: Sửa mojibake UTF-8 dạng double-encoding trong các file views/core bị chạm.
Quy tắc: KHÔNG dùng double-encoding ngược để "sửa" — thay trực tiếp bằng chuỗi
tiếng Việt đúng (nguồn gốc chuẩn). Chỉ chạm các chuỗi đã xác minh byte.
An toàn: in ra thay đổi; có flag --apply để ghi.
Sử dụng: python3 docs/goals/LOG-LG03/tools/fix_mojibake_lg03.py [--apply]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

# (path, pattern-bytes, replacement-clean-utf8) — đã xác minh byte nhị phân
KNOWN = [
    ("views/shipment_360.py",
     b'\xc4\x90\xc3\x83 THU', 'ĐÃ THU'),
    ("views/shipment_360.py",
     b'\xc4\x90\xc3\x83 TR\xc3\x82\xc2\xa2', 'ĐÃ TRẢ'),
    ("views/shipment_360.py",
     b'\xc4\x90\xc3\x83 TR\xc3\x82\xc2\xa3', 'ĐÃ TRẢ'),
    ("views/shipment_360.py",
     b'CHI PH\xc3\x8d \xc4\x90\xc3\x83 BI\xc3\x8aT', 'CHI PHÍ ĐÃ BIẾT'),
    ("views/shipment_360.py",
     b'CHI PH\xc3\x8d \xc4\x90\xc3\x83 BI\xc3\x83\xc2\x8aT', 'CHI PHÍ ĐÃ BIẾT'),
]


def scan_apply(apply: bool) -> int:
    fixed = 0
    for rel, pat, repl in KNOWN:
        p = REPO / rel
        if not p.exists():
            print(f"SKIP (không tồn tại): {rel}")
            continue
        b = p.read_bytes()
        if pat in b:
            b2 = b.replace(pat, repl.encode('utf-8'))
            if apply:
                p.write_bytes(b2)
                print(f"{'APPLIED' if apply else 'WOULD FIX'}: {rel} — {pat[:30]} -> {repl}")
            else:
                print(f"{'FOUND' :7s}: {rel} — {pat[:30]} -> {repl}")
            fixed += 1
    return fixed


def scan_full_repo():
    """Quét toàn repo tìm chuỗi dạng mojibake double-encoding điển hình."""
    pat = re.compile(rb'[\xc0-\xdf][\x80-\xbf](?:[\xc0-\xdf][\x80-\xbf])+[A-Z ]')
    hits = []
    for f in sorted(REPO.glob("**/*.py")):
        if ".git" in f.parts or "__pycache__" in f.parts:
            continue
        b = f.read_bytes()
        for m in pat.finditer(b):
            seg = b[max(0, m.start() - 20):m.end() + 20]
            hits.append((str(f.relative_to(REPO)), m.start(), seg))
    return hits


def main() -> None:
    apply_mode = "--apply" in sys.argv
    n = scan_apply(apply_mode)
    print(f"Total: {n}")
    if not apply_mode:
        hits = scan_full_repo()
        print(f"\nToàn repo: {len(hits)} đoạn nghi mojibake:")
        for path, off, seg in hits[:40]:
            print(f"  {path}:{off} {seg!r}")


if __name__ == "__main__":
    main()
