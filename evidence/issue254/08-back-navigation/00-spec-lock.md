# 00 — SPEC LOCK · LOGI-255-RETURN-TO-LIST-20261102

- **TASK_ID** `LOGI-255-RETURN-TO-LIST-20261102`
- **REPO** `7roger89-web/logistics-work-desk-arena`
- **PR** #255 (updated only — no new PR)
- **SPEC_REF** Issue #254 (existing issue; **no new issue opened**)
- **EXPECTED_HEAD (pre-fix)** `6934f4b1973aa51d60ddb7936d69651cd58d1590`
- **ROLE** IMPLEMENTER · MODE CONTINUE_EXISTING_PR
- **Evidence dir** `evidence/issue254/08-back-navigation/`

## Owner outcome

An operator filters `/lo-hang`, opens one lot on the **Tài chính** tab, and must be
able to return to the **same list with the same filters**.

## WRONG_PASS (written before any code changed)

Explicit failure this task must not accept as done:

> Set `q` + `status` + `period` + `from/to` + `archive` on `/lo-hang`, open a lot's
> debt cluster (`/lo-hang/<id>?tab=tai-chinh`), then try to return. The list comes
> back with **every filter discarded** (and, in this seed, **0 rows**), or the
> operator cannot return at all.

Measured on the pristine head → `results/return-nav-baseline-{A,B,C,D,E}.json`
(all FAIL, see `01-wrong-pass-baseline.md`).

## Two independent behaviours (never conflated)

| Behaviour | What it is | How it is measured |
| --- | --- | --- |
| `IN_APP_RETURN` | the React control **“Về danh sách lô”** on the detail screen | probe tests A/B/D/E, real Chromium |
| `NATIVE_BROWSER_BACK` | Chrome's own Back button | probe test C, real Chromium, separate browser context |

Discriminating rule: **clicking the in-app control is not, and is never reported
as, fixing Chrome Back.**

## Scope locks honoured

- Router state / history only — **no new filter store**, no sessionStorage.
- MemoryRouter **kept**; the app was **not** migrated to `BrowserRouter`.
- `tab=tai-chinh`, finance data, `nextAction` and RBAC paths unchanged.
- No changes to RBAC, finance, DB or Cloud code; no merge; no deploy.
- Only the following UI/test files touched: `component/src/lib/listReturn.ts` (new),
  `component/src/pages/Shipments.tsx`, `component/src/pages/ShipmentDetail.tsx`,
  `component/src/components/ShipmentFinanceSummary.tsx`,
  `tests/component/dom_acceptance_issue255_return_to_list.mjs` (new),
  `tests/test_logi255_return_to_list.py` (new), `component/dist/logi-shell.js` (build output).
