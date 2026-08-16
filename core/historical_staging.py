"""Read-only historical workbook staging for LOG-C06.

The workbook is evidence, not a canonical financial source.  This module keeps raw
cells and deterministic proposals in separate fields and intentionally has no imports
from Streamlit, MongoDB, the canonical ledger, payment code, or AI services.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import xlrd


PARSER_VERSION = "log-c06-staging-v2"
SALE_OWNER = "Thành"
UNKNOWN_CURRENCY = "UNKNOWN"
STAGING_STATES = frozenset(
    {"RAW", "PROPOSED", "CONFIRMED", "REVIEW_REQUIRED", "REJECTED", "NOT_APPLICABLE"}
)
EVENT_TYPES = frozenset(
    {
        "payable_to_a_bo",
        "payment_to_a_bo",
        "held_money_credit",
        "received_on_behalf",
        "paid_on_behalf",
        "customer_receipt",
        "refund_return_credit",
        "fx_conversion_context",
        "adjustment",
        "unallocated",
        "unknown",
    }
)

DEFAULT_SOURCE_PATH = Path(r"D:\Copy of TOYS-2025 - Copy.xls")
SOURCE_FILE_NAMES = ("Copy of TOYS-2025 - Copy.xls", "TOYS-2025 - Copy.xls")

_HEADER_TOKENS = (
    "sale",
    "khach",
    "customer",
    "ngay thang",
    "date",
    "nhan usd",
    "hach ra tien te",
    "chuyen ho",
    "ghi chu",
    "remark",
    "note",
    "tong",
    "so tien",
    "amount",
    "thanh tien",
    "合计",
)
_AMOUNT_LABEL_TOKENS = (
    "amount",
    "so tien",
    "thanh tien",
    "tong",
    "phi",
    "nhan usd",
    "hach ra tien te",
    "chuyen ho",
    "合计",
    "金额",
)


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """Parse workbook numbers without importing the application utility layer."""

    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    raw = str(value).strip()
    if not raw:
        return default
    cleaned = re.sub(r"[^0-9,\.\-]", "", raw)
    if cleaned in {"", "-", ".", ","}:
        return default
    try:
        if "," in cleaned and "." in cleaned:
            last_comma, last_dot = cleaned.rfind(","), cleaned.rfind(".")
            decimal_sep = "," if last_comma > last_dot else "."
            integer_sep = "." if decimal_sep == "," else ","
            tail = cleaned.split(decimal_sep)[-1]
            if len(tail) <= 2:
                cleaned = cleaned.replace(integer_sep, "").replace(decimal_sep, ".")
            else:
                cleaned = cleaned.replace(",", "").replace(".", "")
        elif cleaned.count(",") > 1 or cleaned.count(".") > 1:
            cleaned = cleaned.replace(",", "").replace(".", "")
        elif "," in cleaned:
            head, tail = cleaned.rsplit(",", 1)
            cleaned = f"{head.replace(',', '')}.{tail}" if len(tail) <= 2 else cleaned.replace(",", "")
        elif "." in cleaned:
            head, tail = cleaned.rsplit(".", 1)
            if len(tail) == 3 and len(head.replace("-", "")) >= 1:
                cleaned = cleaned.replace(".", "")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return default


def _parse_date_optional(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:19] if "%H" in fmt else raw[:10], fmt).date()
        except ValueError:
            continue
    return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def normalize_text(value: Any) -> str:
    """Return accent-insensitive text used only by controlled matching rules."""

    raw = str(value or "").translate(str.maketrans({"đ": "d", "Đ": "D"}))
    decomposed = unicodedata.normalize("NFKD", raw)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_marks).strip().casefold()


def _is_non_empty(value: Any) -> bool:
    if value in (None, ""):
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _cell_name(row_index: int, column_index: int) -> str:
    # xlrd.formula.cellname() accepts zero-based indexes and performs the
    # one-based Excel conversion itself.  Adding one here shifted every raw
    # provenance cell by one row and one column.
    return xlrd.formula.cellname(row_index, column_index)


def source_file_hash(source_path: str | Path) -> str:
    """Return the SHA-256 of the source without opening it for writing."""

    digest = hashlib.sha256()
    with Path(source_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_source_workbook(
    explicit_path: str | Path | None = None,
    *,
    project_root: str | Path | None = None,
) -> Path | None:
    """Find the known workbook without scanning or mutating broad directories."""

    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())
    candidates.append(DEFAULT_SOURCE_PATH)
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[1]
    candidates.extend(root / name for name in SOURCE_FILE_NAMES)
    candidates.extend(root.parent / name for name in SOURCE_FILE_NAMES)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _cell_uses_date_format(book: xlrd.book.Book, cell: xlrd.sheet.Cell) -> bool:
    if cell.ctype == xlrd.XL_CELL_DATE:
        return True
    try:
        xf = book.xf_list[cell.xf_index]
        fmt = book.format_map.get(xf.format_key)
        format_string = str(fmt.format_str if fmt else "").casefold()
    except (AttributeError, IndexError, KeyError):
        return False
    return bool(re.search(r"(?:yy|dd|d/|/d|m/|/m)", format_string))


def _parse_xls_date(book: xlrd.book.Book, cell: xlrd.sheet.Cell) -> tuple[str | None, Any]:
    if _cell_uses_date_format(book, cell):
        try:
            value = xlrd.xldate_as_datetime(cell.value, book.datemode)
            return value.date().isoformat(), _jsonable(cell.value)
        except (TypeError, ValueError, OverflowError):
            return None, _jsonable(cell.value)
    raw = str(cell.value or "").strip()
    if not raw or not re.search(r"\d{1,4}[/-]\d{1,2}[/-]\d{1,4}", raw):
        return None, _jsonable(cell.value)
    parsed = _parse_date_optional(raw)
    return (parsed.isoformat() if parsed else None), _jsonable(cell.value)


def _looks_like_header(value: Any) -> bool:
    normalized = normalize_text(value)
    return bool(normalized) and any(token in normalized for token in _HEADER_TOKENS)


def _header_kind(value: Any) -> str:
    normalized = normalize_text(value)
    if "sale" in normalized:
        return "sale"
    if "khach" in normalized or "customer" in normalized:
        return "customer"
    if "ngay thang" in normalized or normalized == "date":
        return "date"
    if "ghi chu" in normalized or "remark" in normalized or "note" in normalized:
        return "note"
    if "ref" in normalized or "bill" in normalized or "ma hang" in normalized:
        return "reference"
    return "amount" if any(token in normalized for token in _AMOUNT_LABEL_TOKENS) else "other"


def _update_headers(header_map: dict[int, str], row_values: Sequence[Any]) -> None:
    for column_index, value in enumerate(row_values):
        if _looks_like_header(value):
            header_map[column_index] = str(value)


def _cell_label(header_map: Mapping[int, str], column_index: int) -> str:
    return str(header_map.get(column_index) or "")


def _is_date_cell(book: xlrd.book.Book, cell: xlrd.sheet.Cell) -> bool:
    parsed, _ = _parse_xls_date(book, cell)
    return parsed is not None


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    raw = str(value).strip()
    if not raw or not re.search(r"\d", raw):
        return None
    parsed = _to_decimal(raw, default=Decimal("NaN"))
    if parsed.is_nan() or not parsed.is_finite():
        return None
    return float(parsed)


_NUMERIC_TEXT_RE = re.compile(
    r"^\s*[-+]?(?:\d[\d\s,./]*)(?:\s*(?:vnd|cny|rmb|usd|yuan|¥|₫))?\s*$",
    re.IGNORECASE,
)


def _looks_like_numeric_text(value: Any) -> bool:
    """Allow numeric/currency text but reject formula/reference prose."""

    if not isinstance(value, str):
        return False
    return bool(_NUMERIC_TEXT_RE.fullmatch(value.strip()))


def _amount_candidates(
    book: xlrd.book.Book,
    row_index: int,
    row_cells: Sequence[xlrd.sheet.Cell],
    header_map: Mapping[int, str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for column_index, cell in enumerate(row_cells):
        if not _is_non_empty(cell.value) or _is_date_cell(book, cell):
            continue
        if cell.ctype == xlrd.XL_CELL_TEXT and not _looks_like_numeric_text(cell.value):
            continue
        amount = _numeric_value(cell.value)
        if amount is None:
            continue
        label = _cell_label(header_map, column_index)
        normalized_label = normalize_text(label)
        if cell.ctype == xlrd.XL_CELL_TEXT and not any(
            token in normalized_label for token in _AMOUNT_LABEL_TOKENS
        ):
            continue
        if "chuyen ho" in normalized_label:
            rank = 0
        elif "hach ra tien te" in normalized_label:
            rank = 1
        elif "nhan usd" in normalized_label:
            rank = 2
        elif any(token in normalized_label for token in _AMOUNT_LABEL_TOKENS):
            rank = 3
        else:
            rank = 4
        candidates.append(
            {
                "cell": _cell_name(row_index, column_index),
                "column": column_index,
                "amount": amount,
                "raw_value": _jsonable(cell.value),
                "label": label,
                "rank": rank,
            }
        )
    return sorted(candidates, key=lambda item: (item["rank"], item["column"]))


def _field_cell(
    row_index: int,
    row_cells: Sequence[xlrd.sheet.Cell],
    header_map: Mapping[int, str],
    kind: str,
) -> tuple[str | None, str | None]:
    for column_index, label in header_map.items():
        if _header_kind(label) != kind or column_index >= len(row_cells):
            continue
        value = row_cells[column_index].value
        if _is_non_empty(value) and normalize_text(value) not in {"sale", "khach", "customer"}:
            return str(value).strip(), _cell_name(row_index, column_index)
    return None, None


def _row_text(row_cells: Sequence[xlrd.sheet.Cell]) -> str:
    return " | ".join(str(cell.value).strip() for cell in row_cells if _is_non_empty(cell.value))


def _known_party(text: str) -> str | None:
    normalized = normalize_text(text)
    if "bg green" in normalized or "b&g green" in normalized:
        return "B&G Green"
    if "luc giac" in normalized:
        return "Lục Giác"
    if "thanh vu" in normalized:
        return "Xưởng đồ chơi Thành Vũ"
    if "nha may" in normalized or "factory" in normalized:
        return "Nhà máy"
    if "chi hai" in normalized or "c hai" in normalized:
        return "Chị Hải"
    return None


def _sale_proposal(raw_sale: str | None, row_text: str) -> dict[str, Any]:
    normalized_sale = normalize_text(raw_sale)
    normalized_row = normalize_text(row_text)
    result: dict[str, Any] = {
        "internal_sale_owner": None,
        "candidate_internal_sale_owner": None,
        "sale_evidence": "missing",
        "sale_confidence": "none",
        "sale_reason": "Không có SALE rõ ràng trong dòng nguồn.",
    }
    if normalized_sale == "thanh":
        result.update(
            {
                "internal_sale_owner": SALE_OWNER,
                "sale_evidence": "explicit_sale_field",
                "sale_confidence": "high",
                "sale_reason": "SALE trong cột SALE là Thành.",
            }
        )
        return result
    if normalized_sale:
        if re.search(r"\bthanh\b", normalized_sale):
            result.update(
                {
                    "candidate_internal_sale_owner": SALE_OWNER,
                    "sale_evidence": "explicit_field_noncanonical",
                    "sale_confidence": "medium",
                    "sale_reason": "Cột SALE có Thành nhưng giá trị không khớp chính xác tên SALE chuẩn.",
                }
            )
        else:
            result.update(
                {
                    "candidate_internal_sale_owner": raw_sale,
                    "sale_evidence": "explicit_other_sale",
                    "sale_confidence": "high",
                    "sale_reason": f"SALE rõ ràng là {raw_sale}, không phải Thành.",
                }
            )
        return result
    if re.search(r"\bthanh\b", normalized_row):
        result.update(
            {
                "candidate_internal_sale_owner": SALE_OWNER,
                "sale_evidence": "free_text_only",
                "sale_confidence": "low",
                "sale_reason": "Chỉ thấy chữ Thành trong ghi chú/nội dung, không có SALE explicit.",
            }
        )
    return result


def _event_type(row_text: str, *, is_checkpoint: bool) -> str:
    normalized = normalize_text(row_text)
    if is_checkpoint:
        return "adjustment"
    if "a bo phai tra" in normalized or "credit" in normalized or "return credit" in normalized:
        return "refund_return_credit"
    if "tien khach da thanh toan" in normalized or "khach da thanh toan" in normalized:
        return "customer_receipt"
    if "nhan ho" in normalized or "nhan mon" in normalized or "chuyen cho thanh" in normalized:
        return "received_on_behalf"
    if "ke toan da chuyen" in normalized and "mon cua thanh" in normalized:
        return "paid_on_behalf"
    if "thanh toan tien hang cho" in normalized or "thanh toan cho nha may" in normalized:
        return "paid_on_behalf"
    if any(token in normalized for token in ("thanh toan ho", "chuyen ho", "chuyen wa", "bao chuyen", "da tt cho truong thanh")):
        return "paid_on_behalf"
    if "ty gia" in normalized or "hach ra tien te" in normalized or "nhan usd" in normalized:
        return "fx_conversion_context"
    if "a bo" in normalized and any(token in normalized for token in ("thanh toan", "pay", "chuyen")):
        return "payment_to_a_bo"
    if "a bo" in normalized and any(token in normalized for token in ("no", "phai tra", "payable")):
        return "payable_to_a_bo"
    return "unknown"


def _bucket_for_event(event_type: str) -> str | None:
    return {
        "payable_to_a_bo": "payable_to_a_bo",
        "payment_to_a_bo": "payable_to_a_bo",
        "held_money_credit": "held_credit",
        "received_on_behalf": "received_on_behalf",
        "paid_on_behalf": "paid_on_behalf",
        "refund_return_credit": "held_credit",
        "unallocated": "unallocated",
    }.get(event_type)


def _currency_for_candidate(
    candidate: Mapping[str, Any],
    row_text: str,
    header_map: Mapping[int, str],
) -> str:
    raw = normalize_text(candidate.get("raw_value"))
    label = normalize_text(candidate.get("label"))
    normalized_row = normalize_text(row_text)
    if "usd" in raw or ("nhan usd" in label and "vnd" not in normalized_row):
        return "USD"
    if "vnd" in raw and "hach ra tien te" not in label:
        return "VND"
    if re.search(r"\b(?:cny|rmb|yuan|te)\b", normalized_row):
        return "CNY"
    if "hach ra tien te" in label or "chuyen ho" in label:
        return "CNY"
    if "nhan usd" in label:
        return "USD"
    if any("usd" in normalize_text(value) for value in header_map.values()) and "vnd" not in normalized_row:
        return "USD" if "nhan usd" in label else UNKNOWN_CURRENCY
    return UNKNOWN_CURRENCY


def _fx_rate(row_text: str) -> float | None:
    match = re.search(r"(?:ty gia|tỷ giá)\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)", row_text, re.IGNORECASE)
    if not match:
        return None
    value = _to_decimal(match.group(1).replace(",", ""), default=Decimal("NaN"))
    return None if value.is_nan() else float(value)


def _source_reference(row_index: int, raw_values: Mapping[str, Any]) -> str:
    cells = list(raw_values)
    if not cells:
        return f"row:{row_index + 1}"
    return f"{cells[0]}:{cells[-1]}"


def _checkpoint_reference(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b[A-ZĐ][A-ZĐ]?\d+\b", text, flags=re.IGNORECASE)))


def _proposal_for_row(
    *,
    book: xlrd.book.Book,
    row_index: int,
    row_cells: Sequence[xlrd.sheet.Cell],
    header_map: Mapping[int, str],
    explicit_date: str | None,
    inherited_date: str | None,
) -> tuple[dict[str, Any], list[str]]:
    row_text = _row_text(row_cells)
    normalized_row = normalize_text(row_text)
    amounts = _amount_candidates(book, row_index, row_cells, header_map)
    sale_raw, sale_cell = _field_cell(row_index, row_cells, header_map, "sale")
    customer_raw, customer_cell = _field_cell(row_index, row_cells, header_map, "customer")
    sale = _sale_proposal(sale_raw, row_text)
    has_amount = bool(amounts)
    checkpoint_markers = [normalize_text(cell.value) for cell in row_cells if _is_non_empty(cell.value)]
    is_checkpoint = has_amount and (
        any(
            marker in {"cua thanh", "tong cua thanh", "tong"}
            or marker.startswith("cua thanh =")
            for marker in checkpoint_markers
        )
        or "合计" in row_text
    )
    event_type = _event_type(row_text, is_checkpoint=is_checkpoint)
    bucket = _bucket_for_event(event_type)
    chosen = amounts[0] if amounts else {}
    if "vnd" in normalized_row:
        converted = [item for item in amounts if "hach ra tien te" in normalize_text(item.get("label"))]
        if converted:
            chosen = converted[0]
    currency = _currency_for_candidate(chosen, row_text, header_map) if chosen else UNKNOWN_CURRENCY
    related_amount = None
    related_currency = None
    for candidate in amounts:
        if candidate is chosen:
            continue
        if "vnd" in normalize_text(candidate.get("raw_value")):
            related_amount = candidate.get("amount")
            related_currency = "VND"
            break
    rate = _fx_rate(row_text)
    if event_type == "fx_conversion_context" and rate and amounts:
        converted_candidates = [candidate for candidate in amounts if candidate is not chosen]
        if converted_candidates:
            related_candidate = max(converted_candidates, key=lambda candidate: candidate["amount"])
            if related_candidate["amount"] > chosen.get("amount", 0):
                related_amount = related_candidate.get("amount")
                related_currency = "VND"
    source_party = customer_raw or _known_party(row_text)
    holder = "A Bò" if event_type in {"received_on_behalf", "paid_on_behalf", "refund_return_credit"} else None
    beneficiary = SALE_OWNER if sale.get("internal_sale_owner") == SALE_OWNER else None
    reasons: list[str] = [str(sale.get("sale_reason") or "")]
    flags: list[str] = []
    if not has_amount:
        status = "RAW"
        reasons = []
    else:
        if not sale_raw:
            flags.append("MISSING_SALE")
        if currency == UNKNOWN_CURRENCY:
            flags.append("MISSING_OR_UNCERTAIN_CURRENCY")
        if event_type in {"received_on_behalf", "paid_on_behalf"} and source_party is None:
            flags.append("MISSING_SOURCE_PARTY")
        if inherited_date and not explicit_date:
            flags.append("INHERITED_DATE_CONTEXT")
        if is_checkpoint:
            flags.append("CHECKPOINT_EVIDENCE")
            if "=" in row_text or _checkpoint_reference(row_text):
                flags.append("CHECKPOINT_REFERENCE_REVIEW")
        if sale.get("sale_evidence") == "explicit_other_sale":
            status = "NOT_APPLICABLE"
        elif sale.get("sale_evidence") == "explicit_sale_field" and currency != UNKNOWN_CURRENCY and event_type != "unknown" and not flags:
            status = "PROPOSED"
        else:
            status = "REVIEW_REQUIRED"
        if not explicit_date and inherited_date:
            reasons.append("Ngày không có ở dòng này; chỉ giữ ngày kế thừa để review, không ghi đè raw.")
        if currency == UNKNOWN_CURRENCY:
            reasons.append("Không xác định được tiền tệ từ trường/ghi chú có kiểm soát.")
        if event_type == "customer_receipt":
            reasons.append("Đây là tiền khách vào tài khoản TT; không tự chứng minh thanh toán cho A Bò.")
        if is_checkpoint:
            reasons.append("Đây là checkpoint/tổng thủ công; không dùng như một dòng thành phần.")
        if sale.get("sale_evidence") == "free_text_only":
            reasons.append("Chữ Thành chỉ nằm trong text tự do; cần xác minh SALE explicit.")
        if sale.get("sale_evidence") == "explicit_other_sale":
            reasons.append("Dòng thuộc SALE khác và được tách khỏi view SALE Thành.")
    if event_type == "unknown" and has_amount:
        reasons.append("Chưa có tín hiệu đủ rõ để ép dòng vào một loại nghiệp vụ.")
    evidence_sufficiency = "high" if status == "PROPOSED" else "review_required" if has_amount else "none"
    confidence = "high" if status == "PROPOSED" else "medium" if sale.get("sale_evidence") in {"explicit_field_noncanonical", "explicit_other_sale"} else "low"
    amount_source_kind = None
    if chosen:
        chosen_column = int(chosen.get("column", -1))
        if 0 <= chosen_column < len(row_cells):
            amount_source_kind = (
                "numeric_text"
                if row_cells[chosen_column].ctype == xlrd.XL_CELL_TEXT
                else "numeric_cell"
            )
    proposal = {
        "internal_sale_owner": sale.get("internal_sale_owner"),
        "candidate_internal_sale_owner": sale.get("candidate_internal_sale_owner"),
        "source": source_party,
        "payer": source_party,
        "holder": holder,
        "beneficial_owner": beneficiary,
        "beneficiary": beneficiary,
        "customer": customer_raw,
        "a_bo_relationship": "A Bò holder/partner context" if holder else None,
        "shipment": None,
        "financial_case": event_type,
        "event_type": event_type,
        "amount": chosen.get("amount") if chosen else None,
        "amount_source_cell": chosen.get("cell") if chosen else None,
        "amount_source_label": chosen.get("label") if chosen else None,
        "amount_source_raw_value": chosen.get("raw_value") if chosen else None,
        "amount_source_kind": amount_source_kind,
        "currency": currency,
        "fx_rate": rate,
        "related_amount": related_amount,
        "related_currency": related_currency,
        "classification": event_type,
        "restriction": "historical_checkpoint" if is_checkpoint else "currency_unknown" if currency == UNKNOWN_CURRENCY else None,
        "candidate_allocation": None,
        "candidate_bucket": bucket,
        "evidence_sufficiency": evidence_sufficiency,
        "confidence": confidence,
        "reasons": [reason for reason in reasons if reason],
        "anomalies": flags,
        "sale_evidence": sale.get("sale_evidence"),
        "sale_confidence": sale.get("sale_confidence"),
        "source_party_evidence": source_party,
        "raw_sale_cell": sale_cell,
        "raw_customer_cell": customer_cell,
        "checkpoint_key": "THANH_ACCUMULATED" if is_checkpoint else None,
        "checkpoint_references": _checkpoint_reference(row_text) if is_checkpoint else [],
    }
    return proposal, flags


def _stage_sheet(
    book: xlrd.book.Book,
    sheet: xlrd.sheet.Sheet,
    *,
    source_file: str,
    source_hash: str,
    imported_at: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    header_map: dict[int, str] = {}
    inherited_date: str | None = None
    explicit_dates: dict[int, str] = {}
    for row_index in range(sheet.nrows):
        row_cells = [sheet.cell(row_index, column_index) for column_index in range(sheet.ncols)]
        raw_values: dict[str, Any] = {}
        raw_types: dict[str, int] = {}
        date_candidates: list[tuple[str, Any]] = []
        for column_index, cell in enumerate(row_cells):
            if not _is_non_empty(cell.value):
                continue
            name = _cell_name(row_index, column_index)
            raw_values[name] = _jsonable(cell.value)
            raw_types[name] = int(cell.ctype)
            parsed_date, raw_date_value = _parse_xls_date(book, cell)
            if parsed_date:
                date_candidates.append((parsed_date, raw_date_value))
        _update_headers(header_map, [cell.value for cell in row_cells])
        if date_candidates:
            explicit_date = date_candidates[0][0]
            explicit_dates[row_index] = explicit_date
            inherited_date = explicit_date
        else:
            explicit_date = None
        if not raw_values:
            continue
        proposal, flags = _proposal_for_row(
            book=book,
            row_index=row_index,
            row_cells=row_cells,
            header_map=header_map,
            explicit_date=explicit_date,
            inherited_date=inherited_date if explicit_date is None else None,
        )
        raw_text = _row_text(row_cells)
        source_id = "C06-" + hashlib.sha256(
            f"{source_hash}|{sheet.name}|{row_index + 1}".encode("utf-8")
        ).hexdigest()[:24]
        date_context = inherited_date if explicit_date is None else None
        item = {
            "source_item_id": source_id,
            "source_file": source_file,
            "source_file_hash": source_hash,
            "sheet": sheet.name,
            "source_row": row_index + 1,
            "source_cell_range": _source_reference(row_index, raw_values),
            "source_reference": f"{sheet.name}!{_source_reference(row_index, raw_values)}",
            "raw_values": raw_values,
            "raw_cell_types": raw_types,
            "raw_text": raw_text,
            "raw_note": raw_text,
            "raw_date": explicit_date,
            "raw_date_serial": date_candidates[0][1] if date_candidates else None,
            "inherited_date_context": date_context,
            "raw_sale": proposal.get("raw_sale") or None,
            "raw_customer": proposal.get("customer") or None,
            "raw_reference": _checkpoint_reference(raw_text),
            "raw_amount": proposal.get("amount"),
            "raw_currency": proposal.get("currency"),
            "parser_version": PARSER_VERSION,
            "imported_at": imported_at,
            "review_status": "RAW",
            "proposal": proposal,
            "review_reason": "; ".join(proposal.get("reasons") or []),
            "anomaly_flags": list(flags),
            "review_history": [],
        }
        item["raw_sale"] = _raw_sale_value(row_cells, header_map)
        item["raw_customer"] = _raw_customer_value(row_cells, header_map)
        item["review_status"] = "RAW" if proposal.get("amount") is None else _proposal_status(proposal)
        items.append(item)
    _add_sequence_anomalies(items, explicit_dates)
    return items


def _raw_sale_value(row_cells: Sequence[xlrd.sheet.Cell], header_map: Mapping[int, str]) -> str | None:
    for column_index, label in header_map.items():
        if _header_kind(label) != "sale" or column_index >= len(row_cells):
            continue
        value = row_cells[column_index].value
        if _is_non_empty(value) and normalize_text(value) not in {"sale"}:
            return str(value).strip()
    return None


def _raw_customer_value(row_cells: Sequence[xlrd.sheet.Cell], header_map: Mapping[int, str]) -> str | None:
    for column_index, label in header_map.items():
        if _header_kind(label) != "customer" or column_index >= len(row_cells):
            continue
        value = row_cells[column_index].value
        if _is_non_empty(value) and normalize_text(value) not in {"khach", "customer"}:
            return str(value).strip()
    return None


def _proposal_status(proposal: Mapping[str, Any]) -> str:
    if proposal.get("sale_evidence") == "explicit_other_sale":
        return "NOT_APPLICABLE"
    if (
        proposal.get("sale_evidence") == "explicit_sale_field"
        and proposal.get("currency") != UNKNOWN_CURRENCY
        and proposal.get("event_type") != "unknown"
        and not proposal.get("anomalies")
    ):
        return "PROPOSED"
    return "REVIEW_REQUIRED"


def _add_sequence_anomalies(items: list[dict[str, Any]], explicit_dates: Mapping[int, str]) -> None:
    by_sheet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item.get("raw_date"):
            by_sheet[str(item.get("sheet"))].append(item)
    for sheet_items in by_sheet.values():
        for current, following in zip(sheet_items, sheet_items[1:]):
            current_date = _parse_date_optional(current.get("raw_date"))
            following_date = _parse_date_optional(following.get("raw_date"))
            if current_date and following_date and current_date > following_date:
                flags = list(current.get("anomaly_flags") or [])
                if "DATE_OUT_OF_SEQUENCE" not in flags:
                    flags.append("DATE_OUT_OF_SEQUENCE")
                current["anomaly_flags"] = flags
                proposal = current.get("proposal") or {}
                proposal["anomalies"] = flags
                proposal.setdefault("reasons", []).append(
                    "Ngày này đứng sau một ngày nhỏ hơn trong chuỗi nguồn; không tự sửa ngày."
                )
                current["proposal"] = proposal
                if current.get("review_status") == "PROPOSED":
                    current["review_status"] = "REVIEW_REQUIRED"
                    current["review_reason"] = "; ".join(proposal.get("reasons") or [])


def _mark_duplicate_looking(items: list[dict[str, Any]]) -> None:
    fingerprints: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        raw_values = item.get("raw_values") or {}
        if item.get("raw_amount") is None or len(raw_values) < 2:
            continue
        signature = json.dumps(raw_values, ensure_ascii=False, sort_keys=True, default=str)
        fingerprints[signature].append(item)
    for matches in fingerprints.values():
        if len(matches) < 2:
            continue
        for item in matches:
            flags = list(item.get("anomaly_flags") or [])
            if "DUPLICATE_LOOKING" not in flags:
                flags.append("DUPLICATE_LOOKING")
            item["anomaly_flags"] = flags
            proposal = item.get("proposal") or {}
            proposal["anomalies"] = flags
            proposal.setdefault("reasons", []).append("Có dòng khác có raw cells giống nhau; không tự xoá bản nào.")
            item["proposal"] = proposal
            if item.get("review_status") == "PROPOSED":
                item["review_status"] = "REVIEW_REQUIRED"
                item["review_reason"] = "; ".join(proposal.get("reasons") or [])


def stage_workbook(
    source_path: str | Path | None = None,
    *,
    imported_at: str | None = None,
) -> dict[str, Any]:
    """Read every non-empty workbook row into a deterministic staging batch."""

    resolved = locate_source_workbook(source_path)
    if resolved is None:
        raise FileNotFoundError("Không tìm thấy workbook lịch sử A Bò.")
    digest = source_file_hash(resolved)
    imported = imported_at or _utc_now().isoformat()
    book = xlrd.open_workbook(str(resolved), formatting_info=True, on_demand=False)
    items: list[dict[str, Any]] = []
    for sheet in book.sheets():
        items.extend(
            _stage_sheet(
                book,
                sheet,
                source_file=str(resolved),
                source_hash=digest,
                imported_at=imported,
            )
        )
    _mark_duplicate_looking(items)
    return {
        "source_file": str(resolved),
        "source_file_hash": digest,
        "parser_version": PARSER_VERSION,
        "imported_at": imported,
        "sheet_names": list(book.sheet_names()),
        "item_count": len(items),
        "items": items,
    }


def stage_fixture_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return isolated, normalized fixture rows for behavior tests."""

    result: list[dict[str, Any]] = []
    for row in rows:
        item = deepcopy(dict(row))
        item.setdefault("source_item_id", "fixture-" + hashlib.sha256(json.dumps(item, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16])
        item.setdefault("parser_version", PARSER_VERSION)
        item.setdefault("review_status", "RAW")
        item.setdefault("review_history", [])
        item.setdefault("anomaly_flags", list((item.get("proposal") or {}).get("anomalies") or []))
        result.append(item)
    return result


def search_staging_items(items: Iterable[Mapping[str, Any]], query: str) -> list[dict[str, Any]]:
    """Search only staged evidence/proposals, never the global canonical ledger."""

    needle = normalize_text(query)
    if not needle:
        return [deepcopy(dict(item)) for item in items]
    results: list[dict[str, Any]] = []
    for item in items:
        proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
        haystack = normalize_text(
            json.dumps(
                {
                    "source_item_id": item.get("source_item_id"),
                    "sheet": item.get("sheet"),
                    "source_row": item.get("source_row"),
                    "source_reference": item.get("source_reference"),
                    "raw_text": item.get("raw_text"),
                    "raw_sale": item.get("raw_sale"),
                    "raw_customer": item.get("raw_customer"),
                    "raw_amount": item.get("raw_amount"),
                    "proposal": proposal,
                },
                ensure_ascii=False,
                default=str,
            )
        )
        if needle in haystack:
            results.append(deepcopy(dict(item)))
    return results


def summarize_staging(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(items)
    states = Counter(str(item.get("review_status") or "RAW") for item in rows)
    other_sales = [
        item
        for item in rows
        if item.get("raw_amount") is not None
        and (item.get("proposal") or {}).get("sale_evidence") == "explicit_other_sale"
    ]
    anomalies = [item for item in rows if item.get("anomaly_flags")]
    currencies = Counter(
        str((item.get("proposal") or {}).get("currency") or UNKNOWN_CURRENCY).upper()
        for item in rows
        if item.get("raw_amount") is not None
    )
    return {
        "total_items": len(rows),
        "states": dict(states),
        "confirmed": states.get("CONFIRMED", 0),
        "high_confidence": sum(
            1
            for item in rows
            if (item.get("proposal") or {}).get("confidence") == "high"
            and item.get("review_status") in {"PROPOSED", "CONFIRMED"}
        ),
        "needs_review": states.get("REVIEW_REQUIRED", 0),
        "other_sale": len(other_sales),
        "anomalies": len(anomalies),
        "currencies": dict(currencies),
    }


def source_evidence(item: Mapping[str, Any]) -> dict[str, Any]:
    """Return a UI-safe evidence view while retaining raw values unchanged."""

    return {
        "source_file": item.get("source_file"),
        "source_file_hash": item.get("source_file_hash"),
        "sheet": item.get("sheet"),
        "source_row": item.get("source_row"),
        "source_cell_range": item.get("source_cell_range"),
        "source_reference": item.get("source_reference"),
        "raw_values": deepcopy(item.get("raw_values") or {}),
        "raw_note": item.get("raw_note"),
        "raw_date": item.get("raw_date"),
        "inherited_date_context": item.get("inherited_date_context"),
        "raw_amount": item.get("raw_amount"),
        "raw_currency": item.get("raw_currency"),
        "raw_sale": item.get("raw_sale"),
        "raw_customer": item.get("raw_customer"),
        "raw_reference": deepcopy(item.get("raw_reference") or []),
        "parser_version": item.get("parser_version"),
        "imported_at": item.get("imported_at"),
        "review_status": item.get("review_status"),
        "proposal": deepcopy(item.get("proposal") or {}),
        "review_reason": item.get("review_reason"),
        "anomaly_flags": list(item.get("anomaly_flags") or []),
        "review_history": deepcopy(item.get("review_history") or []),
    }


__all__ = [
    "DEFAULT_SOURCE_PATH",
    "EVENT_TYPES",
    "PARSER_VERSION",
    "SALE_OWNER",
    "STAGING_STATES",
    "UNKNOWN_CURRENCY",
    "locate_source_workbook",
    "normalize_text",
    "search_staging_items",
    "source_evidence",
    "source_file_hash",
    "stage_fixture_rows",
    "stage_workbook",
    "summarize_staging",
]
