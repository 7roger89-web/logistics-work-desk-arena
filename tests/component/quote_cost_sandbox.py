"""TEST ONLY: run the existing app.py with three synthetic historical records.

LOGI_PR205_COST_REGRESSION=1 AUTH_REQUIRED=false .venv/bin/python -m streamlit run \
    tests/component/quote_cost_sandbox.py --server.address 0.0.0.0 --server.port 9521

Fail closed if a real Mongo URI is configured. Reuses logi_sandbox's one
in-process mongomock transport; no API, business writer or product code added.
This is not original-workbook or real-staging-Mongo acceptance evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
assert os.environ.get("LOGI_PR205_COST_REGRESSION") == "1", "Test launcher requires explicit opt-in"
assert os.environ.get("AUTH_REQUIRED", "").lower() == "false", "Isolated test session only"

from views import logi_sandbox  # noqa: E402

assert not logi_sandbox._real_uri_configured(), "BLOCKED: real Mongo URI configured; no fixture writes allowed"
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT

from core.database import get_db  # noqa: E402
from views.logi_staging_seed import _line, _shipment  # noqa: E402

DB = get_db()
assert DB.name == "logistics_staging" and type(DB.client).__module__.startswith("mongomock")
QUOTE_ID = "Q-PR205-SELL40"
IDS = ["PR205-QUOTE-SELL40", "PR205-ACTUAL-UNKNOWN", "PR205-ACTUAL-COST32"]
if not DB.quotes.find_one({"id": QUOTE_ID}):
    # A historical legacy quote: amount is SELL, never a supplier buy rate.
    DB.quotes.insert_one({"id": QUOTE_ID, "customer_id": "CUST-ANPHAT", "status": "DRAFT", "lines": [
        {"name": "SYNTHETIC quoted SELL", "amount": 40000000, "currency": "VND"},
    ]})
for sid, cost in zip(IDS, [None, None, 32000000]):
    if DB.shipments.find_one({"id": sid}):
        continue
    details = [] if sid == IDS[0] else [_line(
        "SYNTHETIC actual cost " + ("UNKNOWN" if cost is None else "32m"), "", 1, 40000000, cost,
        vat=0, unit="CONT", note="PR205 test-only historical SELL 40m; not a current supplier quotation",
    )]
    if details:
        details[0]["id"] = sid + "-LINE"
    doc = _shipment(sid=sid, customer="An Phát JSC", customer_id="CUST-ANPHAT", contract_id="",
                    status="Đang xử lý", created="15/10/2026", mode="Sea", incoterm="EXW",
                    transport={"pol": "NANSHA", "pod": "HAI PHONG"}, details=details)
    doc["quote_id"] = QUOTE_ID
    doc["created_at"] = doc["updated_at"] = datetime(2026, 10, 15, tzinfo=timezone.utc)
    DB.shipments.insert_one(doc)


def history_snapshot():
    return {"shipments": [DB.shipments.find_one({"id": sid}, {"_id": 0}) for sid in IDS],
            "quote": DB.quotes.find_one({"id": QUOTE_ID}, {"_id": 0})}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


before = logi_sandbox._state.setdefault("pr205_history_before", history_snapshot())
try:
    # The real app, with its real Streamlit React/C1 channel and backend preview.
    runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
finally:
    after = history_snapshot()
    unchanged = fingerprint(before) == fingerprint(after)
    evidence = Path(os.environ.get("PR205_EVIDENCE_DIR", ROOT / "evidence/pr205-historical-sell-buy-cost"))
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "history-integrity.json").write_text(json.dumps({
        "test_only": True, "transport": logi_sandbox.transport_name(), "database": DB.name,
        "fixture_ids": IDS, "quote_id": QUOTE_ID,
        "before_sha256": fingerprint(before), "after_sha256": fingerprint(after), "unchanged": unchanged,
        "actuals": [{"shipment_id": s["id"], "lines": s["data"]["3.4"]["details"]} for s in after["shipments"]],
        "quote_sell": after["quote"]["lines"][0]["amount"],
        "real_mongodb_staging_acceptance": "NOT_RUN", "original_workbook_acceptance": "NOT_RUN",
    }, ensure_ascii=False, indent=2) + "\n")
    assert unchanged, "Historical source data mutated during PR205 fee-selection regression"
