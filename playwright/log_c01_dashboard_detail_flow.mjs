/**
 * Read-only browser flow for LOG-C01 dashboard list -> detail behavior.
 *
 * The function accepts a Codex in-app Browser tab, so it can be run from the
 * node_repl Browser skill without requiring a project-local Playwright package.
 * It only changes dashboard filter/detail UI state; it never saves or deletes
 * business data.
 */
export async function runDashboardDetailFlow(tab, options = {}) {
  const {
    timeRange = "Tháng trước",
    customerPattern = /Đại Long/,
    shipmentPattern = /^T7\.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE \+ KEO$/,
    waitMs = 2500,
  } = options;

  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs);

  const timeRangeBox = tab.playwright.getByRole("combobox").first();
  await timeRangeBox.click();
  await tab.playwright
    .getByRole("option", { name: timeRange, exact: true })
    .click();
  await wait(waitMs);

  const customer = tab.playwright.getByText(customerPattern).first();
  await customer.click();
  await wait(Math.min(waitMs, 800));

  const shipmentButton = tab.playwright
    .getByRole("button", { name: shipmentPattern, exact: true })
    .first();
  const shipmentLabel = await shipmentButton.textContent();
  await shipmentButton.click();
  await wait(waitMs);

  const snapshotAfterFirstClick = String(await tab.playwright.domSnapshot());
  const detailAfterFirstClick = /heading[^\n]*📂/.test(snapshotAfterFirstClick);

  let detailAfterClose = null;
  if (detailAfterFirstClick) {
    const closeButton = tab.playwright
      .getByRole("button", { name: "❌", exact: true })
      .first();
    await closeButton.click();
    await wait(waitMs);
    const snapshotAfterClose = String(await tab.playwright.domSnapshot());
    detailAfterClose = /heading[^\n]*📂/.test(snapshotAfterClose);
  }

  return {
    url: await tab.url(),
    timeRange,
    shipmentLabel,
    detailAfterFirstClick,
    detailAfterClose,
    readOnly: true,
  };
}
