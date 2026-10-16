"""Bounded Lục Giác furniture XLSX reader, not a universal Excel importer.

openpyxl reads values/cached results only; formulas and external links are never
executed. Parsed data is a review proposal, not a quote or a legal tax opinion.
Original bytes use the app's existing GridFS adapter; no new connection/store.
"""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
from typing import Any
from zipfile import BadZipFile, ZipFile

from openpyxl import load_workbook

PARSER_VERSION = "luc-giac/1"
MAX_BYTES = 5 * 1024 * 1024
MAX_EXPANDED_BYTES = 25 * 1024 * 1024
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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


def _table(sheet) -> tuple[int, dict[str, int]] | None:
    # The supported layout has a short title/supplier block, then an explicit
    # dimension/quantity/RMB-unit-price table. Never infer columns by position.
    for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 35), max_col=min(sheet.max_column, 24)):
        cols: dict[str, int] = {}
        for cell in row:
            text = folded(cell.value)
            if "kich thuoc" in text:
                cols["dimensions"] = cell.column
            elif text in {"so luong", "sl", "quantity", "qty"}:
                cols["qty"] = cell.column
            elif "don gia" in text and any(c in text for c in ("rmb", "cny")):
                cols["unit_price"] = cell.column
            elif text in {"model", "ma san pham", "ma hang"}:
                cols["model"] = cell.column
            elif "vat lieu" in text:
                cols["material"] = cell.column
            elif text in {"ten hang", "hang hoa", "san pham", "mo ta"}:
                cols["description"] = cell.column
            elif "ghi chu" in text:
                cols["note"] = cell.column
        if {"dimensions", "qty", "unit_price"} <= cols.keys():
            return row[0].row, cols
    return None


def parse_luc_giac_workbook(data: bytes, file_name: str, *, today: date | None = None) -> dict[str, Any]:
    """Return an editable proposal. No cost/FX/tax is automatically applied."""
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
    if len(wb.worksheets) > 8 or any(s.max_row > 2500 or s.max_column > 40 for s in wb):
        raise ValueError("V1 chỉ hỗ trợ bảng Lục Giác nhỏ (≤8 sheet, 2500 dòng, 40 cột).")

    warnings: list[dict[str, str]] = []
    tables: list[tuple[str, list[dict[str, Any]]]] = []
    texts: list[str] = []
    supplier = ""
    metrics: dict[str, set[float]] = {"cbm": set(), "weight_kg": set()}
    source_facts: dict[str, Any] = {}
    expires: list[date] = []
    source_costs: list[dict[str, Any]] = []
    formula_gap = False
    for sheet in wb:
        val_sheet = values[sheet.title]
        for row in sheet:
            for cell in row:
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

        header = _table(sheet)
        if not header:
            continue
        header_row, cols = header
        goods: list[dict[str, Any]] = []
        for r in range(header_row + 1, min(sheet.max_row, header_row + 200) + 1):
            dims = _dimensions(val_sheet.cell(r, cols["dimensions"]).value)
            if all(v is None for v in dims):
                # Ignore totals, blank rows and narrative blocks, not fake items.
                continue
            item = {k: str(val_sheet.cell(r, c).value or "") for k, c in cols.items() if k in {"description", "model", "material", "note"}}
            goods.append({
                "id": f"row-{r}", **item,
                "length_mm": dims[0], "width_mm": dims[1], "height_mm": dims[2],
                "qty": _number(val_sheet.cell(r, cols["qty"]).value),
                "unit_price": _number(val_sheet.cell(r, cols["unit_price"]).value), "currency": "CNY",
                "source_sheet": sheet.title, "source_row": r,
            })
        if goods:
            tables.append((sheet.title, goods))
    if not tables:
        raise ValueError("Không tìm thấy bảng Lục Giác: cần cột Kích thước (mm), Số lượng, Đơn giá (RMB). V1 không tự đoán bố cục khác.")
    # Prefer the explicit customer sheet, not internal duplicated calculations.
    tables.sort(key=lambda t: 0 if "khach" in folded(t[0]) else 1)
    sheet_name, goods = tables[0]
    all_text = folded(" ".join(texts))
    if any(g["length_mm"] is not None and g["length_mm"] >= 19000 for g in goods) and re.search(r"20\s*(feet|ft|gp|')", all_text):
        warnings.append({"id": "equipment-length", "text": "Container 20 feet vs bàn dài 19 m: xác nhận tháo rời, kích thước kiện và phương tiện; không tự sửa nguồn."})
    if any(len(v) > 1 for v in metrics.values()) or ("25" in all_text and "3 cbm" in all_text):
        warnings.append({"id": "cargo-conflict", "text": "Mâu thuẫn CBM / trọng lượng giữa các sheet (25 CBM / 3900 kg và 3 CBM / 400 kg); cần xác nhận."})
    signature = lambda rows: [(g["length_mm"], g["width_mm"], g["height_mm"]) for g in rows]
    if any(signature(other) != signature(goods) for _, other in tables[1:]):
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
    selected = ["80%" in all_text, "30 ngay" in all_text, bool(re.search(r"14\s*[–−-]\s*20", all_text)), "mot tuan" in all_text or "1 tuan" in all_text]
    return {
        "schema": PARSER_VERSION, "goods": goods, "supplier": supplier,
        "source": {"file_name": file_name, "byte_size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                   "sheet_names": wb.sheetnames, "goods_sheet": sheet_name, "parser_version": PARSER_VERSION,
                   # Evidence for the read-only original-workbook viewer: every
                   # sheet that contained a recognised goods table. A second such
                   # sheet is a duplicated internal calculation, not a customer
                   # presentation.
                   "table_sheets": [name for name, _ in tables]},
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
                                             "source_costs": proposal["source_costs"], "disclosures": proposal["disclosures"]})
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
            **{key: metadata.get(key, [] if key != "source_facts" else {}) for key in ("source_warnings", "source_facts", "source_costs", "disclosures")}}
