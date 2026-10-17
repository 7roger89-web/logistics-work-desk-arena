// PR #205 repair only: historical SELL must never become BUY COST.
// Pure matcher/provenance tests; synthetic facts, no DB or original workbook.
import assert from 'node:assert/strict';
import { importTs } from './lib_loader.mjs';

const { findComparableCosts, costReferenceIssue } = await importTs('component/src/lib/costHistory.ts');
const criteria = { incoterm: 'EXW', mode: 'Sea', origin: 'NANSHA', destination: 'HAI PHONG', cbm: null, weightKg: null, targetDate: '2026-10-16' };
const shipment = (id, actual, extra = {}) => ({
  id, customer: 'SYNTHETIC historical reference', incoterm: 'EXW', mode: 'Sea', createdAt: '2026-10-15',
  transport: { pol: 'NANSHA', pod: 'HAI PHONG' },
  finance: { currency: 'VND', profit: 8000000, actual,
    quote: [{ label: 'Historical quoted SELL', amount: 40000000, ccy: 'VND', qty: 1 }], ...extra },
});
const actual = (cost, extra = {}) => ({ id: 'actual-line-1', label: 'Historical ACTUAL', unit: 'CONT', qty: 1, price: 40000000, amount: 40000000, cost, ccy: 'VND', vat: null, ...extra });
const inputRate = (id, validUntil = '2026-12-31') => ({ id, status: 'ACTIVE', supplier: 'SYNTHETIC supplier', received_at: '2026-10-15', rows: [{
  id: 'rate-line-1', kind: 'CHARGE', status: 'AVAILABLE', chargeLabel: 'Supplier BUY', amount: 31800000, currency: 'VND', unit: 'CONT',
  equipment: '20GP', origin: { name: 'NANSHA' }, destination: { name: 'HAI PHONG' }, validUntil, conditionalAmounts: [],
}] });
const deepFreeze = (value) => { if (value && typeof value === 'object') { Object.freeze(value); for (const v of Object.values(value)) deepFreeze(v); } return value; };
const histories = deepFreeze([
  shipment('QUOTE-40-NO-COST', []),
  shipment('ACTUAL-40-UNKNOWN', [actual(null)]),
  shipment('ACTUAL-40-COST-32', [actual(32000000)]),
]);
const rates = deepFreeze([inputRate('RATE-31.8'), inputRate('RATE-EXPIRED', '2026-07-31'), inputRate('RATE-UNKNOWN-VALIDITY', '')]);
const before = JSON.stringify({ histories, rates });
const matches = findComparableCosts(histories, criteria, rates);
const get = (id) => { const m = matches.find((m) => m.shipmentId === id || m.referenceId.startsWith(id + ':')); assert.ok(m, id); return m; };

// Fails on reviewed head: actualLines() falls back to selling 40000000.
const missing = get('ACTUAL-40-UNKNOWN');
assert.equal(missing.lines[0].price, null, 'ACTUAL cost UNKNOWN must stay UNKNOWN, never fall back to price/amount SELL 40000000');
assert.match(costReferenceIssue(missing, missing.lines[0]), /chưa biết giá vốn/i);
console.log('PASS ACTUAL sell 40000000 / cost UNKNOWN → no cost; never fallback to selling');

const quote = get('QUOTE-40-NO-COST');
assert.equal(quote.lines[0].price, 40000000, 'keep quoted SELL for comparison');
assert.equal(quote.lines[0].priceBasis, 'HISTORICAL_SELL');
assert.match(costReferenceIssue(quote, quote.lines[0]), /Giá đã báo\/dự kiến — không phải giá vốn/);
console.log('PASS QUOTE SELL 40000000 remains comparison-only, ineligible as cost');

const booked = get('ACTUAL-40-COST-32');
assert.equal(booked.lines[0].price, 32000000);
assert.equal(booked.lines[0].priceBasis, 'ACTUAL_COST');
assert.equal(costReferenceIssue(booked, booked.lines[0]), '');
assert.match(booked.lines[0].priceProvenance, /ACTUAL-40-COST-32.*actual-line-1.*finance\.actual\.cost/);
assert.equal(booked.lines[0].ccy, 'VND'); assert.equal(booked.lines[0].unit, 'CONT');
console.log('PASS ACTUAL sell 40000000 / cost 32000000 → only 32000000 with source field/currency/unit provenance');

const supplier = get('RATE-31.8');
assert.equal(supplier.lines[0].price, 31800000);
assert.equal(supplier.lines[0].priceBasis, 'SUPPLIER_RATE');
assert.equal(costReferenceIssue(supplier, supplier.lines[0]), '');
assert.match(supplier.lines[0].priceProvenance, /RATE-31\.8.*rate-line-1.*rows\.amount/);
console.log('PASS INPUT_RATE supplier BUY 31800000 is eligible with supplier row provenance');

assert.equal(get('RATE-EXPIRED').expired, true);
assert.equal(get('RATE-EXPIRED').lines[0].validityStatus, 'EXPIRED');
assert.equal(get('RATE-UNKNOWN-VALIDITY').lines[0].validityStatus, 'UNKNOWN');
assert.ok(get('RATE-UNKNOWN-VALIDITY').differences.some((s) => s.includes('chưa rõ hiệu lực')));
console.log('PASS expired/unknown validity warnings retained, not promoted to current');

for (const [id, line, extra] of [
  ['NO-UNIT', actual(32000000, { unit: '' }), {}],
  ['NO-CCY', actual(32000000, { ccy: '' }), { currency: '' }],
  ['UNSUPPORTED-CCY', actual(32000000, { ccy: 'ZZZ' }), {}],
  ['INVALID-COST', actual(NaN), {}],
  ['NEGATIVE-COST', actual(-1), {}],
]) {
  const m = findComparableCosts([shipment(id, [line], extra)], criteria)[0];
  assert.ok(costReferenceIssue(m, m.lines[0]), id + ' must not be selectable');
  if (id === 'NO-CCY') { assert.equal(m.lines[0].ccy, ''); assert.deepEqual(m.totalsByCurrency, [], 'do not invent VND for an unknown-currency cost'); }
}
const zero = findComparableCosts([shipment('EXPLICIT-ZERO', [actual(0)])], criteria)[0];
assert.equal(zero.lines[0].price, 0); assert.equal(costReferenceIssue(zero, zero.lines[0]), '');
assert.ok(costReferenceIssue(booked, { ...booked.lines[0], priceBasis: undefined }), 'unclassified references fail closed');
assert.ok(costReferenceIssue(quote, { ...booked.lines[0] }), 'QUOTE cannot be made BUY by amount or metadata alone');
console.log('PASS currency/unit/finite-cost prerequisites; explicit zero preserved; unknown/QUOTE metadata cannot bypass guard');

assert.equal(JSON.stringify({ histories, rates }), before, 'pure lookup must not mutate historical cost/sell/profit/rates');
console.log('PASS historical selling/cost/profit and supplier snapshots unchanged (deep-frozen inputs)');
