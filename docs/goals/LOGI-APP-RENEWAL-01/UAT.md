# LOGI #199 — Frozen 8932fcb — isolated Windows Owner trial

`INDEPENDENT_REVIEW=PASS_BOUNDED_A_B_PAPER`;
`OWNER_UAT_READY=YES_FOR_ISOLATED_WINDOWS_STARTUP_AND_UAT`;
`OWNER_UAT=NOT_RUN`; `WINDOWS_RUNTIME=NOT_RUN`; `PRODUCTION_READY=NO`.

Independent ChatGPT Control Tower review of the frozen source/build and archived
Chromium evidence is published at
[`INDEPENDENT_REVIEW_RESULT-8932fcb.md`](../../../evidence/logi-199-owner-delivery/INDEPENDENT_REVIEW_RESULT-8932fcb.md).
The reviewer is a separate actor from the Arena code writer; no new live browser
was executed by that reviewer. The PASS covers only camera A, save/readback B and
Owner paper preservation, NOT Windows OS, full-UI parity or production readiness.

This guide authorizes starting an isolated **local Windows trial** using only
disposable sample data. Do NOT merge main, deploy, use real customer data, or
waive other business/security release gates.

## Frozen app version

- Branch: `arena/d657fb56-logistics-work-desk-arena`.
- Exact app source/dist: **8932fcb4aa2e7705b1e0963a830758bd3d9849ae**.
- [Exact source archive (GitHub login may be required)](https://github.com/7roger89-web/logistics-work-desk-arena/archive/8932fcb4aa2e7705b1e0963a830758bd3d9849ae.zip).
- Do NOT use `logi199-owner-trial`: annotated tag currently resolves to
  `353314484fc52b5d706a90e84d9bbb514e1cfa33`, not this candidate. No retagging or
  release was performed.
- Only evidence at `evidence/logi-199-final-fix/` in **8932fcb** is the A/B review
  input. Documentation commits after that SHA do not change the frozen app.
- Original offline HTML: `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`,
  SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.

## Independent review and web-link status

Historical writer state: no independent reviewer available in the Arena session;
GitHub Issue #199 comment write failed with `Resource not accessible by integration`.
This is **superseded for A/B/paper** by the separate, immutable-SHA ChatGPT
Control Tower review file linked above. Its evidence review is source/artifact
based, not a new live-browser run; no Owner Windows run has occurred.
The failed Issue comment is NOT a release or trial blocker.

No authenticated private web app with outside-sandbox verification is available.
No e2b trial link is being offered, no auth-disabled public app was published,
and no hosting or paid service was created. A new host would need Owner approval
and real authenticated/external-access verification before it could be offered.

## Windows instructions — maximum three steps (pilot permitted; Windows NOT_RUN)

Target selected by Owner: **Windows**. Requirements: Windows x64, working
CPython **3.11 x64** on PATH, venv/pip, Internet access to install dependencies,
ability to execute a `.cmd`, and free local port **9501**. Node/npm and MongoDB
installation are not needed (official dist included, in-memory Mongomock).
Direct dependency wheels were checked for CPython 3.11 / Windows amd64 from
Linux; a full Windows dependency installation and Windows browser launch remain
**NOT_RUN**. Do not interpret this as Windows PASS.

Independent scoped review PASS is now recorded for exact `8932fcb`; to START local Windows UAT:

1. Ensure Python 3.11 x64 is installed with **Add python.exe to PATH**, and
   Internet access is available for the initial dependency installation.
2. Extract `logi199-8932fcb-source-candidate.zip` (or the exact GitHub archive
   above) into a **new writable folder**. Do not add `.env`, secrets,
   production configuration or credentials. Do not run directly inside the ZIP.
3. Double-click **`scripts\logi199_uat.cmd`** inside that folder. Keep its
   console open; after startup open **http://localhost:9501** in your browser.
   It must report `STAGING_ISOLATION_PROOF=PASS ... client=Mongomock ...
   real_uri=NO production_client=NO`. If it stops or this proof is absent,
   stop and retain the error; do not bypass the guard. Ctrl+C stops the local
   server; all test edits disappear on shutdown.

The auth bypass is the unchanged test-only launcher setting and is bound to
**127.0.0.1 only**. Never rebind it publicly, tunnel it, or use production data.
This is a local single-user trial, not an authenticated hosted environment.

## Focused Owner checklist — after successful local Windows start

- T6-FCL at 390×844: initial BOOKING → PICKUP → CUSTOMS EXPORT, 11 nodes / 20
  edges; paper/grid unchanged; pan/zoom/Fit; `Đọc rõ` reaches a real problem;
  select node → bubble → editor.
- ON BOARD: record current OLD date, enter a valid different NEW, Save, reload,
  reopen editor, verify persisted NEW and OLD != NEW. Same-value save is not PASS.
- Record Windows/Python version, startup/isolation log and screenshots. This is
  Owner UAT evidence, separate from reviewer and Linux evidence.

## Actual checks completed / remaining blockers

Author ran the **new ZIP after extraction**, not just the live checkout, on
Linux x86_64 / Python 3.11.2 / real Streamlit / Chromium / loopback / Mongomock.
A PASS: mobile begins booking/pickup/customs-export, focus and pan/zoom/Fit.
B PASS: isolated `2026-10-04 → 2026-10-11`, Save → reload → readback NEW.
Archive: 1,564 tracked files matched blobs at exact 8932fcb, dist/HTML/JPEG hashes
verified. This is author smoke evidence, NOT independent review or Windows PASS.
See `evidence/logi-199-owner-delivery/`.

Independent scoped review has now PASSED; remaining Owner trial tasks are
Windows launcher execution, seeing `STAGING_ISOLATION_PROOF=PASS`, and actual
Owner interaction/feedback. No external private browser URL was verified.
This candidate is authorized for **local isolated Owner trial only** and is
NOT a full-app/production release. The official production release remains blocked.
Production additionally needs explicit Owner authorization and resolution of the
existing, unwaived release blockers; this bounded review does not certify the
whole app, auth/bootstrap, finance or retry-idempotency.
