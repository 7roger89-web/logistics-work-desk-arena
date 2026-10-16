"""READ-ONLY view of the ORIGINAL uploaded workbook — LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.

What this is
------------
The business tables in Bước 1/2 come from the bounded Lục Giác parser
(``core.quote_excel_import``). They are a review proposal, not the workbook.
This module adds the other half of requirement A: the employee can open the
original file's real sheets, in the file's own sheet order, and compare what the
parser proposed against what the customer actually sent.

Fidelity is claimed explicitly, never absolutely
------------------------------------------------
Every response carries ``fidelity``: what is reproduced (values and cached
results, formulas as text, merged cells, column widths, row heights, font,
fill, borders, alignment/wrap, number formats, hidden row/column/sheet flags)
and what is NOT rendered (images, charts, conditional formatting, data
validation, comments, rich-text runs, pivot tables, defined names, external
links). A reader therefore knows exactly which part of a sheet is missing,
instead of trusting a "looks like Excel" claim.

Safety
------
* The stored GridFS bytes are only ever READ; the viewer writes nothing.
* The same zip/size/macro guard rails as the importer are re-applied, so a file
  that somehow reached GridFS cannot turn this endpoint into a decompression or
  macro path.
* openpyxl never evaluates a formula: a cell shows its formula string plus the
  cached result when the file has one. A cached value that does not exist is
  reported as UNKNOWN — never as 0.
* SOURCE CELLS ARE GRANT-GATED, NOT CLASSIFICATION-GATED. Cell content is only
  serialized for a caller that already passed the business permission check
  (``commercial_write``) — on EVERY sheet, the customer sheet included, because a
  one-tab supplier file routinely keeps its cost figure inside that same tab.
  Every other caller gets the sheet locked, with its name, order and dimensions
  still visible so the user knows it exists. The customer-facing quotation is not
  affected: Bước 3 renders the published customer snapshot, not this raw view.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime, time
from typing import Any, Mapping, Sequence
from zipfile import BadZipFile, ZipFile

MAX_ROWS = 200
MAX_COLS = 40
MAX_CELLS = 4000

SHEET_CUSTOMER = "CUSTOMER"
SHEET_INTERNAL = "INTERNAL"
SHEET_UNCLASSIFIED = "UNCLASSIFIED"

INTERNAL_MARKERS = ("noi bo", "chi phi", "gia von", "cost", "tong hop", "du kien", "profit")
SUPPORTED_FEATURES = (
    "Giá trị ô theo đúng vị trí dòng/cột (chữ, số, ngày)",
    "Công thức nguồn hiển thị dạng văn bản, không thực thi",
    "Giá trị cache của công thức khi tệp có lưu",
    "Ô gộp",
    "Độ rộng cột, chiều cao hàng",
    "Font, cỡ chữ, in đậm/nghiêng, màu chữ",
    "Màu nền, đường viền, căn lề, xuống dòng",
    "Định dạng số/thời gian thông dụng; mã định dạng lạ được hiển thị nguyên mã",
    "Cờ ẩn của hàng/cột/sheet",
)
NOT_RENDERED_FEATURES = (
    "Hình ảnh / logo trong sheet",
    "Biểu đồ (chart)",
    "Định dạng có điều kiện",
    "Danh sách chọn (data validation)",
    "Ghi chú / comment ô",
    "Rich text trong một ô (nhiều định dạng trong cùng ô)",
    "Pivot table, sparkline",
    "Named range / liên kết ngoài (chỉ liệt kê tên, không render)",
    "Bản in, tiêu đề lặp, ngắt trang",
)


def folded(value: Any) -> str:
    import unicodedata

    text = unicodedata.normalize("NFD", str(value or "")).lower().replace("đ", "d")
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()


def _zip_guard(data: bytes) -> None:
    from core.quote_excel_import import MAX_BYTES, MAX_EXPANDED_BYTES

    if not data or len(data) > MAX_BYTES:
        raise ValueError("Tệp nguồn vượt giới hạn đọc an toàn.")
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            if sum(x.file_size for x in archive.infolist()) > MAX_EXPANDED_BYTES or len(archive.infolist()) > 300:
                raise ValueError("Workbook vượt giới hạn đọc an toàn.")
            if any("vbaproject" in x.filename.lower() for x in archive.infolist()):
                raise ValueError("Không đọc workbook chứa macro.")
    except BadZipFile as exc:
        raise ValueError("Tệp nguồn không phải XLSX hợp lệ.") from exc


def open_workbook(data: bytes):
    """(workbook with formulas, workbook with cached values). Read-only."""
    from openpyxl import load_workbook

    _zip_guard(data)
    workbook = load_workbook(io.BytesIO(data), data_only=False, keep_links=False)
    values = load_workbook(io.BytesIO(data), data_only=True, keep_links=False)
    if len(workbook.worksheets) > 8 or any(s.max_row > 2500 or s.max_column > 40 for s in workbook):
        raise ValueError("V1 chỉ xem được workbook nhỏ (≤8 sheet, 2500 dòng, 40 cột).")
    return workbook, values


def classify_sheet_names(sheet_names: Sequence[str], proposal: Mapping[str, Any] | None) -> dict[str, str]:
    """THE single sheet-classification rule, from names + the parser's own evidence.

    The customer sheet is the sheet the goods table was actually read from. A
    sheet is INTERNAL when the parser found cost figures in it, when it holds a
    duplicate goods table, or when its name carries an internal marker.
    Everything else is UNCLASSIFIED — and UNCLASSIFIED is **not** public: only
    the one customer sheet is treated as customer-facing. Nothing is assumed
    about "sheet 3".

    Both the viewer and the original-file download gate use THIS function, so the
    two paths cannot drift apart into two different notions of "internal".
    """
    source = (proposal or {}).get("source") or {}
    customer_sheet = str(source.get("goods_sheet") or "")
    cost_sheets = {str(c.get("source_sheet") or "") for c in (proposal or {}).get("source_costs") or []}
    # A sheet that also contained a goods table but was NOT chosen as the
    # customer table is the duplicated internal calculation, whatever it is
    # named.
    table_sheets = {str(name) for name in source.get("table_sheets") or []}
    out: dict[str, str] = {}
    for name in sheet_names:
        name = str(name)
        if name and name == customer_sheet:
            out[name] = SHEET_CUSTOMER
        elif name in cost_sheets or name in table_sheets or any(marker in folded(name) for marker in INTERNAL_MARKERS):
            out[name] = SHEET_INTERNAL
        else:
            out[name] = SHEET_UNCLASSIFIED
    return out


def internal_rows_on_customer_sheet(proposal: Mapping[str, Any] | None) -> list[str]:
    """Cost figures the parser found ON the customer sheet itself.

    NOT a gate. The raw workbook download requires ``commercial_write`` for every
    file, unconditionally, precisely because this function can only report what
    the parser recognised. Kept as the classification/diagnostic rule (see
    ``classify_sheet_names``); never reintroduce it as an authorization input.

    A supplier workbook often keeps one tab, with the internal cost scratched in
    beside the customer table. Then "the customer sheet" is not by itself proof
    that the FILE is publishable: the original bytes still contain the cost. The
    download gate uses this, not the sheet count.
    """
    source = (proposal or {}).get("source") or {}
    customer_sheet = str(source.get("goods_sheet") or "")
    if not customer_sheet:
        return []
    return [str(c.get("label") or "") for c in (proposal or {}).get("source_costs") or []
            if str(c.get("source_sheet") or "") == customer_sheet]


def classify_sheets(workbook, proposal: Mapping[str, Any] | None) -> dict[str, str]:
    """Same rule, applied to an open workbook."""
    return classify_sheet_names([sheet.title for sheet in workbook.worksheets], proposal)


def protected_sheet_names(sheet_names: Sequence[str], proposal: Mapping[str, Any] | None) -> list[str]:
    """Sheets that may not be handed to a customer-view-only role.

    Classification evidence, NOT the download gate: the original file is refused
    without ``commercial_write`` whatever this returns.

    Everything except the single customer sheet. An UNCLASSIFIED sheet is
    protected too: "we could not name it" is not evidence that it is public.
    """
    classification = classify_sheet_names(sheet_names, proposal)
    return [name for name, kind in classification.items() if kind != SHEET_CUSTOMER]


def _font(cell) -> dict[str, Any]:
    font = cell.font
    out: dict[str, Any] = {}
    if font is None:
        return out
    if font.bold:
        out["bold"] = True
    if font.italic:
        out["italic"] = True
    if font.size:
        out["size"] = float(font.size)
    if font.name:
        out["name"] = str(font.name)[:40]
    color = getattr(font.color, "rgb", None)
    if isinstance(color, str) and color not in {"00000000", "FF000000"}:
        out["color"] = "#" + color[-6:]
    return out


def _fill(cell) -> str:
    fill = cell.fill
    if fill is None or fill.fill_type != "solid":
        return ""
    color = getattr(fill.start_color, "rgb", None)
    if isinstance(color, str) and color not in {"00000000", "FFFFFFFF"}:
        return "#" + color[-6:]
    return ""


def _border(cell) -> str:
    border = cell.border
    if border is None:
        return ""
    sides = []
    for name in ("left", "right", "top", "bottom"):
        style = getattr(getattr(border, name, None), "style", None)
        if style:
            sides.append(f"{name[0]}:{style}")
    return ",".join(sides)


def _align(cell) -> dict[str, Any]:
    alignment = cell.alignment
    out: dict[str, Any] = {}
    if alignment is None:
        return out
    if alignment.horizontal:
        out["h"] = str(alignment.horizontal)
    if alignment.vertical:
        out["v"] = str(alignment.vertical)
    if alignment.wrap_text:
        out["wrap"] = True
    return out


def format_number(value: Any, number_format: str) -> str | None:
    """A BOUNDED number-format renderer for the common codes.

    It is deliberately not an Excel format engine: percentages, thousands
    separators, plain decimals, common date patterns and a quoted currency
    suffix/prefix are rendered; anything else returns None and the UI shows the
    raw value plus the format code itself.
    """
    code = (number_format or "").strip()
    if not code or code == "General":
        return None
    try:
        if isinstance(value, (datetime, date, time)):
            if not re.search(r"[yYdDmM]", code):
                return None
            if isinstance(value, datetime):
                moment = value
            elif isinstance(value, date):
                moment = datetime(value.year, value.month, value.day)
            else:
                moment = datetime(1900, 1, 1, value.hour, value.minute, value.second)
            tokens = {"yyyy": f"{moment.year:04d}", "yy": f"{moment.year % 100:02d}",
                      "dd": f"{moment.day:02d}", "d": str(moment.day),
                      "mm": f"{moment.month:02d}", "m": str(moment.month),
                      "hh": f"{moment.hour:02d}", "ss": f"{moment.second:02d}"}
            rendered = re.sub(r"yyyy|yy|dd|d|mm|m|hh|ss", lambda m: tokens[m.group(0)], code)
            return rendered
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        if "%" in code:
            decimals = len(re.search(r"\.(0+)", code).group(1)) if re.search(r"\.(0+)", code) else 0
            return f"{value * 100:,.{decimals}f}%".replace(",", ".")
        symbols = re.findall(r'"([^"]*)"', code)
        symbol = symbols[0] if symbols else ""
        decimals = len(re.search(r"\.(0+)", code).group(1)) if re.search(r"\.(0+)", code) else 0
        grouped = "," in code.split(".")[0]
        rendered = f"{value:,.{decimals}f}" if grouped else f"{value:.{decimals}f}"
        if grouped:
            rendered = rendered.replace(",", "\u00a0")
        if symbol and code.strip().startswith('"'):
            return symbol + rendered
        return rendered + ((" " + symbol) if symbol else "")
    except (AttributeError, ValueError):
        return None


def _cell_payload(cell, cached, *, shared_formula: bool = False) -> dict[str, Any] | None:
    """One bounded, honest cell record. A missing cache is UNKNOWN, never 0."""
    formula = cell.value if cell.data_type == "f" else None
    raw = cell.value
    payload: dict[str, Any] = {"r": cell.row, "c": cell.column}
    style = _font(cell)
    fill = _fill(cell)
    border = _border(cell)
    align = _align(cell)
    number_format = str(cell.number_format or "")
    if number_format and number_format != "General":
        payload["nf"] = number_format[:60]
    if style:
        payload["font"] = style
    if fill:
        payload["fill"] = fill
    if border:
        payload["border"] = border
    if align:
        payload["align"] = align
    if formula is not None:
        payload["f"] = str(formula)[:500]
        payload["kind"] = "formula"
        if cached is None or cached == "":
            payload["value"] = ""
            payload["unknown"] = True
        else:
            payload["value"] = _scalar(cached)
            payload["display"] = _display(cached, number_format)
        payload["shared"] = True if shared_formula else payload.get("shared", False)
        return payload
    if raw is None or raw == "":
        return payload if len(payload) > 2 else None
    payload["kind"] = "value"
    payload["value"] = _scalar(raw)
    payload["display"] = _display(raw, number_format)
    return payload


def _scalar(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    return str(value)[:2000]


def _display(value: Any, number_format: str) -> str:
    formatted = format_number(value, number_format)
    if formatted is not None:
        return formatted
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)[:2000]


def _not_rendered(sheet, workbook) -> dict[str, int]:
    """What this sheet actually contains that the viewer does NOT draw."""
    out: dict[str, int] = {}
    try:
        images = len(getattr(sheet, "_images", []) or [])
        if images:
            out["images"] = images
    except Exception:  # noqa: BLE001 - an unreadable drawing must not break the view
        pass
    for key, attribute in (("charts", "_charts"), ("conditional_formatting", "conditional_formatting"),
                           ("data_validation", "data_validations"), ("comments", "_comments")):
        try:
            count = len(getattr(sheet, attribute, []) or [])
        except Exception:  # noqa: BLE001
            count = 0
        if count:
            out[key] = count
    if getattr(sheet, "sheet_state", "visible") != "visible":
        out["sheet_hidden"] = 1
    try:
        names = len(list(workbook.defined_names))
        if names:
            out["defined_names"] = names
    except Exception:  # noqa: BLE001
        pass
    return out


def sheet_page(data: bytes, sheet_name: str, *, proposal: Mapping[str, Any] | None = None,
               can_view_internal: bool = False, max_rows: int = MAX_ROWS,
               max_cols: int = MAX_COLS) -> dict[str, Any]:
    """One sheet, bounded.

    ``can_view_internal`` is the SOURCE-CELL grant and it defaults to deny for
    every sheet: it means "this caller may read the supplier's original cells at
    all", not "this caller may read the sheets we happened to call internal".
    Callers must pass ``can_operate_business("commercial_write")``.
    """
    workbook, values = open_workbook(data)
    classification = classify_sheets(workbook, proposal)
    if sheet_name not in workbook.sheetnames:
        raise ValueError("Sheet không tồn tại trong workbook gốc.")
    sheet = workbook[sheet_name]
    sheet_class = classification.get(sheet_name, SHEET_UNCLASSIFIED)
    base = {
        "sheet": sheet_name,
        "sheet_index": workbook.sheetnames.index(sheet_name) + 1,
        "classification": sheet_class,
        "sheet_state": str(getattr(sheet, "sheet_state", "visible")),
        "row_count": int(sheet.max_row or 0),
        "column_count": int(sheet.max_column or 0),
        "read_only": True,
    }
    # RAW SOURCE CELLS REQUIRE THE BUSINESS GRANT — on EVERY sheet, INCLUDING the
    # one customer sheet. A customer tab is not proof that its cells are
    # customer-facing: a single-tab supplier file routinely keeps the cost figure
    # in a cell of that same tab (J20/K20 beside the goods table). The gate is
    # therefore the GRANT, never the classification, so a cost the parser did not
    # recognise cannot leak out through a sheet called "customer".
    #
    # Name, index, size, state and classification metadata stay visible, so a
    # lower role still learns that the sheet exists and why it is closed. The
    # customer-facing quotation itself is unaffected: Bước 3 reads the published
    # customer snapshot, not this raw view.
    if not can_view_internal:
        return {**base, "locked": True, "cells": [], "merges": [],
                "reason": "Ô nguồn của workbook gốc chỉ mở với quyền thao tác báo giá (commercial_write): "
                          "sheet khách cũng có thể chứa chi phí nội bộ ngay trong chính các ô của nó. "
                          "Bản báo giá khách vẫn xem được ở Bước 3."}
    row_limit = max(1, min(int(max_rows or MAX_ROWS), MAX_ROWS))
    col_limit = max(1, min(int(max_cols or MAX_COLS), MAX_COLS))
    value_sheet = values[sheet_name]
    cells: list[dict[str, Any]] = []
    truncated = False
    for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, row_limit),
                               max_col=min(sheet.max_column or 1, col_limit)):
        for cell in row:
            if len(cells) >= MAX_CELLS:
                truncated = True
                break
            payload = _cell_payload(cell, value_sheet[cell.coordinate].value)
            if payload is not None:
                cells.append(payload)
        if truncated:
            break
    merges = []
    for merged in list(sheet.merged_cells.ranges)[:400]:
        merges.append({"min_row": merged.min_row, "min_col": merged.min_col,
                       "max_row": merged.max_row, "max_col": merged.max_col,
                       "ref": str(merged)})
    column_widths = {str(key): round(float(dim.width), 2) for key, dim in list(sheet.column_dimensions.items())[:col_limit]
                     if dim.width}
    row_heights = {str(key): round(float(dim.height), 2) for key, dim in list(sheet.row_dimensions.items())[:row_limit]
                   if dim.height}
    hidden_rows = [int(key) for key, dim in list(sheet.row_dimensions.items())[:row_limit] if dim.hidden]
    hidden_columns = [str(key) for key, dim in list(sheet.column_dimensions.items())[:col_limit] if dim.hidden]
    return {
        **base,
        "locked": False,
        "cells": cells,
        "merges": merges,
        "column_widths": column_widths,
        "row_heights": row_heights,
        "hidden_rows": hidden_rows,
        "hidden_columns": hidden_columns,
        "frozen_panes": str(sheet.freeze_panes or ""),
        "truncated": truncated,
        "limits": {"max_rows": row_limit, "max_cols": col_limit, "max_cells": MAX_CELLS},
    }


def overview(data: bytes, proposal: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Sheet tabs in the file's real order, with per-sheet fidelity facts."""
    workbook, _ = open_workbook(data)
    classification = classify_sheets(workbook, proposal)
    sheets = []
    for index, sheet in enumerate(workbook.worksheets, 1):
        sheets.append({
            "name": sheet.title,
            "index": index,
            "classification": classification.get(sheet.title, SHEET_UNCLASSIFIED),
            "state": str(getattr(sheet, "sheet_state", "visible")),
            "row_count": int(sheet.max_row or 0),
            "column_count": int(sheet.max_column or 0),
            "merged_count": len(list(sheet.merged_cells.ranges)),
            "not_rendered": _not_rendered(sheet, workbook),
        })
    return {
        "sheet_names": list(workbook.sheetnames),
        "sheets": sheets,
        "customer_sheet": next((s["name"] for s in sheets if s["classification"] == SHEET_CUSTOMER), ""),
        "fidelity": {
            "supported": list(SUPPORTED_FEATURES),
            "not_rendered": list(NOT_RENDERED_FEATURES),
            "claim": "Bản xem workbook gốc V1 KHÔNG tuyên bố giữ nguyên 100% định dạng.",
        },
    }
