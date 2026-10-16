// Current compiled React, canonical fixture; no browser/DB claim from this DOM lane.
// Generate: python scripts/gen_logi195_dom_fixture.py --fixture /tmp/logi199-dom.json
// Run: node tests/component/dom_sale_home_journey_flow_199.mjs /tmp/logi199-dom.json
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(path.join(ROOT,'component/package.json'));
const {JSDOM}=require('jsdom');
const fixture=JSON.parse(readFileSync(process.argv[2] || '/tmp/logi199-dom.json','utf8'));
const model=structuredClone(fixture.viewModel);
const sid=fixture.expected.shipmentId;
const shipment=model.shipments.find(s=>s.id===sid);
assert.ok(shipment?.journey?.nodes.length,'canonical populated shipment required');
// Distinct file names make a category leak observable, not just an option-count check.
shipment.attachments=['si','vgm','booking','transport','customs'].map(category=>({
  id:`file-${category}`,category,categoryLabel:category,name:`only-${category}-199.pdf`,
  sizeBytes:100,sizeLabel:'100 B',uploadedAt:'16/10/2026',uploadedBy:'fixture',canDownload:false,
}));
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
await click(await until(()=>[...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Lô Hàng'),'shipment navigation link'));
await until(()=>byId('shipment-period-tat-ca'),'shipment list');
await click(byId('shipment-period-tat-ca'));
await click(await until(()=>document.querySelector(`main a[href="/lo-hang/${sid}"]`),'shipment link'));
await until(()=>byId('shipment-journey'),'actual shipment Journey mount');

async function openNode(id,work){
  const close=document.querySelector('[aria-label="Đóng công đoạn"]');
  if(close){await click(close);await until(()=>!byId('journey-modal'),'stage close');}
  await click(byId(`journey-node-${id}`));
  await until(()=>byId('journey-bubble')?.getAttribute('data-node')===id,'selected node bubble');
  await click(byId(`journey-bubble-task-${work}`));
  await until(()=>byId('journey-stage-workspace'),'stage popup, not global workspace');
  await until(()=>byId(work==='docs'?'attachment-category':'sea-export-facts'),'stage work content');
}
await openNode('si-vgm','docs');
let workspace=byId('journey-stage-workspace');
assert.deepEqual([...byId('attachment-category').options].map(o=>o.value).sort(),['si','vgm']);
assert.match(workspace.textContent,/only-si-199.pdf/);
assert.match(workspace.textContent,/only-vgm-199.pdf/);
for(const category of ['customs','booking','transport']) assert.ok(!workspace.textContent.includes(`only-${category}-199.pdf`),`SI/VGM must not show ${category} files`);
assert.equal(byId('missing-info'),null,'no whole-lot checklist in stage docs');
assert.equal(workspace.querySelector('.sticky-action'),null,'no global sticky action in a stage popup');

await openNode('on-board','stage');
workspace=byId('journey-stage-workspace');
assert.equal(workspace.querySelectorAll('input').length,1,'on-board only has its own evidence field');
assert.ok(workspace.querySelector('[aria-label="Ngày xếp hàng lên tàu (on-board)"]'));
assert.equal(byId('missing-info'),null,'global missing fields must not leak into on-board work');
assert.equal(workspace.querySelector('.sticky-action'),null,'global mobile actions stay outside node work');
assert.ok(![...workspace.querySelectorAll('button')].some(b=>b.textContent.trim()==='Tài chính'),'finance not repeated on a node');

await click([...workspace.querySelectorAll('button')].find(b=>b.textContent.trim()==='Chứng từ'));
await until(()=>byId('attachment-category'),'on-board document categories');
assert.deepEqual([...byId('attachment-category').options].map(o=>o.value),['transport']);
// A node with no document categories must stay scoped-empty, not show every file.
await click(document.querySelector('[aria-label="Đóng công đoạn"]'));
await click(byId('journey-node-etd'));
await until(()=>byId('journey-bubble')?.getAttribute('data-node')==='etd','ETD bubble');
await click(byId('journey-bubble-overview'));
await click(await until(()=>byId('journey-quick-more'),'ETD details'));
await click(await until(()=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Quản lý chứng từ →'),'ETD documents link'));
await until(()=>byId('attachment-no-context-category'),'scoped-empty ETD documents');
assert.equal(byId('attachment-category'),null,'ETD has no category and no unrelated upload picker');
workspace=byId('journey-stage-workspace');
for(const category of ['si','vgm','customs','booking','transport']) assert.ok(!workspace.textContent.includes(`only-${category}-199.pdf`));
assert.ok(byId('attachment-no-context-category'));

await click(document.querySelector('[aria-label="Đóng công đoạn"]'));
await click(byId('journey-global-open'));
await until(()=>byId('journey-global-workspace'),'whole-lot workspace remains accessible');
assert.ok([...byId('journey-global-workspace').querySelectorAll('button')].some(b=>b.textContent.trim()==='Tài chính'),'finance kept once in whole-lot workspace');
console.log('SALE_HOME_JOURNEY_DOM=PASS: exact node categories/files; empty category stays empty; no global checklist/actions/finance in node popup; whole-lot finance retained');
