"""Nguồn sự thật duy nhất cho tính toán tài chính Shipment."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Iterable, Mapping

from core.utils import money_round, to_decimal


@dataclass(frozen=True)
class FinancialSummary:
    revenue_net: Decimal
    output_vat: Decimal
    receivable: Decimal
    cost: Decimal
    commission: Decimal
    gross_profit: Decimal
    paid: Decimal
    debt: Decimal
    currency: str = "VND"

    def as_legacy_dict(self) -> dict[str, float | str]:
        # revenue giữ nghĩa "tổng phải thu" để tương thích UI cũ.
        return {
            "revenue": float(self.receivable),
            "revenue_net": float(self.revenue_net),
            "output_vat": float(self.output_vat),
            "receivable": float(self.receivable),
            "cost": float(self.cost),
            "commission": float(self.commission),
            "profit": float(self.gross_profit),
            "paid": float(self.paid),
            "debt": float(self.debt),
            "currency": self.currency,
        }


def _commission_amount(commission: Any) -> Decimal:
    if isinstance(commission, Mapping):
        explicit = to_decimal(commission.get("total"))
        if explicit != 0:
            return explicit
        commission = commission.get("list", [])
    if isinstance(commission, Iterable) and not isinstance(commission, (str, bytes, Mapping)):
        return sum((to_decimal(item.get("amount")) for item in commission if isinstance(item, Mapping)), Decimal("0"))
    return to_decimal(commission)


def calculate_shipment_financials(
    details: Iterable[Mapping[str, Any]] | None,
    commission: Any = None,
    payments: Iterable[Mapping[str, Any]] | None = None,
    currency: str = "VND",
) -> dict[str, float | str]:
    revenue_net = Decimal("0")
    output_vat = Decimal("0")
    total_cost = Decimal("0")

    for item in details or []:
        qty = to_decimal(item.get("qty", 1))
        price_out = to_decimal(item.get("price", item.get("price_out", 0)))
        price_in = to_decimal(item.get("cost", item.get("price_in", 0)))
        vat_rate = to_decimal(item.get("vat_line", item.get("vat", 0)))
        line_net = qty * price_out
        revenue_net += line_net
        output_vat += line_net * vat_rate / Decimal("100")
        total_cost += qty * price_in

    receivable = revenue_net + output_vat
    commission_total = _commission_amount(commission)
    paid = sum(
        (
            to_decimal(p.get("amount"))
            for p in payments or []
            if isinstance(p, Mapping)
            and str(p.get("status") or "").strip().lower() not in {"reversed", "cancelled", "void"}
            and not bool(p.get("is_reversed"))
        ),
        Decimal("0"),
    )
    # Lợi nhuận không bao gồm VAT đầu ra.
    gross_profit = revenue_net - total_cost - commission_total
    debt = receivable - paid

    summary = FinancialSummary(
        revenue_net=money_round(revenue_net, currency),
        output_vat=money_round(output_vat, currency),
        receivable=money_round(receivable, currency),
        cost=money_round(total_cost, currency),
        commission=money_round(commission_total, currency),
        gross_profit=money_round(gross_profit, currency),
        paid=money_round(paid, currency),
        debt=money_round(debt, currency),
        currency=currency.upper(),
    )
    return summary.as_legacy_dict()


def calculate_from_shipment(shipment: Mapping[str, Any]) -> dict[str, float | str]:
    finance = shipment.get("data", {}).get("3.4", {})
    return calculate_shipment_financials(
        finance.get("details", []),
        finance.get("commission", {}),
        finance.get("payments", []),
        shipment.get("currency", finance.get("currency", "VND")),
    )


def apply_financial_snapshot(shipment: dict[str, Any]) -> dict[str, float | str]:
    summary = calculate_from_shipment(shipment)
    finance = shipment.setdefault("data", {}).setdefault("3.4", {})
    finance["out"] = summary["receivable"]
    finance["out_net"] = summary["revenue_net"]
    finance["output_vat"] = summary["output_vat"]
    finance["in"] = summary["cost"]
    finance["profit"] = summary["profit"]
    finance["paid"] = summary["paid"]
    finance["debt"] = summary["debt"]
    finance["currency"] = summary["currency"]
    return summary
