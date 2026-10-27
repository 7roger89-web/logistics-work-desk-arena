/**
 * G1.5 — HEXA customer-portal browser QA against the reference UI.
 *
 * Runs a REAL Chromium against a running Streamlit staging app and records the
 * client-acceptance path:
 *
 *   dashboard (2 lots) → Journey Map per lot → node bubble → readonly modal →
 *   back to map → back to dashboard → zoom in/out/fit → mobile 390x844.
 *
 * It also enforces the hard acceptance rules instead of trusting the render:
 *   * no fabricated figure from HEXA_LucGiac_DEMO.html may appear
 *     (53.400.000 / 30.000.000 / 23.400.000 / 25/10/2026 / ROAD-LG-001 ...);
 *   * every journey node and the open bubble stay inside the map viewport;
 *   * SEA lots never show a ROAD-only stage label;
 *   * exactly 7 stage nodes 00..06 are present.
 *
 * Usage:
 *   node playwright/g15_hexa_portal_qa.mjs \
 *     --url http://127.0.0.1:9501/ --out evidence/g15-hexa-ui/runtime \
 *     --chrome /path/to/chrome [--ld /path/to/libs]
 */
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const URL_ = arg("url", "http://127.0.0.1:9501/");
const OUT = resolve(arg("out", "evidence/g15-hexa-ui/runtime"));
const CHROME = arg("chrome", process.env.CHROME_PATH || "");
const HOST = 'div[data-testid="stBidiComponentIsolated"]';

const FORBIDDEN = [
  "53.400.000", "53400000", "30.000.000", "23.400.000", "42.500.000",
  "25/10/2026", "2026-10-25", "ROAD-LG-001", "ROAD-LG-002",
  "0901 234 567", "29H-886.68", "DEMO-001", "DOC-LG-", "QT-20261022",
];

const checks = [];
function check(name, ok, detail = "") {
  checks.push({ name, ok: Boolean(ok), detail: String(detail).slice(0, 400) });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

/**
 * Resolve puppeteer-core without adding a dependency to the app's package.json.
 * Priority: an explicit --puppeteer-core path, PUPPETEER_CORE_PATH, a normal
 * node_modules install, then this sandbox's disposable QA install.
 */
function loadPuppeteer() {
  const explicit = [
    arg("puppeteer-core", ""),
    process.env.PUPPETEER_CORE_PATH || "",
  ].filter(Boolean);
  for (const candidate of explicit) {
    return require(candidate);
  }
  try {
    return require("puppeteer-core");
  } catch { /* fall through */ }
  const fallback = "/tmp/browsertest/node_modules/puppeteer-core";
  if (existsSync(fallback)) return require(fallback);
  throw new Error(
    "puppeteer-core not found. Run `npm i -D puppeteer-core` or pass --puppeteer-core <path>."
  );
}

function requireChromium() {
  const candidates = [
    CHROME,
    process.env.CHROME_PATH,
    "/tmp/chromium",
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      if (existsSync(candidate)) return candidate;
    } catch { /* try next */ }
  }
  throw new Error("No Chromium binary. Pass --chrome <path> or set CHROME_PATH.");
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function shadowText(page) {
  // Read ONLY what a customer can actually see: ShadowRoot has no innerText,
  // <style> text must not count as content, and hidden subtrees (the closed
  // modal, the unopened utility bubble) must not satisfy an assertion.
  // CSS text-transform is not applied, so assertions stay case-insensitive.
  return page.evaluate((sel) => {
    const host = document.querySelector(sel);
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
    return out.join(" ").replace(/\s+/g, " ");
  }, HOST);
}

async function shadowClick(page, selector) {
  const ok = await page.evaluate(({ sel, target }) => {
    const host = document.querySelector(sel);
    const root = host && host.shadowRoot;
    const el = root && root.querySelector(target);
    if (!el) return false;
    el.click();
    return true;
  }, { sel: HOST, target: selector });
  if (!ok) throw new Error(`element not found in shadow root: ${selector}`);
  await sleep(450);
}

async function containment(page) {
  return page.evaluate((sel) => {
    const host = document.querySelector(sel);
    const root = host && host.shadowRoot;
    if (!root) return { ok: false, reason: "no shadow root" };
    const vp = root.querySelector("#journey-map-viewport");
    if (!vp) return { ok: false, reason: "no viewport" };
    const v = vp.getBoundingClientRect();
    const bad = [];
    root.querySelectorAll(".journey-node").forEach((node) => {
      const r = node.getBoundingClientRect();
      if (r.left < v.left - 1 || r.right > v.right + 1 || r.top < v.top - 1 || r.bottom > v.bottom + 1) {
        bad.push(`node ${node.dataset.testid} outside map`);
      }
    });
    const bubble = root.querySelector('[data-testid="journey-bubble"]');
    if (bubble) {
      const r = bubble.getBoundingClientRect();
      if (r.left < v.left - 1 || r.right > v.right + 1 || r.top < v.top - 1 || r.bottom > v.bottom + 1) {
        bad.push("bubble outside map");
      }
    }
    return {
      ok: bad.length === 0,
      reason: bad.join("; "),
      nodes: root.querySelectorAll(".journey-node").length,
      labels: Array.from(root.querySelectorAll(".journey-node-title")).map((n) => n.textContent),
      states: Array.from(root.querySelectorAll(".journey-node-status")).map((n) => n.textContent),
      zoom: (root.querySelector("#journey-zoom-level") || {}).textContent,
      mapW: Math.round(v.width),
      mapH: Math.round(v.height),
    };
  }, HOST);
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
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const pageErrors = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error" && !/favicon|Failed to load resource/.test(m.text())) {
      pageErrors.push(m.text());
    }
  });

  try {
    await page.goto(URL_, { waitUntil: "networkidle2", timeout: 90000 });
    await page.waitForSelector(HOST, { timeout: 60000 });
    await sleep(3500);

    /* ---------------------------------------------------- desktop dashboard */
    let text = await shadowText(page);
    await page.screenshot({ path: `${OUT}/10-desktop-dashboard.png` });
    check("desktop: two published lots listed", (text.match(/G1-LG-00\d/g) || []).length >= 2);
    check("desktop: 8 dashboard column headers", (text.match(/Hàng hóa & Tuyến|Phương thức|Chặng xác minh|ETA được xác minh|Công nợ|Cập nhật cuối|Hành trình/gi) || []).length >= 7);
    check("desktop: unknown debt is explicit", /UNKNOWN \/ Chưa đối soát/i.test(text));
    check("desktop: no fabricated demo figure", !FORBIDDEN.some((f) => text.includes(f)),
      FORBIDDEN.filter((f) => text.includes(f)).join(","));

    /* ------------------------------------------------------ lot 1 → journey */
    await shadowClick(page, "#dash-shipments-tbody tr:nth-child(1)");
    await sleep(700);
    text = await shadowText(page);
    let c = await containment(page);
    await page.screenshot({ path: `${OUT}/11-desktop-journey-road.png` });
    check("journey: 7 stage nodes 00..06", c.nodes === 7, `nodes=${c.nodes}`);
    check("journey: ROAD stage labels match reference", JSON.stringify(c.labels.slice(0, 7)) ===
      JSON.stringify(["KẾ HOẠCH", "LẤY HÀNG", "NHẬN & GHÉP", "VẬN CHUYỂN", "THÔNG QUAN", "GIAO HÀNG", "THANH TOÁN"]),
      JSON.stringify(c.labels));
    check("journey: nodes contained in map viewport", c.ok, c.reason);
    check("journey: node states use only approved labels", c.states.every((s) => /CHƯA ĐỐI SOÁT|CÓ BẰNG CHỨNG|ĐANG XỬ LÝ|CHỜ THÔNG TIN/.test(s)),
      c.states.join("|"));

    /* ----------------------------------------------------------- node bubble */
    await shadowClick(page, '[data-testid="journey-node-transit"]');
    c = await containment(page);
    text = await shadowText(page);
    await page.screenshot({ path: `${OUT}/12-desktop-node-bubble.png` });
    check("bubble: opens for clicked node", /Vận chuyển/i.test(text) && /Chưa đối soát/i.test(text));
    check("bubble: contained in map viewport", c.ok, c.reason);
    check("bubble: no approved documents claims none", /Không có dữ liệu được duyệt/.test(text));

    /* --------------------------------------------------------- readonly modal */
    await shadowClick(page, '[data-testid="journey-open-workspace"]');
    text = await shadowText(page);
    await page.screenshot({ path: `${OUT}/13-desktop-readonly-modal.png` });
    check("modal: readonly detail sections present",
      /Hồ sơ & chứng từ/i.test(text) && /Báo giá bán/i.test(text) && /Công nợ dịch vụ/i.test(text));
    check("modal: no download button for unpublished docs", !/Tải PDF|Tải tệp|Tải xuống/.test(text));
    check("modal: no fake comment/upload form", (await page.evaluate((sel) => {
      const r = document.querySelector(sel).shadowRoot;
      return !!r.querySelector('input[type="file"], #stage-comment-input');
    }, HOST)) === false);

    /* ------------------------------------------------- back to map + dashboard */
    await shadowClick(page, '[data-testid="modal-back-to-map"]');
    text = await shadowText(page);
    check("modal: back to map keeps bubble", /Vận chuyển/i.test(text) && !/Chi tiết công đoạn ·/i.test(text));
    await shadowClick(page, "#btn-back-to-dashboard");
    text = await shadowText(page);
    await page.screenshot({ path: `${OUT}/14-desktop-back-to-dashboard.png` });
    check("back: dashboard restored with both lots", /G1-LG-001/.test(text) && /G1-LG-002/.test(text));

    /* --------------------------------------------------------- lot 2 SEA view */
    await shadowClick(page, "#dash-shipments-tbody tr:nth-child(2)");
    await sleep(700);
    c = await containment(page);
    text = await shadowText(page);
    await page.screenshot({ path: `${OUT}/15-desktop-journey-sea.png` });
    check("SEA: sea-specific stage label, never ROAD wording", c.labels.includes("VẬN TẢI BIỂN"), JSON.stringify(c.labels));
    check("SEA: no ROAD consolidation label", !c.labels.includes("NHẬN & GHÉP"));

    /* ------------------------------------------------------------------ zoom */
    const zoomBefore = (await containment(page)).zoom;
    await shadowClick(page, '[data-testid="journey-zoom-in"]');
    const zoomIn = (await containment(page)).zoom;
    await shadowClick(page, '[data-testid="journey-zoom-out"]');
    await shadowClick(page, '[data-testid="journey-zoom-out"]');
    const zoomOut = (await containment(page)).zoom;
    await shadowClick(page, '[data-testid="journey-zoom-fit"]');
    const zoomFit = (await containment(page)).zoom;
    c = await containment(page);
    await page.screenshot({ path: `${OUT}/16-desktop-zoom-fit.png` });
    check("zoom: in increases scale", parseInt(zoomIn) > parseInt(zoomBefore), `${zoomBefore}→${zoomIn}`);
    check("zoom: out decreases scale", parseInt(zoomOut) < parseInt(zoomIn), `${zoomIn}→${zoomOut}`);
    check("zoom: fit re-centres inside map", c.ok, `${zoomFit} ${c.reason}`);

    /* ------------------------------------------------------------------ mobile */
    await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await page.reload({ waitUntil: "networkidle2" });
    await page.waitForSelector(HOST, { timeout: 60000 });
    await sleep(3500);
    text = await shadowText(page);
    const cards = await page.evaluate((sel) => {
      const r = document.querySelector(sel).shadowRoot;
      return {
        cards: r.querySelectorAll(".shipment-card-mobile").length,
        tableVisible: !!(r.querySelector(".dash-table-desktop") || {}).offsetParent,
      };
    }, HOST);
    await page.screenshot({ path: `${OUT}/20-mobile-dashboard.png`, fullPage: true });
    check("mobile: card layout replaces the 8-column table", cards.cards >= 2 && cards.tableVisible === false,
      JSON.stringify(cards));

    await shadowClick(page, '[data-testid="shipment-card-G1-LG-001"]');
    await sleep(800);
    c = await containment(page);
    await page
      .evaluate(() => {
        const main = document.querySelector('main[data-testid="stMain"]');
        const host = document.querySelector('div[data-testid="stBidiComponentIsolated"]');
        const r = host.shadowRoot.querySelector("#journey-map-viewport").getBoundingClientRect();
        if (main) main.scrollTop = main.scrollTop + r.top - 12;
      });
    await sleep(500);
    await page.screenshot({ path: `${OUT}/21-mobile-journey.png` });
    check("mobile: journey map renders 7 nodes", c.nodes === 7);
    check("mobile: nodes contained at 390px", c.ok, c.reason);

    await shadowClick(page, '[data-testid="journey-node-customs"]');
    c = await containment(page);
    await page.screenshot({ path: `${OUT}/22-mobile-bubble.png` });
    check("mobile: bubble contained, no clipping", c.ok, c.reason);

    await page.screenshot({ path: `${OUT}/23-mobile-fullpage.png`, fullPage: true });

    check("runtime: no uncaught page errors", pageErrors.length === 0, pageErrors.slice(0, 3).join(" | "));
  } finally {
    await browser.close();
  }

  const failed = checks.filter((x) => !x.ok);
  writeFileSync(`${OUT}/qa-report.json`, JSON.stringify({
    url: URL_,
    generated_at: new Date().toISOString(),
    checks,
    passed: checks.length - failed.length,
    failed: failed.length,
    verdict: failed.length === 0 ? "VISUAL_PASS" : "VISUAL_FAIL",
  }, null, 2));
  console.log(`\n${checks.length - failed.length}/${checks.length} checks passed → ${failed.length === 0 ? "VISUAL_PASS" : "VISUAL_FAIL"}`);
  process.exitCode = failed.length === 0 ? 0 : 1;
}

await main();
