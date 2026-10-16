#!/usr/bin/env python3
"""LOGI #199 — final bounded owner-fidelity fix: A (mobile initial camera) +
B (save/readback with a REAL value change).

Run after rebuilding component/dist and with scripts/logi199_t6_staging_app.py
running on port 9501 (isolated Mongomock).

A — proves on 390x844 that a fresh T6-FCL view starts at the BEGINNING of the
route (BOOKING side, like the Owner HTML oracle), that "Đọc rõ" still jumps to
the stage needing handling, and that selecting a node still focuses it.

B — proves the ON BOARD date truly changes OLD -> NEW on save/reload/readback.
The harness FAILS CLOSED if OLD == NEW or if the readback is not NEW; it never
reuses a same-value save as PASS.
"""
from __future__ import annotations

import json
import hashlib
import subprocess
import os
import shutil
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
URL = os.environ.get("LOGI_STAGING_URL", "http://127.0.0.1:9501")
CHROMIUM = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE", "/tmp/chromium")
CHROMIUM_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
LAUNCH_ENV = {"LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", "/tmp/al2023/lib:/tmp"), **os.environ}

SEED_DATE = "2026-10-04"    # concrete OLD if the field is somehow still empty
ALT_DATE = "2026-10-11"     # valid date guaranteed != SEED_DATE
NODE_IDS = [
    "booking", "pickup", "customs-export", "si-vgm", "gate-in", "etd",
    "on-board", "transit", "arrival", "customs-import", "delivery",
]


def box(locator) -> dict[str, float] | None:
    value = locator.bounding_box(timeout=8000)
    return {key: round(float(value[key]), 2) for key in ("x", "y", "width", "height")} if value else None


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
    page.wait_for_timeout(700)
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


def visible_nodes(page: Page) -> list[dict[str, Any]]:
    """Node cards left-to-right with their visible width inside the map box."""
    m = box(page.get_by_test_id("journey-map-viewport"))
    out = []
    for node_id in NODE_IDS:
        loc = page.get_by_test_id(f"journey-node-{node_id}")
        if not loc.count():
            continue
        b = box(loc)
        if not b or not m:
            continue
        overlap = max(0.0, min(b["x"] + b["width"], m["x"] + m["width"]) - max(b["x"], m["x"]))
        out.append({
            "id": node_id, "box": b, "visible_px": round(overlap, 1),
            "in_view": overlap >= 40, "left_gap_in_map": round(b["x"] - m["x"], 1),
        })
    out.sort(key=lambda r: r["box"]["x"])
    return out


def tap_or_click(locator, how: str = "tap") -> str:
    try:
        if how == "tap":
            locator.tap(timeout=5000)
        else:
            locator.click(timeout=5000)
        return how
    except Exception:
        locator.dispatch_event("click")
        return "dispatch_event"


def open_onboard_editor(page: Page) -> str:
    # Navigate with actual controls rather than clicking an off-screen node.
    page.get_by_test_id("journey-zoom-fit").tap()
    how = "tap"
    page.get_by_test_id("journey-node-on-board").tap()
    page.get_by_test_id("journey-zoom-readable").tap()
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    page.get_by_test_id("journey-bubble-task-stage").tap()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    date_input = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    date_input.wait_for(state="visible", timeout=10000)
    return how


def save_and_reload(page: Page, date_value: str, shot: str) -> dict[str, Any]:
    date_input = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    date_input.fill(date_value)
    page.screenshot(path=str(OUT / shot))
    save_button = page.get_by_test_id("sea-export-facts-save")
    save_button.scroll_into_view_if_needed()
    save_button.tap()
    page.wait_for_timeout(1800)
    return {"save_tapped": True, "filled": date_value}


def capture_a(browser_factory, report: dict[str, Any]) -> None:
    # --- Mobile 390x844: initial camera must start at the journey BEGINNING ---
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_shipment(page, "T6-FCL")
    zoom_level = page.get_by_test_id("journey-zoom-level").inner_text().strip()
    tf = map_transform(page)
    nodes = visible_nodes(page)
    in_view = [n["id"] for n in nodes if n["in_view"]]
    title_px = page.get_by_test_id("journey-node-booking").evaluate(
        "el => parseFloat(getComputedStyle(el.querySelector('.font-extrabold')).fontSize)"
    )
    record = {
        "viewport": [390, 844],
        "node_count": page.locator('[data-testid^="journey-node-"]').count(),
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "zoom_level_text": zoom_level,
        "transform": tf,
        "scale_x_title_px": round(tf["scale"] * title_px, 2) if tf.get("scale") else None,
        "visible_nodes_left_to_right": nodes,
        "visible_ids": in_view,
        "page_errors": errors,
    }
    a_pass = bool(
        in_view and in_view[0] == "booking"
        and "pickup" in in_view
        and any(n.startswith("customs-export") for n in in_view)
        and record["node_count"] == 11
        and zoom_level in ("95%", "100%")
        and (record["scale_x_title_px"] or 0) >= 10
    )
    record["initial_camera_starts_at_journey_beginning"] = a_pass
    record["problem_ids"] = page.locator('[data-testid^="journey-node-"][data-state="PROBLEM"]').evaluate_all(
        "els => els.map(el => el.dataset.testid.replace('journey-node-', ''))"
    )
    report["A_mobile_initial"] = record
    page.screenshot(path=str(OUT / "mobile-after-initial.png"))

    # Easy access to the stage needing handling: "Đọc rõ" focuses it.
    page.get_by_test_id("journey-zoom-readable").tap()
    page.wait_for_timeout(400)
    focus_after = visible_nodes(page)
    report["A_doc_ro_focus"] = {
        "zoom_level_text": page.get_by_test_id("journey-zoom-level").inner_text().strip(),
        "centered_node": min(
            (n for n in focus_after if n["in_view"]),
            key=lambda n: abs(n["box"]["x"] + n["box"]["width"] / 2 - 195),
            default=None,
        ),
    }
    page.screenshot(path=str(OUT / "mobile-after-doc-ro-problem.png"))

    # Selection still focuses the chosen node (far node via DOM click, camera follows).
    page.get_by_test_id("journey-node-delivery").dispatch_event("click")
    page.wait_for_timeout(500)
    after_select = visible_nodes(page)
    report["A_select_focus"] = {
        "selected": page.locator('[data-testid^="journey-node-"][aria-pressed="true"]').evaluate_all(
            "els => els.map(e => e.getAttribute('data-testid'))"
        ),
        "centered_node": min(
            (n for n in after_select if n["in_view"]),
            key=lambda n: abs(n["box"]["x"] + n["box"]["width"] / 2 - 195),
            default=None,
        ),
    }
    page.screenshot(path=str(OUT / "mobile-after-select-focus-delivery.png"))
    # Real touch-pan + zoom/Fit remain usable after the initial-camera change.
    if page.get_by_test_id("journey-bubble").count():
        page.get_by_test_id("journey-bubble-close").tap()
    page.wait_for_timeout(250)
    zoom_before = map_transform(page)
    page.get_by_test_id("journey-zoom-in").tap()
    page.wait_for_timeout(250)
    after_zoom = map_transform(page)
    page.get_by_test_id("journey-zoom-fit").tap()
    page.wait_for_timeout(250)
    after_fit = map_transform(page)
    before_pan = map_transform(page)
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 55, "y": 450}]})
    for x in range(75, 296, 20):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": 450}]})
        page.wait_for_timeout(20)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(200)
    after_pan = map_transform(page)
    report["A_pan_zoom_fit"] = {
        "input": "CDP touchStart/touchMove/touchEnd",
        "delta_x": after_pan["x"] - before_pan["x"],
        "zoom_before": zoom_before["scale"], "zoom_after": after_zoom["scale"],
        "fit_scale": after_fit["scale"],
        "pass": after_pan["x"] > before_pan["x"] + 100 and after_zoom["scale"] > zoom_before["scale"] and after_fit["scale"] < 1,
    }
    browser.close()

    # --- Desktop unchanged (fit overview) ---
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    open_shipment(page, "T6-FCL")
    report["A_desktop_initial"] = {
        "viewport": [1440, 900],
        "zoom_level_text": page.get_by_test_id("journey-zoom-level").inner_text().strip(),
        "transform": map_transform(page),
        "visible": [n["id"] for n in visible_nodes(page) if n["in_view"]],
    }
    page.screenshot(path=str(OUT / "desktop-after-initial.png"))
    browser.close()

    selected = report["A_select_focus"]
    problem_focus = report["A_doc_ro_focus"]["centered_node"]
    report["A_VERDICT"] = "PASS" if (
        a_pass and selected["selected"] == ["journey-node-delivery"]
        and selected["centered_node"]["id"] == "delivery"
        and problem_focus and problem_focus["id"] in record["problem_ids"]
        and report["A_pan_zoom_fit"]["pass"]
    ) else "FAILED"


def capture_b(browser_factory, report: dict[str, Any]) -> None:
    browser = browser_factory()
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    open_shipment(page, "T6-FCL")

    open_onboard_editor(page)
    old = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True).input_value()
    seeded = False
    if not old:
        # Field empty: make the OLD state concrete first, then run OLD -> NEW.
        save_and_reload(page, SEED_DATE, "mobile-save-seed-old.png")
        open_shipment(page, "T6-FCL")
        open_onboard_editor(page)
        old = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True).input_value()
        seeded = True
    new = ALT_DATE if old == SEED_DATE else SEED_DATE
    page.screenshot(path=str(OUT / "mobile-save-before-old.png"))
    record: dict[str, Any] = {
        "environment": "isolated staging / Mongomock",
        "lot": "T6-FCL",
        "stage": "ON BOARD",
        "field": "Ngày xếp hàng lên tàu (on-board)",
        "seeded_old_first": seeded,
        "old_value_before_save": old,
        "new_value_filled": new,
    }
    if new == old:
        record["verdict"] = "FAILED"
        record["reason"] = "NEW equals OLD; refusing a same-value save as PASS"
        report["B_save_readback"] = record
        report["B_OLD_TO_NEW"] = record
        report["B_VERDICT"] = "FAILED"
        browser.close()
        return

    save_and_reload(page, new, "mobile-save-filled-new.png")
    open_shipment(page, "T6-FCL")  # reload before independently reading the value back
    open_onboard_editor(page)
    readback = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True).input_value()
    page.screenshot(path=str(OUT / "mobile-save-readback-new.png"))
    record.update({
        "save_tapped": True,
        "readback_after_reload": readback,
        "state_change": f"{old} -> {readback}",
        "changed": readback != old,
        "verdict": "PASS" if readback == new and readback != old else "FAILED",
    })
    report["B_save_readback"] = record
    report["B_OLD_TO_NEW"] = {
        "old": old,
        "new": new,
        "readback": readback,
        "evidence": "before-shot shows OLD in the field; filled-shot shows NEW; readback-shot shows the persisted NEW after reload",
    }
    report["B_VERDICT"] = record["verdict"]
    browser.close()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before_src = ROOT / "evidence" / "logi-199-restore" / "app-mobile-390x844-initial.png"
    if before_src.is_file():
        shutil.copyfile(before_src, OUT / "mobile-before-initial.png")
    report: dict[str, Any] = {
        "capture_base_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "captured_file_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in ("component/src/components/JourneyMap.tsx", "component/dist/logi-shell.js", "component/dist/logi-shell.css", "evidence/logi-199-final-fix/capture_fix_ab.py")
        },
        "task": "LOGI-199 final bounded fix A (mobile initial camera) + B (save/readback OLD->NEW)",
        "before_image_provenance": "evidence/logi-199-restore/app-mobile-390x844-initial.png captured at HEAD abf3c0edca0e0c24e7cba840ca2923623454653e",
    }
    with sync_playwright() as p:
        def browser_factory():
            return p.chromium.launch(executable_path=CHROMIUM, args=CHROMIUM_ARGS, env=LAUNCH_ENV)

        capture_a(browser_factory, report)
        capture_b(browser_factory, report)

    (OUT / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "A_VERDICT": report.get("A_VERDICT"),
        "A_visible_ids": (report.get("A_mobile_initial") or {}).get("visible_ids"),
        "B_VERDICT": report.get("B_VERDICT"),
        "B_OLD_TO_NEW": report.get("B_OLD_TO_NEW"),
    }, ensure_ascii=False, indent=2))
    if report.get("A_VERDICT") != "PASS" or report.get("B_VERDICT") != "PASS":
        raise SystemExit("A_VERDICT or B_VERDICT != PASS — inspect metrics.json")


if __name__ == "__main__":
    main()
