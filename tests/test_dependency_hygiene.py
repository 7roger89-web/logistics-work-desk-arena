"""Khóa các quyết định dependency hygiene (Phase C).

Hai bảo vệ nhỏ, không cần cài thêm gì:

1. ``streamlit-option-menu`` đã gỡ khỏi ``requirements.txt`` (thay bằng ``st.radio``
   native từ lâu; không còn import nào trong code) — không cho quay lại âm thầm.
2. Mọi direct dependency trong ``requirements.txt`` phải có mặt trong
   ``requirements.lock`` (nguồn cài cho CI/máy dev), bỏ qua dependency kèm marker
   môi trường không áp dụng (ví dụ ``tomli`` cho Python < 3.11).
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock"

_SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", "dist", "build"}


def _requirement_name(line: str) -> str:
    """Trích tên package chuẩn hóa từ một dòng requirements."""
    token = line.split(";", 1)[0].strip()  # bỏ env marker
    token = token.split("#", 1)[0].strip()
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "="):
        token = token.split(sep, 1)[0]
    token = token.split("[", 1)[0]  # bỏ extras, vd pymongo[srv]
    return token.strip().lower().replace("_", "-")


def _direct_requirements() -> list[str]:
    names: list[str] = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ";" in line:
            continue
        names.append(_requirement_name(line))
    return names


def test_streamlit_option_menu_not_declared():
    declared = {_requirement_name(line) for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#") and ";" not in line}
    assert "streamlit-option-menu" not in declared


def test_no_streamlit_option_menu_import_in_python_sources():
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("import streamlit_option_menu") or \
                    stripped.startswith("from streamlit_option_menu"):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == []


def test_lock_covers_every_direct_requirement():
    if not LOCK.is_file():
        pytest.skip("requirements.lock not present in this checkout")
    locked = {
        _requirement_name(line)
        for line in LOCK.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    missing = [name for name in _direct_requirements() if name not in locked]
    assert missing == [], f"direct deps thiếu trong lock: {missing}"
