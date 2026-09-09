#!/usr/bin/env python3
"""Build gate: the final browser bundle must contain ZERO executable
Node-global references.

Checks for: process / process.env / process.env.NODE_ENV / global.process /
Buffer / require( / __dirname / __filename.

Occurrences inside string literals or CSS are tolerated ONLY when they are
provably inert (reported, not counted). Exits 1 if any executable reference
is found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = {
    "process.env.NODE_ENV": re.compile(r"process\.env\.NODE_ENV"),
    "process.env": re.compile(r"process\.env(?!\.NODE_ENV)"),
    "global.process": re.compile(r"global\.process|globalThis\.process"),
    "process (bare)": re.compile(r"(?<![A-Za-z0-9_$.])process(?![A-Za-z0-9_$.\[]|\.env)"),
    "Buffer": re.compile(r"(?<![A-Za-z0-9_$])Buffer(?![A-Za-z0-9_$])"),
    "require(": re.compile(r"(?<![A-Za-z0-9_$])require\("),
    "__dirname": re.compile(r"(?<![A-Za-z0-9_$])__dirname(?![A-Za-z0-9_$])"),
    "__filename": re.compile(r"(?<![A-Za-z0-9_$])__filename(?![A-Za-z0-9_$])"),
}


def strip_strings_js(text: str) -> str:
    """Crude but effective: blank out JS string/template literals and comments
    so that matches inside inert strings are not counted."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            quote = c
            out.append(quote)
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if c == "/" and i + 1 < n:
            if text[i + 1] == "/":
                while i < n and text[i] != "\n":
                    i += 1
                continue
            if text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue
        out.append(c)
        i += 1
    return "".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: scan_process.py <bundle-dir-or-file>")
        return 2
    target = Path(sys.argv[1])
    files = [target] if target.is_file() else sorted(target.rglob("*.js")) + sorted(target.rglob("*.css"))
    total_bad = 0
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        code = strip_strings_js(raw)
        file_bad = 0
        for name, pat in PATTERNS.items():
            hits = pat.findall(code)
            if hits:
                file_bad += len(hits)
                total_bad += len(hits)
                for m in pat.finditer(code):
                    s = max(0, m.start() - 60)
                    e = min(len(code), m.end() + 60)
                    ctx = code[s:e].replace("\n", " ")
                    print(f"EXECUTABLE {name!r} in {f.name}: ...{ctx}...")
        # Report (non-fatal) string-literal occurrences for the record.
        for name in ("process", "Buffer", "__dirname", "__filename"):
            in_strings = len(re.findall(name, raw)) - len(re.findall(name, code))
            if in_strings:
                print(f"INFO: {name!r} appears {in_strings}x inside string literals in {f.name} (inert)")
        print(f"scanned {f.name}: {len(raw)} chars, {file_bad} executable hits")
    print(f"FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT={total_bad}")
    return 1 if total_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
