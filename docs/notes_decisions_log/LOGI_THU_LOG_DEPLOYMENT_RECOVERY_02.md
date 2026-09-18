# LOGI_THU_LOG_DEPLOYMENT_RECOVERY_02 — thu-log deployment identity evidence

`TASK_ID=LOGI_THU_LOG_DEPLOYMENT_RECOVERY_02` · `DATE=2026-09-18` ·
`P2P_LAW_SOURCE=LOCAL_PORTABLE` · `TARGET_APP=thu-log` · `FORBIDDEN_APP=tienthanhlog`

**Status: `THU_LOG_DEPLOYED_RUNTIME_UNVERIFIED`.** Independent establishment of
the deployment mapping failed (§2–§5) and Arena has no provider session, so the
runtime half of this task could not be executed from here. The Owner then
attested `thu-log.streamlit.app` as the target app (§7), which unblocks the
identity *question* by Owner authority only — not by independent verification —
and leaves `Reboot app` + the five-point smoke as Owner-side actions.

Terminology used in this note: `INDEPENDENT_PROOF` = evidence this executor
reproduced itself; `OWNER_ATTESTED` = the Owner's own statement about their
deployment, recorded verbatim, never presented as independent proof.

This note is evidence only. It supersedes the (Owner-invalidated) app
association recorded in `docs/notes_decisions_log/LOGI_UAT_REAL_USE_REPAIR_02.md`
§ Deployment. That section is left untouched as historical record; do not reuse
its app association.

---

## 1. Fresh baseline verification (independent, read-only)

| Check | Method | Result |
|---|---|---|
| `main` SHA | `git ls-remote origin refs/heads/main` + GitHub API `commits?sha=main` | `c8f3fbc501a9b0a743e27e876c0bde683453aaa9` — matches `EXPECTED_MAIN` |
| Local `HEAD` | `git rev-parse HEAD` | `c8f3fbc5…` |
| Forbidden app | no deploy/restart/settings/branch/secret action taken | `FORBIDDEN_APP_TOUCHED=NO` |

## 2. Deployment identity ledger for `thu-log`

| Field | Value | Evidence class |
|---|---|---|
| `THU_LOG_APP_URL` | `https://thu-log.streamlit.app/` | `OWNER_ATTESTED` (2026-09-18, §7) — not independently proven |
| `THU_LOG_REPO` | **UNVERIFIED** — only candidate in this repo: `7roger89-web/logistics-work-desk-arena` | no source names it |
| `THU_LOG_BRANCH` | **UNVERIFIED** — only candidate: `main` | no source names it |
| `THU_LOG_ENTRYPOINT` | **UNVERIFIED** — repo has *two* launchers (`app.py`, `web_app.py`); the Cloud main-file is a provider setting, not a repo fact | no source names it |
| `THU_LOG_CURRENT_REVISION` | **UNVERIFIED** | no provider/runtime read surface |
| `THU_LOG_IDENTITY_PROOF` | `OWNER_ATTESTED` (independent proof: NONE) | §7, §2a |
| `DEPLOYMENT_PATH` | **UNVERIFIED** | one repo-level Streamlit hook exists, but it does not name its app (§3) |

### 2a. What the anonymous probes do and do not prove

Probes were made through a platform-side fetcher (not the sandbox), because the
sandbox cannot open TLS to these hosts (§4).

| URL | Observed final route | Read |
|---|---|---|
| `https://thu-log.streamlit.app/` | `share.streamlit.io/app/thu-log/` — sign-in wall | **registry hit**: the name resolves to an app route |
| `https://thu-log.streamlit.app/_stcore/health` | `…/app/thu-log/_stcore/health` | route preserved (app-scoped routing, not the generic error route) |
| `https://thulog.streamlit.app/` | `share.streamlit.io/errors/not_found` | name-specific, not pattern-generic |
| `https://zz9-random-name-4488.streamlit.app/` | `…/errors/not_found` | control |
| `https://qwerty1234zz.streamlit.app/` | `…/errors/not_found` | control |
| `https://definitely-not-an-app-zzz123.streamlit.app/` | `…/errors/not_found` | control |
| `https://logisticspro-1.streamlit.app/` | `…/errors/not_found` | that name no longer exists (the LG/REL-era preview app) |
| `https://tienthanhlog.streamlit.app/` | app shell served, "Created by 7roger89-web" | public app, **forbidden target — used only as a calibration control** |
| `https://logistics-truongthanh-roger89.streamlit.app/` | shell + "This app has gone to sleep" | public app control |
| `https://share.streamlit.io/user/7roger89-web` | 3 **public** apps listed: `tienthanhlog`, `vnlawer`, `logistics-truongthanh-roger89` | `thu-log` is not in the public inventory |

**Conclusion (honest boundary):** the name `thu-log` exists in Streamlit
Community Cloud, but the app is not anonymously viewable and no anonymous
surface exposes **owner, repository, branch, main file, or revision**. App-name
similarity is explicitly not identity proof (`TARGET_APP_NAME != IDENTITY_PROOF`),
and the Owner-provided prohibition on guessing the URL is respected: the probe
result is reported as a registry hit, **not** as `THU_LOG_APP_URL`.

### 2b. Repository/history search (complete for this repository)

- All **70** remote branches and all **384** commits were fetched and searched.
- Every `*.streamlit.app` reference ever committed: `tienthanhlog.streamlit.app`
  and `logisticspro-1.streamlit.app` only.
- The **only** occurrence of `thu-log` in the entire repository history is a
  prose aspiration: `reports/coder/rp_coder_260914_120000_…-01.md:74`
  ("Live proof belongs on thu-log after merge.", introduced by `f16e681`).
  That proves an intended target *name*, not URL/repo/branch/entrypoint.
- No `README`/badge/config/doc anywhere records a `thu-log` URL; `.streamlit/`
  contains only `config.toml` + `secrets.toml.example` (no app identity).
- Issues/PR bodies and comments: no `thu-log` reference.
- Only repo-handled deployment artifact in history: `.github/workflows/logi-pilot-copy-once.yml`
  (deleted; one-time Atlas pilot copy, unrelated to Streamlit deployment).

## 3. The one deployment mechanism that *does* exist here (and its limit)

`7roger89-web/logistics-work-desk-arena` carries exactly **one** active webhook:
`https://share.streamlit.io/hook` (id `678055509`, created `2026-09-12T06:53:16Z`,
event `push`). Recent deliveries, including the `main@c8f3fbc` push:

| Delivery | guid | result |
|---|---|---|
| `2026-09-17T15:49:22Z` (c8f3fbc) | `59a364d0-b2af-11f1-8fe1-cf3013c29525` | `200 OK` |
| `2026-09-17T15:47:28Z` | `157b4dd6-b2af-11f1-8689-f6f8833c43bb` | `200 OK` |

The hook is **app-agnostic**: generic URL, masked secret, `installation_id=null`,
no app identifier in listings or delivery objects. GitHub's `deployments`
endpoint returns `403 Resource not accessible by integration`. Control Tower
already recorded the same limit in the PR #52 review: *"Unknown: which Streamlit
app/environment and branch the hook serves."* A `200` here is transport success,
not proof that any named app rebuilt (`TRANSPORT_SUCCESS != DEPLOYMENT_SUCCESS`).

Circumstantial only (recorded, not promoted to proof): the hook was created
2026-09-12T06:53:16Z, ~2.5 min before the PR #22 merge push to `main`.

## 4. Why runtime acceptance could not be performed

| Capability | Observed |
|---|---|
| Sandbox TLS egress to `*.streamlit.app` / `share.streamlit.io` | blocked (`curl` rc=35) |
| Sandbox TLS egress to `api.github.com` | allowed (used for all GitHub evidence) |
| Chromium/Playwright binary | none installed |
| Streamlit Community Cloud credential (`~/.streamlit`, env, repo secrets) | none — no provider integration exists for this executor |
| App viewer access | sign-in wall (private) |
| `.streamlit/secrets.toml` (app login) | absent |

Therefore smokes **A–F** (app load, login boundary, customer create, contract
create → real detail, slash-safe `05/2026/HDMB`, `XỬ LÝ NGAY`, `MỞ CHỨNG TỪ`)
are all `NOT_PERFORMED` → `RUNTIME_TARGET_VERIFIED=NO`.

## 5. Precise missing evidence / authority

1. **Provider-side identity (primary blocker).** The app↔repo mapping
   (`Repository`, `Branch`, `Main file path`) is readable only in the app's
   Settings on `share.streamlit.io` under an authenticated Owner session.
   Arena has no Streamlit credential or integration, and the app is not
   anonymously viewable — so no independent verification of `thu-log`'s mapping
   is possible from here.
2. **Provider-side runtime read/write (secondary blocker).** Even with identity
   proven, both `Reboot app` and the employee-path smoke require the Owner's
   authenticated browser session.

### Smallest unblock (Owner, ~30 seconds)

On `share.streamlit.io` → app `thu-log` → **⋮ → Settings**, read:

```text
Repository     = ?
Branch         = ?
Main file path = ?
```

If those read `7roger89-web/logistics-work-desk-arena` / `main` / `app.py`, then
the mapping is established and `main@c8f3fbc` is already delivered (push hook
`200` at `2026-09-17T15:49:22Z`); a `Reboot app` is the only remaining action,
after which the five-point smoke can be run in that browser.

Do **not** re-associate this hook with `tienthanhlog`, and do not create a new
app or a no-op commit as a workaround.

## 6. Mutation ledger

`PRODUCTION_DATA_MUTATED=NO` · `PILOT_MUTATED=NO` · `SECRETS_CHANGED=NO` ·
`INFRASTRUCTURE_CHANGED=NO` · `DEPLOYMENT_MUTATION=NO` · `MAIN_MOVED=NO` ·
`FORBIDDEN_APP_TOUCHED=NO` (no deploy/restart/settings/branch/secret action;
one anonymous read-only GET to the forbidden app's public URL was used only as a
calibration control and is disclosed here).

`INDEPENDENT_IDENTITY_VERDICT=BLOCKED_DEPLOYMENT_IDENTITY` (unchanged — no
independent mapping evidence exists).

## 7. Owner attestation and the remaining Owner-side action (2026-09-18)

Asked how to proceed while identity rested on a provider value only the Owner's
account can read, the Owner selected:

> **"Treat thu-log.streamlit.app as the target (Owner attestation)"**

Recorded exactly as `THU_LOG_IDENTITY_PROOF=OWNER_ATTESTED`, which is
`TARGET_APP=thu-log` confirmed by the deployment's owner. It is **not**
independent verification, and it does not assert `repo` / `branch` /
`main file path` — those remain unread (§5, item 1). It also does not relax any
mutation boundary: no secret, database, infrastructure, app identity or
deployment-architecture change is implied.

Consequence: the code half is already delivered — `main@c8f3fbc` was pushed
`2026-09-17T15:49:21Z` and the repository's only deployment artifact, the
Streamlit Cloud push hook, answered `200 OK` at `15:49:22Z`. Nothing further was
pushed, and no no-op commit was manufactured. What remains cannot be done by an
executor without a provider session.

### Owner-side handover — smallest runtime acceptance on the real app

1. `share.streamlit.io` → app **`thu-log`** → **⋮ → Reboot app** (only if the app
   is not already serving the post-`2026-09-17` build). Optional but useful:
   while in that menu, read `Settings → Repository / Branch / Main file path`
   and paste them here, which converts `OWNER_ATTESTED` into verified identity.
2. Then, in the app itself (read-mostly, no meaningful production data needed):
   - **A — App + login boundary:** app loads; unauthenticated visit shows the
     login screen, not the dashboard.
   - **B — Customer create:** on `Khách Hàng`, create/persist a customer — success
     appears **only after** the authoritative readback; a rejected/failed write
     must not report success.
   - **C — Contract create:** `Hợp đồng → tạo mới` must continue to the **real
     contract detail**; the `Sắp có` placeholder (unbuilt-screen badge) must not
     appear for a created contract.
   - **D — Slash-safe id:** open contract `05/2026/HDMB` (the id PR52 committed in
     the workflow fixture) — real detail, not `*`/NotFound.
   - **E — `XỬ LÝ NGAY`:** from `Việc Cần Xử Lý`, the button follows
     `nextRoute = /lo-hang/{sid}?tab={tab}` and lands on the **canonical
     next-work tab** for that task (hyphenated id, e.g. `lay-hang`, `tai-chinh`,
     `van-tai`, `chung-tu`, `lich-su`), not the wildcard and not a neighbouring tab.
   - **F — `MỞ CHỨNG TỪ`:** on a shipment with a linked contract, the button
     opens `contractPath(id) + "?tab=chung-tu"`, i.e. `ContractDetail`'s
     `Chứng từ HDNT/PL/HDMB` tab (the `core.docgen` workdesk), not the wildcard.

Any failure in B–F is a **code** finding against `main@c8f3fbc` and belongs in a
new evidence note; it must not be attributed to the deployment path.

**`FINAL_VERDICT=THU_LOG_DEPLOYED_RUNTIME_UNVERIFIED`**
`PROVIDER_AUTH_SUBBLOCKER=YES` — `Reboot app` and the smoke both require the
Owner's authenticated `share.streamlit.io` / browser session; Arena holds no
provider credential and the app is not anonymously reachable.

## 8. Continuation round — Owner credential offer vs. available mechanisms (2026-09-18)

The Owner authorized use of credentials supplied "through Arena's supported
secure authentication/credential mechanism". That route was checked before
acting on it, and it does not exist for this task:

| Requirement | Observed in this executor |
|---|---|
| Arena secure credential-entry surface | **none** — no vault, broker, mounted config or credential service (`~/.arena`, `/etc/arena`, `/opt/arena` absent; only `GH_TOKEN`/`GITHUB_TOKEN` env names; listening services are sshd/rpcbind only) |
| Interactive surface available | chat text only — which this task forbids using for passwords, 2FA codes, recovery codes, tokens or secrets, and which must not be used for credentials in any case |
| Provider programmatic auth (API/CLI) | **none exists** — Streamlit Community Cloud app management (Reboot, Settings, logs, Auto-deploy) is documented as **UI-only** at `share.streamlit.io` / the app's own "Manage app" panel; deployment is driven by GitHub pushes |
| Network path to the provider | **blocked** — sandbox TLS egress to `*.streamlit.app` / `share.streamlit.io` fails (`curl` rc=35); only `api.github.com` is reachable |
| Browser automation | **none** — no Chromium/Playwright binary or module |

Consequence: a credential would not create an action surface here, and no
credential was requested or accepted. The remaining actions are provider-session
actions by construction — not code or evidence failures.

### Optional read-only diagnostic (Owner's call, not required)

Flipping app `thu-log` viewer access to *Anyone with the link* temporarily would
let an anonymous fetch read the app's own attribution line ("Created by …"), which
is the only independent owner attribution reachable without a session. It does
**not** reveal repo/branch/main-file, does **not** substitute for B–F, and should
be reverted afterwards. Not required for the deployment path; the app's own login
boundary still protects data.

**`FINAL_VERDICT=BLOCKED_DEPLOYMENT_AUTH`** — identity is Owner-attested, the
integrated revision is already delivered through the repository's existing push
hook, and every remaining step (Settings read, `Reboot app`, live UAT) requires an
authenticated provider session in a real browser.
