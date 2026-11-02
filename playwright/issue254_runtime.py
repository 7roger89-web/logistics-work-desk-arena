"""Issue #254 TEST-only runtime observer wrapping unchanged app.py.

Runs with Streamlit + AUTH_REQUIRED=true + isolated mongomock staging (refuses
any real MONGO_URI). Seeds two real users (`qa.s254.support`, `qa.s254.sale`)
and deterministic multi-currency + quote-only shipments so real Chromium 153
can verify:
  1. Support (`finance_view=True`) seeing compact `Phải thu / Đã thu / Còn phải thu`
     at 1440x900 desktop + 390x844 mobile without horizontal overflow;
  2. Quote-only lot (`LO-254-QUOTE`) keeping `Phải thu` & `Còn phải thu` = `—`;
  3. Multi-currency (`VND`, `USD`, `CNY`) without FX conversion;
  4. Real UI payment record + payment reversal updating `/lo-hang`;
  5. Sale (`finance_view=False`) receiving zero finance money fields in the
     server payload (`sale-payload.json`) and seeing zero finance clusters in UI.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ["S254_EVIDENCE_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = os.environ["S254_TEST_PASSWORD"]
assert len(PASSWORD) >= 8
assert not os.environ.get("MONGO_URI"), "Issue #254 test runtime refuses a real Mongo URI"
assert os.environ.get("AUTH_REQUIRED", "").lower() == "true"

import streamlit as st  # noqa: E402
st.secrets = {}

from core import auth, config, database  # noqa: E402
from core.logic import calculate_from_shipment  # noqa: E402
from core.users import build_user_document  # noqa: E402
from views import logi_sandbox, logi_view_model as vm  # noqa: E402

assert config.AUTH_REQUIRED is True
assert config.MONGO_URI in ("", logi_sandbox.STAGING_URI_PLACEHOLDER)
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
DB = database.get_db()
assert DB.name == "logistics_staging"
assert type(DB.client).__module__.startswith("mongomock")
assert config.ENV_IDENTITY == "PREVIEW"

if not hasattr(vm, "_s254_observed_build"):
    for username, role in (("qa.s254.support", "support"), ("qa.s254.sale", "sale")):
        if DB.users.find_one({"username": username}) is None:
            DB.users.insert_one(
                build_user_document(username, PASSWORD, f"S254 {role.upper()}", role, created_by="s254.fixture")
            )

    base = copy.deepcopy(DB.shipments.find_one({"id": "LO-0308"}, {"_id": 0}))
    assert base is not None

    # 1. Quote-only lot: positive linked quote 28,450,000 VND, empty Finance Actual
    DB.quotes.replace_one(
        {"id": "BG-254-QUOTE-ONLY"},
        {
            "id": "BG-254-QUOTE-ONLY",
            "quote_no": "BG-254-QUOTE-ONLY",
            "customer_id": base.get("customer_id", "CUST-ANPHAT"),
            "status": "ACCEPTED",
            "currency": "VND",
            "lines": [
                {"name": "Cước vận chuyển trọn gói", "qty": 1, "amount": 28_450_000, "currency": "VND", "vat": 0},
            ],
        },
        upsert=True,
    )
    quote_lot = copy.deepcopy(base)
    quote_lot["id"] = "LO-254-QUOTE"
    quote_lot["customer"] = "Công ty CP Minh Long (Chỉ báo giá)"
    quote_lot["quote_id"] = "BG-254-QUOTE-ONLY"
    quote_lot["currency"] = "VND"
    quote_lot["data"]["3.4"] = {"currency": "VND", "details": [], "payments": [], "commission": {"total": 0}}
    DB.shipments.replace_one({"id": "LO-254-QUOTE"}, quote_lot, upsert=True)

    # 2. USD lot: receivable 2,400 USD, received 900 USD, outstanding 1,500 USD
    usd_lot = copy.deepcopy(base)
    usd_lot["id"] = "LO-254-USD"
    usd_lot["customer"] = "Global Tech Trading (USD)"
    usd_lot["currency"] = "USD"
    usd_lot["data"]["3.4"] = {
        "currency": "USD",
        "details": [
            {"id": "ACT-USD-254", "name": "Ocean Freight", "qty": 1, "price": 2400, "vat": 0, "cost": 1950, "currency": "USD"},
        ],
        "payments": [
            {"id": "PAY-USD-254", "amount": 900, "date": "2026-10-18", "note": "Thu đợt 1 USD", "status": "confirmed"},
        ],
        "commission": {"total": 0},
    }
    DB.shipments.replace_one({"id": "LO-254-USD"}, usd_lot, upsert=True)

    # 3. CNY lot: receivable 18,000 CNY, received 18,000 CNY, outstanding 0 CNY (with 1 reversed receipt)
    cny_lot = copy.deepcopy(base)
    cny_lot["id"] = "LO-254-CNY"
    cny_lot["customer"] = "Thâm Quyến Hưng Phát (CNY)"
    cny_lot["currency"] = "CNY"
    cny_lot["data"]["3.4"] = {
        "currency": "CNY",
        "details": [
            {"id": "ACT-CNY-254", "name": "Trucking nội địa TQ", "qty": 1, "price": 18000, "vat": 0, "cost": 14000, "currency": "CNY"},
        ],
        "payments": [
            {"id": "PAY-CNY-REV", "amount": 5000, "date": "2026-10-10", "note": "Phiếu hủy", "status": "reversed", "is_reversed": True},
            {"id": "PAY-CNY-OK", "amount": 18000, "date": "2026-10-19", "note": "Thu đủ CNY", "status": "confirmed"},
        ],
        "commission": {"total": 0},
    }
    DB.shipments.replace_one({"id": "LO-254-CNY"}, cny_lot, upsert=True)

    def write_json(name: str, value: object) -> None:
        raw = json.dumps(value, ensure_ascii=False, default=str, indent=2) + "\n"
        tmp = OUT / (name + ".tmp")
        tmp.write_text(raw, encoding="utf-8")
        tmp.replace(OUT / name)

    lo0308_calc = calculate_from_shipment(DB.shipments.find_one({"id": "LO-0308"}, {"_id": 0}))
    write_json("seed-truth.json", {
        "LO-0308": lo0308_calc,
        "LO-254-QUOTE": {"hasActualLines": False, "quoteAmount": 28450000, "receivable": None, "received": 0.0, "outstanding": None},
        "LO-254-USD": {"currency": "USD", "receivable": 2400.0, "received": 900.0, "outstanding": 1500.0},
        "LO-254-CNY": {"currency": "CNY", "receivable": 18000.0, "received": 18000.0, "outstanding": 0.0},
    })

    ORIGINAL_BUILD = vm.build_view_model

    def observed_build():
        model = ORIGINAL_BUILD()
        user = auth.current_user() or {}
        role_slug = str(user.get("role") or "anon").lower()
        summary = {
            "observed_ns": time.time_ns(),
            "user": model.get("user"),
            "finance_view_permission": auth.has_permission("finance_view"),
            "home_outstanding_total": (model.get("home") or {}).get("outstandingTotal"),
            "home_outstanding_count": (model.get("home") or {}).get("outstandingCount"),
            "receivables_count": len((model.get("receivables") or {}).get("rows") or []),
            "payables_count": len((model.get("payables") or {}).get("rows") or []),
            "reconciliation_count": len((model.get("reconciliation") or {}).get("rows") or []),
            "shipments_finance": {
                row["id"]: row.get("finance")
                for row in (model.get("shipments") or [])
                if row.get("id") in {"LO-0308", "LO-254-QUOTE", "LO-254-USD", "LO-254-CNY"}
            },
        }
        write_json(f"payload-{role_slug}.json", summary)
        return model

    vm.build_view_model = observed_build
    vm._s254_observed_build = observed_build

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
