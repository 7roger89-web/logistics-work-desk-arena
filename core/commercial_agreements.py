"""Bounded commercial agreement & handoff domain for LOG-C13.

An agreement is the accepted commercial terms between the customer and
Truong Thanh: what was sold, under which Incoterm, with which payment terms,
who is responsible for what, which documents are required, and which
Shipment(s) execute it.

Key guarantees:
- An agreement keeps a frozen commercial snapshot of the accepted quote
  (quote id, quote reference, quote version at acceptance time). Later quote
  changes cannot silently change agreed terms.
- Recording payment terms is commercial only: 0 canonical finance writes.
- An AGREED agreement can never be silently overwritten; amendments create a
  new DRAFT revision through the bounded REVISED transition.
- Evidence states (AVAILABLE/MISSING/WAITING/UNKNOWN) are explicit; SIGNED is
  never inferred from filenames or free text.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping
from uuid import uuid4

EVIDENCE_STATES = ("AVAILABLE", "MISSING", "WAITING", "UNKNOWN")
AGREEMENT_STATUSES = ("DRAFT", "REVIEWING", "AGREED", "REVISED", "VOID")
Allowed_TRANSITIONS = {
    "DRAFT": {"REVIEWING", "VOID"},
    "REVIEWING": {"AGREED", "DRAFT", "REVISED", "VOID"},
    "AGREED": {"REVISED"},
    "REVISED": {"REVIEWING", "DRAFT", "VOID"},
    "VOID": set(),
}

HANDOFF_READY = "READY_FOR_OPERATIONS"
HANDOFF_COMMERCIAL_REVIEW = "NEEDS_COMMERCIAL_REVIEW"
HANDOFF_MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"
HANDOFF_STATES = (HANDOFF_READY, HANDOFF_COMMERCIAL_REVIEW, HANDOFF_MISSING_REQUIRED_DATA)

DEFAULT_PAYMENT_TERM_CHOICES = (
    "Đặt cọc trước",
    "Thanh toán trước thông quan",
    "Thanh toán trước khi giao hàng",
    "Thanh toán sau khi giao hàng",
    "Công nợ (credit term)",
)

DEFAULT_REQUIRED_DOCUMENTS = (
    "Commercial invoice",
    "Packing list",
    "Giấy phép / chứng từ hàng hóa (nếu có)",
    "Tờ khai hải quan (khi thực hiện ủy thác nhập khẩu)",
)

ENTRUSTED_DOCUMENT_REQUIREMENTS = (
    "Hợp đồng ủy thác nhập khẩu / biên bản xác nhận phạm vi",
    "Giấy phép chuyên ngành (nếu hàng thuộc diện cấp phép)",
    "Chứng từ giá trị hàng hợp pháp (invoice, hợp đồng mua hàng)",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_agreement_identity(now: date | None = None) -> tuple[str, str]:
    stamp = (now or date.today()).strftime("%Y%m%d")
    token = uuid4().hex[:8].upper()
    return f"AGR-{stamp}-{token}", f"AG-{stamp}-{token}"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _services_from_quote(quote: Mapping[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for index, line in enumerate(quote.get("service_lines") or [], start=1):
        lines.append({
            "line_no": index,
            "code": _text(line.get("code")),
            "service_name": _text(line.get("service_name")),
            "unit": _text(line.get("unit")) or "Lần",
            "qty": line.get("qty", 1),
            "currency": _text(line.get("currency")) or "VND",
            "sell_unit": line.get("sell_unit", 0),
            "calculation_snapshot": {
                "sell_total": line.get("sell_total"),
                "tax_pct": line.get("tax_pct", 0),
                "calculation_basis": line.get("calculation_basis", ""),
            },
            "source_reference": _text(line.get("cost_source")),
        })
    return lines


def _entrusted_terms_from_quote(quote: Mapping[str, Any]) -> dict[str, Any]:
    entrusted = dict(quote.get("entrusted_import") or {})
    fees = (quote.get("fees") or {}).get("entrusted_import") or {}
    basis_currency = str(entrusted.get("goods_currency") or "USD").upper()
    return {
        "active": bool(entrusted.get("active")),
        "rate_pct": entrusted.get("rate_pct", 0),
        "calculation_basis": f"{entrusted.get('goods_value')} {basis_currency} × {entrusted.get('rate_pct')}% theo tỷ giá báo giá ({fees.get('formula', '')})",
        "amount_vnd_snapshot": fees.get("amount_vnd"),
        "importer_of_record_scope": "Truong Thanh (bên nhập khẩu ủy thác) theo phạm vi thỏa thuận; không thay đổi tư cách hải quan thực tế.",
        "customer_responsibility": "Cung cấp chứng từ giá trị hàng hợp pháp, giấy phép chuyên ngành nếu có, và thông tin khai báo trung thực.",
        "truong_thanh_responsibility": "Thực hiện thủ tục nhập khẩu thay theo ủy thác, lập GNT đúng chứng từ, tuân thủ quy định hải quan.",
        "lawful_documentation": "Chứng từ phải khớp hàng thực tế; không tự động hóa khai báo sai lệch hay khai thấp giá trị.",
        "commercial_assumptions": [
            "Tỷ lệ phí do Sale nhập/duyệt; hệ thống không tự chọn 2% hay 3%.",
            "Chưa có policy high-value toàn cục được cấu hình (POLICY_NOT_CONFIGURED) trừ khi được cung cấp thật.",
            "Không tự động yêu cầu high-value review khi chưa có policy cấu hình.",
        ],
        "commercial_review_required": bool(fees.get("commercial_review_required")),
        "commercial_review_reasons": list(fees.get("commercial_review_reasons") or []),
        "source": "Snapshot từ báo giá đã chấp nhận; điều khoản thương mại, không phải bút toán.",
    }


def build_agreement_from_quote(quote: Mapping[str, Any], actor: str = "system", now: date | None = None) -> dict[str, Any]:
    """Create an agreement DRAFT frozen from an accepted quote's commercial terms."""
    agreement_id, agreement_no = new_agreement_identity(now)
    snapshot = dict(quote)
    return {
        "agreement_id": agreement_id,
        "agreement_no": agreement_no,
        "customer_id": _text(quote.get("customer_id")),
        "customer_name": _text(quote.get("customer_name")),
        "quote_id": _text(snapshot.get("id")),
        "quote_reference": _text(snapshot.get("quote_no")),
        "quote_version": int(snapshot.get("version") or 1),
        "quote_accepted_at": snapshot.get("updated_at") or "",
        "status": "DRAFT",
        "version": 1,
        "effective_date": str(now or date.today()),
        "commercial_snapshot": {
            "origin": _text(quote.get("origin")),
            "destination": _text(quote.get("destination")),
            "route": _text(quote.get("route")),
            "incoterm": _text(quote.get("incoterm")) or "EXW",
            "transport_mode": _text(quote.get("transport_mode")) or "Road",
            "goods_description": _text(quote.get("goods_description")),
            "expected_delivery_date": _text(quote.get("expected_delivery_date")),
            "service_lines": _services_from_quote(snapshot),
            "calculation_summary": {
                "selling_price_total_vnd": (snapshot.get("calculation") or {}).get("selling_price_total_vnd", 0),
                "estimated_margin_vnd": (snapshot.get("calculation") or {}).get("estimated_margin_vnd", 0),
                "base_currency": "VND",
                "not_finance_ledger": True,
                "source": "Calculation snapshot của báo giá đã chốt; không phải Finance Ledger.",
            },
            "fx_summary": {
                "rates_to_vnd": {str(k).upper(): v for k, v in dict((snapshot.get("fx_snapshot") or {}).get("rates_to_vnd") or {}).items() if str(k).upper() != "VND"},
                "note": "Tỷ giá báo giá tại thời điểm chốt; không phải tỷ giá giao dịch thực tế, không ghi đè lịch sử.",
            },
        },
        "entrusted_import_terms": _entrusted_terms_from_quote(snapshot),
        "payment_terms": {
            "selected": [],
            "credit_term_days": None,
            "due_date_trigger": "",
            "notes": "Điều khoản thanh toán thương mại; ghi nhận ở đây KHÔNG tạo payment, transaction, allocation hay event Finance Ledger nào.",
        },
        "responsibilities": {
            "truong_thanh": [
                "Thực hiện phạm vi dịch vụ đã bán theo báo giá đã chốt.",
                "Theo dõi factory lots, lịch lấy hàng và chứng từ vận chuyển trong phạm vi đã bán.",
            ],
            "customer_provides": [
                "Xác nhận điều khoản bằng văn bản/chữ ký (khi có thể).",
                "Cung cấp chứng từ giá trị hàng và thông tin khai báo trung thực.",
            ],
        },
        "required_documents": [
            {"name": name, "evidence_state": "UNKNOWN", "note": ""}
            for name in DEFAULT_REQUIRED_DOCUMENTS
        ],
        "factory_lots": deepcopy(quote.get("factory_lots") or []),
        "assumptions": list(quote.get("assumptions") or []),
        "unresolved_issues": [],
        "shipment_ids": [],
        "evidence": {
            "accepted_quotation": False,
            "signed_contract": False,
            "customer_confirmation": False,
            "entrusted_documentation": False,
            "notes": "",
            "source": "Bằng chứng được đánh dấu thủ công theo trạng thái AVAILABLE/MISSING/WAITING/UNKNOWN; không suy 'đã ký' từ tên file hay ghi chú.",
        },
        "status_history": [{"from": None, "to": "DRAFT", "at": _now(), "actor": str(actor or "system")}],
        "is_estimate_only_snapshot": True,
        "ledger_posted": False,
        "created_at": _now(),
        "updated_at": _now(),
        "is_deleted": False,
    }


def allowed_transitions(status: str) -> tuple[str, ...]:
    """Return the business-legal next statuses for an agreement status (display only).

    The transition itself is still enforced by :func:`transition_agreement`,
    which is the single source of truth; this helper only mirrors that map so a
    UI can offer the allowed choices without re-interpreting the rule.
    """
    return tuple(sorted(Allowed_TRANSITIONS.get(str(status or "").upper(), set())))


def transition_agreement(agreement: Mapping[str, Any], next_status: str, actor: str = "system") -> dict[str, Any]:
    current = str(agreement.get("status") or "DRAFT").upper()
    target = str(next_status or "").upper()
    if target not in AGREEMENT_STATUSES or (target != current and target not in Allowed_TRANSITIONS.get(current, set())):
        raise ValueError(f"Không thể chuyển thỏa thuận từ {current} sang {target}.")
    updated = deepcopy(dict(agreement))
    updated["status"] = target
    updated["version"] = int(updated.get("version") or 1) + (1 if target != current else 0)
    updated["updated_at"] = _now()
    history = list(updated.get("status_history") or [])
    if target != current:
        history.append({"from": current, "to": target, "at": _now(), "actor": actor})
    updated["status_history"] = history
    return updated


def _valid_evidence_state(value: Any) -> str:
    text = _text(value).upper()
    return text if text in EVIDENCE_STATES else "UNKNOWN"


def normalize_required_documents(documents: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(documents, Mapping):
        documents = list(documents.values())
    for index, item in enumerate(documents or [], start=1):
        if not isinstance(item, Mapping):
            continue
        name = _text(item.get("name")) or f"Chứng từ {index}"
        rows.append({
            "name": name,
            "evidence_state": _valid_evidence_state(item.get("evidence_state")),
            "note": _text(item.get("note")),
        })
    return rows


def validate_agreement(agreement: Mapping[str, Any]) -> tuple[bool, str]:
    agreement_id = _text(agreement.get("agreement_id"))
    quote_id = _text(agreement.get("quote_id"))
    status = _text(agreement.get("status"))
    version = int(agreement.get("version") or 0)
    if not agreement_id or not quote_id:
        return False, "Thỏa thuận phải có mã và tham chiếu báo giá trước khi lưu."
    if status not in AGREEMENT_STATUSES:
        return False, f"Trạng thái thỏa thuận không hợp lệ: {status}."
    if version < 1:
        return False, "Phiên bản thỏa thuận không hợp lệ."
    return True, ""


def prepare_agreement_for_persistence(agreement: Mapping[str, Any], actor: str = "system") -> dict[str, Any]:
    """Validate and stamp an agreement before the shared document writer is used.

    The request identity is stable per agreement version, making a retry an
    idempotent upsert. Provenance states explicitly that this is a commercial
    record: zero canonical finance writes are implied or performed here.
    """
    candidate = deepcopy(dict(agreement))
    candidate["required_documents"] = normalize_required_documents(candidate.get("required_documents"))
    candidate.setdefault("shipment_ids", [])
    candidate.setdefault("unresolved_issues", [])
    candidate.setdefault("evidence", {})
    evidence = dict(candidate["evidence"])
    for flag in ("accepted_quotation", "signed_contract", "customer_confirmation", "entrusted_documentation"):
        evidence.setdefault(flag, False)
    evidence.setdefault("notes", _text(evidence.get("notes")))
    candidate["evidence"] = evidence
    ok, message = validate_agreement(candidate)
    if not ok:
        raise ValueError(message)
    request_id = f"agr:{candidate['agreement_id']}:v{candidate['version']}"
    candidate["write_request_id"] = request_id
    candidate["id"] = candidate["agreement_id"]
    candidate["provenance"] = {
        "source": "LOG-C13 commercial agreement workspace",
        "actor": str(actor or "system"),
        "write_request_id": request_id,
        "agreement_version": candidate["version"],
        "status": candidate["status"],
        "estimate_only_snapshot": True,
        "ledger_posted": False,
        "updated_at": str(candidate.get("updated_at") or _now()),
    }
    candidate["is_estimate_only_snapshot"] = True
    candidate["ledger_posted"] = False
    return candidate


def handoff_readiness(agreement: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic commercial handoff readiness. No AI, material fields only."""
    reasons: list[str] = []
    quote_reference = _text(agreement.get("quote_id"))
    customer_id = _text(agreement.get("customer_id"))
    services = [line for line in agreement.get("commercial_snapshot", {}).get("service_lines") or [] if _text(line.get("service_name"))]
    lots = [lot for lot in agreement.get("factory_lots") or [] if _text(lot.get("factory_name"))]
    if not quote_reference or not customer_id or not services:
        return {
            "state": HANDOFF_MISSING_REQUIRED_DATA,
            "label": "Còn thiếu thông tin",
            "reasons": ["Thiếu báo giá đã chốt, khách hàng hoặc phạm vi dịch vụ đã bán; không thể bàn giao vận hành."],
            "blocks_operations": True,
            "source": "deterministic handoff readiness (material fields only)",
        }
    if not lots:
        reasons.append("Chưa có nhà máy/lô hàng material nào; Support không xác nhận được hàng bàn giao.")

    status = _text(agreement.get("status")).upper()
    evidence = dict(agreement.get("evidence") or {})
    if status != "AGREED":
        reasons.append(f"Thỏa thuận chưa được khách đồng ý (hiện tại: {status}); cần Sale xác nhận.")
    if not evidence.get("signed_contract") and not evidence.get("customer_confirmation") and not evidence.get("accepted_quotation"):
        reasons.append("Chưa có bằng chứng chấp nhận (signed contract / customer confirmation / báo giá được chấp nhận) được đánh dấu AVAILABLE.")
    for document in agreement.get("required_documents") or []:
        state = (_text(document.get("evidence_state")) or "UNKNOWN").upper()
        name = _text(document.get("name"))
        if state in ("MISSING", "WAITING"):
            reasons.append(f"Chứng từ '{name}' đang {state}." if state == "WAITING" else f"Chứng từ '{name}' MISSING.")
    issues = [str(issue) for issue in (agreement.get("unresolved_issues") or []) if _text(issue)]
    if issues:
        reasons.append(f"Còn {len(issues)} unresolved issue thương mại trước khi operations.")
    if reasons:
        return {
            "state": HANDOFF_COMMERCIAL_REVIEW,
            "label": "Cần Sale xác nhận",
            "reasons": reasons,
            "blocks_operations": False,
            "source": "deterministic handoff readiness (material fields only)",
        }
    return {
        "state": HANDOFF_READY,
        "label": "Sẵn sàng bàn giao vận hành",
        "reasons": [],
        "blocks_operations": False,
        "source": "deterministic handoff readiness (material fields only)",
    }


def _customer_name(customer_id: str, customers: Mapping[str, Mapping[str, Any]]) -> str:
    customer = customers.get(customer_id) if isinstance(customers, Mapping) else None
    if isinstance(customer, Mapping) and _text(customer.get("name")):
        return _text(customer.get("name"))
    return customer_id or "UNKNOWN"


def agreements_for_shipment(shipment_id: str, agreements: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return agreements that reference the given shipment (side-effect free)."""
    linked: list[dict[str, Any]] = []
    for agreement in (agreements.values() if isinstance(agreements, Mapping) else (agreements or [])):
        if not isinstance(agreement, Mapping):
            continue
        if str(shipment_id) in [str(item) for item in (agreement.get("shipment_ids") or [])]:
            linked.append(dict(agreement))
    return linked


def agreements_for_quote(quote_id: str, agreements: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    linked: list[dict[str, Any]] = []
    for agreement in (agreements.values() if isinstance(agreements, Mapping) else (agreements or [])):
        if not isinstance(agreement, Mapping):
            continue
        if _text(agreement.get("quote_id")) == _text(quote_id):
            linked.append(dict(agreement))
    return linked


def commercial_handoff_view(
    shipment: Mapping[str, Any] | None,
    agreement: Mapping[str, Any],
    quote: Mapping[str, Any] | None,
    customers: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the 16-question commercial handoff a Sale gives to Support."""
    snapshot = agreement.get("commercial_snapshot") or {}
    services = [line for line in snapshot.get("service_lines") or [] if isinstance(line, Mapping)]
    lots = [lot for lot in agreement.get("factory_lots") or [] if isinstance(lot, Mapping)]
    customer_id = _text(agreement.get("customer_id"))
    readiness = handoff_readiness(agreement)
    unresolved = [str(issue) for issue in (agreement.get("unresolved_issues") or []) if _text(issue)]
    assumptions = [str(item) for item in (agreement.get("assumptions") or []) if _text(item)]
    payment = dict(agreement.get("payment_terms") or {})
    responsibilities = dict(agreement.get("responsibilities") or {})
    entrusted = dict(agreement.get("entrusted_import_terms") or {})

    first_lot = lots[0] if lots else {}
    factory_lots_summary = [
        {
            "Lô": str(lot.get("lot_no") or index + 1),
            "Nhà máy": _text(lot.get("factory_name")),
            "Liên hệ": _text(lot.get("factory_contact")) or "UNKNOWN",
            "SĐT": _text(lot.get("factory_phone")) or "UNKNOWN",
            "Ngày sẵn hàng": _text(lot.get("ready_date")) or "UNKNOWN",
            "Pickup": _text(lot.get("pickup_address")) or "UNKNOWN",
            "Kiện/CBM/KG": f"{lot.get('packages')} / {lot.get('cbm')} / {lot.get('gross_weight_kg')}",
        }
        for index, lot in enumerate(lots)
    ]

    required_docs = [
        {
            "Chứng từ": _text(document.get("name")),
            "Bằng chứng": _valid_evidence_state(document.get("evidence_state")),
            "Ghi chú": _text(document.get("note")),
        }
        for document in (agreement.get("required_documents") or [])
    ]

    service_names = ", ".join(_text(line.get("service_name")) for line in services if _text(line.get("service_name")))
    tt_actions = list(responsibilities.get("truong_thanh") or [])
    customer_provides = list(responsibilities.get("customer_provides") or [])
    if entrusted.get("active"):
        tt_actions.append(f"Thực hiện ủy thác nhập khẩu theo điều khoản: tỷ lệ {_text(entrusted.get('rate_pct'))}%, phạm vi {_text(entrusted.get('importer_of_record_scope'))}")
        customer_provides.append(entrusted.get("customer_responsibility", ""))

    answer = lambda label, value: {"label": label, "value": value if _text(value) else "UNKNOWN", "source": "agreement snapshot / shipment / quote"}

    rows: list[dict[str, str]] = [
        answer("1. Khách hàng nào?", f"{_text(agreement.get('customer_name'))} ({customer_id})"),
        answer("2. Quote/agreement nào?", f"{agreement.get('agreement_no', 'UNKNOWN')} · báo giá {agreement.get('quote_reference', 'UNKNOWN')} v{agreement.get('quote_version', '?')}"),
        answer("3. Hàng gì?", snapshot.get("goods_description")),
        answer("4. Có bao nhiêu factory/lots?", f"{len(lots)} nhà máy/lô" if lots else "UNKNOWN — chưa có nhà máy/lô material"),
        answer("5. Incoterm nào?", snapshot.get("incoterm")),
        answer("6. Pickup ở đâu?", _text(first_lot.get("pickup_address")) or "UNKNOWN — xác nhận theo từng lô bên dưới"),
        answer("7. Factory contact là ai?", (_text(first_lot.get("factory_contact")) + (" · " + _text(first_lot.get("factory_phone"))) if _text(first_lot.get("factory_contact")) else "UNKNOWN — xác nhận theo từng lô bên dưới")),
        answer("8. Factory ready date?", _text(first_lot.get("ready_date")) or "UNKNOWN — xác nhận theo từng lô bên dưới"),
        answer("9. Customer required delivery date?", snapshot.get("expected_delivery_date")),
        answer("10. Dịch vụ nào đã bán?", service_names),
        answer("11. Trường Thành chịu trách nhiệm gì?", "; ".join(tt_actions) if tt_actions else "UNKNOWN — theo phạm vi dịch vụ đã bán"),
        answer("12. Khách cần cung cấp gì?", "; ".join(item for item in customer_provides if _text(item)) if customer_provides else "UNKNOWN"),
        answer("13. Chứng từ cần gì?", service_names),
        answer("14. Partner/agent nào liên quan?", (shipment.get("data", {}).get("3.4", {}) or {}).get("agency", {}).get("name") if isinstance(shipment, Mapping) and isinstance(shipment.get("data"), Mapping) else "UNKNOWN — cập nhật khi có partner record"),
        answer("15. Commercial assumption cần theo dõi?", "; ".join(assumptions) if assumptions else "Chưa có assumption"),
        answer("16. Còn unresolved issue nào trước operations?", "; ".join(unresolved) if unresolved else "Không còn unresolved issue"),
    ]

    return {
        "agreement_id": agreement.get("agreement_id"),
        "agreement_no": agreement.get("agreement_no"),
        "customer_id": customer_id,
        "customer_name": _customer_name(customer_id, customers),
        "shipment_ids": [str(item) for item in (agreement.get("shipment_ids") or [])],
        "questions": rows,
        "factory_lots": factory_lots_summary,
        "services_sold": [{"name": _text(line.get("service_name")), "qty": line.get("qty"), "currency": _text(line.get("currency"))} for line in services],
        "payment_terms": {
            "selected": list(payment.get("selected") or []),
            "credit_term_days": payment.get("credit_term_days"),
            "due_date_trigger": _text(payment.get("due_date_trigger")),
            "notes": _text(payment.get("notes")),
        },
        "required_documents": required_docs,
        "evidence": {
            "accepted_quotation": bool(agreement.get("evidence", {}).get("accepted_quotation")),
            "signed_contract": bool(agreement.get("evidence", {}).get("signed_contract")),
            "customer_confirmation": bool(agreement.get("evidence", {}).get("customer_confirmation")),
            "entrusted_documentation": bool(agreement.get("evidence", {}).get("entrusted_documentation")),
            "notes": _text(agreement.get("evidence", {}).get("notes")),
        },
        "unresolved_issues": unresolved,
        "assumptions": assumptions,
        "readiness": readiness,
        "read_only": False,
    }


__all__ = [
    "AGREEMENT_STATUSES",
    "Allowed_TRANSITIONS",
    "DEFAULT_PAYMENT_TERM_CHOICES",
    "DEFAULT_REQUIRED_DOCUMENTS",
    "EVIDENCE_STATES",
    "HANDOFF_COMMERCIAL_REVIEW",
    "HANDOFF_MISSING_REQUIRED_DATA",
    "HANDOFF_READY",
    "HANDOFF_STATES",
    "agreements_for_quote",
    "agreements_for_shipment",
    "build_agreement_from_quote",
    "commercial_handoff_view",
    "handoff_readiness",
    "new_agreement_identity",
    "normalize_required_documents",
    "prepare_agreement_for_persistence",
    "transition_agreement",
    "validate_agreement",
]
