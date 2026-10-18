"""Journey node-completion truth — "báo xong khi chưa xong" repair.

Owner-confirmed business rules pinned here (negative + positive per rule):

* Booking: CHỜ XÁC NHẬN khác với có số. A booking NUMBER is never proof the
  carrier confirmed; the node completes only with the confirming fact.
* On-board: ATD ≠ loaded-on-board. Actual departure time is never proof the
  cargo was loaded; the node completes only with the separate on-board fact.
* SI/VGM: hàng LCL không có VGM cấp lô. The si-vgm node exists for SEA FCL
  only, symmetric with the gate-in FCL gate.

Pure-projection tests: no DB, no network, no Streamlit session.
"""
from __future__ import annotations

import pytest

from core.shipment_journey import (
    SEA_FACT_FIELDS,
    build_journey,
    normalize_sea_facts,
    sea_requirement,
)


def _profile(*, load: str = 'FCL', scope=('MAIN_CARRIAGE', 'SEA_DOCUMENTS')) -> dict:
    codes = sorted({'MAIN_CARRIAGE', 'SEA_DOCUMENTS', 'ORIGIN_HANDOFF', *scope})
    return {
        'mode': 'SEA',
        'stages': [{'code': code, 'label': code, 'reason': 'SERVICE_SCOPE'} for code in codes],
        'serviceScope': list(scope),
        'serviceScopeConfirmed': True,
        'loadModel': load,
    }


def _journey(sea_export: dict | None = None, *, atd: str = '', booking_no: str = 'BK-77',
             load: str = 'FCL', profile: dict | None = None) -> dict:
    shipment = {'id': 'S-DONE-FACTS', 'data': {
        '1.2': {'sea_export': dict(sea_export or {})}, '2.4': {}, '2.7': {}}}
    operational = {'main_leg': {'booking_no': booking_no, 'etd': '2026-10-01',
                                'eta': '2026-10-05', 'atd': atd, 'ata': ''},
                   'pickup_leg': {}}
    return build_journey(shipment, profile=profile or _profile(load=load),
                         operational=operational, primary={}, dashboard={}, attachments=[])


def _node(journey: dict, node_id: str) -> dict:
    return next(n for n in journey['nodes'] if n['id'] == node_id)


# ---------------------------------------------------------------------------
# Lỗi 1 — booking: có số KHÔNG đủ, cần fact hãng tàu đã xác nhận
# ---------------------------------------------------------------------------

def test_booking_number_without_any_confirmation_status_is_not_done():
    node = _node(_journey({}, booking_no='BK-77'), 'booking')
    assert node['completed'] is False
    assert node['state'] != 'COMPLETED'
    assert 'BK-77' in node['evidence'], 'the number stays visible as a fact, not as completion'


def test_booking_waiting_for_confirmation_is_not_done():
    node = _node(_journey({'booking_status': 'SUBMITTED'}), 'booking')
    assert node['completed'] is False
    assert node['state'] != 'COMPLETED'


def test_booking_confirmed_by_carrier_is_done():
    node = _node(_journey({'booking_status': 'ACCEPTED'}), 'booking')
    assert node['completed'] is True
    assert node['state'] == 'COMPLETED'


def test_booking_confirmation_without_a_number_is_not_done():
    # Completion needs BOTH facts: a number AND the carrier confirmation.
    node = _node(_journey({'booking_status': 'ACCEPTED'}, booking_no=''), 'booking')
    assert node['completed'] is False


# ---------------------------------------------------------------------------
# Lỗi 2 — on-board: ATD KHÔNG đủ, cần fact riêng chứng minh hàng đã lên tàu
# ---------------------------------------------------------------------------

def test_atd_without_on_board_fact_is_not_done():
    node = _node(_journey({}, atd='2026-10-02'), 'on-board')
    assert node['completed'] is False
    assert node['state'] != 'COMPLETED'


def test_on_board_fact_with_atd_is_done():
    node = _node(_journey({'on_board_at': '2026-10-02T08:30'}, atd='2026-10-02'), 'on-board')
    assert node['completed'] is True
    assert node['state'] == 'COMPLETED'


def test_on_board_fact_without_atd_is_not_done():
    # Completion needs BOTH facts: the departure trigger AND the on-board proof.
    node = _node(_journey({'on_board_at': '2026-10-02T08:30'}, atd=''), 'on-board')
    assert node['completed'] is False


# ---------------------------------------------------------------------------
# Lỗi 3 — si-vgm chặn FCL, đối xứng với gate-in
# ---------------------------------------------------------------------------

def test_sea_lcl_has_no_si_vgm_node():
    ids = {n['id'] for n in _journey({}, load='LCL')['nodes']}
    assert 'si-vgm' not in ids
    assert 'booking' in ids, 'the LCL gate must not remove unrelated stages'


def test_sea_fcl_keeps_si_vgm_node():
    ids = {n['id'] for n in _journey({}, load='FCL')['nodes']}
    assert 'si-vgm' in ids


def test_lcl_requirement_never_points_at_a_missing_si_vgm_node():
    shipment = {'id': 'S-DONE-FACTS', 'data': {'1.2': {'sea_export': {}}, '2.4': {}, '2.7': {}}}
    assert sea_requirement(shipment, _profile(load='LCL')) is None


def test_fcl_si_vgm_requirement_still_fires_before_carrier_acceptance():
    shipment = {'id': 'S-DONE-FACTS', 'data': {
        '1.2': {'sea_export': {'si_status': 'SUBMITTED'}}, '2.4': {}, '2.7': {}}}
    requirement = sea_requirement(shipment, _profile(load='FCL'))
    assert requirement and requirement['stage'] == 'si-vgm'


# ---------------------------------------------------------------------------
# Writer reuse — the new completion facts ride the existing sea-facts writer
# ---------------------------------------------------------------------------

def test_completion_facts_flow_through_the_existing_normalize_writer():
    normalized = normalize_sea_facts({'booking_status': 'ACCEPTED', 'on_board_at': '2026-10-02T08:30'})
    assert normalized == {'booking_status': 'ACCEPTED', 'on_board_at': '2026-10-02T08:30'}
    assert {'booking_status', 'on_board_at'} <= SEA_FACT_FIELDS


def test_invalid_completion_fact_values_are_still_refused():
    with pytest.raises(ValueError):
        normalize_sea_facts({'booking_status': 'DONE'})
    with pytest.raises(ValueError):
        normalize_sea_facts({'on_board_at': 'garbage'})
