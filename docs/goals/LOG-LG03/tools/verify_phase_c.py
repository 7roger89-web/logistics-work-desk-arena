"""Phase C verification: mojibake marker scan, encoding integrity, secret scan."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/logistics_repo")

def collect_source_files():
    paths = []
    for pattern in ("core/*.py", "views/*.py"):
        paths.extend(ROOT.glob(pattern))
    return paths

def main():
    print("=== MOJIBAKE MARKER SCAN (working tree) ===")
    mojibake_found = []
    for p in collect_source_files():
        raw = p.read_bytes()
        # classic double-encoding marker: utf-8 bytes misread as latin-1 then re-encoded
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            mojibake_found.append((str(p), "NOT VALID UTF-8 AT ALL"))
            continue
        # common mojibake sequences after double encoding: \xc3 (Ã), \xc2 (Â)
        # followed by latin-1 artifacts; detect \xc3\xa1 (á) as mojibake only when
        # preceded by another utf-8 byte (pattern "…\xc3\x83" i.e. \xc3 83 after
        # \xc3) — use the robust heuristic: bytes \xc3\x83\xc2 or \xc2\xba or
        # \xc3\xa1\xc2 patterns plus known marker "\xc3\x83\xc2\xa1"
        markers = re.findall(rb"\xc3\x83[\xc2-\xc4]|\xc2\xba[\xe2-\xef]|\xc3\xa1\xc2|\xc3\x83\xe2", raw)
        if markers:
            mojibake_found.append((str(p.relative_to(ROOT)), len(markers)))
    if mojibake_found:
        print("MOJIBAKE PRESENT:")
        for f, n in mojibake_found:
            print(f"  {f}: {n} marker(s)")
    else:
        print("CLEAN: 0 mojibake markers in core/ + views/")

    print("\n=== UTF-8 VALIDITY (all Python files) ===")
    invalid = []
    for p in ROOT.glob("**/*.py"):
        if "venv" in str(p) or "__pycache__" in str(p):
            continue
        try:
            p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            invalid.append(str(p.relative_to(ROOT)))
    print("CLEAN: 0 invalid files" if not invalid else f"INVALID: {invalid}")

    print("\n=== FFFD REPLACEMENT CHARACTER SCAN ===")
    fffd = []
    for p in ROOT.glob("**/*.py"):
        if "venv" in str(p) or "__pycache__" in str(p):
            continue
        if "\ufffd" in p.read_text(encoding="utf-8", errors="replace"):
            fffd.append(str(p.relative_to(ROOT)))
    print("CLEAN: 0 files with U+FFFD" if not fffd else f"FFFD FOUND: {fffd}")

    print("\n=== SECRET SCAN (credentials/URI) ===")
    secret_hits = []
    for p in ROOT.glob("**/*.py"):
        if "venv" in str(p) or "__pycache__" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"(mongodb\+srv://[^\s\"']{5,}|:[A-Za-z0-9!@#$%^&*]{8,200}@cluster[0-9a-z\.]*\.mongodb\.net)", text):
            secret_hits.append((str(p.relative_to(ROOT)), m.group(0)[:30]))
    print("CLEAN: no credentials/URI found in source" if not secret_hits else f"HITS: {secret_hits}")

    print("\n=== AST COMPILE CHECK ===")
    bad = []
    for p in collect_source_files():
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bad.append((str(p.relative_to(ROOT)), str(e)))
    print("CLEAN: all core/ + views/ files parse" if not bad else f"SYNTAX ERRORS: {bad}")

if __name__ == "__main__":
    main()
