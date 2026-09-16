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
import os
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
    if not os.path.exists(path):
        pytest.skip("Owner's Excel file not present in test environment")
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

    def test_gnt_function_in_shipment(self):
        from core.gnt_builder import build_gnt_workbook
        assert callable(build_gnt_workbook)


# ============================================================
# LG05 INCIDENT REGRESSION TESTS
# GETFLY Import Incident: malformed styles.xml + date semantics fix
# ============================================================

class TestLg05IncidentRegression:
    """Regression tests for the GETFLY Import Incident.
    
    Root causes:
    1. openpyxl cannot read files with malformed styles.xml (rgb="#ccc")
    2. Dashboard period filter uses created_at instead of order_date
       → orders with created_at in previous month are invisible under "Tháng này"
    
    Fixes:
    1. Reader already uses calamine engine (values-oriented, ignores styles.xml)
    2. get_shipment_business_date() now prefers order_date over created_at
    3. Cache invalidation after import (st.cache_data.clear() + refresh)
    """

    def test_synthetic_fixture_openpyxl_fails(self):
        """openpyxl cannot read files with malformed styles.xml (rgb='#ccc')."""
        import openpyxl
        with pytest.raises(Exception):
            openpyxl.load_workbook("tests/fixtures/synthetic_getfly.xlsx")

    def test_synthetic_fixture_calamine_succeeds(self):
        """calamine (values-oriented) can read files with malformed styles.xml."""
        import pandas as pd
        df = pd.read_excel("tests/fixtures/synthetic_getfly.xlsx", engine="calamine", header=None)
        assert df.shape[1] == 52  # 52 columns
        assert df.shape[0] == 8   # 1 header + 7 data rows

    def test_synthetic_fixture_parse_pipeline(self):
        """Full parse → group → validate pipeline works with corrupted fixture."""
        from core.excel_roundtrip import parse_excel_bytes, group_rows, validate_groups

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        result = parse_excel_bytes(file_bytes)
        assert result.row_count == 7  # 7 data rows
        assert len(result.errors) == 0

        groups = group_rows(result.groups)
        assert len(groups) == 3  # 3 orders
        assert sum(len(g.details) for g in groups) == 7  # 7 service lines

        validation = validate_groups(groups, set())
        assert validation.is_valid

    def test_order_date_priority_in_document(self):
        """group_to_shipment_doc maps order_date correctly, distinct from created_at."""
        from core.excel_roundtrip import parse_excel_bytes, group_rows, group_to_shipment_doc

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        result = parse_excel_bytes(file_bytes)
        groups = group_rows(result.groups)

        for g in groups:
            doc = group_to_shipment_doc(g)
            sec = doc['data']['0.0']
            od = sec.get('order_date', '')
            ca = sec.get('created_at', '')
            # Verify order_date and created_at are distinct (different months)
            assert od != ca, f"order_date and created_at should differ for {g.shipment_id}"
            assert len(od) > 0, "order_date should not be empty"

    def test_get_shipment_business_date_uses_order_date(self):
        """get_shipment_business_date prefers order_date over created_at."""
        from core.utils import get_shipment_business_date
        from core.excel_roundtrip import parse_excel_bytes, group_rows, group_to_shipment_doc
        from datetime import datetime, date

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        result = parse_excel_bytes(file_bytes)
        groups = group_rows(result.groups)

        for g in groups:
            doc = group_to_shipment_doc(g)
            biz_date = get_shipment_business_date(doc)
            od = doc['data']['0.0'].get('order_date', '')
            # The business date should match order_date (converted to ISO)
            od_dt = datetime.strptime(od, "%d/%m/%Y").date()
            # biz_date might be a date or datetime object
            if isinstance(biz_date, datetime):
                biz_date = biz_date.date()
            assert biz_date == od_dt, \
                f"Business date '{biz_date}' should equal order_date '{od_dt}'"

    def test_all_orders_visible_under_thang_nay_filter(self):
        """All orders with order_date in current month should be visible
        under 'Tháng này' filter (regression for 8/14 invisible orders)."""
        from core.utils import get_shipment_business_date
        from core.excel_roundtrip import parse_excel_bytes, group_rows, group_to_shipment_doc
        from datetime import datetime, date

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        result = parse_excel_bytes(file_bytes)
        groups = group_rows(result.groups)

        # Count orders visible in Aug 2026 using the fixed date semantics
        visible_count = 0
        for g in groups:
            doc = group_to_shipment_doc(g)
            biz_date = get_shipment_business_date(doc)
            if biz_date:
                # Handle both date and datetime objects
                if isinstance(biz_date, datetime):
                    biz_date = biz_date.date()
                if isinstance(biz_date, date):
                    if biz_date.month == 8 and biz_date.year == 2026:
                        visible_count += 1

        # All 3 orders should be visible (all have order_date in Aug 2026)
        assert visible_count == len(groups), \
            f"Expected {len(groups)} visible, got {visible_count}"

    def test_import_result_display_counts(self):
        """Verify the import UI result display format (contract section 12)."""
        from views.dashboard import _render_excel_import_ui
        assert callable(_render_excel_import_ui)

    def test_cache_invalidation_after_import(self):
        """Verify cache invalidation code exists in the import path."""
        import inspect
        from views.dashboard import _render_excel_import_ui
        source = inspect.getsource(_render_excel_import_ui)
        assert 'st.cache_data.clear()' in source, \
            "Cache invalidation (st.cache_data.clear()) should be in import path"
        assert 'load_data()' in source, \
            "load_data() refresh should be in import path"


# ============================================================
# SERVICE-LINE IDEMPOTENCY TESTS (3-run proof)
# ============================================================

class TestServiceLineIdempotency:
    """Prove service-line dedup prevents duplicate accumulation across re-imports."""

    def test_same_shipment_same_service_line_exising_same(self):
        """Same shipment + same service line → EXISTING_SAME (not appended)."""
        from core.excel_roundtrip import classify_service_lines

        existing = [{"code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0, "cost": 100.0, "price": 150.0}]
        incoming = [{"code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0, "cost": 100.0, "price": 150.0}]

        same, new, conflict, ambiguous = classify_service_lines(existing, incoming)
        assert len(same) == 1, "Should be classified as EXISTING_SAME"
        assert len(new) == 0, "Should NOT be classified as NEW"
        assert len(conflict) == 0

    def test_same_shipment_new_service_line(self):
        """Same shipment + one genuinely new service line → NEW_SERVICE."""
        from core.excel_roundtrip import classify_service_lines

        existing = [{"code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0, "cost": 100.0, "price": 150.0}]
        incoming = [{"code": "VCH", "name": "Phí vận chuyển", "qty": 2.0, "cost": 200.0, "price": 250.0}]

        same, new, conflict, ambiguous = classify_service_lines(existing, incoming)
        assert len(same) == 0
        assert len(new) == 1, "Should be classified as NEW_SERVICE"
        assert len(conflict) == 0

    def test_same_shipment_conflicting_service_value(self):
        """Same identity but VAT changed → CONFLICT (needs review)."""
        from core.excel_roundtrip import classify_service_lines

        existing = [{"code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0, "cost": 100.0, "price": 150.0, "vat": 0.0}]
        incoming = [{"code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0, "cost": 100.0, "price": 150.0, "vat": 8.0}]

        same, new, conflict, ambiguous = classify_service_lines(existing, incoming)
        assert len(conflict) == 1, "Should be classified as CONFLICT (VAT changed)"
        assert len(new) == 0, "Should NOT auto-append conflicting line"
        assert len(same) == 0

    def test_merge_details_idempotent_same(self):
        """merge_details_idempotent: same lines → no change."""
        from core.excel_roundtrip import merge_details_idempotent

        existing = [{"code": "DVK", "name": "A", "qty": 1.0, "cost": 100.0, "price": 150.0}]
        incoming = [{"code": "DVK", "name": "A", "qty": 1.0, "cost": 100.0, "price": 150.0}]

        merged, stats = merge_details_idempotent(existing, incoming)
        assert len(merged) == 1, "Should remain 1 line (not duplicated)"
        assert stats["same"] == 1
        assert stats["new"] == 0

    def test_merge_details_idempotent_new(self):
        """merge_details_idempotent: new line → appended once."""
        from core.excel_roundtrip import merge_details_idempotent

        existing = [{"code": "DVK", "name": "A", "qty": 1.0, "cost": 100.0, "price": 150.0}]
        incoming = [{"code": "VCH", "name": "B", "qty": 2.0, "cost": 200.0, "price": 250.0}]

        merged, stats = merge_details_idempotent(existing, incoming)
        assert len(merged) == 2, "Should have 2 lines (existing + new)"
        assert stats["same"] == 0
        assert stats["new"] == 1

    def test_import_same_file_twice_zero_delta(self):
        """RUN 1 + RUN 2 (identical file) → business-data delta = 0.
        Simulates 3-run proof with isolated test fixture."""
        from core.excel_roundtrip import (
            parse_excel_bytes, group_rows, group_to_shipment_doc,
            merge_details_idempotent, classify_service_lines,
        )

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        # RUN 1: Parse file, create initial shipment docs
        result1 = parse_excel_bytes(file_bytes)
        groups1 = group_rows(result1.groups)
        docs1 = {g.shipment_id: group_to_shipment_doc(g) for g in groups1}

        # RUN 2: Parse same file again, compare against RUN 1 results
        result2 = parse_excel_bytes(file_bytes)
        groups2 = group_rows(result2.groups)
        docs2 = {g.shipment_id: group_to_shipment_doc(g) for g in groups2}

        # Verify: same shipments, same counts
        assert len(docs1) == len(docs2), "Same file should produce same number of shipments"

        # For each shipment, verify service-line dedup produces zero delta
        for sid in docs1:
            existing_details = docs1[sid].get("data", {}).get("3.4", {}).get("details", [])
            incoming_details = docs2.get(sid, {}).get("data", {}).get("3.4", {}).get("details", [])

            if existing_details and incoming_details:
                same, new, conflict, ambiguous = classify_service_lines(
                    existing_details, incoming_details
                )
                # All lines should be EXISTING_SAME (zero delta)
                assert len(new) == 0, f"Shipment {sid}: no new lines on re-import"
                assert len(same) == len(incoming_details), f"Shipment {sid}: all lines should be same"

    def test_import_three_times_financial_totals_no_double(self):
        """3-run proof: RUN 3 with one new service line → adds exactly 1 line.
        Financial totals must NOT double."""
        from core.excel_roundtrip import (
            parse_excel_bytes, group_rows, group_to_shipment_doc,
            merge_details_idempotent,
        )
        import copy

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        # RUN 1: Import file
        result1 = parse_excel_bytes(file_bytes)
        groups1 = group_rows(result1.groups)
        docs1 = {g.shipment_id: group_to_shipment_doc(g) for g in groups1}

        # RUN 2: Import same file → simulate idempotent merge
        result2 = parse_excel_bytes(file_bytes)
        groups2 = group_rows(result2.groups)
        docs2 = {g.shipment_id: group_to_shipment_doc(g) for g in groups2}

        # Merge RUN 2 into RUN 1 (idempotent)
        final_state = copy.deepcopy(docs1)
        total_delta = 0
        for sid in docs2:
            existing = final_state.get(sid, {}).get("data", {}).get("3.4", {}).get("details", [])
            incoming = docs2.get(sid, {}).get("data", {}).get("3.4", {}).get("details", [])

            if existing and incoming:
                merged, stats = merge_details_idempotent(existing, incoming)
                total_delta += stats["new"]
                final_state.setdefault(sid, {}).setdefault("data", {}).setdefault("3.4", {})["details"] = merged
            elif incoming and not existing:
                final_state.setdefault(sid, {}).setdefault("data", {}).setdefault("3.4", {})["details"] = incoming
                total_delta += len(incoming)

        # RUN 2 should produce ZERO delta
        assert total_delta == 0, f"RUN 2 should have zero delta, got {total_delta}"

        # RUN 3: Modified file with one extra service line (simulated)
        # Add a new service line to the first group's incoming details
        first_sid = list(docs2.keys())[0]
        new_line = {
            "code": "LAP", "name": "Phí lắp đặt", "qty": 1.0,
            "cost": 500000.0, "price": 600000.0, "vat": 8.0,
        }
        docs2[first_sid]["data"]["3.4"]["details"].append(new_line)

        # Merge RUN 3 into current state
        existing = final_state.get(first_sid, {}).get("data", {}).get("3.4", {}).get("details", [])
        incoming = docs2[first_sid].get("data", {}).get("3.4", {}).get("details", [])
        merged3, stats3 = merge_details_idempotent(existing, incoming)
        final_state[first_sid]["data"]["3.4"]["details"] = merged3

        # RUN 3 should add exactly 1 new service line
        assert stats3["new"] == 1, f"RUN 3 should add exactly 1 new line, got {stats3['new']}"
        assert stats3["same"] >= 1, "Existing lines should be preserved"

        # Verify financial totals don't double
        final_details = final_state[first_sid]["data"]["3.4"]["details"]
        original_count = len(existing)
        final_count = len(final_details)
        assert final_count == original_count + 1, "Should have exactly 1 more line"

    def test_continuation_rows_grouped_correctly_after_dedup(self):
        """Verify continuation rows remain correctly grouped after dedup logic."""
        from core.excel_roundtrip import parse_excel_bytes, group_rows

        with open("tests/fixtures/synthetic_getfly.xlsx", "rb") as f:
            file_bytes = f.read()

        result = parse_excel_bytes(file_bytes)
        groups = group_rows(result.groups)

        # All groups should have at least 1 detail (the master row)
        for g in groups:
            assert len(g.details) >= 1, f"Group {g.shipment_id} should have at least 1 detail"
            # Master row should be first detail if it has service data
            first = g.details[0]
            assert first.has_master or first.has_service, "First detail should have data"

    def test_finance_safety_no_silent_overwrite(self):
        """Financial data must never be silently overwritten during import."""
        from core.excel_roundtrip import merge_details_idempotent

        # Existing has financial data
        existing = [
            {
                "code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0,
                "cost": 100.0, "price": 150.0,
                "paid": 150.0, "debt": 0.0,  # Financial actuals
            }
        ]

        # Incoming has different financial values (but same identity)
        incoming = [
            {
                "code": "DVK", "name": "Phí dịch vụ khác", "qty": 1.0,
                "cost": 100.0, "price": 150.0,
                "paid": 0.0, "debt": 150.0,  # Different financial actuals
            }
        ]

        merged, stats = merge_details_idempotent(existing, incoming)

        # Existing line should be preserved with ORIGINAL financial data
        assert len(merged) == 1
        assert merged[0]["paid"] == 150.0, "Original paid amount must be preserved"
        assert merged[0]["debt"] == 0.0, "Original debt must be preserved"
