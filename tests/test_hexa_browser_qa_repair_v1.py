"""HEXA-BROWSER-QA-REPAIR-V1 regressions.

Findings covered:

- ``F1`` — the customer Node 06 popup exposed the approved *selling quote* money
  (and could expose debt figures) while finance disclosure was unapproved or
  revoked. Quote stays at Node 00 and in Hồ sơ & Chứng từ; it must not appear
  at Node 06 while finance is unapproved/revoked.
- ``F2`` — at 390x844 the ``fitJourney()`` lower zoom clamp (0.65) plus the
  single-row desktop geometry pushed Node 00/06 outside the map viewport.
- ``G1`` — the ``/tt`` desk had no finance_write-only actions for receipt
  confirmation/allocation, financial publication approval and financial
  publication revoke, even though the HTTP API and the Financial Ledger already
  existed.

Runtime evidence: ``RUNTIME_VISUAL_REVIEW=NO``. The DOM assertions below run the
real shipped browser script inside a deterministic ``node`` VM with a simulated
viewport; no real Chromium render was inspected, so ``BROWSER_QA=NOT_RUN`` and
no pixel/visual PASS is claimed here.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from core import database as core_db
from core.hexa_trial_portal import (
    SHIPMENT_A_ID,
    HexaTrialEnvironment,
    create_trial_http_server,
    seed_live_preview_publications,
)

CUSTOMER_USERNAME = "lucgiac.trial"
CUSTOMER_PASSCODE = "LG-Trial-2026!"
OPS_CREDENTIALS = ("tt.ops.truongthanh", "TT-Trial-2026!")
FINANCE_CREDENTIALS = ("tt.finance.truongthanh", "TT-Finance-2026!")
SERVICE_OBLIGATION_ID = "OBL-LG01-SVC-01"

# Money tokens that must never leak into the Node 06 popup while the customer is
# not allowed to see finance: the approved quote total, the seeded paid amount,
# the seeded outstanding balance, and a zero-balance render.
NODE06_FORBIDDEN_TOKENS = (
    "57.240.000",
    "30.000.000",
    "27.240.000",
    "0 VND",
    "Báo giá bán đã duyệt",
)

NODE = shutil.which("node")
requires_node = pytest.mark.skipif(NODE is None, reason="node runtime not installed")


# --------------------------------------------------------------------------- #
# HTTP fixture (isolated trial server; SANDBOX_STAGING / mongomock only)
# --------------------------------------------------------------------------- #
def _http_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    session_token: str | None = None,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, bytes]:
    req_headers: dict[str, str] = dict(headers or {})
    if session_token is not None:
        req_headers["Authorization"] = f"Bearer {session_token}"
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", data=data, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except HTTPError as exc:
        return exc.code, exc.read()


@pytest.fixture()
def trial_server():
    env = HexaTrialEnvironment()
    env.ensure_seeded(force_reset=True)
    server = create_trial_http_server(host="127.0.0.1", port=0, env=env)
    host, port = server.server_address[:2]
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield base_url, env
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _tt_login(base_url: str, credentials: tuple[str, str]) -> str:
    status, raw = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": credentials[0], "passcode": credentials[1]},
    )
    assert status == 200, raw
    return json.loads(raw.decode("utf-8"))["session_token"]


def _customer_login(base_url: str) -> str:
    status, raw = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": CUSTOMER_USERNAME, "passcode": CUSTOMER_PASSCODE},
    )
    assert status == 200, raw
    return json.loads(raw.decode("utf-8"))["session_token"]


def _customer_dashboard(base_url: str, token: str) -> dict[str, Any]:
    status, raw = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=token)
    assert status == 200, raw
    return json.loads(raw.decode("utf-8"))


def _customer_shipment(base_url: str, token: str, shipment_id: str = SHIPMENT_A_ID) -> dict[str, Any]:
    dashboard = _customer_dashboard(base_url, token)
    return next(item for item in dashboard["shipments"] if item["shipment_id"] == shipment_id)


def _current_publication(env: HexaTrialEnvironment) -> dict[str, Any]:
    db = core_db.get_db()
    assert db is not None
    return db["hexa_trial_publications"].find_one(
        {"shipment_id": SHIPMENT_A_ID}, {"_id": 0}
    ) or {}


# --------------------------------------------------------------------------- #
# Deterministic browser-script harness (real shipped JS, simulated viewport)
# --------------------------------------------------------------------------- #
_DOM_PRELUDE = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.env.HTML_PATH, 'utf8');
const VIEW_W = Number(process.env.VIEW_W);
const VIEW_H = Number(process.env.VIEW_H);
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('NO_SCRIPT'); process.exit(2); }

function makeEl(tag, dims) {
  let _text = '';
  const classes = new Set();
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    style: {}, dataset: {}, attrs: {}, value: '', children: [], className: '',
    classList: {
      add(...cs) { cs.forEach(c => classes.add(c)); el.className = Array.from(classes).join(' '); },
      remove(...cs) { cs.forEach(c => classes.delete(c)); el.className = Array.from(classes).join(' '); },
      toggle(c, force) {
        if (force === undefined) { classes.has(c) ? classes.delete(c) : classes.add(c); }
        else if (force) { classes.add(c); } else { classes.delete(c); }
        el.className = Array.from(classes).join(' ');
      },
      contains(c) { return classes.has(c); }
    },
    appendChild(child) { this.children.push(child); return child; },
    removeChild(child) { this.children = this.children.filter(c => c !== child); return child; },
    append(...kids) { kids.forEach(k => this.children.push(k)); },
    get firstChild() { return this.children[0] || null; },
    addEventListener(ev, fn) { this['on' + ev] = fn; },
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'class') this.className = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    get clientWidth() { return (dims && dims.w) || VIEW_W; },
    get clientHeight() { return (dims && dims.h) || VIEW_H; },
    get offsetWidth() { return (dims && dims.w) || VIEW_W; },
    get offsetHeight() { return (dims && dims.h) || VIEW_H; },
    getBoundingClientRect() { return { width: this.clientWidth, height: this.clientHeight, left: 0, top: 0 }; },
    get textContent() {
      if (this.children.length > 0) return _text + this.children.map(c => c.textContent).join(' ');
      return _text;
    },
    set textContent(v) { _text = String(v ?? ''); this.children = []; },
    set innerHTML(v) { if (v === '') { this.children = []; _text = ''; } }
  };
  return el;
}

const elements = {};
const document = {
  getElementById(id) {
    if (!elements[id]) {
      if (id === 'journey-map-viewport') elements[id] = makeEl('div', { w: VIEW_W, h: VIEW_H });
      else elements[id] = makeEl('div');
    }
    return elements[id];
  },
  createElement(tag) { return makeEl(tag); },
  createElementNS(_ns, tag) { return makeEl(tag); },
  querySelectorAll() { return []; },
  body: makeEl('body')
};
"""

_PORTAL_DOM_HARNESS = _DOM_PRELUDE + r"""
const dashData = JSON.parse(process.env.DASH_JSON);
const sandbox = {
  document,
  window: { addEventListener() {}, open() {}, innerWidth: VIEW_W, innerHeight: VIEW_H },
  Intl, encodeURIComponent, Math, Number, JSON, String, Array, Object, Boolean, console,
  setTimeout, clearTimeout,
  fetch: async () => ({ ok: true, status: 200, json: async () => dashData })
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

(async () => {
  await sandbox.renderDashboardData(dashData);
  await sandbox.selectShipmentForJourney('ROAD-LG-001');
  /*BODY*/
})().catch(err => { console.error('HARNESS_FAIL: ' + (err && err.stack ? err.stack : err)); process.exit(1); });
"""

_TT_DESK_HARNESS = _DOM_PRELUDE + r"""
const session = JSON.parse(process.env.TT_SESSION_JSON);
const shipment = JSON.parse(process.env.TT_SHIPMENT_JSON);
const sandbox = {
  document,
  window: { addEventListener() {}, open() {}, __HEXA_TT_TOKEN: 'harness-token' },
  sessionStorage: { getItem() { return 'harness-token'; }, setItem() {}, removeItem() {} },
  Intl, encodeURIComponent, Math, Number, JSON, String, Array, Object, Boolean, console,
  setTimeout, clearTimeout,
  fetch: async (url) => ({
    ok: true,
    status: 200,
    json: async () => (String(url).indexOf('/tt/session') >= 0 ? session : shipment)
  })
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

(async () => {
  document.getElementById('tt-shipment-input').value = 'ROAD-LG-001';
  await sandbox.initTtDesk();
  const section = document.getElementById('tt-finance-section');
  if (!section) throw new Error('TT finance section missing');
  const visible = !section.classList.contains('hidden');
  const expected = session.can_finance_write === true;
  if (visible !== expected) throw new Error('finance desk gate mismatch: visible=' + visible + ' expected=' + expected);
  if (expected) {
    const obligations = document.getElementById('tt-fin-obligation');
    if (!obligations || obligations.children.length === 0) throw new Error('obligation options missing for finance staff');
  }
  console.log('TT_FINANCE_DESK_OK');
})().catch(err => { console.error('HARNESS_FAIL: ' + (err && err.stack ? err.stack : err)); process.exit(1); });
"""


def _run_node(script: str, env_extra: dict[str, str]) -> str:
    proc = subprocess.run(
        [NODE or "node", "-e", script],
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            **env_extra,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"node harness failed: {proc.stdout} {proc.stderr}"
    return proc.stdout


def _portal_dom(base_url: str, dashboard: dict[str, Any], body_js: str, *, width: int, height: int) -> str:
    status, raw_html = _http_request(base_url, "/")
    assert status == 200
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh:
        fh.write(raw_html.decode("utf-8"))
        html_path = fh.name
    try:
        return _run_node(
            _PORTAL_DOM_HARNESS.replace("/*BODY*/", body_js),
            {
                "HTML_PATH": html_path,
                "DASH_JSON": json.dumps(dashboard),
                "VIEW_W": str(width),
                "VIEW_H": str(height),
            },
        )
    finally:
        os.unlink(html_path)


def _node06_text(base_url: str, dashboard: dict[str, Any]) -> str:
    body = r"""
  sandbox.openStageModal('finance-reconciliation', 'info');
  console.log(document.getElementById('journey-modal-body').textContent);
"""
    return _portal_dom(base_url, dashboard, body, width=1348, height=660)


# --------------------------------------------------------------------------- #
# F1 — Node 06 must not expose quote money (or any debt figure) while finance
#      disclosure is unapproved / revoked.
# --------------------------------------------------------------------------- #
@requires_node
def test_f1_node06_hides_quote_and_debt_until_finance_is_approved(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    customer_token = _customer_login(base_url)
    finance_token = _tt_login(base_url, FINANCE_CREDENTIALS)

    # 1. Shipment + progress + quote are published, finance disclosure is NOT.
    dashboard = _customer_dashboard(base_url, customer_token)
    assert next(s for s in dashboard["shipments"] if s["shipment_id"] == SHIPMENT_A_ID)["debt_summary"]["status"] == "UNKNOWN"

    unapproved_text = _node06_text(base_url, dashboard)
    assert "UNKNOWN / Chưa đối soát" in unapproved_text
    for token in NODE06_FORBIDDEN_TOKENS:
        assert token not in unapproved_text, f"F1 leak at Node 06 while finance unapproved: {token}"

    # 2. Node 00 keeps the approved selling quote (policy unchanged).
    node00_text = _portal_dom(
        base_url,
        dashboard,
        r"""
  sandbox.openStageModal('plan', 'info');
  console.log(document.getElementById('journey-modal-body').textContent);
""",
        width=1348,
        height=660,
    )
    assert "57.240.000 VND" in node00_text
    assert "QT-20261022-LG01" in node00_text

    # 3. Finance explicitly approves publication: Node 06 may now show real debt.
    publication = _current_publication(env)
    env.publish_shipment_for_customer(
        session_token=finance_token,
        shipment_id=SHIPMENT_A_ID,
        event_versions=publication.get("event_versions") or {},
        document_versions=publication.get("document_versions") or {},
        quote=publication.get("quote"),
        approve_finance=True,
    )
    approved_dashboard = _customer_dashboard(base_url, customer_token)
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "CONFIRMED"
    approved_text = _node06_text(base_url, approved_dashboard)
    assert "57.240.000 VND" in approved_text
    assert "Chưa đối soát" not in approved_text

    # 4. Finance revoke closes the disclosure again: no quote, no debt figure.
    env.revoke_shipment_publication(
        session_token=finance_token,
        shipment_id=SHIPMENT_A_ID,
        revoke_finance=True,
    )
    revoked_dashboard = _customer_dashboard(base_url, customer_token)
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "UNKNOWN"
    revoked_text = _node06_text(base_url, revoked_dashboard)
    for token in NODE06_FORBIDDEN_TOKENS:
        assert token not in revoked_text, f"F1 leak at Node 06 after finance revoke: {token}"
    assert "UNKNOWN / Chưa đối soát" in revoked_text


# --------------------------------------------------------------------------- #
# F2 — 390x844 must fit all seven nodes; 1440x900 geometry stays as designed.
# --------------------------------------------------------------------------- #
_F2_GEOMETRY_BODY = r"""
  sandbox.fitJourney();
  const tf = document.getElementById('journey-map-transform');
  const match = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(String(tf.style.transform || ''));
  if (!match) throw new Error('fitJourney produced no transform: ' + tf.style.transform);
  const panX = Number(match[1]), panY = Number(match[2]), scale = Number(match[3]);
  const nodes = document.getElementById('journey-nodes-layer').children;
  const px = (v) => Number(String(v || '0').replace('px', ''));
  const rects = nodes.map((el) => {
    const x = px(el.style.left), y = px(el.style.top);
    const w = px(el.style.width), h = px(el.style.height);
    return {
      id: String(el.dataset.testid || ''),
      x: x, y: y, w: w, h: h,
      left: panX + x * scale, top: panY + y * scale,
      right: panX + (x + w) * scale, bottom: panY + (y + h) * scale,
      clickable: typeof el.onclick === 'function'
    };
  });
  if (rects.length !== 7) throw new Error('expected 7 journey nodes, got ' + rects.length);
  for (const r of rects) {
    if (!r.clickable) throw new Error('node not clickable: ' + r.id);
    if (r.left < -0.5 || r.top < -0.5 || r.right > VIEW_W + 0.5 || r.bottom > VIEW_H + 0.5) {
      throw new Error('node outside map viewport: ' + JSON.stringify(r));
    }
    if ((r.right - r.left) < 70 || (r.bottom - r.top) < 50) {
      throw new Error('node shrunk below readability floor: ' + JSON.stringify(r));
    }
  }
  // Fit / Đọc rõ controls live in the bottom control band and must not cover nodes.
  for (const r of rects) {
    if (r.bottom > VIEW_H - 52) throw new Error('node overlaps the zoom control band: ' + JSON.stringify(r));
  }
  console.log(JSON.stringify({ scale: scale, rects: rects }));
"""


@requires_node
def test_f2_mobile_fit_keeps_all_seven_nodes_visible_and_desktop_unchanged(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    customer_token = _customer_login(base_url)
    dashboard = _customer_dashboard(base_url, customer_token)

    # 390x844 viewport => 358 x 614 map canvas (page padding 16px each side).
    mobile_raw = _portal_dom(base_url, dashboard, _F2_GEOMETRY_BODY, width=358, height=614)
    mobile = json.loads(mobile_raw.strip().splitlines()[-1])
    assert mobile["scale"] >= 0.9, f"mobile fit over-shrinks the map: {mobile['scale']}"
    mobile_nodes = {r["id"]: r for r in mobile["rects"]}
    assert "journey-node-plan" in mobile_nodes and "journey-node-finance-reconciliation" in mobile_nodes
    assert mobile_nodes["journey-node-plan"]["left"] >= 0
    assert mobile_nodes["journey-node-finance-reconciliation"]["right"] <= 358
    # Two rows are allowed; a single 1080px row is not (that is what pushed 00/06 off screen).
    assert len({round(r["y"]) for r in mobile["rects"]}) >= 2

    # The node -> bubble -> popup flow still works on mobile.
    flow_output = _portal_dom(
        base_url,
        dashboard,
        r"""
  sandbox.fitJourney();
  sandbox.selectJourneyNode('plan');
  const bubble = document.getElementById('journey-bubble-slot').children[0];
  if (!bubble || bubble.dataset.testid !== 'journey-bubble') throw new Error('node -> bubble flow broken on mobile');
  if (String(bubble.getAttribute('data-node')) !== 'plan') throw new Error('bubble bound to the wrong node');
  sandbox.openStageModal('plan', 'info');
  if (document.getElementById('journey-modal-layer').classList.contains('hidden')) throw new Error('bubble -> popup flow broken on mobile');
  console.log('MOBILE_NODE_BUBBLE_POPUP_OK');
""",
        width=358,
        height=614,
    )
    assert "MOBILE_NODE_BUBBLE_POPUP_OK" in flow_output

    # 1440x900 viewport => 1348 x 660 map canvas; desktop geometry must not regress.
    desktop_raw = _portal_dom(base_url, dashboard, _F2_GEOMETRY_BODY, width=1348, height=660)
    desktop = json.loads(desktop_raw.strip().splitlines()[-1])
    desktop_nodes = {r["id"]: r for r in desktop["rects"]}
    assert [round(desktop_nodes[f"journey-node-{nid}"]["x"]) for nid in (
        "plan", "pickup", "road-ltl", "road-border", "customs-import", "delivery", "finance-reconciliation",
    )] == [24, 172, 320, 468, 616, 764, 912]
    assert {round(r["y"]) for r in desktop["rects"]} == {205}
    assert round(desktop_nodes["journey-node-plan"]["w"]) == 116
    assert round(desktop_nodes["journey-node-plan"]["h"]) == 66


# --------------------------------------------------------------------------- #
# G1 — Finance actions on the /tt desk, gated to finance_write staff.
# --------------------------------------------------------------------------- #
@requires_node
def test_g1_tt_desk_finance_section_is_gated_by_finance_write(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    finance_token = _tt_login(base_url, FINANCE_CREDENTIALS)
    ops_token = _tt_login(base_url, OPS_CREDENTIALS)
    status, raw_html = _http_request(base_url, "/tt", session_token=finance_token)
    assert status == 200
    desk_html = raw_html.decode("utf-8")
    for label in (
        "Xác nhận đã nhận tiền",
        "Duyệt công bố số liệu tài chính",
        "Thu hồi công bố tài chính",
    ):
        assert label in desk_html
    assert "KHÔNG tự ghi nhận thanh toán" in desk_html

    st_fin, raw_fin = _http_request(base_url, "/api/hexa/v0/tt/session", session_token=finance_token)
    st_ops, raw_ops = _http_request(base_url, "/api/hexa/v0/tt/session", session_token=ops_token)
    assert st_fin == 200 and st_ops == 200
    fin_session = json.loads(raw_fin.decode("utf-8"))
    ops_session = json.loads(raw_ops.decode("utf-8"))
    assert fin_session["can_finance_write"] is True
    assert ops_session["can_finance_write"] is False

    status, raw_detail = _http_request(
        base_url, f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}", session_token=finance_token
    )
    assert status == 200
    shipment_detail = json.loads(raw_detail.decode("utf-8"))

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh:
        fh.write(desk_html)
        html_path = fh.name
    try:
        for session_payload in (fin_session, ops_session):
            output = _run_node(
                _TT_DESK_HARNESS,
                {
                    "HTML_PATH": html_path,
                    "VIEW_W": "390",
                    "VIEW_H": "844",
                    "TT_SESSION_JSON": json.dumps(session_payload),
                    "TT_SHIPMENT_JSON": json.dumps(shipment_detail),
                },
            )
            assert "TT_FINANCE_DESK_OK" in output
    finally:
        os.unlink(html_path)


def test_g1_finance_confirm_publish_revoke_over_http(trial_server) -> None:
    from core.financial_ledger import ALLOCATIONS, TRANSACTIONS

    base_url, env = trial_server
    seed_live_preview_publications(env)
    finance_token = _tt_login(base_url, FINANCE_CREDENTIALS)
    ops_token = _tt_login(base_url, OPS_CREDENTIALS)
    customer_token = _customer_login(base_url)
    db = core_db.get_db()
    assert db is not None

    def confirm(token: str, txn_id: str, amount: float, *, obligation_id: str = SERVICE_OBLIGATION_ID):
        return _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/finance/confirm",
            method="POST",
            session_token=token,
            json_body={
                "transaction_id": txn_id,
                "obligation_id": obligation_id,
                "amount": amount,
                "currency": "VND",
                "occurred_at": "2026-10-23",
                "note": "G1 finance desk regression",
            },
        )

    def approve_finance(token: str):
        publication = _current_publication(env)
        return _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
            method="POST",
            session_token=token,
            json_body={
                "event_versions": publication.get("event_versions") or {},
                "document_versions": publication.get("document_versions") or {},
                "quote": publication.get("quote"),
                "approve_finance": True,
            },
        )

    # Operations can never confirm money or approve financial disclosure.
    st_ops_confirm, _ = confirm(ops_token, "TXN-G1-OPS", 1_000_000)
    assert st_ops_confirm == 403
    assert db[TRANSACTIONS].find_one({"id": "TXN-G1-OPS"}) is None
    st_ops_publish, _ = approve_finance(ops_token)
    assert st_ops_publish == 403
    assert _current_publication(env).get("finance_published") is False

    # Finance confirms a receipt and allocates it to this lot's obligation.
    status, raw = confirm(finance_token, "TXN-G1-01", 1_000_000)
    assert status == 200, raw
    # Exact replay is idempotent: no duplicate transaction / allocation rows.
    status, raw = confirm(finance_token, "TXN-G1-01", 1_000_000)
    assert status == 200, raw
    assert db[TRANSACTIONS].count_documents({"id": "TXN-G1-01"}) == 1
    assert db[ALLOCATIONS].count_documents({"transaction_id": "TXN-G1-01"}) == 1

    # Allocation above the outstanding balance is rejected before any write.
    st_over, _ = confirm(finance_token, "TXN-G1-OVER", 99_000_000)
    assert st_over == 403
    assert db[TRANSACTIONS].find_one({"id": "TXN-G1-OVER"}) is None

    # Confirming money never self-publishes: the customer still sees UNKNOWN.
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "UNKNOWN"

    # Customer-sent UNC is evidence only and never confirms payment.
    unc_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    before_txns = db[TRANSACTIONS].count_documents({})
    st_sub, raw_sub = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/stages/finance-reconciliation/submissions",
        method="POST",
        session_token=customer_token,
        json_body={
            "comment": "Khách gửi ủy nhiệm chi (UNC) cho lô ROAD-LG-001.",
            "file_name": "UNC-G1.pdf",
            "mime": "application/pdf",
            "file_base64": base64.b64encode(unc_pdf).decode("ascii"),
        },
    )
    assert st_sub == 200, raw_sub
    assert db[TRANSACTIONS].count_documents({}) == before_txns
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "UNKNOWN"

    # Finance approves disclosure: the customer sees reconciled numbers, still not settled.
    st_ok, raw_ok = approve_finance(finance_token)
    assert st_ok == 200, raw_ok
    disclosed = _customer_shipment(base_url, customer_token)
    assert disclosed["debt_summary"]["status"] == "CONFIRMED"
    assert disclosed["debt_summary"]["total_payable"] == 57_240_000.0
    assert disclosed["debt_summary"]["total_paid"] == 31_000_000.0
    assert disclosed["debt_summary"]["remaining_balance"] == 26_240_000.0
    fin_node = next(n for n in disclosed["journey"]["nodes"] if n["id"] == "finance-reconciliation")
    assert fin_node["completed"] is False
    assert fin_node["finance_detail"]["completed"] is False

    # A new confirmed receipt changes the finance source fingerprint and closes the gate.
    status, raw = confirm(finance_token, "TXN-G1-02", 26_240_000)
    assert status == 200, raw
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "UNKNOWN"
    assert _current_publication(env).get("finance_published") is False

    # Finance re-approves; a fully paid lot still waits for settlement (never auto-DONE).
    st_ok, raw_ok = approve_finance(finance_token)
    assert st_ok == 200, raw_ok
    settled_pending = _customer_shipment(base_url, customer_token)
    assert settled_pending["debt_summary"]["remaining_balance"] == 0.0
    assert "Chờ quyết toán" in settled_pending["debt_summary"]["status_label"]
    fin_node = next(n for n in settled_pending["journey"]["nodes"] if n["id"] == "finance-reconciliation")
    assert fin_node["completed"] is False
    assert fin_node["finance_detail"]["completed"] is False

    # Finance revoke hides every figure again, and republishing as operations cannot reopen it.
    st_rev, raw_rev = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=finance_token,
        json_body={"revoke_finance": True},
    )
    assert st_rev == 200, raw_rev
    revoked = _customer_shipment(base_url, customer_token)
    assert revoked["debt_summary"]["status"] == "UNKNOWN"
    assert revoked["debt_summary"]["total_payable"] is None
    assert revoked["debt_summary"]["total_paid"] is None
    assert revoked["debt_summary"]["remaining_balance"] is None
    st_ops_republish, _ = approve_finance(ops_token)
    assert st_ops_republish == 403
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "UNKNOWN"

    # Another customer never sees this lot or its finance.
    st_md, raw_md = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "minhduc.trial", "passcode": "MD-Trial-2026!"},
    )
    assert st_md == 200
    md_token = json.loads(raw_md.decode("utf-8"))["session_token"]
    st_md_dash, raw_md_dash = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=md_token)
    assert st_md_dash == 200
    md_text = raw_md_dash.decode("utf-8")
    assert "ROAD-LG-001" not in md_text
    assert "OBL-LG01-SVC-01" not in md_text
