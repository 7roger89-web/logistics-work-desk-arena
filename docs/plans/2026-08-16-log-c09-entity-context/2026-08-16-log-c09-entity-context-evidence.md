# LOG-C09 Entity Context Evidence Ledger

## Metadata

- Date: `2026-08-16`
- Plan: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-plan.md`
- Evidence: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-evidence.md`
- Benchmark: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-benchmark.md`
- Actual status: `docs/plans/2026-08-16-log-c09-entity-context/2026-08-16-log-c09-entity-context-actual-status.md`

## Evidence Rules

This ledger records LOG-C09 recovery, source, graph, implementation, runtime, critique, correction, regression, and safety evidence. It does not authorize deployment, release, financial mutation, historical publication, or external communication.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-REC1`: Attached LOG-C09 request recovered; scope is Customer 360, Factory/Supplier 360, and generic Partner/Agent 360 around Shipment 360.
- `E0-P0A-STATE1`: LOG-C07/C08 artifacts and reports are present in the shared worktree; Dashboard and Shipment 360 are preserve-only foundations.
- `E0-P0A-SRC1`: Shipment 360 currently renders customer/supplier/agent/factory context as display-only text/tables but has no entity workspace links.
- `E0-P0A-SRC2`: Existing Customer route is a CRUD/data-editor surface, not a read-first context workspace; no generic Factory/Supplier or Partner/Agent context route exists.
- `E0-P0A-SRC3`: Existing financial projection is canonical/read-labelled and A Bò reconciliation is a separate protected route; no LOG-C09 financial writer is allowed.
- `E0-P0A-ANV1`: Fresh `anvien analyze --force` completed before graph queries; graph and file projection were rebuilt with zero parse failures.
- `E0-P0A-GIT1`: Shared worktree is materially dirty from prior user work; unrelated changes are preserved and no reset is permitted.
- `E0-P0A-P2P1`: `p2p_workflow.py inspect` recognizes the installed logistics project and confirms existing project state/evidence; no release action is requested.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: `core/entity_context.py` is a pure read-only projection module. It consumes loaded customer/shipment mappings plus existing dashboard/workspace read models; it contains no database, ledger writer, persistence, or mutation call.
- `E1-P1A-SAFE1`: customer master fields are returned under `master`; factory lots remain under `lots` with `source=shipment/lot-specific data`; partner finance is a per-shipment list with an explicit no-aggregate note.
- `E1-P1B-TEST1`: `python -m unittest tests.test_entity_context tests.test_shipment_workspace tests.test_shipment_360` -> `Ran 11 tests ... OK`.
- `E1-P1B-SAFE1`: focused tests deep-copy the shipment fixture and assert it is unchanged; multi-lot and absent fields remain explicit `UNKNOWN`.
- `E1-P1-ANV1`: Anvien impact/file-detail evidence was gathered for the existing Shipment 360 and route surfaces before implementation; the new pure module remains bounded to the P1 projection contract.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-SRC1`: `views/entity_context.py` consumes session-loaded customers/shipments and pure `core.entity_context` projections; no database writer, ledger writer, CRUD, or persistence call is present.
- `E2-P2A-RENDER1`: local Streamlit runtime at `http://127.0.0.1:8520/` rendered Customer 360, Factory/Supplier 360, and Partner/Agent 360. Factory with no source option rendered explicit UNKNOWN; Partner rendered generic roles/documents and kept canonical finance subordinate/collapsed.
- `E2-P2B-NAV1`: mounted UI test and real browser flow prove Entity -> Shipment 360 and Shipment 360 -> Customer 360 -> Shipment 360. Legacy shipment mapping keys with whitespace/tab suffixes resolve to the exact Dashboard key before opening.
- `E2-P2B-SAFE1`: `views/shipment_360.py` adds only read/context entry buttons; `views/shipment.py` passes the current `sid` as navigation identity. No finance/document writer path changed.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`

- `E3-P3A-RENDER1`: reusable `playwright/log_c09_entity_context_flow.cjs` executed with bundled Playwright against the real local runtime. Official report: `reports/QA/playwright/2026-08-16-log-c09-entity-context.json`; all 11 checks PASS; screenshot: `reports/QA/playwright/2026-08-16-log-c09-entity-context.png`.
- `E3-P3A-CRITIQUE1`: visual review found legacy document IDs could dead-end when Dashboard keys differed and sidebar navigation needed a real visible target; corrected with explicit navigation shipment id plus key resolver. Re-rendered browser flow passed.
- `E3-P3A-REG1`: `python -m unittest discover -s tests -p "test*.py"` -> `Ran 144 tests in 24.017s`, `OK (skipped=2)`. `python -m compileall -q core views tests` exited 0. Focused LOG-C09/C07/C08 suite: 13 tests OK.
- `E3-P3A-ENV1`: Docker unavailable (`DOCKER_NOT_FOUND`); pytest unavailable (`No module named pytest`). These are environment limitations, not substituted release evidence.

## Closure Evidence

- `E-CLOSE-ANV1`: post-implementation `anvien analyze --force` completed with 252 files scanned, 110 parsed code files, 0 parse failures; file-detail was refreshed for changed route/render files. Shared dirty worktree makes global detect-changes high-risk/noisy; changed paths were reviewed and kept scoped to LOG-C09 plus required plan/QA artifacts.
- `E-CLOSE-SUP1`: supervisor report records bounded local acceptance PASS, with NOT_RELEASED status and Docker/pytest limitations retained.
- `E-CLOSE-GIT1`: P1 commit `ed772ea` exists; final LOG-C09 implementation commit is recorded in the handoff after staging only scoped files.
