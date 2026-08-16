/**
 * Reusable visible-browser flow for LOG-C03 Shipment Dashboard 2.0.
 *
 * The flow is intentionally read-only: it changes filters and navigation
 * state, opens Shipment 360, closes it, and optionally opens a second row.
 */
export async function runShipmentDashboardWorkdeskFlow(tab, options = {}) {
  const {
    timeRange = "Tất cả",
    customerPattern = /ĐẠI LONG|LỤC GIÁC/i,
    shipmentPattern = /^T7\.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE \+ KEO$|^LG-001$/,
    secondShipmentPattern = null,
    waitMs = 2500,
  } = options;

  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs * 2);

  let timeRangeBox;
  for (let attempt = 0; attempt < 12; attempt += 1) {
    timeRangeBox = tab.playwright.getByRole("combobox").first();
    if (await timeRangeBox.count() && await timeRangeBox.isVisible()) break;
    await wait(waitMs);
  }
  if (!timeRangeBox || !(await timeRangeBox.count())) {
    throw new Error("Dashboard time-range filter did not become available");
  }
  await timeRangeBox.click();
  await tab.playwright
    .getByRole("option", { name: timeRange, exact: true })
    .click();
  await wait(waitMs);

  const snapshotBeforeOpen = String(await tab.playwright.domSnapshot());
  const workdeskVisible = snapshotBeforeOpen.includes("Bàn Support") || snapshotBeforeOpen.includes("Lô hàng cần chú ý");
  const separateStatuses = snapshotBeforeOpen.includes("Vận hành:") && snapshotBeforeOpen.includes("Tài chính:");
  const attentionFilterVisible = snapshotBeforeOpen.includes("Cảnh báo") && snapshotBeforeOpen.includes("Sale phụ trách");

  const customerMatches = await tab.playwright.getByText(customerPattern).all();
  let customerVisible = false;
  for (const match of customerMatches) {
    if (await match.isVisible()) {
      customerVisible = true;
      break;
    }
  }
  if (!customerVisible) {
    throw new Error("No visible customer row matched the configured customerPattern");
  }
  await wait(Math.min(waitMs, 800));

  const shipmentButton = tab.playwright
    .getByRole("button", { name: shipmentPattern, exact: true })
    .first();
  const shipmentLabel = await shipmentButton.textContent();
  await shipmentButton.click();
  await wait(waitMs);

  const snapshotAfterFirstClick = String(await tab.playwright.domSnapshot());
  const detailAfterFirstClick = /heading[^\n]*📂/.test(snapshotAfterFirstClick);
  const shipment360Visible = snapshotAfterFirstClick.includes("Shipment 360");
  const financialSummaryVisible = snapshotAfterFirstClick.includes("TỔNG PHẢI THU") || snapshotAfterFirstClick.includes("UNKNOWN");
  const saveButtonCount = await tab.playwright
    .getByRole("button", { name: "💾 LƯU", exact: true })
    .count();

  const result = {
    url: await tab.url(),
    timeRange,
    shipmentLabel,
    workdeskVisible,
    separateStatuses,
    attentionFilterVisible,
    customerVisible,
    detailAfterFirstClick,
    shipment360Visible,
    financialSummaryVisible,
    existingSaveControlsUntouched: saveButtonCount === 2,
    readOnly: true,
  };

  const closeButton = tab.playwright
    .getByRole("button", { name: "❌", exact: true })
    .first();
  await closeButton.click();
  let snapshotAfterClose = "";
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await wait(waitMs);
    snapshotAfterClose = String(await tab.playwright.domSnapshot());
    if (!snapshotAfterClose.includes("Shipment 360 — Hồ sơ tài chính")) break;
  }
  result.detailAfterClose = !snapshotAfterClose.includes("📂");
  result.listRestored = snapshotAfterClose.includes("Bàn Support") || snapshotAfterClose.includes("Lô hàng cần chú ý");

  if (secondShipmentPattern) {
    const secondButton = tab.playwright
      .getByRole("button", { name: secondShipmentPattern, exact: true })
      .first();
    result.secondShipmentLabel = await secondButton.textContent();
    await secondButton.click();
    await wait(waitMs);
    const snapshotAfterSecondClick = String(await tab.playwright.domSnapshot());
    result.secondDetailOpened = /heading[^\n]*📂/.test(snapshotAfterSecondClick);
    result.secondShipment360Visible = snapshotAfterSecondClick.includes("Shipment 360");
  }

  return result;
}
