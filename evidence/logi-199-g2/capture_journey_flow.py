import json
import os
import sys
from playwright.sync_api import sync_playwright

ARGS = ["--no-sandbox", "--disable-gpu", "--single-process", "--no-zygote"]
ENV = {"LD_LIBRARY_PATH": "/tmp/libs/lib:/tmp", "FONTCONFIG_PATH": "/tmp/libs/fonts"}
OUT = os.environ.get("OUT", "/tmp/cap/g2")
os.makedirs(OUT, exist_ok=True)
URL = os.environ.get("URL", "http://127.0.0.1:9501")
report: dict = {}


def scroll_top(pg) -> None:
    pg.evaluate(
        """() => {
          window.scrollTo(0, 0);
          document.documentElement.scrollTop = 0;
          document.body.scrollTop = 0;
          for (const sel of ['[data-testid="stAppViewContainer"]', 'section.main', '.stApp']) {
            const el = document.querySelector(sel);
            if (el) el.scrollTop = 0;
          }
        }"""
    )


def open_lot(pg, lot="T6-FCL") -> None:
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.locator(".logi-shell").first.wait_for(state="visible", timeout=120000)
    pg.wait_for_timeout(1000)
    nav = pg.locator('a[href="/lo-hang"]').first
    nav.wait_for(state="attached", timeout=15000)
    nav.dispatch_event("click")
    pg.wait_for_timeout(800)
    try:
        pg.get_by_test_id("shipment-period-tat-ca").first.click(timeout=8000)
    except Exception as e:
        print("period skip", str(e)[:80])
    link = pg.locator(f'a[href="/lo-hang/{lot}"]').first
    link.wait_for(state="attached", timeout=25000)
    link.dispatch_event("click")
    pg.get_by_test_id("shipment-journey").wait_for(state="visible", timeout=45000)
    pg.wait_for_timeout(1000)
    scroll_top(pg)
    pg.wait_for_timeout(300)


def fonts(pg) -> dict:
    return pg.evaluate(
        """async () => {
          await document.fonts.ready;
          const f = [...document.fonts].map(x => x.family.replace(/"/g, '') + ' ' + x.weight + ' ' + x.status);
          return {
            faces: f.filter(s => /Be Vietnam|IBM Plex/.test(s)).slice(0, 30),
            beLoaded: document.fonts.check('12px "Be Vietnam Pro"'),
            plexLoaded: document.fonts.check('12px "IBM Plex Mono"'),
          };
        }"""
    )


def overflow(pg) -> int:
    return pg.evaluate("() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)")


mode = sys.argv[1] if len(sys.argv) > 1 else "desktop"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/tmp/chromium", args=ARGS, env=ENV)
    if mode == "desktop":
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
        open_lot(pg)
        report["fonts"] = fonts(pg)
        report["desktop_overflow_px"] = overflow(pg)
        report["legend_visible"] = pg.get_by_test_id("journey-status-legend").is_visible()
        report["utility_trigger_visible"] = pg.get_by_test_id("journey-utility-trigger").is_visible()
        pg.screenshot(path=f"{OUT}/desktop-01-journey-initial.png")
        report["zoom_initial"] = pg.get_by_test_id("journey-zoom-level").inner_text()
        report["nodes"] = pg.locator('[data-testid^="journey-node-"]').evaluate_all(
            "els => els.map(e => e.getAttribute('data-testid').replace('journey-node-', '') + ':' + e.getAttribute('data-state'))"
        )

        # node -> bubble
        pg.get_by_test_id("journey-node-on-board").click()
        pg.wait_for_timeout(600)
        report["bubble_visible"] = pg.get_by_test_id("journey-bubble").count()
        report["bubble_tasks"] = pg.locator('[data-testid^="journey-bubble-task-"]').evaluate_all(
            "els => els.map(e => e.innerText.replace(/\\n+/g, ' | ').slice(0, 160))"
        )
        pg.screenshot(path=f"{OUT}/desktop-02-node-bubble.png")

        # bubble -> task popup
        pg.locator('[data-testid="journey-bubble-task-stage"]').click()
        pg.wait_for_timeout(800)
        report["modal_open"] = pg.get_by_test_id("journey-modal").count()
        sec = pg.get_by_test_id("fact-fields-secondary")
        if sec.count():
            report["secondary_folded"] = sec.evaluate("el => !el.hasAttribute('open')")
        pg.screenshot(path=f"{OUT}/desktop-03-task-popup.png")

        # input + save
        inp = pg.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
        report["onboard_input_visible"] = inp.count()
        if inp.count():
            inp.first.wait_for(state="visible", timeout=15000)
            inp.first.fill("2026-10-03")
            pg.get_by_role("button", name="Lưu mốc có bằng chứng", exact=True).click()
            pg.wait_for_timeout(2000)
        pg.screenshot(path=f"{OUT}/desktop-04-after-save.png")

        # readback: reload and reopen the same node/task
        open_lot(pg)
        pg.get_by_test_id("journey-node-on-board").click()
        pg.wait_for_timeout(500)
        pg.locator('[data-testid="journey-bubble-task-stage"]').click()
        pg.wait_for_timeout(800)
        inp2 = pg.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
        if inp2.count():
            inp2.first.wait_for(state="visible", timeout=15000)
            report["readback_value"] = inp2.first.input_value()
        pg.screenshot(path=f"{OUT}/desktop-05-reopen-readback.png")

        # close task modal, then test floating Hồ sơ & Tài chính utility bubble -> whole-lot overlay
        pg.locator('[aria-label="Đóng công đoạn"]').click()
        pg.wait_for_timeout(300)
        pg.get_by_test_id("journey-utility-trigger").click()
        pg.get_by_test_id("journey-utility-bubble").wait_for(state="visible", timeout=10000)
        pg.screenshot(path=f"{OUT}/desktop-06-utility-bubble.png")
        pg.get_by_test_id("journey-utility-item-tai-chinh").click()
        pg.get_by_test_id("journey-global-workspace").wait_for(state="visible", timeout=10000)
        pg.screenshot(path=f"{OUT}/desktop-07-finance-overlay.png")

        report["desktop_errors"] = errs[:5]
        pg.close()
    else:
        pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
        open_lot(pg)
        report["mobile_overflow_px"] = overflow(pg)
        pg.screenshot(path=f"{OUT}/mobile-01-journey-initial.png")

        # Tap arrival node for mobile bubble + sheet screenshots
        pg.get_by_test_id("journey-node-arrival").tap()
        pg.wait_for_timeout(600)
        report["mobile_bubble_visible"] = pg.get_by_test_id("journey-bubble").count()
        pg.screenshot(path=f"{OUT}/mobile-02-node-bubble.png")

        pg.locator('[data-testid="journey-bubble-task-stage"]').tap()
        pg.wait_for_timeout(900)
        report["mobile_modal_open"] = pg.get_by_test_id("journey-modal").count()
        report["mobile_overflow_modal_px"] = overflow(pg)
        pg.screenshot(path=f"{OUT}/mobile-03-task-sheet.png")

        # Mobile bottom sheet real write + readback proof on T6-FCL (on-board node)
        pg.locator('[aria-label="Đóng công đoạn"]').click()
        pg.wait_for_timeout(300)
        pg.get_by_test_id("journey-node-on-board").dispatch_event("click")
        pg.wait_for_timeout(500)
        pg.locator('[data-testid="journey-bubble-task-stage"]').dispatch_event("click")
        pg.wait_for_timeout(800)
        inp_m = pg.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
        if inp_m.count():
            inp_m.first.fill("2026-10-04")
            save_btn = pg.get_by_role("button", name="Lưu mốc có bằng chứng", exact=True)
            save_btn.scroll_into_view_if_needed()
            save_btn.click()
            pg.wait_for_timeout(2000)
            open_lot(pg)
            pg.get_by_test_id("journey-node-on-board").dispatch_event("click")
            pg.wait_for_timeout(500)
            pg.locator('[data-testid="journey-bubble-task-stage"]').dispatch_event("click")
            pg.wait_for_timeout(800)
            inp_m2 = pg.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
            report["mobile_readback_value"] = inp_m2.first.input_value()

        report["mobile_errors"] = errs[:5]
        pg.close()
    b.close()
print(json.dumps(report, ensure_ascii=False, indent=1))
