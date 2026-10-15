"""Real-Chromium capture & visual audit for LOGI-199 G1, G3, and G4."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("STAGING_URL", "http://127.0.0.1:9501")
CHROMIUM = os.environ.get("CHROMIUM_BIN", "/tmp/chromium")
ROOT = Path(__file__).resolve().parents[1]

LAUNCH_ENV = {
    **os.environ,
    "LD_LIBRARY_PATH": "/tmp/libs/lib:/tmp",
    "FONTCONFIG_PATH": "/tmp/libs/fonts",
}
LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]


def nav_sidebar(page, label: str, mobile: bool = False):
    if label.startswith("/"):
        aside_link = page.locator(f'aside a[href="{label}"]').first
    else:
        aside_link = page.locator("aside a", has_text=label).first
    aside_link.dispatch_event("click")
    page.wait_for_timeout(300)
    page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
    page.wait_for_timeout(120)


def check_metrics(page):
    return page.locator(".logi-shell").first.evaluate(
        """el => {
            const root = el.getRootNode();
            const cs = getComputedStyle(el);
            const docOverflow = Math.max(0, document.documentElement.scrollWidth - window.innerWidth);
            const shellOverflow = Math.max(0, el.scrollWidth - el.clientWidth);
            const tooSmall = [];
            for (const node of root.querySelectorAll("*")) {
                if (node.closest && node.closest('[aria-hidden="true"], .sr-only')) continue;
                if (node.classList && node.classList.contains("journey-node-step") && node.closest(".journey-map-first")) continue;
                const directText = Array.from(node.childNodes)
                    .filter(c => c.nodeType === 3)
                    .map(c => c.textContent.trim())
                    .join("");
                if (!directText) continue;
                const r = node.getBoundingClientRect();
                if (r.width < 2 || r.height < 2) continue;
                const s = getComputedStyle(node);
                if (s.visibility === "hidden" || s.display === "none" || Number(s.opacity) === 0) continue;
                const px = parseFloat(s.fontSize);
                if (px < 11.9) {
                    tooSmall.push({ tag: node.tagName, px, text: directText.slice(0, 40), cls: String(node.className || "").slice(0, 60) });
                }
            }
            return {
                fontFamily: cs.fontFamily,
                color: cs.color,
                backgroundColor: cs.backgroundColor,
                overflowPx: Math.max(docOverflow, shellOverflow),
                tooSmallCount: tooSmall.length,
                tooSmallSample: tooSmall.slice(0, 5),
            };
        }"""
    )


def snap(page, out_dir: Path, mode: str, slug: str, report: dict):
    metrics = check_metrics(page)
    img_path = out_dir / f"{mode}-{slug}.png"
    page.screenshot(path=str(img_path))
    report[mode][slug] = {**metrics, "screenshot": str(img_path.relative_to(ROOT))}


def run_g1():
    out_dir = ROOT / "evidence/logi-199-g1"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"desktop": {}, "mobile": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM, args=LAUNCH_ARGS, env=LAUNCH_ENV)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.locator(".logi-shell").first.wait_for(state="visible", timeout=30000)
        page.wait_for_timeout(600)

        routes = [
            ("01-home", "Tổng Quan Công Việc"),
            ("02-shipments", "Lô Hàng"),
            ("03-quotes", "Báo Giá"),
            ("04-receivables", "Thu tiền"),
        ]
        for mode, vp in [("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
            is_mobile = mode == "mobile"
            page.set_viewport_size(vp)
            page.wait_for_timeout(250)
            for slug, nav_label in routes:
                nav_sidebar(page, nav_label, mobile=is_mobile)
                snap(page, out_dir, mode, slug, report)
            report[mode]["errors"] = list(errs)

        browser.close()

    (out_dir / "g1_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def run_g3():
    out_dir = ROOT / "evidence/logi-199-g3"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"desktop": {}, "mobile": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM, args=LAUNCH_ARGS, env=LAUNCH_ENV)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.locator(".logi-shell").first.wait_for(state="visible", timeout=30000)
        page.wait_for_timeout(600)

        for mode, vp in [("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
            is_mobile = mode == "mobile"
            page.set_viewport_size(vp)
            page.wait_for_timeout(250)

            # 1. Home
            nav_sidebar(page, "Tổng Quan Công Việc", mobile=is_mobile)
            snap(page, out_dir, mode, "01-home", report)

            # 2. Điều hành (OperationsControlTower)
            nav_sidebar(page, "Điều hành", mobile=is_mobile)
            snap(page, out_dir, mode, "02-dieu-hanh", report)

            # 3. Lô Hàng (Shipments list)
            nav_sidebar(page, "Lô Hàng", mobile=is_mobile)
            snap(page, out_dir, mode, "03-lo-hang", report)

            # 4. Tạo Lô Mới (CreateShipment)
            nav_sidebar(page, "Tạo Lô Mới", mobile=is_mobile)
            snap(page, out_dir, mode, "04-tao-lo-moi", report)

            # 5. Khách Hàng + CustomerPlaybook (/khach-hang/:id)
            nav_sidebar(page, "Khách Hàng", mobile=is_mobile)
            snap(page, out_dir, mode, "05-khach-hang", report)
            playbook_link = page.locator('[data-testid="customer-open-playbook"]').first
            if playbook_link.count():
                playbook_link.dispatch_event("click")
                page.wait_for_timeout(350)
                page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
                snap(page, out_dir, mode, "05b-customer-playbook", report)

            # 6. Đại Lý Trường Thành (/ngu-canh-doi-tac)
            nav_sidebar(page, "Đại Lý Trường Thành", mobile=is_mobile)
            snap(page, out_dir, mode, "06-doi-tac", report)

            # 7. Báo Giá (/kinh-doanh-bao-gia)
            nav_sidebar(page, "Báo Giá", mobile=is_mobile)
            snap(page, out_dir, mode, "07-bao-gia", report)

            # 8. Hợp đồng + Tạo hợp đồng mới + Chi tiết hợp đồng
            nav_sidebar(page, "Hợp đồng", mobile=is_mobile)
            snap(page, out_dir, mode, "08-hop-dong", report)
            ct_detail = page.locator('a[href^="/hop-dong/HD"]').first
            if ct_detail.count():
                ct_detail.dispatch_event("click")
                page.wait_for_timeout(350)
                page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
                snap(page, out_dir, mode, "08b-hop-dong-chi-tiet", report)
            nav_sidebar(page, "Hợp đồng", mobile=is_mobile)
            new_ct = page.locator('a[href="/hop-dong/moi"]').first
            if new_ct.count():
                new_ct.dispatch_event("click")
                page.wait_for_timeout(350)
                page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
                snap(page, out_dir, mode, "08c-hop-dong-moi", report)

            # 9. Thu tiền (/tai-chinh/thu-tien) + Receipt sheet popup
            nav_sidebar(page, "Thu tiền", mobile=is_mobile)
            snap(page, out_dir, mode, "09-thu-tien", report)
            pay_btn = page.locator("button:visible", has_text=re.compile(r"thu tiền", re.I)).first
            if pay_btn.count():
                pay_btn.click()
                page.wait_for_timeout(300)
                snap(page, out_dir, mode, "09b-thu-tien-popup", report)
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)

            # 10. Đối soát (/tai-chinh/doi-soat)
            nav_sidebar(page, "Đối soát", mobile=is_mobile)
            snap(page, out_dir, mode, "10-doi-soat", report)

            # 11. Công nợ đối tác (/tai-chinh/cong-no-doi-tac) + Payment sheet popup
            nav_sidebar(page, "Công nợ đối tác", mobile=is_mobile)
            snap(page, out_dir, mode, "11-cong-no-doi-tac", report)
            partner_pay_btn = page.locator("button:visible", has_text=re.compile(r"trả đối tác", re.I)).first
            if partner_pay_btn.count():
                partner_pay_btn.click()
                page.wait_for_timeout(250)
                snap(page, out_dir, mode, "11b-cong-no-popup", report)
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
            else:
                report[mode]["11b-cong-no-popup"] = {
                    "status": "NOT_RUN",
                    "reason": "Fixture staging không có dòng công nợ đối tác đã xác nhận (0 dòng — giữ đúng invariant UNKNOWN != 0), nên nút mở popup Trả đối tác không hiển thị.",
                }

            # 12. Báo cáo CEO (/bao-cao-ceo)
            nav_sidebar(page, "Báo cáo CEO", mobile=is_mobile)
            snap(page, out_dir, mode, "12-bao-cao-ceo", report)

            report[mode]["errors"] = list(errs)

        browser.close()

    (out_dir / "g3_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def run_g4():
    out_dir = ROOT / "evidence/logi-199-g4"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"desktop": {}, "mobile": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM, args=LAUNCH_ARGS, env=LAUNCH_ENV)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.locator(".logi-shell").first.wait_for(state="visible", timeout=30000)
        page.wait_for_timeout(600)

        routes = [
            ("01-bieu-thue", "/tra-cuu-thue"),
            ("02-tra-cuu-chinh-sach", "/tra-cuu-chinh-sach"),
            ("03-so-tay", "/so-tay"),
            ("04-dich-thuat", "/dich-thuat"),
            ("05-thanh-toan-quoc-te", "/thanh-toan-quoc-te"),
            ("06-quy-trinh", "/quy-trinh"),
            ("07-bieu-mau", "/bieu-mau"),
            ("08-nguoi-dung", "/nguoi-dung"),
        ]
        for mode, vp in [("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
            is_mobile = mode == "mobile"
            page.set_viewport_size(vp)
            page.wait_for_timeout(250)
            for slug, nav_label in routes:
                nav_sidebar(page, nav_label, mobile=is_mobile)
                snap(page, out_dir, mode, slug, report)

            # Quick-add modal & Notification drawer
            notif_btn = page.locator('button[aria-label="Thông báo"]').first
            if notif_btn.count() and notif_btn.is_visible():
                notif_btn.click()
                page.wait_for_timeout(250)
                snap(page, out_dir, mode, "09-notif-drawer", report)
                close_notif = page.locator('div.fixed.inset-0.z-50 button').first
                if close_notif.count():
                    close_notif.click()
                    page.wait_for_timeout(200)

            add_btn = page.locator('nav button:has-text("Thêm")').first if is_mobile else page.locator("button:visible", has_text="Thêm").first
            if add_btn.count():
                add_btn.click()
                page.wait_for_timeout(250)
                snap(page, out_dir, mode, "10-quick-add-sheet", report)
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)

            report[mode]["errors"] = list(errs)

        browser.close()

    (out_dir / "g4_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def run_gaps():
    g3_dir = ROOT / "evidence/logi-199-g3"
    g4_dir = ROOT / "evidence/logi-199-g4"
    g3_report = json.loads((g3_dir / "g3_report.json").read_text(encoding="utf-8"))
    g4_report = json.loads((g4_dir / "g4_report.json").read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM, args=LAUNCH_ARGS, env=LAUNCH_ENV)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.locator(".logi-shell").first.wait_for(state="visible", timeout=30000)
        page.wait_for_timeout(600)

        # Desktop 08b contract detail + 11b NOT_RUN record
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(250)
        nav_sidebar(page, "Hợp đồng", mobile=False)
        ct_detail = page.locator('a[href^="/hop-dong/HD"]').first
        if ct_detail.count():
            ct_detail.dispatch_event("click")
            page.wait_for_timeout(350)
            page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
            snap(page, g3_dir, "desktop", "08b-hop-dong-chi-tiet", g3_report)
        g3_report["desktop"]["11b-cong-no-popup"] = {
            "status": "NOT_RUN",
            "reason": "Fixture staging không có dòng công nợ đối tác đã xác nhận (0 dòng — giữ đúng invariant UNKNOWN != 0), nên nút mở popup Trả đối tác không hiển thị.",
        }

        # Mobile gaps: 05b-customer-playbook, 08b-hop-dong-chi-tiet, 08c-hop-dong-moi, 09b-thu-tien-popup, 10-quick-add-sheet
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(300)

        nav_sidebar(page, "Khách Hàng", mobile=True)
        playbook_link = page.locator('[data-testid="customer-open-playbook"]').first
        if playbook_link.count():
            playbook_link.dispatch_event("click")
            page.wait_for_timeout(350)
            page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
            snap(page, g3_dir, "mobile", "05b-customer-playbook", g3_report)

        nav_sidebar(page, "Hợp đồng", mobile=True)
        ct_detail_m = page.locator('a[href^="/hop-dong/HD"]').first
        if ct_detail_m.count():
            ct_detail_m.dispatch_event("click")
            page.wait_for_timeout(350)
            page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
            snap(page, g3_dir, "mobile", "08b-hop-dong-chi-tiet", g3_report)

        nav_sidebar(page, "Hợp đồng", mobile=True)
        new_ct_m = page.locator('a[href="/hop-dong/moi"]').first
        if new_ct_m.count():
            new_ct_m.dispatch_event("click")
            page.wait_for_timeout(350)
            page.locator(".logi-shell").first.evaluate("el => { el.scrollTop = 0; }")
            snap(page, g3_dir, "mobile", "08c-hop-dong-moi", g3_report)

        nav_sidebar(page, "Thu tiền", mobile=True)
        pay_btn_m = page.locator("button:visible", has_text=re.compile(r"thu tiền", re.I)).first
        if pay_btn_m.count():
            pay_btn_m.click()
            page.wait_for_timeout(300)
            snap(page, g3_dir, "mobile", "09b-thu-tien-popup", g3_report)
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)

        g3_report["mobile"]["11b-cong-no-popup"] = {
            "status": "NOT_RUN",
            "reason": "Fixture staging không có dòng công nợ đối tác đã xác nhận (0 dòng — giữ đúng invariant UNKNOWN != 0), nên nút mở popup Trả đối tác không hiển thị.",
        }

        nav_sidebar(page, "/nguoi-dung", mobile=True)
        add_btn_m = page.locator('nav button:has-text("Thêm")').first
        if add_btn_m.count():
            add_btn_m.click()
            page.wait_for_timeout(300)
            snap(page, g4_dir, "mobile", "10-quick-add-sheet", g4_report)
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)

        g3_report["mobile"]["errors"] = list(errs)
        g4_report["mobile"]["errors"] = list(errs)
        browser.close()

    (g3_dir / "g3_report.json").write_text(json.dumps(g3_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (g4_dir / "g4_report.json").write_text(json.dumps(g4_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"g3_mobile_keys": list(g3_report["mobile"].keys()), "g4_mobile_keys": list(g4_report["mobile"].keys()), "errors": errs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "g1"
    if stage == "g1":
        run_g1()
    elif stage == "g3":
        run_g3()
    elif stage == "g4":
        run_g4()
    elif stage == "gaps":
        run_gaps()
