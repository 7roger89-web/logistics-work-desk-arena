"""Focused repair of the four findings from the independent source review.

LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 · stacked PR #206 · SYNTHETIC fixture.

  1  the ORIGINAL uploaded workbook is protected on BOTH paths (view + download)
     with the ONE existing business grant (commercial_write), and an
     UNCLASSIFIED sheet is not treated as public;
  2  the edited "dịch vụ" summary reaches the customer XLSX and no longer gets
     overwritten by the option line;
  3  the edited customer display name reaches the To cell while customer_id and
     the directory record stay untouched;
  4  the descriptive labels ("Kính gửi", "Cảng / điểm", "Nơi lấy hàng" …) are
     editable in place and every published region has a declared XLSX rule.

The permission negatives go through the REAL dispatcher (views.logi_c1), not
through a disabled button: a UI hint is never proof of an authorization rule.
"""
from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from datetime import date
from io import BytesIO

from openpyxl import load_workbook
import pytest

from core.quote_customer_text import export_rule, unmapped_regions
from core.quote_workbook_view import SHEET_CUSTOMER as CLASS_CUSTOMER
from core.quote_excel_import import parse_luc_giac_workbook
from scripts.make_luc_giac_three_sheet_fixture import (
    SHEET_CUSTOMER,
    SHEET_INTERNAL_COST,
    SHEET_INTERNAL_DUP,
    build_luc_giac_three_sheet_fixture,
)
from views import logi_c1, logi_sandbox

FIXTURE_NAME = "luc-giac-3sheet-SYNTHETIC.xlsx"
SUMMARY_EDIT = "Dịch vụ trọn gói: vận chuyển biển + thủ tục nhập khẩu + giao tận kho."
OPTION_LINE_EDIT = "Phương án A — KHÁCH ĐỨNG TÊN NHẬP KHẨU (đã sửa)"
DISPLAY_NAME_EDIT = "Công ty Lục Giác — Chi nhánh Hà Nội"
ATTN_EDIT = "Kính gửi Quý công ty"
PORTS_EDIT = "Cảng đi / cảng đến"
PICKUP_EDIT = "Nơi nhận hàng tại xưởng"


@pytest.fixture
def source() -> bytes:
    return build_luc_giac_three_sheet_fixture()


@pytest.fixture
def proposal(source):
    return parse_luc_giac_workbook(source, FIXTURE_NAME, today=date(2026, 10, 16))


@pytest.fixture
def staging():
    import streamlit as st

    had_user = "current_user" in st.session_state
    previous_user = st.session_state.get("current_user")
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    from core.database import get_db

    db = get_db()
    db.customers.insert_one({"id": "CUST-LUCGIAC-REPAIR", "name": "Công ty Lục Giác", "contact_person": "Nguyễn Văn A"})
    try:
        yield db
    finally:
        logi_sandbox.reset_backend()
        if had_user:
            st.session_state["current_user"] = previous_user
        else:
            st.session_state.pop("current_user", None)


def dispatch(event, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, {event: {"seq": 1, "payload": {"requestId": "repair-request", **payload}}})
    assert len(outcomes) == 1
    return outcomes[0]


def as_role(role: str, username: str = "test-actor"):
    import streamlit as st

    st.session_state["current_user"] = {"username": username, "role": role}


def payload(details, **extra):
    return {"customerId": "CUST-LUCGIAC-REPAIR", "salesOwner": "Sale test", "goodsDescription": "Bàn họp văn phòng",
            "incoterm": "EXW", "transportMode": "Sea", "route": "Nansha - Hải Phòng",
            "excelQuote": details, "fx": {"CNY": 3900}, **extra}


def imported(source) -> dict:
    out = dispatch("quote_import_excel", {"customerId": "CUST-LUCGIAC-REPAIR", "fileName": FIXTURE_NAME,
                                          "base64": base64.b64encode(source).decode()})
    assert out["ok"], out
    return out["readback"]


def service_line(**extra):
    return {"id": "fee-a", "service_name": "Vận chuyển Nansha → Hải Phòng", "qty": 1, "unit": "Lần", "currency": "VND",
            "cost_unit": 31800000, "sell_unit": 35000000, "sell_confirmed": True, "tax_pct": 8,
            "internal_note": "PRIVATE-SALE-NOTE", "cost_source": "PRIVATE-RATE-SUPPLIER",
            "public_note": "Đã gồm phí nâng hạ tại cảng đi", **extra}


def repair_draft(source) -> dict:
    """The exact edits the four findings are about."""
    draft = imported(source)
    draft["options"]["A"].update({"scope": "Phạm vi đã thống nhất: vận chuyển và thủ tục nhập khẩu.",
                                  "service_lines": [service_line()]})
    draft["shipment"] = {**dict(draft.get("shipment") or {}), "pickup": "Xưởng Nansha", "delivery": "Thanh Trì, Hà Nội"}
    draft["customer_text"] = {"schema": "quote-customer-text/1", "overrides": {
        "sec.service_summary": SUMMARY_EDIT,      # Finding 2
        "doc.option_line": OPTION_LINE_EDIT,
        "doc.customer_name": DISPLAY_NAME_EDIT,   # Finding 3
        "label.attn": ATTN_EDIT,                  # Finding 4
        "label.ports": PORTS_EDIT,
        "label.pickup": PICKUP_EDIT,
    }}
    return draft


def save(draft) -> str:
    created = dispatch("quote_create", payload(draft))
    assert created["ok"], created
    return created["id"]


def export_text(qid: str):
    from core.database import load_quotes

    exported = dispatch("quote_export_xlsx", {"id": qid})
    assert exported["ok"], exported
    data = base64.b64decode(exported["document"]["downloadBase64"])
    workbook = load_workbook(BytesIO(data))
    sheet = workbook["Bao gia"]
    text = "\n".join(str(cell.value) for row in sheet for cell in row if cell.value is not None)
    return workbook, sheet, text


# ======================================================= Finding 1 — permissions
def test_viewer_may_read_the_customer_quote_but_not_the_supplier_workbook(staging, source):
    """The negative path is the real dispatcher, not a disabled button."""
    qid = save(repair_draft(source))
    as_role("viewer")

    # The customer-facing half still works: a viewer reads the customer sheet.
    customer = dispatch("quote_source_workbook_view", {"id": qid, "sheet": SHEET_CUSTOMER})
    assert customer["ok"] is True
    assert customer["readback"]["can_download_source"] is False

    # …but the raw workbook (which carries the cost sheets) is refused outright.
    refused = dispatch("quote_source_download", {"id": qid})
    assert refused["ok"] is False
    assert "RBAC" in refused["error"] and "commercial_write" in refused["error"]
    assert "document" not in refused or not refused.get("document")
    for sheet in (SHEET_INTERNAL_COST, SHEET_INTERNAL_DUP):
        locked = dispatch("quote_source_workbook_view", {"id": qid, "sheet": sheet})
        assert locked["ok"] is True and locked["readback"]["page"]["locked"] is True
        assert locked["readback"]["page"]["cells"] == []


@pytest.mark.parametrize(
    ("role", "may_take_the_original_file"),
    # The legacy "sales"/"viewer" aliases hold commercial_view only; the current
    # "sale", "support" and "admin" roles hold commercial_write. The two paths
    # must agree for EVERY role, whichever side of that line it falls on.
    [("viewer", False), ("sales", False), ("sale", True), ("support", True), ("admin", True)],
)
def test_view_and_download_share_ONE_permission_decision(staging, source, role, may_take_the_original_file):
    qid = save(repair_draft(source))
    as_role(role)

    download = dispatch("quote_source_download", {"id": qid})
    internal = dispatch("quote_source_workbook_view", {"id": qid, "sheet": SHEET_INTERNAL_COST})
    assert internal["ok"] is True  # the sheet LIST is readable; its CONTENT is the question
    internal_open = internal["readback"]["page"]["locked"] is False

    assert download["ok"] is may_take_the_original_file
    assert internal_open is may_take_the_original_file        # the two paths agree
    assert internal["readback"]["can_download_source"] is may_take_the_original_file
    if may_take_the_original_file:
        assert base64.b64decode(download["document"]["downloadBase64"]) == source
    else:
        assert not download.get("document")


def test_unclassified_sheet_is_not_public(staging, source):
    """An extra, unnameable sheet is protected like an internal one."""
    from openpyxl import load_workbook as open_workbook

    workbook = open_workbook(BytesIO(source))
    workbook.create_sheet("Sheet1")["A1"] = "GHI CHÚ SOẠN THẢO — không rõ có được gửi khách không"
    buffer = BytesIO()
    workbook.save(buffer)
    with_extra = buffer.getvalue()

    imported_extra = dispatch("quote_import_excel", {"customerId": "CUST-LUCGIAC-REPAIR", "fileName": FIXTURE_NAME,
                                                    "base64": base64.b64encode(with_extra).decode()})
    assert imported_extra["ok"], imported_extra
    qid = save(imported_extra["readback"])

    page = dispatch("quote_source_workbook_view", {"id": qid, "sheet": "Sheet1"})
    assert page["ok"] is True
    assert page["readback"]["page"]["classification"] == "UNCLASSIFIED"

    as_role("viewer")
    locked = dispatch("quote_source_workbook_view", {"id": qid, "sheet": "Sheet1"})
    assert locked["readback"]["page"]["locked"] is True, "UNCLASSIFIED must not default to public"
    assert locked["readback"]["page"]["cells"] == []
    assert "commercial_write" in locked["readback"]["page"]["reason"]
    assert dispatch("quote_source_download", {"id": qid})["ok"] is False
    as_role("support")
    unlocked = dispatch("quote_source_workbook_view", {"id": qid, "sheet": "Sheet1"})
    assert unlocked["readback"]["page"]["locked"] is False
    assert any("GHI CHÚ SOẠN THẢO" in str(c.get("value")) for c in unlocked["readback"]["page"]["cells"])


COST_LABEL = "Vận chuyển nội bộ đại lý"
COST_AMOUNT = 12500000


def workbook_with_cost_embedded_in_the_customer_sheet(source) -> bytes:
    """ONE sheet ("BÁO GIÁ") carrying the internal cost at J20/K20.

    Exactly the shape the finding describes, and the shape a supplier really
    sends: a single tab, with the cost scratched in beside the goods table. The
    parser DOES notice this one — but no gate may depend on it noticing.
    """
    from openpyxl import load_workbook as open_workbook

    workbook = open_workbook(BytesIO(source))
    del workbook[SHEET_INTERNAL_COST]
    del workbook[SHEET_INTERNAL_DUP]
    sheet = workbook[SHEET_CUSTOMER]
    sheet.cell(20, 10, COST_LABEL)      # J20
    sheet.cell(20, 11, COST_AMOUNT)     # K20
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def import_embedded(one_sheet: bytes) -> dict:
    """Import EXACTLY these bytes — never a re-render of them.

    openpyxl writes fresh zip timestamps on every save, so two builds of the
    same logical workbook are not byte-identical. Comparing a download against a
    rebuilt copy would be flaky (and would prove the wrong thing), so the bytes
    that were uploaded are the bytes the assertions use.
    """
    out = dispatch("quote_import_excel", {"customerId": "CUST-LUCGIAC-REPAIR", "fileName": FIXTURE_NAME,
                                          "base64": base64.b64encode(one_sheet).decode()})
    assert out["ok"], out
    return out["readback"]


def source_cell_text(page) -> str:
    """Every piece of CELL content the page hands back — the thing under test."""
    chunks = [str(page.get("reason") or "")] if page.get("locked") is False else [""]
    for cell in page.get("cells") or []:
        for key in ("value", "display", "f", "nf"):
            if cell.get(key) not in (None, ""):
                chunks.append(str(cell[key]))
    return "\n".join(chunks)


def test_cost_data_embedded_in_the_customer_sheet_still_protects_the_file(staging, source):
    """A one-sheet workbook is not automatically publishable.

    (2) the raw download is refused, and (3) the raw workbook VIEW must not hand
    back J20/K20 either. Before this test the view was only checked on internal
    sheets — a cost inside the customer sheet walked straight out.
    """
    one_sheet = workbook_with_cost_embedded_in_the_customer_sheet(source)
    readback = import_embedded(one_sheet)
    assert readback["source"]["sheet_names"] == [SHEET_CUSTOMER]      # (1) one sheet only
    assert readback["source"]["goods_sheet"] == SHEET_CUSTOMER
    assert COST_AMOUNT in [c["amount"] for c in readback["source_costs"]]
    assert all(c["source_sheet"] == SHEET_CUSTOMER for c in readback["source_costs"])

    qid = save(readback)

    # (2) the bytes are refused for a read-only role …
    as_role("viewer")
    refused = dispatch("quote_source_download", {"id": qid})
    assert refused["ok"] is False and "RBAC" in refused["error"]
    assert "dòng chi phí nằm ngay trong sheet khách" in refused["error"]

    # … (3) and so is the CELL CONTENT, through the view, on the customer sheet.
    view = dispatch("quote_source_workbook_view", {"id": qid, "sheet": SHEET_CUSTOMER})
    assert view["ok"] is True, view                                     # metadata is allowed
    page = view["readback"]["page"]
    assert page["sheet"] == SHEET_CUSTOMER and page["classification"] == CLASS_CUSTOMER
    assert page["locked"] is True, "the customer tab must not bypass the grant"
    assert page["cells"] == [] and page["merges"] == []
    assert page["row_count"] > 0 and page["sheet_index"] == 1          # it still discloses that the sheet exists
    assert "commercial_write" in page["reason"]
    assert COST_LABEL not in source_cell_text(page)
    assert str(COST_AMOUNT) not in source_cell_text(page)

    # (4) the ordinary CUSTOMER quotation is untouched for the same role.
    customer_doc = dispatch("quote_export_xlsx", {"id": qid})
    assert customer_doc["ok"] is True, customer_doc
    customer_bytes = base64.b64decode(customer_doc["document"]["downloadBase64"])
    customer_text = "\n".join(str(c.value) for row in load_workbook(BytesIO(customer_bytes))["Bao gia"] for c in row if c.value is not None)
    assert "BÁO GIÁ" in customer_text.upper()
    assert COST_LABEL not in customer_text and str(COST_AMOUNT) not in customer_text

    # (5)(6) a role that holds the grant reads the source AND still gets the ORIGINAL bytes.
    as_role("support")
    granted = dispatch("quote_source_workbook_view", {"id": qid, "sheet": SHEET_CUSTOMER})
    assert granted["ok"] is True and granted["readback"]["page"]["locked"] is False
    assert COST_LABEL in source_cell_text(granted["readback"]["page"])
    download = dispatch("quote_source_download", {"id": qid})
    assert download["ok"] is True, download
    payload = download["document"]
    assert base64.b64decode(payload["downloadBase64"]) == one_sheet   # the file as uploaded, byte for byte
    assert payload["byteSize"] == len(one_sheet)
    assert readback["source"]["sha256"] == hashlib.sha256(one_sheet).hexdigest()


@pytest.mark.parametrize("role,granted", [("viewer", False), ("sales", False), ("sale", True),
                                          ("support", True), ("admin", True)])
def test_source_workbook_view_needs_the_grant_on_every_sheet(staging, source, role, granted):
    """The rule is the GRANT, on every sheet — never the parser's classification.

    `sales` is the legacy role: it holds `commercial_view` + `sales_write` but not
    `commercial_write`, so it must be treated exactly like a reader.
    """
    readback = imported(source)
    qid = save(repair_draft(source))
    as_role(role)
    for sheet in readback["source"]["sheet_names"]:                    # (7) the three-sheet file too
        view = dispatch("quote_source_workbook_view", {"id": qid, "sheet": sheet})
        assert view["ok"] is True, (role, sheet, view)
        page = view["readback"]["page"]
        if granted:
            assert page["locked"] is False and page["cells"], (role, sheet)
        else:
            assert page["locked"] is True and page["cells"] == [], (role, sheet)
            assert "commercial_write" in page["reason"]
    # No caller loses the sheet inventory itself.
    assert dispatch("quote_source_workbook_view", {"id": qid})["readback"]["overview"]["sheet_names"] == \
        readback["source"]["sheet_names"]


def test_download_refuses_bytes_that_no_longer_match_the_stored_sha256(staging, source, monkeypatch):
    from core.gridfs_client import GridFSAttachmentStore

    qid = save(repair_draft(source))
    monkeypatch.setattr(GridFSAttachmentStore, "download_file", lambda self, file_id: b"tampered-bytes")
    out = dispatch("quote_source_download", {"id": qid})
    assert out["ok"] is False and "SHA256" in out["error"]


def test_original_file_is_still_never_rewritten(staging, source):
    import hashlib

    qid = save(repair_draft(source))
    out = dispatch("quote_source_download", {"id": qid})
    assert out["ok"] is True
    assert hashlib.sha256(base64.b64decode(out["document"]["downloadBase64"])).hexdigest() == hashlib.sha256(source).hexdigest()


# ============================== Finding 2 — the summary must survive to the XLSX
def test_edited_service_summary_reaches_the_xlsx_and_the_option_line_is_kept(staging, source):
    qid = save(repair_draft(source))
    _, sheet, text = export_text(qid)

    assert SUMMARY_EDIT in text
    assert sheet["A15"].value == SUMMARY_EDIT, "the edited summary owns its own row"
    assert sheet["A16"].value == OPTION_LINE_EDIT, "the option line is NOT overwritten and NOT overwriting"
    assert "Dịch vụ: giao nhận" not in text, "the default summary must not survive the edit"


def test_no_published_region_is_silently_dropped_from_the_file(staging, source):
    """The cross-check exception is gone: region-by-region, the file must agree."""
    draft = repair_draft(source)
    qid = save(draft)
    preview = dispatch("quote_preview", payload(draft))
    assert preview["ok"], preview
    text_map = preview["readback"]["customer"]["text"]

    assert unmapped_regions(text_map) == []
    assert text_map["unmapped"] == []
    assert all(rule for rule in text_map["export_rules"].values())
    assert export_rule("sec.service_summary") is not None

    _, _, text = export_text(qid)
    missing = [(region["id"], part) for region in text_map["regions"] if region["value"].strip()
               for part in str(region["value"]).split("\n") if part.strip() and part not in text]
    assert missing == []


# ============================ Finding 3 — the displayed name, not the directory
def test_edited_display_name_reaches_the_to_cell_without_touching_the_directory(staging, source):
    from core.database import load_quotes

    qid = save(repair_draft(source))
    stored = load_quotes()[qid]
    assert stored["customer_id"] == "CUST-LUCGIAC-REPAIR"          # identity untouched
    assert staging.customers.find_one({"id": "CUST-LUCGIAC-REPAIR"})["name"] == "Công ty Lục Giác"

    preview = dispatch("quote_preview", payload(stored["excel_quote"]))
    values = preview["readback"]["customer"]["text"]["values"]
    assert values["doc.customer_name"] == DISPLAY_NAME_EDIT
    assert "doc.customer_name" in preview["readback"]["customer"]["text"]["mismatches"]

    _, sheet, text = export_text(qid)
    assert sheet["G7"].value == DISPLAY_NAME_EDIT, "the To cell prints what the Sale published"
    assert DISPLAY_NAME_EDIT in text
    to_cell = sheet["G7"].value
    assert to_cell == preview["readback"]["customer"]["text"]["values"]["doc.customer_name"]


def test_restoring_the_display_name_returns_the_confirmed_wording(staging, source):
    draft = repair_draft(source)
    draft["customer_text"]["overrides"].pop("doc.customer_name")
    qid = save(draft)
    _, sheet, _ = export_text(qid)
    assert sheet["G7"].value == "Công ty Lục Giác"


# ====================================== Finding 4 — labels are editable in place
def test_label_edits_round_trip_preview_save_reload_xlsx(staging, source):
    from core.database import load_quotes

    draft = repair_draft(source)
    qid = save(draft)

    # An INDEPENDENT reader, then a preview built from it: this is the reload.
    fresh = load_quotes()[qid]
    preview = dispatch("quote_preview", payload(fresh["excel_quote"]))
    assert preview["ok"], preview
    values = preview["readback"]["customer"]["text"]["values"]
    assert values["label.attn"] == ATTN_EDIT
    assert values["label.ports"] == PORTS_EDIT
    assert values["label.pickup"] == PICKUP_EDIT
    assert values["label.delivery"] == "Giao tại"          # untouched label keeps its default

    _, sheet, text = export_text(qid)
    for edited in (ATTN_EDIT, PORTS_EDIT, PICKUP_EDIT):
        assert edited in text, f"{edited} missing from the customer file"
    assert f"{PORTS_EDIT}: " in sheet["A19"].value
    assert ATTN_EDIT == sheet["F7"].value


def test_a_label_region_only_exists_when_its_line_is_on_the_document(staging, source):
    """Otherwise a region could be editable and yet impossible to print."""
    draft = imported(source)
    draft["options"]["A"].update({"scope": "Phạm vi A", "service_lines": [service_line()]})
    assert not str((draft.get("shipment") or {}).get("pickup") or "").strip()
    qid = save(draft)
    preview = dispatch("quote_preview", payload(load_quotes_for(qid)))
    values = preview["readback"]["customer"]["text"]["values"]
    shipment = preview["readback"]["customer"]["shipment"]
    # The rule, stated once: a label exists exactly when its line is published.
    for label_id, present in (("label.pickup", bool(str(shipment.get("pickup") or "").strip())),
                              ("label.delivery", bool(str(shipment.get("delivery") or "").strip())),
                              ("label.goods", True),
                              ("label.ports", True)):
        assert (label_id in values) is present, f"{label_id} publication must follow its data line"
    assert "label.pickup" not in values                    # this fixture ships no pickup point
    assert "sec.no_services" not in values                  # a service line is published


def test_labels_are_wording_only_and_never_move_a_number(staging, source):
    plain = imported(source)
    plain["options"]["A"].update({"scope": "Phạm vi A", "service_lines": [service_line()]})
    edited = deepcopy(plain)
    edited["customer_text"] = {"schema": "quote-customer-text/1",
                              "overrides": {"label.before_tax": "Cộng trước thuế", "label.duty": "Thuế nhập khẩu dự kiến"}}

    first = dispatch("quote_preview", payload(plain))["readback"]["customer"]
    second = dispatch("quote_preview", payload(edited))["readback"]["customer"]
    assert first["goods_calculation"] == second["goods_calculation"]
    assert second["text"]["values"]["label.before_tax"] == "Cộng trước thuế"

    plain_id, edited_id = save(plain), save(edited)
    _, _, text = export_text(edited_id)
    assert "Cộng trước thuế" in text and "Thuế nhập khẩu dự kiến" in text

    # A wording edit moves no number in the file: the numeric cells are identical.
    def numbers(qid):
        _, sheet, _ = export_text(qid)
        return sorted((cell.coordinate, cell.value) for row in sheet for cell in row
                      if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool))

    assert numbers(plain_id) == numbers(edited_id)
    assert numbers(edited_id), "the exported document really does carry numbers"
    assert any(value == 607180 for _coord, value in numbers(edited_id))


def test_no_amount_fx_or_identity_region_can_be_forged_as_a_label(staging, source):
    """A label id is a label; an amount still has no editable region at all."""
    draft = imported(source)
    draft["customer_text"] = {"schema": "quote-customer-text/1", "overrides": {
        "label.before_tax": "Cộng trước thuế",
        "sec.totals": "TỔNG CỘNG ĐÃ SỬA",
        "total": "KHÔNG ĐƯỢC NHẬN",
        "estimate_vnd": "0",
        "goods.row-8.qty": "9999",
    }}
    qid = save(draft)
    preview = dispatch("quote_preview", payload(load_quotes_for(qid)))
    values = preview["readback"]["customer"]["text"]["values"]
    assert values["label.before_tax"] == "Cộng trước thuế"
    assert values["sec.totals"] == "TỔNG CỘNG ĐÃ SỬA"
    assert not any(key in values for key in ("total", "estimate_vnd", "goods.row-8.qty"))
    assert preview["readback"]["customer"]["goods_calculation"]["quantity"] == 27
    assert preview["readback"]["customer"]["goods_calculation"]["goods_totals"] == [{"currency": "CNY", "amount": 607180}]
    _, _, text = export_text(qid)
    assert "9999" not in text and "KHÔNG ĐƯỢC NHẬN" not in text


def load_quotes_for(qid: str) -> dict:
    from core.database import load_quotes

    return load_quotes()[qid]["excel_quote"]
