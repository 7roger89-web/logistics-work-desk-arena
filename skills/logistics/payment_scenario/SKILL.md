---
id: logistics.payment_scenario
version: 0.1.0
status: foundation
purpose: Calculate supplied USD or authorized China-side RMB payment scenarios with deterministic traceable arithmetic.
triggers:
  - factory payment currency or fee flow needs review
  - quotation needs a payment-cost input
required_inputs:
  - scenario A or scenario B
  - explicit monetary inputs
  - timestamped FX snapshot with source
  - fee amounts with source or manual-input markers
optional_inputs:
  - commercial value fields for consistency review
  - document/clarification notes
output_contract: Status, scenario, amounts, calculation_trace, missing_information, compliance_review, and authority fields.
dependencies:
  - logistics.business_context
  - logistics.customer_intake
dynamic_data_requirements:
  - CURRENT_FX_REQUIRES_TIMESTAMPED_SOURCE
  - bank, wire, intermediary, and conversion fees require explicit source or manual input
authority_boundary: Arithmetic is an estimate of supplied inputs only; it is not a payment instruction, transfer execution, invoice, customs value, or legal approval.
unknown_behavior: Return NEEDS_CUSTOMER_INPUT with missing sources/values; explicit commercial mismatch returns COMPLIANCE_REVIEW_REQUIRED and stops calculation.
provenance: LOG-SKILL01 specification; pricing concepts from ai-business-skills skills/vi/17-pricing-strategy are concept-only.
---

# logistics.payment_scenario

## Purpose

Provide a deterministic calculation record for two legitimate review scenarios.
The function uses decimal arithmetic and exposes each derived amount. It does
not move money or tell anyone how to conceal a commercial value.

## Scenario A — factory receives USD

Required inputs are invoice amount in USD, bank service fee in USD, wire fee
in USD, bank conversion fee in VND, and a USD/VND FX snapshot. The calculation
converts the VND fee to USD, subtracts all fees from the invoice amount, then
converts the received USD amount to VND.

`INPUT → RATE → FEE → INTERMEDIATE_AMOUNT → FINAL_AMOUNT`

## Scenario B — factory receives RMB

Required inputs are source USD, transfer fee in USD, intermediary fee in CNY,
USD/CNY FX, and an explicit confirmation that the China-side flow is
authorized. The calculation subtracts the USD transfer fee, converts the net
USD to CNY, then subtracts the intermediary fee.

An absent or false authorization confirmation never becomes a transfer
instruction. The reference output remains review-only.

## Compliance boundary

Before arithmetic, compare explicit invoice, commercial, payment, declared, or
customs values when supplied. Any amount or currency mismatch returns
`COMPLIANCE_REVIEW_REQUIRED`, lists documents/clarifications, and contains no
evasion, concealment, undervaluation, or false-declaration guidance.

## Trace and source rules

- Every calculated number has a formula/trace stage and source-linked inputs.
- FX must include `source`, timezone-aware `captured_at`, and the requested
  rate.
- Fees must carry `fee_sources` entries or a manual-input marker.
- Missing dynamic data is not permission to estimate.

## Examples

- USD and RMB fixture scenarios produce stable Decimal-derived output.
- A mismatch between invoice and declared values fails closed before payment
  arithmetic.

## Provenance

The separation between strategic pricing advice and explicit scenario
calculation is concept-only reuse from the upstream pricing strategy pattern.
All formulas, compliance boundaries, and output wording are original
LOG-SKILL01 domain content.
