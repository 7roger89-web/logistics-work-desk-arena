"""Locked business rules (LOG-DOCGEN-01 V1).

Everything here is a pure function over plain dicts so it is trivially
testable without MongoDB.  Money arithmetic uses ``Decimal`` with
``ROUND_HALF_UP`` to whole VND, per the owner-locked rule set.

Rules that are CLOSED (must never be re-asked by the Operator):
  * 50,000,000 VND threshold (>= -> HDMB; < -> HDNT + PL)
  * Agent is the seller of goods to Trường Thành
  * VAT 8% (VND only)
  * PXK only after explicit DELIVERY_COMPLETED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping

VAT_RATE = Decimal("0.08")
VND_THRESHOLD = Decimal("50_000_000")
VND_CURRENCY = "VND"

HDNT = "HDNT"
PL = "PL"
HDMB = "HDMB"
PXK = "PXK"
DEBIT_USD = "DEBIT_USD"
DOCUMENT_TYPES = (HDNT, PL, HDMB, PXK)
APPLICABLE_DOCUMENT_TYPES = (HDNT, PL, HDMB)

MAX_HDMB_LINES = 1
MAX_PL_LINES = 18

READY = "READY"
MISSING_INFO = "MISSING_INFO"
NOT_APPLICABLE = "NOT_APPLICABLE"
OWNER_RULE_REQUIRED = "OWNER_RULE_REQUIRED"
BLOCKED = "BLOCKED"

# Prepared statuses shared with the generator / view.
DRAFT = "DRAFT"
GENERATED = "GENERATED"
ISSUED = "ISSUED"


@dataclass
class Readiness:
    """Deterministic readiness snapshot for one document (or rule question).

    ``state`` is one of READY / MISSING_INFO / NOT_APPLICABLE /
    OWNER_RULE_REQUIRED.  ``missing`` lists human-checked missing facts in
    Vietnamese.  ``reason`` is one line of Vietnamese user-facing text.
    """

    document_type: str
    state: str
    reason: str = ""
    missing: tuple[str, ...] = ()
    applicable: bool = True
    source_ref: str = ""
    goods_count: int = 0
    total_after_vat: Decimal = Decimal("0")


@dataclass
class GoodsTotals:
    """Aggregated money facts for a goods line set (VND)."""

    lines: list[dict[str, Any]] = field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    vat_amount: Decimal = Decimal("0")
    total_after_vat: Decimal = Decimal("0")
    currency: str = VND_CURRENCY

    def as_dict(self) -> dict[str, Any]:
        return {
            "lines": list(self.lines),
            "subtotal": int(self.subtotal),
            "vat_amount": int(self.vat_amount),
            "total_after_vat": int(self.total_after_vat),
            "currency": self.currency,
        }


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    raw = str(value).strip().replace(",", "").replace(" ", "")
    if not raw:
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _whole_vnd(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _is_vnd(currency: Any) -> bool:
    return str(currency or "").strip().upper() in ("", VND_CURRENCY)


def normalize_goods_line(line: Mapping[str, Any], sequence: int) -> dict[str, Any]:
    """Normalise one purchase goods line to canonical keys.

    Returns a plain dict with Decimal amounts converted to integer VND.  A line
    that fails quantity/price validation is returned with ``valid: False``.
    """
    description = str(line.get("description") or line.get("name") or "").strip()
    unit = str(line.get("unit") or line.get("unit_of_measure") or "").strip()
    quantity = _decimal(line.get("quantity"))
    unit_price = _decimal(line.get("unit_price_vnd_excl_vat") or line.get("unit_price"))
    vat_rate = _decimal(line.get("vat_rate"))
    amount: Decimal = Decimal("0")
    valid = True
    errors: list[str] = []

    if not description:
        errors.append("Thiếu mô tả hàng hóa")
        valid = False
    if not unit:
        errors.append("Thiếu đơn vị tính")
        valid = False
    if quantity is None or quantity <= 0:
        errors.append("Số lượng phải lớn hơn 0")
        valid = False
    if unit_price is None or unit_price < 0:
        errors.append("Đơn giá phải >= 0")
        valid = False
    if vat_rate is None:
        vat_rate = VAT_RATE
    elif vat_rate != VAT_RATE:
        errors.append("Chỉ hỗ trợ thuế GTGT 8%")
        valid = False

    if valid:
        amount = _whole_vnd(quantity * unit_price)

    return {
        "line_id": str(line.get("line_id") or f"g{sequence:02d}"),
        "sequence": sequence,
        "description": description,
        "specification_or_code": str(line.get("specification_or_code") or "").strip(),
        "unit": unit,
        "quantity": str(quantity),
        "unit_price_vnd_excl_vat": int(unit_price or 0),
        "amount_vnd_excl_vat": int(amount),
        "vat_rate": str(vat_rate or VAT_RATE),
        "currency": VND_CURRENCY,
        "source_reference": str(line.get("source_reference") or "").strip(),
        "confirmed_by": str(line.get("confirmed_by") or "").strip(),
        "confirmed_at": str(line.get("confirmed_at") or "").strip(),
        "valid": valid,
        "validation_errors": errors,
    }


def compute_goods_totals(lines: list[Mapping[str, Any]]) -> tuple[GoodsTotals, list[dict[str, Any]]]:
    """Compute VND totals from a purchase goods line set.

    Returns ``(totals, normalized_lines)``.  ``totals.lines`` holds the
    normalised, validated lines.  If any line is invalid the totals stay at 0
    and the caller must block generation.
    """
    normalized: list[dict[str, Any]] = []
    for index, line in enumerate(lines or [], start=1):
        normalized.append(normalize_goods_line(line, index))

    invalid = [item for item in normalized if not item["valid"]]
    if invalid:
        return GoodsTotals(lines=normalized), normalized

    subtotal = sum((_decimal(item["amount_vnd_excl_vat"]) or Decimal("0") for item in normalized), Decimal("0"))
    subtotal = _whole_vnd(subtotal)
    vat_amount = _whole_vnd(subtotal * VAT_RATE)
    total_after_vat = _whole_vnd(subtotal + vat_amount)
    totals = GoodsTotals(
        lines=normalized,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total_after_vat=total_after_vat,
        currency=VND_CURRENCY,
    )
    return totals, normalized


def total_after_vat(lines: list[Mapping[str, Any]]) -> Decimal | None:
    """Return total-amount-after-VAT in VND, or None when the value is UNKNOWN.

    UNKNOWN != 0: if the goods set cannot produce an authoritative total the
    result is None so callers never substitute a zero.
    """
    totals, normalized = compute_goods_totals(lines)
    if any(not item["valid"] for item in normalized):
        return None
    if not normalized:
        return None
    return totals.total_after_vat


def decide_applicable_documents(
    *,
    goods_lines: list[Mapping[str, Any]],
    currency: str = VND_CURRENCY,
    delivery_completed: bool = False,
) -> dict[str, Readiness]:
    """Apply the 50M threshold rule and return per-document applicability.

    This drives the UI cards and the preflight order.  It never turns an
    UNKNOWN total into zero.
    """
    total = total_after_vat(goods_lines)
    normalized = [normalize_goods_line(line, idx) for idx, line in enumerate(goods_lines or [], start=1)]
    valid_lines = [item for item in normalized if item["valid"]]
    line_count = len(valid_lines)

    if not _is_vnd(currency):
        block_total = _blocked("Hợp đồng mua bán hàng hóa chỉ hỗ trợ VND (V1).", document_type=HDNT, detail="Không có chuyển đổi ngoại tệ.")
        return {
            HDNT: block_total,
            PL: _blocked("Hợp đồng mua bán hàng hóa chỉ hỗ trợ VND (V1).", document_type=PL, detail="Không có chuyển đổi ngoại tệ."),
            HDMB: _blocked("Hợp đồng mua bán hàng hóa chỉ hỗ trợ VND (V1).", document_type=HDMB, detail="Không có chuyển đổi ngoại tệ."),
            PXK: _blocked("Lô hàng không ở dạng VND.", document_type=PXK, detail="PXK không thể xác định nguồn chính xác."),
        }

    if total is None:
        unknown_total = _blocked("Chưa có tổng giá trị sau thuế đáng tin cậy.", document_type=HDNT, detail="Tổng đang UNKNOWN, không thể thay bằng 0.")
        return {
            HDNT: unknown_total,
            PL: _blocked("Chưa có tổng giá trị sau thuế đáng tin cậy.", document_type=PL, detail="Tổng đang UNKNOWN, không thể thay bằng 0."),
            HDMB: _blocked("Chưa có tổng giá trị sau thuế đáng tin cậy.", document_type=HDMB, detail="Tổng đang UNKNOWN, không thể thay bằng 0."),
            PXK: _blocked("Chưa có nguồn hàng hóa đáng tin cậy.", document_type=PXK, detail="PXK cần một nguồn đã chọn."),
        }

    if total < VND_THRESHOLD:
        hdnt = _ready("Áp dụng: tổng sau thuế < 50.000.000 VND.", document_type=HDNT)
        pl = _ready("Áp dụng: tổng sau thuế < 50.000.000 VND.", document_type=PL)
        hdmb = _not_applicable("Không áp dụng: tổng sau thuế < 50.000.000 VND.", document_type=HDMB, detail="Chỉ áp dụng cho HDNT + PL.")
    else:
        hdmb = _ready("Áp dụng: tổng sau thuế >= 50.000.000 VND.", document_type=HDMB)
        hdnt = _not_applicable("Không áp dụng: tổng sau thuế >= 50.000.000 VND.", document_type=HDNT, detail="Chỉ áp dụng cho HDMB.")
        pl = _not_applicable("Không áp dụng: tổng sau thuế >= 50.000.000 VND.", document_type=PL, detail="Chỉ áp dụng cho HDMB.")

    if line_count > MAX_HDMB_LINES:
        hdmb.state = BLOCKED
        hdmb.reason = "HDMB chỉ hỗ trợ tối đa 1 dòng hàng (V1)."
        hdmb.missing = ("HDMB tối đa 1 dòng hàng,",)
    if line_count > MAX_PL_LINES:
        pl.state = BLOCKED
        pl.reason = "PL chỉ hỗ trợ từ 1 đến 18 dòng hàng (V1)."
        pl.missing = ("PL tối đa 18 dòng hàng,",)
    if line_count == 0:
        pl.state = BLOCKED
        pl.reason = "Chưa có dòng hàng hóa mua nào."
        pl.missing = ("Chưa có dòng hàng hóa mua nào,",)
        hdnt.state = BLOCKED
        hdnt.reason = "Chưa có dòng hàng hóa mua nào."
        hdnt.missing = ("Chưa có dòng hàng hóa mua nào,",)

    pxk = _pxk_readiness(delivery_completed=delivery_completed, source_line_count=line_count)
    return {
        HDNT: hdnt,
        PL: pl,
        HDMB: hdmb,
        PXK: pxk,
    }


def _pxk_readiness(*, delivery_completed: bool, source_line_count: int) -> Readiness:
    if not delivery_completed:
        return _blocked(
            "PXK chỉ phát hành khi DELIVERY_COMPLETED = TRUE.",
            document_type=PXK,
            detail="Ngày dự kiến giao hàng không phải là ngày giao thực tế.",
        )
    if source_line_count != 1:
        return _blocked(
            "PXK V1 yêu cầu đúng 1 dòng hàng từ nguồn đã chọn.",
            document_type=PXK,
            detail="Chọn nguồn HDMB hoặc PL có đúng 1 dòng hàng.",
        )
    return _ready("Áp dụng: giao hàng đã hoàn tất và có đúng 1 dòng hàng từ nguồn.", document_type=PXK)


def evaluate_document_readiness(
    document_type: str,
    *,
    goods_lines: list[Mapping[str, Any]],
    agent: Mapping[str, Any] | None,
    company: Mapping[str, Any] | None,
    parent_contract: Mapping[str, Any] | None = None,
    selected_contract: Mapping[str, Any] | None = None,
    delivery_completed: bool = False,
) -> Readiness:
    """Run the targeted preflight for one document type.

    Preflight order: supported -> applicable -> authoritative source ->
    required fields -> semantic validation.
    """
    if document_type not in DOCUMENT_TYPES:
        return Readiness(document_type=document_type, state=OWNER_RULE_REQUIRED, reason="Loại chứng từ chưa được hỗ trợ.")

    applicability = decide_applicable_documents(
        goods_lines=goods_lines,
        currency=(selected_contract or {}).get("currency") or VND_CURRENCY,
        delivery_completed=delivery_completed,
    )
    base = applicability[document_type]
    if base.state == NOT_APPLICABLE or base.state == BLOCKED:
        return base

    missing: list[str] = []
    if document_type in (HDNT, PL, HDMB):
        missing.extend(_authority_missing(agent, company))
    if not goods_lines:
        missing.append("Chưa có dòng hàng hóa mua.")
    if document_type == PL:
        if parent_contract is None:
            return Readiness(document_type=PL, state=BLOCKED, reason="PL cần một Hợp đồng nguyên tắc (HDNT) cha hợp lệ.", missing=("Thiếu HDNT cha,",))
        if not _same_agent_company(parent_contract, agent, company):
            return Readiness(
                document_type=PL,
                state=BLOCKED,
                reason="PL và HDNT cha không cùng Đại lý / Công ty.",
                missing=("Đối tác của PL không khớp HDNT cha,",),
            )
        if parent_contract.get("kind") != HDNT:
            return Readiness(document_type=PL, state=BLOCKED, reason="HDNT cha phải là hợp đồng nguyên tắc.")
    if document_type == HDNT:
        if agent is None or company is None:
            missing.append("Thiếu hồ sơ pháp lý Đại lý / Công ty.")

    if missing:
        return Readiness(
            document_type=document_type,
            state=MISSING_INFO,
            reason=f"Thiếu {len(missing)} thông tin để xuất {document_type}.",
            missing=tuple(missing),
            applicable=True,
        )
    return Readiness(
        document_type=document_type,
        state=READY,
        reason=f"Sẵn sàng xuất {document_type}.",
        applicable=True,
    )


def _authority_missing(agent: Mapping[str, Any] | None, company: Mapping[str, Any] | None) -> list[str]:
    missing: list[str] = []
    if not agent:
        missing.append("Thiếu hồ sơ pháp lý Đại lý (bên bán).")
    else:
        for field in ("legal_name", "legal_address", "legal_code", "legal_representative", "representative_title"):
            if not str(agent.get(field) or "").strip():
                missing.append(f"Thiếu {field} của Đại lý.")
    if not company:
        missing.append("Thiếu hồ sơ pháp lý Công ty.")
    else:
        for field in ("legal_name", "legal_address", "tax_or_legal_code", "legal_representative", "representative_title"):
            if not str(company.get(field) or "").strip():
                missing.append(f"Thiếu {field} của Công ty.")
    return missing


def _same_agent_company(parent: Mapping[str, Any], agent: Mapping[str, Any] | None, company: Mapping[str, Any] | None) -> bool:
    if agent is None or company is None:
        return False
    agent_id = str(agent.get("agent_id") or agent.get("id") or "").strip().upper()
    company_id = str(company.get("company_id") or company.get("id") or "").strip().upper()
    parent_agent = str(parent.get("agent_id") or "").strip().upper()
    parent_company = str(parent.get("company_id") or "").strip().upper()
    return bool(agent_id) and agent_id == parent_agent and bool(company_id) and company_id == parent_company


def _ready(reason: str, document_type: str = "") -> Readiness:
    return Readiness(document_type=document_type, state=READY, reason=reason, applicable=True)


def _not_applicable(reason: str, document_type: str = "", detail: str = "") -> Readiness:
    return Readiness(document_type=document_type, state=NOT_APPLICABLE, reason=reason, applicable=False)


def _blocked(reason: str, document_type: str = "", detail: str = "") -> Readiness:
    return Readiness(document_type=document_type, state=BLOCKED, reason=reason, missing=(detail,) if detail else ())
