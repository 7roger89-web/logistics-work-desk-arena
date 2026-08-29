---
id: logistics.business_context
version: 0.1.0
status: foundation
purpose: Provide stable China-to-Vietnam logistics domain context without embedding live commercial facts.
triggers:
  - logistics workflow starts
  - another Logistics Skill Pack skill needs stable domain context
required_inputs:
  - none; stable context is declarative
optional_inputs:
  - current workflow stage
output_contract: STABLE_CONTEXT plus an explicit DYNAMIC_DATA boundary
dependencies:
  - none
dynamic_data_requirements:
  - current FX requires a timestamped source
  - current freight requires a source or manual input
  - customs, tax, tariff, border, supplier and regulation data require current evidence
authority_boundary: Context is guidance only; it is not a verified shipment fact, financial authority, invoice, customs declaration, or legal truth.
unknown_behavior: Keep dynamic values UNKNOWN and route them to the consuming skill; never fill them with historical or industry-average values.
provenance: LOG-SKILL01 specification; selective concepts from ai-business-skills 20, 17, 31 and 71.
---

# logistics.business_context

## Purpose

This is a small, stable context card for the China → Vietnam logistics
workflow. It can be read independently by the other four skills. It is not a
history dump and it intentionally contains no today's exchange rate, freight
price, customs result, tax/tariff value, supplier quotation, border condition,
or time-sensitive regulation.

## STABLE_CONTEXT

- Domain: China → Vietnam road transportation and related coordination.
- Customer types: importer, trader, factory, and SME.
- Commercial workflow: customer intake → requirement clarification → payment
  scenario review when needed → quotation → human sales follow-up → handoff.
- Transport workflow: China factory/agent coordination → pickup planning →
  cross-border road movement → Vietnam delivery coordination.
- Coordination actors: Vietnam sales/operations, China agent, factory/supplier,
  customs/service partners, and the customer/importer.
- Customs boundary: coordinate documents and service scope; do not promise
  clearance or tax treatment without current evidence and contractual authority.
- Entrusted import: may be considered where legally applicable and supported by
  the required parties/documents; it is not a default legal conclusion.
- Known route vocabulary: Hữu Nghị, Tân Thanh, and Chi Ma. A route mention is
  not proof that a shipment can use that border.
- Supported payment patterns: factory receives USD; factory receives RMB
  through an authorized China-side payment/agent flow. The payment skill only
  calculates supplied inputs and never executes a transfer.
- Quotation principles: separate known, estimated, customer-price, unknown,
  and assumption layers; source dynamic cost inputs; expose exclusions,
  validity, risks, and missing information.
- Margin/pricing principle: strategic pricing advice may inform a human offer,
  but it is not logistics-cost authority.
- Risk rules: preserve uncertainty, surface document/value mismatches, require
  human review for compliance-sensitive cases, and do not conceal or
  undervalue commercial values.
- Data authority rules: customer messages are unverified input; verified
  business values need an explicit source/owner check; quote, invoice, and
  customs declaration remain separate artifacts.

## DYNAMIC_DATA

The following must be supplied separately at the time of use:

- timestamped FX snapshot and source;
- current freight/vendor quotation and source or manual input;
- customs rules, tax/tariff information, and border conditions with current
  evidence;
- supplier/factory quotation, payment fees, bank fees, and other third-party
  costs with a source;
- current regulations or legal interpretations with a qualified review path.

Missing dynamic data is not permission to estimate. The consumer must return
the incomplete result and identify the missing source/input.

## Authority invariants

`AI_GENERATED_VALUE != VERIFIED_BUSINESS_VALUE`

`MARKETING_PRICING_ADVICE != ACTUAL_LOGISTICS_COST`

`MISSING_DYNAMIC_DATA != PERMISSION_TO_ESTIMATE`

`CUSTOMER_MESSAGE != VERIFIED_SHIPMENT_FACT`

`QUOTE != INVOICE`

`QUOTE != CUSTOMS_DECLARATION`

`RETRIEVED_REGULATION != AUTOMATIC_LEGAL_TRUTH`

`CURRENT_FX_REQUIRES_TIMESTAMPED_SOURCE`

`CURRENT_FREIGHT_REQUIRES_SOURCE_OR_MANUAL_INPUT`

`COMMERCIAL_VALUE_MISMATCH -> COMPLIANCE_REVIEW_REQUIRED`

## Examples

- Load this context before `logistics.customer_intake`, then pass only the
  relevant structured output to payment, quote, or sales support.
- Do not add a live USD/VND rate or a temporary border condition here.

## Provenance

Original domain content is written for LOG-SKILL01. Upstream material is
conceptual only; no upstream source text is copied into this contract.
