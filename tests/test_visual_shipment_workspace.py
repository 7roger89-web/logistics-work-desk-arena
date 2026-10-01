"""#160 scope/UNKNOWN/readback tests; isolated canonical writer + mongomock.
No production URI, no replacement workflow/finance/document store.
"""
from copy import deepcopy
import pytest
from core.shipment_execution_profile import build_execution_profile
from core.shipment_journey import normalize_sea_facts
from core.shipment_operations import compatibility_facts
from views import logi_real_data as rd, logi_sandbox, logi_view_model as vm

SCOPE = ['ORIGIN_PICKUP', 'EXPORT_HANDLING', 'EXPORT_CUSTOMS', 'ORIGIN_TERMINAL_OR_BORDER', 'MAIN_CARRIAGE', 'IMPORT_CUSTOMS', 'FINAL_DELIVERY']
IDS = ['booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in', 'etd', 'on-board', 'transit', 'arrival', 'customs-import', 'delivery']


def document(scope=None, load='FCL', mode='Sea'):
    return {'id': 'SEA-160', 'customer': 'An Phát JSC', 'customer_id': 'CUST-ANPHAT', 'status': 'wait', 'currency': 'VND',
        'version': 1, 'updated_by': 'last-writer-not-owner', 'data': {
        '0.0': {'mode': mode, 'incoterm': 'FOB' if mode == 'Sea' else 'FCA', 'execution_profile': {
            'incoterm_version': '2020', 'incoterm_named_place': 'Hai Phong', 'load_model': load,
            'service_scope': SCOPE if scope is None else scope, 'service_scope_confirmed': True,
            'cargo_insurance': {'status': 'NO'}}},
        '1.2': {'transport_legs': [
            {'id': 'pickup-160', 'sequence': 1, 'mode': 'Truck', 'origin': 'Factory', 'destination': 'Hai Phong', 'etd': '2026-10-01', 'atd': '', 'ata': '', 'units': [{'id': 'truck-160', 'kind': 'truck', 'number': '29A', 'type_size': '10T'}]},
            {'id': 'sea-160', 'sequence': 2, 'mode': mode, 'origin': 'Hai Phong', 'destination': 'Singapore', 'booking_no': 'BK-160', 'carrier': 'Carrier', 'vessel': 'Vessel', 'mbl': 'MBL-160', 'etd': '2000-01-01', 'eta': '2000-01-03', 'atd': '', 'ata': '', 'units': [{'id': 'cont-160', 'kind': 'container', 'number': 'ABCD1234567', 'type_size': '40HC'}] if mode == 'Sea' else []}]},
        '2.4': {}, '2.6': {}, '2.7': {}, '3.4': {'details': [], 'payments': []}, 'entrustment': {'active': False}}}


def project(doc, **kwargs):
    return rd.shipment_projection(doc, ledger={}, agents={}, attachments={}, docgen_documents={}, linked_contracts={}, **kwargs)


def nodes(row): return {n['id']: n for n in row['journey']['nodes']}


def test_detailed_sea_export_and_parallel_dependencies():
    row = project(document())
    assert [n['id'] for n in row['journey']['nodes']] == IDS
    assert nodes(row)['etd']['dependencies'] == ['si-vgm', 'gate-in']
    assert nodes(row)['si-vgm']['dependencies'] == ['customs-export']
    assert nodes(row)['gate-in']['dependencies'] == ['customs-export']
    assert row['journey']['primaryAction']['text'] == row['nextAction']
    assert row['journey']['primaryAction']['route'] == row['nextRoute']


@pytest.mark.parametrize('scope,absent', [
    (['MAIN_CARRIAGE'], ['pickup', 'customs-export', 'gate-in', 'customs-import', 'delivery']),
    (['IMPORT_CUSTOMS', 'FINAL_DELIVERY'], ['pickup', 'customs-export', 'si-vgm', 'gate-in']),
    ([], ['pickup', 'customs-export', 'si-vgm', 'gate-in', 'customs-import', 'delivery'])])
def test_scope_gates_owned_work_and_keeps_carriage_facts_reference_only(scope, absent):
    row = project(document(scope=scope))
    assert not (set(absent) & nodes(row).keys())
    assert nodes(row)['booking']['owned'] is ('MAIN_CARRIAGE' in scope)


def test_lcl_and_nonsea_do_not_get_container_gatein_or_detailed_sea():
    assert 'gate-in' not in nodes(project(document(load='LCL')))
    assert 'booking' not in nodes(project(document(mode='Air', load='')))


def test_past_schedule_scope_config_and_declaration_are_not_occurrence():
    doc = document(); doc['china_export_decl_no'] = 'EXP-001'
    row = project(doc)
    assert row['journey']['currentStageId'] == ''
    for id in ('pickup', 'customs-export', 'etd', 'on-board', 'transit', 'arrival'):
        assert nodes(row)[id]['state'] != 'COMPLETED'
    assert nodes(row)['customs-export']['factState'] == 'KNOWN'
    assert nodes(row)['on-board']['factState'] == 'UNKNOWN'


def test_actual_main_sea_leg_controls_position_not_pickup_departure():
    doc = document();doc['data']['1.2']['transport_legs'][0]['atd'] = '2026-10-01'
    assert project(doc)['journey']['currentStageId'] == ''
    doc['data']['1.2']['transport_legs'][1]['atd'] = '2026-10-02'
    row = project(doc)
    assert row['journey']['currentStageId'] == 'transit'
    assert nodes(row)['si-vgm']['state'] != 'COMPLETED'
    assert nodes(row)['gate-in']['state'] != 'COMPLETED'
    doc['data']['1.2']['transport_legs'][1]['ata'] = '2026-10-05'
    assert project(doc)['journey']['currentStageId'] == 'arrival'


def test_primary_critical_and_profile_anchor_remain_authoritative():
    doc = document()
    critical = {'next_action': {'label': 'Critical existing action'}, 'top_alert': {'severity': 'critical'}}
    row = project(doc, dashboard=critical)
    assert row['nextAction'] == 'Critical existing action'
    doc['data']['0.0']['execution_profile']['incoterm_named_place'] = ''
    row = project(doc)
    assert '#shipment-execution-profile' in row['nextRoute']


def test_owner_is_authoritative_dashboard_owner_never_last_writer():
    row = project(document(), dashboard={'owner': 'Owner canonical'})
    assert row['journey']['owner'] == 'Owner canonical'
    assert row['support'] == 'last-writer-not-owner'
    assert project(document())['journey']['owner'] == ''


def test_same_attachment_id_can_belong_to_multiple_nodes_and_upload_is_not_submission():
    doc = document()
    records = [{'id': 'ATT-1', 'original_name': 'bill.pdf', 'category': 'transport'}, {'id': 'ATT-VGM', 'original_name': 'vgm.pdf', 'category': 'vgm'}]
    row = rd.shipment_projection(doc, attachments={'SEA-160': records}, ledger={}, agents={}, docgen_documents={}, linked_contracts={})
    assert len(row['attachments']) == 2
    assert 'ATT-1' in nodes(row)['booking']['documentIds']
    assert 'ATT-1' in nodes(row)['on-board']['documentIds']
    assert nodes(row)['si-vgm']['documentIds'] == ['ATT-VGM']
    assert nodes(row)['si-vgm']['state'] != 'COMPLETED'
    assert row['journey']['seaFacts']['vgm_status'] == 'UNKNOWN'


@pytest.mark.parametrize('fields', [{'si_status': 'DONE'}, {'gate_in_at': 'garbage'}, {'status': 'done'}, {'si_cutoff': '2026-13-35'}])
def test_invalid_or_generic_fields_refused(fields):
    with pytest.raises(ValueError): normalize_sea_facts(fields)


@pytest.fixture
def staging():
    import streamlit as st
    from core.database import save_shipment_atomic
    logi_sandbox.reset_backend(); assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)
    doc = document(scope=SCOPE[:5]);doc.pop('version')
    assert save_shipment_atomic(doc, actor='issue160-fixture')
    yield
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR);logi_sandbox.reset_backend()


def event(name, payload):
    return vm.consume_phase_b_triggers({'seq': 0}, {name: {'seq': 1, 'payload': payload}})[0]


def write(fields, version=None):
    return event('shipment_sea_facts_save', {'shipmentId': 'SEA-160', 'requestId': 'SEA-TEST-160',
        'expectedVersion': vm.read_shipment('SEA-160')['version'] if version is None else version, 'fields': fields})


def test_real_dispatch_atomic_readback_changes_nodes_panel_primary_without_duplicate_stores(staging):
    before = vm.read_shipment('SEA-160'); finance = deepcopy(before['data']['3.4'])
    first = write({'si_status': 'ACCEPTED', 'vgm_status': 'RECEIVED'})
    assert first['ok'], first
    assert first['readback']['journey']['seaFacts']['vgm_status'] == 'RECEIVED'
    assert nodes(first['readback'])['si-vgm']['blockers'] == [first['readback']['nextAction']]
    assert nodes(first['readback'])['si-vgm']['state'] != 'COMPLETED'
    second = write({'vgm_status': 'ACCEPTED'})
    assert second['ok'] and second['requestId'] == 'SEA-TEST-160'
    fresh = vm.read_shipment('SEA-160')
    row = second['readback']; assert nodes(row)['si-vgm']['state'] == 'COMPLETED'
    assert nodes(row)['si-vgm']['blockers'] == []
    assert 'gate-in' in row['nextAction']
    assert nodes(row)['gate-in']['blockers'] == [row['nextAction']]
    assert row['nextAction'] == row['journey']['primaryAction']['text']
    assert fresh['data']['3.4'] == finance
    assert 'stages' not in fresh and 'journey' not in fresh
    assert second['audit']
    clear = write({'vgm_status': '', 'vgm_cutoff': ''})
    assert clear['ok']
    assert nodes(clear['readback'])['si-vgm']['state'] != 'COMPLETED'
    assert clear['persisted']['vgm_status'] == 'UNKNOWN'


def test_stale_version_malicious_payment_and_out_of_scope_fact_refused(staging):
    before = vm.read_shipment('SEA-160')
    for fields, version in [({'vgm_status': 'ACCEPTED'}, -1), ({'payments': []}, before['version'])]:
        result = write(fields, version)
        assert not result['ok']; assert vm.read_shipment('SEA-160') == before
    from core.database import save_shipment_atomic
    doc = vm.read_shipment('SEA-160'); doc['data']['0.0']['execution_profile']['service_scope'] = ['IMPORT_CUSTOMS']
    assert save_shipment_atomic(doc, expected_version=doc['version'], actor='fixture')
    assert not write({'vgm_status': 'ACCEPTED'})['ok']
    assert not write({'gate_in_at': '2026-10-01T16:00'})['ok']


def test_viewer_refusal_and_support_actual_permissions(staging):
    import streamlit as st
    before = vm.read_shipment('SEA-160')
    st.session_state['current_user'] = {'username': 'viewer-160', 'role': 'viewer', 'active': True}
    result = write({'vgm_status': 'ACCEPTED'})
    assert not result['ok'] and 'RBAC' in result['error']; assert vm.read_shipment('SEA-160') == before
    st.session_state['current_user'] = {'username': 'support-160', 'role': 'support', 'active': True}
    assert write({'vgm_status': 'RECEIVED'})['ok']
    result = event('finance_actual_save', {'shipmentId': 'SEA-160', 'requestId': 'COST-160', 'line': {
        'name': 'Handling', 'qty': '1', 'price': '200', 'cost': '100', 'vat': '0', 'journeyStage': 'gate-in'}})
    assert result['ok'], result
    line = result['readback']['finance']['actual'][0]
    assert line['journeyStage'] == 'gate-in'
    assert result['readback']['finance']['payable'] == 100
    count = result['persisted']['lineCount']
    result = event('finance_actual_save', {'shipmentId': 'SEA-160', 'requestId': 'COST-161', 'line': {
        'id': line['id'], 'name': 'Handling', 'qty': '1', 'price': '200', 'cost': '100', 'vat': '0'}})
    assert result['ok'] and result['persisted']['lineCount'] == count
    assert result['readback']['finance']['actual'][0]['journeyStage'] == 'gate-in'


def test_export_decl_reuses_root_fact_not_new_customs_state(staging):
    result = write({'export_declaration_no': 'EXP-160'})
    assert result['ok'], result
    assert vm.read_shipment('SEA-160')['china_export_decl_no'] == 'EXP-160'
    assert 'export_declaration_no' not in result['persisted']
    assert nodes(result['readback'])['customs-export']['state'] != 'COMPLETED'


def test_unexpected_read_failure_remains_correlated_for_ui_refusal(staging, monkeypatch):
    def unavailable(_sid): raise RuntimeError('isolated read failure')
    monkeypatch.setattr(vm, 'read_shipment', unavailable)
    result = write({'si_status': 'ACCEPTED'}, version=1)
    assert not result['ok']
    assert result['requestId'] == 'SEA-TEST-160'
    assert 'isolated read failure' in result['error']
