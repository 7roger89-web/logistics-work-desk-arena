# LOG-TRADE01 trade-compliance foundation

This is a small pure-Python domain boundary for the first China/foreign-origin to Vietnam import workflow. It is not a tariff database, legal database, crawler, customs declaration engine, or autonomous classifier.

## Contract

- `ProductIdentity` is normalized from customer input and remains `NORMALIZED_UNVERIFIED`.
- `FieldState` distinguishes `PROVIDED`, `REQUIRED_FOR_THIS_PRODUCT`, `NOT_RELEVANT`, and `UNKNOWN`.
- `HSAssessment` emits hypotheses only. It never returns a final HS classification.
- `EvidenceRequestPlan` is conditional by product category. Document presence, validity, relevance, and sufficiency are independent.
- `SourceRecord` preserves jurisdiction, authority, URL, retrieval/effective dates, product/HS scope, conclusion, confidence, and evidence status.
- `RegulatoryAssessment` withholds importability and regulatory conclusions when the official source is absent, stale, or conflicting.
- `TradeTaxSnapshot` separates MFN, preferential, VAT, origin evidence, and FTA eligibility. Rates are accepted only from a scoped, current official source and an explicitly confirmed HS code.
- `TaxCalculationResult` is incomplete unless its inputs are explicit and its snapshot is verified; a calculated result contains a formula/value trace.

Tax rates in this module are decimal fractions (`0.10` means 10%), never percentage display values. The calculator treats an explicitly supplied `0` as data; it never assumes an omitted other-tax amount is zero.

The bundled `source_registry.json` contains official Vietnamese discovery entry points only. It has no live retrieval and no tariff rates.
