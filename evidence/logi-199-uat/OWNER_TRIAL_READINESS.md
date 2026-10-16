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
| 1 | Private platform preview of this sandbox (`https://<port>-<sandboxId>.e2b.app`) bound to the running app | Real process: `.venv/bin/python -m streamlit run scripts/logi199_t6_staging_app.py --server.port 9501 --server.address 0.0.0.0`; `GET /_stcore/health` → `200 ok`; `GET /` → `200` with no `X-Frame-Options`/CSP frame-ancestors. Reachability of the proxied URL itself is platform-provided and cannot be re-verified from inside this sandbox. |
| 2 | `MO-APP-DUNG-THU-MAC.command` (double-click trial launcher for macOS) | New file, no app logic rewritten. `bash -n` syntax OK; real end-to-end run on this Linux host: created/reused `.venv`, installed requirements, refused when `.streamlit/secrets.toml` was present (tested in `/tmp`), picked a free port (9501 busy → 9502), started the app, `GET :9502/_stcore/health` → `200`. The macOS-only `open` call is guarded and not part of the pass/fail path. **macOS runtime itself: NOT_RUN** (no macOS host available). |
| 3 | Existing Windows launcher `scripts/logi199_uat.cmd` (from reviewed HEAD) | Reused unchanged; not rewritten. Windows runtime was already recorded as NOT_RUN in the reviewed evidence and remains so. |

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
