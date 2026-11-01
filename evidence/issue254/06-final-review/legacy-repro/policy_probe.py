"""Probe: costIntelligence.rates delivered to role `sale` (no finance_view)."""
import json, os, sys
sys.path.insert(0, os.getcwd())
import streamlit as st
from core import auth, database
from core.users import build_user_document, public_identity
from views import logi_sandbox, logi_view_model as vm

logi_sandbox.reset_backend(); assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
st.session_state.clear(); st.rerun = lambda: None
db = database.get_db()
doc = build_user_document("qa.review.policy", "review-only-password", "Review Policy", "support", created_by="review")
db.users.replace_one({"username": "qa.review.policy"}, doc, upsert=True)
st.session_state["current_user"] = public_identity(doc)

payload = {"requestId": "COST-POLICY-1", "supplier": "Hang tau POLICY",
           "rawText": "SHANGHAI -> HANOI 4250 USD/40HC", "status": "ACTIVE",
           "rows": [{"id": "l1", "kind": "OCEAN_FREIGHT", "status": "QUOTED", "amount": 4250.0,
                     "currency": "USD", "unit": "40HC", "carrier": {"id": "C1", "name": "Hang tau POLICY", "state": "CONFIRMED"},
                     "origin": {"id": "SHA", "name": "Shanghai", "state": "UNKNOWN"},
                     "destination": {"id": "HAN", "name": "Hanoi", "state": "UNKNOWN"},
                     "rawLine": "SHANGHAI -> HANOI 4250 USD/40HC", "confidence": "CONFIRMED"}]}
out = vm.dispatch({"cost_rate_save": {"seq": 1, "event": "cost_rate_save", "payload": payload}})
print("cost_rate_save ok =", out[0]["ok"])

db.users.update_one({"username": "qa.review.policy"}, {"$set": {"role": "sale"}})
fresh = auth.fresh_session_identity_for_action()
print("fresh role =", fresh["role"], "| finance_view =", auth.has_permission("finance_view"))
model = vm.build_view_model()
print("sale canViewFinance =", model["user"]["canViewFinance"])
print("sale lastWrites count =", len(model["lastWrites"]))
rates = model["costIntelligence"]["rates"]
print("sale costIntelligence.rates count =", len(rates))
for r in rates[:3]:
    rows = r.get("rows") or []
    print("  id=", r.get("id"), "| created_by=", r.get("created_by"),
          "| supplier=", r.get("supplier"),
          "| amounts=", [(x.get("amount"), x.get("currency")) for x in rows])
