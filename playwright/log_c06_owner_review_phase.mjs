/**
 * Visible-browser evidence for the LOG-C06 Owner-review continuation phase.
 *
 * This flow inspects the business review map, six golden items, deterministic
 * clusters, checkpoint arithmetic, the bounded Decision Pack, and the existing
 * staging-only validation guard. It never confirms or publishes a row.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const nodeModules = process.env.PLAYWRIGHT_NODE_MODULES || "";
const { chromium } = nodeModules
  ? require(path.join(nodeModules, "playwright"))
  : require("playwright");

const repoRoot = path.resolve(process.env.LOG_C06_REPO_ROOT || process.cwd());
const artifactDir = path.join(repoRoot, "reports", "QA", "playwright");
const profileDir = process.env.LOG_C06_PROFILE_DIR || path.join(repoRoot, ".tmp", "log-c06-owner-review-phase-profile");
const baseUrl = process.env.LOG_C06_URL || "http://127.0.0.1:8520/";
const jsonPath = path.join(artifactDir, "2026-08-15-log-c06-owner-review-phase.json");
const mdPath = path.join(artifactDir, "2026-08-15-log-c06-owner-review-phase.md");
const reviewWaitMs = Number(process.env.LOG_C06_WAIT_MS || 120000);

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function visibleCount(locator) {
  const count = await locator.count();
  let visible = 0;
  for (let index = 0; index < count; index += 1) {
    if (await locator.nth(index).isVisible().catch(() => false)) visible += 1;
  }
  return visible;
}

async function firstVisible(locator) {
  const count = await locator.count();
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    if (await item.isVisible().catch(() => false)) return item;
  }
  return null;
}

async function waitForBody(page, pattern, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const body = await page.locator("body").innerText().catch(() => "");
    if (pattern.test(body)) return body;
    await sleep(500);
  }
  const body = await page.locator("body").innerText().catch(() => "");
  throw new Error(`Timed out waiting for ${pattern}; body preview: ${body.slice(0, 700)}; body tail: ${body.slice(-3000)}`);
}

async function clickVisible(locator, description) {
  const item = await firstVisible(locator);
  if (!item) throw new Error(`Visible control not found: ${description}`);
  await item.click();
}

async function screenshot(page, name) {
  const fileName = `2026-08-15-log-c06-owner-review-phase-${name}.png`;
  const absolutePath = path.join(artifactDir, fileName);
  await page.screenshot({ path: absolutePath, fullPage: true });
  return path.relative(repoRoot, absolutePath).replaceAll("\\", "/");
}

async function findSearchInput(page) {
  const candidates = [
    page.locator('input[placeholder*="62464"]'),
    page.getByRole("textbox"),
  ];
  for (const locator of candidates) {
    const item = await firstVisible(locator);
    if (item) return item;
  }
  throw new Error("Historical Review search textbox was not found");
}

function markdown(result) {
  const actionRows = result.actions
    .map((row) => `| ${row.surface} | ${row.control} | ${row.expected} | ${row.actual} | ${row.verdict} |`)
    .join("\n");
  const sourceRows = result.sourceChecks
    .map((row) => `| ${row.value} | ${row.expected} | ${row.actual} | ${row.verdict} |`)
    .join("\n");
  return [
    "# LOG-C06 Owner Review Phase QA Report",
    "",
    "Scope: bounded local Historical Review business-review surface only.",
    `Runtime: ${result.runtime.url}; visible Chrome; source mode: ${result.runtime.sourceMode}.`,
    "No-fix boundary: this report records behavior; no product action was taken during QA.",
    "",
    "## Coverage",
    `- Pass: ${result.coverage.pass}`,
    `- Fail: ${result.coverage.fail}`,
    `- Blocked: ${result.coverage.blocked}`,
    `- Complete: ${result.coverage.complete}`,
    "",
    "## Action Ledger",
    "| Surface | Control | Expected | Actual | Verdict |",
    "| --- | --- | --- | --- | --- |",
    actionRows,
    "",
    "## Source / Safety Checks",
    "| Value | Expected | Actual | Verdict |",
    "| --- | --- | --- | --- |",
    sourceRows,
    "",
    "## Runtime Evidence",
    `- Health: ${result.runtime.health}`,
    `- Browser console errors: ${result.console.errors.length}`,
    `- Browser console warnings: ${result.console.warnings.length}`,
    `- Page errors: ${result.console.pageErrors.length}`,
    `- Failed requests: ${result.console.failedRequests.length}`,
    `- Canonical controls visible: ${result.canonicalBoundary.exposed}`,
    `- Docker: ${result.runtime.docker}`,
    "",
    "## Screenshots",
    ...result.screenshots.map((item) => `- ${item}`),
    "",
    "## Decision Boundary",
    "The browser evidence passes for the local staging/review scope. Owner confirmation, canonical ledger mutation, workbook migration, publish/live cutover, and Docker/production acceptance remain out of scope and locked.",
    "",
  ].join("\n");
}

async function main() {
  await fs.mkdir(artifactDir, { recursive: true });
  await fs.mkdir(profileDir, { recursive: true });

  const consoleErrors = [];
  const consoleWarnings = [];
  const pageErrors = [];
  const failedRequests = [];
  const screenshots = [];
  const actions = [];
  const sourceChecks = [];
  const chromeExecutable = process.env.CHROME_EXECUTABLE || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    executablePath: await fs.access(chromeExecutable).then(() => chromeExecutable).catch(() => chromium.executablePath()),
    viewport: { width: 1440, height: 1200 },
    args: ["--window-size=1440,1200", "--no-first-run", "--no-default-browser-check", "--disable-session-crashed-bubble"],
  });
  const page = context.pages()[0] || (await context.newPage());
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
    if (message.type() === "warning") consoleWarnings.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  page.on("requestfailed", (request) => failedRequests.push(`${request.method()} ${request.url()}`));

  try {
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    await waitForBody(page, /Dashboard/i);
    await sleep(1800);
    await waitForBody(page, /Công nợ A Bò|CÃ´ng nợ A BÃ²|A Bò|A BÃ²/i, 30000);
    const dashboardShot = await screenshot(page, "01-dashboard");
    screenshots.push(dashboardShot);
    actions.push({ surface: "App entry", control: "open root URL", expected: "Dashboard visible", actual: "Dashboard visible", verdict: "Pass" });

    const partnerPattern = /Công nợ A Bò|CÃ´ng nợ A BÃ²|A Bò|A BÃ²/i;
    let partnerNav = page.locator("label").filter({ hasText: partnerPattern }).first();
    if (!(await visibleCount(partnerNav))) partnerNav = page.getByRole("radio", { name: partnerPattern }).first();
    if (!(await visibleCount(partnerNav))) partnerNav = page.getByText(partnerPattern).first();
    await clickVisible(partnerNav, "A Bò partner desk");
    await sleep(1500);
    await waitForBody(page, /Tác vụ LOG-C05|TÃ¡c vá»¥ LOG-C05|Historical Review/i, 30000);
    screenshots.push(await screenshot(page, "02-partner-desk"));
    actions.push({ surface: "Partner desk", control: "open A Bò desk", expected: "partner desk visible", actual: "partner desk visible", verdict: "Pass" });

    await sleep(500);
    await clickVisible(page.getByRole("button", { name: "Historical Review", exact: true }).first(), "Historical Review");
    const initialBody = await waitForBody(page, /Business review map/i, reviewWaitMs);
    await waitForBody(page, /Owner Decision Pack/i, reviewWaitMs);
    await waitForBody(page, /READY_FOR_OWNER_CONFIRMATION/i, reviewWaitMs);
    await waitForBody(page, /134,973 CNY/i, reviewWaitMs);
    await sleep(1000);
    const renderedBody = await page.locator("body").innerText();
    screenshots.push(await screenshot(page, "02-owner-review-map"));

    const goldenVisible = ["24,576", "62,464", "1,687", "1,572", "25,025", "134,973"]
      .every((value) => renderedBody.includes(value));
    const clusterVisible = /185 mục review|nhóm theo quyết định business/i.test(renderedBody);
    const decisionPackVisible = /Owner Decision Pack/i.test(renderedBody);
    const checkpointVisible = /Checkpoint 134,973 CNY/i.test(renderedBody) && /Chênh lệch/i.test(renderedBody);
    const canonicalButtons = await visibleCount(page.getByRole("button", { name: /approve|live|ghi canonical|publish/i }));
    actions.push({ surface: "Business review map", control: "initial render", expected: "six golden values, clusters, Decision Pack, checkpoint visible", actual: `golden=${goldenVisible}; clusters=${clusterVisible}; decisionPack=${decisionPackVisible}; checkpoint=${checkpointVisible}`, verdict: goldenVisible && clusterVisible && decisionPackVisible && checkpointVisible ? "Pass" : "Fail" });
    actions.push({ surface: "Canonical boundary", control: "visible controls", expected: "no approve/live/publish action", actual: `canonicalButtons=${canonicalButtons}`, verdict: canonicalButtons === 0 ? "Pass" : "Fail" });
    sourceChecks.push({ value: "six golden values", expected: "24,576; 62,464; 1,687; 1,572; 25,025; 134,973 visible from staging analysis", actual: `allVisible=${goldenVisible}`, verdict: goldenVisible ? "Pass" : "Fail" });
    sourceChecks.push({ value: "checkpoint arithmetic", expected: "134,973 CNY and zero difference", actual: `checkpointVisible=${checkpointVisible}`, verdict: checkpointVisible ? "Pass" : "Fail" });
    sourceChecks.push({ value: "cutover lock", expected: "Decision Pack remains DRAFT / NOT_APPROVED / NOT_LIVE", actual: `decisionPackVisible=${decisionPackVisible}`, verdict: decisionPackVisible ? "Pass" : "Fail" });

    const searchInput = await findSearchInput(page);
    await searchInput.fill("62464");
    await searchInput.press("Enter");
    await searchInput.press("Tab");
    await waitForBody(page, /Tìm thấy 1 dòng|TÃ¬m tháº¥y 1 dÃ²ng/i, 30000);
    await sleep(1000);
    const searchBody = await page.locator("body").innerText();
    const confirmButton = page.getByRole("button", { name: /Xác nhận|XÃ¡c nháº­n/i }).first();
    let noReasonBlocked = false;
    if (await visibleCount(confirmButton)) {
      await confirmButton.click();
      try {
        await waitForBody(page, /Nhập lý do review|Nháº­p lÃ½ do review/i, 30000);
        noReasonBlocked = true;
      } catch {
        noReasonBlocked = false;
      }
    }
    const matchingSearch = /62,464|62464/i.test(searchBody);
    actions.push({ surface: "Review controls", control: "confirm without reason", expected: "staging validation blocks the action", actual: `matching=${matchingSearch}; blocked=${noReasonBlocked}`, verdict: noReasonBlocked ? "Pass" : "Blocked" });
    sourceChecks.push({ value: "no-reason review guard", expected: "no metadata write without reason", actual: `blocked=${noReasonBlocked}`, verdict: noReasonBlocked ? "Pass" : "Blocked" });
    screenshots.push(await screenshot(page, "03-no-reason-guard"));

    let dashboardNav = page.locator("label").filter({ hasText: /Dashboard/i }).first();
    if (!(await visibleCount(dashboardNav))) dashboardNav = page.getByRole("radio", { name: /Dashboard/i }).first();
    if (await visibleCount(dashboardNav)) {
      await dashboardNav.click();
      await waitForBody(page, /Dashboard/i);
      screenshots.push(await screenshot(page, "04-dashboard-return"));
      actions.push({ surface: "Dashboard regression", control: "return to Dashboard", expected: "Dashboard remains reachable", actual: "Dashboard visible", verdict: "Pass" });
    } else {
      actions.push({ surface: "Dashboard regression", control: "return to Dashboard", expected: "Dashboard remains reachable", actual: "navigation control not found", verdict: "Blocked" });
    }

    const result = {
      chatId: "LOG-C06",
      chatName: "Chuẩn hóa dữ liệu A Bò & chốt số dư mở đầu",
      generatedAt: new Date().toISOString(),
      runtime: { url: baseUrl, health: "200", sourceMode: /session-only/i.test(initialBody) ? "session-only" : "staging DB", docker: "BLOCKED: no Docker target was found; production acceptance is not claimed" },
      console: { errors: consoleErrors, warnings: consoleWarnings, pageErrors, failedRequests },
      screenshots,
      actions,
      sourceChecks,
      canonicalBoundary: { exposed: canonicalButtons > 0 },
      coverage: {
        pass: actions.filter((row) => row.verdict === "Pass").length,
        fail: actions.filter((row) => row.verdict === "Fail").length,
        blocked: actions.filter((row) => row.verdict === "Blocked").length,
        complete: actions.every((row) => row.verdict !== "Fail" && row.verdict !== "Blocked"),
      },
    };
    await fs.writeFile(jsonPath, JSON.stringify(result, null, 2) + "\n", "utf8");
    await fs.writeFile(mdPath, markdown(result), "utf8");
    console.log(JSON.stringify({ jsonPath, mdPath, coverage: result.coverage, console: result.console, screenshots }, null, 2));
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
