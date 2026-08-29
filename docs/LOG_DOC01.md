# LOG-DOC01 — Bounded Document Evidence Extraction

LOG-DOC01 extracts structured evidence from a bounded set of customer-provided documents and adapts that evidence into the existing LOG-TRADE01 contracts. It does not perform legal analysis, HS finalization, tariff calculation, import approval, licence sufficiency, or hazard conclusions.

## Supported document types

The V0.1 scope is intentionally limited to `PRODUCT_CATALOGUE`, `TECHNICAL_DATASHEET`, `PRODUCT_LABEL_OR_NAMEPLATE`, `SDS_MSDS`, `CERTIFICATE`, and `UNKNOWN_DOCUMENT`. A certificate whose explicit standard is ISO 13485 is represented through the existing canonical `DocumentType.ISO_13485` contract.

## Canonical reuse

The implementation reuses the following LOG-TRADE01 types and functions rather than creating parallel trade ontology objects:

| Canonical file | Reused contract |
|---|---|
| `core/trade_compliance/models.py` | `DocumentType`, `DocumentEvidence`, `ProductIdentity`, `SourceRecord`, `EvidenceStatus`, `SourceAuthority` |
| `core/trade_compliance/identity.py` | `normalize_product_identity` |
| `core/trade_compliance/evidence.py` | `assess_document`, `build_evidence_request_plan` |

`core/document_extraction.py` contains only document-artifact, structured-extraction, provenance, security, and adapter-seam types. `to_trade_document_evidence`, `to_product_identity`, and `build_trade_evidence_plan` are narrow adapters into the canonical contracts.

## Decision boundary

The extraction status describes extraction quality only. Raw OCR or parser text is not a verified fact. Document presence, validity, relevance, and sufficiency remain separate fields. Missing fields remain missing. Conflicts are retained in `StructuredExtraction.conflicts` and produce `REVIEW_REQUIRED`. An incomplete SDS never produces `NON_HAZARDOUS`. ISO 13485 evidence is retained but never converted into import approval.

`TRADE_COMPLIANCE_DECISION=NOT_PERFORMED`: LOG-DOC01 does not call the regulatory assessment or HS/tariff decision functions. LOG-TRADE01 remains responsible for interpreting evidence under its existing fail-closed rules.

## Optional parser adapters

Docling and PaddleOCR are represented by injected adapter callables. No heavy dependency, model weight, or cache is added. The repository reports `DOCLING_RUNTIME_PROVEN=NO` and `PADDLEOCR_RUNTIME_PROVEN=NO` unless a runtime is actually installed and successfully invoked by a caller.

## Security boundary

`DocumentArtifact` rejects path traversal, NUL bytes, executable/script/macro extensions, script markers, oversize payloads, oversize text, invalid page counts, and page counts above the bounded limit. It stores a SHA-256 content digest and retains source URL, page mapping, extraction method, and raw text for provenance. The implementation performs no arbitrary execution and creates no temporary files.

## Validation

The focused test module validates complete datasheet extraction, missing-field fail-closed behavior, complete and incomplete SDS handling, ISO 13485 negative inference, conflict preservation, provenance, security boundaries, unknown-document handling, optional adapter behavior, and mapping into the actual LOG-TRADE01 contract surface.
