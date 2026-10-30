/**
 * Issue #244 — real-Chromium QA for Node 00 on the CUSTOMER portal (HEXA/Lục Giác).
 *
 * Drives the REAL Streamlit customer runtime + the REAL portal asset
 * (`assets/customer_portal/hexa-portal.{html,js,css}`) in Chromium at
 * 1440x900 and 390x844 against an isolated, synthetic publication set.
 *
 * What is proven (a screenshot is NOT a pass):
 *   * node 00 exists for the customer, is the FIRST stop, and is numbered 00;
 *   * it offers "Hồ sơ Kế hoạch đã công bố" with exactly the three published
 *     plan kinds (Báo giá / Hợp đồng / Đề nghị thanh toán) and nothing else;
 *   * a PUBLISHED non-plan document (BL) never appears, and the private /
 *     stale / foreign decoys never appear;
 *   * no internal money leaks (costs, margins, INTERNAL amounts, receipt ids);
 *   * a published document never upgrades the node: stage 00 stays UNKNOWN and
 *     "Đã ký"/"đã thanh toán" is only ever asserted inside a negation;
 *   * a published lot with NO plan document says exactly
 *     "Chưa có hồ sơ Kế hoạch được công bố";
 *   * layout: no horizontal overflow, node 00 reachable and hit-testable, the
 *     bubble stays inside the portal on desktop AND mobile.
 *
 * Usage:
 *   node playwright/issue244_plan_customer_qa.mjs \
 *     --url http://127.0.0.1:9502/ --out evidence/issue244-plan \
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

const URL_ = arg("url", "http://127.0.0.1:9502/");
const OUT = resolve(arg("out", "evidence/issue244-plan"));
const HOST = 'div[data-testid="stBidiComponentIsolated"]';
const LOT = arg("lot", "QA-244-LOT");
const EMPTY_LOT = arg("empty-lot", "QA-244-EMPTY");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* The portal is mounted inside Streamlit's shadow root: every query and click
   happens in there, exactly like a real customer's browser. */
const ROOT_HELPERS = `
  const hosts = [...document.querySelectorAll('${HOST}')];
  const host = hosts.find(h => h.shadowRoot && h.shadowRoot.querySelector('.hexa-portal')) || hosts[0];
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
  return page.evaluate((sel) => {
    const hosts = [...document.querySelectorAll(sel)];
    const host = hosts.find((h) => h.shadowRoot && h.shadowRoot.querySelector(".hexa-portal"));
    const root = host && host.shadowRoot;
    const scroller = root && root.querySelector(".hexa-portal");
    if (!scroller) return "";
    const out = [];
    const walk = (node) => {
      if (node.nodeType === 3) { out.push(node.nodeValue); return; }
      if (node.nodeType !== 1) return;
      const tag = node.tagName;
      if (tag === "STYLE" || tag === "SCRIPT") return;
      if (node.classList && node.classList.contains("hidden")) return;
      const cs = getComputedStyle(node);
      if (cs.display === "none" || cs.visibility === "hidden") return;
      node.childNodes.forEach(walk);
    };
    walk(scroller);
    return out.join(" ").replace(/\s+/g, " ").trim();
  }, HOST);
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

async function existsTestId(page, testid) {
  return shadowEval(page, `return Boolean(root.querySelector('[data-testid="${testid}"]'));`);
}

async function itemText(page, testid) {
  return shadowEval(page, `
    const el = root.querySelector('[data-testid="${testid}"]');
    return el ? (el.textContent || '').replace(/\\s+/g, ' ').trim() : '';
  `);
}

/** Node 00 geometry + deep (shadow-piercing) hit-test, as on the staff side. */
async function nodeGeometry(page) {
  return shadowEval(page, `
    const node = root.querySelector('[data-testid="journey-node-plan"]');
    if (!node) return { found: false };
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
    node.scrollIntoView({ block: 'center', inline: 'center' });
    const r = node.getBoundingClientRect();
    const cx = Math.min(window.innerWidth - 1, Math.max(0, r.left + r.width / 2));
    const cy = Math.min(window.innerHeight - 1, Math.max(0, r.top + r.height / 2));
    const hit = deepHit(cx, cy);
    const bubble = root.querySelector('[data-testid="journey-bubble"]');
    const br = bubble ? bubble.getBoundingClientRect() : null;
    const vp = root.querySelector('[data-testid="journey-map-viewport"]');
    const vr = vp ? vp.getBoundingClientRect() : null;
    return {
      found: true,
      w: Math.round(r.width), h: Math.round(r.height),
      inViewportX: r.left >= -1 && r.right <= window.innerWidth + 1,
      hitOk: Boolean(hit === node || (hit && node.contains(hit)) || (hit && hit.contains(node))),
      hitBy: hit ? (hit.dataset && hit.dataset.testid) || hit.className || hit.tagName : null,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      bubble: br ? { w: Math.round(br.width), left: Math.round(br.left), right: Math.round(br.right) } : null,
      bubbleInsidePortal: br ? (br.left >= -1 && br.right <= window.innerWidth + 1) : null,
      mapWidth: vr ? Math.round(vr.width) : null,
    };
  `);
}

async function openLot(page, lotId) {
  if (!(await clickTestId(page, `shipment-row-${lotId}`))) {
    throw new Error(`lot ${lotId} is not listed for this customer`);
  }
  await sleep(1400);
}

/** Labels of the published plan rows, keyed by the allowlisted document kind. */
async function planRows(page) {
  return shadowEval(page, `
    const block = root.querySelector('[data-testid="journey-plan-published"]');
    if (!block) return null;
    return [...block.querySelectorAll('[data-testid^="journey-plan-document-"]')].map((el) => ({
      kind: String(el.dataset.testid || '').replace('journey-plan-document-', ''),
      text: (el.textContent || '').replace(/\\s+/g, ' ').trim(),
    }));
  `);
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

  const results = { url: URL_, lot: LOT, emptyLot: EMPTY_LOT, chrome: requireChromium(), viewports: {}, checks: [], errors: [] };
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
      await sleep(4500);
      console.log(`\n=== ${viewport.id} ${viewport.width}x${viewport.height} ===`);

      // 1 — the customer sees their published lots (and only those).
      if (!(await existsTestId(page, `shipment-row-${LOT}`))) fail(`${viewport.id}: published lot ${LOT} is not listed`);
      if (!(await existsTestId(page, `shipment-row-${EMPTY_LOT}`))) fail(`${viewport.id}: published lot ${EMPTY_LOT} is not listed`);
      const dashText = await shadowText(page);
      if (/MỘT SỐ LÔ CHƯA ĐƯỢC CÔNG BỐ/.test(dashText)) {
        fail(`${viewport.id}: a publication was denied`, { dashText: dashText.slice(0, 300) });
      }
      pass(`${viewport.id}: dashboard lists both published lots, no denial notice`);

      // 2 — node 00 is (still) the FIRST stop, numbered 00.
      await openLot(page, LOT);
      const nodes = await shadowEval(page, `
        const list = [...root.querySelectorAll('[data-testid^="journey-node-"]')]
          .filter(e => !/journey-node-(discussion|number|plan-published)/.test(e.dataset.testid || ''));
        return list.map(e => ({
          id: String(e.dataset.testid || '').replace('journey-node-', ''),
          state: e.getAttribute('data-state'),
          text: (e.textContent || '').replace(/\\s+/g, ' ').trim(),
        }));
      `);
      if (!nodes.length) fail(`${viewport.id}: journey did not render any node`);
      if (nodes[0].id !== "plan") fail(`${viewport.id}: node 00 is not first`, { first: nodes[0] });
      if (!/KẾ HOẠCH/i.test(nodes[0].text)) fail(`${viewport.id}: node 00 label missing`, { first: nodes[0] });
      if (!/^00/.test(nodes[0].text)) fail(`${viewport.id}: node 00 is not numbered 00`, { first: nodes[0] });
      if (nodes[0].state === "COMPLETED") fail(`${viewport.id}: stage 00 must not be COMPLETED`, { first: nodes[0] });
      pass(`${viewport.id}: node 00 KẾ HOẠCH first, numbered 00, state ${nodes[0].state} (not COMPLETED)`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-6-customer-journey-node00.png`, fullPage: false });

      // 3 — open node 00: "Hồ sơ Kế hoạch đã công bố" with the 3 allowlisted kinds only.
      await clickTestId(page, "journey-node-plan");
      if (!(await existsTestId(page, "journey-plan-published"))) {
        fail(`${viewport.id}: node 00 does not show published plan documents`);
      }
      const rows = await planRows(page);
      const kinds = rows.map((r) => r.kind).sort();
      const expected = ["CUSTOMER_CONTRACT", "CUSTOMER_QUOTE", "PAYMENT_REQUEST"].sort();
      if (JSON.stringify(kinds) !== JSON.stringify(expected)) {
        fail(`${viewport.id}: published plan kinds are not exactly the allowlist`, { kinds });
      }
      const labels = rows.map((r) => r.text);
      for (const label of ["Báo giá", "Hợp đồng", "Đề nghị thanh toán"]) {
        if (!labels.some((t) => t.startsWith(label))) fail(`${viewport.id}: label "${label}" missing`, { labels });
      }
      pass(`${viewport.id}: plan rows = Báo giá / Hợp đồng / Đề nghị thanh toán (${kinds.join(", ")})`);
      await page.screenshot({ path: `${OUT}/${viewport.id}-7-customer-plan-published.png`, fullPage: false });

      // 4 — nothing published-but-not-plan, stale, private or foreign leaks.
      const planText = (await itemText(page, "journey-plan-published")) + " " + labels.join(" ");
      for (const forbidden of [
        "QA-244-BL", "Vận đơn", "SECRET_PRIVATE_CONTRACT", "SECRET_DRIVE",
        "QA-244-QUOTE-V1", "QA-244-PRIVATE", "QA-244-STALE", "QA-244-FOREIGN",
        "385.000.000", "192.500.000", "20.000.000", "TT_ENTITLED", "marg",
      ]) {
        if (planText.includes(forbidden)) fail(`${viewport.id}: "${forbidden}" leaked into node 00`, { planText });
      }
      const pageText = await shadowText(page);
      for (const forbidden of ["SECRET_PRIVATE_CONTRACT", "SECRET_DRIVE", "QA-244-FOREIGN", "QA-244-STALE", "QA-244-PRIVATE"]) {
        if (pageText.includes(forbidden)) fail(`${viewport.id}: "${forbidden}" leaked into the portal`, { pageText: pageText.slice(0, 400) });
      }
      pass(`${viewport.id}: no BL / private / stale / foreign / internal-money leak`);

      // 5 — a published document is metadata, never a signature or a payment.
      if (/Đã ký\s*[:：]/.test(planText)) fail(`${viewport.id}: published contract presented as signed`, { planText });
      if (/đã thanh toán(?!\.)/i.test(planText)) fail(`${viewport.id}: payment request presented as paid`, { planText });
      if (!/không chứng minh đã ký hoặc đã thanh toán/i.test(planText)) {
        fail(`${viewport.id}: the metadata disclaimer is missing`, { planText });
      }
      const planStateAfter = await shadowEval(page, `
        const el = root.querySelector('[data-testid="journey-node-plan"]');
        return el ? el.getAttribute('data-state') : null;
      `);
      if (planStateAfter === "COMPLETED") fail(`${viewport.id}: publishing a document completed stage 00`);
      pass(`${viewport.id}: node 00 stays ${planStateAfter}; disclaimer present, no signature/payment claim`);

      const openGeometry = await nodeGeometry(page);
      results.viewports[viewport.id] = { ...(results.viewports[viewport.id] || {}), openBubble: openGeometry.bubble };
      if (openGeometry.horizontalOverflow) fail(`${viewport.id}: horizontal overflow while node 00 is open`, openGeometry);
      if (openGeometry.bubbleInsidePortal === false) {
        fail(`${viewport.id}: node 00 bubble overflows the portal`, openGeometry);
      }
      pass(`${viewport.id}: open node 00 bubble ${openGeometry.bubble?.w}px stays inside the portal (no overflow)`);

      // 6 — layout: with the bubble CLOSED, node 00 must be reachable and
      //     hit-testable (a 390px map legitimately overlays the node once its
      //     own bubble is open, so that state is measured separately below).
      if (!(await clickTestId(page, "journey-bubble-close"))) fail(`${viewport.id}: node 00 bubble has no close control`);
      await sleep(400);
      const closedGeometry = await nodeGeometry(page);
      results.viewports[viewport.id] = { ...closedGeometry };
      if (!closedGeometry.found) fail(`${viewport.id}: node 00 not measurable`);
      if (closedGeometry.horizontalOverflow) fail(`${viewport.id}: horizontal overflow`, closedGeometry);
      if (!closedGeometry.inViewportX) fail(`${viewport.id}: node 00 not inside the viewport`, closedGeometry);
      if (!closedGeometry.hitOk) fail(`${viewport.id}: node 00 not hit-testable`, closedGeometry);
      pass(`${viewport.id}: bubble closed — no horizontal overflow, node 00 hittable (${closedGeometry.w}x${closedGeometry.h})`);

      // 7 — a published lot with NO plan document says so, and shows no non-plan doc.
      if (viewport.id === "desktop") {
        if (!(await clickTestId(page, "btn-back-to-dashboard"))) fail("back-to-dashboard control missing");
        await sleep(900);
        await openLot(page, EMPTY_LOT);
        await clickTestId(page, "journey-node-plan");
        const emptyText = await itemText(page, "journey-plan-published");
        if (!emptyText.includes("Chưa có hồ sơ Kế hoạch được công bố")) {
          fail("empty plan lot must state the explicit empty wording", { emptyText });
        }
        if (await existsTestId(page, "journey-plan-published-empty") === false) {
          fail("empty plan lot must expose journey-plan-published-empty");
        }
        const emptyRows = await planRows(page);
        if (emptyRows.length) fail("empty plan lot rendered plan rows", { emptyRows });
        if (emptyText.includes("Vận đơn") || emptyText.includes("QA-244-BL")) {
          fail("a PUBLISHED non-plan document was shown as plan evidence", { emptyText });
        }
        pass("published lot without plan docs: 'Chưa có hồ sơ Kế hoạch được công bố', BL excluded");
        await page.screenshot({ path: `${OUT}/desktop-8-customer-plan-empty.png`, fullPage: false });
      }

      results.errors.push(...pageErrors.map((e) => `${viewport.id}: ${e}`));
      if (pageErrors.length) fail(`${viewport.id}: page errors`, { pageErrors });
      await page.close();
    }
  } finally {
    writeFileSync(`${OUT}/customer-plan-results.json`, JSON.stringify(results, null, 1));
    await browser.close();
  }

  console.log("\nISSUE244_CUSTOMER_BROWSER=PASS");
}

main().catch((error) => {
  console.error("\nISSUE244_CUSTOMER_BROWSER=FAIL", error.message);
  process.exitCode = 1;
});
