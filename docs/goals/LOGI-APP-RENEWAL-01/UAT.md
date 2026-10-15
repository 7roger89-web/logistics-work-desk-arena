# LOGI #199 — bounded G2 Owner UAT guide (not currently ready)

**Current gate:** `INDEPENDENT_REVIEW=PENDING`; `OWNER_UAT_READY=NO`; `OWNER_UAT=NOT_RUN`; `PRODUCTION_READY=NO`. Do not start this Owner UAT until Independent Review explicitly returns PASS for the exact candidate and its disclosed source/evidence reconciliation. This file is a focused LOGI #199 follow-up, not a restart of accepted G0–G5 work.

## Exact review candidate and evidence

- Fixed branch: `arena/bb243332-logistics-work-desk-arena`
- Source candidate commit: [`1e899553cc1ad7dbd720eb805e061ec61ae0871a`](https://github.com/7roger89-web/logistics-work-desk-arena/commit/1e899553cc1ad7dbd720eb805e061ec61ae0871a)
- [Download the exact candidate ZIP](https://github.com/7roger89-web/logistics-work-desk-arena/archive/1e899553cc1ad7dbd720eb805e061ec61ae0871a.zip) only after the reviewer authorizes UAT.
- Sole visual reference: `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html` (SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`).
- Current browser evidence: `evidence/logi-199-g2/current-source/` and `evidence/logi-199-g2/metrics.json`.
- **Evidence identity note:** raw metrics record capture source SHA `751f64f5129637eef4fb74515afdf7fa15ca9deb`. GitHub returned 422 and the resumed clone did not contain that commit object. The published candidate rebuilds to the exact recorded JS/CSS and capture-script hashes, but commit-ID identity equivalence is **NOT_VERIFIED**. Independent Review must accept this provenance or request a fresh capture before Owner UAT; the raw metrics are not to be relabeled.

## When authorized by Independent Review

1. Use a **new, isolated folder** for the exact candidate ZIP. Do not copy any app-production configuration, `.env`, `secrets.toml`, Mongo URI, cookies, or credentials.
2. On Windows with Python 3.11+, run `scripts/logi199_uat.cmd`. It is a Windows batch launcher. Its runtime was not executed in the Linux sandbox; a real Windows launch is part of the Owner check. If the isolation guard fails, stop and preserve the log—do not disable or edit the guard.
3. Verify the launcher reports isolated in-process Mongomock, empty real `MONGO_URI`/secrets, and no production client before fixture creation. Open `http://localhost:9501`. Do not use production login, production data, or production ports.
4. Use only the supplied disposable fixtures: `SEA-188` for no Journey nodes, and `T6-FCL` for the populated Journey/touch/save check. The Mongomock store is in-memory and disappears when the launcher stops.
5. Stop the launcher with Ctrl+C when finished. Record only the checklist below, screenshots, and the test result; do not create real transactions or alter production data.

## Focused Owner checklist

| Check | Action | Expected result / record |
|---|---|---|
| SEA-188 empty map, desktop 1440×900 | Open the no-node Journey view and try drag/wheel input inside the map. | Full-width map-first canvas; zero nodes/edges and no fabricated stages/statuses; truthful missing-profile state; one “BỔ SUNG HỒ SƠ” CTA; map transform does not pan/zoom while there are no nodes; no horizontal overflow. Record PASS/FAIL and screenshot. |
| SEA-188 empty map, mobile 390×844 | Repeat on a phone-sized viewport; tap the CTA. | Full-width map; no overflow; exactly one truthful CTA reaches the existing Execution Profile editor; no business write occurs merely by opening the editor. Record PASS/FAIL and screenshot. |
| T6-FCL populated Journey, desktop/mobile | Confirm 11 real fixture nodes and 20 edges; on mobile, use touch drag to pan to ON BOARD. | Existing map-first populated Journey remains intact; touch pan moves the map and does not accidentally select a node until tapped. Record whether touch-pan works. |
| T6-FCL ON BOARD save/readback | Open the existing task editor, enter disposable test date `2026-10-04`, save, reload, and read it back. | The Mongomock fixture returns the exact saved date after reload. No real payment/transaction. Record save and readback separately; if the immediate confirmation label is absent, do not infer failure or success—use the reload/readback result. |
| Isolation and shutdown | Review the launcher preflight log and stop it. | Isolation proof precedes fixture creation; no production DB/client/credentials; in-memory data is gone when stopped. |

The reviewer's source-SHA reconciliation decision is a prerequisite. The Owner's result does not replace Independent Review, and screenshots do not authorize merge or deployment.

## Current release boundary

- `INDEPENDENT_REVIEW=PENDING`
- `OWNER_UAT_READY=NO`; `OWNER_UAT=NOT_RUN`
- `SUPERVISOR_PASS=NOT_CLAIMED`
- `PRODUCTION_READY=NO`
- `NO_MERGE_MAIN_WITHOUT_OWNER_APPROVAL=YES`
- `NO_PRODUCTION_DEPLOY_WITHOUT_OWNER_APPROVAL=YES`

Existing auth/bootstrap/finance coverage and snapshot retry-idempotency blockers remain separate and unwaived. GitHub issue-comment permission is not a release gate; no permission fix is requested.
