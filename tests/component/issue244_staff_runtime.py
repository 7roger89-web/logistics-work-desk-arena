"""Issue #244 QA runtime — the REAL internal shell on isolated staging data.

This is a browser-QA launcher, not application code: it seeds the existing
``mongomock`` staging transport with the plan facts Issue #244 must render
(quote link, an unclassified receipt, a confirmed import form) and then runs the
UNCHANGED ``views.web_app.main``. No production database, no new server, no new
route, no write authority beyond the isolated staging transport.

The seeded facts are the ones the acceptance asks for:

* ``LO-0306`` — quote ``BG-0306`` linked by exact ``quote_id`` while the same
  customer also owns ``BG-9999`` (must never render), a TT↔sub-agent contract
  ``HDMB-SUB-0306`` (must never be reported as the customer contract), a
  confirmed ``TT_ENTRUSTED_DIRECT`` import form and ONE unclassified receipt
  (must stay "cần đối soát", never "đã nhận tiền hàng").
* ``LO-0307`` — no quote, confirmed ``CUSTOMER_SELF`` flow.
* ``LO-0308`` — nothing confirmed at all (UNKNOWN import form).

Run:  streamlit run tests/component/issue244_staff_runtime.py --server.port 9501
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from views import logi_sandbox  # noqa: E402

transport = logi_sandbox.ensure_backend()
assert transport == logi_sandbox.SANDBOX_TRANSPORT, "QA runtime must stay on isolated staging"

from core.database import get_db  # noqa: E402

db = get_db()

# Issue #244 — the plan facts. Only the isolated staging transport is touched.
def _patch_shipment(shipment_id: str, *, quote_id: str | None = None,
                    flow: dict | None = None, payments: list | None = None,
                    clear_flow: bool = False) -> None:
    """Patch the canonical document through whole-subdocument writes.

    ``data["0.0"]`` contains a literal dot, so a dotted ``$set`` path would be
    read by Mongo as nested keys — the whole section is rewritten instead.
    """
    doc = db.shipments.find_one({"id": shipment_id}) or {}
    data = dict(doc.get("data") or {})
    head = dict(data.get("0.0") or {})
    if clear_flow:
        head.pop("commercial_flow", None)
    if flow is not None:
        head["commercial_flow"] = flow
    data["0.0"] = head
    if payments is not None:
        money = dict(data.get("3.4") or {})
        money["payments"] = payments
        data["3.4"] = money
    update: dict = {"data": data}
    if quote_id is not None:
        update["quote_id"] = quote_id
    db.shipments.update_one({"id": shipment_id}, {"$set": update})


_patch_shipment(
    "LO-0306",
    quote_id="BG-0306",
    flow={"mode": "TT_ENTRUSTED_DIRECT", "confirmed": True,
          "company_id": "TT-COMPANY", "sub_agent_id": ""},
    payments=[{"id": "P-244-QA", "amount": 20000000,
               "note": "Khoản thu chưa phân loại", "date": "2026-10-20",
               "created_by": "qa.staging"}],
)
db.contracts.update_one(
    {"id": "HDMB-0306"},
    {"$set": {"shipment_ids": ["LO-0306"], "agent_id": ""}},
)
# Two quotes for the SAME customer: only the lot's exact quote_id may render.
if not db.quotes.find_one({"id": "BG-9999"}):
    db.quotes.insert_one({
        "id": "BG-9999", "quote_no": "BG-9999", "customer_id": "CUST-ANPHAT",
        "customer": "An Phát JSC", "status": "ACCEPTED", "currency": "VND",
        "total": 999000000, "is_deleted": False,
    })
# A TT↔sub-agent purchase contract linked to the same lot: a DIFFERENT instrument.
if not db.contracts.find_one({"id": "HDMB-SUB-0306"}):
    db.contracts.insert_one({
        "id": "HDMB-SUB-0306", "contract_no": "HDMB-SUB-0306",
        "contract_no_display": "HDMB-SUB-0306/2026",
        "shipment_ids": ["LO-0306"], "agent_id": "AGT-PHUANH",
        "company_id": "TT-COMPANY", "status": "active", "is_deleted": False,
    })

_patch_shipment(
    "LO-0307", quote_id="",
    flow={"mode": "CUSTOMER_SELF", "confirmed": True,
          "company_id": "", "sub_agent_id": ""},
)
_patch_shipment("LO-0308", quote_id="", clear_flow=True)

st.set_page_config(layout="wide")
st.warning(
    "QA cô lập Issue #244: dữ liệu mongomock trong bộ nhớ, không phải production; "
    "quyền và dữ liệu khách vẫn đi qua đúng reader/allowlist của app."
)

from views.web_app import main  # noqa: E402

main()
