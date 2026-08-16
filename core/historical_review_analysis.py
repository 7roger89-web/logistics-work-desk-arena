"""Deterministic business review analysis for the LOG-C06 staging phase.

This module consumes staged item dictionaries and returns derived evidence only.  It does
not mutate source items, change review status, write a database, or decide confirmation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from core.historical_owner_reconciliation import build_owner_reconciliation
from core.historical_staging import UNKNOWN_CURRENCY, normalize_text


ANALYSIS_VERSION = "log-c06-owner-review-v2"
READY_FOR_OWNER_CONFIRMATION = "READY_FOR_OWNER_CONFIRMATION"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
UNKNOWN = "UNKNOWN"
NOT_APPLICABLE = "NOT_APPLICABLE"
CHECKPOINT_LOOKBACK_ROWS = 40

GOLDEN_SOURCE_ROWS = (16, 102, 109, 96, 99, 129)
GOLDEN_EXPECTED_AMOUNTS = {
    16: Decimal("24576"),
    102: Decimal("62464"),
    109: Decimal("1687"),
    96: Decimal("1572"),
    99: Decimal("25025"),
    129: Decimal("134973"),
}

CLUSTER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "CHECKPOINT_OR_SUMMARY": {
        "label": "Checkpoint / tổng thủ công",
        "rule_resolution": "Một quyết định về bộ dòng thành phần có thể xử lý cả nhóm; không xác nhận dòng tổng như một khoản tiền riêng.",
        "owner_question": "Các dòng thành phần nào thực sự tạo ra checkpoint, và dòng tổng có phải chỉ là summary không?",
        "one_owner_rule": True,
    },
    "FX_CONTEXT": {
        "label": "Dòng quy đổi / tỷ giá",
        "rule_resolution": "Giữ riêng từng money leg; không dùng dòng quy đổi như khoản thu/chi độc lập.",
        "owner_question": "Dòng này là context quy đổi hay có một money leg thực sự cần đưa vào vị trí A Bò?",
        "one_owner_rule": True,
    },
    "LIKELY_DUPLICATE": {
        "label": "Có khả năng trùng",
        "rule_resolution": "Có thể áp dụng rule không cộng dòng lặp, nhưng cần giữ source row để Owner xác nhận cặp nào trùng.",
        "owner_question": "Dòng nào là bản ghi lặp/summary và dòng nào là khoản tiền thật?",
        "one_owner_rule": False,
    },
    "MISSING_OR_UNCERTAIN_CURRENCY": {
        "label": "Thiếu hoặc chưa chắc currency",
        "rule_resolution": "Không ép currency từ vị trí cột hoặc số học; cần evidence business cho từng nhóm currency.",
        "owner_question": "Các dòng này là CNY, USD, VND hay một đơn vị khác theo source evidence?",
        "one_owner_rule": False,
    },
    "EXPLICIT_SALE_MISSING_PARTY": {
        "label": "SALE Thành rõ nhưng thiếu bên chuyển/nhận",
        "rule_resolution": "Có thể giữ SALE Thành, nhưng không tự gán source party hoặc allocation.",
        "owner_question": "Tiền đến từ ai/đang ở đâu và có liên quan A Bò không?",
        "one_owner_rule": False,
    },
    "CUSTOMER_RECEIPT_LEG": {
        "label": "Tiền khách vào tài khoản TT",
        "rule_resolution": "Giữ đây là money leg khách trả vào TT; không biến thành khoản A Bò trả/nhận nếu chưa có link.",
        "owner_question": "Có liên quan đến vị trí A Bò không, hay chỉ giữ như receipt leg của TT?",
        "one_owner_rule": True,
    },
    "RECEIVED_ON_BEHALF": {
        "label": "Nhận hộ / tiền đang được giữ hộ",
        "rule_resolution": "Có thể gom theo người hưởng được ghi rõ; shipment/allocation vẫn phải có Owner nếu source chưa nêu.",
        "owner_question": "A Bò có thực sự giữ hộ cho Thành/đối tượng này không, và phân bổ vào shipment nào?",
        "one_owner_rule": False,
    },
    "PAID_ON_BEHALF": {
        "label": "Thanh toán hộ",
        "rule_resolution": "Giữ money leg thanh toán hộ; explicit SALE có thể làm sẵn sàng cho Owner confirm nhưng không tự confirm.",
        "owner_question": "Khoản thanh toán hộ này thuộc Thành hay owner khác, và có allocation nào không?",
        "one_owner_rule": False,
    },
    "EXPLICIT_SALE_MISSING_EVENT": {
        "label": "SALE Thành rõ nhưng chưa rõ ý nghĩa khoản tiền",
        "rule_resolution": "Giữ SALE explicit, không ép event hoặc bucket từ số tiền.",
        "owner_question": "Đây là tiền nhận hộ, thanh toán hộ, công nợ hay một summary khác?",
        "one_owner_rule": False,
    },
    "FREE_TEXT_OWNER_ONLY": {
        "label": "Chỉ có chữ Thành trong ghi chú tự do",
        "rule_resolution": "Không coi free text là SALE/owner confirmation.",
        "owner_question": "Có bằng chứng explicit nào xác nhận owner Thành ngoài ghi chú tự do không?",
        "one_owner_rule": False,
    },
    "INHERITED_DATE_ONLY": {
        "label": "Chỉ thừa kế ngày từ dòng trước",
        "rule_resolution": "Giữ ngày context để tìm kiếm, không dùng làm ngày giao dịch chắc chắn.",
        "owner_question": "Ngày thực của khoản tiền là ngày nào, và có thay đổi ý nghĩa opening không?",
        "one_owner_rule": False,
    },
    "MATERIAL_AMBIGUITY": {
        "label": "Mơ hồ về business meaning",
        "rule_resolution": "Không gom thành một rule tài chính; cần Owner quyết định theo source evidence từng cụm nhỏ.",
        "owner_question": "Khoản này thực sự là tiền gì, của ai, đang ở đâu và liên quan shipment/customer nào?",
        "one_owner_rule": False,
    },
}


_GOLDEN_BUSINESS: dict[int, dict[str, Any]] = {
    16: {
        "title": "A Bò còn phải trả 24,576 CNY",
        "money_from": "Lục Giác / dòng chuyển USD được quy đổi sang CNY",
        "money_location": "374,306 CNY tương đương; 349,730 CNY đã chuyển; phần còn lại được ghi là A Bò phải trả",
        "business_meaning": "Workbook ghi rõ phần chênh còn lại là nghĩa vụ A Bò phải trả, và phép tính 374,306 - 349,730 = 24,576.",
        "shipment_or_customer": "Lục Giác; shipment cụ thể không được ghi rõ trong dòng này",
        "certainty": "Cao về câu chữ và arithmetic; vẫn cần Owner xác nhận đây là khoản opening của TT chứ không phải summary/duplicate.",
        "owner_question": "Xác nhận 24,576 CNY là khoản A Bò còn phải trả TT và không phải dòng summary đã được ghi ở nơi khác.",
        "recommendation": "READY_FOR_OWNER_CONFIRMATION: giữ như ứng viên nghĩa vụ A Bò ↔ TT; chưa đưa vào opening.",
        "decision_effect": "Nếu Owner xác nhận, có thể tạo một component CNY có source row 16; hướng nghĩa vụ vẫn phải giữ đúng business meaning.",
    },
    102: {
        "title": "62,464 CNY nhận hộ cho Thành",
        "money_from": "Xưởng đồ chơi Thành Vũ / nhà máy đồ chơi theo ghi chú gốc",
        "money_location": "Ghi là nhận hộ qua A Bò; workbook không chỉ rõ tài khoản thực tế hoặc shipment đích.",
        "business_meaning": "Ghi chú nói nhà máy đồ chơi chuyển món tiền cho Thành; A Bò được mô tả là bên nhận hộ.",
        "shipment_or_customer": "Xưởng đồ chơi Thành Vũ; shipment cụ thể chưa xác định",
        "certainty": "Cao về nguồn và mục đích chuyển cho Thành; chưa đủ để xác định allocation.",
        "owner_question": "Xác nhận A Bò đang giữ hộ cho Thành và cho biết khoản này thuộc shipment/customer nào nếu có.",
        "recommendation": "READY_FOR_OWNER_CONFIRMATION: giữ như tiền nhận hộ cho Thành; chưa phân bổ shipment.",
        "decision_effect": "Nếu xác nhận, có thể tạo component CNY dạng nhận hộ/đang giữ hộ, không tự biến thành công nợ khách hàng.",
    },
    109: {
        "title": "1,687 CNY Lục Giác thanh toán cho Thành",
        "money_from": "Nhà máy Lục Giác",
        "money_location": "Ghi là nhận hộ; khoản được mô tả là nhà máy thanh toán tiền vận chuyển cho Thành.",
        "business_meaning": "SALE Thành explicit và ghi chú gốc nói Lục Giác thanh toán cho Thành; đây là money leg nhận hộ liên quan freight/VC.",
        "shipment_or_customer": "Lục Giác; freight/VC, shipment cụ thể chưa xác định",
        "certainty": "Cao về owner candidate và nguồn; allocation shipment chưa rõ.",
        "owner_question": "Xác nhận khoản này thuộc Thành và có cần gắn vào shipment/freight nào không.",
        "recommendation": "READY_FOR_OWNER_CONFIRMATION: giữ như khoản nhận hộ cho Thành; chưa phân bổ.",
        "decision_effect": "Nếu xác nhận, có thể tạo component CNY nhận hộ cho Thành, không cộng với checkpoint 134,973.",
    },
    96: {
        "title": "1,572 CNY thanh toán cho nhà máy Đà Lạt",
        "money_from": "Kế toán / nhà máy Đà Lạt theo ghi chú gốc",
        "money_location": "Ghi là kế toán đã chuyển tiền; workbook không nói rõ A Bò đang giữ hay khoản đã settled ở đâu.",
        "business_meaning": "Có event thanh toán tiền hàng cho nhà máy Đà Lạt, nhưng “món của Thành” chỉ xuất hiện trong ghi chú tự do, không có SALE explicit.",
        "shipment_or_customer": "Nhà máy Đà Lạt; shipment cụ thể chưa xác định",
        "certainty": "Thấp đến trung bình; còn inherited date và thiếu SALE explicit.",
        "owner_question": "Xác nhận owner Thành và quan hệ A Bò của khoản này; không dùng chữ “món của Thành” một mình để confirm.",
        "recommendation": "REVIEW_REQUIRED / UNKNOWN: không tự đưa vào opening.",
        "decision_effect": "Chưa có effect trong draft; chỉ mở component sau khi Owner xác nhận owner và money leg.",
    },
    99: {
        "title": "25,025 CNY tiền khách vào tài khoản TT",
        "money_from": "Khách hàng của B&G Green",
        "money_location": "Vào tài khoản Trường Thành theo ghi chú gốc; không có bằng chứng A Bò đã nhận hoặc đã trả beneficiary.",
        "business_meaning": "Đây là customer receipt leg cho B&G Green. Receipt leg không tự chứng minh nghĩa vụ giữa A Bò và Thành.",
        "shipment_or_customer": "B&G Green; shipment cụ thể chưa xác định",
        "certainty": "Cao về việc khách đã trả vào TT; thấp về liên hệ với opening A Bò.",
        "owner_question": "Giữ như receipt leg riêng hay có evidence nào nối khoản này vào vị trí A Bò?",
        "recommendation": "READY_FOR_OWNER_CONFIRMATION: giữ riêng receipt leg; không map sang A Bò nếu chưa có link.",
        "decision_effect": "Nếu chỉ xác nhận receipt leg, opening A Bò không đổi; chỉ khi có link business rõ mới tạo component liên quan.",
    },
    129: {
        "title": "134,973 CNY checkpoint / tổng của Thành",
        "money_from": "Summary line do workbook ghi “CỦA THÀNH”",
        "money_location": "Đây là dòng tổng thủ công; không phải bằng chứng một lần tiền mới phát sinh.",
        "business_meaning": "Có exact candidate sum từ các dòng BG GREEN, ABING, Lục Giác, khung tranh Đà Lạt, Alipay và bank; row 129 nên được giữ như checkpoint.",
        "shipment_or_customer": "Nhiều counterparty; allocation từng dòng vẫn tách riêng",
        "certainty": "Cao về arithmetic candidate; trung bình về việc bộ dòng này là đúng business scope của checkpoint.",
        "owner_question": "Xác nhận bộ component rows được đề xuất và xác nhận row 129 chỉ là summary, không cộng thêm lần nữa.",
        "recommendation": "READY_FOR_OWNER_CONFIRMATION: quyết định component set; không confirm checkpoint như khoản tiền độc lập.",
        "decision_effect": "Nếu xác nhận bộ component, các component mới có thể được review riêng; row 129 vẫn bị loại khỏi opening để tránh double count.",
    },
}


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _amount(item: Mapping[str, Any]) -> Decimal | None:
    proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
    return _decimal(proposal.get("amount", item.get("raw_amount")))


def _currency(item: Mapping[str, Any]) -> str:
    proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
    return str(proposal.get("currency") or item.get("raw_currency") or UNKNOWN_CURRENCY).upper()


def _proposal(item: Mapping[str, Any]) -> Mapping[str, Any]:
    proposal = item.get("proposal")
    return proposal if isinstance(proposal, Mapping) else {}


def _normalized_text(item: Mapping[str, Any]) -> str:
    return normalize_text(item.get("raw_text") or "")


def _has_explicit_sale(item: Mapping[str, Any]) -> bool:
    return _proposal(item).get("sale_evidence") == "explicit_sale_field"


def _cluster_key(item: Mapping[str, Any]) -> str:
    proposal = _proposal(item)
    flags = set(item.get("anomaly_flags") or [])
    event_type = str(proposal.get("event_type") or "")
    sale_evidence = str(proposal.get("sale_evidence") or "")
    if proposal.get("checkpoint_key") or event_type == "adjustment" or "CHECKPOINT_EVIDENCE" in flags:
        return "CHECKPOINT_OR_SUMMARY"
    if event_type == "fx_conversion_context" or proposal.get("fx_rate") or proposal.get("related_currency"):
        return "FX_CONTEXT"
    if "DUPLICATE_LOOKING" in flags:
        return "LIKELY_DUPLICATE"
    if _currency(item) == UNKNOWN_CURRENCY:
        return "MISSING_OR_UNCERTAIN_CURRENCY"
    if _has_explicit_sale(item) and "MISSING_SOURCE_PARTY" in flags:
        return "EXPLICIT_SALE_MISSING_PARTY"
    if event_type == "customer_receipt":
        return "CUSTOMER_RECEIPT_LEG"
    if event_type == "received_on_behalf":
        return "RECEIVED_ON_BEHALF"
    if event_type == "paid_on_behalf":
        return "PAID_ON_BEHALF"
    if _has_explicit_sale(item) and event_type == "unknown":
        return "EXPLICIT_SALE_MISSING_EVENT"
    if sale_evidence == "free_text_only":
        return "FREE_TEXT_OWNER_ONLY"
    if "INHERITED_DATE_CONTEXT" in flags:
        return "INHERITED_DATE_ONLY"
    return "MATERIAL_AMBIGUITY"


def classify_review_cluster(item: Mapping[str, Any]) -> str:
    """Return one deterministic review cluster for a staged item."""

    return _cluster_key(item)


def _source_reference(item: Mapping[str, Any]) -> str:
    return str(item.get("source_reference") or f"{item.get('sheet')}!row {item.get('source_row')}")


def _source_row(item: Mapping[str, Any]) -> int:
    try:
        return int(item.get("source_row") or 0)
    except (TypeError, ValueError):
        return 0


def _scaled(value: Decimal) -> int:
    return int((value * Decimal("1000000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _mentions_thanh(item: Mapping[str, Any]) -> bool:
    text = _normalized_text(item)
    proposal = _proposal(item)
    return "thanh" in text or str(proposal.get("candidate_internal_sale_owner") or "").casefold() == "thành"


def _candidate_pool(items: list[Mapping[str, Any]], checkpoint: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    checkpoint_sheet = str(checkpoint.get("sheet") or "")
    checkpoint_row = _source_row(checkpoint)
    expected_currency = _currency(checkpoint)
    checkpoint_proposal = _proposal(checkpoint)
    explicitly_linked_ids = {
        str(source_id)
        for source_id in (checkpoint_proposal.get("checkpoint_component_ids") or [])
        if str(source_id)
    }
    candidates: list[Mapping[str, Any]] = []
    for item in items:
        if str(item.get("sheet") or "") != checkpoint_sheet:
            continue
        if explicitly_linked_ids and str(item.get("source_item_id") or "") not in explicitly_linked_ids:
            continue
        explicitly_linked = str(item.get("source_item_id") or "") in explicitly_linked_ids
        row = _source_row(item)
        if row >= checkpoint_row or row < checkpoint_row - CHECKPOINT_LOOKBACK_ROWS:
            continue
        proposal = _proposal(item)
        amount = _amount(item)
        event_type = str(proposal.get("event_type") or "")
        if amount is None or amount <= 0 or _currency(item) != expected_currency:
            continue
        if proposal.get("sale_evidence") != "explicit_sale_field" and not explicitly_linked:
            continue
        if event_type in {"adjustment", "received_on_behalf", "customer_receipt", "fx_conversion_context"}:
            continue
        if item.get("review_status") == NOT_APPLICABLE:
            continue
        candidates.append(item)
    return sorted(candidates, key=lambda item: (_source_row(item), str(item.get("source_item_id") or "")))


def _exact_subsets(candidates: list[Mapping[str, Any]], expected: Decimal) -> list[tuple[str, ...]]:
    target = _scaled(expected)
    states: dict[int, list[tuple[str, ...]]] = {0: [()]}
    for candidate in candidates:
        amount = _amount(candidate)
        source_id = str(candidate.get("source_item_id") or "")
        if amount is None or not source_id:
            continue
        scaled_amount = _scaled(amount)
        if scaled_amount <= 0 or scaled_amount > target:
            continue
        # Build a fresh state map for each candidate.  Mutating a list that is
        # also present in the current snapshot would let one candidate be
        # selected twice when its new total is another current total.
        snapshot = {total: tuple(combinations) for total, combinations in states.items()}
        next_states = {total: list(combinations) for total, combinations in states.items()}
        for current_total, combinations in snapshot.items():
            next_total = current_total + scaled_amount
            if next_total > target:
                continue
            existing = next_states.setdefault(next_total, [])
            for combination in combinations[:8]:
                proposal = tuple(sorted((*combination, source_id)))
                if proposal not in existing and len(existing) < 8:
                    existing.append(proposal)
        states = next_states
    return sorted(set(states.get(target, [])))


def reconstruct_checkpoint_candidates(
    items: Iterable[Mapping[str, Any]],
    *,
    checkpoint_row: int = 129,
    sheet: str = "Sheet2",
) -> dict[str, Any] | None:
    """Find an exact arithmetic candidate set without changing checkpoint semantics."""

    rows = [dict(item) for item in items]
    checkpoint = next(
        (
            item
            for item in rows
            if str(item.get("sheet") or "") == sheet and _source_row(item) == checkpoint_row
        ),
        None,
    )
    if checkpoint is None:
        return None
    expected = _amount(checkpoint)
    if expected is None:
        return {
            "checkpoint_source_reference": _source_reference(checkpoint),
            "status": "UNKNOWN_SEMANTICS",
            "reason": "Checkpoint amount is unresolved.",
            "component_source_item_ids": [],
        }
    candidates = _candidate_pool(rows, checkpoint)
    solutions = _exact_subsets(candidates, expected)
    candidate_by_id = {str(item.get("source_item_id")): item for item in candidates}
    chosen_ids = list(solutions[0]) if len(solutions) == 1 else []
    chosen_ids.sort(
        key=lambda source_id: (
            _source_row(candidate_by_id[source_id]),
            source_id,
        )
    )
    component_amount = sum((_amount(candidate_by_id[source_id]) or Decimal("0") for source_id in chosen_ids), Decimal("0"))
    candidate_components = [
        {
            "source_item_id": source_id,
            "source_reference": _source_reference(candidate_by_id[source_id]),
            "source_row": _source_row(candidate_by_id[source_id]),
            "amount": _float(_amount(candidate_by_id[source_id])),
            "currency": _currency(candidate_by_id[source_id]),
        }
        for source_id in chosen_ids
    ]
    excluded_candidates = []
    for candidate in candidates:
        source_id = str(candidate.get("source_item_id") or "")
        if source_id not in chosen_ids:
            excluded_candidates.append(
                {
                    "source_reference": _source_reference(candidate),
                    "source_row": _source_row(candidate),
                    "amount": _float(_amount(candidate)),
                    "reason": "NOT_IN_UNIQUE_EXACT_MATCH",
                }
            )
    context_exclusions = []
    for item in rows:
        if str(item.get("sheet") or "") != sheet:
            continue
        row = _source_row(item)
        if row >= checkpoint_row or row < checkpoint_row - CHECKPOINT_LOOKBACK_ROWS:
            continue
        amount = _amount(item)
        if amount is None or amount <= 0 or _currency(item) != _currency(checkpoint):
            continue
        proposal = _proposal(item)
        if proposal.get("sale_evidence") == "explicit_sale_field" and str(proposal.get("event_type") or "") in {
            "received_on_behalf",
            "fx_conversion_context",
        }:
            context_exclusions.append(
                {
                    "source_reference": _source_reference(item),
                    "source_row": row,
                    "amount": _float(amount),
                    "reason": "SEPARATE_MONEY_LEG_NOT_CHECKPOINT_COMPONENT",
                }
            )
    if len(solutions) == 1 and component_amount == expected:
        status = "EXACT_MATCH_CANDIDATE"
        reason = "Unique exact sum found in bounded source context; Owner must confirm business scope before any component can be confirmed."
    elif len(solutions) > 1:
        status = "MULTIPLE_EXACT_MATCHES"
        reason = "More than one exact candidate set exists; arithmetic alone cannot choose the business set."
    else:
        status = "NO_EXACT_MATCH"
        reason = "No exact candidate set was found in the bounded source context."
    return {
        "checkpoint_source_item_id": checkpoint.get("source_item_id"),
        "checkpoint_source_reference": _source_reference(checkpoint),
        "checkpoint_row": checkpoint_row,
        "checkpoint_amount": _float(expected),
        "currency": _currency(checkpoint),
        "operation": "sum",
        "candidate_source_item_ids": chosen_ids,
        "candidate_source_references": [
            _source_reference(candidate_by_id[source_id]) for source_id in chosen_ids
        ],
        "candidate_rows": [_source_row(candidate_by_id[source_id]) for source_id in chosen_ids],
        "candidate_components": candidate_components,
        "candidate_component_amount": _float(component_amount),
        "difference": _float(component_amount - expected),
        "candidate_count": len(candidates),
        "exact_solution_count": len(solutions),
        "excluded_candidate_rows": excluded_candidates,
        "context_exclusion_rows": context_exclusions,
        "status": status,
        "reason": reason,
        "checkpoint_is_not_component": True,
        "double_count_guard": {
            "checkpoint_id_excluded_from_components": checkpoint.get("source_item_id") not in chosen_ids,
            "checkpoint_must_not_enter_opening": True,
        },
    }


def _owner_confirmed_business(item: Mapping[str, Any], row: int) -> dict[str, Any]:
    """Return business-facing wording after the explicit Owner batch is applied."""

    proposal = _proposal(item)
    if row == 16:
        return {
            "title": "24,576 CNY — credit embedded in 99,824.43 checkpoint",
            "money_from": "Lục Giác / USD transfer conversion",
            "money_location": "Historical credit/reduction already contained in the 99,824.43 checkpoint.",
            "business_meaning": "A Bò must return/credit 24,576 CNY to Thành; this is not a second opening subtraction.",
            "shipment_or_customer": "Lục Giác; shipment unresolved",
            "certainty": "Owner confirmed; embedded snapshot lineage is explicit.",
            "owner_question": "No new semantic question; keep the snapshot lineage intact.",
            "recommendation": "APPLIED_TO_STAGING: exclude as a standalone opening event.",
            "decision_effect": "Confirmed source component, excluded from standalone opening because 99,824.43 already contains it.",
        }
    if row == 102:
        return {
            "title": "62,464 CNY — received on behalf for Thành",
            "money_from": "Toy factory / Thành Vũ",
            "money_location": "Held/received through A Bò for Thành; shipment allocation remains unresolved.",
            "business_meaning": "A Bò received money on behalf of Thành; it reduces Thành's debt to A Bò.",
            "shipment_or_customer": "Toy factory / Thành Vũ; no forced shipment id",
            "certainty": "Owner confirmed; source party is preserved and allocation is unallocated.",
            "owner_question": "No further semantic question for this row; shipment linkage is optional evidence.",
            "recommendation": "APPLIED_TO_STAGING: separate received-on-behalf event.",
            "decision_effect": "Included in the confirmed CNY received-on-behalf bucket; not merged with 1,687 CNY.",
        }
    if row == 109:
        return {
            "title": "1,687 CNY — Lục Giác freight received on behalf",
            "money_from": "Lục Giác factory",
            "money_location": "Received/held through A Bò for Thành; freight context retained.",
            "business_meaning": "A Bò received a separate freight payment on behalf of Thành.",
            "shipment_or_customer": "Lục Giác freight; shipment unresolved",
            "certainty": "Owner confirmed; separate event and no invented shipment id.",
            "owner_question": "No further semantic question; preserve unresolved shipment allocation.",
            "recommendation": "APPLIED_TO_STAGING: separate received-on-behalf event.",
            "decision_effect": "Included separately in the confirmed CNY received-on-behalf bucket.",
        }
    if row == 99:
        return {
            "title": "25,025 CNY — B&G Green paid on behalf",
            "money_from": "A Bò paid/transferred on behalf for Thành",
            "money_location": "Paid-on-behalf leg is separate from customer money entering Trường Thành.",
            "business_meaning": "The A Bò → B&G Green leg increases Thành's debt to A Bò; the customer receipt does not settle it.",
            "shipment_or_customer": "B&G Green; shipment unresolved",
            "certainty": "Owner confirmed; both money legs are preserved separately.",
            "owner_question": "No new semantic question; settlement/allocation evidence may be added later.",
            "recommendation": "APPLIED_TO_STAGING: paid-on-behalf component of the 159,998 CNY group.",
            "decision_effect": "Included in the confirmed paid-on-behalf group; receipt leg cannot close the A Bò obligation.",
        }
    if row == 129:
        return {
            "title": "134,973 CNY — confirmed component checkpoint",
            "money_from": "Workbook summary of 11 Thành paid-on-behalf components",
            "money_location": "Summary/checkpoint only; not an additional money event.",
            "business_meaning": "The 11 component rows sum exactly to 134,973 CNY; row 129 is excluded from opening.",
            "shipment_or_customer": "Multiple counterparties; each source row remains separate",
            "certainty": "Owner confirmed; component lineage and summary exclusion are explicit.",
            "owner_question": "No new semantic question; do not add row 129 to its components.",
            "recommendation": "APPLIED_TO_STAGING: retain as a reconciled summary checkpoint.",
            "decision_effect": "The 11 components contribute to the derived 159,998 CNY group; row 129 itself contributes zero.",
        }
    if row in {115, 190, 197, 198}:
        return {
            "title": f"C{row} — received-on-behalf group component",
            "money_from": "Historical received group source cell",
            "money_location": "A Bò received/held the CNY component for Thành; allocation remains unallocated.",
            "business_meaning": "Owner confirmed this source cell as part of the separate 416,482.2426005565 received group.",
            "shipment_or_customer": "Shipment/customer unresolved",
            "certainty": "Owner confirmed group membership; source arithmetic still differs from the checkpoint expectation.",
            "owner_question": "Only the remaining group arithmetic difference needs reconciliation.",
            "recommendation": "APPLIED_TO_STAGING: keep as a separate received-on-behalf event.",
            "decision_effect": "Included in source-component total; not merged with paid-on-behalf rows.",
        }
    return {}


def _business_fields(item: Mapping[str, Any], cluster_key: str, checkpoint: Mapping[str, Any] | None) -> dict[str, Any]:
    row = _source_row(item)
    proposal = _proposal(item)
    amount = _amount(item)
    currency = _currency(item)
    generic = {
        "money_from": str(proposal.get("source") or proposal.get("payer") or "Chưa xác định trong workbook"),
        "money_location": "Workbook chưa chỉ rõ tiền đang ở tài khoản/vị trí nào.",
        "business_meaning": "Workbook có số tiền hoặc ghi chú liên quan nhưng chưa đủ bằng chứng để chọn business meaning duy nhất.",
        "shipment_or_customer": str(proposal.get("customer") or proposal.get("source") or "Chưa xác định trong workbook"),
        "certainty": "Chưa đủ chắc chắn để tự xác nhận.",
        "owner_question": CLUSTER_DEFINITIONS[cluster_key]["owner_question"],
        "recommendation": "Giữ trong staging để Owner quyết định.",
        "decision_effect": "Không tạo component opening khi chưa có CONFIRMED action.",
    }
    if row in _GOLDEN_BUSINESS:
        fields = dict(_GOLDEN_BUSINESS[row])
        if _proposal(item).get("owner_decision_status") == "CONFIRMED":
            fields.update(_owner_confirmed_business(item, row))
        return fields
    event_type = str(proposal.get("event_type") or "")
    normalized = _normalized_text(item)
    if event_type == "customer_receipt":
        generic.update(
            {
                "money_location": "Tài khoản Trường Thành theo ghi chú gốc; chưa có link sang A Bò.",
                "business_meaning": "Đây là money leg khách trả vào TT, không tự chứng minh TT đã trả A Bò hay beneficiary.",
                "certainty": "Cao về receipt leg; thấp về liên hệ với opening A Bò.",
            }
        )
    elif event_type == "received_on_behalf":
        generic.update(
            {
                "money_location": "A Bò được ghi là bên nhận hộ/đang giữ hộ; tài khoản cụ thể chưa có.",
                "business_meaning": "Đối tác/nhà máy được ghi là chuyển tiền nhận hộ; owner hưởng hoặc allocation chưa luôn rõ.",
                "certainty": "Cao nếu raw note chỉ rõ người hưởng; trung bình nếu chỉ có pattern nhận hộ.",
            }
        )
        if "thanh" in normalized:
            generic["business_meaning"] = "Raw note có chỉ dấu tiền chuyển cho Thành; A Bò có thể là bên nhận hộ, nhưng shipment/allocation chưa rõ."
    elif event_type == "paid_on_behalf":
        generic.update(
            {
                "money_location": "Ghi là đã chuyển/thanh toán cho nhà máy hoặc đối tác; settlement location cụ thể chưa có.",
                "business_meaning": "Đây là money leg thanh toán hộ; không tự biến thành khoản Thành sở hữu nếu thiếu SALE/evidence tương ứng.",
                "certainty": "Cao về event thanh toán hộ; owner/allocation phụ thuộc SALE và source party.",
            }
        )
    elif event_type == "fx_conversion_context":
        generic.update(
            {
                "money_location": "Dòng quy đổi giữa VND và CNY; không phải một money leg độc lập nếu source không nói vậy.",
                "business_meaning": "Giữ context tỷ giá và amount liên quan; không cộng dòng quy đổi thêm một lần.",
                "certainty": "Cao về arithmetic FX context; thấp về việc có phải khoản opening độc lập không.",
            }
        )
    elif cluster_key == "CHECKPOINT_OR_SUMMARY":
        generic.update(
            {
                "money_location": "Dòng tổng/checkpoint thủ công trong workbook.",
                "business_meaning": "Không coi là một lần tiền mới phát sinh; cần xác định component set và loại summary khỏi opening.",
                "certainty": "Chỉ chắc về việc đây là summary/checkpoint.",
            }
        )
    if amount is not None and currency != UNKNOWN_CURRENCY:
        generic["decision_effect"] = f"Nếu Owner xác nhận đúng business meaning, có thể xem xét component {amount} {currency}; hiện chưa đưa vào opening."
    return generic


def _owner_review_state(item: Mapping[str, Any], cluster_key: str, checkpoint: Mapping[str, Any] | None) -> str:
    status = str(item.get("review_status") or "RAW")
    if status == NOT_APPLICABLE:
        return NOT_APPLICABLE
    if status == "CONFIRMED":
        return "CONFIRMED"
    if status == "REJECTED":
        return "REJECTED"
    if cluster_key == "CHECKPOINT_OR_SUMMARY":
        return READY_FOR_OWNER_CONFIRMATION if checkpoint and checkpoint.get("status") == "EXACT_MATCH_CANDIDATE" else REVIEW_REQUIRED
    if _source_row(item) in {16, 109} and _currency(item) != UNKNOWN_CURRENCY:
        return READY_FOR_OWNER_CONFIRMATION
    proposal = _proposal(item)
    has_source = bool(proposal.get("source") or proposal.get("payer"))
    if cluster_key == "CUSTOMER_RECEIPT_LEG" and has_source and _currency(item) != UNKNOWN_CURRENCY:
        return READY_FOR_OWNER_CONFIRMATION
    if cluster_key == "RECEIVED_ON_BEHALF" and has_source and _mentions_thanh(item) and _currency(item) != UNKNOWN_CURRENCY:
        return READY_FOR_OWNER_CONFIRMATION
    if cluster_key == "PAID_ON_BEHALF" and _has_explicit_sale(item) and has_source and _currency(item) != UNKNOWN_CURRENCY:
        return READY_FOR_OWNER_CONFIRMATION
    if cluster_key in {"LIKELY_DUPLICATE", "MISSING_OR_UNCERTAIN_CURRENCY", "MATERIAL_AMBIGUITY"}:
        return UNKNOWN
    return REVIEW_REQUIRED


def _derived_row(item: Mapping[str, Any], checkpoint: Mapping[str, Any] | None) -> dict[str, Any]:
    cluster_key = _cluster_key(item)
    fields = _business_fields(item, cluster_key, checkpoint)
    return {
        "source_item_id": item.get("source_item_id"),
        "source_reference": _source_reference(item),
        "sheet": item.get("sheet"),
        "source_row": _source_row(item),
        "amount": _float(_amount(item)),
        "currency": _currency(item),
        "current_review_status": item.get("review_status") or "RAW",
        "owner_review_state": _owner_review_state(item, cluster_key, checkpoint),
        "cluster_key": cluster_key,
        "cluster_label": CLUSTER_DEFINITIONS[cluster_key]["label"],
        "raw_note": item.get("raw_note") or item.get("raw_text") or "",
        "explicit_sale": _has_explicit_sale(item),
        "anomaly_flags": list(item.get("anomaly_flags") or []),
        "owner_decision_id": _proposal(item).get("owner_decision_id"),
        "owner_decision_status": _proposal(item).get("owner_decision_status"),
        "historical_group_key": _proposal(item).get("historical_group_key"),
        "reconciliation_role": _proposal(item).get("reconciliation_role"),
        "opening_inclusion": _proposal(item).get("opening_inclusion"),
        "business": fields,
    }


def _cluster_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("current_review_status") == REVIEW_REQUIRED:
            grouped[str(row["cluster_key"])].append(row)
    result: list[dict[str, Any]] = []
    for key in sorted(grouped):
        definition = CLUSTER_DEFINITIONS[key]
        amounts: defaultdict[str, Decimal] = defaultdict(Decimal)
        for row in grouped[key]:
            amount = _decimal(row.get("amount"))
            if amount is not None:
                amounts[str(row.get("currency") or UNKNOWN_CURRENCY)] += amount
        result.append(
            {
                "cluster_key": key,
                "label": definition["label"],
                "count": len(grouped[key]),
                "amounts_by_currency": {currency: _float(amounts[currency]) for currency in sorted(amounts)},
                "source_item_ids": sorted(str(row["source_item_id"]) for row in grouped[key] if row.get("source_item_id")),
                "example_references": [row["source_reference"] for row in grouped[key][:5]],
                "owner_question": definition["owner_question"],
                "rule_resolution": definition["rule_resolution"],
                "one_owner_rule": bool(definition["one_owner_rule"]),
                "ready_count": sum(
                    1 for row in grouped[key] if row.get("owner_review_state") == READY_FOR_OWNER_CONFIRMATION
                ),
                "unknown_count": sum(1 for row in grouped[key] if row.get("owner_review_state") == UNKNOWN),
            }
        )
    return result


def build_owner_decision_pack(golden_items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for item in golden_items:
        row = int(item.get("source_row") or 0)
        decisions.append(
            {
                "decision_id": f"GOLDEN-{row}",
                "title": item.get("business", {}).get("title") or f"Source row {row}",
                "evidence": {
                    "source_reference": item.get("source_reference"),
                    "amount": item.get("amount"),
                    "currency": item.get("currency"),
                    "raw_note": item.get("raw_note"),
                    "current_review_status": item.get("current_review_status"),
                    "owner_review_state": item.get("owner_review_state"),
                },
                "recommended": item.get("business", {}).get("recommendation"),
                "alternatives": [
                    "Giữ REVIEW_REQUIRED/UNKNOWN và không đưa vào opening.",
                    "Owner cung cấp thêm source evidence trước khi confirm.",
                ],
                "financial_effect_if_confirmed": item.get("business", {}).get("decision_effect"),
                "owner_question": item.get("business", {}).get("owner_question"),
                "application_status": (
                    "APPLIED_TO_STAGING"
                    if item.get("current_review_status") == "CONFIRMED"
                    and item.get("owner_decision_status") == "CONFIRMED"
                    else "PENDING_OWNER_DECISION"
                ),
            }
        )
    return {
        "title": "Owner Decision Pack",
        "analysis_version": ANALYSIS_VERSION,
        "decision_count": len(decisions),
        "decisions": decisions,
        "cutover_lock": "DRAFT / NOT_APPROVED / NOT_LIVE",
        "confirmation_rule": "READY_FOR_OWNER_CONFIRMATION never changes review_status or creates a canonical effect.",
    }


def build_review_analysis(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build all deterministic Owner-review evidence without mutating input items."""

    rows = [dict(item) for item in items]
    checkpoint = reconstruct_checkpoint_candidates(rows)
    checkpoint_by_id = {}
    if checkpoint and checkpoint.get("checkpoint_source_item_id"):
        checkpoint_by_id[str(checkpoint["checkpoint_source_item_id"])] = checkpoint
    derived = [
        _derived_row(item, checkpoint_by_id.get(str(item.get("source_item_id"))))
        for item in rows
    ]
    derived_by_row = {
        (str(row.get("sheet") or ""), int(row.get("source_row") or 0)): row
        for row in derived
    }
    golden_items = [
        derived_by_row[("Sheet2", source_row)]
        for source_row in GOLDEN_SOURCE_ROWS
        if ("Sheet2", source_row) in derived_by_row
    ]
    current_states = Counter(str(row.get("current_review_status") or "RAW") for row in derived)
    owner_states = Counter(str(row.get("owner_review_state") or UNKNOWN) for row in derived)
    review_rows = [row for row in derived if row.get("current_review_status") == REVIEW_REQUIRED]
    clusters = _cluster_summary(derived)
    reconciliation = build_owner_reconciliation(rows)
    return {
        "analysis_version": ANALYSIS_VERSION,
        "item_count": len(derived),
        "review_required_count": len(review_rows),
        "current_status_counts": dict(sorted(current_states.items())),
        "owner_review_state_counts": dict(sorted(owner_states.items())),
        "clustered_review_count": sum(int(cluster["count"]) for cluster in clusters),
        "cluster_count": len(clusters),
        "clusters": clusters,
        "golden_items": golden_items,
        "checkpoint_reconstruction": checkpoint,
        "owner_reconciliation": reconciliation,
        "component_checkpoint_graph": reconciliation.get("component_checkpoint_graph"),
        "post_owner_counts": {
            "CONFIRMED": int(current_states.get("CONFIRMED", 0)),
            "REVIEW_REQUIRED": int(current_states.get(REVIEW_REQUIRED, 0)),
            "UNKNOWN": int(owner_states.get(UNKNOWN, 0)),
            "NOT_APPLICABLE": int(current_states.get(NOT_APPLICABLE, 0)),
            "PROPOSED": int(current_states.get("PROPOSED", 0)),
            "RAW": int(current_states.get("RAW", 0)),
        },
        "owner_decision_pack": build_owner_decision_pack(golden_items),
        "safety": {
            "input_items_mutated": False,
            "review_status_mutated": False,
            "confirmed_rows_created": False,
            "canonical_mutations": 0,
            "checkpoint_excluded_from_opening": True,
        },
    }


__all__ = [
    "ANALYSIS_VERSION",
    "CHECKPOINT_LOOKBACK_ROWS",
    "CLUSTER_DEFINITIONS",
    "GOLDEN_EXPECTED_AMOUNTS",
    "GOLDEN_SOURCE_ROWS",
    "NOT_APPLICABLE",
    "READY_FOR_OWNER_CONFIRMATION",
    "REVIEW_REQUIRED",
    "UNKNOWN",
    "build_owner_decision_pack",
    "build_review_analysis",
    "classify_review_cluster",
    "reconstruct_checkpoint_candidates",
]
