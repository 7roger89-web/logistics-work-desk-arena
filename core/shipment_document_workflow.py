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
    }


def validate_flow_write(
    *,
    shipment: Mapping[str, Any],
    mode: str,
    companies: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
    company_id: str = "",
    sub_agent_id: str = "",
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate ONE explicit operator choice and return the canonical block.

    The legal importer is never guessed.  CUSTOMER_SELF requires a customer
    identity already linked to the lot.  TT_ENTRUSTED_DIRECT requires one
    explicit/uniquely resolvable Trường Thành authority company.
    TT_ENTRUSTED_SUB requires an explicit authority-agent id.
    """

    mode = _text(mode).upper()
    company_id = _text(company_id).upper()
    sub_agent_id = _text(sub_agent_id).upper()
    errors: list[str] = []

    if mode not in FLOW_MODES:
        return None, ["Chọn hình thức nhập khẩu trước khi lưu."]

    if mode == FLOW_CUSTOMER_SELF:
        customer_id = _text(shipment.get("customer_id")).upper()
        if not customer_id:
            errors.append("Lô chưa gắn mã khách hàng; chưa xác định được pháp nhân đứng nhập khẩu.")
        if sub_agent_id:
            errors.append("Khách tự đứng tên nhập khẩu thì không được gắn đơn vị nhận ủy thác tiếp.")
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
        if errors:
            return None, errors
        return {
            "mode": mode,
            "confirmed": True,
            "company_id": company_id,
            "sub_agent_id": "",
        }, []

    agent = _entity_by_id(agents, sub_agent_id, "agent_id", "id")
    if agent is None:
        errors.append("Chọn đơn vị đứng nhập khẩu hộ (ví dụ Phú Anh) từ danh mục đối tác.")
    if errors:
        return None, errors
    return {
        "mode": mode,
        "confirmed": True,
        "company_id": "",
        "sub_agent_id": sub_agent_id,
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
        importer_id = flow["sub_agent_id"]
        importer_kind = "AGENT"
        importer = _entity_by_id(agents, importer_id, "agent_id", "id")
        if importer is None:
            missing.append("Không tìm thấy đối tác đứng nhập khẩu hộ đã chọn.")

    importer = importer or {}
    importer_name = _text(
        importer.get("legal_name")
        or importer.get("name")
        or importer.get("company_name")
    )
    importer_tax_code = _text(importer.get("tax_code") or importer.get("mst"))
    if flow["confirmed"] and not importer_name:
        missing.append("Thiếu tên pháp lý của đơn vị đứng nhập khẩu.")
    if flow["confirmed"] and not importer_tax_code:
        missing.append("Thiếu mã số thuế của đơn vị đứng nhập khẩu.")

    sub_agent = _entity_by_id(agents, flow["sub_agent_id"], "agent_id", "id")
    sub_agent_name = _text(
        (sub_agent or {}).get("legal_name")
        or (sub_agent or {}).get("name")
    )

    return {
        "mode": mode,
        "modeLabel": FLOW_LABELS.get(mode, "Chưa xác nhận hình thức nhập khẩu"),
        "confirmed": bool(flow["confirmed"]),
        "companyId": flow["company_id"],
        "subAgentId": flow["sub_agent_id"],
        "subAgentName": sub_agent_name,
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


def build_document_workflow(
    *,
    flow: Mapping[str, Any],
    quote_linked: bool,
    gnt: Mapping[str, Any] | None,
    delivered: bool,
    pxk: Mapping[str, Any] | None,
    finance: Mapping[str, Any] | None,
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
        "Đã xác định đúng loại hợp đồng; trình tạo/phát hành chứng từ sẽ được nối vào docgen.",
    ))

    if mode == FLOW_TT_ENTRUSTED_SUB:
        steps.append(_step(
            "sub_entrust_contract",
            "Hợp đồng mua bán Trường Thành ↔ đơn vị đứng nhập khẩu hộ",
            STATE_PENDING_DOCUMENT,
            "Bắt buộc cho mô hình ủy thác tiếp; không áp dụng quy tắc ngưỡng 50 triệu của bộ HDNT/PL/HDMB hiện tại.",
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

    if gnt.get("done") or _mapping(gnt.get("document")):
        gnt_state, gnt_reason = STATE_COMPLETE, "Giấy nộp thuế đã được tạo cho lô."
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
    if pxk_flow["gate"] == "PXK_NOT_APPLICABLE":
        pxk_state, pxk_reason = STATE_NOT_APPLICABLE, pxk_flow["reason"]
    elif not pxk_flow["allowed"]:
        pxk_state, pxk_reason = STATE_BLOCKED, pxk_flow["reason"]
    elif _mapping(pxk.get("document")) or pxk.get("done"):
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
