"""Generic XLSX upload and separate editable-workbook draft round trip."""
from __future__ import annotations

import base64
import hashlib
from io import BytesIO

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment

from core.gridfs_client import GridFSAttachmentStore
from views import logi_c1, logi_sandbox

CUSTOMER_ID = "CUST-WORKBOOK-EDIT-V1"
FILE_NAME = "freight-rate-workbook.xlsx"


def freight_workbook() -> bytes:
    wb = Workbook()
    rates = wb.active
    rates.title = "Ocean Freight"
    rates.merge_cells("B2:D2")
    rates["B2"] = "FREIGHT QUOTATION · NINGBO TO HAI PHONG"
    rates["B3"], rates["C3"], rates["D3"] = "Route", "Equipment", "Rate USD"
    rates["B4"], rates["C4"], rates["D4"] = "Ningbo → Hai Phong", "40HQ", 1750
    rates["B5"], rates["C5"], rates["D5"] = "Valid until", "2026-12-31", "=D4*1.05"
    rates["D4"].number_format = '"USD "#,##0.00'
    services = wb.create_sheet("Port charges")
    services["C4"] = "Terminal handling"
    services["D4"] = 210
    services["E4"] = "USD"
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def mixed_customer_workbook() -> bytes:
    wb = Workbook()
    summary = wb.active
    summary.title = "客户说明"
    summary.merge_cells("B2:F2")
    summary["B2"] = "Customer workbook · mixed estimates"
    summary["B4"], summary["C4"] = "Route", "Ningbo → Hanoi"
    summary["B5"], summary["C5"] = "Terms", "Rates subject to confirmation"
    goods = wb.create_sheet("Customer goods tab")
    goods["C6"], goods["D6"], goods["E6"], goods["F6"], goods["G6"] = "SKU", "Product", "Qty", "Currency", "Price"
    goods["C7"], goods["D7"], goods["E7"], goods["F7"], goods["G7"] = "BX-01", "Cabinet", 12, "CNY", 870
    goods["G7"].comment = Comment("Confirm if this is customer sale price", "supplier")
    local = wb.create_sheet("Local charges")
    local["B4"], local["C4"], local["D4"] = "Charge", "Amount", "Currency"
    local["B5"], local["C5"], local["D5"] = "Destination service", 95, "USD"
    local["E5"] = "=C5*1.08"
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


@pytest.fixture
def staging():
    import streamlit as st
    from core.database import get_db

    had_user = "current_user" in st.session_state
    previous_user = st.session_state.get("current_user")
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    db = get_db()
    db.customers.insert_one({"id": CUSTOMER_ID, "name": "Freight customer"})
    try:
        yield db
    finally:
        logi_sandbox.reset_backend()
        if had_user:
            st.session_state["current_user"] = previous_user
        else:
            st.session_state.pop("current_user", None)


def dispatch(event: str, payload: dict):
    outcomes = logi_c1.consume_c1_triggers(
        {"seq": 0}, {event: {"seq": 1, "payload": {"requestId": "workbook-test", **payload}}}
    )
    assert len(outcomes) == 1
    return outcomes[0]


def import_generic(data: bytes):
    return dispatch("quote_import_excel", {
        "customerId": CUSTOMER_ID, "fileName": FILE_NAME,
        "base64": base64.b64encode(data).decode("ascii"),
    })


def test_non_template_workbook_without_quote_columns_uploads_views_edits_saves_and_reopens(staging):
    original = freight_workbook()
    original_sha = hashlib.sha256(original).hexdigest()
    source_book = load_workbook(BytesIO(original), data_only=False, read_only=True)
    source_cells = [str(value) for row in source_book["Ocean Freight"].iter_rows(values_only=True) for value in row if value is not None]
    source_book.close()
    assert not any(value.strip().casefold() in {"kích thước", "size", "số lượng", "quantity", "đơn giá rmb", "price rmb"}
                   for value in source_cells)
    imported = import_generic(original)
    assert imported["ok"], imported
    assert imported["readback"]["workbook_only"] is True
    assert imported["readback"]["workbook_message"] == (
        "Đã nhập Excel thành công. Chưa xác định được bảng để tính giá tự động; "
        "bạn có thể xem, sửa và chọn các cột cần dùng."
    )
    source = imported["readback"]["source"]
    assert source["sheet_names"] == ["Ocean Freight", "Port charges"]
    assert source["sha256"] == original_sha
    listed = dispatch("quote_workbook_sources_list", {"customerId": CUSTOMER_ID})
    assert listed["ok"], listed
    assert any(item["sha256"] == original_sha for item in listed["readback"]["sources"])

    store = GridFSAttachmentStore(staging)
    assert store.download_file(source["storage_file_id"]) == original
    page = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight",
    })
    assert page["ok"], page
    assert page["readback"]["overview"]["sheet_names"] == ["Ocean Freight", "Port charges"]
    cells = {(cell["r"], cell["c"]): cell for cell in page["readback"]["page"]["cells"]}
    assert cells[(2, 2)]["value"] == "FREIGHT QUOTATION · NINGBO TO HAI PHONG"
    assert cells[(4, 4)]["value"] == 1750
    assert cells[(5, 4)]["kind"] == "formula" and cells[(5, 4)]["f"] == "=D4*1.05"
    assert cells[(5, 4)]["unknown"] is True

    saved = dispatch("quote_workbook_draft_save", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight", "expectedVersion": 0,
        "edits": [
            {"sheet": "Ocean Freight", "r": 4, "c": 2, "type": "text", "value": "Ningbo → Hai Phong · checked"},
            {"sheet": "Ocean Freight", "r": 4, "c": 4, "type": "number", "value": "1900"},
        ],
    })
    assert saved["ok"], saved
    assert saved["readback"]["draft"]["saved"] is True
    assert saved["readback"]["draft"]["version"] == 1
    after_save = {(cell["r"], cell["c"]): cell for cell in saved["readback"]["page"]["cells"]}
    assert after_save[(4, 2)]["value"] == "Ningbo → Hai Phong · checked"
    assert after_save[(4, 4)]["value"] == 1900
    assert after_save[(5, 4)]["kind"] == "formula" and after_save[(5, 4)]["f"] == "=D4*1.05"
    assert store.download_file(source["storage_file_id"]) == original
    assert hashlib.sha256(store.download_file(source["storage_file_id"])).hexdigest() == original_sha

    reopened = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight",
    })
    assert reopened["ok"], reopened
    assert reopened["readback"]["draft"]["version"] == 1
    reopened_cells = {(cell["r"], cell["c"]): cell for cell in reopened["readback"]["page"]["cells"]}
    assert reopened_cells[(4, 2)]["value"] == "Ningbo → Hai Phong · checked"
    assert reopened_cells[(4, 4)]["value"] == 1900
    # openpyxl preserves the user formula source but deliberately does not evaluate it.
    drafts = list(store.bucket.find({"metadata.owner_type": "QUOTE_EXCEL_DRAFT", "metadata.source_file_id": source["storage_file_id"]}))
    assert len(drafts) == 1
    edited_bytes = store.download_file(str(drafts[0]._id))
    edited_wb = load_workbook(BytesIO(edited_bytes), data_only=False, keep_links=False)
    assert edited_wb["Ocean Freight"]["B4"].value == "Ningbo → Hai Phong · checked"
    assert edited_wb["Ocean Freight"]["D4"].value == 1900
    assert edited_wb["Ocean Freight"]["D5"].value == "=D4*1.05"
    cached_wb = load_workbook(BytesIO(edited_bytes), data_only=True, keep_links=False)
    assert cached_wb["Ocean Freight"]["D5"].value is None

    stale = dispatch("quote_workbook_draft_save", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight", "expectedVersion": 0,
        "edits": [{"sheet": "Ocean Freight", "r": 4, "c": 4, "type": "number", "value": "2000"}],
    })
    assert stale["ok"] is False and "đổi phiên bản" in stale["error"]

    restored = dispatch("quote_workbook_draft_save", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight", "expectedVersion": 1,
        "edits": [], "restoreOriginal": True,
    })
    assert restored["ok"], restored
    assert restored["readback"]["draft"]["version"] == 2
    restored_cells = {(cell["r"], cell["c"]): cell for cell in restored["readback"]["page"]["cells"]}
    assert restored_cells[(4, 4)]["value"] == 1750
    assert store.download_file(source["storage_file_id"]) == original


def test_workbook_cells_and_draft_are_grant_gated_and_customer_owned(staging):
    import streamlit as st

    original = freight_workbook()
    imported = import_generic(original)
    assert imported["ok"], imported
    source = imported["readback"]["source"]

    st.session_state["current_user"] = {"username": "viewer-workbook", "role": "viewer"}
    listed = dispatch("quote_workbook_sources_list", {"customerId": CUSTOMER_ID})
    assert listed["ok"] is False and "commercial_write" in listed["error"]
    locked = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight",
    })
    assert locked["ok"]
    assert locked["readback"]["page"]["locked"] is True
    assert locked["readback"]["page"]["cells"] == []
    refused = dispatch("quote_workbook_draft_save", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight", "expectedVersion": 0,
        "edits": [{"sheet": "Ocean Freight", "r": 4, "c": 4, "type": "number", "value": "1900"}],
    })
    assert refused["ok"] is False and "commercial_write" in refused["error"]

    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    wrong_customer = dispatch("quote_workbook_draft_save", {
        "customerId": "CUST-OTHER-WORKBOOK", "source": source, "sheet": "Ocean Freight", "expectedVersion": 0,
        "edits": [],
    })
    assert wrong_customer["ok"] is False and "khách hàng" in wrong_customer["error"]


def test_workbook_edit_rejects_formula_injection_and_merged_followers(staging):
    from core.quote_workbook_view import apply_cell_edits

    original = freight_workbook()
    with pytest.raises(ValueError, match="Công thức"):
        apply_cell_edits(original, [{"sheet": "Ocean Freight", "r": 3, "c": 2, "type": "text", "value": "=1+1"}])
    with pytest.raises(ValueError, match="gộp"):
        apply_cell_edits(original, [{"sheet": "Ocean Freight", "r": 2, "c": 3, "type": "text", "value": "not an anchor"}])
    with pytest.raises(ValueError, match="15 chữ số"):
        apply_cell_edits(original, [{"sheet": "Ocean Freight", "r": 4, "c": 4, "type": "number", "value": "1234567890123456"}])


def test_service_only_quote_draft_is_valid_and_customer_export_excludes_cost_and_source(staging):
    original = freight_workbook()
    imported = import_generic(original)
    assert imported["ok"], imported
    source = imported["readback"]["source"]
    details = {
        "schema": "luc-giac/1", "goods_mode": "SERVICE_ONLY", "goods": [], "supplier": "",
        "source": source, "source_warnings": [], "source_facts": {}, "source_costs": [], "disclosures": [],
        "additional_public_notes": "", "active_option": "A",
        "options": {"A": {"scope": "Ocean freight only", "service_lines": [{
            "id": "mapped-freight", "service_name": "Ocean freight 40HQ", "code": "", "unit": "container",
            "qty": 1, "currency": "USD", "cost_unit": 250, "sell_unit": 300, "sell_confirmed": True,
            "tax_pct": None, "internal_note": "PRIVATE-COST-NOTE", "public_note": "",
            "cost_source": "workbook mapping · Ocean Freight row 4", "valid_until": "", "validity_status": "UNKNOWN",
            "source_warning": "", "condition": "UNCONFIRMED",
        }]}, "B": {"scope": "", "service_lines": []}},
        "shipment": {"cbm": None, "weight_kg": None, "pol": "Ningbo", "pod": "Hai Phong", "pickup": "", "delivery": "", "load_model": "FCL", "equipment": "40HQ"},
        "customs": {"confirmed": False, "basis_vnd": None, "basis_note": "", "duty_pct": None, "vat_pct": None, "hs_code": ""},
        "warning_notes": {},
    }
    created = dispatch("quote_create", {
        "customerId": CUSTOMER_ID, "salesOwner": "Sale test", "goodsDescription": "",
        "origin": "Ningbo", "destination": "Hai Phong", "route": "Ningbo → Hai Phong",
        "incoterm": "FOB", "transportMode": "Sea", "fx": {}, "excelQuote": details,
    })
    assert created["ok"], created
    quote = created["readback"]
    assert quote["excelQuote"]["goods_mode"] == "SERVICE_ONLY"
    assert quote["excelQuote"]["goods"] == []
    assert quote["excelQuote"]["calculation"]["row_count"] == 0
    assert quote["excelQuote"]["calculation"]["quantity"] is None
    assert quote["excelQuote"]["calculation"]["estimate_vnd"] is None

    exported = dispatch("quote_export_xlsx", {"id": created["id"]})
    assert exported["ok"], exported
    workbook = load_workbook(BytesIO(base64.b64decode(exported["document"]["downloadBase64"])), data_only=False)
    all_text = "\n".join(str(cell.value or "") for sheet in workbook for row in sheet for cell in row)
    assert "Báo giá chỉ gồm phí dịch vụ; không có hàng hóa." in all_text
    assert "Ocean freight 40HQ" in all_text and "300" in all_text
    assert "250" not in all_text and "PRIVATE-COST-NOTE" not in all_text
    assert "FREIGHT QUOTATION" not in all_text and "Port charges" not in all_text
    assert "DANH MỤC HÀNG HÓA" not in all_text and "THUẾ NHẬP KHẨU DỰ KIẾN" not in all_text


def test_generic_workbook_with_table_far_down_and_right_can_be_opened_and_edited(staging):
    workbook = load_workbook(BytesIO(freight_workbook()))
    rates = workbook["Ocean Freight"]
    for index in range(7):
        workbook.create_sheet(f"Extra rate sheet {index + 1}")
    rates["AZ350"] = "Far table data"
    rates["AZ351"] = 987.5
    output = BytesIO()
    workbook.save(output)
    original = output.getvalue()

    imported = import_generic(original)
    assert imported["ok"], imported
    assert imported["readback"]["workbook_only"] is True
    source = imported["readback"]["source"]
    store = GridFSAttachmentStore(staging)
    assert store.download_file(source["storage_file_id"]) == original

    view = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight", "startRow": 340, "startCol": 48,
    })
    assert view["ok"], view
    page = view["readback"]["page"]
    assert len(view["readback"]["overview"]["sheet_names"]) == 9
    assert page["start_row"] == 340 and page["start_col"] == 48
    assert any(cell["r"] == 350 and cell["c"] == 52 and cell["value"] == "Far table data" for cell in page["cells"])

    saved = dispatch("quote_workbook_draft_save", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Ocean Freight",
        "startRow": 340, "startCol": 48, "expectedVersion": 0,
        "edits": [{"sheet": "Ocean Freight", "r": 351, "c": 52, "type": "number", "value": "1000"}],
    })
    assert saved["ok"], saved
    far = next(cell for cell in saved["readback"]["page"]["cells"] if cell["r"] == 351 and cell["c"] == 52)
    assert far["value"] == 1000
    assert store.download_file(source["storage_file_id"]) == original


def test_mixed_multisheet_cny_usd_formula_workbook_is_stored_and_kept_unmapped(staging):
    original = mixed_customer_workbook()
    original_sha = hashlib.sha256(original).hexdigest()
    imported = import_generic(original)
    assert imported["ok"], imported
    assert imported["readback"]["workbook_only"] is True
    source = imported["readback"]["source"]
    assert source["sheet_names"] == ["客户说明", "Customer goods tab", "Local charges"]
    assert source["sha256"] == original_sha
    assert not imported["readback"].get("goods")

    store = GridFSAttachmentStore(staging)
    assert store.download_file(source["storage_file_id"]) == original
    customer_page = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Customer goods tab",
    })
    assert customer_page["ok"], customer_page
    page = customer_page["readback"]["page"]
    cells = {(cell["r"], cell["c"]): cell for cell in page["cells"]}
    assert cells[(6, 3)]["value"] == "SKU"
    assert cells[(7, 6)]["value"] == "CNY"
    assert cells[(7, 7)]["value"] == 870
    assert customer_page["readback"]["overview"]["sheet_names"] == source["sheet_names"]

    charges = dispatch("quote_source_workbook_view", {
        "customerId": CUSTOMER_ID, "source": source, "sheet": "Local charges",
    })
    assert charges["ok"], charges
    formula = next(cell for cell in charges["readback"]["page"]["cells"] if cell["r"] == 5 and cell["c"] == 5)
    assert formula["kind"] == "formula" and formula["f"] == "=C5*1.08" and formula["unknown"] is True
    assert charges["readback"]["overview"]["sheets"][1]["not_rendered"].get("comments") == 1
    assert store.download_file(source["storage_file_id"]) == original
