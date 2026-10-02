#!/usr/bin/env python3
"""Issue #162 local acceptance host: canonical mongomock only, never production.

Two modes, both on the isolated staging transport:

    python scripts/verify_work_module_library_162.py --fixture /tmp/log162-dom.json
        Build real backend snapshots (base journey → attach → step completion →
        refusal → viewer) by driving the EXISTING dispatcher, then exit.

    python scripts/verify_work_module_library_162.py
        Serve the shipped bundle + the same dispatcher on loopback:9502 for the
        real-browser acceptance.

This is verification tooling, not an application API or a deployment surface.
"""
import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import streamlit as st  # noqa: E402
from views import logi_sandbox, logi_view_model as vm  # noqa: E402
from core.database import save_shipment_atomic  # noqa: E402

SHIPMENT_ID = "SEA-162"
BOUNDED_EVENTS = ("work_module_attach", "work_module_step_complete", "work_module_template_save", "shipment_sea_facts_save")


def _document() -> dict:
    """A shipment whose confirmed scope owns import customs + final delivery."""
    return {
        "id": SHIPMENT_ID, "customer": "An Phát JSC", "customer_id": "CUST-ANPHAT", "status": "wait",
        "currency": "VND",
        "data": {
            "0.0": {"mode": "Sea", "incoterm": "FOB", "execution_profile": {
                "incoterm_version": "2020", "incoterm_named_place": "Hai Phong", "load_model": "FCL",
                "service_scope": ["IMPORT_CUSTOMS", "FINAL_DELIVERY"], "service_scope_confirmed": True,
                "cargo_insurance": {"status": "NO"}}},
            "1.2": {"transport_legs": [
                {"id": "sea-162", "sequence": 1, "mode": "Sea", "origin": "Hai Phong",
                 "destination": "Singapore", "booking_no": "BK-162", "atd": "", "ata": "",
                 "units": [{"id": "cont-162", "kind": "container", "number": "ABCD1621621", "type_size": "40HC"}]}]},
            "2.4": {}, "2.6": {}, "2.7": {}, "3.4": {"details": [], "payments": []}, "entrustment": {},
        },
    }


def bootstrap(actor: dict | None = None) -> None:
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = actor or dict(logi_sandbox.STAGING_ACTOR)
    doc = _document()
    assert save_shipment_atomic(doc, actor="issue162-fixture")
    st.session_state[vm.LAST_WRITES_KEY] = []


def _dispatch(seq: int, event: str, payload: dict) -> dict:
    return vm.consume_phase_b_triggers({"seq": seq - 1}, {event: {"seq": seq, "payload": payload}})[0]


def build_fixture() -> dict:
    """Real dispatcher snapshots for the DOM and browser acceptance.

    Every entry is a FULL view-model payload (what Streamlit would deliver), so
    the bundle renders the real application instead of a hand-made fragment.
    """
    bootstrap()
    before = vm.build_view_model()

    def version_of(model: dict) -> int:
        return next(row["version"] for row in model["shipments"] if row["id"] == SHIPMENT_ID)

    attach = _dispatch(1, "work_module_attach", {
        "shipmentId": SHIPMENT_ID, "templateId": "IMPORT_SPECIAL_HANDLING_DEMO_V1",
        "requestId": "DOM-ATTACH-162", "expectedVersion": version_of(before),
        "provenance": "MANUAL_ADDITION", "reason": "Kiểm chứng kiến trúc"})
    assert attach["ok"], attach
    instance_id = attach["instance"]["instance_id"]
    st.session_state[vm.LAST_WRITES_KEY] = [attach]
    attached = vm.build_view_model()

    first = _dispatch(2, "work_module_step_complete", {
        "shipmentId": SHIPMENT_ID, "instanceId": instance_id, "nodeId": "prepare-file",
        "requestId": "DOM-STEP-1", "expectedVersion": version_of(attached)})
    assert first["ok"], first
    st.session_state[vm.LAST_WRITES_KEY] = [first]
    partial = vm.build_view_model()

    second = _dispatch(3, "work_module_step_complete", {
        "shipmentId": SHIPMENT_ID, "instanceId": instance_id, "nodeId": "submit-process",
        "requestId": "DOM-STEP-2", "expectedVersion": version_of(partial)})
    assert second["ok"], second
    third = _dispatch(4, "work_module_step_complete", {
        "shipmentId": SHIPMENT_ID, "instanceId": instance_id, "nodeId": "result-received",
        "requestId": "DOM-STEP-3", "expectedVersion": version_of(partial) + 1})
    assert third["ok"], third
    st.session_state[vm.LAST_WRITES_KEY] = [third]
    done = vm.build_view_model()

    # A real refusal correlated to the request the browser would send.
    refusal = json.loads(json.dumps(attached))
    refusal["lastWrites"] = [{"event": "work_module_step_complete", "ok": False,
                              "requestId": "DOM-STEP-REFUSED", "shipmentId": SHIPMENT_ID,
                              "error": "Lô đã thay đổi — đọc lại dữ liệu trước khi ghi nhận."}]

    st.session_state["current_user"] = {"username": "viewer162", "role": "VIEWER",
                                        "user_id": "VIEWER-162", "active": True}
    viewer = vm.build_view_model()
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    def rollup(model: dict) -> dict:
        row = next(r for r in model["shipments"] if r["id"] == SHIPMENT_ID)
        return (row["journey"].get("modules") or [{}])[0]

    return {
        "meta": {
            "instanceId": instance_id,
            "shipmentId": SHIPMENT_ID,
            "versions": {"before": version_of(before), "attached": version_of(attached),
                         "partial": version_of(partial), "done": version_of(done)},
            "baseNodeCount": len([n for n in
                                  next(r for r in before["shipments"] if r["id"] == SHIPMENT_ID)["journey"]["nodes"]]),
        },
        "before": before, "attached": attached, "partial": partial, "done": done,
        "refusal": refusal, "viewer": viewer,
    }


HTML = '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/logi-shell.css"><body><div id="host"></div><script type="module">
import mount from '/logi-shell.js';
const deliver=data=>mount({name:'logi_shell',data,parentElement:document.getElementById('host'),setTriggerValue:async(event,value)=>{if(event==='navigate')return;const r=await fetch('/event',{method:'POST',body:JSON.stringify({event,value})});deliver(await r.json());}});
deliver(await (await fetch('/model')).json());
window.deliver=deliver;
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    session = {"seq": 0}

    def send(self, data, mime):
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/model":
            return self.send(json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), "application/json")
        if self.path in ("/logi-shell.js", "/logi-shell.css"):
            p = ROOT / "component/dist" / self.path[1:]
            return self.send(p.read_bytes(), "application/javascript" if p.suffix == ".js" else "text/css")
        self.send(HTML.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/event":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        event = body["event"]
        assert event in BOUNDED_EVENTS, f"bounded verification events only: {event}"
        # The browser sends the SAME envelope the app uses with Streamlit:
        # {"seq": n, "event": name, "payload": {...}} — pass it through verbatim.
        value = body["value"]
        self.session["seq"] = max(self.session["seq"], int(value.get("seq", 0)))
        outcomes = vm.consume_phase_b_triggers({"seq": self.session["seq"] - 1}, {event: value})
        st.session_state[vm.LAST_WRITES_KEY] = outcomes
        self.send(json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--fixture":
        fixture = build_fixture()
        pathlib.Path(sys.argv[2]).write_text(json.dumps(fixture, ensure_ascii=False))
        def rollup(model: dict) -> dict:
            row = next(r for r in model["shipments"] if r["id"] == SHIPMENT_ID)
            return row["journey"]["modules"][0]

        print(f"Wrote #162 fixture: {sys.argv[2]} "
              f"(rollup {rollup(fixture['attached'])['status']}/{rollup(fixture['attached'])['summary']} → "
              f"{rollup(fixture['partial'])['status']}/{rollup(fixture['partial'])['summary']} → "
              f"{rollup(fixture['done'])['status']}/{rollup(fixture['done'])['summary']}; "
              f"gate: {rollup(fixture['attached'])['gateText']})")
        sys.exit(0)
    bootstrap()
    print("Isolated #162 acceptance host: http://127.0.0.1:9502", flush=True)
    HTTPServer(("127.0.0.1", 9502), Handler).serve_forever()
