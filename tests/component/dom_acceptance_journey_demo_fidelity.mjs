// Geometry oracle extracted from the approved, immutable prototype B, not app code.
// Usage: node tests/component/dom_acceptance_journey_demo_fidelity.mjs fixture.json [bundle.js]
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(root, 'component/package.json'));
const { JSDOM } = require('jsdom');
const fixture = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const oracle = JSON.parse(readFileSync(path.join(root, 'tests/component/fixtures/journey_demo_b_geometry.json'), 'utf8'));
const dom = new JSDOM('<!doctype html><body><div id="host"></div>', {url:'http://localhost:9501',pretendToBeVisual:true});
globalThis.window=dom.window; globalThis.document=dom.window.document;
Object.defineProperty(globalThis,'navigator',{value:dom.window.navigator,configurable:true});
for (const k of ['HTMLElement','HTMLInputElement','HTMLSelectElement','HTMLTextAreaElement','Event','MouseEvent','Node','MutationObserver','getComputedStyle']) globalThis[k]=dom.window[k];
dom.window.HTMLElement.prototype.scrollIntoView=()=>{};
// Deterministic viewport exercises fit math; this is not a real CSS-layout oracle.
Object.defineProperty(dom.window.HTMLElement.prototype,'clientWidth',{get(){return this.dataset.testid==='journey-map-viewport'?800:0;}});
Object.defineProperty(dom.window.HTMLElement.prototype,'clientHeight',{get(){return this.dataset.testid==='journey-map-viewport'?760:0;}});
const mount=(await import(pathToFileURL(path.resolve(process.argv[3] || path.join(root,'component/dist/logi-shell.js'))))).default;
const triggers=[];
mount({name:'logi_shell',data:fixture.before,parentElement:document.getElementById('host'),setTriggerValue:(event,value)=>triggers.push({event,value})});
const tick=()=>new Promise(r=>setTimeout(r,100));
const byId=id=>document.querySelector(`[data-testid="${id}"]`);
const click=async el=>{assert.ok(el,'click target');el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await tick();};
const button=(text,parent=document)=>[...parent.querySelectorAll('button')].find(e=>e.textContent.trim()===text);
await tick(); await click([...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Lô Hàng'));
await click(byId('shipment-period-tat-ca'));await click([...document.querySelectorAll('main a')].find(a=>a.textContent.trim()==='SEA-160'));
for(const [id,p] of Object.entries(oracle.positions)) {
  if(['start','completed'].includes(id))continue;
  const el=byId(`journey-node-${id}`);assert.ok(el,id);
  assert.deepEqual({x:parseFloat(el.style.left),y:parseFloat(el.style.top),w:parseFloat(el.style.width),h:parseFloat(el.style.height)},p,`${id}: approved demo B geometry`);
}
assert.ok(byId('journey-parallel-branch'),'visible SI/VGM + Gate-in group');
assert.equal(document.querySelector('path[data-from="customs-export"][data-to="si-vgm"]').getAttribute('d'),'M636,208 C660,208 660,124 684,124');
assert.equal(document.querySelector('path[data-from="customs-export"][data-to="gate-in"]').getAttribute('d'),'M636,208 C660,208 660,292 684,292');
assert.ok(byId('journey-overview-panel'));
const fit=byId('journey-map-transform').style.transform;
await click(button('+'));assert.notEqual(byId('journey-map-transform').style.transform,fit,'zoom changes transform');
await click(button('⤢ Fit Journey'));assert.equal(byId('journey-map-transform').style.transform,fit,'fit restores transform');
await click(button('↺ Reset View'));assert.equal(byId('journey-map-transform').style.transform,'translate(24px, 20px) scale(1)');
byId('journey-map-viewport').dispatchEvent(new MouseEvent('pointerdown',{bubbles:true,button:0,clientX:10,clientY:10}));
window.dispatchEvent(new MouseEvent('pointermove',{clientX:50,clientY:42}));
window.dispatchEvent(new MouseEvent('pointerup',{clientX:50,clientY:42}));await tick();
assert.equal(byId('journey-map-transform').style.transform,'translate(64px, 52px) scale(1)','pan follows pointer delta');
byId('journey-node-si-vgm').dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));await tick();
assert.ok(byId('journey-overview-panel'),'drag-end mouse click does not accidentally select');
for(const id of Object.keys(oracle.positions).filter(id=>!['start','completed'].includes(id))){
  await click(byId(`journey-node-${id}`));assert.ok(byId('journey-side-panel').contains(byId('journey-quick-panel')),`${id}: right-side quick panel`);
}
await click(byId('journey-node-si-vgm'));await click(byId('journey-open-workspace'));
assert.ok(byId('journey-side-panel').contains(byId('journey-stage-workspace')),'real work replaces Quick Panel on the right');
assert.equal(document.querySelectorAll('[data-testid="journey-quick-panel"]').length,1,'only stage header, no duplicate Quick Panel');
await click(byId('journey-collapse-map'));assert.ok(byId('journey-map-rail'));assert.equal(byId('journey-map-viewport'),null);
await click(button('← Quick panel'));assert.ok(byId('journey-map-viewport'),'quick view restores full map');
await click(button('Toàn bộ lô hàng',byId('shipment-journey')));assert.ok(byId('journey-global-workspace'));
assert.ok(byId('shipment-execution-profile'),'current app process remains available');
assert.equal(triggers.length,0,'selection, zoom, fit, collapse and workspace navigation emit no business writes');
console.log('PASS demo B: 11 exact reference positions, parallel group/routes, fit/zoom/reset/pan, drag guard, all node selections, right-side workspace, collapse/expand, global process, zero navigation writes');
process.exit(0);
