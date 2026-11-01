# Issue #247 — S3 customer A/B browser tenant boundary (real Chromium)

**Verdict: `S3=PASS`** for the bounded slice below, on **PR #248** HEAD
`63f959431b64e0c8a0103bd8214265f71852e6b2`.

`PRODUCT_SOURCE_CHANGE=NONE`. Only the TEST fixture
(`tests/component/g15_lg_tt_discussion_runtime.py`), the new real-browser runner
(`playwright/issue247_s3_browser.mjs`) and this evidence directory changed. No
auth, portal, publication-allowlist, financial or RBAC source was modified.

This proves **synthetic tenant/published-source isolation inside one test
runtime**. It does **not** prove Google OIDC, Cloud/Atlas identity, or Issue #247
completion — see [Boundary](#boundary).

---

## 1. HEAD, law preflight, OE gate

| Item | Value |
|---|---|
| Repository | `7roger89-web/logistics-work-desk-arena` |
| PR | **#248** (unchanged, still OPEN / HOLD) <https://github.com/7roger89-web/logistics-work-desk-arena/pull/248> |
| PR head measured before work | `63f959431b64e0c8a0103bd8214265f71852e6b2` (`arena/f1a205f4-…`) |
| PR head at time of this evidence | `63f959431b64e0c8a0103bd8214265f71852e6b2` (**unchanged**) |
| Staging base (untouched) | `arena/ae5f9f47-logistics-work-desk-arena` @ `ba03ae7ac27f2020c761bf405e1aaaab80709c62` |
| Session branch | `arena/bfa65e28-logistics-work-desk-arena` (rebased to the PR head above so the diff is exactly the S3 slice) |
| `main` (untouched) | `9e4190b278dd2ced8771c5249582753d34e561db` |

**P2P_LAW_PREFLIGHT** (`AGENTS.md` read from this repository root):

- `P2P_LAW_SOURCE=LOCAL_PORTABLE`
- `LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`
  (projection carries `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical provenance and
  `PROJECTION_DO_NOT_EDIT=YES`; file sha256 `75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`).
  No cross-repository probe was issued merely to manufacture a 404.
- `EXPERIENCE_CHECK=PASS | SOURCE=.p2p/P2P-EXPERIENCE-CAPSULE.json` (recorded
  `PORTABLE_EXPERIENCE_CONTENT_SHA256=9b10fafe780e47bc82da89d6893d1a88a32c06031dfd7cfb63effc89926cce82`).
- `TASK_BRANCH != LAW_AUTHORITY`; this receipt proves only this executor's own preflight.

**OE_GATE** — “Không bị over engineering chứ?”

- `SIMPLER_PATH`: reuse the existing `g15_lg_tt_discussion_runtime.py` portal
  fixture and the existing HEXA Components-v2 portal; no new app, server,
  framework, DB collection or second publication writer. The B positive control
  is created by the **existing** admin publisher, not by a new path.
- `MATERIAL_PROGRESS`: this was the last missing browser proof (customer A/B) of
  the S3 acceptance; S1/S2 already covered their slices.
- `NECESSITY`: without a separately PUBLISHED B lot the only thing provable is
  “B sees an empty page”, which the spec explicitly rejects as WRONG_PASS.
- `CORE_BEFORE_SUPPORT`: product behaviour first (server allowlist, publication
  allowlist, DOM reset); evidence JSON is a thin observer, no separate QA product.
- `SMALLER_VERIFIABLE_SLICE`: one viewport pair (1440×900, 390×844), two lots,
  four identities. No full-suite campaign re-run (no app/test source changed).
- `OE_VERDICT=DO_IT` — every added element maps to a locked acceptance clause;
  nothing speculative was built.

---

## 2. Test data, principals and one shared DB handle

One OS process, one Streamlit runtime, one in-process `mongomock` database:

| Field | Value |
|---|---|
| `pid` (server) | `3977` (all evidence files) |
| database | `logistics_staging` |
| client module | `mongomock.mongo_client` |
| `MONGO_URI` env | `""` (empty) |
| effective config URI | `mongodb://mongomock.local/logistics_staging` (sandbox placeholder) |
| `ENV_IDENTITY` | `PREVIEW` |
| transport | `SANDBOX_STAGING` |
| Streamlit / mongomock | `1.66.1` / `4.3.0` |
| Chromium / puppeteer-core | `153.0.8010.0` (`HeadlessChrome/153.0.8010.0`) / `24.40.0` |

Principals come **only** from `core.customer_portal.build_customer_principal`
(email → Owner-allowlisted `customers.portal_access_email`). The QA radio selects
a fixed TEST email; **no `customer_id` is ever accepted from the browser**.

| | Customer A | Customer B |
|---|---|---|
| TEST email (masked) | `l***@example.test` | `ot***@example.test` |
| `customers.id` | `QA-LG` | `QA-OTHER` |
| lot | `QA-LOT` (mode `SEA`) | `QA-FOREIGN` (mode `ROAD`) |
| approved event (v1) | `QA-EVENT-PICKUP` — “QA-A Đã lấy hàng tại kho Lục Giác” | `QA-OTHER-EVENT-PICKUP` — “QA-B Đã lấy hàng tại kho khác” |
| approved documents (v1) | `QA-DOC-PL-A` (`PL`) | `QA-OTHER-DOC-BL` (`BL`), `QA-OTHER-DOC-POD` (`POD`) |
| manifest version / pointer | `g15-58054dc98b044c3f822f728e405cdfa5` | `g15-533342de7c9b455a8aef95e93bc65512` |
| `approved_content_sha256` | `dcd66ce2…4d7303` | `e24d37b3…5fc7f98` |

Both manifests were created by the **real**
`core.customer_portal_publish.publish_verified_sources(..., actor_role="admin")`
from each customer's **own** verified sources; the B release was not derived from
A's manifest (`server-publications.json`). Internal-only markers exist in the same
database and must never render: `SECRET_INTERNAL_*`, `SECRET_GRIDFS_*`, event
`internal_notes`, `cost` values `987654321` / `123456789`, plus an `INTERNAL`
document `QA-PRIVATE-DOC-A` and an unverified `QA-UNVERIFIED-DOC-A` on A's lot.

Server model readback (`server-readback-{a,b}.json`), one handle, same pid:

- A: `CustomerDashboardView.cards = ["QA-LOT"]`, payload lots `["QA-LOT"]`,
  documents `["QA-DOC-PL-A"]`, publication `g15-58054dc98b044c3f`.
- B: `cards = ["QA-FOREIGN"]`, payload lots `["QA-FOREIGN"]`, documents
  `["QA-OTHER-DOC-BL","QA-OTHER-DOC-POD"]`, publication `g15-533342de7c9b455a`.
- `payload_clean=true` for both: 15 forbidden markers scanned per role
  (other tenant's lot/event/document ids and titles, other manifest version,
  truncated display version, both `approved_content_sha256` values, `SECRET_*`,
  both internal cost values, other `customer_id`) — **0 found**.
- `payload_has_discussion=false` describes the last render of each role (no node
  open at that instant); the node conversation itself is proven in the browser
  below (composer + unsent draft inside A's pickup bubble).

---

## 3. Real-browser results — desktop and mobile

Command (repo root, one Streamlit process already running, `/_stcore/health` →
`200 ok`):

```bash
LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp \
node playwright/issue247_s3_browser.mjs \
  --url http://127.0.0.1:9503/ --out evidence/issue247/s3 \
  --chrome /tmp/chromium --puppeteer-core /tmp/pw-cli/node_modules/puppeteer-core
# BROWSER_CHECKS=176 FAILED=0 | BROWSER_PAGE_ERRORS=0 | S3_BROWSER=PASS | exit 0
```

Streamlit command (TEST-only, ephemeral password, no URI, no Cloud):

```bash
QA_TEST_PASSWORD=<ephemeral> AUTH_REQUIRED=true MONGO_URI= MONGO_DB_NAME= \
ENV_IDENTITY=PREVIEW S3_EVIDENCE_DIR=$PWD/evidence/issue247/s3 \
python -m streamlit run tests/component/g15_lg_tt_discussion_runtime.py \
  --server.address=0.0.0.0 --server.port=9503 --server.headless=true \
  --browser.gatherUsageStats=false --server.fileWatcherType=none
```

| Viewport | Checks | Page errors | Console errors | Horizontal overflow | Exit |
|---|---:|---:|---:|---|---:|
| 1440×900 | 80 | 0 | 0 | none (document 1440, portal 1280) | 0 |
| 390×844 | 80 | 0 | 0 | none (document 390, portal 358) | 0 |
| server-side (same store) | 16 | — | — | — | — |

Sequence actually performed in **one page/session** per viewport:

1. **A (default granted identity)** → dashboard references `shipment-row-QA-LOT` /
   `shipment-card-QA-LOT`, toolbar `QA-LOT · SEA`, pickup node `COMPLETED` from
   A's own approved event, own document count `1 tệp`.
2. Open the pickup node (**real hit-test**: 131×84 desktop, 100×67 mobile,
   `elementFromPoint` hits the node), node conversation composer present, typed the
   unsent draft `S3-DRAFT-A-DO-NOT-LEAK`, opened the read-only modal (510×15 /
   286×15 button hit) showing `QA-A Packing list` and A's publication version
   `g15-58054dc98b044c3f`.
3. **Switch to B in the SAME page/session** → toolbar `QA-FOREIGN · ROAD`,
   pickup `COMPLETED` from B's own approved event, own document count `2 tệp`,
   B's modal shows B's two documents and B's version `g15-533342de7c9b455a`.
4. **Switch back to A** → A's own lot/event return, B's are absent (symmetric).
5. **Reload** (`page.reload()`, fresh Streamlit session) → defaults to granted A,
   then B again: still only B.
6. **Ungranted verified email** `nobody@example.test` → uniform denial screen.

### Leak checks asserted at every stage (both viewports)

For the *other* tenant, all of the following are absent from the shadow DOM text
**and** from every `input`/`textarea` value inside the component:

- lot id (`QA-LOT` / `QA-FOREIGN`) and dashboard references
  (`shipment-row-*`, `shipment-card-*`),
- approved event title and id,
- published document id and title,
- publication version (full and the 20-char display form),
- `approved_content_sha256`,
- `SECRET_*` internal markers and both internal `cost` values,
- A's unsent draft (textarea value emptied when the identity changed).

Carry-over state is explicitly checked when switching A→B: `journey-bubble`
absent, `#journey-modal-layer` has class `hidden` and `#journey-modal-body` is
empty, sticky toolbar reads B's lot, and no stale form value survives. B is a
**positive control**: it renders its own lot *and* its own approved event, so a
blank portal cannot be mistaken for isolation.

### Server-side canonical checks on the same store (`server-negative.json`)

| Check | Result |
|---|---|
| `build_customer_principal("nobody@example.test")` | **`PortalAccessDenied`** (`principal_created=false`, no fallback to contact email, guess or cached principal) |
| A view cards / B view cards | `["QA-LOT"]` / `["QA-FOREIGN"]` — no overlap |
| A principal + A lot + **B manifest** | `PublicationDenied` |
| A principal + **B lot** + B manifest | `PublicationDenied` |
| `read_approved_sources(A tenant, B shipment, B pins)` | `events=0, documents=0` |
| publish `INTERNAL` document `QA-PRIVATE-DOC-A` (admin, correct CAS) | `PublicationWriteDenied` |
| publish unverified `QA-UNVERIFIED-DOC-A` | `PublicationWriteDenied` |
| A publication pointer / manifest count after denials | unchanged / `[1, 1]` |
| (positive control) A principal + A lot + A manifest | `ALLOWED` |

---

## 4. Fail-before (why the fixture had to change)

At the PR head, `_ensure_published()` published **only** A's `QA-LOT` while the
"Khách khác" radio already existed. Captured with the same real Chromium before
any edit (`fail-before-baseline/`):

- `a-current-fixture.png` — A sees `QA-LOT` + A's pickup milestone.
- `b-current-fixture.png` + `fail-before.json` — B sees **`0 lô đã công bố`** and
  the notice “MỘT SỐ LÔ CHƯA ĐƯỢC CÔNG BỐ”.

That is exactly the accepted WRONG_PASS shape (“B shows an EMPTY portal because no
B publication exists”). The fix is fixture-only: seed B's own verified event and
documents and publish them through the existing admin publisher, so B's page has a
real positive control.

---

## 5. Focused regression (no app source changed)

```bash
python -m pytest \
  tests/test_customer_portal_tenant_reset_g15.py tests/test_customer_portal_core_g1.py \
  tests/test_customer_portal_publish_g15.py tests/test_customer_portal_sources_g15.py \
  tests/test_customer_portal_hexa_publication_v0.py \
  tests/test_customer_portal_g15_independent_challenge.py \
  tests/test_customer_portal_oidc_g1.py tests/test_customer_portal_hexa_reference_ui_g15.py \
  tests/test_customer_dashboard_g1_runtime.py tests/test_g1_pr228_regressions.py \
  tests/test_journey_notes.py -q
# 252 passed, exit 0   (focused-tests.txt)
```

`component/node_modules` was installed with the declared `package.json`
(`npm ci`) because the jsdom-lane test otherwise fails on a missing module — an
environment gap, not a source change. No app or test logic was altered to make
anything green, and no test was skipped, xfailed or deselected.

Not re-run here (deliberately): the two full-suite passes, because this slice
changes **no** application or test-logic source. `FULL_SUITE_AT_S3_HEAD` stays
owned by the Issue #247 final review.

---

## 6. Files

| File | Content |
|---|---|
| `browser-run.txt` | runner stdout + `RUNNER_EXIT=0` |
| `browser-results.json` | 176 checks, geometry, chrome version, page/console errors, server facts |
| `desktop-1-A-journey.png` … `desktop-8-denied.png` | A journey, A bubble+draft, A modal, B journey, B modal, A-again, B-after-reload, denied (1440×900) |
| `mobile-1-A-journey.png` … `mobile-8-denied.png` | same sequence at 390×844 |
| `server-db.json` | pid, database, mongomock module, transport, env identity, versions |
| `server-publications.json` | both PUBLISHED manifests, distinct pins and hashes; internal markers that exist in the DB |
| `server-readback-a.json` / `server-readback-b.json` / `server-readback.json` | server `cards`, payload ids, forbidden-marker scan per role |
| `server-negative.json` | canonical same-store negatives above |
| `server-denied-view.json` | ungranted email → `PortalAccessDenied`, `principal_created=false` |
| `focused-tests.txt` | 252 passed, exit 0 |
| `runtime-env.txt`, `runtime-log.txt` | versions, command, health `200 ok`, expected denial log lines |
| `fail-before-baseline/` | pre-change Chromium screenshots + JSON (B empty portal) |

---

## 7. Boundary

- `OIDC_REAL_AUTH=UNKNOWN` — the identities are TEST-granted fixed emails; no
  Google OIDC login or Cloud deployment is claimed or proven here.
- `CLOUD_UAT=NOT_VERIFIED`, `STAGING_DEPLOY=NOT_VERIFIED`; no Cloud/Atlas/Drive/
  production write, no merge to staging or `main`, PR #250 untouched.
- Customer **comment/attachment writes** are not part of this slice (they belong
  to the existing #236/#237 lanes); S3 proves read isolation, published-source
  isolation and server-side denial.
- `docs/NEXT.md` was intentionally **not** edited: the S3 lock allows only the
  fixture, the runner and `evidence/issue247/s3/`. The Control Tower can record the
  checkpoint when it reviews this evidence.
