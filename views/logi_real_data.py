"""Presentation adapter: real Logistics readers → the frozen Logi-good shape.

Phase B replaces the Phase A sandbox seed projection with a read-only
projection over the CURRENT Logistics readers. There is no duplicate business
truth here: every value comes from ``core.database`` / ``core.logic`` /
``core.shipment_dashboard`` / ``core.docgen`` and is reshaped for display only.

UNKNOWN != ZERO
---------------
A numeric value the real model does not carry is projected as ``None`` and is
rendered as an explicit "—" by the UI. It is never coerced to ``0``, because
for tax, VAT, pack count, weight, CBM, cost, Finance Actual, AR/AP and payments
a blank is a statement about knowledge, not about money.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from core.database import _UNSET_DB

from views.logi_route import shipment_path

UNKNOWN = None
UNKNOWN_LABEL = "—"


# --------------------------------------------------------------------------
# UNKNOWN-safe primitives
# --------------------------------------------------------------------------

def text(value: Any) -> str:
    """Text field: real value or blank. Never a fabricated placeholder."""
    if value is None:
        return ""
    return str(value).strip()


def num(value: Any) -> float | None:
    """Numeric field: real value or None (UNKNOWN). Never 0 for a blank."""
    if value is None or isinstance(value, bool):
        return None if value is None else float(value)
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw.replace(",", "").replace(".", "", raw.count(".") > 1))
    except ValueError:
        return None


def label(value: Any) -> str:
    """Display label: UNKNOWN renders as an explicit em dash."""
    if value is None:
        return UNKNOWN_LABEL
    raw = str(value).strip()
    return raw or UNKNOWN_LABEL


def money(value: Any) -> float | None:
    return num(value)


def _ddmmyyyy(value: Any) -> str:
    """Normalise an ISO/other date string to DD/MM/YYYY, blank when unknown."""
    raw = text(value)
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:19] if len(raw) > 10 and "-" in raw else raw, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return raw


def _money_label(value: Any) -> str:
    amount = num(value)
    if amount is None:
        return UNKNOWN_LABEL
    return f"{amount:,.0f}".replace(",", ".")


# --------------------------------------------------------------------------
# Canonical fact access
# --------------------------------------------------------------------------

def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = shipment.get("data")
    if not isinstance(data, Mapping):
        return {}
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def _transport_leg_projection(leg: Mapping[str, Any]) -> dict[str, Any]:
    """Map one canonical snake_case leg to the typed component contract."""
    units = leg.get("units") if isinstance(leg.get("units"), list) else []
    return {
        "id": text(leg.get("id")),
        "sequence": int(leg.get("sequence") or 0),
        "mode": text(leg.get("mode")),
        "origin": text(leg.get("origin")),
        "destination": text(leg.get("destination")),
        "carrier": text(leg.get("carrier")),
        "etd": text(leg.get("etd")),
        "eta": text(leg.get("eta")),
        "atd": text(leg.get("atd")),
        "ata": text(leg.get("ata")),
        "bookingNo": text(leg.get("booking_no")),
        "mbl": text(leg.get("mbl")),
        "hbl": text(leg.get("hbl")),
        "vessel": text(leg.get("vessel")),
        "voyage": text(leg.get("voyage")),
        "mawb": text(leg.get("mawb")),
        "hawb": text(leg.get("hawb")),
        "flightNo": text(leg.get("flight_no")),
        "units": [
            {
                "id": text(unit.get("id")),
                "kind": text(unit.get("kind")),
                "number": text(unit.get("number")),
                "typeSize": text(unit.get("type_size")),
                "sealNo": text(unit.get("seal_no")),
                "driverName": text(unit.get("driver_name")),
                "driverPhone": text(unit.get("driver_phone")),
            }
            for unit in units if isinstance(unit, Mapping)
        ],
    }


def _declaration_date(customs: Mapping[str, Any]) -> str:
    """Customs declaration date, DD/MM/YYYY, blank when unknown.

    LOGI_GNT_CANONICAL_FIELDS_01: ``tk_date`` is the canonical field for new
    data (Owner-approved 2026-09-12). ``reg_date`` is a READ-ONLY fallback for
    documents written before that ruling — it is never written, and the new
    field always wins when both are present.
    """
    return _ddmmyyyy(customs.get("tk_date") or customs.get("reg_date"))


def operational_stage(shipment: Mapping[str, Any]) -> tuple[str, str]:
    """Derive the operational stage from real shipment facts only.

    Returns ``(label, tone)`` for the donor status badge. No fabricated KPI.
    """
    from core.shipment_operations import compatibility_facts

    delivery = _section(shipment, "2.7")
    customs = _section(shipment, "2.4")
    transport = _section(shipment, "1.2")
    arrival = _section(shipment, "2.6")
    operational = compatibility_facts(shipment)
    status = text(shipment.get("status") or _section(shipment, "0.0").get("st"))

    if delivery.get("is_delivered"):
        return "Đã giao", "green"
    if status == "cancel":
        return "Đã hủy", "gray"
    if customs.get("customs_status"):
        return "Chờ giao", "blue"
    # A registered declaration, or goods already arrived at the border, both
    # mean the shipment is waiting on customs — derived from real facts only.
    if text(customs.get("tk_no")) or _arrived(arrival.get("arrival_date")):
        return "Chờ thông quan", "amber"
    # Structured legs are authoritative when present; legacy ETD is consumed
    # only through compatibility_facts for pre-V1 documents.
    operational_etd = operational.get("etd")
    if text(operational_etd) and _arrived(operational_etd):
        return "Đang vận chuyển", "blue"
    return "Chờ lấy hàng", "gray"


def _arrived(value: Any) -> bool:
    """True when a real ETA/arrival date has already passed (goods at border)."""
    from core.utils import parse_date_optional

    parsed = parse_date_optional(value)
    return bool(parsed and parsed <= date.today())


def document_checklist(
    shipment: Mapping[str, Any],
    execution_profile: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Document completeness derived from real shipment facts (no invention).

    LOGI_SCOPE_AWARE_MISSING_INFO_01 — the checklist becomes scope-aware ONLY
    when the operator-confirmed execution profile is present and confirmed.
    Otherwise legacy four-row behavior is preserved (UNKNOWN scope != not our
    responsibility). No DB read, no second profile build, no new truth.
    """
    from core.shipment_operations import compatibility_facts

    customs = _section(shipment, "2.4")
    delivery = _section(shipment, "2.7")
    operational = compatibility_facts(shipment)
    delivery_unit = operational.get("delivery_unit") if isinstance(operational.get("delivery_unit"), Mapping) else {}
    delivery_plate = text(delivery_unit.get("number"))
    tk = text(customs.get("tk_no"))
    rows = [
        {"name": "Số tờ khai nhập khẩu", "ok": bool(tk),
         "note": tk or "Chưa đăng ký tờ khai"},
        {"name": "Đã thông quan", "ok": bool(customs.get("customs_status")),
         "note": text(customs.get("phan_luong")) or ("Chờ kết quả phân luồng" if tk else "Chờ số tờ khai")},
        {"name": "Xe giao VN + tài xế", "ok": bool(delivery_plate),
         "note": delivery_plate or "Chưa đặt xe giao"},
        {"name": "Xác nhận đã giao hàng", "ok": bool(delivery.get("is_delivered")),
         "note": _ddmmyyyy(delivery.get("delivered_at")) or "Chưa xác nhận"},
    ]

    # Scope-aware filtering: only when serviceScopeConfirmed == true.
    # Do NOT infer scope from incoterm/mode/status — only operator-confirmed.
    profile = execution_profile if isinstance(execution_profile, Mapping) else {}
    if not profile:
        return rows
    if not bool(profile.get("serviceScopeConfirmed")):
        return rows

    # PROFILE_INCOMPLETE or legacy without serviceScope still falls back to
    # legacy behavior: if scope list is absent, keep legacy.
    scope_raw = profile.get("serviceScope")
    if scope_raw is None:
        return rows
    # Normalize to upper strings for safety, but keep existing canonical codes.
    scope_set = {str(item).strip().upper() for item in scope_raw if str(item).strip()}
    if not scope_set:
        # Confirmed but empty scope: no import/delivery relevance.
        return []

    # Derive relevant names ONLY from persisted service scope.
    # IMPORT_CUSTOMS -> tk + customs_status
    # DESTINATION_TRUCKING -> truck + delivered
    # FINAL_DELIVERY -> delivered only (once)
    # MAIN_CARRIAGE or other -> none of the four
    relevant: set[str] = set()
    if "IMPORT_CUSTOMS" in scope_set:
        relevant.add("Số tờ khai nhập khẩu")
        relevant.add("Đã thông quan")
    if "DESTINATION_TRUCKING" in scope_set:
        relevant.add("Xe giao VN + tài xế")
        relevant.add("Xác nhận đã giao hàng")
    if "FINAL_DELIVERY" in scope_set:
        relevant.add("Xác nhận đã giao hàng")

    if not relevant:
        return []

    # Filter preserving original order, unique rows only.
    filtered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        name = row.get("name") or ""
        if name in relevant and name not in seen:
            filtered.append(row)
            seen.add(name)
    return filtered


def missing_docs(
    shipment: Mapping[str, Any],
    execution_profile: Mapping[str, Any] | None = None,
) -> list[str]:
    return [
        row["name"]
        for row in document_checklist(shipment, execution_profile=execution_profile)
        if not row["ok"]
    ]


# --------------------------------------------------------------------------
# Finance projection — QUOTE ESTIMATE stays separate from FINANCE ACTUAL
# --------------------------------------------------------------------------

def _quote_estimate_line(line: Mapping[str, Any]) -> dict[str, Any]:
    """One canonical LOG-C12 service line, projected with a TRUTHFUL currency.

    LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_03 — this used to read

        amount = sell_vnd if sell_vnd is not None else sell_total
        ccy    = "VND"                      # always

    which was safe only while every line was guaranteed convertible. REPAIR_02
    made "no quote-time FX rate" a normal, savable state, so ``sell_vnd`` is now
    legitimately None on a foreign-currency line — and the fallback then
    published the ORIGINAL amount under a VND label: 950 USD rendered as
    "950 VND", understating the figure by roughly 24,000x on the Check chi phí
    screen.

    The label must always describe the amount actually being shown:
      * converted (sell_vnd known) → that VND figure, labelled VND;
      * not converted              → the original amount, labelled with the
                                     line's OWN currency.
    Nothing is converted here and no rate is invented; this is projection only.
    """
    sell_vnd = line.get("sell_vnd")
    if sell_vnd is not None:
        amount, ccy = num(sell_vnd), "VND"
    else:
        amount, ccy = num(line.get("sell_total")), text(line.get("currency")) or "VND"
    return {
        "label": text(line.get("service_name")) or text(line.get("code")) or "Dòng báo giá",
        "amount": amount,
        "ccy": ccy,
        "qty": num(line.get("qty")),
        "vat": num(line.get("tax_pct")),
        "kind": "quote",
    }


def _quote_lines(shipment: Mapping[str, Any], quotes: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Quote estimate lines from the linked quote (a separate object).

    REPAIR_03 — identity precedence. ``build_shipment_draft`` already stamps
    ``shipment.quote_id``, but this projection used to scan the quote store by
    contract/customer, so a customer with several quotes could have ANY of them
    projected onto the lot. The lot's own link is authoritative when present:
    the exact quote, or nothing — never a same-customer substitute, because a
    plausible wrong estimate is worse than a visible absence.

    Legacy shipments carry no ``quote_id``; for those the original
    contract/customer fallback is preserved unchanged. No migration, no rewrite
    of historical shipments.
    """
    def _project(quote: Mapping[str, Any]) -> list[dict[str, Any]] | None:
        # Legacy quote shape: pre-priced ``lines`` that state their own currency.
        lines = quote.get("lines")
        if isinstance(lines, list):
            return [
                {
                    "label": text(line.get("name")) or "Dòng báo giá",
                    "amount": num(line.get("amount")),
                    "ccy": text(line.get("currency")) or "VND",
                    "kind": "quote",
                }
                for line in lines
                if isinstance(line, Mapping)
            ]
        # Canonical LOG-C12 quote shape: service_lines carry the estimate.
        service_lines = quote.get("service_lines")
        if isinstance(service_lines, list):
            return [_quote_estimate_line(line) for line in service_lines
                    if isinstance(line, Mapping)]
        return None

    # (1) The lot's OWN link wins, exactly.
    quote_id = text(shipment.get("quote_id"))
    if quote_id:
        linked = quotes.get(quote_id)
        if not isinstance(linked, Mapping):
            linked = next((q for q in quotes.values()
                           if isinstance(q, Mapping) and text(q.get("id")) == quote_id), None)
        if not isinstance(linked, Mapping):
            return []  # the link names a quote we cannot read — show nothing, guess nothing
        return _project(linked) or []

    # (2) Legacy shipments only: the original contract/customer fallback.
    customer_id = text(shipment.get("customer_id"))
    contract_id = text(shipment.get("contract_id"))
    for quote in quotes.values():
        if not isinstance(quote, Mapping):
            continue
        if contract_id and text(quote.get("id")) == contract_id:
            pass
        elif text(quote.get("customer_id")) != customer_id:
            continue
        projected = _project(quote)
        if projected is not None:
            return projected
    return []


def _partner_projection(
    shipment_id: str,
    *,
    ledger: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Partner payable truth for ONE shipment, read from the canonical ledger.

    UNKNOWN != ZERO: with no canonical obligation/payment records the money
    figures stay None (rendered as “—”), never 0. The partner identity comes
    from the ledger when established; before that, the single existing
    authority_agents master record is offered as a clearly-marked suggestion
    so the shell can start the journey without inventing a partner.

    ``ledger`` (a pre-loaded ``core.financial_ledger.load_ledger_snapshot``)
    and ``agents`` (the already-loaded authority_agents master) are the
    render-local snapshot the component build path passes in; without them the
    original per-call readers run exactly as before.
    """
    from core.database import load_authority_agents
    from core.financial_ledger import shipment_partner_position

    position = shipment_partner_position(shipment_id, records=ledger)
    result: dict[str, Any] = {
        "partnerId": None,
        "partnerName": None,
        "suggested": False,
        "status": position.get("status"),
        "payable": None,
        "paid": None,
        "remaining": None,
        "currency": None,
        "payments": [],
    }
    groups = position.get("partners") or []
    if len(groups) == 1:
        group = groups[0]
        party = group.get("partner") if isinstance(group.get("partner"), Mapping) else {}
        result["partnerId"] = text(party.get("party_id"))
        result["partnerName"] = text(party.get("name"))
        if group.get("status") == "CONFIRMED" and len(group.get("totals_by_currency") or {}) == 1:
            currency = next(iter(group["totals_by_currency"]))
            values = group["totals_by_currency"][currency]
            result.update(
                {
                    "payable": values["payable"],
                    "paid": values["paid"],
                    "remaining": values["remaining"],
                    "currency": currency,
                }
            )
        result["payments"] = [
            {
                "id": text(row.get("transaction_id")),
                "requestId": text(row.get("request_id")),
                "date": _ddmmyyyy(row.get("occurred_at")),
                "kind": text(row.get("transaction_kind")) or "payment",
                "amount": num(row.get("amount")),
                "ccy": text(row.get("currency")),
                "allocated": num(row.get("allocated")),
                "unallocated": num(row.get("unallocated")),
                "note": text(row.get("note")),
            }
            for row in (group.get("payments") or [])
            if isinstance(row, Mapping)
        ]
        return result

    # Nothing established yet: suggest the single existing catalog agent, if any.
    if agents is None:
        try:
            agents = load_authority_agents() or {}
        except Exception:  # noqa: BLE001 - suggestion is best-effort only
            agents = {}
    docs = [d for d in agents.values() if isinstance(d, Mapping) and text(d.get("agent_id") or d.get("id"))]
    if len(docs) == 1:
        doc = docs[0]
        result["suggested"] = True
        result["partnerId"] = text(doc.get("agent_id") or doc.get("id"))
        result["partnerName"] = text(doc.get("legal_name")) or result["partnerId"]
    return result


def finance_service_catalog(cost_catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Service picker: legacy defaults plus operator-maintained catalog overlays.

    Stable catalog ids are authority. Dynamic SERVICE entries can add a new code
    or replace a legacy code via legacy_codes without editing core/config.py.
    """
    from core.config import GETFLY_SERVICES_LIST

    legacy = [
        {
            "id": f"LEGACY:{text(item.get('code'))}",
            "code": text(item.get("code")),
            "name": text(item.get("name")),
            "unit": text(item.get("unit")) or "Lần",
            "group": text(item.get("group")),
            "source": "LEGACY_CONFIG",
        }
        for item in GETFLY_SERVICES_LIST
        if isinstance(item, Mapping) and text(item.get("code"))
    ]
    dynamic = [
        entry for entry in (cost_catalog or {}).values()
        if isinstance(entry, Mapping)
        and text(entry.get("kind")).upper() == "SERVICE"
        and entry.get("active", True) is not False
    ]
    if not dynamic:
        return legacy

    hidden_legacy = {
        str(code).upper()
        for entry in dynamic
        for code in (entry.get("legacy_codes") or entry.get("legacyCodes") or [])
        if str(code).strip()
    }
    by_id: dict[str, dict[str, Any]] = {
        row["id"]: row for row in legacy if row["code"].upper() not in hidden_legacy
    }
    for entry in dynamic:
        identifier = text(entry.get("id"))
        code = text(entry.get("code")).upper()
        if not identifier or not code:
            continue
        # Same visible code replaces the legacy presentation while preserving a
        # stable dynamic id for all new writes.
        for key, row in list(by_id.items()):
            if row.get("code", "").upper() == code:
                by_id.pop(key, None)
        by_id[identifier] = {
            "id": identifier,
            "code": code,
            "name": text(entry.get("name")) or code,
            "unit": text(entry.get("unit")) or "Lần",
            "group": text(entry.get("group")) or "DỊCH VỤ XNK",
            "source": "COST_CATALOG",
        }
    return sorted(by_id.values(), key=lambda row: (row.get("group", ""), row.get("name", ""), row.get("code", "")))


def finance_projection(
    shipment: Mapping[str, Any],
    quotes: Mapping[str, Any],
    *,
    ledger: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Finance Actual from the canonical snapshot; AR/AP from core.logic.

    ``quote`` (estimate) and ``actual`` (booked service lines) are sourced from
    different objects and are never merged or interchanged.

    ``ledger`` / ``agents`` are the render-local snapshot the component build
    path already read (see ``_partner_projection``); passing them down costs
    zero additional reads and leaves the derived figures identical.
    """
    from core.logic import calculate_from_shipment

    finance = _section(shipment, "3.4")
    details = finance.get("details") if isinstance(finance.get("details"), list) else []
    summary = calculate_from_shipment(shipment)
    currency = text(shipment.get("currency") or finance.get("currency") or "VND")

    actual = [
        {
            # Every field below is the SOURCE FIELD the operator already books
            # on ``data["3.4"].details`` — re-shaped for display only, never
            # recomputed. ``id`` is what lets the UI edit the SAME canonical row
            # instead of appending a new one; ``amount`` stays as the sell-side
            # figure the summary rows have always rendered.
            "id": text(line.get("id")),
            "label": text(line.get("display_name") or line.get("name_full") or line.get("name")) or "Dịch vụ",
            "name": text(line.get("name_full") or line.get("display_name")),
            "code": text(line.get("code")),
            "unit": text(line.get("unit")),
            "note": text(line.get("note")),
            "amount": num(line.get("price", line.get("price_out"))),
            "price": num(line.get("price", line.get("price_out"))),
            "cost": num(line.get("cost", line.get("price_in"))),
            "qty": num(line.get("qty")),
            "vat": num(line.get("vat_line", line.get("vat"))),
            "ccy": currency,
            "kind": "actual",
        }
        for line in details
        if isinstance(line, Mapping)
    ]

    payments_raw = finance.get("payments") if isinstance(finance.get("payments"), list) else []
    payments = [
        {
            "id": text(p.get("id")),
            "requestId": text(p.get("request_id")),
            "date": _ddmmyyyy(p.get("date")),
            "kind": text(p.get("note")) or "Khoản thu",
            "amount": num(p.get("amount")),
            "ccy": currency,
            "by": text(p.get("created_by") or p.get("created_by_username")),
            "note": text(p.get("note")),
            "reversed": bool(p.get("is_reversed")) or text(p.get("status")).lower() in {"reversed", "cancelled", "void"},
        }
        for p in payments_raw
        if isinstance(p, Mapping)
    ]

    # ACTUAL PROFIT comes only from booked actual service lines. core.logic
    # legitimately returns 0.0 for an empty book, but presenting that as an
    # actual profit would manufacture a result from unknown inputs, so profit
    # and margin stay UNKNOWN until at least one actual line is booked.
    # Quote Estimate is never used to fill the gap.
    has_actual_lines = bool(details)
    profit = num(summary.get("profit")) if has_actual_lines else UNKNOWN
    revenue_net = num(summary.get("revenue_net"))
    profit_margin = (
        round(profit / revenue_net * 100, 2)
        if profit is not None and revenue_net not in (None, 0)
        else UNKNOWN
    )

    return {
        "quote": _quote_lines(shipment, quotes),
        "actual": actual,
        "currency": currency,
        "hasActualLines": has_actual_lines,
        # AR — canonical snapshot from core.logic (receivable = net + output VAT).
        "receivable": num(summary.get("receivable")),
        "received": num(summary.get("paid")),
        "receivableNet": revenue_net,
        "outputVat": num(summary.get("output_vat")),
        "outstanding": num(summary.get("debt")),
        # AP — cost side of the same service lines.
        "payable": num(summary.get("cost")),
        # The shipment document does not carry a supplier-payment ledger, so
        # "already paid to partners" is UNKNOWN, not zero.
        "paid": UNKNOWN,
        "commission": num((finance.get("commission") or {}).get("total") if isinstance(finance.get("commission"), Mapping) else finance.get("commission")),
        "profit": profit,
        "profitMargin": profit_margin,
        "payments": payments,
        # C2B — partner payable truth for THIS shipment, from the canonical
        # ledger (financial_obligations/transactions/allocations). `paid` above
        # stays UNKNOWN; the partner block carries the ledger-derived figures.
        "partner": _partner_projection(text(shipment.get("id")), ledger=ledger, agents=agents),
        "source": "core.logic.calculate_from_shipment over data.3.4",
    }


def receivables_projection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Global customer-receivable worklist over real shipment finance truth.

    One row per shipment. ``receivable`` / ``outstanding`` come from the
    canonical ``core.logic`` snapshot ONLY when at least one actual service
    line is booked; otherwise they stay UNKNOWN (None) — a blank book is a
    statement about knowledge, never a manufactured zero. Quote Estimate is a
    separate object and is never used to fill a gap. ``received`` is the
    non-reversed customer receipt total and is a genuine zero when no payment
    exists.

    Totals are grouped by currency and never summed across currencies
    (no FX engine, no fake "grand total").
    """
    out_rows: list[dict[str, Any]] = []
    totals: dict[str, dict[str, float | None]] = {}

    for row in rows:
        fin = row.get("finance") if isinstance(row.get("finance"), Mapping) else {}
        currency = (text(fin.get("currency")) or "VND").upper()
        has_actual = bool(fin.get("hasActualLines"))
        receivable = num(fin.get("receivable")) if has_actual else None
        received = num(fin.get("received"))
        outstanding = num(fin.get("outstanding")) if has_actual else None

        out_rows.append({
            "id": text(row.get("id")),
            "customer": text(row.get("customer")),
            "customerId": text(row.get("customerId")),
            "currency": currency,
            "receivable": receivable,
            "received": received,
            "outstanding": outstanding,
            "sale": text(row.get("sale")),
            "support": text(row.get("support")),
            "status": text(row.get("status")),
            "statusTone": text(row.get("statusTone")),
            "hasActualLines": has_actual,
        })

        if not has_actual:
            continue
        bucket = totals.setdefault(
            currency, {"receivable": 0.0, "received": 0.0, "outstanding": 0.0}
        )
        if receivable is not None:
            bucket["receivable"] += receivable
        if received is not None:
            bucket["received"] += received
        if outstanding is not None:
            bucket["outstanding"] += outstanding

    return {"rows": out_rows, "totals": totals}


def partner_payables_projection(
    db: Any | None = None,
    *,
    records: Mapping[str, Any] | None = None,
    shipment_ids: list[str] | None = None,
    agents: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Global THANH TOÁN ĐỐI TÁC / PHẢI TRẢ worklist over canonical C2B truth.

    Reuses ``core.financial_ledger.shipment_partner_position`` per shipment —
    the SAME derived payable/paid/remaining the per-shipment C2B slice already
    proves — and flattens it to one row per SHIPMENT × PARTNER × CURRENCY.

    UNKNOWN != ZERO: a shipment with no canonical obligation/payment record
    contributes NO row (absence is never reported as a 0 payable). Currencies
    are never summed together (no FX engine). Partner identity resolves against
    the authority_agents master and only falls back to the canonical record's
    party name when the master has no match.

    PERFORMANCE REPAIR — the component build path passes the render-local
    snapshot it already read:

    * ``records``  — ``core.financial_ledger.load_ledger_snapshot`` rows, so the
      per-shipment derivation reads no collection;
    * ``shipment_ids`` — the ids the render already loaded
      (``core.database.load_shipment_ids``), so ``db.shipments`` is not read a
      second time for the same answer;
    * ``agents`` — the already-loaded authority_agents master.

    Every argument is optional: a standalone caller keeps the original reads.
    """

    from core.database import get_db, load_authority_agents
    from core.financial_ledger import shipment_partner_position

    db = get_db() if db is None else db
    empty: dict[str, Any] = {
        "rows": [],
        "totals": {},
        "status": "UNKNOWN",
        "derived": True,
        "read_only": True,
    }
    if db is None:
        return {**empty, "error": "MongoDB is not available"}

    if agents is None:
        try:
            agents = load_authority_agents() or {}
        except Exception:  # noqa: BLE001 - name resolution is best-effort only
            agents = {}

    def _master_name(party_id: str, fallback: str) -> str:
        doc = agents.get(party_id) if isinstance(agents.get(party_id), Mapping) else None
        if doc is None:
            doc = next(
                (d for d in agents.values() if isinstance(d, Mapping) and text(d.get("agent_id")) == party_id),
                None,
            )
        if doc is None:
            return fallback or party_id
        return text(doc.get("legal_name")) or fallback or party_id

    if shipment_ids is None:
        # Same query, same projection and same order as before; it is only
        # hoisted so that a render which already has the ids reads them once.
        from core.database import load_shipment_ids

        shipment_ids = load_shipment_ids()

    rows: list[dict[str, Any]] = []
    totals: dict[str, dict[str, Any]] = {}
    for raw_sid in shipment_ids:
        sid = text(raw_sid)
        if not sid:
            continue
        position = shipment_partner_position(sid, db=db, records=records)
        for group in position.get("partners") or []:
            if not isinstance(group, Mapping):
                continue
            party = group.get("partner") if isinstance(group.get("partner"), Mapping) else {}
            partner_id = text(party.get("party_id"))
            if not partner_id:
                continue
            partner_name = _master_name(partner_id, text(party.get("name")))
            by_currency: dict[str, dict[str, Any]] = {}
            for obligation in group.get("obligations") or []:
                if not isinstance(obligation, Mapping):
                    continue
                currency = text(obligation.get("currency")).upper()
                if not currency:
                    continue
                bucket = by_currency.setdefault(
                    currency,
                    {
                        "payable": 0.0,
                        "paid": 0.0,
                        "remaining": 0.0,
                        "status": "CONFIRMED",
                        "obligationIds": [],
                    },
                )
                bucket["payable"] += float(obligation.get("amount") or 0)
                bucket["paid"] += float(obligation.get("allocated") or 0)
                bucket["remaining"] += float(obligation.get("outstanding") or 0)
                obligation_id = text(obligation.get("obligation_id"))
                if obligation_id and obligation_id not in bucket["obligationIds"]:
                    bucket["obligationIds"].append(obligation_id)
                if text(obligation.get("status")).upper() != "CONFIRMED":
                    bucket["status"] = "REVIEW_REQUIRED"
            for currency, values in by_currency.items():
                rows.append(
                    {
                        "id": f"{sid}|{partner_id}|{currency}",
                        "partnerId": partner_id,
                        "partnerName": partner_name,
                        "shipmentId": sid,
                        "currency": currency,
                        "payable": values["payable"],
                        "paid": values["paid"],
                        "remaining": values["remaining"],
                        "status": values["status"],
                        "obligationIds": values["obligationIds"],
                    }
                )
                total = totals.setdefault(
                    currency, {"payable": 0.0, "paid": 0.0, "remaining": 0.0, "count": 0}
                )
                total["payable"] += values["payable"]
                total["paid"] += values["paid"]
                total["remaining"] += values["remaining"]
                total["count"] += 1

    rows.sort(key=lambda r: (r["shipmentId"], r["partnerId"], r["currency"]))
    overall = (
        "UNKNOWN"
        if not rows
        else ("REVIEW_REQUIRED" if any(r["status"] != "CONFIRMED" for r in rows) else "CONFIRMED")
    )
    return {
        "rows": rows,
        "totals": totals,
        "status": overall,
        "derived": True,
        "read_only": True,
    }


# --------------------------------------------------------------------------
# History — real audit only
# --------------------------------------------------------------------------

def timeline_rows(rows: Any) -> list[dict[str, Any]]:
    """Shape canonical audit rows into the frozen timeline entries.

    ONE shaper for every caller, so the single-shipment read and the bulk read
    can never drift apart.
    """
    out: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        created = row.get("created_at")
        stamp = created.strftime("%d/%m %H:%M") if isinstance(created, datetime) else _ddmmyyyy(created)
        action = text(row.get("action"))
        out.append({
            "time": stamp,
            "title": action or "Cập nhật",
            "desc": text(row.get("actor")) or text(row.get("actor_username")),
            "tone": "green" if action in {"create", "direct_payment_created", "delivered"} else "blue",
        })
    return out


def timeline_projection(shipment_id: str, limit: int = 30, *, db: Any = _UNSET_DB) -> list[dict[str, Any]]:
    """Timeline for ONE shipment (single read) — the standalone/fallback path.

    ``db`` is the explicit database handle a STREAMLIT-FREE read worker was
    handed (see ``views.logi_view_model._read_concurrently``).  The default is
    the ``_UNSET_DB`` sentinel: a caller that omits ``db`` keeps the original
    canonical resolution, while an EXPLICIT ``None`` means "the canonical
    resolution already ran and there is no database" — it is passed straight
    through, never re-resolved (a worker must stay Streamlit-free).
    """
    from core.database import load_audit_logs

    return timeline_rows(load_audit_logs("shipment", shipment_id, limit=limit, db=db))


def timelines_projection(shipment_ids: Any, limit: int = 30, *, db: Any = _UNSET_DB) -> dict[str, list[dict[str, Any]]]:
    """Timelines for MANY shipments in ONE bounded audit read.

    PERFORMANCE REPAIR: the component build path used to call
    ``timeline_projection`` once per shipment, i.e. one ``audit_logs`` read per
    row of the worklist. This reads the same rows for the shipment ids the
    caller already loaded, in one query, groups them by shipment in memory and
    applies the same "newest first, at most ``limit`` entries" rule per
    shipment. No audit writer, schema or entry is changed.
    """
    from core.database import load_audit_logs_bulk

    ids = [text(item) for item in (shipment_ids or [])]
    grouped = load_audit_logs_bulk("shipment", [sid for sid in ids if sid], limit_per_entity=limit, db=db)
    return {sid: timeline_rows(rows) for sid, rows in grouped.items()}


# --------------------------------------------------------------------------
# GNT projection
# --------------------------------------------------------------------------

def _gnt_projection(
    shipment: Mapping[str, Any],
    customs: Mapping[str, Any],
    customer_doc: Mapping[str, Any],
    shipment_id: str,
) -> dict[str, Any]:
    import base64
    from views import logi_c1

    gnt_customs = customs.get("gnt") if isinstance(customs.get("gnt"), Mapping) else {}
    payer = text(
        gnt_customs.get("nguoi_nop")
        or customs.get("taxpayer_name")
        or customs.get("nguoi_nop")
    )
    tax_code = text(
        gnt_customs.get("mst")
        or customs.get("taxpayer_tax_code")
        or customs.get("mst")
    )
    address = text(
        gnt_customs.get("dia_chi")
        or customs.get("taxpayer_address")
        or customs.get("dia_chi")
    )
    customs_office = text(gnt_customs.get("ma_hq") or customs.get("ma_hq"))
    customer_hint = text(customer_doc.get("name") or shipment.get("customer") or shipment.get("client"))
    customer_tax_hint = text(customer_doc.get("tax_code") or shipment.get("customer_tax_code"))

    stored = logi_c1.stored_outputs(shipment_id)
    gnt_entries = [
        v for k, v in stored.items()
        if isinstance(v, Mapping) and (v.get("document_type") == "GNT" or str(k).startswith(f"GNT::{shipment_id}"))
    ]
    latest_gnt = gnt_entries[-1] if gnt_entries else None

    gnt_doc = None
    if latest_gnt:
        gnt_raw = latest_gnt.get("bytes")
        b64 = None
        if gnt_raw:
            try:
                b64 = base64.b64encode(gnt_raw).decode("ascii")
            except Exception:  # noqa: BLE001
                b64 = None
        gnt_doc = {
            "fileName": text(latest_gnt.get("file_name") or f"GNT_{shipment_id}.xlsx"),
            "mime": text(latest_gnt.get("mime") or logi_c1._MIME_XLSX),
            "generatedAt": text(latest_gnt.get("generated_at")),
            "generatedBy": text(latest_gnt.get("generated_by")),
            "downloadAvailable": bool(gnt_raw),
            "downloadBase64": b64,
        }

    missing = []
    if not text(customs.get("tk_no")):
        missing.append("Số tờ khai (TK)")
    if not _declaration_date(customs):
        missing.append("Ngày tờ khai")

    raw_duty = customs.get("import_duty_amount")
    duty = None
    if raw_duty is None or str(raw_duty).strip() == "" or str(raw_duty).strip() == "None":
        missing.append("Thuế nhập khẩu")
    else:
        try:
            d_val = float(raw_duty)
            if d_val < 0:
                missing.append("Thuế nhập khẩu (< 0)")
            else:
                duty = d_val
        except (ValueError, TypeError):
            missing.append("Thuế nhập khẩu")

    raw_vat = customs.get("import_vat_amount")
    vat = None
    if raw_vat is None or str(raw_vat).strip() == "" or str(raw_vat).strip() == "None":
        missing.append("VAT hàng nhập khẩu")
    else:
        try:
            v_val = float(raw_vat)
            if v_val < 0:
                missing.append("VAT hàng nhập khẩu (< 0)")
            else:
                vat = v_val
        except (ValueError, TypeError):
            missing.append("VAT hàng nhập khẩu")

    if not payer:
        missing.append("Người nộp thuế")
    if not tax_code:
        missing.append("Mã số thuế")

    no_payable = False
    if duty is not None and vat is not None and duty == 0 and vat == 0 and len(missing) == 0:
        no_payable = True

    ready = (len(missing) == 0) and not no_payable

    return {
        "payer": payer,
        "taxCode": tax_code,
        "address": address,
        "customsOffice": customs_office,
        "customerHint": customer_hint,
        "customerTaxHint": customer_tax_hint,
        "ready": ready,
        "noPayable": no_payable,
        "missing": missing,
        "done": bool(gnt_doc),
        "document": gnt_doc,
    }


# --------------------------------------------------------------------------
# Primary action — ONE actionable next step (LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01)
# --------------------------------------------------------------------------
#
# The shipment detail used to carry TWO next-action authorities: the legacy
# dashboard/readiness projection (shipment.nextAction) at the top and the
# execution-profile projection (executionProfile.nextAction) lower on the page.
# They could disagree. This helper COMPOSES one primary instruction from the
# two existing in-memory projections and routes it to an EXISTING work surface.
# It is a pure UI-projection function: no database read, no persistence, no new
# route, no new writer. The execution profile object it consumes is the SAME
# object ``shipment_projection`` serves as ``executionProfile`` (built ONCE).
#
# Precedence (bounded, issue #82):
#   1. genuine dashboard CRITICAL risk wins;
#   2. execution-profile RED blocker (CONFIG_CHECK / insurance mismatch) wins
#      over dashboard WARNING/INFO;
#   3. execution-profile actionable gap (PROFILE_INCOMPLETE / unmet stage) wins
#      over dashboard WARNING/INFO;
#   4. profile DONE/MONITOR falls back to the existing dashboard action;
#   5. nothing actionable keeps the existing stable/no-alert behavior.

#: Profile next-action code → the EXISTING tab that owns the fact.
PRIMARY_ACTION_TAB_BY_PROFILE_CODE: dict[str, str] = {
    "ORIGIN_PICKUP": "lay-hang",
    "EXPORT_HANDLING": "lay-hang",
    "ORIGIN_HANDOFF": "lay-hang",
    "CROSS_BORDER": "lay-hang",
    "MAIN_CARRIAGE": "van-tai",
    "SEA_DOCUMENTS": "van-tai",
    "AIR_DOCUMENTS": "van-tai",
    "RAIL_CARRIAGE": "van-tai",
    "SEA_EQUIPMENT": "van-tai",
    "SEA_CONSOLIDATION": "van-tai",
    "ROAD_TRUCK_PROFILE": "van-tai",
    "ROAD_CONSOLIDATION": "van-tai",
    "IMPORT_CUSTOMS": "nhap",
    "DELIVERY": "nhap",
}

#: Profile codes handled on the EXISTING execution-profile section itself.
PRIMARY_ACTION_PROFILE_SECTION_CODES = frozenset({
    "PROFILE_INCOMPLETE",
    "CONFIG_CHECK",
    "INSURANCE_EVIDENCE",
})

#: DOM id of the existing execution-profile section (no new surface).
PRIMARY_ACTION_PROFILE_ANCHOR = "shipment-execution-profile"

#: Stable field anchors reused where they already exist. No generalized focus
#: framework: a code without an entry opens the correct tab and scrolls the
#: existing operational content into view, which is enough.
PRIMARY_ACTION_FIELD_ANCHOR_BY_CODE: dict[str, str] = {
    # Existing customs declaration input on the Nhập khẩu & Giao hàng tab.
    "IMPORT_CUSTOMS": "fld-tk",
}

_STABLE_NO_ALERT = "Lô hàng ổn định — không có cảnh báo"


def compose_primary_action(
    *,
    shipment_id: str,
    dashboard: Mapping[str, Any] | None,
    execution_profile: Mapping[str, Any] | None,
    status_tab: str,
) -> dict[str, str]:
    """Compose ONE primary action from the two existing projections.

    Returns ``{"text", "detail", "priority", "route"}``. Pure: it reads only
    the dashboard view and the execution-profile object the caller already
    holds in memory.
    """

    view = dashboard if isinstance(dashboard, Mapping) else {}
    profile = execution_profile if isinstance(execution_profile, Mapping) else {}

    next_action = view.get("next_action") if isinstance(view.get("next_action"), Mapping) else {}
    top_alert = view.get("top_alert") if isinstance(view.get("top_alert"), Mapping) else {}
    dashboard_severity = text(top_alert.get("severity"))
    dashboard_label = text(next_action.get("label") or top_alert.get("label"))
    dashboard_detail = text(next_action.get("detail") or top_alert.get("detail"))
    has_dashboard = bool(dashboard_label)
    dashboard_route = f"{shipment_path(shipment_id)}?tab={status_tab}"

    profile_next = profile.get("nextAction") if isinstance(profile.get("nextAction"), Mapping) else {}
    profile_code = text(profile_next.get("code"))
    profile_label = text(profile_next.get("label"))
    profile_detail = text(profile_next.get("detail"))
    profile_tone = text(profile_next.get("tone"))
    profile_actionable = bool(profile_code) and profile_code not in {"DONE", "MONITOR"} and bool(profile_label)

    def _dashboard_priority() -> str:
        if dashboard_severity == "critical":
            return "Khan"
        if dashboard_severity in {"warning", "info"}:
            return "CanXuLy"
        return "BinhThuong"

    # 1. A genuine critical dashboard risk is never hidden by a profile gap.
    if dashboard_severity == "critical" and has_dashboard:
        return {"text": dashboard_label, "detail": dashboard_detail,
                "priority": "Khan", "route": dashboard_route}

    # 2+3. A profile red blocker or actionable gap wins over WARNING/INFO.
    if profile_actionable:
        priority = "Khan" if profile_tone == "red" else "CanXuLy"
        if profile_code in PRIMARY_ACTION_PROFILE_SECTION_CODES:
            return {"text": profile_label, "detail": profile_detail, "priority": priority,
                    "route": f"{dashboard_route}#{PRIMARY_ACTION_PROFILE_ANCHOR}"}
        tab = PRIMARY_ACTION_TAB_BY_PROFILE_CODE.get(profile_code, status_tab)
        anchor = PRIMARY_ACTION_FIELD_ANCHOR_BY_CODE.get(profile_code)
        route = f"{shipment_path(shipment_id)}?tab={tab}" + (f"#{anchor}" if anchor else "")
        return {"text": profile_label, "detail": profile_detail,
                "priority": priority, "route": route}

    # 4. DONE/MONITOR preserves the existing dashboard action when one exists.
    if has_dashboard:
        return {"text": dashboard_label, "detail": dashboard_detail,
                "priority": _dashboard_priority(), "route": dashboard_route}

    # 5. Nothing actionable: keep the existing stable behavior, invent nothing.
    return {"text": _STABLE_NO_ALERT, "detail": "",
            "priority": "BinhThuong", "route": dashboard_route}


# --------------------------------------------------------------------------
# Shipment projection
# --------------------------------------------------------------------------

def shipment_projection(
    shipment: Mapping[str, Any],
    *,
    customers: Mapping[str, Any] | None = None,
    contracts: Mapping[str, Any] | None = None,
    quotes: Mapping[str, Any] | None = None,
    dashboard: Mapping[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    ledger: Mapping[str, Any] | None = None,
    agents: Mapping[str, Any] | None = None,
    companies: Mapping[str, Any] | None = None,
    docgen_documents: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    linked_contracts: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    attachments: Mapping[str, list[dict[str, Any]]] | None = None,
    attachment_download: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project one canonical shipment document into the frozen UI shape.

    ``ledger`` / ``agents`` / ``docgen_documents`` / ``linked_contracts`` /
    ``attachments`` are the render-local snapshot the component build path reads
    ONCE and shares across every row (see
    ``core.financial_ledger.load_ledger_snapshot``,
    ``docgen_documents_by_shipment``, ``linked_contracts_index``,
    ``attachments_by_shipment``). They project the same facts as the per-call
    readers and exist only so one render does not repeat the same collection
    reads per shipment; omitting them keeps the original behaviour for every
    standalone caller.

    ``attachment_download`` is the session-scoped byte readback of the ONE
    attachment a user just asked to open (see
    ``views.logi_view_model.ATTACHMENT_DOWNLOAD_KEY``); only that attachment is
    marked downloadable, so the payload never carries the whole Drive folder.
    """
    customers = customers or {}
    contracts = contracts or {}
    quotes = quotes or {}
    companies = companies or {}

    from core.shipment_operations import (
        cargo_summary_for_read,
        compatibility_facts,
        transport_legs_for_read,
    )

    sid = text(shipment.get("id") or shipment.get("shipment_id"))
    transport = _section(shipment, "1.2")
    customs = _section(shipment, "2.4")
    arrival = _section(shipment, "2.6")
    delivery = _section(shipment, "2.7")
    head = _section(shipment, "0.0")
    legs, has_structured_legs = transport_legs_for_read(shipment)
    cargo_summary, has_structured_cargo = cargo_summary_for_read(shipment)
    operational = compatibility_facts(shipment)
    first_leg = legs[0] if legs else {}
    pickup_leg = operational.get("pickup_leg") if isinstance(operational.get("pickup_leg"), Mapping) else {}
    pickup_unit = operational.get("pickup_unit") if isinstance(operational.get("pickup_unit"), Mapping) else {}
    delivery_leg = operational.get("delivery_leg") if isinstance(operational.get("delivery_leg"), Mapping) else {}
    delivery_unit = operational.get("delivery_unit") if isinstance(operational.get("delivery_unit"), Mapping) else {}
    main_leg = operational.get("main_leg") if isinstance(operational.get("main_leg"), Mapping) else {}

    customer_id = text(shipment.get("customer_id"))
    customer_doc = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}
    customer_name = text(shipment.get("customer") or shipment.get("client") or customer_doc.get("name"))

    contract_id = text(shipment.get("contract_id") or _section(shipment, "entrustment").get("contract_no"))
    status_label, status_tone = operational_stage(shipment)

    view = dashboard or {}

    # LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — the execution profile is built
    # ONCE per row and reused: as the ``executionProfile`` payload, as the
    # profile side of the ONE composed primary action, and as the scope filter
    # for the import/delivery checklist (LOGI_SCOPE_AWARE_MISSING_INFO_01).
    # Zero additional reads, zero second derivations.
    from core.shipment_execution_profile import build_execution_profile as _build_execution_profile  # noqa: PLC0415

    execution_profile = _build_execution_profile(shipment, legs=legs)

    # Scope-aware missing docs: reuse SAME execution_profile object.
    # EXECUTION_PROFILE_BUILDS_PER_ROW=1, PRIMARY_CHECKLIST_DB_READS_ADDED=0.
    missing = missing_docs(shipment, execution_profile=execution_profile)

    tab = "nhap" if status_label in {"Chờ thông quan", "Chờ giao"} else ("lay-hang" if status_label == "Chờ lấy hàng" else "lay-hang")
    primary_action = compose_primary_action(
        shipment_id=sid,
        dashboard=view,
        execution_profile=execution_profile,
        status_tab=tab,
    )
    next_text = primary_action["text"]
    next_detail = primary_action["detail"]
    priority = primary_action["priority"]
    next_route = primary_action["route"]

    qty_pkg = text(transport.get("qty_pkg"))
    route_origin = text(operational.get("origin"))
    route_destination = text(operational.get("destination"))

    # LOGI_SHIPMENT_DOCUMENT_WORKFLOW_01 — one pure conditional worklist over
    # the facts this projection already has.  No extra DB read, no workflow
    # collection and no duplicate finance/document truth.
    from core.shipment_document_workflow import (  # noqa: PLC0415
        build_document_workflow,
        match_sub_purchase_contract,
        project_commercial_flow,
    )

    gnt_view = _gnt_projection(shipment, customs, customer_doc, sid)
    finance_view = finance_projection(shipment, quotes, ledger=ledger, agents=agents)
    delivery_note_view = _delivery_note_document(sid, grouped=docgen_documents)
    if not delivery_note_view:
        from core.delivery_note import inspect_delivery_note_source  # noqa: PLC0415

        delivery_note_view = inspect_delivery_note_source(
            shipment,
            customer=customer_doc,
        )
    pxk_view = pxk_projection(
        shipment,
        contracts,
        docgen_documents=docgen_documents,
        linked_contracts=linked_contracts,
    )
    commercial_flow = project_commercial_flow(
        shipment,
        customers=customers,
        companies=companies,
        agents=agents,
    )
    quote_id = text(shipment.get("quote_id"))
    quote_linked = bool(
        quote_id
        and (
            isinstance(quotes.get(quote_id), Mapping)
            or any(
                isinstance(row, Mapping) and text(row.get("id")) == quote_id
                for row in quotes.values()
            )
        )
    )
    candidate_contracts: dict[str, Any] = {}
    if linked_contracts is not None:
        candidate_contracts.update(linked_contracts.get(sid.upper()) or {})
    if contract_id and isinstance(contracts.get(contract_id), Mapping):
        candidate_contracts.setdefault(contract_id, contracts[contract_id])
    sub_purchase_contract = match_sub_purchase_contract(commercial_flow, candidate_contracts)

    document_workflow = build_document_workflow(
        flow=commercial_flow,
        quote_linked=quote_linked,
        gnt=gnt_view,
        delivered=bool(delivery.get("is_delivered")),
        pxk=pxk_view,
        finance=finance_view,
        delivery_note=delivery_note_view,
        sub_purchase_contract=sub_purchase_contract,
    )

    return {
        "id": sid,
        "customer": customer_name,
        "customerMST": text(customer_doc.get("tax_code")),
        "customerId": customer_id,
        "contract": contract_id,
        "route": " → ".join(part for part in (route_origin, route_destination) if part) or UNKNOWN_LABEL,
        "borderVN": route_destination or UNKNOWN_LABEL,
        # Sale owner = the dashboard's authoritative owner resolution
        # (sale_owner / internal_sale_owner / assigned_to / assignee), or
        # "Chưa phân công" when none is assigned. Never a fabricated name.
        "sale": text(view.get("owner")) or UNKNOWN_LABEL,
        # LOGI_UAT_REAL_USE_REPAIR_02 — `support` is the LAST PERSON WHO WROTE
        # this document (core.database sets `updated_by` on every save). It is
        # NOT an assignment: no canonical "assigned support/handling employee"
        # field, writer or RBAC permission exists anywhere in this repo (the
        # only canonical responsibility semantics are core.shipment_dashboard's
        # owner resolution — already projected as `sale` — and the per-task
        # `tasks.assignee` written by core.database.add_task). The UI therefore
        # labels this value for what it provably is ("Cập nhật bởi") instead of
        # claiming a responsibility the data does not carry. Introducing a real
        # assignment field is a product-authority decision, not an inference.
        "support": text(shipment.get("updated_by")),
        "status": status_label,
        "statusTone": status_tone,
        "priority": priority,
        "nextAction": next_text,
        "nextActionDetail": next_detail,
        "nextLabel": "XỬ LÝ NGAY" if priority in {"Khan", "CanXuLy"} else "XEM LÔ",
        "nextRoute": next_route,
        "updated": _ddmmyyyy(shipment.get("updated_at")) if not isinstance(shipment.get("updated_at"), datetime)
        else shipment["updated_at"].strftime("%d/%m/%Y %H:%M"),
        "missingDocs": missing,
        "docs": document_checklist(shipment, execution_profile=execution_profile),
        "commercialFlow": commercial_flow,
        "documentWorkflow": document_workflow,
        # LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — real attachments of the
        # lot: bounded metadata read back from the canonical
        # ``shipment_attachments`` collection. Bytes live in Google Drive; no
        # Drive id, folder id or credential is projected here.
        "attachments": attachment_rows(sid, grouped=attachments, download=attachment_download),
        "version": int(shipment.get("version") or 0),
        "rawStatus": text(shipment.get("status") or head.get("st")),
        "mode": text(operational.get("mode")) or text(head.get("mode")),
        "incoterm": text(head.get("incoterm")),
        # LOGI_SHIPMENT_EXECUTION_PROFILE_01 — ONE derived execution profile for
        # this shipment (core.shipment_execution_profile). It is a PURE
        # projection of the document that was already read for this row plus
        # the transport legs already derived above: no extra reader, no extra
        # query, no second business truth. It carries the Incoterms code +
        # version + named place, the operator-confirmed Trường Thành service
        # scope, the mode/load-model/equipment/truck facts (read from the
        # EXISTING canonical fields), the derived Incoterm insurance obligation
        # as distinct from the persisted actual insurance status, the relevant
        # operational stages with their reason, and the next action those
        # stages justify. Reuses the ONE object built above —
        # EXECUTION_PROFILE_BUILDS_PER_ROW=1.
        "executionProfile": execution_profile,
        "createdAt": _ddmmyyyy(head.get("created_at")),
        # Canonical repeatable operational model.  For a legacy document this
        # is a read-only fallback projection; it becomes canonical only when an
        # operator explicitly saves the transport editor.
        "transportLegs": [_transport_leg_projection(leg) for leg in legs],
        "transportLegsStructured": has_structured_legs,
        "cargoStructured": has_structured_cargo,
        # --- compatibility summaries for old one-value UI/readers ---------
        "pickup": {
            "factory": text(shipment.get("factory_name")),
            "address": text(pickup_leg.get("origin")) or route_origin,
            "contact": text(shipment.get("factory_contact")),
            "phone": text(shipment.get("factory_phone")),
            "pickupTime": _ddmmyyyy(pickup_leg.get("etd") or operational.get("etd")),
            "truckType": text(pickup_unit.get("type_size")),
            "plate": text(pickup_unit.get("number")),
            "driver": text(pickup_unit.get("driver_name")),
            "driverPhone": text(pickup_unit.get("driver_phone")),
            "eta": _ddmmyyyy(pickup_leg.get("eta")),
            "ata": _ddmmyyyy(pickup_leg.get("ata")),
        },
        "transport": {
            "bookingNo": text(main_leg.get("booking_no")),
            "carrier": text(main_leg.get("carrier")),
            "mbl": text(main_leg.get("mbl")),
            "hbl": text(main_leg.get("hbl")),
            "vessel": text(main_leg.get("vessel")),
            "etd": _ddmmyyyy(first_leg.get("etd")),
            "pol": route_origin,
            "pod": route_destination,
            "containerNo": text(operational.get("container_no")),
            "qtyPkg": qty_pkg,
        },
        "cargo": {
            "goodsDescription": text(cargo_summary.get("goods_description")),
            "packs": num(cargo_summary.get("package_count")),
            "weight": num(cargo_summary.get("gross_weight_kg")),
            "cbm": num(cargo_summary.get("cbm")),
            "dims": text(cargo_summary.get("dimensions")),
            "type": text(cargo_summary.get("package_type")),
            "note": text(cargo_summary.get("note")),
            "qtyPkg": qty_pkg,
        },
        "exportInfo": {
            "border": route_origin,
            "declarant": text(shipment.get("china_agent")),
            "eta": _ddmmyyyy(first_leg.get("etd")),
            "ata": _ddmmyyyy(first_leg.get("atd")),
            "state": text(first_leg.get("carrier")),
            "chinaDeclNo": text(shipment.get("china_export_decl_no")),
        },
        # --- TAB 2: import & delivery ---
        "importInfo": {
            "borderVN": route_destination,
            "declarationNo": text(customs.get("tk_no")),
            "regDate": _declaration_date(customs),
            "clearDate": _ddmmyyyy(customs.get("clearance_date")),
            # LOGI_GNT_CANONICAL_FIELDS_01 — ACTUAL import duty and import VAT
            # in VND, keyed by the operator from the real customs notice / GNT.
            # They are recorded facts, never derived: no rate, no HS lookup, no
            # FX, no arithmetic anywhere in this path. Still UNKNOWN (None →
            # "—") until an operator records them, because a blank here is a
            # statement about knowledge, not about money.
            "tax": num(customs.get("import_duty_amount")),
            "vat": num(customs.get("import_vat_amount")),
            "inspection": text(customs.get("phan_luong")),
            "customsStatus": bool(customs.get("customs_status")),
            "license": "",
            "gnt": gnt_view,
            "arrivalDate": _ddmmyyyy(arrival.get("arrival_date")) or _ddmmyyyy(operational.get("eta")),
            "freeTime": num(arrival.get("free_time")),
            "truckVN": text(delivery_unit.get("type_size")),
            "plateVN": text(delivery_unit.get("number")),
            "driverVN": text(delivery_unit.get("driver_name")),
            "schedule": _ddmmyyyy(delivery.get("delivery_date") or delivery_leg.get("eta") or delivery_leg.get("etd")),
            "deliveryAddr": text(delivery.get("addr")),
            "receiver": text(delivery.get("receiver_name")),
            "receiverPhone": text(delivery.get("phone_receiver")),
            "receiverTitle": text(delivery.get("receiver_title")),
            "deliveryLocation": text(delivery.get("delivery_location")),
            "delivered": bool(delivery.get("is_delivered")),
            "actualDelivery": _ddmmyyyy(delivery.get("delivered_at") or delivery.get("delivery_date"))
            if delivery.get("is_delivered") else "",
        },
        # --- TAB 3 ---
        "finance": finance_view,
        # --- TAB 4 ---
        "pxk": pxk_view,
        # --- TAB 5 ---
        "timeline": list(history or []),
        # Dashboard/readiness evidence (canonical projection, read-only).
        "ops": {
            "financialFlag": text(view.get("financial_flag")),
            "financialLabel": text(view.get("financial_label")),
            "alerts": [
                {"code": text(a.get("code")), "severity": text(a.get("severity")),
                 "title": text(a.get("label")), "message": text(a.get("detail"))}
                for a in (view.get("alerts") or []) if isinstance(a, Mapping)
            ],
            "arrivalDateLabel": text(view.get("arrival_date_label")),
            "freeTimeExpiryLabel": text(view.get("free_time_expiry_label")),
            "daysRemaining": view.get("days_remaining"),
        },
        # --- Tracking: only real transport/state facts, no fabricated GPS ---
        "tracking": tracking_projection(shipment),
    }


def docgen_documents_by_shipment(
    documents: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Canonical docgen metadata for ALL shipments, read ONCE and grouped.

    PERFORMANCE REPAIR: ``_pxk_document`` used to read ``docgen_documents``
    once per projected shipment (one query per worklist row). This performs the
    same read — same collection, same ``is_deleted`` filter, same ``_id``
    exclusion, same ``id`` keying — a single time for the whole render and
    groups it by shipment in memory. Document identity and persistence are
    untouched; only repeated canonical reads are removed.

    ``documents`` lets the caller hand over the raw ``load_docgen_documents()``
    result it already read for this render (the view-model shares ONE read
    between this grouping and the C1 contract payload); ``None`` keeps the read.
    """
    from core.database import load_docgen_documents

    if documents is None:
        try:
            documents = load_docgen_documents() or {}
        except Exception:  # noqa: BLE001 - a docgen read failure must not blank the desk
            return {}
    grouped: dict[str, dict[str, Any]] = {}
    for record_id, doc in documents.items():
        if not isinstance(doc, Mapping):
            continue
        scope = text(doc.get("shipment_id"))
        if not scope:
            continue
        grouped.setdefault(scope, {})[record_id] = doc
    return grouped


def attachments_by_shipment(*, db: Any = _UNSET_DB) -> dict[str, list[dict[str, Any]]]:
    """Attachment METADATA for ALL shipments, read ONCE and grouped.

    Same performance repair as ``docgen_documents_by_shipment``: the canonical
    ``shipment_attachments`` collection is read a single time per render
    instead of once per projected row. Google Drive holds the bytes; only the
    bounded metadata described in ``core.shipment_attachments`` is grouped here.
    """
    from core.database import load_shipment_attachments

    try:
        records = load_shipment_attachments(db=db) or {}
    except Exception:  # noqa: BLE001 - an attachment read failure must not blank the desk
        return {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records.values():
        if not isinstance(record, Mapping):
            continue
        scope = text(record.get("shipment_id"))
        if not scope:
            continue
        grouped.setdefault(scope, []).append(dict(record))
    return grouped


def attachment_rows(
    shipment_id: str,
    *,
    grouped: Mapping[str, list[dict[str, Any]]] | None = None,
    download: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """UI projection of ONE shipment's attachments (``grouped`` = render-local)."""
    from core.shipment_attachments import project_attachments

    if not shipment_id:
        return []
    if grouped is None:
        from core.database import load_shipment_attachments

        try:
            records: Any = load_shipment_attachments(shipment_id) or {}
        except Exception:  # noqa: BLE001
            return []
    else:
        records = grouped.get(shipment_id) or []
    return project_attachments(records, download=download)


def linked_contracts_index(contracts: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """In-memory ``load_contracts_for_shipment`` index over contracts already read.

    The canonical reader resolves a shipment's linked contracts by scanning the
    whole ``contracts`` collection; the component render already holds those
    exact records (``core.database.load_contracts`` returns the same documents,
    merely re-keyed by ``ContractNo``). Building the same linkage here therefore
    costs no read at all while keeping the identical result shape: contract
    ``id`` → document, matched case-insensitively on ``shipment_ids`` /
    ``shipment_id``.
    """
    index: dict[str, dict[str, Any]] = {}
    for contract in (contracts or {}).values():
        if not isinstance(contract, Mapping) or contract.get("id") is None:
            continue
        contract_id = str(contract.get("id"))
        shipment_ids = [str(item).upper() for item in (contract.get("shipment_ids") or [])]
        single = str(contract.get("shipment_id") or "").upper()
        for scope in shipment_ids:
            index.setdefault(scope, {})[contract_id] = contract
        if single:
            index.setdefault(single, {})[contract_id] = contract
    return index


def pxk_projection(
    shipment: Mapping[str, Any],
    contracts: Mapping[str, Any],
    *,
    docgen_documents: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    linked_contracts: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """PXK facts + the real delivery gate, from core.docgen rules.

    ``docgen_documents`` (``docgen_documents_by_shipment``) and
    ``linked_contracts`` (``linked_contracts_index``) are the render-local
    snapshot the component build path passes; a standalone caller keeps the
    per-call readers unchanged.
    """
    from core.docgen import rules as docgen_rules

    shipment_id = text(shipment.get("id"))
    delivery = _section(shipment, "2.7")
    delivered = bool(delivery.get("is_delivered"))
    missing_delivery = docgen_rules.delivery_facts_missing(delivery) if delivered else []
    contract_id = text(shipment.get("contract_id") or _section(shipment, "entrustment").get("contract_no"))
    contract = contracts.get(contract_id) if isinstance(contracts.get(contract_id), Mapping) else {}
    if not contract:
        # Same canonical N:M linkage the contract page writes ("Lô liên kết →
        # Thêm"): exactly one linked contract is an unambiguous source, several
        # stay UNKNOWN rather than being guessed for display.
        if linked_contracts is not None:
            linked = linked_contracts.get(shipment_id.upper()) or {}
        else:
            from core.database import load_contracts_for_shipment

            try:
                linked = load_contracts_for_shipment(shipment_id) or {}
            except Exception:  # noqa: BLE001 - a linkage read failure must not blank the desk
                linked = {}
        if len(linked) == 1:
            contract_id, contract = next(iter(linked.items()))

    generated = _pxk_document(shipment_id, grouped=docgen_documents)
    return {
        "source": contract_id,
        "sourceName": text(contract.get("contract_no") or contract.get("hdmb_no") or contract.get("hdnt_no")),
        "delivered": delivered,
        "gateOpen": delivered and not missing_delivery,
        "missingDeliveryFacts": list(missing_delivery),
        # Read back from the canonical docgen metadata: the number/date/done
        # facts describe a file that really exists, they are never fabricated.
        "number": generated.get("number", ""),
        "date": generated.get("date", ""),
        "place": text(delivery.get("delivery_location") or delivery.get("addr")),
        "receiver": text(delivery.get("receiver_name")),
        "role": text(delivery.get("receiver_title")),
        "done": bool(generated),
        "document": generated or None,
    }


def _pxk_document(
    shipment_id: str,
    *,
    grouped: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Latest PXK generated for one shipment: metadata + downloadable file.

    Reads the canonical ``docgen_documents`` collection (the writer the contract
    documents already use) and pairs it with the session file store through the
    existing ``views.logi_c1.document_projection``. Returns ``{}`` when nothing
    has been generated — UNKNOWN, never a fabricated "done".

    ``grouped`` is the whole canonical collection, already loaded and grouped by
    shipment (see ``docgen_documents_by_shipment``). When it is supplied this
    shipment's slice comes from memory — an empty slice means "no document for
    this shipment", exactly like the empty result of the single-shipment read —
    and only a caller that supplies nothing pays for the per-shipment read.
    """
    if not shipment_id:
        return {}
    if grouped is None:
        from core.database import load_docgen_documents

        try:
            docs = load_docgen_documents(shipment_id) or {}
        except Exception:  # noqa: BLE001 - a docgen read failure must not blank the desk
            return {}
    else:
        docs = grouped.get(shipment_id) or {}
    pxk = [d for d in docs.values()
           if isinstance(d, Mapping) and text(d.get("document_type")).upper() == "PXK"]
    if not pxk:
        return {}

    def _revision(doc: Mapping[str, Any]) -> int:
        try:
            return int(doc.get("generation_revision") or doc.get("revision") or 1)
        except Exception:  # noqa: BLE001
            return 1

    latest = max(pxk, key=_revision)
    snapshot = latest.get("source_snapshot")
    snapshot = snapshot if isinstance(snapshot, Mapping) else {}
    from views import logi_c1

    file_view = logi_c1.document_projection(latest, logi_c1.stored_outputs(shipment_id))
    return {
        "documentId": file_view["documentId"],
        "recordId": file_view["id"],
        "revision": file_view["revision"],
        "status": file_view["status"],
        "fileName": file_view["fileName"],
        "mime": file_view["mime"],
        "generatedAt": file_view["generatedAt"],
        "generatedBy": file_view["generatedBy"],
        "downloadAvailable": file_view["downloadAvailable"],
        "downloadBase64": file_view["downloadBase64"],
        "number": text(snapshot.get("pxk_no")),
        "date": text(snapshot.get("pxk_date")),
    }


def _delivery_note_document(
    shipment_id: str,
    *,
    grouped: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Latest durable delivery-note metadata for one shipment."""
    if not shipment_id:
        return {}
    if grouped is None:
        from core.database import load_docgen_documents

        try:
            docs = load_docgen_documents(shipment_id) or {}
        except Exception:  # noqa: BLE001
            return {}
    else:
        docs = grouped.get(shipment_id) or {}

    rows = [
        doc for doc in docs.values()
        if isinstance(doc, Mapping)
        and text(doc.get("document_type")).upper() == "DELIVERY_NOTE"
    ]
    if not rows:
        return {}

    def _revision(doc: Mapping[str, Any]) -> int:
        try:
            return int(doc.get("generation_revision") or doc.get("revision") or 1)
        except Exception:  # noqa: BLE001
            return 1

    latest = max(rows, key=_revision)
    snapshot = latest.get("source_snapshot")
    snapshot = snapshot if isinstance(snapshot, Mapping) else {}
    return {
        "done": True,
        "recordId": text(latest.get("id")),
        "documentId": text(latest.get("document_id")),
        "revision": _revision(latest),
        "number": text(snapshot.get("delivery_note_no")),
        "date": text(snapshot.get("delivery_note_date")),
        "fileName": text(latest.get("output_file_name")),
        "status": text(latest.get("status")),
    }


def tracking_projection(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Tracking from real transport/state facts. No invented GPS position."""
    from core.config import CARRIER_LINKS

    from core.shipment_operations import compatibility_facts

    customs = _section(shipment, "2.4")
    delivery = _section(shipment, "2.7")
    arrival = _section(shipment, "2.6")
    status_label, tone = operational_stage(shipment)
    operational = compatibility_facts(shipment)
    main_leg = operational.get("main_leg") if isinstance(operational.get("main_leg"), Mapping) else {}

    carrier = text(main_leg.get("carrier"))
    reference = text(main_leg.get("booking_no") or main_leg.get("mbl") or operational.get("container_no"))
    link_template = CARRIER_LINKS.get(carrier)
    tracking_url = link_template.format(ref=reference) if link_template and reference else ""

    milestones: list[dict[str, Any]] = []
    if text(operational.get("etd")):
        milestones.append({"time": _ddmmyyyy(operational.get("etd")), "title": "ETD — rời nơi lấy hàng",
                           "desc": text(operational.get("origin")), "done": True, "tone": "green"})
    arrival_fact = arrival.get("arrival_date") or operational.get("eta")
    if text(arrival_fact):
        milestones.append({"time": _ddmmyyyy(arrival_fact), "title": "ETA — về cửa khẩu/kho đích",
                           "desc": text(operational.get("destination")), "done": bool(customs.get("tk_no")), "tone": "blue"})
    if text(customs.get("tk_no")):
        milestones.append({"time": _declaration_date(customs), "title": "Đăng ký tờ khai nhập khẩu",
                           "desc": f"TK {text(customs.get('tk_no'))} · luồng {text(customs.get('phan_luong')) or 'chờ phân luồng'}",
                           "done": True, "tone": "blue"})
    if customs.get("customs_status"):
        milestones.append({"time": _ddmmyyyy(customs.get("clearance_date")), "title": "Đã thông quan",
                           "desc": "", "done": True, "tone": "green"})
    if text(delivery.get("delivery_date")):
        milestones.append({"time": _ddmmyyyy(delivery.get("delivery_date")), "title": "Lịch giao hàng",
                           "desc": text(delivery.get("addr")), "done": bool(delivery.get("is_delivered")),
                           "tone": "green" if delivery.get("is_delivered") else "amber"})
    if delivery.get("is_delivered"):
        milestones.append({"time": _ddmmyyyy(delivery.get("delivered_at")), "title": "Đã giao hàng",
                           "desc": text(delivery.get("receiver_name")), "done": True, "tone": "green"})

    return {
        "status": status_label,
        "statusTone": tone,
        "carrier": carrier,
        "reference": reference,
        "trackingUrl": tracking_url,
        "hasLivePosition": False,
        "positionNote": "Không có dữ liệu vị trí thời gian thực — chỉ hiển hiện trạng thái và mốc vận chuyển có thật.",
        "milestones": milestones,
    }
