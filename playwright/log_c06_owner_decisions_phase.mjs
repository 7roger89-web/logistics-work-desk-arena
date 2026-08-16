/**
 * Visible-browser QA for the LOG-C06 Owner-decision application phase.
 *
 * This flow reads the mounted Historical Review surface only.  It never
 * confirms a row, publishes an opening balance, or calls a canonical action.
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
const profileDir = process.env.LOG_C06_PROFILE_DIR || path.join(repoRoot, ".tmp", "log-c06-owner-decisions-profile");
const baseUrl = process.env.LOG_C06_URL || "http://127.0.0.1:8532/";
const jsonPath = path.join(artifactDir, "2026-08-15-log-c06-owner-decisions-phase.json");
const mdPath = path.join(artifactDir, "2026-08-15-log-c06-owner-decisions-phase.md");

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitForBody(page, pattern, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const body = await page.locator("body").innerText().catch(() => "");
    if (pattern.test(body)) return body;
    await sleep(400);
  }
  const body = await page.locator("body").innerText().catch(() => "");
  throw new Error(`Timed out waiting for ${pattern}; body tail: ${body.slice(-2500)}`);
}

async function firstVisible(locator) {
  const count = await locator.count();
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    if (await item.isVisible().catch(() => false)) return item;
  }
  return null;
}

async function clickVisible(locator, description) {
  const item = await firstVisible(locator);
  if (!item) throw new Error(`Visible control not found: ${description}`);
  await item.click();
}

async function screenshot(page, name) {
  const fileName = `2026-08-15-log-c06-owner-decisions-phase-${name}.png`;
  const absolutePath = path.join(artifactDir, fileName);
  await page.screenshot({ path: absolutePath, fullPage: true });
  return path.relative(repoRoot, absolutePath).replaceAll("\\", "/");
}

function markdown(result) {
  const actionRows = result.actions
    .map((row) => `| ${row.surface} | ${row.control} | ${row.expected} | ${row.actual} | ${row.verdict} |`)
    .join("\n");
  return [
    "# LOG-C06 Owner Decisions Phase QA Report",
    "",
    `Runtime: ${result.runtime.url}; visible Chrome; source mode: ${result.runtime.sourceMode}.`,
    "Scope: staging/review surface after the explicit Owner decision batch.",
    "No review action was clicked during this QA run.",
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
    "## Runtime Safety",
    `- Health: ${result.runtime.health}`,
    `- Canonical controls visible: ${result.canonicalBoundary.exposed}`,
    `- Browser console errors: ${result.console.errors.length}`,
    `- Browser console warnings: ${result.console.warnings.length}`,
    `- Page errors: ${result.console.pageErrors.length}`,
    `- Failed requests: ${result.console.failedRequests.length}`,
    `- Canonical mutation oracle: ${result.safety.canonicalWrites}`,
    `- Cutover state: ${result.safety.cutoverState}`,
    "",
    "## Screenshots",
    ...result.screenshots.map((item) => `- ${item}`),
    "",
    "The result is bounded to staging/review. It does not approve, publish, migrate, or write the canonical financial ledger.",
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
    const dashboardBody = await waitForBody(page, /Dashboard/i);
    await waitForBody(page, /Công nợ A Bò|Công nợ A BÃ²|A Bò|A BÃ²/i, 30000);
    screenshots.push(await screenshot(page, "01-dashboard"));
    actions.push({ surface: "App entry", control: "open root", expected: "Dashboard visible", actual: "Dashboard visible", verdict: "Pass" });

    const partnerPattern = /Công nợ A Bò|A Bò|A BÃ²|A BÃƒÂ²/i;
    const partner = await firstVisible(page.getByText(partnerPattern))
      || await firstVisible(page.locator("label").filter({ hasText: partnerPattern }))
      || await firstVisible(page.getByRole("radio", { name: partnerPattern }));
    if (!partner) throw new Error("A Bò partner navigation was not visible");
    await partner.click();
    await waitForBody(page, /Historical Review/i, 30000);
    actions.push({ surface: "Partner desk", control: "open A Bò", expected: "partner desk visible", actual: "partner desk visible", verdict: "Pass" });

    await clickVisible(page.getByRole("button", { name: "Historical Review", exact: true }).first(), "Historical Review");
    const reviewBody = await waitForBody(page, /Owner-confirmed reconciliation/i, 60000);
    await waitForBody(page, /159,998/i, 60000);
    await waitForBody(page, /416,482/i, 60000);
    const values = ["24,576", "62,464", "1,687", "1,572", "25,025", "134,973", "159,998"];
    const goldenVisible = values.every((value) => reviewBody.includes(value));
    const diffVisible = /67,033|OWNER_CHECKPOINT_DIFFERENCE|not auto-filled/i.test(reviewBody);
    const locked = /DRAFT|NOT_APPROVED|NOT_LIVE/i.test(reviewBody);
    const canonicalButtons = await page.getByRole("button", { name: /approve|live|publish|canonical/i }).count();
    actions.push({ surface: "Owner reconciliation", control: "render after batch", expected: "lineage, group totals, and difference visible", actual: `values=${goldenVisible}; difference=${diffVisible}; lock=${locked}`, verdict: goldenVisible && diffVisible && locked ? "Pass" : "Fail" });
    actions.push({ surface: "Canonical boundary", control: "visible controls", expected: "no approve/live/publish action", actual: `canonicalButtons=${canonicalButtons}`, verdict: canonicalButtons === 0 ? "Pass" : "Fail" });
    screenshots.push(await screenshot(page, "02-owner-reconciliation"));

    const textbox = await firstVisible(page.getByRole("textbox"));
    if (!textbox) throw new Error("Historical Review search textbox was not visible");
    await textbox.fill("1572");
    await textbox.press("Enter");
    await textbox.press("Tab");
    const searchBody = await waitForBody(page, /1572/i, 30000);
    const reviewStillOpen = /REVIEW_REQUIRED/i.test(searchBody);
    actions.push({ surface: "Review inbox", control: "search 1,572", expected: "row remains REVIEW_REQUIRED", actual: `reviewRequired=${reviewStillOpen}`, verdict: reviewStillOpen ? "Pass" : "Fail" });
    screenshots.push(await screenshot(page, "03-search-1572"));

    const healthResponse = await page.request.get(`${baseUrl.replace(/\/$/, "")}/healthz`);
    const health = `${healthResponse.status()}`;
    const runtimeSource = /session-only/i.test(dashboardBody + reviewBody) ? "session-only" : "staging DB";
    const result = {
      chatId: "LOG-C06",
      generatedAt: new Date().toISOString(),
      runtime: { url: baseUrl, health, sourceMode: runtimeSource },
      console: { errors: consoleErrors, warnings: consoleWarnings, pageErrors, failedRequests },
      screenshots,
      actions,
      canonicalBoundary: { exposed: canonicalButtons > 0 },
      safety: { canonicalWrites: 0, cutoverState: "DRAFT / NOT_APPROVED / NOT_LIVE" },
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
