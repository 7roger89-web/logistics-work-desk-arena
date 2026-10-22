"""Journey node-completion truth — "báo xong khi chưa xong" repair.

Owner-confirmed business rules pinned here (negative + positive per rule):

* Booking (đã chốt tích hợp T1–T5): a booking NUMBER is never proof the
  carrier confirmed; the node completes only with booking_status == 'CONFIRMED'
  (BOOKING_STATES = UNKNOWN/REQUESTED/CONFIRMED — bỏ biến thể 'ACCEPTED').
* On-board (đã chốt tích hợp T1–T5): ATD ≠ loaded-on-board; the node
  completes from bool(on_board_at) alone — ATD neither required nor proof.
* SI/VGM: hàng LCL có node si-vgm SI-only (label 'SI') — Owner đã chốt batch 2
  đúng (2026-10-19): LCL có SI, không có VGM cấp lô. FCL giữ SI/VGM đủ 4 fact.

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
    node = _node(_journey({'booking_status': 'REQUESTED'}), 'booking')
    assert node['completed'] is False
    assert node['state'] != 'COMPLETED'


def test_booking_confirmed_by_carrier_is_done():
    node = _node(_journey({'booking_status': 'CONFIRMED'}), 'booking')
    assert node['completed'] is True
    assert node['state'] == 'COMPLETED'


def test_booking_request_with_a_number_is_not_done():
    # Số booking + đã gửi yêu cầu KHÔNG đủ: chỉ booking_status == 'CONFIRMED'
    # hoàn thành node (chuỗi T1 chốt — số booking không còn là điều kiện kèm).
    node = _node(_journey({'booking_status': 'REQUESTED'}, booking_no='BK-77'), 'booking')
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


def test_on_board_fact_stands_without_atd():
    # Đã chốt tích hợp T1–T5: done = bool(on_board_at) — bằng chứng lên tàu
    # tự nó hoàn thành node; ATD không phải bằng chứng và không phải điều kiện.
    node = _node(_journey({'on_board_at': '2026-10-02T08:30'}, atd=''), 'on-board')
    assert node['completed'] is True


# ---------------------------------------------------------------------------
# Lỗi 3 — VGM: LCL bỏ yêu cầu VGM, giữ node SI-only (f51710b). Owner đã chốt
# 2026-10-19: batch 2 ĐÚNG — rule đợt 1 "LCL không có node si-vgm" là sai và đã bỏ.
# ---------------------------------------------------------------------------

def test_sea_lcl_tracks_si_only_on_the_si_vgm_node():
    nodes = {n['id']: n for n in _journey({'si_status': 'ACCEPTED'}, load='LCL')['nodes']}
    node = nodes['si-vgm']
    assert node['label'] == 'SI'
    assert node['completed'] is True, 'LCL completes on SI alone — VGM is not a shipper obligation'
    assert 'booking' in nodes, 'the LCL rule must not remove unrelated stages'
    # dương ngược: thiếu SI thì CHƯA done
    assert _node(_journey({}, load='LCL'), 'si-vgm')['completed'] is False


def test_sea_fcl_keeps_si_vgm_node():
    ids = {n['id'] for n in _journey({}, load='FCL')['nodes']}
    assert 'si-vgm' in ids


def test_lcl_requirement_demands_only_si_not_vgm():
    shipment = {'id': 'S-DONE-FACTS', 'data': {
        '1.2': {'sea_export': {'si_status': 'ACCEPTED'}}, '2.4': {}, '2.7': {}}}
    # VGM chưa ACCEPTED cũng KHÔNG tạo yêu cầu cho LCL
    assert sea_requirement(shipment, _profile(load='LCL')) is None
    missing = {'id': 'S-DONE-FACTS', 'data': {'1.2': {'sea_export': {}}, '2.4': {}, '2.7': {}}}
    requirement = sea_requirement(missing, _profile(load='LCL'))
    assert requirement and 'SI' in requirement['text'] and 'VGM' not in requirement['text']


def test_fcl_si_vgm_requirement_still_fires_before_carrier_acceptance():
    shipment = {'id': 'S-DONE-FACTS', 'data': {
        '1.2': {'sea_export': {'si_status': 'SUBMITTED'}}, '2.4': {}, '2.7': {}}}
    requirement = sea_requirement(shipment, _profile(load='FCL'))
    assert requirement and requirement['stage'] == 'si-vgm'


# ---------------------------------------------------------------------------
# Guard factFields — LCL PHẢI có ô nhập SI (dương) và KHÔNG có ô nhập VGM (âm);
# FCL có đủ 4 ô (dương). Regression: guard `continue` cũ bỏ trắng factFields
# của node si-vgm LCL → node cần SI nhưng không có ô nhập → không bao giờ xong.
# ---------------------------------------------------------------------------

def test_lcl_si_vgm_fact_fields_expose_si_inputs():
    # dương: LCL có ô nhập SI — thiếu chúng node không bao giờ xong được
    node = _node(_journey({}, load='LCL'), 'si-vgm')
    keys = [f['key'] for f in node.get('factFields') or []]
    assert keys, 'LCL si-vgm node must not lose its factFields projection'
    assert 'si_status' in keys and 'si_cutoff' in keys


def test_lcl_si_vgm_fact_fields_drop_vgm_inputs():
    # âm: LCL KHÔNG có ô nhập VGM cấp lô
    node = _node(_journey({}, load='LCL'), 'si-vgm')
    keys = [f['key'] for f in node.get('factFields') or []]
    assert 'vgm_status' not in keys and 'vgm_cutoff' not in keys
    assert not [k for k in keys if k.startswith('vgm_')]


def test_fcl_si_vgm_fact_fields_expose_all_four_inputs():
    # dương: FCL giữ đủ 4 ô nhập SI/VGM
    node = _node(_journey({}, load='FCL'), 'si-vgm')
    keys = {f['key'] for f in node.get('factFields') or []}
    assert keys == {'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff'}


# ---------------------------------------------------------------------------
# Writer reuse — the new completion facts ride the existing sea-facts writer
# ---------------------------------------------------------------------------

def test_completion_facts_flow_through_the_existing_normalize_writer():
    normalized = normalize_sea_facts({'booking_status': 'CONFIRMED', 'on_board_at': '2026-10-02T08:30'})
    assert normalized == {'booking_status': 'CONFIRMED', 'on_board_at': '2026-10-02T08:30'}
    assert {'booking_status', 'on_board_at'} <= SEA_FACT_FIELDS


def test_invalid_completion_fact_values_are_still_refused():
    with pytest.raises(ValueError):
        normalize_sea_facts({'booking_status': 'DONE'})
    with pytest.raises(ValueError):
        normalize_sea_facts({'on_board_at': 'garbage'})
