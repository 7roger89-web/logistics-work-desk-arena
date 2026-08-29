---
id: logistics.quote_builder
version: 0.1.0
status: foundation
purpose: Build a source-labelled, incomplete-by-default logistics quotation for human review.
triggers:
  - normalized shipment requirements are ready for pricing review
  - supplier, freight, customs/service, handling, domestic, bank, or entrusted-import costs need assembly
required_inputs:
  - customer/route/shipment summary
  - explicit service lines and cost basis
  - requested quote currency
optional_inputs:
  - timestamped FX snapshot
  - supplier or agent quotation
  - payment scenario result
  - pricing-strategy advice as advisory-only input
output_contract: Quote identity, customer, route, shipment summary, service lines, typed cost basis, selling price, FX, assumptions, exclusions, validity, risks, missing_information, and calculation_trace.
dependencies:
  - logistics.business_context
  - logistics.customer_intake
  - logistics.payment_scenario when payment cost is included
dynamic_data_requirements:
  - CURRENT_FREIGHT_REQUIRES_SOURCE_OR_MANUAL_INPUT
  - non-VND lines require a timestamped FX source for conversion
  - customs, tax, supplier, bank, and third-party costs require current source/manual input
authority_boundary: A quote is an advisory estimate for human review; it is not an invoice, customs declaration, finance ledger, tax conclusion, or acceptance.
unknown_behavior: Preserve UNKNOWN_COST and UNKNOWN selling totals, list missing sources/FX/identity/validity, and never use industry averages or marketing advice as cost.
provenance: LOG-SKILL01 specification; offer/value-stack concepts from ai-business-skills skills/vi/31-offer-design are concept-only and not financial authority.
---

# logistics.quote_builder

## Purpose

Assemble explicit logistics service lines into a reviewable quotation-shaped
object. The builder labels the evidence status of every line and remains
incomplete when dynamic business inputs are absent.

## Evidence labels

- `KNOWN_COST`: explicit cost with a source or manual-input marker.
- `ESTIMATED_COST`: explicit provisional cost with an explicit assumption and
  source/manual marker.
- `CUSTOMER_PRICE`: explicit selling price offered to the customer.
- `UNKNOWN_COST`: cost is absent, unsupported, or missing required dynamic
  source/FX evidence.
- `ASSUMPTION`: an explicit assumption carried into the output; it is not a
  verified business value.

Freight is dynamic. A freight amount without a source or manual input remains
`UNKNOWN_COST`, even if somebody supplies a plausible-looking number.

## Output discipline

The result includes quote ID/version where supplied, customer, route, shipment
summary, service lines, cost basis, selling price, quote currency, FX snapshot,
assumptions, exclusions, validity/expiry, risks, missing information, and a
calculation trace. A missing identity or expiry is visible as `UNKNOWN` rather
than generated silently.

Strategic pricing advice may be returned as `MARKETING_PRICING_ADVICE` for a
human, but it cannot enter logistics cost arithmetic. The invariant is:

`MARKETING_PRICING_ADVICE != ACTUAL_LOGISTICS_COST`

## Examples

- A VND-only quote with sourced freight and an explicit estimated domestic
  line can be `READY_FOR_REVIEW`.
- A USD freight line without source or timestamped FX remains `INCOMPLETE`;
  no industry-average price is inserted.

## Provenance

The value-stack and offer-clarity ideas are concept-only from the upstream
offer-design pattern. The cost labels, source gates, and logistics output are
original LOG-SKILL01 content.
