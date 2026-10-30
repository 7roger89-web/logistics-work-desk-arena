"""Isolated Streamlit v2 + production customer component, fake memory only."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mongomock
import streamlit as st
from core import journey_notes as notes, inbox_attachments as inbox, customer_journey
from core.customer_portal import CustomerPrincipal, PublicationCard, CustomerDashboardView
from views import customer_portal_component as comp, journey_inline, customer_dashboard as dash

class Store:
    def __init__(self): self.files = {}; self.i = 0
    def upload_file(self, *, name, mime, data, metadata=None):
        self.i += 1
        k = f"qa-{self.i}"
        self.files[k] = bytes(data)
        return {"storage_file_id": k, "stored_name": name, "stored_size": len(data)}
    def download_file(self, file_id): return self.files[file_id]
    def delete_file(self, file_id): return self.files.pop(file_id, None) is not None

@st.cache_resource(show_spinner=False)
def fixture():
    db = mongomock.MongoClient()["journey_browser_qa"]
    db.customers.insert_one({"id":"CUST-QA","name":"QA Customer"})
    db.shipments.insert_one({"id":"QA-LOT","customer_id":"CUST-QA","transport_mode":"SEA"})
    store = Store()
    root = notes.create_stage_note(
        customer_id="CUST-QA",shipment_id="QA-LOT",stage_id="pickup",
        body="Bình luận gốc từ Trường Thành",visibility="CUSTOMER",
        actor={"kind":"user","role":"sale","username":"qa.sale"},
        db=db,gridfs=store,storage_backend="gridfs")
    assert root["ok"], root
    return db,store,root["note"]["id"]

st.set_page_config(page_title="Journey Streamlit Browser QA",layout="wide")
st.caption("QA CÔ LẬP — KHÔNG DÙNG CLOUD HAY TÀI KHOẢN THẬT")
db,store,root_id=fixture()
notes._resolve_db = lambda supplied=None: supplied if supplied is not None else db
inbox._resolve_gridfs = lambda supplied=None: supplied if supplied is not None else store
principal=CustomerPrincipal(customer_id="CUST-QA",email="qa@example.test",display_name="QA Customer")
card=PublicationCard(reference="QA-LOT",status_label="Đang xử lý",
    transport_mode="SEA",publication_version="qa-v1",
    approved_at="2026-10-30T09:00:00+00:00")
view=CustomerDashboardView(principal=principal,cards=(card,))
st.session_state["root_qa_id"]=root_id

def on_change():
    dash.handle_portal_events(st.session_state.get(comp.COMPONENT_KEY),principal,view.cards)

discussion=journey_inline.build_customer_discussion(principal,view.cards,db=db)
model=customer_journey.build_portal_model(view,discussion=discussion)
result=comp.render(model,on_change=on_change)
if dash.handle_portal_events(result,principal,view.cards):
    st.rerun()
