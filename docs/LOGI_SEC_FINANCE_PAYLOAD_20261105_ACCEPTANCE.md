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

## 1. Source patch / diff

One file changed, +159/−11 lines (plus one new test file):

- `views/logi_view_model.py` — the ONLY source file touched.
  - `_can_view_finance()` — server payload gate: authenticated session actor
    holds `finance_view` from the single `core/auth.py::ROLE_PERMISSIONS`
    matrix. Fail closed for anonymous (bare `has_permission` alone would
    return True for an anonymous actor via the Viewer fallback).
  - `_restricted_finance()` — restricted per-shipment finance block: keeps
    the commercial quote (`commercial_view`) + currency + UI-safe empty
    shapes; every restricted money figure is None (UNKNOWN, never 0).
    `hasActualLines=False` means "no finance visible to this actor", marked
    by `"restricted": true`.
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
    redactor, no new permission matrix.
  - `_last_writes_readback()` — write outcomes' full-projection readbacks
    are redacted at the payload boundary (covers stale Admin outcomes
    surviving a role downgrade in the same session).
  - `_getfly_preview_projection()` — money redacted at the payload boundary
    (covers a preview left in session state by a previous role as well as
    the actor's own upload).
- `tests/test_logi_sec_finance_payload.py` — NEW, 11 tests (see §2).
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
| BEFORE fix (base HEAD + new tests only) | **5 failed, 5 passed** — Sale distinguishing test, anonymous, role downgrade, frontend role-selector spoof, UI-shape test all FAILED with the sentinel present in Sale's payload. Authorized-role + writer tests passed, proving the fixture valid. |
| AFTER fix (same tests) | **11 passed** |

The 11 tests:

1. `test_sale_payload_contains_no_finance_sentinel` — the distinguishing
   test: Sale payload has no sentinel in shipments[].finance, receivables,
   payables, reconciliation, home, ceoReport, partnerContext, lastWrites or
   getfly; restricted money is None (never 0); stale Admin lastWrites and
   GetFly preview are redacted; Sale still sees shipment id, customer,
   journey, route, status and the BG-0306 commercial quote.
2. `test_sale_payload_matches_admin_quote` — Sale's quote is byte-identical
   to Admin's.
3. `test_authorized_roles_retain_finance_sentinel[admin|support|viewer]` —
   finance_view holders keep the sentinel in finance, payables and
   partnerContext (no narrowing of the role matrix).
4. `test_anonymous_gate_is_fail_closed` — `_can_view_finance()` is False
   with no authenticated identity; standalone helpers redact stale
   lastWrites + GetFly preview under that gate.
5. `test_sandbox_promotes_anonymous_to_staging_actor` — pins pre-existing
   staging behaviour: `ensure_backend()` promotes an empty session to the
   staging SUPPORT actor (production `require_login()` blocks anonymous
   before any build).
6. `test_role_downgrade_same_session_drops_stale_finance` — Support build
   WITH sentinel → same session downgraded to Sale → rebuilt payload has
   no sentinel.
7. `test_frontend_role_selector_cannot_bypass_server` — spoofed client-side
   role keys do not change the server actor (`user.role == "SALE"`) or the
   payload.
8. `test_restricted_finance_shape_is_ui_safe` — restricted block keeps the
   keys React dereferences directly (`actual`, `payments`, `quote`,
   `currency`, `partner.payments`).
9. `test_finance_writers_and_ledger_outcomes_unchanged` — Support still
   records a receipt (same writer, same readback); Sale is still refused
   at the writer boundary; no denied payment is persisted.

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
| FULL suite | `python -m pytest tests -q --continue-on-collection-errors -p no:cacheprovider` | **PASS (no new failures)** — 1961 passed, 44 skipped, 10 subtests passed, 17 failed in 175.44s. All 17 failures are listed in `tests/BASELINE_FAILED.txt` (pre-existing debt); **0 NEW failures** vs baseline (verified by exact set comparison). One baseline entry (`test_dom_acceptance_inbox_desktop_and_mobile`) passed in both full runs — NOT removed from the baseline: the pass is not attributable to this change (inbox/DOM untouched) and may be environment-dependent. |

Two full runs were made (pre- and post-final-reorder of the gate evaluation):
both identical — 17 failed / 1961 passed / 44 skipped / 10 subtests passed,
0 new failures. The reorder changed no behaviour for authenticated actors
(verified: focused + new suite 72 passed after the reorder).

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
  `commercial_view`.
- `costIntelligence` (supplier-rate/catalog snapshots) and
  `financeServiceCatalog` (service code/name/unit) — commercial data under
  `commercial_view`/`tariff`; not ledger finance.
- `importInfo.tax` / `vat` / `gnt` — operational customs facts on the
  import tab (recorded duty/VAT from the customs notice), not ledger
  finance. Classification decision for the reviewer/Owner to confirm; the
  distinguishing test's sentinel was never placed there.
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
5. **P2P law hash note.** The portable notebook file in this checkout
   carries `SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`
   (read directly from `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`); the
   validation doc cited `84914abd…` as portable metadata. The value used
   here is the one in the file actually read. No law content was changed.

## 6. Full-suite result / remaining blocker

Full suite on the final committed code: **1961 passed, 44 skipped,
10 subtests passed, 17 failed — all 17 pre-existing baseline failures,
0 new failures.** No remaining blocker for the bounded fix itself.

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
- `LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`
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
