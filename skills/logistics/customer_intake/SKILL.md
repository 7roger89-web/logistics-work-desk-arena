---
id: logistics.customer_intake
version: 0.1.0
status: foundation
purpose: Transform a loose customer message into a source-preserving structured shipment checklist.
triggers:
  - customer asks for logistics service or quotation
  - sales owner receives new shipment requirements
required_inputs:
  - customer message or explicit request mapping
optional_inputs:
  - multiple factory lots
  - known supplier quotation or payment notes
output_contract: Structured customer, shipment, cargo, factory_lots, commercial_requirements, missing_information, and authority fields.
dependencies:
  - logistics.business_context
dynamic_data_requirements:
  - none for normalization; downstream skills require their own current sources
authority_boundary: Customer statements remain unverified input; this skill does not create a shipment, classify goods, choose a route, or verify customs capability.
unknown_behavior: Emit UNKNOWN for absent values and NEEDS_CUSTOMER_INPUT for missing minimum fields; never infer CBM, Incoterm, route, export capability, or delivery promise.
provenance: LOG-SKILL01 specification; template adapted from ai-business-skills skills/vi/20-brief-client-intake/SKILL.md.
---

# logistics.customer_intake

## Purpose

Turn an informal customer message into the next skill's checklist. Preserve
explicit values, keep missing values visible as `UNKNOWN`, and state exactly
what the customer or sales owner still needs to supply.

## Required output model

### Customer

`company`, `contact_person`, `phone`, and `sales_owner`.

### Shipment

`origin`, `destination`, `incoterm`, `transport_mode`,
`requested_delivery_date`, and `goods_description`.

### Cargo

`package_count`, `package_type`, `dimensions`, `cbm`, `gross_weight`,
`chargeable_basis`, `special_handling`, and
`dangerous_or_restricted_goods`.

### Factory / Supplier

`factory_lots` is a list. Each lot carries `factory_name`, `pickup_address`,
`contact`, `phone`, `cargo_ready_date`, `export_capability`,
`invoice_payment_currency`, and `notes`. Multiple lots are preserved as
separate entries and are not merged without an explicit rule.

### Commercial requirements

`importer_entity`, `customs_requirement`, `entrusted_import_requirement`,
`payment_requirement`, `requested_quotation_currency`, and
`customer_specific_notes`.

## Rules

- `READY` means the minimum required fields are present, not that the shipment
  is verified or accepted.
- Any missing minimum field changes status to `NEEDS_CUSTOMER_INPUT`.
- A customer message is not a verified shipment fact.
- Do not calculate CBM from dimensions, infer an Incoterm, select Hữu Nghị,
  Tân Thanh, or Chi Ma, classify restricted goods, or infer factory export
  capability.
- No database write or shipment creation occurs at this boundary.

## Examples

- A complete request can be passed to `logistics.quote_builder`.
- A request without CBM, Incoterm, or pickup address returns
  `NEEDS_CUSTOMER_INPUT` and lists those paths.

## Provenance

The intake questions and downstream handoff shape are adapted from the upstream
client-intake pattern. Field names, logistics rules, and all wording here are
domain-specific LOG-SKILL01 content.
