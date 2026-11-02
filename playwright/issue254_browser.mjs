/**
 * Issue #254 real Chromium 153 + Streamlit Components v2 verification:
 * - Desktop 1440x900 & Mobile 390x844 for Support (`qa.s254.support`, finance_view=True)
 * - Desktop 1440x900 & Mobile 390x844 for Sale (`qa.s254.sale`, finance_view=False)
 * - Verifies compact cluster `Phải thu / Đã thu / Còn phải thu`, UNKNOWN != 0 on
 *   quote-only lot, multi-currency VND/USD/CNY, payment record + payment reversal
 *   roundtrip on `/lo-hang`, zero horizontal overflow, and server+UI role boundary.
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

const OUT = resolve(arg("out", "evidence/issue254"));
const URL = arg("url", "http://127.0.0.1:9504/");
const CHROME = arg("chrome", "/tmp/chromium");
const PUPPETEER_PATH = arg("puppeteer-core", "/tmp/browsertest/node_modules/puppeteer-core");
const HOST = 'div[data-testid="stBidiComponentIsolated"]';
const PASSWORD = process.env.S254_TEST_PASSWORD;

assert(PASSWORD && PASSWORD.length >= 8, "S254_TEST_PASSWORD required");
assert(existsSync(CHROME), `Chromium binary missing at ${CHROME}`);
const puppeteer = require(PUPPETEER_PATH);
mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const readJson = (name) => JSON.parse(readFileSync(resolve(OUT, name), "utf8"));
const saveJson = (name, val) => writeFileSync(resolve(OUT, name), JSON.stringify(val, null, 2) + "\n");
const fmtVN = (n) => Math.round(n).toLocaleString("en-US").replace(/,/g, ".");

async function until(fn, label, timeout = 45000) {
  const end = Date.now() + timeout;
  let last;
  while (Date.now() < end) {
    try {
      const value = await fn();
      if (value) return value;
      last = value;
    } catch (err) {
      last = String(err);
    }
    await sleep(150);
  }
  throw new Error(`Timed out: ${label}; last=${JSON.stringify(last)}`);
}

async function shadow(page, body) {
  return page.evaluate(
    (code) => new Function(code)(),
    `const host = document.querySelector('${HOST}'); const root = host && host.shadowRoot; ${body}`
  );
}

async function handle(page, selector, text = "") {
  return page.evaluateHandle(
    ({ hostSel, selector, text }) => {
      const root = document.querySelector(hostSel)?.shadowRoot;
      if (!root) return null;
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
      };
      const nodes = [...root.querySelectorAll(selector)].filter(visible);
      return nodes.find((el) => !text || el.textContent.replace(/\s+/g, " ").trim().includes(text)) || null;
    },
    { hostSel: HOST, selector, text }
  );
}

async function clickDom(page, selector, text = "") {
  const h = await until(async () => {
    const h = await handle(page, selector, text);
    return h.asElement() ? h : (await h.dispose(), null);
  }, `clickDom ${selector} ${text}`);
  await page.evaluate((el) => {
    el.scrollIntoView({ block: "center", inline: "nearest" });
    el.click();
  }, h);
  await h.dispose();
  await sleep(250);
}

async function text(page) {
  return shadow(page, "return (root?.textContent || '').replace(/\\s+/g, ' ').trim();");
}

async function scrollShipmentIntoView(page, itemTestId, shipmentId) {
  await shadow(
    page,
    `
    if (!root) return;
    // Dismiss any toast close button so screenshots show unobstructed rows/cards
    const toastClose = [...root.querySelectorAll('button')].find((b) => b.closest('.toast-in'));
    if (toastClose) toastClose.click();
    const el = root.querySelector('[data-testid="${itemTestId}"][data-shipment-id="${shipmentId}"]');
    if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
    `
  );
  await sleep(200);
}

async function login(page, username) {
  await page.goto(URL, { waitUntil: "networkidle2", timeout: 120000 });
  await page.waitForSelector('input[aria-label="Tài khoản"]', { timeout: 120000 });
  await page.locator('input[aria-label="Tài khoản"]').fill(username);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[kind="primaryFormSubmit"]').click();
  await page.waitForSelector(HOST, { timeout: 120000 });
  await until(async () => (await text(page)).includes("Tổng quan"), `authenticated shell for ${username}`, 120000);
}

async function openShipmentsAllTime(page, isMobile = false) {
  const onFocusDetail = await shadow(page, "return !!root?.querySelector('[data-testid=\"shipment-identity-bar\"]');");
  if (onFocusDetail) {
    await clickDom(page, 'a[aria-label="Về trang chủ"]');
    await until(async () => (await text(page)).includes("Tổng quan"), "returned home from focus shell");
  }
  if (isMobile) {
    await clickDom(page, 'button[aria-label="Mở menu"]');
    await clickDom(page, 'a[href="/lo-hang"]', "Lô Hàng");
  } else {
    await clickDom(page, 'aside a[href="/lo-hang"]', "Lô Hàng");
  }
  await until(async () => (await text(page)).includes("Tìm thấy"), "shipments list");
  await clickDom(page, '[data-testid="shipment-period-tat-ca"]');
  await sleep(300);
}

async function readListMetrics(page, itemTestId) {
  return shadow(
    page,
    `
    if (!root) return null;
    const items = [...root.querySelectorAll('[data-testid="${itemTestId}"]')];
    const headers = [...root.querySelectorAll('table.tbl thead th')].map((th) => th.textContent.replace(/\\s+/g, ' ').trim());
    const tblWrap = root.querySelector('table.tbl')?.parentElement;
    const mainEl = root.querySelector('main') || root.firstElementChild;
    const clusters = {};
    let maxRight = 0;
    let minLeft = 99999;
    for (const item of items) {
      const r = item.getBoundingClientRect();
      if (r.width > 0) {
        maxRight = Math.max(maxRight, r.right);
        minLeft = Math.min(minLeft, r.left);
      }
      const id = item.getAttribute('data-shipment-id');
      const sum = item.querySelector('[data-testid="shipment-finance-summary"]');
      clusters[id] = sum ? {
        currency: sum.getAttribute('data-currency'),
        hasActual: sum.getAttribute('data-has-actual'),
        receivable: sum.querySelector('[data-testid="debt-receivable"]')?.textContent.trim(),
        received: sum.querySelector('[data-testid="debt-received"]')?.textContent.trim(),
        outstanding: sum.querySelector('[data-testid="debt-outstanding"]')?.textContent.trim(),
        rect: (() => { const b = sum.getBoundingClientRect(); return { x: Math.round(b.x), y: Math.round(b.y), width: Math.round(b.width), height: Math.round(b.height) }; })(),
      } : null;
    }
    return {
      itemCount: items.length,
      headers,
      docOverflowPx: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      tableOverflowPx: tblWrap ? (tblWrap.scrollWidth - tblWrap.clientWidth) : 0,
      maxRight: Math.round(maxRight),
      minLeft: Math.round(minLeft),
      totalClusterCount: root.querySelectorAll('[data-testid="shipment-finance-summary"]').length,
      clusters,
      mainText: (mainEl?.textContent || '').replace(/\\s+/g, ' ').trim(),
    };
    `
  );
}

async function typeIntoShadowInput(page, selector, value) {
  const h = await until(async () => {
    const h = await handle(page, selector);
    return h.asElement() ? h : (await h.dispose(), null);
  }, `input ${selector}`);
  await page.evaluate((node) => {
    node.scrollIntoView({ block: "center" });
    node.focus();
    if (typeof node.select === "function") node.select();
  }, h);
  await page.keyboard.down("Control");
  await page.keyboard.press("KeyA");
  await page.keyboard.up("Control");
  await page.keyboard.press("Backspace");
  await page.keyboard.type(value);
  await h.dispose();
}

const PAY_AMOUNT = 35_000_000;

const report = {
  chromiumVersion: execFileSync(CHROME, ["--version"], { encoding: "utf8" }).trim(),
  checks: [],
  metrics: {},
};
const pass = (name, details = {}) => {
  report.checks.push({ name, ok: true, ...details });
  console.log(`PASS ${name}`);
};

let browser;
try {
  browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "shell",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars"],
    env: { ...process.env },
  });

  // =========================================================================
  // SESSION 1: SUPPORT (`qa.s254.support`, finance_view = True)
  // =========================================================================
  {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(String(e)));

    // --- 1A. Desktop 1440x900 initial glance + multi-currency + quote-only ---
    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
    await login(page, "qa.s254.support");
    const seedTruth = readJson("seed-truth.json");
    const baseRec = Math.round(seedTruth["LO-0308"].receivable);
    report.seedTruth = seedTruth;
    await openShipmentsAllTime(page, false);
    await until(async () => {
      const m = await readListMetrics(page, "shipment-row");
      return m && m.itemCount >= 4 && m.clusters["LO-0308"] ? m : null;
    }, "desktop shipment rows with finance clusters");

    const deskInitial = await readListMetrics(page, "shipment-row");
    report.metrics.desktopSupportInitial = deskInitial;

    assert.equal(deskInitial.headers.length, 6, `expected 6 desktop columns: ${JSON.stringify(deskInitial.headers)}`);
    assert(deskInitial.headers.includes("Công nợ dịch vụ"), "missing Công nợ dịch vụ header");
    assert(deskInitial.headers.includes("Việc tiếp theo"), "missing Việc tiếp theo header");
    assert(deskInitial.docOverflowPx <= 0, `desktop document horizontal overflow: ${deskInitial.docOverflowPx}px`);
    assert(deskInitial.tableOverflowPx <= 0, `desktop table wrapper horizontal overflow: ${deskInitial.tableOverflowPx}px`);

    assert.deepEqual(
      {
        receivable: deskInitial.clusters["LO-0308"].receivable,
        received: deskInitial.clusters["LO-0308"].received,
        outstanding: deskInitial.clusters["LO-0308"].outstanding,
      },
      {
        receivable: `${fmtVN(baseRec)} VND`,
        received: "0 VND",
        outstanding: `${fmtVN(baseRec)} VND`,
      }
    );
    assert.deepEqual(
      {
        hasActual: deskInitial.clusters["LO-254-QUOTE"].hasActual,
        receivable: deskInitial.clusters["LO-254-QUOTE"].receivable,
        received: deskInitial.clusters["LO-254-QUOTE"].received,
        outstanding: deskInitial.clusters["LO-254-QUOTE"].outstanding,
      },
      { hasActual: "false", receivable: "—", received: "0 VND", outstanding: "—" }
    );
    assert(!deskInitial.mainText.includes("28.450.000"), "quote estimate leaked onto /lo-hang");
    assert.deepEqual(
      {
        receivable: deskInitial.clusters["LO-254-USD"].receivable,
        received: deskInitial.clusters["LO-254-USD"].received,
        outstanding: deskInitial.clusters["LO-254-USD"].outstanding,
      },
      { receivable: "2.400 USD", received: "900 USD", outstanding: "1.500 USD" }
    );
    assert.deepEqual(
      {
        receivable: deskInitial.clusters["LO-254-CNY"].receivable,
        received: deskInitial.clusters["LO-254-CNY"].received,
        outstanding: deskInitial.clusters["LO-254-CNY"].outstanding,
      },
      { receivable: "18.000 CNY", received: "18.000 CNY", outstanding: "0 CNY" }
    );

    await scrollShipmentIntoView(page, "shipment-row", "LO-254-CNY");
    await page.screenshot({ path: resolve(OUT, "desktop-support-shipments-initial.png") });
    pass("desktop_1440x900_support_glance_multiccy_unknown_no_overflow", {
      docOverflowPx: deskInitial.docOverflowPx,
      tableOverflowPx: deskInitial.tableOverflowPx,
    });

    // --- 1B. Click cluster -> open Tài chính / Công nợ -> record 35,000,000 VND -> check /lo-hang ---
    await clickDom(page, '[data-testid="shipment-row"][data-shipment-id="LO-0308"] [data-testid="shipment-finance-summary"]');
    await until(async () => (await text(page)).includes("Lịch sử thu / chi"), "opened Tài chính / Công nợ tab via cluster click");
    await clickDom(page, "button", "GHI NHẬN THANH TOÁN");
    await until(() => shadow(page, "return !!root.querySelector('[data-testid=\"payment-record-sheet\"]');"), "payment sheet opened");
    await typeIntoShadowInput(page, '[data-testid="payment-record-sheet"] input[inputmode="numeric"]', String(PAY_AMOUNT));
    await clickDom(page, '[data-testid="payment-record-submit"]');
    await until(() => shadow(page, "return !root.querySelector('[data-testid=\"payment-record-sheet\"]');"), "payment sheet closed on backend readback");

    await openShipmentsAllTime(page, false);
    const deskAfterPay = await until(async () => {
      const m = await readListMetrics(page, "shipment-row");
      return m?.clusters["LO-0308"]?.received === "35.000.000 VND" ? m : null;
    }, "updated /lo-hang cluster after payment_record");
    assert.equal(deskAfterPay.clusters["LO-0308"].outstanding, `${fmtVN(baseRec - PAY_AMOUNT)} VND`);
    await scrollShipmentIntoView(page, "shipment-row", "LO-0308");
    await page.screenshot({ path: resolve(OUT, "desktop-support-after-payment.png") });
    pass("desktop_payment_record_updates_shipments_list", deskAfterPay.clusters["LO-0308"]);

    // --- 1C. Mobile 390x844 check (while 35M payment is active!) ---
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
    await sleep(350);
    const mobSupport = await until(async () => {
      const m = await readListMetrics(page, "shipment-mobile-card");
      return m && m.itemCount >= 4 && m.clusters["LO-0308"] ? m : null;
    }, "mobile cards rendered at 390x844");
    report.metrics.mobileSupport = mobSupport;
    assert(mobSupport.docOverflowPx <= 0, `mobile document horizontal overflow: ${mobSupport.docOverflowPx}px`);
    assert(mobSupport.maxRight <= 390, `mobile card exceeded 390px viewport: maxRight=${mobSupport.maxRight}`);
    assert.equal(mobSupport.clusters["LO-0308"].received, "35.000.000 VND");
    assert.equal(mobSupport.clusters["LO-0308"].outstanding, `${fmtVN(baseRec - PAY_AMOUNT)} VND`);
    assert.equal(mobSupport.clusters["LO-254-QUOTE"].receivable, "—");
    assert.equal(mobSupport.clusters["LO-254-QUOTE"].outstanding, "—");
    assert.equal(mobSupport.clusters["LO-254-USD"].outstanding, "1.500 USD");
    await scrollShipmentIntoView(page, "shipment-mobile-card", "LO-0308");
    await page.screenshot({ path: resolve(OUT, "mobile-support-shipments.png") });
    pass("mobile_390x844_support_cards_no_overflow", {
      docOverflowPx: mobSupport.docOverflowPx,
      maxRight: mobSupport.maxRight,
    });

    // --- 1D. Reverse that 35,000,000 VND receipt via Điều chỉnh -> check /lo-hang reverts cleanly ---
    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
    await sleep(250);
    await clickDom(page, '[data-testid="shipment-row"][data-shipment-id="LO-0308"] [data-testid="shipment-finance-summary"]');
    await until(async () => (await text(page)).includes("Lịch sử thu / chi"), "re-opened Tài chính / Công nợ for reversal");
    await clickDom(page, "button[data-payment-id]", "Điều chỉnh");
    await until(() => shadow(page, "return !!root.querySelector('[data-testid=\"payment-correction-sheet\"]');"), "correction sheet opened");
    await typeIntoShadowInput(
      page,
      '[data-testid="payment-correction-sheet"] textarea',
      "Khách chuyển nhầm tài khoản, hoàn tác phiếu thu kiểm thử #254"
    );
    await clickDom(page, '[data-testid="payment-correction-sheet"] button', "XÁC NHẬN ĐIỀU CHỈNH");
    await until(() => shadow(page, "return !root.querySelector('[data-testid=\"payment-correction-sheet\"]');"), "correction sheet closed on backend readback");

    await openShipmentsAllTime(page, false);
    const deskAfterRev = await until(async () => {
      const m = await readListMetrics(page, "shipment-row");
      return m?.clusters["LO-0308"]?.received === "0 VND" ? m : null;
    }, "reverted /lo-hang cluster after payment_correction");
    assert.equal(deskAfterRev.clusters["LO-0308"].outstanding, `${fmtVN(baseRec)} VND`);
    await scrollShipmentIntoView(page, "shipment-row", "LO-0308");
    await page.screenshot({ path: resolve(OUT, "desktop-support-after-reversal.png") });
    assert.equal(pageErrors.length, 0, `Support browser errors: ${pageErrors.join(" | ")}`);
    pass("desktop_payment_reversal_updates_shipments_list_no_stale_balance", deskAfterRev.clusters["LO-0308"]);
    await ctx.close();
  }

  // =========================================================================
  // SESSION 2: SALE (`qa.s254.sale`, finance_view = False)
  // =========================================================================
  {
    const ctx = await browser.createBrowserContext();
    const page = await ctx.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(String(e)));

    await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
    await login(page, "qa.s254.sale");
    await openShipmentsAllTime(page, false);
    await until(async () => {
      const m = await readListMetrics(page, "shipment-row");
      return m && m.itemCount >= 4 ? m : null;
    }, "Sale desktop shipment rows");

    const salePayload = readJson("payload-sale.json");
    assert.equal(salePayload.finance_view_permission, false);
    assert.equal(salePayload.user.canViewFinance, false);
    assert.equal(salePayload.home_outstanding_total, null);
    assert.equal(salePayload.receivables_count, 0);
    assert.equal(salePayload.payables_count, 0);
    assert.equal(salePayload.reconciliation_count, 0);
    for (const [sid, fin] of Object.entries(salePayload.shipments_finance)) {
      assert.equal(fin.canView, false, `Sale payload canView not false on ${sid}`);
      assert.equal(fin.receivable, null, `Sale payload leaked receivable on ${sid}`);
      assert.equal(fin.received, null, `Sale payload leaked received on ${sid}`);
      assert.equal(fin.outstanding, null, `Sale payload leaked outstanding on ${sid}`);
      assert.equal(fin.payable, null, `Sale payload leaked payable on ${sid}`);
      assert.equal(fin.profit, null, `Sale payload leaked profit on ${sid}`);
      assert.deepEqual(fin.actual, [], `Sale payload leaked actual lines on ${sid}`);
      assert.deepEqual(fin.payments, [], `Sale payload leaked payments on ${sid}`);
    }

    const saleDesk = await readListMetrics(page, "shipment-row");
    const baseRec = Math.round(readJson("seed-truth.json")["LO-0308"].receivable);
    report.metrics.desktopSale = saleDesk;
    assert.equal(saleDesk.headers.length, 5, `Sale table must have 5 columns: ${JSON.stringify(saleDesk.headers)}`);
    assert(!saleDesk.headers.includes("Công nợ dịch vụ"), "Sale saw Công nợ dịch vụ header");
    assert.equal(saleDesk.totalClusterCount, 0, "Sale saw finance summary cluster on desktop");
    for (const secret of [fmtVN(baseRec), "2.400 USD", "1.500 USD", "18.000 CNY"]) {
      assert(!saleDesk.mainText.includes(secret), `Sale desktop UI leaked ${secret}`);
    }
    await scrollShipmentIntoView(page, "shipment-row", "LO-0308");
    await page.screenshot({ path: resolve(OUT, "desktop-sale-shipments-gated.png") });

    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
    await sleep(300);
    const saleMob = await readListMetrics(page, "shipment-mobile-card");
    report.metrics.mobileSale = saleMob;
    assert.equal(saleMob.totalClusterCount, 0, "Sale saw finance summary cluster on mobile");
    assert(saleMob.docOverflowPx <= 0, `Sale mobile overflow: ${saleMob.docOverflowPx}px`);
    await scrollShipmentIntoView(page, "shipment-mobile-card", "LO-0308");
    await page.screenshot({ path: resolve(OUT, "mobile-sale-shipments-gated.png") });
    assert.equal(pageErrors.length, 0, `Sale browser errors: ${pageErrors.join(" | ")}`);
    pass("sale_role_server_payload_and_ui_gated_desktop_and_mobile");
    await ctx.close();
  }

  report.exitCode = 0;
  saveJson("browser-results.json", report);
  console.log("ISSUE254_REAL_CHROMIUM=PASS");
} catch (err) {
  report.exitCode = 1;
  report.error = String(err?.stack || err);
  saveJson("browser-results.json", report);
  console.error(err);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
}
