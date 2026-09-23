"""Deterministic intl payment comparator calculator (LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01).

Two modes:
  A. Tôi chuyển USD  — forward from gross_usd to net CNY received.
  B. Đại lý cần nhận X CNY — reverse solving for required gross USD including
      recipient bank fee and agent fee (China tranche logic).

Vietnam bank cost: for each USD route using Agribank/BIDV sell.

Comparison: outside-CNY route vs USD routes.

Rounding: Internal Decimal precision preserved; display formatting is separate.
Never round USD to integer during formulas.

Formula version is explicit for snapshot provenance.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, getcontext
from typing import Any

# Use high precision for intermediate calculations
getcontext().prec = 28

FORMULA_VERSION = "1.0.0"

DEFAULT_RECIPIENT_BANK_FEE_USD = Decimal("35")
DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY = Decimal("150")
DEFAULT_CHINA_TRANCHE_SIZE_USD = Decimal("10000")
DEFAULT_HK_AGENT_FEE_PCT = Decimal("0.02")
DEFAULT_VN_SWIFT_FEE_USD = Decimal("5")
DEFAULT_VN_PCT_FEE = Decimal("0.0015")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    txt = str(value).strip()
    if not txt:
        return None
    # Remove commas and spaces
    txt = txt.replace(",", "").replace(" ", "")
    try:
        d = Decimal(txt)
    except Exception:
        return None
    if not d.is_finite():
        return None
    return d


def _quantize_display_usd(d: Decimal) -> str:
    return format(d.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP), "f")


def _quantize_display_cny(d: Decimal) -> str:
    return format(d.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP), "f")


def _quantize_display_vnd(d: Decimal) -> str:
    # whole VND
    return format(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP), "f")


def china_agent_fee_cny(
    gross_usd: Decimal,
    fee_per_tranche: Decimal = DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY,
    tranche_size: Decimal = DEFAULT_CHINA_TRANCHE_SIZE_USD,
) -> Decimal:
    """150 CNY per STARTED 10,000 USD tranche, minimum one tranche.

    gross_usd >0 => at least 1 tranche. gross_usd <=0 => 0.
    Mirrors task spec: 1-10,000 =>150, 10,001-20,000=>300.
    """
    if gross_usd <= 0:
        return Decimal("0")
    # ceil(gross / tranche)
    tranches = (gross_usd / tranche_size).to_integral_value(rounding=ROUND_CEILING)
    if tranches < 1:
        tranches = Decimal("1")
    return tranches * fee_per_tranche


def tranche_count(gross_usd: Decimal, tranche_size: Decimal = DEFAULT_CHINA_TRANCHE_SIZE_USD) -> int:
    if gross_usd <= 0:
        return 0
    t = (gross_usd / tranche_size).to_integral_value(rounding=ROUND_CEILING)
    return int(t)


def china_forward(
    gross_usd: Decimal | Any,
    usd_to_cny: Decimal | Any,
    recipient_bank_fee_usd: Decimal | Any = DEFAULT_RECIPIENT_BANK_FEE_USD,
    fee_per_tranche: Decimal | Any = DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY,
    tranche_size: Decimal | Any = DEFAULT_CHINA_TRANCHE_SIZE_USD,
) -> dict[str, Any]:
    """Mode A China forward: I send gross_usd, agent receives net CNY.

    Returns dict with precise Decimals and trace.
    """
    gross_usd_d = _to_decimal(gross_usd)
    usd_to_cny_d = _to_decimal(usd_to_cny)
    recipient_fee_d = _to_decimal(recipient_bank_fee_usd) or DEFAULT_RECIPIENT_BANK_FEE_USD
    fee_per_tranche_d = _to_decimal(fee_per_tranche) or DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY
    tranche_size_d = _to_decimal(tranche_size) or DEFAULT_CHINA_TRANCHE_SIZE_USD

    if gross_usd_d is None or usd_to_cny_d is None:
        raise ValueError("gross_usd and usd_to_cny required")
    if gross_usd_d < 0 or usd_to_cny_d <= 0:
        raise ValueError("invalid amount/rate")

    usd_after_bank = gross_usd_d - recipient_fee_d
    gross_cny = usd_after_bank * usd_to_cny_d
    china_fee = china_agent_fee_cny(gross_usd_d, fee_per_tranche_d, tranche_size_d)
    net_cny = gross_cny - china_fee
    # if usd_after_bank negative, net may be negative; caller decides
    return {
        "gross_usd": gross_usd_d,
        "recipient_bank_fee_usd": recipient_fee_d,
        "usd_after_bank": usd_after_bank,
        "usd_to_cny": usd_to_cny_d,
        "gross_cny": gross_cny,
        "china_agent_fee_cny": china_fee,
        "net_cny_received": net_cny,
        "tranche_count": tranche_count(gross_usd_d, tranche_size_d),
        "fee_per_tranche": fee_per_tranche_d,
        "tranche_size": tranche_size_d,
        "formula_version": FORMULA_VERSION,
        "trace": [
            f"usd_after_bank = gross_usd - recipient_fee = {gross_usd_d} - {recipient_fee_d} = {usd_after_bank}",
            f"gross_cny = usd_after_bank * usd_to_cny = {usd_after_bank} * {usd_to_cny_d} = {gross_cny}",
            f"china_agent_fee = ceil(gross_usd/{tranche_size_d})*{fee_per_tranche_d} = {china_fee} ({tranche_count(gross_usd_d, tranche_size_d)} tranche(s))",
            f"net_cny = gross_cny - china_fee = {gross_cny} - {china_fee} = {net_cny}",
        ],
    }


def hk_forward(
    gross_usd: Decimal | Any,
    usd_to_cny: Decimal | Any,
    recipient_bank_fee_usd: Decimal | Any = DEFAULT_RECIPIENT_BANK_FEE_USD,
    hk_agent_fee_pct: Decimal | Any = DEFAULT_HK_AGENT_FEE_PCT,
) -> dict[str, Any]:
    """Mode A Hong Kong forward."""
    gross_usd_d = _to_decimal(gross_usd)
    usd_to_cny_d = _to_decimal(usd_to_cny)
    recipient_fee_d = _to_decimal(recipient_bank_fee_usd) or DEFAULT_RECIPIENT_BANK_FEE_USD
    hk_pct_d = _to_decimal(hk_agent_fee_pct)
    if hk_pct_d is None:
        hk_pct_d = DEFAULT_HK_AGENT_FEE_PCT

    if gross_usd_d is None or usd_to_cny_d is None:
        raise ValueError("gross_usd and usd_to_cny required")
    if gross_usd_d < 0 or usd_to_cny_d <= 0:
        raise ValueError("invalid amount/rate")

    usd_after_bank = gross_usd_d - recipient_fee_d
    hk_fee_usd = usd_after_bank * hk_pct_d
    usd_for_conversion = usd_after_bank - hk_fee_usd
    net_cny = usd_for_conversion * usd_to_cny_d

    return {
        "gross_usd": gross_usd_d,
        "recipient_bank_fee_usd": recipient_fee_d,
        "usd_after_bank": usd_after_bank,
        "hk_agent_fee_pct": hk_pct_d,
        "hk_agent_fee_usd": hk_fee_usd,
        "usd_for_conversion": usd_for_conversion,
        "usd_to_cny": usd_to_cny_d,
        "net_cny_received": net_cny,
        "formula_version": FORMULA_VERSION,
        "trace": [
            f"usd_after_bank = gross_usd - 35 = {gross_usd_d} - {recipient_fee_d} = {usd_after_bank}",
            f"hk_agent_fee_usd = usd_after_bank * {hk_pct_d} = {hk_fee_usd}",
            f"usd_for_conversion = usd_after_bank - hk_fee = {usd_for_conversion}",
            f"net_cny = usd_for_conversion * usd_to_cny = {net_cny}",
        ],
    }


def china_reverse(
    target_cny: Decimal | Any,
    usd_to_cny: Decimal | Any,
    recipient_bank_fee_usd: Decimal | Any = DEFAULT_RECIPIENT_BANK_FEE_USD,
    fee_per_tranche: Decimal | Any = DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY,
    tranche_size: Decimal | Any = DEFAULT_CHINA_TRANCHE_SIZE_USD,
) -> dict[str, Any]:
    """Mode B China reverse: agent must receive target_cny. Solve for gross_usd.

    Includes recipient bank fee + tranche fee.
    Uses bounded deterministic iteration until tranche count stabilizes.
    No brute loops.

    Formula: target = (gross - fee_bank)*rate - fee_china(gross)
             => gross = (target + fee_china(gross))/rate + fee_bank
    """
    target_d = _to_decimal(target_cny)
    usd_to_cny_d = _to_decimal(usd_to_cny)
    recipient_fee_d = _to_decimal(recipient_bank_fee_usd) or DEFAULT_RECIPIENT_BANK_FEE_USD
    fee_per_tranche_d = _to_decimal(fee_per_tranche) or DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY
    tranche_size_d = _to_decimal(tranche_size) or DEFAULT_CHINA_TRANCHE_SIZE_USD

    if target_d is None or usd_to_cny_d is None:
        raise ValueError("target_cny and usd_to_cny required")
    if target_d < 0 or usd_to_cny_d <= 0:
        raise ValueError("invalid target/rate")

    # Start with assumption 1 tranche
    fee = fee_per_tranche_d  # minimum
    # Determine stable tranche via iteration
    # We'll do up to 10 iterations (bounded)
    gross = (target_d + fee) / usd_to_cny_d + recipient_fee_d
    for _ in range(10):
        tranches = tranche_count(gross, tranche_size_d)
        # ensure at least 1
        if tranches < 1 and target_d > 0:
            tranches = 1
        new_fee = Decimal(tranches) * fee_per_tranche_d if tranches > 0 else Decimal("0")
        # If target is 0, fee should be 0? but spec says minimum one tranche for positive; if target 0, gross would be recipient_fee + min fee/rate?
        # For reverse, if target ==0, we might still have fee? But to keep stable, use same logic.
        if target_d == 0:
            new_fee = Decimal("0")
            # but gross would be recipient_fee
        if new_fee == fee:
            # also verify gross computed from new_fee is stable
            # need one more check to ensure tranches for new gross still same
            new_gross = (target_d + new_fee) / usd_to_cny_d + recipient_fee_d
            if tranche_count(new_gross, tranche_size_d) == tranches:
                gross = new_gross
                fee = new_fee
                break
            else:
                fee = new_fee
                gross = new_gross
                continue
        fee = new_fee
        gross = (target_d + fee) / usd_to_cny_d + recipient_fee_d
    else:
        # reached max iter, use last
        pass

    # Recompute tranche count for final gross
    final_tranches = tranche_count(gross, tranche_size_d) if target_d != 0 else 0
    if target_d != 0 and final_tranches < 1:
        final_tranches = 1
        fee = fee_per_tranche_d
        gross = (target_d + fee) / usd_to_cny_d + recipient_fee_d
        final_tranches = tranche_count(gross, tranche_size_d)
        fee = Decimal(final_tranches) * fee_per_tranche_d

    # Also compute forward verification: ensure (gross-35)*rate - fee == target (within precision)
    usd_after_bank = gross - recipient_fee_d
    gross_cny = usd_after_bank * usd_to_cny_d
    net_cny = gross_cny - fee

    # Due to Decimal precision, net_cny should equal target exactly for our construction
    # Provide also without fee for comparison (per spec §12)
    gross_without_fee = target_d / usd_to_cny_d + recipient_fee_d

    return {
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": recipient_fee_d,
        "fee_per_tranche": fee_per_tranche_d,
        "tranche_size": tranche_size_d,
        "tranche_count": final_tranches,
        "china_agent_fee_cny": fee,
        "gross_usd_required": gross,
        "usd_after_bank": usd_after_bank,
        "gross_cny": gross_cny,
        "net_cny_received": net_cny,  # should == target
        "gross_usd_without_fee": gross_without_fee,  # comparison only, not production
        "fee_delta_gross": gross - gross_without_fee,
        "formula_version": FORMULA_VERSION,
        "trace": [
            f"Solve: target={(target_d)} = (gross - {recipient_fee_d})*{usd_to_cny_d} - fee(gross)",
            f"Iterate tranche until stable: fee={fee}, tranches={final_tranches}, gross={gross}",
            f"Verify: ({gross} - {recipient_fee_d})*{usd_to_cny_d} - {fee} = {net_cny} (target {target_d})",
            f"Without fee (comparison only): gross_without_fee = {target_d}/{usd_to_cny_d}+{recipient_fee_d} = {gross_without_fee}",
        ],
    }


def hk_reverse(
    target_cny: Decimal | Any,
    usd_to_cny: Decimal | Any,
    recipient_bank_fee_usd: Decimal | Any = DEFAULT_RECIPIENT_BANK_FEE_USD,
    hk_agent_fee_pct: Decimal | Any = DEFAULT_HK_AGENT_FEE_PCT,
) -> dict[str, Any]:
    """HK reverse: gross = target / (rate*(1-pct)) + fee_bank."""
    target_d = _to_decimal(target_cny)
    usd_to_cny_d = _to_decimal(usd_to_cny)
    recipient_fee_d = _to_decimal(recipient_bank_fee_usd) or DEFAULT_RECIPIENT_BANK_FEE_USD
    hk_pct_d = _to_decimal(hk_agent_fee_pct)
    if hk_pct_d is None:
        hk_pct_d = DEFAULT_HK_AGENT_FEE_PCT

    if target_d is None or usd_to_cny_d is None:
        raise ValueError("target and rate required")
    if target_d < 0 or usd_to_cny_d <= 0:
        raise ValueError("invalid")
    if hk_pct_d >= 1 or hk_pct_d < 0:
        raise ValueError("pct in [0,1)")

    denom = usd_to_cny_d * (Decimal("1") - hk_pct_d)
    gross = target_d / denom + recipient_fee_d
    usd_after_bank = gross - recipient_fee_d
    hk_fee = usd_after_bank * hk_pct_d
    usd_for_conv = usd_after_bank - hk_fee
    net_cny = usd_for_conv * usd_to_cny_d

    return {
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": recipient_fee_d,
        "hk_agent_fee_pct": hk_pct_d,
        "gross_usd_required": gross,
        "usd_after_bank": usd_after_bank,
        "hk_agent_fee_usd": hk_fee,
        "usd_for_conversion": usd_for_conv,
        "net_cny_received": net_cny,
        "formula_version": FORMULA_VERSION,
        "trace": [
            f"gross = target / (rate*(1-pct)) + fee_bank = {target_d} / ({usd_to_cny_d}*(1-{hk_pct_d})) + {recipient_fee_d} = {gross}",
        ],
    }


def vietnam_bank_cost(
    gross_usd: Decimal | Any,
    usd_sell_vnd: Decimal | Any,
    vn_swift_fee_usd: Decimal | Any = DEFAULT_VN_SWIFT_FEE_USD,
    vn_pct_fee: Decimal | Any = DEFAULT_VN_PCT_FEE,
) -> dict[str, Any]:
    """Vietnam bank cost for a USD route.

    Formula:
      principal_vnd = gross_usd * usd_sell_vnd
      swift_fee_vnd = 5 * usd_sell_vnd
      vn_bank_pct_fee_vnd = principal_vnd * 0.0015
      total_vnd = principal + swift + pct
    No silent VAT etc.
    """
    gross_d = _to_decimal(gross_usd)
    sell_d = _to_decimal(usd_sell_vnd)
    swift_usd_d = _to_decimal(vn_swift_fee_usd) or DEFAULT_VN_SWIFT_FEE_USD
    pct_d = _to_decimal(vn_pct_fee)
    if pct_d is None:
        pct_d = DEFAULT_VN_PCT_FEE

    if gross_d is None or sell_d is None:
        raise ValueError("gross_usd and sell required")
    if gross_d < 0 or sell_d <= 0:
        raise ValueError("invalid")

    principal = gross_d * sell_d
    swift_vnd = swift_usd_d * sell_d
    pct_fee = principal * pct_d
    total = principal + swift_vnd + pct_fee

    return {
        "gross_usd": gross_d,
        "usd_sell_vnd": sell_d,
        "vn_swift_fee_usd": swift_usd_d,
        "vn_pct_fee_rate": pct_d,
        "principal_vnd": principal,
        "swift_fee_vnd": swift_vnd,
        "vn_pct_fee_vnd": pct_fee,
        "total_vnd": total,
        "formula_version": FORMULA_VERSION,
    }


def outside_cny_route(target_cny: Decimal | Any, outside_cny_vnd: Decimal | Any) -> dict[str, Any]:
    target_d = _to_decimal(target_cny)
    rate_d = _to_decimal(outside_cny_vnd)
    if target_d is None or rate_d is None:
        raise ValueError("target and outside rate required")
    if target_d < 0 or rate_d <= 0:
        raise ValueError("invalid")
    total = target_d * rate_d
    return {
        "target_cny": target_d,
        "outside_cny_vnd": rate_d,
        "total_vnd": total,
        "formula_version": FORMULA_VERSION,
    }


def comparison_for_target_cny(
    target_cny: Decimal | Any,
    outside_cny_vnd: Decimal | Any,
    usd_to_cny: Decimal | Any,
    agribank_sell_vnd: Decimal | Any,
    bidv_sell_vnd: Decimal | Any | None,
    recipient_bank_fee_usd: Decimal | Any = DEFAULT_RECIPIENT_BANK_FEE_USD,
    china_fee_per_tranche: Decimal | Any = DEFAULT_CHINA_AGENT_FEE_PER_TRANCHE_CNY,
    china_tranche_size: Decimal | Any = DEFAULT_CHINA_TRANCHE_SIZE_USD,
    hk_fee_pct: Decimal | Any = DEFAULT_HK_AGENT_FEE_PCT,
    vn_swift_fee_usd: Decimal | Any = DEFAULT_VN_SWIFT_FEE_USD,
    vn_pct_fee: Decimal | Any = DEFAULT_VN_PCT_FEE,
) -> dict[str, Any]:
    """Comparison for Mode B target_cny across all routes.

    Returns outside_total and 4 USD routes (china agri, china bidv, hk agri, hk bidv)
    Each shows required gross, fees, fx, principal, vn fees, total, delta.
    BIDV may be None => RATE_UNAVAILABLE.
    """
    target_d = _to_decimal(target_cny)
    outside_d = _to_decimal(outside_cny_vnd)
    usd_to_cny_d = _to_decimal(usd_to_cny)
    agri_d = _to_decimal(agribank_sell_vnd)
    bidv_d = _to_decimal(bidv_sell_vnd) if bidv_sell_vnd is not None else None

    if target_d is None or outside_d is None or usd_to_cny_d is None or agri_d is None:
        raise ValueError("target, outside, usd_to_cny, agri required")

    outside = outside_cny_route(target_d, outside_d)
    outside_total = outside["total_vnd"]

    # Compute required gross for China and HK (rate independent of VND sell)
    china = china_reverse(target_d, usd_to_cny_d, recipient_bank_fee_usd, china_fee_per_tranche, china_tranche_size)
    hk = hk_reverse(target_d, usd_to_cny_d, recipient_bank_fee_usd, hk_fee_pct)

    china_gross = china["gross_usd_required"]
    hk_gross = hk["gross_usd_required"]

    def _build_vn(gross: Decimal, sell: Decimal | None, channel_label: str):
        if sell is None:
            return {
                "available": False,
                "status": "RATE_UNAVAILABLE",
                "channel": channel_label,
                "gross_usd": gross,
                "usd_sell_vnd": None,
                "principal_vnd": None,
                "swift_fee_vnd": None,
                "vn_pct_fee_vnd": None,
                "total_vnd": None,
                "delta_vnd": None,
            }
        vn = vietnam_bank_cost(gross, sell, vn_swift_fee_usd, vn_pct_fee)
        delta = vn["total_vnd"] - outside_total
        return {
            "available": True,
            "status": "OK",
            "channel": channel_label,
            "gross_usd": vn["gross_usd"],
            "usd_sell_vnd": vn["usd_sell_vnd"],
            "principal_vnd": vn["principal_vnd"],
            "swift_fee_vnd": vn["swift_fee_vnd"],
            "vn_pct_fee_vnd": vn["vn_pct_fee_vnd"],
            "total_vnd": vn["total_vnd"],
            "delta_vnd": delta,
        }

    # Enrich with agent fee details for display
    # China routes: need tranche info for display
    # HK routes: need hk fee

    routes = []

    # China Agribank
    ca = _build_vn(china_gross, agri_d, "USD→China via Agribank")
    ca.update({
        "agent_route": "CHINA",
        "bank": "Agribank",
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": china["recipient_bank_fee_usd"],
        "agent_fee_cny": china["china_agent_fee_cny"],
        "agent_fee_usd": None,
        "tranche_count": china["tranche_count"],
        "usd_after_bank": china["usd_after_bank"],
        "gross_cny": china["gross_cny"],
    })
    routes.append(ca)

    # China BIDV
    cb = _build_vn(china_gross, bidv_d, "USD→China via BIDV")
    cb.update({
        "agent_route": "CHINA",
        "bank": "BIDV",
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": china["recipient_bank_fee_usd"],
        "agent_fee_cny": china["china_agent_fee_cny"],
        "agent_fee_usd": None,
        "tranche_count": china["tranche_count"],
        "usd_after_bank": china["usd_after_bank"],
        "gross_cny": china["gross_cny"],
    })
    routes.append(cb)

    # HK Agribank
    ha = _build_vn(hk_gross, agri_d, "USD→HongKong via Agribank")
    ha.update({
        "agent_route": "HONG_KONG",
        "bank": "Agribank",
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": hk["recipient_bank_fee_usd"],
        "agent_fee_cny": None,
        "agent_fee_usd": hk["hk_agent_fee_usd"],
        "hk_agent_fee_pct": hk["hk_agent_fee_pct"],
        "usd_after_bank": hk["usd_after_bank"],
        "usd_for_conversion": hk["usd_for_conversion"],
    })
    routes.append(ha)

    # HK BIDV
    hb = _build_vn(hk_gross, bidv_d, "USD→HongKong via BIDV")
    hb.update({
        "agent_route": "HONG_KONG",
        "bank": "BIDV",
        "target_cny": target_d,
        "usd_to_cny": usd_to_cny_d,
        "recipient_bank_fee_usd": hk["recipient_bank_fee_usd"],
        "agent_fee_cny": None,
        "agent_fee_usd": hk["hk_agent_fee_usd"],
        "hk_agent_fee_pct": hk["hk_agent_fee_pct"],
        "usd_after_bank": hk["usd_after_bank"],
        "usd_for_conversion": hk["usd_for_conversion"],
    })
    routes.append(hb)

    # Outside
    outside_route = {
        "available": True,
        "status": "OK",
        "channel": "Tệ ngoài",
        "agent_route": "OUTSIDE_CNY",
        "bank": None,
        "target_cny": target_d,
        "outside_cny_vnd": outside_d,
        "total_vnd": outside_total,
        "delta_vnd": Decimal("0"),
        "gross_usd": None,
        "usd_sell_vnd": None,
    }

    return {
        "target_cny": target_d,
        "outside_cny_vnd": outside_d,
        "usd_to_cny": usd_to_cny_d,
        "agribank_sell_vnd": agri_d,
        "bidv_sell_vnd": bidv_d,
        "bidv_status": "OK" if bidv_d is not None else "RATE_UNAVAILABLE",
        "outside_route": outside_route,
        "outside_total_vnd": outside_total,
        "china_reverse": china,
        "hk_reverse": hk,
        "usd_routes": routes,
        "formula_version": FORMULA_VERSION,
    }
