async page => {
  // Flow A — khách Lục Giác gửi bình luận trong bubble node Journey Map, rồi reload.
  // Chạy: playwright-cli run-code "$(cat evidence/.../flows/a-customer-send-reload.js)"
  const steps = {};
  const visibleText = async (re) => page.getByText(re).locator('visible=true').first().innerText();
  const openLotAndNode = async () => {
    await page.getByText('QA-LOT', { exact: true }).locator('visible=true').first().click();
    await page.getByRole('button', { name: /01 LẤY HÀNG/ }).first().waitFor({ timeout: 20000 });
    await page.getByRole('button', { name: /01 LẤY HÀNG/ }).first().click();
    await page.getByText(/Trao đổi \(/).locator('visible=true').first().waitFor({ timeout: 20000 });
    await page.getByText(/Trao đổi \(/).first().click();
    await page.getByTestId('journey-discussion-body').waitFor({ timeout: 20000 });
  };

  // ---- 1. fresh session → customer identity
  await page.goto('http://127.0.0.1:9502/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('radio', { name: 'Lục Giác' }).waitFor({ timeout: 30000 });
  await page.getByText('Lục Giác', { exact: true }).locator('visible=true').first().click();
  await page.getByText('QA-LOT', { exact: true }).locator('visible=true').first().waitFor({ timeout: 25000 });
  steps.lot_visible_for_luc_giac = true;

  await openLotAndNode();
  steps.thread_before = await visibleText(/Trao đổi \(\d+\)/);
  steps.comment_field_in_node_bubble = await page.getByTestId('journey-discussion-body').isVisible();

  // ---- 2. send ONE new comment from the browser
  const marker = 'QA-SEND-' + Date.now();
  await page.getByTestId('journey-discussion-body').fill('Khách Lục Giác: kiểm tra cửa khẩu ' + marker);
  await page.getByTestId('journey-discussion-send').click();
  await page.getByText(marker, { exact: false }).locator('visible=true').first().waitFor({ timeout: 25000 });
  steps.send_acknowledged_no_error =
    (await page.getByText('Không gửi được trao đổi.').count()) === 0;
  steps.thread_after_send = await visibleText(/Trao đổi \(\d+\)/);
  steps.marker = marker;

  // ---- 3. hard reload (new Streamlit session) and read the SAME comment back
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.getByRole('radio', { name: 'Lục Giác' }).waitFor({ timeout: 30000 });
  await page.getByText('Lục Giác', { exact: true }).locator('visible=true').first().click();
  await page.getByText('QA-LOT', { exact: true }).locator('visible=true').first().waitFor({ timeout: 25000 });
  await openLotAndNode();
  steps.after_reload_marker_visible = await page
    .getByText(marker, { exact: false }).locator('visible=true').first()
    .isVisible()
    .catch(() => false);
  steps.thread_after_reload = await visibleText(/Trao đổi \(\d+\)/);
  return steps;
}
