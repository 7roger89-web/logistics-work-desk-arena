# -*- coding: utf-8 -*-
"""SUA CHU TIENG VIET BI LOI (mojibake) — chay 1 lan tren may Owner.

Cach dung (cmd):
    cd /d D:\Logistics_App_GitHub
    python fix_vietnamese.py

Script tu quet MOI file .py trong thu muc repo, giai ma chu bi loi theo
thuat toan da duoc kiem chung (greedy cp1252-glyph -> utf-8), luu file
goc thanh <ten>.py.before_fix (chi lan dau), va in bao cao.
Khong can git, khong can internet, khong dong vao database.
"""
from __future__ import annotations

import glob
import os
import re
import sys

ARTIFACT_MAP = {
    "\u20ac": 0x80, "\u201a": 0x82, "\u0192": 0x83, "\u201e": 0x84,
    "\u2026": 0x85, "\u2020": 0x86, "\u2021": 0x87, "\u02c6": 0x88,
    "\u2030": 0x89, "\u0160": 0x8a, "\u2039": 0x8b, "\u0152": 0x8c,
    "\u017d": 0x8e, "\u2018": 0x91, "\u2019": 0x92, "\u201c": 0x93,
    "\u201d": 0x94, "\u2022": 0x95, "\u2013": 0x96, "\u2014": 0x97,
    "\u02dc": 0x98, "\u2122": 0x99, "\u0161": 0x9a, "\u203a": 0x9b,
    "\u0153": 0x9c, "\u017e": 0x9e, "\u0178": 0x9f,
}

# Mau mojibake de phat hien file bi loi (khong sua)
MOJIBAKE_PATTERNS = re.compile(
    r"Táº¡o|LÃ´|KhÃ¡ch|Báº|t|Dang cháº¡y|Ä\x90ang|vá»«a Ä'| cháº¡y Local|triá»ƒn khai"
)


def char_byte(char: str):
    o = ord(char)
    if 0x0080 <= o <= 0x00FF:
        return o
    if char in ARTIFACT_MAP:
        return ARTIFACT_MAP[char]
    return None


def is_valid_utf8(b: bytes) -> bool:
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def decode(text: str) -> str:
    """Giai ma mojibake: tham-lam phan doan glyph -> byte -> utf-8."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        b = char_byte(c)
        if b is None:
            out.append(c)
            i += 1
            continue
        best = None
        buf = bytearray()
        j = i
        while j < n:
            bb = char_byte(text[j])
            if bb is None:
                break
            buf.append(bb)
            if is_valid_utf8(buf):
                best = (buf.decode("utf-8"), j + 1)
            j += 1
        if best is not None:
            out.append(best[0])
            i = best[1]
        else:
            out.append(c)
            i += 1
    return "".join(out)


def fix_string(src: str) -> str:
    dec = decode(src)
    # Loai BOM (U+FEFF) o dau file vi Python khong cho phep ngoai string
    dec = dec.lstrip("\ufeff")
    # Sua cac truong hop dac biet (byte 91/92 trong "chot")
    dec = dec.replace("cht", "chốt").replace("Cht", "Chốt")
    dec = dec.replace("ch\u2018t", "chốt").replace("Ch\u2018t", "Chốt")
    return dec


def needs_fix(src: str) -> bool:
    if "\ufffd" in src:
        return True
    if MOJIBAKE_PATTERNS.search(src):
        return True
    return False


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    patterns = [
        os.path.join(here, "*.py"),
        os.path.join(here, "core", "*.py"),
        os.path.join(here, "views", "*.py"),
        os.path.join(here, "scripts", "*.py"),
        os.path.join(here, "tests", "*.py"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    files = sorted(set(files))

    fixed_count = 0
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
        if not needs_fix(src):
            continue
        backup = path + ".before_fix"
        if not os.path.exists(backup):
            with open(backup, "w", encoding="utf-8") as f:
                f.write(src)
        dec = fix_string(src)
        if dec == src:
            print(f"  SKIP (khong giai ma duoc): {path}")
            continue
        # Kiem tra syntax truoc khi luu
        try:
            compile(dec, path, "exec")
        except SyntaxError as e:
            print(f"  CANH BAO (khong luu, loi syntax): {path}: {e}")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(dec)
        fixed_count += 1
        print(f"  OK: {path}")

    print()
    print(f"Da sua: {fixed_count} file")
    if fixed_count == 0:
        print("Khong phat hien file bi loi. Da sach!")
    else:
        print("File goc da luu thanh <ten>.py.before_fix trong cung thu muc.")
        print("Nen chay: rd /s /q views\\__pycache__   roi   streamlit run web_app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
