/**
 * Read-only Browser flow for the LOG-C02 Finance partner projection.
 *
 * The function accepts a Codex in-app Browser tab, opens the existing Finance
 * surface, verifies the A Bò / Sale Thành projection defaults and its explicit
 * UNKNOWN/RESTRICTED rule, and never submits a business-data control.
 */
export async function runFinanceProjectionFlow(tab, options = {}) {
  const { waitMs = 3000, selectorTimeoutMs = 30000 } = options;
  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs * 3);

  const financeNav = tab.playwright.getByRole("radio", {
    name: "💰 Thu Tiền & Công Nợ",
    exact: true,
  });
  await financeNav.waitFor({ state: "visible", timeoutMs: selectorTimeoutMs });
  await financeNav.click();
  await wait(waitMs * 2);

  let inputValues = [];
  const deadline = Date.now() + selectorTimeoutMs;
  while (Date.now() < deadline) {
    inputValues = await tab.playwright.evaluate(() =>
      Array.from(document.querySelectorAll("input"))
        .filter((element) => element.getAttribute("aria-label"))
        .map((element) => ({
          label: element.getAttribute("aria-label"),
          value: element.value,
        })),
    );
    const labels = new Set(inputValues.map((item) => item.label));
    if (
      labels.has("Mã đối tác") &&
      labels.has("Tên hiển thị") &&
      labels.has("Sale nội bộ")
    ) {
      break;
    }
    await wait(500);
  }

  const inputByLabel = Object.fromEntries(
    inputValues.map((item) => [item.label, item.value]),
  );
  const snapshot = String(await tab.playwright.domSnapshot());
  const partnerCode = inputByLabel["Mã đối tác"];
  const partnerName = inputByLabel["Tên hiển thị"];
  const saleOwner = inputByLabel["Sale nội bộ"];

  return {
    url: await tab.url(),
    financeSurfaceVisible: snapshot.includes("💰 THU TIỀN & PHÂN BỔ CÔNG NỢ"),
    projectionHeadingVisible: snapshot.includes(
      "A Bò — Sale Thành · Đối soát tài chính đọc-only",
    ),
    canonicalSourceVisible: snapshot.includes(
      "Projection chỉ đọc từ canonical ledger",
    ),
    partnerCode,
    partnerName,
    saleOwner,
    unknownRestrictedRuleVisible: snapshot.includes(
      "UNKNOWN/RESTRICTED không được cộng vào vị trí đã xác nhận.",
    ),
    emptyProjectionHandled: snapshot.includes(
      "Chưa có canonical ledger record phù hợp với đối tác/sale đang chọn.",
    ),
    b2SaveControlAbsent:
      !snapshot.includes("Lưu vị trí đối tác") &&
      !snapshot.includes("Xác nhận vị trí đối tác"),
    legacyReceiptWritePathUntouched: snapshot.includes(
      "Xác nhận ghi khoản thu",
    ),
    readOnly: true,
  };
}
