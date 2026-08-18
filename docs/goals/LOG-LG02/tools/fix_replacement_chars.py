"""Sua ky tu U+FFFD (replacement char) trong cac file .py — mojet bai boc
khi decoder khong phuc hoi duoc byte goc.

Cach lam: voi moi U+FFFD, tra cuu chuoi goc tu file backup
/tmp/web_app_before_fix.py (ban mojibake goc) bang cach tim vi tri tuong
ung. Neu khong xac dinh duoc -> in ra de sua thu cong.

Chi chay tren views/web_app.py va core/database.py (cac file da fix).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path('views/web_app.py').resolve().parents[1]

# Map thu cong (da kiem chung voi backup goc): chuoi mojibake -> chuoi dung
# Duoc lap tu so sanh voi /tmp/web_app_before_fix.py (ban mojibake goc).
MANUAL = [
    ("Thỏa Thuận & B\ufffdn\ufffdGiao", "Thỏa Thuận & Bàn Giao"),
    ("Kh\ufffdch H\ufffdng", "Khách Hàng"),
    ("B\ufffdo Gi\ufffd", "Báo Giá"),
    ("B\ufffdo gi\ufffd", "Báo giá"),
    ("ng\ufffdi d\ufffdng", "người dùng"),
    ("cho ph\ufffdp runtime", "cho phép runtime"),
    ("cho ph\ufffdpruntime", "cho phép runtime"),
    ("ghi \ufffdè", "ghi đè"),
    ("B\ufffdt AUTH_REQUIRED", "Bật AUTH_REQUIRED"),
]


def fix_text(s: str) -> tuple[str, int]:
    n = 0
    for old, new in MANUAL:
        if old in s:
            cnt = s.count(old)
            s = s.replace(old, new)
            n += cnt
    return s, n


def main() -> None:
    targets = [REPO / "views" / "web_app.py", REPO / "core" / "database.py"]
    for p in targets:
        s = p.read_text(encoding="utf-8")
        before = s.count("\ufffd")
        s, n = fix_text(s)
        if before:
            p.write_text(s, encoding="utf-8")
        print(f"{p.name}: fffd before={before} manual_replaced={n} after={s.count(chr(0xfffd))}",
              flush=True)
        # bao cao moi ngu canh U+FFFD con sot
        for m in re.finditer(r".{20}\ufffd.{20}", s):
            print("  REMAIN:", repr(m.group(0)), flush=True)


if __name__ == "__main__":
    main()
