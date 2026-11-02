"""LOGI-255-RETURN-STATE-PRESERVATION (Issue #254 / PR #255) TEST-only runtime.

Wraps the UNCHANGED app.py on the isolated mongomock staging transport (refuses
any real MONGO_URI) with AUTH_REQUIRED=true, and seeds one real Support user
(`qa.s255.support`, finance_view=True) plus one lot with real Finance Actual
lines so the /lo-hang "Công nợ dịch vụ" cluster renders real figures.

Used only to serve the app for the real-Chromium probe
(probe_09_return_state.py) on an isolated QA DB. Not part of the PR product
code path beyond this evidence directory.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ["S255_EVIDENCE_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = os.environ["S255_TEST_PASSWORD"]
assert len(PASSWORD) >= 8
assert not os.environ.get("MONGO_URI"), "LOGI-255-09 runtime refuses a real Mongo URI"
assert os.environ.get("AUTH_REQUIRED", "").lower() == "true"

import streamlit as st  # noqa: E402

st.secrets = {}

from core import auth, config, database  # noqa: E402
from core.logic import calculate_from_shipment  # noqa: E402
from core.users import build_user_document  # noqa: E402
from views import logi_sandbox  # noqa: E402

assert config.AUTH_REQUIRED is True
assert config.MONGO_URI in ("", logi_sandbox.STAGING_URI_PLACEHOLDER)
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
DB = database.get_db()
assert DB.name == "logistics_staging"
assert type(DB.client).__module__.startswith("mongomock")
assert config.ENV_IDENTITY == "PREVIEW"

USERNAME = "qa.s255.support"
if DB.users.find_one({"username": USERNAME}) is None:
    DB.users.insert_one(
        build_user_document(USERNAME, PASSWORD, "S255 Support", "support", created_by="s255.fixture")
    )

# One lot with real Finance Actual lines (VND): receivable 11,000,000,
# received 4,000,000 => outstanding 7,000,000, so the debt cluster shows
# real numbers and stays clickable.
base = copy.deepcopy(DB.shipments.find_one({"id": "LO-0308"}, {"_id": 0}))
assert base is not None
vnd_lot = copy.deepcopy(base)
vnd_lot["id"] = "LO-255-VND"
vnd_lot["customer"] = "Công ty CP Dịch Vụ 255 (VND)"
vnd_lot["currency"] = "VND"
vnd_lot["data"]["3.4"] = {
    "currency": "VND",
    "details": [
        {"id": "ACT-VND-255", "name": "Dịch vụ logistique trọn gói", "qty": 1, "price": 11_000_000, "vat": 0, "cost": 8_000_000, "currency": "VND"},
    ],
    "payments": [
        {"id": "PAY-VND-255", "amount": 4_000_000, "date": "2026-10-20", "note": "Thu đợt 1", "status": "confirmed"},
    ],
    "commission": {"total": 0},
}
DB.shipments.replace_one({"id": "LO-255-VND"}, vnd_lot, upsert=True)

assert "finance_view" in auth.ROLE_PERMISSIONS["support"], "support must hold finance_view"
truth = {
    "user": USERNAME,
    "role": "support",
    "finance_view": "finance_view" in auth.ROLE_PERMISSIONS["support"],
    "lots": sorted(s["id"] for s in DB.shipments.find({}, {"_id": 0, "id": 1})),
    "LO-255-VND": calculate_from_shipment(DB.shipments.find_one({"id": "LO-255-VND"}, {"_id": 0})),
}
(OUT / "seed-truth.json").write_text(json.dumps(truth, ensure_ascii=False, default=str, indent=2) + "\n", encoding="utf-8")

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
