"""Journey screen truth — round 2: the UI must say what is actually there.

TASK 1 (P0) — JourneyBubble docs task: FILE_PRESENT != DOCUMENT_ACCEPTED.
    Files attached to a node were mapped to tone COMPLETED with the green
    '✓ Có bằng chứng' badge. The repo has NO document-acceptance authority
    (uploads never self-accept), so files must render AS files and never as
    accepted evidence.
TASK 2 — booking_status / on_board_at inputs: metadata-driven form + mount,
    and the write→readback flow flips the matching node state.
TASK 3 — JourneyQuickPanel surfaces what_to_do + done_when in the main area
    and admits 'Chưa có hướng dẫn cho công đoạn này' instead of a generic
    filler sentence that pretended guidance existed.

Source-contract tests follow the repo pattern (test_journey_super_goal_186);
the write flow runs the REAL shipment_sea_facts_save writer on sandbox transport.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.shipment_journey import SUBMISSION_STATES, build_journey

ROOT = Path(__file__).resolve().parent.parent
BUBBLE = (ROOT / 'component/src/components/JourneyBubble.tsx').read_text(encoding='utf-8')
QUICK = (ROOT / 'component/src/components/JourneyQuickPanel.tsx').read_text(encoding='utf-8')
DETAIL = (ROOT / 'component/src/pages/ShipmentDetail.tsx').read_text(encoding='utf-8')
JOURNEY = (ROOT / 'component/src/components/ShipmentJourney.tsx').read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# TASK 1 — có tệp ≠ có bằng chứng (JourneyBubble docs task)
# ---------------------------------------------------------------------------

def test_docs_task_never_maps_file_presence_to_completed():
    # âm: exact lie from the P0 report is gone
    assert "tone: attached > 0 ? 'COMPLETED' : 'WAITING'" not in BUBBLE
    assert "attached > 0 ? 'COMPLETED'" not in BUBBLE


def test_docs_task_label_states_files_recorded_not_accepted_evidence():
    # dương: the label says what IS there (files), and explicitly not more
    assert "key: 'docs'" in BUBBLE
    assert "'✓ Tệp đã ghi nhận'" in BUBBLE
    assert 'CHƯA XÁC NHẬN BẰNG CHỨNG' in BUBBLE
    # the per-task badge override is actually rendered
    assert 't.badge ?? TONE_BADGE[t.tone]' in BUBBLE
    # green 'Có bằng chứng' stays reserved for fact-backed COMPLETED only
    assert "COMPLETED: { text: '✓ Có bằng chứng'" in BUBBLE


# ---------------------------------------------------------------------------
# TASK 2 — ô nhập booking_status / on_board_at
# ---------------------------------------------------------------------------

def _project_facts_nodes():
    profile = {
        'mode': 'SEA', 'loadModel': 'FCL', 'serviceScopeConfirmed': True,
        'serviceScope': ['MAIN_CARRIAGE', 'ORIGIN_TERMINAL_OR_BORDER'],
        'stages': [
            {'code': 'MAIN_CARRIAGE', 'label': 'Main carriage', 'reason': 'SERVICE_SCOPE'},
            {'code': 'ORIGIN_HANDOFF', 'label': 'Handoff', 'reason': 'SERVICE_SCOPE'},
        ],
    }
    shipment = {'id': 'UI-TRUTH', 'data': {'1.2': {'sea_export': {}}, '2.4': {}, '2.7': {}}}
    journey = build_journey(shipment, profile=profile,
                            operational={'main_leg': {'booking_no': 'BK-1', 'atd': '2026-10-02'},
                                         'pickup_leg': {}},
                            primary={}, dashboard={}, attachments=[])
    return {n['id']: n for n in journey['nodes']}


def test_booking_and_on_board_expose_their_completion_fact_inputs():
    nodes = _project_facts_nodes()
    booking = [f for f in nodes['booking']['factFields'] if f['key'] == 'booking_status']
    on_board = [f for f in nodes['on-board']['factFields'] if f['key'] == 'on_board_at']
    assert booking and booking[0]['label'] == 'Trạng thái xác nhận hãng tàu'
    assert booking[0]['kind'] == 'status'
    # đúng tập giá trị SUBMISSION_STATES hiện có — không tự đặt tập mới
    assert tuple(o['value'] for o in booking[0]['options']) == SUBMISSION_STATES
    assert on_board and on_board[0]['kind'] == 'datetime'


def test_stage_popup_mounts_the_form_for_booking_and_on_board():
    # dương: both mount lists (hasStageContent + stageContent) include the nodes
    assert "['booking', 'si-vgm', 'gate-in', 'customs-export', 'on-board']" in DETAIL
    assert '["booking", "si-vgm", "gate-in", "customs-export", "on-board"]' in DETAIL
    # the panel renders the backend-declared field list (no hardcoded invention)
    assert 'const fields = node?.factFields ?? []' in JOURNEY


# ---------------------------------------------------------------------------
# TASK 2 — flow: ghi fact qua writer thật → đọc lại → node chuyển trạng thái
# ---------------------------------------------------------------------------

def _document():
    return {
        'id': 'SEA-UI-TRUTH', 'customer': 'An Phát JSC', 'customer_id': 'CUST-ANPHAT',
        'status': 'wait', 'currency': 'VND',
        'data': {
            '0.0': {'mode': 'Sea', 'incoterm': 'FOB', 'execution_profile': {
                'incoterm_version': '2020', 'incoterm_named_place': 'Hai Phong',
                'load_model': 'FCL',
                'service_scope': ['MAIN_CARRIAGE', 'ORIGIN_TERMINAL_OR_BORDER'],
                'service_scope_confirmed': True, 'cargo_insurance': {'status': 'NO'}}},
            '1.2': {'transport_legs': [
                {'id': 'sea-ui', 'sequence': 1, 'mode': 'Sea', 'origin': 'Hai Phong',
                 'destination': 'Singapore', 'booking_no': 'BK-UI-1', 'carrier': 'Carrier',
                 'vessel': 'Vessel', 'etd': '2026-10-01', 'eta': '2026-10-05',
                 'atd': '2026-10-02', 'ata': '',
                 'units': [{'id': 'cont-ui', 'kind': 'container', 'number': 'ABCD1234567',
                            'type_size': '40HC'}]}]},
            '2.4': {}, '2.6': {}, '2.7': {}, '3.4': {'details': [], 'payments': []},
            'entrustment': {'active': False}},
    }


@pytest.fixture
def staging():
    import streamlit as st
    from core.database import save_shipment_atomic
    from views import logi_sandbox
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)
    doc = _document()
    assert save_shipment_atomic(doc, actor='ui-truth-fixture')
    yield
    st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _write(fields):
    from views import logi_view_model as vm
    return vm.consume_phase_b_triggers({'seq': 0}, {'shipment_sea_facts_save': {'seq': 1, 'payload': {
        'shipmentId': 'SEA-UI-TRUTH', 'requestId': 'SEA-UI-TRUTH-1',
        'expectedVersion': vm.read_shipment('SEA-UI-TRUTH')['version'], 'fields': fields}}})[0]


def _nodes(projection):
    return {n['id']: n for n in projection['journey']['nodes']}


def test_write_booking_confirmation_then_readback_completes_only_booking(staging):
    from views import logi_real_data as rd, logi_view_model as vm
    # âm: có số booking + có ATD nhưng CHƯA có fact xác nhận/lên tàu → chưa node nào xong
    before = rd.shipment_projection(vm.read_shipment('SEA-UI-TRUTH'), ledger={}, agents={},
                                    attachments={}, docgen_documents={}, linked_contracts={})
    assert _nodes(before)['booking']['completed'] is False
    assert _nodes(before)['on-board']['completed'] is False

    first = _write({'booking_status': 'ACCEPTED'})
    assert first['ok'], first
    row = first['readback']
    assert _nodes(row)['booking']['completed'] is True
    assert _nodes(row)['booking']['state'] == 'COMPLETED'
    # xác nhận booking KHÔNG kéo on-board xong theo
    assert _nodes(row)['on-board']['completed'] is False

    second = _write({'on_board_at': '2026-10-02T08:30'})
    assert second['ok'], second
    assert _nodes(second['readback'])['on-board']['completed'] is True
    # và booking vẫn giữ trạng thái đã xác nhận sau lần ghi sau
    assert _nodes(second['readback'])['booking']['completed'] is True


def test_invalid_status_value_is_refused_by_the_existing_writer(staging):
    result = _write({'booking_status': 'DONE'})
    assert not result['ok']
