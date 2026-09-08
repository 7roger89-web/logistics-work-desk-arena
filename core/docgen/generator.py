"""Orchestration for LOG-DOCGEN-01 V1 document pack generation.

This module ties the locked rules, the authority masters, the contract store
and the narrow template engine together, then records metadata, revision
history and audit.  It performs ZERO Finance Actual mutations.

Permissions:
  * GENERATE / DOWNLOAD  -> sales_write   (assert_can_generate_documents)
  * ISSUE / SUPERSEDE    -> operations_write (assert_can_issue_documents)

The service layer is the security boundary; UI hiding is never sufficient.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from core.docgen import rules as rules_mod
from core.docgen.rules import (
    BLOCKED,
    DEBIT_USD,
    GENERATED,
    HDMB,
    HDNT,
    ISSUED,
    PL,
    PXK,
    READY,
    Readiness,
)
from core.docgen.template_engine import CachedFormulaValue, mutate_docx, mutate_xlsx
from core.utils import parse_date, to_decimal, utc_now

# ---------------------------------------------------------------------------
# Vietnamese amount-in-words (bounded, VND only).  Kept local so the generator
# does not pull in an unbounded locale dependency for one optional cell.
# ---------------------------------------------------------------------------

_UNITS = ("", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
_TENS = ("", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi")
_HUNDREDS = ("", "một trăm", "hai trăm", "ba trăm", "bốn trăm", "năm trăm", "sáu trăm", "bảy trăm", "tám trăm", "chín trăm")
_SCALE = ("", "nghìn", "triệu", "tỷ")


def _three_digits_words(n: int) -> str:
    """Words for 0..999 in Vietnamese."""
    if n == 0:
        return ""
    parts: list[str] = []
    hundred = n // 100
    ten = (n % 100) // 10
    unit = n % 10
    if hundred:
        parts.append(_HUNDREDS[hundred])
    if ten:
        if ten == 1 and hundred:
            parts.append("mười" if unit in (0, 1) else "mười " + _UNITS[unit])
        elif ten == 1:
            parts.append("mười" + (" " + _UNITS[unit] if unit else ""))
        elif ten == 2 and unit == 0:
            parts.append("hai mươi")
        else:
            base = _TENS[ten]
            if unit:
                if unit == 5 and ten > 0:
                    parts.append(base + " lăm")
                else:
                    parts.append(base + " " + _UNITS[unit])
            else:
                parts.append(base)
    elif unit:
        if hundred:
            parts.append("lẻ " + _UNITS[unit])
        else:
            parts.append(_UNITS[unit])
    return " ".join(parts).strip()


def _int_words(n: int) -> str:
    if n == 0:
        return "không"
    groups: list[int] = []
    while n:
        groups.append(n % 1000)
        n //= 1000
    words: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        value = groups[index]
        if value:
            scale = _SCALE[index]
            words.append(_three_digits_words(value))
            if scale:
                words.append(scale)
    return " ".join(words).strip()


def amount_in_words_vnd(value: Any) -> str:
    """Return e.g. 'một trăm triệu đồng chẵn' for a VND amount."""
    amount = to_decimal(value)
    if amount is None:
        return ""
    rounded = int(amount.quantize(Decimal(1)))
    integer = rounded
    whole = _int_words(integer)
    text = f"{whole} đồng chẵn" if integer else "không đồng"
    return text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _date_ddmmyyyy(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d/%m/%Y")


def _vnd_format(value: Any) -> str:
    amount = to_decimal(value) or Decimal(0)
    return f"{int(amount):,}".replace(",", ".")


def _nonempty(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _document_id(document_type: str, shipment_id: str, counterparty: str) -> str:
    base = f"{str(shipment_id).upper().strip()}-{document_type}-{str(counterparty).upper().strip()}"
    return base


# ---------------------------------------------------------------------------
# Payload builders (pure; no DB)
# ---------------------------------------------------------------------------


def build_xlsx_payload(
    document_type: str,
    *,
    contract_no: str,
    contract_date: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    goods_lines: list[Mapping[str, Any]],
    parent_contract: Mapping[str, Any] | None = None,
    delivery: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the sheet->cell fill map for an XLSX document."""
    delivery = delivery or {}
    totals, _ = rules_mod.compute_goods_totals(goods_lines)
    lines = totals.lines
    words = amount_in_words_vnd(totals.total_after_vat)
    ddmmyyyy = _date_ddmmyyyy(contract_date)

    agent_name = _nonempty(agent.get("legal_name"))
    company_name = _nonempty(company.get("legal_name"))

    if document_type == HDMB:
        goods = lines[0] if lines else {}
        return {
            "HDMB": {
                "A4": f"Số: {contract_no}",
                "A5": _date_line(ddmmyyyy),
                "A8": f"Tên công ty/cá nhân: {agent_name}",
                "A9": f"Địa chỉ: {_nonempty(agent.get('legal_address'))}",
                "A10": f"Điện thoại: {_nonempty(agent.get('phone'))}    Email: {_nonempty(agent.get('email'))}",
                "A11": f"Mã số thuế: {_nonempty(agent.get('legal_code'))}",
                "A12": f"Tài khoản số: {_nonempty(agent.get('bank_account_number'))}    Tại Ngân hàng: {_nonempty(agent.get('bank_name'))}",
                "A13": f"Đại diện bởi Ông/Bà: {_normalize_rep_name(_nonempty(agent.get('legal_representative')))}    Chức vụ: {_nonempty(agent.get('representative_title'))}",
                "A15": f"Tên công ty: {company_name}",
                "A16": f"Địa chỉ: {_nonempty(company.get('legal_address'))}",
                "A17": f"Điện thoại: {_nonempty(company.get('phone'))}    Email: {_nonempty(company.get('email'))}",
                "A18": f"Mã số thuế: {_nonempty(company.get('tax_or_legal_code'))}",
                "A19": f"Tài khoản số: {_nonempty(company.get('bank_account_number'))}",
                "A20": f"Đại diện bởi Ông/Bà: {_normalize_rep_name(_nonempty(company.get('legal_representative')))}    Chức vụ: {_nonempty(company.get('representative_title'))}",
                "B24": _nonempty(goods.get("description")),
                "C24": _nonempty(goods.get("unit")),
                "D24": _to_number(goods.get("quantity")),
                "E24": _to_number(goods.get("unit_price_vnd_excl_vat")),
                "F24": _to_number(goods.get("amount_vnd_excl_vat")),
                "F25": CachedFormulaValue(totals.subtotal),
                "F26": CachedFormulaValue(totals.vat_amount),
                "F27": CachedFormulaValue(totals.total_after_vat),
                "A28": f"(Bằng chữ: {words})",
                "A35": f"* Chủ tài khoản: {_nonempty(agent.get('bank_account_holder'))}",
                "A36": f"* Số tài khoản: {_nonempty(agent.get('bank_account_number'))}",
                "A37": f"* Tại Ngân hàng: {_nonempty(agent.get('bank_name'))}",
                "A38": f"* Chi nhánh: {_nonempty(agent.get('bank_branch'))}",
                "A40": f"3.1. Thời gian giao hàng: Giao hàng vào ngày {_date_ddmmyyyy(delivery.get('delivery_date')) if delivery.get('delivery_date') else '…'}",
                "A41": f"3.2. Địa điểm giao hàng: {_nonempty(delivery.get('delivery_location'))}",
            }
        }

    if document_type == PL:
        parent_no = _nonempty((parent_contract or {}).get("contract_no") or (parent_contract or {}).get("id"))
        parent_date = _nonempty((parent_contract or {}).get("contract_date") or (parent_contract or {}).get("date"))
        fill: dict[str, Any] = {
            "A4": f"Số: {contract_no}",
            "A5": f"Ngày: {ddmmyyyy}",
            "A6": f" Căn cứ Hợp đồng nguyên tắc số {parent_no} ngày {_date_ddmmyyyy(parent_date) if parent_date else parent_no} giữa {agent_name} và {company_name}.",
            "A31": f"(Bằng chữ: {words})",
            "A33": f"Phụ lục này là một bộ phận không tách rời của Hợp đồng nguyên tắc {parent_no} ngày {_date_ddmmyyyy(parent_date) if parent_date else parent_no} và có hiệu lực kể từ ngày ký đến khi hai bên hoàn thành nghĩa vụ thanh toán.",
        }
        for idx, goods in enumerate(lines[: rules_mod.MAX_PL_LINES], start=10):
            fill[f"A{idx}"] = goods["sequence"]
            fill[f"B{idx}"] = _nonempty(goods.get("description"))
            fill[f"C{idx}"] = _nonempty(goods.get("unit"))
            fill[f"D{idx}"] = _to_number(goods.get("quantity"))
            fill[f"E{idx}"] = _to_number(goods.get("unit_price_vnd_excl_vat"))
            fill[f"F{idx}"] = _to_number(goods.get("amount_vnd_excl_vat"))
            
        fill["F28"] = CachedFormulaValue(totals.subtotal)
        fill["F29"] = CachedFormulaValue(totals.vat_amount)
        fill["F30"] = CachedFormulaValue(totals.total_after_vat)
        
        return {"pl": fill}

    if document_type == PXK:
        goods = lines[0] if lines else {}
        return {
            "pxk": {
                "A4": f"Số: {contract_no}",
                "A5": f"Ngày: {ddmmyyyy}",
                "A6": f"Bên giao (Bên A): {agent_name}",
                "A7": f"Địa chỉ: {_nonempty(agent.get('legal_address'))}",
                "A9": f"Bên nhận (Bên B):{company_name}",
                "A10": f" Đại diện nhận hàng:{_nonempty(delivery.get('receiver_name'))}    Chức vụ:{_nonempty(delivery.get('receiver_title'))}",
                "A11": f"Địa điểm nhận hàng: {_nonempty(delivery.get('delivery_location'))}",
                "B15": _nonempty(goods.get("description")),
                "C15": _nonempty(goods.get("unit")),
                "D15": _to_number(goods.get("quantity")),
            }
        }

    raise ValueError(f"Unsupported XLSX document type: {document_type}")


def _normalize_rep_name(name: str) -> str:
    if name.startswith("Ông "):
        return name[4:]
    if name.startswith("Bà "):
        return name[3:]
    return name

def build_docx_run_edits(
    *,
    contract_no: str,
    contract_date: str,
    valid_from: str,
    valid_to: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
) -> list[tuple[int, int, str, str | None]]:
    """Build HDNT run-level edits (para_index, run_index, value, replace)."""
    parsed = parse_date(contract_date)
    day = parsed.strftime("%d")
    month = parsed.strftime("%m")
    year = parsed.strftime("%Y")
    agent_name = _nonempty(agent.get("legal_name"))
    company_name = _nonempty(company.get("legal_name"))
    return [
        (2, 3, contract_no, None),
        (4, 1, day, None),
        (4, 3, month, None),
        (4, 5, year, None),
        (4, 8, _nonempty(company.get("legal_name")), None),
        (5, 3, agent_name, None),
        (6, 1, _nonempty(agent.get("legal_address")), None),
        (7, 1, _nonempty(agent.get("phone")), None),
        (8, 1, _nonempty(agent.get("legal_code")), None),
        (9, 1, _normalize_rep_name(_nonempty(agent.get("legal_representative"))), None),
        (9, 2, "  ", None),
        (9, 3, f"Chức vụ: {_nonempty(agent.get('representative_title'))}", None),
        (11, 3, company_name, None),
        (12, 1, _nonempty(company.get("legal_address")), None),
        (13, 0, f"Điện thoại: {_nonempty(company.get('phone'))}", None),
        (14, 1, _nonempty(company.get("tax_or_legal_code")), None),
        (15, 2, _normalize_rep_name(_nonempty(company.get("legal_representative"))), None),
        (15, 3, "  ", None),
        (15, 4, "", None),
        (15, 5, f"Chức vụ: {_nonempty(company.get('representative_title'))}", None),
        (22, 5, _date_ddmmyyyy(valid_from), None),
        (22, 7, _date_ddmmyyyy(valid_to), None),
        (30, 2, _nonempty(agent.get("bank_account_number")), None),
        (30, 5, _nonempty(agent.get("bank_name")), None),
    ]


def _to_number(value: Any):
    amount = to_decimal(value)
    if amount is None:
        return 0
    if amount == amount.to_integral_value():
        return int(amount)
    return amount


def _date_line(ddmmyyyy: str) -> str:
    # Template A5: "…., ngày …. tháng …. năm …."
    parsed = parse_date(ddmmyyyy)
    return f"Ngày {parsed.strftime('%d')} tháng {parsed.strftime('%m')} năm {parsed.strftime('%Y')}"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def build_metadata(
    document_id: str,
    *,
    document_type: str,
    shipment_id: str,
    contract_id: str,
    parent_contract_id: str | None,
    counterparty_id: str,
    template_hash: str,
    revision: int,
    status: str,
    output_file_name: str,
    output_hash: str,
    source_reference: str,
    source_snapshot: Mapping[str, Any],
    supersedes_document_id: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    return {
        "id": f"{document_id}::R{revision}",
        "document_id": document_id,
        "document_type": document_type,
        "shipment_id": shipment_id,
        "contract_id": contract_id,
        "parent_contract_id": parent_contract_id,
        "counterparty_id": counterparty_id,
        "template_hash": template_hash,
        "generation_revision": revision,
        "revision": revision,
        "status": status,
        "generated_at": now.isoformat(),
        "generated_by": "",
        "source_snapshot": dict(source_snapshot),
        "source_reference": source_reference,
        "output_file_name": output_file_name,
        "output_hash": output_hash,
        "supersedes_document_id": supersedes_document_id,
        "superseded_by_document_id": None,
    }


def _next_revision(document_type: str, shipment_id: str, counterparty: str, existing: Mapping[str, Mapping[str, Any]]) -> int:
    logical = _document_id(document_type, shipment_id, counterparty)
    revisions = [
        int(item.get("generation_revision") or item.get("revision") or 0)
        for item in existing.values()
        if str(item.get("document_id") or "") == logical
    ]
    return (max(revisions) + 1) if revisions else 1


# ---------------------------------------------------------------------------
# Public service API
# ---------------------------------------------------------------------------


class DocumentGenerationError(RuntimeError):
    """Raised when a document cannot be generated safely."""

    def __init__(self, readiness: Readiness) -> None:
        self.readiness = readiness
        super().__init__(readiness.reason)


def generate_xlsx_file(
    template_path: str,
    document_type: str,
    *,
    contract_no: str,
    contract_date: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    goods_lines: list[Mapping[str, Any]],
    parent_contract: Mapping[str, Any] | None = None,
    delivery: Mapping[str, Any] | None = None,
) -> bytes:
    payload = build_xlsx_payload(
        document_type,
        contract_no=contract_no,
        contract_date=contract_date,
        agent=agent,
        company=company,
        goods_lines=goods_lines,
        parent_contract=parent_contract,
        delivery=delivery,
    )
    return mutate_xlsx(template_path, payload)


def generate_docx_file(
    template_path: str,
    *,
    contract_no: str,
    contract_date: str,
    valid_from: str,
    valid_to: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
) -> bytes:
    edits = build_docx_run_edits(
        contract_no=contract_no,
        contract_date=contract_date,
        valid_from=valid_from,
        valid_to=valid_to,
        agent=agent,
        company=company,
    )
    return mutate_docx(template_path, edits)


# The functions below are the thin, DB-touching orchestration seam.  They are
# kept separate so unit tests can exercise the pure builders above and assert
# that persistence/audit is only invoked with the right arguments.


def generate_document(
    document_type: str,
    *,
    shipment_id: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    goods_lines: list[Mapping[str, Any]],
    contract: Mapping[str, Any],
    parent_contract: Mapping[str, Any] | None = None,
    delivery: Mapping[str, Any] | None = None,
    template_path_xlsx: str | None = None,
    template_path_docx: str | None = None,
    existing_documents: Mapping[str, Mapping[str, Any]] | None = None,
    pxk_source: Mapping[str, Any] | None = None,
    document_id_override: str | None = None,
) -> dict[str, Any]:
    """Generate one document file + metadata.  Does not write Finance.

    Each legal document owns its own identity (``hdnt_no`` / ``pl_no`` /
    ``hdmb_no`` / ``pxk_no``).  PXK must be driven by an explicitly selected
    source contract/document (HDMB or PL), never by the generic goods editor.
    ``document_id_override`` is used by supersede to mint a NEW logical id
    (never silently reusing the superseded one).
    """
    from core.auth import can_generate_documents, current_actor_context

    if not can_generate_documents():
        raise PermissionError("sales_write")

    readiness = rules_mod.evaluate_document_readiness(
        document_type,
        goods_lines=goods_lines,
        agent=agent,
        company=company,
        parent_contract=parent_contract,
        selected_contract=contract,
        delivery_completed=bool((delivery or {}).get("delivery_completed")),
        document_identity=contract,
        pxk_source=pxk_source,
        delivery=delivery,
    )
    if readiness.state != READY:
        raise DocumentGenerationError(readiness)

    contract_no = rules_mod.doc_no(document_type, contract) or _nonempty(contract.get("contract_no") or contract.get("id"))
    contract_date = rules_mod.doc_date(document_type, contract) or _nonempty(contract.get("contract_date") or contract.get("date"))
    counterparty_id = _nonempty(agent.get("agent_id") or agent.get("id"))

    # PXK: the source snapshot (not the goods editor) is authoritative for the
    # goods line(s) written into the template.
    if document_type == PXK and pxk_source:
        source_line = (pxk_source or {}).get("source_goods_line")
        if source_line:
            goods_lines = [dict(source_line)]

    if document_type == HDNT:
        if template_path_docx is None:
            raise DocumentGenerationError(_blocked("Thiếu template HDNT (DOCX)."))
        payload = build_docx_run_edits(
            contract_no=contract_no,
            contract_date=contract_date,
            valid_from=_nonempty(contract.get("valid_from")),
            valid_to=_nonempty(contract.get("valid_to")),
            agent=agent,
            company=company,
        )
        output = mutate_docx(template_path_docx, payload)
        output_name = f"{document_type}_{contract_no}.docx"
        template_hash = _sha256(_read_file(template_path_docx))
    else:
        if template_path_xlsx is None:
            raise DocumentGenerationError(_blocked("Thiếu template XLSX."))
        output = generate_xlsx_file(
            template_path_xlsx,
            document_type,
            contract_no=contract_no,
            contract_date=contract_date,
            agent=agent,
            company=company,
            goods_lines=goods_lines,
            parent_contract=parent_contract,
            delivery=delivery,
        )
        output_name = f"{document_type}_{contract_no}.xlsx"
        template_hash = _sha256(_read_file(template_path_xlsx))

    document_id = document_id_override or _document_id(document_type, shipment_id, counterparty_id)
    revision = _next_revision(document_type, shipment_id, counterparty_id, existing_documents or {})
    output_hash = _sha256(output)
    actor = current_actor_context()
    source_snapshot = _build_source_snapshot(
        document_type,
        contract=contract,
        document_no=contract_no,
        document_date=contract_date,
        agent=agent,
        company=company,
        goods_lines=goods_lines,
        parent_contract=parent_contract,
        delivery=delivery,
        pxk_source=pxk_source,
        counterparty_id=counterparty_id,
    )
    metadata = build_metadata(
        document_id,
        document_type=document_type,
        shipment_id=shipment_id,
        contract_id=_nonempty(contract.get("id") or contract_no),
        parent_contract_id=_nonempty((parent_contract or {}).get("id")) if parent_contract else None,
        counterparty_id=counterparty_id,
        template_hash=template_hash,
        revision=revision,
        status=GENERATED,
        output_file_name=output_name,
        output_hash=output_hash,
        source_reference=f"{document_type}:{contract_no}",
        source_snapshot=source_snapshot,
    )
    metadata["generated_by"] = actor["username"]

    return {
        "document_id": document_id,
        "revision": revision,
        "status": GENERATED,
        "output_file_name": output_name,
        "output_hash": output_hash,
        "template_hash": template_hash,
        "bytes": output,
        "metadata": metadata,
    }


def _build_source_snapshot(
    document_type: str,
    *,
    contract: Mapping[str, Any],
    document_no: str,
    document_date: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    goods_lines: list[Mapping[str, Any]],
    parent_contract: Mapping[str, Any] | None,
    delivery: Mapping[str, Any] | None,
    pxk_source: Mapping[str, Any] | None,
    counterparty_id: str,
) -> dict[str, Any]:
    """Build the provenance snapshot of the ACTUAL facts used to generate."""
    snapshot: dict[str, Any] = {
        "document_type": document_type,
        "document_no": document_no,
        "document_date": document_date,
        "agent_id": counterparty_id,
        "company_id": _nonempty(company.get("company_id") or company.get("id")),
        "goods_lines": [dict(g) for g in (goods_lines or [])],
    }
    snapshot[f"{document_type.lower()}_no"] = document_no
    snapshot[f"{document_type.lower()}_date"] = document_date

    if document_type == HDNT:
        snapshot["valid_from"] = _nonempty(contract.get("valid_from"))
        snapshot["valid_to"] = _nonempty(contract.get("valid_to"))
    if document_type == PL:
        parent_no = _nonempty((parent_contract or {}).get("hdnt_no") or (parent_contract or {}).get("contract_no") or (parent_contract or {}).get("id"))
        snapshot["parent_hdnt_id"] = _nonempty((parent_contract or {}).get("id") or parent_no)
        snapshot["parent_hdnt_no"] = parent_no
        snapshot["parent_hdnt_date"] = _nonempty((parent_contract or {}).get("hdnt_date") or (parent_contract or {}).get("contract_date"))
        snapshot["parent_hdnt_revision"] = (parent_contract or {}).get("generation_revision") or (parent_contract or {}).get("revision")
    if document_type == PXK:
        snapshot["delivery_completed"] = bool((delivery or {}).get("delivery_completed"))
        snapshot["receiver_name"] = _nonempty((delivery or {}).get("receiver_name"))
        snapshot["receiver_title"] = _nonempty((delivery or {}).get("receiver_title"))
        snapshot["delivery_location"] = _nonempty((delivery or {}).get("delivery_location"))
        pxk_src = pxk_source or {}
        snapshot["source_document_type"] = str(pxk_src.get("source_document_type") or "").upper()
        snapshot["source_contract_id"] = _nonempty(pxk_src.get("source_contract_id") or pxk_src.get("source_document_id"))
        snapshot["source_revision"] = (pxk_src or {}).get("source_revision")
        snapshot["source_goods_snapshot"] = dict(pxk_src.get("source_goods_line") or {})
    return snapshot


def _blocked(message: str) -> Readiness:
    return Readiness(document_type="", state=BLOCKED, reason=message)


def _read_file(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


# ---------------------------------------------------------------------------
# Document pack summary (pure view model for the UI)
# ---------------------------------------------------------------------------


def build_document_pack(
    *,
    shipment_id: str,
    goods_lines: list[Mapping[str, Any]],
    currency: str = rules_mod.VND_CURRENCY,
    delivery_completed: bool = False,
    agent: Mapping[str, Any] | None = None,
    company: Mapping[str, Any] | None = None,
    parent_contract: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
    pxk_source: Mapping[str, Any] | None = None,
    delivery: Mapping[str, Any] | None = None,
    contracts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the viewer-friendly applicability + readiness summary."""
    totals, _ = rules_mod.compute_goods_totals(goods_lines)
    try:
        applicability = rules_mod.decide_applicable_documents(
            goods_lines=goods_lines,
            currency=currency,
            delivery_completed=delivery_completed,
            pxk_source=pxk_source,
        )
    except Exception:  # noqa: BLE001 - never let summary rendering break the page
        applicability = {}

    cards: list[dict[str, Any]] = []
    for doc_type in rules_mod.APPLICABLE_DOCUMENT_TYPES:
        readiness = rules_mod.evaluate_document_readiness(
            doc_type,
            goods_lines=goods_lines,
            agent=agent,
            company=company,
            parent_contract=parent_contract,
            selected_contract=contract,
            delivery_completed=delivery_completed,
            document_identity=contract,
            pxk_source=pxk_source,
            delivery=delivery,
        )
        cards.append(_card_view(doc_type, readiness))
    pxk_readiness = rules_mod.evaluate_document_readiness(
        PXK,
        goods_lines=goods_lines,
        agent=agent,
        company=company,
        selected_contract=contract,
        delivery_completed=delivery_completed,
        document_identity=contract,
        pxk_source=pxk_source,
        delivery=delivery,
    )
    cards.append(_card_view(PXK, pxk_readiness))
    cards.append({"document_type": DEBIT_USD, "state": "DEFERRED", "reason": "Chưa triển khai", "applicable": False})

    # HDNT reuse rule: a valid existing HDNT for the selected Agent is REUSED /
    # LINKED, never auto-regenerated.  Multiple valid HDNT require selection.
    hdnt_reuse: dict[str, Any] = {}
    if agent:
        candidates = contracts or {}
        decision = rules_mod.classify_valid_hdnt(
            candidates,
            agent_id=_nonempty(agent.get("agent_id") or agent.get("id")),
            company_id=_nonempty(company.get("company_id") or company.get("id")) if company else "",
        )
        if decision["valid_count"] >= 1:
            hdnt_reuse = {
                "valid_count": decision["valid_count"],
                "needs_selection": decision["needs_selection"],
                "reuse_target": decision["reuse_target"],
            }
            for card in cards:
                if card["document_type"] == HDNT:
                    if decision["needs_selection"]:
                        card["state"] = rules_mod.MISSING_INFO
                        card["missing"] = ["Cần chọn HDNT hiện có để tái sử dụng."]
                        card["reason"] = "Có nhiều HDNT hợp lệ — cần chọn một HDNT để tái sử dụng."
                    else:
                        card["state"] = rules_mod.READY
                        card["reason"] = "Tái sử dụng HDNT hiện có (không tạo HDNT mới)."
                        card["source_ref"] = _nonempty(decision["reuse_target"].get("id") or decision["reuse_target"].get("hdnt_no") or decision["reuse_target"].get("contract_no"))
                    break

    return {
        "shipment_id": shipment_id,
        "currency": currency,
        "totals": totals.as_dict(),
        "threshold_vnd": int(rules_mod.VND_THRESHOLD),
        "applicable_documents": [c["document_type"] for c in cards if c["applicable"] and c["state"] in (rules_mod.READY, rules_mod.MISSING_INFO)],
        "cards": cards,
        "hdnt_reuse": hdnt_reuse,
    }


def _card_view(document_type: str, readiness: Readiness) -> dict[str, Any]:
    return {
        "document_type": document_type,
        "state": readiness.state,
        "reason": readiness.reason,
        "missing": list(readiness.missing),
        "source_ref": readiness.source_ref,
        "goods_count": readiness.goods_count,
        "applicable": readiness.applicable,
    }


def reuse_decision_for_agent(
    contracts: Mapping[str, Any] | None,
    *,
    agent: Mapping[str, Any],
    company: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the HDNT reuse/selection decision for the selected Agent."""
    if not agent:
        return {"valid_count": 0, "needs_selection": False, "reuse_target": None, "valid_hdnt": []}
    candidates = {k: c for k, c in (contracts or {}).items() if str(c.get("kind") or c.get("type") or "").upper() == HDNT}
    return rules_mod.classify_valid_hdnt(
        candidates,
        agent_id=_nonempty(agent.get("agent_id") or agent.get("id")),
        company_id=_nonempty(company.get("company_id") or company.get("id")) if company else "",
    )


# ---------------------------------------------------------------------------
# Issue / supersede
# ---------------------------------------------------------------------------


def issue_document(
    document_id: str,
    *,
    revision: int | None = None,
    actor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Mark the latest revision of a generated document as ISSUED (immutable)."""
    from core.auth import assert_can_issue_documents
    from core.database import (
        load_docgen_document,
        load_docgen_document_latest,
        save_docgen_document,
    )

    assert_can_issue_documents()
    from core.auth import current_actor_context

    record = (
        load_docgen_document(f"{document_id}::R{revision}")
        if revision is not None
        else load_docgen_document_latest(document_id)
    )
    if record is None:
        raise DocumentGenerationError(_blocked(f"Không tìm thấy chứng từ {document_id}."))
    if record.get("status") == ISSUED:
        raise DocumentGenerationError(_blocked("Chứng từ đã ISSUED — bất biến, không thể phát hành lại."))

    record["status"] = ISSUED
    record["issued_at"] = utc_now().isoformat()
    record["issued_by"] = current_actor_context()["username"]
    if not save_docgen_document(record):
        raise DocumentGenerationError(_blocked("Không lưu được trạng thái ISSUED."))
    return {"document_id": document_id, "revision": record.get("generation_revision", 1), "status": ISSUED}


def supersede_document(
    old_document_id: str,
    *,
    new_document_id: str,
    document_type: str,
    shipment_id: str,
    contract_no: str,
    contract_date: str,
    agent: Mapping[str, Any],
    company: Mapping[str, Any],
    goods_lines: list[Mapping[str, Any]],
    template_path_xlsx: str | None = None,
    template_path_docx: str | None = None,
) -> dict[str, Any]:
    """Create a new document id that supersedes an ISSUED one. No silent overwrite."""
    from core.auth import assert_can_issue_documents
    from core.database import (
        link_superseded_docgen_document,
        load_docgen_document_latest,
        save_docgen_document,
    )

    assert_can_issue_documents()
    old = load_docgen_document_latest(old_document_id)
    if old is None:
        raise DocumentGenerationError(_blocked(f"Không tìm thấy chứng từ bị thay thế {old_document_id}."))
    if old.get("status") != ISSUED:
        raise DocumentGenerationError(_blocked("Chỉ thay thế chứng từ đã ISSUED."))

    # The new document gets its OWN logical id (new_document_id) and its OWN
    # legal number/date — it must differ from the superseded document.
    contract = {
        "id": new_document_id,
        "contract_no": contract_no,
        "contract_date": contract_date,
        "currency": rules_mod.VND_CURRENCY,
    }
    # Map the per-document legal identity field to the provided new number/date.
    identity_key_no = {"HDNT": "hdnt_no", "PL": "pl_no", "HDMB": "hdmb_no", "PXK": "pxk_no"}.get(document_type)
    identity_key_date = {"HDNT": "hdnt_date", "PL": "pl_date", "HDMB": "hdmb_date", "PXK": "pxk_date"}.get(document_type)
    if identity_key_no:
        contract[identity_key_no] = contract_no
    if identity_key_date:
        contract[identity_key_date] = contract_date

    result = generate_document(
        document_type,
        shipment_id=shipment_id,
        agent=agent,
        company=company,
        goods_lines=goods_lines,
        contract=contract,
        parent_contract=None,
        delivery=None,
        template_path_xlsx=template_path_xlsx,
        template_path_docx=template_path_docx,
        existing_documents={},
        document_id_override=new_document_id,
    )
    metadata = result["metadata"]
    metadata["supersedes_document_id"] = old_document_id
    if not save_docgen_document(metadata):
        raise DocumentGenerationError(_blocked("Không lưu được chứng từ thay thế."))

    # Use the controlled helper for supersede linkage on the ISSUED old record.
    # The generic save_docgen_document no longer permits any modification to ISSUED records.
    if not link_superseded_docgen_document(old_document_id, metadata["document_id"]):
        raise DocumentGenerationError(_blocked("Không cập nhật được chứng từ cũ."))
    result["supersedes_document_id"] = old_document_id
    return result
