# LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — Evidence index

Task: LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · branch: `arena/01a0b23b-logistics-work-desk-arena` (ONE branch, ONE PR: #56)
Baseline: rebased onto `main` @ `1758980` (law projection sha `94990826…` matches the Control Tower).
Repair round 2 scope: two P0 payment-trust repairs + probe upgrade + removal of proxy visual artifacts.

## Round-2 P0 repairs (what the tests actually prove)

1. **Stale-refusal reconsumption fixed** (both customer payment entry points —
   shipment-detail sheet, Receivables sheet, plus the partner & correction writers):
   a backend refusal keeps the form (amount/kind) and mints a NEW requestId for the
   next attempt; the refused request stays historical, so the stale refusal `X` in
   `lastWrites` can never instantly "settle" the retry `Y`.
2. **Success requires an authoritative readback, PER LEDGER in the backend's own
   projection shape**: success = correlated `lastWrites` ok **AND** the canonical
   proof for that write — customer receipts: `finance.payments[].requestId ===
   pendingRequestId`; partner payment: `finance.partner.payments[].requestId`
   (`_partner_projection`, NOT the customer list); partner payable (an obligation,
   not a payment): the canonical obligation result the handler already returns
   (`position` / `obligationId` / `persisted`). ok-without-proof stays
   pending/truthful — never a failure, never green. Refusals surface verbatim
   inline. (Round 3: the round-2 partner gate wrongly used the customer
   `finance.payments` list for both partner writers — corrected; c2b now proves
   the negative guard: customer `finance.payments` NEVER satisfies a partner
   readback.)

## Lanes and results

| Lane | Command / artifact | Result |
|---|---|---|
| Payment-trust DOM acceptance (A–I contract, entry point A: shipment-detail sheet) | `node tests/component/dom_acceptance_payment_trust.mjs` | PASSED checks=11 — A no-lastWrites→pending; B unrelated lastWrites→pending; (A+I) one submit=one intent, double click absorbed; Escape/backdrop cannot dismiss in-flight; E refusal keeps form+inline error; F retry mints NEW id Y≠X; G stale refusal X cannot settle Y; C ok-without-readback stays pending; D ok+fresh readback→close+green (settles only Y); fresh intent per reopen |
| Entry point B (Receivables sheet) same contract | `node tests/component/dom_acceptance_c2c.mjs` | 10 steps passed — double-click→1 intent; unrelated lastWrites cannot fake success; refusal preserves form; retry NEW id; stale X cannot settle; ok-without-readback pending; ok+readback closes |
| Partner payment & payable writers | `node tests/component/dom_acceptance_c2b.mjs` | PASS — 14 checks: payable transport→pending; ok-without-canonical-obligation-proof→pending; canonical obligation result (position/obligationId) settles; payment ok without `finance.partner.payments` match→pending; customer `finance.payments` does NOT satisfy partner readback (negative guard); ok + `finance.partner.payments[].requestId`→green/idle; refusal→retry NEW id→stale-X cannot settle |
| Customer sheet (c2a slice) | `node tests/component/dom_acceptance_c2a.mjs` | PASS — 11 checks incl. ok-without-readback pending, ok+readback closes |
| Correction writer | `node tests/component/dom_acceptance_payment_correction.mjs` | PASSED checks=11 — refusal verbatim; retry NEW correctionRequestId; stale refusal cannot settle; fresh refusal settles only its own id |
| Amount integrity (raw preservation, UNKNOWN≠0) | `node tests/component/dom_acceptance_amount_integrity.mjs` | PASS — 26 checks |
| Full DOM sweep | `node tests/component/dom_acceptance_*.mjs` | 26/29 PASS — failures are exactly the pre-existing baseline trio `consolidation`, `handbook`, `user_access` (stale fixture shapes, verified on baseline; untouched here) |
| Focused Python regression | `pytest tests/test_contract_route_contract.py tests/test_logi_shipment_operational_data_v1.py tests/test_logi_uat_real_use_repair_02.py tests/test_logi_customer_payment_correction_ui_01.py tests/test_logi_c2c_global_receivables.py tests/test_logi_c2b_partner_payable.py` | 57 passed, 1 failed — the failure (`test_logi_shipment_operational_data_v1`) fails identically on baseline (verified, unrelated to frontend) |
| Typecheck | `tsc --noEmit` in `component/` | PASS |
| Production build + `process` scan | `vite build` + `scripts/scan_process.py dist` | PASS, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |
| Real sandbox readback probe (round 2) | `runtime_probe_sandbox.json` | BEFORE (fresh finance requestIds/received/outstanding on `LO-0306`) → WRITE `payment_record` `PAY-REQ-PROBE-2-…` through the ONE canonical handler (`_handle_payment_record` → `save_direct_shipment_payment` → audit → fresh readback) on isolated in-process mongomock → AFTER fresh readback contains the requestId and balances move exactly ±amount. `PERSISTED_PAYMENT_VISIBLE_IN_FRESH_READBACK=YES`, `BALANCES_CONSISTENT=true` |

## Runtime visual gate (truthful)

Browser binaries cannot be downloaded in this executor sandbox (Playwright CDN,
Chrome CDN and apt mirrors all unreachable; puppeteer cache contains only 0-byte
stubs; no pre-installed chromium/chrome/firefox; no host browser tool), and this
Arena session exposes no live-browser capability.

```
BROWSER_RUNTIME_CAPABILITY=UNAVAILABLE_IN_THIS_SESSION
RUNTIME_VISUAL_RESULT=BLOCKED_BY_EXECUTOR_CAPABILITY
DESKTOP_RUNTIME_VERIFIED=NO
MOBILE_RUNTIME_VERIFIED=NO
```

Per the anti-overengineering decision, the round-1 **proxy** visual pages
(`evidence/visual/*.html`) and their builder
(`scripts/build_workflow_overhaul_visual_evidence.py`) are REMOVED from this PR:
they were static mounted-bundle debug pages, never runtime verification, and no
harness replaces them. The repo's own authoritative lane remains available on any
browser-capable machine: `pip install playwright && playwright install chromium`
then `python playwright/acceptance_phase_a.py http://localhost:9501`
(owner preview port; production never touched).
