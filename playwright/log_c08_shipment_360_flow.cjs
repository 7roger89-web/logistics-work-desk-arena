const fs = require("node:fs");
const { chromium } = require("playwright");

const baseUrl = process.env.LOGISTICS_BASE_URL || "http://127.0.0.1:8520/";
const reportJson = "reports/QA/playwright/2026-08-16-log-c08-shipment-360.json";
const reportMarkdown = "reports/QA/playwright/2026-08-16-log-c08-shipment-360.md";
const screenshotPath = "reports/QA/playwright/2026-08-16-log-c08-shipment-360.png";

async function main() {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const result = {
    chat_id: "LOG-C08",
    scope: "Dashboard -> Shipment 360 -> operational workspace -> close/back",
    runtime: baseUrl,
    actions: [],
    checks: {},
    screenshots: [],
  };
  const bodyText = () => page.locator("body").innerText();
  const waitForText = async (needle) => {
    await page.waitForFunction((expected) => document.body.innerText.includes(expected), needle, { timeout: 30000 });
  };

  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  await waitForText("Shipment control room");
  result.actions.push("open dashboard");
  result.checks.dashboardVisible = true;

  result.actions.push("use existing Dashboard queue");
  result.checks.queueSearchVisible = (await page.getByText("Lọc & tìm trong queue", { exact: false }).count()) >= 1;

  await waitForText("LO-0306");
  const shipmentButtons = page.locator('[data-testid="stButton"] button').filter({ hasText: "LO-0306" });
  const shipmentCount = await shipmentButtons.count();
  result.checks.shipmentRowsAvailable = shipmentCount > 0;
  if (!shipmentCount) throw new Error("No shipment button found after LO- search");
  const shipmentId = (await shipmentButtons.first().innerText()).match(/LO-0306/)?.[0] || "LO-0306";
  await shipmentButtons.first().click();
  await waitForText("SHIPMENT 360 · OPERATIONAL WORKSPACE");
  await page.waitForTimeout(1200);
  result.actions.push(`open Shipment 360 ${shipmentId}`);
  const detailBody = await bodyText();
  result.checks.shipment360Visible = detailBody.includes("SHIPMENT 360") && detailBody.includes("NEXT ACTION");
  result.checks.operationalSignalsVisible = (await page.locator(".shipment360-signal").count()) >= 5;
  result.checks.contextVisible = (await page.getByText("Factory lots", { exact: false }).count()) >= 1;
  result.checks.documentsVisible = (await page.getByText("Chứng từ", { exact: false }).count()) >= 1;
  result.checks.financeSeparate = (await page.getByRole("tab", { name: /FINANCE/ }).count()) >= 1;
  result.checks.unknownVisible = detailBody.includes("UNKNOWN");
  result.checks.existingSaveControlsPresent = (await page.getByRole("button", { name: /LƯU/, exact: false }).count()) >= 1;

  await page.locator(".shipment360-title").first().scrollIntoViewIfNeeded();
  await page.screenshot({ path: screenshotPath });
  result.screenshots.push(screenshotPath);
  await page.getByRole("button", { name: "❌", exact: true }).first().click();
  await page.waitForTimeout(2500);
  result.actions.push("close Shipment 360");
  result.checks.queueRestoresAfterClose = (await page.getByText("Lọc & tìm trong queue", { exact: false }).count()) >= 1;
  result.pass = Object.values(result.checks).every(Boolean);

  fs.mkdirSync("reports/QA/playwright", { recursive: true });
  fs.writeFileSync(reportJson, JSON.stringify(result, null, 2));
  fs.writeFileSync(
    reportMarkdown,
    `# LOG-C08 Browser QA — Shipment 360\n\n- Runtime: ${baseUrl}\n- Actions: ${result.actions.join(" -> ")}\n- Result: ${result.pass ? "PASS" : "FAIL"}\n\n## Checks\n\n${Object.entries(result.checks).map(([key, value]) => `- ${key}: ${value ? "PASS" : "FAIL"}`).join("\n")}\n\n- Screenshot: ${screenshotPath}\n- This is local Streamlit runtime evidence; no Docker build/runtime was available.\n`,
  );
  await browser.close();
  if (!result.pass) process.exitCode = 1;
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
