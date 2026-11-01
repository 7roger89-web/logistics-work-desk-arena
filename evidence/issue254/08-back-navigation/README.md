# 08 — RETURN TO LIST (`LOGI-255-RETURN-TO-LIST-20261102`)

Spec: `00-spec-lock.md` · WRONG_PASS baseline: `01-wrong-pass-baseline.md` ·
Source diff: `02-source-diff.patch`.

## 1. Chosen fix (smallest change that keeps the existing router)

The shell runs a `MemoryRouter`, so there is no browser history to lean on, and the
list's filters live in its own search params. The fix therefore carries the list's
**own location** through **router state** and adds **one** explicit control on the
detail screen.

| File | Change |
| --- | --- |
| `component/src/lib/listReturn.ts` **(new)** | `listReturnTarget(pathname, search)` (only a real list location is remembered, anything else → `/lo-hang`), `isListLocation`, `listReturnFromState(state)` (validated, else `/lo-hang`), `listReturnState(listReturn)`. |
| `component/src/pages/Shipments.tsx` | reads its own `useLocation()` → `listReturn` = `pathname + search` (q/status/period/from/to/archive); attaches `state={detailState}` to the lot link, `XỬ LÝ`, `XEM 360°`, and passes `listReturn` to both finance-cluster variants. |
| `component/src/components/ShipmentFinanceSummary.tsx` | optional `listReturn` prop → the cluster `Link` carries the router state. Non-list callers (Receivables, PartnerPayables, …) pass nothing and are unchanged. |
| `component/src/pages/ShipmentDetail.tsx` | reads `location.state`, renders row `shipment-back-row` under the identity bar with `Link data-testid="shipment-back-to-list" data-return-to=…` labelled **“Về danh sách lô”** (+ hint “giữ nguyên bộ lọc đang xem” only when it really came from the list). |
| `component/dist/logi-shell.js` | rebuilt bundle (`npm run build`). |

No new store, no sessionStorage, no `BrowserRouter` migration, no change to
`tab=tai-chinh`, finance figures, `nextAction` or RBAC.

## 2. Automated lanes

| Lane | Command | Result |
| --- | --- | --- |
| Typecheck | `npm run typecheck` | **exit 0** (`logs/build-typecheck.txt`) |
| Build | `npm run build` | **exit 0**, `dist/logi-shell.js` 1,594.70 kB (`logs/build-typecheck.txt`) |
| New DOM acceptance (shipped bundle) | `pytest tests/test_logi255_return_to_list.py` | **1 passed** (`logs/focused-pytest.txt`) |
| Issue #254 regression (incl. its own DOM lane) | `pytest tests/test_issue254_shipment_debt_glance.py` | **7 passed** |
| Focused + new together | `pytest tests/test_issue254_shipment_debt_glance.py tests/test_logi255_return_to_list.py` | **8 passed** |
| Navigation/route regressions | `pytest tests/test_phase_a_component.py tests/test_logi_shipment_primary_action_unify_01.py tests/test_logi_scope_aware_missing_info_01.py tests/test_contract_route_contract.py` | **59 passed** |
| Slash-route + real-use regressions | `pytest tests/test_shipment_slash_route_repair_01.py tests/test_logi_uat_real_use_repair_02.py` | **34 passed** |
| Full suite (fixed tree) | `pytest tests -q -rs` | **2386 passed, 44 skipped, 10 subtests passed** (`logs/full-pytest-fixed.log`) |
| Full suite (pristine `6934f4b1`) | same | **2385 passed, 44 skipped, 10 subtests passed** (`logs/full-pytest-baseline.log`) |

`+1 passed` is exactly the new test. **Skipped count unchanged (44 = 44), 0 xfail in
both logs, 0 failures in both.**

### The new DOM lane discriminates

`tests/component/dom_acceptance_issue255_return_to_list.mjs` mounts the **shipped**
`component/dist/logi-shell.js` in jsdom and drives the real React tree with a live
view-model payload. Run against the pre-fix bundle it fails at the right place:

```
R255_DOM_ROOT=/home/user/pr255 pytest tests/test_logi255_return_to_list.py
→ AssertionError: Timed out waiting for: "Về danh sách lô" control present   (logs/dom-lane-on-prefix-bundle.txt)
```

Against the fixed bundle it passes end-to-end: q filter → cluster → return keeps
`q` and the identical row set; combined `status + period(khác, from/to) + archive`
→ return keeps all five params (`href`/`data-return-to` =
`/lo-hang?status=…&period=khac&from=2020-01-01&to=2030-12-31&archive=tat-ca`) and
the identical row set; a direct entry from **Tổng quan** gets
`data-return-to="/lo-hang"` (plain-list fallback, never stale filters).

## 3. Real-browser acceptance (Chromium 153.0.8010.0, Playwright)

App: the fixed tree served by the same Streamlit runtime on `http://127.0.0.1:9521/`.

| Test | Baseline (`6934f4b1`) | After fix | Evidence |
| --- | --- | --- | --- |
| **A** `q="LO-0"` → debt cluster → in-app control → `q` preserved | FAIL | **PASS** | `results/probe-v2-A.json`, `shots/nav-A-1..3-*.png` |
| **B** `status + period(khác) + from/to + archive` → return keeps exact values **and** same visible rows | FAIL | **PASS** | `results/probe-v2-B.json`, `shots/nav-B-1..3-*.png` |
| **C** native Chrome Back | FAIL (`about:blank`) | **FAIL — unchanged** | `results/probe-v2-C.json`, `shots/nav-C-native-back-after.png` |
| **D** entry from another entrypoint (no list history) | FAIL | **PASS** | `results/probe-v2-D.json`, `shots/nav-D-other-entry-after.png` |
| **E** control present at 1440x900 **and** 390x844, no overflow | FAIL | **PASS** | `results/probe-v2-E.json`, `shots/nav-E-desktop-after.png`, `nav-E-mobile-after.png` |

Key numbers:

- A: control `href` = `data-return-to` = `/lo-hang?period=tat-ca&archive=tat-ca&q=LO-0`;
  after return `q="LO-0"` and rows `[LO-0299, LO-0306, LO-0307, LO-0308, LO-0295]`
  identical before/after, summary still `Tìm thấy 5 lô`.
- B: remembered location
  `/lo-hang?status=Ch%E1%BB%9D+th%C3%B4ng+quan&period=khac&from=2020-01-01&to=2030-12-31&archive=tat-ca`;
  after return all params identical and rows identical (`LO-0306, LO-0307, LO-0308,
  LO-R255-QUOTE, LO-R255-USD`, `Tìm thấy 5 lô`).
- D: `href="/lo-hang"`, `landedOnBlank=false`, list rendered, and the returned state
  is **byte-identical to a fresh `/lo-hang`** (`sameAsFreshList=true`) — the default
  period chip `Tháng này` legitimately shows `0 lô` in this seed, which is why the
  probe compares against a fresh list instead of demanding rows.
- E: desktop control `176x44 @ (97, 201)`; mobile `176x44 @ (28, 283)`, both fully
  inside the viewport, `docOverflowPx=0`, `rootOverflowPx=0`.
- **C (native Back) is still FAIL and is reported as such**: `history_before=2`,
  `history_on_detail=2`, `url_after_back="about:blank"`, `shellPresent=false`. The
  in-app control does **not** fix Chrome Back; making Chrome Back work would require
  the `BrowserRouter` migration this task explicitly excludes.

## 4. Probe plumbing notes (why numbers moved between baseline and after runs)

The acceptance probe measures the app, so three harness-only defects were fixed
while measuring — all documented in `probe/probe_return_nav.py`:

1. **`q` was typed key-by-key** and dropped characters under Streamlit re-renders
   (`"LO-0"` arrived as `"L-0"`, `0 rows`, `detailOpened=false`). Now `fill` + poll
   until the live input actually holds the value (fails loudly otherwise).
2. **D** demanded rows after the fallback, but the seed's default list filter
   (`Tháng này`) is empty for every lot; D now compares against a **fresh `/lo-hang`**
   reference captured in the same run.
3. **E mobile** clicked `Tất cả thời gian` *before* opening the drawer; the drawer
   link re-mounts the list with default filters, so the click was lost and there was
   no card to open. It now re-applies the period after drawer navigation and polls
   for a rendered cluster.

Screenshots are taken with the control scrolled into view (`focus_control`), so the
images show the control rather than a random part of the page.
