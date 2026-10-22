#!/usr/bin/env node
/** Dependency-free checks for the standalone HEXA V0 demo. Run: node verify.mjs */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(here, 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const match = html.match(/\/\* DEMO_LOGIC_START \*\/([\s\S]*?)\/\* DEMO_LOGIC_END \*\//);
if (!match) throw new Error('DEMO_LOGIC markers are missing');
const sandbox = { console };
vm.createContext(sandbox);
vm.runInContext(`${match[1]}\n;this.api = { DEMO_DATA, INITIAL_STATE, ROLE_IDS, UNKNOWN, initialState, reduceState, ltlState, timeFactsFor, auditEventsFor, ltlJourney, fclJourney, renderView, dialogFor };`, sandbox, { filename: 'hexa-v0-inline-logic.js' });
const api = sandbox.api;
const clone = value => JSON.parse(JSON.stringify(value));
const state = (role = 'lg', step = 0, shipment = 'ltl') => ({ role, step, shipment, copyCount: 0 });
let passed = 0;
let failed = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passed += 1;
    results.push({ name, status: 'PASS' });
    console.log(`PASS ${String(passed + failed).padStart(2, '0')} · ${name}`);
  } catch (error) {
    failed += 1;
    results.push({ name, status: 'FAIL', error: error.message });
    console.error(`FAIL ${String(passed + failed).padStart(2, '0')} · ${name}\n  ${error.stack || error.message}`);
  }
}

test('Offline artifact: no external resource, API call, storage or runtime dependency', () => {
  assert.ok(!/(?:src|href)=["']https?:\/\//i.test(html));
  assert.ok(!/@import\s|fetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|WebSocket/i.test(html));
  assert.ok(!/<script[^>]+src=/i.test(html));
  assert.ok(!/<link[^>]+rel=["']stylesheet/i.test(html));
  assert.match(html, /DEMO \/ KHÔNG PHẢI LÔ THẬT/);
  assert.match(html, /data-action="reset"/);
});

test('Exactly two role views; role toggle is explicitly not a security claim', () => {
  assert.deepEqual(Array.from(api.ROLE_IDS), ['lg', 'tt']);
  const roleControls = [...html.matchAll(/data-action="set-role" data-role="(lg|tt)"/g)];
  assert.equal(roleControls.length, 2);
  assert.match(html, /không phải bằng chứng bảo mật đa khách hàng/);
  assert.doesNotMatch(html, /data-role="(?:admin|customer|sale|support)"/);
});

test('Initial LTL state keeps an unverified warehouse rumor out of ETA and commitment', () => {
  const initial = state('lg', 0);
  const s = api.ltlState(initial);
  assert.equal(s.eta, api.UNKNOWN);
  assert.equal(s.committed, '26/10/2026 14:00–15:00 (GMT+7)');
  assert.match(s.unverified, /CHƯA XÁC MINH/);
  const rendered = api.renderView(initial);
  assert.match(rendered, /Chưa cần chọn lịch mới/);
  assert.doesNotMatch(rendered, /27\/10\/2026 09:30/);
  assert.match(rendered, /Lịch khách yêu cầu/);
});

test('Four-state path: TT verifies ETA, LG responds, TT confirms the final plan', () => {
  let current = state('lg', 0);
  current = api.reduceState(current, { type: 'SET_ROLE', role: 'tt' });
  current = api.reduceState(current, { type: 'VERIFY_ETA' });
  assert.equal(current.step, 1);
  assert.equal(api.ltlState(current).eta, '27/10/2026 09:30 (GMT+7)');
  assert.equal(api.ltlState(current).committed, api.UNKNOWN);
  current = api.reduceState(current, { type: 'SET_ROLE', role: 'lg' });
  current = api.reduceState(current, { type: 'SUBMIT_WINDOW' });
  assert.equal(current.step, 2);
  assert.equal(api.ltlState(current).vehicle, api.UNKNOWN);
  current = api.reduceState(current, { type: 'SET_ROLE', role: 'tt' });
  current = api.reduceState(current, { type: 'CONFIRM_PLAN' });
  assert.equal(current.step, 3);
  assert.equal(api.ltlState(current).committed, '27/10/2026 10:30–11:30 (GMT+7)');
  assert.equal(api.ltlState(current).delivery, api.UNKNOWN);
});

test('Wrong role cannot perform the other role’s simulated transition', () => {
  assert.equal(api.reduceState(state('lg', 0), { type: 'VERIFY_ETA' }).step, 0);
  assert.equal(api.reduceState(state('tt', 1), { type: 'SUBMIT_WINDOW' }).step, 1);
  assert.equal(api.reduceState(state('lg', 2), { type: 'CONFIRM_PLAN' }).step, 2);
});

test('Verified ETA shows impact but is not presented as a commitment', () => {
  const current = state('lg', 1);
  const s = api.ltlState(current);
  assert.match(s.impact, /17 giờ 30 phút/);
  assert.match(s.committedNote, /không tự trở thành cam kết/);
  const rendered = api.renderView(current);
  assert.match(rendered, /27\/10\/2026 09:30 \(GMT\+7\)/);
  assert.match(rendered, /Phản hồi khung giờ kho có thể nhận hàng/);
  assert.match(rendered, /trễ 17 giờ 30 phút/);
});

test('LG response is recorded without dispatching a vehicle or completing TT work', () => {
  const current = state('tt', 2);
  const s = api.ltlState(current);
  assert.match(s.response, /Đã ghi nhận/);
  assert.match(s.response, /chưa tự điều phối xe/);
  assert.equal(s.vehicle, api.UNKNOWN);
  assert.match(s.ttTitle, /Điều phối xe/);
  assert.match(api.renderView(current), /công việc TT chưa hoàn tất/);
});

test('Final plan keeps customer request, ETA and commitment as separate facts in both roles', () => {
  const lg = state('lg', 3);
  const tt = state('tt', 3);
  assert.equal(JSON.stringify(api.timeFactsFor(lg)), JSON.stringify(api.timeFactsFor(tt)));
  for (const rendered of [api.renderView(lg), api.renderView(tt)]) {
    assert.match(rendered, /26\/10\/2026 16:00 \(GMT\+7\)/);
    assert.match(rendered, /27\/10\/2026 10:30 \(GMT\+7\)/);
    assert.match(rendered, /27\/10\/2026 10:30–11:30 \(GMT\+7\)/);
    assert.match(rendered, /Chưa xác nhận/);
  }
  const delivery = api.ltlJourney(lg).find(node => node.id === 'delivery');
  assert.equal(delivery.status, 'WAITING');
  assert.match(delivery.evidence, /Đã giao: Chưa xác nhận/);
});

test('Role toggle preserves shipment and event state; Reset restores the initial view', () => {
  const before = state('tt', 2, 'ltl');
  const after = api.reduceState(before, { type: 'SET_ROLE', role: 'lg' });
  assert.equal(after.shipment, 'ltl');
  assert.equal(after.step, 2);
  assert.equal(JSON.stringify(api.timeFactsFor(after)), JSON.stringify(api.timeFactsFor(before)));
  const reset = api.reduceState({ ...after, copyCount: 4 }, { type: 'RESET' });
  assert.equal(JSON.stringify(reset), JSON.stringify(api.initialState()));
});

test('Every LTL state has a demo role owner and a next update deadline', () => {
  for (const s of api.DEMO_DATA.ltl.states) {
    assert.ok(s.responsible.includes('vai trò demo'));
    assert.match(s.nextUpdate, /GMT\+7/);
    assert.ok(s.lastCustomerUpdate.length > 10);
  }
});

test('Active task maps to a short popup with no more than four essential fields', () => {
  for (const role of ['lg', 'tt']) {
    for (let step = 0; step < 4; step += 1) {
      const popup = api.dialogFor('active', state(role, step));
      assert.ok(popup.title.length > 0);
      assert.ok(popup.fields.length <= 4, `${role}/${step}: ${popup.fields.length} fields`);
      assert.doesNotMatch(popup.html, /<form|type="file"|Gửi email|Gửi Zalo/);
    }
  }
});

test('Copying customer text does not send an update or advance the event state', () => {
  const before = state('tt', 1);
  const beforeUpdate = api.ltlState(before).lastCustomerUpdate;
  const after = api.reduceState(before, { type: 'COPY_CUSTOMER_UPDATE' });
  assert.equal(after.step, before.step);
  assert.equal(after.copyCount, before.copyCount + 1);
  assert.equal(api.ltlState(after).lastCustomerUpdate, beforeUpdate);
  const popup = api.dialogFor('customer-update', after);
  assert.match(popup.html, /Sao chép ≠ đã gửi email\/Zalo/);
  assert.doesNotMatch(popup.html, /data-command="SEND/);
});

test('An attached file is not promoted to an accepted document', () => {
  assert.equal(api.DEMO_DATA.ltl.document.status, 'Tệp đã ghi nhận');
  assert.equal(api.DEMO_DATA.ltl.document.accepted, api.UNKNOWN);
  const popup = api.dialogFor('document', state('lg', 0));
  assert.match(popup.html, /không tự trở thành chứng từ đã được chấp nhận/);
  assert.match(popup.html, /Chưa xác nhận/);
});

test('Payment proof does not prove factory release or money received by TT', () => {
  const p = api.DEMO_DATA.ltl.payment;
  assert.equal(p.factoryRelease, api.UNKNOWN);
  assert.equal(p.ttReceipt, api.UNKNOWN);
  for (const role of ['lg', 'tt']) {
    const rendered = api.renderView(state(role, 0));
    assert.match(rendered, /không đồng nghĩa nhà máy đã xác nhận cho xuất/);
    assert.match(rendered, /không phải tiền TT đã thu/);
  }
});

test('LG rendering excludes TT-only internal references and commercial internals', () => {
  const lg = api.renderView(state('lg', 2));
  const tt = api.renderView(state('tt', 2));
  assert.doesNotMatch(lg, /TT-INNER-756/);
  assert.match(tt, /TT-INNER-756/);
  const visibleText = lg.replace(/<[^>]*>/g, ' ');
  assert.doesNotMatch(visibleText, /Giá vốn|\bmargin\b|lợi nhuận nội bộ/i);
});

test('Audit trail exposes source, verifier, version and ETA changes through the selected state', () => {
  const final = state('lg', 3);
  const events = api.auditEventsFor(final);
  assert.equal(events.length, 5);
  for (const event of events) {
    for (const key of ['version', 'source', 'verifiedBy', 'etaChange']) assert.ok(event[key], `${key} missing`);
  }
  const audit = api.dialogFor('audit', final).html;
  assert.match(audit, /LTL-v0/);
  assert.match(audit, /26\/10\/2026 11:00/);
  assert.match(audit, /27\/10\/2026 09:30/);
  assert.match(audit, /LTL-v4/);
  assert.equal(api.auditEventsFor(state('lg', 1)).length, 3);
});

test('FCL has distinct SI, VGM and CY cutoffs, all with explicit timezone', () => {
  const f = api.DEMO_DATA.fcl;
  assert.notEqual(f.si.cutoff, f.vgm.cutoff);
  assert.notEqual(f.vgm.cutoff, f.cyCutoff);
  for (const value of [f.si.cutoff, f.vgm.cutoff, f.cyCutoff]) assert.match(value, /GMT\+7/);
  const rendered = api.renderView(state('tt', 0, 'fcl'));
  assert.match(rendered, /SI cutoff/);
  assert.match(rendered, /VGM cutoff/);
  assert.match(rendered, /CY cutoff/);
  assert.match(rendered, /BK-DEMO-02/);
});

test('SI sent and SI accepted are separate events; submitted-only is not complete', () => {
  const f = api.DEMO_DATA.fcl;
  assert.notEqual(f.si.submittedAt, f.si.acceptedAt);
  assert.equal(api.fclJourney().find(node => node.id === 'si-vgm').status, 'COMPLETED');
  const changed = clone(api.DEMO_DATA);
  changed.fcl.si.status = 'SUBMITTED';
  changed.fcl.si.acceptedAt = '';
  const node = api.fclJourney(changed).find(item => item.id === 'si-vgm');
  assert.equal(node.status, 'CURRENT');
  assert.match(node.evidence, /SI chấp nhận: Chưa xác nhận/);
});

test('ETD is never used as proof of ATD when actual departure is missing', () => {
  const changed = clone(api.DEMO_DATA);
  changed.fcl.atdActual = '';
  const node = api.fclJourney(changed).find(item => item.id === 'etd');
  assert.equal(node.status, 'UPCOMING');
  assert.match(node.evidence, /ETD kế hoạch: 25\/10\/2026 20:00/);
  assert.match(node.evidence, /ATD thực tế: Chưa xác nhận/);
});

test('Arrival and customs clearance remain independent operational facts', () => {
  const changed = clone(api.DEMO_DATA);
  changed.fcl.customsClearanceAt = '';
  const nodes = api.fclJourney(changed);
  assert.equal(nodes.find(node => node.id === 'arrival').status, 'COMPLETED');
  assert.equal(nodes.find(node => node.id === 'customs-import').status, 'UPCOMING');
  assert.match(nodes.find(node => node.id === 'customs-import').evidence, /Chưa xác nhận/);
  assert.notEqual(api.DEMO_DATA.fcl.arrivalAt, api.DEMO_DATA.fcl.customsClearanceAt);
});

test('Partial delivery never completes the whole FCL shipment', () => {
  const f = api.DEMO_DATA.fcl;
  assert.equal(f.deliveredPackages, 4);
  assert.equal(f.totalPackages, 8);
  assert.equal(f.fullDelivery, api.UNKNOWN);
  const node = api.fclJourney().find(item => item.id === 'delivery');
  assert.equal(node.status, 'CURRENT');
  assert.match(node.evidence, /4\/8 kiện/);
  assert.match(node.evidence, /Hoàn tất toàn lô: Chưa xác nhận/);
});

test('LTL rendering does not leak SEA-only SI/VGM/CY fields', () => {
  for (const role of ['lg', 'tt']) {
    const rendered = api.renderView(state(role, 3, 'ltl'));
    assert.doesNotMatch(rendered, /SI cutoff|VGM cutoff|CY cutoff|SI \/ VGM|GATE-IN \/ CY/);
    assert.match(rendered, /NHẬN &amp; GHÉP HÀNG \(LTL\)/);
    assert.match(rendered, /QUA CỬA KHẨU/);
  }
});

test('Source-level responsive order puts urgent work before Journey on mobile and desktop', () => {
  assert.match(html, /<meta name="viewport" content="width=device-width, initial-scale=1">/);
  assert.match(html, /@media \(max-width: 640px\)/);
  for (const viewportState of [state('lg', 0), state('tt', 0), state('lg', 0, 'fcl')]) {
    const rendered = api.renderView(viewportState);
    assert.ok(rendered.indexOf('id="urgent-action"') < rendered.indexOf('id="journey-panel"'));
    if (viewportState.shipment === 'ltl') {
      assert.ok(rendered.indexOf('id="urgent-action"') < rendered.indexOf('class="state-stepper"'));
    }
  }
  assert.match(html, /\.journey-scroll \{ overflow-x: auto;/);
});

test('No Vietnamese typo markers or placeholder TODOs remain in the demo logic', () => {
  assert.doesNotMatch(html, /Thờỉ|Ngườỉ|\bTODO\b|\bTBD\b|lorem ipsum/i);
});

const summary = { total: passed + failed, passed, failed, results };
console.log(`\nHEXA_V0_LOGIC=${failed === 0 ? 'PASS' : 'FAIL'} | TOTAL=${summary.total} | PASS=${passed} | FAIL=${failed}`);
if (process.argv.includes('--json')) console.log(JSON.stringify(summary, null, 2));
if (failed > 0) process.exitCode = 1;
