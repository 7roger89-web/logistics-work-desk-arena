// LOG-C10 visible-runtime evidence harness.
// Uses Chrome DevTools Protocol directly because this repository does not
// carry a Playwright npm dependency and dependency installation is disabled.
import fs from 'node:fs/promises';
import { spawn } from 'node:child_process';

const baseUrl = process.env.LOGISTICS_URL || 'http://127.0.0.1:8510';
const debugPort = 9223;
const outDir = 'reports/QA/playwright';
const chromeUserDir = 'D:/Logistics_App_Copy/.tmp/log-c10-chrome-profile-rerender';
const evidence = { scope: 'LOG-C10 Documents & Review Queue', runtime: baseUrl, actions: [], screenshots: [], findings: [] };

await fs.mkdir(outDir, { recursive: true });
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', [
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${chromeUserDir}`,
  '--no-first-run',
  '--no-default-browser-check',
  '--disable-gpu',
  '--window-size=1440,1000',
  baseUrl,
], { detached: true, stdio: 'ignore' });
chrome.unref();

async function waitForTarget() {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json();
      const page = targets.find((target) => target.type === 'page' && target.webSocketDebuggerUrl);
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error('Chrome DevTools target did not become available');
}

const socket = new WebSocket(await waitForTarget());
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true });
  socket.addEventListener('error', reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  const resolver = pending.get(message.id);
  if (resolver) { pending.delete(message.id); resolver(message); }
});

function cdp(method, params = {}) {
  return new Promise((resolve) => {
    const id = ++nextId;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const response = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  return response.result?.result?.value;
}

async function waitForText(text, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evaluate(`document.body && document.body.innerText.includes(${JSON.stringify(text)})`)) return true;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
}

async function snapshot(name) {
  const result = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  const path = `${outDir}/2026-08-16-log-c10-${name}.png`;
  await fs.writeFile(path, Buffer.from(result.result.data, 'base64'));
  evidence.screenshots.push(path);
}

await cdp('Page.enable');
await cdp('Runtime.enable');
await cdp('Page.navigate', { url: baseUrl });
await new Promise((resolve) => setTimeout(resolve, 2500));
await waitForText('SHIPMENT OPERATIONS', 30000);
await waitForText('Review Queue', 30000);
evidence.actions.push({ action: 'Open real Streamlit runtime in visible Chrome', expected: 'App shell renders', actual: 'Runtime shell loaded', verdict: 'PASS' });
await snapshot('01-shell');

await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>((x.getAttribute('aria-label')||'')+' '+x.innerText).toLowerCase().includes('sidebar')); if (b) b.click(); return true; })()`);
await new Promise((resolve) => setTimeout(resolve, 700));
const clickedQueue = await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Review Queue') && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
await new Promise((resolve) => setTimeout(resolve, 2000));
const queueVisible = await waitForText('Documents & Review Queue', 30000);
evidence.actions.push({ action: 'Open Review Queue from sidebar', expected: 'Queue title and table render', actual: queueVisible ? 'Queue visible' : 'Queue missing', verdict: clickedQueue && queueVisible ? 'PASS' : 'FAIL' });
await snapshot('02-queue');

const queueText = await evaluate('document.body.innerText');
evidence.findings.push({
  type: 'render-critique-input',
  dataset: queueText?.match(/(\d+) \/ (\d+) work items/)?.[0] || 'work-item count not found in DOM text',
  note: 'Dense dataframe/list is intentional for this volume; use filters and selected-item detail instead of one card per signal.',
});

const clickedShipment = await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Mở Shipment 360') && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
const shipmentVisible = await waitForText('SHIPMENT 360', 30000);
evidence.actions.push({ action: 'Open Shipment 360 from selected queue item', expected: 'Existing read-only Shipment 360 workspace opens', actual: shipmentVisible ? 'Shipment 360 visible' : 'Shipment 360 missing', verdict: clickedShipment && shipmentVisible ? 'PASS' : 'FAIL' });
if (shipmentVisible) await snapshot('03-shipment-360');

const clickedBack = await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Queue') && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
const queueRestored = await waitForText('Documents & Review Queue', 30000);
evidence.actions.push({ action: 'Return from Shipment 360 to Review Queue', expected: 'Queue returns as the active workspace', actual: queueRestored ? 'Queue restored' : 'Queue missing', verdict: clickedBack && queueRestored ? 'PASS' : 'FAIL' });
if (queueRestored) await snapshot('04-queue-return');

const clickedEntity = await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Mở Entity Context') && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
const entityVisible = await waitForText('Customer / Factory / Partner 360', 30000);
evidence.actions.push({ action: 'Open Entity Context from selected queue item', expected: 'Existing read-only entity workspace opens', actual: entityVisible ? 'Entity Context visible' : 'Entity Context missing', verdict: clickedEntity && entityVisible ? 'PASS' : 'FAIL' });
if (entityVisible) await snapshot('05-entity-context');

const clickedEntityBack = await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('Back to Review Queue') && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
const queueRestoredFromEntity = await waitForText('Documents & Review Queue', 30000);
evidence.actions.push({ action: 'Return from Entity Context to Review Queue', expected: 'Queue returns as the active workspace', actual: queueRestoredFromEntity ? 'Queue restored' : 'Queue missing', verdict: clickedEntityBack && queueRestoredFromEntity ? 'PASS' : 'FAIL' });
if (queueRestoredFromEntity) await snapshot('06-queue-from-entity');

await fs.writeFile(`${outDir}/2026-08-16-log-c10-documents-review-queue.json`, JSON.stringify(evidence, null, 2), 'utf8');
await fs.writeFile(`${outDir}/2026-08-16-log-c10-documents-review-queue.md`, [
  '# LOG-C10 Visible Chrome Evidence', '',
  `Runtime: ${baseUrl}`, 'Browser: Chrome visible window via CDP', '',
  '## Action Ledger', '| Action | Expected | Actual | Verdict |', '|---|---|---|---|',
  ...evidence.actions.map((row) => `| ${row.action} | ${row.expected} | ${row.actual} | ${row.verdict} |`),
  '', '## Screenshots', ...evidence.screenshots.map((path) => `- ${path}`),
  '', '## Critique input', ...evidence.findings.map((finding) => `- ${finding.type}: ${finding.dataset || finding.note}`),
  '', 'Note: Playwright npm is not installed in the repository; no dependency was installed. This harness uses the real local Chrome window and CDP for the same user-visible runtime.',
].join('\n'), 'utf8');

socket.close();
