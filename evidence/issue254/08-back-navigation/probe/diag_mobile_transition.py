"""Reproduce test_e's desktop->mobile transition and dump what is on screen."""
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


def dump(page, label):
    info = ev(page, """
        const t = (sel) => root.querySelectorAll(sel).length;
        return {
          rows: t('[data-testid="shipment-row"]'),
          cards: t('[data-testid="shipment-mobile-card"]'),
          clusters: t('[data-testid="shipment-finance-summary"]'),
          listSummary: root.querySelector('[data-testid="shipment-list-summary"]')?.textContent?.replace(/\\s+/g,' ').slice(0, 70) || null,
          detail: t('[data-testid="shipment-identity-bar"]'),
          back: t('[data-testid="shipment-back-to-list"]'),
          innerW: window.innerWidth,
          menuBtn: t('button[aria-label="Mở menu"]'),
        };
    """)
    print(label, json.dumps(info, ensure_ascii=False), flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/tmp/chromium",
                          args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                                "--disable-gpu", "--hide-scrollbars", "--no-zygote", "--single-process"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, wait_until="load", timeout=120000)
    page.wait_for_selector('input[aria-label="Tài khoản"]', timeout=120000)
    page.fill('input[aria-label="Tài khoản"]', SUPPORT)
    page.fill('input[type="password"]', PW)
    page.click('button[kind="primaryFormSubmit"]')
    page.wait_for_selector(HOST, timeout=240000)
    time.sleep(3)
    click(page, 'aside a[href="/lo-hang"]', "Lô Hàng")
    time.sleep(2)
    click(page, '[data-testid="shipment-period-tat-ca"]')
    time.sleep(1.5)
    dump(page, "desktop-list:")

    page.set_viewport_size({"width": 390, "height": 844})
    time.sleep(1.5)
    dump(page, "after-resize:")
    print("goto_list-ish:", click(page, 'aside a[href="/lo-hang"]'), click(page, 'a[href="/lo-hang"]', "Lô Hàng"), flush=True)
    time.sleep(1.5)
    dump(page, "after-goto-list:")
    print("period:", click(page, '[data-testid="shipment-period-tat-ca"]'), flush=True)
    time.sleep(2)
    dump(page, "after-period:")
    print("menu:", click(page, 'button[aria-label="Mở menu"]'), flush=True)
    time.sleep(0.8)
    dump(page, "after-menu:")
    print("menu link:", click(page, 'a[href="/lo-hang"]', "Lô Hàng"), flush=True)
    time.sleep(2)
    dump(page, "after-menu-link:")
    ctx.close()
    b.close()
