# 09 — RETURN STATE PRESERVATION (`LOGI-255-RETURN-STATE-PRESERVATION-20261102`)

SPEC_REF: Issue #254 · PR #255 · EXPECTED_HEAD under test: `cb1870f95358be3b9e8c6278ac898fc1c9fa2cba`
Question: does the `/lo-hang` filter set survive **open detail (Công nợ dịch vụ cluster →
tab `tai-chinh`) → switch tab inside the detail (a real `setSp(...)` navigation) →
"Về danh sách lô"**?

## 0. Law preflight

`P2P_LAW_SOURCE=LOCAL_PORTABLE` — `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` carries
`P2P_PORTABLE_LAW_PROJECTION=YES` with canonical provenance; no cross-repo probe was
issued to manufacture a 404. `AGENTS.md` + `docs/NEXT.md` at exact HEAD were read.

## 1. ROOT_CAUSE: **PROVEN**

Hypothesis confirmed at source AND at runtime:

- `ShipmentDetail.tsx` reads the remembered list location from
  `useLocation().state` (`listReturnFromState(locationState)` → the back control's
  `to`/`data-return-to`).
- React Router 7.18.3 `useSearchParams().setSearchParams(next, opts)` is implemented as
  `navigate("?" + next, opts)` (verified in `node_modules/react-router/dist/development/chunk-YRTY65LJ.js:733-743`).
  All 23 `setSp({...})` call sites in `ShipmentDetail.tsx` pass **no** NavigateOptions,
  so the new location's `state` becomes `null` on every tab switch.
- `listReturnFromState(null)` → safe fallback `"/lo-hang"` → every filter lost.

### FAIL-before (real Chromium 153.0.8010.0, isolated mongomock QA DB `logistics_staging`,
Support actor `qa.s255.support`, exact HEAD `cb1870f`, app on `127.0.0.1:9531`)
`results/fail-before-cb1870f.json`, screenshots `shots/09-*-fail-before.png`:

1. `/lo-hang` filtered with ALL six controls: `q=LO-03`, `status=Chờ thông quan`,
   `period=khac`, `from=2020-01-01`, `to=2030-12-31`, `archive=tat-ca` →
   visible rows `[LO-0306, LO-0307, LO-0308]`.
2. Clicked the **Công nợ dịch vụ** cluster of `LO-0308` → detail opened on tab
   **Tài chính** (`pressedTabOnOpen: "Tài chính"`); back control carried the full
   remembered URL:
   `data-return-to = /lo-hang?status=Ch%E1%BB%9D+th%C3%B4ng+quan&period=khac&from=2020-01-01&to=2030-12-31&archive=tat-ca&q=LO-03`
3. Switched tab via the Global Workspace control → `setSp({tab:"lich-su"})` fired
   (`pressedTabAfterSwitch: "Lịch sử"`) — a genuine setSearchParams navigation.
4. **After the switch**: `data-return-to` collapsed to `/lo-hang` (location.state wiped).
5. Clicked **"Về danh sách lô"** → landed on the plain list: `q=''`, status cleared,
   `period=Tháng này`, `from/to=null`, `archive=Đang làm`, rows `[]`.

| Test | cb1870f (before) |
| --- | --- |
| A open → return immediately | PASS |
| **B open → tab switch (setSp) → return** | **FAIL** (all filters + rows lost) |
| C direct entry → safe `/lo-hang` fallback | PASS |
| D 1440x900 + 390x844 control visible, no page overflow | PASS |
| E native browser Back | FAIL — MemoryRouter, reported separately, never substitutes B |

## 2. Fix (minimal — source diff: `02-source-diff.patch`)

`component/src/pages/ShipmentDetail.tsx` only: wrap the single `setSp` binding so every
in-detail search-param write keeps the current `location.state` via the existing
NavigateOptions mechanism:

```ts
const [sp, setSpRaw] = useSearchParams();
const setSp: typeof setSpRaw = useCallback(
  (next, opts) => setSpRaw(next, { ...opts, state: locationState }),
  [setSpRaw, locationState]
);
```

- MemoryRouter kept; `listReturn.ts` unchanged; no sessionStorage/global store;
  no RBAC/finance/route-schema change; `/lo-hang` fallback for direct entry kept.
- All 23 existing `setSp(...)` call sites use the wrapped binding unchanged.
- `component/dist/logi-shell.js` rebuilt (`npm run build`).

### OE_GATE — "Không bị over engineering chứ?" → `OE_VERDICT=DO_IT`
SIMPLER_PATH: alternatives (sessionStorage, global store, BrowserRouter migration,
`nav(-1)`) are all larger or forbidden; MemoryRouter keeps a history stack but
`setSp` pushes, so `nav(-1)` would land on the previous detail tab, not the list —
NavigateOptions `state` is the smallest correct mechanism and the one the task
prescribes. MATERIAL_PROGRESS: fixes a measured FAIL, not a hypothetical.
NECESSITY: acceptance B requires it. CORE_BEFORE_SUPPORT: only the core detail
navigation path changed. SMALLER_VERIFIABLE_SLICE: one wrapped binding + one DOM
lane + one Chromium probe.

## 3. PASS-after (same Chromium 153, same QA DB, fixed bundle served on `127.0.0.1:9532`)
`results/pass-after-fix.json`, screenshots `shots/09-*-pass-after.png`:

- After the tab switch, `data-return-to` is **byte-identical** to before the switch
  (full filtered URL). After "Về danh sách lô": `q=LO-03`, `status=Chờ thông quan`,
  `period=khac`, `from=2020-01-01`, `to=2030-12-31`, `archive=tat-ca`,
  rows `[LO-0306, LO-0307, LO-0308]` — all identical to before opening the lot.

| Test | after fix |
| --- | --- |
| A | PASS |
| **B (with real setSp tab switch before return)** | **PASS** |
| C direct entry | PASS (`data-return-to="/lo-hang"`, safe landing) |
| D desktop 1440x900 + mobile 390x844 | PASS (control visible, no page-level horizontal overflow) |
| E native browser Back | FAIL — unchanged MemoryRouter behaviour, reported separately only |

## 4. Automated lanes (exact final tree)

| Lane | Command | Result |
| --- | --- | --- |
| Typecheck | `cd component && npm run typecheck` | exit 0 (`logs/build-typecheck.txt`) |
| Build | `cd component && npm run build` | exit 0, `dist/logi-shell.js` rebuilt (`logs/build-typecheck.txt`) |
| New DOM lane (shipped bundle) | `pytest tests/test_logi255_return_state_preservation.py` | **1 passed** (`logs/focused-pytest.txt`) |
| Same lane on PRE-FIX bundle (`R255_DOM_ROOT` = pristine `cb1870f` worktree) | same | **1 failed** at `a tab switch (setSp) must not wipe location.state: before=/lo-hang?period=tat-ca&q=LO-0299 after=/lo-hang` (`logs/dom-lane-on-prefix-bundle.txt`) — the lane discriminates |
| Issue #254 + LOGI-255 + navigation/route regressions | `pytest tests/test_logi255_return_state_preservation.py tests/test_logi255_return_to_list.py tests/test_issue254_shipment_debt_glance.py tests/test_phase_a_component.py tests/test_logi_shipment_primary_action_unify_01.py tests/test_logi_scope_aware_missing_info_01.py tests/test_contract_route_contract.py tests/test_shipment_slash_route_repair_01.py tests/test_logi_uat_real_use_repair_02.py -q` | **102 passed** (`logs/focused-pytest.txt`) |
| Full suite BEFORE (exact HEAD `cb1870f`) | `python -m pytest tests -q --continue-on-collection-errors` | **2386 passed, 44 skipped, 0 failed/0 error** (`logs/full-pytest-baseline-cb1870f.txt`) |
| Full suite AFTER (final tree) | same | see `logs/full-pytest-after-fix.txt` — **2387 passed, 44 skipped, 0 failed/0 error** (exactly +1 = the new test; skip count unchanged 44=44, no xfail added, no test removed) |

## 5. Repro commands

```bash
# isolated QA DB (mongomock staging, refuses real MONGO_URI), Support actor seeded
S255_EVIDENCE_DIR=... S255_TEST_PASSWORD=... AUTH_REQUIRED=true \
  python -m streamlit run evidence/issue254/09-return-state/probe/runtime_09.py \
  --server.port 9531 --server.headless true --server.address 0.0.0.0

# real Chromium 153 probe (A/B/C/D/E as above)
S255_TEST_PASSWORD=... python evidence/issue254/09-return-state/probe/probe_09_return_state.py \
  --base http://127.0.0.1:9531/ --out evidence/issue254/09-return-state/results/fail-before-cb1870f.json --tag fail-before
```

## 6. Files

- `probe/runtime_09.py` — test-only runtime wrapper (mongomock staging + `qa.s255.support`).
- `probe/probe_09_return_state.py` — Playwright/Chromium probe (tests A–E).
- `results/fail-before-cb1870f.json`, `results/pass-after-fix.json`, `results/seed-truth.json` — raw results (router state before/after the tab switch, filter state, row IDs, control rects).
- `shots/` — screenshots before/after for both runs, desktop + mobile.
- `logs/` — typecheck/build, focused pytest, DOM lane on pre-fix bundle, full suite before/after.
- `02-source-diff.patch` — the minimal source change.
