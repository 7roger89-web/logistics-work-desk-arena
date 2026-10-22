"""LOGI-199: expose only existing authorized SEA writer fields to stage popups.

The projection never writes facts or manufactures physical-stage completion.
"""
import unittest

from core.shipment_journey import SEA_FACT_FIELDS, build_journey


def _profile(mode='SEA', load_model='FCL', scope=None):
    if scope is None:
        scope = ['MAIN_CARRIAGE', 'EXPORT_HANDLING', 'ORIGIN_TERMINAL_OR_BORDER']
    return {
        'mode': mode, 'loadModel': load_model, 'serviceScopeConfirmed': True,
        'serviceScope': scope,
        'stages': [
            {'code': 'MAIN_CARRIAGE', 'label': 'Main carriage', 'reason': 'SERVICE_SCOPE'},
            {'code': 'ORIGIN_PICKUP', 'label': 'Pickup', 'reason': 'SERVICE_SCOPE'},
            {'code': 'EXPORT_HANDLING', 'label': 'Export', 'reason': 'SERVICE_SCOPE'},
            {'code': 'ORIGIN_HANDOFF', 'label': 'Handoff', 'reason': 'SERVICE_SCOPE'},
        ],
    }


def _project(profile, *, attachments=None):
    shipment = {'id': 'LOGI-199-SEA-FIELDS',
                'data': {'1.2': {'sea_export': {}}, '2.4': {}, '2.7': {}}}
    return build_journey(shipment, profile=profile,
                         operational={'main_leg': {}, 'pickup_leg': {}},
                         primary={}, dashboard={}, attachments=attachments or [])


class SeaStageFields199(unittest.TestCase):
    def test_fcl_fields_match_the_existing_writer_and_belong_only_to_nodes(self):
        nodes = {n['id']: n for n in _project(_profile())['nodes']}
        self.assertEqual([x['key'] for x in nodes['si-vgm']['factFields']],
                         ['si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff'])
        self.assertEqual([x['key'] for x in nodes['gate-in']['factFields']],
                         ['empty_pickup_at', 'stuffing_at', 'eir_no', 'gate_in_at'])
        self.assertEqual([x['key'] for x in nodes['customs-export']['factFields']],
                         ['export_declaration_no', 'export_clearance_at'])
        all_fields = {field['key'] for node in nodes.values()
                      for field in node.get('factFields', [])}
        # Tích hợp T1–T5: profile 4 stage (không DELIVERY/IMPORT) chiếu đúng
        # 12 field này; đều là tập con của writer whitelist (CFS/POD/D-O sống
        # ở node DELIVERY/CFS theo mode).
        self.assertEqual(all_fields, {
            'booking_status', 'export_declaration_no', 'export_clearance_at',
            'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff',
            'empty_pickup_at', 'stuffing_at', 'eir_no', 'gate_in_at',
            'on_board_at'})
        self.assertLessEqual(all_fields, SEA_FACT_FIELDS)
        self.assertEqual(nodes['pickup']['factFields'], [])
        # Node-truth round 2: booking/on-board completion facts now HAVE their
        # input fields (previously pinned absent — that was the gap being fixed).
        self.assertEqual([x['key'] for x in nodes['booking']['factFields']],
                         ['booking_status'])
        self.assertEqual(nodes['booking']['factFields'][0]['label'],
                         'Trạng thái booking')
        self.assertEqual([x['key'] for x in nodes['on-board']['factFields']],
                         ['on_board_at'])

    def test_status_options_are_whitelisted_without_silent_completion(self):
        nodes = {n['id']: n for n in _project(_profile())['nodes']}
        fields = nodes['si-vgm']['factFields']
        self.assertEqual([v['value'] for v in fields[0]['options']],
                         ['UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED'])
        # Tích hợp T1–T5: secondary chỉ bật khi >5 primary (_SECONDARY_FACTS);
        # si-vgm FCL có đúng 4 primary (popup ≤5) nên cutoff không bị fold.
        self.assertFalse(fields[2].get('secondary'))
        self.assertEqual(sum(1 for f in fields if not f.get('secondary')), 4)
        self.assertFalse(nodes['si-vgm']['completed'])
        self.assertFalse(nodes['gate-in']['completed'])
        self.assertFalse(nodes['customs-export']['completed'])

    def test_air_and_lcl_never_invent_fcl_forms(self):
        from core.shipment_journey import AIR_FACT_FIELDS
        air = {n['id']: n for n in _project(_profile(mode='AIR'))['nodes']}
        # Tích hợp T3: node AIR CÓ factFields của riêng AIR — nhưng KHÔNG bao giờ
        # chứa form FCL (si_/vgm_/gate_in) và mọi key nằm trong AIR_FACT_FIELDS.
        air_keys = {f['key'] for n in air.values() for f in n.get('factFields', [])}
        self.assertTrue(air_keys)
        self.assertFalse({'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff',
                          'gate_in_at'} & air_keys)
        self.assertLessEqual(air_keys, AIR_FACT_FIELDS)
        lcl = {n['id']: n for n in _project(_profile(load_model='LCL'))['nodes']}
        self.assertNotIn('gate-in', lcl)
        # False-done batch 2 (f51710b) + guard fix: the LCL node exists as
        # SI-only and KEEPS the SI inputs (si_status/si_cutoff) — without them
        # the node needs SI but can never complete — while dropping ONLY the
        # shipment-level VGM form (vgm_status/vgm_cutoff). The original pin
        # `assertNotIn('factFields', ...)` froze the guard bug this fix removes.
        self.assertIn('si-vgm', lcl)
        self.assertEqual(lcl['si-vgm']['label'], 'SI')
        lcl_keys = [x['key'] for x in lcl['si-vgm'].get('factFields', [])]
        self.assertIn('si_status', lcl_keys)
        self.assertIn('si_cutoff', lcl_keys)
        self.assertNotIn('vgm_status', lcl_keys)
        self.assertNotIn('vgm_cutoff', lcl_keys)

    def test_unowned_export_cannot_offer_an_edit_form(self):
        nodes = {n['id']: n for n in
                 _project(_profile(scope=['MAIN_CARRIAGE']))['nodes']}
        # Tích hợp T1–T5 (fields= trong add()): metadata field được project cả
        # khi unowned — nhưng node KHÔNG có quyền sửa: SeaExportFacts Input và
        # nút Lưu đều disabled={!node?.owned} (ShipmentJourney.tsx) và writer
        # chặn theo scope. Chốt: unowned = không ghi được, không phải ẩn metadata.
        self.assertFalse(nodes['customs-export']['owned'])
        self.assertEqual([x['key'] for x in nodes['customs-export']['factFields']],
                         ['export_declaration_no', 'export_clearance_at'])
        self.assertTrue(nodes['si-vgm']['owned'])


    def test_documents_in_shared_categories_stay_whole_lot(self):
        profile = _profile()
        profile['stages'].append({'code': 'IMPORT_CUSTOMS', 'label': 'Import customs',
                                  'reason': 'SERVICE_SCOPE'})
        profile['serviceScope'].append('IMPORT_CUSTOMS')
        attachments = [
            {'id': 'TR-1', 'category': 'transport'},
            {'id': 'CUS-1', 'category': 'customs'},
            {'id': 'SI-1', 'category': 'si'},
            {'id': 'BOOK-1', 'category': 'booking'},
        ]
        nodes = {n['id']: n for n in _project(profile, attachments=attachments)['nodes']}
        # Transport belongs to many stages, customs to export AND import.
        for node_id in ('booking', 'pickup', 'gate-in', 'on-board', 'arrival'):
            self.assertNotIn('TR-1', nodes[node_id]['documentIds'])
        self.assertNotIn('CUS-1', nodes['customs-export']['documentIds'])
        self.assertNotIn('CUS-1', nodes['customs-import']['documentIds'])
        # Category exclusive to one node may be safely scoped there.
        self.assertEqual(nodes['booking']['documentIds'], ['BOOK-1'])
        self.assertEqual(nodes['si-vgm']['documentIds'], ['SI-1'])


if __name__ == '__main__':
    unittest.main()
