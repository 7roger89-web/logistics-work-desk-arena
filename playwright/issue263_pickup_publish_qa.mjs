/**
 * Issue #263 — real-Chromium acceptance for "công bố mốc Lấy hàng".
 *
 * The loop proven here is the Owner's, on the REAL Streamlit app + REAL built
 * component bundle, on isolated mongomock staging data:
 *
 *   staff (qa.263.support) saves the pickup ATD through the product UI
 *     → customer A still sees nothing
 *       → Admin (qa.263.admin) verifies the pending source and publishes it
 *         through the EXISTING publication screen
 *           → customer A reloads and sees the milestone
 *             → customer B still sees nothing of customer A.
 *
 * No `public_events` fixture exists anywhere: the runtime deletes them at
 * start and `/?!as=state` exposes the authoritative DB snapshot, so every
 * source row the Admin verifies was created by the staff action in THIS run.
 *
 * Usage:
 *   node playwright/issue263_pickup_publish_qa.mjs --url http://127.0.0.1:9513 \
 *     --out evidence/LOGI-G15-PUBLISH-PICKUP-20261102/browser \
 *     --chrome /tmp/chromium --puppeteer-core /tmp/browser/node_modules/puppeteer-core
 */
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);
const arg = (name, fallback = "") => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};
const URL_ = arg("url", "http://127.0.0.1:9513/").replace(/\/$/, "");
const OUT = resolve(arg("out", "evidence/LOGI-G15-PUBLISH-PICKUP-20261102/browser"));
const CHROME = arg("chrome", "/tmp/chromium");
const PUPPETEER = arg("puppeteer-core", "/tmp/browser/node_modules/puppeteer-core");
const PASSWORD = process.env.ISSUE263_TEST_PASSWORD;
const EVIDENCE_DIR = resolve(arg("evidence-dir", "/tmp/g15ev"));
const HOST = 'div[data-testid="stBidiComponentIsolated"]';
const LOT_A = "LO-263-A";
const LOT_B = "LO-263-B";
const CUST_A = "CUST-263-A";
const ATD = "2026-11-02";
const SECRETS = ["SECRET_263_INTERNAL_MARGIN", "987654321", "0900263999", "桂A-26399"];
if (!PASSWORD) throw new Error("ISSUE263_TEST_PASSWORD required");
if (!existsSync(CHROME)) throw new Error(`Chromium missing at ${CHROME}`);
const puppeteer = require(PUPPETEER);
mkdirSync(OUT, { recursive: true });

const checks = [];
const notes = {};
function check(name, pass, detail = "") {
  checks.push({ name, pass: Boolean(pass), detail: String(detail).slice(0, 600) });
  console.log(`${pass ? "PASS" : "FAIL"} ${name} :: ${String(detail).replace(/\s+/g, " ").slice(0, 160)}`);
  if (!pass) throw new Error(`CHECK FAILED: ${name} :: ${String(detail).slice(0, 300)}`);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(fn, label, timeout = 60000) {
  const end = Date.now() + timeout;
  let last = "";
  while (Date.now() < end) {
    try {
      last = await fn();
      if (last) return last;
    } catch (error) { last = error.message; }
    await sleep(400);
  }
  throw new Error(`timeout: ${label} (last=${String(last).slice(0, 200)})`);
}

/* --------------------------------------------------------------- shadow DOM */
async function shadowText(page) {
  return page.evaluate((sel) => {
    const root = document.querySelector(sel)?.shadowRoot;
    if (!root) return "";
    const walk = (n) => {
      let out = "";
      n.childNodes.forEach((c) => {
        if (c.nodeType === 3) out += c.textContent;
        else if (c.nodeType === 1) out += c.shadowRoot ? walk(c.shadowRoot) : walk(c);
      });
      return out;
    };
    return walk(root).replace(/\s+/g, " ");
  }, HOST);
}
async function clickShadow(page, selector, text = "", scope = "") {
  const ok = await until(async () => page.evaluate(({ hostSel, selector, text, scope }) => {
    const root = document.querySelector(hostSel)?.shadowRoot;
    if (!root) return false;
    const base = scope ? root.querySelector(scope) : root;
    if (!base) return false;
    const el = [...base.querySelectorAll(selector)].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }).find((e) => !text
      || (e.textContent || "").replace(/\s+/g, " ").toLowerCase().includes(text.toLowerCase()));
    if (!el) return false;
    el.scrollIntoView({ block: "center" });
    el.click();
    return true;
  }, { hostSel: HOST, selector, text, scope }), `click ${selector} ${text}`, 45000).catch(() => false);
  await sleep(900);
  return ok;
}

/* ------------------------------------------------------------------ Streamlit */
async function login(page, username) {
  await page.goto(`${URL_}/`, { waitUntil: "networkidle2", timeout: 180000 });
  const needsLogin = await until(async () => page.$('input[aria-label="Tài khoản"]'), "login form", 180000);
  if (needsLogin) {
    await page.locator('input[aria-label="Tài khoản"]').fill(username);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.locator('button[kind="primaryFormSubmit"]').click();
  }
  await page.waitForSelector(HOST, { timeout: 180000 });
  await until(async () => (await shadowText(page)).includes("Tổng quan"), `shell for ${username}`, 120000);
}
async function readState(browser, viewport, mode = "state") {
  // The QA runtime writes the authoritative snapshot to the evidence dir while
  // rendering `?as=<mode>`; Streamlit's pretty JSON display drops commas, so the
  // file (not the DOM text) is the artifact the runner compares against.
  const marker = Date.now();
  const page = await browser.newPage();
  await page.setViewport({ width: viewport.width, height: viewport.height });
  await page.goto(`${URL_}/?as=${mode}&t=${marker}`, { waitUntil: "networkidle2", timeout: 180000 });
  await until(async () => page.evaluate(() => (document.body.innerText || "").includes("customer_id")),
    `state page ${mode}`, 180000);
  await page.close();
  const path = resolve(EVIDENCE_DIR, "state-readback.json");
  const payload = await until(async () => {
    if (!existsSync(path)) return null;
    try {
      const parsed = JSON.parse(readFileSync(path, "utf8"));
      return Array.isArray(parsed?.shipments) ? parsed : null;
    } catch { return null; }
  }, `state file ${mode}`, 30000);
  await sleep(400);
  return payload;
}

async function asideIsVisible(page) {
  return page.evaluate((sel) => {
    const rect = document.querySelector(sel)?.shadowRoot?.querySelector("aside")?.getBoundingClientRect();
    return Boolean(rect && rect.width > 0);
  }, HOST);
}
/** The narrow layout hides the sidebar behind the product's own "Mở menu". */
async function openShipmentList(page) {
  const desktop = await asideIsVisible(page);
  if (!desktop) await clickShadow(page, 'button[aria-label="Mở menu"]');
  await clickShadow(page, desktop ? 'aside a[href="/lo-hang"]' : 'a[href="/lo-hang"]', "Lô hàng");
  await until(async () => (await shadowText(page)).includes("Tìm thấy"), "shipments list", 90000);
  if (!desktop) {
    // The drawer is an overlay; dismiss it through its own close control before
    // touching anything behind it.
    const closed = await page.evaluate((sel) => {
      const overlay = [...document.querySelectorAll(sel)].map((h) => h.shadowRoot)
        .filter(Boolean).map((root) => root.querySelector("div.fixed.inset-0"))
        .find((el) => el && el.getBoundingClientRect().width > 0);
      const button = overlay?.querySelector("button");
      if (!button) return false;
      button.click();
      return true;
    }, HOST);
    if (closed) await sleep(1200);
  }
}

/* ------------------------------------------------------------------ staff flow */
async function staffSavesPickup(page, browser, viewport) {
  await login(page, "qa.263.support");
  await openShipmentList(page);
  await clickShadow(page, "button", "Tất cả thời gian");
  await sleep(700);
  await clickShadow(page, `a[href="/lo-hang/${LOT_A}"]`);
  await until(async () => (await shadowText(page)).includes("MỞ CÔNG ĐOẠN"), "lot detail", 90000);
  const before = await shadowText(page);
  check(`${viewport.id}: staff lot opens before any milestone is published`,
    !before.includes("Đã lấy hàng"), "no milestone text on the staff lot");
  await page.screenshot({ path: `${OUT}/${viewport.id}-1-staff-lot-before.png` });

  await clickShadow(page, "button", "Đóng Quick Panel");
  await sleep(1000);
  await clickShadow(page, '[data-testid="journey-global-page"]');
  await until(async () => page.evaluate((sel) => Boolean(
    document.querySelector(sel)?.shadowRoot?.querySelector('[data-testid="journey-global-workspace"]'),
  ), HOST), "global workspace", 90000);
  await clickShadow(page, "button", "Thông tin", '[data-testid="journey-global-workspace"]');
  await until(async () => (await shadowText(page)).includes("CÁC CHẶNG VẬN CHUYỂN"), "leg editor", 90000);
  await clickShadow(page, "summary", "Chặng 1");
  await sleep(600);

  // The ATD field is the ONE labelled input of the pickup leg; `Field` wraps its
  // own input, so the input is INSIDE the label element.
  const atdHandle = await until(async () => page.evaluateHandle((sel) => {
    const root = document.querySelector(sel)?.shadowRoot;
    const ws = root?.querySelector('[data-testid="journey-global-workspace"]');
    const label = [...(ws?.querySelectorAll("label") || [])]
      .find((l) => (l.querySelector("span")?.textContent || "").trim() === "ATD");
    return label?.querySelector("input") || null;
  }, HOST), "ATD input", 60000);
  check(`${viewport.id}: the staff pickup ATD field is present`, Boolean(atdHandle.asElement()));
  await atdHandle.asElement().click();
  await atdHandle.asElement().focus();
  await page.keyboard.down("Control");
  await page.keyboard.press("KeyA");
  await page.keyboard.up("Control");
  await page.keyboard.type(ATD, { delay: 45 });
  await sleep(400);
  const typed = await page.evaluate((el) => el.value, atdHandle);
  check(`${viewport.id}: staff types the real pickup date into ATD`, typed === ATD, `value=${typed}`);
  await page.screenshot({ path: `${OUT}/${viewport.id}-2-staff-atd-typed.png` });

  await clickShadow(page, "button", "LƯU CÁC CHẶNG");
  const acknowledged = await until(async () => {
    const text = await shadowText(page);
    return text.includes("Đã gửi các chặng vận chuyển") ? text : null;
  }, "staff save dispatched", 90000).catch(() => "");
  check(`${viewport.id}: staff save is sent from the product UI`, Boolean(acknowledged));
  await sleep(2500);
  await page.screenshot({ path: `${OUT}/${viewport.id}-3-staff-saved.png` });

  // Authoritative readback: the source row exists BECAUSE of this action.
  const state = await until(async () => {
    const snapshot = await readState(browser, viewport);
    return snapshot?.public_events?.length === 1 ? snapshot : null;
  }, "pending source created by the staff action", 90000);
  notes[`${viewport.id}_staff_state`] = state;
  const source = state.public_events[0];
  const lot = state.shipments.find((row) => row.id === LOT_A) || {};
  check(`${viewport.id}: the staff action persisted the pickup date`, lot.pickup_atd === ATD,
    `pickup_atd=${lot.pickup_atd}`);
  check(`${viewport.id}: the staff action created exactly ONE unverified source`,
    source.customer_id === CUST_A && source.shipment_id === LOT_A
      && source.stage_id === "pickup" && source.occurred_at === ATD
      && source.verified === false && source.recorded_by === "qa.263.support",
    JSON.stringify(source));
  check(`${viewport.id}: nothing is published yet after the staff save`,
    state.publications.length === 0 && !lot.published,
    `publications=${state.publications.length} published=${lot.published || ""}`);
  return state;
}

/* ------------------------------------------------------------------ customer */
async function openCustomer(page, mode) {
  await page.goto(`${URL_}/?as=${mode}`, { waitUntil: "networkidle2", timeout: 180000 });
  await page.waitForSelector(HOST, { timeout: 180000 });
  await until(async () => (await shadowText(page)).length > 200, `customer ${mode} portal`, 180000);
  await sleep(2500);
  return shadowText(page);
}

/* ------------------------------------------------------------------ admin flow */
async function adminVerifiesAndPublishes(page, browser, viewport) {
  await login(page, "qa.263.admin");
  const summary = await until(async () => page.evaluateHandle(() => [...document.querySelectorAll("summary")]
    .find((s) => (s.textContent || "").includes("duyệt và công bố"))), "publication expander", 120000);
  await summary.asElement().scrollIntoView();
  await summary.asElement().click();
  // Streamlit replaces the panel DOM on every rerun, so the panel is re-queried
  // (never cached) before each read or screenshot.
  const panelHandle = async () => until(async () => page.evaluateHandle(() =>
    [...document.querySelectorAll('[data-testid="stExpander"]')]
      .find((e) => (e.querySelector("summary")?.textContent || "").includes("duyệt và công bố"))),
  "publication panel", 120000);
  const panelText = async () => page.evaluate(() => {
    const panel = [...document.querySelectorAll('[data-testid="stExpander"]')]
      .find((e) => (e.querySelector("summary")?.textContent || "").includes("duyệt và công bố"));
    return panel ? panel.innerText.replace(/\s+/g, " ") : "";
  });
  const panelShot = async (path) => (await panelHandle()).asElement().screenshot({ path });

  await until(async () => (await panelText()).includes("Nguồn chờ xác minh"), "pending source block", 120000);
  const pending = await panelText();
  check(`${viewport.id}: Admin sees the staff source waiting for verification`,
    pending.includes("Nguồn chờ xác minh") && pending.includes("Đã lấy hàng")
      && pending.includes("2026-11-02") && pending.includes("qa.263.support"),
    pending.match(/Nguồn chờ xác minh[\s\S]{0,180}/)?.[0] || pending.slice(0, 180));
  await panelShot(`${OUT}/${viewport.id}-4-admin-pending-source.png`);

  // Real clicks: streamlit only reacts to a real pointer event on the checkbox.
  const confirmBox = await until(async () => page.evaluateHandle(() =>
    [...document.querySelectorAll('input[type="checkbox"]')]
      .find((c) => (c.closest("label")?.textContent || "").includes("đối chiếu nguồn này"))),
  "verify confirmation checkbox", 90000);
  await confirmBox.asElement().scrollIntoView();
  await confirmBox.asElement().click();
  await sleep(1500);
  const verifyBtn = await until(async () => page.evaluateHandle(() =>
    [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Xác minh nguồn"))),
  "verify button", 90000);
  if (await page.evaluate((el) => el.disabled, verifyBtn)) {
    throw new Error("verify button still disabled after the Admin confirmation");
  }
  await verifyBtn.asElement().scrollIntoView();
  await verifyBtn.asElement().click();

  // The authoritative result of the Admin action is the stored source row.
  const verifiedState = await until(async () => {
    const snapshot = await readState(browser, viewport);
    return snapshot?.public_events?.[0]?.verified === true ? snapshot : null;
  }, "source verified by the Admin action", 120000);
  notes[`${viewport.id}_verified_state`] = verifiedState;
  const verifiedSource = verifiedState.public_events[0];
  check(`${viewport.id}: Admin verified THAT source and nothing else`,
    verifiedSource.id.startsWith("pickup:") && verifiedSource.verified_by === "qa.263.admin"
      && verifiedSource.occurred_at === ATD && verifiedSource.state === "VERIFIED"
      && verifiedSource.customer_id === CUST_A,
    JSON.stringify(verifiedSource));
  check(`${viewport.id}: verification alone did not publish anything`,
    verifiedState.publications.length === 0, `publications=${verifiedState.publications.length}`);

  await until(async () => !(await panelText()).includes("Nguồn chờ xác minh"), "pending block cleared", 120000);
  await until(async () => (await panelText()).includes("Mốc tiến độ được duyệt"), "verified event selector", 120000);
  await panelShot(`${OUT}/${viewport.id}-5-admin-verified.png`);

  const eventSelect = await until(async () => page.$('input[aria-label="Mốc tiến độ được duyệt"]'),
    "verified event multiselect", 120000);
  await eventSelect.click();
  await page.waitForSelector('[role="listbox"] [role="option"]', { timeout: 90000 });
  const options = await page.$$eval('[role="listbox"] [role="option"]',
    (els) => els.map((e) => e.innerText.replace(/\s+/g, " ")));
  notes[`${viewport.id}_publisher_options`] = options;
  check(`${viewport.id}: the existing publisher offers exactly the ONE verified pickup version`,
    options.length === 1 && options[0].includes("Đã lấy hàng") && options[0].includes(verifiedSource.version),
    JSON.stringify(options));
  await page.click('[role="listbox"] [role="option"]');
  await sleep(1800);
  await page.keyboard.press("Escape");
  await sleep(1800);

  const publishDisabled = async () => page.evaluate(() => {
    const button = [...document.querySelectorAll("button")]
      .find((b) => (b.textContent || "").includes("Duyệt và công bố phiên bản mới"));
    return button ? button.disabled : null;
  });
  check(`${viewport.id}: publish stays disabled until the Admin confirms the selection`,
    (await publishDisabled()) === true, "disabled before confirmation");
  await until(async () => page.evaluateHandle(() =>
    [...document.querySelectorAll('input[type="checkbox"]')]
      .find((c) => (c.closest("label")?.textContent || "").includes("Tôi đã đối chiếu nguồn nghiệp vụ"))),
  "publish confirmation checkbox", 90000).then((handle) => handle.asElement().click());
  await sleep(1800);
  check(`${viewport.id}: publish becomes available only after explicit confirmation`,
    (await publishDisabled()) === false, "enabled after confirmation");
  await until(async () => page.evaluateHandle(() =>
    [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Duyệt và công bố phiên bản mới"))),
  "publish button", 90000).then(async (handle) => {
    await handle.asElement().scrollIntoView();
    await handle.asElement().click();
  });

  const publishedState = await until(async () => {
    const snapshot = await readState(browser, viewport);
    return snapshot?.publications?.[0]?.state === "PUBLISHED" ? snapshot : null;
  }, "publication written by the Admin action", 150000);
  notes[`${viewport.id}_published_state`] = publishedState;
  const publication = publishedState.publications[0];
  const source = publishedState.public_events[0];
  const lotA = publishedState.shipments.find((row) => row.id === LOT_A) || {};
  check(`${viewport.id}: the publication is pinned to that exact verified version`,
    publication.approved_by === "qa.263.admin"
      && publication.event_versions?.[source.id] === source.version
      && lotA.published === publication.version,
    JSON.stringify({ publication, published: lotA.published }));
  await sleep(2500);
  await panelShot(`${OUT}/${viewport.id}-6-admin-published.png`);
  return { publication, source };
}

/* ----------------------------------------------------------------------- main */
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  env: { ...process.env, LD_LIBRARY_PATH: "/tmp/al2023/lib:/tmp" },
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--single-process"],
});
const viewports = [
  { id: "desktop", width: 1440, height: 900 },
  { id: "mobile", width: 390, height: 844 },
];
let failure = null;
try {
  for (const viewport of viewports) {
    await readState(browser, viewport, "reset");
    const staffPage = await browser.newPage();
    await staffPage.setViewport({ width: viewport.width, height: viewport.height });
    await staffSavesPickup(staffPage, browser, viewport);
    await staffPage.close();

    // B — before publication, customer A must not see the new milestone.
    const aBeforePage = await browser.newPage();
    await aBeforePage.setViewport({ width: viewport.width, height: viewport.height });
    const aBefore = await openCustomer(aBeforePage, "khach-a");
    notes[`${viewport.id}_customer_before`] = aBefore.slice(0, 1500);
    check(`${viewport.id}: customer A does NOT see the milestone before publication`,
      !aBefore.includes("Đã lấy hàng"), aBefore.slice(0, 160));
    await aBeforePage.screenshot({ path: `${OUT}/${viewport.id}-3b-customer-a-before.png`, fullPage: true });
    await aBeforePage.close();

    const adminPage = await browser.newPage();
    await adminPage.setViewport({ width: viewport.width, height: viewport.height });
    await adminVerifiesAndPublishes(adminPage, browser, viewport);

    const aPage = await browser.newPage();
    await aPage.setViewport({ width: viewport.width, height: viewport.height });
    const aText = await openCustomer(aPage, "khach-a");
    notes[`${viewport.id}_customer_after`] = aText.slice(0, 3000);
    check(`${viewport.id}: customer A reloads and sees the published milestone`,
      aText.includes("Đã lấy hàng") && aText.includes(LOT_A), aText.slice(0, 200));
    const leaked = SECRETS.filter((secret) => aText.includes(secret));
    check(`${viewport.id}: the customer payload carries no INTERNAL/finance data`,
      leaked.length === 0, JSON.stringify(leaked));
    await aPage.screenshot({ path: `${OUT}/${viewport.id}-7-customer-a-milestone.png`, fullPage: true });
    await aPage.close();

    const bPage = await browser.newPage();
    await bPage.setViewport({ width: viewport.width, height: viewport.height });
    const bText = await openCustomer(bPage, "khach-b");
    notes[`${viewport.id}_customer_b`] = bText.slice(0, 1500);
    check(`${viewport.id}: customer B never sees customer A's lot or milestone`,
      !bText.includes(LOT_A) && !bText.includes("Đã lấy hàng"), bText.slice(0, 200));
    await bPage.screenshot({ path: `${OUT}/${viewport.id}-8-customer-b-empty.png`, fullPage: true });
    await bPage.close();
  }
} catch (error) {
  failure = error.message;
} finally {
  await browser.close();
}

writeFileSync(resolve(OUT, "browser-checks.json"),
  JSON.stringify({ checks, notes, failure }, null, 2) + "\n");
if (failure) {
  console.log(`ISSUE263_PICKUP_BROWSER=FAIL :: ${failure}`);
} else {
  console.log(`ISSUE263_PICKUP_BROWSER=${checks.every((c) => c.pass) ? "PASS" : "FAIL"} (${checks.length} checks)`);
}
process.exit(failure ? 1 : 0);
