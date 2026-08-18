"""Decode mojibake strings found in core/database.py by reversing double-encoding.

Strategy: for each candidate mojibake string, try variants of
  text.encode(enc1).decode(enc2) / text.encode(enc2).decode(enc1)
and smart-quote/NBSP normalization until a plausible all-Vietnamese string emerges.
"""
import codecs
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

CANDIDATES = [
    "Khoản thu má»›i phải có request identity.",
    "Lá»‹ch sử thanh toán không được thêm/xoá trùc tiếp.",
    "Lá»‹ch sử thanh toán cũ không được ghi Äè.",
    "Lá»‹ch sử thanh toán không được Ä‘á»•i ID hoặc xoá.",
    "Khoản thu Đã được xử lý trÆ°á»›c Ä‘ó.",
]


def reverse_double_encoding(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen = set()
    for enc in ("latin-1", "cp1252", "windows-1252"):
        # variant 1: original UTF-8 bytes were read as `enc`, then stored
        try:
            back = text.encode(enc).decode("utf-8")
            if back not in seen and _is_plausible(back):
                seen.add(back)
                results.append((back, f"encode({enc})/decode(utf-8)"))
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        # variant 2: original `enc`-encoded bytes were read as UTF-8
        try:
            back = text.encode("utf-8").decode(enc)
            if back not in seen and _is_plausible(back):
                seen.add(back)
                results.append((back, f"encode(utf-8)/decode({enc})"))
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    # variant 3: normalize smart quotes / NBSP before reversing
    norm = (
        text.replace("\u00c2\u00a0", " ")
        .replace("\u201c", '"').replace("\u201d", '"')
        .replace("\u2018", "'").replace("\u2019", "'")
    )
    for enc in ("latin-1", "cp1252"):
        try:
            back = norm.encode(enc).decode("utf-8")
            if back not in seen and _is_plausible(back):
                seen.add(back)
                results.append((back, f"norm+encode({enc})/decode(utf-8)"))
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    return results


def _is_plausible(s: str) -> bool:
    # plausible = mostly printable ASCII/Vietnamese letters, no replacement chars
    if not s or "\ufffd" in s:
        return False
    weird = sum(1 for c in s if not (c.isprintable() or c in "·—–"))
    return weird == 0


def main() -> int:
    for cand in CANDIDATES:
        print(f"\nMOJIBAKE: {cand!r}")
        decoded = reverse_double_encoding(cand)
        if decoded:
            for back, method in decoded:
                print(f"  -> {back!r}  ({method})")
        else:
            # byte-level inspection
            print("  (no clean reverse; raw bytes below)")
            print("  ", cand.encode("utf-8").hex(" "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
