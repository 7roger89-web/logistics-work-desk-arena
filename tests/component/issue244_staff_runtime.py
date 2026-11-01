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
* ``LO-0310`` — a BRAND-NEW lot whose customer contract number CONTAINS
  slashes (``HDMB/2026/01``), so the Node 00 CTA must encode it as ONE route
  segment and the real contract workdesk must open for it.
* ``LO-0309`` — a BRAND-NEW lot: no profile/scope, so the Journey has no
  operational node at all (empty Journey). Its quote ``BG-0309`` is only
  ``SENT`` (linked ≠ accepted) and its contract ``HDMB-0309`` has a commercial
  agreement that records ``customer_confirmation`` only, never ``signed_contract``.

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

# Issue #244 BLOCKER 3 — the brand-new lot. It has NO mode/Incoterm and no
# operational section, so `build_journey` produces zero nodes and the shell
# renders its fresh cockpit. That is exactly the lot that must still be able to
# open Node 00 KẾ HOẠCH.
FRESH_LOT = "LO-0309"
if not db.shipments.find_one({"id": FRESH_LOT}):
    db.shipments.insert_one({
        "id": FRESH_LOT, "shipment_id": FRESH_LOT,
        "customer": "An Phát JSC", "client": "An Phát JSC",
        "customer_id": "CUST-ANPHAT",
        "contract_id": "HDMB-0309", "quote_id": "BG-0309",
        "status": "pending", "currency": "VND", "version": 0,
        "is_deleted": False, "is_archived": False,
        "created_at": "2026-10-30", "updated_at": "2026-10-30",
        "data": {
            "0.0": {}, "1.2": {}, "2.4": {}, "2.6": {}, "2.7": {},
            "3.4": {"details": [], "payments": [], "commission": {"list": [], "total": 0, "note": ""}},
            "entrustment": {"active": False},
        },
    })
# BLOCKER 1 — linked but NOT accepted (SENT): the node must never complete.
if not db.quotes.find_one({"id": "BG-0309"}):
    db.quotes.insert_one({
        "id": "BG-0309", "quote_no": "BG-0309", "customer": "An Phát JSC",
        "customer_id": "CUST-ANPHAT", "status": "SENT", "currency": "VND",
        "total": 120000000, "is_deleted": False,
    })
# BLOCKER 2 — a commercial agreement that records customer_confirmation ONLY.
# core.commercial_agreements keeps signed_contract and customer_confirmation
# apart; the panel must not turn the second one into "đã ký".
if not db.contracts.find_one({"id": "HDMB-0309"}):
    db.contracts.insert_one({
        "id": "HDMB-0309", "contract_no": "HDMB-0309",
        "customer_id": "CUST-ANPHAT", "customer": "An Phát JSC",
        "shipment_ids": [FRESH_LOT], "agent_id": "", "status": "active",
        "is_deleted": False,
    })
if not db.agreements.find_one({"agreement_id": "AGR-0309"}):
    db.agreements.insert_one({
        "id": "AGR-0309", "agreement_id": "AGR-0309", "agreement_no": "TT-0309",
        "customer_id": "CUST-ANPHAT", "customer_name": "An Phát JSC",
        "shipment_ids": [FRESH_LOT], "contract_id": "HDMB-0309",
        "status": "AGREED", "version": 2, "is_deleted": False,
        "evidence": {
            "accepted_quotation": True, "signed_contract": False,
            "customer_confirmation": True, "entrusted_documentation": False,
            "notes": "Khách xác nhận điều khoản qua email; KHÔNG phải chữ ký hợp đồng.",
        },
    })

# Issue #244 F4 — a contract number that contains "/": the Node 00 CTA must
# reach /hop-dong/<one encoded segment>, not a wildcard route.
SLASH_LOT = "LO-0310"
SLASH_CONTRACT = "HDMB/2026/01"
if not db.shipments.find_one({"id": SLASH_LOT}):
    db.shipments.insert_one({
        "id": SLASH_LOT, "shipment_id": SLASH_LOT,
        "customer": "An Phát JSC", "client": "An Phát JSC",
        "customer_id": "CUST-ANPHAT",
        "contract_id": SLASH_CONTRACT, "quote_id": "BG-0310",
        "status": "pending", "currency": "VND", "version": 0,
        "is_deleted": False, "is_archived": False,
        "created_at": "2026-10-30", "updated_at": "2026-10-30",
        "data": {
            "0.0": {"commercial_flow": {"mode": "CUSTOMER_SELF", "confirmed": True,
                                         "company_id": "", "sub_agent_id": ""}},
            "1.2": {}, "2.4": {}, "2.6": {}, "2.7": {},
            "3.4": {"details": [], "payments": [], "commission": {"list": [], "total": 0, "note": ""}},
            "entrustment": {"active": False},
        },
    })
if not db.quotes.find_one({"id": "BG-0310"}):
    db.quotes.insert_one({
        "id": "BG-0310", "quote_no": "BG-0310", "customer": "An Phát JSC",
        "customer_id": "CUST-ANPHAT", "status": "ACCEPTED", "currency": "VND",
        "total": 150000000, "is_deleted": False,
    })
if not db.contracts.find_one({"id": SLASH_CONTRACT}):
    db.contracts.insert_one({
        "id": SLASH_CONTRACT, "contract_no": SLASH_CONTRACT,
        "customer_id": "CUST-ANPHAT", "customer": "An Phát JSC",
        "shipment_ids": [SLASH_LOT], "agent_id": "", "status": "active",
        "value": 150000000, "currency": "VND", "is_deleted": False,
    })

st.set_page_config(layout="wide")
st.warning(
    "QA cô lập Issue #244: dữ liệu mongomock trong bộ nhớ, không phải production; "
    "quyền và dữ liệu khách vẫn đi qua đúng reader/allowlist của app."
)

from views.web_app import main  # noqa: E402

main()
