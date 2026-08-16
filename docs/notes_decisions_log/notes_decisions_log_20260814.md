# LOG-C01 Decision Log — 2026-08-14

## Decision 1 — Dashboard first-click transition

- Decision: preserve the current dashboard layout and detail renderer; add only an explicit rerun after the existing shipment-selection state assignments.
- Reason: current runtime reproduced a two-click defect, while the detail branch already worked after an active shipment id existed.
- Evidence: `E0-P0A-UI1`, `E0-P0A-SRC1`, `E1-P1A-SRC1`, `E1-P1A-UI1`.
- Safety boundary: verification used the real local Streamlit runtime and read-only Browser actions; no save/delete/payment/upload action was submitted.

## Decision 2 — Stop at bounded local verification

- Decision: do not modify credentials, auth policy, worker dependencies, payment atomicity, persistence, Docker, or deployment as part of LOG-C01 P1-A.
- Reason: those are separate security/data/operations boundaries requiring their own evidence and, where applicable, owner authorization. The current worktree also prevents a safe isolated commit of the already-dirty dashboard file.
- Next decision needed: owner chooses whether Logistics remains local-admin-only or should enter a separate multi-user/deployment hardening phase after credential rotation and authentication design.

## Decision 3 — Closure boundary

- Decision: close LOG-C01 as `BLOCKED` overall, with supervisor `REJECT` for the overall readiness claim.
- Evidence: the local dashboard slice passes, but the final P2P doctor/governance drift is `FAIL`, Docker is unavailable, and the dirty worktree prevents a safe isolated commit.
- Safety: leave the P2P-managed files, credentials, auth posture, worker, payment, and persistence paths unchanged until separately authorized and verified.

## LOG-C02 Decision 1 — Reuse current customer calculation

- Decision: use `core.logic.calculate_from_shipment` as the source for total
  receivable, collected, outstanding receivable, known cost, and estimated
  profit in the new read model.
- Reason: it is the current code-backed calculation used by shipment finance,
  customer debt overview, and reports. A second UI balance would create drift.
- Evidence: `E0-P0A-LOGIC`, `E1-P1A-SRC`, `E1-P1A-TEST`.

## LOG-C02 Decision 2 — Mark missing ledger concepts UNKNOWN

- Decision: do not derive global payable, unallocated money, reconciliation,
  evidence completeness, debit balance, tax obligation, or actual profit from
  unrelated fields.
- Reason: current records are distributed across shipment payments, agency
  fields, proxy payments, contract transactions, entrustment wallets, GNT
  rows, and audit logs; they are not a single obligation/allocation ledger.
- Evidence: `E0-P0A-REPORTS`, `E0-P0A-PAYMENT`, `E0-P0A-PROXY`,
  `E0-P0A-ENTRUST`, `E0-P0A-TAX`, `E1-P1A-TEST`.

## LOG-C02 Decision 3 — Read-only first-view summary

- Decision: render Shipment 360 before the existing operational tabs and load
  related proxy/entrustment records only for display.
- Reason: owners need a fast financial view while support users must not be
  exposed to a new workflow or unsafe write path. The existing edit/save
  surfaces remain unchanged.
- Evidence: `E1-P1B-UI`, `E1-P1B-NOWRITE`, QA browser artifact.

## LOG-C02 Decision 4 — Stop at bounded local PASS

- Decision: treat Slice A as locally PASS but keep overall LOG-C02 `BLOCKED`
  until supervisor review; do not claim financial closure or persistence safety.
- Reason: the dirty worktree prevents a safe isolated commit, no durable
  write→reload proof was requested or performed, and existing security,
  governance, Docker, and payment-integrity findings remain outside scope.
- Safety: no P2P change, real-data mutation, migration, deployment, credential
  change, or payment write was performed.

## LOG-C02 Decision 5 — Supervisor closure boundary

- Decision: accept the read-only Shipment 360 Slice A as locally proven, but
  reject overall LOG-C02 closure/readiness for now.
- Reason: the worktree is not isolatable for a safe commit; durable write/read
  proof is unknown; Contract proxy atomicity, P2P governance drift, Docker, and
  security/operations findings remain separate.
- Evidence: `reports/supervisor/rp_supervisor_260814_log_c02_shipment_360.md`,
  `E1-P1A-SRC`..`E2-SUPERVISOR`.
- Required boundary: do not add ledger writes or repair protected
  P2P/security/persistence surfaces as part of this slice.

## LOG-C02 Decision 6 — B0 bounded atomicity result

- Decision: implement only the Contract proxy pair atomicity fix and keep the
  overall B0 result `PARTIAL`.
- Reason: the existing pair had two independent saves. A supported Mongo
  transaction now covers both documents and their audit rows; unsupported
  topology fails closed. Fixture injection and isolated fresh-client Mongo
  read-back passed.
- Evidence: `E0-P2B-TEST1..E0-P2B-TEST4`,
  `reports/Data-Integrity/rp_data_260814_150045_by_gpt-5-codex_financial-write-safety.md`.
- Boundary: no ledger, migration, Quick Entry, real-money write, P2P edit,
  deployment, or credential change.

## LOG-C02 Decision 7 — Do not generalize idempotency

- Decision: do not treat the lump-sum payment route as proof that all payment
  writers are retry-safe.
- Reason: the same fixture reproduced direct shipment payment duplication
  when a retry generated a new payment ID (40,000 became 80,000), and an
  injected entrustment second-write failure left the first document present.
- Evidence: `E0-P2B-TEST5..E0-P2B-TEST10`,
  `reports/Edge-Case/rp_edge_260814_150045_by_gpt-5-codex_financial-write-safety.md`.
- Next smallest slice: define request identity/correction semantics for
  direct payment and close entrustment batch failure semantics with fixtures.

## LOG-C02 Decision 8 — Quick Entry remains closed

- Decision: `CAN QUICK ENTRY BEGIN SAFELY? = NO`.
- Reason: the material financial write family is not uniformly safe, and the
  minimum obligation/transaction/allocation/adjustment/evidence ledger does
  not yet exist for held/unallocated and received-on-behalf money.
- Evidence: B0 R3 actual-status and coder/data-integrity reports.
- User action: none required for this safe stop; owner direction is needed
  before selecting the duplicate external payment and correction semantics
  for the next slice.

## LOG-C02 Decision 9 — B1 owner semantics accepted

- Decision: use a stable immutable request identity for one business payment
  action; retries reuse it, while equal amount/customer/date with a different
  request identity remains a separate legitimate transaction.
- Decision: preserve original financial history; corrections use a linked
  reversal/correction record with reason, actor, timestamp, and evidence as
  available. No silent delete or overwrite.
- Decision: an entrustment batch is all-or-nothing. Independent items must be
  modeled as independent actions rather than a disguised partial batch.
- Evidence: current LOG-C02 B1 owner attachment and
  `E0-P2B1-OWNER1`.

## LOG-C02 Decision 10 — B1 scope boundary

- Decision: implement only direct shipment payment identity, entrustment batch
  atomicity, minimum correction foundation, and the complete fixture matrix.
- Boundary: do not build Quick Entry, held/unallocated ledger, broad
  accounting, standalone proxy/contract transfer fixes, GetFly redesign, or
  shipment audit/outbox refactor.
- Safety: shared identity/correction storage must not require `shipment_id` so
  future payment-only and held-money cases remain representable.

## LOG-C02 Decision 11 — B1 financial write safety accepted

- Decision: B1 is **PASS** for the bounded direct shipment payment,
  correction/reversal, and entrustment batch boundary.
- Evidence: 37 full unittest cases pass, 6/6 disposable Mongo fixture cases
  pass with fresh-client read-back, compileall passes, fixture cleanup leaves no
  generated database, and the new Supervisor report verdict is PASS.
- Safety: same-request direct retry has one effect; equal legitimate payments
  with distinct request identities are accepted; corrections preserve the
  original; entrustment failure leaves zero partial state; derived balances are
  recalculated from effective history.
- Boundary: Quick Entry remains closed. No held/unallocated ledger, broad
  obligation/allocation model, standalone legacy writer, deployment, migration,
  P2P edit, credential change, or real-money write is authorized by this result.
- Next: recommend only a bounded B2 ledger foundation after this handoff; no
  new Owner decision is required for the current B1 semantics.

## LOG-C02 Decision 12 — B2 canonical ledger foundation

- Decision: implement the bounded B2 canonical ledger and read-only A Bò/Sale
  Thành projection; keep Quick Entry, migration, auto-netting, real-money
  writes, and P2P changes closed.
- Result: canonical obligation/transaction/allocation history is shipment-
  optional; balances are derived; ownership/restriction/UNKNOWN and currency
  guards fail closed; allocation reversal and later shipment linking preserve
  history. The Finance projection is read-only.
- Evidence: coder report
  `reports/coder/rp_coder_260814_165400_by_gpt-5-codex_log_c02_b2_ledger.md`,
  Data-Integrity commit `4f77b8c`, Edge-Case commit `9695244`, B2 checkpoint
  `6386198`, and plan evidence `E2-P1C-TEST1-R2..E2-P1C-REVIEW6-R2`.
- Current result: `PARTIAL / NOT READY FOR PRODUCTION WRITE ENABLEMENT` until
  supervisor review, Docker/browser limitation, B1 Atlas timeout rerun, and
  general adjustment/FX boundaries are explicitly closed or accepted.

## LOG-C03 Decision 1 — Dashboard product closure and helper split

- Decision: LOG-C03 product/project acceptance is `PASS` for the bounded
  shipment-first Dashboard 2.0 criteria. The P2P formal helper is separately
  `BLOCKED` and must not be converted into a product defect.
- Evidence: `E4-P3A-ORACLE1..E4-P3A-BROWSER2`,
  `Reports/QA/playwright/2026-08-14-log-c03-closure.json`, and the latest
  Supervisor report.
- Classification: Docker and pytest are `NOT_APPLICABLE` to this product
  closure; the financial write oracle is a closed
  `GOAL_ACCEPTANCE_REQUIREMENT`; the P2P marker is a
  `P2P_INFRASTRUCTURE_REQUIREMENT`.
- Safety: the mounted oracle records `financial_write_count = 0`, financial
  fixture before/after differences `0`, and browser QA submitted no save,
  delete, payment, or other business-data action.
- Known gap: real `SALE Thành` remains `0/78` because normalized owner source
  is absent. The fixture proves filter semantics without inferring an owner;
  no schema migration is opened.
- Boundary: do not build Docker, install pytest, modify P2P, migrate owner
  data, or start LOG-C04 automatically.

## LOG-C04 Decision 1 — Canonical projection and read-only desk boundary

- Decision: implement LOG-C04 as a read-only projection of the canonical
  ledger. `SALE Thành` remains the exact `internal_sale_owner` management
  filter, never a financial party or second balance book.
- Result: projection buckets distinguish TT payable, A Bò-held credit,
  received-on-behalf, paid-on-behalf, unallocated, UNKNOWN, and restricted;
  currencies remain separate and source/allocation/provenance IDs are exposed.
- Evidence: `e117e1d`, `215a9ad`, `E1-P1A-*`, `E1-P1B-*`, and
  `tests/test_reconciliation_desk.py` (11/11).

## LOG-C04 Decision 2 — Truthful live empty state

- Decision: do not seed or migrate financial data just to make the new desk
  show the golden `62464` row. When the live projection has no normalized
  SALE Thành owner/partner row, the UI states that fact and leaves positive
  trace/review states unmounted.
- Evidence: visible browser at `http://127.0.0.1:8520/`, official QA
  `Reports/qa/playwright/2026-08-14-log-c04-partner-reconciliation.json`, and
  `liveFixtureSearchAbsentTruthful=true`.

## LOG-C04 Decision 3 — Local product verdict and blockers

- Decision: local Streamlit product scope is PASS for the implemented
  read-only desk, route, search/period flow, write oracle, and LOG-C03
  Dashboard regression. Docker-built runtime acceptance and positive live
  data/trace coverage remain BLOCKED by environment/source state.
- Evidence: 64/64 unittest pass with 2 opt-in skips, compileall pass, visible
  browser console errors/warnings `[]`, and coder report
  `reports/coder/rp_coder_260814_210500_by_gpt-5-codex_log-c04-reconciliation.md`.
- Boundary: no workbook import, live ledger mutation, owner migration, FX
  rewrite, Quick Entry, global accounting close, or LOG-C05 was opened.

## LOG-C04 Decision 4 — Supervisor bounded acceptance

- Decision: supervisor PASS for the bounded local product scope. This closes
  LOG-C04 implementation without claiming Docker-built runtime acceptance,
  positive live fixture coverage, global accounting closure, or P2P helper
  completion.
- Evidence: `reports/supervisor/rp_supervisor_260814_211500_by_gpt-5-codex_log-c04-reconciliation.md`,
  official QA JSON/Markdown, 64/64 unittest pass with 2 opt-in skips, and
  visible browser console errors/warnings `[]`.
- Boundary: P2P formal helper remains BLOCKED by its separate-objective
  linter; Docker is unavailable; no LOG-C05 implementation begins in this
  task.
