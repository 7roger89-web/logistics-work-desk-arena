/**
 * Issue #244 — real-Chromium QA for Node 00 KẾ HOẠCH on the staff Journey Map.
 *
 * Drives the REAL Streamlit app + the REAL built component bundle
 * (`component/dist/logi-shell.js`) in Chromium 153 at 1440x900 and 390x844.
 *
 * What is proven (a pretty screenshot is NOT a pass):
 *   * Node 00 is the first stop of the journey and opens the plan panel INSIDE
 *     the Journey (no jump to a global tab, no Streamlit expander above the map);
 *   * the quote shown is the lot's exact quote_id, and the same customer's other
 *     ACCEPTED quote never appears;
 *   * the customer contract is shown, the TT↔sub-agent contract is not, and
 *     "Đã ký" is never claimed;
 *   * an unclassified receipt stays "cần đối soát" and its amount never renders;
 *   * returning keeps the same lot + node;
 *   * layout: no horizontal overflow, primary controls inside the viewport and
 *     hit-testable (elementFromPoint) on BOTH viewports.
 *
 * Usage:
 *   node playwright/issue244_plan_staff_qa.mjs \
 *     --url http://127.0.0.1:9501/ --out evidence/issue244-plan \
 *     --chrome /tmp/chromium [--puppeteer-core /tmp/browsertest/node_modules/puppeteer-core]
 */
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
function loadPuppeteer() {
  for (const candidate of [arg("puppeteer-core", ""), process.env.PUPPETEER_CORE_PATH || ""].filter(Boolean)) {
    return require(candidate);
  }
  try { return require("puppeteer-core"); } catch { /* fall through */ }
  const fallback = "/tmp/browsertest/node_modules/puppeteer-core";
  if (existsSync(fallback)) return require(fallback);
  throw new Error("puppeteer-core not found (pass --puppeteer-core <path>)");
}
function requireChromium() {
  for (const candidate of [arg("chrome", ""), process.env.CHROME_PATH || "", "/tmp/chromium"].filter(Boolean)) {
    if (existsSync(candidate)) return candidate;
  }
  throw new Error("No Chromium binary. Pass --chrome <path> or set CHROME_PATH.");
}

const URL_ = arg("url", "http://127.0.0.1:9501/");
const OUT = resolve(arg("out", "evidence/issue244-plan"));
const HOST = 'div[data-testid="stBidiComponentIsolated"]';
const LOT = arg("lot", "LO-0306");
const FRESH_LOT = arg("fresh-lot", "LO-0309");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* The journey bundle is mounted inside Streamlit's shadow root, so every query
   and every synthetic click happens in there — same as a real operator. */
const ROOT_HELPERS = `
  const host = document.querySelector('${HOST}');
  const root = host && host.shadowRoot;
`;

async function shadowEval(page, body) {
  return page.evaluate((code) => {
    // eslint-disable-next-line no-new-func
    const fn = new Function(code);
    return fn();
  }, `${ROOT_HELPERS}\n${body}`);
}

async function shadowText(page) {
  const value = await page.evaluate(({ hostSel }) => {
    const host = document.querySelector(hostSel);
    const root = host && host.shadowRoot;
    if (!root) return "";
    const walk = (node) => {
      let out = "";
      node.childNodes.forEach((child) => {
        if (child.nodeType === 3) out += child.textContent;
        else if (child.nodeType === 1) {
          const el = child;
          if (el.shadowRoot) out += walk(el.shadowRoot);
          else out += walk(el);
        }
      });
      return out;
    };
    return walk(root).replace(/\\s+/g, " ").trim();
  }, { hostSel: HOST });
  return value;
}

async function clickTestId(page, testid) {
  const clicked = await shadowEval(page, `
    const el = root.querySelector('[data-testid="${testid}"]');
    if (!el) return false;
    el.scrollIntoView({ block: 'center', inline: 'center' });
    el.click();
    return true;
  `);
  await sleep(700);
  return clicked;
}

async function clickText(page, needle, selector = "a,button") {
  const clicked = await shadowEval(page, `
    const els = [...root.querySelectorAll('${selector}')];
    const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
    const el = els.find(e => norm(e.textContent) === ${JSON.stringify(needle)})
      || els.find(e => norm(e.textContent).startsWith(${JSON.stringify(needle)}))
      || els.find(e => norm(e.textContent).includes(${JSON.stringify(needle)}));
    if (!el) return false;
    el.scrollIntoView({ block: 'center', inline: 'center' });
    el.click();
    return true;
  `);
  await sleep(700);
  return clicked;
}

async function attrOf(page, testid, attribute) {
  return shadowEval(page, `
    const el = root.querySelector('[data-testid="${testid}"]');
    return el ? el.getAttribute(${JSON.stringify(attribute)}) : null;
  `);
}

async function existsTestId(page, testid) {
  return shadowEval(page, `return Boolean(root.querySelector('[data-testid="${testid}"]'));`);
}

async function itemText(page, testid) {
  return shadowEval(page, `
    const el = root.querySelector('[data-testid="${testid}"]');
    return el ? (el.textContent || '').replace(/\\s+/g, ' ').trim() : '';
  `);
}

/** Geometry + hit-testing of the plan panel's own controls. */
async function planGeometry(page) {
  return shadowEval(page, `
    const panel = root.querySelector('[data-testid="plan-quick-panel"]');
    if (!panel) return { found: false };
    const rect = panel.getBoundingClientRect();
    // Streamlit mounts the shell in a shadow root, so document.elementFromPoint
    // only ever retargets to the host. Descend through every nested shadow root
    // to hit-test the REAL control the operator would press.
    const deepHit = (x, y) => {
      let el = document.elementFromPoint(x, y);
      let guard = 0;
      while (el && el.shadowRoot && guard < 8) {
        const inner = el.shadowRoot.elementFromPoint(x, y);
        if (!inner || inner === el) break;
        el = inner; guard += 1;
      }
      return el;
    };
    const ids = ['plan-panel-close','plan-item-cta-quotation','plan-item-cta-customer_contract','plan-item-cta-customer_advance'];
    const controls = ids.map((id) => {
      const el = root.querySelector('[data-testid="' + id + '"]');
      if (!el) return { id, present: false };
      // Scroll the control into view exactly as the operator would, then measure
      // the position it is actually reachable at.
      el.scrollIntoView({ block: 'center', inline: 'nearest' });
      const r = el.getBoundingClientRect();
      const cx = Math.min(window.innerWidth - 1, Math.max(0, r.left + r.width / 2));
      const cy = Math.min(window.innerHeight - 1, Math.max(0, r.top + r.height / 2));
      const hit = deepHit(cx, cy);
      const inside = hit === el || (hit && el.contains(hit)) || (hit && hit.contains(el));
      return {
        id, present: true, w: Math.round(r.width), h: Math.round(r.height),
        inViewportX: r.left >= -1 && r.right <= window.innerWidth + 1,
        inViewportY: r.top >= -1 && r.bottom <= window.innerHeight + 1,
        hitOk: Boolean(inside),
      };
    });
    return {
      found: true,
      rect: { w: Math.round(rect.width), h: Math.round(rect.height) },
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      controls,
    };
  `);
}

async function openLot(page, lotId) {
  const openedList = await clickText(page, "Lô Hàng", "a");
  if (!openedList) throw new Error("nav 'Lô Hàng' not found");
  // Real list control: the seeded lots predate "tháng này".
  await clickText(page, "Tất cả thời gian", "button");
  const opened = await clickText(page, lotId, "a");
  if (!opened) throw new Error(`lot ${lotId} not clickable in the list`);
  await sleep(1200);
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const puppeteer = loadPuppeteer();
  const browser = await puppeteer.launch({
    executablePath: requireChromium(),
    headless: "shell",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars"],
    env: { ...process.env },
  });

  const results = { url: URL_, lot: LOT, chrome: requireChromium(), viewports: {}, checks: [], errors: [] };
  const pass = (name, extra = {}) => { results.checks.push({ name, ok: true, ...extra }); console.log(`  ✓ ${name}`); };
  const fail = (name, extra = {}) => {
    results.checks.push({ name, ok: false, ...extra });
    console.log(`  ✗ ${name} ${JSON.stringify(extra)}`);
    throw new Error(name);
  };

  try {
    for (const viewport of [{ id: "desktop", width: 1440, height: 900 }, { id: "mobile", width: 390, height: 844 }]) {
      const page = await browser.newPage();
      const pageErrors = [];
      page.on("pageerror", (e) => pageErrors.push(String(e)));
      page.on("console", (m) => {
        if (m.type() === "error" && !/favicon|Failed to load resource|websocket/i.test(m.text())) pageErrors.push(m.text());
      });
      await page.setViewport({ width: viewport.width, height: viewport.height });
      await page.goto(URL_, { waitUntil: "networkidle2", timeout: 120000 });
      await page.waitForSelector(HOST, { timeout: 120000 });
      await sleep(4000);
      console.log(`\n=== ${viewport.id} ${viewport.width}x${viewport.height} ===`);

      await openLot(page, LOT);
      // The shell lives in a shadow root, so the lot identity is read from the
      // rendered component text, not from document.body.
      const openedHeading = await shadowEval(page, `
        const h1 = root.querySelector('h1');
        return h1 ? (h1.textContent || '').trim() : '';
      `);
      if (!openedHeading.includes(LOT)) fail(`${viewport.id}: lot ${LOT} did not open`, { openedHeading });

      // 1 — Node 00 is visible on the Journey, FIRST, before the operational nodes.
      const stepper = await shadowEval(page, `
        return [...root.querySelectorAll('[data-testid^="journey-step-"]')].map(e => e.getAttribute('data-testid'));
      `);
      if (!stepper.length) fail(`${viewport.id}: journey stepper not rendered`);
      if (stepper[0] !== "journey-step-plan") fail(`${viewport.id}: Node 00 is not first`, { stepper });
      const planCard = await itemText(page, "journey-step-plan");
      if (!planCard.toUpperCase().includes("KẾ HOẠCH")) fail(`${viewport.id}: Node 00 label missing`, { planCard });
      if (!planCard.includes("00")) fail(`${viewport.id}: Node 00 is not numbered 00`, { planCard });
      pass(`${viewport.id}: Node 00 KẾ HOẠCH renders first (${stepper.join(" → ")})`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-1-journey-node00.png`, fullPage: false });

      // 2 — click opens the plan panel INSIDE the journey.
      if (!(await clickTestId(page, "journey-step-plan"))) fail(`${viewport.id}: Node 00 not clickable`);
      await sleep(600);
      if (!(await existsTestId(page, "plan-quick-panel"))) fail(`${viewport.id}: plan panel did not open inside the journey`);
      const panelText = await shadowEval(page, `
        const el = root.querySelector('[data-testid="plan-quick-panel"]');
        return el ? (el.textContent || '').replace(/\\s+/g, ' ').trim() : '';
      `);
      pass(`${viewport.id}: plan panel opened inside the Journey`);

      // 3 — Báo giá: the EXACT quote only.
      const quoteRow = await itemText(page, "plan-item-quotation");
      const quoteState = await attrOf(page, "plan-item-quotation", "data-item-state");
      if (!quoteRow.includes("BG-0306")) fail(`${viewport.id}: lot quote missing`, { quoteRow });
      if (quoteRow.includes("BG-9999")) fail(`${viewport.id}: a sibling quote of the same customer leaked`, { quoteRow });
      const quoteHref = await attrOf(page, "plan-item-cta-quotation", "href");
      if (!String(quoteHref || "").startsWith("/kinh-doanh-bao-gia")) {
        fail(`${viewport.id}: "Mở báo giá" must open the EXISTING quote screen`, { quoteHref });
      }
      pass(`${viewport.id}: quote = exact quote_id BG-0306 (state ${quoteState}), CTA ${quoteHref}`);

      // 4 — Hợp đồng: the customer instrument, never signed by inference.
      const contractRow = await itemText(page, "plan-item-customer_contract");
      const signature = await attrOf(page, "plan-item-customer_contract", "data-signature");
      if (!contractRow.includes("HDMB-0306")) fail(`${viewport.id}: customer contract missing`, { contractRow });
      if (contractRow.includes("HDMB-SUB-0306")) fail(`${viewport.id}: TT↔sub-agent contract reported as the customer contract`);
      if (signature !== "UNVERIFIED") fail(`${viewport.id}: signature must stay unverified`, { signature });
      if (contractRow.includes("Đã ký")) fail(`${viewport.id}: "Đã ký" claimed without evidence`, { contractRow });
      const contractHref = await attrOf(page, "plan-item-cta-customer_contract", "href");
      if (!String(contractHref || "").startsWith("/hop-dong")) {
        fail(`${viewport.id}: "Mở hợp đồng" must open the EXISTING contract screen`, { contractHref });
      }
      pass(`${viewport.id}: customer contract HDMB-0306 unsigned (CTA ${contractHref})`);

      // 5 — Tạm ứng: unverified; an unclassified receipt is never money received.
      const advanceRow = await itemText(page, "plan-item-customer_advance");
      const advanceState = await attrOf(page, "plan-item-customer_advance", "data-item-state");
      if (advanceState !== "UNVERIFIED") fail(`${viewport.id}: advance must stay UNVERIFIED`, { advanceState, advanceRow });
      if (!advanceRow.includes("Chưa xác minh đã nhận")) fail(`${viewport.id}: advance label wrong`, { advanceRow });
      if (!advanceRow.includes("cần đối soát")) fail(`${viewport.id}: unclassified receipt not surfaced`, { advanceRow });
      if (/20[.,]?000[.,]?000/.test(panelText)) fail(`${viewport.id}: an unclassified receipt amount rendered`, {});
      if (/đã nhận tiền hàng|đã thanh toán tiền hàng/i.test(panelText)) {
        fail(`${viewport.id}: the panel claims money was received`, {});
      }
      pass(`${viewport.id}: advance "Chưa xác minh đã nhận" + "cần đối soát", no amount`);

      // 6 — next actions answer "đang thiếu gì / cần làm gì tiếp".
      const nextBlock = await itemText(page, "plan-next-actions");
      if (!/chưa có bằng chứng chữ ký|cần đối soát|Chưa xác minh khoản/.test(nextBlock)) {
        fail(`${viewport.id}: next-action block does not answer what is missing`, { nextBlock });
      }
      pass(`${viewport.id}: next actions answered from the same facts`);

      // 7 — geometry: no horizontal overflow, controls reachable and hittable.
      const geometry = await planGeometry(page);
      results.viewports[viewport.id] = geometry;
      if (!geometry.found) fail(`${viewport.id}: plan panel not measurable`);
      if (geometry.horizontalOverflow) fail(`${viewport.id}: horizontal overflow`, geometry);
      for (const control of geometry.controls) {
        if (!control.present) fail(`${viewport.id}: control missing`, { control });
        if (!control.inViewportX || !control.inViewportY) fail(`${viewport.id}: control outside the viewport`, { control });
        if (!control.hitOk) fail(`${viewport.id}: control not hit-testable (covered)`, { control });
      }
      pass(`${viewport.id}: no horizontal overflow; ${geometry.controls.length}/${geometry.controls.length} controls hittable in viewport`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-2-plan-panel.png`, fullPage: false });

      // 8 — closing returns to the SAME lot + node.
      if (!(await clickTestId(page, "plan-panel-close"))) fail(`${viewport.id}: plan panel has no close control`);
      await sleep(500);
      const stillLot = (await shadowText(page)).includes(LOT);
      if (!stillLot) fail(`${viewport.id}: closing the plan left the lot`);
      if (!(await clickTestId(page, "journey-step-plan"))) fail(`${viewport.id}: Node 00 not reachable after returning`);
      if (!(await existsTestId(page, "plan-quick-panel"))) fail(`${viewport.id}: returning did not restore the plan panel`);
      pass(`${viewport.id}: closed and re-opened Node 00 on the same lot`);

      // 9 — the detailed map keeps Node 00 above the first operational node and
      //     keeps the in-map conversation for BOTH nodes (#236 regression).
      await clickTestId(page, "plan-panel-close");
      await clickText(page, "Bản đồ chi tiết", "button");
      await sleep(900);
      const mapInfo = await shadowEval(page, `
        const plan = root.querySelector('[data-testid="journey-node-plan"]');
        const others = [...root.querySelectorAll('[data-testid^="journey-node-"]')]
          .filter(e => !/journey-node-(plan|discussion|number)/.test(e.dataset.testid || ''));
        const op = others[0];
        return {
          hasPlan: Boolean(plan),
          planTop: plan ? Number(String(plan.style.top).replace('px','')) : null,
          opId: op ? op.dataset.testid : null,
          opTop: op ? Number(String(op.style.top).replace('px','')) : null,
          planNumber: (root.querySelector('[data-testid="journey-node-number-plan"]') || {}).textContent || '',
          planTalk: Boolean(root.querySelector('[data-testid="journey-node-discussion-plan"]')),
          opTalk: op ? Boolean(root.querySelector('[data-testid="journey-node-discussion-' + op.dataset.testid.replace('journey-node-','') + '"]')) : false,
        };
      `);
      if (!mapInfo.hasPlan) fail(`${viewport.id}: Node 00 missing on the detailed map`);
      if (!(mapInfo.planTop < mapInfo.opTop)) fail(`${viewport.id}: Node 00 is not above the first operational node`, mapInfo);
      if (mapInfo.planNumber.trim() !== "00") fail(`${viewport.id}: Node 00 map badge is not 00`, mapInfo);
      if (!mapInfo.planTalk) fail(`${viewport.id}: Node 00 lost its in-map conversation`);
      if (!mapInfo.opTalk) fail(`${viewport.id}: an operational node lost its in-map conversation (#236 regression)`, mapInfo);
      pass(`${viewport.id}: map keeps Node 00 above ${mapInfo.opId}, badge 00, conversations intact`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-3-detail-map-node00.png`, fullPage: false });

      // 10 — BLOCKER 3: a BRAND-NEW lot whose operational Journey is empty
      //      (no BOOKING/SI/VGM/transport node) must still expose Node 00.
      //      Same check on desktop and mobile, because the fresh cockpit is a
      //      different surface from the populated map.
      await clickText(page, "Lô Hàng", "a");
      await clickText(page, "Tất cả thời gian", "button");
      if (!(await clickText(page, FRESH_LOT, "a"))) fail(`${viewport.id}: fresh lot ${FRESH_LOT} not clickable`);
      await sleep(1400);
      const freshInfo = await shadowEval(page, `
        const section = root.querySelector('[data-testid="shipment-journey"]');
        const open = root.querySelector('[data-testid="journey-empty-plan-open"]');
        let hitOk = false;
        if (open) {
          const deepHit = (x, y) => {
            let el = document.elementFromPoint(x, y);
            let guard = 0;
            while (el && el.shadowRoot && guard < 8) {
              const inner = el.shadowRoot.elementFromPoint(x, y);
              if (!inner || inner === el) break;
              el = inner; guard += 1;
            }
            return el;
          };
          open.scrollIntoView({ block: 'center', inline: 'center' });
          const r = open.getBoundingClientRect();
          const hit = deepHit(Math.min(window.innerWidth - 1, Math.max(0, r.left + r.width / 2)),
                               Math.min(window.innerHeight - 1, Math.max(0, r.top + r.height / 2)));
          hitOk = Boolean(hit === open || (hit && open.contains(hit)) || (hit && hit.contains(open)));
        }
        return {
          empty: section ? section.getAttribute('data-empty-journey') : null,
          steps: [...root.querySelectorAll('[data-testid^="journey-step-"]')].length,
          planOpen: Boolean(open),
          planOpenText: open ? (open.textContent || '').replace(/\\s+/g, ' ').trim() : '',
          hitOk,
          heading: (root.querySelector('h1') || {}).textContent || '',
          horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        };
      `);
      if (freshInfo.empty !== "true") fail(`${viewport.id}: fresh lot must render the fresh Journey surface`, freshInfo);
      if (freshInfo.steps !== 0) fail(`${viewport.id}: a fresh lot must not invent operational nodes`, freshInfo);
      if (!freshInfo.planOpen) fail(`${viewport.id}: Node 00 missing on the fresh Journey`, freshInfo);
      if (!/KẾ HOẠCH/.test(freshInfo.planOpenText.toUpperCase())) fail(`${viewport.id}: fresh Node 00 label wrong`, freshInfo);
      if (!freshInfo.hitOk) fail(`${viewport.id}: fresh Node 00 is not hit-testable`, freshInfo);
      if (freshInfo.horizontalOverflow) fail(`${viewport.id}: horizontal overflow on the fresh Journey`, freshInfo);
      pass(`${viewport.id}: fresh lot with 0 operational nodes still exposes a hittable Node 00`);

      if (!(await clickTestId(page, "journey-empty-plan-open"))) fail(`${viewport.id}: fresh Node 00 did not open`);
      if (!(await existsTestId(page, "plan-quick-panel"))) fail(`${viewport.id}: fresh Node 00 opened no plan panel`);
      const freshState = await attrOf(page, "plan-quick-panel", "data-plan-state");
      // BLOCKER 1 — linked (SENT) quote never completes the node.
      if (freshState === "COMPLETED") fail(`${viewport.id}: a linked-but-unaccepted quote completed Node 00`, { freshState });
      if (freshState !== "WAITING") fail(`${viewport.id}: fresh lot plan state should wait on acceptance`, { freshState });
      const freshQuote = await itemText(page, "plan-item-quotation");
      if (!freshQuote.includes("Đã gửi khách")) fail(`${viewport.id}: quote status not rendered`, { freshQuote });
      if (/Khách đã chấp nhận/.test(freshQuote)) fail(`${viewport.id}: a SENT quote presented as accepted`, { freshQuote });
      // BLOCKER 2 — customer_confirmation is not a signature.
      const freshSignature = await attrOf(page, "plan-item-customer_contract", "data-signature");
      const freshContract = await itemText(page, "plan-item-customer_contract");
      if (freshSignature !== "UNVERIFIED") fail(`${viewport.id}: customer confirmation became a signature`, { freshSignature });
      if (/Đã ký|Đã có xác nhận ký/.test(freshContract)) fail(`${viewport.id}: signed claim without contract evidence`, { freshContract });
      if (!freshContract.includes("Khách đã xác nhận điều khoản thương mại")) {
        fail(`${viewport.id}: the recorded confirmation is not stated truthfully`, { freshContract });
      }
      if (!freshContract.includes("chưa phải chữ ký hợp đồng")) {
        fail(`${viewport.id}: the confirmation/signature distinction is missing`, { freshContract });
      }
      pass(`${viewport.id}: fresh Node 00 — linked≠accepted (${freshState}), confirmation≠signature`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-9-fresh-journey-node00.png`, fullPage: false });

      // Closing returns to the SAME fresh lot and Node 00 reopens.
      if (!(await clickTestId(page, "plan-panel-close"))) fail(`${viewport.id}: fresh plan panel has no close control`);
      await sleep(500);
      const stillFresh = await shadowEval(page, `
        const h = root.querySelector('h1');
        const open = root.querySelector('[data-testid="journey-empty-plan-open"]');
        return { heading: h ? (h.textContent || '').trim() : '', open: Boolean(open) };
      `);
      if (!stillFresh.heading.includes(FRESH_LOT)) fail(`${viewport.id}: closing the fresh plan left the lot`, stillFresh);
      if (!stillFresh.open) fail(`${viewport.id}: Node 00 not reachable again on the same fresh lot`, stillFresh);
      if (!(await clickTestId(page, "journey-empty-plan-open"))) fail(`${viewport.id}: fresh Node 00 did not reopen`);
      if (!(await existsTestId(page, "plan-quick-panel"))) fail(`${viewport.id}: reopening did not restore the same panel`);
      pass(`${viewport.id}: fresh lot closed and re-opened Node 00 on the same lot`);
      await clickTestId(page, "plan-panel-close");

      // 11 — a lot with no quote / customer-self form, in the SAME session.
      if (viewport.id === "desktop") {
        await clickText(page, "Lô Hàng", "a");
        await clickText(page, "Tất cả thời gian", "button");
        if (!(await clickText(page, "LO-0307", "a"))) fail("LO-0307 not clickable");
        await sleep(1200);
        await clickTestId(page, "journey-step-plan");
        await sleep(500);
        const other = {
          quote: await itemText(page, "plan-item-quotation"),
          advance: await itemText(page, "plan-item-customer_advance"),
        };
        if (!other.quote.includes("Chưa gắn báo giá")) fail("LO-0307 quote state wrong", other);
        if (other.quote.includes("BG-0306")) fail("LO-0307 borrowed LO-0306's quote", other);
        if (!other.advance.includes("Không áp dụng")) fail("CUSTOMER_SELF advance must be NOT_APPLICABLE", other);
        pass("LO-0307 (CUSTOMER_SELF, no quote): 'Chưa gắn báo giá' + 'Không áp dụng'");
        await page.screenshot({ path: `${OUT}/desktop-4-customer-self-lot.png`, fullPage: false });

        await clickText(page, "Lô Hàng", "a");
        await clickText(page, "Tất cả thời gian", "button");
        if (!(await clickText(page, "LO-0308", "a"))) fail("LO-0308 not clickable");
        await sleep(1200);
        await clickTestId(page, "journey-step-plan");
        await sleep(500);
        const unknownAdvance = await itemText(page, "plan-item-customer_advance");
        if (!unknownAdvance.includes("Chưa xác nhận hình thức nhập khẩu")) {
          fail("unconfirmed import form must stay undetermined", { unknownAdvance });
        }
        if (unknownAdvance.includes("Không áp dụng")) fail("unconfirmed import form resolved to N/A", { unknownAdvance });
        pass("LO-0308 (import form not confirmed): advance stays undetermined");
        await page.screenshot({ path: `${OUT}/desktop-5-unknown-flow-lot.png`, fullPage: false });
      }

      results.errors.push(...pageErrors.map((e) => `${viewport.id}: ${e}`));
      if (pageErrors.length) fail(`${viewport.id}: page errors`, { pageErrors });
      await page.close();
    }
  } finally {
    writeFileSync(`${OUT}/staff-plan-results.json`, JSON.stringify(results, null, 1));
    await browser.close();
  }

  console.log("\nISSUE244_STAFF_BROWSER=PASS");
}

main().catch((error) => {
  console.error("\nISSUE244_STAFF_BROWSER=FAIL", error.message);
  process.exit(1);
});
