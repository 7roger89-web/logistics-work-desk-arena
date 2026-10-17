"""Acceptance C–J of LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.

Covers, on the SYNTHETIC three-sheet Lục Giác-shaped fixture (never the Owner's
real workbook):

  C  the goods table extracted from the customer sheet: 5 rows / 27 pcs / 607,180 RMB
  D  a formula without a cached value stays UNKNOWN and never becomes 0
  E  the title edited to "BÁO GIÁ NHẬP KHẨU BÀN HỌP"
  F  a product name, a column heading, a payment term and a multi-line note edited
  G  the edits are saved, re-read from an independent reader and survive
  H  the exported XLSX opened with openpyxl shows exactly the edited wording
  I  no cost, cost source, internal note or internal metadata in the customer file
  J  a SENT version is immutable while a new draft is edited
  L  the ORIGINAL GridFS bytes keep their SHA256 after all of that

It also asserts the property this task turns on: the Step-3 preview and the XLSX
export consume ONE resolved customer text map, so a region can never be visible
on screen while the file prints the default.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from openpyxl import load_workbook
import pytest

from core.quote_customer_text import (
    CUSTOMER_TEXT_SCHEMA,
    export_rule,
    sanitize_customer_text,
    unmapped_regions,
)
from core.quote_excel_import import parse_luc_giac_workbook
from core.quotations import calculate_quote, customer_quote_snapshot, new_quote_document, transition_quote
from scripts.make_luc_giac_three_sheet_fixture import build_luc_giac_three_sheet_fixture
from views import logi_c1, logi_sandbox

FIXTURE_NAME = "luc-giac-3sheet-SYNTHETIC.xlsx"
TITLE_EDIT = "BÁO GIÁ NHẬP KHẨU BÀN HỌP"
PRODUCT_EDIT = "Bàn họp nhập khẩu cao cấp"
COLUMN_EDIT = "Nội dung dịch vụ"
PAYMENT_EDIT = "Thanh toán 70% trước khi giao hàng, 30% sau khi nhận hàng."
MULTILINE_NOTE = "Giao hàng tại kho khách\nKiểm tra và ký biên bản bàn giao\nBảo hành theo nhà sản xuất"
CLOSING_EDIT = "Rất mong nhận được phản hồi sớm từ Quý khách."
ADDENDUM_EDIT = "Ghi chú bổ sung: thời gian giao hàng có thể thay đổi theo lịch tàu."

# Region ids that BOTH the paper and the XLSX must carry.
ROUNDTRIP_REGIONS = (
    "doc.title", "doc.greeting", "doc.customer_name", "doc.goods_description", "doc.route",
    "doc.option_line", "scope", "notes.additional", "doc.closing", "doc.addendum",
    "col.goods.name", "col.goods.qty", "col.service.name", "col.service.amount",
    "sec.goods", "sec.services", "sec.totals", "sec.customs", "sec.notes",
    # Finding 4 — the descriptive labels that used to be hardcoded on the paper.
    "label.attn", "label.goods", "label.route", "label.ports", "label.scope",
    "label.before_tax", "label.estimate_total", "label.customs_basis",
    "label.duty", "label.vat", "label.duty_rate", "label.vat_rate",
    "doc.disclaimer",
)
# NOTHING is excused any more: a published region that the preview shows and the
# XLSX omits is a defect (Finding 2/6), so this list must stay EMPTY.
PREVIEW_ONLY_REGIONS: tuple[str, ...] = ()


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
    db.customers.insert_one({"id": "CUST-LUCGIAC-TEXT", "name": "Công ty Lục Giác", "contact_person": "Nguyễn Văn A"})
    try:
        yield db
    finally:
        logi_sandbox.reset_backend()
        if had_user:
            st.session_state["current_user"] = previous_user
        else:
            st.session_state.pop("current_user", None)


def dispatch(event, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, {event: {"seq": 1, "payload": {"requestId": "test-request", **payload}}})
    assert len(outcomes) == 1
    return outcomes[0]


def payload(details, **extra):
    return {"customerId": "CUST-LUCGIAC-TEXT", "salesOwner": "Sale test", "goodsDescription": "Bàn họp văn phòng",
            "incoterm": "EXW", "transportMode": "Sea", "route": "Nansha - Hải Phòng",
            "excelQuote": details, "fx": {}, **extra}


def imported(source):
    out = dispatch("quote_import_excel", {"customerId": "CUST-LUCGIAC-TEXT", "fileName": FIXTURE_NAME,
                                          "base64": base64.b64encode(source).decode()})
    assert out["ok"], out
    return out["readback"]


def service_line(**extra):
    return {"id": "fee-a", "service_name": "Vận chuyển Nansha → Hải Phòng", "qty": 1, "unit": "Lần", "currency": "VND",
            "cost_unit": 31800000, "sell_unit": 35000000, "sell_confirmed": True, "tax_pct": 8,
            "internal_note": "PRIVATE-SALE-NOTE", "public_note": "Đã gồm phí nâng hạ tại cảng đi",
            "cost_source": "PRIVATE-RATE-SUPPLIER", **extra}


def edited_draft(source) -> dict:
    """The Step-3 edits a Sale would make by clicking text in the preview."""
    draft = imported(source)
    draft["options"]["A"].update({"scope": "Phạm vi đã thống nhất: vận chuyển và thủ tục nhập khẩu.", "service_lines": [service_line()]})
    draft["options"]["B"]["scope"] = "Phương án ủy thác"
    draft["goods"][0]["description"] = PRODUCT_EDIT
    draft["additional_public_notes"] = MULTILINE_NOTE
    draft["customer_text"] = {"schema": CUSTOMER_TEXT_SCHEMA, "overrides": {
        "doc.title": TITLE_EDIT,
        "doc.greeting": "Cảm ơn Quý khách đã gửi yêu cầu. Chúng tôi xin báo giá như sau:",
        "col.service.name": COLUMN_EDIT,
        "note.payment": PAYMENT_EDIT,
        "doc.closing": CLOSING_EDIT,
        "doc.addendum": ADDENDUM_EDIT,
    }}
    return draft


def exported_workbook(exported) -> tuple[list, str]:
    data = base64.b64decode(exported["document"]["downloadBase64"])
    workbook = load_workbook(BytesIO(data))
    cells = [cell for sheet in workbook for row in sheet for cell in row]
    return workbook, "\n".join(str(cell.value or "") for cell in cells)


# ---------------------------------------------------------- C / D on the fixture
def test_extracted_goods_table_is_five_rows_27_pieces_607180_rmb(proposal):
    quote = calculate_quote({"excel_quote": proposal})
    calculation = quote["excel_quote"]["calculation"]
    assert calculation["row_count"] == 5
    assert calculation["quantity"] == 27
    assert calculation["goods_totals"] == [{"currency": "CNY", "amount": 607180}]
    assert proposal["source"]["sheet_names"] == ["BÁO GIÁ", "LG nhập - Đại lý TT L Xuất", "Dự kiến Chi phí"]
    assert proposal["goods"][0]["unit_price"] == 13055  # the customer sheet, not the internal copy
    assert all(g["source_sheet"] == "BÁO GIÁ" for g in proposal["goods"])


def test_uncached_formula_never_becomes_zero(source):
    workbook = load_workbook(BytesIO(source))
    workbook["BÁO GIÁ"]["G8"] = "=SUM(F8:F12)"  # overwrite a real price with an uncached formula
    data = BytesIO()
    workbook.save(data)
    parsed = parse_luc_giac_workbook(data.getvalue(), "uncached.xlsx")
    assert parsed["goods"][0]["unit_price"] is None
    quote = calculate_quote({"excel_quote": parsed})
    assert quote["excel_quote"]["goods"][0]["line_total"] is None
    assert quote["excel_quote"]["calculation"]["goods_totals"][0]["amount"] is None
    assert quote["excel_quote"]["calculation"]["estimate_vnd"] is None
    assert any(w["id"] == "formula-gap" for w in parsed["source_warnings"])


# ------------------------------------------------------- the map itself (unit)
def test_text_map_covers_the_document_and_never_exposes_an_amount(proposal):
    proposal["options"]["A"].update({"scope": "Phạm vi A", "service_lines": [service_line()]})
    quote = calculate_quote({"excel_quote": proposal, "status": "DRAFT", "customer_name": "Công ty Lục Giác"})
    snapshot = customer_quote_snapshot(quote)
    text = snapshot["text"]
    ids = set(text["values"])
    assert {"doc.title", "doc.greeting", "doc.customer_name", "scope", "notes.additional", "doc.closing"} <= ids
    assert {i for i in ids if i.startswith("goods.row-")} >= {"goods.row-8.name", "goods.row-8.model", "goods.row-8.material", "goods.row-8.note"}
    assert "service.fee-a.name" in ids and "note.payment" in ids
    assert text["editable_region_count"] == len(text["regions"])
    # Bound regions mirror the canonical field they belong to, and nothing else.
    assert text["values"]["goods.row-8.name"] == proposal["goods"][0]["description"]
    assert text["values"]["service.fee-a.name"] == "Vận chuyển Nansha → Hải Phòng"
    assert text["values"]["scope"] == "Phạm vi A"
    assert text["values"]["col.service.name"] == "Chi tiết"  # untouched label = its default
    # No amount, FX rate, tax percentage or total is a text region.
    facts = {str(quote["excel_quote"]["calculation"]["goods_totals"][0]["amount"]), "607180", "607,180"}
    assert not (facts & set(text["values"].values()))
    assert not any(key in ids for key in ("total", "amount_vnd", "estimate_vnd", "fx_rate", "vat_total"))
    assert all(region["id"] == rid for rid, region in [(r["id"], r) for r in text["regions"]])


def test_a_guarded_identity_region_warns_instead_of_silently_renaming():
    proposal = parse_luc_giac_workbook(build_luc_giac_three_sheet_fixture(), FIXTURE_NAME)
    quote = calculate_quote({"excel_quote": {**proposal, "customer_text": sanitize_customer_text(
        {"overrides": {"doc.customer_name": "CÔNG TY TNHH LỤC GIÁC (bản trình bày)"}})},
        "status": "DRAFT", "customer_name": "Công ty Lục Giác", "customer_id": "CUST-LUCGIAC-TEXT"})
    snapshot = customer_quote_snapshot(quote)
    region = next(r for r in snapshot["text"]["regions"] if r["id"] == "doc.customer_name")
    assert region["guarded"] is True and region["mismatch"] is True
    assert snapshot["text"]["values"]["doc.customer_name"] == "CÔNG TY TNHH LỤC GIÁC (bản trình bày)"
    assert snapshot["customer_id"] == "CUST-LUCGIAC-TEXT"  # the directory identity is untouched


def test_sanitizer_refuses_bound_ids_unknown_shapes_and_formula_text():
    clean = sanitize_customer_text({"overrides": {
        "doc.title": "Tiêu đề mới " * 500,
        "scope": "KHÔNG ĐƯỢC NHẬN",                    # bound to a canonical field
        "goods.row-8.name": "KHÔNG ĐƯỢC NHẬN",         # bound to a canonical field
        "doc.addendum": "=1+1",                        # a formula is never a stored value
        "doc.closing": "   ",
        "": "bỏ",
        "doc.greeting": 12345,
        "doc.option_line": "<img src=x onerror=alert(1)>",
    }})
    overrides = clean["overrides"]
    assert clean["schema"] == CUSTOMER_TEXT_SCHEMA
    assert set(overrides) == {"doc.title", "doc.addendum", "doc.option_line", "doc.greeting"}
    # A long value is truncated at the documented bound (6k for a stored
    # override; the editor caps a short label at 2k), never stored unbounded.
    assert 5990 <= len(overrides["doc.title"]) <= 6000  # trailing space trimmed at the bound
    assert overrides["doc.addendum"].startswith("'=1+1")   # literal text, never executable
    assert overrides["doc.option_line"] == "<img src=x onerror=alert(1)>"[:2000]  # stored as TEXT only
    assert overrides["doc.greeting"] == "12345"


# ------------------------------------------------ E/F/G/H/I/J/L on the real path
def test_inline_text_edits_round_trip_to_preview_and_xlsx(staging, source):
    from core.database import load_quotes

    draft = edited_draft(source)
    created = dispatch("quote_create", payload(draft, fx={"CNY": 3900}))
    assert created["ok"], created
    qid = created["id"]
    assert created["readback"]["status"] == "DRAFT"

    # G — an INDEPENDENT fresh reader (not the browser's optimistic copy).
    fresh = load_quotes()[qid]
    overrides = fresh["excel_quote"]["customer_text"]["overrides"]
    assert overrides["doc.title"] == TITLE_EDIT
    assert overrides["note.payment"] == PAYMENT_EDIT
    assert overrides["col.service.name"] == COLUMN_EDIT
    assert fresh["excel_quote"]["goods"][0]["description"] == PRODUCT_EDIT
    assert fresh["excel_quote"]["additional_public_notes"].count("\n") == 2

    # E/F — the SAME resolved map the preview renders.
    preview = dispatch("quote_preview", payload(fresh["excel_quote"], fx={"CNY": 3900}))
    assert preview["ok"], preview
    customer = preview["readback"]["customer"]
    values = customer["text"]["values"]
    assert values["doc.title"] == TITLE_EDIT
    assert values["doc.customer_name"] == "Công ty Lục Giác"
    assert values["goods.row-8.name"] == PRODUCT_EDIT
    assert values["service.fee-a.name"] == "Vận chuyển Nansha → Hải Phòng"
    assert values["col.service.name"] == COLUMN_EDIT
    assert values["note.payment"] == PAYMENT_EDIT
    assert values["notes.additional"] == MULTILINE_NOTE
    assert values["doc.closing"] == CLOSING_EDIT
    assert values["doc.addendum"] == ADDENDUM_EDIT
    assert values["scope"] == "Phạm vi đã thống nhất: vận chuyển và thủ tục nhập khẩu."

    # H — the exported XLSX opened again shows the same wording.
    exported = dispatch("quote_export_xlsx", {"id": qid})
    assert exported["ok"], exported
    workbook, text = exported_workbook(exported)
    assert TITLE_EDIT in text
    assert PRODUCT_EDIT in text
    assert COLUMN_EDIT in text
    assert PAYMENT_EDIT in text
    assert "Dòng một" not in text  # this note is the multi-line one below
    for line_text in MULTILINE_NOTE.split("\n"):
        assert line_text in text
    assert CLOSING_EDIT in text and ADDENDUM_EDIT in text
    assert not any(cell.data_type == "f" for sheet in workbook for row in sheet for cell in row)
    assert TITLE_EDIT in str(workbook["Bao gia"]["A5"].value) and TITLE_EDIT in str(workbook["Bao gia"]["A11"].value)

    # Requirement 8 — ONE map for preview and file: every populated round-trip
    # region value the preview shows is really printed in the XLSX.
    ids = {region["id"] for region in customer["text"]["regions"]}
    assert set(ROUNDTRIP_REGIONS) <= ids
    assert PREVIEW_ONLY_REGIONS == ()
    # No published region may be silently skipped: every one names where it is
    # printed, and an unmapped id is a hard failure.
    assert unmapped_regions(customer["text"]) == []
    missing = []
    for region in customer["text"]["regions"]:
        if not region["value"].strip():
            continue
        for part in str(region["value"]).split("\n"):
            if part.strip() and part not in text:
                missing.append((region["id"], part))
    assert missing == []


def test_sent_version_text_is_frozen_while_a_draft_is_edited(staging, source):
    from core.database import load_quotes

    draft = edited_draft(source)
    created = dispatch("quote_create", payload(draft, fx={"CNY": 3900}))
    assert created["ok"], created
    qid = created["id"]
    for status in ("READY_FOR_REVIEW", "SENT"):
        moved = dispatch("quote_transition", {"id": qid, "nextStatus": status})
        assert moved["ok"], moved
    sent = deepcopy(load_quotes()[qid]["sent_versions"])
    assert sent and sent[0]["customer_snapshot"]["text"]["values"]["doc.title"] == TITLE_EDIT

    # J — the Sale edits the wording again. A SENT quote must become a NEW draft.
    latest = load_quotes()[qid]
    revised_draft = dict(latest["excel_quote"])
    revised_draft["customer_text"] = {"schema": CUSTOMER_TEXT_SCHEMA,
                                      "overrides": {**latest["excel_quote"]["customer_text"]["overrides"],
                                                    "doc.title": "BÁO GIÁ SỬA LẦN HAI"}}
    revised = dispatch("quote_edit", payload(revised_draft, id=qid, expectedVersion=latest["version"], fx={"CNY": 3900}))
    assert revised["ok"], revised
    assert revised["readback"]["status"] == "DRAFT"
    stored = load_quotes()[qid]
    assert stored["sent_versions"] == sent  # frozen history, byte for byte

    historical = dispatch("quote_export_xlsx", {"id": qid, "sentVersion": sent[0]["version"]})
    assert historical["ok"]
    _, old_text = exported_workbook(historical)
    assert TITLE_EDIT in old_text and "BÁO GIÁ SỬA LẦN HAI" not in old_text
    current = dispatch("quote_export_xlsx", {"id": qid})
    assert current["ok"]
    _, new_text = exported_workbook(current)
    assert "BÁO GIÁ SỬA LẦN HAI" in new_text and TITLE_EDIT not in new_text
    # Two versions must never share the same write identity.
    assert sent[0]["customer_snapshot"]["version"] < stored["version"]


def test_export_carries_no_internal_cost_source_note_or_metadata(staging, source):
    created = dispatch("quote_create", payload(edited_draft(source), fx={"CNY": 3900}))
    assert created["ok"], created
    exported = dispatch("quote_export_xlsx", {"id": created["id"]})
    assert exported["ok"], exported
    workbook, text = exported_workbook(exported)
    for secret in ("PRIVATE-SALE-NOTE", "PRIVATE-RATE-SUPPLIER", "31800000", "cost_unit", "7500000"):
        assert secret not in text
    assert "PRIVATE" not in text
    assert "Nội bộ" not in text and "Tính giá nội bộ" not in text
    # No internal cost columns, no hidden sheet, no second worksheet, no formulas.
    assert workbook.sheetnames == ["Bao gia"]
    assert all(sheet.sheet_state == "visible" for sheet in workbook.worksheets)
    assert list(workbook.defined_names) == []
    assert not any(cell.data_type == "f" for sheet in workbook for row in sheet for cell in row)
    # The internal cost SHEETS of the source workbook are not in the customer file.
    assert all(name.strip() not in {"LG nhập - Đại lý TT L Xuất", "Dự kiến Chi phí"} for name in workbook.sheetnames)
    with ZipFile(BytesIO(base64.b64decode(exported["document"]["downloadBase64"]))) as archive:
        assert sum(1 for name in archive.namelist() if name.startswith("xl/worksheets/sheet")) == 1
        package = "".join(archive.read(name).decode("utf-8", "ignore")
                          for name in archive.namelist() if name.endswith(".xml"))
    assert "PRIVATE" not in package
    assert "Dự kiến Chi phí" not in package and "LG nhập - Đại lý TT L Xuất" not in package


def test_saved_text_survives_an_independent_reload_and_edit_cycle(staging, source):
    """G: save → reload the stored quote → edit again → reload → still there."""
    from core.database import load_quotes

    created = dispatch("quote_create", payload(edited_draft(source), fx={"CNY": 3900}))
    qid = created["id"]
    reopened = load_quotes()[qid]["excel_quote"]
    assert reopened["customer_text"]["overrides"]["doc.title"] == TITLE_EDIT
    # Reopening and saving WITHOUT touching the text must not erase it.
    second = dispatch("quote_edit", payload(reopened, id=qid, expectedVersion=load_quotes()[qid]["version"], fx={"CNY": 3900}))
    assert second["ok"], second
    assert second["readback"]["excelQuote"]["customer_text"]["overrides"]["doc.title"] == TITLE_EDIT
    assert second["readback"]["excelQuote"]["customer_text"]["overrides"]["doc.addendum"] == ADDENDUM_EDIT
    # A forged payload claiming the title again through a bound id is refused.
    forged = dict(reopened)
    forged["customer_text"] = {"schema": CUSTOMER_TEXT_SCHEMA,
                               "overrides": {**reopened["customer_text"]["overrides"],
                                             "scope": "Đổi phạm vi bằng override", "goods.row-8.name": "Tên hàng qua override"}}
    third = dispatch("quote_edit", payload(forged, id=qid, expectedVersion=load_quotes()[qid]["version"], fx={"CNY": 3900}))
    assert third["ok"], third
    stored = load_quotes()[qid]["excel_quote"]
    # Only the two BOUND ids are refused: the canonical fields own that text.
    assert stored["customer_text"]["overrides"] == reopened["customer_text"]["overrides"]
    assert stored["goods"][0]["description"] == PRODUCT_EDIT
    assert stored["options"]["A"]["scope"] == "Phạm vi đã thống nhất: vận chuyển và thủ tục nhập khẩu."


def test_original_gridfs_bytes_keep_their_sha256_after_every_edit(staging, source):
    import hashlib

    created = dispatch("quote_create", payload(edited_draft(source), fx={"CNY": 3900}))
    qid = created["id"]
    downloaded = dispatch("quote_source_download", {"id": qid})
    assert downloaded["ok"], downloaded
    original = base64.b64decode(downloaded["document"]["downloadBase64"])
    assert original == source
    assert hashlib.sha256(original).hexdigest() == hashlib.sha256(source).hexdigest()
    stored = staging.quotes.find_one({"id": qid})
    assert stored["excel_quote"]["source"]["sha256"] == hashlib.sha256(source).hexdigest()
    assert staging.quotes.count_documents({"id": qid}) == 1


def test_text_edits_do_not_change_any_amount(staging, source):
    """Amounts stay backend-computed: editing the wording moves no number."""
    from core.database import load_quotes

    baseline = imported(source)
    baseline["options"]["A"].update({"scope": "Phạm vi A", "service_lines": [service_line()]})
    first = dispatch("quote_create", payload(baseline, fx={"CNY": 3900}))
    assert first["ok"], first
    numbers = first["readback"]["excelQuote"]["calculation"]

    tweaked = deepcopy(load_quotes()[first["id"]]["excel_quote"])
    tweaked["customer_text"] = {"schema": CUSTOMER_TEXT_SCHEMA, "overrides": {
        "doc.title": TITLE_EDIT, "col.goods.line_total": "Số tiền phải trả", "note.payment": PAYMENT_EDIT}}
    second = dispatch("quote_edit", payload(tweaked, id=first["id"], expectedVersion=load_quotes()[first["id"]]["version"], fx={"CNY": 3900}))
    assert second["ok"], second
    after = second["readback"]["excelQuote"]["calculation"]
    assert after == numbers
    exported = dispatch("quote_export_xlsx", {"id": first["id"]})
    workbook, text = exported_workbook(exported)
    assert "Số tiền phải trả" in text          # the LABEL is editable
    assert 607180 in [cell.value for sheet in workbook for row in sheet for cell in row]  # the NUMBER is not
