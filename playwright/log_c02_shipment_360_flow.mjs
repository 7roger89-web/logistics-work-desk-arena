/**
 * Read-only browser flow for the LOG-C02 Shipment 360 summary.
 *
 * The function accepts a Codex in-app Browser tab and uses only visible UI
 * state. It selects an existing shipment, verifies the financial-first
 * summary, closes the detail, and never submits a business-data control.
 */
export async function runShipment360Flow(tab, options = {}) {
  const {
    timeRange = "Tất cả",
    customerPattern = /Đại Long/,
    shipmentPattern = /^T7\.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE \+ KEO$/,
    waitMs = 3000,
  } = options;

  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs * 2);

  const timeRangeBox = tab.playwright.getByRole("combobox").first();
  await timeRangeBox.click();
  await tab.playwright
    .getByRole("option", { name: timeRange, exact: true })
    .click();
  await wait(waitMs);

  const customer = tab.playwright.getByText(customerPattern).first();
  await customer.click();
  await wait(Math.min(waitMs, 1200));

  const shipmentButton = tab.playwright
    .getByRole("button", { name: shipmentPattern, exact: true })
    .first();
  const shipmentLabel = await shipmentButton.textContent();
  await shipmentButton.click();
  await wait(waitMs * 2);

  const snapshotAfterOpen = String(await tab.playwright.domSnapshot());
  const summaryIndex = snapshotAfterOpen.indexOf("Shipment 360");
  const operationalTabsIndex = snapshotAfterOpen.indexOf('tab "🚛 PICKUP');
  const totalReceivableIndex = snapshotAfterOpen.indexOf("TỔNG PHẢI THU");
  const saveControlCount = await tab.playwright
    .getByRole("button", { name: "💾 LƯU", exact: true })
    .count();

  const result = {
    url: await tab.url(),
    timeRange,
    shipmentLabel,
    detailAfterOpen: snapshotAfterOpen.includes("📂 T7.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE + KEO"),
    financialSummaryVisible:
      snapshotAfterOpen.includes("TỔNG PHẢI THU") &&
      snapshotAfterOpen.includes("CÒN PHẢI THU") &&
      snapshotAfterOpen.includes("CHƯA ĐỐI SOÁT"),
    totalReceivableShowsValue: /TỔNG PHẢI THU[\s\S]{0,180}\d[\d,.]* VND/.test(
      snapshotAfterOpen.slice(totalReceivableIndex, totalReceivableIndex + 180),
    ),
    sourceVisible: snapshotAfterOpen.includes("core.logic.calculate_from_shipment"),
    unknownStateVisible: snapshotAfterOpen.includes("UNKNOWN"),
    moneyMapVisible: snapshotAfterOpen.includes("Money map & nguồn số liệu"),
    financialBeforeOperationalTabs:
      summaryIndex >= 0 &&
      operationalTabsIndex >= 0 &&
      summaryIndex < operationalTabsIndex,
    existingSaveControlsUntouched: saveControlCount === 2,
    readOnly: true,
  };

  const closeButton = tab.playwright
    .getByRole("button", { name: "❌", exact: true })
    .first();
  await closeButton.click();
  await wait(waitMs);
  const snapshotAfterClose = String(await tab.playwright.domSnapshot());
  result.detailAfterClose = !snapshotAfterClose.includes("📂 T7.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE + KEO");
  result.listRestored = snapshotAfterClose.includes("👤 Đại Long (1)");
  result.filterPreserved = snapshotAfterClose.includes("Đang hiển thị TẤT CẢ");
  return result;
}
