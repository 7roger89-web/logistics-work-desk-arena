// Compiled React + canonical backend fixture; no browser/DB claim from this DOM lane.
// Generate: .venv/bin/python scripts/gen_logi195_dom_fixture.py --fixture /tmp/logi211-dom.json --with-attachments
// Run: node tests/component/dom_sale_home_journey_flow_199.mjs /tmp/logi211-dom.json
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(path.join(ROOT,'component/package.json'));
const {JSDOM}=require('jsdom');
const fixture=JSON.parse(readFileSync(process.argv[2] || '/tmp/logi211-dom.json','utf8'));
const model=structuredClone(fixture.viewModel);
const sid=fixture.expected.shipmentId;
const shipment=model.shipments.find(s=>s.id===sid);
assert.ok(shipment?.journey?.nodes.length,'canonical populated shipment required');

// The fixture generator saved these through the canonical attachment writer and
// the backend allocated documentIds per node; this lane only asserts rendering.
const attachmentIds=fixture.expected.attachmentIds || [];
assert.equal(attachmentIds.length,5,'fixture must carry the five distinct files');
const si=shipment.journey.nodes.find(n=>n.id==='si-vgm');
const etd=shipment.journey.nodes.find(n=>n.id==='etd');
assert.deepEqual([...si.documentCategories].sort(),['si','vgm'],'backend node categories are SI/VGM only');
assert.deepEqual([...si.documentIds].sort(),['fixture-si-199','fixture-vgm-199'],'backend allocated only SI/VGM files to the node');
assert.deepEqual(etd.documentCategories,[],'ETD has no document category');

const dom=new JSDOM('<!doctype html><html><body><div id="host"></div></body></html>',{url:'http://localhost/',pretendToBeVisual:true});
const {window}=dom;
globalThis.window=window;globalThis.document=window.document;
Object.defineProperty(globalThis,'navigator',{value:window.navigator,configurable:true});
for(const key of ['HTMLElement','HTMLInputElement','HTMLTextAreaElement','HTMLSelectElement','HTMLAnchorElement','HTMLButtonElement','Element','Event','CustomEvent','MouseEvent','KeyboardEvent','Node','MutationObserver','getComputedStyle']) globalThis[key]=window[key];
window.HTMLElement.prototype.scrollIntoView=()=>{};
window.scrollTo=()=>{};
const tick=()=>new Promise(resolve=>setTimeout(resolve,50));
async function until(read,label){
  const deadline=Date.now()+5000;
  while(Date.now()<deadline){const value=read();if(value)return value;await tick();}
  assert.fail(`Timed out waiting for ${label}`);
}
const $=selector=>document.querySelector(selector);
const byId=id=>$(`[data-testid="${id}"]`);
const click=async el=>{assert.ok(el,'click target exists');el.dispatchEvent(new window.MouseEvent('click',{bubbles:true,cancelable:true,button:0,view:window}));await tick();};
const mount=(await import(pathToFileURL(path.join(ROOT,'component/dist/logi-shell.js')))).default;
mount({name:'logi_shell',data:model,parentElement:document.getElementById('host'),setTriggerValue:()=>{}});
await until(()=>$('.logi-shell'),'application shell');

// 0 — Home: an unbound manual task says "Mở lô" and opens its own lot, with no
// invented export tab. This is the compiled projection of the Python routing.
await until(()=>byId('attention-now'),'home attention panel');
const taskLinks=[...document.querySelectorAll('a[data-attention-source="TASK"], [data-attention-source="TASK"] a')];
assert.ok(taskLinks.length>0,'home shows the real manual tasks');
for(const link of taskLinks){
  assert.ok(link.textContent.includes('Mở lô'),'TASK action label must say Mo lo');
  const href=link.getAttribute('href');
  assert.ok(href.startsWith('/lo-hang/'),'task opens a shipment route');
  assert.ok(!href.includes('?'),`unbound task must not invent a tab: ${href}`);
}

await click(await until(()=>[...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Lô Hàng'),'shipment navigation link'));
await until(()=>byId('shipment-period-tat-ca'),'shipment list');
await click(byId('shipment-period-tat-ca'));
await click(await until(()=>document.querySelector(`main a[href="/lo-hang/${sid}"]`),'shipment link'));
await until(()=>byId('shipment-journey'),'actual shipment Journey mount');

async function closeStage(){
  const close=document.querySelector('[aria-label="Đóng công đoạn"]');
  if(close){await click(close);await until(()=>!byId('journey-modal'),'stage close');}
}
async function openNode(id,work){
  await closeStage();
  await click(byId(`journey-node-${id}`));
  await until(()=>byId('journey-bubble')?.getAttribute('data-node')===id,'selected node bubble');
  await click(byId(`journey-bubble-task-${work}`));
  await until(()=>byId('journey-stage-workspace'),'stage popup, not global workspace');
}

// 1 — SI/VGM documents are exactly the node's own categories/files.
await openNode('si-vgm','docs');
let workspace=byId('journey-stage-workspace');
assert.ok(byId('journey-stage-documents'),'stage document panel rendered');
const categories=byId('journey-stage-doc-categories').textContent;
for(const category of ['si','vgm']) assert.ok(categories.includes(category),`SI/VGM category ${category} shown`);
for(const category of ['booking','customs','transport']) assert.ok(!categories.includes(category),`SI/VGM must not own ${category}`);
const files=byId('journey-stage-doc-files').textContent;
assert.match(files,/only-si-199\.pdf/);
assert.match(files,/only-vgm-199\.pdf/);
for(const category of ['booking','transport','customs']) assert.ok(!workspace.textContent.includes(`only-${category}-199.pdf`),`SI/VGM popup must not show ${category} files`);
assert.equal(byId('missing-info'),null,'no whole-lot checklist in the SI/VGM popup');
assert.equal(document.querySelector('.sticky-action'),null,'no global sticky action in the SI/VGM popup');

// 2 — a node with no category stays scoped-empty; never falls back to the lot.
await closeStage();
await click(byId('journey-node-etd'));
await until(()=>byId('journey-bubble')?.getAttribute('data-node')==='etd','ETD bubble');
await click(byId('journey-bubble-overview'));
await until(()=>byId('journey-quick-more'),'ETD details');
await click(byId('journey-quick-more'));
await click(await until(()=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Quản lý chứng từ →'),'ETD documents link'));
await until(()=>byId('journey-stage-documents'),'ETD stage documents');
workspace=byId('journey-stage-workspace');
assert.match(workspace.textContent,/Chưa có loại chứng từ được chỉ định cho công đoạn/);
assert.match(workspace.textContent,/Chưa có tệp nào được ghi nhận riêng cho công đoạn này/);
assert.equal(byId('journey-stage-doc-files'),null,'ETD has no file list at all');
for(const category of ['si','vgm','booking','transport','customs']) assert.ok(!workspace.textContent.includes(`only-${category}-199.pdf`),`empty-category popup must not show ${category}`);
assert.equal(byId('missing-info'),null,'no whole-lot checklist in an empty-category popup');
assert.equal(workspace.querySelector('.sticky-action'),null,'no sticky action inside an empty-category popup');

// 3 — the whole-lot workspace keeps the lot-wide content and every file.
await closeStage();
await click(byId('journey-global-open'));
await until(()=>byId('journey-global-workspace'),'whole-lot workspace stays accessible');
// The global tab is committed by the router after the panel mounts, so wait
// for the lot-wide block instead of asserting on the first paint.
await until(()=>byId('missing-info'),'whole-lot missing-info remains available outside node popups');
await click(await until(()=>[...byId('journey-global-workspace').querySelectorAll('button')].find(b=>b.textContent.trim()==='Chứng từ'),'whole-lot documents tab'));
await until(()=>byId('shipment-attachments'),'whole-lot attachment list');
const lot=byId('shipment-attachments').textContent;
for(const category of ['si','vgm','booking','transport','customs']) assert.ok(lot.includes(`only-${category}-199.pdf`),`whole-lot list keeps ${category}`);
assert.ok(!lot.includes('Tệp liên quan công đoạn'),'whole-lot surface is not stage-scoped');
assert.equal(byId('journey-stage-workspace'),null,'global workspace is not a node popup');

console.log('SALE_HOME_JOURNEY_DOM=PASS: node docs exact; empty category stays empty; no global checklist/sticky in node popups; whole-lot documents retained');
