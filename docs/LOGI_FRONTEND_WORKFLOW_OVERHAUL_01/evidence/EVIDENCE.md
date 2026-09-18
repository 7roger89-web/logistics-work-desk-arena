# LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — Evidence index

Task: LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · branch: `arena/01a0b23b-logistics-work-desk-arena`
Baseline: `main` @ `c8f3fbc501a9b0a743e27e876c0bde683453aaa9` (fresh-checked, no drift).

## Lanes and results

| Lane | Command / artifact | Result |
|---|---|---|
| Focused DOM regression (real production bundle, jsdom) | `node tests/component/dom_acceptance_*.mjs` | New/updated: payment_trust 11✓, payment_correction 10✓, c2a 10✓, c2b 11✓, c2c 10✓, amount_integrity 26✓, home_hierarchy 5✓, navigation_context 7✓ (flows A–F), role_trust 2✓, p2_polish 4✓, shipment_header_edit 7✓, phase_a 32✓, real_use_repair 10✓, create_shipment 5✓, contract_workflow 6✓, finance_actual_entry 12✓, getfly_dsdh 6✓, user_management 13✓ |
| Pre-existing baseline failures (NOT from this branch) | `consolidation`, `handbook`, `user_access` DOM tests | Fail identically on baseline bundle `c8f3fbc` (verified) — stale fixture shapes; untouched here |
| Focused Python regression | `pytest tests/test_contract_route_contract.py tests/test_logi_shipment_operational_data_v1.py tests/test_logi_uat_real_use_repair_02.py tests/test_logi_customer_payment_correction_ui_01.py tests/test_logi_c2c_global_receivables.py tests/test_logi_c2b_partner_payable.py` | 57 passed, 1 failed — the failure (`test_logi_shipment_operational_data_v1`) fails identically on baseline (verified, unrelated to frontend) |
| Typecheck | `tsc --noEmit` in `component/` | PASS |
| Production build + `process` scan | `vite build` + `scripts/scan_process.py dist` | PASS, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |
| Real sandbox transport probe | `runtime_probe_sandbox.json` | Isolated mongomock staging via canonical writers: `payment_record` outcome echoes the correlated `requestId` (the exact contract the P0 UI now waits for) |
| Live isolated app (inspection aid) | Streamlit :9501, no `MONGO_URI` → auto-seeded sandbox staging | Serves the candidate bundle; READ-ONLY inspection, no production contact |
| Static visual pages | `evidence/visual/*.html` | **PROXY_ONLY · NOT_RUNTIME_ACCEPTANCE** — mounted-bundle debug pages; never runtime verification |

## Runtime visual gate (truthful)

Browser binaries cannot be downloaded in this executor sandbox (Playwright CDN,
Chrome CDN and apt mirrors all unreachable; puppeteer cache contains only 0-byte
stubs; no pre-installed chromium/chrome/firefox; no host browser tool), and this
Arena session exposes no live-browser capability.

```
BROWSER_RUNTIME_CAPABILITY=UNAVAILABLE_IN_THIS_SESSION
RUNTIME_VISUAL_GATE=BLOCKED_BY_EXECUTOR_CAPABILITY
DESKTOP_RUNTIME_VERIFIED=NO
MOBILE_RUNTIME_VERIFIED=NO
VISUAL_EVIDENCE=PROXY_ONLY
```

On any machine with a browser, the repo's own authoritative lane applies:
`pip install playwright && playwright install chromium` then
`python playwright/acceptance_phase_a.py http://localhost:9501`.
