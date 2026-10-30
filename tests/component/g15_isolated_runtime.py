"""Isolated QA only: synthetic identities + in-memory data; NOT an authentication test."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import mongomock
from core import customer_portal as portal
from views import customer_dashboard

@st.cache_resource
def synthetic_db():
    db = mongomock.MongoClient()['disposable_g15_qa']
    db.customers.insert_many([
        {'id':'QA-LG','name':'Lục Giác QA','portal_access_email':'lg@example.test'},
        {'id':'QA-OTHER','name':'Khách khác QA','portal_access_email':'other@example.test'},
    ])
    db.shipments.insert_many([
        {'id':'QA-LOT','customer_id':'QA-LG','transport_mode':'SEA','internal_notes':'SECRET_INTERNAL','cost':987654321},
        {'id':'QA-FOREIGN','customer_id':'QA-OTHER','transport_mode':'ROAD'},
    ])
    db.public_events.insert_many([
        {'id':'QA-EVENT','version':'v1','customer_id':'QA-LG','shipment_id':'QA-LOT','stage_id':'pickup','public_title':'QA Đã lấy hàng','occurred_at':'2026-10-30T01:00:00Z','verified':True,'verified_at':'2026-10-30T02:00:00Z','visibility':'CUSTOMER','internal_notes':'SECRET_EVENT'},
        {'id':'QA-FOREIGN-EVENT','version':'v1','customer_id':'QA-OTHER','shipment_id':'QA-FOREIGN','stage_id':'pickup','public_title':'SECRET_FOREIGN_EVENT','occurred_at':'2026-10-30T01:00:00Z','verified':True,'verified_at':'2026-10-30T02:00:00Z','visibility':'CUSTOMER'},
    ])
    db.public_documents.insert_many([
        {'id':'QA-DOC','version':'v2','customer_id':'QA-LG','shipment_id':'QA-LOT','kind':'PL','public_title':'QA Packing list','status':'AVAILABLE','verified':True,'visibility':'CUSTOMER','storage_file_id':'SECRET_GRIDFS'},
        {'id':'QA-PRIVATE','version':'v1','customer_id':'QA-LG','shipment_id':'QA-LOT','kind':'PL','public_title':'SECRET_PRIVATE_DOC','status':'AVAILABLE','verified':True,'visibility':'TT'},
    ])
    return db

st.set_page_config(layout='wide')
st.warning('QA cô lập: danh tính giả lập, dữ liệu mongomock, không chứng minh OIDC thật.')
db = synthetic_db()
role = st.radio('QA identity (test only)', ['Admin','Lục Giác','Khách khác','Viewer'], horizontal=True)
if role == 'Admin':
    customer_dashboard.render_owner_portal_access_control({'role':'admin','username':'qa-admin'},db=db)
elif role == 'Viewer':
    customer_dashboard.render_owner_portal_access_control({'role':'viewer','username':'qa-viewer'},db=db)
else:
    email = 'lg@example.test' if role == 'Lục Giác' else 'other@example.test'
    principal = portal.build_customer_principal(verified_email=email,db=db)
    customer_dashboard.render_customer_dashboard(principal,db=db)
