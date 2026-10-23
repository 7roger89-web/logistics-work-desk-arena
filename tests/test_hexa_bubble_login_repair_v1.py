"""Regression suite for HEXA-BUBBLE-CONTAINMENT-LOGIN-REPAIR (RED -> GREEN).

Covers the two real-Chrome defects confirmed on branch ``arena/36ca27f5-logistics-work-desk-arena``
at ``EXPECTED_HEAD = ac46fb197638b033789c51ec09c9984daffc89e7``:

1. **F2 — Node bubble containment, stacking context, clickability & mobile scroll**:
   - Mobile ``390x844``:
     * ``Node03`` bubble overflowed right edge of map/viewport;
     * ``Node06`` bubble overflowed left edge under pan/zoom;
     * ``Node00-03`` placed bubbles above Row 0 with ``translateY(-100%)``, clipping header
       and ``Close`` outside ``#journey-map-viewport`` (``overflow: hidden``) so ``Close``
       could not receive a normal click;
     * ``Node04/05`` placed bubbles below Row 1 past the bottom of ``#journey-map-viewport``
       and behind ``.journey-zoom-bar`` (``z-index: 20 > 2``), cutting off the bottom and
       ``Xem chi tiết`` button;
     * ``.journey-canvas`` enforced ``touch-action: none`` on mobile, blocking normal vertical
       touch scrolling.
   - Desktop ``1440x900``:
     * ``#journey-map-transform`` created a child stacking context at ``z-index: 2`` below
       ``[data-testid="journey-utility-trigger"]`` (``▤ Hồ sơ & Chứng từ``, ``z-index: 18``),
       so on ``Node05/06`` the top-right ``Close`` button landed directly behind
       ``▤ Hồ sơ & Chứng từ`` and ``document.elementFromPoint(cx, cy)`` hit the utility button
       instead of ``Close``.

2. **TT internal login (``render_tt_login_html()`` + ``/tt`` desk bootstrap)**:
   - Both ``<form onsubmit="event.preventDefault(); loginTt();">`` and
     ``<button type="submit" onclick="loginTt()">`` invoked ``loginTt()``, sending **2**
     ``POST /api/hexa/v0/tt/auth/login`` requests per click and calling ``document.write(html)``
     twice in the same JS global lexical scope, throwing
     ``SyntaxError: Identifier 'currentTtShipment' has already been declared`` and leaving
     ``/tt`` broken until manually re-navigated.

Runtime honesty note:
This suite runs the real shipped HTML/CSS/JS inside Node ``jsdom`` against a real local
``ThreadingHTTPServer`` + ``mongomock`` (``SANDBOX_STAGING``). Because Chromium/Chrome is
unavailable in the Arena sandbox, ``BROWSER_QA=NOT_RUN`` and no visual pixel PASS is claimed
from ``jsdom``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from core.hexa_trial_portal import (
    CUSTOMER_JOURNEY_STAGE_IDS,
    SHIPMENT_A_ID,
    HexaTrialEnvironment,
    create_trial_http_server,
    seed_live_preview_publications,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
JSDOM_MODULES = REPO_ROOT / "component" / "node_modules"
NODE = shutil.which("node")

CUSTOMER_CREDENTIALS = ("lucgiac.trial", "LG-Trial-2026!")
OPS_CREDENTIALS = ("tt.ops.truongthanh", "TT-Trial-2026!")
FINANCE_CREDENTIALS = ("tt.finance.truongthanh", "TT-Finance-2026!")

requires_jsdom = pytest.mark.skipif(
    NODE is None or not (JSDOM_MODULES / "jsdom").is_dir(),
    reason="node + component/node_modules/jsdom required",
)


def _http_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    session_token: str | None = None,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, str], bytes]:
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
            return resp.status, dict(resp.headers.items()), resp.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


@pytest.fixture()
def trial_server():
    env = HexaTrialEnvironment()
    env.ensure_seeded(force_reset=True)
    seed_live_preview_publications(env)
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


def _run_node_jsdom(script_body: str, extra_env: dict[str, str]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".cjs", delete=False) as fh:
        fh.write(script_body)
        script_path = fh.name
    try:
        env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "NODE_PATH": str(JSDOM_MODULES),
            **extra_env,
        }
        proc = subprocess.run(
            [NODE, script_path],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        assert proc.returncode == 0, f"Node jsdom harness failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        assert lines, f"Empty stdout from Node jsdom harness (stderr={proc.stderr})"
        return json.loads(lines[-1])
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Faithful W3C Box + Transform + Stacking-Context + Overflow-Clip + Hit-Test
# engine attached onto real JSDOM over the live ThreadingHTTPServer.
# --------------------------------------------------------------------------- #
_JSDOM_GEOMETRY_SCRIPT = r"""
const { JSDOM, VirtualConsole } = require('jsdom');

const BASE_URL = process.env.BASE_URL;
const VIEW_W = Number(process.env.VIEW_W);
const VIEW_H = Number(process.env.VIEW_H);
const USERNAME = process.env.CUST_USER;
const PASSCODE = process.env.CUST_PASS;
const SHIPMENT_ID = process.env.SHIPMENT_ID;

function parsePx(val, fallback = 0) {
  if (val === undefined || val === null || val === '') return fallback;
  const m = String(val).match(/^(-?\d+(?:\.\d+)?)px$/);
  return m ? Number(m[1]) : fallback;
}

function parseTransform(str, selfH) {
  let tx = 0, ty = 0, scale = 1, hasTransform = false;
  if (!str || str === 'none') return { tx, ty, scale, hasTransform };
  hasTransform = true;
  const trMatch = String(str).match(/translate\(\s*(-?[\d.]+)px\s*,\s*(-?[\d.]+)px\s*\)/);
  if (trMatch) {
    tx += Number(trMatch[1]);
    ty += Number(trMatch[2]);
  }
  const tyPct = String(str).match(/translateY\(\s*(-?[\d.]+)%\s*\)/);
  if (tyPct) {
    ty += (Number(tyPct[1]) / 100) * selfH;
  }
  const scMatch = String(str).match(/scale\(\s*([\d.]+)\s*\)/);
  if (scMatch) {
    scale *= Number(scMatch[1]);
  }
  return { tx, ty, scale, hasTransform };
}

function estimateBubbleSubtreeSizes(bubbleEl) {
  const bw = parsePx(bubbleEl.style.width, VIEW_W <= 720 ? 250 : 290);
  const headH = 60;
  const footH = 38;
  const listEl = bubbleEl.querySelector('.journey-bubble-list');
  const tasks = listEl ? Array.from(listEl.children) : [];
  let naturalListH = 0;
  const taskHeights = tasks.map((t) => {
    const title = (t.querySelector('.journey-bubble-title') || {}).textContent || '';
    const charsPerLine = Math.max(16, Math.floor((bw - 56) / 7.1));
    const lines = Math.min(2, Math.max(1, Math.ceil(title.length / charsPerLine)));
    const h = 20 + lines * 17 + 2 + 18 + 1;
    naturalListH += h;
    return h;
  });
  const naturalTotal = 2 + headH + naturalListH + footH;
  const maxH = parsePx(bubbleEl.style.maxHeight, Infinity);
  const totalH = Math.min(naturalTotal, maxH);
  const effectiveListH = Math.max(0, totalH - 2 - headH - footH);
  return { bw, totalH, headH, effectiveListH, footH, taskHeights };
}

(async () => {
  const htmlRes = await fetch(BASE_URL + '/');
  const html = await htmlRes.text();
  const cssRes = await fetch(BASE_URL + '/assets/journey/logi-shell.css');
  const shellCss = await cssRes.text();

  // Extract inline <style> so we verify REAL CSS rules shipped by render_trial_portal_html()
  const inlineStyleMatch = html.match(/<style>([\s\S]*?)<\/style>/);
  const inlineCss = inlineStyleMatch ? inlineStyleMatch[1] : '';

  // Parse real canvas height & touch-action rules for desktop vs mobile (<=720px)
  const isMobile = VIEW_W <= 720;
  function computeCanvasCssMetrics() {
    let minH = 520;
    let h = Math.max(520, Math.min(660, VIEW_H - 230));
    let touchAction = 'none';
    const mediaBlocks = Array.from(inlineCss.matchAll(/@media\s*\(max-width:\s*720px\)\s*\{([\s\S]*?)\n\s*\}/g));
    if (isMobile && mediaBlocks.length > 0) {
      const mobileCss = mediaBlocks.map(m => m[1]).join('\n');
      const clampMatch = mobileCss.match(/\.journey-canvas\s*\{[^}]*height:\s*clamp\(\s*(\d+)px\s*,\s*calc\(100dvh\s*-\s*(\d+)px\)\s*,\s*(\d+)px\s*\)/);
      if (clampMatch) {
        const lo = Number(clampMatch[1]);
        const sub = Number(clampMatch[2]);
        const hi = Number(clampMatch[3]);
        h = Math.max(lo, Math.min(hi, VIEW_H - sub));
      }
      const minMatch = mobileCss.match(/\.journey-canvas\s*\{[^}]*min-height:\s*(\d+)px/);
      if (minMatch) minH = Number(minMatch[1]);
      else minH = 0;
      const taMatch = mobileCss.match(/\.journey-canvas\s*\{[^}]*touch-action:\s*([^;!}\n]+)/);
      if (taMatch) touchAction = taMatch[1].trim();
    }
    return { cssHeight: Math.max(minH, h), touchAction };
  }

  // Parse .journey-bubble-above rule in inlineCss to faithfully reflect whether translateY(-100%) is active!
  const aboveRuleMatch = inlineCss.match(/\.journey-bubble-above\s*\{([^}]*)\}/);
  const aboveRuleTransform = (aboveRuleMatch && /translateY\(\s*-100%\s*\)/.test(aboveRuleMatch[1]))
    ? 'translateY(-100%)'
    : 'none';

  // Parse z-index of .journey-bubble-layer / #journey-bubble-slot if declared in CSS
  const bubbleLayerRuleMatch = inlineCss.match(/\.journey-bubble-layer\s*\{([^}]*)\}/);
  const bubbleLayerZ = (bubbleLayerRuleMatch && bubbleLayerRuleMatch[1].match(/z-index:\s*(-?\d+)/))
    ? Number(bubbleLayerRuleMatch[1].match(/z-index:\s*(-?\d+)/)[1])
    : null;

  const jsErrors = [];
  const vConsole = new VirtualConsole();
  vConsole.on('jsdomError', (e) => jsErrors.push(String(e && e.stack ? e.stack : e)));

  const dom = new JSDOM(html, {
    url: BASE_URL + '/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: vConsole,
    beforeParse(win) {
      let scrollYVal = 0;
      let scrollXVal = 0;
      Object.defineProperty(win, 'innerWidth', { get: () => VIEW_W, configurable: true });
      Object.defineProperty(win, 'innerHeight', { get: () => VIEW_H, configurable: true });
      Object.defineProperty(win, 'scrollY', { get: () => scrollYVal, configurable: true });
      Object.defineProperty(win, 'pageYOffset', { get: () => scrollYVal, configurable: true });
      Object.defineProperty(win, 'scrollX', { get: () => scrollXVal, configurable: true });

      function maxScrollY() {
        const docH = computePageLayout().docHeight;
        return Math.max(0, docH - VIEW_H);
      }
      win.scrollTo = function(a, b) {
        if (typeof a === 'object' && a !== null) {
          if (typeof a.top === 'number') scrollYVal = Math.max(0, Math.min(maxScrollY(), a.top));
          if (typeof a.left === 'number') scrollXVal = Math.max(0, a.left);
        } else {
          if (typeof a === 'number') scrollXVal = Math.max(0, a);
          if (typeof b === 'number') scrollYVal = Math.max(0, Math.min(maxScrollY(), b));
        }
      };
      win.scrollBy = function(a, b) {
        const dy = (typeof a === 'object' && a !== null) ? Number(a.top || 0) : Number(b || 0);
        const dx = (typeof a === 'object' && a !== null) ? Number(a.left || 0) : Number(a || 0);
        win.scrollTo(scrollXVal + dx, scrollYVal + dy);
      };

      const cookieJar = {};
      win.fetch = async (input, init = {}) => {
        const target = String(input).startsWith('http') ? String(input) : (BASE_URL + String(input));
        const hdrs = Object.assign({}, init.headers || {});
        const cookieStr = Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join('; ');
        if (cookieStr && !hdrs['Cookie']) hdrs['Cookie'] = cookieStr;
        const r = await fetch(target, Object.assign({}, init, { headers: hdrs }));
        const setCookie = r.headers.get('set-cookie');
        if (setCookie) {
          const kv = setCookie.split(';')[0].split('=');
          if (kv.length >= 2) {
            const k = kv[0].trim();
            const v = kv.slice(1).join('=').trim();
            if (v) cookieJar[k] = v; else delete cookieJar[k];
          }
        }
        return r;
      };

      const canvasMetrics = computeCanvasCssMetrics();

      function computePageLayout() {
        const doc = win.document;
        const padX = 16;
        const contentW = VIEW_W - padX * 2;
        const headerH = isMobile ? 150 : 62;
        let cursorY = headerH + 14;
        const kpiH = isMobile ? 154 : 52;
        const kpiTop = cursorY;
        cursorY += kpiH + 10;
        const selectorEl = doc.getElementById('customer-shipment-selector');
        let selectorTop = cursorY, selectorH = 0;
        if (selectorEl && !selectorEl.classList.contains('hidden')) {
          selectorH = isMobile ? 340 : 190;
          cursorY += selectorH + 10;
        }
        const toolbarH = isMobile ? 136 : 44;
        const toolbarTop = cursorY;
        cursorY += toolbarH + 6;
        const vpEl = doc.getElementById('journey-map-viewport');
        const inlineMinH = vpEl ? parsePx(vpEl.style.minHeight, 0) : 0;
        const vpH = Math.max(canvasMetrics.cssHeight, inlineMinH);
        const vpTop = cursorY;
        cursorY += vpH + 36;
        return {
          padX, contentW, headerH, kpiTop, kpiH, selectorTop, selectorH,
          toolbarTop, toolbarH, vpLeft: padX, vpTop, vpW: contentW, vpH,
          docHeight: cursorY, touchAction: canvasMetrics.touchAction
        };
      }
      win.__computePageLayout = computePageLayout;

      function isHiddenOrDetached(el) {
        let cur = el;
        while (cur && cur.nodeType === 1) {
          if (cur.classList && cur.classList.contains('hidden')) return true;
          if (cur.style && cur.style.display === 'none') return true;
          if (isMobile && cur.classList && cur.classList.contains('journey-map-hint')) return true;
          cur = cur.parentElement;
        }
        return false;
      }

      // Compute viewport-relative rect (accounting for scrollY + ancestor transforms!)
      function getRect(el) {
        const doc = win.document;
        if (!el || isHiddenOrDetached(el)) {
          return { left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0, x: 0, y: 0 };
        }
        const L = computePageLayout();
        const sy = scrollYVal;
        const vpLeft = L.vpLeft;
        const vpTop = L.vpTop - sy;
        const vpInnerLeft = vpLeft + 1;
        const vpInnerTop = vpTop + 1;
        const vpInnerW = L.vpW - 2;
        const vpInnerH = L.vpH - 2;

        const mk = (l, t, w, h) => ({
          left: l, top: t, right: l + w, bottom: t + h, width: w, height: h, x: l, y: t
        });

        if (el === doc.documentElement || el === doc.body) {
          return mk(0, -sy, VIEW_W, L.docHeight);
        }
        if (el.classList.contains('portal-header')) {
          return mk(0, -sy, VIEW_W, L.headerH);
        }
        if (el.classList.contains('customer-kpi-strip')) {
          return mk(L.padX, L.kpiTop - sy, L.contentW, L.kpiH);
        }
        if (el.id === 'customer-shipment-selector') {
          return mk(L.padX, L.selectorTop - sy, L.contentW, L.selectorH);
        }
        if (el.classList.contains('journey-toolbar')) {
          return mk(L.padX, L.toolbarTop - sy, L.contentW, L.toolbarH);
        }
        if (el.id === 'journey-map-viewport') {
          return mk(vpLeft, vpTop, L.vpW, L.vpH);
        }
        if (el.id === 'journey-map-transform') {
          const tf = parseTransform(el.style.transform, 520);
          return mk(vpInnerLeft + tf.tx, vpInnerTop + tf.ty, 1080 * tf.scale, 520 * tf.scale);
        }
        if (el.classList.contains('journey-bubble-layer') || el.id === 'journey-bubble-slot') {
          const tfEl = doc.getElementById('journey-map-transform');
          if (tfEl && tfEl.contains(el)) {
            const tfRect = getRect(tfEl);
            return tfRect;
          }
          return mk(vpInnerLeft, vpInnerTop, vpInnerW, vpInnerH);
        }
        // Utility trigger container / button / dropdown (top:12px; right:12px inside viewport)
        const utilBtn = doc.querySelector('[data-testid="journey-utility-trigger"]');
        if (utilBtn && (el === utilBtn || el === utilBtn.parentElement || utilBtn.contains(el))) {
          const btnW = isMobile ? 168 : 182;
          const btnH = 31;
          return mk(vpInnerLeft + vpInnerW - 12 - btnW, vpInnerTop + 12, btnW, btnH);
        }
        if (el.id === 'journey-utility-bubble') {
          return mk(vpInnerLeft + vpInnerW - 12 - 280, vpInnerTop + 49, 280, 122);
        }
        // Zoom bar & status hint inside viewport
        if (el.classList.contains('journey-zoom-bar')) {
          if (isMobile) {
            return mk(vpInnerLeft + 8, vpInnerTop + vpInnerH - 8 - 44, vpInnerW - 16, 44);
          }
          return mk(vpInnerLeft + vpInnerW - 12 - 304, vpInnerTop + vpInnerH - 12 - 42, 304, 42);
        }
        const zoomBar = doc.querySelector('.journey-zoom-bar');
        if (zoomBar && zoomBar.contains(el)) {
          const zr = getRect(zoomBar);
          const kids = Array.from(zoomBar.children);
          const idx = Math.max(0, kids.indexOf(el));
          const kw = zr.width / Math.max(1, kids.length);
          return mk(zr.left + idx * kw, zr.top + 4, kw - 4, zr.height - 8);
        }
        if (el.classList.contains('journey-map-hint')) {
          return mk(vpInnerLeft + 12, vpInnerTop + vpInnerH - 12 - 34, 390, 34);
        }
        // Journey nodes inside #journey-map-transform
        if (el.classList.contains('journey-node') || el.closest('.journey-node')) {
          const nodeEl = el.classList.contains('journey-node') ? el : el.closest('.journey-node');
          const tfEl = doc.getElementById('journey-map-transform');
          const tf = parseTransform(tfEl ? tfEl.style.transform : '', 520);
          const nx = parsePx(nodeEl.style.left, 0);
          const ny = parsePx(nodeEl.style.top, 0);
          const nw = parsePx(nodeEl.style.width, isMobile ? 82 : 116);
          const nh = parsePx(nodeEl.style.height, isMobile ? 60 : 66);
          return mk(vpInnerLeft + tf.tx + nx * tf.scale, vpInnerTop + tf.ty + ny * tf.scale, nw * tf.scale, nh * tf.scale);
        }
        // Journey bubble & its interactive controls!
        const bubbleEl = el.classList.contains('journey-bubble') ? el : el.closest('.journey-bubble');
        if (bubbleEl) {
          const sizes = estimateBubbleSubtreeSizes(bubbleEl);
          const tfEl = doc.getElementById('journey-map-transform');
          const insideTransform = Boolean(tfEl && tfEl.contains(bubbleEl));
          const parentTf = insideTransform ? parseTransform(tfEl.style.transform, 520) : { tx: 0, ty: 0, scale: 1 };
          let localLeft = parsePx(bubbleEl.style.left, 0);
          let localTop = parsePx(bubbleEl.style.top, 0);
          if (bubbleEl.classList.contains('journey-bubble-above') && aboveRuleTransform === 'translateY(-100%)') {
            localTop -= sizes.totalH;
          }
          const bLeft = vpInnerLeft + parentTf.tx + localLeft * parentTf.scale;
          const bTop = vpInnerTop + parentTf.ty + localTop * parentTf.scale;
          const bW = sizes.bw * parentTf.scale;
          const bH = sizes.totalH * parentTf.scale;
          if (el === bubbleEl) return mk(bLeft, bTop, bW, bH);

          const headH = sizes.headH * parentTf.scale;
          const listH = sizes.effectiveListH * parentTf.scale;
          const footH = sizes.footH * parentTf.scale;
          if (el.classList.contains('journey-bubble-head')) return mk(bLeft, bTop + 1, bW, headH);
          if (el.classList.contains('journey-bubble-close')) {
            const cw = (isMobile ? 36 : 28) * parentTf.scale;
            const ch = (isMobile ? 36 : 28) * parentTf.scale;
            return mk(bLeft + bW - 14 * parentTf.scale - cw, bTop + 10 * parentTf.scale, cw, ch);
          }
          if (el.classList.contains('journey-bubble-list')) return mk(bLeft, bTop + 1 + headH, bW, listH);
          if (el.classList.contains('journey-bubble-task') || el.closest('.journey-bubble-task')) {
            const tEl = el.classList.contains('journey-bubble-task') ? el : el.closest('.journey-bubble-task');
            const listEl = bubbleEl.querySelector('.journey-bubble-list');
            const idx = listEl ? Array.from(listEl.children).indexOf(tEl) : 0;
            const prevH = sizes.taskHeights.slice(0, Math.max(0, idx)).reduce((a, b) => a + b, 0) * parentTf.scale;
            const curH = (sizes.taskHeights[idx] || 60) * parentTf.scale;
            const visTop = bTop + 1 + headH + prevH;
            const visBottom = Math.min(bTop + 1 + headH + listH, visTop + curH);
            return mk(bLeft, visTop, bW, Math.max(0, visBottom - visTop));
          }
          if (el.classList.contains('journey-bubble-foot')) {
            return mk(bLeft, bTop + bH - 1 - footH, bW, footH);
          }
          if (el.classList.contains('journey-bubble-open')) {
            return mk(bLeft + 14 * parentTf.scale, bTop + bH - 1 - footH + 6 * parentTf.scale, 152 * parentTf.scale, 24 * parentTf.scale);
          }
        }
        // Stage modal dialog (position: fixed; inset: 0; z-index: 200)
        if (el.id === 'journey-modal-layer' || el.classList.contains('journey-modal-backdrop')) {
          return mk(0, 0, VIEW_W, VIEW_H);
        }
        if (el.classList.contains('journey-modal-card') || el.closest('.journey-modal-card')) {
          const mw = isMobile ? VIEW_W : Math.min(620, VIEW_W - 32);
          const mh = Math.round(VIEW_H * 0.78);
          const ml = (VIEW_W - mw) / 2;
          const mt = isMobile ? (VIEW_H - mh) : (VIEW_H - mh) / 2;
          if (el.classList.contains('journey-modal-close')) {
            return mk(ml + mw - 86, mt + 14, 70, 30);
          }
          return mk(ml, mt, mw, mh);
        }
        return mk(0, 0, 120, 32);
      }

      win.HTMLElement.prototype.getBoundingClientRect = function() {
        return getRect(this);
      };
      Object.defineProperty(win.HTMLElement.prototype, 'clientWidth', {
        get() {
          if (this.id === 'journey-map-viewport') return computePageLayout().vpW - 2;
          return Math.round(getRect(this).width);
        },
        configurable: true
      });
      Object.defineProperty(win.HTMLElement.prototype, 'clientHeight', {
        get() {
          if (this.id === 'journey-map-viewport') return computePageLayout().vpH - 2;
          return Math.round(getRect(this).height);
        },
        configurable: true
      });
      Object.defineProperty(win.HTMLElement.prototype, 'offsetWidth', {
        get() { return Math.round(getRect(this).width); },
        configurable: true
      });
      Object.defineProperty(win.HTMLElement.prototype, 'offsetHeight', {
        get() { return Math.round(getRect(this).height); },
        configurable: true
      });

      // Real CSS Stacking Context + overflow:hidden clipping hit-test per W3C CSSOM View!
      win.document.elementFromPoint = function(x, y) {
        if (x < 0 || y < 0 || x > VIEW_W || y > VIEW_H) return null;
        const doc = win.document;

        // 1. Check top-level fixed modal layer (z-index: 200) first
        const modal = doc.getElementById('journey-modal-layer');
        if (modal && !modal.classList.contains('hidden')) {
          const closeBtn = modal.querySelector('[data-testid="journey-modal-close"]');
          const cr = closeBtn ? getRect(closeBtn) : null;
          if (cr && x >= cr.left && x <= cr.right && y >= cr.top && y <= cr.bottom) return closeBtn;
          const card = modal.querySelector('.journey-modal-card');
          const cardR = card ? getRect(card) : null;
          if (cardR && x >= cardR.left && x <= cardR.right && y >= cardR.top && y <= cardR.bottom) return card;
          return modal.querySelector('.journey-modal-backdrop') || modal;
        }

        // 2. Check inside #journey-map-viewport (overflow: hidden clips ALL descendants to vpRect!)
        const vp = doc.getElementById('journey-map-viewport');
        if (vp && !isHiddenOrDetached(vp)) {
          const vpR = getRect(vp);
          const inVp = (x >= vpR.left && x <= vpR.right && y >= vpR.top && y <= vpR.bottom);
          if (inVp) {
            // Collect stacking-context children inside #journey-map-viewport in true CSS paint order!
            // Any element inside #journey-map-transform shares #journey-map-transform's z-index: 2!
            const candidates = [];
            function hitBubbleInteractive(bubbleEl, stackZ, order) {
              const bR = getRect(bubbleEl);
              if (x < bR.left || x > bR.right || y < bR.top || y > bR.bottom) return;
              const subTargets = [
                bubbleEl.querySelector('[data-testid="journey-bubble-close"]'),
                bubbleEl.querySelector('[data-testid="journey-open-workspace"]'),
                bubbleEl.querySelector('[data-testid="journey-bubble-task-stage"]'),
                bubbleEl.querySelector('[data-testid="journey-bubble-task-docs"]'),
                bubbleEl
              ].filter(Boolean);
              for (const t of subTargets) {
                const r = getRect(t);
                if (r.width > 0 && r.height > 0 && x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) {
                  candidates.push({ el: t, z: stackZ, order });
                  return;
                }
              }
            }

            Array.from(vp.children).forEach((child, domOrder) => {
              if (isHiddenOrDetached(child)) return;
              if (child.style && child.style.pointerEvents === 'none') return;
              if (child.classList.contains('journey-sea-chart')) return;

              if (child.id === 'journey-map-transform') {
                const tfZ = parseInt(child.style.zIndex || '2', 10);
                // Nodes (z-index: 10 inside tfZ)
                const nodes = Array.from(child.querySelectorAll('.journey-node'));
                nodes.forEach((n) => {
                  const nr = getRect(n);
                  if (x >= nr.left && x <= nr.right && y >= nr.top && y <= nr.bottom) {
                    candidates.push({ el: n, z: tfZ, innerZ: 10, order: domOrder });
                  }
                });
                // If #journey-bubble-slot is STILL inside #journey-map-transform, its stacking context ceiling is tfZ (2)!
                const innerBubble = child.querySelector('.journey-bubble');
                if (innerBubble) {
                  hitBubbleInteractive(innerBubble, tfZ, domOrder + 0.5);
                }
                return;
              }

              // Direct child of #journey-map-viewport!
              let childZ = parseInt(child.style.zIndex || '', 10);
              if (Number.isNaN(childZ)) {
                if (child.classList.contains('journey-bubble-layer') || child.id === 'journey-bubble-slot') {
                  childZ = bubbleLayerZ !== null ? bubbleLayerZ : 0;
                } else if (child.classList.contains('journey-zoom-bar') || child.classList.contains('journey-map-hint')) {
                  childZ = 20;
                } else {
                  childZ = 0;
                }
              }

              if (child.id === 'journey-bubble-slot' || child.classList.contains('journey-bubble-layer')) {
                const outerBubble = child.querySelector('.journey-bubble');
                if (outerBubble) hitBubbleInteractive(outerBubble, childZ, domOrder);
                return;
              }

              const utilTrigger = child.querySelector && child.querySelector('[data-testid="journey-utility-trigger"]');
              if (utilTrigger) {
                const ur = getRect(utilTrigger);
                if (x >= ur.left && x <= ur.right && y >= ur.top && y <= ur.bottom) {
                  candidates.push({ el: utilTrigger, z: childZ, order: domOrder });
                }
                const drop = child.querySelector('#journey-utility-bubble');
                if (drop && !drop.classList.contains('hidden')) {
                  const dr = getRect(drop);
                  if (x >= dr.left && x <= dr.right && y >= dr.top && y <= dr.bottom) {
                    candidates.push({ el: drop, z: childZ, order: domOrder + 0.1 });
                  }
                }
                return;
              }

              const cr = getRect(child);
              if (x >= cr.left && x <= cr.right && y >= cr.top && y <= cr.bottom) {
                candidates.push({ el: child, z: childZ, order: domOrder });
              }
            });

            if (candidates.length > 0) {
              candidates.sort((a, b) => (a.z !== b.z ? b.z - a.z : (b.innerZ || 0) - (a.innerZ || 0) || b.order - a.order));
              return candidates[0].el;
            }
            return vp;
          }
        }

        // Outside #journey-map-viewport (e.g. clipped header/toolbar above map!)
        const toolbar = doc.querySelector('.journey-toolbar');
        if (toolbar) {
          const tr = getRect(toolbar);
          if (x >= tr.left && x <= tr.right && y >= tr.top && y <= tr.bottom) return toolbar;
        }
        return doc.body;
      };
    }
  });

  await new Promise((r) => setTimeout(r, 80));
  const win = dom.window;
  const doc = win.document;

  // Log in cleanly via customer login form submit
  doc.getElementById('cust-username').value = USERNAME;
  doc.getElementById('cust-passcode').value = PASSCODE;
  const loginForm = doc.querySelector('#customer-login-screen form');
  loginForm.dispatchEvent(new win.Event('submit', { bubbles: true, cancelable: true }));
  await new Promise((r) => setTimeout(r, 120));

  // Open target shipment into Journey Map
  await win.selectShipmentForJourney(SHIPMENT_ID);
  await new Promise((r) => setTimeout(r, 40));

  const stageIds = JSON.parse(process.env.STAGE_IDS_JSON);
  const nodeReports = [];

  for (const stageId of stageIds) {
    const nodeBtn = doc.querySelector(`[data-testid="journey-node-${stageId}"]`);
    if (!nodeBtn) throw new Error('Missing node button: ' + stageId);

    // Ensure node itself is scrolled into browser viewport before normal user click (just like a user / Playwright scroll-into-view before clicking node)
    const preNodeRect = nodeBtn.getBoundingClientRect();
    if (preNodeRect.bottom > VIEW_H - 8) {
      win.scrollBy(0, preNodeRect.bottom - (VIEW_H - 40));
    } else if (preNodeRect.top < 8) {
      win.scrollBy(0, preNodeRect.top - 40);
    }

    // Normal click on node (must NOT be covered by another overlay!)
    const nr = nodeBtn.getBoundingClientRect();
    const nHit = doc.elementFromPoint((nr.left + nr.right) / 2, (nr.top + nr.bottom) / 2);
    const nodeClickable = Boolean(nHit && (nHit === nodeBtn || nodeBtn.contains(nHit)));
    nodeBtn.click();

    const vp = doc.getElementById('journey-map-viewport');
    const vpRect = vp.getBoundingClientRect();
    const bubble = doc.querySelector('[data-testid="journey-bubble"]');
    const closeBtn = doc.querySelector('[data-testid="journey-bubble-close"]');
    const detailsBtn = doc.querySelector('[data-testid="journey-open-workspace"]');
    if (!bubble || !closeBtn || !detailsBtn) {
      throw new Error('Missing bubble / close / details DOM on stage ' + stageId);
    }

    const bRect = bubble.getBoundingClientRect();
    const cRect = closeBtn.getBoundingClientRect();
    const dRect = detailsBtn.getBoundingClientRect();

    const closeHit = doc.elementFromPoint((cRect.left + cRect.right) / 2, (cRect.top + cRect.bottom) / 2);
    const detailsHit = doc.elementFromPoint((dRect.left + dRect.right) / 2, (dRect.top + dRect.bottom) / 2);

    const overflowLeftVp = Math.max(0, vpRect.left - bRect.left);
    const overflowRightVp = Math.max(0, bRect.right - vpRect.right);
    const overflowTopVp = Math.max(0, vpRect.top - bRect.top);
    const overflowBottomVp = Math.max(0, bRect.bottom - vpRect.bottom);
    const outsideScreenVert = bRect.top < 0 || bRect.bottom > VIEW_H;
    const outsideScreenHoriz = bRect.left < 0 || bRect.right > VIEW_W;

    const closeHitOk = Boolean(closeHit && (closeHit === closeBtn || closeBtn.contains(closeHit)));
    const detailsHitOk = Boolean(detailsHit && (detailsHit === detailsBtn || detailsBtn.contains(detailsHit)));

    // Normal click on Close (only clicks cleanly if elementFromPoint hits Close!)
    let closeWorked = false;
    if (closeHitOk) {
      closeHit.click();
      closeWorked = doc.querySelector('[data-testid="journey-bubble"]') === null;
    }

    // Re-open node normally -> click Details normally -> verify modal opens -> close modal normally
    nodeBtn.click();
    const detailsBtn2 = doc.querySelector('[data-testid="journey-open-workspace"]');
    const dRect2 = detailsBtn2.getBoundingClientRect();
    const detailsHit2 = doc.elementFromPoint((dRect2.left + dRect2.right) / 2, (dRect2.top + dRect2.bottom) / 2);
    let detailsOpenedModal = false;
    if (detailsHit2 && (detailsHit2 === detailsBtn2 || detailsBtn2.contains(detailsHit2))) {
      detailsHit2.click();
      const modalLayer = doc.getElementById('journey-modal-layer');
      detailsOpenedModal = Boolean(modalLayer && !modalLayer.classList.contains('hidden'));
      const modalClose = doc.querySelector('[data-testid="journey-modal-close"]');
      if (modalClose) modalClose.click();
    }

    nodeReports.push({
      stageId,
      nodeClickable,
      overflowLeftVp: Math.round(overflowLeftVp * 10) / 10,
      overflowRightVp: Math.round(overflowRightVp * 10) / 10,
      overflowTopVp: Math.round(overflowTopVp * 10) / 10,
      overflowBottomVp: Math.round(overflowBottomVp * 10) / 10,
      outsideScreenHoriz,
      outsideScreenVert,
      closeHitTag: closeHit ? (closeHit.dataset && closeHit.dataset.testid) || closeHit.className || closeHit.tagName : null,
      detailsHitTag: detailsHit ? (detailsHit.dataset && detailsHit.dataset.testid) || detailsHit.className || detailsHit.tagName : null,
      closeHitOk,
      detailsHitOk,
      closeWorked,
      detailsOpenedModal
    });
  }

  // Also check zoom + pan stress (e.g., panning Node06 near left edge & zooming in on Node03)
  win.fitJourney();
  win.zoomOut();
  const n6 = doc.querySelector('[data-testid="journey-node-finance-reconciliation"]');
  // Simulate panning map left by 45px then opening Node06
  vpDispatchDrag(win, doc, -45, 0);
  n6.click();
  const vpRectAfterPan = doc.getElementById('journey-map-viewport').getBoundingClientRect();
  const n6BubbleAfterPan = doc.querySelector('[data-testid="journey-bubble"]').getBoundingClientRect();
  const n6PanOverflowLeft = Math.round(Math.max(0, vpRectAfterPan.left - n6BubbleAfterPan.left) * 10) / 10;

  function vpDispatchDrag(w, d, dx, dy) {
    const vpEl = d.getElementById('journey-map-viewport');
    const r = vpEl.getBoundingClientRect();
    const Ev = w.MouseEvent;
    vpEl.dispatchEvent(new Ev('pointerdown', { bubbles: true, clientX: r.left + 10, clientY: r.top + 80 }));
    vpEl.dispatchEvent(new Ev('pointermove', { bubbles: true, clientX: r.left + 10 + dx, clientY: r.top + 80 + dy }));
    vpEl.dispatchEvent(new Ev('pointerup', { bubbles: true, clientX: r.left + 10 + dx, clientY: r.top + 80 + dy }));
  }

  // Check mobile scroll + full map/toolbar visibility when scrolled into view
  win.scrollTo(0, 0);
  const scrollBefore = win.scrollY;
  win.scrollBy(0, 260);
  const scrollAfter = win.scrollY;

  const layoutInfo = win.__computePageLayout();
  console.log(JSON.stringify({
    jsErrors,
    touchAction: layoutInfo.touchAction,
    scrollMoved: scrollAfter > scrollBefore,
    n6PanOverflowLeft,
    nodeReports
  }));
  dom.window.close();
})().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
"""


@requires_jsdom
def test_f2_mobile_390x844_bubbles_contained_clickable_scrollable_without_clipping(trial_server) -> None:
    """Mobile 390x844: all 7 nodes 00-06 open bubbles strictly inside map & screen bounds,
    Close & Details pass elementFromPoint() hit-testing and normal click, pan/zoom keeps
    Node06 inside left bound, and mobile canvas permits native vertical scrolling."""
    base_url, _env = trial_server
    result = _run_node_jsdom(
        _JSDOM_GEOMETRY_SCRIPT,
        {
            "BASE_URL": base_url,
            "VIEW_W": "390",
            "VIEW_H": "844",
            "CUST_USER": CUSTOMER_CREDENTIALS[0],
            "CUST_PASS": CUSTOMER_CREDENTIALS[1],
            "SHIPMENT_ID": SHIPMENT_A_ID,
            "STAGE_IDS_JSON": json.dumps(list(CUSTOMER_JOURNEY_STAGE_IDS)),
        },
    )
    assert result["jsErrors"] == [], f"Unexpected JS errors on mobile Journey: {result['jsErrors']}"
    assert result["scrollMoved"] is True
    bad = [
        r for r in result["nodeReports"]
        if (
            not r["nodeClickable"]
            or r["overflowLeftVp"] > 0
            or r["overflowRightVp"] > 0
            or r["overflowTopVp"] > 0
            or r["overflowBottomVp"] > 0
            or r["outsideScreenHoriz"]
            or r["outsideScreenVert"]
            or not r["closeHitOk"]
            or not r["detailsHitOk"]
            or not r["closeWorked"]
            or not r["detailsOpenedModal"]
        )
    ]
    assert bad == [], f"Mobile 390x844 bubble containment/clickability failures: {json.dumps(bad, ensure_ascii=False, indent=2)}"
    assert result["n6PanOverflowLeft"] == 0, (
        f"Node06 bubble overflowed left edge by {result['n6PanOverflowLeft']}px after pan/zoom"
    )
    assert "pan-y" in result["touchAction"] or result["touchAction"] == "auto", (
        f"Mobile .journey-canvas blocked native vertical scroll with touch-action={result['touchAction']!r}"
    )


@requires_jsdom
def test_f2_desktop_1440x900_bubbles_stacking_context_not_occluded_by_utility_button(trial_server) -> None:
    """Desktop 1440x900: all 7 nodes 00-06 (especially Node05/06 near top-right utility trigger
    '▤ Hồ sơ & Chứng từ') keep bubble, Close, and Details strictly inside map & viewport bounds
    with true elementFromPoint() clickability and zero regression to map-first flow."""
    base_url, _env = trial_server
    result = _run_node_jsdom(
        _JSDOM_GEOMETRY_SCRIPT,
        {
            "BASE_URL": base_url,
            "VIEW_W": "1440",
            "VIEW_H": "900",
            "CUST_USER": CUSTOMER_CREDENTIALS[0],
            "CUST_PASS": CUSTOMER_CREDENTIALS[1],
            "SHIPMENT_ID": SHIPMENT_A_ID,
            "STAGE_IDS_JSON": json.dumps(list(CUSTOMER_JOURNEY_STAGE_IDS)),
        },
    )
    assert result["jsErrors"] == [], f"Unexpected JS errors on desktop Journey: {result['jsErrors']}"
    bad = [
        r for r in result["nodeReports"]
        if (
            not r["nodeClickable"]
            or r["overflowLeftVp"] > 0
            or r["overflowRightVp"] > 0
            or r["overflowTopVp"] > 0
            or r["overflowBottomVp"] > 0
            or r["outsideScreenHoriz"]
            or r["outsideScreenVert"]
            or not r["closeHitOk"]
            or not r["detailsHitOk"]
            or not r["closeWorked"]
            or not r["detailsOpenedModal"]
        )
    ]
    assert bad == [], f"Desktop 1440x900 bubble containment/occlusion failures: {json.dumps(bad, ensure_ascii=False, indent=2)}"


# --------------------------------------------------------------------------- #
# Part 2 — Internal TT Login single-POST + clean /tt activation + zero JS error
# --------------------------------------------------------------------------- #
_TT_LOGIN_JSDOM_SCRIPT = r"""
const { JSDOM, VirtualConsole } = require('jsdom');

const BASE_URL = process.env.BASE_URL;
const TT_USER = process.env.TT_USER;
const TT_PASS = process.env.TT_PASS;
const TRIGGER_MODE = process.env.TRIGGER_MODE; // 'click' | 'enter' | 'double_click' | 'iframe_click'

(async () => {
  const loginPageRes = await fetch(BASE_URL + '/tt/login');
  const loginHtml = await loginPageRes.text();

  const authPosts = [];
  const allRequests = [];
  const jsErrors = [];
  const cookieJar = {};

  function buildVirtualConsole() {
    const vc = new VirtualConsole();
    vc.on('jsdomError', (err) => {
      jsErrors.push(String(err && err.message ? err.message : err));
    });
    return vc;
  }

  let navigatedUrl = null;
  const isIframe = TRIGGER_MODE === 'iframe_click';

  function makeFetchForWindow() {
    return async (input, init = {}) => {
      const pathOrUrl = String(input);
      const target = pathOrUrl.startsWith('http') ? pathOrUrl : (BASE_URL + pathOrUrl);
      const method = String((init && init.method) || 'GET').toUpperCase();
      allRequests.push(`${method} ${pathOrUrl}`);
      if (method === 'POST' && pathOrUrl.includes('/api/hexa/v0/tt/auth/login')) {
        authPosts.push(pathOrUrl);
        if (TRIGGER_MODE === 'double_click') {
          await new Promise((r) => setTimeout(r, 40));
        }
      }
      const hdrs = Object.assign({}, init.headers || {});
      if (!isIframe) {
        const cookieStr = Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join('; ');
        if (cookieStr && !hdrs['Cookie']) hdrs['Cookie'] = cookieStr;
      }
      const res = await fetch(target, Object.assign({}, init, { headers: hdrs }));
      const setCookie = res.headers.get('set-cookie');
      if (setCookie && !isIframe) {
        const kv = setCookie.split(';')[0].split('=');
        if (kv.length >= 2) cookieJar[kv[0].trim()] = kv.slice(1).join('=').trim();
      }
      return res;
    };
  }

  let activeWin = null;
  let rootDom = null;

  if (isIframe) {
    // Embedded iframe window with real origin URL (e.g. https://{port}-{sandbox}.e2b.app/tt/login inside cross-origin parent)
    const parentWindow = {};
    rootDom = new JSDOM(loginHtml, {
      url: BASE_URL + '/tt/login',
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      virtualConsole: buildVirtualConsole(),
      beforeParse(win) {
        win.fetch = makeFetchForWindow();
        try {
          Object.defineProperty(win.Window.prototype, 'top', { get: () => parentWindow, configurable: true });
        } catch (_e) {}
      }
    });
    activeWin = rootDom.window;
  } else {
    rootDom = new JSDOM(loginHtml, {
      url: BASE_URL + '/tt/login',
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      virtualConsole: buildVirtualConsole(),
      beforeParse(win) {
        win.fetch = makeFetchForWindow();
      }
    });
    activeWin = rootDom.window;
  }

  const win = activeWin;
  const doc = win.document;

  doc.getElementById('tt-user').value = TT_USER;
  doc.getElementById('tt-pass').value = TT_PASS;

  const form = doc.querySelector('form');
  const submitBtn = doc.querySelector('button[type="submit"]');

  if (TRIGGER_MODE === 'click' || TRIGGER_MODE === 'iframe_click') {
    submitBtn.click();
  } else if (TRIGGER_MODE === 'double_click') {
    submitBtn.click();
    submitBtn.click();
  } else if (TRIGGER_MODE === 'enter') {
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit(submitBtn);
    } else {
      form.dispatchEvent(new win.Event('submit', { bubbles: true, cancelable: true }));
    }
  }

  await new Promise((r) => setTimeout(r, 450));

  for (const msg of jsErrors) {
    if (msg.includes('Not implemented: navigation')) {
      navigatedUrl = '/tt';
    }
  }

  let deskState = null;
  if (navigatedUrl) {
    const savedSessionToken = win.sessionStorage.getItem('hexa_tt_token') || '';
    const cookieStr = Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join('; ');
    const deskRes = await fetch(BASE_URL + navigatedUrl, {
      headers: cookieStr ? { Cookie: cookieStr } : {}
    });
    const deskHtml = await deskRes.text();
    const deskDom = new JSDOM(deskHtml, {
      url: BASE_URL + navigatedUrl,
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      virtualConsole: buildVirtualConsole(),
      beforeParse(dWin) {
        if (savedSessionToken) dWin.sessionStorage.setItem('hexa_tt_token', savedSessionToken);
        dWin.fetch = makeFetchForWindow();
      }
    });
    await new Promise((r) => setTimeout(r, 450));
    const dDoc = deskDom.window.document;
    deskState = {
      deskHttpStatus: deskRes.status,
      pathname: deskDom.window.location.pathname,
      eventsRows: dDoc.querySelectorAll('#tt-events-tbody tr').length,
      docsRows: dDoc.querySelectorAll('#tt-docs-tbody tr').length,
      financeVisible: !dDoc.getElementById('tt-finance-section').classList.contains('hidden')
    };
    deskDom.window.close();
  } else {
    deskState = {
      deskHttpStatus: 200,
      pathname: win.location.pathname,
      eventsRows: doc.querySelectorAll('#tt-events-tbody tr').length,
      docsRows: doc.querySelectorAll('#tt-docs-tbody tr').length,
      financeVisible: Boolean(doc.getElementById('tt-finance-section') && !doc.getElementById('tt-finance-section').classList.contains('hidden'))
    };
  }

  const finalJsErrors = jsErrors.filter((m) => !m.includes('Not implemented: navigation'));

  console.log(JSON.stringify({
    authPostCount: authPosts.length,
    jsErrors: finalJsErrors,
    deskState
  }));
  rootDom.window.close();
})().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
"""


@requires_jsdom
@pytest.mark.parametrize(
    ("role_name", "creds", "expect_finance_visible", "trigger_mode"),
    [
        ("finance", FINANCE_CREDENTIALS, True, "click"),
        ("finance", FINANCE_CREDENTIALS, True, "enter"),
        ("operations", OPS_CREDENTIALS, False, "click"),
        ("operations", OPS_CREDENTIALS, False, "enter"),
        ("finance", FINANCE_CREDENTIALS, True, "double_click"),
        ("finance", FINANCE_CREDENTIALS, True, "iframe_click"),
    ],
)
def test_tt_login_single_post_clean_navigation_and_zero_js_exception(
    trial_server,
    role_name: str,
    creds: tuple[str, str],
    expect_finance_visible: bool,
    trigger_mode: str,
) -> None:
    """Clicking 'Đăng nhập nội bộ TT' once, pressing Enter, rapid double-clicking, or submitting
    inside a cookie-blocked iframe must issue strictly ONE POST /api/hexa/v0/tt/auth/login,
    activate /tt immediately with live shipment data, and raise zero JS exceptions."""
    base_url, _env = trial_server
    out = _run_node_jsdom(
        _TT_LOGIN_JSDOM_SCRIPT,
        {
            "BASE_URL": base_url,
            "TT_USER": creds[0],
            "TT_PASS": creds[1],
            "TRIGGER_MODE": trigger_mode,
        },
    )
    assert out["authPostCount"] == 1, (
        f"{role_name}/{trigger_mode} sent {out['authPostCount']} login POSTs instead of 1: {out}"
    )
    assert out["jsErrors"] == [], (
        f"{role_name}/{trigger_mode} raised JS exception(s): {out['jsErrors']}"
    )
    desk = out["deskState"]
    assert desk["deskHttpStatus"] == 200
    assert desk["pathname"] == "/tt"
    assert desk["eventsRows"] >= 1, f"/tt did not initialize candidate events automatically: {desk}"
    assert desk["docsRows"] >= 1, f"/tt did not initialize candidate documents automatically: {desk}"
    assert desk["financeVisible"] is expect_finance_visible


_CUSTOMER_LOGIN_AND_F1_G1_SCRIPT = r"""
const { JSDOM, VirtualConsole } = require('jsdom');

const BASE_URL = process.env.BASE_URL;
const CUST_USER = process.env.CUST_USER;
const CUST_PASS = process.env.CUST_PASS;

(async () => {
  const html = await (await fetch(BASE_URL + '/')).text();
  const jsErrors = [];
  const custLoginPosts = [];
  const cookieJar = {};
  const vc = new VirtualConsole();
  vc.on('jsdomError', (e) => jsErrors.push(String(e && e.message ? e.message : e)));

  const dom = new JSDOM(html, {
    url: BASE_URL + '/',
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(win) {
      win.fetch = async (input, init = {}) => {
        const pathOrUrl = String(input);
        const target = pathOrUrl.startsWith('http') ? pathOrUrl : (BASE_URL + pathOrUrl);
        const method = String((init && init.method) || 'GET').toUpperCase();
        if (method === 'POST' && pathOrUrl.includes('/api/hexa/v0/auth/login')) {
          custLoginPosts.push(pathOrUrl);
        }
        const hdrs = Object.assign({}, init.headers || {});
        const cookieStr = Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join('; ');
        if (cookieStr && !hdrs['Cookie']) hdrs['Cookie'] = cookieStr;
        const r = await fetch(target, Object.assign({}, init, { headers: hdrs }));
        const sc = r.headers.get('set-cookie');
        if (sc) {
          const kv = sc.split(';')[0].split('=');
          if (kv.length >= 2) cookieJar[kv[0].trim()] = kv.slice(1).join('=').trim();
        }
        return r;
      };
    }
  });

  await new Promise((r) => setTimeout(r, 80));
  const win = dom.window;
  const doc = win.document;

  doc.getElementById('cust-username').value = CUST_USER;
  doc.getElementById('cust-passcode').value = CUST_PASS;
  doc.getElementById('btn-customer-login').click();
  await new Promise((r) => setTimeout(r, 140));

  const selectorText = doc.getElementById('customer-shipment-selector').textContent || '';
  console.log(JSON.stringify({
    custLoginPostCount: custLoginPosts.length,
    jsErrors,
    selectorText
  }));
  dom.window.close();
})().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
"""


@requires_jsdom
def test_customer_login_single_post_and_f1_g1_non_regression(trial_server) -> None:
    """Non-regression check:
    - Customer 'Đăng nhập' button click sends strictly 1 POST with 0 JS exceptions;
    - F1 financial summary text renders verified VND figures once approved by Finance;
    - Operations POST /publish with revoke_finance=True still returns HTTP 403 and preserves
      published customer financial figures;
    - Finance POST /revoke with revoke_finance=True returns HTTP 200 and clears customer
      financial figures back to 'UNKNOWN / Chưa đối soát' immediately."""
    base_url, _env = trial_server

    # 1. Finance staff confirms partial payment & approves financial publication on ROAD-LG-001
    st_fin, _, body_fin = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": FINANCE_CREDENTIALS[0], "passcode": FINANCE_CREDENTIALS[1]},
    )
    assert st_fin == 200
    fin_token = json.loads(body_fin.decode("utf-8"))["session_token"]

    st_detail, _, body_detail = _http_request(
        base_url, f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}", session_token=fin_token
    )
    assert st_detail == 200
    detail = json.loads(body_detail.decode("utf-8"))
    ob_id = detail["financial_obligations"][0]["id"]
    pub = detail["publication"]

    st_conf, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/finance/confirm",
        method="POST",
        session_token=fin_token,
        json_body={
            "transaction_id": "TXN-REPAIR-F1G1-01",
            "obligation_id": ob_id,
            "amount": 10_000_000,
            "currency": "VND",
            "occurred_at": "2026-10-23",
            "note": "F1+G1 non-regression verification",
        },
    )
    assert st_conf == 200

    st_pub, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=fin_token,
        json_body={
            "event_versions": pub.get("event_versions") or {},
            "document_versions": pub.get("document_versions") or {},
            "quote": pub.get("quote"),
            "approve_finance": True,
        },
    )
    assert st_pub == 200

    # 2. Customer single-click login sends strictly 1 POST and sees approved VND figures
    cust = _run_node_jsdom(
        _CUSTOMER_LOGIN_AND_F1_G1_SCRIPT,
        {
            "BASE_URL": base_url,
            "CUST_USER": CUSTOMER_CREDENTIALS[0],
            "CUST_PASS": CUSTOMER_CREDENTIALS[1],
        },
    )
    assert cust["custLoginPostCount"] == 1
    assert cust["jsErrors"] == []
    assert "57.240.000 VND" in cust["selectorText"]
    assert "40.000.000 VND" in cust["selectorText"]
    assert "17.240.000 VND" in cust["selectorText"]

    # 3. Operations staff attempting revoke_finance via /revoke (and approve_finance via /publish) MUST receive HTTP 403
    st_ops, _, body_ops = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": OPS_CREDENTIALS[0], "passcode": OPS_CREDENTIALS[1]},
    )
    assert st_ops == 200
    ops_token = json.loads(body_ops.decode("utf-8"))["session_token"]

    st_forbidden, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=ops_token,
        json_body={"revoke_finance": True},
    )
    assert st_forbidden == 403

    cust_still_published = _run_node_jsdom(
        _CUSTOMER_LOGIN_AND_F1_G1_SCRIPT,
        {
            "BASE_URL": base_url,
            "CUST_USER": CUSTOMER_CREDENTIALS[0],
            "CUST_PASS": CUSTOMER_CREDENTIALS[1],
        },
    )
    assert "57.240.000 VND" in cust_still_published["selectorText"]
    assert "40.000.000 VND" in cust_still_published["selectorText"]

    # 4. Finance staff revoking finance succeeds (HTTP 200) and clears customer financial view
    st_rev, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=fin_token,
        json_body={"revoke_finance": True},
    )
    assert st_rev == 200

    cust_after = _run_node_jsdom(
        _CUSTOMER_LOGIN_AND_F1_G1_SCRIPT,
        {
            "BASE_URL": base_url,
            "CUST_USER": CUSTOMER_CREDENTIALS[0],
            "CUST_PASS": CUSTOMER_CREDENTIALS[1],
        },
    )
    assert "57.240.000 VND" not in cust_after["selectorText"]
    assert "40.000.000 VND" not in cust_after["selectorText"]
    assert "UNKNOWN / Chưa đối soát" in cust_after["selectorText"]

