#!/usr/bin/env python3
"""Contract UAT proof: isolated mongomock, real dispatcher/writer/readback.
Never connect to production or pilot. Generates the production-bundle DOM inputs.
"""
import json
import pathlib
import sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import streamlit as st
    from core import database as db
    from views import logi_sandbox, logi_c1, logi_view_model as vm
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)
    session = {'seq': 0}
    seq = 0
    def dispatch(cid, **extra):
        nonlocal seq
        seq += 1
        payload = dict(id=cid, customerId='CUST-ANPHAT', requestId=f'REQ-{seq}', **extra)
        trigger = {'contract_create': dict(seq=seq, event='contract_create', payload=payload)}
        result = logi_c1.consume_c1_triggers(session, trigger)
        assert len(result) == 1
        assert result[0]['requestId'] == payload['requestId']
        assert logi_c1.consume_c1_triggers(session, trigger) == [], 'replay must not write'
        st.session_state[vm.LAST_WRITES_KEY] = result
        return result[0]
    initial = vm.build_view_model()
    ids = ['HD-01', '05/2026/HDMB', 'HD SPACE', 'HĐ-ĐÔ', 'HD%25', 'HD%2F']
    slash_outcome = None
    for cid in ids:
        with patch.object(db, 'save_contract_to_cloud', wraps=db.save_contract_to_cloud) as writer:
            out = dispatch(cid)
            assert out['ok'], out
            assert writer.call_count == 1
        if cid == ids[1]:
            slash_outcome = out
        assert logi_c1.read_contract(cid)['id'] == cid
    success = vm.build_view_model()
    assert all(any(c['id'] == cid for c in success['contracts']) for cid in ids)
    before = logi_c1.read_contract(ids[1])
    with patch.object(db, 'save_contract_to_cloud', wraps=db.save_contract_to_cloud) as writer:
        duplicate = dispatch(ids[1])
        assert not duplicate['ok'] and writer.call_count == 0
    assert logi_c1.read_contract(ids[1]) == before
    with patch('core.auth.can_edit_contract', return_value=False), patch.object(db, 'save_contract_to_cloud') as writer:
        rbac = dispatch('HD-RBAC')
        assert not rbac['ok'] and writer.call_count == 0
    with patch.object(db, 'save_contract_to_cloud') as writer:
        validation = dispatch('HD-BAD', pl_required='INVALID')
        assert not validation['ok'] and writer.call_count == 0
    with patch.object(db, 'save_contract_to_cloud', return_value=False), patch.object(db, 'get_last_db_error', return_value='Writer refused test'):
        failure = dispatch('HD-WRITER')
        assert not failure['ok'] and failure['error'] == 'Writer refused test'
    with patch.object(db, 'save_contract_to_cloud', side_effect=RuntimeError('Writer exception test')):
        exception = dispatch('HD-EXCEPTION')
        assert not exception['ok'] and 'Writer exception test' in exception['error']
    # Success state carries the slash contract's own authoritative result.
    success['lastWrites'] = [slash_outcome]
    output = dict(initial=initial, success=success, ids=ids,
                  failures=[duplicate, rbac, validation, failure, exception])
    dest = ROOT / 'tests/component/fixtures/view_model_contract_workflow.json'
    dest.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: 6 supported IDs; canonical write/readback; duplicate, RBAC, validation, writer false/exception; replay guard')


if __name__ == '__main__':
    main()
