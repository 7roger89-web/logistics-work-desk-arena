#!/usr/bin/env python3
"""#160 local browser acceptance host: canonical mongomock only, never production.

Run from repo root: python scripts/verify_visual_shipment_workspace.py
Serves the shipped bundle and forwards test clicks to the existing dispatcher.
This is a verification script, not an application API or deployment surface.
"""
import json
import pathlib
import runpy
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import streamlit as st
from views import logi_sandbox, logi_view_model as vm
from core.database import save_shipment_atomic

logi_sandbox.reset_backend()
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
st.session_state['current_user'] = dict(logi_sandbox.STAGING_ACTOR)
helper = runpy.run_path(str(ROOT / 'tests/test_visual_shipment_workspace.py'))
doc = helper['document'](); doc.pop('version')
assert save_shipment_atomic(doc, actor='issue160-browser-fixture')
st.session_state[vm.LAST_WRITES_KEY] = []

HTML = '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/logi-shell.css"><body><div id="host"></div><script type="module">
import mount from '/logi-shell.js';
const deliver=data=>mount({name:'logi_shell',data,parentElement:document.getElementById('host'),setTriggerValue:async(event,value)=>{if(event==='navigate')return;const r=await fetch('/event',{method:'POST',body:JSON.stringify({event,value})});deliver(await r.json());}});
deliver(await (await fetch('/model')).json());
window.deliver=deliver;
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def send(self, data, mime):
        self.send_response(200); self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path == '/model': return self.send(json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), 'application/json')
        if self.path in ('/logi-shell.js', '/logi-shell.css'):
            p = ROOT / 'component/dist' / self.path[1:]
            return self.send(p.read_bytes(), 'application/javascript' if p.suffix == '.js' else 'text/css')
        self.send(HTML.encode(), 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path != '/event': self.send_error(404); return
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        event = body['event']
        assert event in ('shipment_sea_facts_save', 'finance_actual_save'), 'bounded verification events only'
        outcomes = vm.consume_phase_b_triggers({'seq': 0}, {event: body['value']})
        st.session_state[vm.LAST_WRITES_KEY] = outcomes
        self.send(json.dumps(vm.build_view_model(), ensure_ascii=False).encode(), 'application/json')

    def log_message(self, *args): pass

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--fixture':
        before = vm.build_view_model()
        result = vm.consume_phase_b_triggers({'seq': 0}, {'shipment_sea_facts_save': {'seq': 1, 'payload': {
            'shipmentId': 'SEA-160', 'requestId': 'SEA-FIXTURE', 'expectedVersion': vm.read_shipment('SEA-160')['version'],
            'fields': {'si_status': 'ACCEPTED', 'vgm_status': 'ACCEPTED', 'si_cutoff': '2026-10-01'}}}})
        assert result[0]['ok'], result
        st.session_state[vm.LAST_WRITES_KEY] = result
        after = vm.build_view_model()
        st.session_state['current_user'] = {'username': 'viewer160', 'role': 'VIEWER', 'active': True}
        viewer = vm.build_view_model()
        pathlib.Path(sys.argv[2]).write_text(json.dumps({'before': before, 'after': after, 'viewer': viewer}, ensure_ascii=False))
        sys.exit(0)
    print('Isolated #160 acceptance host: http://127.0.0.1:9501', flush=True)
    HTTPServer(('127.0.0.1', 9501), Handler).serve_forever()
