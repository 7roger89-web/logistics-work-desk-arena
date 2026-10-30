# Issue #244 — Node 00 KẾ HOẠCH: browser evidence

Everything below was produced by driving the REAL Streamlit apps with the REAL
built assets in Chromium 153, at **1440×900 (desktop)** and **390×844 (mobile)**.
Screenshots are not the proof — the assertions in the two runners are.

## Staff (`playwright/issue244_plan_staff_qa.mjs` → `ISSUE244_STAFF_BROWSER=PASS`, 20 checks)

Isolated runtime: `tests/component/issue244_staff_runtime.py` (mongomock, seeded
plan facts on the staging lot data, unchanged `views.web_app`).

| file | what it shows |
| --- | --- |
| `desktop-1-journey-node00.png`, `mobile-1-journey-node00.png` | stepper starts at `journey-step-plan` → `journey-step-MAIN_CARRIAGE` → `journey-step-delivery`; Node 00 badge `00` |
| `desktop-2-plan-panel.png`, `mobile-2-plan-panel.png` | plan panel opened INSIDE the Journey: quote `BG-0306` (CTA `/kinh-doanh-bao-gia?q=BG-0306`), contract `HDMB-0306` UNVERIFIED (CTA `/hop-dong/HDMB-0306`), advance “Chưa xác minh đã nhận” + “cần đối soát”, 4/4 controls hit-testable, no horizontal overflow |
| `desktop-3-detail-map-node00.png`, `mobile-3-detail-map-node00.png` | detailed map keeps Node 00 above the first operational node with both in-map conversations (#236 intact) |
| `desktop-4-customer-self-lot.png` | LO-0307 (CUSTOMER_SELF, no quote): “Chưa gắn báo giá” + “Không áp dụng” |
| `desktop-5-unknown-flow-lot.png` | LO-0308 (import form unconfirmed): advance stays undetermined |

Decoys proven absent from the rendered panel: `BG-9999` (sibling quote of the
same customer), `HDMB-SUB-0306` (TT↔sub-agent contract), the unclassified
receipt amount `20,000,000`, and any “Đã ký” / “đã nhận tiền hàng” claim.
Raw results: `staff-plan-results.json`.

## Customer (`playwright/issue244_plan_customer_qa.mjs` → `ISSUE244_CUSTOMER_BROWSER=PASS`, 15 checks)

Isolated runtime: `tests/component/issue244_customer_runtime.py` (synthetic
identities `QA-244-LG` / `QA-244-OTHER`, publications built through the real
`core.hexa_customer_publication` allowlist + `approved_content_fingerprint`).

| file | what it shows |
| --- | --- |
| `desktop-6-customer-journey-node00.png`, `mobile-6-customer-journey-node00.png` | node 00 first, numbered 00, state `UNKNOWN` (never COMPLETED) |
| `desktop-7-customer-plan-published.png`, `mobile-7-customer-plan-published.png` | “Hồ sơ Kế hoạch đã công bố” = exactly `CUSTOMER_QUOTE` / `CUSTOMER_CONTRACT` / `PAYMENT_REQUEST`, labels `Báo giá` / `Hợp đồng` / `Đề nghị thanh toán`, plus the metadata disclaimer |
| `desktop-8-customer-plan-empty.png` | a PUBLISHED lot with no plan document: “Chưa có hồ sơ Kế hoạch được công bố” (its published BL stays outside the plan block) |

Decoys proven absent from node 00 and from the whole portal text: the published
non-plan BL, `SECRET_PRIVATE_CONTRACT`, `SECRET_DRIVE`, `QA-244-QUOTE-V1`
(stale version), `QA-244-PRIVATE`, `QA-244-STALE`, `QA-244-FOREIGN`, and the
internal amounts `385.000.000` / `192.500.000` / `20.000.000`.
Raw results: `customer-plan-results.json`.

## Repair cycle — the three independent-review blockers (HEAD `d9b5c91`)

| blocker | defect | fix | proof |
| --- | --- | --- | --- |
| 1 | a linked quote with `status=DRAFT/SENT/REJECTED` could still make Node 00 `COMPLETED` | `_node_state()` now requires `quote.accepted` (the quote record itself says `ACCEPTED`) before completion; no-quote and unreadable-link keep distinct evidence text | pytest `DRAFT/SENT/REJECTED/EXPIRED` → `WAITING`, `ACCEPTED` → `COMPLETED`; browser `data-plan-state=WAITING` on desktop + mobile |
| 2 | `customer_confirmation` was mapped to the same `ATTESTED` label as a signature | `_signature_evidence()` separates the two canonical flags and only attests when the contract record itself carries a signature, or an AGREED agreement names **this** contract and sets `signed_contract`; unattributable evidence is ignored and confirmation-only is stated as “Khách đã xác nhận điều khoản thương mại (chưa phải chữ ký hợp đồng)” | pytest: confirmation-only, no-identity, different-identity, instrument-tied positive; browser: `data-signature=UNVERIFIED`, no `Đã ký` / `Đã có xác nhận ký` |
| 3 | a brand-new lot (zero operational nodes) fell into the fresh cockpit with **no** Node 00 | `FreshShipmentCockpit` renders a `00 KẾ HOẠCH` card and opens the SAME `PlanQuickPanel` from the same `s.plan` inside the fresh Journey rail; no BOOKING/SI/VGM/transport node is invented | jsdom STEP 9; Chromium `desktop-9-fresh-journey-node00.png`, `mobile-9-fresh-journey-node00.png` |

New isolated lot for the browser/DOM proof: **`LO-0309`** in
`tests/component/issue244_staff_runtime.py` (no mode/Incoterm → `journey.nodes == []`),
quote `BG-0309` = `SENT`, contract `HDMB-0309` unsigned, agreement `AGR-0309`
carrying `customer_confirmation` only.

Re-run results at `d9b5c91`:

- `tests/test_issue244_plan_node.py` → **39 passed** (+9 blocker regressions).
- jsdom `ISSUE244_PLAN_DOM_ACCEPTANCE=PASS (9 checks)`.
- `ISSUE244_STAFF_BROWSER=PASS` (26 checks, desktop + mobile, includes the empty-Journey lot).
- `ISSUE244_CUSTOMER_BROWSER=PASS` (15 checks) — no regression on the customer side.
- `tsc --noEmit` clean, `npm run build` clean, `scan_process.py dist` → 0 hits.
- Full suite in clean worktrees: base `2fcb74e` **41F / 2262P / 45S** → `d9b5c91`
  **40F / 2302P / 45S**, with **0** newly failing tests
  (`evidence/issue244-plan/pytest-failed-set.txt`).

## How to reproduce

```bash
# staff
AUTH_REQUIRED=false ENV_IDENTITY=PREVIEW MONGO_URI="" /tmp/venv/bin/streamlit run \
  tests/component/issue244_staff_runtime.py --server.port 9501 --server.address 0.0.0.0 --server.headless true
node playwright/issue244_plan_staff_qa.mjs --url http://127.0.0.1:9501/ --out evidence/issue244-plan --chrome /tmp/chromium

# customer
AUTH_REQUIRED=false ENV_IDENTITY=PREVIEW MONGO_URI="" /tmp/venv/bin/streamlit run \
  tests/component/issue244_customer_runtime.py --server.port 9502 --server.address 0.0.0.0 --server.headless true
node playwright/issue244_plan_customer_qa.mjs --url http://127.0.0.1:9502/ --out evidence/issue244-plan --chrome /tmp/chromium
```

Sandbox note: `export LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp` before running Chromium.
