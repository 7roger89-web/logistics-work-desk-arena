---
id: logistics.sales_enablement
version: 0.1.0
status: foundation
purpose: Support human logistics sales with fact-safe quote explanation, follow-up, objection handling, FAQ, handoff, and next action.
triggers:
  - customer asks a quotation or service-scope question
  - customer raises a logistics objection
  - sales owner needs a structured handoff or follow-up draft
required_inputs:
  - objection key or customer question
  - optional verified facts with source
optional_inputs:
  - quote output
  - intake output
  - payment scenario output
  - customer-specific notes
output_contract: Human-review response containing FACT, SALES_ARGUMENT, ASSUMPTION, reply draft, FAQ/objection data, handoff, evidence needed, and next action.
dependencies:
  - logistics.business_context
  - logistics.customer_intake
  - logistics.quote_builder when explaining a quote
dynamic_data_requirements:
  - delivery, customs, tax, border, freight, FX, and payment claims require current sourced evidence
authority_boundary: Advisory copy only; never auto-send, promise clearance/delivery/tax treatment, or turn an assumption into a verified fact.
unknown_behavior: Label unsourced claims as ASSUMPTION, request evidence, and keep can_send false with human review required.
provenance: LOG-SKILL01 specification; template adapted from ai-business-skills skills/vi/71-sales-enablement/SKILL.md; retention skill 69 is not used.
---

# logistics.sales_enablement

## Purpose

Give a sales owner a reusable, logistics-specific response structure. It
explains quotation scope, prepares a follow-up, handles common objections,
answers FAQs, identifies service differentiation, and recommends the next
human action.

## Content layers

- `FACT`: only caller-supplied values with an explicit verification flag and
  source.
- `SALES_ARGUMENT`: safe explanation of process, scope, or differentiators;
  it is not evidence of a current shipment outcome.
- `ASSUMPTION`: an unverified condition that needs confirmation.

The response is always human-review-only. It cannot send Zalo/email/messages,
create a CRM record, or promise customs clearance, delivery time, or tax
treatment without explicit evidence and contractual authority.

## Initial objection library

The reference library covers:

- `price_higher` — “Giá bên anh cao hơn.”
- `competitor_cheaper` — “Bên khác báo rẻ hơn.”
- `delivery_time` — “Bao lâu hàng về?”
- `customs_clearance` — “Có chắc thông quan được không?”
- `delay` — “Nếu hàng bị chậm thì sao?”
- `why_information` — “Tại sao cần cung cấp nhiều thông tin như vậy?”
- `factory_rmb` — “Factory chỉ nhận RMB.”
- `not_ready` — “Tôi chưa muốn quyết định.”

Each entry contains a reply draft, sales arguments, assumptions, evidence
needed, and a next action. The drafts use conditional language and do not
make unsupported guarantees.

## Examples

- Use `factory_rmb` only to explain what information an authorized payment
  scenario needs; do not provide a transfer instruction.
- Use `delivery_time` to ask for cargo-ready date and route evidence; do not
  state a guaranteed arrival time.

## Provenance

The one-pager/objection/handoff shape is adapted from the upstream sales
enablement template. Logistics language, source-gated facts, and safety
boundaries are original LOG-SKILL01 content. The upstream retention pattern is
explicitly not used in this tranche.
