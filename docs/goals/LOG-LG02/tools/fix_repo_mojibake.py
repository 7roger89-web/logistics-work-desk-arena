"""Sua toan bo file Python trong repo bi mojibake encoding (fix repo-wide).

Coi fix_mojibake.py da sua views/web_app.py. Quet TOAN BO .py trong repo,
ap dung cung bo decoder (idempotent: bo qua file khong con artifact char),
compile-verify tung file truoc khi ghi, va xoa __pycache__ cu.

Chu y: mojibake doc (.md) KHONG sua — do la bang chung (evidence) giu nguyen.

Su dung (tu root repo, tren Windows cung duoc):
    python docs\goals\LOG-LG02\tools\fix_repo_mojibake.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DOC_DIRS = {REPO / "docs"}

_ARTIFACT_CHARS = set("€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ")
_ARTIFACT_MAP: dict[str, int] = {
    "€": 0x80, "‚": 0x82, "ƒ": 0x83, "„": 0x84, "…": 0x85, "†": 0x86,
    "‡": 0x87, "ˆ": 0x88, "‰": 0x89, "Š": 0x8A, "‹": 0x8B, "Œ": 0x8C,
    "Ž": 0x8E, "‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94, "•": 0x95,
    "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9A, "›": 0x9B,
    "œ": 0x9C, "ž": 0x9E, "Ÿ": 0x9F,
}
# Ky tu mojibake don gian (0x80-0xFF va 0xC0-0xFF) ngoai cac artifact tren.
_MOJIBAKE_RE = re.compile(
    r"[€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ"
    r"\u0080\u0081\u0084\u008b\u008d\u008f\u0090\u009d\u00a0-\u00ff]"
)


def decode_mojibake(text: str) -> bytes:
    out = bytearray()
    for char in text:
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            out.append(code)
        elif char in _ARTIFACT_MAP:
            out.append(_ARTIFACT_MAP[char])
        else:
            out.extend(char.encode("utf-8"))
    return bytes(out)


def fix_nbsp_loss(buf: bytes) -> bytes:
    fixed = bytearray()
    i = 0
    n = len(buf)
    while i < n:
        byte = buf[i]
        if 0xC0 <= byte <= 0xDF and i + 1 < n:
            nxt = buf[i + 1]
            if not (0x80 <= nxt <= 0xBF):
                fixed.append(byte)
                fixed.append(0xA0 if nxt == 0x20 else nxt)
                i += 2
                continue
        if 0xE0 <= byte <= 0xEF and i + 2 < n:
            a, b = buf[i + 1], buf[i + 2]
            if not (0x80 <= a <= 0xBF and 0x80 <= b <= 0xBF):
                fixed.append(byte)
                fixed.append(a if 0x80 <= a <= 0xBF else (0xA0 if a == 0x20 else a))
                fixed.append(b if 0x80 <= b <= 0xBF else (0xA0 if b == 0x20 else b))
                i += 3
                continue
        fixed.append(byte)
        i += 1
    return bytes(fixed)


def fix_file(path: Path) -> str:
    """Fix 1 file .py. Tra ve "FIXED"/"CLEAN"/"SKIP"/"ERROR". """
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return "SKIP"

    if original.startswith("\ufeff"):
        original = original[1:]

    # Idempotent: khong con artifact char -> file sach.
    if not any(c in _ARTIFACT_CHARS for c in original):
        # Van kiem mojibake don gian (0xC0-0xFF) de bao dam.
        if not _MOJIBAKE_RE.search(original):
            return "CLEAN"
        # Co mojibake don gian nhung khong co artifact -> chi chay pass 2.
        buf = original.encode("utf-8")
    else:
        buf = decode_mojibake(original)
        buf = fix_nbsp_loss(buf)

    fixed_chars = []
    for char in buf.decode("latin-1"):
        code = ord(char)
        if 0x0080 <= code <= 0x00FF:
            fixed_chars.append(char.encode("latin-1"))
        else:
            fixed_chars.append(char.encode("utf-8"))
    fixed = b"".join(fixed_chars).decode("utf-8", errors="replace")

    if fixed == original:
        return "CLEAN"

    # Validate: phai compile duoc va khong duoc mat noi dung.
    try:
        compile(fixed, str(path), "exec")
    except SyntaxError:
        return "ERROR"

    # Khong duoc giam qua 10% chieu dai (bao ve danh mat du lieu).
    if len(fixed) < len(original) * 0.9:
        return "ERROR"

    path.write_text(fixed, encoding="utf-8")
    return "FIXED"


def clean_pycache(root: Path) -> int:
    removed = 0
    for d in root.rglob("__pycache__"):
        if d.is_dir():
            for f in d.iterdir():
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
            try:
                d.rmdir()
            except OSError:
                pass
    return removed


def main() -> int:
    py_files = sorted(p for p in REPO.rglob("*.py")
                      if not any(d in p.parents for d in {REPO / ".git"}))

    fixed, clean, skip, error = 0, 0, 0, 0
    for p in py_files:
        rel = p.relative_to(REPO)
        if rel.parts[0] == "docs":
            # Doc mau/ket qua khong sua (evidence giu nguyen).
            skip += 1
            continue
        try:
            res = fix_file(p)
        except Exception as exc:  # noqa: BLE001
            print(f"  [EXC ] {rel}: {exc}", flush=True)
            error += 1
            continue
        if res == "FIXED":
            fixed += 1
            print(f"  [FIXED] {rel}", flush=True)
        elif res == "CLEAN":
            clean += 1
        elif res == "SKIP":
            skip += 1
        else:
            error += 1
            print(f"  [ERROR] {rel} — khong sua (can kiem tra thu cong)", flush=True)

    removed = clean_pycache(REPO)
    print(f"\nRESULT: FIXED={fixed} CLEAN={clean} SKIP(doc)={skip} ERROR={error} "
          f"pycache_removed={removed}", flush=True)
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
