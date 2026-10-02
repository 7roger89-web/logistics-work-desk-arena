// Real-browser acceptance for Issue #170 Operations Control Tower V1.
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const output = process.argv[2] || "/tmp/log170-screenshots";
mkdirSync(output, { recursive: true });

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const HOST = "http://127.0.0.1:9502";
const host = spawn(process.env.PYTHON || "python", ["scripts/verify_work_module_library_162.py"], {
  cwd: root,
  stdio: ["ignore", "ignore", "pipe"],
});
let hostErrors = "";
host.stderr.on("data", (b) => (hostErrors += b));
let browser;

const shot = (page, name) => page.screenshot({ path: path.join(output, name), fullPage: false });

try {
  let up = false;
  for (let i = 0; i < 150; i++) {
    try {
      if ((await fetch(`${HOST}/model`)).ok) {
        up = true;
        break;
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  assert.ok(up, "acceptance host came up");

  browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));

  // Create one real BLOCKING module through the existing authoritative UI so
  // the Tower must aggregate shared Attention instead of a manager-only fake.
  await page.goto(HOST);
  await page.getByRole("link", { name: "Lô Hàng", exact: true }).first().click();
  await page.getByTestId("shipment-period-tat-ca").click();
  await page.getByRole("link", { name: "SEA-162", exact: true }).click();
  await page.getByTestId("shipment-journey").waitFor();

  await page.getByTestId("journey-add-module").click();
  await page.getByTestId("journey-add-module-panel").waitFor();
  await page.getByRole("radio", { name: "Chọn IMPORT SPECIAL HANDLING", exact: true }).check();
  await page.getByTestId("journey-add-module-confirm").click();
  await page
    .locator('[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]')
    .first()
    .waitFor({ timeout: 15000 });

  // Manager route is separate from Home and CEO Report.
  await page.getByRole("link", { name: "Điều hành", exact: true }).first().click();
  const tower = page.getByTestId("operations-control-tower");
  const hero = page.getByTestId("control-intervention-queue");
  const horizon = page.getByTestId("control-horizon");
  await tower.waitFor();

  assert.ok(
    await hero.evaluate(
      (a, b) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING),
      await horizon.elementHandle(),
    ),
    "manager intervention queue is the visual hero before horizon",
  );
  const towerText = await tower.innerText();
  const liveModel = await (await page.request.get(`${HOST}/model`)).json();
  const vnParts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const vnPart = (type) => vnParts.find((part) => part.type === type)?.value;
  const vietnamDate = `${vnPart("year")}-${vnPart("month")}-${vnPart("day")}`;
  assert.equal(
    liveModel.operationsControl.horizon.asOf,
    vietnamDate,
    "Tower and Attention use the Vietnam business date rather than runner UTC date",
  );
  assert.match(towerText, /Chưa có tín hiệu/);
  assert.match(towerText, /không có nghĩa lô khỏe hay an toàn/i);
  assert.doesNotMatch(towerText, /health score|risk score|leaderboard|quá tải/i);

  const blocker = page
    .locator('[data-testid="control-intervention-row"][data-control-band="BLOCKING"]')
    .filter({ hasText: "Prepare specialist file" })
    .first();
  await blocker.waitFor();
  assert.match(await blocker.innerText(), /DELIVERY/);
  assert.match(await blocker.innerText(), /IMPORT SPECIAL HANDLING|Prepare specialist file/i);
  await shot(page, "desktop-1-manager-queue-hero.png");

  // Filter is factual and bounded.
  await hero.getByRole("button", { name: "Chặn", exact: true }).click();
  const filteredRows = page.locator('[data-testid="control-intervention-row"]');
  assert.ok((await filteredRows.count()) >= 1, "blocking filter returns actual rows");
  for (let i = 0; i < await filteredRows.count(); i++) {
    assert.equal(await filteredRows.nth(i).getAttribute("data-control-band"), "BLOCKING");
  }
  await shot(page, "desktop-2-blocking-filter.png");

  // Drill-down must reduce uncertainty to the exact existing module context.
  const filteredBlocker = page
    .locator('[data-testid="control-intervention-row"][data-control-band="BLOCKING"]')
    .filter({ hasText: "Prepare specialist file" })
    .first();
  await filteredBlocker.click();
  await page.getByTestId("journey-module-context").waitFor();
  assert.match(await page.getByTestId("journey-module-context").innerText(), /IMPORT SPECIAL HANDLING/i);
  assert.match(await page.getByTestId("journey-module-context").innerText(), /Prepare specialist file/i);

  // Return and prove manager controls remain usable; no employee verdicts.
  await page.getByRole("link", { name: "Điều hành", exact: true }).first().click();
  await tower.waitFor();
  const workload = page.getByTestId("control-workload");
  assert.doesNotMatch(await workload.innerText(), /quá tải|rảnh|leaderboard|performance score/i);
  await hero.getByRole("button", { name: "Sắp hạn", exact: true }).click();
  await shot(page, "desktop-3-workload-and-horizon.png");

  // Mobile: dense manager content reflows instead of becoming a desktop map.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("control-intervention-queue").scrollIntoViewIfNeeded();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert.ok(overflow <= 1, `no horizontal page overflow (got ${overflow})`);
  const firstVisible = page.locator('[data-testid="control-intervention-row"]').first();
  if (await firstVisible.count()) {
    const box = await firstVisible.boundingBox();
    assert.ok(box && box.width <= 390, "mobile intervention row fits viewport");
  }
  await shot(page, "mobile-1-control-tower.png");

  assert.deepEqual(errors, [], "zero page errors for #170 flow");
  console.log(
    `PASS #170 browser: real blocker -> manager hero -> factual filter -> exact module drilldown -> workload neutral -> 390px no overflow -> ${output}`,
  );
} catch (err) {
  console.error(hostErrors.slice(-1800));
  throw err;
} finally {
  await browser?.close();
  host.kill();
}
