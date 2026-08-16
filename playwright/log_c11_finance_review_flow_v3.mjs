// LOG-C11 visible browser evidence harness.
import fs from 'node:fs/promises';
import { spawn } from 'node:child_process';

const baseUrl = process.env.LOGISTICS_URL || 'http://127.0.0.1:8510';
const debugPort = 9224;
const outDir = 'reports/QA/playwright';
const chromeUserDir = 'D:/Logistics_App_Copy/.tmp/log-c11-chrome-profile';
const evidence = { scope: 'LOG-C11 Finance Review', runtime: baseUrl, actions: [], screenshots: [], findings: [] };
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
let seq = 0;
const pending = new Map();
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  const waiter = pending.get(message.id);
  if (waiter) { pending.delete(message.id); waiter(message); }
});
function command(method, params = {}) {
  return new Promise((resolve) => {
    const id = ++seq;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  return result?.result?.result?.value;
}
async function waitForText(text, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const body = await evaluate('document.body.innerText');
    if (body?.includes(text)) return true;
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
  return false;
}
async function clickText(text) {
  return evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x => x.innerText.includes(${JSON.stringify(text)}) && x.offsetParent !== null); if (!b) return false; b.click(); return true; })()`);
}
async function snapshot(name) {
  const shot = await command('Page.captureScreenshot', { format: 'png' });
  const path = `${outDir}/2026-08-16-log-c11-${name}.png`;
  await fs.writeFile(path, Buffer.from(shot.result.data, 'base64'));
  evidence.screenshots.push(path);
}

await new Promise((resolve, reject) => socket.addEventListener('open', resolve, { once: true }));
await command('Page.enable');
const shellVisible = await waitForText('LOGISTICS', 30000);
evidence.actions.push({ action: 'Open local application shell', expected: 'Application shell renders', actual: shellVisible ? 'Shell visible' : 'Shell missing', verdict: shellVisible ? 'PASS' : 'FAIL' });
await snapshot('v3-01-shell');
await evaluate(`(() => { const b=[...document.querySelectorAll('button')].find(x => ((x.getAttribute('aria-label')||'')+' '+x.innerText).toLowerCase().includes('sidebar')); if (b) b.click(); return true; })()`);
await new Promise((resolve) => setTimeout(resolve, 700));
const openedFinance = await clickText('Finance Review');
const financeVisible = await waitForText('FINANCIAL CONTROL', 30000);
evidence.actions.push({ action: 'Open Finance Review from navigation', expected: 'Finance Review workspace renders', actual: financeVisible ? 'Finance Review visible' : 'Finance Review missing', verdict: openedFinance && financeVisible ? 'PASS' : 'FAIL' });
await snapshot('v3-02-finance-review');
const financeText = await evaluate('document.body.innerText');
await fs.writeFile(`${outDir}/2026-08-16-log-c11-finance-review-v3-body.txt`, financeText || '', 'utf8');
evidence.findings.push({ type: 'render-critique-input', note: financeText?.includes('UNKNOWN') ? 'UNKNOWN state visible' : 'UNKNOWN state not visible in current dataset', hasInvestigationQueue: financeText?.includes('Investigation queue'), hasCurrency: financeText?.includes('Currency'), hasReadOnly: financeText?.toLowerCase().includes('read-only') });
const backQueue = await clickText('Review Queue');
const queueVisible = await waitForText('Documents & Review Queue', 30000);
evidence.actions.push({ action: 'Return to Review Queue', expected: 'Review Queue remains reachable', actual: queueVisible ? 'Review Queue visible' : 'Review Queue missing', verdict: backQueue && queueVisible ? 'PASS' : 'FAIL' });
if (queueVisible) await snapshot('v3-03-review-queue-return');
await fs.writeFile(`${outDir}/2026-08-16-log-c11-finance-review-v3.json`, JSON.stringify(evidence, null, 2), 'utf8');
await fs.writeFile(`${outDir}/2026-08-16-log-c11-finance-review-v3.md`, [
  '# LOG-C11 Finance Review Browser Evidence', '', `Runtime: ${baseUrl}`, '',
  '## Action Ledger', '| Action | Expected | Actual | Verdict |', '|---|---|---|---|',
  ...evidence.actions.map((row) => `| ${row.action} | ${row.expected} | ${row.actual} | ${row.verdict} |`),
  '', '## Screenshots', ...evidence.screenshots.map((path) => `- ${path}`),
  '', '## Critique input', ...evidence.findings.map((finding) => `- ${JSON.stringify(finding)}`),
].join('\n'), 'utf8');
socket.close();
