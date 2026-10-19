// TT_ENTRUSTED_SUB legal-importer DOM lane (deterministic jsdom).
//
// Generate the fixture from the REAL backend projection:
//   .venv/bin/python scripts/gen_logi195_dom_fixture.py \
//     --fixture /tmp/logi211-dom.json --entrusted-sub
// Run:
//   node tests/component/dom_entrusted_sub_importer_199.mjs /tmp/logi211-dom.json
//
// Proves, against the committed bundle:
// - the importer selector is sourced from authority_companies (A) and excludes
//   the Trường Thành signing company;
// - the contract agent (B) stays a separate field and is never the importer;
// - a historical SUB row with no company link renders UNKNOWN and cannot be
//   confirmed (button locked), so the UI cannot report a false legal identity.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(ROOT, 'component/package.json'));
const { JSDOM } = require('jsdom');
const fixture = JSON.parse(readFileSync(process.argv[2] || '/tmp/logi211-dom.json', 'utf8'));
const model = structuredClone(fixture.viewModel);
const expected = fixture.expected.entrustedSub;
assert.ok(expected, 'fixture must be generated with --entrusted-sub');

const sid = expected.shipmentId;
const legacySid = expected.legacyShipmentId;
const row = model.shipments.find((s) => s.id === sid);
const legacyRow = model.shipments.find((s) => s.id === legacySid);
assert.ok(row?.commercialFlow, 'canonical SUB shipment required');
assert.ok(legacyRow?.commercialFlow, 'legacy SUB shipment required');
assert.equal(row.commercialFlow.importerCompanyId, expected.importerCompanyId);
assert.equal(row.commercialFlow.legalImporterName, expected.importerName);
assert.equal(row.commercialFlow.legalImporterTaxCode, expected.importerTaxCode);
assert.equal(row.commercialFlow.subAgentId, expected.contractAgentId);
assert.equal(legacyRow.commercialFlow.importerCompanyId, '');
assert.equal(legacyRow.commercialFlow.legalImporterName, '');

const dom = new JSDOM('<!doctype html><html><body><div id="host"></div></body></html>', {
  url: 'http://localhost/',
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
Object.defineProperty(globalThis, 'navigator', { value: window.navigator, configurable: true });
for (const key of [
  'HTMLElement', 'HTMLInputElement', 'HTMLTextAreaElement', 'HTMLSelectElement',
  'HTMLAnchorElement', 'HTMLButtonElement', 'Element', 'Event', 'CustomEvent',
  'MouseEvent', 'KeyboardEvent', 'Node', 'MutationObserver', 'getComputedStyle',
]) globalThis[key] = window[key];
window.HTMLElement.prototype.scrollIntoView = () => {};
window.scrollTo = () => {};

const writes = [];
const tick = (ms = 50) => new Promise((resolve) => setTimeout(resolve, ms));
async function until(read, label) {
  const deadline = Date.now() + 6000;
  while (Date.now() < deadline) {
    const value = read();
    if (value) return value;
    await tick();
  }
  assert.fail(`Timed out waiting for ${label}`);
}
const $ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const byId = (id) => $(`[data-testid="${id}"]`)[0];
const text = (el) => (el?.textContent || '').replace(/\s+/g, ' ').trim();
const click = async (el) => {
  assert.ok(el, 'click target exists');
  el.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true, button: 0, view: window }));
  await tick();
};

const mount = (await import(pathToFileURL(path.join(ROOT, 'component/dist/logi-shell.js')))).default;
mount({ name: 'logi_shell', data: model, parentElement: document.getElementById('host'), setTriggerValue: (event, value) => writes.push({ event, value }) });
await until(() => document.querySelector('.logi-shell'), 'application shell');

async function gotoDocuments(shipmentId) {
  await click(await until(() => $('a').find((a) => text(a) === 'Lô Hàng'), 'shipment nav'));
  await click(await until(() => byId('shipment-period-tat-ca'), 'shipment period'));
  await click(await until(() => document.querySelector(`main a[href="/lo-hang/${shipmentId}"]`), 'shipment link'));
  await until(() => byId('shipment-journey'), 'shipment journey');
  await click(await until(() => $('button').find((b) => text(b).includes('Toàn bộ lô hàng')), 'global workspace trigger'));
  const workspace = await until(() => byId('journey-global-workspace'), 'global workspace');
  const tab = await until(() => $('button', workspace).find((b) => text(b) === 'Chứng từ'), 'Chứng từ tab');
  await click(tab);
  return until(() => byId('shipment-commercial-flow'), 'commercial-flow section');
}

// 1 — valid SUB: importer is company A, contract partner is agent B
const flow = await gotoDocuments(sid);
const subRadio = flow.querySelector("input[name='commercial-flow'][value='TT_ENTRUSTED_SUB']");
assert.ok(subRadio?.checked, 'SUB radio reflects the persisted mode');
const importerSelect = byId('commercial-flow-importer-company');
assert.ok(importerSelect, 'importer company select exists');
assert.equal(importerSelect.value, expected.importerCompanyId, 'importer select is the company link');
const importerOptionIds = [...importerSelect.options].map((o) => o.value);
assert.ok(importerOptionIds.includes(expected.importerCompanyId), 'company A is selectable');
assert.ok(!importerOptionIds.includes(expected.signingCompanyId), 'signing TT company is not offered as importer');
const importerText = text(importerSelect.selectedOptions[0]);
assert.ok(importerText.includes(expected.importerName), 'importer option carries the company legal name');
assert.ok(importerText.includes(expected.importerTaxCode), 'importer option carries the company MST');

const agentSelect = byId('commercial-flow-contract-agent');
assert.ok(agentSelect, 'contract-agent select exists');
assert.equal(agentSelect.value, expected.contractAgentId, 'contract agent stays a separate field');
assert.ok(text(agentSelect.selectedOptions[0]).includes(expected.contractAgentName));

const persisted = byId('commercial-flow-persisted-importer');
assert.ok(persisted, 'persisted importer card exists');
assert.ok(text(persisted).includes(expected.importerName), 'card shows the company importer');
assert.ok(text(persisted).includes(expected.importerTaxCode), 'card shows the company MST');
assert.ok(text(persisted).includes('authority_companies'), 'card states the company master provenance');
assert.ok(text(persisted).includes('không phải pháp nhân nhập khẩu'), 'card keeps the agent relation distinct');

const confirm = $('button', flow).find((b) => text(b).includes('XÁC NHẬN HÌNH THỨC NHẬP KHẨU'));
assert.ok(confirm, 'confirm button exists');
assert.equal(confirm.disabled, false, 'valid SUB is confirmable');

// 2 — historical SUB without a company link: UNKNOWN, confirm locked
const legacyFlow = await gotoDocuments(legacySid);
const legacyRadio = legacyFlow.querySelector("input[name='commercial-flow'][value='TT_ENTRUSTED_SUB']");
assert.ok(legacyRadio?.checked, 'historical SUB mode is shown honestly');
const legacyImporter = byId('commercial-flow-importer-company');
assert.ok(legacyImporter, 'historical row still shows the importer selector');
assert.equal(legacyImporter.value, '', 'no agent id is silently promoted into the importer');
const legacyCard = byId('commercial-flow-persisted-importer');
assert.ok(text(legacyCard).includes('UNKNOWN'), 'historical row renders UNKNOWN importer');
assert.ok(text(legacyCard).includes('CHƯA ĐỦ HỒ SƠ') || text(legacyFlow).includes('CHƯA ĐỦ HỒ SƠ'),
  'historical row is not presented as complete');
const legacyConfirm = $('button', legacyFlow).find((b) => text(b).includes('XÁC NHẬN HÌNH THỨC NHẬP KHẨU'));
assert.ok(legacyConfirm, 'legacy confirm button exists');
assert.equal(legacyConfirm.disabled, true, 'legacy row cannot be confirmed without a company link');

assert.deepEqual(writes, [], 'rendering these panels performs no business write');
console.log('PASS entrusted-sub importer 199 (jsdom): company importer from authority_companies, contract agent separate, legacy row UNKNOWN + locked');
process.exit(0);
