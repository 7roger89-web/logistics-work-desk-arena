"""Isolated real Streamlit QA host. Run with AUTH_REQUIRED=true, no Mongo URI, and QA_TEST_PASSWORD set. Seeds disposable mongomock users; adds native QA-only transient projection/role controls. Production files are unchanged."""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import streamlit as st
# Test-process-only secret source isolation. Never read or edit host secrets.
# Caller must clear MONGO_URI; inherited real Mongo config is refused.
st.secrets = {}
from core import config
assert config.MONGO_URI in ('', 'mongodb://mongomock.local/logistics_staging'), 'QA refuses any real Mongo URI'
from views import logi_sandbox
assert logi_sandbox.ensure_backend() == 'SANDBOX_STAGING'
from core import database
db = database.get_db()
assert db.name == 'logistics_staging'
assert type(db.client).__module__.startswith('mongomock')
assert config.ENV_IDENTITY == 'PREVIEW'
if st.session_state.get('current_user', {}).get('username') == 'staging.support':
    st.session_state.pop('current_user', None)
from core.users import build_user_document
if db.users.find_one({'username': 'qa.admin'}) is None:
    db.users.insert_one(build_user_document('qa.admin', os.environ['QA_TEST_PASSWORD'], 'QA Admin', 'admin'))
from views import logi_view_model as vm
if not hasattr(vm, '_qa_original_build'):
    vm._qa_original_build = vm.build_view_model
def qa_build():
    model = vm._qa_original_build()
    state = st.session_state.get('qa_state', 'normal')
    if state == 'absent':
        model['shipments'] = [s for s in model['shipments'] if s['id'] != 'LO-0306']
    elif state in ('journey-ready', 'journey-empty'):
        fixture = json.loads((ROOT / 'tests/component/fixtures/view_model_journey_fresh_188.json').read_text(encoding='utf-8'))
        donor = next(s for s in fixture['before']['shipments'] if s['id'] == 'LO-0306')
        for s in model['shipments']:
            if s['id'] == 'LO-0306':
                s['journey'] = donor['journey'] if state == 'journey-ready' else {'nodes': [], 'modules': []}
    evidence = {'head': __import__('subprocess').check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'transport': logi_sandbox.transport_name(), 'db': db.name, 'state': state, 'shipments': list(db.shipments.find({}, {'_id': 0})), 'lastWrites': model.get('lastWrites', [])}
    (ROOT / '.tmp/react310-readback.json').write_text(json.dumps(evidence, default=str, ensure_ascii=False), encoding='utf-8')
    return model
vm.build_view_model = qa_build
from views.web_app import main
main()
if st.session_state.get('current_user', {}).get('role') == 'admin':
    st.selectbox('QA transient projection state', ['normal', 'absent', 'journey-ready', 'journey-empty'], key='qa_state')
    def revoke():
        assert db.name == 'logistics_staging' and type(db.client).__module__.startswith('mongomock')
        db.users.update_one({'username': 'qa.admin'}, {'$set': {'role': 'viewer'}})
    st.checkbox('QA downgrade test account to viewer', on_change=revoke)
