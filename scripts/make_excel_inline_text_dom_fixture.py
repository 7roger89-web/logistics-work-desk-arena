"""Real-data fixture for the DOM acceptance of inline text editing.

LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1. Everything here is produced by the REAL
modules on the SYNTHETIC three-sheet Lục Giác-shaped workbook — the parser, the
price engine, the customer snapshot (which carries the text map) and the
read-only workbook view. Nothing is hand-written JSON, so a DOM test that mounts
the production bundle exercises the same shapes the app serves.

Usage:
  .venv/bin/python scripts/make_excel_inline_text_dom_fixture.py .tmp/dom_fixture.json
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # runnable from any cwd, like the other repo scripts
    sys.path.insert(0, str(ROOT))

from core.quote_excel_import import parse_luc_giac_workbook
from core.quote_workbook_view import overview, sheet_page
from core.quotations import calculate_quote, customer_quote_snapshot
from scripts.make_luc_giac_three_sheet_fixture import (
    SHEET_CUSTOMER,
    SHEET_INTERNAL_COST,
    build_luc_giac_three_sheet_fixture,
)

QUOTE_ID = "Q-20261016-DOMFIX1"
CUSTOMER_ID = "CUST-LUCGIAC-DOM"
CUSTOMER_NAME = "Công ty Lục Giác"


def build() -> dict:
    data = build_luc_giac_three_sheet_fixture()
    proposal = parse_luc_giac_workbook(data, "luc-giac-3sheet-SYNTHETIC.xlsx", today=date(2026, 10, 16))
    proposal["options"]["A"].update({
        "scope": "Vận chuyển Nansha → Hải Phòng, thông quan và giao tại kho khách.",
        "service_lines": [{
            "id": "fee-a", "service_name": "Vận chuyển Nansha → Hải Phòng", "qty": 1, "unit": "Lần",
            "currency": "VND", "cost_unit": 31800000, "sell_unit": 35000000, "sell_confirmed": True,
            "tax_pct": 8, "internal_note": "PRIVATE-SALE-NOTE", "public_note": "Đã gồm nâng hạ tại cảng đi",
            "cost_source": "PRIVATE-RATE-SUPPLIER",
        }],
    })
    proposal["shipment"].update({"pol": "NANSHA", "pod": "HAI PHONG", "load_model": "FCL", "equipment": "20GP",
                                 "delivery": "Thanh Trì, Hà Nội"})
    quote = calculate_quote({
        "id": QUOTE_ID, "quote_no": "BG-2026-DOMFIX1", "status": "DRAFT", "version": 1,
        "customer_id": CUSTOMER_ID, "customer_name": CUSTOMER_NAME, "customer_contact": "Nguyễn Văn A",
        "sales_owner": "staging.support", "goods_description": "Bàn họp văn phòng",
        "origin": "Trung Quốc", "destination": "Việt Nam", "route": "Nansha - Hải Phòng", "incoterm": "EXW",
        "transport_mode": "Sea", "expected_delivery_date": "2026-12-20",
        "excel_quote": proposal,
        "fx_snapshot": {"rates_to_vnd": {"CNY": 3900.0},
                        "source": "Tỷ giá do Sale xác nhận cho dự toán."},
        "service_lines": [], "created_at": "2026-10-16T08:00:00+00:00", "status_history": [],
        "is_estimate": True, "ledger_posted": False,
    })
    details = deepcopy(quote["excel_quote"])
    details["customer_text"] = {"schema": "quote-customer-text/1", "overrides": {}}
    snapshot = customer_quote_snapshot(quote)
    info = overview(data, proposal)
    page = sheet_page(data, SHEET_CUSTOMER, proposal=proposal, can_view_internal=True)
    # The same sheet as a caller WITHOUT the business grant: the DOM acceptance
    # proves an internal cost sheet is locked, never rendered for a lower role.
    locked_page = sheet_page(data, SHEET_INTERNAL_COST, proposal=proposal, can_view_internal=False)
    return {
        "synthetic": True,
        "note": "SYNTHETIC fixture — NOT the Owner's original Lục Giác workbook.",
        "customerId": CUSTOMER_ID,
        "customerName": CUSTOMER_NAME,
        "quote_id": QUOTE_ID,
        "excelQuote": details,
        "customer": snapshot,
        "textMap": snapshot["text"],
        "workbookView": {
            "read_only": True, "sha256": proposal["source"]["sha256"],
            "file_name": proposal["source"]["file_name"], "overview": info, "page": page,
            "note": "Bản xem workbook gốc chỉ để đối chiếu.",
        },
        "workbookViewInternal": {
            "read_only": True, "sha256": proposal["source"]["sha256"],
            "file_name": proposal["source"]["file_name"], "overview": info, "page": locked_page,
            "note": "Sheet nội bộ: chỉ liệt kê tên, không gửi nội dung.",
        },
    }


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".tmp/dom_fixture.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build()
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DOM_FIXTURE: {target} ({target.stat().st_size} bytes); "
          f"regions={payload['textMap']['editable_region_count']}; "
          f"sheets={payload['workbookView']['overview']['sheet_names']}")
