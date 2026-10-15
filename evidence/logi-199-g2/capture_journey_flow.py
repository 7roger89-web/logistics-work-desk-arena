#!/usr/bin/env python3
"""Focused LOGI-APP-RENEWAL-01 zero-node/pointer and T6 browser evidence.

Run after rebuilding component/dist and starting scripts/logi199_t6_staging_app.py
on port 9501. The only business write is the required isolated Mongomock
T6-FCL on-board-date save/readback. Zero-node CTA testing is read-only; no
Receivables/payment flow runs in this bounded capture.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(__file__).resolve().parent
OUT = EVIDENCE_ROOT / "current-source"
BEFORE = EVIDENCE_ROOT / "before" / "baseline_metrics.json"
URL = os.environ.get("LOGI_STAGING_URL", "http://127.0.0.1:9501")
DATE_VALUE = "2026-10-04"
CHROMIUM = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE", "/tmp/chromium")
CHROMIUM_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process", "--no-zygote"]
ZERO_SHIPMENT_ID = "SEA-188"


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def source_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def box(locator: Locator) -> dict[str, float] | None:
    value = locator.bounding_box(timeout=8000)
    return {key: round(float(value[key]), 2) for key in ("x", "y", "width", "height")} if value else None


def node_selection(page: Page) -> list[str]:
    return page.locator('[data-testid^="journey-node-"][aria-pressed="true"]').evaluate_all(
        "els => els.map(el => el.getAttribute('data-testid'))"
    )


def map_transform(page: Page) -> dict[str, Any]:
    return page.get_by_test_id("journey-map-transform").evaluate(
        """el => {
          const transform = el.style.transform || getComputedStyle(el).transform;
          const match = transform.match(/translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)\s*scale\(\s*([\d.]+)\s*\)/);
          return match
            ? {raw: transform, x: Number(match[1]), y: Number(match[2]), scale: Number(match[3])}
            : {raw: transform, x: null, y: null, scale: null};
        }"""
    )


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


def open_lot(page: Page) -> None:
    open_shipment(page, "T6-FCL")


def open_receivables(page: Page) -> None:
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.locator(".logi-shell").first.wait_for(state="visible", timeout=120000)
    page.wait_for_timeout(1000)
    route = page.locator('a[href="/tai-chinh/thu-tien"]').first
    route.wait_for(state="attached", timeout=25000)
    route.dispatch_event("click")
    page.get_by_text("Thu tiền khách · Phải thu", exact=True).wait_for(state="visible", timeout=30000)
    page.wait_for_timeout(300)


def viewport_overflow(page: Page) -> dict[str, float]:
    return page.evaluate(
        """() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
          horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
          documentHeight: document.documentElement.scrollHeight,
          viewportHeight: window.innerHeight
        })"""
    )


def no_box_overlap(a: dict[str, float] | None, b: dict[str, float] | None) -> bool | None:
    if not a or not b:
        return None
    return not (
        a["x"] < b["x"] + b["width"]
        and a["x"] + a["width"] > b["x"]
        and a["y"] < b["y"] + b["height"]
        and a["y"] + a["height"] > b["y"]
    )


def capture_desktop(browser: Browser, report: dict[str, Any]) -> None:
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_lot(page)
    identity = page.get_by_test_id("shipment-identity-bar")
    attention = page.get_by_test_id("attention-now")
    toolbar = page.get_by_test_id("journey-compact-toolbar")
    map_viewport = page.get_by_test_id("journey-map-viewport")
    completion = page.get_by_test_id("shipment-completion-goals")
    map_box = box(map_viewport)
    completion_box = box(completion)
    primary = page.get_by_test_id("attention-primary-cta")
    record: dict[str, Any] = {
        "viewport": [1440, 900],
        "identity_box": box(identity),
        "attention_box": box(attention),
        "attention_primary_text": primary.inner_text().strip(),
        "attention_primary_box": box(primary),
        "toolbar_box": box(toolbar),
        "map_box": map_box,
        "map_height_px": map_box["height"] if map_box else None,
        "map_height_target_780_810": bool(map_box and 780 <= map_box["height"] <= 810),
        "completion_review_box": completion_box,
        "completion_review_collapsed": page.get_by_test_id("completion-goal-toggle").get_attribute("aria-expanded") == "false",
        "completion_review_below_map": bool(map_box and completion_box and completion_box["y"] >= map_box["y"] + map_box["height"] - 1),
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "node_count": page.locator('[data-testid^="journey-node-"]').count(),
        "initial_transform": map_transform(page),
        "horizontal_overflow": viewport_overflow(page)["horizontalOverflow"],
        "business_attention_visible": attention.is_visible(),
        "primary_cta_visible": primary.is_visible(),
        "page_errors": errors,
    }
    before_desktop = report.get("before", {}).get("captures", {}).get("desktop", {})
    before_map = before_desktop.get("map_box")
    if before_map and map_box:
        record["map_height_delta_px_vs_before"] = round(map_box["height"] - before_map["height"], 2)
        record["map_top_y_delta_px_vs_before"] = round(map_box["y"] - before_map["y"], 2)
    record["attention_text"] = attention.inner_text().strip()
    record["toolbar_text"] = toolbar.inner_text().strip()
    if record["node_count"] != 11:
        raise AssertionError(f"T6-FCL expected 11 Journey nodes, got {record['node_count']}.")
    page.screenshot(path=str(OUT / "desktop-t6-fcl-journey-initial.png"))

    node = page.get_by_test_id("journey-node-on-board")
    node.click(timeout=12000)
    bubble = page.get_by_test_id("journey-bubble")
    bubble.wait_for(state="visible", timeout=10000)
    record["on_board_node_box"] = box(node)
    record["node_bubble_box"] = box(bubble)
    record["node_bubble_within_map"] = bool(
        map_box and box(bubble)
        and box(bubble)["x"] >= map_box["x"] - 1
        and box(bubble)["x"] + box(bubble)["width"] <= map_box["x"] + map_box["width"] + 1
    )
    page.screenshot(path=str(OUT / "desktop-t6-fcl-node-bubble.png"))
    page.get_by_test_id("journey-bubble-task-stage").click(timeout=10000)
    modal = page.get_by_test_id("journey-modal")
    modal.wait_for(state="visible", timeout=10000)
    modal_box = box(modal)
    record["task_modal_box"] = modal_box
    record["task_modal_center_error_px"] = round(
        abs((modal_box["x"] + modal_box["width"] / 2) - 720), 2
    ) if modal_box else None
    page.screenshot(path=str(OUT / "desktop-t6-fcl-task-popup.png"))
    record["page_errors"] = errors
    report["desktop"] = record
    # Keep the page open until the shared single-process Chromium browser is closed.


def install_touch_probe(page: Page) -> None:
    page.evaluate(
        """() => {
          window.__logiTouchEvents = [];
          const collect = event => {
            const path = typeof event.composedPath === 'function' ? event.composedPath() : [];
            const inMap = path.some(node => node instanceof Element && node.getAttribute('data-testid') === 'journey-map-viewport');
            if (!inMap) return;
            window.__logiTouchEvents.push({
              type: event.type,
              pointerType: event.pointerType || null,
              clientX: Number.isFinite(event.clientX) ? event.clientX : null,
              clientY: Number.isFinite(event.clientY) ? event.clientY : null
            });
          };
          ['pointerdown', 'pointermove', 'pointerup', 'pointercancel', 'touchstart', 'touchmove', 'touchend']
            .forEach(type => window.addEventListener(type, collect, true));
        }"""
    )


def dispatch_touch_pan(page: Page) -> dict[str, Any]:
    viewport = box(page.get_by_test_id("journey-map-viewport"))
    if not viewport:
        return {"verdict": "FAILED", "reason": "map viewport missing"}
    page.wait_for_timeout(200)
    before_transform = map_transform(page)
    if before_transform.get("x") is None:
        return {"verdict": "FAILED", "reason": f"unrecognized map transform: {before_transform.get('raw')}"}
    before_node = box(page.get_by_test_id("journey-node-on-board"))
    selected_before = node_selection(page)
    if page.get_by_test_id("journey-bubble").count():
        return {"verdict": "FAILED", "reason": "bubble must be closed before pan"}
    install_touch_probe(page)
    start_x = int(viewport["x"] + max(48, viewport["width"] * 0.14))
    end_x = int(viewport["x"] + viewport["width"] * 0.86)
    y = int(viewport["y"] + viewport["height"] * 0.47)
    session = page.context.new_cdp_session(page)
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": start_x, "y": y, "id": 1, "radiusX": 2, "radiusY": 2, "force": 1}]})
    for step in range(1, 13):
        x = round(start_x + (end_x - start_x) * step / 12)
        session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y, "id": 1, "radiusX": 2, "radiusY": 2, "force": 1}]})
        page.wait_for_timeout(20)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(300)
    events = page.evaluate("window.__logiTouchEvents || []")
    after_transform = map_transform(page)
    if after_transform.get("x") is None:
        return {"verdict": "FAILED", "reason": f"unrecognized map transform after touch: {after_transform.get('raw')}", "events": events}
    after_node = box(page.get_by_test_id("journey-node-on-board"))
    selected_after = node_selection(page)
    bubble_count = page.get_by_test_id("journey-bubble").count()
    pointer_down = [event for event in events if event["type"] == "pointerdown"]
    pointer_moves = [event for event in events if event["type"] == "pointermove"]
    pointer_up = [event for event in events if event["type"] == "pointerup"]
    delta_x = round(float(after_transform["x"]) - float(before_transform["x"]), 2)
    node_delta_x = round(after_node["x"] - before_node["x"], 2) if after_node and before_node else None
    pass_touch = bool(
        pointer_down and pointer_moves and pointer_up
        and all(event["pointerType"] == "touch" for event in pointer_down + pointer_moves + pointer_up)
    )
    pass_direction = delta_x >= 120 and node_delta_x is not None and node_delta_x >= 120
    pass_no_selection = selected_after == selected_before and not selected_after and bubble_count == 0
    verdict = "PASS" if pass_touch and pass_direction and pass_no_selection else "FAILED"
    return {
        "verdict": verdict,
        "input_method": "CDP Input.dispatchTouchEvent; touchStart + 12 touchMove + touchEnd",
        "viewport_box": viewport,
        "start": [start_x, y],
        "end": [end_x, y],
        "observed_event_types": sorted({event["type"] for event in events}),
        "pointer_type_values": sorted({event["pointerType"] for event in pointer_down + pointer_moves + pointer_up}),
        "pointerdown_count": len(pointer_down),
        "pointermove_count": len(pointer_moves),
        "pointerup_count": len(pointer_up),
        "transform_before": before_transform,
        "transform_after": after_transform,
        "transform_delta_x": delta_x,
        "node_box_before": before_node,
        "node_box_after": after_node,
        "node_delta_x": node_delta_x,
        "selected_nodes_before": selected_before,
        "selected_nodes_after": selected_after,
        "bubble_count_after": bubble_count,
        "checks": {
            "touch_pointer_events": pass_touch,
            "map_transform_moved_in_drag_direction": pass_direction,
            "no_accidental_node_selection": pass_no_selection,
        },
    }


def mobile_targets(page: Page) -> dict[str, Any]:
    ids = [
        "journey-global-page", "attention-primary-cta", "journey-global-open", "journey-attach-open",
        "journey-zoom-in", "journey-zoom-out", "journey-zoom-fit", "journey-zoom-readable",
    ]
    targets: dict[str, Any] = {}
    for test_id in ids:
        locator = page.get_by_test_id(test_id)
        if locator.count() and locator.first.is_visible():
            target_box = box(locator.first)
            targets[test_id] = target_box
    primary = {"attention-primary-cta"}
    sizes = {
        test_id: {
            "width": rect["width"],
            "height": rect["height"],
            "target_class": "primary" if test_id in primary else "secondary",
            "minimum_px": 40 if test_id in primary else 36,
            "passes": rect["height"] >= (40 if test_id in primary else 36),
        }
        for test_id, rect in targets.items() if rect
    }
    groups = {
        "toolbar_and_page": [test_id for test_id in ("journey-global-page", "journey-global-open") if test_id in targets],
        "zoom_bar": [test_id for test_id in ("journey-zoom-in", "journey-zoom-out", "journey-zoom-fit", "journey-zoom-readable") if test_id in targets],
    }
    isolation = {}
    for group, members in groups.items():
        isolation[group] = {
            f"{members[i]}__{members[j]}": no_box_overlap(targets[members[i]], targets[members[j]])
            for i in range(len(members)) for j in range(i + 1, len(members))
        }
    return {"boxes": targets, "sizes": sizes, "non_overlap_pairs": isolation,
            "all_target_heights_pass": bool(sizes) and all(item["passes"] for item in sizes.values())}


def capture_mobile(browser: Browser, report: dict[str, Any]) -> None:
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_lot(page)
    map_viewport = page.get_by_test_id("journey-map-viewport")
    map_box = box(map_viewport)
    record: dict[str, Any] = {
        "viewport": [390, 844],
        "map_box": map_box,
        "node_count": page.locator('[data-testid^="journey-node-"]').count(),
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "horizontal_overflow": viewport_overflow(page)["horizontalOverflow"],
        "targets": mobile_targets(page),
        "page_errors": errors,
    }
    if record["node_count"] != 11:
        raise AssertionError(f"T6-FCL expected 11 mobile Journey nodes, got {record['node_count']}.")
    report["mobile_journey"] = record
    page.screenshot(path=str(OUT / "mobile-t6-fcl-journey-initial.png"))

    # Exercise adjacent controls with actual touch taps and make sure each stays in its lane.
    zoom_level = page.get_by_test_id("journey-zoom-level")
    zoom_before = zoom_level.inner_text().strip()
    page.get_by_test_id("journey-zoom-in").tap()
    page.wait_for_timeout(120)
    zoom_after_in = zoom_level.inner_text().strip()
    page.get_by_test_id("journey-zoom-out").tap()
    page.wait_for_timeout(120)
    zoom_after_out = zoom_level.inner_text().strip()
    zoom_isolation = {
        "zoom_in_changed_level": zoom_after_in != zoom_before,
        "zoom_out_restored_level": zoom_after_out == zoom_before,
        "global_workspace_stayed_closed": page.get_by_test_id("journey-global-workspace").count() == 0,
        "no_node_selected": node_selection(page) == [],
        "no_bubble_opened": page.get_by_test_id("journey-bubble").count() == 0,
    }
    zoom_before_global = zoom_level.inner_text().strip()
    page.get_by_test_id("journey-global-open").tap()
    global_workspace = page.get_by_test_id("journey-global-workspace")
    global_workspace.wait_for(state="visible", timeout=10000)
    zoom_after_global_open = zoom_level.inner_text().strip()
    zoom_isolation["global_open_did_not_change_zoom"] = zoom_after_global_open == zoom_before_global
    page.get_by_role("button", name="Đóng Global Workspace").tap()
    global_workspace.wait_for(state="detached", timeout=10000)
    zoom_isolation["global_open_close_isolated"] = (
        page.get_by_test_id("journey-global-workspace").count() == 0
        and node_selection(page) == []
        and page.get_by_test_id("journey-bubble").count() == 0
    )
    page.get_by_test_id("journey-zoom-readable").tap()
    page.wait_for_timeout(150)
    record["adjacent_control_isolation"] = zoom_isolation

    page.get_by_test_id("journey-node-arrival").tap()
    bubble = page.get_by_test_id("journey-bubble")
    bubble.wait_for(state="visible", timeout=10000)
    record["arrival_node_box"] = box(page.get_by_test_id("journey-node-arrival"))
    record["arrival_bubble_box"] = box(bubble)
    bubble_close_box = box(page.get_by_test_id("journey-bubble-close"))
    record["bubble_close_target_box"] = bubble_close_box
    record["bubble_close_target_height_at_least_36"] = bool(bubble_close_box and bubble_close_box["height"] >= 36)
    record["bubble_task_target_box"] = box(page.get_by_test_id("journey-bubble-task-stage"))
    record["bubble_task_primary_height_at_least_40"] = bool(record["bubble_task_target_box"] and record["bubble_task_target_box"]["height"] >= 40)
    page.screenshot(path=str(OUT / "mobile-02-node-bubble.png"))
    page.get_by_test_id("journey-bubble-close").tap()
    bubble.wait_for(state="detached", timeout=10000)
    record["bubble_close_isolated"] = node_selection(page) == [] and page.get_by_test_id("journey-modal").count() == 0
    page.get_by_test_id("journey-node-arrival").tap()
    bubble.wait_for(state="visible", timeout=10000)
    page.get_by_test_id("journey-bubble-task-stage").tap()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    page.screenshot(path=str(OUT / "mobile-03-task-sheet.png"))
    page.get_by_role("button", name="Đóng công đoạn").tap()
    page.get_by_test_id("journey-modal").wait_for(state="detached", timeout=10000)

    # Real CDP touch pan; never substitute a mouse drag for this proof.
    report["touch_pan"] = dispatch_touch_pan(page)
    report["TOUCH_PAN_VERDICT"] = report["touch_pan"]["verdict"]
    page.screenshot(path=str(OUT / "mobile-04-touch-pan-after.png"))

    # Isolated Mongomock write/readback path required by this task; not a payment.
    page.get_by_test_id("journey-node-on-board").tap()
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    page.get_by_test_id("journey-bubble-task-stage").tap()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    date_input = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    date_input.wait_for(state="visible", timeout=10000)
    prior_date_value = date_input.input_value()
    date_input.fill(DATE_VALUE)
    page.screenshot(path=str(OUT / "mobile-04-onboard-touch-editor.png"))
    save_button = page.get_by_test_id("sea-export-facts-save")
    save_button.scroll_into_view_if_needed()
    save_button.tap()
    page.wait_for_timeout(1800)
    backend_status = page.get_by_text("Đã xác nhận từ backend", exact=False)
    backend_confirmation_visible = bool(backend_status.count() and backend_status.first.is_visible())
    save_status_text = save_button.inner_text().strip()
    save_alerts = page.get_by_role("alert").all_inner_texts()
    report["mobile_stage_save"] = {
        "environment": "isolated staging / Mongomock",
        "lot": "T6-FCL",
        "stage": "ON BOARD",
        "date": DATE_VALUE,
        "prior_date_value_before_edit": prior_date_value,
        "save_tapped": True,
        "backend_confirmation_visible": backend_confirmation_visible,
        "save_button_text_after_tap": save_status_text,
        "stage_alerts_after_save": save_alerts,
        "no_payment_flow_used": True,
    }
    open_lot(page)  # reload before independently reading the persisted mock value
    report["readback_touch_pan"] = dispatch_touch_pan(page)
    page.get_by_test_id("journey-node-on-board").tap()
    page.get_by_test_id("journey-bubble").wait_for(state="visible", timeout=10000)
    page.get_by_test_id("journey-bubble-task-stage").tap()
    page.get_by_test_id("journey-modal").wait_for(state="visible", timeout=10000)
    readback = page.get_by_label("Ngày xếp hàng lên tàu (on-board)", exact=True)
    readback.wait_for(state="visible", timeout=10000)
    readback_value = readback.input_value()
    report["mobile_readback"] = {"after_reload": True, "date": readback_value, "expected_date": DATE_VALUE}
    report["TAP_SAVE_READBACK_VERDICT"] = "PASS" if report["mobile_stage_save"]["save_tapped"] and readback_value == DATE_VALUE else "FAILED"
    page.screenshot(path=str(OUT / "mobile-t6-fcl-onboard-touch-readback.png"))
    record["page_errors"] = errors
    record["horizontal_overflow_after_reload"] = viewport_overflow(page)["horizontalOverflow"]
    report["mobile_journey"] = record


def capture_zero_node(
    browser: Browser,
    report: dict[str, Any],
    *,
    label: str,
    width: int,
    height: int,
    mobile: bool,
) -> None:
    """Capture the real canonical SEA-188 zero-node projection at one viewport."""
    page = browser.new_page(
        viewport={"width": width, "height": height},
        is_mobile=mobile,
        has_touch=mobile,
        device_scale_factor=1,
    )
    errors: list[str] = []
    requests: list[dict[str, str]] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    page.on("request", lambda request: requests.append({"method": request.method, "url": request.url}))
    open_shipment(page, ZERO_SHIPMENT_ID)

    shell = page.get_by_test_id("journey-zero-map-first")
    viewport = page.get_by_test_id("journey-map-viewport")
    notice = page.get_by_test_id("journey-empty-map")
    profile = page.get_by_test_id("journey-zero-profile")
    profile_state = page.get_by_test_id("journey-zero-profile-state")
    next_action = page.get_by_test_id("journey-zero-next-action")
    cta = page.get_by_test_id("journey-zero-primary-cta")
    shell_box = box(shell)
    viewport_box = box(viewport)
    notice_box = box(notice)
    node_count = page.locator('[data-testid^="journey-node-"]').count()
    cta_count = page.locator('[data-testid="journey-zero-primary-cta"]').count()
    labelled_cta_count = page.locator("button").evaluate_all(
        "els => els.filter(el => el.textContent.includes('BỔ SUNG HỒ SƠ')).length"
    )
    style = viewport.evaluate(
        """el => {
          const css = getComputedStyle(el);
          return {cursor: css.cursor, touchAction: css.touchAction,
            pointerEvents: css.pointerEvents, backgroundImage: css.backgroundImage};
        }"""
    )
    background_image = str(style.get("backgroundImage") or "")
    transform_before = map_transform(page)
    overflow = viewport_overflow(page)
    route_text = page.get_by_test_id("journey-compact-toolbar").inner_text().strip()

    record: dict[str, Any] = {
        "fixture": ZERO_SHIPMENT_ID,
        "journey_shape": "canonical shipment with journey.nodes=[]",
        "viewport": [width, height],
        "zero_shell_box": shell_box,
        "map_viewport_box": viewport_box,
        "map_width_matches_zero_shell": bool(
            shell_box and viewport_box and abs(shell_box["width"] - viewport_box["width"]) <= 1
        ),
        "notice_box": notice_box,
        "computed_style": {
            "cursor": style["cursor"],
            "touchAction": style["touchAction"],
            "pointerEvents": style["pointerEvents"],
            "approved_vietnam_chart_data_image_loaded": "data:image/webp" in background_image,
        },
        "transform_before_pointer": transform_before,
        "node_count": node_count,
        "edge_count": page.locator('[data-testid="journey-map-transform"] svg path').count(),
        "empty_state_text": notice.inner_text().strip(),
        "profile_state_label": profile_state.inner_text().strip(),
        "profile_status_visible": profile.is_visible(),
        "server_projected_primary_action": next_action.inner_text().strip(),
        "toolbar_text": route_text,
        "unknown_phase_stays_unconfirmed": "Đang ở: Chưa xác định" in route_text,
        "cta_count": cta_count,
        "labelled_cta_count": labelled_cta_count,
        "cta_text": cta.inner_text().strip(),
        "horizontal_overflow": overflow["horizontalOverflow"],
        "document_dimensions": overflow,
        "page_errors": errors,
    }
    report[f"zero_node_{label}"] = record
    if node_count != 0:
        raise AssertionError(f"{ZERO_SHIPMENT_ID} expected zero Journey nodes, got {node_count}.")
    if cta_count != 1 or labelled_cta_count != 1 or not record["cta_text"].startswith("BỔ SUNG HỒ SƠ"):
        raise AssertionError(f"{ZERO_SHIPMENT_ID} must render exactly one truthful BỔ SUNG HỒ SƠ CTA.")
    if not record["profile_status_visible"] or not record["profile_state_label"] or not record["server_projected_primary_action"]:
        raise AssertionError("Fresh-shipment profile status/primary action is missing from the zero state.")
    if "Chưa có sơ đồ Journey" not in record["empty_state_text"] or node_count != 0:
        raise AssertionError("Zero-state must be truthful and must not fabricate Journey nodes.")
    if not record["map_width_matches_zero_shell"]:
        raise AssertionError("Zero-node Journey map viewport must fill its map-first shell.")
    if record["computed_style"]["cursor"] != "default" or record["computed_style"]["touchAction"] != "auto":
        raise AssertionError(f"Empty chart viewport is still gesture-styled: {record['computed_style']!r}.")
    if not record["computed_style"]["approved_vietnam_chart_data_image_loaded"]:
        raise AssertionError("Owner-selected Vietnam chart data-image is not rendered on the zero-node map.")
    if not record["unknown_phase_stays_unconfirmed"]:
        raise AssertionError("Zero-node toolbar must keep the current Journey phase unconfirmed.")

    page.screenshot(path=str(OUT / f"{label}-zero-node-initial.png"))

    # Exercise real pointer events on a blank chart corner, away from the status card.
    page.evaluate(
        """() => {
          window.__logiZeroPointerEvents = [];
          const collect = event => {
            const inMap = event.composedPath().some(node =>
              node instanceof Element && node.getAttribute('data-testid') === 'journey-map-viewport');
            if (inMap) window.__logiZeroPointerEvents.push({type: event.type, pointerType: event.pointerType || null});
          };
          ['pointerdown', 'pointermove', 'pointerup', 'pointercancel'].forEach(type =>
            window.addEventListener(type, collect, true));
        }"""
    )
    if not viewport_box:
        raise AssertionError("Zero-node map viewport has no rendered box.")
    start_x = int(viewport_box["x"] + 12)
    start_y = int(viewport_box["y"] + 12)
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(start_x + 80, start_y + 48, steps=6)
    page.mouse.up()
    page.wait_for_timeout(180)
    pointer_events = page.evaluate("window.__logiZeroPointerEvents || []")
    transform_after = map_transform(page)
    pointer_types = sorted({event["pointerType"] for event in pointer_events if event["pointerType"]})
    pointer_no_pan = bool(
        any(event["type"] == "pointerdown" for event in pointer_events)
        and any(event["type"] == "pointermove" for event in pointer_events)
        and any(event["type"] == "pointerup" for event in pointer_events)
        and transform_after["raw"] == transform_before["raw"]
    )
    record["pointer_test"] = {
        "input": "Playwright mouse drag dispatching browser pointer events over decorative empty chart",
        "pointer_types": pointer_types,
        "observed_event_types": sorted({event["type"] for event in pointer_events}),
        "transform_after_pointer": transform_after,
        "transform_unchanged": transform_after["raw"] == transform_before["raw"],
        "no_pan_verdict": "PASS" if pointer_no_pan else "FAILED",
    }
    report[f"zero_node_{label}"] = record
    if not pointer_no_pan:
        raise AssertionError(f"Pointer-down changed empty Journey map state: {record['pointer_test']!r}.")

    request_start = len(requests)
    if mobile:
        cta.tap()
    else:
        cta.click()
    workspace = page.get_by_test_id("journey-global-workspace")
    editor = page.get_by_test_id("shipment-execution-profile")
    workspace.wait_for(state="visible", timeout=15000)
    editor.wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(300)
    cta_requests = requests[request_start:]
    non_read_http = [request for request in cta_requests if request["method"] not in ("GET", "HEAD", "OPTIONS")]
    editor_in_workspace = workspace.locator('[data-testid="shipment-execution-profile"]').count() == 1
    record["cta_editor_test"] = {
        "opens_existing_execution_profile_editor": editor.is_visible() and editor_in_workspace,
        "workspace_visible": workspace.is_visible(),
        "url_after_cta": page.evaluate("location.pathname + location.search + location.hash"),
        "non_read_http_requests_during_cta": non_read_http,
        "no_non_read_http_request": not non_read_http,
        "no_business_write_proof": "DOM acceptance asserts zero non-navigation write triggers for this CTA",
    }
    report[f"zero_node_{label}"] = record
    if not record["cta_editor_test"]["opens_existing_execution_profile_editor"]:
        raise AssertionError("Zero-node CTA did not open the existing Execution Profile editor.")
    if non_read_http:
        raise AssertionError(f"Zero-node CTA caused a non-read HTTP request: {non_read_http!r}.")
    page.screenshot(path=str(OUT / f"{label}-zero-node-execution-profile-editor.png"))
    record["page_errors"] = errors
    report[f"zero_node_{label}"] = record


def capture_receivables(browser: Browser, report: dict[str, Any]) -> None:
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=1)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)[:240]))
    open_receivables(page)
    page.get_by_role("button", name="THU TIỀN", exact=True).first.tap()
    sheet = page.get_by_test_id("receivable-pay-sheet")
    sheet.wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(200)
    save = page.get_by_test_id("receivable-pay-submit")
    cancel = page.get_by_test_id("receivable-pay-cancel")
    save_text = save.inner_text().strip()
    save_lines = save.evaluate(
        """el => {
          const doc = el.ownerDocument;
          const walker = doc.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          const lineYs = [];
          while (walker.nextNode()) {
            if (!walker.currentNode.textContent.trim()) continue;
            const range = doc.createRange();
            range.selectNodeContents(walker.currentNode);
            for (const rect of range.getClientRects()) {
              if (rect.width > 0 && rect.height > 0 && !lineYs.some(y => Math.abs(y - rect.y) < 1)) lineYs.push(rect.y);
            }
          }
          return lineYs.length;
        }"""
    )
    record: dict[str, Any] = {
        "viewport": [390, 844],
        "sheet_box": box(sheet),
        "save_box": box(save),
        "cancel_box": box(cancel),
        "save_text": save_text,
        "save_text_line_boxes": save_lines,
        "emoji_present": any(0x1F300 <= ord(char) <= 0x1FAFF for char in save_text),
        "save_one_line": save_lines == 1,
        "save_target_height_at_least_40": bool(box(save) and box(save)["height"] >= 40),
        "cancel_target_height_at_least_36": bool(box(cancel) and box(cancel)["height"] >= 36),
        "page_errors": errors,
    }
    before_rec = report.get("before", {}).get("captures", {}).get("mobile_receivables_before", {})
    before_save_box = before_rec.get("save_box")
    if before_save_box and record["save_box"]:
        record["save_height_delta_px_vs_before"] = round(record["save_box"]["height"] - before_save_box["height"], 2)
    record["save_text_lines_before"] = before_rec.get("save_line_box_count")
    record["save_text_lines_after"] = save_lines
    page.screenshot(path=str(OUT / "mobile-receivables-pay-sheet.png"))

    # Deliberately leave amount empty: exercise validation, not a transaction.
    save.tap()
    page.get_by_text("Chưa nhập số tiền", exact=True).wait_for(state="visible", timeout=10000)
    pending = page.get_by_test_id("receivable-pay-pending")
    record["empty_amount_validation"] = {
        "validation_visible": page.get_by_text("Chưa nhập số tiền", exact=True).is_visible(),
        "sheet_stayed_open": sheet.is_visible(),
        "pay_pending_visible": pending.count() > 0 and pending.is_visible(),
        "amount_left_blank": page.get_by_placeholder("VD: 150000000", exact=True).input_value().strip() == "",
    }
    page.screenshot(path=str(OUT / "mobile-receivables-validation.png"))
    cancel.tap()
    sheet.wait_for(state="detached", timeout=10000)
    record["cancel_closed_sheet"] = sheet.count() == 0
    record["page_errors"] = errors
    report["mobile_receivables"] = record


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "goal": "LOGI-APP-RENEWAL-01 / LOGI-199 G2 zero-node and current-browser replay",
        "owner_reference": "reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html",
        "owner_reference_sha256": "26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f",
        "source_sha": source_sha(),
        "capture_script_sha256": sha256(Path(__file__).resolve()),
        "dist_sha256": {
            "logi-shell.js": sha256(ROOT / "component/dist/logi-shell.js"),
            "logi-shell.css": sha256(ROOT / "component/dist/logi-shell.css"),
        },
        "staging_url": URL,
        "capture_output_directory": str(OUT.relative_to(ROOT)),
        "runtime": {"available": False},
        "touch_pan": {"verdict": "NOT_VERIFIED", "reason": "runtime not yet started"},
        "TOUCH_PAN_VERDICT": "NOT_VERIFIED",
        "TAP_SAVE_READBACK_VERDICT": "NOT_RUN",
        "zero_node_desktop": {"verdict": "NOT_RUN"},
        "zero_node_mobile": {"verdict": "NOT_RUN"},
        "CAPTURE_VERDICT": "NOT_RUN",
    }
    if BEFORE.is_file():
        report["before"] = json.loads(BEFORE.read_text(encoding="utf-8"))
    runtime_available = False
    try:
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "/tmp/al2023/lib:/tmp" + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=CHROMIUM, args=CHROMIUM_ARGS, env=env)
            runtime_available = True
            report["runtime"] = {"available": True, "browser": browser.version, "chromium_executable": CHROMIUM}
            try:
                capture_desktop(browser, report)
                capture_mobile(browser, report)
                capture_zero_node(browser, report, label="desktop", width=1440, height=900, mobile=False)
                capture_zero_node(browser, report, label="mobile", width=390, height=844, mobile=True)
            finally:
                browser.close()
    except Exception as error:
        report["runtime_error"] = f"{type(error).__name__}: {error}"
        if report["TOUCH_PAN_VERDICT"] == "NOT_VERIFIED":
            report["TOUCH_PAN_VERDICT"] = "FAILED" if runtime_available else "NOT_VERIFIED"
            report["touch_pan"]["reason"] = "capture failed before touch evidence" if runtime_available else "no usable browser runtime"
        if report["TAP_SAVE_READBACK_VERDICT"] == "NOT_RUN":
            report["TAP_SAVE_READBACK_VERDICT"] = "FAILED" if runtime_available else "NOT_VERIFIED"
        for key in ("zero_node_desktop", "zero_node_mobile"):
            if report.get(key, {}).get("verdict") == "NOT_RUN":
                report[key]["verdict"] = "FAILED" if runtime_available else "NOT_VERIFIED"
    checks = {
        "desktop_populated_11_nodes": report.get("desktop", {}).get("node_count") == 11,
        "mobile_populated_11_nodes": report.get("mobile_journey", {}).get("node_count") == 11,
        "mobile_touch_pan": report.get("TOUCH_PAN_VERDICT") == "PASS",
        "mobile_save_reload_readback": report.get("TAP_SAVE_READBACK_VERDICT") == "PASS",
    }
    for label in ("desktop", "mobile"):
        zero = report.get(f"zero_node_{label}", {})
        checks[f"{label}_zero_node_empty_map"] = (
            zero.get("node_count") == 0
            and zero.get("computed_style", {}).get("cursor") == "default"
            and zero.get("computed_style", {}).get("touchAction") == "auto"
            and zero.get("pointer_test", {}).get("no_pan_verdict") == "PASS"
            and zero.get("cta_editor_test", {}).get("opens_existing_execution_profile_editor") is True
            and zero.get("cta_editor_test", {}).get("no_non_read_http_request") is True
        )
    report["acceptance_checks"] = checks
    report["CAPTURE_VERDICT"] = "PASS" if checks and all(checks.values()) and not report.get("runtime_error") else "FAILED"
    for label in ("desktop", "mobile"):
        if f"zero_node_{label}" in report and "verdict" not in report[f"zero_node_{label}"]:
            report[f"zero_node_{label}"]["verdict"] = "PASS" if checks.get(f"{label}_zero_node_empty_map") else "FAILED"
    (OUT / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["CAPTURE_VERDICT"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
