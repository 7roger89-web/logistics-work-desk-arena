/** Issue #247 S3 — real Chromium A ↔ B customer tenant boundary.
 *
 * One Streamlit process, one in-process mongomock TEST database, TWO customers
 * with their OWN published releases. The browser is the real Chromium 153 that
 * `evidence/arena-tooling-20261030/README.md` provisioned; nothing here is a
 * jsdom/component mock.
 *
 * Per viewport (1440x900 and 390x844) the runner:
 *   1. opens the portal as granted customer A, asserts A's own published lot,
 *      opens the Journey Map pickup node, leaves an unsent draft, opens the
 *      read-only document modal;
 *   2. switches to granted customer B in the SAME page/session and asserts B's
 *      own published lot + B's own approved event, and that A's lot, A's event,
 *      A's documents, A's publication version, A's open bubble and A's draft are
 *      all gone from the shadow DOM (text AND form values);
 *   3. switches back to A and proves the isolation is symmetric;
 *   4. reloads the page (fresh Streamlit session) and repeats B isolation;
 *   5. selects the ungranted verified email and asserts the server refused it.
 *
 * Exit 0 only when every positive and negative assertion passes on BOTH
 * viewports. Server-side truth is read from the same-process evidence files the
 * fixture writes (S3_EVIDENCE_DIR), never constructed by this script.
 *
 * Usage (repo root):
 *   LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp node playwright/issue247_s3_browser.mjs \
 *     --url http://127.0.0.1:9503/ --out evidence/issue247/s3 \
 *     --chrome /tmp/chromium --puppeteer-core /tmp/pw-cli/node_modules/puppeteer-core
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);
const arg = (name, fallback = "") => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : fallback;
};
const OUT = resolve(arg("out", "evidence/issue247/s3"));
const URL_ = arg("url", "http://127.0.0.1:9503/");
const CHROME = arg("chrome", "/tmp/chromium");
const HOST = 'div[data-testid="stBidiComponentIsolated"]';

const LOT_A = "QA-LOT";
const LOT_B = "QA-FOREIGN";
const TITLE_A = "QA-A Đã lấy hàng tại kho Lục Giác";
const TITLE_B = "QA-B Đã lấy hàng tại kho khác";
const DOC_A = "QA-DOC-PL-A";
const DOC_TITLE_A = "QA-A Packing list";
const DOC_B = ["QA-OTHER-DOC-BL", "QA-OTHER-DOC-POD"];
const DOC_B_TITLE = "QA-B Bill of lading";
const DOC_B_TITLE_2 = "QA-B Biên bản giao hàng";
const DRAFT_MARKER = "S3-DRAFT-A-DO-NOT-LEAK";
const ROLE_A = "Lục Giác";
const ROLE_B = "Khách khác";
const ROLE_DENIED = "Khách chưa được cấp quyền";
const DENIED_TEXT = "Tài khoản này chưa được cấp quyền xem dữ liệu";

if (!existsSync(CHROME)) throw new Error(`real Chromium binary required at ${CHROME}`);
const puppeteer = require(arg("puppeteer-core", "puppeteer-core"));
mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const readJson = (name) => JSON.parse(readFileSync(resolve(OUT, name), "utf8"));
const save = (name, value) =>
  writeFileSync(resolve(OUT, name), JSON.stringify(value, null, 2) + "\n");

const checks = [];
const pageErrors = [];
const consoleErrors = [];
function check(name, condition, detail = "") {
  const record = { name, pass: !!condition, detail: String(detail) };
  checks.push(record);
  console.log(`${condition ? "PASS" : "FAIL"} ${name}${detail ? " :: " + detail : ""}`);
  if (!condition) throw new Error(`ASSERTION FAILED: ${name} ${detail}`);
}
async function until(fn, label, timeout = 60000) {
  const end = Date.now() + timeout;
  let last;
  while (Date.now() < end) {
    try {
      const value = await fn();
      if (value) return value;
      last = value;
    } catch (error) {
      last = String(error);
    }
    await sleep(150);
  }
  throw new Error(`Timed out: ${label}; last=${JSON.stringify(last)}`);
}

function viewportPlan() {
  return [
    { id: "desktop", width: 1440, height: 900 },
    { id: "mobile", width: 390, height: 844 },
  ];
}

const shadowEval = (page, code) =>
  page.evaluate((body) => {
    const root = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
    if (!root) return null;
    return new Function("root", body)(root);
  }, code);

const shadowText = async (page) => {
  const text = await page.evaluate(() => {
    const root = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
    return root ? root.textContent || "" : "";
  });
  return String(text).replace(/\s+/g, " ");
};

const pageText = async (page) =>
  String(await page.evaluate(() => document.body.innerText)).replace(/\s+/g, " ");

async function pickRole(page, label) {
  const clicked = await page.evaluate((text) => {
    const labels = [...document.querySelectorAll('[data-testid="stRadio"] label')];
    const hit = labels.find((el) => el.textContent.replace(/\s+/g, " ").trim() === text);
    if (!hit) return false;
    hit.click();
    return true;
  }, label);
  if (!clicked) throw new Error(`QA identity radio option not found: ${label}`);
  await sleep(400);
}

const waitShadow = (page, predicate, label, timeout = 60000) =>
  until(async () => {
    const text = await shadowText(page);
    return predicate(text) ? text : null;
  }, label, timeout);

async function clickShadow(page, selector, label) {
  const handle = await until(async () => {
    const found = await page.evaluateHandle((hostSel, sel) => {
      const root = document.querySelector(hostSel)?.shadowRoot;
      if (!root) return null;
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && cs.display !== "none" && cs.visibility !== "hidden";
      };
      const node = [...root.querySelectorAll(sel)].find(visible);
      return node || null;
    }, HOST, selector);
    return found.asElement() ? found : (await found.dispose(), null);
  }, `click ${selector} (${label})`);
  await page.evaluate((el) => el.scrollIntoView({ block: "center", inline: "nearest" }), handle);
  await sleep(120);
  const hit = await page.evaluate((el) => {
    const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2;
    const y = r.top + r.height / 2;
    const root = el.getRootNode();
    const target = (root.elementFromPoint ? root : document).elementFromPoint(x, y);
    return { ok: !!target && (target === el || el.contains(target)), w: Math.round(r.width), h: Math.round(r.height) };
  }, handle);
  const box = await handle.boundingBox();
  if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  else await page.evaluate((el) => el.click(), handle);
  await handle.dispose();
  return hit;
}

async function geometry(page) {
  return page.evaluate(() => {
    const root = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
    const target = root ? root.querySelector("#customer-portal-root") || root.firstElementChild : null;
    const docOverflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
    const shadowOverflow = target ? target.scrollWidth - target.clientWidth : null;
    return {
      viewport: [window.innerWidth, window.innerHeight],
      documentHorizontalOverflow: docOverflow > 1,
      documentScrollWidth: document.documentElement.scrollWidth,
      shadowHorizontalOverflow: shadowOverflow !== null ? shadowOverflow > 1 : null,
      shadowScrollWidth: target ? target.scrollWidth : null,
      shadowClientWidth: target ? target.clientWidth : null,
    };
  });
}

async function formValues(page) {
  return page.evaluate(() => {
    const root = document.querySelector('div[data-testid="stBidiComponentIsolated"]')?.shadowRoot;
    if (!root) return [];
    return [...root.querySelectorAll("input, textarea")]
      .filter((el) => el.type !== "file")
      .map((el) => String(el.value || ""));
  });
}

async function lotMarkers(page) {
  return shadowEval(page, `return {
    rows: [...root.querySelectorAll('[data-testid^="shipment-row-"]')].map((e) => e.dataset.testid),
    cards: [...root.querySelectorAll('[data-testid^="shipment-card-"]')].map((e) => e.dataset.testid),
    toolbarId: (root.querySelector('#toolbar-id') || {}).textContent || '',
    docCount: (root.querySelector('#utility-doc-count') || {}).textContent || '',
    nodes: [...root.querySelectorAll('[data-testid^="journey-node-"]')]
      .filter((e) => /^journey-node-(plan|pickup|consolidate|transit|customs|delivery|finance)$/.test(e.dataset.testid || ''))
      .map((e) => ({ id: e.dataset.testid, state: e.getAttribute('data-state') })),
    bubble: (root.querySelector('[data-testid="journey-bubble"]') || {}).textContent || '',
    bubbleOpen: !!root.querySelector('[data-testid="journey-bubble"]'),
    modalClass: (root.querySelector('#journey-modal-layer') || {}).className || '',
    modalText: (root.querySelector('#journey-modal-body') || {}).textContent || '',
  };`);
}

/** Open the read-only modal and keep it open across a late Streamlit rerun.
 * A Journey-Map rerun (discussion delivery) legitimately re-renders the map and
 * closes the modal, so opening it is retried and the settled state is asserted.
 */
async function waitReadonlyModal(page, tag) {
  const deadline = Date.now() + 40000;
  while (Date.now() < deadline) {
    let state = await lotMarkers(page);
    if (/hidden/.test(state.modalClass) || !state.modalText.trim()) {
      await shadowEval(page, `const b = root.querySelector('[data-testid="journey-open-workspace"]'); if (b) b.click(); return !!b;`);
      await sleep(700);
      state = await lotMarkers(page);
    }
    if (!/hidden/.test(state.modalClass) && state.modalText.trim()) {
      await sleep(1500);
      const settled = await lotMarkers(page);
      if (!/hidden/.test(settled.modalClass) && settled.modalText.trim()) return settled;
    }
    await sleep(250);
  }
  throw new Error(`${tag}: read-only modal did not stay open`);
}

async function closeReadonlyModal(page) {
  await shadowEval(page,
    `const b = root.querySelector('[data-testid="modal-back-to-map"]') || root.querySelector('#journey-modal-close'); if (b) b.click(); return !!b;`);
  await sleep(700);
}

function assertIsolation(label, text, values, ui, { own, foreign }) {
  check(`${label} · own lot rendered`, text.includes(own.lot), own.lot);
  check(`${label} · own approved event rendered`, text.includes(own.title), own.title);
  check(`${label} · foreign lot absent`, !text.includes(foreign.lot), foreign.lot);
  check(`${label} · foreign event absent`, !text.includes(foreign.title), foreign.title);
  check(`${label} · foreign document absent`, !text.includes(foreign.docTitle), foreign.docTitle);
  check(`${label} · foreign document id absent`, !text.includes(foreign.docId), foreign.docId);
  check(`${label} · foreign publication version absent`, !text.includes(foreign.displayVersion), foreign.displayVersion);
  check(`${label} · foreign approved hash absent`, !text.includes(foreign.sha256), "sha256");
  check(
    `${label} · no leftover form value`,
    values.every((value) => !value.includes(DRAFT_MARKER) && !value.includes(foreign.lot)),
    JSON.stringify(values),
  );
  check(`${label} · internal markers absent`, !/SECRET_|987654321|123456789/.test(text), "SECRET_/cost");
  check(
    `${label} · own dashboard reference present`,
    ui.rows.includes(`shipment-row-${own.lot}`) || ui.cards.includes(`shipment-card-${own.lot}`),
    JSON.stringify({ rows: ui.rows, cards: ui.cards }),
  );
  check(
    `${label} · foreign dashboard reference absent`,
    !ui.rows.includes(`shipment-row-${foreign.lot}`) && !ui.cards.includes(`shipment-card-${foreign.lot}`),
    JSON.stringify({ rows: ui.rows, cards: ui.cards }),
  );
}

async function runViewport(page, viewport) {
  const errorsBefore = pageErrors.length;
  const tag = viewport.id;
  await page.setViewport({ width: viewport.width, height: viewport.height });
  await page.goto(URL_, { waitUntil: "networkidle2" });
  await page.waitForSelector('[data-testid="stRadio"]', { timeout: 60000 });
  await waitShadow(page, (t) => t.includes("HEXA"), `${tag} portal mounted`);
  // The fixture writes its same-process readback when the first session boots.
  const server = await until(async () => {
    try {
      return serverFacts();
    } catch (error) {
      return null;
    }
  }, `${tag} server evidence files`);

  // ---- A: default granted identity, own published lot ------------------- //
  let text = await waitShadow(page, (t) => t.includes(LOT_A), `${tag} A lot`);
  await sleep(1500);
  let ui = await lotMarkers(page);
  let values = await formValues(page);
  const accountA = await pageText(page);
  check(`${tag} A account label`, /l\*\*\*@example\.test/.test(accountA), "l***@example.test");
  assertIsolation(`${tag} A`, text, values, ui,
    {
      own: { lot: LOT_A, title: TITLE_A, docTitle: DOC_TITLE_A, docId: DOC_A },
      foreign: {
        lot: LOT_B, title: TITLE_B, docTitle: DOC_B_TITLE, docId: DOC_B[0],
        displayVersion: server.b.displayVersion, sha256: server.b.sha256,
      },
    });
  check(`${tag} A pickup completed`, ui.nodes.some((n) => n.id === "journey-node-pickup" && n.state === "COMPLETED"),
    JSON.stringify(ui.nodes));
  check(`${tag} A own document count`, ui.docCount.trim() === "1 tệp", ui.docCount);
  let geo = await geometry(page);
  check(`${tag} A no horizontal overflow`, !geo.documentHorizontalOverflow && geo.shadowHorizontalOverflow !== true,
    JSON.stringify(geo));
  await page.screenshot({ path: resolve(OUT, `${tag}-1-A-journey.png`), fullPage: false });

  // ---- A: open pickup bubble, leave a draft, open the document modal ---- //
  const nodeHit = await clickShadow(page, '[data-testid="journey-node-pickup"]', `${tag} A pickup`);
  check(`${tag} A pickup node is a real hit target`, nodeHit.ok && nodeHit.w >= 40 && nodeHit.h >= 24, JSON.stringify(nodeHit));
  await waitShadow(page, (t) => t.includes(TITLE_A), `${tag} A bubble`);
  const composer = await until(async () => {
    const ready = await shadowEval(page,
      `const ta = root.querySelector('[data-testid="journey-discussion-body"]'); return ta ? ta.placeholder : null;`);
    return ready || null;
  }, `${tag} A composer`);
  check(`${tag} A composer is the node conversation`, String(composer).includes("Viết"), String(composer));
  await shadowEval(page, `root.querySelector('[data-testid="journey-discussion-body"]').focus(); return 1;`);
  await page.keyboard.type(DRAFT_MARKER, { delay: 12 });
  const draftValue = await shadowEval(page,
    `return root.querySelector('[data-testid="journey-discussion-body"]').value;`);
  check(`${tag} A draft typed locally`, draftValue === DRAFT_MARKER, String(draftValue));
  await page.screenshot({ path: resolve(OUT, `${tag}-2-A-bubble-draft.png`), fullPage: false });

  await sleep(1800);
  const modalHit = await clickShadow(page, '[data-testid="journey-open-workspace"]', `${tag} A modal`);
  let modalText = (await waitReadonlyModal(page, `${tag} A`)).modalText;
  check(`${tag} A modal shows own document`, modalText.includes(DOC_TITLE_A), DOC_TITLE_A);
  check(`${tag} A modal shows own publication version`, modalText.includes(server.a.displayVersion),
    server.a.displayVersion);
  check(`${tag} A modal hides foreign document`, !modalText.includes(DOC_B_TITLE), DOC_B_TITLE);
  check(`${tag} A modal hit target`, modalHit.ok, JSON.stringify(modalHit));
  await page.screenshot({ path: resolve(OUT, `${tag}-3-A-modal.png`), fullPage: false });
  await closeReadonlyModal(page);

  // ---- B: SAME page/session, granted customer with its own release ------ //
  await pickRole(page, ROLE_B);
  text = await waitShadow(page, (t) => t.includes(LOT_B) && t.includes(TITLE_B), `${tag} B lot`);
  await sleep(1500);
  ui = await lotMarkers(page);
  values = await formValues(page);
  const accountB = await pageText(page);
  check(`${tag} B account label`, /ot\*\*\*@example\.test/.test(accountB), "ot***@example.test");
  check(`${tag} B is a positive control (own publication)`, text.includes(LOT_B) && text.includes(TITLE_B),
    `${LOT_B}/${TITLE_B}`);
  assertIsolation(`${tag} B`, text, values, ui,
    {
      own: { lot: LOT_B, title: TITLE_B, docTitle: DOC_B_TITLE, docId: DOC_B[0] },
      foreign: {
        lot: LOT_A, title: TITLE_A, docTitle: DOC_TITLE_A, docId: DOC_A,
        displayVersion: server.a.displayVersion, sha256: server.a.sha256,
      },
    });
  check(`${tag} B carry-over bubble closed`, ui.bubbleOpen === false, String(ui.bubbleOpen));
  check(`${tag} B carry-over modal closed`, /hidden/.test(ui.modalClass) && ui.modalText.trim() === "",
    JSON.stringify({ modalClass: ui.modalClass, modalText: ui.modalText.slice(0, 40) }));
  check(`${tag} B toolbar is B's own lot`, ui.toolbarId.trim() === LOT_B, ui.toolbarId);
  check(`${tag} B own document count`, ui.docCount.trim() === "2 tệp", ui.docCount);
  check(`${tag} B pickup completed from B's own event`,
    ui.nodes.some((n) => n.id === "journey-node-pickup" && n.state === "COMPLETED"), JSON.stringify(ui.nodes));
  geo = await geometry(page);
  check(`${tag} B no horizontal overflow`, !geo.documentHorizontalOverflow && geo.shadowHorizontalOverflow !== true,
    JSON.stringify(geo));
  await page.screenshot({ path: resolve(OUT, `${tag}-4-B-journey.png`), fullPage: false });

  await clickShadow(page, '[data-testid="journey-node-pickup"]', `${tag} B pickup`);
  const bBubble = await until(async () => {
    const state = await lotMarkers(page);
    return state.bubbleOpen ? state : null;
  }, `${tag} B bubble`);
  check(`${tag} B bubble carries B's approved event`, bBubble.bubble.includes(TITLE_B), TITLE_B.slice(0, 20));
  check(`${tag} B bubble hides A's event`, !bBubble.bubble.includes(TITLE_A), TITLE_A);
  await sleep(1800);
  await clickShadow(page, '[data-testid="journey-open-workspace"]', `${tag} B modal`);
  const bModal = await waitReadonlyModal(page, `${tag} B`);
  check(`${tag} B modal shows own documents`,
    bModal.modalText.includes(DOC_B_TITLE) && bModal.modalText.includes(DOC_B_TITLE_2),
    "B documents");
  check(`${tag} B modal shows own publication version`, bModal.modalText.includes(server.b.displayVersion),
    server.b.displayVersion);
  check(`${tag} B modal hides A's document and version`,
    !bModal.modalText.includes(DOC_TITLE_A) && !bModal.modalText.includes(server.a.displayVersion),
    "A metadata");
  await page.screenshot({ path: resolve(OUT, `${tag}-5-B-modal.png`), fullPage: false });
  await closeReadonlyModal(page);

  // ---- back to A: symmetric isolation ---------------------------------- //
  await pickRole(page, ROLE_A);
  text = await waitShadow(page, (t) => t.includes(LOT_A) && !t.includes(LOT_B), `${tag} A again`);
  await sleep(1500);
  ui = await lotMarkers(page);
  values = await formValues(page);
  assertIsolation(`${tag} A-again`, text, values, ui,
    {
      own: { lot: LOT_A, title: TITLE_A, docTitle: DOC_TITLE_A, docId: DOC_A },
      foreign: {
        lot: LOT_B, title: TITLE_B, docTitle: DOC_B_TITLE, docId: DOC_B[0],
        displayVersion: server.b.displayVersion, sha256: server.b.sha256,
      },
    });
  await clickShadow(page, '[data-testid="journey-node-pickup"]', `${tag} A-again pickup`);
  const aAgain = await until(async () => {
    const state = await lotMarkers(page);
    return state.bubbleOpen ? state : null;
  }, `${tag} A-again bubble`);
  check(`${tag} A-again bubble shows A's own event`, aAgain.bubble.includes(TITLE_A), TITLE_A.slice(0, 20));
  check(`${tag} A-again bubble hides B's event`, !aAgain.bubble.includes(TITLE_B), TITLE_B);
  await page.screenshot({ path: resolve(OUT, `${tag}-6-A-again.png`), fullPage: false });

  // ---- reload: fresh Streamlit session, repeat B isolation ------------- //
  await page.reload({ waitUntil: "networkidle2" });
  await page.waitForSelector('[data-testid="stRadio"]', { timeout: 60000 });
  text = await waitShadow(page, (t) => t.includes(LOT_A), `${tag} reload A`);
  check(`${tag} reload starts at granted A`, text.includes(LOT_A) && !text.includes(LOT_B), LOT_A);
  await pickRole(page, ROLE_B);
  text = await waitShadow(page, (t) => t.includes(LOT_B) && t.includes(TITLE_B), `${tag} reload B`);
  await sleep(1500);
  ui = await lotMarkers(page);
  values = await formValues(page);
  assertIsolation(`${tag} B-after-reload`, text, values, ui,
    {
      own: { lot: LOT_B, title: TITLE_B, docTitle: DOC_B_TITLE, docId: DOC_B[0] },
      foreign: {
        lot: LOT_A, title: TITLE_A, docTitle: DOC_TITLE_A, docId: DOC_A,
        displayVersion: server.a.displayVersion, sha256: server.a.sha256,
      },
    });
  check(`${tag} reload B has B's own document count`, ui.docCount.trim() === "2 tệp", ui.docCount);
  await page.screenshot({ path: resolve(OUT, `${tag}-7-B-after-reload.png`), fullPage: false });

  // ---- ungranted verified email: server refusal, no data -------------- //
  await pickRole(page, ROLE_DENIED);
  const deniedPage = await until(async () => {
    const body = await pageText(page);
    return body.includes(DENIED_TEXT) ? body : null;
  }, `${tag} denied screen`);
  check(`${tag} denied identity message`, deniedPage.includes(DENIED_TEXT), DENIED_TEXT);
  const deniedShadow = await shadowText(page);
  check(`${tag} denied screen exposes no lot`,
    !deniedShadow.includes(LOT_A) && !deniedShadow.includes(LOT_B) && !deniedShadow.includes(TITLE_A)
      && !deniedShadow.includes(TITLE_B),
    deniedShadow.slice(0, 60));
  check(`${tag} denied screen has no portal account label`,
    !deniedPage.includes("l***@example.test") && !deniedPage.includes("ot***@example.test"),
    "account label");
  await page.screenshot({ path: resolve(OUT, `${tag}-8-denied.png`), fullPage: false });

  check(`${tag} no page errors`, pageErrors.length === errorsBefore,
    JSON.stringify(pageErrors.slice(errorsBefore)));
}

// The B document title used in DOM text assertions (first published document).

function serverFacts({ requireDeniedView = false } = {}) {
  const db = readJson("server-db.json");
  const publications = readJson("server-publications.json");
  const readback = readJson("server-readback.json");
  const negative = readJson("server-negative.json");
  let deniedView = null;
  try {
    deniedView = readJson("server-denied-view.json");
  } catch (error) {
    if (requireDeniedView) throw error;
  }
  const a = publications.a;
  const b = publications.b;
  return {
    db,
    publications,
    readback,
    negative,
    deniedView,
    a: {
      version: a.manifest_version,
      displayVersion: a.manifest_version.slice(0, 20),
      sha256: a.approved_content_sha256,
      pointer: a.pointer_version,
    },
    b: {
      version: b.manifest_version,
      displayVersion: b.manifest_version.slice(0, 20),
      sha256: b.approved_content_sha256,
      pointer: b.pointer_version,
    },
  };
}

function checkServerEvidence(server) {
  const { db, publications, readback, negative, deniedView } = server;
  check("server: one in-process mongomock TEST database",
    db.database === "logistics_staging" && String(db.client_module).startsWith("mongomock")
      && db.mongo_uri_env === "" && db.transport === "SANDBOX_STAGING"
      && db.env_identity === "PREVIEW",
    JSON.stringify({ database: db.database, module: db.client_module, uri: db.mongo_uri_env }));
  const pid = db.pid;
  check("server: same process for DB, publications and both readbacks",
    publications.pid === pid
      && readback.pid === pid
      && readback.roles.a?.pid === pid
      && readback.roles.b?.pid === pid,
    JSON.stringify({ pid, pids: [publications.pid, readback.pid,
      readback.roles.a?.pid, readback.roles.b?.pid] }));

  check("server: A and B have independent PUBLISHED manifests",
    publications.a.state === "PUBLISHED" && publications.b.state === "PUBLISHED"
      && publications.a.manifest_version !== publications.b.manifest_version
      && publications.a.pointer_version === publications.a.manifest_version
      && publications.b.pointer_version === publications.b.manifest_version,
    JSON.stringify({ a: publications.a.manifest_version, b: publications.b.manifest_version }));
  check("server: A and B publish different sources",
    Object.keys(publications.a.event_versions).join() === "QA-EVENT-PICKUP"
      && Object.keys(publications.b.event_versions).join() === "QA-OTHER-EVENT-PICKUP"
      && Object.keys(publications.a.document_versions).join() === DOC_A
      && Object.keys(publications.b.document_versions).join() === DOC_B.join(),
    JSON.stringify({ a: publications.a.document_versions, b: publications.b.document_versions }));

  const aCards = (readback.roles.a?.cards || []).map((card) => card.reference);
  const bCards = (readback.roles.b?.cards || []).map((card) => card.reference);
  check("server: A view cards are exactly A's own lot", JSON.stringify(aCards) === JSON.stringify([LOT_A]),
    JSON.stringify(aCards));
  check("server: B view cards are exactly B's own lot", JSON.stringify(bCards) === JSON.stringify([LOT_B]),
    JSON.stringify(bCards));
  check("server: A payload has no foreign/internal marker",
    readback.roles.a?.payload_clean === true && (readback.roles.a?.forbidden_markers || []).length >= 8,
    JSON.stringify(readback.roles.a?.forbidden_markers_found));
  check("server: B payload has no foreign/internal marker",
    readback.roles.b?.payload_clean === true && (readback.roles.b?.forbidden_markers || []).length >= 8,
    JSON.stringify(readback.roles.b?.forbidden_markers_found));
  check("server: A payload ids are A's own",
    JSON.stringify(readback.roles.a?.payload_lot_ids) === JSON.stringify([LOT_A])
      && JSON.stringify(readback.roles.a?.payload_document_ids) === JSON.stringify([DOC_A]),
    JSON.stringify(readback.roles.a?.payload_lot_ids));
  check("server: B payload ids are B's own",
    JSON.stringify(readback.roles.b?.payload_lot_ids) === JSON.stringify([LOT_B])
      && JSON.stringify(readback.roles.b?.payload_document_ids) === JSON.stringify([...DOC_B]),
    JSON.stringify(readback.roles.b?.payload_lot_ids));

  check("server: ungranted verified email raises PortalAccessDenied",
    negative.ungranted_email?.denied === true
      && negative.ungranted_email?.exception === "PortalAccessDenied",
    JSON.stringify(negative.ungranted_email));
  check("server: tenant split has no overlap",
    JSON.stringify(negative.tenant_split?.a?.cards) === JSON.stringify([LOT_A])
      && JSON.stringify(negative.tenant_split?.b?.cards) === JSON.stringify([LOT_B]),
    JSON.stringify(negative.tenant_split));
  check("server: cross-tenant manifest denied",
    negative.cross_tenant_manifest === "PublicationDenied"
      && negative.foreign_shipment_manifest === "PublicationDenied"
      && negative.own_manifest_allowed === "ALLOWED",
    JSON.stringify({
      own: negative.own_manifest_allowed,
      cross: negative.cross_tenant_manifest,
      foreign: negative.foreign_shipment_manifest,
    }));
  check("server: cross-tenant source read returns zero rows",
    negative.cross_tenant_source_rows?.events === 0
      && negative.cross_tenant_source_rows?.documents === 0,
    JSON.stringify(negative.cross_tenant_source_rows));
  check("server: INTERNAL and unverified sources cannot be published",
    negative.private_document === "PublicationWriteDenied"
      && negative.unverified_document === "PublicationWriteDenied"
      && negative.pointer_after_denials === publications.a.pointer_version
      && JSON.stringify(negative.manifests_before_after) === JSON.stringify([1, 1]),
    JSON.stringify({
      private: negative.private_document,
      unverified: negative.unverified_document,
      pointer: negative.pointer_after_denials,
      counts: negative.manifests_before_after,
    }));
  check("server: denied browser identity never got a principal",
    deniedView.principal_created === false
      && ["PortalAccessDenied", "PortalDataError"].includes(deniedView.exception),
    JSON.stringify(deniedView));
}

const result = {
  url: URL_,
  started_at: new Date().toISOString(),
  chrome: "",
  checks: [],
  page_errors: pageErrors,
  console_errors: consoleErrors,
  exit: 1,
};

try {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  result.chrome = String(await browser.version());

  for (const viewport of viewportPlan()) {
    const page = await browser.newPage();
    page.on("pageerror", (error) => {
      pageErrors.push({ viewport: viewport.id, error: String(error).slice(0, 400) });
    });
    page.on("console", (message) => {
      if (message.type() === "error") {
        consoleErrors.push({ viewport: viewport.id, text: message.text().slice(0, 400) });
      }
    });
    try {
      await runViewport(page, viewport);
    } finally {
      await page.close();
    }
  }

  const server = serverFacts({ requireDeniedView: true });
  result.server = {
    db: server.db,
    a: server.a,
    b: server.b,
    publications: server.publications,
    negative: server.negative,
    denied_view: server.deniedView,
  };
  checkServerEvidence(server);
  result.checks = checks;
  result.finished_at = new Date().toISOString();
  result.exit = 0;
  save("browser-results.json", result);
  console.log("");
  console.log(`BROWSER_CHECKS=${checks.length} FAILED=${checks.filter((c) => !c.pass).length}`);
  console.log(`BROWSER_PAGE_ERRORS=${pageErrors.length}`);
  console.log("S3_BROWSER=PASS");
  await browser.close();
  process.exit(0);
} catch (error) {
  result.checks = checks;
  result.finished_at = new Date().toISOString();
  result.error = String(error && error.stack ? error.stack : error);
  result.exit = 1;
  try {
    save("browser-results.json", result);
  } catch (_) {
    /* evidence write is best effort on failure */
  }
  console.error("");
  console.error(`BROWSER_CHECKS=${checks.length} FAILED=${checks.filter((c) => !c.pass).length}`);
  console.error(`S3_BROWSER=FAIL: ${error && error.message ? error.message : error}`);
  process.exit(1);
}
