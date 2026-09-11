"""LOGI_TARIFF_LOOKUP_01 — focused backend acceptance for /tra-cuu-thue.

Proves the bounded read-only adapter (``views.tariff_lookup``) and its
view-model/dispatcher wiring over the EXISTING canonical reader
(``core.utils.fast_search_tariff``) with a local governed-schema fixture
database. Business-truth invariants:

- exact / partial / keyword lookup behave as the existing reader does
- no-result and no-database states fail HONEST (never fabricated rows)
- UNKNOWN != ZERO: absent fields stay ``None``, never ``0`` / ``"0%"``
- values pass through verbatim (no float re-formatting or percent edits)
- provenance is preserved as what the backend truly knows (nothing
  authoritative) and never invented
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from views import logi_sandbox
from views import logi_view_model as vm
from views import tariff_lookup as tl


# ---------------------------------------------------------------------------
# Fixture: a small reference database with the CANONICAL sanitized schema
# (scripts/initialize_tariff_db.py) plus one richer variant with an extra
# duty column, to prove verbatim passthrough of unknown deployment columns.
# ---------------------------------------------------------------------------

CANONICAL_ROWS = [
    ("9401.61.00", "Ghế ngồi có lưng bằng gỗ", "Seats with wooden frames"),
    ("9403.20.10", "Bàn kim loại cho văn phòng", "Metal office tables"),
    ("4418.10.00", "Cửa sổ, cửa đi bằng gỗ", "Wooden windows and doors"),
]


def _write_db(path: Path, rows=CANONICAL_ROWS, extra_column: bool = False,
              rate: str | None = "10.5") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        if extra_column:
            conn.execute(
                'CREATE TABLE tariff_table ("Mã HS" TEXT, "Mô tả tiếng Việt" TEXT,'
                ' "Mô tả tiếng Anh" TEXT, "Thuế NK" TEXT)'
            )
            rows = [row + (rate,) for row in rows]
        else:
            conn.execute(
                'CREATE TABLE tariff_table ("Mã HS" TEXT, "Mô tả tiếng Việt" TEXT,'
                ' "Mô tả tiếng Anh" TEXT)'
            )
        placeholders = "(" + ", ".join(["?"] * (4 if extra_column else 3)) + ")"
        conn.executemany(f"INSERT INTO tariff_table VALUES {placeholders}", rows)
    return path


@pytest.fixture()
def tariff_db(tmp_path, monkeypatch):
    """Canonical 3-column fixture DB wired into BOTH import namespaces."""
    path = _write_db(tmp_path / "tariff" / "tariff.db")
    monkeypatch.setattr(tl, "TARIFF_DB_PATH", path)
    import core.utils
    monkeypatch.setattr(core.utils, "TARIFF_DB_PATH", path)
    return path


# ---------------------------------------------------------------------------
# Lookup behaviour
# ---------------------------------------------------------------------------

def test_exact_hs_lookup(tariff_db):
    result = tl.tariff_lookup_view("9403.20.10")
    assert result["searched"] is True
    assert result["count"] == 1
    row = result["rows"][0]
    assert row["hsCode"] == "9403.20.10"
    assert row["descriptionVi"] == "Bàn kim loại cho văn phòng"
    assert row["descriptionEn"] == "Metal office tables"


def test_partial_hs_lookup(tariff_db):
    result = tl.tariff_lookup_view("9401")
    assert result["searched"] is True
    assert result["count"] == 1
    assert result["rows"][0]["hsCode"] == "9401.61.00"


def test_keyword_lookup_vietnamese_and_english(tariff_db):
    vn = tl.tariff_lookup_view("ghế")
    assert vn["count"] == 1
    assert vn["rows"][0]["hsCode"] == "9401.61.00"
    en = tl.tariff_lookup_view("wooden")
    assert en["count"] == 2


def test_no_result_state_is_honest(tariff_db):
    result = tl.tariff_lookup_view("zzzz-khong-co")
    assert result["searched"] is True
    assert result["rows"] == [] and result["count"] == 0
    assert result["reason"] and "Không tìm thấy" in result["reason"]


def test_short_query_is_not_searched(tariff_db):
    result = tl.tariff_lookup_view("9")
    assert result["searched"] is False
    assert result["rows"] == []
    assert result["reason"]


def test_missing_database_fails_honest(tariff_db, monkeypatch):
    import core.utils
    monkeypatch.setattr(core.utils, "TARIFF_DB_PATH", tariff_db.parent / "absent.db")
    result = tl.tariff_lookup_view("9401")
    assert result["searched"] is True
    assert result["count"] == 0
    assert result["source"]["configured"] is False
    assert result["source"]["rows"] is None
    assert result["reason"] == "Chưa có dữ liệu biểu thuế để tra cứu."
    # A missing database must never masquerade as a clean no-match.
    assert "Chưa nạp" in result["source"]["note"]


def test_empty_database_fails_honest(tariff_db, tmp_path, monkeypatch):
    empty = tmp_path / "empty" / "tariff.db"
    empty.parent.mkdir(parents=True)
    with sqlite3.connect(str(empty)) as conn:
        conn.execute('CREATE TABLE tariff_table ("Mã HS" TEXT,'
                     ' "Mô tả tiếng Việt" TEXT, "Mô tả tiếng Anh" TEXT)')
    import core.utils
    monkeypatch.setattr(core.utils, "TARIFF_DB_PATH", empty)
    result = tl.tariff_lookup_view("9401")
    assert result["searched"] is True
    assert result["count"] == 0
    assert result["source"]["configured"] is True
    assert result["source"]["rows"] == 0
    assert result["reason"]


# ---------------------------------------------------------------------------
# Business-truth invariants
# ---------------------------------------------------------------------------

def test_unknown_fields_are_none_never_zero(tariff_db):
    result = tl.tariff_lookup_view("9401")
    row = result["rows"][0]
    # The canonical schema carries no duty/VAT/source/effective-date columns.
    assert "importDuty" not in row and "vat" not in row
    assert all(field["label"] not in {"Thuế NK", "VAT"} for field in row["fields"])
    assert result["provenance"]["source"] is None
    assert result["provenance"]["effectiveDate"] is None


def test_values_pass_through_verbatim(tariff_db, tmp_path, monkeypatch):
    rich = _write_db(tmp_path / "rich" / "tariff.db", extra_column=True)
    monkeypatch.setattr(tl, "TARIFF_DB_PATH", rich)
    import core.utils
    monkeypatch.setattr(core.utils, "TARIFF_DB_PATH", rich)
    result = tl.tariff_lookup_view("9403")
    row = result["rows"][0]
    extra = {field["label"]: field["value"] for field in row["fields"]}
    # Verbatim text "10.5" — not float 10.5, not "10.50%", not zero-coerced.
    assert extra["Thuế NK"] == "10.5"
    assert isinstance(extra["Thuế NK"], str)


def test_null_rate_stays_unknown_not_zero(tariff_db, tmp_path, monkeypatch):
    rich = _write_db(tmp_path / "null_rate" / "tariff.db",
                     rows=[CANONICAL_ROWS[0]], extra_column=True, rate=None)
    monkeypatch.setattr(tl, "TARIFF_DB_PATH", rich)
    import core.utils
    monkeypatch.setattr(core.utils, "TARIFF_DB_PATH", rich)
    row = tl.tariff_lookup_view("9401")["rows"][0]
    extra = {field["label"]: field["value"] for field in row["fields"]}
    assert extra["Thuế NK"] is None  # UNKNOWN != ZERO


def test_provenance_never_claims_official_authority(tariff_db):
    result = tl.tariff_lookup_view("9401")
    provenance = result["provenance"]
    assert provenance["authoritative"] is False
    assert provenance["note"]
    assert "chính thức" in provenance["note"]


def test_source_status_reports_governed_path(tariff_db):
    status = tl.tariff_source_status()
    assert status["configured"] is True
    assert status["rows"] == 3
    assert status["path"].endswith("tariff.db")


# ---------------------------------------------------------------------------
# View-model + dispatcher wiring (read-only surface)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    logi_sandbox.ensure_backend()
    yield
    logi_sandbox.reset_backend()


def test_view_model_exposes_tariff_slice(staging, tariff_db):
    import streamlit as st

    model = vm.build_view_model()
    assert model["tariff"]["searched"] is False  # no query yet — honest idle
    assert model["tariff"]["source"]["configured"] is True
    st.session_state[vm.TARIFF_QUERY_KEY] = "9401"
    model = vm.build_view_model()
    assert model["tariff"]["searched"] is True
    assert model["tariff"]["count"] == 1
    assert model["tariff"]["rows"][0]["hsCode"] == "9401.61.00"


def test_tariff_event_is_declared():
    assert "tariff_lookup" in vm.TARIFF_EVENTS
    assert "tariff_lookup" in vm.ALL_EVENTS


def test_tariff_event_records_query_and_is_replay_safe(staging):
    import streamlit as st

    trigger = {"tariff_lookup": {"seq": 7, "event": "tariff_lookup",
                                 "payload": {"query": "  9401  "}}}
    outcomes = vm.consume_tariff_triggers({"seq": 0}, trigger)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is True
    assert st.session_state[vm.TARIFF_QUERY_KEY] == "9401"
    # Replayed seq must be ignored (no double handling).
    assert vm.consume_tariff_triggers({"seq": 7}, trigger) == []
    # Empty query is rejected honestly.
    outcomes = vm.consume_tariff_triggers(
        {"seq": 8}, {"tariff_lookup": {"seq": 9, "event": "tariff_lookup",
                                       "payload": {"query": "   "}}})
    assert outcomes[0]["ok"] is False and outcomes[0]["error"]


def test_dispatch_tariff_lookup_triggers_single_rerun(staging, tariff_db, monkeypatch):
    import streamlit as st

    reruns = []
    monkeypatch.setattr(st, "rerun", lambda: reruns.append(1))
    trigger = {"tariff_lookup": {"seq": 11, "event": "tariff_lookup",
                                 "payload": {"query": "9401"}}}
    vm.dispatch(trigger)
    assert st.session_state[vm.TARIFF_QUERY_KEY] == "9401"
    assert len(reruns) == 1
    # The one-shot trigger is gone on the rerun → no further rerun, no loop.
    vm.dispatch({})
    assert len(reruns) == 1
