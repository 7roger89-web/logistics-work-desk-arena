"""LOGI-199 T1 — SEA FCL lifecycle truth (continues PR #201).

Each FCL milestone is its own evidence fact on the existing ``data.1.2.sea_export``
block, written only through the existing ``shipment_sea_facts_save`` writer
(RBAC + expectedVersion + readback). No new store, node id or workflow engine.

Invariants exercised (GOAL #199 §2):
* booking request / booking number != carrier confirmation;
* export declaration != export clearance;
* ATD != on-board proof;
* empty pickup / stuffing / seal / EIR do not complete gate-in;
* POD only after actual delivery; empty return only for FCL;
* every fact gated by the confirmed service scope, never by Incoterm alone.
"""
from copy import deepcopy

import pytest

from core.shipment_journey import normalize_sea_facts
from tests.test_visual_shipment_workspace import SCOPE, document, event, nodes, project, staging  # noqa: F401


def sea(doc):
    return doc['data']['1.2'].setdefault('sea_export', {})


# --------------------------------------------------------------------------- projection

def test_booking_number_alone_or_request_is_not_confirmation():
    doc = document()
    assert nodes(project(doc))['booking']['completed'] is False
    assert 'BK-160' in nodes(project(doc))['booking']['evidence']
    sea(doc)['booking_status'] = 'REQUESTED'
    node = nodes(project(doc))['booking']
    assert node['completed'] is False and 'chưa có xác nhận' in node['evidence']
    sea(doc)['booking_status'] = 'CONFIRMED'
    assert nodes(project(doc))['booking']['completed'] is True


def test_export_declaration_is_not_clearance():
    doc = document(); doc['china_export_decl_no'] = 'EXP-1'
    node = nodes(project(doc))['customs-export']
    assert node['completed'] is False and node['factState'] == 'KNOWN'
    sea(doc)['export_clearance_at'] = '2026-10-02'
    node = nodes(project(doc))['customs-export']
    assert node['completed'] is True and 'Thông quan: 2026-10-02' in node['evidence']


def test_atd_does_not_prove_on_board_loading():
    doc = document(); doc['data']['1.2']['transport_legs'][1]['atd'] = '2026-10-03'
    row = project(doc)
    assert nodes(row)['etd']['completed'] is True          # departure happened
    assert nodes(row)['on-board']['completed'] is False    # loading not proven
    assert nodes(row)['on-board']['factState'] == 'UNKNOWN'
    sea(doc)['on_board_at'] = '2026-10-03'
    assert nodes(project(doc))['on-board']['completed'] is True


def test_container_chain_steps_never_complete_gate_in_and_seal_is_counted_per_unit():
    doc = document()
    legs = doc['data']['1.2']['transport_legs']
    legs[1]['units'].append({'id': 'cont-161', 'kind': 'container', 'number': 'EFGH7654321', 'type_size': '20GP'})
    legs[1]['units'][0]['seal_no'] = 'SEAL-1'
    sea(doc).update(empty_pickup_at='2026-09-29', stuffing_at='2026-09-30', eir_no='EIR-9')
    node = nodes(project(doc))['gate-in']
    assert node['completed'] is False
    assert 'Seal: 1/2 container' in node['evidence'] and 'EIR: EIR-9' in node['evidence']
    sea(doc)['gate_in_at'] = '2026-10-01T08:00'
    assert nodes(project(doc))['gate-in']['completed'] is True


def test_delivery_pod_and_empty_return_are_separate_facts():
    doc = document()
    sea(doc).update(do_released_at='2026-10-06', pod_received_at='2026-10-07')
    node = nodes(project(doc))['delivery']
    assert node['completed'] is False
    assert node['state'] == 'PROBLEM' and any('POD' in b for b in node['blockers'])
    doc['data']['2.7'] = {'is_delivered': True, 'delivered_at': '2026-10-07'}
    node = nodes(project(doc))['delivery']
    assert node['completed'] is True and not any('POD' in b for b in node['blockers'])
    assert [f['key'] for f in node['factFields']] == ['do_released_at', 'pod_received_at', 'empty_return_at']


def test_lcl_delivery_never_offers_empty_return_or_gate_in():
    row = project(document(load='LCL'))
    assert 'gate-in' not in nodes(row)
    assert 'empty_return_at' not in [f['key'] for f in nodes(row)['delivery']['factFields']]


def test_fields_are_attached_only_to_their_owning_node_and_projection_does_not_mutate():
    doc = document(); original = deepcopy(doc)
    row = project(doc)
    keys = {n['id']: [f['key'] for f in n['factFields']] for n in row['journey']['nodes']}
    assert keys['booking'] == ['booking_status']
    assert keys['customs-export'] == ['export_declaration_no', 'export_clearance_at']
    assert keys['gate-in'] == ['empty_pickup_at', 'stuffing_at', 'eir_no', 'gate_in_at']
    assert keys['on-board'] == ['on_board_at']
    assert keys['etd'] == [] and keys['customs-import'] == []
    assert doc == original


@pytest.mark.parametrize('fields', [{'booking_status': 'ACCEPTED'}, {'on_board_at': 'tomorrow'},
                                    {'eir_no': 'x' * 121}, {'pod_received_at': '2026-02-30'}])
def test_invalid_lifecycle_values_refused(fields):
    with pytest.raises(ValueError):
        normalize_sea_facts(fields)


# --------------------------------------------------------------------------- canonical writer

def write(fields):
    from views import logi_view_model as vm
    return event('shipment_sea_facts_save', {'shipmentId': 'SEA-160', 'requestId': 'T1-FCL',
        'expectedVersion': vm.read_shipment('SEA-160')['version'], 'fields': fields})


def test_writer_readback_confirms_booking_and_on_board(staging):  # noqa: F811
    result = write({'booking_status': 'REQUESTED'})
    assert result['ok'], result
    assert nodes(result['readback'])['booking']['completed'] is False
    result = write({'booking_status': 'CONFIRMED', 'on_board_at': '2026-10-03'})
    assert result['ok'], result
    assert result['persisted']['booking_status'] == 'CONFIRMED'
    assert nodes(result['readback'])['booking']['completed'] is True
    assert nodes(result['readback'])['on-board']['completed'] is True


def test_writer_refuses_pod_before_delivery_and_out_of_scope_delivery_facts(staging):  # noqa: F811
    from views import logi_view_model as vm
    before = vm.read_shipment('SEA-160')
    # fixture scope = first five segments: no destination trucking / delivery
    for fields in ({'pod_received_at': '2026-10-07'}, {'empty_return_at': '2026-10-08'}, {'do_released_at': '2026-10-06'}):
        result = write(fields)
        assert not result['ok'], fields
    assert vm.read_shipment('SEA-160') == before


def test_writer_pod_requires_actual_delivery(staging):  # noqa: F811
    from core.database import save_shipment_atomic
    from views import logi_view_model as vm
    doc = vm.read_shipment('SEA-160')
    doc['data']['0.0']['execution_profile']['service_scope'] = SCOPE
    assert save_shipment_atomic(doc, expected_version=doc['version'], actor='fixture')
    refused = write({'pod_received_at': '2026-10-07'})
    assert not refused['ok'] and 'giao hàng thực tế' in refused['error']
    assert write({'do_released_at': '2026-10-06'})['ok']
    doc = vm.read_shipment('SEA-160'); doc['data']['2.7'] = {'is_delivered': True, 'delivered_at': '2026-10-07'}
    assert save_shipment_atomic(doc, expected_version=doc['version'], actor='fixture')
    ok = write({'pod_received_at': '2026-10-07', 'empty_return_at': '2026-10-09'})
    assert ok['ok'], ok
    node = nodes(ok['readback'])['delivery']
    assert node['completed'] is True and 'POD: 2026-10-07' in node['evidence'] and 'Trả rỗng: 2026-10-09' in node['evidence']


def test_writer_refuses_container_chain_on_lcl(staging):  # noqa: F811
    from core.database import save_shipment_atomic
    from views import logi_view_model as vm
    doc = vm.read_shipment('SEA-160')
    doc['data']['0.0']['execution_profile']['load_model'] = 'LCL'
    for leg in doc['data']['1.2']['transport_legs']:
        if leg['mode'] == 'Sea': leg['units'] = []
    assert save_shipment_atomic(doc, expected_version=doc['version'], actor='fixture')
    for fields in ({'stuffing_at': '2026-09-30'}, {'eir_no': 'EIR-1'}, {'empty_pickup_at': '2026-09-29'}):
        assert not write(fields)['ok'], fields
