// Real-browser acceptance for Issue #166 Support Attention / Now V1.
//
// Reuses the existing isolated #162 acceptance host so all writes go through
// the real dispatcher -> authoritative persistence -> fresh readback path.
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const output = process.argv[2] || "/tmp/log166-screenshots";
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

const shot = (page, name) =>
  page.screenshot({ path: path.join(output, name), fullPage: false });

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

  const openShipment = async () => {
    await page.goto(HOST);
    await page.getByRole("link", { name: "Lô Hàng", exact: true }).first().click();
    await page.getByTestId("shipment-period-tat-ca").click();
    await page.getByRole("link", { name: "SEA-162", exact: true }).click();
    await page.getByTestId("shipment-journey").waitFor();
  };

  await openShipment();

  // Base acceptance A: work attention may exist while Journey keeps its own
  // physical/operational position. Attention must render before Journey and
  // must not certify a fake all-clear state.
  const initialAttention = page.getByTestId("attention-now");
  await initialAttention.waitFor();
  const journey = page.getByTestId("shipment-journey");
  assert.ok(
    await initialAttention.evaluate(
      (a, b) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING),
      await journey.elementHandle(),
    ),
    "Attention renders before Journey",
  );
  const initialPrimary = page.locator('[data-attention-source="PRIMARY_ACTION"]').first();
  await initialPrimary.waitFor();
  assert.match(await initialPrimary.innerText(), /Bổ sung số tờ khai nhập khẩu/);
  const initialModel = await (await page.request.get(`${HOST}/model`)).json();
  const initialStage = initialModel.shipments.find((s) => s.id === "SEA-162").journey.currentStageId;
  assert.doesNotMatch(await page.locator("main").innerText(), /toàn bộ lô hàng đang ổn định/i);
  await shot(page, "desktop-1-action-before-journey.png");

  // Attach the existing ACTIVE gated demo module through the real UI.
  await page.getByTestId("journey-add-module").click();
  await page.getByTestId("journey-add-module-panel").waitFor();
  await page.getByRole("radio", { name: "Chọn IMPORT SPECIAL HANDLING", exact: true }).check();
  const beforeAttach = await (await page.request.get(`${HOST}/model`)).json();
  const beforeVersion = beforeAttach.shipments.find((s) => s.id === "SEA-162").version;
  await page.getByTestId("journey-add-module-confirm").click();

  const moduleAttention = page
    .locator('[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]')
    .first();
  await moduleAttention.waitFor({ timeout: 15000 });
  const afterAttach = await (await page.request.get(`${HOST}/model`)).json();
  const lotAfterAttach = afterAttach.shipments.find((s) => s.id === "SEA-162");
  assert.ok(lotAfterAttach.version > beforeVersion, "attach persisted before Attention readback");
  assert.equal(
    lotAfterAttach.journey.currentStageId,
    initialStage,
    "Attention/module attach does not rewrite Journey physical/current position",
  );
  const instanceId = lotAfterAttach.journey.modules[0].instanceId;
  assert.match(await moduleAttention.innerText(), /Chặn/);
  assert.match(await moduleAttention.innerText(), /DELIVERY/);
  assert.match(await moduleAttention.innerText(), /Prepare specialist file/);
  await shot(page, "desktop-2-blocking-attention.png");

  // Attention deep-link must reach the exact existing module context.
  await moduleAttention.getByRole("link", { name: "Mở quy trình", exact: true }).click();
  await page.getByTestId("journey-module-context").waitFor();
  assert.match(await page.getByTestId("journey-module-context").innerText(), /IMPORT SPECIAL HANDLING/i);
  assert.match(await page.getByTestId("journey-module-context").innerText(), /Prepare specialist file/i);

  // Complete the first real step through the existing authoritative workspace.
  await page.getByTestId("journey-open-workspace").click();
  await page.getByTestId("journey-stage-workspace").waitFor();
  await page
    .getByTestId("journey-stage-workspace")
    .getByRole("button", { name: "Thông tin", exact: true })
    .click();
  await page.getByTestId("work-module-step-panel").waitFor();
  await page.getByTestId("work-module-step-complete").click();

  await page.waitForFunction(
    () => {
      const item = document.querySelector(
        '[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]',
      );
      return item?.textContent?.includes("Submit / process");
    },
    undefined,
    { timeout: 15000 },
  );
  const afterStep = await (await page.request.get(`${HOST}/model`)).json();
  const moduleAfterStep = afterStep.shipments
    .find((s) => s.id === "SEA-162")
    .journey.modules.find((m) => m.instanceId === instanceId);
  assert.equal(moduleAfterStep.completedCount, 1, "canonical completion fact persisted");
  assert.equal(moduleAfterStep.status, "BLOCKING", "gate stays blocking after only one step");
  assert.match(await moduleAttention.innerText(), /Submit \/ process/);
  await shot(page, "desktop-3-attention-after-authoritative-readback.png");

  // Home must derive the same top Attention truth, not a competing priority list.
  await page.locator('header a[href="/"]').first().click();
  await page.getByRole("heading", { name: /Ưu tiên bây giờ:/ }).waitFor();
  const homeText = await page.locator("main").innerText();
  assert.match(homeText, /Submit \/ process/);
  assert.match(homeText, /Chặn DELIVERY/);
  await shot(page, "desktop-4-home-same-attention-truth.png");
  await page.getByRole("button", { name: /XỬ LÝ NGAY/ }).click();
  await page.getByTestId("attention-now").waitFor();
  assert.match(
    await page
      .locator('[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]')
      .first()
      .innerText(),
    /Submit \/ process/,
  );

  // Create one ACTIVE gate-less module through the existing bounded library.
  const GATELESS_ID = "GATELESS_BROWSER_166";
  const GATELESS_NAME = "Quy trình tham chiếu không chặn cổng";
  await page.getByRole("link", { name: "Thư viện quy trình", exact: true }).first().click();
  await page.getByTestId("work-module-library").waitFor();
  await page.getByTestId("wm-library-new").click();
  const form = page.getByTestId("wm-library-form");
  await form.waitFor();
  await form.getByLabel("Mã quy trình", { exact: true }).fill(GATELESS_ID);
  await form.getByLabel("Tên hiển thị", { exact: true }).fill(GATELESS_NAME);
  await form.getByLabel("Trạng thái", { exact: true }).selectOption("ACTIVE");
  await form.getByLabel("Công đoạn neo", { exact: true }).selectOption("customs-import");
  assert.equal(await form.getByLabel("Cổng chặn", { exact: true }).inputValue(), "");
  await form.getByLabel("Mã bước 1", { exact: true }).fill("note-info");
  await form.getByLabel("Tên bước 1", { exact: true }).fill("Ghi nhận thông tin");
  await form.getByTestId("wm-add-step").click();
  await form.getByLabel("Mã bước 2", { exact: true }).fill("review-internal");
  await form.getByLabel("Tên bước 2", { exact: true }).fill("Rà soát nội bộ");
  await form.getByLabel("Phụ thuộc bước 2", { exact: true }).selectOption("note-info");
  await form.getByLabel("Loại phụ thuộc 2", { exact: true }).selectOption("INFORMATIONAL");
  await page.getByTestId("wm-library-submit").click();
  await page.waitForFunction(
    (id) =>
      [...document.querySelectorAll('[data-testid^="wm-row-"]')].some((row) =>
        row.textContent?.includes(id),
      ),
    GATELESS_ID,
    { timeout: 15000 },
  );

  // Attach the gate-less module and prove Attention stays ACTION with no fake gate.
  await page.getByRole("link", { name: "Lô Hàng", exact: true }).first().click();
  await page.getByTestId("shipment-period-tat-ca").click();
  await page.getByRole("link", { name: "SEA-162", exact: true }).click();
  await page.getByTestId("journey-add-module").click();
  await page.getByRole("radio", { name: `Chọn ${GATELESS_NAME}`, exact: true }).check();
  await page.getByTestId("journey-add-module-confirm").click();
  await page.waitForFunction(
    (name) =>
      [...document.querySelectorAll('[data-attention-source="WORK_MODULE"]')].some((item) =>
        item.textContent?.includes(name),
      ),
    GATELESS_NAME,
    { timeout: 15000 },
  );
  const gateLessAttention = page
    .locator('[data-attention-source="WORK_MODULE"]')
    .filter({ hasText: GATELESS_NAME })
    .first();
  assert.equal(await gateLessAttention.getAttribute("data-attention-band"), "ACTION");
  assert.doesNotMatch(await gateLessAttention.innerText(), /Chặn/);
  assert.doesNotMatch(await gateLessAttention.innerText(), /DELIVERY/);
  await shot(page, "desktop-5-gateless-action-no-fake-block.png");

  // Mobile: Attention rows stay readable and the page does not overflow.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("attention-now").scrollIntoViewIfNeeded();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert.ok(overflow <= 1, `no horizontal page overflow (got ${overflow})`);
  const firstAttentionButton = page
    .getByTestId("attention-now")
    .locator("a")
    .first();
  const box = await firstAttentionButton.boundingBox();
  assert.ok(box && box.height >= 40, "mobile Attention action remains tappable");
  await shot(page, "mobile-1-attention.png");

  assert.deepEqual(errors, [], "zero page errors for #166 flow");
  console.log(
    `PASS #166 browser: blocking module -> Attention before Journey -> real completion readback updates next action -> Home shares same truth -> gate-less module ACTION without fake gate -> 390px no overflow -> ${output}`,
  );
} catch (err) {
  console.error(hostErrors.slice(-1800));
  throw err;
} finally {
  await browser?.close();
  host.kill();
}
