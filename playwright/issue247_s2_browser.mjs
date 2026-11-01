/** Issue #247 S2: real Chromium + unchanged app.py + same-process DB observer.
 * Start issue247_s2_runtime.py first. Each viewport creates ONE distinct test
 * payment intent and asserts a delta of exactly one payment/request/audit.
 * No jsdom, no direct browser DB writes, no product-source mutation.
 */
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);
const arg = (name, fallback = "") => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : fallback;
};
const OUT = resolve(arg("out", "evidence/issue247/s2"));
const URL = arg("url", "http://127.0.0.1:9501/");
const CHROME = arg("chrome", "/tmp/chromium");
const HOST = 'div[data-testid="stBidiComponentIsolated"]';
const LOT = "LO-0306";
const AMOUNT = "137000";
const PASSWORD = process.env.S2_TEST_PASSWORD;
assert(PASSWORD && PASSWORD.length >= 8, "S2_TEST_PASSWORD required");
assert(existsSync(CHROME), "real Chromium binary required");
const puppeteer = require(arg("puppeteer-core", "puppeteer-core"));
mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const readJson = (name) => JSON.parse(readFileSync(resolve(OUT, name), "utf8"));
const save = (name, value) => writeFileSync(resolve(OUT, name), JSON.stringify(value, null, 2) + "\n");
async function until(fn, label, timeout = 45000) {
  const end = Date.now() + timeout;
  let last;
  while (Date.now() < end) {
    try { const value = await fn(); if (value) return value; last = value; }
    catch (error) { last = String(error); }
    await sleep(150);
  }
  throw new Error(`Timed out: ${label}; last=${JSON.stringify(last)}`);
}
async function shadow(page, body) {
  return page.evaluate((code) => new Function(code)(), `
    const host = document.querySelector('${HOST}');
    const root = host && host.shadowRoot;
    ${body}
  `);
}
async function handle(page, selector, text = "") {
  return page.evaluateHandle(({ hostSel, selector, text }) => {
    const root = document.querySelector(hostSel)?.shadowRoot;
    if (!root) return null;
    const visible = (el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
    };
    const nodes = [...root.querySelectorAll(selector)].filter(visible);
    return nodes.find((el) => !text || el.textContent.replace(/\s+/g, " ").trim().includes(text)) || null;
  }, { hostSel: HOST, selector, text });
}
async function click(page, selector, text = "") {
  const h = await until(async () => {
    const h = await handle(page, selector, text);
    return h.asElement() ? h : (await h.dispose(), null);
  }, `click ${selector} ${text}`);
  await clickHandle(page, h);
  await h.dispose();
}
async function clickDom(page, selector, text = "") {
  const h = await until(async () => {
    const h = await handle(page, selector, text);
    return h.asElement() ? h : (await h.dispose(), null);
  }, `dom click ${selector} ${text}`);
  await page.evaluate((el) => { el.scrollIntoView({ block: "center", inline: "nearest" }); el.click(); }, h);
  await h.dispose();
  await sleep(250);
}
async function clickHandle(page, h) {
  await page.evaluate((el) => el.scrollIntoView({ block: "center", inline: "nearest" }), h);
  await sleep(120);
  const box = await h.boundingBox();
  assert(box && box.width > 0 && box.height > 0, "visible click target");
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
}
async function text(page) {
  return shadow(page, "return (root?.textContent || '').replace(/\\s+/g, ' ').trim();");
}
async function instrument(page, events) {
  await page.evaluate((hostSel) => {
    const root = document.querySelector(hostSel)?.shadowRoot;
    if (!root || root.__s2Instrumented) return;
    root.__s2Instrumented = true;
    window.__s2Events = [];
    for (const type of ["click", "input", "change"]) {
      root.addEventListener(type, (event) => {
        const el = event.target;
        window.__s2Events.push({
          type, trusted: event.isTrusted, ns: performance.timeOrigin + performance.now(),
          testId: el.getAttribute?.("data-testid") || el.closest?.("[data-testid]")?.getAttribute("data-testid") || null,
          tag: el.tagName, text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 100),
          value: el.tagName === "INPUT" && el.inputMode === "numeric" ? el.value : undefined,
        });
      }, true);
    }
  }, HOST);
}
async function login(page) {
  await page.goto(URL, { waitUntil: "networkidle2", timeout: 120000 });
  await page.waitForSelector('input[aria-label="Tài khoản"]', { timeout: 120000 });
  await page.locator('input[aria-label="Tài khoản"]').fill("qa.s2.support");
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[kind="primaryFormSubmit"]').click();
  await page.waitForSelector(HOST, { timeout: 120000 });
  await until(async () => (await text(page)).includes("Tổng quan"), "authenticated staff shell", 120000);
  await instrument(page);
}
async function openLotFinance(page) {
  // MemoryRouter deliberately has no deep-link URL. Always use visible nav.
  await click(page, 'a[href="/lo-hang"]');
  await until(async () => (await text(page)).includes("Tìm thấy"), "shipment list");
  await click(page, '[data-testid="shipment-period-tat-ca"]');
  if (page.viewport().width < 768) {
    await click(page, `[data-testid="shipment-mobile-card"][data-shipment-id="${LOT}"] a`, "XEM 360°");
  } else {
    await click(page, `[data-testid="shipment-row"][data-shipment-id="${LOT}"] a`, LOT);
  }
  await until(async () => (await text(page)).includes(`Ghi nhận thanh toán`) || (await text(page)).includes(LOT), "shipment detail");
  await clickDom(page, '[data-testid="journey-global-page"]');
  await until(() => shadow(page, "return !!root.querySelector('[data-testid=\"journey-global-workspace\"]')"), "global workspace tabs");
  await clickDom(page, '[data-testid="journey-global-workspace"] button', "Tài chính");
  await until(async () => (await text(page)).includes("Lịch sử thu / chi"), "finance tab");
}
async function openSheet(page) {
  await click(page, "button", "＋ GHI NHẬN THANH TOÁN");
  await until(() => shadow(page, "return !!root.querySelector('[data-testid=\"payment-record-sheet\"]')"), "payment sheet");
}
async function amountInput(page, value) {
  const h = await handle(page, '[data-testid="payment-record-sheet"] input[inputmode="numeric"]');
  const el = h.asElement(); assert(el, "amount input");
  await page.evaluate((node) => { node.scrollIntoView({ block: "center" }); node.focus(); node.select(); }, el);
  await page.keyboard.press("Backspace");
  await page.keyboard.type(value);
  await h.dispose();
  await until(() => shadow(page, `return root.querySelector('[data-testid="payment-record-sheet"] input[inputmode="numeric"]')?.value === ${JSON.stringify(value)};`), "typed amount");
}
async function geometry(page) {
  return shadow(page, `
    const sheet = root.querySelector('[data-testid="payment-record-sheet"]');
    const submit = root.querySelector('[data-testid="payment-record-submit"]');
    if (!sheet || !submit) return { found: false };
    submit.scrollIntoView({block:'center', inline:'nearest'});
    const r = submit.getBoundingClientRect();
    const s = sheet.getBoundingClientRect();
    const x = r.left+r.width/2, y = r.top+r.height/2;
    let hit = document.elementFromPoint(x,y), guard=0;
    while (hit?.shadowRoot && guard++ < 8) {
      const inner = hit.shadowRoot.elementFromPoint(x,y);
      if (!inner || inner === hit) break;
      hit = inner;
    }
    const hitOk = hit === submit || submit.contains(hit);
    const inViewport = r.left >= -1 && r.right <= innerWidth+1 && r.top >= -1 && r.bottom <= innerHeight+1;
    const overflow = document.documentElement.scrollWidth > innerWidth+1 || root.scrollWidth > root.clientWidth+1;
    return {found:true, hitOk, inViewport, overflow, disabled:submit.disabled,
      viewport:{width:innerWidth,height:innerHeight}, submit:{x:r.x,y:r.y,width:r.width,height:r.height},
      sheet:{x:s.x,y:s.y,width:s.width,height:s.height}, documentScrollWidth:document.documentElement.scrollWidth,
      rootScrollWidth:root.scrollWidth, rootClientWidth:root.clientWidth};
  `);
}
function assertDelta(before, after, requestId, actor) {
  assert.equal(after.payment_count, before.payment_count + 1, "exactly one new payment");
  assert.equal(after.request_count, before.request_count + 1, "exactly one new request");
  assert.equal(after.audit_count, before.audit_count + 1, "exactly one new audit");
  assert.equal(after.event_count, before.event_count + 1, "exactly one new domain event");
  assert.equal(after.pid, before.pid, "same OS process");
  assert.equal(after.database_object_id, before.database_object_id, "same DB object");
  assert.equal(after.client_object_id, before.client_object_id, "same Mongo client");
  const payment = after.payments.find((p) => p.request_id === requestId);
  const request = after.requests.find((r) => r.request_id === requestId);
  const audit = after.audits.find((a) => a.after?.request_id === requestId || a.after?.payment?.request_id === requestId);
  const event = after.events.find((e) => e.payload?.request_id === requestId);
  assert(payment && request && audit && event, `all four records carry ${requestId}`);
  assert.equal(String(payment.amount), AMOUNT);
  assert.equal(payment.currency || after.currency, after.currency);
  assert.equal(request.shipment_id, LOT);
  assert.equal(audit.entity_id, LOT);
  assert.equal(event.payload.shipment_id, LOT);
  assert.equal(audit.actor_username, actor);
  assert.equal(audit.actor_role, "support");
  assert.equal(after.payments.filter((p) => p.request_id === requestId).length, 1);
  assert.equal(after.requests.filter((r) => r.request_id === requestId).length, 1);
  assert.equal(after.audits.filter((a) => a.after?.request_id === requestId || a.after?.payment?.request_id === requestId).length, 1);
  return { payment, request, audit, event };
}

const results = { url: URL, chrome: CHROME, chromiumVersion: execFileSync(CHROME, ["--version"], { encoding: "utf8" }).trim(), viewports: {}, checks: [], errors: [] };
const pass = (name, extra = {}) => { results.checks.push({ name, ok: true, ...extra }); console.log(`PASS ${name}`); };
let browser;
try {
  browser = await puppeteer.launch({ executablePath: CHROME, headless: "shell",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars"],
    env: { ...process.env } });
  results.browserVersion = await browser.version();
  let initial;
  for (const viewport of [{ id: "desktop", width: 1440, height: 900 }, { id: "mobile", width: 390, height: 844 }]) {
    const page = await browser.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(String(e)));
    await page.setViewport({ width: viewport.width, height: viewport.height, deviceScaleFactor: 1 });
    const receipt = { viewport, steps: [] };
    results.viewports[viewport.id] = receipt;
    try {
      await login(page);
      await until(() => { const r = readJson("latest-readback.json"); return r.actor.username === "qa.s2.support" && r.finance_write && r; }, "support readback");
      if (!initial) {
        initial = readJson("pre-state.json");
        assert.equal(initial.currency, "VND");
        pass("initial_fixture_and_real_chromium", { initial });
      }
      receipt.initialReadback = readJson("latest-readback.json");
      await openLotFinance(page);
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-finance.png`), fullPage: false });
      await openSheet(page);
      // Nonpositive input is rejected before dispatch; compare canonical call log.
      const callsBeforeInvalid = readJson("writer-calls.json").length;
      await amountInput(page, "0");
      await click(page, '[data-testid="payment-record-submit"]');
      await until(async () => (await text(page)).includes("Chưa nhập số tiền"), "invalid amount refusal");
      await sleep(700);
      assert.equal(readJson("writer-calls.json").length, callsBeforeInvalid, "invalid amount reached writer");
      receipt.invalid = { amount: "0", writerCallsBefore: callsBeforeInvalid, writerCallsAfter: readJson("writer-calls.json").length, dom: await text(page) };
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-invalid.png`) });
      pass(`${viewport.id}_invalid_zero_writes`);
      await amountInput(page, "abc");
      await click(page, '[data-testid="payment-record-submit"]');
      await until(async () => (await text(page)).includes("Chưa nhập số tiền"), "non-numeric amount refusal");
      await sleep(500);
      assert.equal(readJson("writer-calls.json").length, callsBeforeInvalid, "non-numeric amount reached writer");
      receipt.invalidNonNumeric = { amount: "abc", writerCallsAfter: readJson("writer-calls.json").length };
      pass(`${viewport.id}_invalid_nonnumeric_zero_writes`);
      await amountInput(page, AMOUNT);
      const requestId = await shadow(page, "return root.querySelector('[data-testid=\"payment-record-sheet\"] b.font-mono')?.textContent.trim();");
      assert(/^PAY-REQ-[A-Z0-9]+-[A-Z0-9]+$/.test(requestId || ''), "stable request id visible in sheet");
      receipt.requestId = requestId;
      receipt.before = readJson("latest-readback.json").raw;
      receipt.geometryBeforeSubmit = await geometry(page);
      assert(receipt.geometryBeforeSubmit.hitOk && receipt.geometryBeforeSubmit.inViewport && !receipt.geometryBeforeSubmit.overflow, "submit reachable without overflow");
      await instrument(page);
      const validSubmitStartNs = await page.evaluate(() => performance.timeOrigin + performance.now());
      const submit = (await handle(page, '[data-testid="payment-record-submit"]')).asElement();
      await page.evaluate((el) => el.scrollIntoView({ block: "center" }), submit);
      const box = await submit.boundingBox();
      // Two physical clicks in immediate succession: the second must be absorbed.
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
      await submit.dispose();
      await until(() => shadow(page, "return !!root.querySelector('[data-testid=\"payment-record-pending\"]')"), "pending DOM");
      receipt.pending = await shadow(page, `
        const s=root.querySelector('[data-testid="payment-record-submit"]');
        return {text:root.querySelector('[data-testid="payment-record-pending"]').textContent,
          submitDisabled:s.disabled, sheetPresent:!!root.querySelector('[data-testid="payment-record-sheet"]'),
          successToast:(root.textContent||'').includes('Đã ghi nhận khoản thu')};
      `);
      assert(receipt.pending.submitDisabled && !receipt.pending.successToast, "no premature green");
      const pendingProbe = readJson("latest-readback.json");
      assert(!pendingProbe.lastWrites.some((w) => w.requestId === requestId), "pending before backend outcome");
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-pending.png`) });
      pass(`${viewport.id}_pending_no_premature_success`, receipt.pending);
      const confirmed = await until(() => {
        const r = readJson("latest-readback.json");
        const w = r.lastWrites.find((w) => w.event === "payment_record" && w.requestId === requestId);
        const p = r.fresh_payment_projection.find((p) => p.requestId === requestId);
        return w?.ok && p && r.raw.payments.some((p) => p.request_id === requestId) ? r : null;
      }, "correlated backend + fresh model + raw store", 120000);
      receipt.confirmed = confirmed;
      receipt.matched = assertDelta(receipt.before, confirmed.raw, requestId, "qa.s2.support");
      const calls = readJson("writer-calls.json").filter((c) => c.request_id === requestId);
      assert.equal(calls.length, 1, "double click caused duplicate writer call");
      assert.equal(calls[0].ok, true);
      receipt.writerCalls = calls;
      await until(async () => !(await shadow(page, "return !!root.querySelector('[data-testid=\"payment-record-sheet\"]')")), "sheet closes after confirmation");
      await until(async () => (await text(page)).includes(receipt.matched.payment.id), "visible persisted payment id");
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-success.png`) });
      pass(`${viewport.id}_same_store_one_payment_request_audit`, { requestId, before: receipt.before, after: confirmed.raw });
      receipt.domEventsBeforeReload = await page.evaluate(() => window.__s2Events || []);
      receipt.submitClickEvents = receipt.domEventsBeforeReload.filter((e) => e.type === 'click' && e.testId === 'payment-record-submit' && e.ns >= validSubmitStartNs);
      // The intentional double-click may deliver two trusted DOM clicks before
      // React paints `disabled`; the product's synchronous pending ref must still
      // produce exactly ONE writer call (asserted below). Never fake a single DOM
      // click by hiding the second physical click.
      assert(receipt.submitClickEvents.length >= 1 && receipt.submitClickEvents.length <= 2, 'one or two physical submit clicks captured');
      assert(receipt.submitClickEvents.every((e) => e.trusted), 'submit clicks are trusted browser events');
      // Full reload: Streamlit session auth is intentionally not persisted in
      // browser storage, so re-authenticate the SAME TEST Support user if the
      // canonical login gate appears. MemoryRouter also returns home.
      await page.reload({ waitUntil: "networkidle2", timeout: 120000 });
      await page.waitForSelector(`input[aria-label="Tài khoản"], ${HOST}`, { timeout: 120000 });
      if (await page.$('input[aria-label="Tài khoản"]')) {
        await page.locator('input[aria-label="Tài khoản"]').fill("qa.s2.support");
        await page.locator('input[type="password"]').fill(PASSWORD);
        await page.locator('button[kind="primaryFormSubmit"]').click();
      }
      await page.waitForSelector(HOST, { timeout: 120000 });
      await until(async () => (await text(page)).includes("Tổng quan"), "shell after reload");
      await instrument(page);
      await openLotFinance(page);
      await until(async () => (await text(page)).includes(receipt.matched.payment.id), "payment survives reload");
      const reloaded = await until(() => {
        const r = readJson("latest-readback.json");
        return r.observed_ns > confirmed.observed_ns && r.fresh_payment_projection.some((p) => p.requestId === requestId) ? r : null;
      }, "fresh post-reload model");
      assertDelta(receipt.before, reloaded.raw, requestId, "qa.s2.support");
      receipt.reloaded = reloaded;
      await openSheet(page);
      await amountInput(page, AMOUNT);
      receipt.geometryAfterReload = await geometry(page);
      assert(receipt.geometryAfterReload.hitOk && receipt.geometryAfterReload.inViewport && !receipt.geometryAfterReload.overflow, "post-reload submit reachable");
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-reload-sheet.png`) });
      // Cancel without a second write; preserve the single persisted intent.
      await click(page, '[data-testid="payment-record-sheet"] button', "Hủy");
      receipt.domEventsAfterReload = await page.evaluate(() => window.__s2Events || []);
      receipt.domEvents = [...receipt.domEventsBeforeReload, ...receipt.domEventsAfterReload];
      receipt.pageErrors = pageErrors;
      assert.equal(pageErrors.length, 0, `browser errors: ${pageErrors.join("; ")}`);
      pass(`${viewport.id}_reload_geometry_and_no_browser_errors`, { geometry: receipt.geometryAfterReload });
    } catch (error) {
      receipt.failure = String(error?.stack || error);
      receipt.dom = await text(page).catch(() => "");
      receipt.pageErrors = pageErrors;
      await page.screenshot({ path: resolve(OUT, `${viewport.id}-failure.png`) }).catch(() => {});
      throw error;
    } finally { await page.close(); }
  }
  results.final = readJson("latest-readback.json");
  results.rbacNegative = readJson("rbac-negative.json");
  assert.equal(results.final.raw.payment_count, initial.payment_count + 2, "one distinct payment per viewport, no duplicates");
  pass("S2_REAL_BROWSER_SAME_STORE", { finalCounts: {
    payments: results.final.raw.payment_count, requests: results.final.raw.request_count,
    audits: results.final.raw.audit_count, events: results.final.raw.event_count } });
  results.exitCode = 0;
} catch (error) {
  results.errors.push(String(error?.stack || error));
  results.exitCode = 1;
  console.error(error);
} finally {
  save("browser-results.json", results);
  if (browser) await browser.close();
}
process.exitCode = results.exitCode;
