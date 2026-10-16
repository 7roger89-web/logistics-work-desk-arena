// PR #205 repair: actual built app, native Streamlit → React/C1 channel.
// Start quote_cost_sandbox.py first. Only disposable SANDBOX_STAGING data.
// Historical records are seeded in the REAL schema, not injected view models;
// supplier rates and workbook upload go through the existing app UI.
import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const url = process.argv[2] || 'http://127.0.0.1:9521';
const evidence = path.resolve(root, process.argv[3] || 'evidence/pr205-historical-sell-buy-cost');
const scratch = path.join(root, '.tmp/pr205-cost-provenance');
mkdirSync(evidence, { recursive: true }); mkdirSync(scratch, { recursive: true });
const fixture = path.join(scratch, 'luc-giac-SYNTHETIC.xlsx');
execFileSync(process.env.PYTHON || path.join(root, '.venv/bin/python'), ['scripts/make_luc_giac_quote_fixture.py', fixture], { cwd: root });
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
  headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage', '--no-zygote'],
  env: process.env.CHROMIUM_LIB_PATH ? { ...process.env, LD_LIBRARY_PATH: process.env.CHROMIUM_LIB_PATH } : process.env });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.setDefaultTimeout(15000);
const errors = [], checks = [], observations = {};
page.on('pageerror', (e) => errors.push(e.message));
page.on('dialog', (d) => d.accept());
const ok = (text) => { checks.push(text); console.log('PASS ' + text); };
const fresh = async () => page.locator('[data-testid="excel-quote-workspace"][data-preview-current="true"]').waitFor({ timeout: 30000 });
const ref = (id) => page.locator(`[data-testid="excel-cost-reference"][data-reference-id="${id}"]`);
const search = async (query) => { await page.getByTestId('excel-cost-search').fill(query); };
const capture = async (id, name) => {
  while (await page.locator('.toast-in button').count()) await page.locator('.toast-in button').first().click();
  await page.getByTestId(id).evaluate((el) => { const shell = el.closest('.logi-shell'); shell.scrollTop += el.getBoundingClientRect().top - shell.getBoundingClientRect().top - 76; });
  await page.screenshot({ path: path.join(evidence, name) });
};
const addRate = async (supplier, date) => {
  await page.getByTestId('cost-rate-raw').fill('OOCL\nNANSHA-HAIPHONG\nO/F VND31800000/20GP' + (date ? ` 有效期到 ${date}` : ''));
  await page.getByLabel('Nguồn / người báo (nếu biết)').fill(supplier);
  await page.getByTestId('cost-rate-parse').click();
  await page.getByTestId('cost-rate-save').click();
  await page.getByTestId('cost-rate-history').getByText(supplier, { exact: true }).first().waitFor();
};
try {
  await page.goto(url);
  await page.getByRole('link', { name: 'Báo Giá', exact: true }).first().waitFor({ timeout: 60000 });
  assert.equal(await page.getByTestId('role-preview-switcher').count(), 1, 'BLOCKED: not isolated SANDBOX_STAGING');
  assert.match(await page.locator('.global-footer').innerText(), /staging cách ly/);
  await page.getByRole('link', { name: 'Báo Giá', exact: true }).first().click();
  await page.getByTestId('quote-workspace-kho-gia-von').click();
  await addRate('PR205-INPUT-VALID — SYNTHETIC', '31/12/2027');
  await addRate('PR205-INPUT-EXPIRED — SYNTHETIC', '31/07/2026');
  await addRate('PR205-INPUT-UNKNOWN — SYNTHETIC', '');
  ok('Valid/expired/unknown supplier snapshots created via existing Cost Intelligence UI');
  await page.getByTestId('quote-workspace-bao-gia').click();
  await page.getByTestId('quote-excel-open').click();
  await page.getByTestId('excel-customer-toggle').click();
  await page.getByTestId('excel-customer-search').fill('CUST-ANPHAT');
  await page.getByTestId('excel-customer').getByRole('button', { name: /An Phát JSC/ }).click();
  await page.getByTestId('excel-upload').setInputFiles(fixture);
  await page.getByTestId('excel-apply').waitFor(); await fresh();
  await page.getByTestId('excel-apply').click();
  await page.getByTestId('excel-next').click();
  await page.getByTestId('excel-equipment').selectOption('20GP');
  await page.getByTestId('excel-pol').fill('NANSHA');
  await page.getByTestId('excel-pod').fill('HAI PHONG');
  await fresh();
  assert.equal(await page.getByTestId('excel-fee-1').count(), 0);

  await search('PR205-QUOTE-SELL40');
  const quoted = ref('PR205-QUOTE-SELL40'); await quoted.waitFor();
  assert.match(await quoted.innerText(), /40\.000\.000 VND/);
  assert.match(await quoted.innerText(), /Giá đã báo\/dự kiến — không phải giá vốn/);
  assert.equal(await quoted.getByTestId('excel-pick-cost-1').isEnabled(), false);
  await quoted.getByTestId('excel-pick-cost-1').evaluate((el) => el.click());
  assert.equal(await page.getByTestId('excel-fee-1').count(), 0);
  observations.quote = { sell: 40000000, displayedForComparison: true, costPickEnabled: false, addedFees: 0 };
  await capture('excel-cost-picker', '01-quote-sell40-comparison-only-1440x900.png');
  ok('QUOTE SELL 40000000: explicit non-cost label, disabled action, no fee appended');

  await search('PR205-ACTUAL-UNKNOWN');
  const missing = ref('PR205-ACTUAL-UNKNOWN'); await missing.waitFor();
  assert.match(await missing.locator('.eq-cost-result b').innerText(), /Chưa xác định/);
  assert.doesNotMatch(await missing.locator('.eq-cost-result b').innerText(), /40\.000\.000/);
  assert.match(await missing.innerText(), /Chưa biết giá vốn thực tế — không dùng giá bán thay thế/);
  assert.equal(await missing.getByTestId('excel-pick-cost-1').isEnabled(), false);
  await missing.getByTestId('excel-pick-cost-1').evaluate((el) => el.click());
  assert.equal(await page.getByTestId('excel-fee-1').count(), 0);
  observations.actualUnknown = { historicalSell: 40000000, cost: null, costPickEnabled: false, addedFees: 0 };
  await capture('excel-cost-picker', '02-actual-unknown-no-sell-fallback-1440x900.png');
  ok('ACTUAL SELL 40000000 / COST UNKNOWN: unknown displayed, disabled action, no selling fallback');

  await search('PR205-ACTUAL-COST32');
  const booked = ref('PR205-ACTUAL-COST32'); await booked.waitFor();
  assert.match(await booked.locator('.eq-cost-result b').innerText(), /32\.000\.000 VND \/ CONT/);
  assert.doesNotMatch(await booked.locator('.eq-cost-result b').innerText(), /40\.000\.000/);
  assert.match(await booked.innerText(), /PR205-ACTUAL-COST32-LINE.*finance\.actual\.cost/);
  assert.equal(await booked.getByTestId('excel-pick-cost-1').isEnabled(), true);
  await booked.getByTestId('excel-pick-cost-1').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-1-cost').inputValue(), '32000000');
  assert.equal(await page.getByTestId('excel-fee-1-sell').inputValue(), '');
  assert.equal(await page.getByTestId('excel-fee-1-confirmed').isChecked(), false);
  assert.match(await page.getByTestId('excel-fee-1-source').innerText(), /finance\.actual\.cost.*VND\/CONT/);
  assert.match(await page.getByTestId('excel-fee-1-source').innerText(), /CHƯA RÕ HIỆU LỰC/);
  observations.actualCost = { historicalSell: 40000000, selectedCost: 32000000, newSell: '', newSellConfirmed: false, currency: 'VND', unit: 'CONT', sourceField: 'finance.actual.cost' };
  await capture('excel-fee-1', '03-actual-cost32-new-sell-blank-1440x900.png');
  ok('ACTUAL SELL 40000000 / COST 32000000: only 32000000 selected, provenance retained, new sell blank after backend preview');

  await search('PR205-INPUT-VALID');
  const supplier = page.getByTestId('excel-cost-reference').filter({ hasText: 'PR205-INPUT-VALID' });
  await supplier.waitFor();
  assert.equal(await supplier.getAttribute('data-source'), 'INPUT_RATE');
  assert.match(await supplier.innerText(), /Hiệu lực nguồn: 2027-12-31/);
  assert.match(await supplier.innerText(), /rows\.amount/);
  const snapshotId = (await supplier.getAttribute('data-reference-id')).split(':')[0];
  assert.equal(await supplier.getByTestId('excel-pick-cost-1').isEnabled(), true);
  await supplier.getByTestId('excel-pick-cost-1').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-2-cost').inputValue(), '31800000');
  assert.equal(await page.getByTestId('excel-fee-2-cost').isEditable(), false);
  assert.equal(await page.getByTestId('excel-fee-2-sell').inputValue(), '');
  assert.equal(await page.getByTestId('excel-fee-2-confirmed').isChecked(), false);
  // C1 rehydrates linked supplier fields from the immutable snapshot, replacing
  // the browser note with authoritative supplier/snapshot/row provenance.
  const supplierSource = await page.getByTestId('excel-fee-2-source').innerText();
  assert.ok(supplierSource.includes(snapshotId));
  assert.match(supplierSource, /PR205-INPUT-VALID.*line-1/s);
  observations.inputRate = { selectedCost: 31800000, newSell: '', newSellConfirmed: false, lockedSupplierCost: true };
  await capture('excel-fee-2', '04-input-rate318-new-sell-blank-1440x900.png');
  ok('INPUT_RATE 31800000: selectable genuine supplier rate, immutable cost source, new sell blank after backend preview');

  await search('PR205-INPUT-EXPIRED');
  assert.match(await page.getByTestId('excel-cost-reference').innerText(), /ĐÃ HẾT HẠN/);
  await capture('excel-cost-picker', '05-expired-warning-retained-1440x900.png');
  await search('PR205-INPUT-UNKNOWN');
  assert.match(await page.getByTestId('excel-cost-reference').innerText(), /CHƯA RÕ HIỆU LỰC/);
  ok('Expired and unknown-validity supplier warnings retained, never relabelled current');
  assert.equal(await page.getByTestId('excel-fee-3').count(), 0);
  assert.equal(await page.getByTestId('excel-quote-workspace').getAttribute('data-saved-id'), '');
  ok('Cost selection only edits a new unsaved quote; no automatic create/send or old shipment write');

  await page.setViewportSize({ width: 390, height: 844 });
  await search('PR205-QUOTE-SELL40');
  await capture('excel-cost-picker', '06-mobile-quote-not-cost-390x844.png');
  const layout = await page.getByTestId('excel-quote-workspace').evaluate((el) => ({
    viewport: innerWidth, documentWidth: document.documentElement.scrollWidth,
    shellOverflow: el.closest('.logi-shell').scrollWidth - el.closest('.logi-shell').clientWidth,
  }));
  assert.ok(layout.documentWidth <= layout.viewport + 1 && layout.shellOverflow <= 1, JSON.stringify(layout));
  assert.equal(await quoted.getByTestId('excel-pick-cost-1').isEnabled(), false);
  observations.mobile = layout;
  ok('Mobile 390×844: comparison-only QUOTE remains disabled and no horizontal page/shell overflow');

  // Same CostCheck feature/ranking/search surface, guarded against another
  // historical-SELL → legacy quote cost path. Navigation, no old-record edits.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole('button', { name: 'Danh sách báo giá', exact: true }).click();
  await page.getByTestId('quote-workspace-check-chi-phi').click();
  await page.getByTestId('cost-incoterm').fill('EXW');
  await page.getByTestId('cost-pol').fill('NANSHA');
  await page.getByTestId('cost-pod').fill('HAI PHONG');
  await page.getByTestId('cost-search').click();
  for (const id of ['PR205-QUOTE-SELL40', 'PR205-ACTUAL-UNKNOWN']) {
    const result = page.locator(`[data-testid="cost-result"][data-shipment-id="${id}"]`);
    await result.waitFor();
    assert.equal(await result.getByRole('button', { name: 'DÙNG LÀM GIÁ VỐN', exact: true }).isEnabled(), false);
  }
  const actualResult = page.locator('[data-testid="cost-result"][data-shipment-id="PR205-ACTUAL-COST32"]');
  await actualResult.getByRole('button', { name: 'DÙNG LÀM GIÁ VỐN', exact: true }).click();
  assert.equal((await page.getByTestId('quote-line-1-cost').inputValue()).replace(/\D/g, ''), '32000000');
  assert.equal(await page.getByTestId('quote-line-1-sell').inputValue(), '');
  ok('Existing CostCheck still searches/compares and seeds true ACTUAL cost into legacy quote with sell blank; QUOTE/unknown cost disabled');
  assert.deepEqual(errors, []); ok('No browser page errors');

  const history = JSON.parse(readFileSync(path.join(evidence, 'history-integrity.json'), 'utf8'));
  assert.equal(history.unchanged, true); assert.equal(history.before_sha256, history.after_sha256);
  assert.equal(history.quote_sell, 40000000);
  assert.equal(history.actuals[1].lines[0].price, 40000000); assert.equal(history.actuals[1].lines[0].cost, null);
  assert.equal(history.actuals[2].lines[0].price, 40000000); assert.equal(history.actuals[2].lines[0].cost, 32000000);
  ok('Server-side whole historical-record fingerprints unchanged; old sell 40000000 and actual costs UNKNOWN/32000000 retained');
  writeFileSync(path.join(evidence, 'browser-results.json'), JSON.stringify({
    status: 'PASS', checks, observations, url, browserProvider: 'PLAYWRIGHT', transport: 'SANDBOX_STAGING',
    viewModelInjection: false, mockedBrowserRoutes: false, supplierInputThroughExistingUI: true,
    bundle_sha256: createHash('sha256').update(readFileSync(path.join(root, 'component/dist/logi-shell.js'))).digest('hex'),
    originalWorkbookAcceptance: 'NOT_RUN', realMongoStagingAcceptance: 'NOT_RUN', ownerDeviceUAT: 'PENDING',
  }, null, 2) + '\n');
} catch (e) {
  await page.screenshot({ path: path.join(evidence, 'browser-failure.png') }).catch(() => {});
  writeFileSync(path.join(evidence, 'browser-failure.json'), JSON.stringify({ status: 'FAILED', error: String(e.stack || e), checks, observations, url }, null, 2) + '\n');
  throw e;
} finally { await browser.close(); }
