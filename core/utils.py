"""Tiện ích dùng chung, không chứa nghiệp vụ riêng của giao diện."""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import logging
import lzma
import os
import re
import sqlite3
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore[assignment]

from core.config import CARRIER_LINKS, GEMINI_API_KEYS, GEMINI_MODEL, TARIFF_DB_PATH

LOGGER = logging.getLogger("logistics_pro")
MONEY_QUANT = Decimal("0.01")


def to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """Parse tiền an toàn, hỗ trợ định dạng 1,234,567 và 1.234.567."""
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
            # Ký tự xuất hiện sau cùng được coi là dấu thập phân khi có 1-2 số phía sau.
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


def safe_float(value: Any) -> float:
    return float(to_decimal(value))


def money_round(value: Any, currency: str = "VND") -> Decimal:
    amount = to_decimal(value)
    quant = Decimal("1") if currency.upper() == "VND" else MONEY_QUANT
    return amount.quantize(quant, rounding=ROUND_HALF_UP)


def parse_date_optional(value: Any) -> date | None:
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


def parse_date(value: Any, default: date | None = None) -> date:
    return parse_date_optional(value) or default or date.today()


def get_shipment_business_date(shipment: Any) -> date | None:
    """Return a shipment business date without inventing a date.
    Priority: order_date (canonical business order date from GETFLY)
    > created_at (record creation timestamp) > top-level fallback.
    Missing or malformed values stay ``None`` for bounded filters.
    """
    if not isinstance(shipment, dict):
        return None
    data = shipment.get("data")
    section = data.get("0.0") if isinstance(data, dict) else None
    if isinstance(section, dict):
        # Prefer order_date (GETFLY "Ngày đặt hàng") as canonical business date
        order_dt = parse_date_optional(section.get("order_date"))
        if order_dt is not None:
            return order_dt
        # Fall back to created_at (GETFLY "Ngày tạo")
        nested = parse_date_optional(section.get("created_at"))
        if nested is not None:
            return nested
    return parse_date_optional(shipment.get("created_at"))

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def mark_changed(resource: str = "shipments") -> None:
    if st is None:
        return
    st.session_state.needs_refresh = True
    dirty = st.session_state.setdefault("dirty_resources", set())
    dirty.add(resource)


def log_error(error: Exception | str, context: str = "") -> None:
    LOGGER.exception("%s: %s", context, error) if isinstance(error, Exception) else LOGGER.error("%s: %s", context, error)


def escape_html(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def get_tracking_url(carrier: str, ref_no: str) -> str:
    ref = quote_plus(str(ref_no).strip())
    template = CARRIER_LINKS.get(carrier)
    if template:
        return template.format(ref=ref)
    # Air cargo fallback: tìm theo AWB trên Google thay vì tạo URL hãng không chắc chắn.
    return f"https://www.google.com/search?q={quote_plus(f'{carrier} cargo tracking {ref_no}') }"


# LOGI_TARIFF_FAST_DB_02 — Admin-managed tariff asset -> local SQLite.
# Runtime NEVER opens the XLSX. ADMIN uploads a workbook once; the backend
# converts it to an indexed SQLite database, stores the compressed database in
# Mongo, and each app process materializes that compact asset into /tmp on the
# first lookup. An explicit existing TARIFF_DB_PATH still wins.
_TARIFF_TEMP_PREFIX = "logistics-tariff-"


def invalidate_tariff_db_cache() -> None:
    """Forget the resolved tariff path after an Admin replaces the source."""
    resolve_tariff_db_path.cache_clear()


@lru_cache(maxsize=1)
def resolve_tariff_db_path() -> Path:
    configured = Path(TARIFF_DB_PATH)

    # Admin-managed asset is the primary source once it exists. This prevents a
    # stale default tariff.db left in an app process from shadowing a fresh
    # workbook the Admin just published.
    try:
        from core.database import load_tariff_asset
        asset = load_tariff_asset()
    except Exception as exc:  # noqa: BLE001 - lookup must fail closed
        log_error(exc, "resolve_tariff_db_path.asset")
        asset = None

    if isinstance(asset, dict):
        compressed = asset.get("payload_lzma")
        sha256 = str(asset.get("db_sha256") or "").strip().lower()
        if isinstance(compressed, (bytes, bytearray)) and sha256:
            target = Path(tempfile.gettempdir()) / (
                f"{_TARIFF_TEMP_PREFIX}{sha256[:16]}.db"
            )
            if target.exists() and target.stat().st_size > 0:
                return target

            tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            try:
                raw = lzma.decompress(bytes(compressed))
                digest = hashlib.sha256(raw).hexdigest()
                if digest != sha256:
                    raise ValueError(
                        "Tariff database checksum mismatch: "
                        f"{digest} != {sha256}"
                    )
                tmp.write_bytes(raw)
                os.replace(tmp, target)
                return target
            except (OSError, lzma.LZMAError, ValueError) as exc:
                log_error(exc, "resolve_tariff_db_path.materialize")
            finally:
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass

    # Backward-compatible fallback for deployments that still own an explicit
    # local tariff database and have not published an Admin-managed asset yet.
    return configured

def _tariff_columns(conn: sqlite3.Connection) -> set[str]:
    try:
        return {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(tariff_table)").fetchall()
        }
    except sqlite3.Error:
        return set()


def _fts_query(raw: str) -> str:
    # FTS syntax is never accepted from the caller verbatim. Each Unicode word
    # becomes an escaped prefix term, so a product phrase is an AND search.
    tokens = re.findall(r"\w+", raw, flags=re.UNICODE)
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens[:12])


def fast_search_tariff(keyword: str, limit: int = 100) -> pd.DataFrame:
    """Fast bounded tariff lookup.

    * Code-looking input: indexed exact / prefix B-tree lookup.
    * Product/policy text: SQLite FTS5 over Vietnamese description + policy.
    * Older externally configured databases without FTS fall back to LIKE.

    The XLSX is build input only and is never loaded in the request path.
    """
    raw = str(keyword or "").strip()
    if len(raw) < 2:
        return pd.DataFrame()
    db_path = resolve_tariff_db_path()
    if not db_path.exists():
        return pd.DataFrame()

    bounded_limit = max(1, min(int(limit), 200))
    normalized_code = re.sub(r"[.\s]", "", raw)
    code_like = normalized_code.isdigit() and 2 <= len(normalized_code) <= 8

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            conn.execute("PRAGMA query_only=ON")
            columns = _tariff_columns(conn)
            if "Mã HS" not in columns:
                return pd.DataFrame()

            row_order = '"_source_row"' if "_source_row" in columns else "rowid"

            if code_like:
                if len(normalized_code) == 8:
                    sql = f'''
                        SELECT * FROM tariff_table
                        WHERE "Mã HS" = ?
                        ORDER BY {row_order}
                        LIMIT ?
                    '''
                    return pd.read_sql_query(
                        sql, conn, params=(normalized_code, bounded_limit)
                    )

                # GLOB with a constant prefix is optimized by SQLite into a
                # range scan over idx_tariff_hs; exact heading goes first.
                sql = f'''
                    SELECT * FROM tariff_table
                    WHERE "Mã HS" GLOB ?
                    ORDER BY
                        CASE WHEN "Mã HS" = ? THEN 0 ELSE 1 END,
                        length("Mã HS"),
                        "Mã HS",
                        {row_order}
                    LIMIT ?
                '''
                return pd.read_sql_query(
                    sql,
                    conn,
                    params=(
                        normalized_code + "*",
                        normalized_code,
                        bounded_limit,
                    ),
                )

            fts = _fts_query(raw)
            if fts:
                try:
                    return pd.read_sql_query(
                        '''
                        SELECT t.*
                        FROM tariff_fts
                        JOIN tariff_table AS t ON t.id = tariff_fts.rowid
                        WHERE tariff_fts MATCH ?
                        ORDER BY bm25(tariff_fts), coalesce(t."_source_row", t.id)
                        LIMIT ?
                        ''',
                        conn,
                        params=(fts, bounded_limit),
                    )
                except (sqlite3.Error, pd.errors.DatabaseError):
                    # Governed external v1 DBs may not have the v2 FTS table.
                    pass

            text_columns = [
                name
                for name in (
                    "Mô tả tiếng Việt",
                    "Mô tả tiếng Anh",
                    "Chính sách mặt hàng",
                    "Giảm VAT",
                )
                if name in columns
            ]
            if not text_columns:
                return pd.DataFrame()
            search_term = f"%{raw}%"
            where = " OR ".join(f'"{name}" LIKE ?' for name in text_columns)
            sql = f"SELECT * FROM tariff_table WHERE {where} LIMIT ?"
            return pd.read_sql_query(
                sql,
                conn,
                params=tuple([search_term] * len(text_columns) + [bounded_limit]),
            )
    except (sqlite3.Error, pd.errors.DatabaseError, OSError) as exc:
        log_error(exc, "fast_search_tariff")
        return pd.DataFrame()


HS_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "stt": {"type": "integer"},
            "input_name": {"type": "string"},
            "hs_code": {"type": "string"},
            "vnaccs_name": {"type": "string"},
            "english_name": {"type": "string"},
            "rule": {"type": "string"},
            "reasoning": {"type": "string"},
            "note": {"type": "string"},
            "confidence": {"type": "number"},
            "requires_human_review": {"type": "boolean"},
            "missing_information": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["stt", "input_name", "hs_code", "vnaccs_name", "english_name", "rule", "reasoning", "note", "confidence", "requires_human_review", "missing_information"],
    },
}


def get_ai_response_hs_batch(text: str) -> list[dict[str, Any]]:
    """Gọi Gemini bằng Google GenAI SDK, hỗ trợ danh sách key dự phòng."""
    if not str(text).strip():
        return []
    if not GEMINI_API_KEYS:
        raise RuntimeError(
            "Chưa cấu hình Gemini. Dùng [gemini].api_key, [gemini].api_keys "
            "hoặc GEMINI_KEYS trong secrets.toml."
        )
    try:
        from google import genai
        from google.genai import types
        from core.prompts import HS_CLASSIFICATION_PROMPT
    except ImportError as exc:
        raise RuntimeError("Thiếu thư viện google-genai. Hãy cài requirements.txt của gói nâng cấp.") from exc

    failures: list[str] = []
    for index, api_key in enumerate(GEMINI_API_KEYS, start=1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=HS_CLASSIFICATION_PROMPT.format(user_input=text),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=HS_RESPONSE_SCHEMA,
                    temperature=0.1,
                ),
            )
            payload = json.loads(response.text or "[]")
            if not isinstance(payload, list):
                raise ValueError("Gemini không trả về JSON Array.")
            return payload
        except Exception as exc:
            failures.append(f"key #{index}: {type(exc).__name__}: {str(exc)[:240]}")

    raise RuntimeError("Tất cả Gemini API key đều thất bại. " + " | ".join(failures))


def load_cbpg_rules() -> dict[str, Any]:
    """Điểm mở rộng cho rule versioning; rule đang dùng vẫn nằm trong tariff view."""
    return {"version": "legacy-2026-01", "requires_human_review": True}


def send_telegram_msg(message: str) -> bool:
    from core.notifications import enqueue_raw_notification
    return enqueue_raw_notification(message)
