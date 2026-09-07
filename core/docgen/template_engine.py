"""Narrow, non-destructive OOXML mutation for LOG-DOCGEN-01 V1 templates.

The sandbox-only legal template binaries are loaded from a configurable
template directory and are treated as immutable.  Generation always works on a
fresh in-memory copy.  Everything outside the explicitly mapped cells is left
byte-for-byte identical, so merged cells, styles, fonts, borders, fills,
number formats, formulas, print settings, page margins, orientation and
relationships are preserved.

This is a single narrow component: it knows only how to write the mapped
source/input cells of the HDMB / pxk / pl XLSX sheets and the HDNT DOCX
paragraph runs.  It is deliberately NOT a generic OOXML framework.
"""

from __future__ import annotations

import io
import zipfile
from decimal import Decimal
from typing import Any, Mapping
from xml.sax.saxutils import escape

from lxml import etree

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NSMAP = {"x": SHEET_NS}
_NUMBER_TYPES = (int, float, Decimal)


def _parse(xml_bytes: bytes):
    return etree.fromstring(xml_bytes)


def _serialize(element) -> bytes:
    return etree.tostring(element, xml_declaration=True, encoding="UTF-8", standalone=True)


def _cell(sheet_element, coord: str):
    cells = sheet_element.findall(".//x:c", NSMAP)
    for cell in cells:
        if cell.get("r") == coord:
            return cell
    return None


def _shared_strings_map(sst_element):
    """Return (by_index list, text->index dict, sst root element)."""
    by_index: list[str] = []
    text_index: dict[str, int] = {}
    for si in sst_element.findall("x:si", NSMAP):
        # Concatenate every <t> text node under the <si>.
        texts = si.findall(".//x:t", NSMAP)
        value = "".join(t.text or "" for t in texts)
        by_index.append(value)
        text_index.setdefault(value, len(by_index) - 1)
    return by_index, text_index


def _append_shared_string(sst_element, text_index: dict[str, int], text: str) -> int:
    if text in text_index:
        return text_index[text]
    si = etree.SubElement(sst_element, f"{{{SHEET_NS}}}si")
    t = etree.SubElement(si, f"{{{SHEET_NS}}}t")
    t.text = text
    if text != text.strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    index = len(text_index)
    text_index[text] = index
    count = int(sst_element.get("count", "0"))
    unique = int(sst_element.get("uniqueCount", "0"))
    sst_element.set("count", str(count + 1))
    sst_element.set("uniqueCount", str(unique + 1))
    return index


def _set_shared_string(cell, sst_element, text_index: dict[str, int], text: str) -> None:
    index = _append_shared_string(sst_element, text_index, text)
    # Strip existing value/formula/inline str children.
    for tag in ("v", "f", "is"):
        for child in cell.findall(f"x:{tag}", NSMAP):
            cell.remove(child)
    cell.set("t", "s")
    v = etree.SubElement(cell, f"{{{SHEET_NS}}}v")
    v.text = str(index)


def _set_number(cell, value) -> None:
    for tag in ("v", "f", "is"):
        for child in cell.findall(f"x:{tag}", NSMAP):
            cell.remove(child)
    if "t" in cell.attrib:
        del cell.attrib["t"]
    v = etree.SubElement(cell, f"{{{SHEET_NS}}}v")
    if isinstance(value, Decimal):
        v.text = format(value, "f")
    elif isinstance(value, float):
        v.text = repr(value)
    else:
        v.text = str(int(value))


def _write_cell(cell, sst_element, text_index: dict[str, int], value) -> None:
    if isinstance(value, _NUMBER_TYPES) and not isinstance(value, bool):
        _set_number(cell, value)
    elif isinstance(value, bool):
        _set_number(cell, 1 if value else 0)
    else:
        _set_shared_string(cell, sst_element, text_index, str(value))


def _sheet_path_by_name(workbook_element, rels_element) -> dict[str, str]:
    """Map sheet name to its worksheet part path (e.g. xl/worksheets/sheet1.xml)."""
    rel_map: dict[str, str] = {}
    for rel in rels_element.findall(f"{{{PKG_REL_NS}}}Relationship"):
        rel_map[rel.get("Id")] = rel.get("Target")
    sheet_paths: dict[str, str] = {}
    for sheet in workbook_element.findall(".//x:sheet", NSMAP):
        rel_id = sheet.get(f"{{{REL_NS}}}id")
        target = rel_map.get(rel_id, "")
        if not target:
            continue
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        sheet_paths[sheet.get("name")] = target
    return sheet_paths


def mutate_xlsx(template_path: str, fill: Mapping[str, Mapping[str, Any]]) -> bytes:
    """Return a new XLSX workbook with the mapped cells written.

    ``fill`` maps sheet name -> {cell coordinate -> value}.  Text values are
    written as shared strings; numeric values keep the cell's style but are
    written as numbers.  Everything else in the package is preserved.
    """
    with open(template_path, "rb") as handle:
        raw = handle.read()

    reader = zipfile.ZipFile(io.BytesIO(raw))
    parts: dict[str, bytes] = {info.filename: reader.read(info.filename) for info in reader.infolist()}
    entry_order = [info.filename for info in reader.infolist()]

    workbook = _parse(parts.get("xl/workbook.xml", b"<workbook/>"))
    rels = _parse(parts.get("xl/_rels/workbook.xml.rels", b"<Relationships/>"))
    sheet_paths = _sheet_path_by_name(workbook, rels)

    sst_element = None
    text_index: dict[str, int] = {}
    sst_path = "xl/sharedStrings.xml"

    for sheet_name, payload in fill.items():
        path = sheet_paths.get(sheet_name)
        if not path or payload is None:
            continue
        if path not in parts:
            continue
        sheet = _parse(parts[path])
        if sst_element is None and sst_path in parts:
            sst_element = _parse(parts[sst_path])
            _by_index, text_index = _shared_strings_map(sst_element)

        for coord, value in payload.items():
            cell = _cell(sheet, coord)
            if cell is None:
                continue
            if sst_element is None:
                # No shared strings part: write text inline.
                if isinstance(value, _NUMBER_TYPES) and not isinstance(value, bool):
                    _set_number(cell, value)
                else:
                    for tag in ("v", "f", "is"):
                        for child in cell.findall(f"x:{tag}", NSMAP):
                            cell.remove(child)
                    cell.set("t", "inlineStr")
                    is_el = etree.SubElement(cell, f"{{{SHEET_NS}}}is")
                    t = etree.SubElement(is_el, f"{{{SHEET_NS}}}t")
                    t.text = str(value)
                continue
            _write_cell(cell, sst_element, text_index, value)

        parts[path] = _serialize(sheet)

    if sst_element is not None and sst_path in parts:
        parts[sst_path] = _serialize(sst_element)

    # Rebuild the zip preserving original entry order and metadata.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as writer:
        for name in entry_order:
            data = parts.get(name)
            if data is None:
                continue
            writer.writestr(name, data)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# DOCX (HDNT) mutation via python-docx run-level edits.
# ---------------------------------------------------------------------------


def mutate_docx(template_path: str, run_edits: list[tuple[int, int, str, str | None]]) -> bytes:
    """Return a new DOCX with the mapped runs rewritten.

    ``run_edits`` is a list of ``(para_index, run_index, value, replace)``.
    When ``replace`` is None the whole run text is set to ``value``; otherwise
    only the first occurrence of ``replace`` inside the run text is swapped for
    ``value``.  Run properties (rPr) are preserved because we never rebuild the
    paragraph or run element.
    """
    import docx  # noqa: PLC0415

    document = docx.Document(template_path)
    paragraphs = list(document.paragraphs)
    for para_index, run_index, value, replace in run_edits:
        if para_index >= len(paragraphs):
            continue
        runs = paragraphs[para_index].runs
        if run_index >= len(runs):
            continue
        run = runs[run_index]
        current = run.text
        if replace is None:
            run.text = str(value)
        else:
            if replace in current:
                run.text = current.replace(replace, str(value), 1)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
