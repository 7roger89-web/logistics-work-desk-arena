"""Admin-managed NotebookLM registry for the Logistics shell.

One persisted app setting owns the shared NotebookLM list.  ADMIN may replace
that bounded list through one typed component event; all other roles are
read-only consumers.  The Google notebooks themselves stay external and are
opened in the reusable top-level browsing context used by the shell.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

NOTEBOOKLM_SETTING_ID = "notebooklm_registry"
NOTEBOOKLM_EVENTS = {"notebooklm_registry_save"}
MAX_NOTEBOOKS = 30
MAX_LABEL_LEN = 120

DEFAULT_ITEMS: list[dict[str, str]] = [
    {
        "label": "Tra cứu mã HS",
        "url": "https://notebook.google.com/notebook/f5c90bb9-9244-4027-a9ae-84f6ab023a09/preview",
    },
    {
        "label": "Bộ Thông Tin Truyền Thông",
        "url": "https://notebook.google.com/notebook/242b2eed-2a6d-4bb8-a0b2-c347d79e1047/preview",
    },
    {
        "label": "Bộ Y Tế",
        "url": "https://notebook.google.com/notebook/5a5d2a90-9881-49fc-9c65-e820b9497088/preview",
    },
    {
        "label": "Hóa Chất",
        "url": "https://notebook.google.com/notebook/50716c0b-7da6-4984-9f05-be0b19be4b95/preview",
    },
    {
        "label": "Bộ KHCN",
        "url": "https://notebook.google.com/notebook/6afaf293-e6d1-42f4-beaa-208f2d417f92/preview",
    },
]

_NOTEBOOK_URL_RE = re.compile(
    r"^https://notebook\.google\.com/notebook/"
    r"[0-9a-fA-F-]{36}/preview(?:[?#].*)?$"
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_items(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("Danh sách NotebookLM không hợp lệ.")
    if not raw:
        raise ValueError("Phải giữ ít nhất một NotebookLM.")
    if len(raw) > MAX_NOTEBOOKS:
        raise ValueError(f"Tối đa {MAX_NOTEBOOKS} NotebookLM.")

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"Notebook #{index} không hợp lệ.")
        label = _text(item.get("label"))
        url = _text(item.get("url"))
        if not label:
            raise ValueError(f"Notebook #{index} chưa có tên.")
        if len(label) > MAX_LABEL_LEN:
            raise ValueError(f"Tên notebook #{index} quá dài.")
        if not _NOTEBOOK_URL_RE.match(url):
            raise ValueError(
                f"URL notebook #{index} phải là link NotebookLM dạng /notebook/<id>/preview."
            )
        if url in seen:
            raise ValueError(f"Notebook #{index} bị trùng URL.")
        seen.add(url)
        out.append({"label": label, "url": url})
    return out


def registry_projection(*, db: Any = None) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import load_app_setting

    stored = load_app_setting(NOTEBOOKLM_SETTING_ID, db=db)
    source = "DEFAULTS"
    items = [dict(item) for item in DEFAULT_ITEMS]
    if isinstance(stored, Mapping):
        value = stored.get("value")
        if isinstance(value, Mapping):
            try:
                items = _normalize_items(value.get("items"))
                source = "APP_SETTINGS"
            except ValueError:
                # Fail safe: a malformed persisted setting must not blank the launcher.
                items = [dict(item) for item in DEFAULT_ITEMS]
                source = "DEFAULTS_INVALID_STORED"

    return {
        "items": items,
        "canManage": bool(can_operate_business("*")),
        "source": source,
        "maxItems": MAX_NOTEBOOKS,
    }


def _result(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
    return {
        "event": "notebooklm_registry_save",
        "id": NOTEBOOKLM_SETTING_ID,
        "ok": ok,
        "error": error,
        **extra,
    }


def _handle_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_app_setting

    request_id = _text(payload.get("requestId"))
    if not can_operate_business("*"):
        return _result(False, "RBAC: chỉ Admin mới được quản lý NotebookLM.", requestId=request_id)

    try:
        items = _normalize_items(payload.get("items"))
    except ValueError as exc:
        return _result(False, str(exc), requestId=request_id)

    if not save_app_setting(
        NOTEBOOKLM_SETTING_ID,
        {"items": items},
    ):
        return _result(
            False,
            get_last_db_error() or "Không lưu được danh sách NotebookLM.",
            requestId=request_id,
        )

    return _result(
        True,
        requestId=request_id,
        readback=registry_projection(),
        persisted={"count": len(items)},
    )


def consume_notebooklm_triggers(session: dict[str, Any], result: Any) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(NOTEBOOKLM_EVENTS):
        envelope = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(envelope, dict):
            continue
        seq = envelope.get("seq")
        if not isinstance(seq, int) or seq <= int(session.get("seq") or 0):
            continue
        session["seq"] = seq
        payload = envelope.get("payload")
        if not isinstance(payload, Mapping):
            outcomes.append(_result(False, "Payload không hợp lệ."))
            continue
        try:
            outcomes.append(_handle_save(payload))
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                _result(
                    False,
                    f"{type(exc).__name__}: {exc}",
                    requestId=_text(payload.get("requestId")),
                )
            )
    return outcomes
