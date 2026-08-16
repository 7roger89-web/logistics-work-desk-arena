/**
 * Reusable visible-browser flow for LOG-C04 A Bò / SALE Thành.
 *
 * The flow only changes Streamlit navigation, search text, expanders, and
 * period/report comparison inputs. It never submits a financial action.
 * Live data is not seeded by this flow; the 62464 golden case is asserted by
 * the pure fixture suite and reported here only when it exists in the live
 * canonical projection.
 */
export async function runPartnerReconciliationDeskFlow(tab, options = {}) {
  const {
    searchTerm = "62464",
    reportedAmount = "",
    waitMs = 2500,
    selectorTimeoutMs = 30000,
  } = options;
  const wait = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds));

  await tab.reload();
  await wait(waitMs * 2);

  const deskNav = tab.playwright
    .getByRole("radio", { name: /Công nợ A Bò/i })
    .first();
  await deskNav.waitFor({ state: "visible", timeoutMs: selectorTimeoutMs });
  await deskNav.click();
  await wait(waitMs * 2);

  const snapshotInitial = String(await tab.playwright.domSnapshot());
  const titleVisible = snapshotInitial.includes("Công nợ A Bò");
  const ownerFilterVisible = snapshotInitial.includes("SALE Thành");
  const ownerCoverageStateVisible =
    snapshotInitial.includes("internal_sale_owner") ||
    snapshotInitial.includes("Chưa có dòng canonical nào được gắn SALE Thành");
  const readOnlyCopyVisible = snapshotInitial.includes("chỉ đọc") && snapshotInitial.includes("không có sổ Thành riêng");
  const honestUnavailableState =
    snapshotInitial.includes("Chưa đọc được canonical ledger") ||
    snapshotInitial.includes("Chưa có canonical ledger record phù hợp");

  if (!titleVisible) {
    throw new Error("LOG-C04 desk title did not become visible after route navigation");
  }

  const result = {
    url: await tab.url(),
    routeReachable: true,
    titleVisible,
    ownerFilterVisible,
    ownerCoverageStateVisible,
    readOnlyCopyVisible,
    honestUnavailableState,
    searchTerm,
    liveFixtureSearchVisible: false,
    liveFixtureSearchAbsentTruthful: false,
    traceVisible: false,
    periodDraftVisible: false,
    reportedComparisonVisible: false,
    readOnly: true,
  };

  const searchBox = tab.playwright
    .getByRole("textbox", { name: /Mã shipment, số tiền/i })
    .first();
  if (await searchBox.count() && await searchBox.isVisible()) {
    await searchBox.fill(searchTerm);
    await searchBox.press("Enter");
    await wait(waitMs);
    const snapshotAfterSearch = String(await tab.playwright.domSnapshot());
    result.liveFixtureSearchVisible =
      snapshotAfterSearch.includes("Tìm thấy") && snapshotAfterSearch.includes(searchTerm);
    result.liveFixtureSearchAbsentTruthful =
      !result.liveFixtureSearchVisible && snapshotAfterSearch.includes("Không thấy dòng nào chứa");
    const traceSelect = tab.playwright.getByRole("combobox", { name: /Dòng cần lần theo/i }).first();
    if (await traceSelect.count() && await traceSelect.isVisible()) {
      await traceSelect.click();
      await wait(Math.min(waitMs, 800));
      await tab.playwright.getByRole("option").first().click();
      await wait(waitMs);
      const snapshotAfterTrace = String(await tab.playwright.domSnapshot());
      result.traceVisible = snapshotAfterTrace.includes("Nguồn và chứng từ của dòng này");
    }
  }

  const periodInputs = tab.playwright.getByPlaceholder("YYYY/MM/DD");
  result.periodDraftVisible = (await periodInputs.count()) >= 2;

  if (reportedAmount && result.periodDraftVisible) {
    const reportedInput = tab.playwright
      .getByRole("textbox", { name: /A Bò báo lại/i })
      .first();
    if (await reportedInput.count() && await reportedInput.isVisible()) {
      await reportedInput.fill(String(reportedAmount));
      await wait(waitMs);
      const snapshotAfterReported = String(await tab.playwright.domSnapshot());
      result.reportedComparisonVisible = snapshotAfterReported.includes("Nếu A Bò báo một số khác");
    }
  }

  return result;
}
