async page => {
  // S2 — shared-handle full journey on the repository's own QA harness
  // (tests/component/g15_lg_tt_discussion_runtime.py, port 9503).
  // customer send -> reload -> staff reply -> customer read-back -> other tenant.
  const out = { steps: {}, ok: false };
  const step = (name, value) => { out.steps[name] = value; };
  const wait = (ms) => page.waitForTimeout(ms);

  const openCustomerThread = async () => {
    await page.getByText('Lục Giác', { exact: true }).locator('visible=true').first().click();
    await wait(6000);
    await page.getByText('QA-LOT', { exact: true }).locator('visible=true').first().waitFor({ timeout: 30000 });
    await page.getByText('QA-LOT', { exact: true }).locator('visible=true').first().click();
    await wait(5000);
    await page.getByRole('button', { name: /01 LẤY HÀNG/ }).first().click();
    await wait(3500);
    const header = page.getByText(/Trao đổi \(\d+\)/).first();
    await header.waitFor({ timeout: 25000 });
    const before = await header.innerText();
    await header.click();
    await wait(3000);
    await page.getByTestId('journey-discussion-body').waitFor({ timeout: 25000 });
    return before;
  };

  const threadHeader = () => page.getByText(/Trao đổi \(\d+\)/).first().innerText();

  // ── 1. customer sends a comment inside the node bubble
  await page.goto('http://127.0.0.1:9503/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('radio', { name: 'Lục Giác' }).waitFor({ timeout: 40000 });
  const before = await openCustomerThread();
  step('header_before', before);

  const customerMarker = 'QA-CUST-' + Date.now();
  out.customer_marker = customerMarker;
  await page.getByTestId('journey-discussion-body').fill('Khách Lục Giác: ' + customerMarker);
  await page.getByTestId('journey-discussion-send').click();
  await wait(7000);
  step('customer_send_error', await page.getByTestId('journey-discussion-error').first().innerText().catch(() => null));
  step('customer_send_error_alert', await page.getByText('Không gửi được trao đổi.').count());
  step('customer_marker_visible_after_send',
    await page.getByText(customerMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));
  step('header_after_send', await threadHeader());

  // ── 2. hard reload, same comment must still be there (new Streamlit session)
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.getByRole('radio', { name: 'Lục Giác' }).waitFor({ timeout: 40000 });
  await openCustomerThread();
  step('customer_marker_visible_after_reload',
    await page.getByText(customerMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));
  step('header_after_reload', await threadHeader());

  // ── 3. staff logs in and answers on the SAME lot/stage
  const staffMarker = 'QA-STAFF-' + Date.now();
  out.staff_marker = staffMarker;
  await page.getByText('Trường Thành (nội bộ)', { exact: true }).locator('visible=true').first().click();
  await wait(5000);
  await page.getByRole('textbox', { name: 'Tài khoản' }).fill('truong.thanh');
  await page.getByLabel('Mật khẩu').fill('Qa-Passw0rd-2026');
  await page.getByRole('button', { name: 'Đăng nhập' }).click();
  await wait(9000);
  step('staff_logged_in', await page.getByText(/Đang đăng nhập nội bộ/).count());
  await page.getByRole('link', { name: /QA-LOT/ }).first().click();
  await wait(7000);
  await page.getByTestId('journey-detail-map-toggle').click();
  await wait(4500);
  await page.getByTestId('journey-node-pickup').click();
  await wait(3000);
  await page.getByTestId('journey-node-discussion-pickup').click();
  await wait(4000);
  step('staff_sees_customer_note',
    await page.getByText(customerMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));
  await page.getByTestId('journey-discussion-body').fill(staffMarker);
  await page.getByTestId('journey-discussion-visibility').selectOption('CUSTOMER');
  await wait(500);
  await page.getByTestId('journey-discussion-send').click();
  await wait(8000);
  step('staff_send_error', await page.getByTestId('journey-discussion-error').first().innerText().catch(() => null));
  step('staff_reply_in_thread',
    await page.getByText(staffMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));

  // ── 4. customer reloads and reads the staff answer
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.getByRole('radio', { name: 'Lục Giác' }).waitFor({ timeout: 40000 });
  await openCustomerThread();
  step('customer_reads_staff_reply',
    await page.getByText(staffMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));
  step('customer_still_reads_own_note',
    await page.getByText(customerMarker, { exact: false }).locator('visible=true').first().isVisible().catch(() => false));
  step('header_after_staff_reply', await threadHeader());

  // ── 5. another tenant must not reach the lot at all
  await page.getByText('Khách khác', { exact: true }).locator('visible=true').first().click();
  await wait(7000);
  step('other_tenant_lot_visible', await page.getByText('QA-LOT', { exact: true }).locator('visible=true').count());
  step('other_tenant_nodes', await page.locator('[data-testid^="journey-node-"]').count());
  step('other_tenant_discussion_frames', await page.getByTestId('journey-discussion-body').count());

  const s = out.steps;
  out.ok = (
    s.customer_send_error_alert === 0
    && s.customer_marker_visible_after_send === true
    && s.customer_marker_visible_after_reload === true
    && s.staff_logged_in >= 1
    && s.staff_sees_customer_note === true
    && s.staff_send_error == null
    && s.staff_reply_in_thread === true
    && s.customer_reads_staff_reply === true
    && s.other_tenant_lot_visible === 0
    && s.other_tenant_nodes === 0
    && s.other_tenant_discussion_frames === 0
  );
  return out;
}
