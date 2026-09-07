"""LOG-DOCGEN-01 — bounded Shipment Document Pack Generator.

V1 supports HDNT, PL, HDMB and PXK generation for a single shipment.
Debit USD is explicitly out of scope and shown as deferred in the UI.

This package intentionally implements only what is needed to make V1 work
correctly and safely:
  * authority (approved Company / Agent master)  -> authority.py
  * locked business rules (threshold, VAT, PXK)  -> rules.py
  * OOXML template mutation (narrow, non-destructive) -> template_engine.py
  * orchestration / metadata / revision / audit -> generator.py
"""

from core.docgen.generator import (
    build_document_pack,
    generate_document,
    issue_document,
    supersede_document,
)
from core.docgen.rules import (
    Readiness,
    compute_goods_totals,
    decide_applicable_documents,
    evaluate_document_readiness,
    normalize_goods_line,
)

__all__ = [
    "build_document_pack",
    "generate_document",
    "issue_document",
    "supersede_document",
    "Readiness",
    "compute_goods_totals",
    "decide_applicable_documents",
    "evaluate_document_readiness",
    "normalize_goods_line",
]
