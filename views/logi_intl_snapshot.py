"""Bounded immutable snapshot handler for LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01.

Single responsibility: re-derive arithmetic with Decimal via
core.intl_payment_calculator (never trusts browser math), build provenance
snapshot, persist via canonical writer, return fresh readback.

No money transfer, no browser automation, no private API bypass.
"""

from __future__ import annotations

from typing import Any, Mapping
from decimal import Decimal


def _text(value: Any) -> str:
    from views import logi_real_data as rd

    return rd.text(value)


def _serialize_decimal(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            return format(value, "f")
        return str(value)
    except Exception:
        return str(value)


def _pick_first_decimal(*candidates) -> Decimal | None:
    for c in candidates:
        if c is not None:
            return c
    return None


def _normalize_rate_provenance(
    effective: Decimal | None,
    prov: Mapping[str, Any],
    candidate_keys: list[str],
    label: str,
    captured_at: str,
) -> dict[str, Any]:
    """Ensure provenance truth: effective value must match what prov claims is LIVE.
    If mismatch, normalize to MANUAL with live_reference."""
    base = dict(prov) if isinstance(prov, Mapping) else {}
    status = str(base.get("status") or "").upper()
    source = str(base.get("source") or base.get("source_url") or "").lower()
    # Extract claim from prov (where numeric might live)
    claim: Decimal | None = None
    claim_key = None
    for k in candidate_keys:
        v = base.get(k)
        if v is None or v == "":
            continue
        try:
            txt = str(v).strip().replace(",", "").replace(" ", "")
            if not txt:
                continue
            dec = Decimal(txt)
            if dec.is_finite():
                claim = dec
                claim_key = k
                break
        except Exception:
            continue
    # MANUAL or UNAVAILABLE always truthful if effective matches or is None appropriately
    if status == "MANUAL":
        # Ensure manual provenance carries the effective value
        if effective is not None and claim is None:
            base["value"] = _serialize_decimal(effective)
        elif effective is not None and claim is not None and abs(claim - effective) > Decimal("0.000001"):
            base["value"] = _serialize_decimal(effective)
            base["note"] = f"Manual value {effective} differs from prov {claim}; normalized to manual per truth"
        base.setdefault("captured_at", captured_at)
        return base
    if status == "RATE_UNAVAILABLE":
        return base
    # LIVE / OK — must match effective
    if effective is None and claim is None:
        return base
    if effective is None or claim is None:
        # One missing while other present => mismatch => normalize to MANUAL
        manual = {
            "status": "MANUAL",
            "source": "MANUAL",
            "source_url": "manual",
            "value": _serialize_decimal(effective) if effective is not None else None,
            "captured_at": captured_at,
            "live_reference": dict(base),
            "reason": f"{label}: effective {effective} != provenance {claim} — normalized to MANUAL",
        }
        return manual
    if abs(claim - effective) > Decimal("0.000001"):
        # LIVE claim lies about effective rate — normalize
        manual = {
            "status": "MANUAL",
            "source": "MANUAL",
            "source_url": "manual",
            "value": _serialize_decimal(effective),
            "captured_at": captured_at,
            "live_reference": dict(base),
            "reason": f"{label}: LIVE provenance {claim} (key {claim_key}) != effective {effective} — truthful MANUAL",
        }
        return manual
    return base


def handle_contract_intl_snapshot_save(payload: Mapping[str, Any], deps: Mapping[str, Any]) -> dict[str, Any]:
    """Implement the typed event. `deps` supplies injected helpers to keep view pure."""
    # deps: read_contract, contract_projection, _result, _audit
    read_contract = deps["read_contract"]
    contract_projection = deps["contract_projection"]
    _result = deps["_result"]
    _audit = deps["_audit"]

    from uuid import uuid4
    from core.auth import can_edit_contract
    from core.database import get_last_db_error, save_contract_intl_snapshot
    from core.intl_payment_calculator import (
        FORMULA_VERSION,
        comparison_for_target_cny,
        china_forward,
        hk_forward,
        vietnam_bank_cost,
    )

    cid = _text(payload.get("contractId") or payload.get("contract_id") or payload.get("id"))
    cid = cid.strip().upper()
    request_id = _text(payload.get("requestId"))
    snapshot_id = _text(payload.get("snapshotId") or payload.get("id") or "")
    if not snapshot_id:
        snapshot_id = f"INTL-{uuid4().hex.upper()[:12]}"
    else:
        snapshot_id = snapshot_id.strip().upper()
        if not snapshot_id.startswith("INTL-"):
            snapshot_id = f"INTL-{snapshot_id}"

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("contract_intl_snapshot_save", cid, ok, error, requestId=request_id, snapshotId=snapshot_id, **extra)

    if not cid:
        return _res(False, "Thiếu mã hợp đồng (contractId).")
    if not can_edit_contract():
        return _res(False, "RBAC: không có quyền sửa hợp đồng (sales_write).")
    contract = read_contract(cid)
    if contract is None:
        return _res(False, f"Không tìm thấy hợp đồng {cid}.")

    raw_mode = _text(payload.get("mode")).strip().upper()
    if raw_mode in ("A", "TOI_CHUYEN_USD", "TOI CHUYEN USD", "MODE_A"):
        mode = "A"
    elif raw_mode in ("B", "DAI_LY_CAN_NHAN", "DAI LY CAN NHAN", "MODE_B"):
        mode = "B"
    else:
        mode = ""
        if _text(payload.get("gross_usd")) or _text(payload.get("grossUsd")):
            mode = "A"
        elif _text(payload.get("target_cny")) or _text(payload.get("targetCny")):
            mode = "B"
        else:
            return _res(False, "Thiếu mode: chọn A (Tôi chuyển USD) hoặc B (Đại lý cần nhận).")

    def _dec(key: str) -> Decimal | None:
        raw = payload.get(key)
        if raw is None:
            # try camelCase variant
            # convert snake to camel: gross_usd -> grossUsd
            parts = key.split("_")
            camel = parts[0] + "".join(p.title() for p in parts[1:])
            raw = payload.get(camel)
        if raw is None and key == "agribank_sell_vnd":
            raw = payload.get("agri_sell_vnd") or payload.get("usd_sell_vnd")
        if raw is None and key == "bidv_sell_vnd":
            raw = payload.get("bidvSellVnd")
        if raw is None and key == "outside_cny_vnd":
            raw = payload.get("outsideCnyVnd") or payload.get("outside_rate")
        if raw is None and key == "usd_to_cny":
            raw = payload.get("usdToCny")
        if raw is None or raw == "":
            return None
        try:
            txt = str(raw).strip().replace(",", "").replace(" ", "").replace("\xa0", "")
            if not txt:
                return None
            d = Decimal(txt)
            if not d.is_finite():
                return None
            return d
        except Exception:
            return None

    usd_to_cny = _dec("usd_to_cny")
    agri_sell = _dec("agribank_sell_vnd")
    bidv_sell = _dec("bidv_sell_vnd")
    outside_rate = _dec("outside_cny_vnd")

    recipient_fee = _pick_first_decimal(_dec("recipient_bank_fee_usd"), _dec("recipientBankFeeUsd"))
    china_fee_per_tranche = _pick_first_decimal(_dec("china_fee_per_tranche_cny"), _dec("chinaFeePerTrancheCny"))
    china_tranche_size = _pick_first_decimal(_dec("china_tranche_size_usd"), _dec("chinaTrancheSizeUsd"))
    hk_pct = _pick_first_decimal(_dec("hk_fee_pct"), _dec("hkFeePct"))
    vn_swift = _pick_first_decimal(_dec("vn_swift_fee_usd"), _dec("vnSwiftFeeUsd"))
    vn_pct = _pick_first_decimal(_dec("vn_pct_fee"), _dec("vnPctFee"))

    fx_boc = payload.get("fxBoc") if isinstance(payload.get("fxBoc"), Mapping) else payload.get("fx_boc") if isinstance(payload.get("fx_boc"), Mapping) else {}
    fx_agri = payload.get("fxAgribank") if isinstance(payload.get("fxAgribank"), Mapping) else payload.get("fx_agribank") if isinstance(payload.get("fx_agribank"), Mapping) else {}
    fx_bidv = payload.get("fxBidv") if isinstance(payload.get("fxBidv"), Mapping) else payload.get("fx_bidv") if isinstance(payload.get("fx_bidv"), Mapping) else {}

    # minimal provenance fallback — truthful per-rate
    # Allow explicit sourceKind from frontend: LIVE|MANUAL|UNAVAILABLE
    def _coerce_kind(raw, default_live_valid: bool) -> str:
        k = str(raw or "").strip().upper()
        if k in ("LIVE", "MANUAL", "UNAVAILABLE", "RATE_UNAVAILABLE"):
            return "UNAVAILABLE" if k == "RATE_UNAVAILABLE" else k
        # Heuristic: if prov claims OK/LIVE treat as LIVE, else MANUAL
        if isinstance(prov, Mapping) and str(prov.get("status") or "").upper() in ("OK", "LIVE"):
            return "LIVE"
        return "MANUAL" if default_live_valid else "UNAVAILABLE"

    # If frontend sent explicit kinds, prefer them; else infer
    boc_kind_raw = payload.get("usdCnySourceKind") or payload.get("usd_cny_source_kind") or payload.get("sourceKindBoc")
    agri_kind_raw = payload.get("agribankSourceKind") or payload.get("agribank_source_kind")
    bidv_kind_raw = payload.get("bidvSourceKind") or payload.get("bidv_source_kind")
    if not isinstance(fx_boc, Mapping) or not fx_boc:
        fx_boc = {"source": "MANUAL", "status": "MANUAL" if usd_to_cny is not None else "RATE_UNAVAILABLE", "source_url": "manual", "usd_to_cny": _serialize_decimal(usd_to_cny), "value": _serialize_decimal(usd_to_cny)}
    if not isinstance(fx_agri, Mapping) or not fx_agri:
        fx_agri = {"source": "MANUAL", "status": "MANUAL" if agri_sell is not None else "RATE_UNAVAILABLE", "source_url": "manual", "usd_sell_vnd": _serialize_decimal(agri_sell), "value": _serialize_decimal(agri_sell)}
    if not isinstance(fx_bidv, Mapping) or not fx_bidv:
        fx_bidv = {"source": "MANUAL", "status": "MANUAL" if bidv_sell is not None else "RATE_UNAVAILABLE", "source_url": "manual", "usd_sell_vnd": _serialize_decimal(bidv_sell), "value": _serialize_decimal(bidv_sell)}
    # Normalize truth: effective numeric must agree with provenance claim
    _now_for_prov = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    fx_boc = _normalize_rate_provenance(usd_to_cny, fx_boc, ["usd_to_cny", "value", "buying_rate", "usdToCny"], "USD_CNY", _now_for_prov)
    fx_agri = _normalize_rate_provenance(agri_sell, fx_agri, ["usd_sell_vnd", "sell", "usdSellVnd", "value"], "AGRIBANK_USD_SELL", _now_for_prov)
    fx_bidv = _normalize_rate_provenance(bidv_sell, fx_bidv, ["usd_sell_vnd", "sell", "usdSellVnd", "value"], "BIDV_USD_SELL", _now_for_prov)

    outputs: dict[str, Any] = {}
    inputs: dict[str, Any] = {}
    try:
        if mode == "A":
            gross = _dec("gross_usd")
            if gross is None or gross <= 0:
                return _res(False, "Mode A cần gross_usd > 0.")
            if usd_to_cny is None or usd_to_cny <= 0:
                return _res(False, "Thiếu tỷ giá USD→CNY (usd_to_cny) — chọn nguồn BOC hoặc nhập tay.")
            agent_route = _text(payload.get("agent_route") or payload.get("agentRoute") or "CHINA").strip().upper()
            if agent_route not in ("CHINA", "HONG_KONG", "HK"):
                if "TRUNG" in agent_route or "CHINA" in agent_route:
                    agent_route = "CHINA"
                else:
                    agent_route = "HONG_KONG"
                if agent_route == "HK":
                    agent_route = "HONG_KONG"
            if agent_route == "CHINA":
                _rf = recipient_fee if recipient_fee is not None else Decimal("35")
                _cf = china_fee_per_tranche if china_fee_per_tranche is not None else Decimal("150")
                _cs = china_tranche_size if china_tranche_size is not None else Decimal("10000")
                fwd = china_forward(gross, usd_to_cny, _rf, _cf, _cs)
                bank_pick = _text(payload.get("vn_bank") or payload.get("bank") or "").strip().upper()
                sell_for_vn = agri_sell if bank_pick in ("AGRIBANK", "AGRI") else bidv_sell if bank_pick == "BIDV" else agri_sell
                vn_cost = None
                if sell_for_vn is not None:
                    _vs = vn_swift if vn_swift is not None else Decimal("5")
                    _vp = vn_pct if vn_pct is not None else Decimal("0.0015")
                    vn_cost = vietnam_bank_cost(gross, sell_for_vn, _vs, _vp)
                outputs = {
                    "mode": "A",
                    "agent_route": agent_route,
                    "forward": {k: _serialize_decimal(v) if isinstance(v, Decimal) else v for k, v in fwd.items() if k != "trace"},
                    "trace": fwd.get("trace"),
                    "vn_cost": {k: _serialize_decimal(v) if isinstance(v, Decimal) else v for k, v in vn_cost.items()} if vn_cost else None,
                }
                inputs = {"gross_usd": _serialize_decimal(gross), "agent_route": agent_route}
            else:
                _hk = hk_pct if hk_pct is not None else Decimal("0.02")
                _rf2 = recipient_fee if recipient_fee is not None else Decimal("35")
                _vs2 = vn_swift if vn_swift is not None else Decimal("5")
                _vp2 = vn_pct if vn_pct is not None else Decimal("0.0015")
                fwd = hk_forward(gross, usd_to_cny, _rf2, _hk)
                bank_pick = _text(payload.get("vn_bank") or payload.get("bank") or "").strip().upper()
                sell_for_vn = agri_sell if bank_pick in ("AGRIBANK", "AGRI") else bidv_sell if bank_pick == "BIDV" else agri_sell
                vn_cost = None
                if sell_for_vn is not None:
                    vn_cost = vietnam_bank_cost(gross, sell_for_vn, _vs2, _vp2)
                outputs = {
                    "mode": "A",
                    "agent_route": agent_route,
                    "forward": {k: _serialize_decimal(v) if isinstance(v, Decimal) else v for k, v in fwd.items() if k != "trace"},
                    "trace": fwd.get("trace"),
                    "vn_cost": {k: _serialize_decimal(v) if isinstance(v, Decimal) else v for k, v in vn_cost.items()} if vn_cost else None,
                }
                inputs = {"gross_usd": _serialize_decimal(gross), "agent_route": agent_route}
            inputs["usd_to_cny"] = _serialize_decimal(usd_to_cny)
        else:
            target = _dec("target_cny")
            if target is None or target <= 0:
                return _res(False, "Mode B cần target_cny > 0.")
            if outside_rate is None or outside_rate <= 0:
                return _res(False, "Mode B cần outside_cny_vnd > 0 (tỷ giá tệ ngoài).")
            if usd_to_cny is None or usd_to_cny <= 0:
                return _res(False, "Thiếu tỷ giá USD→CNY.")
            if agri_sell is None or agri_sell <= 0:
                return _res(False, "Thiếu tỷ giá USD bán Agribank (cần để tính VND).")

            cmp = comparison_for_target_cny(
                target,
                outside_rate,
                usd_to_cny,
                agri_sell,
                bidv_sell,
                recipient_fee if recipient_fee is not None else Decimal("35"),
                china_fee_per_tranche if china_fee_per_tranche is not None else Decimal("150"),
                china_tranche_size if china_tranche_size is not None else Decimal("10000"),
                hk_pct if hk_pct is not None else Decimal("0.02"),
                vn_swift if vn_swift is not None else Decimal("5"),
                vn_pct if vn_pct is not None else Decimal("0.0015"),
            )

            def _ser(o: Any) -> Any:
                if isinstance(o, Decimal):
                    return _serialize_decimal(o)
                if isinstance(o, dict):
                    return {k: _ser(v) for k, v in o.items()}
                if isinstance(o, list):
                    return [_ser(x) for x in o]
                return o

            outputs = _ser(cmp)
            inputs = {
                "target_cny": _serialize_decimal(target),
                "outside_cny_vnd": _serialize_decimal(outside_rate),
                "usd_to_cny": _serialize_decimal(usd_to_cny),
                "agribank_sell_vnd": _serialize_decimal(agri_sell),
                "bidv_sell_vnd": _serialize_decimal(bidv_sell) if bidv_sell is not None else None,
            }
    except ValueError as ve:
        return _res(False, str(ve))
    except Exception as exc:
        return _res(False, f"Lỗi tính toán: {type(exc).__name__}: {exc}")

    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).isoformat()
    snapshot_doc: dict[str, Any] = {
        "id": snapshot_id,
        "contract_id": cid,
        "mode": mode,
        "created_at": now_iso,
        "formula_version": FORMULA_VERSION,
        "inputs": inputs,
        "fx": {
            "boc": dict(fx_boc),
            "agribank": dict(fx_agri),
            "bidv": dict(fx_bidv),
            "usd_to_cny": _serialize_decimal(usd_to_cny),
            "agribank_sell_vnd": _serialize_decimal(agri_sell),
            "bidv_sell_vnd": _serialize_decimal(bidv_sell) if bidv_sell is not None else None,
            "outside_cny_vnd": _serialize_decimal(outside_rate),
        },
        "fee_rules": {
            "recipient_bank_fee_usd": _serialize_decimal(recipient_fee if recipient_fee is not None else Decimal("35")),
            "china_fee_per_tranche_cny": _serialize_decimal(china_fee_per_tranche if china_fee_per_tranche is not None else Decimal("150")),
            "china_tranche_size_usd": _serialize_decimal(china_tranche_size if china_tranche_size is not None else Decimal("10000")),
            "hk_fee_pct": _serialize_decimal(hk_pct if hk_pct is not None else Decimal("0.02")),
            "vn_swift_fee_usd": _serialize_decimal(vn_swift if vn_swift is not None else Decimal("5")),
            "vn_pct_fee": _serialize_decimal(vn_pct if vn_pct is not None else Decimal("0.0015")),
        },
        "outputs": outputs,
        "is_deleted": False,
    }
    if not save_contract_intl_snapshot(snapshot_doc):
        return _res(False, get_last_db_error() or "Không lưu được snapshot.")

    # Fresh readback
    from views import logi_view_model as vm
    fresh = read_contract(cid)
    readback = None
    if fresh:
        from core.database import load_authority_agents, load_authority_companies, load_contracts, load_docgen_documents

        docs_by_scope = {cid: load_docgen_documents(cid) or {}}
        try:
            from core.database import load_contract_intl_snapshots

            snaps = load_contract_intl_snapshots(cid) or {}
            grouped = {cid: sorted([dict(v) for v in snaps.values()], key=lambda r: str(r.get("created_at") or ""), reverse=True)[:20]}
        except Exception:
            grouped = {cid: []}
        readback = contract_projection(
            fresh,
            shipments=vm.load_shipments(),
            docs_by_scope=docs_by_scope,
            companies=load_authority_companies() or {},
            agents=load_authority_agents() or {},
            all_contracts=load_contracts() or {},
            intl_snapshots_by_contract=grouped,
        )
    return _res(True, readback=readback, persisted={"snapshotId": snapshot_id, "mode": mode}, audit=_audit("contract", cid))
