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

#: Configured path remains supported; the canonical reader may transparently
#: fall back to the repository-bundled compressed 2026 database.
TARIFF_DB_PATH = core_utils.TARIFF_DB_PATH

#: The canonical reader ignores keywords shorter than this (same rule client-side).
MIN_QUERY_LENGTH = 2

#: Hard ceiling on rows delivered to the view-model (payload boundedness).
MAX_ROWS = 200

_PROVENANCE_NOTE = (
    "Nguồn tra cứu được build từ file BIỂU THUẾ do Admin cung cấp và lưu thành "
    "SQLite có chỉ mục để tra nhanh. Kết quả dùng cho tra cứu nội bộ; KHÔNG thay "
    "thế quyết định phân loại chính thức hoặc văn bản pháp luật gốc."
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
    """Honest status + embedded provenance of the governed reference DB."""
    db_path = core_utils.resolve_tariff_db_path()
    path = str(db_path)
    if not db_path.exists():
        return {
            "configured": False,
            "path": path,
            "rows": None,
            "note": (
                "Chưa nạp dữ liệu BIỂU THUẾ. Hãy cấu hình TARIFF_DB_PATH hoặc "
                "đưa bundle tariff_2026.db.xz vào data/."
            ),
            "sourceFile": None,
            "sourceSha256": None,
            "year": None,
            "searchMode": None,
        }

    rows: int | None = None
    meta: dict[str, str] = {}
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            rows = int(
                conn.execute("SELECT COUNT(*) FROM tariff_table").fetchone()[0]
            )
            try:
                meta = {
                    str(key): str(value)
                    for key, value in conn.execute(
                        "SELECT key, value FROM tariff_meta"
                    ).fetchall()
                }
            except sqlite3.Error:
                meta = {}
    except (sqlite3.Error, TypeError, ValueError):
        rows = None

    return {
        "configured": True,
        "path": path,
        "rows": rows,
        "note": None if rows else (
            "Cơ sở dữ liệu BIỂU THUẾ đã kết nối nhưng đang trống."
        ),
        "sourceFile": meta.get("source_filename"),
        "sourceSha256": meta.get("source_sha256"),
        "year": meta.get("year"),
        "searchMode": meta.get("search"),
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
            "source": source.get("sourceFile"),
            "effectiveDate": source.get("year"),
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
    canonical = {
        "Mã HS": "hsCode",
        "Mô tả tiếng Việt": "descriptionVi",
        "Mô tả tiếng Anh": "descriptionEn",
        "Đơn vị tính": "unit",
        "NK TT": "importNormal",
        "NK ưu đãi": "importPreferential",
        "VAT": "vat",
        "Chính sách mặt hàng": "policy",
        "Giảm VAT": "vatReduction",
    }
    row: dict[str, Any] = {
        "hsCode": None,
        "descriptionVi": None,
        "descriptionEn": None,
        "unit": None,
        "importNormal": None,
        "importPreferential": None,
        "vat": None,
        "policy": None,
        "vatReduction": None,
        "fields": [],
    }
    for column, value in record.items():
        name = str(column)
        if name in {"id", "_source_row", "V"}:
            continue
        text = _clean(value)
        key = canonical.get(name)
        if key:
            row[key] = text
        elif text is not None:
            # Only NON-EMPTY agreement/rate columns are delivered; a 40-column
            # source row never becomes a 40-field payload full of empty values.
            row["fields"].append({"label": name, "value": text})
    return row

