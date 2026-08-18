"""Sua dong ConcurrentUpdateError bi mojibake trong core/database.py.

Loc dong co 'LÃ´' (mojibake cua 'Lô') trong f-string cua loi va thay bang
thong bao tieng Viet dung.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
p = REPO / "core/database.py"
src = p.read_text(encoding="utf-8")

pat = re.compile(
    r'raise ConcurrentUpdateError\(f"LÃ´ \{sid\} vá»«a Ä‘[^\n]*"\)'
)

def repl(m: re.Match) -> str:
    return ('raise ConcurrentUpdateError(f"Lô {sid} vừa được người khác '
            'cập nhật. Hãy Reload Data rồi lưu lại.")')

new, cnt = pat.subn(repl, src)
assert cnt > 0, "khong tim thay dong mojibake"
compile(new, str(p), "exec")
p.write_text(new, encoding="utf-8")
print("replaced:", cnt, "fffd:", new.count("\ufffd"),
      "mojibake_left:", len(re.findall(r"LÃ´|vá»«a", new)))
