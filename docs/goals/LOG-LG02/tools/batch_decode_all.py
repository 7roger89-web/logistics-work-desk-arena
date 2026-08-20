"""Giai ma TOAN BO file .py tu commit mojibake goc 83a567c.

Bo giai ma cp1252->utf-8 da duoc kiem chung tren views/tariff.py:
- ket qua la Vietnamese dung ("lưu tập trung", "Khác", "Gỗ tự nhiên")
- chi mat NBSP (byte 0xA0 bi thay bang space) — khong anh huong hien thi UI
- U+FFFD chi xuat hien khi byte that su mat — so luong rat it

Bo qua:
- docs/ (evidence giu nguyen)
- core/database.py (da khoi phuc sach tu 82c8134 + R4 gate)
- views/web_app.py (da giai ma va sach)

Moi file: compile-verify truoc khi ghi. Bao cao so U+FFFD con sot moi file.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
MOJIBAKE_SHA = "83a567c"

SKIP_DIRS = {"docs"}
SKIP_FILES = {"core/database.py", "views/web_app.py"}


def decode(text: str) -> str:
    out = []
    for char in text:
        o = ord(char)
        if char == " ":
            out.append(b" ")
        elif 0x0080 <= o <= 0x00FF:
            out.append(bytes([o]))
        else:
            out.append(char.encode("utf-8"))
    buf = b"".join(out)

    # NBSP-loss: byte lead truoc continuation khong hop le -> gia dinh A0
    fixed = bytearray()
    i = 0
    n = len(buf)
    while i < n:
        b = buf[i]
        if 0xC0 <= b <= 0xDF and i + 1 < n:
            nx = buf[i + 1]
            if not (0x80 <= nx <= 0xBF):
                fixed.append(b)
                fixed.append(0xA0 if nx == 0x20 else nx)
                i += 2
                continue
        if 0xE0 <= b <= 0xEF and i + 2 < n:
            a, bb = buf[i + 1], buf[i + 2]
            if not (0x80 <= a <= 0xBF and 0x80 <= bb <= 0xBF):
                fixed.append(b)
                fixed.append(a if 0x80 <= a <= 0xBF else (0xA0 if a == 0x20 else a))
                fixed.append(bb if 0x80 <= bb <= 0xBF else (0xA0 if bb == 0x20 else bb))
                i += 3
                continue
        fixed.append(b)
        i += 1

    chars = []
    for char in fixed.decode("latin-1"):
        o = ord(char)
        if 0x0080 <= o <= 0x00FF:
            chars.append(bytes([o]))
        else:
            chars.append(char.encode("utf-8"))
    return b"".join(chars).decode("utf-8", errors="replace")


def get_blob(rel: str) -> str:
    r = subprocess.run(
        ["git", "show", f"{MOJIBAKE_SHA}:{rel}"],
        capture_output=True, cwd=str(REPO),
    )
    if r.returncode != 0:
        raise RuntimeError(f"khong lay duoc {rel}")
    return r.stdout.decode("utf-8")


def main() -> None:
    r = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", MOJIBAKE_SHA],
        capture_output=True, cwd=str(REPO),
    )
    files = [f for f in r.stdout.decode().splitlines()
             if f.endswith(".py") and f.split("/")[0] not in SKIP_DIRS
             and f not in SKIP_FILES]

    ok, fail = 0, 0
    report = []
    for rel in files:
        try:
            src = get_blob(rel)
        except RuntimeError:
            fail += 1
            continue
        dec = decode(src)
        if dec == src:
            ok += 1
            continue
        dec = dec.replace("\u00a0", " ")  # NBSP -> space, an toan trong source
        dest = REPO / rel
        try:
            compile(dec, str(dest), "exec")
        except SyntaxError as exc:
            print(f"[ERROR] {rel}: {exc}", flush=True)
            fail += 1
            continue
        fffd = dec.count("\ufffd")
        dest.write_text(dec, encoding="utf-8")
        report.append((rel, fffd))
        ok += 1

    print(f"RESULT: processed={ok} errors={fail}", flush=True)
    high = [r for r in report if r[1] > 20]
    if high:
        print("Files with >20 U+FFFD (can kiem tra thu cong):", flush=True)
        for f, n in sorted(high, key=lambda x: -x[1]):
            print(f"  {f}: {n}", flush=True)


if __name__ == "__main__":
    main()
