/**
 * Reusable visible-browser flow for LOG-C07 Logistics Operations Workspace.
 *
 * The flow is read-only. It validates grouped navigation, shipment search,
 * exception-first filtering, source-labelled financial disclosure, the
 * Shipment 360 open/close path, and the preserved A Bò read-only boundary.
 */
export async function runLogC07OperationsWorkspaceFlow(page, options = {}) {
  const {
    baseUrl = "http://127.0.0.1:8520/",
    shipmentQuery = "LO-0306",
    unrelatedShipment = "T1 - 107850148710",
    screenshotDir = null,
    waitMs = 1200,
  } = options;

  const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
  const bodyText = () => page.locator("body").innerText();
  const waitForBodyText = async (needle, timeoutMs = 30000) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if ((await bodyText()).includes(needle)) return;
      await wait(400);
    }
    throw new Error(`Timed out waiting for body text: ${needle}`);
  };
  const result = {
    scope: "LOG-C07 shipment-first operations workspace",
    readOnly: true,
    actions: [],
    checks: {},
    screenshots: [],
  };

  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("text=PRIMARY WORK SURFACE · SHIPMENT QUEUE", { timeout: 30000 });
  result.actions.push("open dashboard");
  result.checks.groupedNavigation = (await page.locator(".ops-nav-group").allTextContents()).join("|").includes("OPERATIONS");
  result.checks.shipmentFirstQueue = (await bodyText()).includes("Lô hàng cần xử lý");

  const customerNav = page.getByRole("button", { name: /Khách Hàng/ }).first();
  await customerNav.click();
  await waitForBodyText("QUẢN LÝ KHÁCH HÀNG");
  result.actions.push("open commercial context");
  result.checks.navigationReachesCustomerContext = (await bodyText()).includes("QUẢN LÝ KHÁCH HÀNG");

  await page.getByRole("button", { name: /Dashboard/ }).first().click();
  await page.waitForSelector("text=PRIMARY WORK SURFACE · SHIPMENT QUEUE", { timeout: 30000 });
  result.actions.push("return to operations");

  await page.getByText("🔎 BỘ LỌC DỮ LIỆU & THỜI GIAN", { exact: true }).click();
  const searchBox = page.getByLabel("Tìm kiếm:", { exact: true });
  await searchBox.fill(shipmentQuery);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(waitMs * 2);
  const filteredBody = await bodyText();
  result.actions.push(`search ${shipmentQuery}`);
  result.checks.searchScopesQueue = /\d+\/\d+ lô đang hiển thị/.test(filteredBody);
  result.checks.searchExcludesUnrelated = !filteredBody.includes(unrelatedShipment);
  result.checks.separateOperationalFinancialStatus = filteredBody.includes("Vận hành:") && filteredBody.includes("Tài chính:");
  result.checks.explicitUnknown = filteredBody.includes("UNKNOWN") || filteredBody.includes("chưa có");

  const financialDisclosure = page.getByText("Vì sao ra số này?", { exact: true }).first();
  await financialDisclosure.click();
  await page.waitForTimeout(400);
  const financialBody = await bodyText();
  result.actions.push("open financial explanation");
  result.checks.financialMeaningVisible = financialBody.includes("Ý nghĩa hiện tại");
  result.checks.financialSourcesVisible = financialBody.includes("Nguồn và điều kiện tính");
  result.checks.financialReadOnlyNotice = financialBody.includes("canonical financial truth");

  const openButton = page.getByRole("button", { name: shipmentQuery, exact: true }).first();
  await openButton.click();
  await page.waitForTimeout(waitMs * 2);
  const detailBody = await bodyText();
  result.actions.push("open Shipment 360");
  result.checks.shipment360Opens = detailBody.includes(`📂 ${shipmentQuery}`) && /Shipment 360/i.test(detailBody);
  result.checks.existingSaveControlsUntouched = (await page.getByRole("button", { name: "💾 LƯU", exact: true }).count()) === 2;

  await page.getByRole("button", { name: "❌", exact: true }).click();
  await page.waitForSelector("text=PRIMARY WORK SURFACE · SHIPMENT QUEUE", { timeout: 30000 });
  result.actions.push("close Shipment 360");
  result.checks.queueRestoresAfterClose = (await bodyText()).includes("Lô hàng cần xử lý");

  await page.getByRole("button", { name: /Công nợ A Bò/ }).first().click();
  await waitForBodyText("canonical ledger");
  await waitForBodyText("read-only");
  const aboBody = await bodyText();
  result.actions.push("open A Bò read-only desk");
  result.checks.aboReadOnlyBoundary = aboBody.includes("canonical ledger") && aboBody.includes("read-only") && !/PUBLISH|PUBLISHING/i.test(aboBody);

  await page.getByRole("button", { name: /Dashboard/ }).first().click();
  await page.waitForSelector("text=PRIMARY WORK SURFACE · SHIPMENT QUEUE", { timeout: 30000 });
  result.actions.push("return to dashboard");

  if (screenshotDir) {
    const screenshotPath = `${screenshotDir}/2026-08-16-log-c07-operations-workspace.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    result.screenshots.push(screenshotPath);
  }

  result.pass = Object.values(result.checks).every(Boolean);
  return result;
}
