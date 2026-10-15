"""LOGI-199 T5 — each stage popup shows at most 5 primary evidence fields.

Extra fields are folded (secondary), never removed: they stay editable.
"""
from tests.test_logi199_t2_t4_mode_truth import air_doc, lcl_doc, road_doc
from tests.test_visual_shipment_workspace import document, project


def test_every_stage_popup_has_at_most_five_primary_fields_and_keeps_extras():
    for doc in (document(), lcl_doc(), air_doc(), road_doc(), road_doc(load='LTL', units=[])):
        for node in project(doc)['journey']['nodes']:
            fields = node['factFields']
            if not fields:
                continue
            primary = [f for f in fields if not f.get('secondary')]
            assert 1 <= len(primary) <= 5, (node['id'], [f['key'] for f in fields])
    cfs = next(n for n in project(lcl_doc())['journey']['nodes'] if n['id'] == 'cfs-receipt')
    keys = {f['key']: f.get('secondary', False) for f in cfs['factFields']}
    assert keys == {'cfs_received_at': False, 'cfs_receipt_no': True, 'cfs_package_count': False,
                    'cfs_weight_kg': True, 'cfs_cbm': False, 'consolidated_at': False}
