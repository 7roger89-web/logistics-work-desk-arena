#!/usr/bin/env python3
"""Build the production-safe FORM_07 template from the exact Owner source.

Issue #168 — FORM_07 "Biên bản giao nhận" pilot.

INPUT (evidence only, never committed to main):
  owner-input/form07-source-168:owner_inputs/form07/Mau-Bien-ban-giao-nhan-hang-hoa.docx
  SHA-256 cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5
  git blob e2c3dea169bff006f4073f7fae2b2c285c912f3f (18997 bytes)

OUTPUT (Git-resident production asset):
  assets/templates/form07/FORM07-bien-ban-giao-nhan-v1.docx

The script refuses to run unless the input hash matches the pinned Owner
receipt. It performs ONLY bounded, asserted mutations:

  1. dot-leader bind slots -> single-run Jinja/docxtpl tokens (layout, fonts,
     italics/bold and every static word around the slots are preserved);
  2. the goods table's three empty body rows -> one ``{%tr for %}`` tag row,
     one token row and one ``{%tr endfor %}`` tag row (docxtpl row loop);
  3. goods table readability (2026-10-09 Supervisor A7 repair): near-equal
     Owner column widths (~1650 dxa each) are redistributed within the exact
     printable width so product names/specs stay readable; the 24 goods cell
     paragraphs get an explicit zero indent overriding the inherited Normal
     right indent (936 dxa), which alone fragments short values; the header
     row repeats on page continuation (``w:tblHeader``) and is kept with the
     first data row (``w:keepNext``); data rows keep ``w:cantSplit``;
  4. docProps metadata scrub (personal author names, revision counter and
     mutable timestamps replaced by fixed system values);
  5. deterministic ZIP repack (fixed 1980-01-01 entry dates, original entry
     order) so the sanitized asset has one stable SHA-256.

Everything else (styles.xml, settings.xml, numbering.xml, theme, fonts, the
VML straight-line under the national motto, sectPr page size/margins) stays
byte-identical. No wording is rewritten; a static prefix that is legally part
of a bound name ("CÔNG TY") is subsumed by the full canonical legal_name
binding and documented in the spec.

Run:
  git cat-file blob e2c3dea169bff006f4073f7fae2b2c285c912f3f > /tmp/form07-source.docx
  python3 scripts/form07_build_sanitized_template.py /tmp/form07-source.docx
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "assets/templates/form07/FORM07-bien-ban-giao-nhan-v1.docx"

SOURCE_SHA256 = "cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5"
SOURCE_SIZE_BYTES = 18997
SOURCE_GIT_BLOB_SHA = "e2c3dea169bff006f4073f7fae2b2c285c912f3f"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
FIXED_TEMPLATE_TIMESTAMP = "2026-10-03T00:00:00Z"
SYSTEM_AUTHOR = "Logistics Work Desk"


def _fail(message: str) -> None:
    raise SystemExit(f"FORM07-SANITIZE: {message}")


def _run_text(run: str) -> str:
    return "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", run, flags=re.S))


def _set_run_text(run: str, new_text: str) -> str:
    """Replace the FIRST <w:t> payload of a run and drop any other <w:t>."""
    escaped = (
        new_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    space = ' xml:space="preserve"' if new_text != new_text.strip() or "\u00a0" in new_text else ""
    out, replaced = re.subn(
        r"<w:t(?: [^>]*)?>.*?</w:t>",
        lambda _match: f"<w:t{space}>{escaped}</w:t>",
        run,
        count=1,
        flags=re.S,
    )
    if replaced != 1:
        _fail(f"run without <w:t>: {run[:120]}")
    # Drop any ADDITIONAL <w:t> nodes after the first (kept) one.
    seen = 0

    def _keep_first(match: re.Match) -> str:
        nonlocal seen
        seen += 1
        return match.group(0) if seen == 1 else ""

    return re.sub(r"<w:t(?: [^>]*)?>.*?</w:t>", _keep_first, out, flags=re.S)


def _must_replace_once(document: str, old: str, new: str, label: str) -> str:
    count = document.count(old)
    if count != 1:
        _fail(f"{label}: expected exactly 1 occurrence, found {count}")
    return document.replace(old, new, 1)


def _run_spans(paragraph: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(0))
        for match in re.finditer(r"<w:r(?: [^>]*)?>.*?</w:r>|<w:r(?: [^>]*)?/>", paragraph, flags=re.S)
    ]


def _runs_of(paragraph: str) -> list[str]:
    return [run for _, _, run in _run_spans(paragraph)]


def _rewrite_paragraph_runs(paragraph: str, edits: dict[int, str | None], label: str) -> str:
    """Apply {run_index: new_text_or_None(delete)} to one paragraph.

    Position-based: identical runs (same serialization) inside one paragraph
    are still addressed by their own index.
    """
    spans = _run_spans(paragraph)
    if not spans:
        _fail(f"{label}: paragraph has no runs")
    for index in edits:
        if index >= len(spans):
            _fail(f"{label}: run index {index} out of range ({len(spans)} runs)")
    pieces: list[str] = []
    cursor = 0
    for index, (start, end, run) in enumerate(spans):
        pieces.append(paragraph[cursor:start])
        if index in edits:
            replacement = edits[index]
            pieces.append("" if replacement is None else _set_run_text(run, replacement))
        else:
            pieces.append(run)
        cursor = end
    pieces.append(paragraph[cursor:])
    return "".join(pieces)


def _paragraph_containing(document: str, needle: str, label: str) -> str:
    matches = [
        paragraph
        for paragraph in re.findall(r"<w:p [^>]*>.*?</w:p>|<w:p>.*?</w:p>", document, flags=re.S)
        if needle in "".join(_run_text(run) for run in _runs_of(paragraph))
    ]
    if len(matches) != 1:
        _fail(f"{label}: expected 1 paragraph containing {needle!r}, found {len(matches)}")
    return matches[0]


def sanitize_document(document: str) -> str:
    # ---- Header table, top-left: "CÔNG TY............." ------------------
    # The static prefix "CÔNG TY" is legally part of the bound canonical
    # company legal_name ("CÔNG TY ..."), so the whole slot becomes the token.
    para = _paragraph_containing(document, "CÔNG TY", "header-company")
    runs = _runs_of(para)
    if _run_text(runs[0]) != "CÔNG TY" or _run_text(runs[1]) != ".............":
        _fail("header-company: unexpected run layout")
    new_para = _rewrite_paragraph_runs(para, {0: "{{ cong_ty }}", 1: None}, "header-company")
    document = _must_replace_once(document, para, new_para, "header-company")

    # ---- Header table: "Số: …….." ----------------------------------------
    para = _paragraph_containing(document, ": ……..", "header-number")
    new_para = _rewrite_paragraph_runs(para, {1: ": {{ so_bien_ban }}"}, "header-number")
    document = _must_replace_once(document, para, new_para, "header-number")

    # ---- Header table: "......., ngày….tháng…..năm ......." ---------------
    para = _paragraph_containing(document, ", ngày….tháng…..năm ", "header-dateloc")
    runs = _runs_of(para)
    expected = ["                 ", "  ", ".......", ", ngày….tháng…..năm ", "......."]
    if [_run_text(run) for run in runs[:5]] != expected:
        _fail("header-dateloc: unexpected run layout")
    new_para = _rewrite_paragraph_runs(
        para,
        {2: "{{ dia_diem }}", 3: ", ngày {{ ngay }} tháng {{ thang }} năm ", 4: "{{ nam }}"},
        "header-dateloc",
    )
    document = _must_replace_once(document, para, new_para, "header-dateloc")

    # ---- "Căn cứ Hợp đồng mua bán giữa ..........." -----------------------
    para = _paragraph_containing(document, "Căn cứ Hợp đồng mua bán giữa", "basis-contract")
    runs = _runs_of(para)
    if _run_text(runs[1]) != "...................................................":
        _fail("basis-contract: unexpected run layout")
    new_para = _rewrite_paragraph_runs(
        para, {1: "{{ ben_b_name }} và {{ ben_a_name }}"}, "basis-contract"
    )
    document = _must_replace_once(document, para, new_para, "basis-contract")

    # ---- "Căn cứ Đơn đặt hàng ngày…………….của Công ty ……………." ---------------
    # "Công ty" is subsumed by the canonical legal_name binding (documented).
    para = _paragraph_containing(document, "Căn cứ Đơn đặt hàng ngày", "basis-order")
    new_para = _rewrite_paragraph_runs(
        para,
        {0: "Căn cứ Đơn đặt hàng ngày {{ ngay_dat_hang }} của {{ ben_a_name }}."},
        "basis-order",
    )
    document = _must_replace_once(document, para, new_para, "basis-order")

    # ---- Parties paragraph (single paragraph with <w:br/> line breaks) ----
    para = _paragraph_containing(document, "chúng tôi gồm", "parties")
    runs = _runs_of(para)
    texts = [_run_text(run) for run in runs]
    if len(runs) != 52:
        _fail(f"parties: expected 52 runs, found {len(runs)}")
    edits: dict[int, str | None] = {
        # Intro: "Hôm nay, ngày ……tháng …. năm\xa0….. tại ………., chúng tôi gồm: "
        0: "Hôm nay, ngày {{ ngay }} tháng {{ thang }} năm {{ nam }}\u00a0tại {{ dia_diem }}, chúng tôi gồm: ",
        1: None, 2: None, 3: None, 4: None, 5: None,
        # BÊN A (Bên nhận hàng): {{ ben_a_name }}
        9: "\u00a0{{ ben_a_name }}",
        # - Địa chỉ : {{ ben_a_address }}
        13: " {{ ben_a_address }}", 14: None, 15: None,
        # - Điện thoại : {{ ben_a_phone }}
        18: ": {{ ben_a_phone }}",
        # - Đại diện Ông/bà: {{ ben_a_representative }} Chức vụ: {{ ... }}
        22: "{{ ben_a_representative }}  Chức vụ",
        23: ": {{ ben_a_representative_title }}",
        # BÊN B (Bên giao hàng): {{ ben_b_name }}
        30: "{{ ben_b_name }}",
        # - Địa chỉ: {{ ben_b_address }}
        33: "Địa chỉ:\u00a0 {{ ben_b_address }}",
        # - Điện thoại: {{ ben_b_phone }}
        38: "{{ ben_b_phone }}", 39: None,
        # - Đại diện Ông/bà {{ ben_b_representative }} Chức vụ: {{ ... }}
        45: "\u00a0 {{ ben_b_representative }} ", 46: None,
        48: ": {{ ben_b_representative_title }}", 49: None,
    }
    # Guard: every edited slot really is a dot-leader (or the intro run).
    for index in (9, 13, 14, 15, 18, 22, 23, 30, 33, 38, 39, 45, 48, 49):
        slot = texts[index]
        if index in (22, 33):
            if "…" not in slot and "..." not in slot:
                _fail(f"parties run {index}: not a dot-leader: {slot!r}")
        elif not re.fullmatch(r"[\s\u00a0.…:]*", slot):
            _fail(f"parties run {index}: not a dot-leader: {slot!r}")
    if texts[47] != "Chức vụ":
        _fail(f"parties run 47: expected 'Chức vụ', found {texts[47]!r}")
    new_para = _rewrite_paragraph_runs(para, edits, "parties")
    document = _must_replace_once(document, para, new_para, "parties")

    # ---- Goods table: rows 2..4 (three empty body rows) -------------------
    tables = re.findall(r"<w:tbl>.*?</w:tbl>", document, flags=re.S)
    goods_table = next(
        (table for table in tables if "Tên hàng" in table and "Quy cách" in table), None
    )
    if goods_table is None:
        _fail("goods-table: not found")
    rows = re.findall(r"<w:tr [^>]*>.*?</w:tr>|<w:tr>.*?</w:tr>", goods_table, flags=re.S)
    if len(rows) != 4:
        _fail(f"goods-table: expected 4 rows, found {len(rows)}")
    for row in rows[1:]:
        if _run_text(row).strip():
            _fail("goods-table: body row is not empty in the Owner source")

    def _row_tokens(row: str, tokens: list[str]) -> str:
        """Write one token into each of the six cells (empty cells get a run)."""
        cells = re.findall(r"<w:tc>.*?</w:tc>", row, flags=re.S)
        if len(cells) != 6 or len(tokens) != 6:
            _fail(f"goods-table: expected 6 cells/tokens, got {len(cells)}/{len(tokens)}")
        out_row = row
        for cell, token in zip(cells, tokens):
            paragraphs = re.findall(r"<w:p [^>]*>.*?</w:p>", cell, flags=re.S)
            if len(paragraphs) != 1:
                _fail("goods-table: cell without exactly one paragraph")
            paragraph = paragraphs[0]
            rpr_match = re.search(r"<w:pPr>.*?<w:rPr>(.*?)</w:rPr>.*?</w:pPr>", paragraph, flags=re.S)
            rpr = f"<w:rPr>{rpr_match.group(1)}</w:rPr>" if rpr_match else ""
            run = f'<w:r>{rpr}<w:t xml:space="preserve">{token}</w:t></w:r>'
            new_paragraph = paragraph.replace("</w:p>", f"{run}</w:p>", 1)
            out_row = out_row.replace(paragraph, new_paragraph, 1)
        return out_row

    for_row = _row_tokens(
        rows[1], ["{%tr for line in goods_lines %}", "", "", "", "", ""]
    )
    body_row = _row_tokens(
        rows[2],
        [
            "{{ line.stt }}",
            "{{ line.ten_hang }}",
            "{{ line.quy_cach }}",
            "{{ line.dvt }}",
            "{{ line.so_luong }}",
            "{{ line.ghi_chu }}",
        ],
    )
    endfor_row = _row_tokens(rows[3], ["{%tr endfor %}", "", "", "", "", ""])

    new_table = goods_table
    for old_row, new_row in ((rows[1], for_row), (rows[2], body_row), (rows[3], endfor_row)):
        new_table = _must_replace_once(new_table, old_row, new_row, "goods-table-row")

    # ---- Pagination: never split a goods row across pages -----------------
    # A data row broken by a page break separates one goods line across two
    # pages (seen: "Kính" at the bottom of p1, "nổi 5mm" at the top of p2).
    # w:cantSplit keeps each row intact; Word/LibreOffice then moves the whole
    # row to the next page. Applied to the header row and every loop row
    # (docxtpl replicates the body row; the for/endfor tag rows are removed
    # at render time, so they need no treatment).
    def _cant_split(row: str, label: str) -> str:
        if "<w:cantSplit" in row:
            return row
        trpr = re.search(r"<w:trPr>.*?</w:trPr>", row, flags=re.S)
        if trpr is None:
            # No row properties yet: insert a minimal <w:trPr> right after <w:tr>.
            m = re.search(r"<w:tr(?: [^>]*)?>", row)
            if m is None:
                _fail(f"{label}: row has no <w:tr> open tag")
            trpr_xml = '<w:trPr><w:cantSplit w:val="true"/></w:trPr>'
            return row[: m.end()] + trpr_xml + row[m.end() :]
        new_trpr = trpr.group(0).replace("</w:trPr>", '<w:cantSplit w:val="true"/></w:trPr>', 1)
        return row.replace(trpr.group(0), new_trpr, 1)

    new_table = _must_replace_once(
        new_table, rows[0], _cant_split(rows[0], "goods-table-header"), "goods-table-cantsplit"
    )
    # body_row is the template row docxtpl replicates per goods line.
    new_table = new_table.replace(body_row, _cant_split(body_row, "goods-table-body"), 1)

    # ---- Readability: redistribute the six goods columns --------------------
    # Owner grid/tcW are near-equal (~1650 dxa each), so "Khung nhôm định
    # hình" and "1200x600" fragment into 2-3-character lines. New widths stay
    # within the exact printable area (pgSz 12240 - left 1418 - right 1134 =
    # 9688 dxa): STT compact, Tên hàng + Quy cách wider, ĐVT + Số lượng
    # compact, Ghi chú takes the residual. tblGrid and every tcW are set
    # coherently; fixed layout enforces them. Fonts/wording untouched.
    # Proven by LibreOffice render measurement (2026-10-09): the Owner Normal
    # style carries w:ind w:right="936" for justified body text, which the
    # unstyled table paragraphs inherit - eating 936 dxa from every cell, so
    # widths alone cannot fix readability. Each goods cell paragraph gets an
    # explicit zero indent (table-only override; body text keeps Owner style).
    GOODS_WIDTHS = [800, 2800, 1900, 800, 1000, 2388]
    GOODS_TOTAL = sum(GOODS_WIDTHS)
    if GOODS_TOTAL != 9688:
        _fail(f"goods-table-widths: widths sum to {GOODS_TOTAL}, expected 9688")

    grid_match = re.search(r"<w:tblGrid>.*?</w:tblGrid>", new_table, flags=re.S)
    if grid_match is None:
        _fail("goods-table-widths: tblGrid not found")
    if len(re.findall(r"<w:gridCol ", grid_match.group(0))) != 6:
        _fail("goods-table-widths: tblGrid does not carry exactly 6 gridCol")
    new_grid = "<w:tblGrid>" + "".join(
        f'<w:gridCol w:w="{width}"/>' for width in GOODS_WIDTHS
    ) + "</w:tblGrid>"
    new_table = _must_replace_once(
        new_table, grid_match.group(0), new_grid, "goods-table-grid"
    )

    # tblW auto(0) -> fixed total; add fixed layout so grid+tcW are honored.
    if new_table.count('<w:tblW w:w="0" w:type="auto"/>') != 1:
        _fail("goods-table-widths: expected exactly 1 auto tblW in goods table")
    if "<w:tblLayout" in new_table:
        _fail("goods-table-widths: unexpected pre-existing tblLayout")
    new_table = _must_replace_once(
        new_table,
        '<w:tblW w:w="0" w:type="auto"/>',
        f'<w:tblW w:w="{GOODS_TOTAL}" w:type="dxa"/><w:tblLayout w:type="fixed"/>',
        "goods-table-tblW",
    )

    def _set_row_cell_widths(row: str, label: str) -> str:
        parts = re.split(r'(<w:tcW w:w="\d+" w:type="dxa"/>)', row)
        hits = [part for part in parts if part.startswith("<w:tcW")]
        if len(hits) != 6:
            _fail(f"{label}: expected 6 tcW cells, found {len(hits)}")
        out: list[str] = []
        column = 0
        for part in parts:
            if part.startswith("<w:tcW"):
                out.append(f'<w:tcW w:w="{GOODS_WIDTHS[column]}" w:type="dxa"/>')
                column += 1
            else:
                out.append(part)
        return "".join(out)

    current_rows = re.findall(
        r"<w:tr [^>]*>.*?</w:tr>|<w:tr>.*?</w:tr>", new_table, flags=re.S
    )
    if len(current_rows) != 4:
        _fail(f"goods-table-widths: expected 4 rows, found {len(current_rows)}")
    for index, row in enumerate(current_rows):
        new_table = _must_replace_once(
            new_table, row,
            _set_row_cell_widths(row, f"goods-table-widths-row{index}"),
            f"goods-table-widths-row{index}",
        )

    # ---- Repeatable header: tblHeader + keep-with-next ----------------------
    # tblHeader repeats the header row on page continuation; keepNext on each
    # header paragraph keeps the header with the first data row so the header
    # never sits alone at the bottom of a page. Data rows keep cantSplit.
    current_rows = re.findall(
        r"<w:tr [^>]*>.*?</w:tr>|<w:tr>.*?</w:tr>", new_table, flags=re.S
    )
    header_row = current_rows[0]
    if "<w:tblHeader" in header_row:
        _fail("goods-table-header: unexpected pre-existing tblHeader")
    header_trpr = re.search(r"<w:trPr>.*?</w:trPr>", header_row, flags=re.S)
    if header_trpr is None or "<w:cantSplit" not in header_trpr.group(0):
        _fail("goods-table-header: header lost its cantSplit row properties")
    new_header_trpr = header_trpr.group(0).replace(
        "</w:trPr>", '<w:tblHeader w:val="true"/></w:trPr>', 1
    )
    header_row = header_row.replace(header_trpr.group(0), new_header_trpr, 1)
    header_row, keep_next_count = re.subn(
        r"(<w:pPr(?: [^>]*)?>)",
        r"\1<w:keepNext/>",
        header_row,
    )
    if keep_next_count != 6:
        _fail(f"goods-table-header: expected 6 keepNext insertions, got {keep_next_count}")
    new_table = _must_replace_once(
        new_table, current_rows[0], header_row, "goods-table-header-repeat"
    )

    # ---- Zero cell indent: override inherited Normal right indent ----------
    # Owner Normal style indents body paragraphs 936 dxa on the right; the 24
    # unstyled goods cell paragraphs inherit it, which alone fragments short
    # values ("100" -> "1/0/0") no matter the column widths. Schema order in
    # CT_PPr is keepNext before ind before jc.
    new_table, header_ind_count = re.subn(
        '<w:pPr><w:keepNext/>',
        '<w:pPr><w:keepNext/><w:ind w:left="0" w:right="0"/>',
        new_table,
    )
    if header_ind_count != 6:
        _fail(f"goods-table-indent: expected 6 header ind insertions, got {header_ind_count}")
    new_table, body_ind_count = re.subn(
        '<w:pPr><w:jc w:val="left"/>',
        '<w:pPr><w:ind w:left="0" w:right="0"/><w:jc w:val="left"/>',
        new_table,
    )
    if body_ind_count != 18:
        _fail(f"goods-table-indent: expected 18 body ind insertions, got {body_ind_count}")

    document = _must_replace_once(document, goods_table, new_table, "goods-table")

    return document


def scrub_core_properties(xml_text: str) -> str:
    xml_text = re.sub(r"<dc:creator>.*?</dc:creator>", f"<dc:creator>{SYSTEM_AUTHOR}</dc:creator>", xml_text, flags=re.S)
    xml_text = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", f"<cp:lastModifiedBy>{SYSTEM_AUTHOR}</cp:lastModifiedBy>", xml_text, flags=re.S)
    xml_text = re.sub(r"<cp:revision>.*?</cp:revision>", "<cp:revision>1</cp:revision>", xml_text, flags=re.S)
    xml_text = re.sub(
        r'(<dcterms:created[^>]*>).*?(</dcterms:created>)',
        rf"\g<1>{FIXED_TEMPLATE_TIMESTAMP}\g<2>",
        xml_text,
        flags=re.S,
    )
    xml_text = re.sub(
        r'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',
        rf"\g<1>{FIXED_TEMPLATE_TIMESTAMP}\g<2>",
        xml_text,
        flags=re.S,
    )
    if "Tien Thanh" in xml_text:
        _fail("core.xml still carries the personal author name")
    return xml_text


def scrub_app_properties(xml_text: str) -> str:
    xml_text = re.sub(r"<Company>.*?</Company>", "<Company></Company>", xml_text, flags=re.S)
    xml_text = re.sub(r"<TotalTime>.*?</TotalTime>", "<TotalTime>0</TotalTime>", xml_text, flags=re.S)
    return xml_text


def main() -> None:
    if len(sys.argv) != 2:
        _fail("usage: form07_build_sanitized_template.py <source.docx>")
    source_path = Path(sys.argv[1])
    raw = source_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256 or len(raw) != SOURCE_SIZE_BYTES:
        _fail(
            "SOURCE_HASH_MISMATCH: computed "
            f"{digest} / {len(raw)} bytes, expected {SOURCE_SHA256} / {SOURCE_SIZE_BYTES}"
        )

    reader = zipfile.ZipFile(io.BytesIO(raw))
    if reader.testzip() is not None:
        _fail("source ZIP is corrupt")
    names = reader.namelist()
    banned = [name for name in names if re.search(r"vbaProject|activeX|embeddings|comments|people|header\d|footer\d|externalLinks", name, re.I)]
    if banned:
        _fail(f"source carries unexpected parts: {banned}")

    parts = {name: reader.read(name) for name in names}
    document = parts["word/document.xml"].decode("utf-8")
    document = sanitize_document(document)
    parts["word/document.xml"] = document.encode("utf-8")
    parts["docProps/core.xml"] = scrub_core_properties(parts["docProps/core.xml"].decode("utf-8")).encode("utf-8")
    parts["docProps/app.xml"] = scrub_app_properties(parts["docProps/app.xml"].decode("utf-8")).encode("utf-8")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as writer:
        for name in names:  # original entry order, fixed timestamps
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            writer.writestr(info, parts[name])
    OUTPUT_PATH.write_bytes(buffer.getvalue())

    sanitized_sha = hashlib.sha256(buffer.getvalue()).hexdigest()
    print(f"SOURCE_SHA256={digest} (matches pinned Owner receipt)")
    print(f"SOURCE_GIT_BLOB_SHA(expected)={SOURCE_GIT_BLOB_SHA}")
    print(f"WROTE={OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"SANITIZED_SIZE_BYTES={len(buffer.getvalue())}")
    print(f"SANITIZED_SHA256={sanitized_sha}")


if __name__ == "__main__":
    main()
