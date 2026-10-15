from unittest.mock import patch
from copy import deepcopy
from pathlib import Path
import json, mongomock
import core.database as db
client=mongomock.MongoClient()
store=client['test_logi199_isolated']
store.contracts.insert_one({'id':'CTR-001','is_deleted':False})
store.contract_intl_payment_snapshots.create_index('id', unique=True)
payload={'id':'SNAP-001','contract_id':'CTR-001','mode':'B','created_at':'2026-10-15T00:00:00+00:00','inputs':{'target_cny':'10000'},'outputs':{'total':1}}
with patch.object(db,'get_db',return_value=store), patch('core.auth.can_edit_contract',return_value=True):
 first=db.save_contract_intl_snapshot(payload, actor='test-only')
 second=db.save_contract_intl_snapshot(payload, actor='test-only')
 bad=deepcopy(payload);bad['inputs']['target_cny']='9999'
 tamper=db.save_contract_intl_snapshot(bad, actor='test-only')
 count=store.contract_intl_payment_snapshots.count_documents({})
 result={'boundary':'mongomock only; authorized writer + required unique index fixture, not live DB/RBAC acceptance','first':first,'idempotent':second,'tamper_accepted':tamper,'persisted_rows':count}
 print(json.dumps(result,indent=2))
 assert first and second and not tamper and count==1
