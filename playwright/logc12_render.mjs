import { chromium } from 'playwright';
import fs from 'fs';
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const evidence = 'reports/QA/playwright';
  fs.mkdirSync(evidence, { recursive: true });
  const result = { steps: [], errors: [] };
  try {
    await page.goto('http://localhost:8501', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    result.steps.push({ name: 'initial', url: page.url(), title: await page.title(), body: (await page.locator('body').innerText()).slice(0, 6000) });
    await page.screenshot({ path: `${evidence}/2026-08-16-log-c12-initial.png`, fullPage: true });
    const sales = page.getByText('Sales & Báo Giá', { exact: true }).first();
    if (await sales.count()) {
      await sales.click();
      await page.waitForTimeout(1800);
      result.steps.push({ name: 'sales_workspace', url: page.url(), body: (await page.locator('body').innerText()).slice(0, 10000) });
      await page.screenshot({ path: `${evidence}/2026-08-16-log-c12-sales-workspace.png`, fullPage: true });
      const newQuote = page.getByText('Báo giá mới', { exact: true }).first();
      if (await newQuote.count()) {
        await newQuote.click();
        await page.waitForTimeout(900);
        result.steps.push({ name: 'new_quote_form', body: (await page.locator('body').innerText()).slice(0, 12000) });
        await page.screenshot({ path: `${evidence}/2026-08-16-log-c12-new-quote.png`, fullPage: true });
      }
    } else {
      result.steps.push({ name: 'sales_workspace', blocked: 'Sales & Báo Giá control not visible; likely authentication or runtime blocker.' });
    }
  } catch (error) {
    result.errors.push(String(error));
  }
  fs.writeFileSync(`${evidence}/2026-08-16-log-c12-render.json`, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})();
