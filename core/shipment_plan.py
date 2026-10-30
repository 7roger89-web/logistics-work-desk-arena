"""Node 00 — Kế hoạch (plan) truth projection.  Issue #244.

One **read-only** projection of the three things that must be settled BEFORE a
lot moves, using only sources the repository already owns:

``Báo giá``   ← the quote **exactly linked** by ``shipment.quote_id``
``Hợp đồng``  ← the customer-facing contract linked to THIS lot
``Tạm ứng``   ← goods advance from the customer to Trường Thành, which only
                exists for a *confirmed* entrusted-import flow

Hard rules carried by this module (they are the acceptance contract):

* **No fuzzy linking.** The lot's quote is ``shipment.quote_id`` or nothing;
  another quote of the same customer is never borrowed.  A contract is only a
  customer contract when its ``customer_id`` is this lot's customer; a
  TT↔sub-agent purchase contract is a different instrument and can never be
  reported as the customer contract.
* **No implied signature.** A linked contract, a generated PDF or an attachment
  is NOT a signature.  ``ATTESTED`` requires an explicit recorded signature /
  customer-confirmation evidence that already exists in the repository
  (``core.commercial_agreements`` evidence flags); anything else stays
  ``UNVERIFIED``.
* **No implied payment.** Nothing in this repository classifies an incoming
  receipt as "customer paid the goods advance for this lot".  A quote amount, an
  estimated service line, a partner payable or a payment *request* therefore
  never becomes money received.  Unclassified receipts are surfaced as
  "cần đối soát", never as a paid advance, and never as a debt.
* **UNKNOWN stays UNKNOWN.** Missing facts render as explicit unknown states;
  nothing is defaulted to 0 / PAID / SIGNED / DONE.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

PLAN_STAGE_ID = "plan"
PLAN_NODE_LABEL = "KẾ HOẠCH"

#: Where the existing writers live. These are the SAME routes/tabs the shipped
#: document workflow already points at — no new screen is introduced.
QUOTE_ROUTE = "/kinh-doanh-bao-gia"
CONTRACT_ROUTE = "/hop-dong"
FINANCE_TAB = "tai-chinh"

QUOTE_STATE_LINKED = "LINKED"
QUOTE_STATE_MISSING = "MISSING"
QUOTE_STATE_UNRESOLVED = "UNRESOLVED"

CONTRACT_STATE_LINKED = "LINKED"
CONTRACT_STATE_MISSING = "MISSING"
CONTRACT_STATE_AMBIGUOUS = "AMBIGUOUS"

SIGNATURE_ATTESTED = "ATTESTED"
SIGNATURE_UNVERIFIED = "UNVERIFIED"

ADVANCE_NOT_APPLICABLE = "NOT_APPLICABLE"
ADVANCE_UNVERIFIED = "UNVERIFIED"
ADVANCE_MODE_UNKNOWN = "MODE_UNKNOWN"
#: Reserved for a future, separately approved receipt-classification source.
#: Deliberately unreachable today: see :func:`build_advance_item`.
ADVANCE_RECEIVED = "RECEIVED"

_MODE_ENTRUSTED = {"TT_ENTRUSTED_DIRECT", "TT_ENTRUSTED_SUB"}

#: Quote status vocabulary is owned by ``core.quotations.QUOTE_STATUSES``;
#: these are display labels only.
QUOTE_STATUS_LABELS: dict[str, str] = {
    "DRAFT": "Bản nháp",
    "READY_FOR_REVIEW": "Chờ duyệt nội bộ",
    "SENT": "Đã gửi khách",
    "ACCEPTED": "Khách đã chấp nhận",
    "REJECTED": "Khách từ chối",
    "EXPIRED": "Hết hiệu lực",
    "READY_TO_CREATE_SHIPMENT": "Sẵn sàng tạo lô",
}

NODE_STATE_COMPLETED = "COMPLETED"
NODE_STATE_WAITING = "WAITING"
NODE_STATE_PROBLEM = "PROBLEM"


def _text(value: Any, limit: int = 240) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    return str(value).replace("\r", " ").strip()[:limit]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _upper(value: Any) -> str:
    return _text(value).upper()


def _find_quote(quote_id: str, quotes: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """The ONE quote this lot points at, or nothing.

    ``quotes`` is keyed differently by each reader (quote id / quote_no), so the
    id is also matched on the record's own ``id``/``quote_no``.  No other quote
    is ever considered: a same-customer quote is not this lot's quote.
    """
    if not quote_id:
        return None
    rows = quotes or {}
    direct = rows.get(quote_id)
    if isinstance(direct, Mapping):
        return direct
    target = quote_id.upper()
    for row in rows.values():
        if not isinstance(row, Mapping):
            continue
        if _upper(row.get("id")) == target or _upper(row.get("quote_no")) == target:
            return row
    return None


def build_quote_item(shipment: Mapping[str, Any], quotes: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Quote status for THIS lot, from the exact ``quote_id`` link only."""
    quote_id = _text(shipment.get("quote_id"), 64)
    if not quote_id:
        return {
            "id": "quotation",
            "label": "Báo giá",
            "state": QUOTE_STATE_MISSING,
            "stateLabel": "Chưa gắn báo giá",
            "detail": "Lô chưa được gắn báo giá nào. Không dùng báo giá khác của cùng khách.",
            "quoteId": "",
            "quoteNo": "",
            "quoteStatus": "",
            "targetRoute": QUOTE_ROUTE,
            "actionLabel": "Mở báo giá",
        }

    quote = _find_quote(quote_id, quotes)
    if quote is None:
        return {
            "id": "quotation",
            "label": "Báo giá",
            "state": QUOTE_STATE_UNRESOLVED,
            "stateLabel": "Không đọc được báo giá đã gắn",
            "detail": f"Lô trỏ tới báo giá {quote_id} nhưng không tìm thấy hồ sơ báo giá tương ứng.",
            "quoteId": quote_id,
            "quoteNo": "",
            "quoteStatus": "",
            "targetRoute": QUOTE_ROUTE,
            "actionLabel": "Mở báo giá",
        }

    status = _upper(quote.get("status")) or "DRAFT"
    quote_no = _text(quote.get("quote_no"), 64) or _text(quote.get("id"), 64) or quote_id
    status_label = QUOTE_STATUS_LABELS.get(status, status)
    # ACCEPTED is reported only because the quote record itself says so — a
    # linked quote is not an accepted quote.
    detail = f"Báo giá {quote_no} · {status_label}."
    if status != "ACCEPTED":
        detail += " Chưa có trạng thái khách chấp nhận."
    return {
        "id": "quotation",
        "label": "Báo giá",
        "state": QUOTE_STATE_LINKED,
        "stateLabel": status_label,
        "detail": detail,
        "quoteId": _text(quote.get("id"), 64) or quote_id,
        "quoteNo": quote_no,
        "quoteStatus": status,
        "accepted": status == "ACCEPTED",
        "targetRoute": f"{QUOTE_ROUTE}?q={quote_no}",
        "actionLabel": "Mở báo giá",
    }


def _candidate_contracts(
    shipment: Mapping[str, Any],
    shipment_id: str,
    contracts: Mapping[str, Any] | None,
    linked_contracts: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    """Contracts that are linked to THIS lot — never the whole collection."""
    rows: dict[str, Mapping[str, Any]] = {}
    for key, row in _mapping(linked_contracts).items():
        if isinstance(row, Mapping):
            rows[_text(key) or _text(row.get("id"))] = row
    contract_id = _text(shipment.get("contract_id"), 64)
    if contract_id:
        row = _mapping(contracts).get(contract_id)
        if isinstance(row, Mapping):
            rows.setdefault(contract_id, row)
    if not shipment_id:
        return list(rows.values())
    for key, row in _mapping(contracts).items():
        if not isinstance(row, Mapping):
            continue
        scope = {_upper(item) for item in (row.get("shipment_ids") or [])}
        single = _upper(row.get("shipment_id"))
        if _upper(shipment_id) in scope or (single and single == _upper(shipment_id)):
            rows.setdefault(_text(key) or _text(row.get("id")), row)
    return [row for row in rows.values() if _text(row.get("id") or row.get("contract_no"))]


def _contract_is_customer_facing(row: Mapping[str, Any], customer_id: str) -> bool:
    """A TT↔sub-agent purchase contract is a DIFFERENT instrument."""
    if _upper(row.get("agent_id")):
        return False
    contract_customer = _upper(row.get("customer_id") or row.get("client_id"))
    return bool(customer_id) and contract_customer == customer_id


def _signature_evidence(
    contract_rows: Sequence[Mapping[str, Any]],
    agreements: Mapping[str, Any] | Sequence[Any] | None,
    *,
    shipment_id: str,
    customer_id: str,
) -> tuple[str, str]:
    """Signature / customer-confirmation evidence, only where it is recorded.

    Accepted sources are the EXISTING commercial-agreement evidence flags
    (``core.commercial_agreements``) for an AGREED agreement on this lot, or an
    explicit signature field already on the contract record.  A linked contract,
    a generated file or an attachment proves nothing here.
    """
    contract_ids = {
        _upper(row.get("id") or row.get("contract_no")) for row in contract_rows
        if _text(row.get("id") or row.get("contract_no"))
    }
    for row in contract_rows:
        if _text(row.get("signed_at"), 40) or row.get("signed") is True:
            return SIGNATURE_ATTESTED, "hồ sơ hợp đồng có ghi nhận chữ ký"

    rows = agreements.values() if isinstance(agreements, Mapping) else (agreements or ())
    for agreement in rows:
        if not isinstance(agreement, Mapping):
            continue
        if _upper(agreement.get("customer_id")) != customer_id:
            continue
        scope = {_upper(item) for item in (agreement.get("shipment_ids") or [])}
        if _upper(shipment_id) not in scope:
            continue
        agreement_contract = _upper(agreement.get("contract_id") or agreement.get("contract_no"))
        if contract_ids and agreement_contract and agreement_contract not in contract_ids:
            continue
        evidence = _mapping(agreement.get("evidence"))
        if _upper(agreement.get("status")) != "AGREED":
            continue
        if evidence.get("signed_contract") or evidence.get("customer_confirmation"):
            flag = "signed_contract" if evidence.get("signed_contract") else "customer_confirmation"
            return SIGNATURE_ATTESTED, f"hồ sơ thỏa thuận thương mại ghi nhận {flag}"
    return SIGNATURE_UNVERIFIED, ""


def build_contract_item(
    shipment: Mapping[str, Any],
    *,
    contracts: Mapping[str, Any] | None = None,
    linked_contracts: Mapping[str, Any] | None = None,
    agreements: Mapping[str, Any] | Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Customer contract status for THIS lot (never a TT↔sub-agent contract)."""
    shipment_id = _text(shipment.get("id") or shipment.get("shipment_id"), 64)
    customer_id = _upper(shipment.get("customer_id"))
    candidates = _candidate_contracts(shipment, shipment_id, contracts, linked_contracts)
    customer_rows = [row for row in candidates if _contract_is_customer_facing(row, customer_id)]

    if not customer_rows:
        other = " Không dùng hợp đồng Trường Thành ↔ đơn vị nhập khẩu hộ thay thế." if candidates else ""
        return {
            "id": "customer_contract",
            "label": "Hợp đồng với khách",
            "state": CONTRACT_STATE_MISSING,
            "stateLabel": "Chưa có hợp đồng với khách",
            "detail": "Lô chưa gắn hợp đồng khách hàng nào." + other,
            "contractId": "",
            "contractNo": "",
            "signature": SIGNATURE_UNVERIFIED,
            "signatureLabel": "Chưa xác minh",
            "targetRoute": CONTRACT_ROUTE,
            "actionLabel": "Mở hợp đồng",
        }

    if len(customer_rows) > 1:
        return {
            "id": "customer_contract",
            "label": "Hợp đồng với khách",
            "state": CONTRACT_STATE_AMBIGUOUS,
            "stateLabel": "Chưa xác minh",
            "detail": f"Có {len(customer_rows)} hợp đồng cùng khớp lô này; cần chọn đúng một hợp đồng, hệ thống không tự đoán.",
            "contractId": "",
            "contractNo": "",
            "signature": SIGNATURE_UNVERIFIED,
            "signatureLabel": "Chưa xác minh",
            "targetRoute": CONTRACT_ROUTE,
            "actionLabel": "Mở hợp đồng",
        }

    row = customer_rows[0]
    contract_id = _text(row.get("id") or row.get("contract_no"), 64)
    contract_no = _text(row.get("contract_no") or row.get("id"), 64)
    signature, source = _signature_evidence(
        customer_rows, agreements, shipment_id=shipment_id, customer_id=customer_id
    )
    if signature == SIGNATURE_ATTESTED:
        signature_label = "Đã có xác nhận ký"
        detail = f"Hợp đồng {contract_no} đã có xác nhận ký ({source})."
    else:
        signature_label = "Chưa xác minh chữ ký"
        detail = (
            f"Hợp đồng {contract_no} đã gắn lô nhưng chưa có bằng chứng chữ ký/xác nhận của khách; "
            "hợp đồng đã link không đồng nghĩa đã ký."
        )
    return {
        "id": "customer_contract",
        "label": "Hợp đồng với khách",
        "state": CONTRACT_STATE_LINKED,
        "stateLabel": "Đã gắn hợp đồng" if signature != SIGNATURE_ATTESTED else "Đã có xác nhận ký",
        "detail": detail,
        "contractId": contract_id,
        "contractNo": contract_no,
        "signature": signature,
        "signatureLabel": signature_label,
        "targetRoute": f"{CONTRACT_ROUTE}/{contract_id}" if contract_id else CONTRACT_ROUTE,
        "actionLabel": "Mở hợp đồng",
    }


def build_advance_item(
    flow: Mapping[str, Any] | None,
    *,
    payments: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Goods advance from the customer to Trường Thành — only for entrusted lots.

    There is no receipt-classification authority in this repository, so
    ``RECEIVED`` is unreachable: an unclassified receipt is reported as
    "cần đối soát", never as a paid advance and never as a debt.
    """
    flow = _mapping(flow)
    mode = _upper(flow.get("mode"))
    confirmed = bool(flow.get("confirmed")) and mode in _MODE_ENTRUSTED | {"CUSTOMER_SELF"}

    if not confirmed:
        return {
            "id": "customer_advance",
            "label": "Tạm ứng tiền hàng cho TT",
            "state": ADVANCE_MODE_UNKNOWN,
            "stateLabel": "Chưa xác nhận hình thức nhập khẩu",
            "applicable": None,
            "received": False,
            "detail": "Chưa xác nhận hình thức nhập khẩu nên chưa xác định khoản tạm ứng tiền hàng có áp dụng hay không.",
            "reconcileCount": 0,
            "targetTab": FINANCE_TAB,
            "actionLabel": "Mở tài chính",
        }

    if mode not in _MODE_ENTRUSTED:
        return {
            "id": "customer_advance",
            "label": "Tạm ứng tiền hàng cho TT",
            "state": ADVANCE_NOT_APPLICABLE,
            "stateLabel": "Không áp dụng",
            "applicable": False,
            "received": False,
            "detail": "Khách tự đứng tên nhập khẩu; Trường Thành không thu tạm ứng tiền hàng cho lô này.",
            "reconcileCount": 0,
            "targetTab": FINANCE_TAB,
            "actionLabel": "Mở tài chính",
        }

    reconcile = sum(
        1
        for row in (payments or ())
        if isinstance(row, Mapping)
        and not row.get("reversed")
        and _text(row.get("amount")) not in {"", "0", "0.0"}
    )
    detail = (
        "Chưa có bản ghi khoản khách chuyển tiền hàng cho Trường Thành đúng lô/hợp đồng, "
        "đúng mục đích và đơn vị tiền tệ."
    )
    if reconcile:
        detail += f" Có {reconcile} khoản thu chưa phân loại cần đối soát — không kết luận đã thanh toán."
    return {
        "id": "customer_advance",
        "label": "Tạm ứng tiền hàng cho TT",
        "state": ADVANCE_UNVERIFIED,
        "stateLabel": "Chưa xác minh đã nhận",
        "applicable": True,
        "received": False,
        "detail": detail,
        "reconcileCount": reconcile,
        "targetTab": FINANCE_TAB,
        "actionLabel": "Mở tài chính",
    }


def _next_actions(items: Sequence[Mapping[str, Any]]) -> list[str]:
    """What is still missing / what to do next — derived from the same items."""
    actions: list[str] = []
    quote, contract, advance = items[0], items[1], items[2]
    if quote["state"] == QUOTE_STATE_MISSING:
        actions.append("Gắn báo giá cho lô trước khi lấy hàng.")
    elif quote["state"] == QUOTE_STATE_UNRESOLVED:
        actions.append("Báo giá đã gắn không đọc được; kiểm tra lại liên kết báo giá của lô.")
    elif not quote.get("accepted"):
        actions.append(f"Báo giá đang ở trạng thái “{quote['stateLabel']}”; chưa có trạng thái khách chấp nhận.")

    if contract["state"] == CONTRACT_STATE_MISSING:
        actions.append("Chưa có hợp đồng với khách cho lô này.")
    elif contract["state"] == CONTRACT_STATE_AMBIGUOUS:
        actions.append("Nhiều hợp đồng cùng khớp lô; cần chọn đúng một hợp đồng với khách.")
    elif contract.get("signature") != SIGNATURE_ATTESTED:
        actions.append("Hợp đồng đã gắn nhưng chưa có bằng chứng chữ ký/xác nhận của khách.")

    if advance["state"] == ADVANCE_MODE_UNKNOWN:
        actions.append("Xác nhận hình thức nhập khẩu để biết khoản tạm ứng tiền hàng có áp dụng.")
    elif advance["state"] == ADVANCE_UNVERIFIED:
        actions.append("Chưa xác minh khoản khách chuyển tiền hàng cho Trường Thành của lô này.")
    return actions


def _node_state(items: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    """Honest map state for node 00 — never COMPLETED without evidence."""
    quote, contract, advance = items[0], items[1], items[2]
    if quote["state"] in {QUOTE_STATE_MISSING, QUOTE_STATE_UNRESOLVED}:
        return NODE_STATE_PROBLEM, "Chưa gắn được báo giá cho lô."
    if contract["state"] != CONTRACT_STATE_LINKED:
        return NODE_STATE_WAITING, "Chưa xác minh được hợp đồng với khách của lô."
    if contract.get("signature") != SIGNATURE_ATTESTED:
        return NODE_STATE_WAITING, "Hợp đồng chưa có bằng chứng chữ ký/xác nhận."
    if advance["state"] in {ADVANCE_MODE_UNKNOWN, ADVANCE_UNVERIFIED}:
        return NODE_STATE_WAITING, "Chưa xác minh khoản tạm ứng tiền hàng."
    return NODE_STATE_COMPLETED, "Đủ bằng chứng cho cả ba mục kế hoạch."


def build_plan_node(
    shipment: Mapping[str, Any],
    *,
    quotes: Mapping[str, Any] | None = None,
    contracts: Mapping[str, Any] | None = None,
    linked_contracts: Mapping[str, Any] | None = None,
    agreements: Mapping[str, Any] | Sequence[Any] | None = None,
    flow: Mapping[str, Any] | None = None,
    payments: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """The Node 00 payload: three bounded items + honest next actions."""
    items = [
        build_quote_item(shipment, quotes),
        build_contract_item(
            shipment,
            contracts=contracts,
            linked_contracts=linked_contracts,
            agreements=agreements,
        ),
        build_advance_item(flow, payments=payments),
    ]
    state, evidence = _node_state(items)
    return {
        "id": PLAN_STAGE_ID,
        "label": PLAN_NODE_LABEL,
        "state": state,
        "evidence": evidence,
        "items": items,
        "nextActions": _next_actions(items),
        "summary": {
            "problem": sum(1 for item in items if item["state"] in {QUOTE_STATE_MISSING, QUOTE_STATE_UNRESOLVED}),
            "waiting": sum(
                1 for item in items
                if item["state"] not in {QUOTE_STATE_MISSING, QUOTE_STATE_UNRESOLVED, ADVANCE_NOT_APPLICABLE}
            ),
        },
    }


# --------------------------------------------------------------------------- #
# Customer side — ONLY already-published plan documents
# --------------------------------------------------------------------------- #

#: The three plan document kinds the customer publication allowlist already
#: carries (``core.hexa_customer_publication.ALLOWED_DOCUMENT_KINDS``).
PLAN_DOCUMENT_LABELS: tuple[tuple[str, str], ...] = (
    ("CUSTOMER_QUOTE", "Báo giá"),
    ("CUSTOMER_CONTRACT", "Hợp đồng"),
    ("PAYMENT_REQUEST", "Đề nghị thanh toán"),
)
PLAN_DOCUMENT_KINDS = frozenset(kind for kind, _label in PLAN_DOCUMENT_LABELS)
_LABEL_BY_KIND = dict(PLAN_DOCUMENT_LABELS)
EMPTY_PLAN_DOCUMENTS_LABEL = "Chưa có hồ sơ Kế hoạch được công bố"


def customer_plan_documents(documents: Sequence[Mapping[str, Any]] | None) -> list[dict[str, str]]:
    """Kind-filter over ALREADY published documents (metadata only).

    ``documents`` must be the allowlisted projection from
    ``core.hexa_customer_publication.build_customer_publication`` — this
    function never reads storage, never accepts raw shipment rows, and never
    returns amounts, bytes, storage ids or internal kinds.  A published document
    does not prove a signature or a payment.
    """
    rows: list[dict[str, str]] = []
    for document in documents or ():
        if not isinstance(document, Mapping):
            continue
        kind = _upper(document.get("kind"))
        if kind not in PLAN_DOCUMENT_KINDS:
            continue
        document_id = _text(document.get("id"), 40)
        if not document_id:
            continue
        rows.append({
            "kind": kind,
            "label": _LABEL_BY_KIND[kind],
            "title": _text(document.get("public_title") or document.get("title"), 160) or _LABEL_BY_KIND[kind],
            "version": _text(document.get("version"), 20),
        })
    return rows[:50]
