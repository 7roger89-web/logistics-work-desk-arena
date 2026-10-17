// Actual Streamlit → React v2 → C1 → existing writers/GridFS → fresh VM.
// No browser route mocks, fake API, injected view-model, or second server.
// Run app.py separately on an isolated SANDBOX_STAGING port, AUTH_REQUIRED=false.
// PLAYWRIGHT_MODULE, CHROMIUM_EXECUTABLE, CHROMIUM_LIB_PATH and PYTHON may point
// to sandbox-only tools. The app and its lockfile do not gain browser deps.
import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const url = process.argv[2] || 'http://127.0.0.1:9501';
const evidence = path.resolve(root, process.argv[3] || 'evidence/excel-quote-import-v1');
const scratch = path.resolve(root, '.tmp/excel-quote-import-v1');
mkdirSync(evidence, { recursive: true }); mkdirSync(scratch, { recursive: true });
const PY = process.env.PYTHON || path.join(root, '.venv/bin/python');
const fixture = path.join(scratch, 'luc-giac-SYNTHETIC.xlsx');
execFileSync(PY, ['scripts/make_luc_giac_quote_fixture.py', fixture], { cwd: root });
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
  headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage', '--no-zygote'],
  env: process.env.CHROMIUM_LIB_PATH ? { ...process.env, LD_LIBRARY_PATH: process.env.CHROMIUM_LIB_PATH } : process.env });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
page.setDefaultTimeout(20000);
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('dialog', (d) => d.accept());
const checks = [];
const ok = (text) => { checks.push(text); console.log('PASS ' + text); };
const fresh = async () => page.locator('[data-testid="excel-quote-workspace"][data-preview-current="true"]').waitFor({ timeout: 30000 });
const goQuotes = async () => { await page.getByRole('link', { name: 'Báo Giá', exact: true }).first().click(); await page.getByTestId('quote-excel-open').waitFor(); };
const screenshot = async (name) => {
  // Dismiss real transient notices, rather than hiding UI in injected CSS.
  while (await page.locator('.toast-in button').count()) await page.locator('.toast-in button').first().click();
  await page.getByTestId('excel-quote-workspace').evaluate((el) => { let p = el; while (p) { p.scrollTop = 0; p = p.parentElement || p.getRootNode()?.host; } window.scrollTo(0, 0); });
  await page.screenshot({ path: path.join(evidence, name) });
};
const captureAt = async (id, name) => {
  while (await page.locator('.toast-in button').count()) await page.locator('.toast-in button').first().click();
  await page.getByTestId(id).evaluate((el) => { const shell = el.closest('.logi-shell'); shell.scrollTop += el.getBoundingClientRect().top - shell.getBoundingClientRect().top - 76; });
  await page.screenshot({ path: path.join(evidence, name) });
};
const noOverflow = async (label) => {
  const m = await page.getByTestId('excel-quote-workspace').evaluate((el) => { const shell = el.closest('.logi-shell'); return { viewport: innerWidth, document: document.documentElement.scrollWidth, shell: shell.scrollWidth - shell.clientWidth, workspace: Math.round(el.getBoundingClientRect().width) }; });
  assert.ok(m.document <= m.viewport + 1 && m.shell <= 1, `${label}: ${JSON.stringify(m)}`);
  ok(`${label}: no horizontal page/shell overflow ${JSON.stringify(m)}`);
  return m;
};
const download = async (trigger, file) => { const event = page.waitForEvent('download'); await trigger(); const d = await event; await d.saveAs(path.join(scratch, file)); return path.join(scratch, file); };
const workbook = (file) => JSON.parse(execFileSync(PY, ['-c', 'import json,sys;from openpyxl import load_workbook; w=load_workbook(sys.argv[1]); cells=[c for s in w for row in s for c in row];print(json.dumps({"text":"\\n".join(str(c.value or "") for c in cells),"formulas":sum(c.data_type=="f" for c in cells)},ensure_ascii=False))', file], { cwd: root, encoding: 'utf8' }));
let qid, sentVersion, desktopMetrics, mobileMetrics;
try {
  await page.goto(url);
  await page.getByRole('link', { name: 'Khách Hàng', exact: true }).first().waitFor({ timeout: 60000 });
  assert.equal(await page.getByTestId('role-preview-switcher').count(), 1, 'BLOCKED: this acceptance runner is SANDBOX_STAGING-only; no writes allowed against real MongoDB');
  assert.match(await page.locator('.global-footer').innerText(), /staging cách ly/);
  await page.getByRole('link', { name: 'Khách Hàng', exact: true }).first().click();
  // Create disposable customer through the existing customer screen, then
  // choose that EXISTING directory identity from the quote picker.
  await page.getByRole('button', { name: 'Khách mới', exact: true }).first().click();
  await page.getByLabel('Mã khách hàng').fill('CUST-LUCGIAC-XLSX');
  await page.getByLabel('Tên khách hàng').fill('Công ty Lục Giác');
  await page.getByRole('button', { name: /TẠO KHÁCH HÀNG/ }).click();
  // A rerun may reuse the same disposable identity; close the refused modal.
  try { await page.getByRole('heading', { name: 'Tạo khách hàng mới', exact: true }).waitFor({ state: 'hidden', timeout: 5000 }); }
  catch { await page.getByRole('button', { name: 'Hủy', exact: true }).click(); }
  await goQuotes();
  // Supply an explicitly SYNTHETIC historical price through Cost Intelligence,
  // not a mocked list or a direct database insertion.
  await page.getByTestId('quote-workspace-kho-gia-von').click();
  await page.getByTestId('cost-rate-raw').fill('OOCL\nNANSHA-HAIPHONG\nO/F VND31800000/20GP 有效期到 31/07/2026');
  await page.getByLabel('Nguồn / người báo (nếu biết)').fill('FIXTURE-RATE-LUCGIAC — giá cũ mô phỏng');
  await page.getByTestId('cost-rate-parse').click();
  await page.getByTestId('cost-rate-save').waitFor();
  await page.getByTestId('cost-rate-save').click();
  await page.getByTestId('cost-rate-history').getByText('FIXTURE-RATE-LUCGIAC — giá cũ mô phỏng', { exact: true }).first().waitFor();
  ok('Existing Cost Intelligence parse/review/save populated rate_cards through the real UI');
  await page.getByTestId('quote-workspace-bao-gia').click();
  await page.getByTestId('quote-excel-open').click();
  await page.getByTestId('excel-customer-toggle').click();
  await page.getByTestId('excel-customer-search').fill('CUST-LUCGIAC-XLSX');
  await page.getByTestId('excel-customer').getByRole('button', { name: /Công ty Lục Giác/ }).click();
  await page.getByTestId('excel-goods-description').fill('Bàn họp văn phòng từ Trung Quốc về Việt Nam');
  await page.getByTestId('excel-upload').setInputFiles(fixture);
  await page.getByTestId('excel-apply').waitFor();
  await fresh();
  const summary = await page.getByTestId('excel-goods-summary').innerText();
  assert.match(summary, /5.*dòng/s); assert.match(summary, /27.*chiếc/s); assert.match(summary, /607\.180.*RMB/);
  assert.equal(await page.getByTestId('excel-goods-3-length_mm').inputValue(), '12000');
  assert.equal(await page.getByLabel('Model hàng 2', { exact: true }).inputValue(), '');
  assert.match(await page.getByTestId('excel-warnings').innerText(), /ĐÃ HẾT HẠN/);
  ok('Real XLSX upload/review: 5 rows / 27 pcs / 607180 RMB; sparse model stays blank; expiry/conflicts remain');
  await page.getByTestId('excel-goods-1-qty').fill('15'); await fresh();
  assert.match(await page.getByTestId('excel-goods-summary').innerText(), /594\.125/);
  assert.match(await page.getByTestId('excel-goods-summary').innerText(), /26.*chiếc/s);
  await page.getByTestId('excel-goods-1-qty').fill('16'); await fresh();
  ok('Quantity edit recomputed by Python: 15 → 26 pcs / 594125 RMB, restored 16 → 27 / 607180');
  await screenshot('desktop-step1-review-1440x900.png');
  await captureAt('excel-goods-1', 'desktop-goods-1440x900.png');
  await page.getByTestId('excel-apply').click();
  await page.getByTestId('excel-next').click();
  await page.getByTestId('excel-equipment').selectOption('20GP');
  await page.getByTestId('excel-pol').fill('NANSHA');
  await page.getByTestId('excel-pod').fill('HAI PHONG');
  await page.getByTestId('excel-delivery').fill('Thanh Trì, Hà Nội — cần xác nhận kiện tháo rời');
  await page.getByTestId('excel-scope').fill('A: Vận chuyển Nansha–Hải Phòng–Hà Nội theo thỏa thuận; khách tự đứng tên nhập khẩu. Không tự cộng nâng hạ.');
  await page.getByTestId('excel-cost-search').fill('FIXTURE-RATE-LUCGIAC');
  await page.getByTestId('excel-pick-cost-1').first().click();
  await fresh();
  assert.equal(await page.getByTestId('excel-fee-1-cost').inputValue(), '31800000');
  assert.equal(await page.getByTestId('excel-fee-1-cost').isEditable(), false);
  assert.equal(await page.getByTestId('excel-fee-1-sell').inputValue(), '');
  assert.equal(await page.getByTestId('excel-fee-1-sell').evaluate((el) => getComputedStyle(el).borderTopStyle), 'solid');
  assert.match(await page.getByTestId('excel-fee-1-source').innerText(), /ĐÃ HẾT HẠN/);
  await page.getByTestId('excel-save').click();
  await page.locator('[data-testid="excel-quote-workspace"][data-saved-id^="Q-"]').waitFor();
  qid = await page.getByTestId('excel-quote-workspace').getAttribute('data-saved-id');
  assert.match(await page.getByTestId('excel-saved').innerText(), /Nháp/);
  ok(`Backend draft ${qid} saved/read back with blank sell; reference cost is NOT sell`);
  await page.getByTestId('excel-fee-1-name').fill('Vận chuyển EXW Nansha–Hải Phòng');
  await page.getByTestId('excel-fee-1-internal-note').fill('PRIVATE-SALE-BROWSER-ONLY — nguồn nội bộ không công bố');
  await page.getByTestId('excel-fee-1-sell').fill('35000000');
  await page.getByTestId('excel-fee-1-vat').fill('0'); // explicit known fixture VAT, never fabricated by app
  await page.getByTestId('excel-fee-1-confirmed').check(); await fresh();
  assert.match(await page.getByTestId('excel-service-subtotal').innerText(), /35\.000\.000/);
  await page.getByTestId('excel-option-B').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-1').count(), 0);
  await page.getByTestId('excel-scope').fill('B: Dịch vụ nhập khẩu ủy thác; phí phải thống nhất riêng.');
  await page.getByTestId('excel-add-fee').click();
  await page.getByTestId('excel-fee-1-name').fill('Phí ủy thác mô phỏng phương án B');
  await page.getByTestId('excel-fee-1-sell').fill('50000000');
  await page.getByTestId('excel-fee-1-vat').fill('0');
  await page.getByTestId('excel-fee-1-confirmed').check(); await fresh();
  await page.getByTestId('excel-option-A').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-1-sell').inputValue(), '35000000');
  assert.equal(await page.getByTestId('excel-fee-2').count(), 0);
  ok('A/B switching keeps independently entered costs/selling prices; B did not inherit A');
  await page.getByTestId('excel-step-3').click(); await fresh();
  assert.match(await page.getByTestId('excel-public-total').innerText(), /Chưa xác định/);
  assert.match(await page.getByTestId('excel-customer-preview').innerText(), /thiếu tỷ giá/);
  ok('Missing FX and unconfirmed customs produce no determined VND grand total');
  await page.getByTestId('excel-step-2').click();
  await page.getByTestId('excel-fx-USD').fill('26500');
  await page.getByTestId('excel-fx-CNY').fill('4000');
  await page.getByTestId('excel-fx-CNY_PER_USD').fill('6.78');
  await page.getByRole('alert').filter({ hasText: 'không tự ghi đè tỷ giá đã nhập' }).waitFor();
  await page.getByTestId('excel-fx-CNY').fill(''); await fresh();
  ok('Conflicting direct/cross FX rejected explicitly, never silently overwrites an entered rate');
  await page.getByTestId('excel-customs-basis_vnd').fill('2400000000');
  await page.getByTestId('excel-customs-duty_pct').fill('5');
  await page.getByTestId('excel-customs-vat_pct').fill('8');
  await page.getByTestId('excel-customs-basis-note').fill('Giả định kiểm thử riêng: trị giá hải quan 2,4 tỷ; không suy ra từ giá bán / toàn bộ phí Trung Quốc.');
  await fresh(); assert.match(await page.getByTestId('excel-customs-result').innerText(), /Chưa xác định/);
  await page.getByTestId('excel-customs-confirmed').check(); await fresh();
  assert.match(await page.getByTestId('excel-customs-result').innerText(), /321\.600\.000/);
  await page.getByTestId('excel-fee-1-sell').fill('36000000');
  await page.getByTestId('excel-fee-1-confirmed').check(); await fresh();
  assert.match(await page.getByTestId('excel-customs-result').innerText(), /321\.600\.000/);
  await page.getByTestId('excel-fee-1-sell').fill('35000000');
  await page.getByTestId('excel-fee-1-confirmed').check();
  await page.getByTestId('excel-delivery-date').fill('31/02/2027');
  await page.getByRole('alert').filter({ hasText: 'Ngày giao dự kiến không hợp lệ' }).waitFor();
  assert.equal(await page.getByTestId('excel-save').isEnabled(), false);
  await page.getByTestId('excel-delivery-date').fill('2026-12-20'); await fresh();
  ok('Confirmed independent customs basis: 321600000 VND, unchanged when Sale raises sell; invalid 31/02/2027 rejected');
  desktopMetrics = await noOverflow('desktop 1440×900');
  await screenshot('desktop-step2-internal-1440x900.png');
  await captureAt('excel-fee-1', 'desktop-fee-reference-vs-sell-1440x900.png');
  await page.getByTestId('excel-step-3').click();
  await page.getByTestId('excel-disclose-production').uncheck();
  await page.getByTestId('excel-public-notes').fill('PUBLIC-BROWSER-V1: Báo giá kiểm thử, cần xác nhận giá hiện hành.\nDòng thứ hai: Không gồm nâng hạ chưa chọn.');
  await fresh();
  const publicText = await page.getByTestId('excel-customer-preview').innerText();
  assert.ok(!publicText.includes('Sản xuất dự kiến 30 ngày.'));
  assert.ok(!publicText.includes('PRIVATE-SALE-BROWSER-ONLY'));
  assert.ok(!publicText.includes('31.800.000'));
  assert.match(publicText, /NANSHA → HAI PHONG/);
  assert.match(publicText, /Cơ sở riêng đã xác nhận: 2\.400\.000\.000/);
  assert.match(publicText, /2\.729\.796\.165/);
  await page.getByTestId('excel-save-step3').click();
  await page.getByTestId('excel-export').waitFor({ state: 'visible' });
  await page.locator('[data-testid="excel-export"]:enabled').waitFor();
  const draftFile = await download(() => page.getByTestId('excel-export').click(), 'draft-customer.xlsx');
  const xlsx = workbook(draftFile);
  assert.ok(xlsx.text.includes('PUBLIC-BROWSER-V1') && xlsx.text.includes('Dòng thứ hai'));
  for (const internal of ['PRIVATE-SALE-BROWSER-ONLY', 'FIXTURE-RATE-LUCGIAC', '31800000', 'Sản xuất dự kiến 30 ngày.', 'Lợi nhuận', 'Giá vốn']) assert.ok(!xlsx.text.includes(internal), `customer XLSX leaked ${internal}`);
  assert.equal(xlsx.formulas, 0);
  assert.ok(xlsx.text.includes('NANSHA → HAI PHONG') && xlsx.text.includes('Thanh Trì, Hà Nội'));
  assert.ok(xlsx.text.includes('2400000000'));
  ok('Actual downloaded XLSX opened with openpyxl: chosen disclosures/multiline notes present; internal cost/profit/source/notes absent; no formulas');
  await screenshot('desktop-step3-customer-1440x900.png');
  await captureAt('excel-public-total', 'desktop-customer-total-1440x900.png');
  await page.getByTestId('excel-transition').click();
  await page.getByTestId('excel-transition').filter({ hasText: 'Đánh dấu đã gửi khách' }).waitFor();
  await page.getByTestId('excel-transition').click();
  await page.locator('[data-testid^="excel-history-"]').waitFor();
  sentVersion = Number((await page.locator('[data-testid^="excel-history-"]').first().getAttribute('data-testid')).replace('excel-history-', ''));
  ok(`Explicit DRAFT → READY_FOR_REVIEW → SENT persisted immutable customer version v${sentVersion}; no email/deploy`);
  // Fresh browser reload establishes the readback, not just an optimistic DOM.
  await page.reload();
  await page.getByRole('link', { name: 'Báo Giá', exact: true }).first().waitFor({ timeout: 60000 });
  await goQuotes();
  await page.locator('tr').filter({ hasText: qid }).getByRole('button', { name: 'Sửa', exact: true }).click();
  await fresh();
  await page.getByTestId('excel-step-3').click();
  assert.equal(await page.getByTestId('excel-disclose-production').isChecked(), false);
  assert.match(await page.getByTestId('excel-public-notes').inputValue(), /PUBLIC-BROWSER-V1/);
  // Source action belongs to step 1, not a duplicated hidden control.
  assert.equal(await page.getByRole('button', { name: 'Tải file nguồn đã lưu', exact: true }).count(), 0);
  ok('Browser refresh/reopen restored customer, disclosures, notes and sent history from backend (existing in-memory staging transport only)');
  await page.getByTestId('excel-public-notes').fill('PUBLIC-BROWSER-V2-DRAFT: thay đổi không sửa bản đã gửi.');
  await fresh();
  await page.getByTestId('excel-save-step3').click();
  await page.getByTestId('excel-saved').filter({ hasText: 'Nháp' }).waitFor();
  const historyFile = await download(() => page.getByTestId(`excel-history-${sentVersion}`).click(), 'sent-v1-customer.xlsx');
  const historical = workbook(historyFile);
  assert.ok(historical.text.includes('PUBLIC-BROWSER-V1') && !historical.text.includes('PUBLIC-BROWSER-V2-DRAFT'));
  ok('Saving a new DRAFT leaves historical sent XLSX content unchanged');
  await page.getByTestId('excel-step-1').click(); await fresh();
  const sourcePath = await download(() => page.getByRole('button', { name: 'Tải file nguồn đã lưu', exact: true }).click(), 'source-readback.xlsx');
  const hash = (file) => createHash('sha256').update(readFileSync(file)).digest('hex');
  assert.equal(hash(sourcePath), hash(fixture));
  ok('Original XLSX source downloaded after refresh has byte-identical SHA256');
  await page.setViewportSize({ width: 390, height: 844 });
  mobileMetrics = await noOverflow('mobile 390×844 step1');
  await screenshot('mobile-step1-390x844.png');
  await captureAt('excel-goods-1', 'mobile-goods-390x844.png');
  await page.getByTestId('excel-step-2').click();
  await page.getByTestId('excel-option-B').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-1-sell').inputValue(), '50000000');
  await page.getByTestId('excel-option-A').click(); await fresh();
  assert.equal(await page.getByTestId('excel-fee-1-sell').inputValue(), '35000000');
  await noOverflow('mobile 390×844 step2 A/B interaction');
  await captureAt('excel-fee-1', 'mobile-fee-390x844.png');
  await page.getByTestId('excel-step-3').click();
  await page.getByTestId('excel-disclose-drawing').uncheck(); await fresh();
  assert.ok(!(await page.getByTestId('excel-public-disclosures').innerText()).includes('Có bản vẽ thiết kế'));
  await page.getByTestId('excel-disclose-drawing').check(); await fresh();
  await noOverflow('mobile 390×844 step3 disclosure interaction');
  await screenshot('mobile-step3-390x844.png');
  await captureAt('excel-public-total', 'mobile-customer-total-390x844.png');
  assert.deepEqual(errors, []);
  ok('Actual responsive app interaction and screenshots at 1440×900 / 390×844; no page errors');
  writeFileSync(path.join(evidence, 'browser-results.json'), JSON.stringify({ environment: 'actual app.py / Streamlit Components v2 / SANDBOX_STAGING (mongomock + GridFS)', productionVerified: false, fixture: 'SYNTHETIC three-sheet workbook, NOT original Lục Giác', qid, sentVersion, url, desktopMetrics, mobileMetrics, errors, checks }, null, 2));
} catch (error) {
  await page.screenshot({ path: path.join(scratch, 'failure.png') }).catch(() => {});
  console.error('FAILED', error);
  console.error((await page.getByTestId('excel-quote-workspace').innerText().catch(() => 'No workspace')).slice(-7000));
  throw error;
} finally { await browser.close(); }
