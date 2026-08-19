"""
LOG-LG05 tests: Excel Round-Trip (52 columns) & GNT Generation (C1-02/NS).

Covers:
- 52-column header contract (exact spelling/order)
- Round-trip: export → parse → re-export (headers and data preserved)
- UNKNOWN vs ZERO semantics
- Dedup detection
- GNT prerequisites check
- GNT workbook structure (2 sheets, auto-fill, amount in words)
"""

import io
import datetime
import pytest
import pandas as pd

from unittest.mock import patch, MagicMock


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def sample_shipment():
    """A shipment with import/customs data for GNT."""
    return {
        "id": "S-LG05-001",
        "customer_id": "CUS-1",
        "customer": "CÔNG TY TNHH A",
        "created_by": "admin",
        "created_at": "2026-08-01",
        "status": "import",
        "data": {
            "1.1": {"order_date": "2026-08-01", "executor": "admin"},
            "2.4": {
                "tk_no": "12345678",
                "tk_date": "15/08/2026",
                "import_duty_amount": 5000000,
                "import_vat_amount": 800000,
            },
            "3.4": {"details": [
                {"name": "Thủ tục hải quan", "unit": "Lô", "qty": 1, "cost": 2000000, "price": 3000000},
            ]},
        },
    }


@pytest.fixture
def sample_shipment_no_gnt():
    """A shipment without import/customs data — GNT should fail."""
    return {
        "id": "S-LG05-002",
        "customer_id": "CUS-2",
        "customer": "CÔNG TY TNHH B",
        "created_by": "admin",
        "created_at": "2026-08-01",
        "status": "new",
        "data": {
            "1.1": {"order_date": "2026-08-01", "executor": "admin"},
        },
    }


@pytest.fixture
def sample_shipment_partial_gnt():
    """A shipment with partial GNT data (missing tk_date)."""
    return {
        "id": "S-LG05-003",
        "customer_id": "CUS-3",
        "customer": "CÔNG TY TNHH C",
        "created_by": "admin",
        "created_at": "2026-08-01",
        "status": "import",
        "data": {
            "1.1": {"order_date": "2026-08-01", "executor": "admin"},
            "2.4": {
                "tk_no": "87654321",
                "import_duty_amount": 1000000,
                "import_vat_amount": 200000,
            },
        },
    }


@pytest.fixture
def owner_excel_bytes():
    """Read the Owner's actual Excel file for round-trip testing."""
    path = "/home/ubuntu/upload/danhsachdonhang-.xlsx"
    with open(path, "rb") as f:
        return f.read()


# ============================================================
# 52-COLUMN CONTRACT
# ============================================================

class Test52ColumnContract:
    """Verify the exact 52-column header contract."""

    def test_headers_count(self):
        from core.excel_roundtrip import HEADERS_52
        assert len(HEADERS_52) == 52

    def test_headers_first_four(self):
        from core.excel_roundtrip import HEADERS_52
        assert HEADERS_52[0] == "Ngày đặt hàng"
        assert HEADERS_52[1] == "Ngày tạo"
        assert HEADERS_52[2] == "Mã ĐH"
        assert HEADERS_52[3] == "Người thực hiện"

    def test_headers_last_three(self):
        from core.excel_roundtrip import HEADERS_52
        assert HEADERS_52[49] == "REFUN"
        assert HEADERS_52[50] == "HOA HỒNG KH GỬI"
        assert HEADERS_52[51] == "CẤP ĐỘ RỦI RO"


# ============================================================
# ROUND-TRIP: PARSE → GROUP → VALIDATE
# ============================================================

class TestExcelRoundTrip:
    """Test import flow: parse, group, validate."""

    def test_parse_owner_file_no_errors(self, owner_excel_bytes):
        from core.excel_roundtrip import parse_excel_bytes
        result = parse_excel_bytes(owner_excel_bytes)
        assert len(result.errors) == 0
        assert result.row_count > 0

    def test_group_owner_file(self, owner_excel_bytes):
        from core.excel_roundtrip import parse_excel_bytes, group_rows
        result = parse_excel_bytes(owner_excel_bytes)
        groups = group_rows(result.groups)
        assert len(groups) >= 10  # Owner's file has ~14 shipments

    def test_group_details_match(self, owner_excel_bytes):
        from core.excel_roundtrip import parse_excel_bytes, group_rows
        result = parse_excel_bytes(owner_excel_bytes)
        groups = group_rows(result.groups)
        total_details = sum(len(g.details) for g in groups)
        assert total_details >= 30  # Owner's file has ~39 service rows

    def test_validate_new_shipments(self, owner_excel_bytes):
        from core.excel_roundtrip import parse_excel_bytes, group_rows, validate_groups
        result = parse_excel_bytes(owner_excel_bytes)
        groups = group_rows(result.groups)
        validated = validate_groups(groups, set())
        assert validated.is_valid
        assert all(g.status == "new" for g in validated.groups)

    def test_validate_existing_shipments(self, owner_excel_bytes):
        from core.excel_roundtrip import parse_excel_bytes, group_rows, validate_groups
        result = parse_excel_bytes(owner_excel_bytes)
        groups = group_rows(result.groups)
        # First group's ID is already "existing"
        existing_ids = {groups[0].shipment_id}
        validated = validate_groups(groups, existing_ids)
        assert validated.groups[0].status == "existing"

    def test_validate_duplicate_ids(self):
        from core.excel_roundtrip import ImportRow, group_rows, validate_groups
        row1 = ImportRow(1, {"shipment_id": "DUP-001", "customer_name": "A"})
        row2 = ImportRow(2, {"shipment_id": "DUP-001", "customer_name": "B"})
        groups = group_rows([row1, row2])
        validated = validate_groups(groups, set())
        # Duplicate detection generates a warning
        assert any("Trùng Mã ĐH" in w for w in validated.warnings)

    def test_unknown_vs_zero_semantics(self):
        """Missing values must remain None, never default to 0 or ''."""
        from core.excel_roundtrip import ImportRow
        row = ImportRow(1, {"shipment_id": "X", "phone": None, "email": None})
        assert row.get("phone") is None
        assert row.get("email") is None
        assert row.get("shipment_id") == "X"


# ============================================================
# EXPORT → RE-IMPORT ROUND-TRIP
# ============================================================

class TestExcelExportRoundTrip:
    """Test export then re-import."""

    def test_export_headers_match(self):
        from core.excel_roundtrip import HEADERS_52, export_to_excel_bytes
        ships = [{"id": "RT-001", "data": {}}]
        xlsx_bytes = export_to_excel_bytes(ships)
        df = pd.read_excel(io.BytesIO(xlsx_bytes), engine="calamine", header=0)
        assert list(df.columns) == HEADERS_52

    def test_export_roundtrip_preserves_data(self, owner_excel_bytes):
        from core.excel_roundtrip import (
            parse_excel_bytes, group_rows, validate_groups,
            group_to_shipment_doc, export_to_excel_bytes, HEADERS_52,
        )
        # Parse original
        result = parse_excel_bytes(owner_excel_bytes)
        groups = group_rows(result.groups)
        validated = validate_groups(groups, set())

        # Export
        docs = [group_to_shipment_doc(g) for g in validated.groups[:5]]
        xlsx_bytes = export_to_excel_bytes(docs)

        # Re-import
        df = pd.read_excel(io.BytesIO(xlsx_bytes), engine="calamine", header=0)
        assert list(df.columns) == HEADERS_52
        assert len(df) >= 5  # At least one row per shipment

        # First column should be shipment ID
        ids = df["Mã ĐH"].dropna().tolist()
        expected_ids = [g.shipment_id for g in validated.groups[:5]]
        for eid in expected_ids:
            assert eid in ids


# ============================================================
# GNT PREREQUISITES
# ============================================================

class TestGntPrerequisites:
    """Test GNT prerequisite checks."""

    def test_gnt_ready(self, sample_shipment):
        from core.gnt_builder import check_gnt_prerequisites
        prereq = check_gnt_prerequisites(sample_shipment)
        assert prereq["ready"] is True
        assert len(prereq["missing"]) == 0

    def test_gnt_not_ready_no_data(self, sample_shipment_no_gnt):
        from core.gnt_builder import check_gnt_prerequisites
        prereq = check_gnt_prerequisites(sample_shipment_no_gnt)
        assert prereq["ready"] is False
        assert len(prereq["missing"]) > 0

    def test_gnt_not_ready_missing_date(self, sample_shipment_partial_gnt):
        from core.gnt_builder import check_gnt_prerequisites
        prereq = check_gnt_prerequisites(sample_shipment_partial_gnt)
        assert prereq["ready"] is False
        assert any("Ngày tờ khai" in m for m in prereq["missing"])

    def test_gnt_not_ready_zero_amount(self):
        from core.gnt_builder import check_gnt_prerequisites
        ship = {
            "id": "S-ZERO",
            "data": {"2.4": {
                "tk_no": "111",
                "tk_date": "01/01/2026",
                "import_duty_amount": 0,  # Zero = not ready
                "import_vat_amount": 0,
            }},
        }
        prereq = check_gnt_prerequisites(ship)
        assert prereq["ready"] is False
        assert any("Thuế" in m for m in prereq["missing"])

    def test_gnt_data_fields(self, sample_shipment):
        from core.gnt_builder import check_gnt_prerequisites
        prereq = check_gnt_prerequisites(sample_shipment)
        data = prereq["data"]
        assert data["tk_no"] == "12345678"
        assert data["tk_date"] == "15/08/2026"
        assert data["import_duty_amount"] == 5000000
        assert data["import_vat_amount"] == 800000


# ============================================================
# GNT WORKBOOK GENERATION
# ============================================================

class TestGntWorkbook:
    """Test GNT workbook generation."""

    def test_workbook_two_sheets(self, sample_shipment):
        from core.gnt_builder import check_gnt_prerequisites, build_gnt_workbook
        prereq = check_gnt_prerequisites(sample_shipment)
        wb_bytes = build_gnt_workbook(prereq["data"])
        assert len(wb_bytes) > 0

        df1 = pd.read_excel(io.BytesIO(wb_bytes), sheet_name="NHẬP THÔNG TIN", engine="calamine")
        df2 = pd.read_excel(io.BytesIO(wb_bytes), sheet_name="GIẤY NỘP THUẾ", engine="calamine")
        assert df1.shape[0] > 0
        assert df2.shape[0] > 0

    def test_workbook_auto_filled(self, sample_shipment):
        from core.gnt_builder import check_gnt_prerequisites, build_gnt_workbook
        prereq = check_gnt_prerequisites(sample_shipment)
        wb_bytes = build_gnt_workbook(prereq["data"])

        df1 = pd.read_excel(io.BytesIO(wb_bytes), sheet_name="NHẬP THÔNG TIN", engine="calamine")
        # Check that TK number and dates are auto-filled
        found_tk_no = any(
            str(v) == "12345678" for v in df1.iloc[:, 1].dropna().tolist()
        )
        assert found_tk_no

    def test_total_amount_in_words(self):
        from core.gnt_builder import doc_so_thanh_chu_vi
        result = doc_so_thanh_chu_vi(5800000)
        assert "Năm triệu tám trăm nghìn đồng" in result

    def test_total_amount_zero(self):
        from core.gnt_builder import doc_so_thanh_chu_vi
        result = doc_so_thanh_chu_vi(0)
        assert "đồng" in result

    def test_workbook_no_exception_empty_data(self):
        """Should not crash even with minimal data."""
        from core.gnt_builder import build_gnt_workbook
        data = {"tk_no": "", "tk_date": "", "import_duty_amount": 0, "import_vat_amount": 0}
        wb_bytes = build_gnt_workbook(data)
        assert len(wb_bytes) > 0


# ============================================================
# DASHBOARD UI INTEGRATION
# ============================================================

class TestLg05DashboardUI:
    """Test that LG05 UI elements exist in dashboard."""

    def test_import_function_exists(self):
        from views.dashboard import _render_excel_import_ui
        assert callable(_render_excel_import_ui)

    def test_export_function_exists(self):
        from views.dashboard import _handle_excel_export
        assert callable(_handle_excel_export)

    def test_gnt_function_exists(self):
        from views.dashboard import _render_gnt_dialog
        assert callable(_render_gnt_dialog)
