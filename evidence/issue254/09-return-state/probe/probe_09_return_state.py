"""LOGI-255-RETURN-STATE-PRESERVATION-20261102 — real-Chromium acceptance probe.

Exact HEAD under test: cb1870f95358be3b9e8c6278ac898fc1c9fa2cba (PR #255 head).

Question: does the /lo-hang filter set survive
  list -> open lot via the "Công nợ dịch vụ" cluster (tab=tai-chinh)
  -> SWITCH TAB inside the detail (a real setSp(...) navigation)
  -> click "Về danh sách lô" ?

Tests:
  A  filters -> cluster -> return immediately (no tab switch) -> filters+rows kept
  B  filters (q+status+period khac+from/to+archive) -> cluster -> verify tai-chinh
     -> switch tab inside the Global Workspace (setSp) -> verify the switch happened
     -> "Về danh sách lô" -> ALL params and visible row IDs identical
  C  direct entry (Home card, no list state) -> return control is the plain-list
     fallback and lands on a safe /lo-hang
  D  1440x900 and 390x844: back control visible, no horizontal overflow
  E  NATIVE browser Back from the detail (reported SEPARATELY, never substitutes B)

Router-state evidence: the shell is a MemoryRouter, so the browser URL never
changes; the remembered list location is observable verbatim on the detail's
"Về danh sách lô" control as href/data-return-to (it is listReturnFromState(
location.state)), captured BEFORE and AFTER the tab switch.

Usage: python probe_09_return_state.py --base http://127.0.0.1:9531/ --out results/run.json --tag fail-before|pass-after
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("S255_EVIDENCE_DIR", HERE.parent)).resolve()
SHOTS = OUT / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)
HOST = 'div[data-testid="stBidiComponentIsolated"]'
SUPPORT = "qa.s255.support"
BACK_ID = '[data-testid="shipment-back-to-list"]'
PW = os.environ["S255_TEST_PASSWORD"]


# ------------------------------------------------------------------ helpers
def ev(page, body, arg=None):
    js = ("(arg) => { const root = document.querySelector('%s')?.shadowRoot; %s }" % (HOST, body))
    return page.evaluate(js, arg)


def wait_shell(page, timeout=240):
    page.wait_for_selector(HOST, timeout=timeout * 1000)
    end = time.time() + timeout
    while time.time() < end:
        if ev(page, """return !!root?.querySelector('a[href="/lo-hang"]')"""):
            return True
        time.sleep(0.3)
    return False


def login(page, base, user=SUPPORT):
    page.goto(base, wait_until="load", timeout=120000)
    page.wait_for_selector('input[aria-label="Tài khoản"]', timeout=120000)
    page.fill('input[aria-label="Tài khoản"]', user)
    page.fill('input[type="password"]', PW)
    page.click('button[kind="primaryFormSubmit"]')
    wait_shell(page)
    time.sleep(1.0)


def click(page, selector, text=None):
    return bool(ev(page, """
        const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
          return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
        const els = [...root.querySelectorAll(arg.sel)].filter(vis);
        const el = arg.txt ? els.find(e => e.textContent.replace(/\\s+/g,' ').includes(arg.txt)) : els[0];
        if (!el) return false;
        el.scrollIntoView({ block: 'center', inline: 'nearest' });
        el.click();
        return true;
    """, {"sel": selector, "txt": text}))


def goto_list(page):
    if ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')"""):
        click(page, 'a[aria-label="Về trang chủ"]')
        time.sleep(1.0)
    for _ in range(40):
        if click(page, 'aside a[href="/lo-hang"]') or click(page, 'a[href="/lo-hang"]', "Lô Hàng"):
            break
        time.sleep(0.4)
    time.sleep(1.2)
    return page


def type_q(page, value):
    loc = page.locator('div[data-testid="stBidiComponentIsolated"] input[placeholder*="Nhập mã lô"]').first
    loc.fill(value)
    end = time.time() + 8
    got = None
    while time.time() < end:
        got = ev(page, """const i = root.querySelector('input[placeholder*="Nhập mã lô"]'); return i ? i.value : null;""")
        if got == value:
            break
        time.sleep(0.25)
    if got != value:
        raise RuntimeError(f"q input did not take the value: wanted {value!r}, got {got!r}")
    time.sleep(0.8)


def set_date(page, testid, value):
    """Set a date input and RETRY until React has actually taken the value."""
    for _ in range(6):
        got = ev(page, """
            const el = root.querySelector('[data-testid="' + arg.t + '"]');
            if (!el) return null;
            if (el.value !== arg.v) {
              Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(el, arg.v);
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return el.value;
        """, {"t": testid, "v": value})
        if got == value:
            return got
        time.sleep(0.5)
    return got


def click_status(page, label):
    """Click a status chip in the filter panel and verify it became active."""
    for _ in range(4):
        clicked = ev(page, """
            const panel = [...root.querySelectorAll('div')].find(d => (d.className||'').includes('no-scrollbar'));
            if (!panel) return false;
            const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
            const b = [...panel.querySelectorAll('button')].filter(vis)
                .find(e => e.textContent.replace(/\\s+/g,' ').trim() === arg.label);
            if (!b) return false;
            b.scrollIntoView({ block: 'center' });
            b.click();
            return true;
        """, {"label": label})
        time.sleep(0.9)
        active = ev(page, """
            const panel = [...root.querySelectorAll('div')].find(d => (d.className||'').includes('no-scrollbar'));
            if (!panel) return null;
            const b = [...panel.querySelectorAll('button')].find(e => /bg-\\[#0f2a4a\\]/.test(e.className||''));
            return b ? b.textContent.replace(/\\s+/g,' ').trim() : null;
        """)
        if clicked and active == label:
            return True
    return False


def filter_state(page):
    return ev(page, """
        const q = root.querySelector('input[placeholder*="Nhập mã lô"]')?.value ?? null;
        const pressed = (sel) => { const b = root.querySelector(sel); return b ? b.getAttribute('aria-pressed') : null; };
        const chips = [...root.querySelectorAll('[data-testid="shipment-period-controls"] button')]
            .filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim());
        const arch = [...root.querySelectorAll('[data-testid="shipment-archive-controls"] button')]
            .filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim());
        const panel = [...root.querySelectorAll('div')].find(d => (d.className||'').includes('no-scrollbar'));
        const statusChip = panel
            ? [...panel.querySelectorAll('button')].filter(b => /bg-\\[#0f2a4a\\]/.test(b.className||'')).map(b => b.textContent.trim())
            : [];
        const rows = [...root.querySelectorAll('[data-testid="shipment-row"]')].map(r => r.getAttribute('data-shipment-id'));
        const cards = [...root.querySelectorAll('[data-testid="shipment-mobile-card"]')].map(r => r.getAttribute('data-shipment-id'));
        return {
          q, periodPressed: chips, archivePressed: arch, statusChips: statusChip,
          from: root.querySelector('[data-testid="shipment-date-from"]')?.value ?? null,
          to: root.querySelector('[data-testid="shipment-date-to"]')?.value ?? null,
          rows, cards,
          summary: root.querySelector('[data-testid="shipment-list-summary"]')?.innerText.replace(/\\s+/g,' ').trim() || '',
        };
    """)


def back_control(page):
    return ev(page, """
        const a = root.querySelector('[data-testid="shipment-back-to-list"]');
        if (!a) return {present: false};
        const r = a.getBoundingClientRect();
        const cs = getComputedStyle(a);
        return {present: true, tag: a.tagName, href: a.getAttribute('href'),
                dataReturnTo: a.getAttribute('data-return-to'),
                text: a.textContent.replace(/\\s+/g,' ').trim(),
                aria: a.getAttribute('aria-label'),
                rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                visible: r.width > 0 && r.height > 0};
    """)


def router_state(page):
    """MemoryRouter state as observed from the rendered tree + browser URL."""
    return {
        "browserUrl": page.url,
        "historyLength": page.evaluate("history.length"),
        "backControl": back_control(page),
        "globalWorkspaceOpen": ev(page, """return !!root?.querySelector('[data-testid="journey-global-workspace"]')"""),
        "pressedTab": ev(page, """
            const ws = root?.querySelector('[data-testid="journey-global-workspace"]');
            if (!ws) return null;
            const b = [...ws.querySelectorAll('button')].find(b => b.getAttribute('aria-pressed') === 'true');
            return b ? b.textContent.trim() : null;
        """),
        "detailOpen": ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')"""),
    }


def open_cluster(page, sid):
    ok = ev(page, """
        const a = root.querySelector('[data-testid="shipment-row"][data-shipment-id="' + arg.id + '"] [data-testid="shipment-finance-summary"]')
               || root.querySelector('[data-testid="shipment-mobile-card"][data-shipment-id="' + arg.id + '"] [data-testid="shipment-finance-summary"]');
        if (!a) return false;
        a.scrollIntoView({ block: 'center' });
        a.click();
        return true;
    """, {"id": sid})
    time.sleep(2.2)
    return ok and ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')""")


def switch_tab(page, label):
    """Click a tab button INSIDE the Global Workspace -> ShipmentDetail's
    onGlobal -> setSp({ tab }) — a real setSearchParams navigation."""
    ok = ev(page, """
        const ws = root.querySelector('[data-testid="journey-global-workspace"]');
        if (!ws) return false;
        const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
          return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
        const b = [...ws.querySelectorAll('button')].filter(vis)
            .find(e => e.textContent.replace(/\\s+/g,' ').trim() === arg.label);
        if (!b) return false;
        b.scrollIntoView({ block: 'center' });
        b.click();
        return true;
    """, {"label": label})
    time.sleep(1.2)
    pressed = ev(page, """
        const ws = root?.querySelector('[data-testid="journey-global-workspace"]');
        if (!ws) return null;
        const b = [...ws.querySelectorAll('button')].find(b => b.getAttribute('aria-pressed') === 'true');
        return b ? b.textContent.trim() : null;
    """)
    return ok, pressed


def overflow(page):
    """Page-level horizontal overflow: does the DOCUMENT actually scroll
    sideways? (Elements inside overflow-x-auto containers legitimately extend
    their own rect but do not scroll the page.)"""
    return ev(page, """
        const doc = document.documentElement;
        const back = root.querySelector('[data-testid="shipment-back-to-list"]');
        const r = back ? back.getBoundingClientRect() : null;
        return {
          viewport: window.innerWidth,
          docScrollWidth: doc.scrollWidth,
          bodyScrollWidth: document.body.scrollWidth,
          pageOverflows: doc.scrollWidth > window.innerWidth + 1 || document.body.scrollWidth > window.innerWidth + 1,
          backControlRect: r ? {right: Math.round(r.right), bottom: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height)} : null,
          backControlInsideViewport: r ? (r.right <= window.innerWidth + 1 && r.left >= -1 && r.width > 0 && r.height > 0) : false,
        };
    """)


def shot(page, name):
    page.screenshot(path=str(SHOTS / name))


def apply_full_filter(page, q="LO-03", status="Chờ thông quan"):
    goto_list(page)
    # open the status filter panel (retry until the panel really exists)
    for _ in range(6):
        ev(page, """
            const b = [...root.querySelectorAll('button')].find(b => b.textContent.replace(/\\s+/g,' ').trim() === 'Lọc');
            if (b) { b.click(); return true; } return false;
        """)
        time.sleep(0.7)
        if ev(page, """return [...root.querySelectorAll('div')].some(d => (d.className||'').includes('no-scrollbar') && d.querySelector('button'));"""):
            break
    status_ok = click_status(page, status)
    click(page, '[data-testid="shipment-period-khac"]')
    time.sleep(0.7)
    from_ok = set_date(page, "shipment-date-from", "2020-01-01")
    to_ok = set_date(page, "shipment-date-to", "2030-12-31")
    time.sleep(0.5)
    click(page, '[data-testid="shipment-archive-tat-ca"]')
    time.sleep(1.0)
    type_q(page, q)
    st = filter_state(page)
    st["_statusApplied"] = status_ok
    st["_fromApplied"] = (from_ok == "2020-01-01")
    st["_toApplied"] = (to_ok == "2030-12-31")
    return st


# ------------------------------------------------------------------ tests
def test_a(page, out, tag):
    """A: filter -> cluster -> return immediately (NO tab switch)."""
    before = apply_full_filter(page)
    shot(page, f"09-A-1-list-filtered-{tag}.png")
    opened = open_cluster(page, before["rows"][-1] if before["rows"] else "LO-0308")
    rs = router_state(page)
    shot(page, f"09-A-2-detail-tai-chinh-{tag}.png")
    clicked = click(page, BACK_ID)
    time.sleep(1.8)
    after = filter_state(page)
    same_params = all(before[k] == after[k] for k in ("q", "periodPressed", "archivePressed", "statusChips", "from", "to"))
    same_rows = before["rows"] == after["rows"] and bool(after["rows"])
    out["A"] = {
        "tag": tag, "filter_before": before, "detailOpened": opened,
        "routerStateOnDetail": rs, "backClicked": clicked, "filter_after": after,
        "sameParams": same_params, "sameRows": same_rows,
        "verdict": "PASS" if (opened and same_params and same_rows) else "FAIL",
    }
    shot(page, f"09-A-3-after-return-{tag}.png")
    return out["A"]["verdict"]


def test_b(page, out, tag):
    """B: full filter -> cluster (tai-chinh) -> SWITCH TAB (real setSp) -> return."""
    before = apply_full_filter(page)
    shot(page, f"09-B-1-list-filtered-{tag}.png")
    target = "LO-0308" if "LO-0308" in before["rows"] else before["rows"][0]
    opened = open_cluster(page, target)
    rs_before_tab = router_state(page)
    shot(page, f"09-B-2-detail-tai-chinh-{tag}.png")

    # verify we are really on tab tai-chinh
    tai_chinh_pressed = rs_before_tab.get("pressedTab")

    # the discriminating step: a REAL setSp(...) navigation inside the detail
    switched, pressed_after = switch_tab(page, "Lịch sử")
    rs_after_tab = router_state(page)
    shot(page, f"09-B-3-detail-after-tab-switch-{tag}.png")

    clicked = click(page, BACK_ID)
    time.sleep(1.8)
    after = filter_state(page)
    shot(page, f"09-B-4-after-return-{tag}.png")

    same_params = all(before[k] == after[k] for k in ("q", "periodPressed", "archivePressed", "statusChips", "from", "to"))
    same_rows = before["rows"] == after["rows"] and bool(after["rows"])
    state_kept_after_tab_switch = (
        rs_after_tab["backControl"].get("present")
        and rs_after_tab["backControl"].get("dataReturnTo") == rs_before_tab["backControl"].get("dataReturnTo")
        and rs_after_tab["backControl"].get("dataReturnTo", "").startswith("/lo-hang?")
    )
    out["B"] = {
        "tag": tag, "openedLot": target, "detailOpened": opened,
        "pressedTabOnOpen": tai_chinh_pressed,
        "tabSwitchClicked": switched, "pressedTabAfterSwitch": pressed_after,
        "routerStateBeforeTabSwitch": rs_before_tab,
        "routerStateAfterTabSwitch": rs_after_tab,
        "stateKeptAfterTabSwitch": state_kept_after_tab_switch,
        "backClicked": clicked, "filter_before": before, "filter_after": after,
        "sameParams": same_params, "sameRows": same_rows,
        "verdict": "PASS" if (opened and switched and pressed_after == "Lịch sử"
                              and state_kept_after_tab_switch and same_params and same_rows
                              and before.get("_statusApplied") and before.get("_fromApplied") and before.get("_toApplied")) else "FAIL",
    }
    return out["B"]["verdict"]


def test_c(page, base, out, tag):
    """C: direct entry (no list state) -> plain-list fallback, safe landing."""
    page.goto(base, wait_until="load", timeout=120000)
    time.sleep(2.0)
    if page.locator('input[aria-label="Tài khoản"]').count() > 0:
        login(page, base)
    goto_list(page)
    fresh = filter_state(page)  # reference: default filters of a fresh /lo-hang
    click(page, 'aside a[href="/"]')
    time.sleep(1.5)
    clicked = ev(page, """
        const btn = [...root.querySelectorAll('button')].find(b => /^Mở LO-/.test(b.textContent.trim()));
        if (!btn) return null;
        btn.scrollIntoView({ block: 'center' });
        btn.click();
        return btn.textContent.trim();
    """)
    time.sleep(2.2)
    opened = ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')""")
    ctl = back_control(page)
    rs = router_state(page)
    ok = click(page, BACK_ID)
    time.sleep(1.8)
    landed = filter_state(page)
    shot(page, f"09-C-1-after-direct-return-{tag}.png")
    out["C"] = {
        "tag": tag, "homeButton": clicked, "detailOpened": opened, "backControl": ctl,
        "routerState": rs, "backClicked": ok,
        "fallbackIsPlainList": ctl.get("dataReturnTo") == "/lo-hang",
        "landedOnList": bool(landed and landed.get("summary")),
        "landedFilters": landed,
        "verdict": "PASS" if (opened and ctl.get("dataReturnTo") == "/lo-hang" and ok and landed and landed.get("summary")) else "FAIL",
    }
    return out["C"]["verdict"]


def test_d(browser, base, out, tag):
    """D: back control visible + no horizontal overflow at 1440x900 and 390x844."""
    res = {}
    for name, w, h in (("desktop", 1440, 900), ("mobile", 390, 844)):
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        login(page, base)
        goto_list(page)
        if name == "mobile":
            click(page, 'button[aria-label="Mở menu"]')
            time.sleep(0.5)
            click(page, 'a[href="/lo-hang"]', "Lô Hàng")
            time.sleep(1.2)
        before = apply_full_filter(page)
        target = "LO-0308" if "LO-0308" in before["rows"] else before["rows"][0]
        opened = open_cluster(page, target)
        ctl = back_control(page)
        ov = overflow(page)
        shot(page, f"09-D-{name}-detail-{tag}.png")
        res[name] = {
            "viewport": [w, h], "detailOpened": opened, "backControl": ctl,
            "overflow": ov,
            "verdict": "PASS" if (opened and ctl.get("present") and ctl.get("visible")
                                  and not ov["pageOverflows"] and ov["backControlInsideViewport"]) else "FAIL",
        }
        ctx.close()
    out["D"] = {"tag": tag, "desktop": res["desktop"], "mobile": res["mobile"],
                "verdict": "PASS" if all(res[n]["verdict"] == "PASS" for n in res) else "FAIL"}
    return out["D"]["verdict"]


def test_e(page, out, tag):
    """E: NATIVE browser Back from the detail — reported separately (MemoryRouter
    means it cannot restore the in-app route); never substitutes for B."""
    goto_list(page)
    click(page, '[data-testid="shipment-period-tat-ca"]')
    time.sleep(0.8)
    type_q(page, "LO-03")
    url_before = page.url
    hist_before = page.evaluate("history.length")
    opened = open_cluster(page, "LO-0308")
    url_detail = page.url
    hist_detail = page.evaluate("history.length")
    page.go_back(wait_until="load", timeout=60000)
    time.sleep(2.5)
    shell = ev(page, "return !!document.querySelector('%s')?.shadowRoot" % HOST)
    after = filter_state(page) if shell else None
    out["E"] = {
        "tag": tag, "detailOpened": opened,
        "urlBefore": url_before, "urlOnDetail": url_detail, "urlAfterNativeBack": page.url,
        "historyBefore": hist_before, "historyOnDetail": hist_detail,
        "shellPresentAfterBack": bool(shell), "blankPage": page.url == "about:blank",
        "filterAfterNativeBack": after,
        "verdict": "PASS" if (shell and after and after.get("q") == "LO-03") else "FAIL (native back; MemoryRouter — reported separately)",
    }
    shot(page, f"09-E-native-back-{tag}.png")
    return out["E"]["verdict"]


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:9531/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    out = {"tag": args.tag, "base": args.base, "head": os.environ.get("PROBE_HEAD", "cb1870f")}
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = "/home/user/.pw-tools/al2023/lib"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/home/user/.pw-tools/chromium-bin/chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
            env=env,
        )
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        login(page, args.base)
        only = args.only.split(",") if args.only else ["A", "B", "C", "D", "E"]
        if "A" in only:
            test_a(page, out, args.tag)
        if "B" in only:
            test_b(page, out, args.tag)
        if "C" in only:
            test_c(page, args.base, out, args.tag)
        if "E" in only:
            test_e(page, out, args.tag)
        if "D" in only:
            test_d(browser, args.base, out, args.tag)
        browser.close()

    out["FINAL"] = {
        "A": out.get("A", {}).get("verdict"),
        "B": out.get("B", {}).get("verdict"),
        "C": out.get("C", {}).get("verdict"),
        "D": out.get("D", {}).get("verdict"),
        "E_native_back_separate": out.get("E", {}).get("verdict"),
    }
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(out["FINAL"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
