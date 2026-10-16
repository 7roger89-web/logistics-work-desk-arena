#!/usr/bin/env python3
"""LOGI #199 — restore the Owner-approved paper chart background.

Side-by-side Chromium comparison of the Owner HTML oracle
(``reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html``, SHA-256
``26e2e5cf…c3647f``) and the real app (isolated Mongomock staging) after the
background restoration.

Captures per the Owner request:
- Desktop 1440x900: initial map, node bubble, task popup — Owner HTML + app.
- Mobile 390x844: initial map, real touch pan, popup/bottom sheet — both.
- Zero-node SEA-188: full paper background, no fabricated stages, one CTA.
- One isolated save/reload/readback (T6-FCL ON BOARD date).

Also proves the texture in the app is byte-identical to the donor JPEG embedded
in the Owner HTML (same SHA-256) and that the donor parameters are used
(#EDF1F5 base, 760px repeat, opacity 0.34, multiply, 52x52 grid rgba(120,146,170,0.16)).

Run after rebuilding component/dist and starting scripts/logi199_t6_staging_app.py
on port 9501. The only business write is the isolated Mongomock T6-FCL
on-board-date save/readback.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(__file__).resolve().parent
OUT = EVIDENCE_ROOT
OWNER_HTML = ROOT / "reference" / "owner-2026-10-15" / "logi-journey-mimo-sonnet-fusion.html"
OWNER_URL = f"file://{OWNER_HTML}"
URL = os.environ.get("LOGI_STAGING_URL", "http://127.0.0.1:9501")
DATE_VALUE = "2026-10-04"
CHROMIUM = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE", "/tmp/chromium")
CHROMIUM_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
LAUNCH_ENV = {"LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", "/tmp/al2023/lib:/tmp"), **os.environ}

# Owner-approved donor parameters (exact values from the approved HTML oracle).
DONOR_PARAMS = {
    "base": "#EDF1F5",
    "textureSize": "760px",
    "textureRepeat": "repeat",
    "textureOpacity": 0.34,
    "textureBlend": "multiply",
    "gridSize": "52px 52px",
    "gridColor": "rgba(120, 146, 170, 0.16)",
}


def box(locator) -> dict[str, float] | None:
    value = locator.bounding_box(timeout=8000)
    return {key: round(float(value[key]), 2) for key in ("x", "y", "width", "height")} if value else None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_sha() -> str:
    import subprocess

    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def dist_hashes() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in ("logi-shell.js", "logi-shell.css"):
        path = ROOT / "component" / "dist" / name
        out[name] = sha256_bytes(path.read_bytes()) if path.is_file() else None
    return out


# --------------------------------------------------------------------------- #
# Owner HTML oracle helpers
# --------------------------------------------------------------------------- #

def owner_texture_params(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const all = [...document.querySelectorAll('div')];
          const tex = all.find(el => (el.getAttribute('style') || '').includes('760px'));
          const grid = all.find(el => (el.getAttribute('style') || '').includes('52px 52px'));
          const wrap = tex ? tex.parentElement : null;
          const read = el => {
            if (!el) return null;
            const css = getComputedStyle(el);
            const bg = css.backgroundImage || '';
            const m = bg.match(/url\\("?data:image\\/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)"?\\)/);
            return {
              opacity: css.opacity,
              mixBlendMode: css.mixBlendMode,
              backgroundSize: css.backgroundSize,
              backgroundRepeat: css.backgroundRepeat,
              backgroundColor: css.backgroundColor,
              dataImageMime: m ? m[1] : null,
              dataImageBytes: m ? m[2].length : null,
              dataImageSha256: m ? null : null,
              _b64: m ? m[2] : null,
            };
          };
          const t = read(tex), g = read(grid), w = read(wrap);
          const gridImage = grid ? getComputedStyle(grid).backgroundImage : '';
          return {
            wrapBackground: w ? w.backgroundColor : null,
            texture: t && {opacity: t.opacity, mixBlendMode: t.mixBlendMode, backgroundSize: t.backgroundSize, backgroundRepeat: t.backgroundRepeat, dataImageMime: t.dataImageMime, dataImageSha256: t._b64 ? null : null, _b64: t._b64},
            grid: g && {backgroundSize: g.backgroundSize, backgroundImage: gridImage.slice(0, 220)},
          };
        }"""
    )


def owner_transform(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const svg = [...document.querySelectorAll('svg')].find(el => (el.getAttribute('style') || '').includes('scale('));
          const raw = svg ? (svg.style.transform || '') : '';
          const m = raw.match(/translate\\(\\s*(-?[\\d.]+)px,\\s*(-?[\\d.]+)px\\)\\s*scale\\(\\s*([\\d.]+)\\s*\\)/);
          return m ? {raw, x: Number(m[1]), y: Number(m[2]), scale: Number(m[3])} : {raw, x: null, y: null, scale: null};
        }"""
    )


def open_owner(page: Page) -> None:
    page.goto(OWNER_URL, wait_until="load", timeout=60000)
    page.locator('[data-node="BOOKING"]').first.wait_for(state="visible", timeout=30000)
    page.wait_for_timeout(900)


# --------------------------------------------------------------------------- #
# App helpers (same canonical selectors as evidence/logi-199-g2/capture_journey_flow.py)
# --------------------------------------------------------------------------- #

def open_shipment(page: Page, shipment_id: str) -> None:
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.locator(".logi-shell").first.wait_for(state="visible", timeout=120000)
    page.wait_for_timeout(1000)
    nav = page.locator('a[href="/lo-hang"]').first
    nav.wait_for(state="attached", timeout=20000)
    nav.dispatch_event("click")
    page.wait_for_timeout(500)
    try:
        page.get_by_test_id("shipment-period-tat-ca").first.click(timeout=7000)
    except Exception:
        pass
    lot_link = page.locator(f'a[href="/lo-hang/{shipment_id}"]').first
    lot_link.wait_for(state="attached", timeout=25000)
    lot_link.dispatch_event("click")
    page.get_by_test_id("shipment-journey").wait_for(state="visible", timeout=45000)
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, 0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0")
    page.wait_for_timeout(200)


def map_transform(page: Page) -> dict[str, Any]:
    return page.get_by_test_id("journey-map-transform").evaluate(
        """el => {
          const transform = el.style.transform || getComputedStyle(el).transform;
          const match = transform.match(/translate\\(\\s*(-?[\\d.]+)px,\\s*(-?[\\d.]+)px\\)\\s*scale\\(\\s*([\\d.]+)\\s*\\)/);
          return match
            ? {raw: transform, x: Number(match[1]), y: Number(match[2]), scale: Number(match[3])}
            : {raw: transform, x: null, y: null, scale: null};
        }"""
    )


def tap_or_click(locator, how: str = "tap") -> str:
    """Real touch tap when the node is on-screen; recorded dispatch click otherwise."""
    try:
        if how == "tap":
            locator.tap(timeout=5000)
        else:
            locator.click(timeout=5000)
        return how
    except Exception:
        locator.dispatch_event("click")
        return "dispatch_event"


def app_texture_params(page: Page) -> dict[str, Any]:
    """Read the donor layers through locators (the shell renders in a shadow root,
    so plain document.querySelector cannot see it)."""
    read = """el => {
      const css = getComputedStyle(el);
      const bg = css.backgroundImage || '';
      let dataImageMime = null, b64 = null;
      const i = bg.indexOf('data:image/');
      if (i >= 0) {
        const mimeEnd = bg.indexOf(';', i);
        dataImageMime = bg.slice(i + 11, mimeEnd);
        const b64Start = bg.indexOf('base64,', mimeEnd) + 7;
        let cand = bg.slice(b64Start, bg.indexOf(')', b64Start));
        if (cand.endsWith('"') || cand.endsWith("'")) cand = cand.slice(0, -1);
        b64 = cand;
      }
      return {
        opacity: css.opacity, mixBlendMode: css.mixBlendMode,
        backgroundSize: css.backgroundSize, backgroundRepeat: css.backgroundRepeat,
        backgroundColor: css.backgroundColor,
        dataImageMime, _b64: b64,
        backgroundImage: bg.slice(0, 220),
      };
    }"""
    vp = page.get_by_test_id("journey-map-viewport")
    tex = page.get_by_test_id("journey-map-texture")
    grid = page.get_by_test_id("journey-map-grid")
    return {
        "viewportBackground": vp.evaluate("el => getComputedStyle(el).backgroundColor") if vp.count() else None,
        "texture": tex.evaluate(read) if tex.count() else None,
        "grid": grid.evaluate(read) if grid.count() else None,
    }


def install_touch_probe(page: Page) -> None:
    page.evaluate(
        """() => {
          window.__logiTouchEvents = [];
          const collect = event => {
            const path = typeof event.composedPath === 'function' ? event.composedPath() : [];
            const inMap = path.some(node => node instanceof Element && (
              node.getAttribute('data-testid') === 'journey-map-viewport' ||
              node.getAttribute('data-node') ||
              String(node.className || '').includes('touch-none') ||
              String(node.className || '').includes('journey-canvas')));
            if (!inMap) return;
            window.__logiTouchEvents.push({
              type: event.type, pointerType: event.pointerType || null,
              clientX: Number.isFinite(event.clientX) ? event.clientX : null,
            });
          };
          ['pointerdown', 'pointermove', 'pointerup', 'pointercancel', 'touchstart', 'touchmove', 'touchend']
            .forEach(type => window.addEventListener(type, collect, true));
        }"""
    )


SELECTED_NODES = '[data-testid^="journey-node-"][aria-pressed="true"], [data-node][aria-pressed="true"]'


def selected_node_ids(page: Page) -> list[str]:
    return page.locator(SELECTED_NODES).evaluate_all(
        "els => els.map(el => el.getAttribute('data-testid') || el.getAttribute('data-node'))"
    )


def dispatch_touch_pan(page: Page, map_probe, band_probe=None) -> dict[str, Any]:
    """CDP real touch pan over an empty map region. map_probe() -> transform dict.

    band_probe() -> y coordinate (CSS px) of an empty band inside the map; when
    omitted the band sits at 47% of the viewport height.
    """
    before_transform = map_probe()
    if before_transform.get("x") is None:
        return {"verdict": "FAILED", "reason": f"unrecognized transform: {before_transform.get('raw')}"}
    selected_before = selected_node_ids(page)
    install_touch_probe(page)
    vw = page.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
    start_x = int(vw["w"] * 0.14)
    end_x = int(vw["w"] * 0.86)
    y = int(band_probe() if band_probe else vw["h"] * 0.47)
    session = page.context.new_cdp_session(page)
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": start_x, "y": y, "id": 1, "radiusX": 2, "radiusY": 2, "force": 1}]})
    for step in range(1, 13):
        x = round(start_x + (end_x - start_x) * step / 12)
        session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y, "id": 1, "radiusX": 2, "radiusY": 2, "force": 1}]})
        page.wait_for_timeout(20)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(350)
    events = page.evaluate("window.__logiTouchEvents || []")
    after_transform = map_probe()
    selected_after = selected_node_ids(page)
    overlays_after = {
        "roleDialogs": page.locator('[role=dialog]').count(),
        "appBubbles": page.get_by_test_id("journey-bubble").count(),
        "appModals": page.get_by_test_id("journey-modal").count(),
    }
    delta_x = round(float(after_transform["x"]) - float(before_transform["x"]), 2) if after_transform.get("x") is not None else None
    pass_touch = bool(events) and all(e["pointerType"] == "touch" for e in events if e["pointerType"] is not None)
    overlays_clear = all(v == 0 for v in overlays_after.values())
    return {
        "verdict": "PASS" if pass_touch and (delta_x or 0) >= 100 and not selected_after and overlays_clear else "FAILED",
        "input_method": "CDP Input.dispatchTouchEvent; touchStart + 12 touchMove + touchEnd",
        "observed_event_types": sorted({e["type"] for e in events}),
        "transform_before": before_transform,
        "transform_after": after_transform,
        "transform_delta_x": delta_x,
        "selected_before": selected_before,
        "selected_after": selected_after,
        "overlays_after": overlays_after,
    }


# --------------------------------------------------------------------------- #
# Captures
# --------------------------------------------------------------------------- #

def capture_owner(browser_factory, report: dict[str, Any]) -> None:
    # Desktop
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    open_owner(page)
    params = owner_texture_params(page)
    report["owner_texture"] = params
    report["owner_data_nodes"] = page.evaluate(
        "() => [...document.querySelectorAll('[data-node]')].map(el => el.getAttribute('data-node')).filter(v => v && !v.startsWith('zoom') && v !== 'utility-trigger')"
    )
    page.screenshot(path=str(OUT / "owner-desktop-1440x900-initial.png"))
    page.locator('[data-node="ON_BOARD"]').click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "owner-desktop-1440x900-node-bubble.png"))
    page.locator("button", has_text="OB-01").first.click()
    page.wait_for_timeout(500)
    dialogs = page.locator('[role="dialog"]')
    report["owner_desktop"] = {
        "viewport": [1440, 900],
        "bubble_dialog_count": dialogs.count(),
        "popup_visible": dialogs.count() >= 2,
    }
    page.screenshot(path=str(OUT / "owner-desktop-1440x900-task-popup.png"))
    browser.close()

    # Mobile
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    open_owner(page)
    page.screenshot(path=str(OUT / "owner-mobile-390x844-initial.png"))
    # Node bubble + task bottom sheet first (nodes are on-screen in the initial fit).
    page.locator('[data-node="ON_BOARD"]').tap()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "owner-mobile-390x844-node-bubble.png"))
    page.locator("button", has_text="OB-01").first.tap()
    page.wait_for_timeout(600)
    dialog = page.locator('[role="dialog"]').last
    dialog_box = box(dialog)
    report["owner_mobile"] = {
        "viewport": [390, 844],
        "sheet_box": dialog_box,
        "sheet_bottom_anchored": bool(dialog_box and dialog_box["y"] + dialog_box["height"] >= 844 - 8),
    }
    page.screenshot(path=str(OUT / "owner-mobile-390x844-task-sheet.png"))
    # Close the sheet (last dialog), then the bubble (first dialog), then pan.
    for _ in range(2):
        dialogs = page.locator('[role="dialog"]')
        if not dialogs.count():
            break
        close_btn = dialogs.last.locator("button", has_text="✕")
        if close_btn.count():
            close_btn.first.tap()
            page.wait_for_timeout(350)
        else:
            break
    band_y = page.locator('[data-node="BOOKING"]').evaluate("el => el.getBoundingClientRect().top - 40")
    pan = dispatch_touch_pan(page, lambda: owner_transform(page), band_probe=lambda: band_y)
    pan["dialogs_open_after_pan"] = page.locator('[role="dialog"]').count()
    report["owner_mobile_pan"] = pan
    report["owner_mobile"]["pan_verdict"] = pan["verdict"]
    page.screenshot(path=str(OUT / "owner-mobile-390x844-touch-pan.png"))
    page.screenshot(path=str(OUT / "owner-mobile-390x844-task-sheet.png"))
    browser.close()


def capture_app(browser_factory, report: dict[str, Any]) -> None:
    # Desktop T6-FCL
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_shipment(page, "T6-FCL")
    params = app_texture_params(page)
    report["app_texture"] = params
    record: dict[str, Any] = {
        "viewport": [1440, 900],
        "node_count": page.locator('[data-testid^="journey-node-"]').count(),
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "map_box": box(page.get_by_test_id("journey-map-viewport")),
    }
    if record["node_count"] != 11:
        raise AssertionError(f"T6-FCL expected 11 Journey nodes, got {record['node_count']}.")
    page.screenshot(path=str(OUT / "app-desktop-1440x900-initial.png"))
    page.get_by_test_id("journey-node-on-board").click()
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    record["node_bubble_box"] = box(page.get_by_test_id("journey-bubble"))
    page.screenshot(path=str(OUT / "app-desktop-1440x900-node-bubble.png"))
    page.get_by_test_id("journey-bubble-task-stage").click()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    modal_box = box(page.get_by_test_id("journey-modal"))
    record["task_modal_box"] = modal_box
    record["task_modal_center_error_px"] = round(abs((modal_box["x"] + modal_box["width"] / 2) - 720), 2) if modal_box else None
    page.screenshot(path=str(OUT / "app-desktop-1440x900-task-popup.png"))
    record["page_errors"] = errors
    report["app_desktop"] = record
    browser.close()

    # Mobile T6-FCL: initial, node bubble, sheet, real touch pan, save/readback
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_shipment(page, "T6-FCL")
    record = {
        "viewport": [390, 844],
        "node_count": page.locator('[data-testid^="journey-node-"]').count(),
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "map_box": box(page.get_by_test_id("journey-map-viewport")),
    }
    if record["node_count"] != 11:
        raise AssertionError(f"T6-FCL expected 11 mobile Journey nodes, got {record['node_count']}.")
    page.screenshot(path=str(OUT / "app-mobile-390x844-initial.png"))
    page.get_by_test_id("journey-node-arrival").tap()
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    record["node_bubble_box"] = box(page.get_by_test_id("journey-bubble"))
    page.screenshot(path=str(OUT / "app-mobile-390x844-node-bubble.png"))
    page.get_by_test_id("journey-bubble-task-stage").tap()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    sheet_box = box(page.get_by_test_id("journey-modal"))
    record["sheet_box"] = sheet_box
    record["sheet_bottom_anchored"] = bool(sheet_box and sheet_box["y"] + sheet_box["height"] >= 844 - 8)
    page.screenshot(path=str(OUT / "app-mobile-390x844-task-sheet.png"))
    page.get_by_role("button", name="Đóng công đoạn").tap()
    page.get_by_test_id("journey-modal").wait_for(state="detached", timeout=10000)
    if page.get_by_test_id("journey-bubble").count():
        page.get_by_test_id("journey-bubble-close").tap()
        page.get_by_test_id("journey-bubble").wait_for(state="detached", timeout=10000)
    pan = dispatch_touch_pan(page, lambda: map_transform(page))
    report["app_mobile_pan"] = pan
    page.screenshot(path=str(OUT / "app-mobile-390x844-touch-pan.png"))

    # Isolated save/reload/readback (T6-FCL ON BOARD date) — the only business write.
    # Re-open the lot first so the map re-fits after the manual pan.
    open_shipment(page, "T6-FCL")
    save_open_how = tap_or_click(page.get_by_test_id("journey-node-on-board"))
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    tap_or_click(page.get_by_test_id("journey-bubble-task-stage"))
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    date_input = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    date_input.wait_for(state="visible", timeout=10000)
    prior_date_value = date_input.input_value()
    date_input.fill(DATE_VALUE)
    save_button = page.get_by_test_id("sea-export-facts-save")
    save_button.scroll_into_view_if_needed()
    save_button.tap()
    page.wait_for_timeout(1800)
    report["app_mobile_save"] = {
        "environment": "isolated staging / Mongomock",
        "lot": "T6-FCL",
        "stage": "ON BOARD",
        "date": DATE_VALUE,
        "prior_date_value_before_edit": prior_date_value,
        "save_tapped": True,
        "open_method": save_open_how,
        "no_payment_flow_used": True,
    }
    open_shipment(page, "T6-FCL")
    readback_open_how = tap_or_click(page.get_by_test_id("journey-node-on-board"))
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    tap_or_click(page.get_by_test_id("journey-bubble-task-stage"))
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    readback = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    readback.wait_for(state="visible", timeout=10000)
    readback_value = readback.input_value()
    report["app_mobile_readback"] = {"after_reload": True, "date": readback_value, "expected_date": DATE_VALUE, "open_method": readback_open_how}
    report["TAP_SAVE_READBACK_VERDICT"] = "PASS" if readback_value == DATE_VALUE else "FAILED"
    page.screenshot(path=str(OUT / "app-mobile-390x844-onboard-readback.png"))
    record["page_errors"] = errors
    report["app_mobile"] = record
    browser.close()

    # Zero-node SEA-188 (desktop + mobile)
    for label, width, height, mobile in (
        ("app-desktop-1440x900", 1440, 900, False),
        ("app-mobile-390x844", 390, 844, True),
    ):
        browser = browser_factory()
        page = browser.new_page(viewport={"width": width, "height": height}, is_mobile=mobile, has_touch=mobile, device_scale_factor=1)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)[:240]))
        open_shipment(page, "SEA-188")
        zero = {
            "viewport": [width, height],
            "node_count": page.locator('[data-testid^="journey-node-"]').count(),
            "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
            "cta_count": page.locator('[data-testid="journey-zero-primary-cta"]').count(),
            "empty_state_text": page.get_by_test_id("journey-empty-map").inner_text().strip()[:160],
            "toolbar_text": page.get_by_test_id("journey-compact-toolbar").inner_text().strip()[:160],
            "texture": app_texture_params(page),
            "page_errors": errors,
        }
        report[f"zero_node_{label}"] = zero
        if zero["node_count"] != 0 or zero["edge_count"] != 0:
            raise AssertionError(f"{label} zero-node state fabricated nodes/edges: {zero['node_count']}/{zero['edge_count']}.")
        if zero["cta_count"] != 1 or "Chưa có sơ đồ Journey" not in zero["empty_state_text"]:
            raise AssertionError(f"{label} zero-node state is not the truthful one-CTA empty state: {zero!r}.")
        page.screenshot(path=str(OUT / f"{label}-zero-node.png"))
        browser.close()


def compare(report: dict[str, Any]) -> None:
    owner = report.get("owner_texture") or {}
    app = report.get("app_texture") or {}
    o_t, a_t = owner.get("texture") or {}, app.get("texture") or {}
    o_g, a_g = owner.get("grid") or {}, app.get("grid") or {}

    def data_sha(params: dict[str, Any]) -> str | None:
        b64 = params.get("_b64")
        return sha256_bytes(base64.b64decode(b64)) if b64 else None

    o_sha, a_sha = data_sha(o_t), data_sha(a_t)
    report["texture_identity"] = {
        "owner_data_image_sha256": o_sha,
        "app_data_image_sha256": a_sha,
        "bytes_identical_to_donor": bool(o_sha and a_sha and o_sha == a_sha),
        "donor_expected_sha256": "e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627",
        "app_matches_owner_embedded_jpeg": a_sha == "e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627",
    }
    checks = {
        "base_#EDF1F5_owner": (owner.get("wrapBackground") or "").upper().replace(" ", "") in ("RGB(237,241,245)", "#EDF1F5"),
        "base_#EDF1F5_app": (app.get("viewportBackground") or "").upper().replace(" ", "") in ("RGB(237,241,245)", "#EDF1F5"),
        "texture_size_760_owner": (o_t.get("backgroundSize") or "").startswith("760px"),
        "texture_size_760_app": (a_t.get("backgroundSize") or "").startswith("760px"),
        "texture_repeat_owner": o_t.get("backgroundRepeat") == DONOR_PARAMS["textureRepeat"],
        "texture_repeat_app": a_t.get("backgroundRepeat") == DONOR_PARAMS["textureRepeat"],
        "texture_opacity_0.34_owner": abs(float(o_t.get("opacity") or 0) - 0.34) < 0.001,
        "texture_opacity_0.34_app": abs(float(a_t.get("opacity") or 0) - 0.34) < 0.001,
        "texture_multiply_owner": o_t.get("mixBlendMode") == DONOR_PARAMS["textureBlend"],
        "texture_multiply_app": a_t.get("mixBlendMode") == DONOR_PARAMS["textureBlend"],
        "texture_is_jpeg_owner": o_t.get("dataImageMime") == "jpeg",
        "texture_is_jpeg_app": a_t.get("dataImageMime") == "jpeg",
        "grid_52px_owner": (o_g.get("backgroundSize") or "").startswith("52px 52px"),
        "grid_52px_app": (a_g.get("backgroundSize") or "").startswith("52px 52px"),
        "grid_color_owner": DONOR_PARAMS["gridColor"].replace(" ", "") in (o_g.get("backgroundImage") or "").replace(" ", ""),
        "grid_color_app": DONOR_PARAMS["gridColor"].replace(" ", "") in (a_g.get("backgroundImage") or "").replace(" ", ""),
    }
    report["donor_param_checks"] = checks
    report["DONOR_PARAMS_VERDICT"] = "PASS" if all(checks.values()) else "FAILED"
    report["pan_verdicts"] = {
        "owner_mobile_pan": (report.get("owner_mobile_pan") or {}).get("verdict"),
        "app_mobile_pan": (report.get("app_mobile_pan") or {}).get("verdict"),
    }
    report["COMPARISON_VERDICT"] = (
        "PASS"
        if report["DONOR_PARAMS_VERDICT"] == "PASS"
        and report["texture_identity"]["bytes_identical_to_donor"]
        and report.get("TAP_SAVE_READBACK_VERDICT") == "PASS"
        and all(v == "PASS" for v in report["pan_verdicts"].values())
        else "INCOMPLETE"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "task": "LOGI-199 restore Owner-approved paper chart background",
        "source_sha": source_sha(),
        "dist": dist_hashes(),
        "owner_reference": {
            "path": "reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html",
            "sha256": sha256_bytes(OWNER_HTML.read_bytes()),
        },
        "chromium": CHROMIUM,
    }
    with sync_playwright() as p:
        def browser_factory():
            # Fresh Chromium per section (this sandbox's headless shell is
            # unreliable across close/recreate cycles on one instance).
            return p.chromium.launch(executable_path=CHROMIUM, args=CHROMIUM_ARGS, env=LAUNCH_ENV)

        capture_owner(browser_factory, report)
        capture_app(browser_factory, report)
    compare(report)
    # Strip raw base64 payloads from the serialized report (hashes are kept).
    def strip_b64(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: strip_b64(v) for k, v in obj.items() if k != "_b64"}
        if isinstance(obj, list):
            return [strip_b64(v) for v in obj]
        return obj

    (OUT / "metrics.json").write_text(json.dumps(strip_b64(report), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "DONOR_PARAMS_VERDICT": report["DONOR_PARAMS_VERDICT"],
        "texture_identity": report["texture_identity"],
        "TAP_SAVE_READBACK_VERDICT": report.get("TAP_SAVE_READBACK_VERDICT"),
        "COMPARISON_VERDICT": report["COMPARISON_VERDICT"],
    }, ensure_ascii=False, indent=2))
    if report["COMPARISON_VERDICT"] != "PASS":
        raise SystemExit("COMPARISON_VERDICT != PASS — inspect metrics.json")


if __name__ == "__main__":
    main()
