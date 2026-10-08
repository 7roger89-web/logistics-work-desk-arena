// #160: production bundle + canonical backend snapshots; sent != persisted.
// python scripts/verify_visual_shipment_workspace.py --fixture /tmp/log160-dom.json
// node tests/component/dom_acceptance_visual_shipment_workspace.mjs /tmp/log160-dom.json
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(root, 'component/package.json'));
const { JSDOM } = require('jsdom');
const fixture = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const dom = new JSDOM('<!doctype html><body><div id="host"></div>', {url:'http://localhost:9501',pretendToBeVisual:true});
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, 'navigator', {value:dom.window.navigator,configurable:true});
for (const key of ['HTMLElement','HTMLInputElement','HTMLSelectElement','HTMLTextAreaElement','Event','MouseEvent','Node','MutationObserver','getComputedStyle']) globalThis[key] = dom.window[key];
dom.window.HTMLElement.prototype.scrollIntoView = () => {};
const mount = (await import(pathToFileURL(path.join(root,'component/dist/logi-shell.js')))).default;
const triggers = [];
const deliver = data => mount({name:'logi_shell',data,parentElement:document.getElementById('host'),setTriggerValue:(event,value)=>triggers.push({event,value})});
const tick = () => new Promise(r => setTimeout(r,120));
const byId = id => document.querySelector(`[data-testid="${id}"]`);
const click = async el => {assert.ok(el,'click target exists');el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await tick();};
const button = (label, parent=document) => [...parent.querySelectorAll('button')].find(e=>e.textContent.trim()===label);
deliver(fixture.before); await tick();
await click([...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Lô Hàng'));
await click(byId('shipment-period-tat-ca'));
await click([...document.querySelectorAll('main a')].find(a=>a.textContent.trim()==='SEA-160'));
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length,11);
assert.equal(byId('journey-node-on-board').dataset.state,'UPCOMING');
const beforeEvents=triggers.length;
await click(byId('journey-node-si-vgm'));
assert.match(byId('journey-quick-panel').textContent,/SI \/ VGM/);
assert.equal(triggers.length,beforeEvents,'selection is view state only');
await click(byId('journey-open-workspace'));
assert.ok(byId('journey-stage-workspace'));
await click(button('Thông tin',byId('journey-stage-workspace')));
const form=byId('sea-export-facts');assert.ok(form);
for(const label of ['Trạng thái SI','Trạng thái VGM']) {
  const select=form.querySelector(`select[aria-label="${label}"]`);
  Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(select,'ACCEPTED');
  select.dispatchEvent(new Event('change',{bubbles:true}));await tick();
}
await click(button('Lưu mốc có bằng chứng',form));
const written=triggers.filter(t=>t.event==='shipment_sea_facts_save');assert.equal(written.length,1);
assert.deepEqual(written[0].value.payload.fields,{si_status:'ACCEPTED',vgm_status:'ACCEPTED'});
assert.equal(written[0].value.payload.expectedVersion,fixture.before.shipments.find(s=>s.id==='SEA-160').version);
assert.match(form.textContent,/Đang chờ đọc lại/);
assert.notEqual(byId('journey-node-si-vgm').dataset.state,'COMPLETED');
// Real backend refusal correlated to the actual request; no local completion.
const refusal=structuredClone(fixture.before);refusal.lastWrites=[{event:'shipment_sea_facts_save',ok:false,requestId:written[0].value.payload.requestId,error:'Lô đã thay đổi — đọc lại dữ liệu trước khi lưu.'}];
deliver(refusal);await tick();assert.match(document.querySelector('[role="alert"]').textContent,/Lô đã thay đổi/);
assert.notEqual(byId('journey-node-si-vgm').dataset.state,'COMPLETED');
// Fresh canonical writer snapshot updates the same mounted route + panel.
deliver(fixture.after);await tick();assert.equal(byId('journey-node-si-vgm').dataset.state,'COMPLETED');
assert.ok(byId('sea-export-facts'),'stage context survives readback');
assert.match(byId('journey-quick-panel').textContent,/SI: ACCEPTED · VGM: ACCEPTED/);
await click(button('Chứng từ',byId('journey-stage-workspace')));
assert.match(document.querySelector('main').textContent,/công đoạn|liên quan/i);
await click(button('Chi phí',byId('journey-stage-workspace')));
assert.match(document.querySelector('main').textContent,/Chi phí/i);
await click(button('Lịch sử',byId('journey-stage-workspace')));
assert.match(document.querySelector('main').textContent,/lịch sử toàn lô|audit toàn lô/i);
await click(button('Thông tin',byId('journey-stage-workspace')));
deliver(fixture.viewer);await tick();
assert.ok([...byId('sea-export-facts').querySelectorAll('input,select,button')].every(el=>el.disabled),'viewer cannot write');
// Issue #190 (Owner reference 6f6c655): the global-workspace control lives in
// the page identity bar now; same behaviour (stage workspace closes, rail mode).
await click(byId('journey-global-page'));
assert.equal(byId('journey-stage-workspace'),null);
assert.ok(byId('shipment-execution-profile'),'canonical global work stays reachable');
console.log('PASS #160: 11 nodes, view-only selection, scoped workspace, bounded write, pending/refusal, canonical fresh readback, document/finance/history navigation, viewer RBAC, global escape');
process.exit(0);
