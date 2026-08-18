"""Scan remaining English user-visible UI labels per view file (LG03 W6)."""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
FILES = [
    "views/quotations.py",
    "views/agreements.py",
    "views/contracts.py",
    "views/finance.py",
    "views/partner_reconciliation.py",
    "views/reports.py",
    "views/tariff.py",
    "views/tracking.py",
    "views/knowledge_base.py",
    "views/entity_context.py",
    "views/customers.py",
]

# Strings to keep (international/technical terms)
KEEP = {"None", "OK", "Sea", "Air", "Road", "Rail", "Express", "EXW", "FOB",
        "CIF", "DAP", "DDP", "CFR", "FCA", "Tất cả", "VND", "USD", "ID"}


def looks_english(text: str) -> bool:
    text = text.strip()
    if len(text) < 3:
        return False
    latin = re.sub(r"[^A-Za-z0-9 .,:!?/%&'\-–—()]", "", text)
    ratio = len(latin) / max(len(text), 1)
    # must be majority latin and contain at least 2 words or a long word
    has_word = re.search(r"[A-Za-z]{4,}", text)
    return ratio > 0.75 and bool(has_word)


def main() -> int:
    pattern = re.compile(r"""(["'])([^"']{2,90})\1""")
    triggers = ("st.title(", "st.header(", "st.subheader(", "st.markdown(",
                "st.button(", "st.checkbox(", "st.selectbox(", "st.radio(",
                "st.caption(", 'selectbox("', "options=", "labels", "label=")
    for rel in FILES:
        path = REPO / rel
        if not path.exists():
            print(f"== {rel}: FILE MISSING")
            continue
        src = path.read_text(encoding="utf-8")
        out: list[str] = []
        for lineno, line in enumerate(src.splitlines(), 1):
            if not any(t in line for t in triggers):
                continue
            for m in pattern.finditer(line):
                txt = m.group(2)
                if looks_english(txt) and txt not in KEEP:
                    out.append(f"  L{lineno}: {txt!r}")
        print(f"== {rel} ({len(out)} EN labels)")
        for o in out[:30]:
            print(o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
