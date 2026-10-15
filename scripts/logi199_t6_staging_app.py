"""LOGI-199 isolated real-app staging launcher.

Runs the REAL app on in-process Mongomock only, after adding the existing T6
mode fixtures through ``save_shipment_atomic`` and a fresh zero-node shipment
through the canonical ``shipment_create`` dispatcher. This launcher refuses a
real MONGO_URI or any non-Mongomock transport before it imports/runs the app.
Never used by production (``app.py`` and production auth are unchanged).
"""
from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if os.environ.get("MONGO_URI"):
    raise SystemExit("LOGI-199 staging refuses a non-empty MONGO_URI.")

from views import logi_sandbox  # noqa: E402

FIXTURE_IDS = ("T6-FCL", "T6-LCL", "T6-AIR", "T6-ROAD-LTL", "T6-ROAD-FTL", "T6-AIR-CONSOLIDATED")
FRESH_ID = "SEA-188"
FRESH_CUSTOMER_ID = "CUST-MOI-188"
FRESH_CUSTOMER_NAME = "Khách hàng mới 188"
PROFILE_ANCHOR = "shipment-execution-profile"


def _require_isolated_mongomock() -> None:
    """Fail closed before seeding or rendering if the effective config is real."""
    transport = logi_sandbox.ensure_backend()
    if transport != logi_sandbox.SANDBOX_TRANSPORT:
        raise SystemExit("LOGI-199 staging refuses REAL_MONGO; no fixture was written.")

    import mongomock
    from core import config, database

    client = logi_sandbox._state.get("client")
    if not isinstance(client, mongomock.MongoClient):
        raise SystemExit("LOGI-199 staging requires an in-process Mongomock client.")
    if logi_sandbox._real_uri_configured():
        raise SystemExit("LOGI-199 staging refuses a configured real MongoDB URI.")
    if config.MONGO_URI != logi_sandbox.STAGING_URI_PLACEHOLDER:
        raise SystemExit("LOGI-199 staging URI identity is not the Mongomock placeholder.")
    if config.MONGO_DB_NAME != logi_sandbox.STAGING_DB_NAME:
        raise SystemExit("LOGI-199 staging database identity is not logistics_staging.")
    if database._init_connection_impl() is not client:
        raise SystemExit("LOGI-199 staging database handle is not the isolated Mongomock client.")

    if not logi_sandbox._state.get("_logi199_isolation_proof_logged"):
        print(
            "STAGING_ISOLATION_PROOF=PASS "
            "transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO production_client=NO",
            flush=True,
        )
        logi_sandbox._state["_logi199_isolation_proof_logged"] = True


def _fixtures() -> list[dict]:
    from tests.test_logi199_t2_t4_mode_truth import air_doc, lcl_doc, road_doc
    from tests.test_visual_shipment_workspace import document

    docs = [
        document(),
        lcl_doc(),
        air_doc(),
        road_doc(load="LTL", units=[], scope=["ORIGIN_PICKUP", "MAIN_CARRIAGE", "FINAL_DELIVERY"]),
    ]
    consolidated = air_doc()
    consolidated["data"]["0.0"]["execution_profile"]["load_model"] = "CONSOLIDATED"
    docs.extend([road_doc(load="FTL"), consolidated])
    out = []
    for sid, doc in zip(FIXTURE_IDS, docs):
        doc = deepcopy(doc)
        doc.pop("version", None)
        doc["id"] = sid
        doc["data"]["0.0"].setdefault("created_at", "2026-10-15")
        out.append(doc)
    return out


def _seed_t6_once() -> None:
    _require_isolated_mongomock()
    from core.database import save_shipment_atomic
    from views.logi_view_model import read_shipment

    for doc in _fixtures():
        if read_shipment(doc["id"]) is None and not save_shipment_atomic(
            doc, actor="logi199-t6-fixture"
        ):
            raise SystemExit(f"Could not seed isolated T6 fixture {doc['id']}.")


def _seed_fresh_zero_node_once() -> dict:
    """Create and verify the real empty-Journey shape without resetting T6."""
    from views import logi_view_model as vm

    if vm.read_shipment(FRESH_ID) is None:
        outcomes = vm.consume_phase_b_triggers(
            {"seq": 0},
            {
                "shipment_create": {
                    "seq": 1,
                    "payload": {
                        "shipmentId": FRESH_ID,
                        "customerId": FRESH_CUSTOMER_ID,
                        "customer": FRESH_CUSTOMER_NAME,
                        "requestId": "REQ-JOURNEY-188-FRESH",
                    },
                }
            },
        )
        if not outcomes or not outcomes[0].get("ok"):
            raise SystemExit(f"Canonical shipment_create did not seed {FRESH_ID}.")

    doc = vm.read_shipment(FRESH_ID) or {}
    if not doc:
        raise SystemExit("Fresh-shipment fixture was not persisted in Mongomock.")
    head = (doc.get("data") or {}).get("0.0") or {}
    transport_legs = (doc.get("data") or {}).get("1.2", {}).get("transport_legs") or []
    model = vm.build_view_model()
    row = next((shipment for shipment in model.get("shipments", []) if shipment.get("id") == FRESH_ID), None)
    if row is None:
        raise SystemExit("Fresh-shipment fixture is missing from the canonical view model.")
    journey = row.get("journey") or {}
    profile = row.get("executionProfile") or {}
    primary_route = (journey.get("primaryAction") or {}).get("route")

    if head.get("execution_profile") or head.get("mode") or head.get("incoterm") or transport_legs:
        raise SystemExit("Fresh fixture unexpectedly contains profile, mode, Incoterm, or transport legs.")
    if journey.get("nodes") != []:
        raise SystemExit(f"Fresh fixture is not zero-node: {journey.get('nodes')!r}")
    if profile.get("state") != "PROFILE_INCOMPLETE" or profile.get("serviceScopeConfirmed") is not False:
        raise SystemExit("Fresh fixture profile/scope is not truthfully incomplete.")
    if profile.get("serviceScope") or primary_route != f"/lo-hang/{FRESH_ID}?tab=van-tai#{PROFILE_ANCHOR}":
        raise SystemExit("Fresh fixture profile action is not the existing Execution Profile editor route.")

    return {
        "fixture": "FRESH_SHIPMENT_188",
        "shipmentId": FRESH_ID,
        "customer": FRESH_CUSTOMER_NAME,
        "persisted": True,
        "version": doc.get("version"),
        "journeyNodes": 0,
        "profileState": profile.get("state"),
        "profileStateLabel": profile.get("stateLabel"),
        "serviceScope": profile.get("serviceScope"),
        "serviceScopeConfirmed": profile.get("serviceScopeConfirmed"),
        "firstMode": head.get("mode"),
        "incoterm": head.get("incoterm"),
        "transportLegs": len(transport_legs),
        "primaryAction": (journey.get("primaryAction") or {}).get("text"),
        "projectedPrimaryRoute": primary_route,
        "nextRoute": row.get("nextRoute"),
        "nextAction": row.get("nextAction"),
        "nextActionDetail": row.get("nextActionDetail"),
        "fixture_creation": "canonical shipment_create; isolated Mongomock only",
    }


_seed_t6_once()
_ZERO_NODE_FIXTURE = _seed_fresh_zero_node_once()
if not logi_sandbox._state.get("_logi199_zero_fixture_logged"):
    print("LOGI199_ZERO_FIXTURE=" + json.dumps(_ZERO_NODE_FIXTURE, ensure_ascii=False, sort_keys=True), flush=True)
    logi_sandbox._state["_logi199_zero_fixture_logged"] = True
from views.web_app import main  # noqa: E402

main()
