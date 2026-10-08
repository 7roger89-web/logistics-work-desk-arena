// ============================================================================
// LOGI_UAT_REAL_USE_REPAIR_02 — DOM acceptance for three reproduced real-use
// defects, run against the REAL production bundle (component/dist/logi-shell.js)
// in jsdom with a REAL-backend fixture (scripts/gen_real_use_repair_fixture.py —
// isolated mongomock staging; every outcome went through the bounded dispatcher:
// RBAC → canonical writer → audit → fresh read).
//
//   P0-A  CUSTOMER CREATE FALSE SUCCESS
//         Old behaviour: the modal closed, the form cleared and a green
//         "Đã gửi tạo khách hàng …" was claimed the instant the event was
//         handed to the transport — even when the transport refused and even
//         when the backend then refused the write. Required now:
//           1. transport refusal  → data retained, modal open, NO success claim
//           2. transport success  → still NO success claim; bounded waiting
//           3. backend refusal    → data retained, real error verbatim
//           4. backend success    → only THEN close/clear, and only when the
//                                   customer genuinely exists in fresh data
//           5. an unrelated backend write can never be mistaken for success
//           6. one click can never double-send
//
//   P1-A  NEXT WORK TAB
//         "XỬ LÝ NGAY" parsed the tab with /tab=(\w+)/ — `\w` excludes `-`, so
//         the real hyphenated tab (`lay-hang`) was truncated to `lay`, matched
//         no tab, and the intended work section never opened.
//
//   P1-B  CONTRACT DOCUMENT HANDOFF
//         "MỞ CHỨNG TỪ" on a linked contract only re-selected the SHIPMENT's
//         own documents tab the employee already stood on; it never reached
//         the contract's own HDNT/PL/HDMB workdesk.
//
// Run: node tests/component/dom_acceptance_real_use_repair.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_real_use_repair.json"), "utf8")
);

const INITIAL = FIX.initial;
const CREATE_OK = FIX.createOk;
const DUPLICATE_ERROR = FIX.duplicateError;
const UNRELATED_CHANGE = FIX.unrelatedChange;
const CUSTOMER_ID = FIX.customerId;
const CUSTOMER_NAME = FIX.customerName;
const HYPHEN_SHIPMENT = FIX.hyphenTabShipment;
const HYPHEN_ROUTE = FIX.hyphenTabRoute;
const HYPHEN_TAB = HYPHEN_ROUTE.split("?tab=")[1];
const LINKED_SHIPMENT = FIX.linkedContractShipment;
const LINKED_CONTRACT = FIX.linkedContractId;

// The fixture must genuinely exercise the hyphen case, otherwise P1-A would
// pass vacuously against the old bundle too.
assert.ok(HYPHEN_TAB.includes("-"), "fixture tab must be hyphenated to challenge P1-A");

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;

globalThis.window = window;
globalThis.document = window.document;
try {
  Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true });
} catch {
  /* keep node navigator */
}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const bodyText = () => text(window.document.body);
const mainText = () => text($("main")[0] ?? window.document.body);

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

// Issue #190 — the permanent shipment tab row was removed from the default
// Journey first screen; the tabs now live in the Global Workspace opened via
// "Toàn bộ lô hàng". This helper opens it and clicks the remapped tab.
async function openGlobalTab(label) {
  await click("Toàn bộ lô hàng", "button");
  await click(label, "button", window.document.querySelector('[data-testid="journey-global-workspace"]'));
}

async function type(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

/** Rewrite the fixture outcome's requestId to the one the real click produced. */
function withRequestId(state, requestId) {
  const clone = structuredClone(state);
  for (const w of clone.lastWrites ?? []) w.requestId = requestId;
  return clone;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
let triggers = [];
const mountRef = { current: null };
let lastInvokeCleanup = null;

function transport(event, value) {
  triggers.push({ event, value });
}

function invoke(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  lastInvokeCleanup = mountRef.current({
    name: "logi_shell", data, parentElement: host, setTriggerValue: transport,
  });
}

/** A fresh view-model delivery on the SAME mounted component — exactly what
 *  Streamlit does after the dispatcher's rerun: no unmount, route + component
 *  state survive, only the data channel (and the bound transport) update.
 *  Passing `setTriggerValue: undefined` reproduces the REAL disconnected
 *  transport: `bindTransport(null)` makes `dispatchLogiEvent` return false. */
function deliver(data, { connected = true } = {}) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: connected ? transport : undefined,
  });
}

/** Optional step filter: `node <this> --only 8,9` runs a single defect's
 *  challenge. Used to prove EACH repair independently rejects the old bundle
 *  (P0-A fails first otherwise and would mask P1-A / P1-B). */
const onlyArg = process.argv.indexOf("--only");
const ONLY = onlyArg > -1 ? new Set(process.argv[onlyArg + 1].split(",").map(Number)) : null;
const run = (n) => !ONLY || ONLY.has(n);

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot the real bundle on the customers page");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  invoke(INITIAL);
  await tick(140);
  await click("Khách Hàng", "a", $("aside")[0]);
  assert.ok(mainText().includes("Khách Hàng"), "customers page did not render");
  assert.ok(!mainText().includes(CUSTOMER_ID), "fixture customer must be absent before the create");
  ok("boot clean; /khach-hang renders with the customer genuinely absent");
}

// ---------------------------------------------------------------------------
if (run(2)) console.log("STEP 2 — P0-A · TRANSPORT FAILURE keeps the data and claims nothing");
if (run(2)) {
  await click("Khách mới", "button");
  await tick();

  const idInput = $('input[placeholder="VD: CUST-ABC"]')[0];
  const nameInput = $('input[placeholder="Công ty / cá nhân"]')[0];
  assert.ok(idInput && nameInput, "create form inputs missing");
  await type(idInput, CUSTOMER_ID);
  await type(nameInput, CUSTOMER_NAME);

  // The component is NOT connected to the backend transport: the real
  // `dispatchLogiEvent` returns false (bindTransport(null)).
  deliver(INITIAL, { connected: false });
  await tick(80);

  const before = triggers.length;
  await click("💾 TẠO KHÁCH HÀNG", "button");
  await tick(80);

  const t = bodyText();
  // 1. no success claim of ANY kind
  assert.ok(!t.includes("Đã gửi tạo khách hàng"),
    "OLD BEHAVIOUR: a transport failure still claimed 'Đã gửi tạo khách hàng'");
  assert.ok(!t.includes("Đã tạo khách hàng"),
    "a transport failure must never claim the customer was created");
  // 2. the modal did NOT close
  assert.ok(t.includes("Tạo khách hàng mới"),
    "OLD BEHAVIOUR: the modal closed on a transport failure");
  // 3. the entered data is RETAINED verbatim
  const idNow = $('input[placeholder="VD: CUST-ABC"]')[0];
  const nameNow = $('input[placeholder="Công ty / cá nhân"]')[0];
  assert.equal(idNow.value, CUSTOMER_ID, "OLD BEHAVIOUR: the form cleared the entered id");
  assert.equal(nameNow.value, CUSTOMER_NAME, "OLD BEHAVIOUR: the form cleared the entered name");
  // 4. a useful failure state is shown
  assert.ok(t.includes("Chưa lưu được — dữ liệu vẫn được giữ"), "failure banner missing");
  assert.ok(t.includes("chưa kết nối backend"), "the real failure reason is not stated");
  // 5. nothing was transported
  assert.equal(triggers.length, before, "no event may be recorded when the transport refused");
  ok("transport failure → data retained, modal open, no success claim, useful failure state");
}

// ---------------------------------------------------------------------------
if (run(3)) console.log("STEP 3 — P0-A · TRANSPORT SUCCESS is still not persistence");
let sentRequestId = "";
if (run(3)) {
  // Reconnect the transport (same mounted component, same open modal).
  deliver(INITIAL);
  await tick(80);
  const before = triggers.length;
  await click("💾 TẠO KHÁCH HÀNG", "button");
  await tick(80);

  const creates = triggers.slice(before).filter((tr) => tr.event === "customer_create");
  assert.equal(creates.length, 1, "expected exactly one customer_create trigger");
  const payload = creates[0].value.payload;
  assert.equal(payload.id, CUSTOMER_ID);
  assert.equal(payload.name, CUSTOMER_NAME);
  assert.equal(typeof payload.requestId, "string");
  assert.ok(payload.requestId, "the event MUST carry a requestId to correlate the outcome");
  sentRequestId = payload.requestId;

  const t = bodyText();
  assert.ok(t.includes("Tạo khách hàng mới"),
    "OLD BEHAVIOUR: the modal closed on transport success alone");
  assert.ok(!t.includes("Đã tạo khách hàng"),
    "OLD BEHAVIOUR: success was claimed on transport alone");
  assert.ok(t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "bounded waiting state missing");
  const btn = findClickable("ĐANG CHỜ BACKEND XÁC NHẬN…", "button");
  assert.ok(btn && btn.disabled, "the submit button must be locked while the outcome is in flight");
  ok("transport success → still no claim; bounded waiting state, button locked, requestId sent");
}

// ---------------------------------------------------------------------------
if (run(4)) console.log("STEP 4 — P0-A · one click can never double-send");
if (run(4)) {
  const before = triggers.length;
  const btn = findClickable("ĐANG CHỜ BACKEND XÁC NHẬN…", "button");
  btn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);
  const creates = triggers.slice(before).filter((tr) => tr.event === "customer_create");
  assert.equal(creates.length, 0, "a second click must not emit a second customer_create");
  ok("second click while in flight emits nothing");
}

// ---------------------------------------------------------------------------
if (run(5)) console.log("STEP 5 — P0-A · an UNRELATED backend write is never success");
if (run(5)) {
  // The version genuinely changes and a write outcome exists, but it is not
  // THIS request's customer_create outcome.
  deliver(UNRELATED_CHANGE);
  await tick(140);
  const t = bodyText();
  assert.ok(t.includes("Tạo khách hàng mới"),
    "an unrelated backend write must not close the form");
  assert.ok(!t.includes("Đã tạo khách hàng"),
    "an unrelated backend write must never be reported as a successful create");
  assert.ok(t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"),
    "the intent must still be waiting for its own authoritative outcome");
  ok("unrelated write + version change → still waiting, no false success");
}

// ---------------------------------------------------------------------------
if (run(6)) console.log("STEP 6 — P0-A · BACKEND REFUSAL keeps the data and shows the real error");
if (run(6)) {
  deliver(withRequestId(DUPLICATE_ERROR, sentRequestId));
  await tick(160);
  const t = bodyText();
  assert.ok(t.includes("Tạo khách hàng mới"), "a refusal must keep the operator on the form");
  assert.ok(t.includes(`Mã khách hàng ${CUSTOMER_ID} đã tồn tại.`),
    "the real backend error must be visible verbatim");
  assert.ok(!t.includes("Đã tạo khách hàng"), "a refusal must never claim success");
  assert.ok(!t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "pending state must clear after the outcome");
  // The operator's data survived the refusal.
  assert.equal($('input[placeholder="VD: CUST-ABC"]')[0].value, CUSTOMER_ID,
    "the entered id must survive a backend refusal");
  assert.equal($('input[placeholder="Công ty / cá nhân"]')[0].value, CUSTOMER_NAME,
    "the entered name must survive a backend refusal");
  const btn = findClickable("💾 TẠO KHÁCH HÀNG", "button");
  assert.ok(btn && !btn.disabled, "the form must be usable again after a refusal");
  ok("backend refusal → data retained, real error verbatim, form usable again");
}

// ---------------------------------------------------------------------------
if (run(7)) console.log("STEP 7 — P0-A · BACKEND SUCCESS is the only thing that closes the form");
if (run(7)) {
  // Re-submit to obtain a fresh in-flight requestId, then answer it ok=True.
  await click("💾 TẠO KHÁCH HÀNG", "button");
  await tick(80);
  const creates = triggers.filter((tr) => tr.event === "customer_create");
  const rid = creates[creates.length - 1].value.payload.requestId;
  assert.notEqual(rid, sentRequestId, "a new intent must carry a NEW requestId");

  deliver(withRequestId(CREATE_OK, rid));
  await tick(180);
  const t = bodyText();
  assert.ok(!t.includes("Tạo khách hàng mới"),
    "an authoritative success must close the modal");
  assert.ok(t.includes("Đã tạo khách hàng " + CUSTOMER_ID),
    "the success claim must name the customer the backend confirmed");
  // …and the customer is genuinely in the fresh data behind the modal.
  assert.ok(mainText().includes(CUSTOMER_ID),
    "the confirmed customer must be present in the refreshed list");
  ok("authoritative success (outcome + fresh readback) → closes, clears, claims");
}

// ---------------------------------------------------------------------------
if (run(8)) console.log("STEP 8 — P1-A · 'XỬ LÝ NGAY' opens the REAL hyphenated work tab");
if (run(8)) {
  invoke(CREATE_OK);
  await tick(140);
  await click("Lô Hàng", "a", $("aside")[0]);
  await tick(80);
  const lotLink = $("a").find((a) => text(a) === HYPHEN_SHIPMENT);
  assert.ok(lotLink, `shipment link ${HYPHEN_SHIPMENT} not found`);
  lotLink.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(160);
  assert.ok(mainText().includes(HYPHEN_SHIPMENT), "shipment detail did not open");

  // The banner action carries the backend's own nextRoute (hyphenated tab).
  const action = findClickable("XỬ LÝ NGAY", "button") || findClickable("XEM LÔ", "button");
  assert.ok(action, "next-action banner button missing");
  action.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(160);

  // Issue #190 — the selected tab is the ACTIVE one in the Global Workspace:
  // the composed tab route opens it directly. Old bundle truncated "lay-hang"
  // → "lay", which matches no tab, so the view silently fell back to default.
  const gwRoot = window.document.querySelector('[data-testid="journey-global-workspace"]');
  assert.ok(gwRoot, "Global Workspace must open for the composed tab route (#190)");
  const active = $("button", gwRoot).filter((b) => (b.className || "").includes("border-slate-900"));
  assert.equal(active.length, 1,
    `OLD BEHAVIOUR: the truncated tab matched NO section, so no work section opened (active tabs: ${active.length})`);
  const TAB_LABEL = { "lay-hang": "Xuất khẩu", "nhap": "Nhập & Giao",
                      "van-tai": "Thông tin", "tai-chinh": "Tài chính",
                      "chung-tu": "Chứng từ", "lich-su": "Lịch sử" };
  const wanted = TAB_LABEL[HYPHEN_TAB];
  assert.ok(wanted, `unmapped fixture tab ${HYPHEN_TAB}`);
  assert.ok(text(active[0]).includes(wanted),
    `OLD BEHAVIOUR: the hyphenated tab "${HYPHEN_TAB}" was truncated — active tab is "${text(active[0])}", expected "${wanted}"`);
  ok(`"XỬ LÝ NGAY" opened the real work section (${HYPHEN_TAB} → ${wanted})`);
}

// ---------------------------------------------------------------------------
if (run(9)) console.log("STEP 9 — P1-B · 'MỞ CHỨNG TỪ' reaches the CONTRACT document workdesk (SLASH-ID boundary)");
if (run(9)) {
  // P1-B acceptance, unblocked by PR #52's contractPath().
  //
  // This deliberately drives the REAL slash boundary "05/2026/HDMB" (the same
  // id PR52 committed in view_model_contract_workflow.json). A contract number
  // is ONE route segment yet can contain "/", so a raw path emits
  // /hop-dong/05/2026/HDMB and misses single-segment /hop-dong/:id, landing on
  // the "*" wildcard. Exercising a slash-free id here would prove nothing.
  const SLASH_ID = "05/2026/HDMB";
  const state = structuredClone(CREATE_OK);
  const ship = state.shipments.find((x) => x.id === LINKED_SHIPMENT);
  assert.ok(ship, `fixture shipment ${LINKED_SHIPMENT} missing`);
  const con = state.contracts.find((c) => c.id === ship.contract);
  assert.ok(con, `fixture contract ${ship.contract} missing`);
  ship.contract = SLASH_ID;
  con.id = SLASH_ID;
  if (con.contractNo !== undefined) con.contractNo = SLASH_ID;
  assert.ok(SLASH_ID.includes("/"), "the boundary under test must contain a slash");

  invoke(state);
  await tick(140);
  await click("Lô Hàng", "a", $("aside")[0]);
  await tick(80);
  const lotLink = $("a").find((a) => text(a) === LINKED_SHIPMENT);
  assert.ok(lotLink, `shipment link ${LINKED_SHIPMENT} not found`);
  lotLink.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(160);

  // Start on the shipment's own documents tab — exactly where the old
  // behaviour stranded the employee.
  await openGlobalTab("Chứng từ");
  await tick(160);
  assert.ok(mainText().includes("Hợp đồng / docgen liên kết hiện có"), "linked-contract card missing");
  assert.ok(mainText().includes("Phiếu xuất kho"),
    "precondition: the employee starts on the SHIPMENT documents surface");

  const openDocs = findClickable("MỞ CHỨNG TỪ", "a,button");
  assert.ok(openDocs, "MỞ CHỨNG TỪ control missing");
  // The emitted route must keep the slash id as ONE encoded segment.
  const href = openDocs.getAttribute("href") || "";
  assert.ok(!/^\/hop-dong\/[^?#]*\/[^?#]*/.test(href),
    `slash-unsafe contract route emitted: ${href}`);
  assert.ok(href.includes("tab=chung-tu"), `contract documents tab not requested: ${href}`);

  openDocs.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(220);

  const t = mainText();
  // Must land on the contract's OWN document workdesk, not the wildcard.
  assert.ok(!t.includes("Sắp có") && !t.includes("Không tìm thấy"),
    `OLD BEHAVIOUR: slash id ${SLASH_ID} fell through to wildcard/NotFound (href=${href})`);
  assert.ok(t.includes(SLASH_ID),
    `the contract ${SLASH_ID} detail surface was not reached`);
  assert.ok(t.includes("Chứng từ HDNT · PL · HDMB"),
    "OLD BEHAVIOUR: the contract document workdesk (HDNT/PL/HDMB) did not open");
  assert.ok(t.includes("SINH CHỨNG TỪ"),
    "the real contract docgen action must be reachable");
  assert.ok(!t.includes("Phiếu xuất kho"),
    "OLD BEHAVIOUR: the employee was left in the shipment PXK documents surface");
  ok(`MỞ CHỨNG TỪ opened the real contract document workdesk for slash id ${SLASH_ID}`);
}

// ---------------------------------------------------------------------------
if (run(10)) console.log("STEP 10 — P1-C · responsibility labels state what the data really is");
if (run(10)) {
  invoke(CREATE_OK);
  await tick(140);
  await click("Lô Hàng", "a", $("aside")[0]);
  await tick(80);
  const lotLink = $("a").find((a) => text(a) === LINKED_SHIPMENT);
  lotLink.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(160);
  // LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 · OWNER_RUNTIME_UAT_REPAIR (issue #86):
  // the responsibility facts moved out of the primary visual path into ONE small
  // secondary disclosure ("Thông tin thêm"). The SEMANTICS under test are
  // unchanged — the disclosure is opened first, then the same truthful labels
  // must be exactly what the operator reads.
  await click("Thông tin thêm", "button");
  const t = mainText();
  assert.ok(!t.includes("Sale · Support"),
    "OLD BEHAVIOUR: updated_by was presented under a 'Support' responsibility label");
  assert.ok(t.includes("Cập nhật bởi"),
    "the last-writer value must be labelled for what it provably is");
  assert.ok(t.includes("Sale phụ trách"),
    "the canonical owner resolution must keep its own label");
  ok("no fabricated assignment semantics: updated_by is labelled 'Cập nhật bởi'");
}

console.log(`\nALL ${passed} DOM ACCEPTANCE CHECKS PASSED`);
