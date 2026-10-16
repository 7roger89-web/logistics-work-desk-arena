"""Evidence generator for LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.

Runs the REAL C1 seam on the SYNTHETIC three-sheet Lục Giác-shaped workbook:
import → Step-3 inline edits → save (quote_create) → independent fresh read →
customer snapshot (the SAME map the preview renders) → customer XLSX export →
reopen with openpyxl. Then writes the artifacts an Owner can inspect:

  evidence/excel-fidelity-inline-edit-v1/customer-quote-SYNTHETIC-edited.xlsx
  evidence/excel-fidelity-inline-edit-v1/xlsx-vs-preview.json
  evidence/excel-fidelity-inline-edit-v1/source-immutability.json
  evidence/excel-fidelity-inline-edit-v1/fidelity-declared.json

The workbook is SYNTHETIC. Nothing here is evidence about the Owner's original
Lục Giác file, and the transport is the in-memory staging one, not real MongoDB.

Usage: .venv/bin/python scripts/export_excel_customer_crosscheck.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from copy import deepcopy
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.quote_customer_text import CUSTOMER_TEXT_SCHEMA
from core.quote_excel_import import parse_luc_giac_workbook
from core.quote_workbook_view import overview
from core.quotations import customer_quote_snapshot
from scripts.make_luc_giac_three_sheet_fixture import build_luc_giac_three_sheet_fixture
from views import logi_c1, logi_sandbox

EVIDENCE = ROOT / "evidence/excel-fidelity-inline-edit-v1"
FIXTURE_NAME = "luc-giac-3sheet-SYNTHETIC.xlsx"
TITLE_EDIT = "BÁO GIÁ NHẬP KHẨU BÀN HỌP"
PRODUCT_EDIT = "Bàn họp nhập khẩu cao cấp"
COLUMN_EDIT = "Nội dung dịch vụ"
PAYMENT_EDIT = "Thanh toán 70% trước khi giao hàng, 30% sau khi nhận hàng."
MULTILINE_NOTE = "Giao hàng tại kho khách\nKiểm tra và ký biên bản bàn giao\nBảo hành theo nhà sản xuất"
# Text that must NEVER reach the customer file.
INTERNAL_STRINGS = ["PRIVATE-SALE-NOTE", "PRIVATE-RATE-SUPPLIER", "31800000", "31.800.000",
                    "LG nhập - Đại lý TT L Xuất", "Dự kiến Chi phí", "PRIVATE-INTERNAL-NOTE"]


def dispatch(event: str, payload: dict) -> dict:
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, {event: {"seq": 1, "payload": {"requestId": "evidence", **payload}}})
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def main() -> None:
    import streamlit as st

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    from core.database import get_db
    get_db().customers.insert_one({"id": "CUST-LUCGIAC-EVIDENCE", "name": "Công ty Lục Giác", "contact_person": "Nguyễn Văn A"})

    source = build_luc_giac_three_sheet_fixture()
    source_sha = hashlib.sha256(source).hexdigest()
    proposal = parse_luc_giac_workbook(source, FIXTURE_NAME, today=date(2026, 10, 16))

    imported = dispatch("quote_import_excel", {"customerId": "CUST-LUCGIAC-EVIDENCE", "fileName": FIXTURE_NAME,
                                              "base64": base64.b64encode(source).decode()})
    assert imported["ok"], imported
    draft = imported["readback"]
    draft["options"]["A"].update({
        "scope": "Phạm vi đã thống nhất: vận chuyển và thủ tục nhập khẩu.",
        "service_lines": [{"id": "fee-a", "service_name": "Vận chuyển Nansha → Hải Phòng", "qty": 1, "unit": "Lần",
                           "currency": "VND", "cost_unit": 31800000, "sell_unit": 35000000, "sell_confirmed": True,
                           "tax_pct": 8, "internal_note": "PRIVATE-INTERNAL-NOTE", "cost_source": "PRIVATE-RATE-SUPPLIER",
                           "public_note": "Đã gồm phí nâng hạ tại cảng đi"}],
    })
    draft["goods"][0]["description"] = PRODUCT_EDIT
    draft["additional_public_notes"] = MULTILINE_NOTE
    draft["customer_text"] = {"schema": CUSTOMER_TEXT_SCHEMA, "overrides": {
        "doc.title": TITLE_EDIT, "col.service.name": COLUMN_EDIT, "note.payment": PAYMENT_EDIT,
    }}

    created = dispatch("quote_create", {
        "customerId": "CUST-LUCGIAC-EVIDENCE", "salesOwner": "staging.support", "goodsDescription": "Bàn họp văn phòng",
        "incoterm": "EXW", "transportMode": "Sea", "route": "Nansha - Hải Phòng", "excelQuote": draft, "fx": {"CNY": 3900},
    })
    assert created["ok"], created
    qid = created["id"]

    # Independent fresh reader — never the browser's optimistic copy.
    from core.database import load_quotes
    fresh = load_quotes()[qid]
    preview = dispatch("quote_preview", {
        "customerId": "CUST-LUCGIAC-EVIDENCE", "salesOwner": "staging.support", "goodsDescription": "Bàn họp văn phòng",
        "incoterm": "EXW", "transportMode": "Sea", "route": "Nansha - Hải Phòng", "excelQuote": fresh["excel_quote"], "fx": {"CNY": 3900},
    })
    assert preview["ok"], preview
    customer = preview["readback"]["customer"]
    values = customer["text"]["values"]

    exported = dispatch("quote_export_xlsx", {"id": qid})
    assert exported["ok"], exported
    data = base64.b64decode(exported["document"]["downloadBase64"])
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    xlsx_path = EVIDENCE / "customer-quote-SYNTHETIC-edited.xlsx"
    xlsx_path.write_bytes(data)

    workbook = load_workbook(BytesIO(data))
    cells = [(sheet.title, cell.coordinate, cell.value, cell.data_type)
             for sheet in workbook for row in sheet for cell in row if cell.value not in (None, "")]
    flat = "\n".join(str(cell.value) for cell in [c for s in workbook for row in s for c in row] if cell.value is not None)

    # Every region the preview shows must be findable in the file, unless the UI
    # documents it as preview-only (the exporter prints the option line instead).
    preview_only = {"sec.service_summary"}
    missing = [rid for rid, value in values.items()
               if rid not in preview_only and str(value).strip() and str(value).strip() not in flat]
    leaks = [needle for needle in INTERNAL_STRINGS if needle in flat]
    formulas = [(sheet, coord) for sheet, coord, _v, kind in cells if kind == "f"]
    numbers = {rid: value for rid, value in values.items()
               if any(ch.isdigit() for ch in str(value)) and rid.startswith(("goods.", "service.")) }

    json.dump({
        "syntheticFixture": True, "quoteId": qid, "status": fresh["status"], "version": fresh["version"],
        "exportedFile": xlsx_path.name, "exportedBytes": len(data),
        "sheetNames": workbook.sheetnames,
        "previewRegionCount": customer["text"]["editable_region_count"],
        "regionsMissingFromXlsx": missing,
        "previewOnlyRegions": sorted(preview_only),
        "internalStringLeaks": leaks,
        "formulaCells": formulas,
        "internalSheetNamesInFile": [n for n in workbook.sheetnames if n != "Bao gia"],
        "definedNames": list(workbook.defined_names),
        "sampleCells": {"A5": workbook.active["A5"].value, "A11": workbook.active["A11"].value},
        # Exactly where each edited sentence landed in the file, so a reviewer can
        # open it and look — no trusting a summary.
        "whereEachEditLanded": {region_id: [f"{sheet}!{coord}" for sheet, coord, value, _kind in cells
                                            if str(text).strip() in str(value)][:3]
                                for region_id, text in {"doc.title": values["doc.title"],
                                                        "goods.row-8.name": values["goods.row-8.name"],
                                                        "col.service.name": values["col.service.name"],
                                                        "note.payment": values["note.payment"],
                                                        "notes.additional": values["notes.additional"]}.items()},
        "editedRegions": {"doc.title": values["doc.title"], "goods.row-8.name": values["goods.row-8.name"],
                          "col.service.name": values["col.service.name"], "note.payment": values["note.payment"],
                          "notes.additional": values["notes.additional"]},
        "goodsTotalRows": customer["goods_calculation"]["row_count"],
        "goodsTotalQuantity": customer["goods_calculation"]["quantity"],
        "goodsTotals": customer["goods_calculation"]["goods_totals"],
        "estimateVnd": customer["goods_calculation"]["estimate_vnd"],
        "note": "Preview text vs the exported XLSX. Every mismatch is listed, never smoothed over.",
    }, open(EVIDENCE / "xlsx-vs-preview.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    stored = dispatch("quote_source_download", {"id": qid})
    assert stored["ok"], stored
    stored_bytes = base64.b64decode(stored["document"]["downloadBase64"])
    json.dump({
        "syntheticFixture": True,
        "sourceSha256BeforeEdits": source_sha,
        "sourceSha256AfterEdits": hashlib.sha256(stored_bytes).hexdigest(),
        "byteIdentical": stored_bytes == source,
        "gridfsFileId": fresh["excel_quote"]["source"].get("storage_file_id"),
        "customerXlsxPackageEntries": sorted(ZipFile(BytesIO(data)).namelist()),
        "note": "Editing the quotation never rewrites the customer's original file.",
    }, open(EVIDENCE / "source-immutability.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    info = overview(source, proposal)
    json.dump({
        "syntheticFixture": True,
        "sheetNamesInFileOrder": info["sheet_names"],
        "sheets": [{"name": s["name"], "classification": s["classification"], "rows": s["row_count"],
                    "cols": s["column_count"], "merges": s["merged_count"], "not_rendered": s["not_rendered"]}
                   for s in info["sheets"]],
        "fidelity": info["fidelity"],
        "note": "Declared by the viewer itself. Images/charts/conditional formatting/data validation/comments/"
                "rich text/pivots/sparklines/named ranges/print settings are NOT rendered — no 100% claim.",
    }, open(EVIDENCE / "fidelity-declared.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(json.dumps({"quoteId": qid, "regionsMissingFromXlsx": missing, "internalStringLeaks": leaks,
                      "formulaCells": formulas, "sheetNames": workbook.sheetnames,
                      "sourceByteIdentical": stored_bytes == source, "xlsx": str(xlsx_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
