// Representative real-browser acceptance for Issue #172 on the isolated #162 staging host.
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const output = process.argv[2] || "/tmp/customer-playbook-172-screenshots";
mkdirSync(output, { recursive: true });

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const HOST = "http://127.0.0.1:9502";
const host = spawn(process.env.PYTHON || "python", ["scripts/verify_work_module_library_162.py"], {
  cwd: root,
  stdio: ["ignore", "ignore", "pipe"],
});
let hostErrors = "";
host.stderr.on("data", (buffer) => (hostErrors += buffer));
let browser;
const shot = (page, name) => page.screenshot({ path: path.join(output, name), fullPage: false });

try {
  let up = false;
  for (let attempt = 0; attempt < 150; attempt++) {
    try {
      if ((await fetch(`${HOST}/model`)).ok) {
        up = true;
        break;
      }
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.ok(up, "isolated staging acceptance host came up");

  browser = await chromium.launch({
    headless: true,
    ...(process.env.PLAYWRIGHT_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH }
      : {}),
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto(HOST);
  await page.getByRole("link", { name: "Lô Hàng", exact: true }).first().click();
  await page.getByTestId("shipment-period-tat-ca").click();
  await page.getByRole("link", { name: "SEA-162", exact: true }).click();
  await page.getByTestId("shipment-journey").waitFor();

  // Setup one real Work Module blocker through the already-existing isolated
  // test writer. The Playbook itself is never used to write or attach anything.
  await page.getByTestId("journey-add-module").click();
  await page.getByTestId("journey-add-module-panel").waitFor();
  const templateChoice = page.getByRole("radio", { name: "Chọn IMPORT SPECIAL HANDLING", exact: true });
  await templateChoice.check();
  await page.getByTestId("journey-add-module-confirm").click();
  await page.locator('[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]').first().waitFor({ timeout: 15000 });

  const liveModel = await (await page.request.get(`${HOST}/model`)).json();
  const linked = liveModel.shipments.find((row) => row.id === "SEA-162");
  assert.ok(linked, "the isolated shipment exists");
  assert.equal(linked.customerId, "CUST-ANPHAT", "browser fixture carries exact customerId linkage");
  const customer = liveModel.customers.find((row) => row.id === linked.customerId);
  assert.ok(customer, "the exact customer master exists");
  const blocker = liveModel.attention.find((item) => item.shipmentId === linked.id && item.band === "BLOCKING");
  assert.ok(blocker, "the existing shared Attention projection has a linked BLOCKING item");

  await page.getByRole("link", { name: "Khách Hàng", exact: true }).first().click();
  await page.getByRole("textbox", { name: "Tìm khách hàng theo mã, tên, MST, SĐT, email" }).fill(customer.id);
  await page.getByTestId("customer-open-playbook").first().click();

  const detail = page.getByTestId("customer-playbook");
  await detail.waitFor();
  assert.equal(await detail.getAttribute("data-customer-id"), customer.id);
  assert.ok((await detail.innerText()).includes(customer.name), "customer identity renders from master");
  const note = page.getByTestId("customer-operating-note");
  if (customer.note?.trim()) {
    assert.ok((await note.innerText()).includes(customer.note), "the exact existing note is rendered");
  } else {
    assert.match(await note.innerText(), /Chưa ghi nhận ghi chú vận hành\./);
  }

  const shipmentRow = page.locator('[data-testid="customer-playbook-shipment"][data-shipment-id="SEA-162"]');
  await shipmentRow.waitFor();
  assert.equal(
    await shipmentRow.getByTestId("customer-playbook-shipment-link").getAttribute("href"),
    "/lo-hang/SEA-162",
    "linked shipment opens its direct canonical route",
  );
  const action = liveModel.shipments.find((row) => row.id === "SEA-162").journey?.primaryAction;
  if (action?.route) {
    assert.equal(
      await shipmentRow.getByTestId("customer-playbook-primary-action").getAttribute("href"),
      action.route,
      "existing primary action route is reused verbatim",
    );
  }

  const attentionRow = page.locator(`[data-testid="attention-item-${blocker.id}"]`);
  await attentionRow.waitFor();
  assert.equal(await attentionRow.getAttribute("data-attention-band"), blocker.band);
  assert.ok((await attentionRow.innerText()).includes(blocker.reason), "shared Attention reason is unchanged");
  assert.equal(await attentionRow.locator("a").getAttribute("href"), blocker.route, "shared Attention route is unchanged");
  assert.ok((await page.getByTestId("customer-playbook-concentration").innerText()).includes("Work Module đã gắn"));
  assert.doesNotMatch(await detail.innerText(), /risk score|recommendation|healthy|safe|khỏe|an toàn/i);
  await shot(page, "desktop-customer-playbook.png");

  await page.setViewportSize({ width: 390, height: 844 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 1, `390px customer detail has no horizontal page overflow (got ${overflow}px)`);
  const detailBox = await detail.boundingBox();
  assert.ok(detailBox && detailBox.width <= 390, "390px detail surface fits the viewport");
  await shot(page, "mobile-390-customer-playbook.png");

  // Clicking the shared Attention item reaches the existing exact shipment /
  // module workspace context instead of a customer-specific route or writer.
  await page.setViewportSize({ width: 1440, height: 1000 });
  await attentionRow.locator("a").click();
  const moduleContext = page.getByTestId("journey-module-context");
  await moduleContext.waitFor();
  assert.match(await moduleContext.innerText(), /IMPORT SPECIAL HANDLING/i);
  assert.match(await moduleContext.innerText(), /Prepare specialist file|Result received/i);
  assert.deepEqual(errors, [], "zero browser page errors in the representative workflow");

  console.log(`PASS #172 browser: isolated exact-linked customer -> existing BLOCKING Attention -> canonical module context -> desktop + 390px no-overflow -> ${output}`);
} catch (error) {
  console.error(hostErrors.slice(-2200));
  throw error;
} finally {
  await browser?.close();
  host.kill();
}
