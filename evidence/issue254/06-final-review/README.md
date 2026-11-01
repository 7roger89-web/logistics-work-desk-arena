# LOGI-255 — FINAL ACCEPTANCE (independent reviewer) · PR #255 · spec ref Issue #254

- Task: `LOGI-255-FINAL-ACCEPTANCE-20261101` · Role: **INDEPENDENT_REVIEWER** (no code change, no merge, no deploy)
- Repo: `7roger89-web/logistics-work-desk-arena` (NOT `logistics-work-desk`)
- `P2P_LAW_SOURCE=LOCAL_PORTABLE` — `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`
  (`P2P_PORTABLE_LAW_PROJECTION=YES`, `CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`,
  `SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`). No cross-repo probe was issued.
- `AGENTS.md` read at HEAD; `docs/NEXT.md` read at HEAD (checkpoint dated 31/10, `CURRENT` = Issue #247/PR #248).
- Review time (UTC): 2026-11-01T15:30Z.

## 1. Measured baseline

| fact | value | evidence |
|---|---|---|
| `gh pr view 255 headRefOid` | `911f3174596245fc8ec4d68daef634fa07032f90` = `EXPECTED_HEAD` | `01-head-and-pr.txt` |
| PR state / base | **OPEN**, base `arena/ae5f9f47-logistics-work-desk-arena`, `MERGEABLE`, `mergeStateStatus=CLEAN` | `01-head-and-pr.txt` |
| required check | `contract-shape` **pass** (`runs/41319902544`) | `01-head-and-pr.txt` |
| Issue #254 | OPEN (not closed by the PR) | `01-head-and-pr.txt` |
| working tree | clean (`git diff --exit-code` = 0, `--cached` = 0, no untracked non-ignored) **before** evidence was added | `01-head-and-pr.txt` |

`git diff --exit-code` on tracked source is still empty after this review: the only additions are files under
`evidence/issue254/06-final-review/` (this note + logs + repro). No product code, test, docs, `ops/` were touched,
nothing was merged, deployed or pushed by the reviewer.

## 2. Acceptance — verdict per line

| # | requirement | verdict | evidence |
|---|---|---|---|
| 1 | Legacy `lastWrites` row (no `_provenance`) must not reach another actor/role | **FAIL (leak reproduced) / runtime reachability not established** | §3, `leaked-*.json` |
| 2a | Server payload boundary for `sale` (no lot finance outside `finance_view`, UNKNOWN != 0) | **PASS (source + payload artifacts)** | §4, `payload-sale.json`, `payload-support.json` |
| 2b | Real browser UAT (desktop 1440×900 + mobile 390×844, Chromium) executed by the reviewer | **UNKNOWN** — no Chromium executable in this container | `04-browser-env.txt` |
| 2c | Browser Back keeps filters / reload parity vs backend / tab Tài chính | **UNKNOWN — not covered by any artifact** | §4 |
| 3 | `costIntelligence.rates` policy for `sale` | **UNKNOWN — Owner decision required** | §5 |
| 4 | Full `python -m pytest tests -q` at exact HEAD, 0 FAILED / 0 ERROR / no new SKIP | **PASS on clean replay** (2375 passed, 44 skipped, 0 failed) + 1 pre-existing wall-clock flake documented | `02-full-suite-run.txt`, `06-flake-analysis.txt` |
| 5 | Focused suites | **PASS** (`test_logi255_lastwrites_actor_isolation` + `_finance_boundary` + `test_issue254_shipment_debt_glance` = 16 passed) | §4 |

## 3. Check 1 — legacy row (the blocker)

`views/logi_view_model.py::_last_writes_for_actor()` deliberately keeps the old behaviour for rows **without**
`_provenance` (`delivered.append(row)`), so a stored outcome written by the previous code version stays readable by
whoever holds the session afterwards. Reproduced deterministically through the real boundary
(`vm.dispatch()` → `LAST_WRITES_KEY` → `vm.build_view_model()`), with the row converted to the pre-fix shape
(no `_provenance`, i.e. exactly what `st.session_state[LAST_WRITES_KEY] = outcomes` wrote before this commit):

- **same account, demoted Support→Sale via the canonical store + `auth.fresh_session_identity_for_action()`**:
  `lastWrites` still contains `cost_rate_save / COST-REVIEW-LEGACY-1` with `readback.rows[0].amount = 4250 USD`,
  `supplier = "Hang tau REVIEW"`, `created_by = qa.review.s255` → `leaked-sale-lastwrites.json`.
  (`payment_record` *is* blocked by the old `finance_view` list — the leak is the sibling money event.)
- **same tab, account A deactivated → account B (both Support) logs in without `logout()`**:
  `LAST_WRITES_KEY` survives (it is only cleared inside `core/auth.py::logout()`), so B receives A's
  `payment_record` outcome: `requestId = PAY-REVIEW-LEGACY-B`, `persisted.amount = 35.000.000`,
  `audit[0].actor = qa.review.s255` → `leaked-support-b-lastwrites.json`.
- Control: a row **with** provenance is correctly dropped for the same Sale session (`lastWrites == []`).

Runtime reachability of the unstamped shape: **not established**. Deploying a new build restarts the Streamlit
process (session_state dies), no in-app writer stores unstamped outcomes, and `scripts/*.py` fixtures are not
runtime. So this is a *fail-open branch + missing test*, not a demonstrated live incident. The PR's own 5 tests
(A–E) never exercise the unstamped branch; the docstring states the compromise explicitly, so it is a conscious
scope decision that contradicts the invariant the commit claims ("chỉ trả cho đúng actor/role đã ghi").

Smallest repair (not done here, reviewer must not change code):
treat a missing/invalid stamp as **not delivered** (fail closed) instead of `delivered.append(row)`, and add one
negative test: write outcome as Support A → strip `_provenance` → demote the same account to Sale / switch to
Support B → `model["lastWrites"] == []`. That test must fail on today's HEAD and pass after the change.

## 4. Check 2 — browser UX

The reviewer container has **no Chromium**: no system browser, no `ms-playwright` cache, `@sparticuz/chromium`
(binary extracted from the allowed npm registry) cannot start because `libnss3/libnssutil3/libnspr4` are absent and
the Debian mirror is unreachable (`apt-get install -s libnss3` → *Unable to locate package*). See `04-browser-env.txt`.
Per the review contract this is `UNKNOWN`, never `PASS`.

Cross-check of the implementer's committed artifacts (`05-browser-artifact-crosscheck.txt`) — consistency only,
**not** an independent execution:
- PNG dimensions match the claim: desktop `1440x900` ×4, mobile `390x844` ×2.
- `payload-support.json` finance block == backend truth `seed-truth.json` (`receivable 66,960,000` /
  `received 0` / `outstanding 66,960,000`; quote-only lot keeps `receivable = null`, `hasActualLines = false`).
- browser claims after recording/reversing a payment match the same arithmetic (35,000,000 → 31,960,000, then back).
- `payload-sale.json`: `finance_view_permission = false`, every lot `canView=false`,
  `source="restricted:finance_view"`, all money fields `null`, `quote` only (contract explicitly allows quote).
- Visually (desktop/mobile screenshots) the cluster reads `Phải thu / Đã thu / Còn phải thu`, no horizontal
  overflow at 390 px, and the Sale screenshots carry no finance cluster.

Not covered by any artifact, therefore `UNKNOWN`: **Browser Back retaining q/status/period/archive**, **reload
parity against the backend**, **opening the lot's `tai-chinh` tab from the list**, and the `q`/`status`/`archive`
filters themselves (`playwright/issue254_browser.mjs` only clicks `shipment-period-tat-ca`).

## 5. Check 3 — cost intelligence policy (`UNKNOWN`, Owner decision)

First-hand probe at this HEAD (`legacy-repro/policy_probe.py`): Support saves a supplier rate, the same account is
demoted to `sale` → `canViewFinance=false`, `lastWrites=[]`, yet

```
sale costIntelligence.rates count = 1
  id= COST-POLICY-1 | created_by= qa.review.policy | supplier= Hang tau POLICY | amounts= [(4250.0, 'USD')]
```

So the same commercial cost that the PR blocks on the `lastWrites` channel is delivered to `sale` on another
channel with no gate (`views/logi_view_model.py` `"costIntelligence"` projection has no permission check), and the
frontend consumes it inside the quoting workflow (`component/src/pages/SalesQuotes.tsx` workspaces
`check-chi-phi` / `kho-gia-von` → `CostCheck`, `CostIntelligencePanel`; route `/kinh-doanh-bao-gia`, permission
`sales`, which `sale` holds).

The repo contains two contradictory precedents, which is why this cannot be decided by a reviewer:
- `docs/LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.md` (lines 56/60): supplier cost data arriving as a workbook requires
  **`commercial_write`**, and a `commercial_view`-only reader was treated as a leak to be fixed.
- The quoting workflow itself treats supplier cost rates as a **`commercial_view`** capability Sale needs.

Owner decision required (one sentence suffices, no code change by the reviewer):
**is `costIntelligence.rates` (supplier cost snapshots with amount/currency/supplier/created_by) part of what a
`sale` may see in the quoting workflow, and if yes under which grant (`commercial_view`), i.e. must
`lastWrites`, `costIntelligence.rates` and the supplier-workbook gate agree on the same permission?**
Until that is answered this acceptance line stays `UNKNOWN`; it is **not** a PR #255 regression and it is out of
`finance_view` scope.

## 6. Regression

`02-full-suite-run.txt`: clean replay at `911f317` → **2375 passed, 44 skipped, 0 failed, 0 error, EXIT=0**
(matches the implementer receipt `2375 passed / 44 skipped`). Two earlier reviewer runs showed 7 and 3 failures:
`Cannot find module 'jsdom'` (the reviewer's own `npm ci` was still running) and one GNT wall-clock flake —
mechanism, interleaved base/head control (BASE 1/10 vs HEAD 1/10) and openpyxl `docProps/core.xml` root cause in
`06-flake-analysis.txt`. Not attributed to the PR.

Reproduce check 1:
```
AUTH_REQUIRED=true python -m pytest evidence/issue254/06-final-review/legacy-repro/test_legacy_lastwrites_repro.py -q -p no:cacheprovider -s
# 3 passed  (the assertions PASS *because* the leak is reproduced; see the printed payloads)
```

## 7. Verdict

**REJECT** — single smallest blocker: the unstamped `lastWrites` branch is fail-open and untested
(`_last_writes_for_actor`, source + one negative test). Browser UAT (2b/2c) and cost-intelligence policy (3)
remain `UNKNOWN`: the first needs a container with Chromium, the second needs one Owner decision.
