"""Diagnose the 390x844 list layout: which row/card testids and clusters exist."""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/user/review-255-evidence")
PW = (ROOT / ".pw").read_text().strip()
HOST = 'div[data-testid="stBidiComponentIsolated"]'
BASE = "http://127.0.0.1:9521/"
SUPPORT = "qa.r255.support"


def ev(page, body, arg=None):
    js = "(arg) => { const root = document.querySelector('%s')?.shadowRoot; %s }" % (HOST, body)
    return page.evaluate(js, arg)


def click(page, selector, text=None):
    return ev(page, """
        const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
          return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
        const els = [...root.querySelectorAll(arg.sel)].filter(vis);
        const el = arg.txt ? els.find(e => e.textContent.replace(/\\s+/g,' ').includes(arg.txt)) : els[0];
        if (!el) return false;
        el.scrollIntoView({ block: 'center', inline: 'nearest' });
        el.click();
        return true;
    """, {"sel": selector, "txt": text})


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/tmp/chromium",
                          args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                                "--disable-gpu", "--hide-scrollbars", "--no-zygote", "--single-process"])
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(BASE, wait_until="load", timeout=120000)
    page.wait_for_selector('input[aria-label="Tài khoản"]', timeout=120000)
    page.fill('input[aria-label="Tài khoản"]', SUPPORT)
    page.fill('input[type="password"]', PW)
    page.click('button[kind="primaryFormSubmit"]')
    page.wait_for_selector(HOST, timeout=240000)
    time.sleep(3)
    # open the mobile nav and go to the list
    print("menu button:", click(page, 'button[aria-label="Mở menu"]'))
    time.sleep(0.6)
    print("sidebar list link:", click(page, 'a[href="/lo-hang"]', "Lô Hàng"))
    time.sleep(2.0)
    print("all time:", click(page, '[data-testid="shipment-period-tat-ca"]'))
    time.sleep(2.0)
    print(json.dumps(ev(page, """
        const ids = (sel) => [...root.querySelectorAll(sel)].map(e => e.getAttribute('data-shipment-id'));
        return {
          rows: ids('[data-testid="shipment-row"]'),
          cards: ids('[data-testid="shipment-mobile-card"]'),
          clusters: [...root.querySelectorAll('[data-testid="shipment-finance-summary"]')].map(e => ({
              href: e.getAttribute('href'),
              parentCard: e.closest('[data-testid="shipment-mobile-card"]')?.getAttribute('data-shipment-id') || null,
              parentRow: e.closest('[data-testid="shipment-row"]')?.getAttribute('data-shipment-id') || null,
              rect: (({x,y,width,height}) => ({x, y, w: width, h: height}))(e.getBoundingClientRect()),
          })),
          summary: root.querySelector('[data-testid="shipment-list-summary"]')?.textContent?.slice(0, 80),
        };
    """), ensure_ascii=False, indent=1)[:2500], flush=True)
    ctx.close()
    b.close()
