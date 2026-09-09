#!/usr/bin/env python3
"""Phase A REAL-BROWSER acceptance (authoritative when a browser is available).

Run against the live Streamlit Preview (the ONE Components v2 component root
rendering the literal Logi-good UI):

    # default target (owner's machine)
    python playwright/acceptance_phase_a.py
    python playwright/acceptance_phase_a.py http://localhost:9501

Requires:  pip install playwright && playwright install chromium

It performs the 12-item Phase A acceptance checklist with real clicks in a
real Chromium, and fails (exit 1) on the first broken step. Screenshots are
written to test-results/ for visual parity review.

NOTE: this repo's sandbox cannot download a browser, so the mechanical
acceptance (tests/component/dom_acceptance_phase_a.mjs) runs the SAME
production bundle in a DOM and drives the SAME actions. This script is the
authoritative real-browser confirmation for the live Preview.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501").rstrip("/")
SHOTS = Path("test-results/phase-a")
SHOTS.mkdir(parents=True, exist_ok=True)

_passed = 0
_failed = 0


def check(page: Page, name: str, cond: bool) -> None:
    global _passed, _failed
    ok = bool(cond)
    if ok:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}")
    if not ok:
        shot = SHOTS / f"FAIL-{_passed + _failed:02d}.png"
        try:
            page.screenshot(path=str(shot), full_page=False)
            print(f"        screenshot: {shot}")
        except Exception:
            pass
        raise SystemExit(f"ACCEPTANCE FAILED at: {name}")


def body_text(page: Page) -> str:
    # The app renders inside an open shadow root (isolate_styles=True).
    return page.evaluate(
        """() => {
            const host = document.querySelector('[data-testid="stBidiComponentIsolated"]');
            const root = host && host.shadowRoot ? host.shadowRoot : document;
            const shell = root.querySelector('.logi-shell');
            return (shell ? shell.textContent : document.body.textContent) || '';
        }"""
    )


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page_errors: list[str] = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        print(f"Target: {BASE}")
        page.goto(BASE, wait_until="networkidle", timeout=90000)
        # wait for the v2 component to mount + first view-model render
        page.wait_for_function(
            """() => {
                const host = document.querySelector('[data-testid="stBidiComponentIsolated"]');
                return !!(host && host.shadowRoot && host.shadowRoot.querySelector('.logi-shell h1, .logi-shell header'));
            }""",
            timeout=60000,
        )
        page.wait_for_timeout(800)

        print("STEP 1 — boot")
        t = body_text(page)
        check(page, "no 'process is not defined'", "process is not defined" not in t)
        check(page, "no BidiComponent Error", "BidiComponent Error" not in t)
        check(page, "no uncaught page errors", not page_errors)
        check(page, "shell rendered (TRƯỜNG THÀNH)", "TRƯỜNG THÀNH" in t)
        page.screenshot(path=str(SHOTS / "01-home.png"))

        print("STEP 2 — header")
        check(page, "subtitle", "Phú Anh Logistics · Nội bộ" in t)
        check(page, "global search present",
              page.locator('.logi-shell input[placeholder^="Tìm mã lô"]').count() >= 1)
        check(page, "notification bell", page.locator('button[aria-label="Thông báo"]').count() >= 1)
        check(page, "Thêm button", page.get_by_role("button", name="Thêm").count() >= 1)

        print("STEP 3 — sidebar")
        t = body_text(page)
        for g in ["VẬN HÀNH", "KINH DOANH & ĐỐI TÁC", "TÀI CHÍNH & ĐỐI SOÁT", "CÔNG CỤ", "QUẢN TRỊ"]:
            check(page, f"sidebar group {g}", g in t)
        for it in ["Tổng Quan Công Việc", "Việc Cần Xử Lý", "Lô Hàng", "Tạo Lô Mới", "Theo Dõi Vận Chuyển"]:
            check(page, f"sidebar item {it}", it in t)

        print("STEP 4 — click Tổng Quan")
        page.get_by_text("Tổng Quan Công Việc", exact=True).first.click()
        page.wait_for_timeout(500)
        check(page, "Home hero", "Hôm nay tôi cần làm gì?" in body_text(page))
        page.screenshot(path=str(SHOTS / "04-home.png"))

        print("STEP 5 — click Việc Cần Xử Lý")
        page.get_by_text("Việc Cần Xử Lý", exact=True).first.click()
        page.wait_for_timeout(500)
        check(page, "Tasks heading", "Việc Cần Xử Lý" in body_text(page))
        check(page, "10 task rows", page.locator(".logi-shell table.tbl tbody tr").count() == 10)
        page.screenshot(path=str(SHOTS / "05-tasks.png"))

        print("STEP 6 — click Lô Hàng")
        page.get_by_text("Lô Hàng", exact=True).first.click()
        page.wait_for_timeout(500)
        check(page, "Shipments list", "Lô Hàng" in body_text(page))
        check(page, "5 shipment rows", page.locator(".logi-shell table.tbl tbody tr").count() == 5)
        page.screenshot(path=str(SHOTS / "06-shipments.png"))

        print("STEP 7 — open LO-0306")
        page.locator(".logi-shell table.tbl").get_by_text("LO-0306", exact=True).first.click()
        page.wait_for_timeout(600)
        t = body_text(page)
        check(page, "detail header LO-0306", "LO-0306" in t and "An Phát" in t)
        check(page, "missing-info states", "thiếu" in t.lower())
        page.screenshot(path=str(SHOTS / "07-detail.png"))

        print("STEP 8 — five donor tabs")
        tab_markers = {
            "Lấy hàng & Xuất khẩu": "Nhà máy & lịch lấy hàng",
            "Nhập khẩu & Giao hàng": "Tờ khai & thuế nhập khẩu",
            "Tài chính / Công nợ": "Phải thu khách hàng (VND)",
            "Chứng từ & PXK": "Phiếu xuất kho (PXK)",
            "Lịch sử": "Dòng thời gian — LO-0306",
        }
        for label, marker in tab_markers.items():
            page.get_by_role("button", name=label, exact=True).first.click()
            page.wait_for_timeout(400)
            check(page, f"tab {label}", marker in body_text(page))
            page.screenshot(path=str(SHOTS / f"08-tab-{label[:12].strip().replace(' ', '_')}.png"))

        print("STEP 9 — global search finds a shipment")
        search = page.locator('.logi-shell input[placeholder^="Tìm mã lô"]').first
        search.click()
        search.fill("an phát")
        page.wait_for_timeout(500)
        check(page, "search result LO-0306 · An Phát", "LO-0306 · An Phát" in body_text(page))
        page.locator("button", has_text="LO-0306 · An Phát").first.click()
        page.wait_for_timeout(600)
        check(page, "search navigated to LO-0306", "LO-0306" in body_text(page))
        page.screenshot(path=str(SHOTS / "09-search.png"))

        print("STEP 10 — Quick Add opens/closes")
        page.get_by_role("button", name="Thêm", exact=True).first.click()
        page.wait_for_timeout(400)
        check(page, "Quick Add opens", "Thêm mới nhanh" in body_text(page))
        page.locator(".logi-shell", has_text="Thêm mới nhanh").get_by_role("button").first.click()
        page.wait_for_timeout(400)
        check(page, "Quick Add closes", "Chọn việc muốn làm" not in body_text(page))

        print("STEP 11 — Notifications opens/closes")
        page.locator('button[aria-label="Thông báo"]').first.click()
        page.wait_for_timeout(400)
        check(page, "Notifications opens", "Thông báo · 4 chưa đọc" in body_text(page))
        # close: the X button is the first svg button inside the drawer
        page.evaluate(
            """() => {
                const host = document.querySelector('[data-testid="stBidiComponentIsolated"]');
                const root = host.shadowRoot;
                const drawer = [...root.querySelectorAll('div')].find(d => d.className && d.className.includes('w-[380px]'));
                const btn = drawer && [...drawer.querySelectorAll('button')].find(b => b.querySelector('svg'));
                if (btn) btn.click();
            }"""
        )
        page.wait_for_timeout(400)
        check(page, "Notifications closes", "Thông báo · 4 chưa đọc" not in body_text(page))

        print("STEP 12 — route + tab survive a backend rerun")
        # open LO-0306 detail and switch to the Tài chính tab
        page.get_by_text("Lô Hàng", exact=True).first.click()
        page.wait_for_timeout(500)
        page.locator(".logi-shell table.tbl").get_by_text("LO-0306", exact=True).first.click()
        page.wait_for_timeout(600)
        page.get_by_role("button", name="Tài chính / Công nợ", exact=True).first.click()
        page.wait_for_timeout(400)
        # trigger a real Streamlit rerun (Rerun button in the toolbar)
        rerun = page.locator('[data-testid="stRerunButton"], [aria-label="Rerun"], [data-baseweb="tooltip"] >> text=Rerun')
        if rerun.count() == 0:
            # fall back: press the toolbar rerun via keyboard shortcut (R)
            page.keyboard.press("r")
        else:
            rerun.first.click()
        page.wait_for_timeout(1500)
        t = body_text(page)
        check(page, "route survives rerun (LO-0306)", "LO-0306" in t)
        check(page, "tab survives rerun (Tài chính)", "Phải thu khách hàng (VND)" in t)
        page.screenshot(path=str(SHOTS / "12-rerun.png"))

        browser.close()

    total = _passed + _failed
    print(f"\nREAL-BROWSER ACCEPTANCE: {_passed}/{total} checks passed")
    if _failed:
        raise SystemExit(1)
    print("PHASE_A_BROWSER_ACCEPTANCE=PASS")


if __name__ == "__main__":
    main()
