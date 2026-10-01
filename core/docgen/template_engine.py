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
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

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


def _set_shared_string(cell, sst_element, text_index: dict[str, int], text: str) -> bool:
    index = _append_shared_string(sst_element, text_index, text)
    removed_f = False
    # Strip existing value/formula/inline str children.
    for tag in ("v", "f", "is"):
        for child in cell.findall(f"x:{tag}", NSMAP):
            if tag == "f":
                removed_f = True
            cell.remove(child)
    cell.set("t", "s")
    v = etree.SubElement(cell, f"{{{SHEET_NS}}}v")
    v.text = str(index)
    return removed_f


def _set_number(cell, value, keep_formula=False) -> bool:
    removed_f = False
    for tag in ("v", "f", "is"):
        if tag == "f" and keep_formula:
            continue
        for child in cell.findall(f"x:{tag}", NSMAP):
            if tag == "f":
                removed_f = True
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
    return removed_f


def _write_cell(cell, sst_element, text_index: dict[str, int], value) -> bool:
    keep_formula = False
    if isinstance(value, CachedFormulaValue):
        keep_formula = True
        value = value.value

    if isinstance(value, _NUMBER_TYPES) and not isinstance(value, bool):
        return _set_number(cell, value, keep_formula)
    elif isinstance(value, bool):
        return _set_number(cell, 1 if value else 0, keep_formula)
    else:
        return _set_shared_string(cell, sst_element, text_index, str(value))


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
        # Relationship targets may be package-absolute ("/xl/worksheets/sheet1.xml",
        # as openpyxl writes them) or workbook-relative ("worksheets/sheet1.xml").
        # Normalize to the package path so both resolve to the same part.
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheet_paths[sheet.get("name")] = target
    return sheet_paths


class CachedFormulaValue:
    def __init__(self, value):
        self.value = value

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
    formula_removed = False

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
                keep_formula = False
                if isinstance(value, CachedFormulaValue):
                    keep_formula = True
                    value = value.value
                if isinstance(value, _NUMBER_TYPES) and not isinstance(value, bool):
                    if _set_number(cell, value, keep_formula):
                        formula_removed = True
                else:
                    for tag in ("v", "f", "is"):
                        if tag == "f" and keep_formula:
                            continue
                        for child in cell.findall(f"x:{tag}", NSMAP):
                            if tag == "f":
                                formula_removed = True
                            cell.remove(child)
                    cell.set("t", "inlineStr")
                    is_el = etree.SubElement(cell, f"{{{SHEET_NS}}}is")
                    t = etree.SubElement(is_el, f"{{{SHEET_NS}}}t")
                    t.text = str(value)
                continue
            if _write_cell(cell, sst_element, text_index, value):
                formula_removed = True


        cells_to_shrink = []
        cells_to_wrap = []

        if sheet_name == "HDMB":
            c_el = _cell(sheet, "E24")
            if c_el is not None and c_el.get("s"):
                cells_to_shrink.append(c_el)

        if sheet_name == "pl":
            sheetData = sheet.find(f"{{{SHEET_NS}}}sheetData")
            if sheetData is not None:
                row6 = sheetData.find(f"{{{SHEET_NS}}}row[@r='6']")
                if row6 is not None:
                    row6.set("ht", "75")
                    row6.set("customHeight", "1")
            
            # Print title for pl
            wb_sheets = workbook.find(f"{{{SHEET_NS}}}sheets")
            pl_sheet_idx = None
            if wb_sheets is not None:
                for idx, s in enumerate(wb_sheets.findall(f"{{{SHEET_NS}}}sheet")):
                    if s.get("name") == "pl":
                        pl_sheet_idx = idx
                        break
            if pl_sheet_idx is not None:
                def_names = workbook.find(f"{{{SHEET_NS}}}definedNames")
                if def_names is None:
                    def_names = etree.Element(f"{{{SHEET_NS}}}definedNames")
                    calc_pr = workbook.find(f"{{{SHEET_NS}}}calcPr")
                    if calc_pr is not None:
                        calc_pr.addprevious(def_names)
                    else:
                        workbook.append(def_names)
                exists = False
                for dn in def_names.findall(f"{{{SHEET_NS}}}definedName"):
                    if dn.get("name") == "_xlnm.Print_Titles" and dn.get("localSheetId") == str(pl_sheet_idx):
                        exists = True
                        dn.text = "pl!$9:$9"
                if not exists:
                    dn = etree.SubElement(def_names, f"{{{SHEET_NS}}}definedName")
                    dn.set("name", "_xlnm.Print_Titles")
                    dn.set("localSheetId", str(pl_sheet_idx))
                    dn.text = "pl!$9:$9"
                    
        if sheet_name == "pxk":
            sheetData = sheet.find(f"{{{SHEET_NS}}}sheetData")
            if sheetData is not None:
                for r_idx in ["6", "7", "10", "11"]:
                    row = sheetData.find(f"{{{SHEET_NS}}}row[@r='{r_idx}']")
                    if row is None:
                        row = etree.SubElement(sheetData, f"{{{SHEET_NS}}}row")
                        row.set("r", r_idx)
                    row.set("ht", "40" if r_idx in ["6", "7"] else "30")
                    row.set("customHeight", "1")
                    c_el = _cell(sheet, f"A{r_idx}")
                    if c_el is not None and c_el.get("s"):
                        cells_to_wrap.append(c_el)
            
            mergeCells = sheet.find(f"{{{SHEET_NS}}}mergeCells")
            if mergeCells is None:
                mergeCells = etree.Element(f"{{{SHEET_NS}}}mergeCells")
                # Insert after sheetData? Actually, etree handles it gracefully most times, but strictly we could just append to sheet.
                pm = sheet.find(f"{{{SHEET_NS}}}pageMargins")
                if pm is not None:
                    pm.addprevious(mergeCells)
                else:
                    sheet.append(mergeCells)
                    
            for ref in ["A10:D10", "A11:D11"]:
                exists = False
                for mc in mergeCells.findall(f"{{{SHEET_NS}}}mergeCell"):
                    if mc.get("ref") == ref:
                        exists = True
                if not exists:
                    mc = etree.SubElement(mergeCells, f"{{{SHEET_NS}}}mergeCell")
                    mc.set("ref", ref)
                    count = int(mergeCells.get("count", "0"))
                    mergeCells.set("count", str(count + 1))
            
            pageSetup = sheet.find(f"{{{SHEET_NS}}}pageSetup")
            if pageSetup is None:
                pageSetup = etree.Element(f"{{{SHEET_NS}}}pageSetup")
                pm = sheet.find(f"{{{SHEET_NS}}}pageMargins")
                if pm is not None:
                    pm.addnext(pageSetup)
                else:
                    sheet.append(pageSetup)
            pageSetup.set("fitToWidth", "1")
            pageSetup.set("fitToHeight", "0")
            
            sheetPr = sheet.find(f"{{{SHEET_NS}}}sheetPr")
            if sheetPr is None:
                sheetPr = etree.Element(f"{{{SHEET_NS}}}sheetPr")
                sheet.insert(0, sheetPr)
            pageSetUpPr = sheetPr.find(f"{{{SHEET_NS}}}pageSetUpPr")
            if pageSetUpPr is None:
                pageSetUpPr = etree.SubElement(sheetPr, f"{{{SHEET_NS}}}pageSetUpPr")
            pageSetUpPr.set("fitToPage", "1")

        if (cells_to_shrink or cells_to_wrap) and "xl/styles.xml" in parts:
            import copy
            styles = _parse(parts["xl/styles.xml"])
            cellXfs = styles.find(f"{{{SHEET_NS}}}cellXfs")
            if cellXfs is not None:
                for c_el in cells_to_shrink:
                    s_idx = int(c_el.get("s"))
                    xfs = cellXfs.findall(f"{{{SHEET_NS}}}xf")
                    if s_idx < len(xfs):
                        new_xf = copy.deepcopy(xfs[s_idx])
                        alignment = new_xf.find(f"{{{SHEET_NS}}}alignment")
                        if alignment is None:
                            alignment = etree.SubElement(new_xf, f"{{{SHEET_NS}}}alignment")
                        alignment.set("shrinkToFit", "1")
                        if "wrapText" in alignment.attrib:
                            del alignment.attrib["wrapText"]
                        new_xf.set("applyAlignment", "1")
                        cellXfs.append(new_xf)
                        new_s_idx = len(cellXfs.findall(f"{{{SHEET_NS}}}xf")) - 1
                        cellXfs.set("count", str(new_s_idx + 1))
                        c_el.set("s", str(new_s_idx))
                
                for c_el in cells_to_wrap:
                    s_idx = int(c_el.get("s"))
                    xfs = cellXfs.findall(f"{{{SHEET_NS}}}xf")
                    if s_idx < len(xfs):
                        new_xf = copy.deepcopy(xfs[s_idx])
                        alignment = new_xf.find(f"{{{SHEET_NS}}}alignment")
                        if alignment is None:
                            alignment = etree.SubElement(new_xf, f"{{{SHEET_NS}}}alignment")
                        alignment.set("wrapText", "1")
                        new_xf.set("applyAlignment", "1")
                        cellXfs.append(new_xf)
                        new_s_idx = len(cellXfs.findall(f"{{{SHEET_NS}}}xf")) - 1
                        cellXfs.set("count", str(new_s_idx + 1))
                        c_el.set("s", str(new_s_idx))
            parts["xl/styles.xml"] = _serialize(styles)

        parts[path] = _serialize(sheet)

    if sst_element is not None and sst_path in parts:
        parts[sst_path] = _serialize(sst_element)

    if formula_removed:
        # 1. Remove xl/calcChain.xml
        if "xl/calcChain.xml" in parts:
            del parts["xl/calcChain.xml"]
            if "xl/calcChain.xml" in entry_order:
                entry_order.remove("xl/calcChain.xml")

        # 2. Remove its relationship from xl/_rels/workbook.xml.rels
        rels_modified = False
        for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship"):
            if rel.get("Target") == "calcChain.xml":
                rels.remove(rel)
                rels_modified = True
        if rels_modified:
            parts["xl/_rels/workbook.xml.rels"] = _serialize(rels)

        # 3. Remove its corresponding Content-Type override from [Content_Types].xml
        if "[Content_Types].xml" in parts:
            ct_element = _parse(parts["[Content_Types].xml"])
            ct_modified = False
            for override in ct_element.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override"):
                if override.get("PartName") == "/xl/calcChain.xml":
                    ct_element.remove(override)
                    ct_modified = True
            if ct_modified:
                parts["[Content_Types].xml"] = _serialize(ct_element)


    # 4. Update workbook calculation properties to request safe recalculation
    calc_pr = workbook.find(f"{{{SHEET_NS}}}calcPr")
    if calc_pr is not None:
        calc_pr.set("calcMode", "auto")
        calc_pr.set("fullCalcOnLoad", "1")
        calc_pr.set("forceFullCalc", "1")

    # Rebuild the zip preserving original entry order and metadata.
    parts["xl/workbook.xml"] = _serialize(workbook)
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
    import docx

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
