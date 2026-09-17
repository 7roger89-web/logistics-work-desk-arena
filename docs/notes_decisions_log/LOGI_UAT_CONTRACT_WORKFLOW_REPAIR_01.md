# LOGI_UAT_CONTRACT_WORKFLOW_REPAIR_01

## Intent and boundary

Repair employee contract create → authoritative outcome → existing detail, unsafe
contract paths and misleading wildcard only. Base main freshly fetched:
`344add65273500fd39eb15f3c19d8036ffc78f1b`. Session branch:
`arena/01a0aeea-logistics-work-desk-arena`. No deployment or self-merge.

Law: LOCAL_PORTABLE, generated projection with canonical provenance and SHA;
canonical authenticated API returned repository-scoped 404. Applied AGENTS.md
P2P_EVIDENCE_FIRST_VERIFICATION_V1 capsule. Agent claims are not evidence;
a passing test proves only the challenged behavior. No formal plan invented.
OE: DO_IT — retain existing router, dispatcher, lastWrites and canonical writer;
no new async framework, router architecture, schema or permissions.
Remote recovery check: exact-goal PR search empty; fetched all remote heads and
inspected recent PRs/commit subjects; no durable exact-goal work found.

## Root causes and bounded audit

1. Create treated dispatch transport boolean as permission/persistence success,
   immediately navigated, and did not send a requestId. Now one UUID and one
   dispatch enter neutral pending. Only matching event/requestId/ok **and** the
   authoritative contracts projection allow navigation. Failure remains on form
   with backend error. No optimistic contract; no effect redispatch or timeout retry.
2. C1 outcomes did not echo contract-create request identity. The existing
   dispatcher now attaches it for success, refusal and caught exceptions alike.
   Handler, canonical writer, RBAC and audit semantics unchanged.
3. Eight active dynamic path sites emitted raw IDs: create (1), list desktop
   and mobile (3), Layout desktop/mobile search (2), shipment detail links (2).
   All use the tiny contract-only `contractPath` encoding helper.
4. Wildcard falsely claimed an unfinished feature. All CURRENT NAV targets
   have explicit real routes and none has `soon: true`; wildcard is NotFound.
   No intentionally deferred route remains to map to PhaseBPlaceholder.
5. Five detail handlers said “Đã gửi…” even when dispatch returned false.
   Their wording was transport-only, not authoritative persistence wording;
   it remains transport-only, but is now guarded, with red connection failure.
   Save/goods/link transport messages are neutral blue rather than green.

No unrelated capability implemented. Drive, finance, GNT, CEO, GetFly, roles,
translation policies and shipment assignment remain untouched. The existing
GetFly section in NewContract is unchanged. PR49/PR51 untouched.

## Installed router identity challenge

Installed react-router-dom 7.18.3 / React Router route matching:
- Baseline `/hop-dong/05/2026/HDMB` matches `*`, not detail.
- Encoded `/hop-dong/05%2F2026%2FHDMB` matches detail and resolves `05/2026/HDMB`.
- Backend writer permits internal spaces, Unicode and percent characters (only
  trims/uppercases ID). Canonical writer/readback challenged `HD-01`,
  `05/2026/HDMB`, `HD SPACE`, `HĐ-ĐÔ`, `HD%25`, `HD%2F`.
- Router params turn literal `HD%2F` into `HD/` despite segment encoding.
  Therefore ContractDetail decodes the original location segment exactly once,
  rather than double-decoding params. Production-bundle DOM checks assert the
  exact canonical h1 identity for all six IDs.

## Reproducible evidence

Run from repository root (Python dependencies in isolated `.venv`):

```sh
.venv/bin/python scripts/gen_contract_workflow_fixture.py
.venv/bin/python -m pytest tests/test_contract_route_contract.py \
  tests/test_logi_interaction_latency_repair_01.py \
  tests/test_logi_contract_core_gaps_01.py tests/test_phase_c1_business_contracts.py -q
node tests/component/dom_acceptance_contract_workflow.mjs
node tests/component/dom_acceptance_contract_core_edit.mjs
(cd component && npm run typecheck && npm run build && python3 ../scripts/scan_process.py dist)
```

Observed:
- Fixture generator PASS: real isolated mongomock dispatcher → canonical writer
  → readback; six IDs; duplicate leaves existing document unchanged and writer
  uncalled; RBAC and validation writer uncalled; writer false and thrown exception
  return failures; every request echoes identity; sequence replay emits no write.
- 67 focused Python tests PASS. Contract-specific callback lifecycle spy proves
  handler=1, canonical writer=1, VM builds=1, explicit st.rerun=0, correlated
  authoritative readback. Existing PR50 stale-auth tests also retained/passed.
- New committed-bundle jsdom acceptance: 6 groups PASS. Encoded list links and
  exact identity; backend duplicate/RBAC/validation/writer refusals stay put;
  unrelated outcome and preexisting entity cannot navigate; ok without readback
  remains pending; fresh matching success navigates on SAME mount; all four
  actual tab panels render; disconnected transport stays put; desktop/mobile
  search resolves slash ID; malformed route shows NotFound and safe links.
- Existing contract core-edit production-bundle acceptance: 8 checks PASS.
- Typecheck/build PASS; executable process scan=0.

Baseline repro (extract the ORIGINAL committed bundle to an external .mjs):

```sh
git show 344add65273500fd39eb15f3c19d8036ffc78f1b:component/dist/logi-shell.js > /home/user/logi-baseline.mjs
BASELINE_BUNDLE=/home/user/logi-baseline.mjs node tests/component/dom_acceptance_contract_workflow.mjs
BUNDLE_PATH=/home/user/logi-baseline.mjs node tests/component/dom_acceptance_contract_workflow.mjs
```

First command's baseline mode PASS: observes emitted raw slash path and rendered
“Sắp có”. Second adversarial command **fails as required**, exit 1: expected
three encoded desktop/mobile links, found zero. This rejects the old bundle,
not merely an agent assertion. Static route contract additionally covers all
8 builders (including direct shipment links) and CURRENT NAV route coverage.

## Evidence boundary / truthful verdict

PROVEN for isolated canonical backend and committed production-bundle DOM,
plus mocked Streamlit callback/script lifecycle. DOM route fault injection uses
a malformed shipment target only to exercise the unmodified App wildcard.
Fixtures are sandbox readbacks, not fabricated production contracts. Request IDs
are rebound to actual UI clicks at the test transport boundary. These tests do
not claim live production UAT, browser visual/layout verification, deployment,
or concurrent cross-session duplicate uniqueness beyond existing business rules.
If no outcome/readback arrives, pending remains honest; no speculative retry.

Bundle SHA256:
- JS `4f92584263af9347f1c196236571f74c1ca533a211208cb50d079fd82d4b971b`
- CSS `67340ffcd124f02cdcd6eb77711673d124f2121fadc949e8a592c85321b9f797`

Production mutations=0; pilot mutations=0; secrets changed=NO.
Ready for independent Control Tower review, not merged or deployed.
