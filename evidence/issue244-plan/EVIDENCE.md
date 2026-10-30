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
