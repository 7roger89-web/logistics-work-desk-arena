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


def _project(profile):
    shipment = {'id': 'LOGI-199-SEA-FIELDS',
                'data': {'1.2': {'sea_export': {}}, '2.4': {}, '2.7': {}}}
    return build_journey(shipment, profile=profile,
                         operational={'main_leg': {}, 'pickup_leg': {}},
                         primary={}, dashboard={}, attachments=[])


class SeaStageFields199(unittest.TestCase):
    def test_fcl_fields_match_the_existing_writer_and_belong_only_to_nodes(self):
        nodes = {n['id']: n for n in _project(_profile())['nodes']}
        self.assertEqual([x['key'] for x in nodes['si-vgm']['factFields']],
                         ['si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff'])
        self.assertEqual([x['key'] for x in nodes['gate-in']['factFields']], ['gate_in_at'])
        self.assertEqual([x['key'] for x in nodes['customs-export']['factFields']],
                         ['export_declaration_no'])
        all_fields = {field['key'] for node in nodes.values()
                      for field in node.get('factFields', [])}
        self.assertEqual(all_fields, SEA_FACT_FIELDS)
        self.assertNotIn('factFields', nodes['pickup'])
        self.assertNotIn('factFields', nodes['on-board'])

    def test_status_options_are_whitelisted_without_silent_completion(self):
        nodes = {n['id']: n for n in _project(_profile())['nodes']}
        fields = nodes['si-vgm']['factFields']
        self.assertEqual([v['value'] for v in fields[0]['options']],
                         ['UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED'])
        self.assertTrue(fields[2]['secondary'])
        self.assertFalse(nodes['si-vgm']['completed'])
        self.assertFalse(nodes['gate-in']['completed'])
        self.assertFalse(nodes['customs-export']['completed'])

    def test_air_and_lcl_never_invent_fcl_forms(self):
        air = {n['id']: n for n in _project(_profile(mode='AIR'))['nodes']}
        self.assertFalse(any(n.get('factFields') for n in air.values()))
        lcl = {n['id']: n for n in _project(_profile(load_model='LCL'))['nodes']}
        self.assertNotIn('gate-in', lcl)
        self.assertEqual([f['key'] for f in lcl['si-vgm']['factFields']],
                         ['si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff'])

    def test_unowned_export_cannot_offer_an_edit_form(self):
        nodes = {n['id']: n for n in
                 _project(_profile(scope=['MAIN_CARRIAGE']))['nodes']}
        self.assertFalse(nodes['customs-export']['owned'])
        self.assertNotIn('factFields', nodes['customs-export'])
        self.assertTrue(nodes['si-vgm']['owned'])


if __name__ == '__main__':
    unittest.main()
