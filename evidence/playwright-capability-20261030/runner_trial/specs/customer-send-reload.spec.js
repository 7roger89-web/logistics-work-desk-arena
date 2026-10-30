const { test, expect } = require('@playwright/test');

test('customer sends a Journey Map node comment, reload keeps it', async ({ page }) => {
  const marker = 'QA-RUNNER-' + Date.now();
  const openThread = async () => {
    await page.getByText('Lục Giác', { exact: true }).locator('visible=true').first().click();
    await page.waitForTimeout(6000);
    const lot = page.getByText('QA-LOT', { exact: true }).locator('visible=true').first();
    await expect(lot).toBeVisible({ timeout: 25000 });
    await lot.click();
    await page.waitForTimeout(5000);
    await page.getByRole('button', { name: /01 LẤY HÀNG/ }).first().click();
    await page.waitForTimeout(3500);
    const header = page.getByText(/Trao đổi \(\d+\)/).first();
    await expect(header).toBeVisible({ timeout: 25000 });
    const before = await header.innerText();
    await header.click();
    await page.waitForTimeout(3000);
    await expect(page.getByTestId('journey-discussion-body')).toBeVisible();
    return before;
  };

  await page.goto('/');
  const before = await openThread();
  await page.getByTestId('journey-discussion-body').fill('Khách: ' + marker);
  await page.getByTestId('journey-discussion-send').click();
  await page.waitForTimeout(7000);
  await expect(page.getByTestId('journey-discussion-error')).toHaveCount(0);
  await expect(page.getByText(marker)).toBeVisible({ timeout: 25000 });

  await page.reload();
  await openThread();
  await expect(page.getByText(marker)).toBeVisible({ timeout: 25000 });
  expect(before).toMatch(/Trao đổi \(0\)/);
});
