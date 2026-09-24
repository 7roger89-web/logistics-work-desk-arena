"""Phase C1 — the business-contracts vertical slice, in the frozen Logi-good shell.

KHÁCH HÀNG → BÁO GIÁ → THỎA THUẬN/BÀN GIAO → HỢP ĐỒNG → HÀNG HÓA HỢP ĐỒNG
→ HDNT/PL/HDMB → LINK SHIPMENT → DOWNLOAD/HISTORY.

This module is a presentation adapter + the ONE bounded dispatcher for the C1
destinations.  It adds NO second source of truth:

* every value is projected from the CURRENT Logistics readers
  (``core.database``, ``core.quotations``, ``core.commercial_agreements``,
  ``core.docgen``);
* every write goes: typed event → RBAC (``core.auth``) → existing writer/service
  → audit → fresh backend read → refreshed view-model.

UNKNOWN != ZERO throughout: a blank quantity/unit-price stays ``None`` and is
rendered "—"; it is never silently coerced to 0.
"""

from __future__ import annotations

import base64
from typing import Any, Mapping

from views import logi_real_data as rd
from views import logi_sandbox

# ---------------------------------------------------------------------------
# Event set (typed trigger values surfaced by the ONE component root)
# ---------------------------------------------------------------------------

C1_EVENTS = {
    "customer_create",
    "customer_edit",
    "customer_archive",
    "customer_import",
    # LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — paste a GetFly DSDH block and
    # take ONLY the customer identity it really carries, through the existing
    # customer_import writer above. No Excel upload, no second importer, no
    # invented contract field.
    "customer_getfly_import",
    "quote_create",
    "quote_edit",
    "quote_transition",
    "agreement_create",
    "agreement_edit",
    "agreement_transition",
    "contract_create",
    "contract_save",
    "contract_goods_save",
    "contract_docgen_generate",
    "contract_docgen_issue",
    "contract_shipment_link",
    # LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — ONE bounded write event
    # for the /ngu-canh-doi-tac agent master. authority_agents is already part
    # of the C1 authority payload, so the C1 dispatcher is its natural surface:
    # RBAC → existing core.database.save_authority_agent → audit → fresh read.
    # No agents_v2 collection, no partner table, no new writer.
    "authority_agent_save",
    # LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — bounded immutable snapshot for
    # the international payment comparator (Hợp đồng → Thanh toán quốc tế).
    # One typed event carries the full calculator inputs + FX provenance + fee
    # rules; the server re-derives the arithmetic with Decimal, persists the
    # snapshot via the canonical writer, and returns the fresh readback. A
    # later live-rate refresh creates a NEW snapshot; it never overwrites existing
    # ones. Also exposed as the shorter alias `contract_payment_snapshot_save`
    # for older clients.
    "contract_intl_snapshot_save",
    "contract_payment_snapshot_save",
    # LOGI_QUOTE_COST_WORKFLOW_UX_01 — ONE bounded, READ-ONLY quote export.
    # It mutates nothing: it re-reads the canonical quote, renders the customer
    # quotation through the EXISTING core.excel_utils.generate_quote_excel and
    # returns bounded base64 bytes on the same lastWrites channel every other
    # download already uses. No second exporter, no API server, no Office
    # automation, no Owner-local PC.
    "quote_export_xlsx",
    # LOGI_COST_INTELLIGENCE_01 — parse is read-only; the other two are bounded writes.
    "cost_rate_parse",
    "cost_rate_save",
    "cost_rate_status_set",
    "cost_catalog_save",
}

_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_UNKNOWN = rd.UNKNOWN
_LABEL = rd.UNKNOWN_LABEL


def _text(value: Any) -> str:
    return rd.text(value)


def _num(value: Any) -> float | None:
    return rd.num(value)


def _money_label(value: Any) -> str:
    return rd._money_label(value)


# ---------------------------------------------------------------------------
# Fresh reads (straight from the database, never the render cache)
# ---------------------------------------------------------------------------

def read_customer(cid: str) -> dict[str, Any] | None:
    from core.database import get_db

    db = get_db()
    if db is None:
        return None
    return db.customers.find_one({"id": cid, "is_deleted": {"$ne": True}}, {"_id": 0})


def read_quote(qid: str) -> dict[str, Any] | None:
    from core.database import get_db

    db = get_db()
    if db is None:
        return None
    return db.quotes.find_one({"id": qid, "is_deleted": {"$ne": True}}, {"_id": 0})


def read_agreement(aid: str) -> dict[str, Any] | None:
    from core.database import get_db

    db = get_db()
    if db is None:
        return None
    return db.agreements.find_one({"id": aid, "is_deleted": {"$ne": True}}, {"_id": 0})


def read_contract(cid: str) -> dict[str, Any] | None:
    from core.database import get_db

    db = get_db()
    if db is None:
        return None
    return db.contracts.find_one({"id": cid, "is_deleted": {"$ne": True}}, {"_id": 0})


# ---------------------------------------------------------------------------
# Session-scoped generated-file store (download availability, per persistence
# capability: metadata persists cross-session, bytes are session-only)
# ---------------------------------------------------------------------------

def _outputs_key(scope: str) -> str:
    return f"logi_c1_doc_outputs_{scope}"


def stored_outputs(scope: str) -> dict[str, dict[str, Any]]:
    import streamlit as st

    outputs = st.session_state.get(_outputs_key(scope))
    return dict(outputs) if isinstance(outputs, dict) else {}


def store_output(scope: str, record_id: str, payload: Mapping[str, Any]) -> None:
    import streamlit as st

    if not record_id:
        return
    outputs = stored_outputs(scope)
    if record_id in outputs:
        return  # existing (possibly ISSUED) revisions are never overwritten
    outputs[record_id] = dict(payload)
    st.session_state[_outputs_key(scope)] = outputs


# ---------------------------------------------------------------------------
# Projections
# ---------------------------------------------------------------------------

def customer_projection(c: Mapping[str, Any]) -> dict[str, Any]:
    name = _text(c.get("name"))
    tax_code = _text(c.get("tax_code"))
    return {
        "id": _text(c.get("id")),
        "name": name,
        # Compatibility aliases for the donor shell search (name / MST).
        "short": name,
        "mst": tax_code,
        "phone": _text(c.get("phone")),
        "email": _text(c.get("email")),
        "contactPerson": _text(c.get("contact_person")),
        "taxCode": tax_code,
        "address": _text(c.get("address")),
        "note": _text(c.get("note")),
    }


_QUOTE_STATUS_LABEL = {
    "DRAFT": "Nháp",
    "READY_FOR_REVIEW": "Chờ review",
    "SENT": "Đã gửi khách",
    "ACCEPTED": "Khách chốt",
    "REJECTED": "Từ chối",
    "EXPIRED": "Hết hạn",
    "READY_TO_CREATE_SHIPMENT": "Sẵn sàng tạo lô",
}


def quote_projection(q: Mapping[str, Any]) -> dict[str, Any]:
    from core.quotations import allowed_transitions

    calc = q.get("calculation") if isinstance(q.get("calculation"), Mapping) else {}
    status = _text(q.get("status")) or "DRAFT"
    service_lines = q.get("service_lines") if isinstance(q.get("service_lines"), list) else []
    # Legacy staging quote shape (estimate summary) falls back to `total`/`lines`.
    total = _num(calc.get("selling_price_total_vnd"))
    if total is None:
        total = _num(q.get("total"))
    lines_out: list[dict[str, Any]] = []
    for line in service_lines:
        if not isinstance(line, Mapping):
            continue
        lines_out.append({
            "code": _text(line.get("code")),
            "serviceName": _text(line.get("service_name")),
            "unit": _text(line.get("unit")) or "Lần",
            "qty": _num(line.get("qty")),
            "currency": _text(line.get("currency")) or "VND",
            "costUnit": _num(line.get("cost_unit")),
            "sellUnit": _num(line.get("sell_unit")),
            "taxPct": _num(line.get("tax_pct")),
            "costTotal": _num(line.get("cost_total")),
            "sellTotal": _num(line.get("sell_total")),
            "costVnd": _num(line.get("cost_vnd")),
            "sellVnd": _num(line.get("sell_vnd")),
            # LOGI_INTERNAL_UX_SIMPLIFY_01 — optional operator note round trip.
            "note": _text(line.get("note")),
        })
    fx = q.get("fx_snapshot") if isinstance(q.get("fx_snapshot"), Mapping) else {}
    fx_rates = {str(code).upper(): _num(rate)
                for code, rate in dict(fx.get("rates_to_vnd") or {}).items()}
    # Only the currencies actually used by the quote's lines are disclosed, so
    # the VND total is never shown without the rate it was derived from.
    line_currencies = sorted({str(line.get("currency") or "VND").upper() for line in lines_out})
    return {
        "id": _text(q.get("id")),
        "quoteNo": _text(q.get("quote_no")) or _text(q.get("id")),
        "customerId": _text(q.get("customer_id")),
        "customer": _text(q.get("customer_name")) or _text(q.get("customer")),
        "salesOwner": _text(q.get("sales_owner")),
        "status": status,
        "statusLabel": _QUOTE_STATUS_LABEL.get(status, status),
        "origin": _text(q.get("origin")),
        "destination": _text(q.get("destination")),
        "route": _text(q.get("route")),
        "incoterm": _text(q.get("incoterm")),
        "transportMode": _text(q.get("transport_mode")),
        "goodsDescription": _text(q.get("goods_description")),
        "expectedDeliveryDate": _text(q.get("expected_delivery_date")),
        "currency": "VND",
        "total": total,
        "sellingPriceTotalVnd": _num(calc.get("selling_price_total_vnd")),
        "estimatedCostVnd": _num(calc.get("estimated_cost_vnd")),
        "estimatedMarginVnd": _num(calc.get("estimated_margin_vnd")),
        "isEstimate": True,
        "ledgerPosted": bool(q.get("ledger_posted")),
        "fxRatesToVnd": fx_rates,
        "fxSource": _text(fx.get("source")),
        "fxNeededFor": [code for code in line_currencies if code != "VND"],
        "serviceLines": lines_out,
        "assumptions": list(q.get("assumptions") or []),
        # Customer-facing notes round trip so reopening a quote restores exactly
        # what the customer was (or will be) shown.
        "customerNotes": [_text(n) for n in (q.get("customer_notes") or []) if _text(n)],
        "statusHistory": list(q.get("status_history") or []),
        "version": int(q.get("version") or 0),
        "shipmentId": _text(q.get("shipment_id")),
        "allowedTransitions": list(allowed_transitions(status)),
        "source": "core.database.load_quotes",
    }


_AGREEMENT_STATUS_LABEL = {
    "DRAFT": "Nháp",
    "REVIEWING": "Đang review",
    "AGREED": "Đã đồng ý",
    "REVISED": "Đã sửa đổi",
    "VOID": "Vô hiệu",
}


def agreement_projection(a: Mapping[str, Any]) -> dict[str, Any]:
    from core.commercial_agreements import allowed_transitions, handoff_readiness

    status = _text(a.get("status")) or "DRAFT"
    snapshot = a.get("commercial_snapshot") if isinstance(a.get("commercial_snapshot"), Mapping) else {}
    return {
        "id": _text(a.get("agreement_id")) or _text(a.get("id")),
        "agreementNo": _text(a.get("agreement_no")),
        "customerId": _text(a.get("customer_id")),
        "customer": _text(a.get("customer_name")),
        "quoteId": _text(a.get("quote_id")),
        "quoteReference": _text(a.get("quote_reference")),
        "status": status,
        "statusLabel": _AGREEMENT_STATUS_LABEL.get(status, status),
        "version": int(a.get("version") or 0),
        "effectiveDate": _text(a.get("effective_date")),
        "commercialSnapshot": {
            "origin": _text(snapshot.get("origin")),
            "destination": _text(snapshot.get("destination")),
            "route": _text(snapshot.get("route")),
            "incoterm": _text(snapshot.get("incoterm")),
            "transportMode": _text(snapshot.get("transport_mode")),
            "goodsDescription": _text(snapshot.get("goods_description")),
            "expectedDeliveryDate": _text(snapshot.get("expected_delivery_date")),
            "serviceLines": list(snapshot.get("service_lines") or []),
            "calculationSummary": snapshot.get("calculation_summary") or {},
        },
        "paymentTerms": a.get("payment_terms") if isinstance(a.get("payment_terms"), Mapping) else {},
        "responsibilities": a.get("responsibilities") if isinstance(a.get("responsibilities"), Mapping) else {},
        "requiredDocuments": list(a.get("required_documents") or []),
        "factoryLots": list(a.get("factory_lots") or []),
        "assumptions": list(a.get("assumptions") or []),
        "unresolvedIssues": list(a.get("unresolved_issues") or []),
        "evidence": a.get("evidence") if isinstance(a.get("evidence"), Mapping) else {},
        "shipmentIds": list(a.get("shipment_ids") or []),
        "statusHistory": list(a.get("status_history") or []),
        "handoff": handoff_readiness(a),
        "allowedTransitions": list(allowed_transitions(status)),
        "source": "core.database.load_agreements",
    }


_DOC_LABEL = {"HDNT": "Hợp đồng nguyên tắc", "PL": "Phụ lục Hợp đồng", "HDMB": "Hợp đồng mua bán", "PXK": "Phiếu xuất kho"}


def document_projection(d: Mapping[str, Any], stored: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    record_id = _text(d.get("id"))
    doc_type = _text(d.get("document_type")).upper()
    entry = stored.get(record_id)
    download = None
    if entry and entry.get("bytes"):
        try:
            download = base64.b64encode(entry["bytes"]).decode("ascii")
        except Exception:  # noqa: BLE001
            download = None
    return {
        "id": record_id,
        "documentId": _text(d.get("document_id")),
        "documentType": doc_type,
        "documentTypeLabel": _DOC_LABEL.get(doc_type, doc_type),
        "revision": d.get("generation_revision") or d.get("revision") or 1,
        "status": _text(d.get("status")),
        "fileName": _text(d.get("output_file_name")),
        "mime": _MIME_DOCX if doc_type == "HDNT" else _MIME_XLSX,
        "generatedAt": _text(d.get("generated_at")),
        "generatedBy": _text(d.get("generated_by")),
        "issuedAt": _text(d.get("issued_at")),
        "issuedBy": _text(d.get("issued_by")),
        "templateHash": _text(d.get("template_hash"))[:16],
        "outputHash": _text(d.get("output_hash"))[:16],
        "supersedes": _text(d.get("supersedes_document_id")),
        "supersededBy": _text(d.get("superseded_by_document_id")),
        "downloadAvailable": bool(entry and entry.get("bytes")),
        "downloadBase64": download,
    }


def _goods_display(line: Mapping[str, Any], index: int) -> dict[str, Any]:
    qty = rd.num(line.get("quantity"))
    price = rd.num(line.get("unit_price_vnd_excl_vat"))
    amount = None
    if qty is not None and price is not None:
        amount = round(qty * price)
    return {
        "stt": index,
        "description": _text(line.get("description")),
        "unit": _text(line.get("unit")),
        "quantity": qty,
        "unitPrice": price,
        "vatRate": _text(line.get("vat_rate")) or "0.08",
        "amount": amount,
    }


def _party_view(record: Mapping[str, Any] | None, kind: str) -> dict[str, Any] | None:
    if not record:
        return None
    code_field = "legal_code" if kind == "agent" else "tax_or_legal_code"
    return {
        "id": _text(record.get(f"{kind}_id") or record.get("id")),
        "legalName": _text(record.get("legal_name")),
        "legalCode": _text(record.get(code_field)),
        "legalAddress": _text(record.get("legal_address")),
        "representative": _text(record.get("legal_representative")),
        "representativeTitle": _text(record.get("representative_title")),
        "phone": _text(record.get("phone")),
        "email": _text(record.get("email")),
        "bankAccountHolder": _text(record.get("bank_account_holder")),
        "bankAccountNumber": _text(record.get("bank_account_number")),
        "bankName": _text(record.get("bank_name")),
        "bankBranch": _text(record.get("bank_branch")),
    }


def _contract_identity(contract: Mapping[str, Any]) -> dict[str, Any]:
    stored = contract.get("doc_identity") if isinstance(contract.get("doc_identity"), Mapping) else {}
    return {
        "hdntNo": _text(contract.get("hdnt_no") or stored.get("hdnt_no")),
        "hdntDate": _text(contract.get("hdnt_date") or stored.get("hdnt_date")),
        "validFrom": _text(contract.get("valid_from") or stored.get("valid_from")),
        "validTo": _text(contract.get("valid_to") or stored.get("valid_to")),
        "plNo": _text(contract.get("pl_no") or stored.get("pl_no")),
        "plDate": _text(contract.get("pl_date") or stored.get("pl_date")),
        "hdmbNo": _text(contract.get("hdmb_no") or stored.get("hdmb_no")),
        "hdmbDate": _text(contract.get("hdmb_date") or stored.get("hdmb_date")),
    }


def _goods_totals_view(goods_raw: Any, pack: Mapping[str, Any]) -> dict[str, Any] | None:
    """Goods totals exactly as the authoritative rule states them.

    ``core.docgen.rules.total_after_vat`` is the single source of the
    UNKNOWN != ZERO decision: it returns ``None`` when the goods set cannot
    produce a reliable total (no line at all, or a line with an UNKNOWN
    quantity/price).  ``compute_goods_totals`` — which ``build_document_pack``
    reports — returns dataclass zeros in exactly those cases, so forwarding it
    verbatim made the desk render a hard "0 ₫" and derive the HDNT/PL vs HDMB
    threshold decision from a fabricated zero while the readiness cards on the
    same screen said "Tổng đang UNKNOWN, không thể thay bằng 0".

    A genuine zero (real lines that sum to 0) is still returned as 0.
    """
    from core.docgen import rules as docgen_rules

    try:
        authoritative = docgen_rules.total_after_vat(
            [line for line in (goods_raw or []) if isinstance(line, Mapping)])
    except Exception:  # noqa: BLE001 - never blank the desk on a rule error
        return None
    if authoritative is None:
        return None
    totals = pack.get("totals")
    return dict(totals) if isinstance(totals, Mapping) else None


def _doc_card_view(card: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize ONE readiness card to the declared payload contract.

    ``core.docgen.generator.build_document_pack`` emits the deferred DEBIT_USD
    card without a ``missing`` list (nothing is missing — it is not
    implemented).  The payload contract (``DocCard.missing: string[]``) and the
    page that renders it require the key, so an absent list used to take the
    whole shell down with "Cannot read properties of undefined".  Normalizing
    here keeps the authoritative card content untouched and the ONE payload
    self-consistent.
    """
    return {
        "document_type": _text(card.get("document_type")),
        "state": _text(card.get("state")),
        "reason": _text(card.get("reason")),
        "missing": [_text(m) for m in (card.get("missing") or []) if _text(m)],
        "source_ref": _text(card.get("source_ref")),
        "goods_count": card.get("goods_count"),
        "applicable": bool(card.get("applicable")),
    }


def contract_projection(
    c: Mapping[str, Any],
    *,
    shipments: Mapping[str, Any],
    docs_by_scope: Mapping[str, dict[str, Any]],
    companies: Mapping[str, Any],
    agents: Mapping[str, Any],
    all_contracts: Mapping[str, Any],
    contract_index: Mapping[str, Any] | None = None,
    intl_snapshots_by_contract: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    from core.docgen import generator as gen

    cid = _text(c.get("id")) or _text(c.get("contract_no"))
    company_id = _text(c.get("company_id"))
    agent_id = _text(c.get("agent_id"))
    # Same resolution as the generate path (incl. single-record fallback) so the
    # list/detail readback and the docgen preflight always agree on parties.
    company, agent = _resolve_authority(c, companies, agents)

    goods_raw = c.get("goods_lines") if isinstance(c.get("goods_lines"), list) else []
    goods = [_goods_display(line, idx) for idx, line in enumerate(goods_raw, start=1) if isinstance(line, Mapping)]

    identity = _contract_identity(c)
    contract_view = {
        "id": cid,
        "contract_no": _text(c.get("contract_no")) or cid,
        "currency": "VND",
        "hdnt_no": identity["hdntNo"],
        "hdnt_date": identity["hdntDate"],
        "valid_from": identity["validFrom"],
        "valid_to": identity["validTo"],
        "pl_no": identity["plNo"],
        "pl_date": identity["plDate"],
        "hdmb_no": identity["hdmbNo"],
        "hdmb_date": identity["hdmbDate"],
    }

    # HDNT reuse / parent (authoritative, from core.docgen rules).
    parent_contract = None
    hdnt_reuse: dict[str, Any] = {}
    if agent and company:
        hdnt_reuse = gen.reuse_decision_for_agent(all_contracts, agent=agent, company=company)
        if hdnt_reuse.get("valid_count") == 1:
            parent_contract = hdnt_reuse.get("reuse_target")

    delivery = {"delivery_completed": False, "delivery_date": "", "delivery_location": "",
                "receiver_name": "", "receiver_title": ""}
    try:
        pack = gen.build_document_pack(
            shipment_id=cid,
            goods_lines=goods_raw,
            delivery_completed=False,
            agent=agent,
            company=company,
            parent_contract=parent_contract,
            contract=contract_view,
            pxk_source=None,
            delivery=delivery,
            contracts=all_contracts,
        )
    except Exception:  # noqa: BLE001 - one bad contract must not blank the desk
        # Totals stay UNKNOWN (None) on the error path too — an unreadable
        # contract must never be presented as a 0 ₫ total.
        pack = {"totals": None, "threshold_vnd": 50_000_000,
                "applicable_documents": [], "cards": [], "hdnt_reuse": {}}

    linked_ids = [str(x).upper() for x in _linked_shipment_ids(cid, contract_index)]
    legacy = _text(c.get("shipment_id"))
    if legacy and legacy.upper() not in linked_ids:
        linked_ids.append(legacy.upper())
    linked_shipments = []
    for sid in linked_ids:
        ship = shipments.get(sid)
        if not isinstance(ship, Mapping):
            continue
        linked_shipments.append({
            "id": _text(ship.get("id")),
            "customer": _text(ship.get("customer") or ship.get("client")),
            "status": _text(ship.get("status")),
            "to": f"/lo-hang/{_text(ship.get('id'))}",
        })

    stored = stored_outputs(cid)
    docs = docs_by_scope.get(cid, {})
    documents = [document_projection(d, stored) for d in docs.values() if isinstance(d, Mapping)]
    documents.sort(key=lambda d: (d["documentType"], d["revision"]))

    # LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — readback of immutable payment snapshots
    _intl_snaps = []
    if intl_snapshots_by_contract is not None:
        _intl_snaps = list(intl_snapshots_by_contract.get(cid.upper(), []) or [])
        _intl_snaps = _intl_snaps[:20]

    status = _text(c.get("status")) or "active"
    return {
        "id": cid,
        "contractNo": _text(c.get("contract_no")) or cid,
        "kind": _text(c.get("kind")) or _text(c.get("type")),
        "status": status,
        "statusTone": "green" if status == "active" else "gray",
        "client": _text(c.get("client")) or _text(c.get("customer")),
        "customerId": _text(c.get("customer_id")),
        "company": _text((company or {}).get("legal_name")),
        "companyLegal": _text((company or {}).get("legal_name")),
        "agent": _text((agent or {}).get("legal_name")),
        "companyId": company_id,
        "agentId": agent_id,
        "value": _num(c.get("value")),
        "currency": _text(c.get("currency")) or "VND",
        "note": _text(c.get("note")),
        "contractDate": _text(c.get("date") or c.get("contract_date")),
        # LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the operator's explicit PL
        # decision, read back VERBATIM from the stored contract: "YES", "NO" or
        # "" (= chưa chọn). An absent field on a legacy contract is "" — it is
        # never presented as "Không cần PL".
        "plRequired": _pl_required_decision(c.get("pl_required")) or "",
        "parties": {"company": _party_view(company, "company"), "agent": _party_view(agent, "agent")},
        "goodsLines": goods,
        "goodsTotals": _goods_totals_view(goods_raw, pack),
        "thresholdVnd": pack.get("threshold_vnd"),
        "applicableDocuments": pack.get("applicable_documents") or [],
        "docCards": [_doc_card_view(card) for card in (pack.get("cards") or [])
                     if isinstance(card, Mapping)],
        "hdntReuse": pack.get("hdnt_reuse") or {},
        "identity": identity,
        "linkedShipments": linked_shipments,
        "documents": documents,
        "intlSnapshots": _intl_snaps,
        "intlSnapshotCount": len(_intl_snaps),
        "source": "core.database.load_contracts + core.docgen.build_document_pack",
    }


# ---------------------------------------------------------------------------
# Assemble the C1 payload for the view-model `data` channel
# ---------------------------------------------------------------------------

def _linked_shipment_ids(cid: str, contract_index: Mapping[str, Any] | None) -> list[str]:
    """Shipment ids additively linked to contract ``cid``.

    PERFORMANCE REPAIR (LOGI_INTERACTION_LATENCY_FINALIZE_02): the C1 payload
    issued one ``contracts.find_one`` round-trip per projected contract (N+1)
    although ``assemble_c1_payload`` had just read the whole non-deleted
    contract set. When the caller hands over that render-local set
    (``contract_index``: canonical upper-case ``id`` → contract document) the
    same ``shipment_ids`` field is taken from it in memory — the same documents
    the per-contract read would have returned, because every write path that
    changes a contract (``save_contract_to_cloud``, ``link_contract_to_shipment``)
    invalidates the contracts reader before the next render. A standalone
    caller that passes no index keeps the original per-contract read.
    """
    if contract_index is None:
        from core.database import load_shipments_for_contract

        return load_shipments_for_contract(cid)
    contract = contract_index.get(str(cid or "").strip().upper())
    if not isinstance(contract, Mapping):
        return []
    return [str(x) for x in (contract.get("shipment_ids") or [])]


def _contract_index(contracts: Mapping[str, Any]) -> dict[str, Any]:
    """``load_contracts()`` result re-keyed by the stored ``id`` value, exactly.

    The per-contract read this replaces is an exact match on the stored ``id``
    (``find_one({"id": cid.upper()})``), so the key is the stored value as-is —
    not normalised — and the lookup side upper-cases, precisely as before.
    """
    index: dict[str, Any] = {}
    for contract in contracts.values():
        if not isinstance(contract, Mapping) or contract.get("id") is None:
            continue
        key = str(contract.get("id"))
        if key not in index:
            index[key] = contract
    return index


def assemble_c1_payload(
    *,
    shipments: Mapping[str, Any] | None = None,
    customers: Mapping[str, Any] | None = None,
    quotes: Mapping[str, Any] | None = None,
    contracts: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
    agreements: Mapping[str, Any] | None = None,
    companies: Mapping[str, Any] | None = None,
    docgen_documents: Mapping[str, Any] | None = None,
    intl_snapshots_by_contract: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Assemble the C1 reference payload.

    PERFORMANCE REPAIR: ``shipments`` lets the component build path hand over
    the canonical shipment map it ALREADY read for this render
    (``views.logi_view_model.load_shipments()``) instead of the render loading
    the same full collection a second time for contract links. The data is the
    identical reader result, so nothing about the projection changes; a
    standalone caller that passes nothing keeps the original read.

    LOGI_INTERACTION_LATENCY_FINALIZE_02 extends the same rule to the other
    sources the ONE ``build_view_model`` render has already read for this very
    request — ``customers``, ``quotes``, ``contracts``, ``agents``,
    ``agreements``, ``companies`` and the raw ``docgen_documents`` map — so
    the post-action render no longer pays a second round-trip per source (and
    one more per contract, see ``_linked_shipment_ids``). Each parameter is
    the identical reader result; nothing is cached across renders and a caller
    that passes nothing keeps every original read.
    """
    from core.database import (
        load_agreements,
        load_authority_agents,
        load_authority_companies,
        load_contracts,
        load_customers,
        load_docgen_documents,
        load_quotes,
    )

    customers = (load_customers() if customers is None else customers) or {}
    quotes = (load_quotes() if quotes is None else quotes) or {}
    agreements = (load_agreements() if agreements is None else agreements) or {}
    contracts = (load_contracts() if contracts is None else contracts) or {}
    companies = (load_authority_companies() if companies is None else companies) or {}
    agents = (load_authority_agents() if agents is None else agents) or {}
    if shipments is None:
        shipments = _load_shipments_for_links()
    if docgen_documents is None:
        docgen_documents = load_docgen_documents() or {}

    # LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — bulk load immutable snapshots once per render
    if intl_snapshots_by_contract is None:
        try:
            from core.database import load_contract_intl_snapshots
            _all_snaps = load_contract_intl_snapshots() or {}
            _grouped: dict[str, list[dict[str, Any]]] = {}
            for snap in _all_snaps.values():
                if not isinstance(snap, Mapping):
                    continue
                cid_key = str(snap.get("contract_id") or "").strip().upper()
                if not cid_key:
                    continue
                _grouped.setdefault(cid_key, []).append(dict(snap))
            for lst in _grouped.values():
                lst.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
            intl_snapshots_by_contract = _grouped
        except Exception:
            intl_snapshots_by_contract = {}

    docs_by_scope: dict[str, dict[str, Any]] = {}
    for doc in docgen_documents.values():
        if not isinstance(doc, Mapping):
            continue
        scope = _text(doc.get("shipment_id"))
        docs_by_scope.setdefault(scope, {})[_text(doc.get("id"))] = doc
    contract_index = _contract_index(contracts)

    return {
        "customers": [customer_projection(c) for c in customers.values() if isinstance(c, Mapping)],
        "quotes": [quote_projection(q) for q in quotes.values() if isinstance(q, Mapping)],
        "agreements": [agreement_projection(a) for a in agreements.values() if isinstance(a, Mapping)],
        "contracts": [
            contract_projection(
                c,
                shipments=shipments,
                docs_by_scope=docs_by_scope,
                companies=companies,
                agents=agents,
                all_contracts=contracts,
                contract_index=contract_index,
                intl_snapshots_by_contract=intl_snapshots_by_contract,
            )
            for c in contracts.values() if isinstance(c, Mapping)
        ],
        "authority": {
            "companies": [(_party_view(v, "company") or {}) for v in companies.values() if isinstance(v, Mapping)],
            "agents": [(_party_view(v, "agent") or {}) for v in agents.values() if isinstance(v, Mapping)],
        },
    }


def _load_shipments_for_links() -> dict[str, Any]:
    from views import logi_view_model as vm

    try:
        return vm.load_shipments()
    except Exception:  # noqa: BLE001
        return {}


# ---------------------------------------------------------------------------
# Template path resolution (production owner-gate; staging synth only)
# ---------------------------------------------------------------------------

def _resolve_template_paths() -> tuple[str | None, str | None]:
    from core.config import DOCGEN_TEMPLATE_DIR

    if DOCGEN_TEMPLATE_DIR is not None:
        return (
            str(DOCGEN_TEMPLATE_DIR / "truong-thanh-agent.xlsx"),
            str(DOCGEN_TEMPLATE_DIR / "HDNT-TT-agent.docx"),
        )
    if logi_sandbox.transport_name() == logi_sandbox.SANDBOX_TRANSPORT:
        from views import logi_docgen_templates

        return logi_docgen_templates.staging_template_paths()
    return None, None


# ---------------------------------------------------------------------------
# Write handlers
# ---------------------------------------------------------------------------

def _actor() -> str:
    from core.auth import current_user

    user = current_user() or {}
    return rd.text(user.get("username")) or "system"


def _result(event: str, entity_id: str, ok: bool, error: str = "", readback: dict[str, Any] | None = None,
            **extra: Any) -> dict[str, Any]:
    return {"event": event, "id": entity_id, "ok": ok, "error": error, "readback": readback, **extra}


def _audit(entity_type: str, entity_id: str, limit: int = 6) -> list[dict[str, Any]]:
    from core.database import load_audit_logs

    return [
        {"action": rd.text(row.get("action")), "actor": rd.text(row.get("actor")),
         "createdAt": str(row.get("created_at"))}
        for row in (load_audit_logs(entity_type, entity_id, limit=limit) or [])
        if isinstance(row, Mapping)
    ]


def _handle_customer_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    """CREATE one customer through the EXISTING canonical writer.

    LOGI_UAT_REAL_USE_REPAIR_02: the outcome now echoes the ``requestId`` the
    component sent, exactly like ``shipment_create`` / ``authority_agent_save``
    already do. No new framework: this reuses the SAME lastWrites correlation
    mechanism, so the form can tell "the event was transported" apart from
    "the canonical writer accepted it", and a refusal can never be rendered as
    success. ``persisted`` carries the fresh readback identity so the UI can
    require the customer to genuinely exist before it claims anything.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, save_customer_to_cloud

    cid = _text(payload.get("id")).strip().upper()
    name = _text(payload.get("name"))
    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("customer_create", cid, ok, error, requestId=request_id, **extra)

    if not cid or not name:
        return _res(False, "Mã và tên khách hàng là bắt buộc.")
    if not can_operate_business("customers"):
        return _res(False, "RBAC: không có quyền customers.")
    if cid in (load_customers() or {}):
        return _res(False, f"Mã khách hàng {cid} đã tồn tại.")
    doc = {
        "id": cid, "name": name,
        "phone": _text(payload.get("phone")), "email": _text(payload.get("email")),
        "contact_person": _text(payload.get("contactPerson")),
        "tax_code": _text(payload.get("taxCode")), "address": _text(payload.get("address")),
        "note": _text(payload.get("note")),
    }
    if not save_customer_to_cloud(doc):
        return _res(False, get_last_db_error() or "Không lưu được khách hàng.")
    fresh = read_customer(cid)
    if fresh is None:
        # Writer reported success but the canonical readback does not carry the
        # customer: TRANSPORT/WRITE_RETURN != PERSISTENCE. Report the truth.
        return _res(False,
                    f"Writer báo thành công nhưng đọc lại không thấy khách hàng {cid}.")
    return _res(True, readback=customer_projection(fresh),
                persisted={"id": _text(fresh.get("id")).upper() or cid,
                           "name": _text(fresh.get("name"))},
                audit=_audit("customer", cid))


def _handle_customer_edit(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_customer_to_cloud

    cid = _text(payload.get("id")).strip().upper()
    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("customer_edit", cid, ok, error, requestId=request_id, **extra)

    if not cid:
        return _res(False, "Thiếu mã khách hàng.")
    if not can_operate_business("customers"):
        return _res(False, "RBAC: không có quyền customers.")
    existing = read_customer(cid)
    if existing is None:
        return _res(False, f"Không tìm thấy khách hàng {cid}.")
    for key in ("name", "phone", "email", "contact_person", "tax_code", "address", "note"):
        if key in payload:
            existing[key] = _text(payload.get(key))
    if not _text(existing.get("name")):
        return _res(False, "Tên khách hàng không được để trống.")
    if not save_customer_to_cloud(existing):
        return _res(False, get_last_db_error() or "Không lưu được khách hàng.")
    fresh = read_customer(cid)
    if fresh is None:
        return _res(False,
                    f"Writer báo thành công nhưng đọc lại không thấy khách hàng {cid}.")
    return _res(True, readback=customer_projection(fresh),
                persisted={"id": _text(fresh.get("id")).upper() or cid,
                           "name": _text(fresh.get("name"))},
                audit=_audit("customer", cid))


def _handle_customer_archive(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import has_permission
    from core.database import delete_customer

    cid = _text(payload.get("id")).strip().upper()
    if not cid:
        return _result("customer_archive", cid, False, "Thiếu mã khách hàng.")
    if not has_permission("customer_delete"):
        return _result("customer_archive", cid, False, "RBAC: chỉ Admin có quyền lưu trữ khách hàng.")
    reason = _text(payload.get("reason"))
    if not reason:
        return _result("customer_archive", cid, False, "Cần lý do lưu trữ.")
    if not delete_customer(cid, reason=reason):
        return _result("customer_archive", cid, False, "Không thể lưu trữ khách hàng.")
    return _result("customer_archive", cid, True, audit=_audit("customer", cid))


def _handle_customer_import(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, save_customer_to_cloud

    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    if not rows:
        return _result("customer_import", "", False, "Không có dòng dữ liệu để import.")
    if not can_operate_business("customers"):
        return _result("customer_import", "", False, "RBAC: không có quyền customers.")
    existing = load_customers() or {}
    created, skipped, errors = 0, 0, []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        cid = _text(row.get("id")).strip().upper()
        name = _text(row.get("name"))
        if not cid or not name:
            continue
        if cid in existing:
            skipped += 1
            continue
        doc = {
            "id": cid, "name": name,
            "phone": _text(row.get("phone")), "email": _text(row.get("email")),
            "contact_person": _text(row.get("contactPerson") or row.get("contact_person")),
            "tax_code": _text(row.get("taxCode") or row.get("tax_code")),
            "address": _text(row.get("address")), "note": _text(row.get("note")),
        }
        if save_customer_to_cloud(doc):
            existing[cid] = doc
            created += 1
        else:
            errors.append(cid)
    return _result("customer_import", "", not bool(errors),
                   f"Đã thêm {created} khách hàng, bỏ qua {skipped} đã tồn tại, lỗi {len(errors)}.",
                   created=created, skipped=skipped, failed=list(errors))


def _handle_customer_getfly_import(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Import the CUSTOMER identity a pasted GetFly DSDH table really carries.

    GetFly's order sheet carries ``Tên KH`` / ``Mã KH`` (plus order id/date and
    service lines) and nothing about a contract number, a buyer-company legal
    record or an MST. So this is the whole importable surface, and it is handed
    to the EXISTING ``customer_import`` handler — the same canonical
    ``save_customer_to_cloud`` writer, the same duplicate rule, the same RBAC —
    instead of a second importer. Column keywords come from
    ``core.getfly_reader`` so the Excel path and this text path can never map
    ``Tên KH`` differently.

    A file upload is not available on this bridge (the component transport only
    carries typed JSON events), which is why the entry point is paste, exactly
    like the existing customer import sheet on /khach-hang.
    """
    from core.auth import can_operate_business
    from core.getfly_reader import customer_rows_from_text
    from core.database import load_customers

    text_value = _text(payload.get("text"))
    # Echoed so the component matches THIS outcome to the exact paste it sent —
    # the same contract shipment_create uses; "event transported" is never a
    # success claim.
    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("customer_getfly_import", "", ok, error,
                       requestId=request_id, **extra)

    if not can_operate_business("customers"):
        return _res(False, "RBAC: không có quyền customers.")
    extracted = customer_rows_from_text(text_value)
    rows = list(extracted.get("rows") or [])
    if not rows:
        return _res(False,
                    extracted.get("reason") or "Không đọc được khách hàng nào từ dữ liệu dán.",
                    orders=list(extracted.get("orders") or []),
                    skippedMissing=list(extracted.get("skipped") or []))
    outcome = _handle_customer_import({"rows": rows})
    fresh = load_customers() or {}
    imported = [
        {"id": _text(row.get("id")).upper(), "name": _text(row.get("name"))}
        for row in rows
        if isinstance(fresh.get(_text(row.get("id")).upper()), Mapping)
    ]
    return _res(bool(outcome.get("ok")),
                _text(outcome.get("error")),
                customers=imported,
                requested=len(rows),
                orders=list(extracted.get("orders") or []),
                skippedMissing=list(extracted.get("skipped") or []))


#: Currencies the quote form can price a service line in besides VND.
_FX_QUOTE_CURRENCIES = ("USD", "CNY")


def _quote_fx_snapshot(payload: Mapping[str, Any], service_lines: list[dict[str, Any]],
                       base: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the canonical ``fx_snapshot`` from rates the operator entered.

    NO FAKE FX: the quotation model requires a quote-time rate for every
    non-VND line (``core.quotations.convert_to_vnd`` raises without one) and
    labels it as a quoting rate, not a transaction rate. This handler used to
    bake ``USD 25500 / CNY 3500`` into every quote, so the VND totals shown on
    the desk (and carried into agreements/lots) were derived from a constant
    nobody entered. Rates now come from the payload; a foreign-currency line
    without an operator rate is refused in Vietnamese instead of converted.

    ``base`` keeps the rates already stored on the quote when an edit only
    changes one of them (the edit form pre-fills from the same snapshot).
    """
    from core.quotations import normalize_fx_snapshot

    previous = dict((base or {}).get("rates_to_vnd") or {}) if isinstance(base, Mapping) else {}
    supplied = payload.get("fx") if isinstance(payload.get("fx"), Mapping) else {}
    rates: dict[str, Any] = {"VND": 1}
    for code in _FX_QUOTE_CURRENCIES:
        rate = _num(supplied.get(code))
        if rate is None:
            rate = _num(previous.get(code))
        if rate is not None and rate > 0:
            rates[code] = rate
    # REPAIR_02: a missing rate is UNKNOWN, not an error. NO FAKE FX still holds
    # — nothing is converted without an operator-entered rate — but the quote is
    # perfectly truthful in its own currency, so the Sale can save the DRAFT and
    # add the rate later. calculate_quote leaves the VND figures UNKNOWN and
    # says why, instead of refusing the save or inventing a rate.
    return normalize_fx_snapshot({
        "rates_to_vnd": rates,
        "source": "Tỷ giá SALE nhập khi báo giá; không phải tỷ giá giao dịch thực tế.",
    })


# ---------------------------------------------------------------------------
# LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_01 — UNKNOWN != ZERO on the quote line.
#
# The previous shape was `_num(x) if _num(x) is not None else 0`. That turned a
# field the operator never filled into a CANONICAL ZERO: the desk said "chưa
# biết" and the database said "0đ / 0% VAT". A quote built from a pasted
# customer message states a selling price and nothing else, so this silently
# manufactured a 100% margin and a 0% VAT commitment.
#
# The quotation engine (core.quotations.calculate_quote) is Decimal-typed and
# treats every line number as present, so preserving UNKNOWN through it would
# be a broad rewrite of the pricing authority, its projection and the contract
# handoff. The bounded, truthful alternative is to FAIL CLOSED at Save: a line
# whose Giá vốn or VAT was never stated is refused by name, and the operator
# supplies the real value. An explicit 0 typed by the operator is still valid —
# what is rejected is the ABSENCE of an answer, not the answer zero.
# ---------------------------------------------------------------------------

def _optional_line_number(line: Mapping[str, Any], key: str, index: int, label: str):
    """Read an OPTIONAL numeric line field: blank stays UNKNOWN (``None``).

    LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_02 — internal cost price and VAT are
    frequently unknown while a quotation is being written from a customer
    conversation. Blocking the save (REPAIR_01) forced the Sale to invent them,
    which is the same lie as coercing them to 0. They now travel as ``None``,
    and core.quotations.calculate_quote keeps every figure derived from them
    UNKNOWN. A value that IS supplied is still validated as a real number.
    """
    raw = line.get(key)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    value = _num(raw)
    if value is None:
        raise ValueError(f"Dòng dịch vụ {index}: {label} không phải là số hợp lệ.")
    return value


def _required_line_number(line: Mapping[str, Any], key: str, index: int, label: str) -> float:
    """Read a REQUIRED numeric line field, refusing a blank instead of zeroing it."""
    raw = line.get(key)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ValueError(
            f"Dòng dịch vụ {index}: chưa điền {label}. "
            "Ô trống nghĩa là CHƯA BIẾT, không phải 0 — nhập số thật (có thể là 0 nếu đúng là 0)."
        )
    value = _num(raw)
    if value is None:
        raise ValueError(f"Dòng dịch vụ {index}: {label} không phải là số hợp lệ.")
    return value


def _customer_notes(payload: Mapping[str, Any]) -> list[str]:
    """Customer-facing general notes typed/pasted on the quote form.

    Deliberately SEPARATE from ``quote['assumptions']``: that list carries
    INTERNAL control statements (estimate disclaimer, agent price
    reconciliation, customs policy) which must never be printed onto a document
    the customer receives. This field is the only text the export prints.
    """
    raw = payload.get("customerNotes")
    if not isinstance(raw, list):
        return []
    notes: list[str] = []
    for item in raw:
        note = _text(item).strip()
        if note and note not in notes:
            notes.append(note)
    return notes


def _quote_payload(customer_doc: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.quotations import calculate_quote

    service_lines: list[dict[str, Any]] = []
    for line in (payload.get("serviceLines") if isinstance(payload.get("serviceLines"), list) else []):
        if not isinstance(line, Mapping):
            continue
        service_lines.append({
            "code": _text(line.get("code")),
            "service_name": _text(line.get("serviceName")) or _text(line.get("code")),
            "unit": _text(line.get("unit")) or "Lần",
            "qty": _num(line.get("qty")) if _num(line.get("qty")) is not None else 1,
            "currency": _text(line.get("currency")) or "VND",
            # Giá bán is the number quoted to the customer: required.
            # Giá vốn / Thuế are internal facts that may still be UNKNOWN.
            "cost_unit": _optional_line_number(line, "costUnit", len(service_lines) + 1, "Giá vốn (unit)"),
            "sell_unit": _required_line_number(line, "sellUnit", len(service_lines) + 1, "Giá bán (unit)"),
            "tax_pct": _optional_line_number(line, "taxPct", len(service_lines) + 1, "Thuế %"),
            "cost_source": _text(line.get("costSource")) or "Nhập bởi SALE/Support; cần đối chiếu agent nếu là phí Trung Quốc.",
            # LOGI_INTERNAL_UX_SIMPLIFY_01 — optional free-form operator note.
            # Carried verbatim on the canonical line; core.quotations never
            # reads it for arithmetic (deep-copied through untouched).
            "note": _text(line.get("note")),
        })
    if not service_lines:
        raise ValueError("Cần ít nhất một dòng dịch vụ báo giá.")
    quote = {
        "customer_id": _text(payload.get("customerId")),
        "customer_name": _text(customer_doc.get("name")),
        "sales_owner": _text(payload.get("salesOwner")),
        "origin": _text(payload.get("origin")),
        "destination": _text(payload.get("destination")),
        "route": _text(payload.get("route")),
        "incoterm": _text(payload.get("incoterm")) or "EXW",
        "transport_mode": _text(payload.get("transportMode")) or "Road",
        "goods_description": _text(payload.get("goodsDescription")),
        "expected_delivery_date": _text(payload.get("expectedDeliveryDate")),
        "factory_lots": payload.get("factoryLots") if isinstance(payload.get("factoryLots"), list) else [],
        "service_lines": service_lines,
        "fx_snapshot": _quote_fx_snapshot(payload, service_lines),
        "entrusted_import": {"active": False, "goods_value": 0, "goods_currency": "USD", "rate_pct": 0,
                             "review_requested": False, "review_reason": "",
                             "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"},
                             "source": "Chưa khai báo phí ủy thác."},
        "remittance_estimate": {"remitted_amount_usd": 0, "bank_fee_pct": 0, "swift_fee_usd": 0,
                                "receiving_bank_fee_usd": 0, "agent_conversion_fee_usd": 0,
                                "rmb_conversion_fee_cny": 0},
        "include_remittance_in_cost": False,
        # INTERNAL control statements. These stay inside the app and are NEVER
        # printed onto the customer's quotation.
        "assumptions": [
            "Đây là estimate/quotation, chưa phải nghĩa vụ thanh toán.",
            "Giá agent/đối tác phải được đối chiếu với nguồn báo giá thực tế.",
            "Không tự động hóa khai báo hải quan sai lệch.",
        ],
        # CUSTOMER-FACING general notes (e.g. the pasted sentence "Nếu có phát
        # sinh về xử lý hàng hóa, sẽ báo ngay tại thời điểm phát sinh."). This
        # is the ONLY note list the XLSX "Ghi chú" block prints.
        "customer_notes": _customer_notes(payload),
    }
    # Normalise calculation immediately (raises ValueError on bad lines).
    return calculate_quote(quote)


def _handle_quote_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, save_quotes_to_cloud
    from core.quotations import new_quote_document, prepare_quote_for_persistence

    customer_id = _text(payload.get("customerId"))
    if not customer_id:
        return _result("quote_create", "", False, "Vui lòng chọn khách hàng.")
    if not can_operate_business("sales_write"):
        return _result("quote_create", "", False, "RBAC: không có quyền sales_write.")
    customers = load_customers() or {}
    customer = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}
    if not customer:
        return _result("quote_create", "", False, f"Không tìm thấy khách hàng {customer_id}.")
    try:
        base = _quote_payload(customer, payload)
        quote = new_quote_document(base)
        stamped = prepare_quote_for_persistence(quote, actor=_actor())
    except ValueError as exc:
        return _result("quote_create", "", False, str(exc))
    if not save_quotes_to_cloud({_text(stamped.get("id")): stamped}):
        return _result("quote_create", "", False, get_last_db_error() or "Không lưu được báo giá.")
    fresh = read_quote(_text(stamped.get("id")))
    return _result("quote_create", _text(stamped.get("id")), True,
                   readback=quote_projection(fresh or {}),
                   persisted={"id": _text(stamped.get("id")), "quoteNo": _text(stamped.get("quote_no")),
                              "status": _text(stamped.get("status"))},
                   audit=_audit("quote", _text(stamped.get("id"))))


def _handle_quote_edit(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, save_quotes_to_cloud
    from core.quotations import calculate_quote, prepare_quote_for_persistence

    qid = _text(payload.get("id"))
    if not qid:
        return _result("quote_edit", qid, False, "Thiếu mã báo giá.")
    if not can_operate_business("sales_write"):
        return _result("quote_edit", qid, False, "RBAC: không có quyền sales_write.")
    quote = read_quote(qid)
    if quote is None:
        return _result("quote_edit", qid, False, f"Không tìm thấy báo giá {qid}.")
    for key in ("sales_owner", "origin", "destination", "route", "incoterm",
                "goods_description", "expected_delivery_date"):
        if key in payload:
            quote[key] = _text(payload.get(key))
    # Customer-facing notes: only replaced when this edit actually carries them,
    # so an edit that does not touch the notes can never silently erase them.
    if "customerNotes" in payload:
        quote["customer_notes"] = _customer_notes(payload)
    if isinstance(payload.get("serviceLines"), list):
        service_lines: list[dict[str, Any]] = []
        try:
          for line in payload.get("serviceLines"):
            if not isinstance(line, Mapping):
                continue
            service_lines.append({
                "code": _text(line.get("code")),
                "service_name": _text(line.get("serviceName")) or _text(line.get("code")),
                "unit": _text(line.get("unit")) or "Lần",
                "qty": _num(line.get("qty")) if _num(line.get("qty")) is not None else 1,
                "currency": _text(line.get("currency")) or "VND",
                "cost_unit": _optional_line_number(line, "costUnit", len(service_lines) + 1, "Giá vốn (unit)"),
                "sell_unit": _required_line_number(line, "sellUnit", len(service_lines) + 1, "Giá bán (unit)"),
                "tax_pct": _optional_line_number(line, "taxPct", len(service_lines) + 1, "Thuế %"),
                "cost_source": _text(line.get("costSource")) or "Nhập bởi SALE/Support.",
                # LOGI_INTERNAL_UX_SIMPLIFY_01 — same optional operator note
                # as create; an edit replaces lines wholesale, note included.
                "note": _text(line.get("note")),
            })
        except ValueError as exc:
            return _result("quote_edit", qid, False, str(exc))
        if service_lines:
            quote["service_lines"] = service_lines
    if isinstance(payload.get("fx"), Mapping) or isinstance(payload.get("serviceLines"), list):
        # Re-price with the rates the operator entered for THIS edit; rates they
        # did not touch stay as stored on the quote (never re-invented here).
        try:
            quote["fx_snapshot"] = _quote_fx_snapshot(
                payload, quote.get("service_lines") or [], base=quote.get("fx_snapshot"))
        except ValueError as exc:
            return _result("quote_edit", qid, False, str(exc))
    try:
        recomputed = calculate_quote(quote)
        stamped = prepare_quote_for_persistence(recomputed, actor=_actor())
    except ValueError as exc:
        return _result("quote_edit", qid, False, str(exc))
    if not save_quotes_to_cloud({qid: stamped}):
        return _result("quote_edit", qid, False, get_last_db_error() or "Không lưu được báo giá.")
    fresh = read_quote(qid)
    return _result("quote_edit", qid, True, readback=quote_projection(fresh or {}),
                   audit=_audit("quote", qid))


def _handle_quote_transition(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_quotes_to_cloud
    from core.quotations import prepare_quote_for_persistence, transition_quote

    qid = _text(payload.get("id"))
    target = _text(payload.get("nextStatus")).upper()
    if not qid or not target:
        return _result("quote_transition", qid, False, "Thiếu mã báo giá hoặc trạng thái đích.")
    if not can_operate_business("sales_write"):
        return _result("quote_transition", qid, False, "RBAC: không có quyền sales_write.")
    quote = read_quote(qid)
    if quote is None:
        return _result("quote_transition", qid, False, f"Không tìm thấy báo giá {qid}.")
    try:
        updated = transition_quote(quote, target, actor=_actor())
        stamped = prepare_quote_for_persistence(updated, actor=_actor())
    except ValueError as exc:
        return _result("quote_transition", qid, False, str(exc))
    if not save_quotes_to_cloud({qid: stamped}):
        return _result("quote_transition", qid, False, get_last_db_error() or "Không lưu được trạng thái.")
    fresh = read_quote(qid)
    return _result("quote_transition", qid, True, readback=quote_projection(fresh or {}),
                   persisted={"status": _text((fresh or {}).get("status"))}, audit=_audit("quote", qid))


def _handle_agreement_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.commercial_agreements import build_agreement_from_quote, prepare_agreement_for_persistence
    from core.database import get_last_db_error, save_agreements_to_cloud

    qid = _text(payload.get("quoteId"))
    if not qid:
        return _result("agreement_create", "", False, "Thiếu báo giá nguồn.")
    if not can_operate_business("commercial_write"):
        return _result("agreement_create", "", False, "RBAC: không có quyền commercial_write.")
    quote = read_quote(qid)
    if quote is None:
        return _result("agreement_create", "", False, f"Không tìm thấy báo giá {qid}.")
    if _text(quote.get("status")).upper() not in ("ACCEPTED", "READY_TO_CREATE_SHIPMENT"):
        return _result("agreement_create", "", False,
                       "Thỏa thuận chỉ được tạo từ báo giá đã được khách chốt (ACCEPTED / READY_TO_CREATE_SHIPMENT).")
    try:
        agreement = build_agreement_from_quote(quote, actor=_actor())
        stamped = prepare_agreement_for_persistence(agreement, actor=_actor())
    except ValueError as exc:
        return _result("agreement_create", "", False, str(exc))
    aid = _text(stamped.get("agreement_id"))
    if not save_agreements_to_cloud({aid: stamped}):
        return _result("agreement_create", aid, False, get_last_db_error() or "Không lưu được thỏa thuận.")
    fresh = read_agreement(aid)
    return _result("agreement_create", aid, True, readback=agreement_projection(fresh or {}),
                   persisted={"id": aid, "agreementNo": _text(stamped.get("agreement_no"))},
                   audit=_audit("agreement", aid))


def _handle_agreement_edit(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.commercial_agreements import prepare_agreement_for_persistence
    from core.database import get_last_db_error, save_agreements_to_cloud

    aid = _text(payload.get("id"))
    if not aid:
        return _result("agreement_edit", aid, False, "Thiếu mã thỏa thuận.")
    if not can_operate_business("commercial_write"):
        return _result("agreement_edit", aid, False, "RBAC: không có quyền commercial_write.")
    agreement = read_agreement(aid)
    if agreement is None:
        return _result("agreement_edit", aid, False, f"Không tìm thấy thỏa thuận {aid}.")
    for key in ("payment_terms", "responsibilities", "required_documents", "evidence",
                "unresolved_issues", "assumptions", "shipment_ids"):
        if key in payload:
            agreement[key] = payload.get(key)
    try:
        stamped = prepare_agreement_for_persistence(agreement, actor=_actor())
    except ValueError as exc:
        return _result("agreement_edit", aid, False, str(exc))
    if not save_agreements_to_cloud({aid: stamped}):
        return _result("agreement_edit", aid, False, get_last_db_error() or "Không lưu được thỏa thuận.")
    fresh = read_agreement(aid)
    return _result("agreement_edit", aid, True, readback=agreement_projection(fresh or {}),
                   audit=_audit("agreement", aid))


def _handle_agreement_transition(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.commercial_agreements import prepare_agreement_for_persistence, transition_agreement
    from core.database import get_last_db_error, save_agreements_to_cloud

    aid = _text(payload.get("id"))
    target = _text(payload.get("nextStatus")).upper()
    if not aid or not target:
        return _result("agreement_transition", aid, False, "Thiếu mã thỏa thuận hoặc trạng thái đích.")
    if not can_operate_business("commercial_write"):
        return _result("agreement_transition", aid, False, "RBAC: không có quyền commercial_write.")
    agreement = read_agreement(aid)
    if agreement is None:
        return _result("agreement_transition", aid, False, f"Không tìm thấy thỏa thuận {aid}.")
    try:
        updated = transition_agreement(agreement, target, actor=_actor())
        stamped = prepare_agreement_for_persistence(updated, actor=_actor())
    except ValueError as exc:
        return _result("agreement_transition", aid, False, str(exc))
    if not save_agreements_to_cloud({aid: stamped}):
        return _result("agreement_transition", aid, False, get_last_db_error() or "Không lưu được trạng thái.")
    fresh = read_agreement(aid)
    return _result("agreement_transition", aid, True, readback=agreement_projection(fresh or {}),
                   persisted={"status": _text((fresh or {}).get("status"))}, audit=_audit("agreement", aid))


# ---------------------------------------------------------------------------
# LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the two explicit contract facts
# the desk could display but never record.
#
# ``pl_required``: the operator's OWN decision about a phụ lục. It is stored
# verbatim as "YES" / "NO" / "" and "" is a real state ("chưa chọn"), never a
# silent "Không cần PL". This field records the decision on the contract; it
# deliberately does NOT override core.docgen's HDNT+PL-vs-HDMB threshold rule.
#
# ``date``: the contract signing date. ``contract_projection`` already reads it
# (``contractDate``) and ``core.docgen.generator`` falls back to it for a
# document date, but no component event could write it before this slice.
# ---------------------------------------------------------------------------

PL_REQUIRED = "YES"
PL_NOT_REQUIRED = "NO"

#: Operator-facing refusal when the PL answer is neither label and not blank.
_PL_REFUSAL = ("PL chỉ nhận 'Có PL', 'Không cần PL', hoặc để trống (chưa xác định) "
               "— app không tự đoán.")

#: Every spelling of the two operator labels (plus the honest "not chosen"),
#: folded to ASCII so "Có PL" and "Co PL" mean the same stored fact.
_PL_ALIASES = {
    "CO PL": PL_REQUIRED,
    "COPL": PL_REQUIRED,
    "PL": PL_REQUIRED,
    "YES": PL_REQUIRED,
    "TRUE": PL_REQUIRED,
    "1": PL_REQUIRED,
    "KHONG CAN PL": PL_NOT_REQUIRED,
    "KHONGCANPL": PL_NOT_REQUIRED,
    "KHONG PL": PL_NOT_REQUIRED,
    "NO": PL_NOT_REQUIRED,
    "FALSE": PL_NOT_REQUIRED,
    "0": PL_NOT_REQUIRED,
    "": "",
    "CHUA CHON": "",
    "UNKNOWN": "",
    "NONE": "",
}


def _pl_required_decision(value: Any) -> str | None:
    """Normalize the explicit PL choice: ``YES`` / ``NO`` / ``""`` (not chosen).

    Returns ``None`` for anything the two-label contract cannot represent, so a
    handler refuses instead of guessing. ``False``/``0``/``""`` mean "the
    operator has not decided", never "Không cần PL".
    """
    import unicodedata

    raw = "" if value is None else str(value)
    folded = "".join(
        char for char in unicodedata.normalize("NFD", raw).lower()
        if unicodedata.category(char) != "Mn"
    )
    folded = " ".join(folded.replace("_", " ").replace("-", " ").split()).upper()
    if folded in {"None", "NULL", "-"}:
        folded = ""
    return _PL_ALIASES.get(folded)


def _contract_doc(cid: str, customer_id: str | None, customer_name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": cid,
        "contract_no": cid,
        "normalized_no": cid,
        "customer": customer_name,
        "client": customer_name,
        "customer_id": customer_id or "",
        "kind": _text(payload.get("kind")),
        "status": _text(payload.get("status")) or "active",
        "value": _num(payload.get("value")) if payload.get("value") not in (None, "") else None,
        "currency": _text(payload.get("currency")) or "VND",
        "note": _text(payload.get("note")),
        # Key present = an explicit choice was made on the create form; a blank
        # choice stays "" (UNKNOWN) so the desk keeps asking instead of writing
        # a decision nobody made.
        "date": _text(payload.get("date") or payload.get("contract_date")),
        "pl_required": _pl_required_decision(payload.get("pl_required")) or "",
    }


def _handle_contract_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_edit_contract
    from core.database import get_last_db_error, load_contracts, load_customers, save_contract_to_cloud

    cid = _text(payload.get("id")).strip().upper()
    if not cid:
        return _result("contract_create", cid, False, "Cần số hợp đồng.")
    if not can_edit_contract():
        return _result("contract_create", cid, False, "RBAC: không có quyền sửa hợp đồng (sales_write).")
    contracts = load_contracts() or {}
    if cid in {_text(v.get("id")) or _text(v.get("contract_no")) for v in contracts.values()}:
        return _result("contract_create", cid, False, f"Số hợp đồng {cid} đã tồn tại.")
    customer_id = _text(payload.get("customerId"))
    customers = load_customers() or {}
    customer = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}
    customer_name = _text(customer.get("name")) or _text(payload.get("client"))
    if not customer_name:
        return _result("contract_create", cid, False, "Cần đối tác / khách hàng cho hợp đồng.")
    # An unparseable PL answer must never be quietly recorded as "no PL": the
    # whole point of the flag is that a blank means "not decided yet".
    if "pl_required" in payload and _pl_required_decision(payload.get("pl_required")) is None:
        return _result("contract_create", cid, False, _PL_REFUSAL)
    doc = _contract_doc(cid, customer_id or None, customer_name, payload)
    if not save_contract_to_cloud(doc):
        return _result("contract_create", cid, False, get_last_db_error() or "Không lưu được hợp đồng.")
    fresh = read_contract(cid)
    from views import logi_view_model as vm

    return _result("contract_create", cid, True,
                   readback=_contract_readback(fresh or {}, vm.load_shipments()),
                   audit=_audit("contract", cid))


def _contract_readback(contract: Mapping[str, Any], shipments: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import load_authority_agents, load_authority_companies, load_contracts, load_docgen_documents

    cid = _text(contract.get("id"))
    docs_by_scope = {cid: load_docgen_documents(cid) or {}}
    return contract_projection(
        contract,
        shipments=shipments,
        docs_by_scope=docs_by_scope,
        companies=load_authority_companies() or {},
        agents=load_authority_agents() or {},
        all_contracts=load_contracts() or {},
    )


def _handle_contract_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_edit_contract
    from core.database import get_last_db_error, save_contract_to_cloud

    cid = _text(payload.get("id")).strip().upper()
    if not cid:
        return _result("contract_save", cid, False, "Thiếu mã hợp đồng.")
    if not can_edit_contract():
        return _result("contract_save", cid, False, "RBAC: không có quyền sửa hợp đồng (sales_write).")
    contract = read_contract(cid)
    if contract is None:
        return _result("contract_save", cid, False, f"Không tìm thấy hợp đồng {cid}.")
    for key in ("company_id", "agent_id", "kind", "status", "currency", "note"):
        if key in payload:
            value = _text(payload.get(key))
            contract[key] = value.upper() if key in ("company_id", "agent_id") else value
    # LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the three facts the desk could
    # show but not keep. Key presence is the intent marker: an absent key leaves
    # the stored value untouched, so a save of one field never blanks another.
    if "pl_required" in payload:
        decision = _pl_required_decision(payload.get("pl_required"))
        if decision is None:
            return _result("contract_save", cid, False, _PL_REFUSAL)
        contract["pl_required"] = decision
    if "date" in payload or "contract_date" in payload:
        supplied = payload.get("date") if "date" in payload else payload.get("contract_date")
        contract["date"] = _text(supplied)
    if "customerId" in payload or "customer_id" in payload:
        supplied_customer = _text(payload.get("customerId") or payload.get("customer_id")).upper()
        if not supplied_customer:
            # A contract always has a counterparty: clearing the picker is a
            # mistake, not a business fact, so it is refused rather than stored.
            return _result("contract_save", cid, False,
                           "Hợp đồng luôn cần một khách hàng — hãy chọn khách khác thay vì để trống.")
        from core.database import load_customers

        customers = load_customers() or {}
        customer = customers.get(supplied_customer)
        if not isinstance(customer, Mapping):
            return _result("contract_save", cid, False,
                           f"Không có khách hàng {supplied_customer} trong danh bạ.")
        customer_name = _text(customer.get("name"))
        if not customer_name:
            return _result("contract_save", cid, False,
                           f"Khách hàng {supplied_customer} chưa có tên trong danh bạ.")
        contract["customer_id"] = supplied_customer
        contract["customer"] = customer_name
        contract["client"] = customer_name
    if "value" in payload:
        contract["value"] = _num(payload.get("value")) if payload.get("value") not in (None, "") else None
    # Document legal identity (per-document numbers/dates) live on the contract.
    identity = contract.setdefault("doc_identity", {}) if isinstance(contract.get("doc_identity"), Mapping) else {}
    if not isinstance(identity, dict):
        identity = {}
    for field in ("hdnt_no", "hdnt_date", "valid_from", "valid_to", "pl_no", "pl_date", "hdmb_no", "hdmb_date"):
        if field in payload:
            identity[field] = _text(payload.get(field))
    contract["doc_identity"] = identity
    if not save_contract_to_cloud(contract):
        return _result("contract_save", cid, False, get_last_db_error() or "Không lưu được hợp đồng.")
    fresh = read_contract(cid)
    from views import logi_view_model as vm

    return _result("contract_save", cid, True, readback=_contract_readback(fresh or {}, vm.load_shipments()),
                   audit=_audit("contract", cid))


def _handle_contract_goods_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_edit_contract
    from core.database import get_last_db_error, save_contract_to_cloud

    cid = _text(payload.get("id")).strip().upper()
    if not cid:
        return _result("contract_goods_save", cid, False, "Thiếu mã hợp đồng.")
    if not can_edit_contract():
        return _result("contract_goods_save", cid, False, "RBAC: không có quyền sửa hợp đồng (sales_write).")
    contract = read_contract(cid)
    if contract is None:
        return _result("contract_goods_save", cid, False, f"Không tìm thấy hợp đồng {cid}.")
    rows = payload.get("goodsLines") if isinstance(payload.get("goodsLines"), list) else None
    if rows is None:
        return _result("contract_goods_save", cid, False, "Thiếu dữ liệu hàng hóa.")
    serialised: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        description = _text(row.get("description"))
        quantity = None if row.get("quantity") in (None, "") else str(row.get("quantity"))
        unit_price = None if row.get("unitPrice") in (None, "") else str(row.get("unitPrice"))
        # A fully-empty editor row carries no business fact: drop it rather than
        # persisting a blank line that would silently block generation. UNKNOWN
        # still != ZERO for any row that has a description but a blank number.
        if not description and quantity is None and unit_price is None:
            continue
        serialised.append({
            "description": description,
            "unit": _text(row.get("unit")),
            "quantity": quantity,
            "unit_price_vnd_excl_vat": unit_price,
            "vat_rate": "0.08",
        })
    contract["goods_lines"] = serialised
    if not save_contract_to_cloud(contract):
        return _result("contract_goods_save", cid, False, get_last_db_error() or "Không lưu được hàng hóa.")
    fresh = read_contract(cid)
    from views import logi_view_model as vm

    return _result("contract_goods_save", cid, True, readback=_contract_readback(fresh or {}, vm.load_shipments()),
                   persisted={"lineCount": len(serialised)}, audit=_audit("contract", cid))


def _resolve_authority(contract: Mapping[str, Any], companies: Mapping[str, Any], agents: Mapping[str, Any]):
    company_id = _text(contract.get("company_id"))
    agent_id = _text(contract.get("agent_id"))
    company = companies.get(company_id) if company_id else None
    agent = agents.get(agent_id) if agent_id else None
    # Single-record fallback mirrors the contract workspace's default selection.
    if company is None and len(companies) == 1:
        company = next(iter(companies.values()))
    if agent is None and len(agents) == 1:
        agent = next(iter(agents.values()))
    return company, agent


def _handle_contract_docgen_generate(payload: Mapping[str, Any]) -> dict[str, Any]:
    from datetime import date

    from core.auth import can_generate_documents, current_actor_context
    from core.database import (
        link_contract_to_shipment,
        load_authority_agents,
        load_authority_companies,
        load_contracts,
        load_docgen_documents,
        save_contract_to_cloud,
        save_docgen_document,
    )
    from core.docgen import generator as gen
    from core.docgen.rules import HDMB, HDNT, PL, READY

    cid = _text(payload.get("id")).strip().upper()
    if not cid:
        return _result("contract_docgen_generate", cid, False, "Thiếu mã hợp đồng.")
    if not can_generate_documents():
        return _result("contract_docgen_generate", cid, False, "RBAC: không có quyền sales_write để sinh chứng từ.")
    contract = read_contract(cid)
    if contract is None:
        return _result("contract_docgen_generate", cid, False, f"Không tìm thấy hợp đồng {cid}.")

    companies = load_authority_companies() or {}
    agents = load_authority_agents() or {}
    company, agent = _resolve_authority(contract, companies, agents)
    if company is None or agent is None:
        return _result("contract_docgen_generate", cid, False,
                       "Chưa chọn đủ hồ sơ pháp lý Công ty (bên mua) và Đại lý (bên bán).",
                       gate="BLOCKED_NO_AUTHORITY")

    goods_lines = contract.get("goods_lines") if isinstance(contract.get("goods_lines"), list) else []
    identity = _contract_identity(contract)
    contract_view = {
        "id": cid,
        "contract_no": _text(contract.get("contract_no")) or cid,
        "currency": "VND",
        "hdnt_no": identity["hdntNo"], "hdnt_date": identity["hdntDate"],
        "valid_from": identity["validFrom"], "valid_to": identity["validTo"],
        "pl_no": identity["plNo"], "pl_date": identity["plDate"],
        "hdmb_no": identity["hdmbNo"], "hdmb_date": identity["hdmbDate"],
    }

    # HDNT reuse rule: never auto-regenerate a valid existing HDNT.
    all_contracts = load_contracts() or {}
    reuse = gen.reuse_decision_for_agent(all_contracts, agent=agent, company=company)
    parent_contract = reuse.get("reuse_target") if reuse.get("valid_count") == 1 else None
    if reuse.get("valid_count", 0) > 1:
        return _result("contract_docgen_generate", cid, False,
                       "Có nhiều HDNT hợp lệ cho Đại lý + Công ty này — cần chọn một HDNT để tái sử dụng.",
                       gate="BLOCKED_HDNT_NEEDS_SELECTION")

    # Preflight exactly like the donor: only READY documents are generated.
    delivery = {"delivery_completed": False, "delivery_date": "", "delivery_location": "",
                "receiver_name": "", "receiver_title": ""}
    pack = gen.build_document_pack(
        shipment_id=cid,
        goods_lines=goods_lines,
        delivery_completed=False,
        agent=agent,
        company=company,
        parent_contract=parent_contract,
        contract=contract_view,
        pxk_source=None,
        delivery=delivery,
        contracts=all_contracts,
    )
    cards = pack.get("cards") or []
    states = {card["document_type"]: card["state"] for card in cards}

    requested = [str(x).upper() for x in (payload.get("documentTypes") or []) if str(x).upper() in (HDNT, PL, HDMB)]
    to_generate = requested or [HDNT, PL, HDMB]
    reused_hdnt: dict[str, Any] | None = None
    if reuse.get("valid_count", 0) == 1:
        reused_hdnt = parent_contract
        # Never auto-regenerate a valid HDNT; a reuse is reported, not produced.
        to_generate = [dt for dt in to_generate if dt != HDNT]

    xlsx_path, docx_path = _resolve_template_paths()
    if xlsx_path is None or docx_path is None:
        return _result("contract_docgen_generate", cid, False,
                       "Chưa có template chứng từ (DOCGEN_TEMPLATE_DIR) — hệ thống không tự sinh file giả.",
                       gate="TEMPLATE_ASSET_STORAGE_OWNER_GATE", failClosed=True)

    actor = current_actor_context()
    for line in goods_lines:
        if isinstance(line, dict):
            line.setdefault("confirmed_by", actor["username"])
            line.setdefault("confirmed_at", date.today().isoformat())

    existing = load_docgen_documents(cid) or {}
    produced: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for doc_type in to_generate:
        state = states.get(doc_type)
        if state != READY:
            card = next((c for c in cards if c.get("document_type") == doc_type), {})
            blocked.append({
                "documentType": doc_type,
                "reason": card.get("reason") or f"{doc_type} chưa sẵn sàng để xuất.",
                "missing": list(card.get("missing") or []),
                "state": state,
            })
            continue

        # Each legal document owns its own identity: the generated document is
        # persisted as its OWN contract record (id = its legal number) so it is
        # reusable — e.g. a fresh HDNT becomes the valid parent of a later PL.
        doc_contract = dict(contract_view)
        doc_no = _text(doc_contract.get(f"{doc_type.lower()}_no")).strip().upper()
        doc_contract["id"] = doc_no
        if not doc_contract["id"]:
            blocked.append({"documentType": doc_type, "reason": f"Thiếu số {doc_type}.", "state": "MISSING_INFO"})
            continue

        try:
            generated = gen.generate_document(
                doc_type,
                shipment_id=cid,
                agent=agent,
                company=company,
                goods_lines=goods_lines,
                contract=doc_contract,
                parent_contract=parent_contract if doc_type in (PL, HDNT) else None,
                delivery=delivery,
                template_path_xlsx=xlsx_path,
                template_path_docx=docx_path,
                existing_documents=existing,
            )
        except gen.DocumentGenerationError as exc:
            blocked.append({"documentType": doc_type, "reason": exc.readiness.reason,
                            "missing": list(exc.readiness.missing), "state": exc.readiness.state})
            continue
        except PermissionError:
            blocked.append({"documentType": doc_type, "reason": "RBAC: không có quyền sinh chứng từ."})
            continue

        # Persist the generated document as a reusable child contract record
        # (mirrors views/docgen._do_generate): kind, legal identity, parties.
        doc_contract["kind"] = doc_type
        doc_contract["contract_no"] = doc_contract.get(f"{doc_type.lower()}_no") or doc_contract["id"]
        doc_contract["agent_id"] = _text(agent.get("agent_id") or agent.get("id"))
        doc_contract["company_id"] = _text(company.get("company_id") or company.get("id"))
        save_contract_to_cloud(doc_contract)
        link_contract_to_shipment(doc_contract["id"], cid)

        metadata = generated.get("metadata") or {}
        metadata["generated_by"] = actor["username"]
        if not save_docgen_document(metadata):
            blocked.append({"documentType": doc_type, "reason": "Không lưu được metadata chứng từ."})
            continue
        record_id = _text(metadata.get("id")) or f"{generated['document_id']}::R{generated['revision']}"
        store_output(
            cid, record_id,
            {"file_name": generated.get("output_file_name"), "mime": _MIME_DOCX if doc_type == HDNT else _MIME_XLSX,
             "bytes": generated.get("bytes") or b"", "document_type": doc_type,
             "revision": generated.get("revision")},
        )
        produced.append({
            "documentType": doc_type, "ok": True,
            "documentId": _text(generated.get("document_id")),
            "revision": generated.get("revision"),
            "fileName": _text(generated.get("output_file_name")),
            "isOfficeFile": (generated.get("bytes") or b"")[:2] == b"PK",
        })

    if not produced and not blocked and to_generate:
        blocked.append({"documentType": ", ".join(to_generate),
                        "reason": "Không có chứng từ nào được sinh.", "state": "NOT_APPLICABLE"})
    if not produced and blocked:
        first = blocked[0]
        return _result("contract_docgen_generate", cid, False, first["reason"],
                       gate="BLOCKED", blocked=blocked, reusedHdnt=reused_hdnt, failClosed=True)
    fresh = read_contract(cid)
    from views import logi_view_model as vm

    return _result("contract_docgen_generate", cid, True,
                   readback=_contract_readback(fresh or {}, vm.load_shipments()),
                   produced=produced, blocked=blocked, reusedHdnt=reused_hdnt,
                   service="core.docgen.generator.generate_document",
                   audit=_audit("contract", cid))


def _handle_contract_docgen_issue(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import PermissionDeniedError
    from core.docgen import generator as gen

    document_id = _text(payload.get("documentId"))
    revision = payload.get("revision")
    if not document_id:
        return _result("contract_docgen_issue", document_id, False, "Thiếu mã chứng từ.")
    try:
        result = gen.issue_document(document_id, revision=int(revision) if revision else None)
    except gen.DocumentGenerationError as exc:
        return _result("contract_docgen_issue", document_id, False, exc.readiness.reason)
    except (PermissionError, PermissionDeniedError):
        return _result("contract_docgen_issue", document_id, False, "RBAC: không có quyền operations_write để phát hành.")
    return _result("contract_docgen_issue", document_id, True,
                   persisted={"documentId": result.get("document_id"), "status": result.get("status")},
                   audit=_audit("docgen_document", _text(result.get("document_id"))))


def _handle_contract_shipment_link(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import get_last_db_error, link_contract_to_shipment

    cid = _text(payload.get("id")).strip().upper()
    sid = _text(payload.get("shipmentId")).strip().upper()
    if not cid or not sid:
        return _result("contract_shipment_link", cid, False, "Thiếu mã hợp đồng hoặc mã lô.")
    if not link_contract_to_shipment(cid, sid):
        return _result("contract_shipment_link", cid, False, get_last_db_error() or "Không liên kết được lô với hợp đồng.")
    fresh = read_contract(cid)
    from views import logi_view_model as vm

    return _result("contract_shipment_link", cid, True,
                   readback=_contract_readback(fresh or {}, vm.load_shipments()),
                   linkedShipmentIds=[str(x).upper() for x in (fresh or {}).get("shipment_ids", [])],
                   audit=_audit("contract", cid))


# ---------------------------------------------------------------------------
# LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — Đại Lý Trường Thành agent
# master CREATE / EDIT through the EXISTING canonical writer.
# ---------------------------------------------------------------------------

#: The ONLY fields this event may write — exactly what the existing
#: authority_agents master projects (views.logi_c1._party_view). No tax /
#: credit / SLA / risk / rating field exists, so none is accepted.
AGENT_SAVE_FIELDS: tuple[tuple[str, str], ...] = (
    ("legalName", "legal_name"),
    ("legalCode", "legal_code"),
    ("legalAddress", "legal_address"),
    ("legalRepresentative", "legal_representative"),
    ("representativeTitle", "representative_title"),
    ("phone", "phone"),
    ("email", "email"),
    ("bankAccountHolder", "bank_account_holder"),
    ("bankAccountNumber", "bank_account_number"),
    ("bankName", "bank_name"),
    ("bankBranch", "bank_branch"),
)


def read_authority_agent(agent_id: str) -> dict[str, Any] | None:
    """Fresh read of ONE agent master straight from the canonical reader."""
    from core.database import load_authority_agents

    agents = load_authority_agents() or {}
    record = agents.get(agent_id)
    if isinstance(record, Mapping):
        return dict(record)
    record = next(
        (d for d in agents.values()
         if isinstance(d, Mapping) and _text(d.get("agent_id")) == agent_id),
        None,
    )
    return dict(record) if record else None


def _handle_authority_agent_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """CREATE or EDIT one authority_agents master via the existing writer.

    Flow: RBAC (sales_write — Admin/Support/Sale allowed, viewer refused)
      → core.database.save_authority_agent (upsert + audit, canonical agent_id
        handling — the writer itself re-enforces the same permission)
      → fresh load_authority_agents readback through the SAME _party_view
        projection every other screen uses, so one master never renders two
        ways. No optimistic persistence: the component shows the saved master
        only when this readback arrives.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_authority_agent

    agent_id = _text(payload.get("agentId") or payload.get("id")).strip().upper()
    request_id = _text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("authority_agent_save", agent_id, ok, error,
                       requestId=request_id, **extra)

    if not agent_id:
        return _res(False, "Thiếu mã đại lý.")
    legal_name = _text(payload.get("legalName"))
    if not legal_name:
        return _res(False, "Tên pháp lý là bắt buộc — hồ sơ đại lý không tên không dùng được.")
    if not can_operate_business("sales_write"):
        return _res(False, "RBAC: không có quyền sales_write.")

    # Merge-on-edit: only the fields this form genuinely carries are overlaid,
    # so an edit can never blank master data this slice does not manage.
    doc = read_authority_agent(agent_id) or {}
    doc["agent_id"] = agent_id
    doc["legal_name"] = legal_name
    for payload_key, doc_key in AGENT_SAVE_FIELDS:
        if payload_key in payload:
            doc[doc_key] = _text(payload.get(payload_key))

    if not save_authority_agent(doc):
        return _res(False, get_last_db_error() or "Không lưu được hồ sơ đại lý.")

    fresh = read_authority_agent(agent_id)
    return _res(True, readback=_party_view(fresh or {}, "agent"),
                persisted={"agentId": agent_id, "legalName": _text((fresh or {}).get("legal_name"))},
                audit=_audit("authority_agent", agent_id))


def _handle_quote_export_xlsx(payload: Mapping[str, Any]) -> dict[str, Any]:
    """READ-ONLY: render the customer quotation XLSX for ONE existing quote.

    Authority chain: RBAC (commercial_view) -> fresh canonical quote read ->
    existing ``core.excel_utils.generate_quote_excel`` -> bounded base64 on the
    normal outcome channel. Nothing is written, no ledger is touched and the
    quote document itself is not modified.
    """
    import base64

    from core.auth import can_operate_business
    from core.database import load_authority_companies
    from core.config import BASE_DIR
    from core.excel_utils import generate_quote_excel

    qid = _text(payload.get("id"))
    request_id = _text(payload.get("requestId"))
    if not qid:
        return _result("quote_export_xlsx", "", False, "Thiếu mã báo giá.", requestId=request_id)
    if not can_operate_business("commercial_view"):
        return _result("quote_export_xlsx", qid, False,
                       "RBAC: không có quyền xem báo giá.", requestId=request_id)
    quote = read_quote(qid)
    if quote is None:
        return _result("quote_export_xlsx", qid, False,
                       f"Không tìm thấy báo giá {qid}.", requestId=request_id)

    # Company authority: the EXISTING legal master. Never a hard-coded brand,
    # and never the sample customer from the Owner's reference workbook.
    companies = load_authority_companies() or {}
    company = next(iter(companies.values()), {}) if companies else {}

    # Contact enrichment from the EXISTING customer master, resolved by the
    # quote's canonical customer_id. Read-only: the customer is never mutated,
    # and a customer the master does not hold simply contributes nothing.
    customer = read_customer(_text(quote.get("customer_id"))) or {}

    # The quotation's own date authority lives in core.excel_utils
    # (_quote_display_date): explicit quote date → canonical created_at → today.
    # Nothing is stamped here, so re-exporting an old quote keeps its own date.
    logo = BASE_DIR / "logo.png" if (BASE_DIR / "logo.png").exists() else None
    try:
        buffer = generate_quote_excel(dict(quote), company=company,
                                      customer=customer, logo_path=logo)
    except Exception as exc:  # noqa: BLE001 - surface the real reason, write nothing
        return _result("quote_export_xlsx", qid, False,
                       f"Không tạo được file báo giá: {exc}", requestId=request_id)

    data = buffer.getvalue()
    file_name = f"BAOGIA_{_text(quote.get('quote_no')) or qid}.xlsx"
    return _result(
        "quote_export_xlsx", qid, True,
        requestId=request_id,
        document={
            "fileName": file_name,
            "mime": _MIME_XLSX,
            "downloadAvailable": True,
            "downloadBase64": base64.b64encode(data).decode("ascii"),
            "byteSize": len(data),
        },
    )


_HANDLERS = {
    "customer_create": _handle_customer_create,
    "customer_edit": _handle_customer_edit,
    "customer_archive": _handle_customer_archive,
    "customer_import": _handle_customer_import,
    "customer_getfly_import": _handle_customer_getfly_import,
    "quote_create": _handle_quote_create,
    "quote_edit": _handle_quote_edit,
    "quote_transition": _handle_quote_transition,
    "agreement_create": _handle_agreement_create,
    "agreement_edit": _handle_agreement_edit,
    "agreement_transition": _handle_agreement_transition,
    "contract_create": _handle_contract_create,
    "contract_save": _handle_contract_save,
    "contract_goods_save": _handle_contract_goods_save,
    "contract_docgen_generate": _handle_contract_docgen_generate,
    "contract_docgen_issue": _handle_contract_docgen_issue,
    "contract_shipment_link": _handle_contract_shipment_link,
    "authority_agent_save": _handle_authority_agent_save,
    "contract_intl_snapshot_save": lambda p: __import__("views.logi_intl_snapshot", fromlist=["handle_contract_intl_snapshot_save"]).handle_contract_intl_snapshot_save(p, {"read_contract": read_contract, "contract_projection": contract_projection, "_result": _result, "_audit": _audit}),
    "contract_payment_snapshot_save": lambda p: __import__("views.logi_intl_snapshot", fromlist=["handle_contract_intl_snapshot_save"]).handle_contract_intl_snapshot_save(p, {"read_contract": read_contract, "contract_projection": contract_projection, "_result": _result, "_audit": _audit}),
    "quote_export_xlsx": _handle_quote_export_xlsx,
    "cost_rate_parse": lambda p: __import__("views.logi_cost_intelligence", fromlist=["handle_cost_rate_parse"]).handle_cost_rate_parse(p, {"_result": _result, "_audit": _audit, "_actor": _actor}),
    "cost_rate_save": lambda p: __import__("views.logi_cost_intelligence", fromlist=["handle_cost_rate_save"]).handle_cost_rate_save(p, {"_result": _result, "_audit": _audit, "_actor": _actor}),
    "cost_rate_status_set": lambda p: __import__("views.logi_cost_intelligence", fromlist=["handle_cost_rate_status_set"]).handle_cost_rate_status_set(p, {"_result": _result, "_audit": _audit, "_actor": _actor}),
    "cost_catalog_save": lambda p: __import__("views.logi_cost_intelligence", fromlist=["handle_cost_catalog_save"]).handle_cost_catalog_save(p, {"_result": _result, "_audit": _audit, "_actor": _actor}),
}


def consume_c1_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded Phase C1 dispatcher (pure over an explicit session dict).

    Only the declared C1 event names are handled; anything else is ignored.
    A replayed ``seq`` can never double-write.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(C1_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        handler = _HANDLERS.get(event_name)
        if handler is None:  # pragma: no cover - C1_EVENTS and _HANDLERS agree
            continue
        try:
            outcomes.append(handler(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            outcomes.append(_result(event_name, _text(data.get("id")), False,
                                    f"{type(exc).__name__}: {exc}"))
        # Correlate every create result, including caught writer exceptions.
        if event_name == "contract_create":
            outcomes[-1]["requestId"] = _text(data.get("requestId"))
    if outcomes:
        session["writes"] = outcomes
    return outcomes
