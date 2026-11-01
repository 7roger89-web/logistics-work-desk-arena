import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const puppeteer = require(process.env.PUPPETEER_CORE_PATH || "puppeteer-core");
const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i < 0 ? fallback : process.argv[i + 1];
};
const URL_ = arg("url", "http://127.0.0.1:9501/");
const CHROME = arg("chrome", process.env.CHROME_PATH || "/tmp/chromium");
import { mkdirSync, writeFileSync } from "node:fs";
const out = arg("out", "/tmp/g15-isolated-results");
mkdirSync(out, { recursive: true });
const checks = [];
function assert(name, condition, detail = "") {
  checks.push({ name, pass: !!condition, detail });
  console.log((condition ? "PASS " : "FAIL ") + name + " " + detail);
  if (!condition) throw Error(name);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--single-process"],
});
const p = await browser.newPage();
await p.setViewport({ width: 1440, height: 900 });
const shadowText = () =>
  p.evaluate(
    () =>
      document.querySelector('[data-testid="stBidiComponentIsolated"]')
        ?.shadowRoot?.innerText ||
      document.querySelector('[data-testid="stBidiComponentIsolated"]')
        ?.shadowRoot?.textContent ||
      "",
  );
const shadowClick = (sel) =>
  p.evaluate((s) => {
    const el = document
      .querySelector('[data-testid="stBidiComponentIsolated"]')
      ?.shadowRoot?.querySelector(s);
    if (!el) throw Error("missing " + s);
    el.click();
  }, sel);
try {
  await p.goto(URL_, { waitUntil: "networkidle2" });
  await p.waitForSelector("details");
  await (await p.$$("details"))[1].$("summary").then((e) => e.click());
  await sleep(1200);
  assert(
    "admin chosen lot",
    await p.$eval('input[aria-label="Lô hàng"]', (e) => e.value === "QA-LOT"),
  );
  for (const label of [
    "Mốc tiến độ được duyệt",
    "Chứng từ được duyệt (chỉ metadata, không tải tệp)",
  ]) {
    await p.click(`input[aria-label="${label}"]`);
    await p.waitForSelector(
      `[role="listbox"][aria-label="${label}"] [role="option"]`,
    );
    console.log(
      "options",
      await p.$$eval(
        `[role="listbox"][aria-label="${label}"] [role="option"]`,
        (es) => es.map((e) => e.innerText),
      ),
    );
    await p.click(`[role="listbox"][aria-label="${label}"] [role="option"]`);
    await sleep(1200);
    await p.keyboard.press("Escape");
    await sleep(300);
  }
  assert(
    "cannot submit before confirm",
    await p.$$eval(
      "button",
      (bs) =>
        bs.find((b) => b.textContent.includes("Duyệt và công bố phiên bản mới"))
          ?.disabled === true,
    ),
  );
  const oldVersion =
    (await p.$eval("body", (e) => e.innerText)).match(
      /Bản đang công bố: (g15-[a-f0-9]+)/,
    )?.[1] || "";
  await p.click('[data-testid="stCheckbox"] label');
  await sleep(600);
  let btn = await p.$$('button[data-testid="stBaseButton-primary"]');
  for (const b of btn) {
    if (
      (await p.evaluate((e) => e.textContent, b)).includes("Duyệt và công bố")
    ) {
      assert(
        "confirm enables publish",
        !(await p.evaluate((e) => e.disabled, b)),
      );
      await b.click();
      break;
    }
  }
  await p.waitForFunction(
    (old) => {
      const m = document.body.innerText.match(
        /Bản đang công bố: (g15-[a-f0-9]+)/,
      );
      return m && m[1] !== old;
    },
    { timeout: 15000 },
    oldVersion,
  );
  let before = await p.$eval("body", (e) => e.innerText);
  let version = before.match(/Bản đang công bố: (g15-[a-f0-9]+)/)?.[1];
  assert("release pointer read back", !!version, version);
  await p.screenshot({ path: out + "/admin-published.png", fullPage: true });
  await p.reload({ waitUntil: "networkidle2" });
  await sleep(1300);
  const summaries = await p.$$("details");
  await summaries[1].$("summary").then((e) => e.click());
  await p.waitForFunction(
    (v) => document.body.innerText.includes(v),
    { timeout: 10000 },
    version,
  );
  assert("same pointer after browser reload", true, version);
  await p.$eval('input[type="radio"][value="1"]', (e) =>
    e.closest("label").click(),
  );
  await p.waitForSelector('[data-testid="stBidiComponentIsolated"]', {
    timeout: 20000,
  });
  await sleep(1200);
  let text = await shadowText();
  assert("LG dashboard approved lot", text.includes("QA-LOT"));
  assert(
    "foreign or secrets absent from customer component",
    ![
      "QA-FOREIGN",
      "SECRET_INTERNAL",
      "SECRET_EVENT",
      "SECRET_GRIDFS",
      "SECRET_PRIVATE_DOC",
      "987654321",
    ].some((x) => text.includes(x)),
  );
  await shadowClick('[data-testid="btn-open-journey-QA-LOT"]');
  await sleep(500);
  text = await shadowText();
  assert("approved event visible in Journey", text.includes("QA Đã lấy hàng"));
  await p.screenshot({ path: out + "/customer-journey.png", fullPage: true });
  await shadowClick("#btn-global-docs");
  await sleep(500);
  text = await shadowText();
  assert(
    "approved doc version visible",
    text.includes("QA Packing list") &&
      text.includes("QA-DOC") &&
      text.includes("v2"),
  );
  assert(
    "private and foreign information absent",
    ![
      "SECRET_INTERNAL",
      "SECRET_EVENT",
      "SECRET_GRIDFS",
      "SECRET_PRIVATE_DOC",
      "SECRET_FOREIGN_EVENT",
      "987654321",
      "QA-FOREIGN",
    ].some((x) => text.includes(x)),
  );
  await p.screenshot({ path: out + "/customer-document.png", fullPage: true });
  await p.$eval('input[type="radio"][value="2"]', (e) =>
    e.closest("label").click(),
  );
  await p.waitForFunction(
    () => document.body.innerText.includes("Khách khác QA"),
    { timeout: 10000 },
  );
  await sleep(1000);
  text = await shadowText();
  await p.screenshot({
    path: out + "/cross-tenant-stale-modal.png",
    fullPage: true,
  });
  console.log(
    "modal visibility",
    await p.evaluate(() => {
      let root = document.querySelector(
        '[data-testid="stBidiComponentIsolated"]',
      )?.shadowRoot;
      let el = root?.querySelector("#journey-modal-layer");
      return {
        hidden: el?.classList.contains("hidden"),
        display: el ? getComputedStyle(el).display : null,
      };
    }),
  );
  assert(
    "other customer cannot see LG lot",
    !text.includes("QA-LOT") &&
      !text.includes("QA Đã lấy hàng") &&
      !text.includes("QA Packing list"),
  );
  await p.$eval('input[type="radio"][value="3"]', (e) =>
    e.closest("label").click(),
  );
  await sleep(1000);
  const body = await p.$eval("body", (e) => e.innerText);
  assert(
    "viewer has no publication control",
    !body.includes("duyệt và công bố tiến độ/chứng từ"),
  );
} catch (e) {
  console.error(e.stack);
  process.exitCode = 1;
} finally {
  writeFileSync(
    out + "/results.json",
    JSON.stringify(
      {
        url: URL_,
        environment:
          "disposable mongomock; synthetic identities; real Streamlit components; no Google OAuth",
        checks,
      },
      null,
      2,
    ),
  );
  await browser.close();
}
