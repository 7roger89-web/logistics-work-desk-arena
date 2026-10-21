"""Shipment-level commercial/import flow and document workflow projection.

LOGI_SHIPMENT_DOCUMENT_WORKFLOW_01

This module is deliberately pure and small.  It does not persist anything and
it does not introduce a workflow engine or a second source of truth.  The
canonical shipment stores only the operator-confirmed import model under
``data["0.0"]["commercial_flow"]``; every workflow card is re-derived from
that stored fact plus the existing quote/GNT/delivery/PXK/finance projections.

UNKNOWN stays UNKNOWN.  A missing legal importer, missing source document or
missing payment classification is never converted to a plausible default.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

FLOW_CUSTOMER_SELF = "CUSTOMER_SELF"
FLOW_TT_ENTRUSTED_DIRECT = "TT_ENTRUSTED_DIRECT"
FLOW_TT_ENTRUSTED_SUB = "TT_ENTRUSTED_SUB"
FLOW_MODES = {
    FLOW_CUSTOMER_SELF,
    FLOW_TT_ENTRUSTED_DIRECT,
    FLOW_TT_ENTRUSTED_SUB,
}

FLOW_LABELS = {
    FLOW_CUSTOMER_SELF: "Khách hàng tự đứng tên nhập khẩu",
    FLOW_TT_ENTRUSTED_DIRECT: "Trường Thành nhận ủy thác và trực tiếp đứng nhập khẩu",
    FLOW_TT_ENTRUSTED_SUB: "Trường Thành ủy thác tiếp qua đối tác",
}

STATE_COMPLETE = "COMPLETE"
STATE_READY = "READY"
STATE_MISSING = "MISSING_INFO"
STATE_PENDING_DOCUMENT = "PENDING_DOCUMENT"
STATE_CONDITIONAL = "CONDITIONAL"
STATE_NOT_APPLICABLE = "NOT_APPLICABLE"
STATE_BLOCKED = "BLOCKED"

STATE_LABELS = {
    STATE_COMPLETE: "Đã hoàn tất",
    STATE_READY: "Sẵn sàng",
    STATE_MISSING: "Thiếu thông tin",
    STATE_PENDING_DOCUMENT: "Cần chứng từ",
    STATE_CONDITIONAL: "Theo phát sinh",
    STATE_NOT_APPLICABLE: "Không áp dụng",
    STATE_BLOCKED: "Đang bị chặn",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = _mapping(shipment.get("data"))
    return _mapping(data.get(key))


def _entity_by_id(
    records: Mapping[str, Any] | None,
    identifier: str,
    *id_keys: str,
) -> Mapping[str, Any] | None:
    identifier = _text(identifier)
    if not identifier:
        return None
    records = records or {}
    direct = records.get(identifier)
    if isinstance(direct, Mapping):
        return direct
    upper = identifier.upper()
    for row in records.values():
        if not isinstance(row, Mapping):
            continue
        for key in id_keys:
            if _text(row.get(key)).upper() == upper:
                return row
    return None


def _entity_tax_code(entity: Mapping[str, Any] | None) -> str:
    """MST of one resolved master row, across the repo's real spellings.

    ``tax_or_legal_code`` (COMPANY authority master) is read FIRST: the
    consumers of this helper — signing company, legal importer, handover
    parties — are COMPANY rows, so their own field is the truth.  An AGENT
    row has no ``tax_or_legal_code`` and falls through to ``legal_code``,
    which stays in the chain as the AGENT-master spelling (customers keep
    ``tax_code``).  Reading ``legal_code`` first let a legal-form value win
    over the real tax code of a company master that carries both.

    Values are stripped ONE BY ONE before choosing, so a blank or
    whitespace-only spelling can no longer mask the real MST behind it.
    An absent MST stays blank; it is never invented.
    """
    row = entity or {}
    for key in ("tax_or_legal_code", "legal_code", "tax_code", "mst"):
        value = _text(row.get(key))
        if value:
            return value
    return ""


def _entity_display_name(entity: Mapping[str, Any] | None, *keys: str) -> str:
    """First non-blank name spelling of a resolved master row.

    Same reason as :func:`_entity_tax_code`: the values are stripped ONE BY
    ONE, so a whitespace-only ``legal_name`` cannot mask the real ``name``
    behind it and empty the party label.
    """
    row = entity or {}
    for key in keys:
        value = _text(row.get(key))
        if value:
            return value
    return ""


def stored_flow(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Return the persisted commercial-flow block without inventing defaults."""
    head = _section(shipment, "0.0")
    raw = _mapping(head.get("commercial_flow"))
    mode = _text(raw.get("mode")).upper()
    if mode not in FLOW_MODES:
        mode = ""
    return {
        "mode": mode,
        "confirmed": bool(raw.get("confirmed")) and bool(mode),
        "company_id": _text(raw.get("company_id")).upper(),
        "sub_agent_id": _text(raw.get("sub_agent_id")).upper(),
        # TT_ENTRUSTED_SUB — legal importer company, resolved from
        # ``authority_companies``.  It is a SEPARATE identity from
        # ``sub_agent_id`` (the contract partner in ``authority_agents``).
        # Historical lots saved before this field existed read back as "" and
        # must stay unresolved instead of reinterpreting the agent id.
        "importer_company_id": _text(raw.get("importer_company_id")).upper(),
    }



def resolve_sub_purchase_contract(
    *,
    shipment: Mapping[str, Any],
    flow: Mapping[str, Any],
    contracts: Mapping[str, Any] | None,
    linked_contracts: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Resolve the ONE candidate contract set, for the projection AND the writer.

    Same no-guess rule as ``pxk_projection``: the shipment's own contract id
    wins; otherwise only the linked contracts are considered.  A contract being
    LINKED never means signed/valid — it stays a precondition, not evidence.
    """
    sid = _text(shipment.get("id")).upper()
    contract_id = _text(shipment.get("contract_id"))
    candidate: dict[str, Any] = {}
    if linked_contracts is not None:
        linked = _mapping(linked_contracts).get(sid) if sid else None
        candidate.update(_mapping(linked))
    if contract_id and isinstance(_mapping(contracts).get(contract_id), Mapping):
        candidate.setdefault(contract_id, _mapping(contracts)[contract_id])
    return match_sub_purchase_contract(flow, candidate)

def validate_flow_write(
    *,
    shipment: Mapping[str, Any],
    mode: str,
    companies: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
    company_id: str = "",
    sub_agent_id: str = "",
    importer_company_id: str = "",
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate ONE explicit operator choice and return the canonical block.

    The legal importer is never guessed.  CUSTOMER_SELF requires a customer
    identity already linked to the lot.  TT_ENTRUSTED_DIRECT requires one
    explicit/uniquely resolvable Trường Thành authority company.
    TT_ENTRUSTED_SUB keeps the authority-agent contract partner in
    ``sub_agent_id`` and requires a DIFFERENT legal importer resolved from the
    ``authority_companies`` master (``importer_company_id``).  An agent id is
    never reinterpreted as a company id.
    """

    mode = _text(mode).upper()
    company_id = _text(company_id).upper()
    sub_agent_id = _text(sub_agent_id).upper()
    importer_company_id = _text(importer_company_id).upper()
    errors: list[str] = []

    if mode not in FLOW_MODES:
        return None, ["Chọn hình thức nhập khẩu trước khi lưu."]

    if mode == FLOW_CUSTOMER_SELF:
        customer_id = _text(shipment.get("customer_id")).upper()
        if not customer_id:
            errors.append("Lô chưa gắn mã khách hàng; chưa xác định được pháp nhân đứng nhập khẩu.")
        if sub_agent_id:
            errors.append("Khách tự đứng tên nhập khẩu thì không được gắn đơn vị nhận ủy thác tiếp.")
        if importer_company_id:
            errors.append("Khách tự đứng tên nhập khẩu thì không có pháp nhân đứng nhập khẩu hộ.")
        if errors:
            return None, errors
        return {
            "mode": mode,
            "confirmed": True,
            "company_id": "",
            "sub_agent_id": "",
        }, []

    if mode == FLOW_TT_ENTRUSTED_DIRECT:
        companies = companies or {}
        if not company_id:
            candidates = [
                row for row in companies.values()
                if isinstance(row, Mapping)
                and _text(row.get("company_id") or row.get("id"))
            ]
            if len(candidates) == 1:
                company_id = _text(candidates[0].get("company_id") or candidates[0].get("id")).upper()
        company = _entity_by_id(companies, company_id, "company_id", "id")
        if company is None:
            errors.append("Chưa chọn đúng pháp nhân Trường Thành sẽ đứng tên nhập khẩu.")
        if sub_agent_id:
            errors.append("Lô Trường Thành trực tiếp nhập khẩu thì không được gắn đơn vị nhận ủy thác tiếp.")
        if importer_company_id:
            errors.append("Lô Trường Thành trực tiếp nhập khẩu thì không có pháp nhân đứng nhập khẩu hộ.")
        if errors:
            return None, errors
        return {
            "mode": mode,
            "confirmed": True,
            "company_id": company_id,
            "sub_agent_id": "",
        }, []

    companies = companies or {}
    if not company_id:
        candidates = [
            row for row in companies.values()
            if isinstance(row, Mapping)
            and _text(row.get("company_id") or row.get("id"))
        ]
        if len(candidates) == 1:
            company_id = _text(candidates[0].get("company_id") or candidates[0].get("id")).upper()

    company = _entity_by_id(companies, company_id, "company_id", "id")
    if company is None:
        errors.append("Chưa chọn pháp nhân Trường Thành ký với đơn vị nhập khẩu hộ.")

    agent = _entity_by_id(agents, sub_agent_id, "agent_id", "id")
    if agent is None:
        errors.append(
            "Chọn đối tác hợp đồng nhận ủy thác (ví dụ Phú Anh) từ danh mục đối tác; "
            "đại lý không phải pháp nhân đứng nhập khẩu."
        )

    # The legal importer is an independent, explicit choice from the COMPANY
    # master.  It is never derived from the agent id, the contract or a name.
    importer_company = _entity_by_id(companies, importer_company_id, "company_id", "id")
    if not importer_company_id:
        errors.append("Chọn pháp nhân thực tế đứng tên nhập khẩu hộ từ danh mục pháp nhân.")
    elif importer_company is None:
        errors.append("Không tìm thấy pháp nhân đứng tên nhập khẩu hộ trong danh mục pháp nhân.")
    elif company_id and importer_company_id == company_id:
        errors.append("Pháp nhân đứng tên nhập khẩu hộ phải khác pháp nhân Trường Thành ký hợp đồng.")
    if errors:
        return None, errors
    return {
        "mode": mode,
        "confirmed": True,
        "company_id": company_id,
        "sub_agent_id": sub_agent_id,
        "importer_company_id": importer_company_id,
    }, []


def project_commercial_flow(
    shipment: Mapping[str, Any],
    *,
    customers: Mapping[str, Any] | None = None,
    companies: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the operator-confirmed flow and its legal importer identity."""

    flow = stored_flow(shipment)
    mode = flow["mode"]
    customer_id = _text(shipment.get("customer_id")).upper()
    importer: Mapping[str, Any] | None = None
    importer_kind = ""
    importer_id = ""
    missing: list[str] = []

    if not flow["confirmed"]:
        missing.append("Chưa xác nhận hình thức nhập khẩu.")
    elif mode == FLOW_CUSTOMER_SELF:
        importer = _entity_by_id(customers, customer_id, "customer_id", "id")
        importer_kind = "CUSTOMER"
        importer_id = customer_id
        if not customer_id:
            missing.append("Lô chưa có mã khách hàng.")
        if importer is None:
            missing.append("Không tìm thấy hồ sơ pháp lý khách hàng đang đứng nhập khẩu.")
    elif mode == FLOW_TT_ENTRUSTED_DIRECT:
        importer_id = flow["company_id"]
        importer_kind = "COMPANY"
        importer = _entity_by_id(companies, importer_id, "company_id", "id")
        if importer is None:
            missing.append("Không tìm thấy pháp nhân Trường Thành đã chọn.")
    elif mode == FLOW_TT_ENTRUSTED_SUB:
        # The legal importer comes ONLY from the selected authority company.
        # ``sub_agent_id`` stays the contract partner and is never promoted to
        # a legal identity.  A missing/invalid/stale company stays UNKNOWN.
        candidate_id = flow["importer_company_id"]
        if not candidate_id:
            missing.append("Chưa chọn pháp nhân thực tế đứng tên nhập khẩu hộ từ danh mục pháp nhân.")
        elif candidate_id == flow["company_id"]:
            missing.append(
                "Pháp nhân đứng tên nhập khẩu hộ phải khác pháp nhân Trường Thành ký hợp đồng."
            )
        else:
            importer = _entity_by_id(companies, candidate_id, "company_id", "id")
            if importer is None:
                missing.append("Không tìm thấy pháp nhân đứng tên nhập khẩu hộ trong danh mục pháp nhân.")
            else:
                importer_kind = "COMPANY"
                importer_id = candidate_id

    importer = importer or {}
    importer_name = _entity_display_name(
        importer, "legal_name", "name", "company_name"
    )
    # Repo truth: each master spells MST differently — the COMPANY authority
    # master stores it as ``tax_or_legal_code`` (views/contracts.py,
    # views/docgen.py, views/logi_c1.py, core/docgen/rules.py, staging seed),
    # the AGENT master as ``legal_code``, customers as ``tax_code``.  Read the
    # real field of the resolved importer instead of assuming one shared key,
    # or TT_ENTRUSTED_DIRECT would never resolve an MST from live master data.
    importer_tax_code = _entity_tax_code(importer)
    if flow["confirmed"] and not importer_name:
        missing.append("Thiếu tên pháp lý của đơn vị đứng nhập khẩu.")
    if flow["confirmed"] and not importer_tax_code:
        missing.append("Thiếu mã số thuế của đơn vị đứng nhập khẩu.")

    sub_agent = _entity_by_id(agents, flow["sub_agent_id"], "agent_id", "id")
    sub_agent_name = _entity_display_name(sub_agent, "legal_name", "name")
    # Same MST resolution as the legal importer above: group companies can
    # share ONE legal name, so the handover party choices (entrustment_parties)
    # need each party's own MST to stay distinguishable.  Absent stays blank.
    sub_agent_tax_code = _entity_tax_code(sub_agent)
    # The signing company is a distinct party of the same chain; its name is
    # needed to label an EXPLICIT handover party choice (never to infer it).
    signing_company = _entity_by_id(companies, flow["company_id"], "company_id", "id")
    signing_company_name = _entity_display_name(
        signing_company, "legal_name", "name", "company_name"
    )
    signing_company_tax_code = _entity_tax_code(signing_company)

    return {
        "mode": mode,
        "modeLabel": FLOW_LABELS.get(mode, "Chưa xác nhận hình thức nhập khẩu"),
        "confirmed": bool(flow["confirmed"]),
        "companyId": flow["company_id"],
        "companyName": signing_company_name,
        "companyTaxCode": signing_company_tax_code,
        "subAgentId": flow["sub_agent_id"],
        "subAgentName": sub_agent_name,
        "subAgentTaxCode": sub_agent_tax_code,
        "importerCompanyId": importer_id if mode == FLOW_TT_ENTRUSTED_SUB else "",
        "legalImporterKind": importer_kind,
        "legalImporterId": importer_id,
        "legalImporterName": importer_name,
        "legalImporterTaxCode": importer_tax_code,
        "missing": missing,
        "ready": bool(flow["confirmed"]) and not missing,
    }


def _step(
    identifier: str,
    label: str,
    state: str,
    reason: str,
    *,
    target_tab: str = "",
    target_route: str = "",
    action_label: str = "",
) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label,
        "state": state,
        "stateLabel": STATE_LABELS[state],
        "reason": reason,
        "targetTab": target_tab,
        "targetRoute": target_route,
        "actionLabel": action_label,
    }


def pxk_flow_gate(flow: Mapping[str, Any]) -> dict[str, Any]:
    """Return the commercial-flow gate that applies before PXK docgen.

    This is shared by the read-side workflow and the server write handler so
    UI applicability and backend authorization cannot drift apart.
    """
    mode = _text(flow.get("mode")).upper()
    confirmed = bool(flow.get("confirmed")) and mode in FLOW_MODES
    if not confirmed:
        return {
            "allowed": False,
            "gate": "COMMERCIAL_FLOW_REQUIRED",
            "reason": "Xác nhận hình thức nhập khẩu trước khi tạo Phiếu xuất kho.",
        }
    if mode == FLOW_CUSTOMER_SELF:
        return {
            "allowed": False,
            "gate": "PXK_NOT_APPLICABLE",
            "reason": "Khách hàng tự đứng tên nhập khẩu; Phiếu xuất kho của Trường Thành không áp dụng cho luồng này.",
        }
    return {"allowed": True, "gate": "READY", "reason": ""}


def gnt_flow_gate(flow: Mapping[str, Any], taxpayer_tax_code: Any) -> dict[str, Any]:
    """Protect GNT generation with the confirmed legal-importer identity.

    The tax code is the stable comparison key.  Names can contain punctuation
    and abbreviations, so they remain display evidence and are never used as a
    fuzzy legal-identity matcher.
    """
    mode = _text(flow.get("mode")).upper()
    confirmed = bool(flow.get("confirmed")) and mode in FLOW_MODES
    if not confirmed:
        return {
            "allowed": False,
            "gate": "COMMERCIAL_FLOW_REQUIRED",
            "reason": "Xác nhận hình thức nhập khẩu trước khi tạo Giấy nộp thuế.",
        }

    importer_tax_code = _text(flow.get("legalImporterTaxCode"))
    if not importer_tax_code:
        return {
            "allowed": False,
            "gate": "LEGAL_IMPORTER_TAX_CODE_REQUIRED",
            "reason": "Pháp nhân đứng nhập khẩu chưa có mã số thuế trong hồ sơ master.",
        }

    actual_tax_code = _text(taxpayer_tax_code)
    if actual_tax_code and actual_tax_code != importer_tax_code:
        return {
            "allowed": False,
            "gate": "GNT_TAXPAYER_MISMATCH",
            "reason": (
                "MST người nộp thuế trên GNT không khớp pháp nhân đứng nhập khẩu "
                f"đã xác nhận ({actual_tax_code} ≠ {importer_tax_code})."
            ),
        }
    return {"allowed": True, "gate": "READY", "reason": ""}


def match_sub_purchase_contract(
    flow: Mapping[str, Any],
    contracts: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Match the linked TT↔sub-agent purchase contract without guessing.

    Exactly one contract whose company_id + agent_id match the confirmed flow
    is usable.  Zero stays missing; multiple matches stay ambiguous.
    """
    mode = _text(flow.get("mode")).upper()
    if mode != FLOW_TT_ENTRUSTED_SUB or not bool(flow.get("confirmed")):
        return {"status": "NOT_APPLICABLE", "id": "", "contractNo": "", "matches": []}

    company_id = _text(flow.get("companyId") or flow.get("company_id")).upper()
    agent_id = _text(flow.get("subAgentId") or flow.get("sub_agent_id")).upper()
    matches: list[dict[str, str]] = []
    for row in (contracts or {}).values():
        if not isinstance(row, Mapping):
            continue
        if _text(row.get("company_id")).upper() != company_id:
            continue
        if _text(row.get("agent_id")).upper() != agent_id:
            continue
        identifier = _text(row.get("id") or row.get("contract_no")).upper()
        if not identifier:
            continue
        matches.append({
            "id": identifier,
            "contractNo": _text(row.get("contract_no")) or identifier,
        })

    if len(matches) == 1:
        return {"status": "LINKED", **matches[0], "matches": matches}
    if len(matches) > 1:
        return {"status": "AMBIGUOUS", "id": "", "contractNo": "", "matches": matches}
    return {"status": "MISSING", "id": "", "contractNo": "", "matches": []}


def build_document_workflow(
    *,
    flow: Mapping[str, Any],
    quote_linked: bool,
    gnt: Mapping[str, Any] | None,
    delivered: bool,
    pxk: Mapping[str, Any] | None,
    finance: Mapping[str, Any] | None,
    sub_purchase_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the shipment's conditional document/work lifecycle.

    This is an operator worklist, not an accounting state machine.  Existing
    capabilities (quote, GNT, delivery, PXK, finance) are surfaced directly.
    Document types not yet generated by the repository stay explicitly marked
    PENDING_DOCUMENT / CONDITIONAL instead of being fabricated as complete.
    """

    mode = _text(flow.get("mode")).upper()
    confirmed = bool(flow.get("confirmed")) and mode in FLOW_MODES
    gnt = _mapping(gnt)
    pxk = _mapping(pxk)
    finance = _mapping(finance)

    steps: list[dict[str, Any]] = []
    steps.append(_step(
        "quotation",
        "Báo giá",
        STATE_COMPLETE if quote_linked else STATE_PENDING_DOCUMENT,
        "Lô đã gắn báo giá." if quote_linked else "Lô chưa gắn báo giá.",
        target_route="/kinh-doanh-bao-gia",
        action_label="Mở báo giá",
    ))

    if not confirmed:
        gate_reason = "Xác nhận hình thức nhập khẩu trước để hệ thống chọn đúng bộ chứng từ."
        steps.extend([
            _step("customer_contract", "Hợp đồng với khách hàng", STATE_BLOCKED, gate_reason),
            _step("sub_entrust_contract", "Hợp đồng Trường Thành ↔ đơn vị nhập khẩu hộ", STATE_BLOCKED, gate_reason),
            _step("customer_advance_request", "Đề nghị khách hàng tạm ứng", STATE_BLOCKED, gate_reason),
            _step("tax_payment", "Giấy nộp thuế", STATE_BLOCKED, gate_reason, target_tab="nhap"),
            _step("vn_agent_payment_request", "Đề nghị thanh toán đại lý Việt Nam", STATE_BLOCKED, gate_reason, target_tab="tai-chinh"),
            _step("foreign_agent_payment_request", "Đề nghị thanh toán đại lý nước ngoài", STATE_BLOCKED, gate_reason, target_tab="tai-chinh"),
            _step("delivery_note", "Phiếu giao hàng", STATE_BLOCKED, gate_reason, target_tab="nhap"),
            _step("warehouse_issue", "Phiếu xuất kho", STATE_BLOCKED, gate_reason, target_tab="chung-tu"),
            _step("customer_final_request", "Đề nghị khách hàng thanh toán còn lại", STATE_BLOCKED, gate_reason, target_tab="tai-chinh"),
        ])
        return _workflow_result(steps)

    customer_contract_label = (
        "Hợp đồng vận chuyển với khách hàng"
        if mode == FLOW_CUSTOMER_SELF
        else "Hợp đồng ủy thác nhập khẩu với khách hàng"
    )
    steps.append(_step(
        "customer_contract",
        customer_contract_label,
        STATE_PENDING_DOCUMENT,
        (
            "Đã xác định đúng loại hợp đồng theo mô hình lô. Repo hiện chưa có template/generator "
            "riêng cho hợp đồng với khách hàng; không dùng nhầm docgen Công ty ↔ Đại lý (HDNT/PL/HDMB)."
        ),
    ))

    if mode == FLOW_TT_ENTRUSTED_SUB:
        purchase = _mapping(sub_purchase_contract)
        purchase_status = _text(purchase.get("status")).upper()
        if purchase_status == "LINKED":
            purchase_state = STATE_READY
            purchase_reason = (
                f"Đã liên kết {purchase.get('contractNo') or purchase.get('id')} đúng Trường Thành ↔ "
                "đơn vị nhập khẩu hộ. Mở workdesk hợp đồng để kiểm tra/sinh chứng từ bằng docgen hiện hữu."
            )
        elif purchase_status == "AMBIGUOUS":
            purchase_state = STATE_BLOCKED
            purchase_reason = (
                f"Có {len(purchase.get('matches') or [])} hợp đồng cùng khớp hai bên; cần chọn/liên kết đúng một hợp đồng, hệ thống không tự đoán."
            )
        else:
            purchase_state = STATE_PENDING_DOCUMENT
            purchase_reason = (
                "Chưa có hợp đồng liên kết khớp đúng Trường Thành ↔ đơn vị nhập khẩu hộ. "
                "Repo đã có docgen Agent bán hàng → Trường Thành (HDNT/PL/HDMB); phải dùng đúng bộ rule hiện hữu."
            )
        steps.append(_step(
            "sub_entrust_contract",
            "Hồ sơ mua bán Trường Thành ↔ đơn vị đứng nhập khẩu hộ",
            purchase_state,
            purchase_reason,
            target_route=(
                f"/hop-dong/{purchase.get('id')}"
                if purchase_status == "LINKED" and purchase.get("id")
                else "/hop-dong"
            ),
            action_label="Mở hợp đồng mua vào",
        ))
    else:
        steps.append(_step(
            "sub_entrust_contract",
            "Hợp đồng Trường Thành ↔ đơn vị đứng nhập khẩu hộ",
            STATE_NOT_APPLICABLE,
            "Lô này không ủy thác tiếp cho một pháp nhân khác.",
        ))

    steps.append(_step(
        "customer_advance_request",
        "Đề nghị khách hàng tạm ứng",
        STATE_CONDITIONAL,
        "Tỷ lệ 50%–80% phải lấy từ điều khoản hợp đồng đã xác nhận; chưa được hard-code.",
        target_tab="tai-chinh",
    ))

    gnt_gate = gnt_flow_gate(flow, gnt.get("taxCode"))
    # Tax payment truth is SEPARATE from GNT generation.
    # GNT generation (done/document) means a paper exists, not that customs received money.
    # COMPLETE requires explicit taxPaid evidence (gnt.taxPaid / taxPaidAt).
    tax_paid = bool(gnt.get("taxPaid") or gnt.get("taxPaidAt") or gnt.get("paidAt"))
    has_gnt_doc = bool(gnt.get("done") or _mapping(gnt.get("document")))
    if not gnt_gate["allowed"]:
        gnt_state, gnt_reason = STATE_MISSING, gnt_gate["reason"]
    elif tax_paid:
        gnt_state, gnt_reason = STATE_COMPLETE, "Đã nộp thuế nhập khẩu (có bằng chứng thanh toán)."
    elif has_gnt_doc:
        # GNT exists but no payment evidence — remain READY, not COMPLETE
        gnt_state, gnt_reason = STATE_READY, "Đã tạo Giấy nộp thuế (GNT), chờ chứng từ nộp thuế — chưa có bằng chứng đã nộp."
    elif gnt.get("noPayable"):
        gnt_state, gnt_reason = STATE_NOT_APPLICABLE, "Thuế nhập khẩu và VAT nhập khẩu đều đã biết bằng 0."
    elif gnt.get("ready"):
        gnt_state, gnt_reason = STATE_READY, "Đủ dữ liệu để tạo Giấy nộp thuế."
    else:
        missing = [str(x) for x in (gnt.get("missing") or []) if str(x).strip()]
        gnt_state = STATE_MISSING
        gnt_reason = "Thiếu: " + ", ".join(missing) if missing else "Chưa đủ dữ liệu thuế/tờ khai."
    steps.append(_step(
        "tax_payment", "Giấy nộp thuế", gnt_state, gnt_reason,
        target_tab="nhap", action_label="Mở phần nhập khẩu",
    ))

    partner = _mapping(finance.get("partner"))
    partner_remaining = partner.get("remaining")
    if partner_remaining is not None and float(partner_remaining or 0) > 0:
        partner_reason = "Đã có khoản phải trả đối tác; cần phân loại đại lý VN/nước ngoài trước khi phát hành đề nghị."
    else:
        partner_reason = "Chỉ phát sinh khi lô có nghĩa vụ phải trả đúng đối tác; chưa tự suy diễn quốc gia của đại lý."
    for identifier, label in (
        ("vn_agent_payment_request", "Đề nghị thanh toán đại lý Việt Nam"),
        ("foreign_agent_payment_request", "Đề nghị thanh toán đại lý nước ngoài"),
    ):
        steps.append(_step(
            identifier, label, STATE_CONDITIONAL, partner_reason,
            target_tab="tai-chinh", action_label="Mở tài chính",
        ))

    steps.append(_step(
        "delivery_note",
        "Phiếu giao hàng",
        STATE_PENDING_DOCUMENT if delivered else STATE_BLOCKED,
        "Đã giao hàng; cần phát hành phiếu giao hàng." if delivered
        else "Chưa xác nhận giao hàng thực tế.",
        target_tab="nhap",
        action_label="Mở giao hàng",
    ))

    pxk_flow = pxk_flow_gate(flow)
    has_pxk = bool(_mapping(pxk.get("document")) or pxk.get("done"))
    if pxk_flow["gate"] == "PXK_NOT_APPLICABLE" and has_pxk:
        pxk_state, pxk_reason = (
            STATE_BLOCKED,
            "Lô đã có Phiếu xuất kho từ mô hình trước. Giữ nguyên chứng từ lịch sử để kiểm toán; mô hình hiện tại không cho phát hành PXK mới.",
        )
    elif pxk_flow["gate"] == "PXK_NOT_APPLICABLE":
        pxk_state, pxk_reason = STATE_NOT_APPLICABLE, pxk_flow["reason"]
    elif not pxk_flow["allowed"]:
        pxk_state, pxk_reason = STATE_BLOCKED, pxk_flow["reason"]
    elif has_pxk:
        pxk_state, pxk_reason = STATE_COMPLETE, "Phiếu xuất kho của lô đã được tạo."
    elif not delivered:
        pxk_state, pxk_reason = STATE_BLOCKED, "Chỉ xét Phiếu xuất kho sau khi đã giao hàng."
    elif pxk.get("gateOpen"):
        pxk_state, pxk_reason = STATE_READY, "Đã giao và đủ điều kiện docgen để tạo Phiếu xuất kho."
    else:
        missing = [str(x) for x in (pxk.get("missingDeliveryFacts") or []) if str(x).strip()]
        pxk_state = STATE_MISSING
        pxk_reason = "Thiếu: " + ", ".join(missing) if missing else "Chưa đủ điều kiện tạo Phiếu xuất kho."
    steps.append(_step(
        "warehouse_issue", "Phiếu xuất kho", pxk_state, pxk_reason,
        target_tab="chung-tu", action_label="Mở Phiếu xuất kho",
    ))

    outstanding = finance.get("outstanding")
    if outstanding is not None and float(outstanding or 0) > 0:
        final_reason = "Lô còn phải thu khách hàng; số đề nghị phải lấy từ công nợ thực tế và điều khoản hợp đồng."
    elif outstanding is not None and float(outstanding or 0) == 0:
        final_reason = "Công nợ hiện tại đã về 0; không tự sinh thêm đề nghị thanh toán."
    else:
        final_reason = "Chưa có Finance Actual đủ để xác định số còn phải thu."
    steps.append(_step(
        "customer_final_request",
        "Đề nghị khách hàng thanh toán còn lại",
        STATE_CONDITIONAL,
        final_reason,
        target_tab="tai-chinh",
        action_label="Mở tài chính",
    ))

    return _workflow_result(steps)


def _workflow_result(steps: list[dict[str, Any]]) -> dict[str, Any]:
    applicable = [s for s in steps if s["state"] != STATE_NOT_APPLICABLE]
    complete = [s for s in applicable if s["state"] == STATE_COMPLETE]
    ready = [s for s in applicable if s["state"] == STATE_READY]
    attention = [
        s for s in applicable
        if s["state"] in {STATE_MISSING, STATE_PENDING_DOCUMENT, STATE_BLOCKED}
    ]
    return {
        "steps": steps,
        "summary": {
            "complete": len(complete),
            "total": len(applicable),
            "ready": len(ready),
            "attention": len(attention),
            "notApplicable": len(steps) - len(applicable),
        },
    }


# ---------------------------------------------------------------------------
# TT_ENTRUSTED_SUB — two approved operational stages
# ---------------------------------------------------------------------------
#
# The Owner approved exactly two extra stages for the sub-entrustment flow:
#   * ``entrustment-ready``      — the lot is ready to be performed under the
#                                  sub-entrustment, with a recorded basis;
#   * ``tt-warehouse-handover``  — goods were actually handed over at the
#                                  warehouse by the recorded giver to the
#                                  recorded receiver.
#
# Selecting the legal importer, having a LINKED contract, uploading a file,
# declaring/clearing customs, having a D/O, creating a PXK, choosing a partner
# or completing DELIVERY of another leg are NOT evidence for either stage.
#
# Both facts live in ONE small block inside the EXISTING shipment document:
# ``data["0.0"]["entrustment_evidence"]``.  No collection, no workflow engine.

ENTRUSTMENT_EVIDENCE_BLOCK = "entrustment_evidence"
ENTRUSTMENT_READY_NODE = "entrustment-ready"
ENTRUSTMENT_HANDOVER_NODE = "tt-warehouse-handover"
ENTRUSTMENT_NODE_IDS = (ENTRUSTMENT_READY_NODE, ENTRUSTMENT_HANDOVER_NODE)

#: UI/writer field name -> stored key inside the evidence block.
ENTRUSTMENT_FIELDS: dict[str, str] = {
    "entrustment_ready_at": "ready_at",
    "entrustment_ready_ref": "ready_ref",
    "warehouse_handover_at": "handover_at",
    "warehouse_handover_from": "handover_from",
    "warehouse_handover_from_label": "handover_from_label",
    "warehouse_handover_to": "handover_to",
    "warehouse_handover_to_label": "handover_to_label",
    "warehouse_handover_doc_no": "handover_doc_no",
}
_ENTRUSTMENT_READY_FIELDS = ("ready_at", "ready_ref")
_ENTRUSTMENT_TIME_FIELDS = ("ready_at", "handover_at")
_ENTRUSTMENT_HANDOVER_FIELDS = ("handover_at", "handover_from", "handover_to", "handover_doc_no")
#: Optional stage-local display names for the two handover sides.  They live
#: ONLY in this evidence block — master data (authority_companies/agents) is
#: never rewritten — and blank means "show the master party label".  They are
#: deliberately NOT members of ``_ENTRUSTMENT_HANDOVER_FIELDS``: a display
#: correction is not handover evidence, must never be REQUIRED for a
#: handover, and recording one alone must not read as a started handover.
_ENTRUSTMENT_HANDOVER_LABEL_FIELDS = ("handover_from_label", "handover_to_label")
_ENTRUSTMENT_MAX_TEXT = {
    "ready_ref": 200,
    "handover_doc_no": 120,
    "handover_from_label": 200,
    "handover_to_label": 200,
}


def stored_entrustment_evidence(shipment: Mapping[str, Any]) -> dict[str, str]:
    """Read the bounded evidence block without inventing defaults."""
    raw = _mapping(_section(shipment, "0.0").get(ENTRUSTMENT_EVIDENCE_BLOCK))
    return {
        "ready_at": _text(raw.get("ready_at")),
        "ready_ref": _text(raw.get("ready_ref")),
        "handover_at": _text(raw.get("handover_at")),
        "handover_from": _text(raw.get("handover_from")).upper(),
        "handover_from_label": _text(raw.get("handover_from_label")),
        "handover_to": _text(raw.get("handover_to")).upper(),
        "handover_to_label": _text(raw.get("handover_to_label")),
        "handover_doc_no": _text(raw.get("handover_doc_no")),
    }


def entrustment_parties(flow: Mapping[str, Any]) -> list[dict[str, str]]:
    """The three legal parties of a SUB chain, as explicit choices only.

    Order: signing company, contract partner, legal importer.  Duplicate ids
    collapse; an absent id is never replaced by a guess.

    Labels carry the party's MST (when its master row resolved one) and its
    role in the chain: group companies can share ONE legal name, so a bare
    name does not identify a handover party.  A missing MST is omitted from
    the label, never invented.
    """
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for id_key, name_key, tax_key, role_label in (
        ("companyId", "companyName", "companyTaxCode", "bên ký ủy thác"),
        ("subAgentId", "subAgentName", "subAgentTaxCode", "đối tác hợp đồng"),
        ("importerCompanyId", "legalImporterName", "legalImporterTaxCode", "đứng tên nhập khẩu"),
    ):
        identifier = _text(flow.get(id_key)).upper()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        label = _text(flow.get(name_key)) or identifier
        tax_code = _text(flow.get(tax_key))
        if tax_code:
            label += f" · MST {tax_code}"
        label += f" · {role_label}"
        rows.append({"id": identifier, "label": label})
    return rows


#: Accepted evidence-time shapes. A value is parsed AS A WHOLE — never sliced —
#: so ``2026-10-10NOT-A-TIME`` is refused instead of silently passing as a date.
#: Timezone designators are deliberately NOT accepted: the two facts are local
#: warehouse moments and converting zones would invent information.
_EVIDENCE_TIME_FORMATS: tuple[tuple[str, bool], ...] = (
    ("%Y-%m-%dT%H:%M", True),
    ("%Y-%m-%d %H:%M", True),
    ("%d/%m/%Y %H:%M", True),
    ("%Y-%m-%dT%H:%M:%S", True),
    ("%Y-%m-%d %H:%M:%S", True),
    ("%d/%m/%Y %H:%M:%S", True),
    ("%Y-%m-%d", False),
    ("%d/%m/%Y", False),
)


def _parse_evidence_time(value: Any) -> tuple[bool, datetime] | None:
    """Parse ONE evidence timestamp; ``(has_time, moment)`` or None.

    ``has_time`` is the PRECISION of the input: a legacy pure date carries no
    invented hour, and a date+time keeps its hours and minutes.
    """
    raw = _text(value)
    if not raw:
        return None
    for fmt, has_time in _EVIDENCE_TIME_FORMATS:
        try:
            return has_time, datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _normalize_evidence_time(value: Any) -> str:
    """Canonicalise an evidence timestamp without dropping or inventing time."""
    raw = _text(value)
    if not raw:
        return ""
    parsed = _parse_evidence_time(raw)
    if parsed is None:
        raise ValueError(
            "Mốc thời gian phải là YYYY-MM-DD, YYYY-MM-DDTHH:mm, "
            "DD/MM/YYYY hoặc DD/MM/YYYY HH:mm (không nhận múi giờ)."
        )
    has_time, moment = parsed
    return moment.isoformat(sep="T", timespec="minutes" if moment.second == 0 else "seconds") if has_time else moment.date().isoformat()


def _evidence_time_order(later_raw: Any, earlier_raw: Any) -> str:
    """Judge whether ``later`` may follow ``earlier``; return a problem code.

    Codes: ``"day"``/``"time"`` = proved inversion at that precision;
    ``"unproven"`` = same calendar day but one side has no hour, so the order
    cannot be established; ``""`` = no problem proved.

    The DAY is always derivable from a valid date, so it is compared FIRST and
    regardless of whether either side carries a time — dropping that check was
    a false-DONE hole (a handover dated before the ready date but carrying an
    hour used to pass as "incomparable"). Hours are only compared when BOTH
    sides recorded one; an hour is never invented, and mixed precision on the
    same day stays explicitly unproven instead of being assumed either way.
    """
    later = _parse_evidence_time(later_raw)
    earlier = _parse_evidence_time(earlier_raw)
    if later is None or earlier is None:
        return ""
    later_has_time, later_moment = later
    earlier_has_time, earlier_moment = earlier
    # 1+2: the calendar day is determinate for every valid input.
    if later_moment.date() < earlier_moment.date():
        return "day"
    if later_moment.date() > earlier_moment.date():
        return ""
    # 3+5: same day. Both date+time -> exact order; both pure dates -> the
    # legacy day-based contract holds (equal day is not an inversion).
    if later_has_time and earlier_has_time:
        return "time" if later_moment < earlier_moment else ""
    if not later_has_time and not earlier_has_time:
        return ""
    # 4: same day, exactly one side has an hour. Order NOT proven.
    return "unproven"


_EVIDENCE_TIME_ORDER_REASON = {
    "day": "Thời điểm bàn giao không thể trước ngày xác nhận ủy thác sẵn sàng.",
    "time": "Thời điểm bàn giao không thể trước giờ xác nhận ủy thác sẵn sàng.",
    "unproven": (
        "Cùng ngày nhưng thiếu giờ ở một mốc nên chưa chứng minh được bàn giao diễn ra "
        "sau khi ủy thác sẵn sàng; ghi đủ giờ cho cả hai mốc."
    ),
}


def _party_label(rows: list[dict[str, str]], identifier: str) -> str:
    for row in rows:
        if row["id"] == identifier:
            return row["label"]
    return identifier


def project_entrustment_stages(
    flow: Mapping[str, Any],
    contract: Mapping[str, Any] | None,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the TWO SUB-only stage truths from recorded evidence.

    ``done`` is NEVER derived from the flow alone, the contract status alone,
    an attachment, customs, PXK or another leg's DELIVERY.  It requires the
    explicit evidence fact, and the handover requires BOTH actual parties.
    """
    mode = _text(flow.get("mode")).upper()
    if mode != FLOW_TT_ENTRUSTED_SUB:
        return {"applicable": False, "parties": [], "ready": {}, "handover": {}}

    parties = entrustment_parties(flow)
    party_ids = {row["id"] for row in parties}
    contract = _mapping(contract)
    contract_status = _text(contract.get("status")).upper()
    contract_no = _text(contract.get("contractNo")) or _text(contract.get("id"))
    evidence = _mapping(evidence)
    ready_at = _text(evidence.get("ready_at"))
    ready_ref = _text(evidence.get("ready_ref"))
    handover_at = _text(evidence.get("handover_at"))
    handover_from = _text(evidence.get("handover_from")).upper()
    handover_to = _text(evidence.get("handover_to")).upper()
    # Stage-local display names (Owner correction at the handover stage);
    # blank falls back to the master party label below.  They never take
    # part in any done/missing derivation.
    handover_from_label = _text(evidence.get("handover_from_label"))
    handover_to_label = _text(evidence.get("handover_to_label"))
    handover_doc_no = _text(evidence.get("handover_doc_no"))

    ready_missing: list[str] = []
    if not bool(flow.get("confirmed")):
        ready_missing.append("Chưa xác nhận hình thức nhập khẩu.")
    elif not bool(flow.get("ready")):
        detail = "; ".join(str(item) for item in (flow.get("missing") or []) if str(item).strip())
        ready_missing.append(
            "Thiếu hồ sơ pháp nhân đứng nhập khẩu" + (f": {detail}" if detail else ".")
        )
    if contract_status == "AMBIGUOUS":
        count = len(contract.get("matches") or [])
        ready_missing.append(
            f"Có {count} hợp đồng cùng khớp hai bên; phải chọn đúng một hợp đồng, không tự đoán."
        )
    elif contract_status != "LINKED":
        ready_missing.append(
            "Chưa có hợp đồng liên kết khớp đúng Trường Thành ↔ đơn vị đứng nhập khẩu hộ."
        )
    if not ready_at:
        ready_missing.append("Chưa ghi nhận ngày xác nhận đủ điều kiện thực hiện ủy thác.")
    elif _parse_evidence_time(ready_at) is None:
        # A value the current writer would refuse is NOT evidence — legacy rows
        # may hold raw text because the normalizer used to be bypassed.
        ready_missing.append("Ngày xác nhận đã lưu không đúng định dạng; ghi lại mốc hợp lệ.")
    if not ready_ref:
        ready_missing.append("Chưa ghi nhận căn cứ xác nhận (hợp đồng / biên bản phạm vi ủy thác).")

    handover_missing: list[str] = []
    if not handover_at:
        handover_missing.append("Chưa ghi nhận thời điểm bàn giao thực tế tại kho.")
    elif _parse_evidence_time(handover_at) is None:
        handover_missing.append("Thời điểm bàn giao đã lưu không đúng định dạng; ghi lại mốc hợp lệ.")
    if not handover_from:
        handover_missing.append("Chưa xác định bên giao của lần bàn giao.")
    if not handover_to:
        handover_missing.append("Chưa xác định bên nhận của lần bàn giao.")
    if handover_from and handover_to and handover_from == handover_to:
        handover_missing.append("Bên giao và bên nhận phải khác nhau.")
    if any(pid and pid not in party_ids for pid in (handover_from, handover_to)):
        handover_missing.append("Bên giao/bên nhận không thuộc chuỗi ủy thác của lô.")
    if not handover_doc_no:
        handover_missing.append("Chưa có số biên bản giao nhận.")
    order_problem = _evidence_time_order(handover_at, ready_at)
    if order_problem:
        handover_missing.append(_EVIDENCE_TIME_ORDER_REASON[order_problem])

    ready_done = not ready_missing
    # P0-A: the handover is the SECOND stage. Recorded handover evidence never
    # outruns its prerequisite — if the entrustment is not ready (missing ready
    # facts, lost legal importer, contract no longer exactly LINKED), a stored
    # handover stays NOT done and the node states why. Historical evidence is
    # preserved untouched; only the completion claim fails closed.
    if not ready_done:
        handover_missing.append(
            "Chưa hoàn thành công đoạn ủy thác sẵn sàng; bàn giao chỉ được xác nhận sau khi công đoạn trước đủ điều kiện."
        )
    handover_done = not handover_missing
    ready_evidence = " · ".join(
        item
        for item in (
            f"Pháp nhân nhập khẩu: {_text(flow.get('legalImporterName'))}" if flow.get("legalImporterName") else "",
            f"Hợp đồng: {contract_no}" if contract_status == "LINKED" and contract_no else "",
            f"Xác nhận: {ready_at}" if ready_at else "",
            f"Căn cứ: {ready_ref}" if ready_ref else "",
        )
        if item
    )
    handover_evidence = " · ".join(
        item
        for item in (
            f"Bàn giao: {handover_at}" if handover_at else "",
            f"{handover_from_label or _party_label(parties, handover_from)} → {handover_to_label or _party_label(parties, handover_to)}"
            if handover_from and handover_to and handover_from != handover_to
            else "",
            f"Biên bản: {handover_doc_no}" if handover_doc_no else "",
        )
        if item
    )
    return {
        "applicable": True,
        "parties": parties,
        "contractNo": contract_no if contract_status == "LINKED" else "",
        # UI field name -> stored value, so the panel never invents its own read.
        "values": {key: _text(evidence.get(stored)) for key, stored in ENTRUSTMENT_FIELDS.items()},
        "ready": {
            "done": ready_done,
            "evidence": ready_evidence,
            "missing": ready_missing,
        },
        "handover": {
            "done": handover_done,
            "evidence": handover_evidence,
            "missing": handover_missing,
        },
    }


def validate_entrustment_evidence_write(
    *,
    shipment: Mapping[str, Any],
    flow: Mapping[str, Any],
    contract: Mapping[str, Any] | None,
    fields: Mapping[str, Any],
) -> tuple[dict[str, str] | None, list[str]]:
    """Validate ONE explicit evidence write for the two SUB stages.

    Fail-closed rules:
    * only the SUB flow, already confirmed with a resolved legal importer;
    * the contract must be exactly LINKED before readiness can be recorded;
    * a recorded value is never silently blanked by a later write;
    * a handover needs the time, TWO DIFFERENT parties of this chain, and the
      handover document number — a partial record is refused.
    """
    mode = _text(flow.get("mode")).upper()
    if mode != FLOW_TT_ENTRUSTED_SUB:
        return None, ["Hai công đoạn này chỉ áp dụng cho luồng ủy thác tiếp."]
    if not bool(flow.get("confirmed")) or not bool(flow.get("ready")):
        return None, [
            "Phải xác nhận đúng hình thức nhập khẩu và đủ hồ sơ pháp nhân đứng nhập khẩu trước khi ghi bằng chứng."
        ]
    if not fields:
        return None, ["Chưa có trường bằng chứng nào để lưu."]
    unknown = [str(key) for key in fields if str(key) not in ENTRUSTMENT_FIELDS]
    if unknown:
        return None, [f"Trường không thuộc bằng chứng ủy thác/bàn giao: {', '.join(sorted(unknown))}."]

    existing = stored_entrustment_evidence(shipment)
    merged = dict(existing)
    written_keys = {ENTRUSTMENT_FIELDS[str(key)] for key in fields}
    for key, value in fields.items():
        stored_key = ENTRUSTMENT_FIELDS[str(key)]
        # Time fields MUST be parsed whole. They used to be caught by the
        # ready-text branch below, so a garbage or hour-bearing timestamp was
        # stored verbatim and the normalizer never ran.
        if stored_key in _ENTRUSTMENT_TIME_FIELDS:
            normalized = _normalize_evidence_time(value)
        elif stored_key in {"handover_from", "handover_to"}:
            normalized = _text(value).upper()
        else:
            normalized = _text(value)
        if existing.get(stored_key) and not normalized:
            return None, [f"Không được xóa bằng chứng đã ghi ({stored_key})."]
        merged[stored_key] = normalized

    # F-1 — the display name BELONGS TO ONE SIDE.  A display name is written
    # for the party chosen on that side; when this same write changes the side
    # (``handover_from``/``handover_to`` differs from what is stored) and does
    # NOT carry the matching display name, the old name no longer belongs to
    # anybody and is dropped, so the evidence line falls back to the master
    # label of the NEW party instead of showing the previous party's name.
    # Sending the new name in the same write keeps it; an unchanged side keeps
    # its recorded name untouched.
    #
    # This is a WRITER-SIDE drop of a stale pointer, NOT a hole in the
    # "never blank recorded evidence" rule above: that rule still refuses a
    # blank write for an UNCHANGED side (the caller would be erasing a fact),
    # while here the stored name is provably about a party that is no longer on
    # that side, and the drop is the documented way back to the master label.
    for side_key in ("handover_from", "handover_to"):
        if merged[side_key] == existing[side_key]:
            continue
        label_key = f"{side_key}_label"
        if label_key in written_keys:
            continue
        merged[label_key] = ""

    # Display names are optional, but when recorded they stay bounded like
    # every other text fact of this block.
    for label_key in _ENTRUSTMENT_HANDOVER_LABEL_FIELDS:
        if len(merged.get(label_key, "")) > _ENTRUSTMENT_MAX_TEXT[label_key]:
            return None, [f"Tên hiển thị bàn giao dài quá {_ENTRUSTMENT_MAX_TEXT[label_key]} ký tự."]

    contract_status = _text(_mapping(contract).get("status")).upper()
    ready_complete = False
    if any(merged.get(key) for key in _ENTRUSTMENT_READY_FIELDS):
        if contract_status != "LINKED":
            return None, ["Chưa có hợp đồng liên kết đúng hai bên; chưa thể xác nhận ủy thác sẵn sàng."]
        if not merged.get("ready_at") or not merged.get("ready_ref"):
            return None, ["Cần đủ ngày xác nhận và căn cứ xác nhận ủy thác."]
        if len(merged["ready_ref"]) > _ENTRUSTMENT_MAX_TEXT["ready_ref"]:
            return None, [f"Căn cứ xác nhận dài quá {_ENTRUSTMENT_MAX_TEXT['ready_ref']} ký tự."]
        ready_complete = True

    if any(merged.get(key) for key in _ENTRUSTMENT_HANDOVER_FIELDS):
        # P0-A: a handover can never be recorded ahead of its prerequisite. This
        # also covers a replay of an old payload: the prerequisite is re-checked
        # against the CURRENT contract/importer state, never trusted from before.
        if not ready_complete:
            return None, [
                "Chưa hoàn thành công đoạn ủy thác sẵn sàng "
                "(cần hợp đồng liên kết, ngày xác nhận và căn cứ); chưa thể ghi bàn giao."
            ]
        party_ids = {row["id"] for row in entrustment_parties(flow)}
        missing = [key for key in _ENTRUSTMENT_HANDOVER_FIELDS if not merged.get(key)]
        if missing:
            return None, ["Bàn giao cần đủ thời điểm, bên giao, bên nhận và số biên bản giao nhận."]
        if merged["handover_from"] == merged["handover_to"]:
            return None, ["Bên giao và bên nhận phải khác nhau."]
        if any(merged[key] not in party_ids for key in ("handover_from", "handover_to")):
            return None, ["Bên giao/bên nhận phải thuộc chuỗi ủy thác của lô."]
        if len(merged["handover_doc_no"]) > _ENTRUSTMENT_MAX_TEXT["handover_doc_no"]:
            return None, [f"Số biên bản giao nhận dài quá {_ENTRUSTMENT_MAX_TEXT['handover_doc_no']} ký tự."]
        order_problem = _evidence_time_order(merged["handover_at"], merged.get("ready_at"))
        if order_problem:
            return None, [_EVIDENCE_TIME_ORDER_REASON[order_problem]]

    return merged, []
