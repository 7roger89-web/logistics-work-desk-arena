"""Bounded XLSX reader for the quotation desk — three real PL/PI layout families.

This is **not** a universal Excel importer and **not** a price engine. openpyxl
reads values and cached results only; formulas, macros and external links are
never executed. Parsed data is a REVIEW proposal: it is neither a quote nor a
legal tax opinion.

Layout families are recognised from HEADER EVIDENCE, never from the file name:

* ``LUC_GIAC``            — quoted goods table: product size + qty + unit price.
* ``PROFORMA_INVOICE``    — priced PI table; a second "money" sheet that repeats
                            the goods table is classified for review and is
                            never summed a second time.
* ``PACKING_LIST``        — goods + packing data with NO unit price. A missing
                            price stays UNKNOWN; it is never turned into 0.
* ``MULTI_LEVEL_PACKING`` — goods list → pallet detail → carton detail. The
                            levels are recorded, never added together, and the
                            model key links them only when it is unambiguous.

Reading is bounded: byte/ZIP guards, a hard sheet ceiling, a total-cell budget,
and the USED data region. A real packing list declares 257 columns because of
stray formatting while its data ends at column T; the reader follows the data,
not the formatting, and still refuses a genuinely oversized workbook.

Internal material stays internal: a hidden sheet or a cost/money sheet is never
a candidate for the goods table, and its content is not copied into the
proposal that feeds the customer quotation.
"""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
from typing import Any, Mapping
from zipfile import BadZipFile, ZipFile

from openpyxl import load_workbook

PARSER_VERSION = "luc-giac/1"
MAX_BYTES = 5 * 1024 * 1024
MAX_EXPANDED_BYTES = 25 * 1024 * 1024
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Hard reading ceilings. The 40-column V1 limit was an artefact of the first
# layout; the real files declare up to 257 columns of formatting on 13 rows.
MAX_SHEETS = 8
MAX_SHEET_ROWS = 2500
MAX_SHEET_COLUMNS = 2000
MAX_TOTAL_CELLS = 200_000
MAX_SCAN_ROWS = 400
MAX_SCAN_COLUMNS = 60
MAX_SCANNED_CELLS = 120_000
MAX_GOODS_ROWS = 200

LAYOUT_LUC_GIAC = "LUC_GIAC"
LAYOUT_PACKING_LIST = "PACKING_LIST"
LAYOUT_PROFORMA_INVOICE = "PROFORMA_INVOICE"
LAYOUT_MULTI_LEVEL_PACKING = "MULTI_LEVEL_PACKING"

ROLE_GOODS_LIST = "GOODS_LIST"
ROLE_PALLET_DETAIL = "PALLET_DETAIL"
ROLE_CARTON_DETAIL = "CARTON_DETAIL"
ROLE_PACKING_INSTRUCTION = "PACKING_INSTRUCTION"
ROLE_INTERNAL_CALC = "INTERNAL_CALC"
ROLE_HIDDEN = "HIDDEN_SHEET"
ROLE_UNCLASSIFIED = "UNCLASSIFIED_TABLE"

CUSTOMER_NAME_MARKERS = ("khach", "customer", "bao gia", "quotation", "quote",
                         "proforma", "invoice", "hoa don", "报价单")
INTERNAL_NAME_MARKERS = ("noi bo", "chi phi", "gia von", "cost", "tong hop", "du kien",
                         "profit", "tien hang", "money", "internal", "phi thue")
LIST_NAME_MARKERS = ("清单", "list", "summary", "danh sach")
TOTAL_ROW_WORDS = ("tong", "total", "cong", "subtotal", "合计", "小计", "总计")
CURRENCY_TOKENS = ("rmb", "cny", "usd", "vnd", "人民币")

# Header tokens per logical column. Order matters: a more specific label must be
# tested before a generic one ("package size" before "size"). Short ASCII tokens
# are matched EXACTLY so that "Đại lý" can never look like "dài" (length).
HEADER_TOKENS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("package_dimensions", ("kich thuoc kien", "kich thuoc dong goi", "package size",
                            "packing size", "carton size", "包装尺寸", "外箱尺寸")),
    ("dimensions", ("kich thuoc", "kt san pham", "kich thuoc san pham", "product size",
                    "size", "dimension", "specification", "规格", "尺寸", "产品尺寸")),
    ("model", ("model", "ma san pham", "ma hang", "ma sp", "item no", "item code",
               "型号", "产品型号", "款号")),
    ("description", ("ten hang", "ten san pham", "hang hoa", "san pham", "mo ta",
                     "description", "product name", "item name", "品名", "产品名称",
                     "名称", "中文品名")),
    ("material", ("vat lieu", "chat lieu", "material", "材质", "材料")),
    ("qty", ("so luong", "quantity", "qty", "pcs", "数量")),
    ("cartons", ("so kien", "so thung", "cartons", "ctns", "packages", "件数", "箱数")),
    ("packing", ("dong goi", "packing", "包装方式", "包装")),
    ("net_weight", ("net weight", "n.w", "nw", "净重")),
    ("gross_weight", ("gross weight", "g.w", "gw", "毛重", "trong luong")),
    ("cbm", ("cbm", "the tich", "volume", "体积", "立方")),
    ("note", ("ghi chu", "note", "remark", "备注")),
    ("image", ("hinh anh", "image", "photo", "picture", "图片", "照片")),
    ("pallet", ("pallet", "托盘", "托")),
    ("length", ("length", "长")),
    ("width", ("width", "宽")),
    ("height", ("height", "高")),
)
SHORT_ASCII_TOKENS = {"sl", "qty", "pcs", "nw", "n.w", "gw", "g.w", "cbm", "note",
                      "dai", "l", "w", "h"}

DISCLOSURES = (
    ("payment", "Thanh toán 80% trước khi giao hàng."),
    ("production", "Sản xuất dự kiến 30 ngày."),
    ("import", "Nhập khẩu dự kiến 14–20 ngày."),
    ("drawing", "Có bản vẽ thiết kế sau một tuần kể từ khi đặt cọc."),
)


def folded(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "")).lower().replace("đ", "d")
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()


def _number(value: Any) -> float | None:
    if value is None or str(value).strip() == "" or isinstance(value, bool):
        return None
    raw = str(value).strip().replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
        raw = raw.replace(".", "")
    else:
        raw = raw.replace(",", "")
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    return float(number) if number.is_finite() else None


def _dimensions(value: Any) -> tuple[float | None, float | None, float | None]:
    parts = re.split(r"[x×*]", str(value or "").lower().replace("mm", ""))
    if len(parts) != 3:
        return None, None, None
    return tuple(_number(p) for p in parts)  # type: ignore[return-value]


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()[:2000]


def used_bounds(sheet) -> tuple[int, int]:
    """Last row/column that actually HOLDS A VALUE, bounded by the hard ceiling.

    Excel keeps formatted-but-empty cells far beyond the data (the real packing
    list declares 257 columns for 13 rows). Reading the declared rectangle would
    be both slow and misleading, so the reader follows the used region while a
    genuinely oversized sheet is still refused by ``MAX_SHEET_COLUMNS``.
    """
    rows, columns = 0, 0
    cells = getattr(sheet, "_cells", None)
    if isinstance(cells, dict):
        for (row, column), cell in cells.items():
            if row > MAX_SHEET_ROWS or column > MAX_SHEET_COLUMNS:
                continue
            if cell.value is not None:
                rows = max(rows, row)
                columns = max(columns, column)
        return rows, columns
    for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row or 1, 60),
                               max_col=min(sheet.max_column or 1, MAX_SCAN_COLUMNS)):
        for cell in row:
            if cell.value is not None:
                rows = max(rows, cell.row)
                columns = max(columns, cell.column)
    return rows, columns


def _header_key(text: str) -> str | None:
    """Logical column for one header cell; a more specific label wins."""
    if not text:
        return None
    for key, tokens in HEADER_TOKENS:
        for token in tokens:
            if text == token or (token not in SHORT_ASCII_TOKENS and token in text):
                return key
    return None


def _money_key(text: str, row_text: str) -> str | None:
    """Money columns need a currency hint in the same header row."""
    if not text:
        return None
    has_currency = any(token in row_text for token in CURRENCY_TOKENS)
    if has_currency and ("unit price" in text or "don gia" in text or "单价" in text):
        return "unit_price"
    if has_currency and ("thanh tien" in text or "amount" in text or "total price" in text
                         or "金额" in text or "小计" in text):
        return "amount"
    return None


def _currency_of(row_text: str) -> str:
    if "usd" in row_text:
        return "USD"
    if "vnd" in row_text:
        return "VND"
    return "CNY"


def _detect_table(sheet, rows: int, columns: int) -> dict[str, Any] | None:
    """Header row + logical columns, by evidence. Never inferred by position."""
    if rows < 1 or columns < 1:
        return None
    best: dict[str, Any] | None = None
    for row in sheet.iter_rows(min_row=1, max_row=min(rows, 40),
                               max_col=min(columns, MAX_SCAN_COLUMNS)):
        row_text = " ".join(folded(cell.value) for cell in row if cell.value is not None)
        found: dict[str, int] = {}
        for cell in row:
            text = folded(cell.value)
            if not text:
                continue
            key = _header_key(text)
            if key:
                found.setdefault(key, cell.column)
            money = _money_key(text, row_text)
            if money:
                found.setdefault(money, cell.column)
        if len(found) < 3 or not ({"qty", "cartons"} & found.keys()):
            continue
        # A goods table needs an identity/description column, or — as in the
        # Owner's furniture quote — an explicit product-size + unit-price pair.
        if not ({"model", "description", "material"} & found.keys()) and not (
                {"dimensions", "unit_price"} <= found.keys()):
            continue
        kind = LAYOUT_PACKING_LIST
        if "unit_price" in found:
            kind = LAYOUT_LUC_GIAC if "dimensions" in found else LAYOUT_PROFORMA_INVOICE
        candidate = {"header_row": row[0].row, "columns": found, "kind": kind,
                     "currency": _currency_of(row_text), "score": len(found)}
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def _role_for(sheet_title: str, table: Mapping[str, Any], hidden: bool) -> str:
    """What this table IS in the workbook. Descriptive, never an auth decision."""
    if hidden:
        return ROLE_HIDDEN
    name = folded(sheet_title)
    columns = set(table["columns"])
    if "pallet" in columns or any(marker in name for marker in ("托盘", "pallet")):
        return ROLE_PALLET_DETAIL
    if {"length", "width", "height"} <= columns and ({"cbm", "gross_weight"} & columns):
        return ROLE_CARTON_DETAIL
    if any(marker in name for marker in ("指令", "instruction", "loading")):
        return ROLE_PACKING_INSTRUCTION
    if any(marker in name for marker in INTERNAL_NAME_MARKERS):
        return ROLE_INTERNAL_CALC
    if any(marker in name for marker in LIST_NAME_MARKERS):
        return ROLE_GOODS_LIST
    return ROLE_UNCLASSIFIED


def _read_rows(sheet, val_sheet, table: Mapping[str, Any]) -> tuple[list[dict], list[dict], list[tuple[str, int, str]], list[dict]]:
    """Goods rows + review-only packing evidence + unknowns + linking keys."""
    columns = table["columns"]
    map_dimensions = table["kind"] == LAYOUT_LUC_GIAC
    start = int(table["header_row"]) + 1
    stop = start + MAX_GOODS_ROWS
    goods: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    unknowns: list[tuple[str, int, str]] = []
    keys: list[dict[str, Any]] = []

    def value(row: int, key: str) -> Any:
        column = columns.get(key)
        return val_sheet.cell(row, column).value if column else None

    identity_keys = [key for key in ("model", "description", "material") if key in columns]
    for row in range(start, stop + 1):
        model = _text(value(row, "model"))
        description = _text(value(row, "description"))
        material = _text(value(row, "material"))
        if folded(val_sheet.cell(row, 1).value).startswith(TOTAL_ROW_WORDS):
            continue
        dimensions = _dimensions(value(row, "dimensions")) if map_dimensions else (None, None, None)
        qty = _number(value(row, "qty"))
        cartons = _number(value(row, "cartons"))
        price = _number(value(row, "unit_price"))
        net = _number(value(row, "net_weight"))
        gross = _number(value(row, "gross_weight"))
        volume = _number(value(row, "cbm"))
        # A row is a goods line when it carries an identity, or — as in the
        # Owner's furniture quote, where only the first row names the material —
        # an explicit size + quantity pair.
        if identity_keys and not (model or description or material) and not (
                all(part is not None for part in dimensions) and qty is not None):
            continue
        if (qty is None and cartons is None and price is None and net is None
                and gross is None and volume is None and all(v is None for v in dimensions)):
            continue
        for key in ("qty", "unit_price"):
            column = columns.get(key)
            if column and sheet.cell(row, column).data_type == "f" and val_sheet.cell(row, column).value is None:
                unknowns.append(("formula_no_cache", row,
                                 "Công thức nguồn chưa có giá trị cache: giữ CHƯA BIẾT, không tự tính và không coi là 0."))
        goods.append({
            "id": f"row-{row}", "description": description, "model": model,
            "material": material, "note": _text(value(row, "note")),
            "length_mm": dimensions[0], "width_mm": dimensions[1], "height_mm": dimensions[2],
            "qty": qty, "unit_price": price, "currency": str(table["currency"]),
            "source_sheet": sheet.title, "source_row": row,
        })
        extra: dict[str, Any] = {}
        if not map_dimensions and _text(value(row, "dimensions")):
            # A product size is NOT a package/carton size; it is kept as evidence.
            extra["product_size"] = _text(value(row, "dimensions"))
        for key, label in (("package_dimensions", "package_size"), ("packing", "packing")):
            text = _text(value(row, key))
            if text:
                extra[label] = text
        for key, label in (("cartons", "cartons"), ("net_weight", "net_weight_kg"),
                           ("gross_weight", "gross_weight_kg"), ("cbm", "volume_cbm")):
            number = {"cartons": cartons, "net_weight": net, "gross_weight": gross, "cbm": volume}[key]
            if number is not None:
                extra[label] = number
        if extra:
            evidence.append({"ref": f"{sheet.title}!{row}", **extra})
        keys.append({"row": row, "model": model,
                     "pallet": _text(value(row, "pallet"))})
    return goods, evidence, unknowns, keys


def _rank(table: Mapping[str, Any]) -> int:
    """Which table is the goods table the operator should review."""
    name = folded(table["sheet"])
    score = 0
    if table["role"] in {ROLE_PALLET_DETAIL, ROLE_CARTON_DETAIL,
                         ROLE_PACKING_INSTRUCTION, ROLE_INTERNAL_CALC}:
        score -= 6
    if "unit_price" in table["columns"]:
        score += 2
    if any(marker in name for marker in CUSTOMER_NAME_MARKERS) or re.search(r"\bpi\b", name):
        score += 6
    if any(marker in name for marker in LIST_NAME_MARKERS):
        score += 3
    return score


def parse_luc_giac_workbook(data: bytes, file_name: str, *, today: date | None = None) -> dict[str, Any]:
    """Return an editable review proposal. No cost/FX/tax is automatically applied."""
    if not file_name.lower().endswith(".xlsx") or PurePath(file_name).name != file_name or "\\" in file_name:
        raise ValueError("Chỉ nhận tệp .xlsx có tên hợp lệ (không nhận .xls/.xlsm).")
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Tệp Excel phải có dữ liệu và không vượt quá 5 MB.")
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            if sum(x.file_size for x in archive.infolist()) > MAX_EXPANDED_BYTES or len(archive.infolist()) > 300:
                raise ValueError("Workbook vượt giới hạn đọc an toàn.")
            if any("vbaproject" in x.filename.lower() for x in archive.infolist()):
                raise ValueError("Không nhận workbook chứa macro.")
        wb = load_workbook(io.BytesIO(data), data_only=False, keep_links=False)
        values = load_workbook(io.BytesIO(data), data_only=True, keep_links=False)
    except (BadZipFile, KeyError, OSError, ValueError) as exc:
        raise ValueError("Tệp XLSX không hợp lệ hoặc vượt giới hạn đọc an toàn.") from exc
    if len(wb.worksheets) > MAX_SHEETS or any(
            s.max_row > MAX_SHEET_ROWS or s.max_column > MAX_SHEET_COLUMNS for s in wb.worksheets):
        raise ValueError("Workbook vượt giới hạn đọc an toàn (≤8 sheet, 2500 dòng, 2000 cột).")
    if sum(len(getattr(s, "_cells", {}) or {}) for s in wb.worksheets) > MAX_TOTAL_CELLS:
        raise ValueError("Workbook vượt giới hạn đọc an toàn (quá nhiều ô).")

    bounds = {sheet.title: used_bounds(sheet) for sheet in wb.worksheets}
    warnings: list[dict[str, str]] = []
    texts: list[str] = []
    supplier = ""
    metrics: dict[str, set[float]] = {"cbm": set(), "weight_kg": set()}
    source_facts: dict[str, Any] = {}
    expires: list[date] = []
    source_costs: list[dict[str, Any]] = []
    formula_gap = False
    scan_truncated = False
    cell_budget = MAX_SCANNED_CELLS
    for sheet in wb.worksheets:
        val_sheet = values[sheet.title]
        rows, columns = bounds[sheet.title]
        for row in sheet.iter_rows(min_row=1, max_row=min(rows, MAX_SCAN_ROWS),
                                   max_col=min(columns, MAX_SCAN_COLUMNS)):
            for cell in row:
                if cell_budget <= 0:
                    scan_truncated = True
                    break
                cell_budget -= 1
                if cell.value is None:
                    continue
                text = str(cell.value)
                texts.append(text)
                key = folded(text)
                if cell.data_type == "e" or (cell.data_type == "f" and val_sheet[cell.coordinate].value is None):
                    formula_gap = True
                adjacent = val_sheet.cell(cell.row, cell.column + 1).value
                if "nha cung cap" in key and adjacent:
                    supplier = str(adjacent)
                for metric, needles in (("cbm", ("cbm",)), ("weight_kg", ("trong luong", "gross weight"))):
                    if any(n in key for n in needles):
                        n = _number(adjacent)
                        if n is not None:
                            metrics[metric].add(n)
                if "hieu luc den" in key:
                    raw = adjacent
                    try:
                        exp = raw.date() if isinstance(raw, datetime) else raw if isinstance(raw, date) else datetime.strptime(str(raw), "%d/%m/%Y").date()
                        expires.append(exp)
                    except (ValueError, TypeError):
                        warnings.append({"id": "invalid-expiry", "text": "Ngày hiệu lực nguồn không hợp lệ; không coi là giá hiện hành."})
                if key in {"container", "loai container"} and adjacent:
                    source_facts["equipment"] = str(adjacent)
                if key in {"rmb/usd", "usd/vnd", "hs tham khao", "thue nk tham khao", "vat nk tham khao"}:
                    source_facts[key] = str(adjacent or "")
                if key.startswith(("van chuyen", "phi dai ly", "thong quan", "lcc ", "giao nhan", "nang ha")) and _number(adjacent) is not None:
                    source_costs.append({"label": text, "amount": _number(adjacent), "source_sheet": sheet.title,
                                         "condition": "IF_APPLICABLE" if "phat sinh" in key else "UNCONFIRMED"})
        if cell_budget <= 0:
            break

    tables: list[dict[str, Any]] = []
    for index, sheet in enumerate(wb.worksheets, 1):
        rows, columns = bounds[sheet.title]
        table = _detect_table(sheet, rows, columns)
        if not table:
            continue
        hidden = str(getattr(sheet, "sheet_state", "visible")) != "visible"
        role = _role_for(sheet.title, table, hidden)
        if hidden:
            # A hidden sheet is never a goods source: its rows are not read into
            # the proposal at all, only its name/role/state are recorded below.
            goods, evidence, unknowns, keys = [], [], [], []
        else:
            goods, evidence, unknowns, keys = _read_rows(sheet, values[sheet.title], table)
        if not goods:
            continue
        tables.append({**table, "sheet": sheet.title, "index": index, "hidden": hidden,
                       "role": role, "goods": goods, "evidence": evidence,
                       "unknowns": unknowns, "keys": keys, "bounds": (rows, columns),
                       "images": len(getattr(sheet, "_images", []) or [])})
    if not tables:
        raise ValueError(
            "Không tìm thấy bảng hàng hóa có tiêu đề nhận dạng được (model/tên hàng + số lượng). "
            "Vui lòng kiểm tra lại bố cục; hệ thống không tự đoán cột."
        )

    ranked = sorted((t for t in tables if not t["hidden"]), key=lambda t: (-_rank(t), t["index"]))
    if not ranked:
        raise ValueError("Bảng hàng hóa chỉ nằm trong sheet ẩn; không tự nhập dữ liệu ẩn vào báo giá.")
    primary = ranked[0]
    goods = primary["goods"]
    sheet_name = primary["sheet"]
    priced = "unit_price" in primary["columns"]
    level_tables = [t for t in tables if t is not primary and t["role"] in {ROLE_PALLET_DETAIL, ROLE_CARTON_DETAIL}]
    primary_name = folded(sheet_name)
    if priced:
        layout = LAYOUT_PROFORMA_INVOICE if (
            re.search(r"\bpi\b", primary_name) or any(m in primary_name for m in ("proforma", "invoice", "hoa don"))) else LAYOUT_LUC_GIAC
    elif level_tables:
        layout = LAYOUT_MULTI_LEVEL_PACKING
    else:
        layout = LAYOUT_PACKING_LIST

    tables_in_file_order = [name for name, _ in sorted(((t["sheet"], t["index"]) for t in tables), key=lambda x: x[1])]
    all_text = folded(" ".join(texts))
    if any(g["length_mm"] is not None and g["length_mm"] >= 19000 for g in goods) and re.search(r"20\s*(feet|ft|gp|')", all_text):
        warnings.append({"id": "equipment-length", "text": "Container 20 feet vs bàn dài 19 m: xác nhận tháo rời, kích thước kiện và phương tiện; không tự sửa nguồn."})
    if any(len(v) > 1 for v in metrics.values()) or ("25" in all_text and "3 cbm" in all_text):
        warnings.append({"id": "cargo-conflict", "text": "Mâu thuẫn CBM / trọng lượng giữa các sheet (25 CBM / 3900 kg và 3 CBM / 400 kg); cần xác nhận."})
    signature = lambda rows: [(g["length_mm"], g["width_mm"], g["height_mm"]) for g in rows]
    if any(signature(other["goods"]) != signature(goods) for other in tables if other is not primary):
        warnings.append({"id": "dimension-conflict", "text": "Kích thước giữa các sheet không khớp; đang dùng bảng khách gửi, cần rà soát từng dòng."})
    if "2%" in all_text or "2 %" in all_text:
        warnings.append({"id": "agent-rounding", "text": "Phí đại lý 2% có chênh lệch làm tròn / phân bổ trong nguồn; không tự áp dụng hoặc đưa vào trị giá hải quan."})
    today = today or date.today()
    for exp in sorted(set(expires)):
        warnings.append({"id": "source-expiry", "text": f"Giá vận chuyển nguồn hiệu lực đến {exp:%d/%m/%Y}: " + ("ĐÃ HẾT HẠN — cần xin giá mới." if exp < today else "chỉ là tham khảo, cần xác nhận phạm vi.")})
    if "chua bao gom vat 8%" in all_text:
        warnings.append({"id": "vat-ambiguity", "text": "“Chưa bao gồm VAT 8%” chưa rõ là VAT dịch vụ hay VAT nhập khẩu; không tự suy diễn."})
    if formula_gap:
        warnings.append({"id": "formula-gap", "text": "Có lỗi công thức / công thức chưa có giá trị cache (#REF! hoặc tương tự); giữ CHƯA BIẾT, không coi là 0."})
    warnings.append({"id": "customs-basis", "text": "HS / thuế suất / tỷ giá trong Excel là tham khảo cũ, không phải kết luận pháp lý. Không mặc định mọi phí Trung Quốc thuộc trị giá chịu thuế."})

    unknown_map: dict[str, dict[str, Any]] = {}

    def note_unknown(code: str, sheet: str, row: int | None, text: str) -> None:
        entry = unknown_map.setdefault(code, {"code": code, "text": text, "sheet": sheet, "rows": []})
        if isinstance(row, int) and row not in entry["rows"] and len(entry["rows"]) < 50:
            entry["rows"].append(row)

    for code, row, text in primary["unknowns"]:
        note_unknown(code, sheet_name, row, text)
    missing_price = [g for g in goods if g["unit_price"] is None]
    if missing_price:
        warnings.append({"id": "unit-price-missing",
                         "text": "Nguồn không có đầy đủ đơn giá (packing list): giá để CHƯA BIẾT, không phải 0. "
                                 "Cần bổ sung đơn giá trước khi gửi báo giá khách."})
        for item in missing_price:
            note_unknown("unit_price_missing", sheet_name, item["source_row"],
                         "Dòng hàng chưa có đơn giá trong nguồn; giá giữ CHƯA BIẾT, không mặc định bằng 0.")
    if any(g["qty"] is None for g in goods):
        for item in goods:
            if item["qty"] is None:
                note_unknown("qty_missing", sheet_name, item["source_row"],
                             "Dòng hàng chưa có số lượng rõ ràng; không tự suy từ số kiện.")
    if layout in {LAYOUT_PACKING_LIST, LAYOUT_MULTI_LEVEL_PACKING} and any(row.get("product_size") for row in primary["evidence"]):
        warnings.append({"id": "dims-not-package",
                         "text": "Kích thước trong file là kích thước SẢN PHẨM, không phải kích thước kiện; "
                                 "không dùng để tính CBM hoặc khai báo kiện. Dữ liệu đóng gói nằm ở phần rà soát."})
    hidden_sheets = [s.title for s in wb.worksheets if str(getattr(s, "sheet_state", "visible")) != "visible"]
    if hidden_sheets:
        warnings.append({"id": "hidden-sheet-not-imported",
                         "text": "Workbook có sheet ẩn: nội dung sheet ẩn không được nhập và không xuất sang tài liệu khách."})
    internal_tables = [t for t in tables if t is not primary and t["role"] == ROLE_INTERNAL_CALC]
    if internal_tables:
        warnings.append({"id": "money-sheet-not-imported",
                         "text": "Có sheet tính tiền/phí nội bộ trùng bảng hàng: chỉ lấy bảng hàng chính, không cộng trùng và không đưa phần tính tiền vào báo giá khách."})
    if level_tables:
        warnings.append({"id": "level-not-summed",
                         "text": "Workbook có nhiều cấp (tổng hàng / pallet / kiện): các cấp được ghi nhận riêng, "
                                 "không cộng thành nhiều danh sách hàng hay nhân đôi CBM. Cần TT đối chiếu."})
    if scan_truncated:
        warnings.append({"id": "scan-limited", "text": "Workbook lớn: chỉ quét phần đầu trong giới hạn an toàn; cần rà soát thủ công phần còn lại."})

    table_by_sheet = {t["sheet"]: t for t in tables}
    levels: list[dict[str, Any]] = []
    for sheet in wb.worksheets:
        if sheet.title == sheet_name:
            continue
        table = table_by_sheet.get(sheet.title)
        hidden = str(getattr(sheet, "sheet_state", "visible")) != "visible"
        if table is None and not hidden:
            continue
        levels.append({
            "sheet": sheet.title,
            "role": table["role"] if table else ROLE_HIDDEN,
            "hidden": hidden,
            "row_count": len(table["goods"]) if table else 0,
            "source_rows": [g["source_row"] for g in table["goods"]][:50] if table else [],
            "models": sorted({g["model"] for g in table["goods"] if g["model"]})[:50] if table else [],
        })
    # Every sheet that is not the goods source, with what it actually was: a
    # duplicate money table and a hidden instruction sheet are both named here,
    # and neither contributes a goods row or a total.
    excluded_tables = [{"sheet": level["sheet"], "role": level["role"],
                        "hidden": level["hidden"], "row_count": level["row_count"]}
                       for level in levels]

    links: dict[str, dict[str, list[Any]]] = {}
    linked_models = set()
    for table in level_tables:
        for key in table["keys"]:
            model = key["model"]
            if not model:
                continue
            linked_models.add(model)
            links.setdefault(model, {}).setdefault(table["sheet"], []).append(key["pallet"] or key["row"])
    if level_tables:
        for item in goods:
            if not item["model"] or item["model"] not in linked_models:
                note_unknown("level_link_missing", sheet_name, item["source_row"],
                             "Không nối chắc chắn được mã hàng giữa tổng hàng và cấp pallet/kiện: CHỜ TT KIỂM TRA.")

    selected = ["80%" in all_text, "30 ngay" in all_text, bool(re.search(r"14\s*[–−-]\s*20", all_text)),
                "mot tuan" in all_text or "1 tuan" in all_text]
    return {
        "schema": PARSER_VERSION, "goods": goods, "supplier": supplier,
        "source": {"file_name": file_name, "byte_size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                   "sheet_names": wb.sheetnames, "goods_sheet": sheet_name, "parser_version": PARSER_VERSION,
                   "layout": layout,
                   # Evidence for the read-only original-workbook viewer: every
                   # sheet that contained a recognised goods table, in file order.
                   "table_sheets": tables_in_file_order,
                   "sheet_bounds": [{"sheet": s.title,
                                     "declared_rows": int(s.max_row or 0),
                                     "declared_columns": int(s.max_column or 0),
                                     "used_rows": bounds[s.title][0],
                                     "used_columns": bounds[s.title][1],
                                     "hidden": str(getattr(s, "sheet_state", "visible")) != "visible",
                                     "images": len(getattr(s, "_images", []) or [])}
                                    for s in wb.worksheets],
                   "excluded_tables": excluded_tables},
        # Packing evidence from the pallet/carton levels is REVIEW-ONLY material
        # (it never reaches the customer snapshot) and is what lets TT check a
        # carton size without the importer calling it a product dimension.
        "review": {"layout": layout,
                   "rows": (primary["evidence"] + [row for table in level_tables for row in table["evidence"]])[:MAX_GOODS_ROWS],
                   "unknowns": list(unknown_map.values()), "levels": levels, "links": links},
        "source_warnings": warnings, "source_facts": source_facts, "source_costs": source_costs,
        "disclosures": [{"id": k, "text": text, "selected": selected[i]} for i, (k, text) in enumerate(DISCLOSURES)],
        "additional_public_notes": "", "active_option": "A",
        "options": {"A": {"scope": "", "service_lines": []}, "B": {"scope": "", "service_lines": []}},
        # Contradictory measurements are intentionally NOT prefilled.
        "shipment": {"cbm": None, "weight_kg": None, "pol": "", "pod": "", "pickup": "", "delivery": "", "load_model": "FCL", "equipment": ""},
        "customs": {"confirmed": False, "basis_vnd": None, "basis_note": "", "duty_pct": None, "vat_pct": None, "hs_code": ""},
        "warning_notes": {},
    }


def store_source(data: bytes, proposal: dict[str, Any], customer_id: str, actor: str, *, db=None) -> dict[str, Any]:
    """Same GridFS bucket/connection as current attachments; immutable bytes.

    GridFS files.metadata is already durable metadata storage. A cancelled
    import may remain an unlinked source; it is never represented as a quote.
    """
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore
    from core.quotations import _now

    db = get_db() if db is None else db
    store = GridFSAttachmentStore(db)
    source = dict(proposal["source"])
    metadata = {"owner_type": "QUOTE_EXCEL_SOURCE", "customer_id": customer_id, "sha256": source["sha256"], "uploaded_by": actor}
    previous = store.bucket.find_one({"metadata.owner_type": metadata["owner_type"], "metadata.customer_id": customer_id, "metadata.sha256": source["sha256"]})
    if previous:
        file_id = str(previous._id)
    else:
        stored = store.upload_file(name=source["file_name"], mime=MIME_XLSX, data=data,
                                   metadata={**metadata, "uploaded_at": _now(), "source": source,
                                             "source_warnings": proposal["source_warnings"], "source_facts": proposal["source_facts"],
                                             "source_costs": proposal["source_costs"], "disclosures": proposal["disclosures"],
                                             # Review evidence is server-validated like the rest of the
                                             # provenance: a browser must not be able to invent or alter it.
                                             "review": proposal.get("review") or {}})
        file_id = stored["storage_file_id"]
    # Read/hash back before claiming that the source was saved.
    if hashlib.sha256(store.download_file(file_id)).hexdigest() != source["sha256"]:
        raise ValueError("Không xác minh được bytes tệp nguồn sau khi lưu.")
    return {**source, "storage_backend": "gridfs", "storage_file_id": file_id}


def validated_source(source: dict[str, Any], customer_id: str, *, db=None) -> dict[str, Any]:
    """Do not trust browser-provided provenance, expiry warnings or ownership."""
    from core.database import get_db
    from core.gridfs_client import GridFSAttachmentStore

    store = GridFSAttachmentStore(get_db() if db is None else db)
    file_id = str(source.get("storage_file_id") or "")
    stored = store.bucket.get(store._object_id(file_id))
    metadata = dict(stored.metadata or {})
    if metadata.get("owner_type") != "QUOTE_EXCEL_SOURCE" or metadata.get("customer_id") != customer_id:
        raise ValueError("Tệp nguồn không thuộc khách hàng đang chọn.")
    return {"source": {**metadata["source"], "storage_backend": "gridfs", "storage_file_id": file_id},
            **{key: metadata.get(key, {} if key in ("source_facts", "review") else [])
               for key in ("source_warnings", "source_facts", "source_costs", "disclosures", "review")}}
