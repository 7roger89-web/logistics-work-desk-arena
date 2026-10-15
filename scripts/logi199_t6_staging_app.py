"""LOGI-199 T6 — isolated staging launcher for the real-browser acceptance run.

Runs the REAL app (``views.web_app.main``) on the existing sandbox transport
(mongomock, no MONGO_URI, no secrets) after adding four mode fixtures through the
canonical writer ``save_shipment_atomic``. Refuses to run against a real database.
Never used by production (``app.py`` is unchanged).
"""
from __future__ import annotations

import os
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if os.environ.get("MONGO_URI"):
    raise SystemExit("LOGI-199 T6 staging launcher refuses a real MONGO_URI.")

from views import logi_sandbox  # noqa: E402

FIXTURE_IDS = ("T6-FCL", "T6-LCL", "T6-AIR", "T6-ROAD-LTL", "T6-ROAD-FTL", "T6-AIR-CONSOLIDATED")


def _fixtures() -> list[dict]:
    from tests.test_logi199_t2_t4_mode_truth import air_doc, lcl_doc, road_doc
    from tests.test_visual_shipment_workspace import document
    docs = [document(), lcl_doc(), air_doc(), road_doc(load="LTL", units=[],
            scope=["ORIGIN_PICKUP", "MAIN_CARRIAGE", "FINAL_DELIVERY"])]
    consolidated = air_doc()
    consolidated['data']['0.0']['execution_profile']['load_model'] = 'CONSOLIDATED'
    docs.extend([road_doc(load='FTL'), consolidated])
    out = []
    for sid, doc in zip(FIXTURE_IDS, docs):
        doc = deepcopy(doc)
        doc.pop("version", None)
        doc["id"] = sid
        doc["data"]["0.0"].setdefault("created_at", "2026-10-15")
        out.append(doc)
    return out


def _seed_once() -> None:
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    from core.database import save_shipment_atomic
    from views.logi_view_model import read_shipment
    for doc in _fixtures():
        if read_shipment(doc["id"]) is None:
            assert save_shipment_atomic(doc, actor="logi199-t6-fixture"), doc["id"]


_seed_once()
from views.web_app import main  # noqa: E402

main()
