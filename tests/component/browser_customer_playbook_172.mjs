// Real-browser acceptance for Issue #172 Customer Playbook V1.
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const output = process.argv[2] || "/tmp/log172-screenshots";
mkdirSync(output, { recursive: true });

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const HOST = "http://127.0.0.1:9502";
const host = spawn(
  process.env.PYTHON || "python3",
  ["scripts/verify_work_module_library_162.py"],
  {
    cwd: root,
    stdio: ["ignore", "ignore", "pipe"],
  }
);
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

  // 1. Attach one real BLOCKING Work Module to SEA-162 (customerId=CUST-ANPHAT)
  // through the existing authoritative UI so shared Attention carries a real
  // BLOCKING item for CUST-ANPHAT.
  await page.goto(HOST);
  await page.getByRole("link", { name: "Lô Hàng", exact: true }).first().click();
  await page.getByTestId("shipment-period-tat-ca").click();
  await page.getByRole("link", { name: "SEA-162", exact: true }).click();
  await page.getByTestId("shipment-journey").waitFor();

  await page.getByTestId("journey-add-module").click();
  await page.getByTestId("journey-add-module-panel").waitFor();
  await page
    .getByRole("radio", { name: "Chọn IMPORT SPECIAL HANDLING", exact: true })
    .check();
  await page.getByTestId("journey-add-module-confirm").click();
  await page
    .locator('[data-attention-source="WORK_MODULE"][data-attention-band="BLOCKING"]')
    .first()
    .waitFor({ timeout: 15000 });

  // 2. Enrich the live backend model in-browser with:
  //    - existing customer operational note on CUST-ANPHAT
  //    - a second attached module of the same template (WAITING) + one UNKNOWN
  //      module on the second exact-linked shipment LO-0306 (customerId=CUST-ANPHAT)
  //    - a name-similar unlinked shipment (customer="An Phát JSC", customerId="")
  //      plus its own attention item to challenge exact-linkage boundary
  await page.evaluate(async () => {
    const model = await (await fetch("/model")).json();
    const anphat = model.customers.find((c) => c.id === "CUST-ANPHAT");
    if (anphat) {
      anphat.note =
        "Ghi chú vận hành chuẩn: kiểm tra seal và gửi biên bản kiểm đếm container trước khi giao kho Đình Vũ.";
    }
    const sea162 = model.shipments.find((s) => s.id === "SEA-162");
    const lo0306 = model.shipments.find((s) => s.id === "LO-0306");
    const modTemplate = sea162?.journey?.modules?.[0];
    if (lo0306 && modTemplate) {
      lo0306.journey = lo0306.journey || {
        nodes: [],
        edges: [],
        currentStageId: "customs-import",
        owner: "Sale A",
        positionNote: "",
        seaFacts: {},
        primaryAction: {
          text: lo0306.nextAction || "Khai báo hải quan",
          detail: lo0306.nextActionDetail || "",
          priority: "CanXuLy",
          route: lo0306.nextRoute || "/lo-hang/LO-0306?tab=nhap",
        },
      };
      lo0306.journey.modules = [
        {
          ...structuredClone(modTemplate),
          instanceId: "WM-SECOND-WAITING",
          status: "WAITING",
          summary: "1/3 bước",
          completedCount: 1,
          totalCount: 3,
          gateText: "",
        },
        {
          instanceId: "WM-UNKNOWN-172",
          templateId: "UNKNOWN_TEMPLATE_172",
          templateVersion: 9,
          name: "UNKNOWN_TEMPLATE_172",
          description: "",
          status: "UNKNOWN",
          summary: "UNKNOWN",
          completedCount: 0,
          totalCount: 0,
          nextStep: "",
          nextStepId: "",
          deadline: "",
          blocker: "Không đọc được phiên bản quy trình đã gắn.",
          gate: {},
          gateText: "",
          provenance: "MANUAL_ADDITION",
          addedBy: "support",
          addedAt: "2026-10-03",
          reason: "",
          unresolved: true,
          steps: [],
        },
      ];
    }

    // Add unlinked name-similar shipment (no customerId)
    if (lo0306) {
      model.shipments.push({
        ...structuredClone(lo0306),
        id: "LO-NAME-ONLY-999",
        customerId: "",
        customer: "An Phát JSC",
        status: "Đang vận chuyển",
      });
    }

    // Add UNKNOWN attention item on LO-0306 and an unlinked shipment attention item
    model.attention = model.attention || [];
    model.attention.push(
      {
        id: "ATT-UNKNOWN-172",
        shipmentId: "LO-0306",
        sourceType: "WORK_MODULE",
        sourceRef: "MODULE:LO-0306:WM-UNKNOWN-172",
        band: "ACTION",
        reason: "Không đọc được phiên bản quy trình đã gắn.",
        action: "Kiểm tra quy trình đã gắn",
        context: "UNKNOWN_TEMPLATE_172",
        route: "/lo-hang/LO-0306?tab=nhap",
        owner: "",
        deadline: "",
        deadlineDate: "",
        blockedGate: "",
        primary: false,
        moduleTemplateId: "UNKNOWN_TEMPLATE_172",
        moduleName: "UNKNOWN_TEMPLATE_172",
        provenance: "work_module:UNKNOWN_TEMPLATE_172@9",
        unknown: true,
      },
      {
        id: "ATT-UNLINKED-999",
        shipmentId: "LO-NAME-ONLY-999",
        sourceType: "TASK",
        sourceRef: "TASK:UNLINKED-999",
        band: "OVERDUE",
        reason: "Việc được giao",
        action: "Việc của lô chỉ trùng tên",
        context: "An Phát JSC",
        route: "/lo-hang/LO-NAME-ONLY-999?tab=lay-hang",
        owner: "Support A",
        deadline: "01/10/2026",
        deadlineDate: "2026-10-01",
        blockedGate: "",
        primary: false,
        provenance: "core.database.load_tasks",
        unknown: false,
      }
    );

    // Ensure CUST-THIENAN has zero attention items so Scenario D is tested cleanly
    model.attention = model.attention.filter((a) => a.shipmentId !== "LO-0295");

    window.deliver(model);
  });

  // 3. Navigate to Customers (/khach-hang) and open CUST-ANPHAT playbook
  await page.getByRole("link", { name: "Khách Hàng", exact: true }).first().click();
  const openAnPhat = page.getByTestId("customer-open-playbook-CUST-ANPHAT");
  await openAnPhat.waitFor();
  await shot(page, "desktop-1-customers-list.png");
  await openAnPhat.click();

  const playbook = page.getByTestId("customer-playbook");
  await playbook.waitFor();

  const identityBlock = page.getByTestId("playbook-identity-note");
  const attentionHero = page.getByTestId("playbook-attention-hero");
  const shipmentsBlock = page.getByTestId("playbook-linked-shipments");
  const concentrationBlock = page.getByTestId("playbook-concentration");

  // Verify visual ordering and 4-block structure
  assert.ok(
    await attentionHero.evaluate(
      (a, b) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING),
      await shipmentsBlock.elementHandle()
    ),
    "Customer Attention hero is above linked shipments"
  );

  // Scenario A — customer operating note
  const noteText = await page.getByTestId("playbook-operating-note-text").innerText();
  assert.match(noteText, /kiểm tra seal và gửi biên bản kiểm đếm container/i);

  // Scenario B — exact customerId linkage (LO-0306 & SEA-162 included; LO-NAME-ONLY-999 excluded)
  const playbookText = await playbook.innerText();
  assert.match(playbookText, /LO-0306/);
  assert.match(playbookText, /SEA-162/);
  assert.doesNotMatch(playbookText, /LO-NAME-ONLY-999/);
  assert.doesNotMatch(playbookText, /Việc của lô chỉ trùng tên/);

  // Scenario C — Attention reuse
  const blockingItem = page
    .locator('[data-testid="playbook-attention-item"][data-attention-band="BLOCKING"]')
    .filter({ hasText: "Prepare specialist file" })
    .first();
  await blockingItem.waitFor();
  assert.match(await blockingItem.innerText(), /DELIVERY/);

  // Scenario E & F — Work Modules concentration & UNKNOWN semantics
  const concText = await concentrationBlock.innerText();
  assert.match(concText, /IMPORT SPECIAL HANDLING/i);
  assert.match(concText, /2 lô · 2 lần gắn/);
  assert.match(concText, /Đang chặn: 1/);
  assert.match(concText, /Đang chờ: 1/);
  assert.match(concText, /UNKNOWN \(Chưa xác định\): 1/);
  assert.doesNotMatch(
    playbookText,
    /healthy|safe|risky|problematic|bottleneck|leaderboard/i
  );
  await shot(page, "desktop-2-customer-playbook-hero.png");

  await concentrationBlock.scrollIntoViewIfNeeded();
  await shot(page, "desktop-3-shipments-and-concentration.png");

  // Drill-down from Customer Attention hero into exact shipment module context
  await blockingItem.scrollIntoViewIfNeeded();
  await blockingItem.getByTestId("playbook-attention-link").click();
  await page.getByTestId("journey-module-context").waitFor();
  assert.match(
    await page.getByTestId("journey-module-context").innerText(),
    /IMPORT SPECIAL HANDLING/i
  );
  assert.match(
    await page.getByTestId("journey-module-context").innerText(),
    /Prepare specialist file/i
  );
  await shot(page, "desktop-4-attention-drilldown.png");

  // Scenario D — Customer with linked shipment, empty note, and no Attention
  await page.getByRole("link", { name: "Khách Hàng", exact: true }).first().click();
  await page.getByTestId("customer-open-playbook-CUST-THIENAN").click();
  await page.getByTestId("playbook-operating-note-empty").waitFor();
  await page.getByTestId("playbook-attention-empty").waitFor();
  const emptyAttText = await page.getByTestId("playbook-attention-empty").innerText();
  assert.doesNotMatch(emptyAttText, /healthy|safe|an toàn|ổn 100%/i);
  await shot(page, "desktop-5-no-attention-neutral.png");

  // Scenario G — Mobile 390px usable with zero horizontal page overflow
  await page.getByRole("link", { name: "Khách Hàng", exact: true }).first().click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("customer-open-playbook-mobile-CUST-ANPHAT").click();
  await page.getByTestId("customer-playbook").waitFor();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth
  );
  assert.ok(overflow <= 1, `no horizontal page overflow at 390px (got ${overflow})`);
  const heroBox = await page.getByTestId("playbook-attention-hero").boundingBox();
  assert.ok(heroBox && heroBox.width <= 390, "mobile hero fits within 390px viewport");
  await shot(page, "mobile-1-customer-playbook-390px.png");

  assert.deepEqual(errors, [], "zero page errors for #172 flow");
  console.log(
    `PASS #172 browser: exact customerId linkage -> operating note -> shared Attention drilldown -> factual module/gate concentration -> UNKNOWN preserved -> neutral empty state -> 390px no overflow -> ${output}`
  );
} catch (err) {
  console.error(hostErrors.slice(-1800));
  throw err;
} finally {
  await browser?.close();
  host.kill();
}
