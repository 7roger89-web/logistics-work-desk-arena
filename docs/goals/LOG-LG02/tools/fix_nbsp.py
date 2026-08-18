"""Thay NBSP (U+00A0) bang space thuong trong tat ca file .py cua repo.

Nen tai: sau bo decoder mojibake, byte 0xA0 (NBSP goc) duoc phuc hoi thanh
ky tu U+00A0. Trong source code Python, NBSP khong can thiet va lam man
grep/log; Streamlit hien thi giong space thuong. Thay bang space an toan,
khong anh huong compile hay hanh vi.

Idempotent: khong co U+00A0 -> bo qua.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

fixed = 0
for p in sorted(pth for pth in REPO.rglob("*.py")
                if pth.parts[0] != ".git"):
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if "\u00a0" not in s:
        continue
    s2 = s.replace("\u00a0", " ")
    p.write_text(s2, encoding="utf-8")
    fixed += 1
    print(f"[NBSP] {p.relative_to(REPO)}", flush=True)
print(f"RESULT: nbsp_fixed={fixed}", flush=True)
