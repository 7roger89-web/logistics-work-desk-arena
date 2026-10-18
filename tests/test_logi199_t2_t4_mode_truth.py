"""LOGI-199 T2 (SEA LCL), T3 (AIR), T4 (ROAD FTL/LTL) — mode-correct evidence.

Same projection (`core.shipment_journey`) and same canonical writer
(`shipment_sea_facts_save`, RBAC + expectedVersion + readback). AIR/ROAD facts
live in `data.1.2.air_facts` / `data.1.2.road_facts`; no sea field completes an
air/road node, and choosing LCL/LTL never means consolidation happened.
"""
from copy import deepcopy

import pytest

from core.shipment_execution_profile import build_execution_profile
from core.shipment_journey import normalize_mode_facts
from tests.test_visual_shipment_workspace import document, event, nodes, project


def stage(doc, code):
    return next(s for s in build_execution_profile(doc)['stages'] if s['code'] == code)


# =========================================================================== T2 SEA LCL

def lcl_doc(scope=None):
    doc = document(load='LCL', scope=scope)
    doc['data']['1.2']['transport_legs'][1]['units'] = []
    return doc


def test_lcl_selected_is_not_consolidated_and_no_fcl_container_work():
    doc = lcl_doc()
    row = project(doc)
    ids = [n['id'] for n in row['journey']['nodes']]
    assert 'gate-in' not in ids and 'cfs-receipt' in ids
    assert stage(doc, 'SEA_CONSOLIDATION')['done'] is False
    assert stage(doc, 'SEA_CONSOLIDATION')['missing'] == ''   # no invented next action
    si = nodes(row)['si-vgm']
    assert si['label'] == 'SI' and [f['key'] for f in si['factFields']] == ['si_status', 'si_cutoff']
    assert 'VGM' not in row['nextAction']
    assert nodes(row)['cfs-receipt']['completed'] is False


def test_lcl_cfs_receipt_alone_does_not_complete_and_blank_quantity_stays_unknown():
    doc = lcl_doc()
    doc['data']['1.2']['sea_export'] = {'cfs_received_at': '2026-10-01', 'cfs_package_count': '12', 'cfs_cbm': '3.5'}
    node = nodes(project(doc))['cfs-receipt']
    assert node['completed'] is False
    assert '12 kiện' in node['evidence'] and '3.5 CBM' in node['evidence'] and ' kg' not in node['evidence']
    doc['data']['1.2']['sea_export']['consolidated_at'] = '2026-10-02'
    assert nodes(project(doc))['cfs-receipt']['completed'] is True
    assert stage(doc, 'SEA_CONSOLIDATION')['done'] is True


def test_lcl_delivery_has_deconsolidation_and_no_empty_return():
    keys = [f['key'] for f in nodes(project(lcl_doc()))['delivery']['factFields']]
    assert keys == ['deconsolidated_at', 'do_released_at', 'pod_received_at']


@pytest.mark.parametrize('fields', [{'cfs_package_count': '-1'}, {'cfs_package_count': '1.5'},
                                    {'cfs_cbm': 'abc'}, {'cfs_weight_kg': 'nan'}])
def test_lcl_quantities_validated(fields):
    with pytest.raises(ValueError):
        normalize_mode_facts(fields, 'SEA')


def test_blank_quantity_is_unknown_not_zero():
    assert normalize_mode_facts({'cfs_package_count': ''}, 'SEA') == {'cfs_package_count': ''}
    assert normalize_mode_facts({'cfs_weight_kg': '1,250.50'}, 'SEA') == {'cfs_weight_kg': '1250.5'}


# =========================================================================== T3 AIR

AIR_SCOPE = ['EXPORT_HANDLING', 'EXPORT_CUSTOMS', 'MAIN_CARRIAGE', 'IMPORT_CUSTOMS', 'FINAL_DELIVERY']


def air_doc(legs=None):
    doc = document(mode='Air', load='DIRECT', scope=AIR_SCOPE)
    doc['data']['0.0']['incoterm'] = 'FCA'
    doc['data']['1.2']['transport_legs'] = legs or [
        {'id': 'air-1', 'sequence': 1, 'mode': 'Air', 'origin': 'HAN', 'destination': 'FRA', 'carrier': 'VN',
         'mawb': '738-12345675', 'hawb': 'TT-H1', 'flight_no': 'VN37', 'etd': '2026-10-10', 'atd': '', 'eta': '', 'ata': '', 'units': []}]
    return doc


def test_air_chain_uses_awb_flight_and_never_sea_nodes():
    row = project(air_doc())
    ids = [n['id'] for n in row['journey']['nodes']]
    assert {'air-booking', 'air-acceptance', 'uplift', 'air-arrival'} <= set(ids)
    assert not ({'booking', 'si-vgm', 'gate-in', 'on-board', 'cfs-receipt', 'AIR_DOCUMENTS'} & set(ids))
    assert nodes(row)['air-booking']['completed'] is True
    assert 'MAWB 738-12345675' in nodes(row)['air-booking']['evidence']
    assert set(row['journey']['seaFacts']) >= {'air_uplifted_at'} and 'si_status' not in row['journey']['seaFacts']


def test_air_sea_facts_cannot_complete_air_nodes():
    doc = air_doc()
    doc['data']['1.2']['transport_legs'][0]['flight_no'] = ''
    doc['data']['1.2']['sea_export'] = {'on_board_at': '2026-10-10', 'booking_status': 'CONFIRMED', 'gate_in_at': '2026-10-09'}
    row = project(doc)
    assert nodes(row)['air-booking']['completed'] is False
    assert nodes(row)['uplift']['completed'] is False


def test_flight_atd_is_not_uplift_and_ata_marks_arrival():
    doc = air_doc(); leg = doc['data']['1.2']['transport_legs'][0]
    leg['atd'] = '2026-10-10'
    row = project(doc)
    assert nodes(row)['uplift']['completed'] is False and 'ATD: 2026-10-10' in nodes(row)['uplift']['evidence']
    doc['data']['1.2']['air_facts'] = {'air_uplifted_at': '2026-10-10T23:40', 'air_acceptance_at': '2026-10-09'}
    leg['ata'] = '2026-10-11'
    row = project(doc)
    assert nodes(row)['uplift']['completed'] is True
    assert nodes(row)['air-acceptance']['completed'] is True
    assert row['journey']['currentStageId'] == 'air-arrival'


def test_air_transit_only_with_connecting_leg():
    legs = [
        {'id': 'a1', 'sequence': 1, 'mode': 'Air', 'origin': 'HAN', 'destination': 'DOH', 'mawb': '157-1', 'flight_no': 'QR977', 'units': []},
        {'id': 'a2', 'sequence': 2, 'mode': 'Air', 'origin': 'DOH', 'destination': 'FRA', 'flight_no': 'QR69', 'atd': '2026-10-12', 'units': []}]
    row = project(air_doc(legs))
    assert nodes(row)['air-transit']['completed'] is True
    assert 'air-transit' not in nodes(project(air_doc()))


# =========================================================================== T4 ROAD

def road_doc(load='FTL', scope=None, units=None):
    doc = document(mode='Sea', load=load, scope=scope or ['ORIGIN_PICKUP', 'MAIN_CARRIAGE', 'FINAL_DELIVERY'])
    doc['data']['0.0'].update(mode='Truck', incoterm='DAP')
    doc['data']['1.2']['transport_legs'] = [
        {'id': 'road-1', 'sequence': 1, 'mode': 'Truck', 'origin': 'Bắc Ninh', 'destination': 'TP.HCM',
         'units': units if units is not None else [{'id': 't1', 'kind': 'truck', 'number': '99C-12345', 'type_size': '9.6m', 'driver_name': ''}]}]
    return doc


def test_domestic_road_has_no_customs_or_border_or_maritime_nodes():
    row = project(road_doc())
    ids = set(n['id'] for n in row['journey']['nodes'])
    assert not ({'customs-export', 'customs-import', 'road-border', 'booking', 'si-vgm', 'gate-in', 'on-board'} & ids)
    assert 'road-vehicle' in ids


def test_ftl_vehicle_needs_plate_and_driver_for_every_truck():
    row = project(road_doc())
    assert nodes(row)['road-vehicle']['completed'] is False
    doc = road_doc(units=[{'id': 't1', 'kind': 'truck', 'number': '99C-12345', 'type_size': '9.6m', 'driver_name': 'Nguyễn Văn A'}])
    assert nodes(project(doc))['road-vehicle']['completed'] is True


def test_ltl_selected_is_not_consolidated():
    doc = road_doc(load='LTL', units=[])
    assert stage(doc, 'ROAD_CONSOLIDATION')['done'] is False
    assert nodes(project(doc))['road-ltl']['completed'] is False
    doc['data']['1.2']['road_facts'] = {'ltl_received_at': '2026-10-01', 'ltl_package_count': '4'}
    assert nodes(project(doc))['road-ltl']['completed'] is False
    doc['data']['1.2']['road_facts']['ltl_consolidated_at'] = '2026-10-02'
    assert nodes(project(doc))['road-ltl']['completed'] is True
    assert stage(doc, 'ROAD_CONSOLIDATION')['done'] is True


def test_cross_border_road_shows_border_only_with_scope():
    doc = road_doc(scope=['ORIGIN_PICKUP', 'CROSS_BORDER_COORDINATION', 'MAIN_CARRIAGE', 'FINAL_DELIVERY'])
    node = nodes(project(doc))['road-border']
    assert node['completed'] is False and node['owned'] is True
    doc['data']['1.2']['road_facts'] = {'border_crossed_at': '2026-10-03T10:00'}
    assert nodes(project(doc))['road-border']['completed'] is True


def test_road_delivery_handover_and_pod_are_separate_from_delivery():
    doc = road_doc(); original = deepcopy(doc)
    keys = [f['key'] for f in nodes(project(doc))['delivery']['factFields']]
    assert keys == ['handover_doc_no', 'pod_received_at']
    doc['data']['1.2']['road_facts'] = {'pod_received_at': '2026-10-05'}
    node = nodes(project(doc))['delivery']
    assert node['completed'] is False and node['state'] == 'PROBLEM'
    assert original['data']['1.2'].get('road_facts') is None


def test_rail_history_still_reads_and_is_not_writable():
    doc = road_doc(); doc['data']['0.0']['mode'] = 'Rail'
    doc['data']['1.2']['transport_legs'][0].update(mode='Rail', units=[])
    project(doc)  # read path unchanged, no exception
    with pytest.raises(ValueError):
        normalize_mode_facts({'pod_received_at': '2026-10-01'}, 'RAIL')


@pytest.mark.parametrize('mode,fields', [('AIR', {'si_status': 'ACCEPTED'}), ('AIR', {'gate_in_at': '2026-10-01'}),
                                         ('ROAD', {'vgm_status': 'ACCEPTED'}), ('ROAD', {'air_uplifted_at': '2026-10-01'}),
                                         ('SEA', {'ltl_consolidated_at': '2026-10-01'})])
def test_cross_mode_fields_refused(mode, fields):
    with pytest.raises(ValueError):
        normalize_mode_facts(fields, mode)


# =========================================================================== canonical writer

@pytest.fixture
def staged():
    import streamlit as st
    from views import logi_sandbox
    logi_sandbox.reset_backend(); assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)

    def put(doc):
        from core.database import save_shipment_atomic
        doc = deepcopy(doc); doc.pop('version', None)
        assert save_shipment_atomic(doc, actor='logi199-t2t4-fixture')
    yield put
    logi_sandbox.reset_backend()


def write(fields):
    from views import logi_view_model as vm
    return event('shipment_sea_facts_save', {'shipmentId': 'SEA-160', 'requestId': 'T2T4',
        'expectedVersion': vm.read_shipment('SEA-160')['version'], 'fields': fields})


def test_writer_air_uplift_persists_in_air_block_with_readback(staged):
    staged(air_doc())
    result = write({'air_acceptance_at': '2026-10-09', 'air_chargeable_kg': '412.5', 'air_uplifted_at': '2026-10-10T23:40'})
    assert result['ok'], result
    assert result['persisted'] == {'air_acceptance_at': '2026-10-09', 'air_chargeable_kg': '412.5', 'air_uplifted_at': '2026-10-10T23:40'}
    assert nodes(result['readback'])['uplift']['completed'] is True
    from views import logi_view_model as vm
    assert 'sea_export' not in vm.read_shipment('SEA-160')['data']['1.2']
    assert not write({'on_board_at': '2026-10-10'})['ok']


def test_writer_domestic_road_refuses_border_and_ltl_on_ftl(staged):
    staged(road_doc())
    from views import logi_view_model as vm
    before = vm.read_shipment('SEA-160')
    assert not write({'border_crossed_at': '2026-10-03'})['ok']
    assert not write({'ltl_consolidated_at': '2026-10-03'})['ok']
    assert vm.read_shipment('SEA-160') == before
    ok = write({'handover_doc_no': 'BBGN-01'})
    assert ok['ok'], ok
    assert ok['persisted'] == {'handover_doc_no': 'BBGN-01'}


def test_writer_lcl_refuses_vgm_and_records_cfs(staged):
    staged(lcl_doc())
    assert not write({'vgm_status': 'ACCEPTED'})['ok']
    result = write({'cfs_received_at': '2026-10-01', 'cfs_package_count': '12'})
    assert result['ok'], result
    assert nodes(result['readback'])['cfs-receipt']['completed'] is False
    result = write({'consolidated_at': '2026-10-02'})
    assert nodes(result['readback'])['cfs-receipt']['completed'] is True


def test_writer_viewer_rbac_refused_for_air(staged):
    import streamlit as st
    staged(air_doc())
    st.session_state['current_user'] = {'username': 'viewer-199', 'role': 'viewer', 'active': True}
    result = write({'air_uplifted_at': '2026-10-10'})
    assert not result['ok'] and 'RBAC' in result['error']
