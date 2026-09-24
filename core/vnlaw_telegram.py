"""Telegram -> VNLAW read-only adapter for internal Support/Sale lookup.

This module owns no legal logic. It sends one bounded question to the existing
VNLAW POST /verified-query boundary, then renders only the authority groups
that VNLAW itself marked as verified/official information. Discovery candidates
are never queried or promoted here.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

import requests

DEFAULT_TOP_K = 3
DEFAULT_TIMEOUT_SECONDS = 15
MAX_TELEGRAM_MESSAGE = 3900
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_VIETNAM_TIMEZONE = timezone(timedelta(hours=7))

_FORCE_LABELS = {
    "in_force": "có hiệu lực tại thời điểm tra cứu trong phạm vi VNLAW đã xác minh",
    "suspended": "tạm ngưng tại thời điểm tra cứu trong phạm vi VNLAW đã xác minh",
    "repealed": "đã hết hiệu lực tại thời điểm tra cứu trong phạm vi VNLAW đã xác minh",
    "absent": "chưa tồn tại tại thời điểm tra cứu trong phạm vi đã xác minh",
}


class VNLAWConfigError(RuntimeError):
    """Missing/unsafe integration configuration."""


class VNLAWServiceError(RuntimeError):
    """VNLAW is configured but did not return a usable verified result."""


def parse_allowed_user_ids(raw: str | None) -> frozenset[str]:
    """Parse comma/space/semicolon-separated Telegram numeric user IDs."""
    if not raw:
        return frozenset()
    values = re.split(r"[,;\s]+", raw.strip())
    return frozenset(value for value in values if value.isdigit())


def allowed_user_ids() -> frozenset[str]:
    return parse_allowed_user_ids(os.environ.get("TELEGRAM_ALLOWED_USER_IDS"))


def is_allowed_telegram_user(user_id: int | str | None) -> bool:
    if user_id is None:
        return False
    allowed = allowed_user_ids()
    return bool(allowed) and str(user_id) in allowed


def parse_question(text: str, *, today: date | None = None) -> tuple[str, str]:
    """Return (query, as_of_date).

    Plain text means current as of today. Staff can explicitly query history
    with /law YYYY-MM-DD <question>. Dates embedded in ordinary prose are
    never guessed into legal-time semantics.
    """
    value = (text or "").strip()
    if not value:
        raise ValueError("Câu hỏi đang trống.")

    if value.startswith("/"):
        first, _, rest = value.partition(" ")
        command = first.split("@", 1)[0].casefold()
        if command in {"/law", "/vnlaw"}:
            value = rest.strip()
        elif command in {"/start", "/help"}:
            raise ValueError("HELP")
        else:
            raise ValueError("Lệnh không hỗ trợ. Dùng /law <câu hỏi>.")

    vietnam_today = datetime.now(_VIETNAM_TIMEZONE).date()
    as_of = (today or vietnam_today).isoformat()
    first, sep, rest = value.partition(" ")
    if _DATE_RE.fullmatch(first):
        try:
            as_of = date.fromisoformat(first).isoformat()
        except ValueError as exc:
            raise ValueError("Ngày tra cứu phải có dạng YYYY-MM-DD và là ngày hợp lệ.") from exc
        value = rest.strip() if sep else ""
    if not value:
        raise ValueError("Thiếu câu hỏi sau ngày tra cứu.")
    return value, as_of


def _service_config() -> tuple[str, str | None]:
    base_url = (os.environ.get("VNLAW_API_URL") or "").strip().rstrip("/")
    token = (os.environ.get("VNLAW_API_TOKEN") or "").strip() or None
    if not base_url:
        raise VNLAWConfigError("VNLAW_API_URL chưa được cấu hình.")

    parsed = urlparse(base_url)
    host = (parsed.hostname or "").casefold()
    is_loopback = host in _LOOPBACK_HOSTS
    if parsed.scheme not in {"http", "https"} or not host:
        raise VNLAWConfigError("VNLAW_API_URL không hợp lệ.")
    if parsed.scheme != "https" and not is_loopback:
        raise VNLAWConfigError("VNLAW_API_URL bên ngoài máy phải dùng HTTPS.")
    if not is_loopback and not token:
        raise VNLAWConfigError("VNLAW_API_TOKEN là bắt buộc cho VNLAW API từ xa.")
    return base_url, token


def query_vnlaw(
    query: str,
    as_of_date: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    session: Any = requests,
) -> dict[str, Any]:
    """Call the existing VNLAW verified-query boundary; no discovery fallback."""
    base_url, token = _service_config()
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = session.post(
            f"{base_url}/verified-query",
            json={
                "query": query,
                "as_of_date": as_of_date,
                "top_k": top_k,
                "scope": "verified",
            },
            headers=headers,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise VNLAWServiceError(f"Không gọi được VNLAW: {exc}") from exc

    if not isinstance(payload, dict):
        raise VNLAWServiceError("VNLAW trả về dữ liệu không hợp lệ.")
    for key in ("legal_hits", "technical_hits", "guidance_hits"):
        if not isinstance(payload.get(key), list):
            raise VNLAWServiceError(f"VNLAW thiếu nhóm dữ liệu hợp lệ: {key}.")
    return payload


def _clip(text: Any, limit: int = 520) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _append_with_budget(lines: list[str], section: list[str], limit: int) -> bool:
    candidate = "\n".join(lines + section)
    if len(candidate) > limit:
        return False
    lines.extend(section)
    return True


def format_vnlaw_result(
    payload: Mapping[str, Any], *, limit: int = MAX_TELEGRAM_MESSAGE
) -> str:
    """Render VNLAW authority groups without inventing a synthesized legal claim."""
    query = _clip(payload.get("query"), 240)
    as_of = _clip(payload.get("as_of_date"), 20)
    legal = list(payload.get("legal_hits") or [])
    technical = list(payload.get("technical_hits") or [])
    guidance = list(payload.get("guidance_hits") or [])

    lines = [
        "⚖️ VNLAW — KẾT QUẢ ĐÃ XÁC MINH",
        f"Câu hỏi: {query}",
        f"Thời điểm tra cứu: {as_of}",
    ]

    if not legal and not technical and not guidance:
        lines.extend(
            [
                "",
                "⚠️ VNLAW chưa có đủ bằng chứng đã xác minh để trả lời câu này.",
                "Bot không dùng dữ liệu khám phá/chưa xác minh để tự suy ra kết luận.",
                "",
                "Phạm vi trả lời chỉ là phần dữ liệu VNLAW đã xác minh, không đại diện toàn bộ pháp luật Việt Nam.",
            ]
        )
        return "\n".join(lines)[:limit]

    if legal:
        _append_with_budget(lines, ["", "📚 Văn bản pháp luật đã xác minh:"], limit)
        for hit in legal[:3]:
            chunk = hit.get("chunk") or {}
            force = str(chunk.get("force") or "UNKNOWN")
            force_label = _FORCE_LABELS.get(force, force)
            validity = (
                f"{chunk.get('valid_from') or '?'} → "
                f"{chunk.get('valid_to') or 'chưa có mốc kết thúc trong dữ liệu'}"
            )
            section = [
                "",
                f"• {chunk.get('breadcrumb') or chunk.get('document_number') or 'Không rõ điều khoản'}",
                f"  Trạng thái: {force_label}",
                f"  Khoảng hiệu lực dữ liệu: {validity}",
                f"  Nội dung: {_clip(chunk.get('text'))}",
            ]
            locator = _clip(chunk.get("source_locator"), 260)
            if locator:
                section.append(f"  Vị trí nguồn: {locator}")
            url = str(chunk.get("source_url") or "").strip()
            if url:
                section.append(f"  Nguồn chính thức: {url}")
            if not _append_with_budget(lines, section, limit - 260):
                break

    if technical:
        _append_with_budget(
            lines, ["", "🧰 Quy chuẩn kỹ thuật đã xác minh:"], limit - 220
        )
        for hit in technical[:2]:
            chunk = hit.get("chunk") or {}
            section = [
                "",
                f"• {chunk.get('breadcrumb') or chunk.get('document_number') or 'Quy chuẩn'}",
                f"  Nội dung: {_clip(chunk.get('text'))}",
            ]
            url = str(chunk.get("source_url") or "").strip()
            if url:
                section.append(f"  Nguồn chính thức: {url}")
            if not _append_with_budget(lines, section, limit - 220):
                break

    if guidance:
        _append_with_budget(
            lines,
            ["", "ℹ️ Hướng dẫn chính thức (không phải trạng thái pháp luật):"],
            limit - 220,
        )
        for hit in guidance[:2]:
            section = [
                "",
                f"• {hit.get('document_number') or 'Văn bản hướng dẫn'} — "
                f"{_clip(hit.get('title'), 180)}",
                f"  Trích bằng chứng: {_clip(hit.get('evidence_excerpt'), 420)}",
            ]
            url = str(hit.get("official_url") or "").strip()
            if url:
                section.append(f"  Nguồn chính thức: {url}")
            if not _append_with_budget(lines, section, limit - 220):
                break

    footer = [
        "",
        "⚠️ Chỉ phản ánh phạm vi dữ liệu VNLAW đã xác minh; bot không tự suy rộng sang phần chưa có evidence.",
    ]
    if len("\n".join(lines + footer)) <= limit:
        lines.extend(footer)
    else:
        text = "\n".join(lines)
        reserve = len("\n".join(footer)) + 2
        text = text[: max(0, limit - reserve)].rstrip()
        return text + "\n" + "\n".join(footer)
    return "\n".join(lines)


def answer_vnlaw_question(text: str, *, today: date | None = None) -> str:
    query, as_of = parse_question(text, today=today)
    payload = query_vnlaw(query, as_of)
    return format_vnlaw_result(payload)


HELP_TEXT = """⚖️ Tra cứu VNLAW nội bộ

Gửi thẳng câu hỏi, ví dụ:
Máy móc đã qua sử dụng nhập khẩu cần điều kiện gì?

Mặc định bot tra cứu theo ngày hiện tại.
Muốn tra cứu tại một ngày cụ thể:
/law 2025-01-01 <câu hỏi>

Bot chỉ hiển thị dữ liệu VNLAW đã xác minh và nguồn chính thức; không tự dùng dữ liệu khám phá để kết luận."""
