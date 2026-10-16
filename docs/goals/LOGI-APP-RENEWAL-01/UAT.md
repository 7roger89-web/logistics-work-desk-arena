# LOGI #199 — Owner delivery candidate 8932fcb (NOT YET UAT-APPROVED)

`INDEPENDENT_REVIEW=INCOMPLETE`; `OWNER_UAT_READY=NO`; `OWNER_UAT=NOT_RUN`;
`WINDOWS_RUNTIME=NOT_RUN`; `PRODUCTION_READY=NO`.

This corrects stale candidate links in the old guide. It does NOT authorize
Owner UAT or waive the independent-review gate. Final approved-trial promotion
is blocked until a genuinely separate reviewer returns PASS on the frozen SHA.
No G0–G5 recertification, product redesign, main merge or production deployment.

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

## Review dispatch and web-link status

No independent agent/tool is exposed in this session; native reviewer CLIs are
absent. GitHub collaborator list contains only Owner. A handoff was prepared in
`evidence/logi-199-owner-delivery/INDEPENDENT_REVIEW_REQUEST.md`. Attempt to post
it to issue #199 failed (`Resource not accessible by integration`, exit 1).
**No reviewer was actually assigned/notified; no independent PASS exists.**
Owner/Control Tower must send that handoff to an available separate reviewer.
This is a permissions/delegation blocker, not a request for credentials.

No authenticated private web app with outside-sandbox verification is available.
No e2b trial link is being offered, no auth-disabled public app was published,
and no hosting or paid service was created. A new host would need Owner approval
and real authenticated/external-access verification before it could be offered.

## Windows instructions — maximum three steps (gated draft)

Target selected by Owner: **Windows**. Requirements: Windows x64, working
CPython **3.11 x64** on PATH, venv/pip, Internet access to install dependencies,
ability to execute a `.cmd`, and free local port **9501**. Node/npm and MongoDB
installation are not needed (official dist included, in-memory Mongomock).
Direct dependency wheels were checked for CPython 3.11 / Windows amd64 from
Linux; a full Windows dependency installation and Windows browser launch remain
**NOT_RUN**. Do not interpret this as Windows PASS.

Once Independent Review PASS is recorded for exactly 8932fcb:

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

## Focused Owner checklist after review + Windows launch succeed

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

Blocking final Owner delivery: independent review not dispatched/completed;
Windows runtime/Owner launch unverified; no safe externally verified web link.
Final approved-trial package/release is deliberately not promoted.
Production additionally needs explicit Owner authorization and resolution of the
existing, unwaived release blockers; this bounded review does not certify the
whole app, auth/bootstrap, finance or retry-idempotency.
