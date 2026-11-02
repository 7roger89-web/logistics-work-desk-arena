"""LOGI-255-RETURN-TO-LIST — acceptance probe (real Chromium, both before and after the fix).

Independent of the PR's own harness. Each run uses its own browser context so
history is clean; Chromium `go_back()` (test C/F) is measured SEPARATELY from the
in-app control (tests A/B/D/E) because they are different behaviours.

Tests:
  A  q filter -> open debt cluster -> in-app return -> q kept
  B  status + period(khác, from/to) + archive -> open -> in-app return -> same params AND same row set
  C  native browser Back from the detail screen (independent result)
  D  entry from another entrypoint (Tổng quan) -> in-app return lands on /lo-hang, never a blank page
  E  control present + readable + no horizontal overflow at 1440x900 and 390x844

Usage: python probe_return_nav.py --base http://127.0.0.1:PORT/ --out file.json --tag baseline|after
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("/home/user/review-255-evidence")
PW = (ROOT / ".pw").read_text().strip()
HOST = 'div[data-testid="stBidiComponentIsolated"]'
SUPPORT = "qa.r255.support"
BACK_ID = '[data-testid="shipment-back-to-list"]'


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
    """Set q deterministically and wait until React has actually taken it.

    Keystroke typing dropped characters while Streamlit re-rendered ("LO-0"
    arrived as "L-0"), and the native value-setter was reverted by the controlled
    input. Playwright `fill` (shadow-DOM piercing) plus a poll on the live value
    is deterministic.
    """
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
    return ev(page, """
        const el = root.querySelector('[data-testid="' + arg.t + '"]');
        if (!el) return false;
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(el, arg.v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return el.value;
    """, {"t": testid, "v": value})


def filter_state(page):
    return ev(page, """
        const q = root.querySelector('input[placeholder*="Nhập mã lô"]')?.value ?? null;
        const pressed = (sel) => { const b = root.querySelector(sel); return b ? b.getAttribute('aria-pressed') : null; };
        const chips = [...root.querySelectorAll('[data-testid="shipment-period-controls"] button')]
            .filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim());
        const arch = [...root.querySelectorAll('[data-testid="shipment-archive-controls"] button')]
            .filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim());
        const statusChip = [...root.querySelectorAll('button')]
            .filter(b => /bg-\\[#0f2a4a\\]/.test(b.className||'') && !b.closest('[data-testid="shipment-period-controls"]')
                    && !b.closest('[data-testid="shipment-archive-controls"]') && b.textContent.trim().length <= 22)
            .map(b => b.textContent.trim()).slice(0, 3);
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


def open_cluster(page, sid="LO-0308"):
    ok = ev(page, """
        const a = root.querySelector('[data-testid="shipment-row"][data-shipment-id="' + arg.id + '"] [data-testid="shipment-finance-summary"]')
               || root.querySelector('[data-testid="shipment-mobile-card"][data-shipment-id="' + arg.id + '"] [data-testid="shipment-finance-summary"]');
        if (!a) return false;
        a.scrollIntoView({ block: 'center' });
        a.click();
        return true;
    """, {"id": sid})
    time.sleep(2.0)
    return ok and ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')""")


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
                fontSize: parseFloat(cs.fontSize), visible: r.width > 0 && r.height > 0};
    """)


def fallback_return(page):
    """Today's operator path when the screen has no in-app return control."""
    if ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')"""):
        click(page, 'a[aria-label="Về trang chủ"]')
        time.sleep(1.2)
    for _ in range(30):
        if click(page, 'aside a[href="/lo-hang"]') or click(page, 'a[href="/lo-hang"]', "Lô Hàng"):
            break
        time.sleep(0.4)
    time.sleep(1.8)
    return True


def click_back(page):
    ok = click(page, BACK_ID)
    time.sleep(1.6)
    return ok


def shot(page, path):
    page.screenshot(path=str(path))


def focus_control(page):
    """Scroll the return control into the middle of the viewport so a screenshot
    actually shows it (the detail screen opens scrolled to the finance card)."""
    return ev(page, """
        const el = root.querySelector('[data-testid="shipment-back-to-list"]');
        if (!el) return false;
        el.scrollIntoView({ block: 'center' });
        return true;
    """)


# ------------------------------------------------------------------ tests
def test_a(page, out, tag):
    goto_list(page)
    click(page, '[data-testid="shipment-period-tat-ca"]')
    time.sleep(0.8)
    click(page, '[data-testid="shipment-archive-tat-ca"]')
    time.sleep(0.8)
    type_q(page, "LO-0")
    before = filter_state(page)
    shot(page, ROOT / "shots" / f"nav-A-1-list-filtered-{tag}.png")
    opened = open_cluster(page)
    focus_control(page)
    shot(page, ROOT / "shots" / f"nav-A-2-detail-control-{tag}.png")
    ctl = back_control(page)
    used = "in_app_button" if ctl.get("present") else "sidebar_fallback"
    returned = click_back(page) if ctl.get("present") else fallback_return(page)
    time.sleep(1.0)
    after = filter_state(page)
    out["A"] = {
        "tag": tag, "filter_before": before, "detailOpened": opened,
        "backControl": ctl, "returnPathUsed": used, "returnClicked": bool(returned),
        "filter_after": after,
        "qPreserved": before["q"] == after["q"] and after["q"] == "LO-0",
        "rowsPreserved": before["rows"] == after["rows"],
        "verdict": "PASS" if (ctl.get("present") and before["q"] == after["q"] == "LO-0"
                              and before["rows"] == after["rows"] and after["rows"]) else "FAIL",
    }
    shot(page, ROOT / "shots" / f"nav-A-3-after-return-{tag}.png")
    return out["A"]["verdict"]


def test_b(page, out, tag):
    goto_list(page)
    # status filter
    click(page, "button", "Lọc")
    time.sleep(0.5)
    status_ok = click(page, "button", "Chờ thông quan")
    time.sleep(0.9)
    # period = khác + explicit wide date range, archive = tất cả
    click(page, '[data-testid="shipment-period-khac"]')
    time.sleep(0.7)
    set_date(page, "shipment-date-from", "2020-01-01")
    set_date(page, "shipment-date-to", "2030-12-31")
    time.sleep(0.8)
    click(page, '[data-testid="shipment-archive-tat-ca"]')
    time.sleep(1.0)
    before = filter_state(page)
    shot(page, ROOT / "shots" / f"nav-B-1-list-combined-{tag}.png")
    opened = open_cluster(page)
    focus_control(page)
    shot(page, ROOT / "shots" / f"nav-B-2-detail-control-{tag}.png")
    ctl = back_control(page)
    returned = click_back(page) if ctl.get("present") else fallback_return(page)
    time.sleep(1.0)
    after = filter_state(page)
    same_rows = before["rows"] == after["rows"] and bool(after["rows"])
    same_params = ({k: before[k] for k in ("q", "periodPressed", "archivePressed", "from", "to")}
                   == {k: after[k] for k in ("q", "periodPressed", "archivePressed", "from", "to")})
    out["B"] = {"tag": tag, "statusApplied": status_ok, "filter_before": before, "detailOpened": opened,
                "backControl": ctl, "filter_after": after, "sameParams": same_params,
                "sameRows": same_rows, "returnPathUsed": "in_app_button" if ctl.get("present") else "sidebar_fallback",
                "verdict": "PASS" if (ctl.get("present") and same_params and same_rows) else "FAIL"}
    shot(page, ROOT / "shots" / f"nav-B-3-after-return-{tag}.png")
    return out["B"]["verdict"]


def test_c(page, out, tag):
    goto_list(page)
    click(page, '[data-testid="shipment-period-tat-ca"]')
    time.sleep(0.8)
    type_q(page, "LO-0")
    hist_before = page.evaluate("history.length")
    url_before = page.url
    opened = open_cluster(page)
    hist_detail = page.evaluate("history.length")
    url_detail = page.url
    page.go_back(wait_until="load", timeout=60000)
    time.sleep(2.2)
    shell = ev(page, "return !!document.querySelector('%s')?.shadowRoot" % HOST)
    after = filter_state(page) if shell else None
    out["C"] = {"tag": tag, "detailOpened": opened,
                "history_before": hist_before, "history_on_detail": hist_detail,
                "url_before": url_before, "url_on_detail": url_detail,
                "url_after_back": page.url, "shellPresent": shell,
                "blankPage": page.url == "about:blank",
                "filter_after": after,
                "qPreserved": bool(after and after["q"] == "LO-0"),
                "verdict": "PASS" if (shell and after and after["q"] == "LO-0") else "FAIL"}
    shot(page, ROOT / "shots" / f"nav-C-native-back-{tag}.png")
    return out["C"]["verdict"]


def test_d(page, out, tag):
    # D = "another entrypoint, no list history": the control must land on a
    # usable /lo-hang, never a blank page and never stale filters.
    page.goto(page.url, wait_until="load", timeout=120000)
    time.sleep(2.0)
    if page.locator('input[aria-label="Tài khoản"]').count() > 0:
        login(page, page.url)

    # Reference: what a FRESH /lo-hang looks like with default filters in this
    # seed. The fallback target must reproduce exactly that, not something worse.
    goto_list(page)
    fresh = filter_state(page)
    fresh_href = page.url

    click(page, 'aside a[href="/"]')
    time.sleep(1.5)
    clicked = ev(page, """
        const btn = [...root.querySelectorAll('button')].find(b => /^Mở LO-/.test(b.textContent.trim()));
        if (!btn) return null;
        const label = btn.textContent.trim();
        btn.scrollIntoView({ block: 'center' });
        btn.click();
        return label;
    """)
    time.sleep(2.0)
    opened = ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')""")
    ctl = back_control(page)
    if ctl.get("present"):
        click_back(page)
    else:
        fallback_return(page)
    time.sleep(1.2)
    after = filter_state(page)
    list_visible = ev(page, """return !!root?.querySelector('[data-testid="shipment-list-summary"]')""")
    same_as_fresh = (
        after["q"] == fresh["q"]
        and after["periodPressed"] == fresh["periodPressed"]
        and after["archivePressed"] == fresh["archivePressed"]
        and after["rows"] == fresh["rows"]
    )
    ok = bool(ctl.get("present")) and ctl.get("href") == "/lo-hang" and list_visible and page.url != "about:blank" and same_as_fresh
    out["D"] = {"tag": tag, "entryButton": clicked, "detailOpened": opened, "backControl": ctl,
                "listVisibleAfterReturn": list_visible, "filter_after": after,
                "freshListReference": fresh, "freshListUrl": fresh_href,
                "sameAsFreshList": same_as_fresh,
                "landedOnBlank": page.url == "about:blank",
                "verdict": "PASS" if ok else "FAIL"}
    shot(page, ROOT / "shots" / f"nav-D-other-entry-{tag}.png")
    return out["D"]["verdict"]


def test_e(page, out, tag):
    results = {}
    for name, w, h in (("desktop", 1440, 900), ("mobile", 390, 844)):
        page.set_viewport_size({"width": w, "height": h})
        time.sleep(1.0)
        goto_list(page)
        click(page, '[data-testid="shipment-period-tat-ca"]')
        time.sleep(0.8)
        if name == "mobile":
            # The drawer link re-mounts the list with its DEFAULT filters
            # ("Tháng này"), which is empty in this seed, so the period choice
            # made above is lost and there would be no card to click. Re-apply
            # the wide period after the drawer navigation, then open a card.
            click(page, 'button[aria-label="Mở menu"]')
            time.sleep(0.6)
            click(page, 'a[href="/lo-hang"]', "Lô Hàng")
            time.sleep(1.8)
        ok = False
        for attempt in range(3):
            click(page, '[data-testid="shipment-period-tat-ca"]')
            time.sleep(1.2)
            for _ in range(12):
                ok = bool(ev(page, """
                    const card = root.querySelector('[data-testid="shipment-mobile-card"] [data-testid="shipment-finance-summary"]');
                    const row  = root.querySelector('[data-testid="shipment-row"] [data-testid="shipment-finance-summary"]');
                    const a = card || row;
                    if (!a) return false;
                    a.scrollIntoView({ block: 'center' });
                    a.click();
                    return true;
                """))
                if ok:
                    break
                time.sleep(0.5)
            for _ in range(20):
                if ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')"""):
                    break
                time.sleep(0.25)
            if ev(page, """return !!root?.querySelector('[data-testid="shipment-identity-bar"]')"""):
                break
        time.sleep(0.5)
        ctl = back_control(page)
        metrics = ev(page, """
            const rootEl = root.firstElementChild;
            return {docOverflowPx: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                    rootOverflowPx: rootEl ? rootEl.scrollWidth - rootEl.clientWidth : 0,
                    viewport: window.innerWidth};
        """)
        focus_control(page)
        rect_in_view = ev(page, """
            const el = root.querySelector('[data-testid="shipment-back-to-list"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                    inViewport: r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight && r.right <= window.innerWidth};
        """)
        results[name] = {"viewport": f"{w}x{h}", "opened": ok, "backControl": ctl,
                         "controlRectInViewport": rect_in_view, **metrics}
        shot(page, ROOT / "shots" / f"nav-E-{name}-{tag}.png")
    ok = all(r["backControl"].get("present") and r["backControl"].get("visible")
             and r["backControl"]["rect"]["w"] > 0 and r["backControl"]["rect"]["h"] >= 40
             and r["docOverflowPx"] <= 0 and r["rootOverflowPx"] <= 0
             and r["backControl"]["rect"]["x"] >= 0
             and r["backControl"]["rect"]["x"] + r["backControl"]["rect"]["w"] <= r["viewport"]
             for r in results.values())
    out["E"] = {**results, "verdict": "PASS" if ok else "FAIL"}
    return out["E"]["verdict"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--only", default="ABCDE", help="subset of A,B,C,D,E")
    args = ap.parse_args()

    only = {c for c in args.only.upper() if c in "ABCDE"}
    out = {"baseUrl": args.base, "tag": args.tag, "tests": {}}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/tmp/chromium",
                              args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                                    "--disable-gpu", "--hide-scrollbars", "--no-zygote", "--single-process"])
        out["browser"] = {"version": b.version, "executable": "/tmp/chromium"}
        for name, fn in (("A", test_a), ("B", test_b), ("D", test_d), ("E", test_e)):
            if name not in only:
                continue
            ctx = b.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            try:
                print(f"[test {name}] start", flush=True)
                login(page, args.base)
                fn(page, out["tests"], args.tag)
                print(f"[test {name}] {out['tests'].get(name, {}).get('verdict')}", flush=True)
            except Exception as exc:  # noqa: BLE001 - record, never fake a pass
                out["tests"][name] = {"verdict": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
            finally:
                ctx.close()
        # C uses its own context: history must start clean
        ctx = b.new_context(viewport={"width": 1440, "height": 900}) if "C" in only else None
        if ctx is None:
            b.close()
            out["summary"] = {k: v.get("verdict") for k, v in out["tests"].items()}
            Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(out["summary"], ensure_ascii=False), flush=True)
            return 0
        page = ctx.new_page()
        try:
            login(page, args.base)
            test_c(page, out["tests"], args.tag)
        except Exception as exc:  # noqa: BLE001
            out["tests"]["C"] = {"verdict": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
        finally:
            ctx.close()
        b.close()

    out["summary"] = {k: v.get("verdict") for k, v in out["tests"].items()}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    print(json.dumps(out.get("A", {}), ensure_ascii=False)[:900] if "A" in out else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
