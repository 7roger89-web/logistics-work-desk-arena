"""Real Chromium checks against isolated Streamlit component-v2 runtime."""
from __future__ import annotations
import base64,hashlib,io,json,os
from pathlib import Path
from pypdf import PdfWriter
from playwright.sync_api import sync_playwright

OUT=Path("test-results/graphify-journey-browser")
OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get("BROWSER_URL","http://127.0.0.1:9501")
PNG=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")
pdf=PdfWriter();pdf.add_blank_page(width=400,height=400)
buf=io.BytesIO();pdf.write(buf);PDF=buf.getvalue()
done=[]
def check(what,ok,detail=""):
    done.append({"name":what,"ok":bool(ok),"detail":str(detail)})
    if not ok: raise AssertionError(f"{what} — {detail}")
    print("PASS",what,detail,flush=True)
def tid(page,name): return page.get_by_test_id(name)
def open_node(page):
    tid(page,"btn-open-journey-QA-LOT").wait_for(timeout=45000)
    tid(page,"btn-open-journey-QA-LOT").click()
    tid(page,"journey-node-pickup").wait_for(timeout=25000)
    tid(page,"journey-node-pickup").click()
    tid(page,"journey-discussion").wait_for(timeout=25000)
    check("discussion inside node bubble",tid(page,"journey-bubble").count()==1)
    page.get_by_text("Bình luận gốc từ Trường Thành").wait_for(timeout=25000)
def upload(page,message,name,mime,data):
    tid(page,"journey-discussion-body").fill(message)
    tid(page,"journey-discussion-file").set_input_files(
        {"name":name,"mimeType":mime,"buffer":data})
    page.get_by_text(f"Đã chọn: {name}").wait_for(timeout=20000)
    tid(page,"journey-discussion-send").click()
    page.get_by_text(message,exact=True).wait_for(timeout=30000)
    check("saved comment+file "+name,True,len(data))
def download(page,name,expected):
    locator=page.get_by_text(name,exact=True)
    locator.wait_for(timeout=15000)
    with page.expect_download(timeout=30000) as event:
        locator.locator("xpath=..").get_by_role("button",name="Tải").click()
    actual=Path(event.value.path()).read_bytes()
    check("file roundtrip "+name,actual==expected,hashlib.sha256(actual).hexdigest()[:16])
def scenario(browser,mobile=False):
    name="mobile" if mobile else "desktop"
    ctx=browser.new_context(
        viewport={"width":390,"height":844} if mobile else {"width":1280,"height":900},
        is_mobile=mobile,has_touch=mobile,accept_downloads=True)
    page=ctx.new_page()
    errors=[]
    page.on("pageerror",lambda e: errors.append(str(e)))
    page.goto(URL,wait_until="domcontentloaded",timeout=90000)
    open_node(page)
    page.screenshot(path=str(OUT/f"{name}-bubble.png"),full_page=True)
    bubble=tid(page,"journey-bubble").bounding_box()
    check(name+" visible bubble",bubble and bubble["width"]>40 and bubble["height"]>70,bubble)
    if not mobile:
        tid(page,"journey-discussion-reply-").first.wait_for(timeout=5000) if False else None
        page.locator('[data-testid^="journey-discussion-reply-"]').first.click()
        tid(page,"journey-discussion-body").fill("Khách xác nhận lấy hàng")
        tid(page,"journey-discussion-send").click()
        page.get_by_text("Khách xác nhận lấy hàng",exact=True).wait_for(timeout=30000)
        check("reply read back",True)
        upload(page,"QA PNG","qa.png","image/png",PNG)
        download(page,"qa.png",PNG)
        upload(page,"QA PDF","qa.pdf","application/pdf",PDF)
        download(page,"qa.pdf",PDF)
        page.reload(wait_until="domcontentloaded",timeout=90000)
        open_node(page)
        check("reload preserves both files",
             page.get_by_text("QA PNG",exact=True).count()>0 and
             page.get_by_text("QA PDF",exact=True).count()>0)
        page.screenshot(path=str(OUT/"desktop-roundtrip.png"),full_page=True)
    check(name+" no uncaught page errors",not errors,errors[:2])
    ctx.close()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            scenario(browser,False)
            scenario(browser,True)
        finally:
            browser.close()
    print("REAL_STREAMLIT_BROWSER_QA=PASS",len(done),flush=True)
except Exception as e:
    print("REAL_STREAMLIT_BROWSER_QA=FAIL",type(e).__name__,e,flush=True)
    (OUT/"results.json").write_text(json.dumps({"checks":done,"status":"FAIL",
        "error":f"{type(e).__name__}: {e}"},ensure_ascii=False,indent=2))
    raise
(OUT/"results.json").write_text(json.dumps({"checks":done,"status":"PASS"},ensure_ascii=False,indent=2))
