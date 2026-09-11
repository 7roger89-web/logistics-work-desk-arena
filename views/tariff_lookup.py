"""Bounded READ-ONLY tariff lookup adapter for the ``/tra-cuu-thue`` workspace.

Presentation adapter ONLY (LOGI_TARIFF_LOOKUP_01). It wraps the EXISTING
canonical reader (``core.utils.fast_search_tariff``) over the deployment-
governed reference database at ``TARIFF_DB_PATH``. No new database, no new
API, no writer, no classifier, no external service.

BUSINESS TRUTH RULES (finance/customs-adjacent — fail honest, never fabricate):

- UNKNOWN != ZERO: a value the source does not carry arrives as ``None`` and
  is never coerced to ``0`` / ``"0%"``.
- Values are passed through VERBATIM (no float re-formatting, no unit or
  percent conversion) so a display can never alter the underlying data.
- The canonical sanitized schema (``scripts/initialize_tariff_db.py``) carries
  only ``Mã HS`` / ``Mô tả tiếng Việt`` / ``Mô tả tiếng Anh``. There are NO
  duty / VAT / provenance / effective-date columns in the current authoritative
  schema, so ``provenance`` is reported as absent and the UI must show the
  bounded "not an official ruling" warning. If an operator later connects a
  richer governed database, extra columns surface verbatim via ``fields``
  without this adapter inventing semantics for them.
- The lookup never claims an official HS classification. It only finds rows
  that already exist in the organization's reference database.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd

from core import utils as core_utils
from core.utils import fast_search_tariff

#: Same governed path the canonical reader reads — one source of truth.
TARIFF_DB_PATH = core_utils.TARIFF_DB_PATH

#: The canonical reader ignores keywords shorter than this (same rule client-side).
MIN_QUERY_LENGTH = 2

#: Hard ceiling on rows delivered to the view-model (payload boundedness).
MAX_ROWS = 200

_PROVENANCE_NOTE = (
    "Nguồn nội bộ: cơ sở dữ liệu tham chiếu nội bộ (tariff_table) hiện không "
    "có metadata nguồn / ngày hiệu lực, nên tính chính danh chưa được thiết lập. "
    "Kết quả chỉ mang tính tra cứu tham khảo, KHÔNG phải quyết định phân loại "
    "chính thức của hải quan; vui lòng đối chiếu biểu thuế nhập khẩu có hiệu lực."
)


def _clean(value: Any) -> str | None:
    """Verbatim string passthrough; genuinely-absent values stay ``None``."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    # Common SQL NULL spellings are "no data", never a real value.
    if text == "" or text.lower() in {"none", "nan", "null", "<na>"}:
        return None
    return text


def tariff_source_status() -> dict[str, Any]:
    """Honest status of the governed reference database (never raises)."""
    db_path = core_utils.TARIFF_DB_PATH
    path = str(db_path)
    if not db_path.exists():
        return {
            "configured": False,
            "path": path,
            "rows": None,
            "note": (
                "Chưa nạp dữ liệu biểu thuế tham chiếu (TARIFF_DB_PATH). "
                "Kết nối dữ liệu đã được tổ chức phê duyệt qua quy trình quản "
                "trị dữ liệu; kho mã này không chứa dữ liệu mẫu thay thế."
            ),
        }
    rows: int | None = None
    try:
        with sqlite3.connect(path) as conn:
            rows = int(conn.execute("SELECT COUNT(*) FROM tariff_table").fetchone()[0])
    except (sqlite3.Error, TypeError, ValueError):
        rows = None
    return {
        "configured": True,
        "path": path,
        "rows": rows,
        "note": None if rows else (
            "Cơ sở dữ liệu tham chiếu đã kết nối nhưng đang trống "
            "(chưa nạp dữ liệu biểu thuế đã được phê duyệt)."
        ),
    }


def tariff_lookup_view(query: object, limit: int = 100) -> dict[str, Any]:
    """One bounded lookup over the EXISTING reader, shaped for the view-model.

    Read-only. Every field the canonical schema does not carry is ``None``
    (rendered as an explicit unknown), never zero.
    """
    raw = str(query or "").strip()
    source = tariff_source_status()
    result: dict[str, Any] = {
        "query": raw[:120],
        "searched": False,
        "reason": None,
        "rows": [],
        "count": 0,
        "truncated": False,
        "limit": min(int(limit), MAX_ROWS),
        "source": source,
        # Provenance is what the backend actually knows: nothing authoritative.
        "provenance": {
            "source": None,
            "effectiveDate": None,
            "authoritative": False,
            "note": _PROVENANCE_NOTE,
        },
    }
    if len(raw) < MIN_QUERY_LENGTH:
        result["reason"] = (
            "Nhập ít nhất 2 ký tự: mã HS (chính xác hoặc một phần) hoặc tên hàng."
        )
        return result
    try:
        frame = fast_search_tariff(raw, limit=result["limit"])
    except Exception:  # pragma: no cover - reader already fails closed
        frame = pd.DataFrame()
    result["searched"] = True
    if frame is None or frame.empty:
        result["reason"] = (
            "Không tìm thấy dòng nào khớp trong cơ sở dữ liệu tham chiếu nội bộ."
            if source.get("configured") and source.get("rows")
            else "Chưa có dữ liệu biểu thuế để tra cứu."
        )
        return result
    if len(frame) > result["limit"]:
        frame = frame.head(result["limit"])
    result["truncated"] = bool(source.get("rows") and len(frame) >= result["limit"])
    rows = [_row_projection(record) for record in frame.to_dict(orient="records")]
    result["rows"] = rows
    result["count"] = len(rows)
    return result


def _row_projection(record: dict[str, Any]) -> dict[str, Any]:
    canonical = {"Mã HS": "hsCode", "Mô tả tiếng Việt": "descriptionVi",
                 "Mô tả tiếng Anh": "descriptionEn"}
    row: dict[str, Any] = {"hsCode": None, "descriptionVi": None,
                           "descriptionEn": None, "fields": []}
    for column, value in record.items():
        text = _clean(value)
        key = canonical.get(str(column))
        if key:
            row[key] = text
        else:
            # Unknown extra columns of a richer deployment DB pass through
            # verbatim, uninterpreted — no invented rate semantics.
            row["fields"].append({"label": str(column), "value": text})
    return row
