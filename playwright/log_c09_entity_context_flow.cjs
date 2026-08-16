const fs = require("node:fs");
const { chromium } = require("playwright");

const baseUrl = process.env.LOGISTICS_BASE_URL || "http://127.0.0.1:8520/";
const reportJson = "reports/QA/playwright/2026-08-16-log-c09-entity-context.json";
const reportMarkdown = "reports/QA/playwright/2026-08-16-log-c09-entity-context.md";
const screenshotPath = "reports/QA/playwright/2026-08-16-log-c09-entity-context.png";

async function main() {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const result = {
    chat_id: "LOG-C09",
    scope: "Entity Context -> Customer 360 -> Shipment 360 -> Customer 360 return",
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
  await waitForText("Entity Context");
  const entityNav = page.getByRole("button", { name: "🧭 Entity Context", exact: true });
  await entityNav.scrollIntoViewIfNeeded();
  await entityNav.click();
  await waitForText("Customer / Factory / Partner 360");
  result.actions.push("open Entity Context");
  result.checks.entityWorkspaceVisible = true;

  await page.getByRole("button", { name: "Open Customer context", exact: true }).click();
  await waitForText("Customer 360 ·");
  result.actions.push("open Customer 360");
  const customerBody = await bodyText();
  result.checks.customerIdentityVisible = customerBody.includes("Master identity / contact");
  result.checks.customerShipmentContextVisible = (await page.getByRole("button", { name: /Open Shipment 360/ }).count()) > 0;
  result.checks.unknownDisclosureVisible = customerBody.includes("Missing / unknown data");

  await page.getByRole("button", { name: /Open Shipment 360/ }).first().click();
  await waitForText("SHIPMENT 360");
  result.actions.push("open Shipment 360 from Customer 360");
  const shipmentBody = await bodyText();
  result.checks.shipment360Visible = shipmentBody.includes("SHIPMENT 360") && shipmentBody.includes("NEXT ACTION");
  result.checks.customerLinkVisible = (await page.getByRole("button", { name: "Open Customer 360", exact: true }).count()) === 1;
  result.checks.factoryUnknownOrLinkVisible = shipmentBody.includes("Factory lots") || shipmentBody.includes("UNKNOWN");
  result.checks.partnerUnknownOrLinkVisible = shipmentBody.includes("Agent/partner") || shipmentBody.includes("UNKNOWN");

  await page.getByRole("button", { name: "Open Customer 360", exact: true }).click();
  await waitForText("Customer 360 ·");
  result.actions.push("open Customer 360 from Shipment 360");
  result.checks.backToShipmentVisible = (await page.getByRole("button", { name: "← Back to Shipment 360", exact: true }).count()) === 1;
  await page.getByRole("button", { name: "← Back to Shipment 360", exact: true }).click();
  await waitForText("SHIPMENT 360");
  result.actions.push("return to Shipment 360");
  result.checks.shipment360RestoresAfterReturn = (await page.getByRole("button", { name: "❌", exact: true }).count()) === 1;

  await page.screenshot({ path: screenshotPath, fullPage: false });
  result.screenshots.push(screenshotPath);
  result.pass = Object.values(result.checks).every(Boolean);

  fs.mkdirSync("reports/QA/playwright", { recursive: true });
  fs.writeFileSync(reportJson, JSON.stringify(result, null, 2));
  fs.writeFileSync(
    reportMarkdown,
    `# LOG-C09 Browser QA — Entity Context\n\n- Runtime: ${baseUrl}\n- Actions: ${result.actions.join(" -> ")}\n- Result: ${result.pass ? "PASS" : "FAIL"}\n\n## Checks\n\n${Object.entries(result.checks).map(([key, value]) => `- ${key}: ${value ? "PASS" : "FAIL"}`).join("\n")}\n\n- Screenshot: ${screenshotPath}\n- Scope is local read-only context navigation; no deployment or release was performed.\n`,
  );
  await browser.close();
  if (!result.pass) process.exitCode = 1;
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
