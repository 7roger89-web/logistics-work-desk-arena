#!/usr/bin/env python3
"""LG03 W1: Quet tat ca string literal user-visible trong views/ va core/.
Phan loai: VIETNAMESE_OK / ENGLISH_USER_VISIBLE / TECHNICAL_VISIBLE / MIXED_LANGUAGE.
Moji-bake: tim pattern mo gia ma.
Output: docs/goals/LOG-LG03/evidence/W1_raw_strings.json
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCAN_DIRS = [ROOT / "views", ROOT / "core"]
EXCLUDE_FILES = {"users.py", "state.py", "config.py"}  # users/state/config = internal

VIET_RE = re.compile(r"[\u00C0-\u024F]|(?:[A-Za-z]+\s*[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ])")
MOJI_RE = re.compile(r"Áº|Á»|Ã|Ä|Âª|Ã£|á»|áº")


def classify(s: str) -> str:
    has_vi = VIET_RE.search(s)
    # technical identifiers stay English by policy (keys, statuses)
    if re.fullmatch(r"[A-Z_][A-Z0-9_]*", s) or re.fullmatch(r"[a-z_][a-z0-9_]*", s):
        return "TECHNICAL_INTERNAL"
    is_ascii = all(ord(c) < 128 for c in s)
    if has_vi and is_ascii is False:
        if MOJI_RE.search(s):
            return "MOJIBAKE"
        return "VIETNAMESE_OK" if not VIET_RE.search(s.replace(" ", "")) is None and False else "VIETNAMESE_OK"
    return "ENGLISH_USER_VISIBLE"


def _classify_robust(s: str) -> str:
    has_vi = bool(VIET_RE.search(s))
    has_latin = bool(re.search(r"[A-Za-z]{2,}", s))
    if MOJI_RE.search(s):
        return "MOJIBAKE"
    if has_vi:
        return "VIETNAMESE_OK"
    if has_latin:
        return "ENGLISH_USER_VISIBLE"
    return "NON_TEXT"


def scan(path: Path) -> list[dict]:
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if len(v) < 2 or len(v) > 300:
                continue
            if v.isspace() or not v.strip():
                continue
            cat = _classify_robust(v)
            if cat == "NON_TEXT":
                continue
            out.append({"file": str(path.relative_to(ROOT)), "line": node.lineno,
                        "cat": cat, "text": v[:150]})
    return out


def main() -> None:
    results = []
    for d in SCAN_DIRS:
        for f in sorted(d.glob("*.py")):
            if f.name in EXCLUDE_FILES:
                continue
            results.extend(scan(f))
    summary = {}
    for r in results:
        summary[r["cat"]] = summary.get(r["cat"], 0) + 1
    report = {"summary": summary, "items": results}
    out_path = ROOT / "docs/goals/LOG-LG03/evidence/W1_raw_strings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("files scanned:", len({r['file'] for r in results}))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
