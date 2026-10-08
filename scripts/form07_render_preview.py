#!/usr/bin/env python3
"""Issue #168 — deterministic DOCX → HTML previews for the evidence pack.

The sandbox has no LibreOffice/pandoc (apt repositories unreachable), so the
visual comparison between the Owner original, the sanitized derivative and a
real generated sample is rendered by this small structural reader: it walks
``word/document.xml`` (body only), preserving paragraph order, run bold /
underline, paragraph alignment and table geometry. It is an evidence aid, not
a Word-compatible layout engine — the authoritative structural checks live in
``tests/test_form07_delivery_receipt.py`` (python-docx) and the byte-exact
pins in ``assets/templates/form07/FORM07.template.json``.

Run:  python3 scripts/form07_render_preview.py
Out:  evidence/168/form07-original.html
      evidence/168/form07-sanitized.html
      evidence/168/form07-sample.html
"""

from __future__ import annotations

import hashlib
import html
import io
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "evidence" / "168"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SOURCE_BLOB = "e2c3dea169bff006f4073f7fae2b2c285c912f3f"  # Owner original (transport branch)
SANITIZED = ROOT / "assets/templates/form07/FORM07-bien-ban-giao-nhan-v1.docx"

CSS = """
body{font-family:'Times New Roman',serif;max-width:820px;margin:24px auto;padding:0 16px;color:#111;line-height:1.45}
table{border-collapse:collapse;width:100%;margin:8px 0}
td,th{border:1px solid #666;padding:4px 6px;vertical-align:top}
.c{text-align:center}.r{text-align:right}.j{text-align:justify}
u{text-decoration:underline}
.meta{font-family:monospace;font-size:12px;background:#f4f4f4;border:1px solid #ddd;padding:8px;margin-bottom:16px}
"""


def _run_html(run: ET.Element) -> str:
    props = run.find(f"{W}rPr")
    bold = props is not None and props.find(f"{W}b") is not None
    italic = props is not None and props.find(f"{W}i") is not None
    underline = props is not None and props.find(f"{W}u") is not None
    parts: list[str] = []
    for child in run:
        if child.tag == f"{W}t":
            parts.append(html.escape(child.text or ""))
        elif child.tag == f"{W}tab":
            parts.append("&emsp;")
        elif child.tag == f"{W}br":
            parts.append("<br>")
    text = "".join(parts)
    if not text:
        return ""
    if underline:
        text = f"<u>{text}</u>"
    if italic:
        text = f"<i>{text}</i>"
    if bold:
        text = f"<b>{text}</b>"
    return text


def _paragraph_html(paragraph: ET.Element) -> str:
    props = paragraph.find(f"{W}pPr")
    align = ""
    if props is not None:
        jc = props.find(f"{W}jc")
        if jc is not None:
            align = {"center": "c", "right": "r", "both": "j", "justify": "j"}.get(
                jc.get(f"{W}val", ""), ""
            )
    inner = "".join(_run_html(run) for run in paragraph.findall(f"{W}r"))
    cls = f' class="{align}"' if align else ""
    return f"<p{cls}>{inner or '&nbsp;'}</p>"


def _block_html(element: ET.Element) -> str:
    if element.tag == f"{W}p":
        return _paragraph_html(element)
    if element.tag == f"{W}tbl":
        rows = []
        for row in element.findall(f"{W}tr"):
            cells = []
            for cell in row.findall(f"{W}tc"):
                cell_body = "".join(_block_html(child) for child in cell)
                cells.append(f"<td>{cell_body}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        return "<table>" + "".join(rows) + "</table>"
    return ""


def docx_to_html(docx_bytes: bytes, title: str, meta_lines: list[str]) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as package:
        document_xml = package.read("word/document.xml")
    body = ET.fromstring(document_xml).find(f"{W}body")
    blocks = "".join(_block_html(child) for child in body)
    meta = "<br>".join(html.escape(line) for line in meta_lines)
    return (
        "<!DOCTYPE html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"<div class=\"meta\">{meta}</div>{blocks}</body></html>"
    )


def owner_original_bytes() -> bytes:
    return subprocess.run(
        ["git", "cat-file", "blob", SOURCE_BLOB],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout


def sample_bytes() -> bytes:
    """A real sample rendered by core.docgen.form07 from staging-shaped facts."""
    from core.docgen.form07 import build_form07_context, render_form07_docx
    from tests.test_form07_delivery_receipt import GOODS_LINES, MANUAL, _full_facts

    facts = _full_facts()
    return render_form07_docx(build_form07_context(
        delivery=facts["delivery"],
        goods_lines=GOODS_LINES,
        agent=facts["agent"],
        company=facts["company"],
        manual=MANUAL,
    ))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    original = owner_original_bytes()
    sanitized = SANITIZED.read_bytes()
    sample = sample_bytes()
    targets = (
        ("form07-original.html", original, "Owner original — Mau-Bien-ban-giao-nhan-hang-hoa.docx"),
        ("form07-sanitized.html", sanitized, "Sanitized production template — FORM07-bien-ban-giao-nhan-v1.docx"),
        ("form07-sample.html", sample, "Generated sample — core.docgen.form07 render (staging-shaped facts)"),
    )
    for name, payload, title in targets:
        digest = hashlib.sha256(payload).hexdigest()
        page = docx_to_html(payload, title, [
            title,
            f"sha256={digest}",
            f"size={len(payload)} bytes",
            "rendered by scripts/form07_render_preview.py (structural reader, body only — no LibreOffice in sandbox)",
        ])
        (OUT_DIR / name).write_text(page, encoding="utf-8")
        print(f"{name}: {len(payload)} bytes, sha256 {digest[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
