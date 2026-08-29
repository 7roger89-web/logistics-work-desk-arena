# LOG-SKILL01 Logistics Skill Pack v0.1 Foundation Plan

## Metadata

- Date: 2026-08-29
- Status: complete_for_owner_review
- Plan: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-plan.md
- Evidence: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-evidence.md
- Benchmark: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-benchmark.md
- Actual status: docs/plans/2026-08-29-log-skill01-logistics-skill-pack/2026-08-29-log-skill01-logistics-skill-pack-actual-status.md

## Goal

Build the minimum usable Logistics Skill Pack v0.1 from the fresh GitHub
canonical Logistics repository. The pack will contain five independent
declarative skill contracts, a small machine-readable provenance/index file,
and pure reference behavior for intake, payment, quote, compliance, and sales
support. It will not add a runtime loader, modify the existing app, import
upstream wholesale, or touch P2P core.

## Rules

- Complete P0 actual status before implementation work.
- Use the fresh GitHub main HEAD and tree as the task authority; do not reuse the deleted local checkout as authority.
- Use one task-scoped sparse/shallow/filtered workspace only.
- Keep the deleted D:/Logistics_App_Copy path deleted; do not restore or recreate it.
- Apply MINIMUM_SUFFICIENT_WORK, BOUNDED_RECON, TARGETED_VALIDATION_FIRST, and STOP_WHEN_EVIDENCE_IS_SUFFICIENT.
- Implement only the five requested logistics capabilities and tiny supporting reference code/tests.
- Treat upstream content as inspect-only evidence. Adapt concepts/templates selectively; do not vendor the upstream repository.
- Preserve stable context separately from dynamic FX, freight, customs, tax, border, supplier, and regulation data.
- Never turn missing input into an estimate, verified fact, customs result, invoice, or payment authorization.
- Keep commercial discrepancies fail-closed at COMPLIANCE_REVIEW_REQUIRED with no evasion path.
- Because the current user explicitly requires one clean candidate commit, do not create intermediate commits; stage only the final allowlist and make one local candidate commit after all focused validation passes.
- Do not push, merge, deploy, release, access production credentials, or write production data.
- Record evidence and benchmarkable inventory as each slice completes.
- Run Anvien only when useful and available; if its graph/index is unavailable, record that limitation rather than inventing impact evidence.

## Problem

The fresh canonical GitHub repository contains the existing Logistics Work Desk
application and operational test/docs surfaces, but no repo-local five-skill
Logistics Skill Pack in the canonical tree. The deleted local checkout cannot
be recovered or treated as evidence. The implementation must therefore be
reconstructed from the LOG-SKILL01 specification and fresh repository/source
inspection, with no assumption that any deleted uncommitted work survived.

## Scope

- Add five independent contracts under skills/logistics/:
  - logistics.business_context
  - logistics.customer_intake
  - logistics.payment_scenario
  - logistics.quote_builder
  - logistics.sales_enablement
- Add one small JSON pack index with exact skill IDs, workflow, authority invariants, and upstream provenance.
- Add pure Python reference functions only where needed to make the contracts testable:
  intake normalization, Decimal payment scenarios, compliance consistency check,
  source-labelled quote reasoning, and fact-safe sales response construction.
- Add four small static fixtures: simple shipment, RMB factory, incomplete intake, and compliance discrepancy.
- Add focused tests for the pack contract/index, intake, payment/compliance, quote, and sales behavior.
- Add the standard plan/evidence/benchmark/actual-status set and one coder/supervisor report pair.
- Keep the workspace sparse and do not checkout unnecessary vendor/runtime directories.

## Non-Goals

- No import or vendoring of all ai-business-skills files.
- No new agent, capability ontology, loader, orchestration, MCP, Arena, vector, graph, marketplace, CRM, API, database, or production framework.
- No LOG-TRADE01, route optimization, Docling/PaddleOCR, customs APIs, translation, CRM, lead generation, retention, analytics, autonomous messaging, or external integrations.
- No modification to existing core/, views/, app.py, web_app.py, database, credentials, or production data.
- No current FX/freight/customs/tax/border/supplier/regulation values in stable context.
- No invoice, customs declaration, transfer instruction, concealment, undervaluation, false declaration, or evasion behavior.

## Requirements

### Fresh authority and provenance

- Record canonical source as GitHub repository 7roger89-web/logistics-work-desk.
- Record remote URL, default branch, fresh base SHA, and fresh base tree SHA.
- Record the one task workspace path/type/size and sparse/shallow/filter properties.
- Inspect ai-business-skills at its current pinned master commit, version, license,
  exact referenced paths, and reuse classification. Record text reuse explicitly.

### Five-skill contract

Every SKILL.md must expose id, version/status, purpose, triggers, required and
optional inputs, output contract, dependencies, dynamic-data requirements,
authority boundary, unknown behavior, examples, and provenance. Contracts must
remain independently readable and must not require a runtime loader.

### Domain invariants

- AI_GENERATED_VALUE != VERIFIED_BUSINESS_VALUE
- MARKETING_PRICING_ADVICE != ACTUAL_LOGISTICS_COST
- MISSING_DYNAMIC_DATA != PERMISSION_TO_ESTIMATE
- CUSTOMER_MESSAGE != VERIFIED_SHIPMENT_FACT
- QUOTE != INVOICE
- QUOTE != CUSTOMS_DECLARATION
- RETRIEVED_REGULATION != AUTOMATIC_LEGAL_TRUTH
- CURRENT_FX_REQUIRES_TIMESTAMPED_SOURCE
- CURRENT_FREIGHT_REQUIRES_SOURCE_OR_MANUAL_INPUT
- COMMERCIAL_VALUE_MISMATCH -> COMPLIANCE_REVIEW_REQUIRED

### Reference behavior

- Intake preserves explicit values and multi-factory lots, emits UNKNOWN and NEEDS_CUSTOMER_INPUT, and never infers CBM, Incoterm, route, classification, or export capability.
- Payment uses Decimal arithmetic for USD and authorized China-side RMB scenarios, requires timestamped FX and explicit fee sources/manual inputs, and emits INPUT -> RATE -> FEE -> INTERMEDIATE_AMOUNT -> FINAL_AMOUNT traces.
- Payment/compliance mismatch returns COMPLIANCE_REVIEW_REQUIRED, required documents/clarifications, no payment instruction, and no evasion guidance.
- Quote output labels KNOWN_COST, ESTIMATED_COST, CUSTOMER_PRICE, UNKNOWN_COST, and ASSUMPTION; missing dynamic input remains explicit and prevents a complete total.
- Sales output separates FACT, SALES_ARGUMENT, and ASSUMPTION, covers the eight requested objections, and is human-review-only.

## Acceptance Criteria

- The five requested skill IDs exist exactly once and are independently loadable as Markdown contracts.
- Upstream provenance records the exact inspected paths and classifications without vendoring source text.
- Fixture C returns NEEDS_CUSTOMER_INPUT with missing Incoterm, CBM, and pickup instead of invented values.
- USD/RMB payment outputs are deterministic, Decimal-derived, and traceable.
- Fixture D returns COMPLIANCE_REVIEW_REQUIRED without a payment instruction or evasion guidance.
- Quote missing freight/FX evidence returns INCOMPLETE and does not use pricing advice or an industry average as cost.
- Sales output covers all required objections, uses source-gated facts, and cannot auto-send or make unsupported guarantees.
- Focused parser/schema/fixture/arithmetic/quote/compliance/sales tests and affected-module compile checks pass.
- Targeted git diff --check passes for the final allowlist.
- Exactly one clean local candidate commit is created on a task branch; no push/merge/deploy occurs.
- Existing application and P2P core files remain unchanged by this task.

## Checklist

- [x] P0-A: Complete actual status from fresh GitHub authority.
  - Goal: establish canonical branch/tree, workspace identity, current repository structure, preserved application surfaces, upstream provenance, and the exact implementation boundary.
  - Work Steps: query GitHub refs; create one sparse/shallow/filtered workspace; inspect AGENTS.md, root conventions, tree paths, tests, and existing app sibling surfaces; inspect upstream metadata and six exact reference paths; write actual-status and update downstream phases before code.
  - Implementation Gate: actual-status contains a completed P0 decision with evidence IDs, fresh base identity, relationship/touch map, and explicit next actions.
  - Acceptance: current reality is classified without relying on the deleted checkout, and only P1-A is authorized to start.

### P1: Contracts, provenance, context, and intake

- Phase Goal: establish the five independent skill contracts/index and make customer messages consumable without fabrication.
- Phase Boundary:
  - In scope: skills/logistics contracts/index/context, pure intake reference, fixtures A/C, focused contract/intake tests.
  - Out of scope: existing app runtime, database, upstream vendor tree, payment/quote/sales behavior beyond contract references.
  - Dependencies: P0-A fresh authority and completed actual-status.
- Phase Implementation Rule: do not implement P1 directly. Implement P1-A, verify and record it, refresh actual-status, then implement P1-B.
- Ordered Slice List:
  - P1-A: Add five skill contracts, pack index, stable context, and provenance.
  - P1-B: Add source-preserving intake normalization and complete/incomplete fixtures.

- [x] P1-A: Add five skill contracts, pack index, stable context, and provenance.
  - Goal: create the minimal independently readable skill-pack surface and record selective upstream reuse.
  - Scope Boundary:
    - Editable: skills/__init__.py, skills/logistics/__init__.py, five SKILL.md files, skills/logistics/skill-pack.json, contract test.
    - Inspect-only: fresh GitHub AGENTS.md/tree and upstream raw skill files.
    - Preserve-only: core/, views/, app.py, web_app.py, .streamlit/, data/, existing tests unrelated to the pack.
    - Out of scope: any loader, framework, app wiring, or upstream vendor copy.
  - Non-Goals: executable business logic, live data, runtime integration, and current price/rate facts.
  - Pre-flight Questions:
    - Data source: LOG-SKILL01 specification, fresh repo tree, and pinned upstream metadata/path inspection.
    - Display permission: N/A; no UI surface.
    - DB read flow: N/A; static contracts only.
    - DB write flow: N/A; no persistence.
    - Render location: skills/logistics/ Markdown and JSON files.
    - UI behavior flow: N/A; host-neutral pack.
    - Docker runtime: N/A; no app/runtime change.
    - Playwright target: N/A; no UI behavior.
    - Behavior test: exact five IDs, frontmatter fields, required sections, provenance, and invariants.
    - Cleanup/quarantine: do not create upstream copies or generated caches; ignored bytecode is rebuildable.
    - External side effects: none.
    - N/A notes: Anvien impact is N/A for a missing new surface; Git tree evidence is used for absence.
  - Work Steps:
    1. Add the five contracts, pack index, stable/dynamic context boundary, workflow, authority invariants, and upstream classifications.
       - UI flow check: N/A; no UI.
       - DB/data flow check: assert no persistence/runtime dependency.
       - Render location check: each skill is independently readable and index paths resolve.
       - Mini QA for each completed implementation slice (MUST): N/A; static contract parser is sufficient.
       - Evidence target: E1-P1A-CONTRACT1 and E1-P1A-PROV1.
    2. Parse JSON/frontmatter and verify the exact five-skill index and source classifications.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: required contract sections and dynamic-data rules are present.
       - Mini QA for each completed implementation slice (MUST): N/A; focused unittest.
       - Evidence target: E1-P1A-TEST1 and E1-P1A-BOUND1.
  - Implementation Gate:
    - Before editing, P0 actual-status is complete; no existing skills/loader path exists in the fresh tree; no runtime integration is authorized.
  - Acceptance:
    - Source: five contracts, index, and provenance are present with no copied upstream source text.
    - Runtime/UI: N/A; direct parsing proves host-neutral loadability.
    - DB/data: no writes or live values.
    - Behavior test: exact five IDs and required metadata/sections pass.
    - Cleanup/quarantine: no vendor tree, loader, or temporary generated artifact.
    - Evidence IDs: E1-P1A-CONTRACT1..E1-P1A-BOUND1.
    - Actual-status rows refreshed: pack surface and business context missing -> correct.
  - Evidence Targets: contract parser, index path resolution, provenance and invariant scan.
  - Actual-status Update: mark P1-A correct and authorize P1-B only.
  - Commit Boundary: no intermediate commit; preserve final allowlist for the single candidate commit.

- [x] P1-B: Add source-preserving intake normalization and complete/incomplete fixtures.
  - Goal: turn loose customer messages into a structured checklist with explicit unknowns and multi-lot support.
  - Scope Boundary:
    - Editable: skills/logistics/reference/intake.py, local common helper if needed, fixtures A/C, focused intake tests.
    - Inspect-only: customer intake contract and existing app customer modules.
    - Preserve-only: existing customer UI/database behavior and all non-pack tests.
    - Out of scope: route selection, CBM inference, goods classification, CRM, or database writes.
  - Non-Goals: verification of customer claims or automatic shipment creation.
  - Pre-flight Questions:
    - Data source: explicit request mapping/message and customer_intake contract.
    - Display permission: N/A; pure return object.
    - DB read flow: N/A; no DB.
    - DB write flow: N/A; no write.
    - Render location: reference function result and JSON fixtures.
    - UI behavior flow: N/A; direct caller boundary.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: complete fixture, incomplete fixture, multi-lot preservation, and input immutability.
    - Cleanup/quarantine: static fixture/in-memory only.
    - External side effects: none.
    - N/A notes: customer message remains unverified data.
  - Work Steps:
    1. Implement canonical customer, shipment, cargo, factory_lots, and commercial_requirements normalization with aliases and UNKNOWN.
       - UI flow check: N/A.
       - DB/data flow check: prove no database/app imports and no input mutation.
       - Render location check: status and missing_information are visible in the returned object.
       - Mini QA for each completed implementation slice (MUST): N/A; direct unittest.
       - Evidence target: E1-P1B-INTAKE1.
    2. Run complete/incomplete/multi-lot fixture tests and compile the affected reference package.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: NEEDS_CUSTOMER_INPUT is emitted for absent Incoterm, CBM, and pickup.
       - Mini QA for each completed implementation slice (MUST): N/A; focused unittest.
       - Evidence target: E1-P1B-TEST1 and E1-P1B-BOUND1.
  - Implementation Gate:
    - P1-A contract/index tests pass and the normalizer remains a pure local function.
  - Acceptance:
    - Source: required minimum fields and multi-lot shape are represented.
    - Runtime/UI: complete input returns READY; missing input returns NEEDS_CUSTOMER_INPUT with UNKNOWN.
    - DB/data: input is not mutated and nothing is persisted.
    - Behavior test: fixtures A/C and a two-lot case pass.
    - Cleanup/quarantine: no app runtime artifact is generated.
    - Evidence IDs: E1-P1B-INTAKE1..E1-P1B-BOUND1.
    - Actual-status rows refreshed: customer intake missing -> correct.
  - Evidence Targets: intake output shape, missing fields, multi-lot preservation, import boundary.
  - Actual-status Update: mark intake correct and authorize P2-A.
  - Commit Boundary: no intermediate commit; preserve final allowlist for the single candidate commit.

### P2: Payment, compliance, and quotation

- Phase Goal: add deterministic payment/compliance reference behavior and a no-fabrication quote layer.
- Phase Boundary:
  - In scope: pure payment, compliance, quote reference modules, fixtures B/D and quote data in A, focused tests.
  - Out of scope: existing finance/quotation writers, customs systems, FX APIs, payment execution, invoices, and declarations.
  - Dependencies: P1 contracts and intake shape.
- Phase Implementation Rule: implement P2-A, verify and record it, refresh actual-status, then implement P2-B.
- Ordered Slice List:
  - P2-A: Add Decimal USD/RMB payment scenarios and fail-closed compliance check.
  - P2-B: Add source-labelled quote reasoning with explicit missing dynamic data.

- [x] P2-A: Add Decimal USD/RMB payment scenarios and fail-closed compliance check.
  - Goal: calculate explicit supplied scenarios with an auditable trace and stop on value inconsistencies.
  - Scope Boundary:
    - Editable: skills/logistics/reference/payment.py, common helper if needed, fixtures B/D, focused payment tests.
    - Inspect-only: existing core/payment_logic.py and payment-related app docs.
    - Preserve-only: existing app payment allocation/persistence and all production data.
    - Out of scope: transfer execution, concealment, undervaluation, customs-value advice, or live FX retrieval.
  - Non-Goals: legal approval or transaction authorization.
  - Pre-flight Questions:
    - Data source: explicit payload, timestamped FX snapshot, fee source/manual input, and discrepancy fields.
    - Display permission: N/A; pure structured result.
    - DB read flow: N/A; no DB.
    - DB write flow: N/A; no write.
    - Render location: payment result with amounts and calculation_trace.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: exact USD/RMB arithmetic, missing FX, authorization gate, and compliance stop.
    - Cleanup/quarantine: in-memory payloads and static fixtures only.
    - External side effects: none.
    - N/A notes: returned amount is an estimate of supplied inputs, never an instruction.
  - Work Steps:
    1. Implement Decimal formulas, timestamp/source validation, fee provenance gates, and ordered trace entries.
       - UI flow check: N/A.
       - DB/data flow check: no import of existing writers or database.
       - Render location check: amounts and every derived stage are in the returned trace.
       - Mini QA for each completed implementation slice (MUST): N/A; direct unittest.
       - Evidence target: E2-P2A-PAY1.
    2. Implement consistency assessment and run fixture B/D plus missing-input tests.
       - UI flow check: N/A.
       - DB/data flow check: no payment instruction or external side effect.
       - Render location check: discrepancy status and required documents are explicit.
       - Mini QA for each completed implementation slice (MUST): N/A; focused unittest.
       - Evidence target: E2-P2A-COMP1 and E2-P2A-TEST1.
  - Implementation Gate:
    - Intake/contract tests pass; existing payment writer stays preserve-only; no dynamic source can be silently defaulted.
  - Acceptance:
    - Source: Scenario A/B formulas and compliance stop are explicit.
    - Runtime/UI: exact deterministic outputs and trace stages pass.
    - DB/data: no writes and no payment instruction.
    - Behavior test: missing FX returns NEEDS_CUSTOMER_INPUT; discrepancy returns COMPLIANCE_REVIEW_REQUIRED.
    - Cleanup/quarantine: no network/credential/runtime artifacts.
    - Evidence IDs: E2-P2A-PAY1..E2-P2A-BOUND1.
    - Actual-status rows refreshed: payment/compliance missing -> correct.
  - Evidence Targets: arithmetic values, trace sequence, source gates, compliance output.
  - Actual-status Update: mark payment/compliance correct and authorize P2-B.
  - Commit Boundary: no intermediate commit; preserve final allowlist for the single candidate commit.

- [x] P2-B: Add source-labelled quote reasoning with explicit missing dynamic data.
  - Goal: produce a quote-shaped estimate without turning pricing advice or missing dynamic data into cost truth.
  - Scope Boundary:
    - Editable: skills/logistics/reference/quote.py, fixture A quote data, focused quote tests.
    - Inspect-only: quote_builder contract and existing quotation modules.
    - Preserve-only: core/quotations.py, finance ledger, quote persistence, and app UI.
    - Out of scope: live freight/FX/customs/tax APIs, invoices, declarations, or industry-average defaults.
  - Non-Goals: acceptance of a quote or commercial authorization.
  - Pre-flight Questions:
    - Data source: normalized intake, explicit service lines, source/manual cost inputs, and FX snapshot.
    - Display permission: N/A; pure result.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: quote object with lines, totals, missing_information, risks, and calculation_trace.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: complete quote and missing freight/FX source case.
    - Cleanup/quarantine: static fixture/in-memory only.
    - External side effects: none.
    - N/A notes: pricing strategy is advisory and cannot create cost arithmetic.
  - Work Steps:
    1. Implement line classification, source/manual gating, optional FX conversion, quote identity/validity, and trace.
       - UI flow check: N/A.
       - DB/data flow check: no quotation writer or persistence import.
       - Render location check: all required quote fields and typed statuses are returned.
       - Mini QA for each completed implementation slice (MUST): N/A; direct unittest.
       - Evidence target: E2-P2B-QUOTE1.
    2. Test complete and incomplete quote paths and verify no fabricated total or strategy-derived cost.
       - UI flow check: N/A.
       - DB/data flow check: input immutability and no write.
       - Render location check: missing dynamic inputs remain visible and status is INCOMPLETE.
       - Mini QA for each completed implementation slice (MUST): N/A; focused unittest.
       - Evidence target: E2-P2B-TEST1 and E2-P2B-BOUND1.
  - Implementation Gate:
    - Payment/reference boundaries are passing; quote code is separate from existing app quotation authority.
  - Acceptance:
    - Source: all requested cost/price labels and authority boundaries exist.
    - Runtime/UI: complete fixture yields reviewable estimate; missing data yields incomplete quote.
    - DB/data: no persistence or mutation.
    - Behavior test: missing freight/FX cannot produce a complete selling total.
    - Cleanup/quarantine: no live API/config/cache artifact.
    - Evidence IDs: E2-P2B-QUOTE1..E2-P2B-BOUND1.
    - Actual-status rows refreshed: quote builder missing -> correct.
  - Evidence Targets: cost labels, dynamic gates, output shape, no-fabrication test.
  - Actual-status Update: mark quote correct and authorize P3-A.
  - Commit Boundary: no intermediate commit; preserve final allowlist for the single candidate commit.

### P3: Sales enablement

- Phase Goal: add fact-safe logistics response support and complete the requested domain surface.
- Phase Boundary:
  - In scope: sales contract/reference module, eight objection cases, focused sales tests, final bounded validation.
  - Out of scope: CRM, Zalo, autonomous messaging, lead generation, retention, and app sales UI.
  - Dependencies: P1/P2 contracts and reference outputs.
- Phase Implementation Rule: implement P3-A, verify and record it, then run the closure lane.
- Ordered Slice List:
  - P3-A: Add structured sales enablement and objection library.

- [x] P3-A: Add structured sales enablement and objection library.
  - Goal: give a human sales owner safe explanation, objection, FAQ, handoff, and next-action support.
  - Scope Boundary:
    - Editable: skills/logistics/reference/sales.py and focused sales tests.
    - Inspect-only: sales_enablement contract and upstream 71-sales-enablement/69-retention references.
    - Preserve-only: existing sales UI, CRM, messaging, and outbound systems.
    - Out of scope: any send/persist operation, unsupported promise, or competitor factual claim.
  - Non-Goals: autonomous communications or customer relationship automation.
  - Pre-flight Questions:
    - Data source: static safe response library and caller-supplied verified facts with source.
    - Display permission: N/A; advisory return object.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: structured response object.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: eight objection keys, output structure, promise guard, and source-gated FACT.
    - Cleanup/quarantine: static data only.
    - External side effects: none; no message transport.
    - N/A notes: unknown facts become assumptions/evidence requests.
  - Work Steps:
    1. Add the eight-key library and response builder with FACT/SALES_ARGUMENT/ASSUMPTION separation.
       - UI flow check: N/A.
       - DB/data flow check: no CRM/message/database import.
       - Render location check: draft, next action, evidence needed, and human review flag are present.
       - Mini QA for each completed implementation slice (MUST): N/A; direct unittest.
       - Evidence target: E3-P3A-SALES1.
    2. Run objection coverage, forbidden-promise, and verified-fact source tests.
       - UI flow check: N/A.
       - DB/data flow check: no external side effect.
       - Render location check: can_send remains false and unsupported guarantees are absent.
       - Mini QA for each completed implementation slice (MUST): N/A; focused unittest.
       - Evidence target: E3-P3A-TEST1 and E3-P3A-BOUND1.
  - Implementation Gate:
    - quote and payment outputs are available as advisory inputs; no app messaging path is in scope.
  - Acceptance:
    - Source: required objections and structured layers exist.
    - Runtime/UI: pure response builder returns safe human-review output.
    - DB/data: no external write or send.
    - Behavior test: eight objections and source-gated fact handling pass.
    - Cleanup/quarantine: no profile, transport, or generated runtime artifact.
    - Evidence IDs: E3-P3A-SALES1..E3-P3A-BOUND1.
    - Actual-status rows refreshed: sales enablement missing -> correct; all five skills correct.
  - Evidence Targets: objection coverage, output schema, safe-language scan, isolation.
  - Actual-status Update: mark all five behaviors correct and authorize P4.
  - Commit Boundary: no intermediate commit; preserve final allowlist for the single candidate commit.

### P4: Review, cleanup, and one-candidate closure

- Phase Goal: independently review the exact candidate scope, remove only dead work created by this task, run final focused validation, and create one clean local candidate commit.
- Phase Boundary:
  - In scope: supervisor report, plan/evidence/benchmark/actual-status refresh, decision log, final allowlisted commit.
  - Out of scope: push, merge, deploy, release, production, broad regression, and unrelated dirty-worktree cleanup.
  - Dependencies: P1/P2/P3 acceptance and final focused validation.
- Phase Implementation Rule: do not close until supervisor PASS, no dead task-created artifacts, and final candidate identity checks are complete.

- [x] P4-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: independently verify source, tests, provenance, diff allowlist, and all authority boundaries.
  - Work Steps:
    1. Review the current source and coder report against this plan and current GitHub base.
    2. If rejected, return only the failed scope to implementation, re-run focused checks, and review again.
  - Implementation Gate: P1/P2/P3 evidence is current and no unresolved same-scope blocker exists.
  - Acceptance: supervisor writes PASS with no residual unverified same-invariant surface.

- [x] P4-B: Remove dead work created during this plan.
  - Goal: ensure only useful pack, fixtures, tests, standard plan files, decision log, and required reports remain in the task-created diff.
  - Work Steps:
    1. Review the exact task-created allowlist and remove only obsolete task-created artifacts.
    2. Verify no vendor tree, loader, cache, temp output, rejected approach, or unrelated app/P2P file is staged.
  - Implementation Gate: cleanup targets are created by this task and not user work.
  - Acceptance: final allowlist is minimal; unrelated source and the deleted checkout remain untouched.

- [x] P4-C: Close the plan.
  - Goal: run final focused validation and create the one clean candidate commit from the fresh GitHub base.
  - Work Steps:
    1. Run parser/frontmatter/schema, fixture, arithmetic, quote, compliance, sales, compile, and targeted git diff --check validation.
    2. Run Anvien detect-changes if available; record unavailable status if the graph/index cannot be used.
    3. Stage only the explicit LOG-SKILL01 allowlist; verify candidate SHA/tree/base/tree/clean worktree and exact changed files.
    4. Create exactly one local candidate commit; verify no push, production touch, P2P core change, or duplicate workspace.
  - Implementation Gate: P4-A and P4-B pass; all required validation has current output.
  - Acceptance: final evidence records candidate identity and terminal verdict LOG_SKILL01_GITHUB_CANONICAL_CANDIDATE_READY_FOR_OWNER_GATE.

## Risk Notes

- The original local workspace was intentionally deleted and must not be restored or used.
- GitHub main is the only task authority; any prior local SHA is historical context only unless current ancestry proves relevance.
- The workspace is sparse/shallow/filtered to keep disk use bounded. Do not expand it with unnecessary vendor/runtime directories.
- Existing Logistics application code handles production-oriented payment/quotation behavior; new reference modules must remain isolated and non-authoritative.
- Upstream plugin metadata reports version 3.7.0 while no v3.7.0 tag was returned; record the distinction.
- Dynamic facts and legal/customs outcomes require current source/owner review and never become permanent context by default.

## Closure note

P4 technical review passed. The exact staged allowlist passed focused
validation, the supervisor report is `PASS`, generated Anvien side effects were
removed, and the branch is ready for the one local candidate commit. The
candidate SHA/tree and clean-worktree state are captured by the final terminal
verification and return packet. Owner gate remains required; no push, merge,
release, deploy, or production action is included.
