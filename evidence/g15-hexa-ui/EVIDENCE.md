# G1.5 — Khôi phục giao diện cổng khách hàng Lục Giác đúng HTML gốc

Task: rebuild the G1 customer portal so it is the Owner's reference
`HEXA_LucGiac_DEMO.html` (Dashboard 8 cột → map-first Journey 00–06), fed only by
server-approved publication data — not a CSS-decorated Streamlit page, and not
the unrelated `HEXA-Journey-Timeline-V0.html` prototype.

---

## 1. Law / planning preflight

| Gate | Value |
|---|---|
| `P2P_LAW_SOURCE` | **`LOCAL_PORTABLE`** — `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` carries `P2P_PORTABLE_LAW_PROJECTION=YES`, `CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`, `SOURCE_CONTENT_SHA256=11ce33bb…68bd4b`, `PACKAGE_VERSION=8.4.7-C-codex.74`. Canonical repo was not reached in this session, so canonical does **not** win. No cross-repo probe was fabricated. |
| `EXPERIENCE` | `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` → record `shared-exp-b2611df4c9393f0017f07dcb` (`DISTRIBUTION_WITHOUT_ACTOR_CONSUMPTION`) — applied as: law + experience receipt recorded here before substantive work. |
| `INITIAL_PLANNING_CLASSIFICATION` | **`UIUX`** (skill `.agents/skills/p2p-uiux/SKILL.md`) |
| `RUNTIME_UI_REVIEW_REQUIRED` | `YES` — real Chromium was available (`PLAYWRIGHT`-equivalent capability, `puppeteer-core` + Chromium 138), so code inspection alone could never produce a visual PASS. |
| Boundary | No merge to main, no production touch, no secrets/OIDC/Atlas change, no G1 rebuild. |

### `OE_GATE`

> **Không bị over engineering chứ?**

- `SIMPLER_PATH` — reuse the already-present `st.components.v2` mount machinery
  (`views/logi_shell.py` pattern) instead of a second server, a React rebuild, or
  a text-rewriting Streamlit hack. Done: 1 HTML + 1 CSS + 1 JS + 1 image, no
  `npm`, no new runtime.
- `MATERIAL_PROGRESS` — the portal now **is** the Owner's reference: same
  8-column dashboard, same map-first journey, same node/bubble/modal/zoom model,
  in the real Streamlit app behind the real principal.
- `NECESSITY` — the previous G1 page could not satisfy the brief at any CSS
  budget: it had no journey map, no nodes, no bubbles, no modal.
- `CORE_BEFORE_SUPPORT` — core first: principal → publication allowlist →
  journey model → dashboard/journey. Support surfaces (owner email control,
  logout, notices) were left as they were.
- `SMALLER_VERIFIABLE_SLICE` — the deliverable is one authenticated screen plus
  its QA harness; it did not grow a contract designer, a stage-document uploader
  or a comment channel (all three exist in the reference **as demo-only
  write UI** and were deliberately dropped — G1 has no backend contract for
  them).

`OE_VERDICT=DO_IT` — the presentation port is the only path that satisfies
"Dashboard → Map-First Journey 00–06 đúng bản HTML", and it reuses the runtime
already in production instead of adding one.

---

## 2. Reference integrity (input, not substituted)

| Item | Value |
|---|---|
| File | `/tmp/arena-coding-uploads/HEXA_LucGiac_DEMO.html` (Owner attachment) |
| Bytes | **826,336** |
| SHA-256 | **`b91c878e44256e741c533f75e62fdcc89507413d609b0b3d365af85810fbb40a`** |
| Verified | `sha256sum` before any code change, and re-stated in
  `views/customer_portal_component.REFERENCE_SHA256` |
| Rejected | `HEXA-Journey-Timeline-V0.html` — a different prototype; never opened, never used |

Baseline renders were produced from that exact file (local `file://`, Chromium
138, DPR 1) **before** any code was written — see §6.

---

## 3. What changed

### 3.1 New: ported reference assets (`assets/customer_portal/`)

| File | SHA-256 | Origin |
|---|---|---|
| `hexa-portal.html` | `4f2c5604…fac4b` | reference `<body>` markup | 
| `hexa-portal.css` | `3a94a755…04a464` | reference `<style>` (347 lines) |
| `hexa-portal.js` | `b62a12ff…49d4` | reference interaction engine (626 lines) |
| `sea-chart.webp` | `f83d4216…abdef9` | the reference's embedded sea chart, decoded byte-for-byte (107,956 bytes, RIFF/WEBP) |

The port keeps the reference geometry and behaviour verbatim: node size
116×74 (110×74 mobile), desktop pitch 148 / x0 24, mobile grid
`MOBILE_POS` 3-2-2 with rows `[120,220,320]`, `journeyEdgePath()` bezier
rules, `positionBubbleElement()` collision avoidance against the utility chip,
zoom bar and legend, `fitJourney()` bounds maths, zoom clamp 0.55–1.85, drag and
ctrl+wheel pan, Esc parity.

Only three scoping changes were necessary, all mechanical:

1. `:root` / `body` → `.hexa-portal`, because a Components-v2 mount lives in a
   shadow root (custom properties would otherwise never resolve).
2. `*{box-sizing}` → `.hexa-portal, .hexa-portal *`.
3. Inline `style="…"` on three decorative layers and `onclick=""` handlers were
   replaced by three equivalent CSS classes (`.journey-map-texture`,
   `.journey-map-grid`, `.journey-hint-bar`) and `addEventListener` bindings —
   identical values, no visual change.

**Deleted from the reference (not decoration — fabrication):**
`window.__DEMO_DATA__` and all its figures (53.400.000 VND, 30.000.000 VND,
23.400.000 VND, ETA 25/10/2026, contact "Ms. Minh Tú 0901 234 567", plate
"29H-886.68", documents `DOC-LG-*`, quote `QT-20261022-LG01`, contract
`HD-LG-2026-01`, demo timeline/comments), the in-browser canvas/PDF voucher
generator (`buildDemoVoucherCanvas` / `buildPdfBuffer` / `buildDemoVoucherPdf`),
the `Tải PDF minh họa` download buttons, and the demo comment/upload form
(`#stage-comment-input`, `#btn-submit-stage-collab`).

### 3.2 New: `core/customer_journey.py` (pure model, no I/O)

Server-built presentation model. The hard rules are encoded as code, not copy:

- `PUBLISHED` ⇒ **only** "this version was approved". A stage becomes
  `COMPLETED` **only** if an approved, version-pinned public event maps to it;
  everything else is `UNKNOWN` → `CHƯA ĐỐI SOÁT` / "Chưa xác minh"
  ("No approved data"), never "chưa bắt đầu" and never inferred from ordering.
- `current` is never inferred (G1 carries no current-stage marker) → `false`.
- Unmapped event stages are dropped, never folded into a neighbour.
- Stage names follow the mode: ROAD `Nhận & ghép` / `Vận chuyển`; SEA
  `Gom hàng & đóng container` / `Vận tải biển`; AIR `Gom hàng & chuyến bay`;
  RAIL `Gom hàng & xếp toa`; **unknown mode** gets explicit
  `Chặng 02 — chưa xác định phương thức`, so a SEA/mode-less lot can never show
  ROAD evidence wording.
- Nothing is invented: cargo/route/ETA/contact/timeline/documents/quote are shown
  only if the publication released them; debt is `status=UNKNOWN` because no
  reconciliation record crosses the G1 boundary (a released quote is **not**
  treated as a payable debt).
- `display_timestamp()` is presentation-only (`2026-10-24T08:00:00Z` →
  `24/10/2026 08:00 UTC`); unparseable values pass through untouched.

### 3.3 New: `views/customer_portal_component.py`

One `st.components.v2.component("hexa_customer_portal", html=…, css=…, js=…,
isolate_styles=True)` mount, registered once per Streamlit runtime (the same
`_state`/`Runtime.instance()` pattern as `views/logi_shell.py`). `height="content"`
so the tall journey view is never clipped by a fixed component frame. Assets are
read once via `st.cache_resource`; a missing asset raises `PortalAssetError`
which renders a truthful error — never a blank or a fake dashboard.

### 3.4 Changed: `core/customer_portal.py` (+21/−3)

`PublicationCard` gained `timeline`, `documents`, `quote` — populated **only**
from `hexa_customer_publication.build_customer_publication()`'s already
allowlisted, version-pinned public projection (`_public_events`,
`_public_docs`, `_public_quote`). No new query, no new collection, no widening:
foreign rows, unapproved events/documents and internal fields still cannot cross
the boundary.

### 3.5 Changed: `views/customer_dashboard.py` (+151/−70)

The native-Streamlit card/table renderer was replaced by the reference mount.
The principal path is untouched: `web_app.main()` → `current_oidc_session()` →
`build_customer_principal(verified_email=…)` → `load_customer_dashboard()`.
Also: masked account hint (`po***@example.com`) instead of the full address in
the page body, an explicit non-production data strip
(`DỮ LIỆU STAGING — KHÔNG PHẢI SẢN XUẤT` from `ENV_IDENTITY`), and the
denied/OIDC-problem/no-lot screens kept as-is.

### 3.6 Tests

- **New** `tests/test_customer_portal_hexa_reference_ui_g15.py` (23 tests):
  asset provenance/parity, "demo machinery did not survive", chart hash, the
  pure model rules above, and real `AppTest` runtime assertions on the mounted
  component payload (own lots only, internal/foreign sentinels absent, one mount,
  no internal shell, revocation, forged query params).
- **Updated** `tests/test_customer_dashboard_g1_runtime.py` — two assertions were
  bound to the old native widgets; they now read the mounted payload. Security
  intent unchanged (the same negative cases still run).

---

## 4. Evidence layers

### 4.1 `SOURCE_REVIEW`

- Byte-verified reference (§2) and byte-identical sea chart
  (`f83d4216…abdef9`).
- Reference ids/headers/tokens/functions asserted present in the ported assets;
  forbidden demo identifiers and every fabricated figure asserted absent
  (`test_assets_are_the_owner_reference_not_another_prototype`,
  `test_demo_machinery_did_not_survive_the_port`).
- No second server / framework / bridge: `views/customer_portal_component.py` has
  no `fastapi|flask|uvicorn|requests|httpx`; the only new entry is the same v2
  component registry already used by the internal shell.
  `SOURCE_REVIEW` alone is **not** used as the visual verdict.

### 4.2 `TEST_PASS` (Python / Streamlit runtime)

Environment: Python 3.11, `streamlit 1.66.1`, `mongomock`, `pytest`;
`requirements.txt` fully installed.

```
$ python -m pytest tests/test_customer_portal_hexa_reference_ui_g15.py -q
23 passed

$ python -m pytest tests/test_customer_dashboard_g1_runtime.py \
    tests/test_customer_portal_core_g1.py \
    tests/test_customer_portal_oidc_g1.py \
    tests/test_customer_portal_hexa_publication_v0.py -q
89 passed
```

Full-suite regression, per `AGENTS.md` (baseline from a pristine worktree of the
base commit, then the same command on HEAD):

```
base  4eb3d12 (worktree /tmp/base-wt): 36 failed, 2021 passed, 45 skipped
HEAD  (this change)                  : 36 failed, 2044 passed, 45 skipped
new failures (comm -13): NONE
newly fixed  (comm -23): NONE
```

`tests/test_customer_portal_core_g1.py::test_customer_modules_have_no_browser_identity_or_url_id_path`
is in the **pre-existing** failing set on the base commit (it greps
`st.query_params` in `views/web_app.py`, which already used it for
`?portal=customer` presentation routing). Not introduced here, not masked.

### 4.3 `VISUAL_PASS` (real browser)

`playwright/g15_hexa_portal_qa.mjs` — real Chromium 138 driven by
`puppeteer-core` against the running Streamlit app, asserting from the shadow
root (visible text only; `<style>` and `.hidden` subtrees excluded):

```
$ node playwright/g15_hexa_portal_qa.mjs --url http://127.0.0.1:9501/ \
     --out evidence/g15-hexa-ui/runtime
26/26 checks passed → VISUAL_PASS
```

Covered: 2 published lots, 7 dashboard headers + 8 columns, explicit
`UNKNOWN / Chưa đối soát`, 7 nodes 00–06, ROAD label set, node/bubble containment
inside `#journey-map-viewport`, bubble → modal → back-to-map → back-to-dashboard,
SEA label set with no ROAD label, zoom in 113%→128%, zoom out 128%→98%, fit
re-centre, mobile 390×844 card layout (table hidden), mobile 7 nodes + contained
bubble, zero uncaught page errors. The harness also fails if **any** reference
demo figure appears on screen.

### 4.4 Security negatives (browser, not just unit)

| Probe | Result | Evidence |
|---|---|---|
| Non-allowlisted verified email | "Tài khoản này chưa được cấp quyền…", no portal mounted, no lot string | `runtime/30-security-denied-1440.png` |
| Forged `?customer_id=CUST-MINHDUC&shipment_id=G1-MD-001&lot=…&version=v9` | lots = `["G1-LG-001","G1-LG-002"]`, `G1-MD-001` absent, forged id not echoed | `runtime/31-security-forged-params-1440.png` |
| Internal/admin surface for a customer session | `build_view_model`, `logi_shell.render`, `require_login` never called; no owner email control | `test_customer_portal_never_mounts_the_internal_shell` |
| Owner revokes grant between reruns | portal unmounted, no data | `test_revoked_access_after_mount_shows_no_data` |
| Reference demo money/ETA/documents | absent from payload, DOM text and screenshots | `test_*` + QA check "no fabricated demo figure" |

### 4.5 `LIVE_GOOGLE`

**`LIVE_GOOGLE=NOT_RE-VERIFIED_IN_SANDBOX`.** The sandbox has no staging Google
client and no route to `accounts.google.com`, and the brief forbids touching
OIDC. Browser QA therefore authenticated through the *same synthetic-claim
harness path the existing G1 runtime tests already use*
(`streamlit.user_info._get_user_info` patched to an `email_verified` Google
claim + mongomock seeded from `scripts/seed_customer_portal_staging.py`). No
identity-emulation control ships in the app. The real
`GET https://thu-log-g1-test.streamlit.app` → Google → allowlist → portal path
must still be re-confirmed by the Owner on staging; nothing in this change alters
`core/customer_portal_oidc.py`, `secrets.toml`, or the principal resolution.

---

## 5. Evidence inventory

Reference baselines (rendered from the verified file, Chromium, DPR 1):
`evidence/g15-hexa-ui/00-ref-dashboard-1440.png`, `01-ref-journey-1440.png`,
`02-ref-dashboard-390.png`, `03-ref-journey-390.png`,
`04-ref-node-bubble-1440.png`, `05-ref-journey-390-map.png`,
`06-ref-mobile-bubble-390.png`, `07-ref-modal-1440.png`.

Staging app after authentication (real Chromium):
`runtime/10-desktop-dashboard.png`, `11-desktop-journey-road.png`,
`12-desktop-node-bubble.png`, `13-desktop-readonly-modal.png`,
`14-desktop-back-to-dashboard.png`, `15-desktop-journey-sea.png`,
`16-desktop-zoom-fit.png`, `20-mobile-dashboard.png`,
`21-mobile-journey.png`, `22-mobile-bubble.png`, `23-mobile-fullpage.png`,
`30-security-denied-1440.png`, `31-security-forged-params-1440.png`,
`qa-report.json`.

Direct visual comparison (same viewport, same layout maths):

| Reference | Portal |
|---|---|
| `00-ref-dashboard-1440.png` | `runtime/10-desktop-dashboard.png` |
| `01-ref-journey-1440.png` / `04-ref-node-bubble-1440.png` | `runtime/11-desktop-journey-road.png` / `12-desktop-node-bubble.png` |
| `07-ref-modal-1440.png` | `runtime/13-desktop-readonly-modal.png` |
| `06-ref-mobile-bubble-390.png` | `runtime/22-mobile-bubble.png` |

Known, intentional visual differences (all in the direction of *less* content,
never *invented* content):

1. The reference's fixed `DEMO — DỮ LIỆU MINH HỌA` strip and amber notice
   banner are replaced by the honest `DỮ LIỆU STAGING — KHÔNG PHẢI SẢN XUẤT`
   strip (identical `#f59e0b` / `.demo-badge-fixed` styling, different truth).
2. All seven nodes render `CHƯA ĐỐI SOÁT` (grey stripe) and the toolbar shows
   `Đang ở: Chưa xác minh`, `ETA kho: Chưa xác minh` — because the staged
   publications carry no approved events (`event_versions: {}`). This is the
   required behaviour, not a regression: `PUBLISHED` ≠ stage completed.
3. Header account chip shows the masked email; the reference has no account.
4. Modal drops the demo download buttons and the demo comment/upload block.
5. Numbers are absent rather than demo numbers (`UNKNOWN / Chưa đối soát`).

---

## 6. Reproduce

```bash
# assets + model + view are plain files; no build step
python -m pytest tests/test_customer_portal_hexa_reference_ui_g15.py -q

# local staging app (synthetic Google claim + mongomock seed; see §4.5)
python -m streamlit run /tmp/run_portal_demo.py --server.port 9501 \
    --server.address 0.0.0.0 --server.headless true

# real-browser acceptance
CHROME_PATH=/path/to/chrome node playwright/g15_hexa_portal_qa.mjs \
    --url http://127.0.0.1:9501/ --out evidence/g15-hexa-ui/runtime
```

`playwright/g15_hexa_portal_qa.mjs` deliberately does not add a dependency:
it resolves `puppeteer-core` from `--puppeteer-core`, `PUPPETEER_CORE_PATH`,
`node_modules`, or the disposable sandbox install, and Chromium from
`--chrome` / `CHROME_PATH`.

---

## 7. Branch / SHAs / diff

| Field | Value |
|---|---|
| Session branch | `arena/baf65589-logistics-work-desk-arena` (active; cannot be renamed) |
| Requested staging branch | `arena/ae5f9f47-logistics-work-desk-arena` — **not** pushed to; see blocker B1 |
| Base SHA | `4eb3d127db71f810fd05a0e5eabbb985103efbab` (re-measured, matches the brief) |
| Head SHA | see the commit on this branch carrying this file (base + this change) |
| Changed/added | `core/customer_portal.py`, `views/customer_dashboard.py`, `core/customer_journey.py` *(new)*, `views/customer_portal_component.py` *(new)*, `assets/customer_portal/{hexa-portal.html,hexa-portal.css,hexa-portal.js,sea-chart.webp}` *(new)*, `tests/test_customer_portal_hexa_reference_ui_g15.py` *(new)*, `tests/test_customer_dashboard_g1_runtime.py`, `playwright/g15_hexa_portal_qa.mjs` *(new)*, `evidence/g15-hexa-ui/**` |
| Not touched | `core/customer_portal_oidc.py`, `.streamlit/secrets*`, `core/auth.py`, `views/logi_*`, `component/**`, `main` |

---

## 8. Blockers / open items

- **B1 — branch identity.** The session is pinned to
  `arena/baf65589-logistics-work-desk-arena`; pushing
  `arena/ae5f9f47-logistics-work-desk-arena` is out of scope for this session and
  no force-push is allowed. The fast-forward with an expected-SHA guard must be
  run by whoever owns that branch (see §9).
- **B2 — `LIVE_GOOGLE`** (§4.5) can only be confirmed on the staging host.
- **B3 — approved stage/doc/quote data does not exist yet in staging.** The
  publication documents in `scripts/seed_customer_portal_staging.py` carry
  `event_versions: {}` / `document_versions: {}` / `quote: {}`, so every lot is
  honestly `UNKNOWN`. The UI path for approved events IS implemented
  (`build_stage_nodes` + `display_timestamp` + document/quote sections, unit
  tested); it will light up when an Owner-approved publication releases versions.
  **No customer-facing completion state was fabricated to make the screenshot
  look like the demo.**
- **B4 — the reference's write surfaces stay out.** Stage comments, uploads and
  fake PDF downloads are demo-only UI with no backend contract; they were removed
  rather than wired to a stub, per "no write without a contract".

---

## 9. Handoff — fast-forward with SHA guard (owner of the staging branch)

```bash
BASE=4eb3d127db71f810fd05a0e5eabbb985103efbab
HEAD_SHA=$(git rev-parse arena/baf65589-logistics-work-desk-arena)  # recorded after commit
git fetch origin
[ "$(git rev-parse origin/arena/ae5f9f47-logistics-work-desk-arena)" = "$BASE" ] || { echo "STALE: refusing"; exit 1; }
git push origin "$HEAD_SHA":refs/heads/arena/ae5f9f47-logistics-work-desk-arena
```

No `--force`, no merge into `main`.

---

## 10. Verdict

**`PROVEN`** for the in-sandbox scope, with the explicit boundaries above:

- `SOURCE_REVIEW=PROVEN` (reference verified byte-for-byte; port content asserted)
- `TEST_PASS=PROVEN` (23 new + 89 portal tests; full suite 0 new failures vs base)
- `VISUAL_PASS=PROVEN` (26/26 real-browser checks, desktop 1440×900 + mobile
  390×844, containment and negative-data assertions)
- `LIVE_GOOGLE=NOT_RE-VERIFIED_IN_SANDBOX` (B2)
- `BRANCH_ALIGNMENT=BLOCKED_SESSION_SCOPE` (B1)
- `APPROVED_STAGE_DATA=NOT_YET_PUBLISHED_IN_STAGING` (B3) — renders as
  `CHƯA ĐỐI SOÁT` / `Chưa xác minh` by design
