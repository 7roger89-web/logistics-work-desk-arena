# LOGI #199 — Owner trial readiness receipt (this session)

Purpose: make the reviewed Journey-G2 app **openable and usable by the Owner now**, and
record exactly which pre-handover checks were performed, with their real environment and
their honest limits. This is not a redesign, not a G0–G5 rerun, and not a production release.

Fixed branch for this session: `arena/3851e3be-logistics-work-desk-arena`
(parent reviewed branch: `arena/bb243332-logistics-work-desk-arena`).

## 1. Preflight receipts (this actor, this session)

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
```
Read: repo-root `AGENTS.md`; `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` (projection header:
`P2P_PORTABLE_LAW_PROJECTION=YES`, `CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`,
`SOURCE_CONTENT_SHA256=11ce33bb…68bd4b` — matches the Owner-supplied canonical hash; projection file
sha256 `75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`). Canonical cross-repo read
was not attempted: this is a repo-scoped clone with valid portable law, and portable law forbids a
cross-repo probe made only to manufacture fallback. Order of fallback honoured: canonical (not
already reachable in this session) → installed (absent) → portable (valid, used).

```
EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb
```
Bounded lookup against `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` (1 record, `state=ACTIVE`,
authority `NON_AUTHORITATIVE_VERIFIED_EXPERIENCE`). Its lesson — the executing actor must itself
consume law/capability and emit bounded source-bound receipts before substantive work — is applied
here by emitting this session's own receipts rather than inheriting another actor's. Advisory only;
it did not widen authority or scope.

```json
{"schema":"p2p-skill-consumption-receipt/1","skills":[{"id":"p2p-uiux","path":".agents/skills/p2p-uiux/SKILL.md","sha256":"98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2","consumption":"READ_AND_APPLIED"}]}
```
`p2p-uiux` hash verified on disk against `.p2p/portable/P2P-SKILL-PROJECTION.json`
(`SKILL_CHECK=NO_MATCH` for the remaining projected skills: this task is trial delivery/UAT handoff,
not prompt authoring, quorum, atlas, feedback, or an explicit reality-check request). Applied
guidance: `RUNTIME_ACCESSIBLE AND SUITABLE_BROWSER_CAPABILITY => RUNTIME_UI_REVIEW_REQUIRED=YES`;
in this host `BROWSER_CAPABILITY=UNAVAILABLE` (no Chromium/Playwright binary), so this session makes
**no** claim of new pixel-level visual review and reuses the existing real-browser G2 capture as the
visual evidence of record.
`INITIAL_PLANNING_CLASSIFICATION=UIUX`; `FINAL_ROUTING_CLASSIFICATION=UIUX` (delivery/UX of an
existing interface; no new UI was designed).

## 2. Reviewed HEAD verified exactly

```
REVIEWED_HEAD=7ef144c22081d64806fde6e3149c4d69afd1552a
```
- `git fetch` → object present; local `HEAD` reset to exactly this commit (no other branch created,
  `main` untouched at `5c6642a339ec53fe4cc300b15f665e2cd5384bca`).
- Worktree was clean before and after (`git status --porcelain` empty).
- Reviewed artifact identity re-derived from the tree, not trusted from prose:
  `component/dist/logi-shell.js` sha256 `3b650f8f2d7171113ddcd927f885133898d60d5cd22dece16a95dfc092089e5c`,
  `component/dist/logi-shell.css` sha256 `412f27aa81d65b5c0a3bafadd98f3c3123ee6a2d5ec5ea4957ca3084409917fb`
  — both equal the values recorded in `docs/goals/LOGI-APP-RENEWAL-01/state.json` / `UAT.md` for the
  reviewed candidate.
- Owner-ordered scope: Independent Supervisor `PASS` for the Journey **G2** interface (Vietnam map,
  11 nodes, zero-node, touch-pan, save/readback on sample data). That gate is the Owner's input to
  this task; this session did not self-sign any independent review.

## 3. Trial surface handed to the Owner

| # | Surface | Verified how |
|---|---|---|
| 1 | **`LOGI199-GOI-DUNG-THU.zip`** (self-contained trial package, offered in this session's file viewer) | Built with `tar` excludes + `zipfile` (launcher stored `0755`). Verified by fresh extraction in a clean directory: `bash MO-APP-DUNG-THU-MAC.command` created `.venv`, installed `requirements.txt`, picked a free port (9501 busy → 9502) and served `GET /_stcore/health` → `200`; then `AppTest` boot of the extracted package: `APP_BOOT_EXCEPTIONS=0` after `STAGING_ISOLATION_PROOF=PASS transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO production_client=NO`, `T6-FCL : 11 nodes / 11 edges / PROFILE_READY`, `SEA-188 : 0 nodes / PROFILE_INCOMPLETE`. macOS-only `open` call is guarded and not part of the pass/fail path. **macOS runtime itself: NOT_RUN** (no macOS host). Windows: shim `MO-APP-DUNG-THU-WINDOWS.cmd` → existing `scripts/logi199_uat.cmd`, unchanged. |
| 2 | In-session **LIVE PREVIEW** panel of the running app | App side proven: `.venv/bin/python -m streamlit run scripts/logi199_t6_staging_app.py --server.port 9501 --server.address 0.0.0.0`; `GET /_stcore/health` → `200 ok`; `GET /` → `200`, no `X-Frame-Options`/CSP `frame-ancestors`, and a request carrying preview `Host` + `Origin` returns `200`. The panel itself (platform-mediated, token-aware) could **not** be exercised from this sandbox → `NOT_VERIFIED`. |
| 3 | Direct raw URL `https://<port>-<sandboxId>.e2b.app` | **BLOCKED — do not give this to the Owner.** Verified from outside the sandbox through the platform harness: the previous session's host `9501-iy8u55letdgw3pj2zik7m.e2b.app` returned `502 Bad Gateway — Sandbox not found. The sandbox iy8u55letdgw3pj2zik7m wasn't found.` (sandbox destroyed; link died with it, not an app/WS/DNS defect), and the current host `9501-itob6xjzlw38yfqeywv27.e2b.app` returned `403 Forbidden — Missing traffic access token. The sandbox itob6xjzlw38yfqeywv27 requires a traffic access token.` The gate is the `e2b-traffic-access-token` HTTP header (E2B restrict-public-access), which a phone/desktop address bar cannot send. No token exists in the sandbox env; no hosting/tunnel was created and public access was not flipped (Owner consent required). |

In-sandbox egress check (diagnostic): `registry.npmjs.org`, `pypi.org`, `github.com` reachable; `cdn.playwright.dev`, `playwright.download.prss.microsoft.com`, `storage.googleapis.com`, `deb.debian.org` unreachable → **no browser binary can be installed here**, so no new pixel-level visual capture was possible in this session either.

Isolation and data: the app runs on **in-process Mongomock only**, database `logistics_staging`,
with `MONGO_URI` blanked; `STAGING_ISOLATION_PROOF=PASS transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO production_client=NO`
was printed before any fixture was written. No real MongoDB, no production credentials, no customer
data. The reviewed launcher fails closed if a real URI/secrets path is present.

## 4. Pre-handover checks actually performed

| Owner check | Verdict | Evidence in this session |
|---|---|---|
| App starts for real | PASS | AppTest run of the exact launcher: `APP_BOOT_EXCEPTIONS=0`, after `STAGING_ISOLATION_PROOF=PASS`; live server healthy on `:9501`. |
| Vietnam / Biển Đông / Hoàng Sa / Trường Sa background appears | PASS (asset + wiring) | `component/src/assets/journey/vietnam-east-sea-chart.webp` rendered here and read back: labels `VIỆT NAM`, `BIỂN ĐÔNG`, `Quần đảo Hoàng Sa (Việt Nam)`, `Quần đảo Trường Sa (Việt Nam)`. It is referenced as the Journey map background (`JourneyMap.tsx`: `backgroundImage: url(chartPaperUrl)`) and is inlined in the reviewed bundle (`component/dist/logi-shell.js` contains the chart). New pixel capture in this host: not possible (no browser binary) → no new visual PASS claimed. |
| `T6-FCL` shows the full Journey, not split in half | PASS | Canonical view-model built over the trial fixtures: `nodes=11` (`booking, pickup, customs-export, si-vgm, gate-in, etd, on-board, transit, arrival, customs-import, delivery`), `edges=11`; `data-empty-journey` absent, so the shell renders the populated map-first Journey (no `journey-map-rail`) rather than the zero-node full-width exception. |
| `SEA-188` shows "no Journey yet" | PASS | Created through the canonical `shipment_create` path: `journeyNodes=0`, `profileState=PROFILE_INCOMPLETE`, `serviceScope=[]`, `serviceScopeConfirmed=false`, `incoterm=""`, `transportLegs=0`, primary action "Bổ sung hồ sơ thực hiện lô". |
| Clicking a node opens the right bubble and form | PASS (component contract) | Reviewed-bundle DOM acceptance on `component/dist/logi-shell.js` at this HEAD: zero-node `nodes=[]` variant and missing-`journey` variant both PASS ("one CTA reaches Execution Profile through Global Workspace, zero business writes"); `dom_hook_transition_197.mjs` PASS in both directions on the same mounted instance; node → bubble → stage workspace paths are asserted in the reviewed `dom_acceptance_journey_demo_fidelity.mjs` / `..._logi197_journey_clarity.mjs` lanes (not re-run here: their fixtures were captured before this task). Real-browser node/bubble evidence of record remains the reviewed G2 capture. |
| Save and read back on test data, nothing written to production | PASS | Through the real dispatcher on isolated Mongomock: task-editor write `shipment_sea_facts_save` for `T6-FCL` ON BOARD field `on_board_at` = `2026-10-04` → `ok=true`, version `1 → 2`, readback `'2026-10-04'` (matches), Journey still `11 nodes / 11 edges`, transport still `SANDBOX_STAGING`. |
| Simple way to stop the app | PASS | Preview: **Control + C** in the sandbox process UI (or the platform stop control). Trial launcher: close the window or **Control + C**. In-memory Mongomock data disappears on stop. |

## 5. Not verified here (explicit)

- No new real-browser (pixel/DOM-in-browser) capture in this host: `BROWSER_CAPABILITY=UNAVAILABLE`
  (no Chromium/Playwright binary). Visual evidence of record stays the reviewed G2 capture; nothing
  in this session overrides or re-labels it.
- macOS launcher runtime: NOT_RUN (Linux-only host). Logic and guards were executed here; the macOS
  double-click, Gatekeeper prompt, and Python install path were not.
- Windows launcher: still NOT_RUN (as in the reviewed evidence).
- The private preview URL's external reachability is provided by the platform; verified from the
  inside only as a healthy local server on `0.0.0.0:9501`.
- Business-module breadth (finance, partner payables, auth/RBAC coverage gaps) is out of scope and
  unchanged; no Owner UAT, merge, promotion, or production deploy is claimed.

## 6. OE gate

`SIMPLER_PATH=YES` (runs the existing reviewed launcher and existing bundle; reuses the existing
in-memory staging transport, no new service, no cloud spend, no new access). `MATERIAL_PROGRESS=YES`
(Owner can open and use the app now). `NECESSITY=YES` (the Owner's single stated goal). `CORE_BEFORE_SUPPORT=YES`
(app first; documentation afterwards, minimal). `SMALLER_VERIFIABLE_SLICE=YES` (health + real dispatcher
readback + data/map presence; no full-suite ceremony, no G0–G5 rerun, no new browser stack).
`OE_VERDICT=DO_IT`; `SKIP_IT` for any new tunnel/host/deployment or UI change.

## 7. Learning reconciliation

`LEARNING_RECONCILIATION=NONE` — routine delivery/handoff work; no repeated or material failure and no
newly reusable correction beyond the already-ACTIVE record consumed above.

## 8. Access repair (Owner report: "link không mở được")

Owner-reported failure was reproduced and explained from **outside** the sandbox, not from `localhost`:

| Probe (external, via the platform harness) | Result |
|---|---|
| `https://9501-iy8u55letdgw3pj2zik7m.e2b.app/` (the link handed over previously) | `502 Bad Gateway — "Sandbox not found. The sandbox iy8u55letdgw3pj2zik7m wasn't found."` |
| `https://9501-itob6xjzlw38yfqeywv27.e2b.app/` (this session's sandbox) | `403 Forbidden — "Missing traffic access token. The sandbox itob6xjzlw38yfqeywv27 requires a traffic access token."` |

Failure classification (the Owner's question 2):

- **Sandbox expired / replaced** — PRIMARY CAUSE of the reported failure. `E2B_SANDBOX_ID` changed from
  `iy8u55letdgw3pj2zik7m` to `itob6xjzlw38yfqeywv27`; the preview host embeds the sandbox id, so the old
  host is permanently gone. The old app process and `.venv` were gone with it.
- **Access control (private, token-gated)** — SECONDARY, permanent for this environment: the sandbox is
  created with restricted public traffic. Every request must carry the `e2b-traffic-access-token` header.
  A URL opened by a phone/desktop browser cannot send that header → a bare link can never work, regardless
  of the app being healthy.
- **Not the causes:** Streamlit health (`/_stcore/health` = `200 ok`), DNS (both hosts resolve; the
  platform answers with typed 502/403 pages), TLS, and the app itself (`APP_BOOT_EXCEPTIONS=0`).
  WebSocket/React rendering could not be blamed or cleared because no browser can exist in this sandbox
  (browser-download hosts are unreachable); this is stated as a limit, not as a pass.

Actions taken (in the Owner's preferred order — "smallest path that works", no new hosting, no cost, no
new access): withdraw the dead link, rebuild the environment from the exact reviewed revision, and deliver
a **self-contained one-click trial package** that does not depend on any sandbox or token:

1. Restored the trial branch to the reviewed revision: fetched `origin`, hard-reset
   `arena/3851e3be-logistics-work-desk-arena` to the pushed trial HEAD `07f90d4`
   (= reviewed HEAD `7ef144c` + launchers + docs), worktree clean, and re-derived the reviewed bundle
   identity (`logi-shell.js` `3b650f8f…`, `logi-shell.css` `412f27aa…` — match).
2. Re-ran the trial app on the current sandbox for the in-session preview panel
   (`0.0.0.0:9501`, Mongomock only, `AUTH_REQUIRED=false` for this staging launcher only).
3. Built `LOGI199-GOI-DUNG-THU.zip` (5.2 MB, 382 entries) and proved it by fresh extraction →
   launcher → `.venv` install → app up on a free port → `APP_BOOT_EXCEPTIONS=0` →
   `T6-FCL` 11/11 `PROFILE_READY`, `SEA-188` 0 nodes `PROFILE_INCOMPLETE`.
4. Added `HUONG-DAN-DUNG-THU.txt` (Vietnamese, in-package) and `MO-APP-DUNG-THU-WINDOWS.cmd` (thin shim
   onto the existing `scripts/logi199_uat.cmd`); no application, component, auth, or production code changed.

Owner-facing access verdicts: `OWNER_PREVIEW_ACCESS=BLOCKED` for a bare URL (proved externally by the 403
token gate), `NOT_VERIFIED` for the platform preview panel, `PASS` for the self-contained package on
Linux (macOS runtime `NOT_RUN`). Lifetime note recorded for the Owner: the preview link lives only while
this session's sandbox lives (and only through the platform panel); the downloaded package has no such
expiry.
