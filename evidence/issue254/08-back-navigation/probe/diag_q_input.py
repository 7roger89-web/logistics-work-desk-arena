"""Diagnose how to set the q input reliably in real Chromium (probe plumbing only)."""
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


def state(page):
    return page.evaluate(
        """() => { const r = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
        if (!r) return null;
        const i = r.querySelector('input[placeholder*="Nhập mã lô"]');
        return {q: i ? i.value : null, rows: [...r.querySelectorAll('[data-testid="shipment-row"]')].map(e => e.getAttribute('data-shipment-id'))}; }"""
    )


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
    page.wait_for_selector(HOST, timeout=240_000)
    time.sleep(3)

    # go to /lo-hang via sidebar
    page.evaluate("""() => { const r = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
        const a = [...r.querySelectorAll('aside a')].find(a => a.getAttribute('href') === '/lo-hang'); if (a) a.click(); }""")
    time.sleep(2.5)
    page.evaluate("""() => { const r = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
        const b = r.querySelector('[data-testid="shipment-period-tat-ca"]'); if (b) b.click(); }""")
    time.sleep(2)
    print("base:", json.dumps(state(page), ensure_ascii=False)[:300], flush=True)

    loc = page.locator('div[data-testid="stBidiComponentIsolated"] input[placeholder*="Nhập mã lô"]')
    print("locator count:", loc.count(), flush=True)

    # attempt 1: playwright fill
    try:
        loc.first.fill("LO-0")
    except Exception as exc:
        print("fill error:", exc, flush=True)
    print("after fill t0:", json.dumps(state(page), ensure_ascii=False)[:200], flush=True)
    time.sleep(1.5)
    print("after fill t1.5:", json.dumps(state(page), ensure_ascii=False)[:200], flush=True)

    # attempt 2: insert_text after clearing
    page.evaluate("""() => { const r = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
        const i = r.querySelector('input[placeholder*="Nhập mã lô"]'); if (i) { i.focus(); i.select(); } }""")
    page.keyboard.press("Backspace")
    time.sleep(1.0)
    page.keyboard.insert_text("LO-0")
    time.sleep(1.5)
    print("after insert_text:", json.dumps(state(page), ensure_ascii=False)[:200], flush=True)

    # attempt 3: press keys one by one slowly
    page.evaluate("""() => { const r = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
        const i = r.querySelector('input[placeholder*="Nhập mã lô"]'); if (i) { i.focus(); i.select(); } }""")
    page.keyboard.press("Backspace")
    time.sleep(1.0)
    for ch in "LO-0":
        page.keyboard.type(ch)
        time.sleep(0.12)
    time.sleep(1.5)
    print("after slow type:", json.dumps(state(page), ensure_ascii=False)[:200], flush=True)
    b.close()
