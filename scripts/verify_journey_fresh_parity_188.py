#!/usr/bin/env python3
"""Issue #188 bounded acceptance host — a production-shaped FRESH shipment.

Isolated in-process ``mongomock`` staging only (``SANDBOX_STAGING``), exactly
like ``scripts/verify_visual_shipment_workspace.py``: no real ``MONGO_URI``, no
production database, no secrets, no deploy, no ``tienthanhlog``.

Why a second host exists at all
-------------------------------
The Owner-observed production failure was a *fresh* shipment
(``journey.nodes=[]``) losing the approved cockpit. The #160 host only ever
served a fully populated SEA-160, so that production shape was never
exercised. This host serves the missing shape and nothing else.

The fixture is created through the SAME canonical handler the Create Shipment
screen uses (``vm.consume_phase_b_triggers`` → ``shipment_create``), with no
first mode, no Incoterm and no service scope — i.e. exactly what the create
form persists when the operator has not stated those facts yet. The host then
FAILS CLOSED unless the persisted shipment is truthfully:

* persisted (fresh canonical readback sees it);
* profile-incomplete / scope-unconfirmed;
* ``journey.nodes == []``;
* free of fabricated mode / transport legs / service scope.

``/fixture`` exposes that server-side truth so the real-browser lane can prove
the DOM it renders belongs to a genuinely zero-node shipment instead of
trusting DOM markers alone.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from views import logi_sandbox, logi_view_model as vm  # noqa: E402

FRESH_ID = "SEA-188"
FRESH_CUSTOMER_ID = "CUST-MOI-188"
FRESH_CUSTOMER_NAME = "Khách hàng mới 188"
PROFILE_ANCHOR = "shipment-execution-profile"

_state: dict = {}


def build_fresh_fixture() -> dict:
    """Create the fresh shipment canonically and verify the fixture truth."""
    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

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
    assert outcomes and outcomes[0].get("ok"), outcomes
    doc = vm.read_shipment(FRESH_ID) or {}
    assert doc, "fresh shipment was not persisted"
    head = (doc.get("data") or {}).get("0.0") or {}
    assert not head.get("execution_profile"), "fixture must not carry a confirmed profile"
    assert not head.get("mode"), "fixture must not carry a first mode"
    assert not head.get("incoterm"), "fixture must not carry an Incoterm"
    assert not (doc.get("data") or {}).get("1.2", {}).get("transport_legs"), "no fabricated legs"

    model = vm.build_view_model()
    row = next((s for s in model.get("shipments", []) if s.get("id") == FRESH_ID), None)
    assert row is not None, "fresh shipment missing from the view model"
    journey = row.get("journey") or {}
    assert journey.get("nodes") == [], f"fixture is not zero-node: {journey.get('nodes')!r}"
    profile = row.get("executionProfile") or {}
    assert profile.get("state") == "PROFILE_INCOMPLETE", profile.get("state")
    assert profile.get("serviceScopeConfirmed") is False, "scope must stay unconfirmed"
    assert not profile.get("serviceScope"), "no fabricated service scope"
    # Supervisor B1: the projected profile action must own the tab that actually
    # mounts ShipmentExecutionProfile (van-tai), never the status tab.
    projected = (journey.get("primaryAction") or {}).get("route")
    assert projected == f"/lo-hang/{FRESH_ID}?tab=van-tai#{PROFILE_ANCHOR}", projected
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
        "transportLegs": 0,
        # Attention is a top-level projection the detail page filters by
        # shipmentId (ShipmentDetail.tsx), so count it the same way.
        "attentionItems": len(
            [i for i in (model.get("attention") or []) if i.get("shipmentId") == FRESH_ID]
        ),
        "primaryAction": (journey.get("primaryAction") or {}).get("text"),
        "projectedPrimaryRoute": projected,
        "nextRoute": row.get("nextRoute"),
        "nextAction": row.get("nextAction"),
        "nextActionDetail": row.get("nextActionDetail"),
    }


HTML = """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/logi-shell.css"><body><div id="host"></div>
<script type="module">
import mount from '/logi-shell.js';
const deliver=data=>mount({name:'logi_shell',data,parentElement:document.getElementById('host'),
  setTriggerValue:async(event,value)=>{if(event==='navigate')return;
    const r=await fetch('/event',{method:'POST',body:JSON.stringify({event,value})});
    deliver(await r.json());}});
deliver(await (await fetch('/model')).json());
window.deliver=deliver;
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, data: bytes, mime: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 - stdlib handler API
        if self.path == "/model":
            return self._send(
                json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), "application/json"
            )
        if self.path == "/fixture":
            return self._send(json.dumps(_state, ensure_ascii=False).encode(), "application/json")
        if self.path in ("/logi-shell.js", "/logi-shell.css"):
            path = ROOT / "component/dist" / self.path[1:]
            mime = "application/javascript" if path.suffix == ".js" else "text/css"
            return self._send(path.read_bytes(), mime)
        self._send(HTML.encode(), "text/html; charset=utf-8")

    def do_POST(self):  # noqa: N802 - stdlib handler API
        if self.path != "/event":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        event = body["event"]
        # Bounded verification events only: the fresh fixture must produce no
        # fabricated business write just because a read-only surface was read.
        assert event in ("shipment_sea_facts_save", "finance_actual_save", "shipment_create"), event
        outcomes = vm.consume_phase_b_triggers({"seq": 0}, {event: body["value"]})
        st.session_state[vm.LAST_WRITES_KEY] = outcomes
        self._send(
            json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), "application/json"
        )

    def log_message(self, *args):  # keep the acceptance log clean
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #188 fresh-shipment acceptance host")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9502)
    parser.add_argument("--dump-fixture", metavar="PATH", help="write the fixture truth to PATH and exit")
    parser.add_argument(
        "--dump-model",
        metavar="PATH",
        help="write {'before': <view model>, 'meta': <fixture truth>} to PATH and exit "
        "(the shape tests/component/dom_acceptance_*.mjs consume)",
    )
    args = parser.parse_args()

    _state.update(build_fresh_fixture())
    if args.dump_fixture:
        pathlib.Path(args.dump_fixture).write_text(
            json.dumps(_state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(_state, ensure_ascii=False))
        return 0
    if args.dump_model:
        payload = {"before": vm.build_view_model(), "meta": dict(_state)}
        pathlib.Path(args.dump_model).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(_state, ensure_ascii=False))
        return 0

    print(
        f"Issue #188 fresh-shipment acceptance host: http://{args.host}:{args.port} "
        f"({FRESH_ID}, journey.nodes=[])",
        flush=True,
    )
    HTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
