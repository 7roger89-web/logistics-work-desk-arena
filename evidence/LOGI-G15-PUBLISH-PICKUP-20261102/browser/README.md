# Issue #263 — browser acceptance (desktop 1440×900 + mobile 390×844)

Run: `node playwright/issue263_pickup_publish_qa.mjs --url http://127.0.0.1:9513/ \
  --out evidence/LOGI-G15-PUBLISH-PICKUP-20261102/browser --evidence-dir <runtime evidence dir>`

App under test: `playwright/issue263_runtime.py` — Streamlit + the REAL built
component bundle, isolated `mongomock` staging DB, `AUTH_REQUIRED=true`.
`?as=reset` wipes every `public_events` / `customer_publications` row for the two
test lots before each viewport, so no pre-seeded publication fixture can exist.

Result: **PASS — 36/36 checks** (`browser-checks.json`, `00-summary.json`).

Proven loop, per viewport, with the DB snapshot as the authority at each step:

| step | evidence |
| --- | --- |
| staff types the pickup date into the real ATD field of `Chặng 1` and saves | `*-2-staff-atd-typed.png`, `*-3-staff-saved.png`, `staff-dispatch-log.json` |
| that ONE action persists `pickup_atd` and creates exactly one `PENDING` source | `browser-checks.json` → `*_staff_state` |
| nothing is published yet; customer A sees no milestone | `*-3b-customer-a-before.png` |
| Admin sees the pending source, ticks the real confirmation, verifies | `*-4-admin-pending-source.png`, `*_verified_state` |
| verification alone publishes nothing | `*_verified_state.publications == []` |
| the EXISTING publisher offers exactly that verified version; publish is disabled until confirmed | `*-5-admin-verified.png`, `*_publisher_options` |
| publication pins the exact verified version and bumps the lot | `*_published_state` |
| customer A reloads and sees `Đã lấy hàng` on `LO-263-A` | `*-7-customer-a-milestone.png` |
| customer B sees neither the lot nor the milestone | `*-8-customer-b-empty.png` |
| no INTERNAL/finance/driver secret appears in the customer payload | checks `... carries no INTERNAL/finance data` |

`final-state-readback.json` is the authoritative DB snapshot after the last
Admin publication. Failure modes not covered here (stale version, unverified
source, tampered-after-approval content) are covered by
`tests/test_g15_pickup_producer.py` (mutation cases M1–M4).
