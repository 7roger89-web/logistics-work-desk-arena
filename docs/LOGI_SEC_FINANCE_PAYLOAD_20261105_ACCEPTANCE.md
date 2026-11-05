# ACCEPTANCE — LOGI-SEC-FINANCE-PAYLOAD-20261105

TASK_ID=LOGI-SEC-FINANCE-PAYLOAD-20261105
MODE=CONTINUE_IMPLEMENTATION
OWNER_APPROVAL=GRANTED_FOR_BOUNDED_SECURITY_FIX
BASE_HEAD=b0a6734af5c3ecc207530c67d185f2c366a04e8f (origin/main, verified by fetch)
BRANCH=task/LOGI-SEC-FINANCE-PAYLOAD-20261105
DATE=2026-11-05

## Verdict

**KẾT LUẬN: XONG** (bounded payload fix + regression; no merge, no deploy).

The previous executor's runtime finding is now CONFIRMED by execution, not
just source review: before the fix, a Sale session's real
`build_view_model()` payload contained the finance sentinel 123456789 VND
(5 regression tests FAILED before, 11 PASS after on the same tests).

> **Correction round (2026-11-05, after independent review REJECT).**
> The independent review (`~/workspace/pr269-independent-review/
> PR269-INDEPENDENT-REVIEW.md`, VERDICT=REJECT, MERGE_READY=NO) proved
> with distinct sentinels that actual import duty 222222222 and VAT
> 333333333 still reached Sale via `shipments[].importInfo` and the
> `lastWrites` readback, and that Operations received the commercial quote
> without `commercial_view`. This document was updated for that correction:
> §1 (new helpers), §2 (new tests, corrected FAIL-before counts), §4
> (importInfo.tax/vat moved from KEPT to redacted), §5 (doc-error
> corrections), §8 (correction-round evidence). See §8 for the full record.

## 1. Source patch / diff

Two files changed (cumulative vs base `b0a6734`, see §8 for the
correction-round split; `git diff b0a6734 --stat`: logi_view_model.py
+214/−11, test file +634 new, ACCEPTANCE.md +430 new, NEXT.md +16):

- `views/logi_view_model.py` — the ONLY source file touched.
  - `_can_view_finance()` — server payload gate: authenticated session actor
    holds `finance_view` from the single `core/auth.py::ROLE_PERMISSIONS`
    matrix. Fail closed for anonymous (bare `has_permission` alone would
    return True for an anonymous actor via the Viewer fallback).
  - `_can_view_commercial()` (correction round) — same fail-closed shape
    for `commercial_view`.
  - `_restricted_finance()` — restricted per-shipment finance block: keeps
    the commercial quote + currency + UI-safe empty shapes; every
    restricted money figure is None (UNKNOWN, never 0).
    `hasActualLines=False` means "no finance visible to this actor", marked
    by `"restricted": true`. **Correction round:** the quote is copied
    ONLY when the actor holds `commercial_view`; Operations (neither
    `finance_view` nor `commercial_view`) gets `quote: []`.
  - `_restricted_import_info()` (correction round) — importInfo for a
    no-finance actor: declaration identity survives (declaration number,
    dates, customs status, GNT readiness); the two ACTUAL tax money
    figures `tax`/`vat` become None (UNKNOWN, never 0). Returns a new
    dict; the stored shipment document is never mutated.
  - `_redact_getfly_preview()` — GetFly preview money (cost/price/revenue/
    profit in orders, service lines, summary and `normalizedRows`) → None.
  - `build_view_model()` — gate evaluated once per render (after
    `ensure_backend()`, so it describes the actor the render actually
    serves); rows redacted BEFORE any derived projection reads them
    (home, receivables, CEO actuals, attention/control); C2D payables and
    the reconciliation desk NOT built without the gate — the ledger snapshot
    is never consulted, and the empty shape is byte-identical to the
    no-records case (UNKNOWN, never a 0 payable). CEO report and partner
    context inherit redaction from their (redacted) inputs — no second
    redactor, no new permission matrix. **Correction round:** the same
    redaction point also replaces `row["importInfo"]` with the restricted
    block above.
  - `_last_writes_readback()` — write outcomes' full-projection readbacks
    are redacted at the payload boundary (covers stale Admin outcomes
    surviving a role downgrade in the same session). **Correction round:**
    the readback's `importInfo.tax`/`vat` are redacted at the same point.
  - `_getfly_preview_projection()` — money redacted at the payload boundary
    (covers a preview left in session state by a previous role as well as
    the actor's own upload).
- `tests/test_logi_sec_finance_payload.py` — NEW, 13 tests (see §2).
- No change to `core/auth.py` (role matrix untouched), no change to any
  writer, no frontend change, no dist rebuild (React already renders
  `null` money as UNKNOWN via `fmtCcy`/`fmtMillionsCcy`/`fmtPct`).

Full diff: `git diff b0a6734af5c3ecc207530c67d185f2c366a04e8f..HEAD -- views/logi_view_model.py`
(and the new test file). No other files modified.

## 2. Regression tests — FAIL-before / PASS-after on the same tests

Fixture: synthetic shipment `LO-SEC-0306` (clone of seed LO-0306) with
finance sentinel **123456789 VND** in the actual line (price + cost), in a
customer payment, and in a canonical ledger obligation (partner
AGT-PHUANH). Tests run the REAL `build_view_model()` path on the isolated
staging database (mongomock), serializing the finance-bearing payload
sections exactly as the renderer receives them.

Command (venv `~/workspace/venvs/logi-secfix`, Python 3.12.3,
streamlit 1.66.1, all requirements installed):

```
python -m pytest tests/test_logi_sec_finance_payload.py -q -p no:cacheprovider
```

| Run | Result |
|---|---|
| BEFORE fix (base HEAD + new tests only) | **5 failed, 6 passed** — Sale distinguishing test, anonymous, role downgrade, frontend role-selector spoof, UI-shape test all FAILED with the sentinel present in Sale's payload. Authorized-role + writer tests passed, proving the fixture valid. *(Corrected 2026-11-05: the original "5 failed, 5 passed" was an arithmetic slip — the file has 11 tests.)* |
| AFTER fix (same tests) | **11 passed** |
| CORRECTION ROUND — BEFORE fix (source reverted to 08e5a63, new tests kept) | **7 failed, 6 passed** — the 5 above plus the 2 new tests (Operations no-quote/no-tax; customs write-safety). |
| CORRECTION ROUND — AFTER fix | **13 passed** |

The 13 tests (11 original + 2 new in the correction round):

1. `test_sale_payload_contains_no_finance_sentinel` — the distinguishing
   test: Sale payload has no sentinel in shipments[].finance, receivables,
   payables, reconciliation, home, ceoReport, partnerContext, lastWrites or
   getfly; restricted money is None (never 0); stale Admin lastWrites and
   GetFly preview are redacted; Sale still sees shipment id, customer,
   journey, route, status and the BG-0306 commercial quote. **Correction
   round:** also asserts no duty/VAT sentinel (222222222/333333333) in
   shipments[].importInfo or lastWrites readbacks, importInfo.tax/vat None
   with declaration identity kept, and the stored shipment still holds the
   true tax figures after a redacted render.
2. `test_sale_payload_matches_admin_quote` — Sale's quote is byte-identical
   to Admin's.
3. `test_authorized_roles_retain_finance_sentinel[admin|support|viewer]` —
   finance_view holders keep the sentinel in finance, payables and
   partnerContext (no narrowing of the role matrix). **Correction round:**
   also keep the true duty/VAT in shipments and lastWrites readbacks.
4. `test_anonymous_gate_is_fail_closed` — `_can_view_finance()` is False
   with no authenticated identity; standalone helpers redact stale
   lastWrites + GetFly preview under that gate. **Correction round:**
   also redacts importInfo.tax/vat in the stale readback.
5. `test_sandbox_promotes_anonymous_to_staging_actor` — pins pre-existing
   staging behaviour: `ensure_backend()` promotes an empty session to the
   staging SUPPORT actor (production `require_login()` blocks anonymous
   before any build).
6. `test_role_downgrade_same_session_drops_stale_finance` — Support build
   WITH sentinel → same session downgraded to Sale → rebuilt payload has
   no sentinel. **Correction round:** also no duty/VAT sentinel.
7. `test_frontend_role_selector_cannot_bypass_server` — spoofed client-side
   role keys do not change the server actor (`user.role == "SALE"`) or the
   payload. **Correction round:** also no duty/VAT sentinel.
8. `test_restricted_finance_shape_is_ui_safe` — restricted block keeps the
   keys React dereferences directly (`actual`, `payments`, `quote`,
   `currency`, `partner.payments`). **Correction round:** also asserts
   importInfo.tax/vat None with `declarationNo` present.
9. `test_finance_writers_and_ledger_outcomes_unchanged` — Support still
   records a receipt (same writer, same readback); Sale is still refused
   at the writer boundary; no denied payment is persisted.
10. `test_operations_receives_no_quote_and_no_tax` (NEW) — Operations
    (neither `finance_view` nor `commercial_view`) receives no ledger
    sentinel, no duty/VAT sentinel, and `finance.quote == []`; journey,
    route and status survive.
11. `test_customs_field_write_does_not_clobber_tax` (NEW) — write-safety:
    saving an unrelated customs field (`tk_no`) as Support leaves the
    stored true duty/VAT untouched, and a Sale render hides the numbers
    without mutating the stored document.

## 3. CI gates (AGENTS.md order)

Toolchain: isolated venv `~/workspace/venvs/logi-secfix` (Python 3.12.3),
`pip install -r requirements.txt -r requirements-dev.txt` (exit 0;
streamlit 1.66.1; benign warning: pymongo 4.19.0 does not provide extra
`srv` — not needed for mongomock). No real database, no production data,
synthetic fixtures only.

| Gate | Command | Result |
|---|---|---|
| ruff (changed files) | `python -m ruff check views/logi_view_model.py tests/test_logi_sec_finance_payload.py` | **PASS** — all checks passed |
| ruff (repo-wide) | `python -m ruff check .` | **FAIL (pre-existing, NOT_RUN-as-pass)** — exit 1, 7 errors, ALL in files this task did not touch (`tests/test_dashboard_financial_write_oracle.py`, `tests/test_intl_payment_comparator.py`, `tests/test_lg05_excel_roundtrip_gnt.py`, `views/contracts.py`, `views/shipment_360.py`). Untouched files are byte-identical to base HEAD, so these errors exist on base too. Per AGENTS.md only NEW errors are this task's responsibility: **0 new**. |
| router | `python scripts/check_router.py` | **PASS** — ROUTER CHECK PASSED |
| focused finance suite | C2A + C2C + C2D + CEO report + GetFly + auth-required + financial-write-safety + finance-logic + finance-review (9 files) | **PASS** — 84 passed, 6 skipped, 2 subtests passed |
| focused + new (after final reorder) | new tests + C2A + C2C + C2D + CEO + GetFly (6 files) | **PASS** — 72 passed |
| focused finance/customs/GNT (correction round) | new tests + C2A + C2C + C2D + CEO + GetFly (both files) + auth-required + financial-write-safety + finance-logic + finance-review + GNT canonical fields + GNT/docgen reality + LG08 GetFly safety + LG08 GNT contract + financial-amount-input-integrity + financial-ledger (17 files) | **PASS** — 171 passed, 7 skipped, 2 subtests passed |
| FULL suite | `python -m pytest tests -q --continue-on-collection-errors -p no:cacheprovider` | **PASS (no new failures)** — 1961 passed, 44 skipped, 10 subtests passed, 17 failed in 175.44s. All 17 failures are listed in `tests/BASELINE_FAILED.txt` (pre-existing debt); **0 NEW failures** vs baseline (verified by exact set comparison). One baseline entry (`test_dom_acceptance_inbox_desktop_and_mobile`) passed in both full runs — NOT removed from the baseline: the pass is not attributable to this change (inbox/DOM untouched) and may be environment-dependent. |

Two full runs were made (pre- and post-final-reorder of the gate evaluation):
both identical — 17 failed / 1961 passed / 44 skipped / 10 subtests passed,
0 new failures. The reorder changed no behaviour for authenticated actors
(verified: focused + new suite 72 passed after the reorder).

> **Correction round (2026-11-05) — full-suite re-measurement on the fixed
> code:** **17 failed, 1963 passed, 44 skipped, 10 subtests passed in
> 196.02s** (log `~/workspace/pr269-independent-review/evidence/
> pytest-head-fix.log`). Exact set comparison vs the base run (24 failed /
> 1953 passed): head failure set ⊆ base failure set — **0 NEW failures**.
> The 7 base-only failures are the 5 PR tests now fixed + the flaky inbox
> DOM test + the flaky timing test
> (`test_independent_reads_overlap_instead_of_serialising`), both of which
> passed in this run. Counts differ from the earlier "17 failed / 1961
> passed" because this run has 2 more passing tests and the timing test
> passed; counts differ from the independent review's "18 failed / 1960
> passed" for the same reason (that run had the timing test failing).
> The number that matters — **0 new failures vs base** — was reproduced by
> exact set comparison in every run. Do not report the suite as green: 17
> failures remain, all pre-existing baseline debt.

## 4. What was checked and deliberately NOT changed

Checked (source-verified, no amounts leak):

- `shipments[].finance` — redacted (quote preserved).
- `receivables` / `payables` / `reconciliation` — redacted / not built.
- `home.outstandingTotal/Label/Count` — derived from redacted rows → None /
  UNKNOWN label.
- `ceoReport` — finance sections empty from redacted inputs; operations /
  actionables preserved.
- `partnerContext.finance` — rows [] (status UNKNOWN) from redacted
  payables; partner identity preserved.
- `lastWrites` — readback finance redacted; outcome event/ok/error kept.
  **Correction round:** readback importInfo.tax/vat also redacted.
- `importInfo` — **correction round:** `tax`/`vat` redacted to None for
  actors without `finance_view` (shipments + lastWrites readbacks);
  declaration identity (`declarationNo`, dates, `customsStatus`, `gnt`
  readiness) preserved. The stored shipment keeps the true figures.
- `getfly` — money redacted (orders, lines, summary, normalizedRows).
- `document_workflow` — uses finance only as booleans (remaining>0,
  outstanding>0) to pick reason strings; no amounts in text.
- `ops.financialFlag/financialLabel`, alerts, notifications — fixed status
  tokens only (`CHỜ THU` / `CHỜ TRẢ` / `ĐÃ THU ĐỦ` … from
  `core/shipment_360.py`), no amounts.
- `timeline` — time/action/actor/tone only, no money values.
- `_remember()` — stores the already-redacted delivered model in session.
- `_shipment_document_review_projection()` — document-field review, no
  money fields by construction.

Deliberately KEPT (permitted data, separate authorization):

- Commercial quotes (`finance.quote`, BG-0306 lines) — Sale holds
  `commercial_view`. **Correction round:** the quote is now copied only
  when the actor holds `commercial_view`; Operations gets `quote: []`.
- `costIntelligence` (supplier-rate/catalog snapshots) and
  `financeServiceCatalog` (service code/name/unit) — commercial data under
  `commercial_view`/`tariff`; not ledger finance.
- `importInfo` declaration identity (`declarationNo`, dates,
  `customsStatus`, `gnt` readiness) — operational customs facts, not
  money. The ACTUAL tax amounts (`tax`/`vat`) are NOT kept: they are
  restricted finance (see §4 above); the earlier "operational customs
  facts" classification of the amounts was rejected by independent review
  and corrected in this round.
- `intlFxRates`, `tariff`, `handbook`, `inbox`, `workModules`,
  `userAccess`, `notebookLM`, `docgenTemplates`, `translation`,
  `attachmentPolicy`, `shipmentDocumentPicker` — no finance money.

## 5. Known observations (out of scope, NOT fixed here)

1. **Sentinel-scan collision (test scope note).** The seeded authority
   master carries bank account number `0123456789`, which contains the
   substring `123456789`. It is projected into `model["authority"]` for
   every role. The regression scan therefore covers exactly the nine
   finance payload paths named in the packet, not the whole-model JSON.
   Whether authority bank details belong in the payload is a separate
   follow-up, not this task.
2. **Staging auto-login.** `ensure_backend()` promotes an empty session to
   the staging SUPPORT actor. Production `require_login()` blocks anonymous
   before any build; the payload gate itself is fail-closed for anonymous.
   Unchanged pre-existing behaviour.
3. **`has_permission()` anonymous quirk.** Bare `has_permission()` returns
   True for an anonymous actor for `finance_view` (Viewer fallback fires
   before the anonymous check). The new gate ANDs `is_authenticated()` to
   close it. The quirk itself lives in `core/auth.py` and was NOT changed
   (minimal scope; the gate is the fix).
4. **No real-browser UI evidence.** React null-handling was verified at the
   formatter level (`fmtCcy`/`fmtMillionsCcy`/`fmtPct` return UNKNOWN for
   null) and by the UI-shape test; no browser run was made in this sandbox
   (same limitation as the previous executor's environment). Owner/CT
   browser UAT remains the visual gate.
5. **P2P law hash note (CORRECTED 2026-11-05).** The portable notebook
   file in this checkout records
   `SOURCE_CONTENT_SHA256=84914abd55960d6a5effad957ff9ebbdf917f632c8b18baa3a29c74a5d6ae4a7`
   (read directly from `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` line 5).
   The earlier text of this document (and its preflight receipts) wrongly
   cited `11ce33bb…` — that is the canonical notebook content hash from an
   earlier verification, not the value in the file actually read. No law
   content was changed; only this receipt was corrected.
6. **Finance-state boolean oracles (independent review F-4, recorded,
   NOT fixed here).** `documentWorkflow` reason strings, `ops.financialFlag`
   and `home.summary.financialAttention` are derived from unredacted
   finance before the row redaction, so Sale sees true finance-state
   signals (no amounts). No new RBAC decision exists for them; the Owner
   decides whether they are intended. Recorded as follow-up only.
7. **Authority bank accounts (independent review F-5, recorded, NOT fixed
   here).** `_party_view` projects bank account numbers for all authority
   companies/agents to every role; no documented policy classifies them.
   Owner policy decision needed (company account plausibly shared, agent
   accounts unclear). Recorded as follow-up only.
8. **C1 quote cost/margin channel (independent review F-2 follow-up,
   recorded, NOT fixed here).** `model["quotes"]` projects full quote
   economics (cost/margin) to every actor with no permission gate.
   Pre-existing, outside this PR's diff. Owner decision needed.
9. **Echoed-None field save (probed 2026-11-05, NOT fixed here — write
   behaviour unchanged per packet).** A `shipment_field_save` carrying an
   explicit `import_duty_amount: null` DOES overwrite the stored true
   figure with None (blank-stays-blank semantics, by design). The
   redaction itself never mutates the source, and saving an unrelated
   customs field (`tk_no`) leaves the tax figures intact (proven by
   `test_customs_field_write_does_not_clobber_tax`). A client that echoes
   a redacted (None) tax value into a field save would clear the stored
   figure — mitigation needs an Owner decision (write-side `finance_view`
   gate on the two tax fields, or a frontend rule never to submit hidden
   fields). Recorded as follow-up only.

## 6. Full-suite result / remaining blocker

Full suite on the final committed code: **1961 passed, 44 skipped,
10 subtests passed, 17 failed — all 17 pre-existing baseline failures,
0 new failures.** No remaining blocker for the bounded fix itself.

Correction-round re-measurement (2026-11-05, same host, same commands):
**1963 passed, 44 skipped, 10 subtests passed, 17 failed — 0 new
failures** (exact set comparison vs base 24 failed / 1953 passed; see §3
and §8). The count shift vs the earlier 1961/17 is +2 new tests passing
and the flaky timing test passing in this run. No remaining blocker for
the bounded fix itself; the 17 failures are pre-existing baseline debt
(plus two flaky tests that pass intermittently).

Remaining (outside this task, per stop condition):

- Draft PR creation needs GitHub write access from this host (see §8).
- Owner/CT browser UAT is the visual gate (no real-browser evidence from
  this sandbox).
- Independent review (ChatGPT) of this branch, then Owner merge decision.

## 7. Handoff

- `SECURITY_AUDIT_MODE=FINDING_VALIDATION` (prior executor) →
  `RESULT`: the finding `SALE_FINANCE_PAYLOAD_UNFILTERED` is now
  **CONFIRMED by runtime test** (was NEEDS_VALIDATION) and **FIXED** by
  this patch + regression. `CONFIRMED_FINDINGS=1`, `PATCH=READY_FOR_REVIEW`.
- `COCKPIT=WAITING_SECURITY_GATE` → **security gate for the payload
  boundary is now satisfied by this change**; the Cockpit integration
  itself is NOT started here (per stop condition) and still needs the
  Owner-only decision + independent review.
- NEXT=ChatGPT independent review of this branch (per packet), then Owner
  decision on the draft PR. No merge without Owner authorization.
- Rollback: revert the single commit on this branch; no data migration,
  no schema change, no production state touched.

## Preflight receipts

- `P2P_LAW_SOURCE=LOCAL_PORTABLE`
- `LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_CONTENT_SHA256=84914abd55960d6a5effad957ff9ebbdf917f632c8b18baa3a29c74a5d6ae4a7` *(corrected 2026-11-05; the earlier `11ce33bb…` value was the canonical notebook content hash, not this file's recorded value)*
- `EXPERIENCE_CHECK=NO_MATCH` (portable capsule: 1 record, no trigger match)
- Skills read: `.agents/skills/p2p-karpathy/SKILL.md`,
  `.agents/skills/security-audit/SKILL.md` (FINDING_VALIDATION mode;
  this turn is the separately authorized implementation lane).
- `OE_GATE`: Không bị over engineering chứ? — SIMPLER_PATH=YES (one
  helper + gate at the existing payload boundary, reusing
  `has_permission('finance_view')`); MATERIAL_PROGRESS=YES;
  NECESSITY=YES (runtime-confirmed leak); CORE_BEFORE_SUPPORT=YES;
  SMALLER_VERIFIABLE_SLICE=YES. `OE_VERDICT=DO_IT`.
- `LEARNING_RECONCILIATION=CANDIDATE`: checking a sandbox by PATH alone
  can miss WSL (prior executor's correction, already recorded); this
  session adds: a `build_view_model()` run as anonymous on the sandbox
  transport is silently promoted to the staging SUPPORT actor by
  `ensure_backend()` — a full-payload anonymous test must assert the gate
  directly instead of through the build.

## 8. Correction round (2026-11-05) — independent review REJECT → minimal fix

Review: `~/workspace/pr269-independent-review/PR269-INDEPENDENT-REVIEW.md`
(REVIEW_VERDICT=REJECT, MERGE_READY=NO, NEW_REGRESSIONS=0,
SECURITY_BOUNDARY=FAILED). Owner-approved correction on the same branch;
no restart of discovery, no re-approval requested.

### What changed (one commit on this branch)

- `views/logi_view_model.py` (+58/−8 vs 08e5a63; cumulative +214/−11 vs base):
  - `_can_view_commercial()` — fail-closed `commercial_view` gate, same
    shape as `_can_view_finance()` (reuses `core.auth.ROLE_PERMISSIONS`).
  - `_restricted_finance()` — quote copied ONLY when the actor holds
    `commercial_view`; Operations gets `quote: []` (F-2).
  - `_restricted_import_info()` — new helper: declaration identity survives,
    `tax`/`vat` → None (UNKNOWN, never 0), source never mutated (F-1).
  - `build_view_model()` — the existing redaction point also replaces
    `row["importInfo"]` (F-1, shipments path).
  - `_last_writes_readback()` — the same redaction applied to
    `readback["importInfo"]` (F-1, stale-readback path).
- `tests/test_logi_sec_finance_payload.py` (+137/−5 lines; 11 → 13 tests, F-3):
  distinct DUTY=222222222 / VAT=333333333 sentinels in data["2.4"];
  new `test_operations_receives_no_quote_and_no_tax` and
  `test_customs_field_write_does_not_clobber_tax`; duty/VAT + stored-source
  assertions added to the Sale / authorized-role / anonymous / downgrade /
  spoof / UI-shape tests.
- This document (F-6): FAIL-before corrected to 5 failed, 6 passed; law
  hash corrected to `84914abd…`; NEXT.md head sha corrected to 08e5a63;
  full-suite counts reported as actually measured (see §3/§6).

### Verification (all real runs, venv `~/workspace/venvs/logi-secfix`)

| Check | Result |
|---|---|
| New tests, WITH fix | **13 passed** (8.39s) |
| New tests, WITHOUT fix (source stashed, tests kept) | **7 failed, 6 passed** — the 5 original + 2 new tests fail; authorized-role + writer tests still pass |
| Focused finance/customs/GNT (17 files) | **171 passed, 7 skipped, 2 subtests passed** |
| ruff (changed files) | **PASS** — all checks passed |
| ruff (repo-wide) | 7 errors, identical set to base (5 files untouched by this PR) — **0 new** |
| router | **PASS** — ROUTER CHECK PASSED |
| Full suite (fixed code) | **17 failed, 1963 passed, 44 skipped, 10 subtests passed** — 0 new failures vs base (exact set comparison; head failure set ⊆ base 24-failure set) |
| Distinguishing test | Sale/Operations receive NO DUTY/VAT sentinel via shipments or lastWrites; Admin/Support keep exact figures; Sale keeps journey, declaration identity and quote; Operations gets `finance.quote == []`; stored source data and write functions unchanged |

### Write-safety probe (evidence `~/workspace/pr269-independent-review/evidence/probe_write_echo.py`)

- Saving an unrelated customs field (`tk_no`) leaves stored duty/VAT
  untouched. A redacted render never mutates the stored document.
- A field save carrying an explicit `import_duty_amount: null` DOES
  overwrite the stored true figure with None (blank-stays-blank semantics,
  by design, pre-existing). Write behaviour was NOT changed per packet
  ("chức năng ghi không đổi"); recorded as follow-up in §5 item 9 — Owner
  decision (write-side `finance_view` gate on the two tax fields, or a
  frontend rule never to submit hidden fields).

### Out of scope, recorded only (F-4 / F-5 / C1)

- F-4 finance-state boolean oracles (workflow reasons, `ops.financialFlag`,
  `home.summary.financialAttention`) — §5 item 6.
- F-5 authority bank account numbers — §5 item 7.
- C1 `model["quotes"]` cost/margin channel — §5 item 8.
- No role-matrix change, no Shipment Cockpit work, no merge, no deploy,
  no production data.

### Preflight receipts (correction round)

- `LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_CONTENT_SHA256=84914abd55960d6a5effad957ff9ebbdf917f632c8b18baa3a29c74a5d6ae4a7`
- `SKILL_CHECK=PASS | SKILL=.agents/skills/p2p-karpathy/SKILL.md | SHA256=cbe1b4c9082f0e253c75df20a9ca06ba3a4cc414ae1153c8b5a0fa3c03059ecd | MANIFEST=.p2p/portable/P2P-SKILL-PROJECTION.json | MATCH=YES` (skill not reinstalled/recreated/modified)
- `EXPERIENCE_CHECK=NO_MATCH` (portable capsule: 1 procedural record, no trigger match)
- `OE_GATE`: Không bị over engineering chứ? — SIMPLER_PATH=YES (extend the
  existing redaction point + existing gate, no new abstraction);
  MATERIAL_PROGRESS=YES; NECESSITY=YES (review REJECT blocker);
  CORE_BEFORE_SUPPORT=YES; SMALLER_VERIFIABLE_SLICE=YES. `OE_VERDICT=DO_IT`.
- Review read: `~/workspace/pr269-independent-review/PR269-INDEPENDENT-REVIEW.md`.
- Repo HEAD before this round: `08e5a632bf6316fb9cff14f8e97ca31c5cde6491`
  (PR head, verified); base `b0a6734af5c3ecc207530c67d185f2c366a04e8f`.
- NEXT=independent re-review of the corrected diff + extended distinguishing
  test, then Owner merge decision. No merge without Owner authorization.
