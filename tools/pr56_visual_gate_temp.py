#!/usr/bin/env python3
from __future__ import annotations

import json, os, re, sys, time
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:9501"
OUT=Path("/tmp/pr56-visual")
OUT.mkdir(parents=True, exist_ok=True)
CANDIDATE=os.environ["CANDIDATE_SHA"]

results={}
material_failures=[]
minor_notes=[]
page_errors=[]
console_errors=[]
bad_responses=[]

def rec(key, ok, detail=""):
    ok=bool(ok)
    results[key]={"ok":ok,"detail":str(detail)}
    print(f"{'PASS' if ok else 'FAIL'} {key}: {detail}", flush=True)
    if not ok:
        material_failures.append(f"{key}: {detail}")

def note(key, detail):
    results[key]={"ok":None,"detail":str(detail)}
    print(f"NOTE {key}: {detail}", flush=True)

def root_text(page):
    return page.evaluate("""() => {
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      const r=h&&h.shadowRoot?h.shadowRoot:document;
      const s=r.querySelector('.logi-shell');
      return (s?s.textContent:document.body.textContent)||'';
    }""")

def shadow_eval(page, expr):
    return page.evaluate(f"""() => {{
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      const root=h&&h.shadowRoot?h.shadowRoot:document;
      return ({expr});
    }}""")

def wait_shell(page):
    page.goto(BASE, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function("""() => {
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      return !!(h&&h.shadowRoot&&h.shadowRoot.querySelector('.logi-shell'));
    }""", timeout=60000)
    page.wait_for_timeout(1000)

def shot(page,name,full=False):
    page.screenshot(path=str(OUT/name), full_page=full)

def overflow(page):
    return shadow_eval(page, """(() => {
      const s=root.querySelector('.logi-shell');
      return {shell:s?Math.max(0,s.scrollWidth-s.clientWidth):null,
              page:Math.max(0,document.documentElement.scrollWidth-window.innerWidth)};
    })()""")

def active_in_dialog(page, label_fragment):
    return shadow_eval(page, f"""(() => {{
      const d=[...root.querySelectorAll('[role="dialog"]')].find(x=>(x.textContent||'').includes({json.dumps(label_fragment)}));
      const a=root.activeElement;
      return !!(d&&a&&d.contains(a));
    }})()""")

def active_summary(page):
    return page.evaluate("""() => {
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      const root=h&&h.shadowRoot?h.shadowRoot:document;
      const a=root.activeElement;
      const d=document.activeElement;
      return {
        shadow: a ? {tag:a.tagName, text:(a.textContent||'').trim().slice(0,80),
                     placeholder:a.getAttribute('placeholder'), testid:a.getAttribute('data-testid')} : null,
        document: d ? {tag:d.tagName, testid:d.getAttribute?.('data-testid')||null} : null
      };
    }""")

def click_sidebar(page, label):
    page.get_by_text(label, exact=True).first.click()
    page.wait_for_timeout(500)

def make_contact_sheet():
    imgs=[]
    for p in sorted(OUT.glob("*.png")):
        try:
            im=Image.open(p).convert("RGB")
            im.thumbnail((650,430))
            canvas=Image.new("RGB",(680,470),"white")
            canvas.paste(im,((680-im.width)//2,30))
            d=ImageDraw.Draw(canvas)
            d.text((8,8),p.name,fill="black")
            imgs.append(canvas)
        except Exception:
            pass
    if not imgs:
        return
    cols=2
    rows=(len(imgs)+cols-1)//cols
    sheet=Image.new("RGB",(cols*680,rows*470),(238,240,243))
    for i,im in enumerate(imgs):
        sheet.paste(im,((i%cols)*680,(i//cols)*470))
    sheet.save(OUT/"contact-sheet.jpg",quality=88)

with sync_playwright() as p:
    browser=p.chromium.launch(
        headless=True,
        executable_path=os.environ["CHROME_PATH"],
        args=["--no-sandbox","--disable-dev-shm-usage"],
    )
    ctx=browser.new_context(viewport={"width":1440,"height":900})
    page=ctx.new_page()
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("console", lambda m: console_errors.append(m.text) if m.type=="error" else None)
    page.on("response", lambda r: bad_responses.append(f"{r.status} {r.url}") if r.status>=400 else None)

    # HOME — exact rendered candidate
    wait_shell(page)
    txt=root_text(page)
    rec("identity_render", "TRƯỜNG THÀNH" in txt and "Preview / Staging" in txt,
        f"candidate {CANDIDATE} rendered with sandbox label")
    rec("home_priority", ("Ưu tiên bây giờ:" in txt or "Không có việc khẩn" in txt) and "Ảnh vận hành hôm nay" in txt,
        "single priority area + operational snapshot")
    rec("home_old_duplicate_removed", "VIỆC TIẾP THEO" not in txt and "Chỉ số vận hành hôm nay" not in txt,
        "old duplicate sections absent")
    ov=overflow(page)
    rec("desktop_no_page_overflow", (ov["page"] or 0)<=2, ov)
    rec("sandbox_role_preview", "XEM TRƯỚC" in txt.upper(), "preview-only role label visible")
    shot(page,"01-home-desktop.png")

    # SHIPMENTS list context — q + real status filter -> detail -> back
    click_sidebar(page,"Lô Hàng")
    q=page.locator('.logi-shell input[placeholder^="Nhập mã lô"]').first
    q.fill("LO-03")
    page.get_by_role("button", name="Lọc", exact=True).first.click()
    page.wait_for_timeout(150)
    status_btn=page.get_by_role("button", name="Chờ thông quan", exact=True).first
    if status_btn.count():
        status_btn.click()
    page.wait_for_timeout(350)
    rec("shipments_filter_applied", q.input_value()=="LO-03" and "Chờ thông quan" in root_text(page),
        "search + status filter visibly active")
    shot(page,"02-shipments-context-desktop.png")
    page.locator(".logi-shell table.tbl").get_by_text("LO-0306", exact=True).first.click()
    page.wait_for_timeout(650)
    rec("shipment_detail_open", "LO-0306" in root_text(page), "LO-0306 opened")
    shot(page,"03-shipment-detail-desktop.png")
    page.get_by_role("button", name="Quay lại", exact=True).first.click()
    page.wait_for_function("""() => {
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      const r=h&&h.shadowRoot?h.shadowRoot:document;
      const i=r.querySelector('input[placeholder^="Nhập mã lô"]');
      return !!i;
    }""", timeout=10000)
    restored=shadow_eval(page, """(() => {
      const i=root.querySelector('input[placeholder^="Nhập mã lô"]');
      const b=[...root.querySelectorAll('button')].find(x=>(x.textContent||'').trim()==='Chờ thông quan');
      return {q:i?.value||'', statusClass:b?.className||'', statusVisible:!!b};
    })()""")
    rec("shipments_context_restored", restored["q"]=="LO-03" and restored["statusVisible"] and "bg-[#0f2a4a]" in restored["statusClass"],
        restored)
    shot(page,"04-shipments-context-restored.png")

    # GLOBAL SEARCH — customer destination has the intended entity already visible
    click_sidebar(page,"Tổng Quan Công Việc")
    g=page.locator('.logi-shell input[placeholder^="Tìm mã lô"]').first
    g.click(); g.fill("An Phát"); page.wait_for_timeout(450)
    customer_result=page.locator('button', has_text="Khách hàng").filter(has_text=re.compile("An Phát",re.I)).first
    if customer_result.count():
        customer_result.click(); page.wait_for_timeout(500)
        cust_state=shadow_eval(page, """(() => {
          const i=root.querySelector('input[placeholder^="Nhập mã (CUST"]');
          return {q:i?.value||'', text:(root.querySelector('.logi-shell')?.textContent||'')};
        })()""")
        rec("global_customer_context", "An Phát" in cust_state["q"] and "An Phát" in cust_state["text"],
            f"destination q={cust_state['q']}")
        shot(page,"05-global-customer.png")
    else:
        rec("global_customer_context", False, "customer search result not found")

    # GLOBAL SEARCH — discover actual rendered quote id, then land with it filtered
    click_sidebar(page,"Kinh doanh · Báo giá")
    page.wait_for_timeout(400)
    quote_id=shadow_eval(page, """(() => {
      const row=root.querySelector('table.tbl tbody tr');
      const first=row?.querySelector('td span');
      return (first?.textContent||'').trim();
    })()""")
    if quote_id:
        click_sidebar(page,"Tổng Quan Công Việc")
        g=page.locator('.logi-shell input[placeholder^="Tìm mã lô"]').first
        g.click(); g.fill(quote_id); page.wait_for_timeout(450)
        quote_result=page.locator('button', has_text="Báo giá").filter(has_text=quote_id).first
        if quote_result.count():
            quote_result.click(); page.wait_for_timeout(500)
            quote_state=shadow_eval(page, """(() => {
              const i=root.querySelector('input[placeholder^="Nhập mã (Q-"], input[placeholder^="Nhập mã (BG-"]');
              return {q:i?.value||'', text:(root.querySelector('.logi-shell')?.textContent||'')};
            })()""")
            rec("global_quote_context", quote_id in quote_state["q"] and quote_id in quote_state["text"],
                f"quote={quote_id}, destination q={quote_state['q']}")
            shot(page,"06-global-quote.png")
        else:
            rec("global_quote_context", False, f"global quote suggestion absent for {quote_id}")
    else:
        rec("global_quote_context", False, "could not discover rendered quote id")

    # SHIPMENT DETAIL continuity + partner finance
    click_sidebar(page,"Lô Hàng")
    page.locator('.logi-shell input[placeholder^="Nhập mã lô"]').first.fill("LO-0306")
    page.wait_for_timeout(250)
    page.get_by_text("LO-0306", exact=True).first.click(); page.wait_for_timeout(600)
    dtext=root_text(page)
    rec("shipment_detail_continuity",
        all(x in dtext for x in ["LO-0306","Tài chính cần theo dõi","Sửa thông tin lô","Vận chuyển & Hàng hóa","Tài chính / Công nợ"]),
        "header → next action → tabs → maintenance disclosure all visible")
    page.get_by_role("button", name=re.compile("Sửa thông tin lô")).first.click(); page.wait_for_timeout(200)
    rec("shipment_edit_disclosure", "Tên lô" in root_text(page) and "Ngày tạo" in root_text(page),
        "maintenance controls remain available on demand")
    page.get_by_role("button", name="Tài chính / Công nợ", exact=True).first.click(); page.wait_for_timeout(350)
    fin=root_text(page)
    rec("partner_finance_labels",
        all(x in fin for x in ["Phải trả đối tác (VND)","Phải trả","Đã trả","Còn phải trả"]),
        "partner payable/paid/remaining are visually distinct")
    rec("partner_unknown_not_zero", "— tr VND" in fin and "không tự thành 0" in fin,
        "UNKNOWN is shown as dash, not zero")
    shot(page,"07-finance-partner-desktop.png")

    # PAYMENT dialog — semantics, actual Shadow-DOM focus, tab trap
    pay_open=page.get_by_role("button", name=re.compile("GHI NHẬN THANH TOÁN")).first
    pay_open.click(); page.wait_for_timeout(220)
    dlg=page.locator('[role="dialog"]').filter(has_text="Ghi nhận thanh toán").first
    rec("payment_dialog_semantics", dlg.count()==1 and dlg.get_attribute("aria-modal")=="true",
        "role=dialog + aria-modal")
    focus=active_summary(page)
    rec("payment_focus_inside", active_in_dialog(page,"Ghi nhận thanh toán"), focus)
    # Tab and Shift+Tab should remain in dialog. Record the exact focus
    # sequence so a failure is evidence, not a black-box boolean.
    tab_ok=True
    tab_trace=[]
    for _ in range(8):
        page.keyboard.press("Tab")
        inside=active_in_dialog(page,"Ghi nhận thanh toán")
        tab_trace.append({"key":"Tab","inside":inside,"active":active_summary(page)})
        if not inside:
            tab_ok=False
            break
    if tab_ok:
        for _ in range(4):
            page.keyboard.press("Shift+Tab")
            inside=active_in_dialog(page,"Ghi nhận thanh toán")
            tab_trace.append({"key":"Shift+Tab","inside":inside,"active":active_summary(page)})
            if not inside:
                tab_ok=False
                break
    rec("payment_tab_trap", tab_ok, tab_trace)
    shot(page,"08-payment-sheet-open.png")

    # Install a same-mutation pending/Escape probe. It fires synchronously when
    # the pending marker enters the real DOM, before a fast backend response can
    # close the sheet and confuse the measurement.
    page.evaluate("""() => {
      const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
      const root=h.shadowRoot;
      window.__pr56EscapeProbe={seen:false, afterEscape:null, pendingText:''};
      const obs=new MutationObserver(() => {
        const p=root.querySelector('[data-testid="payment-record-pending"]');
        if(p && !window.__pr56EscapeProbe.seen){
          window.__pr56EscapeProbe.seen=true;
          window.__pr56EscapeProbe.pendingText=p.textContent||'';
          const a=root.activeElement || p;
          a.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,composed:true,cancelable:true}));
          window.__pr56EscapeProbe.afterEscape=!!root.querySelector('[role="dialog"]');
          obs.disconnect();
        }
      });
      obs.observe(root,{subtree:true,childList:true,characterData:true,attributes:true});
    }""")

    # Light CDP latency gives us a chance to capture the real pending frame.
    cdp=ctx.new_cdp_session(page)
    try:
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions",{
            "offline":False,"latency":1200,
            "downloadThroughput":250000,"uploadThroughput":250000,
            "connectionType":"cellular3g"
        })
    except Exception as e:
        minor_notes.append(f"network throttle unavailable: {e}")

    amount=dlg.locator('input[placeholder^="VD: 150000000"]').first
    amount.fill("1000000")
    dlg.locator('[data-testid="payment-record-submit"]').first.click()
    try:
        page.wait_for_function("() => window.__pr56EscapeProbe && window.__pr56EscapeProbe.seen", timeout=5000)
        probe=page.evaluate("() => window.__pr56EscapeProbe")
        rec("payment_pending_truthful", "ĐANG CHỜ BACKEND XÁC NHẬN" in probe["pendingText"], probe)
        rec("payment_pending_escape_guard", probe["afterEscape"] is True,
            "Escape dispatched at the exact pending DOM mutation and dialog remained")
        # capture pending if it is still live under throttling
        if page.locator('[data-testid="payment-record-pending"]').count():
            shot(page,"09-payment-pending.png")
        else:
            note("payment_pending_screenshot","pending frame settled before screenshot; synchronous DOM probe still captured it")
    except Exception as e:
        rec("payment_pending_truthful", False, f"pending marker not observed: {e}")

    try:
        cdp.send("Network.emulateNetworkConditions",{
            "offline":False,"latency":0,
            "downloadThroughput":-1,"uploadThroughput":-1,
            "connectionType":"none"
        })
    except Exception:
        pass

    try:
        page.wait_for_function("""() => {
          const h=document.querySelector('[data-testid="stBidiComponentIsolated"]');
          const r=h&&h.shadowRoot?h.shadowRoot:document;
          return ((r.querySelector('.logi-shell')||document.body).textContent||'').includes('Đã ghi nhận khoản thu');
        }""", timeout=15000)
        rec("payment_authoritative_success", True, "real sandbox write settled after authoritative readback")
    except Exception as e:
        rec("payment_authoritative_success", False, f"no success/readback within 15s: {e}")
    shot(page,"10-payment-after-outcome.png")

    # RECEIVABLES — clean context so prior global-search state cannot
    # contaminate this dialog/accessibility verification.
    c5=browser.new_context(viewport={"width":1440,"height":900})
    p5=c5.new_page(); wait_shell(p5)
    p5.get_by_text("Thu tiền", exact=True).first.click(); p5.wait_for_timeout(450)
    rtext=root_text(p5)
    rec("receivables_page", "Thu tiền khách · Phải thu" in rtext and "LO-0306" in rtext,
        "receivables desk rendered in clean context")
    row=p5.locator(".logi-shell table.tbl tbody tr", has_text="LO-0306").first
    if row.count() and row.get_by_role("button", name="Thu tiền", exact=True).count():
        opener=row.get_by_role("button", name="Thu tiền", exact=True).first
        opener.click(); p5.wait_for_timeout(180)
        rdlg=p5.locator('[role="dialog"]').filter(has_text="Ghi nhận khoản thu").first
        rec("receivables_payment_dialog", rdlg.count()==1 and active_in_dialog(p5,"Ghi nhận khoản thu"),
            "second payment entry uses accessible sheet and focuses inside")
        shot(p5,"11-receivables-payment.png")
        p5.keyboard.press("Escape"); p5.wait_for_timeout(180)
        closed=p5.locator('[role="dialog"]').filter(has_text="Ghi nhận khoản thu").count()==0
        focus_return=shadow_eval(p5, """(() => {
          const a=root.activeElement;
          return !!(a && (a.textContent||'').includes('Thu tiền'));
        })()""")
        rec("dialog_idle_escape_and_focus_return", closed and focus_return,
            f"closed={closed}, focus_return={focus_return}")
    else:
        rec("receivables_payment_dialog", False, "LO-0306 Thu tiền action not found")
    c5.close()

    # QUICK ADD — clean context, representative non-financial dialog.
    c6=browser.new_context(viewport={"width":1440,"height":900})
    p6=c6.new_page(); wait_shell(p6)
    p6.get_by_role("button", name="Thêm", exact=True).first.click(); p6.wait_for_timeout(180)
    qdlg=p6.locator('[role="dialog"]').filter(has_text="Thêm mới nhanh").first
    rec("quick_add_dialog", qdlg.count()==1 and active_in_dialog(p6,"Thêm mới nhanh"),
        "quick-add real dialog + focus")
    p6.keyboard.press("Escape"); p6.wait_for_timeout(150)
    rec("quick_add_escape", p6.locator('[role="dialog"]').filter(has_text="Thêm mới nhanh").count()==0,
        "idle Escape closes")
    c6.close()

    # MOBILE — actual 390x844 rendering
    page.set_viewport_size({"width":390,"height":844})
    wait_shell(page)
    mtxt=root_text(page)
    mov=overflow(page)
    rec("mobile_home", ("Ưu tiên bây giờ:" in mtxt or "Không có việc khẩn" in mtxt) and "Ảnh vận hành hôm nay" in mtxt,
        "Home renders at 390x844")
    rec("mobile_home_no_overflow", (mov["page"] or 0)<=2 and (mov["shell"] or 0)<=2, mov)
    rec("mobile_bottom_nav", all(x in mtxt for x in ["Tổng quan","Lô hàng","Hợp đồng","Tài chính"]),
        "mobile bottom navigation present")
    shot(page,"12-home-mobile.png")

    page.get_by_text("Lô hàng", exact=True).last.click(); page.wait_for_timeout(450)
    mlist=root_text(page)
    rec("mobile_shipments", "LO-0306" in mlist and "XỬ LÝ" in mlist and "360°" in mlist,
        "mobile shipment cards preserve action distinction")
    shot(page,"13-shipments-mobile.png")
    if page.get_by_text("LO-0306", exact=True).count():
        mobile_lo=None
        for candidate in page.get_by_text("LO-0306", exact=True).all():
            if candidate.is_visible():
                mobile_lo=candidate
                break
        if mobile_lo is None:
            rec("mobile_detail", False, "LO-0306 exists only in hidden desktop markup")
        else:
            mobile_lo.click(); page.wait_for_timeout(500)
            rec("mobile_detail", "LO-0306" in root_text(page) and "Sửa thông tin lô" in root_text(page),
                "shipment detail usable on mobile")
            shot(page,"14-detail-mobile.png")
            if page.get_by_role("button", name="Tài chính / Công nợ", exact=True).count():
                page.get_by_role("button", name="Tài chính / Công nợ", exact=True).first.click(); page.wait_for_timeout(320)
                if page.get_by_role("button", name=re.compile("GHI NHẬN THANH TOÁN")).count():
                    page.get_by_role("button", name=re.compile("GHI NHẬN THANH TOÁN")).first.click(); page.wait_for_timeout(180)
                    box=page.locator('[role="dialog"]').first.bounding_box()
                    fits=bool(box and box["x"]>=-1 and box["x"]+box["width"]<=391 and box["y"]>=-1 and box["y"]<844)
                    rec("mobile_payment_sheet", fits, box)
                    shot(page,"15-payment-mobile.png")
                    page.keyboard.press("Escape"); page.wait_for_timeout(100)
    else:
        rec("mobile_detail", False, "LO-0306 not visible")

    # Console/network scope: ignore favicon-only noise, flag app/runtime failures.
    rec("no_uncaught_page_errors", len(page_errors)==0, page_errors)
    material_console=[x for x in console_errors if "favicon" not in x.lower()]
    if material_console:
        minor_notes.append("console errors: "+str(material_console[:10]))
    essential=[]
    for x in bad_responses:
        if "favicon" in x.lower():
            continue
        if "404" in x and "_stcore" in x:
            continue
        essential.append(x)
    rec("no_material_network_errors", len(essential)==0, essential[:20])
    browser.close()

make_contact_sheet()

summary={
  "candidate_sha":CANDIDATE,
  "desktop_viewport":"1440x900",
  "mobile_viewport":"390x844",
  "results":results,
  "page_errors":page_errors,
  "console_errors":console_errors,
  "bad_responses":bad_responses,
  "material_failures":material_failures,
  "minor_notes":minor_notes,
  "overall":"PASS" if not material_failures else "FAIL",
}
(OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print("VISUAL_GATE_SUMMARY="+json.dumps(summary,ensure_ascii=False), flush=True)
sys.exit(0 if not material_failures else 1)
