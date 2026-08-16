/**
 * Reusable visible-browser flow for LOG-C05 manager report and Debit Draft.
 *
 * The flow navigates the existing A Bò desk, opens both read-only modes,
 * checks the deterministic explanation labels, returns to the desk, and
 * returns to Dashboard. It never seeds fixtures and never clicks a snapshot
 * or financial action.
 */
export async function runManagerReportDebitFlow(tab, options = {}) {
  const {
    waitMs = 2500,
    selectorTimeoutMs = 30000,
    captureCheckpoint = async () => {},
  } = options;
  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs * 2);

  let deskNav = tab.playwright
    .getByRole("radio", { name: /Công nợ A Bò/i })
    .first();
  if (!(await deskNav.count())) {
    deskNav = tab.playwright.getByText(/Công nợ A Bò/i).first();
  }
  let deskNavReady = false;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (await deskNav.count() && await deskNav.isVisible()) {
      deskNavReady = true;
      break;
    }
    await wait(1000);
  }
  if (!deskNavReady) {
    await deskNav.waitFor({ state: "visible", timeoutMs: selectorTimeoutMs });
  }
  await deskNav.click();
  await wait(waitMs * 2);

  const deskSnapshot = String(await tab.playwright.domSnapshot());
  await captureCheckpoint("desk");
  const result = {
    url: await tab.url(),
    routeReachable: true,
    deskTitleVisible: deskSnapshot.includes("Công nợ A Bò"),
    reportActionVisible: false,
    debitActionVisible: false,
    reportTitleVisible: false,
    reportExplanationVisible: false,
    reportShipmentSectionVisible: false,
    reportTruthfulEmptyState: false,
    debitTitleVisible: false,
    debitFormulaVisible: false,
    debitIncludedSectionVisible: false,
    debitExcludedSectionVisible: false,
    debitTruthfulEmptyState: false,
    snapshotButtonDisabledOrAbsent: false,
    returnedToDesk: false,
    returnedToDashboard: false,
    readOnly: true,
  };

  const reportButton = tab.playwright
    .getByRole("button", { name: "Báo cáo Sếp", exact: true })
    .first();
  result.reportActionVisible = (await reportButton.count()) > 0 && await reportButton.isVisible();
  if (result.reportActionVisible) {
    await reportButton.click();
    await wait(waitMs);
    const reportSnapshot = String(await tab.playwright.domSnapshot());
    await captureCheckpoint("report");
    result.reportTitleVisible = reportSnapshot.includes("BÁO CÁO CÔNG NỢ A BÒ");
    result.reportExplanationVisible = reportSnapshot.includes("DIỄN GIẢI SỐ LIỆU");
    result.reportShipmentSectionVisible = reportSnapshot.includes("Shipment quan trọng");
    result.reportTruthfulEmptyState =
      reportSnapshot.includes("Chưa có dữ liệu canonical đủ điều kiện") ||
      reportSnapshot.includes("Chưa đọc được canonical ledger");
    const backFromReport = tab.playwright
      .getByRole("button", { name: "← Quay lại bàn đối soát", exact: true })
      .first();
    if (await backFromReport.count() && await backFromReport.isVisible()) {
      await backFromReport.click();
      await wait(waitMs);
    }
  }

  const debitButton = tab.playwright
    .getByRole("button", { name: "Debit Draft", exact: true })
    .first();
  result.debitActionVisible = (await debitButton.count()) > 0 && await debitButton.isVisible();
  if (result.debitActionVisible) {
    await debitButton.click();
    await wait(waitMs);
    const debitSnapshot = String(await tab.playwright.domSnapshot());
    await captureCheckpoint("debit");
    result.debitTitleVisible = debitSnapshot.includes("DEBIT DRAFT");
    result.debitFormulaVisible = debitSnapshot.includes("Vì sao debit ra số này?");
    result.debitIncludedSectionVisible = debitSnapshot.includes("Dòng được cộng vào Debit");
    result.debitExcludedSectionVisible = debitSnapshot.includes("Dòng bị loại khỏi Debit");
    result.debitTruthfulEmptyState =
      debitSnapshot.includes("Chưa có dữ liệu canonical đủ điều kiện") ||
      debitSnapshot.includes("Chưa có số debit đủ điều kiện") ||
      debitSnapshot.includes("Chưa đọc được canonical ledger");
    const snapshotButton = tab.playwright
      .getByRole("button", { name: "Lưu READY_FOR_REVIEW snapshot", exact: true })
      .first();
    result.snapshotButtonDisabledOrAbsent =
      !(await snapshotButton.count()) || !(await snapshotButton.isEnabled());
    const backFromDebit = tab.playwright
      .getByRole("button", { name: "← Quay lại bàn đối soát", exact: true })
      .first();
    if (await backFromDebit.count() && await backFromDebit.isVisible()) {
      await backFromDebit.click();
      await wait(waitMs);
    }
  }

  const afterBack = String(await tab.playwright.domSnapshot());
  result.returnedToDesk = afterBack.includes("Tác vụ LOG-C05") || afterBack.includes("Công nợ A Bò");
  let dashboardNav = tab.playwright
    .getByRole("radio", { name: /Dashboard/i })
    .first();
  if (!(await dashboardNav.count())) {
    dashboardNav = tab.playwright.getByText(/Dashboard/i).first();
  }
  if (await dashboardNav.count() && await dashboardNav.isVisible()) {
    await dashboardNav.click();
    await wait(waitMs);
    const dashboardSnapshot = String(await tab.playwright.domSnapshot());
    await captureCheckpoint("dashboard");
    result.returnedToDashboard = dashboardSnapshot.includes("Dashboard");
  }
  return result;
}
