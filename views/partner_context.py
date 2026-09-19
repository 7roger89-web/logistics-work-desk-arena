"""Bounded READ-ONLY partner-context adapter for the ``/ngu-canh-doi-tac`` workspace.

Presentation adapter ONLY (LOGI_PARTNER_CONTEXT_WORKSPACE_01). It exposes the
partner/entity context capability that ALREADY EXISTS in Logistics Work Desk and
was previously reachable only from the Streamlit entity workspace:

    core.entity_context.build_entity_context("partner", …)    shipment-partner index
    core.database.load_authority_agents()                     legal Agent master
    views.logi_real_data.partner_payables_projection()        canonical C2B/C2D ledger

No new source of truth is introduced: every field below is a passthrough (or a
key-verified union) of those readers. There is no new database, service, router,
API, store, index or writer here — and none is implied by this module.

Layering: :func:`partner_context_projection` is pure over the sources it is
handed (so it is testable without a database), while :func:`partner_context_view`
is the ONE-READ wrapper the view-model calls: it loads the master and the
canonical ledger through the existing readers and forwards the caller's
selection recorded by the bounded dispatcher.

BUSINESS TRUTH RULES (partner + finance adjacent — fail honest, never fabricate):

- UNKNOWN != ZERO: a missing identity/contact field stays ``None`` and renders
  as an explicit "—"; a partner with no canonical payable is reported as
  ``status = "UNKNOWN"`` with no rows, never as a 0 payable.
- No partner master-data model is created here: a partner without an
  ``authority_agents`` record keeps ``masterStatus = "UNKNOWN"`` and the UI says
  plainly that no approved master record exists.
- Financial figures are the ones the canonical ledger already derived
  (obligation + payment + allocation, one row per SHIPMENT × CURRENCY). This
  adapter never re-derives, re-allocates or totals them.
- Currencies stay separate. No FX, no cross-currency sum, no partner-level
  payable summary (that is the C2D worklist's job, reached by navigation).
- Nothing the backend does not model is exposed or inferred: no relationship /
  risk / credit / reliability score, no tier, no account manager, no SLA, no
  partner note or activity. ``unavailable`` lists exactly that, so an absent
  panel is a statement about the system rather than a silently empty one.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.entity_context import build_entity_context, list_context_entities

#: Existing React route for one shipment (donor route, unchanged).
SHIPMENT_ROUTE_PREFIX = "/lo-hang/"

#: Existing C2D partner-payable worklist route (navigation only, no duplication).
PAYABLE_WORKLIST_ROUTE = "/tai-chinh/cong-no-doi-tac"

#: Payload boundedness ceilings — the same discipline as the tariff adapter.
MAX_PARTNERS = 200
MAX_SHIPMENTS = 60
MAX_DOCUMENTS = 40

#: Context a partner workspace would usually carry but this backend does not
#: model anywhere. Surfaced verbatim so the page never looks "quietly empty".
UNAVAILABLE_CONTEXT: tuple[str, ...] = (
    "Điểm quan hệ đối tác / xếp hạng rủi ro — không có nguồn dữ liệu",
    "Hạng đối tác, quản lý tài khoản, hạn mức công nợ — không có master",
    "Ghi chú, lịch sử liên hệ, kho tài liệu riêng của đối tác — không có lưu trữ",
    "Điều khoản SLA / cam kết dịch vụ — không có nguồn dữ liệu",
)

#: Honest status of the slice (the UI renders a distinct state for each).
OK = "OK"
NO_SELECTION = "NO_SELECTION"
NO_SOURCE = "NO_PARTNER_SOURCE"
NOT_FOUND = "PARTNER_NOT_FOUND"

_FINANCE_STATUS_LABEL = {
    "CONFIRMED": "ĐÃ XÁC NHẬN",
    "REVIEW_REQUIRED": "CẦN REVIEW",
    "UNKNOWN": "CHƯA XÁC ĐỊNH",
}


def _text(value: Any) -> str | None:
    """Verbatim string passthrough; genuinely-absent values stay ``None``.

    ``UNKNOWN`` is the sentinel the existing entity-context readers use for "not
    known", so it is normalised to ``None`` here rather than displayed as a word.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null", "<na>", "unknown"}:
        return None
    return text


def _key(value: Any) -> str:
    text = _text(value)
    return text.casefold() if text else ""


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [item for item in value.values() if isinstance(item, Mapping)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


# ---------------------------------------------------------------------------
# Authoritative sources, read as they are
# ---------------------------------------------------------------------------

def _agent_master(agents: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """``authority_agents`` indexed by ``agent_id`` and by storage id.

    The party shape comes from the EXISTING C1 projection (``_party_view``) so
    this workspace and the contract screens can never disagree about one master.
    """
    from views.logi_c1 import _party_view

    indexed: dict[str, dict[str, Any]] = {}
    for record in _rows(agents):
        view = _party_view(record, "agent")
        if not isinstance(view, dict):
            continue
        for ident in (_text(record.get("agent_id")), _text(record.get("id"))):
            if ident:
                indexed.setdefault(ident.casefold(), view)
    return indexed


# ---------------------------------------------------------------------------
# Options: the simplest current authoritative lookup (no new index/service)
# ---------------------------------------------------------------------------

def partner_options(
    *,
    agents: Mapping[str, Any] | None = None,
    customers: Any = None,
    shipments: Any = None,
    payable_rows: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Every partner the backend can actually name, with where it came from.

    A partner appears when the legal Agent master carries it, the canonical
    partner ledger references it, or a shipment document names it as
    partner/agent. Identity is never merged across sources: the label prefers
    the master record and every other source is listed explicitly.
    """
    entries: dict[str, dict[str, Any]] = {}

    def _entry(key: str, label: str, source: str, shipment_id: str | None) -> dict[str, Any]:
        entry = entries.setdefault(
            key,
            {"key": key, "label": label or key, "master": False,
             "sources": [], "shipmentIds": [], "currencies": []},
        )
        if source not in entry["sources"]:
            entry["sources"].append(source)
        if shipment_id and shipment_id not in entry["shipmentIds"]:
            entry["shipmentIds"].append(shipment_id)
        # A master-backed label always wins over a ledger/shipment-derived one.
        if source == "authority_agents" and label:
            entry["label"] = label
        return entry

    master = _agent_master(agents)
    claimed: set[str] = set()
    for record in _rows(agents):
        agent_id = _text(record.get("agent_id")) or _text(record.get("id"))
        if not agent_id:
            continue
        legal_name = _text(record.get("legal_name")) or agent_id
        view = master.get(agent_id.casefold()) or {}
        entry = _entry(agent_id, legal_name, "authority_agents", None)
        entry["master"] = True
        entry["legalCode"] = _text(view.get("legalCode"))
        entry["phone"] = _text(view.get("phone"))
        entry["email"] = _text(view.get("email"))
        claimed.update(filter(None, (agent_id.casefold(), legal_name.casefold())))

    # Canonical ledger counterparties: authoritative partner + real shipment link.
    for row in payable_rows or []:
        if not isinstance(row, Mapping):
            continue
        partner_id = _text(row.get("partnerId")) or ""
        name = _text(row.get("partnerName")) or partner_id
        key = partner_id or name
        if not key:
            continue
        entry = _entry(key, name, "canonical partner ledger (C2B/C2D)", _text(row.get("shipmentId")))
        currency = _text(row.get("currency"))
        if currency and currency not in entry["currencies"]:
            entry["currencies"].append(currency)
        claimed.update(filter(None, (key.casefold(), name.casefold())))

    # Shipment-partner index (names the operational data carries directly).
    for option in [
        option for option in list_context_entities(customers or {}, shipments or {})
        if option.get("entity_type") == "partner"
    ]:
        name = _text(option.get("entity_key"))
        if not name or name.casefold() in claimed:
            continue
        _entry(name, _text(option.get("label")) or name, "shipment partner/agent index", None)

    options = sorted(entries.values(), key=lambda item: (item["label"] or "").casefold())
    for option in options:
        option["shipmentIds"] = sorted(option["shipmentIds"])
        option["shipmentCount"] = len(option["shipmentIds"])
    return {
        "options": options[:MAX_PARTNERS],
        "count": len(options),
        "truncated": len(options) > MAX_PARTNERS,
        "limit": MAX_PARTNERS,
    }


# ---------------------------------------------------------------------------
# The one projection the workspace renders
# ---------------------------------------------------------------------------

def _identity_block(master: Mapping[str, Any] | None, context: Mapping[str, Any] | None,
                    fallback_label: str) -> dict[str, Any]:
    """Authoritative identity, with each source kept explicit."""
    party = dict(master) if isinstance(master, Mapping) else None
    context_identity = (context or {}).get("identity") or {}
    context_master = (context or {}).get("master") or {}
    return {
        # authority_agents master fields, verbatim (empty string == unknown).
        "party": party,
        "masterStatus": "KNOWN" if party else _text(context_master.get("status")) or "UNKNOWN",
        "masterSource": ("authority_agents (legal Agent master)" if party
                         else _text(context_master.get("source"))
                         or "Không có hồ sơ master được phê duyệt cho đối tác này"),
        "displayName": _text((party or {}).get("legalName")) or _text(context_identity.get("name")) or fallback_label,
        "displayId": _text((party or {}).get("id")) or _text(context_identity.get("id")) or fallback_label,
        "contextName": _text(context_identity.get("name")),
        "contextId": _text(context_identity.get("id")),
    }


def _context_shipment_rows(context: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Operational rows exactly as ``core.entity_context`` derived them.

    Keyed by the shipment id as the source wrote it (so navigation keeps the
    exact id) and de-duplicated case-insensitively.
    """
    rows: dict[str, dict[str, Any]] = {}
    for row in list((context or {}).get("shipments") or []):
        if not isinstance(row, Mapping):
            continue
        sid = _text(row.get("shipment_id"))
        if not sid or any(existing.casefold() == sid.casefold() for existing in rows):
            continue
        rows[sid] = {
            "shipmentId": sid,
            "status": _text(row.get("status")),
            "requiredDate": _text(row.get("required_date")),
            "plannedDate": _text(row.get("planned_date")),
            "attention": _text(row.get("attention")),
            "attentionDetail": _text(row.get("attention_detail")),
            "role": _text(row.get("role")),
            "route": _text(row.get("route")),
            "operationalContext": _text(row.get("operational_context")),
            "source": _text(row.get("source")) or "core.entity_context + shipment_dashboard",
        }
    return rows


def _finance_rows(payable_rows: list[Mapping[str, Any]] | None,
                  selected_keys: set[str]) -> list[dict[str, Any]]:
    """This partner's C2D rows verbatim — never re-derived, never merged."""
    out: list[dict[str, Any]] = []
    for row in payable_rows or []:
        if not isinstance(row, Mapping):
            continue
        identities = {_key(row.get("partnerId")), _key(row.get("partnerName"))}
        if not (identities & selected_keys):
            continue
        out.append({
            "id": _text(row.get("id")),
            "shipmentId": _text(row.get("shipmentId")),
            "currency": _text(row.get("currency")),
            "payable": row.get("payable"),
            "paid": row.get("paid"),
            "remaining": row.get("remaining"),
            "status": _text(row.get("status")),
            "obligationIds": list(row.get("obligationIds") or []),
            "source": "core.financial_ledger.shipment_partner_position (C2D projection)",
        })
    out.sort(key=lambda item: (str(item.get("shipmentId")), str(item.get("currency"))))
    return out


def partner_context_projection(
    selected: str | None,
    *,
    agents: Mapping[str, Any] | None = None,
    customers: Any = None,
    shipments: Any = None,
    payables: Mapping[str, Any] | None = None,
    quotes: Mapping[str, Any] | None = None,
    agreements: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure projection over the sources handed to it (no I/O, no DB access)."""
    payable_rows = list((payables or {}).get("rows") or []) if isinstance(payables, Mapping) else []
    selection = partner_options(
        agents=agents, customers=customers, shipments=shipments, payable_rows=payable_rows
    )
    options = selection["options"]
    chosen = _text(selected)

    base: dict[str, Any] = {
        "readOnly": True,
        "options": options,
        "optionCount": selection["count"],
        "optionTruncated": selection["truncated"],
        "optionLimit": selection["limit"],
        # Exactly the terms this adapter can genuinely match on (no fuzzy/AI).
        "searchFields": ["mã đối tác", "tên / legal name", "điện thoại", "email"],
        "selectedKey": None,
        "selectedLabel": None,
        "status": OK,
        "reason": None,
    }

    if not options:
        return {
            **base,
            "status": NO_SOURCE,
            "reason": (
                "Chưa có đối tác nào trong dữ liệu hiện tại: không có hồ sơ "
                "authority_agents, không có nghĩa vụ/thanh toán đối tác canonical "
                "và không có lô nào gắn partner/agent. Đây là trạng thái chưa xác "
                "định — không có dữ liệu mẫu được tạo thay thế."
            ),
        }
    if not chosen:
        return {**base, "status": NO_SELECTION,
                "reason": "Chọn một đối tác để xem ngữ cảnh từ dữ liệu hiện có."}

    match = next(
        (option for option in options
         if _key(option.get("key")) == _key(chosen) or _key(option.get("label")) == _key(chosen)),
        None,
    )
    if match is None:
        return {
            **base,
            "status": NOT_FOUND,
            "reason": (
                f"Không tìm thấy đối tác “{chosen}” trong dữ liệu hiện có — "
                "không có bản ghi nào được tạo thay thế."
            ),
        }

    key = str(match.get("key") or chosen)
    label = str(match.get("label") or key)
    master_index = _agent_master(agents)
    master = master_index.get(_key(key)) or master_index.get(_key(label))

    # The existing entity-context projection, keyed on the partner NAME it indexes.
    context = build_entity_context(
        "partner", label,
        customers=customers or {}, shipments=shipments or {},
        quotes=quotes, agreements=agreements,
    )

    finance = _finance_rows(payable_rows, {_key(key), _key(label)})
    context_rows = _context_shipment_rows(context)
    context_by_key = {_key(sid): row for sid, row in context_rows.items()}

    # The route can only serve a shipment the desk actually has.
    shipment_keys = {str(sid).casefold() for sid in (shipments or {}).keys()} if isinstance(shipments, Mapping) else set()
    for document in _rows(shipments):
        own = _text(document.get("id"))
        if own:
            shipment_keys.add(own.casefold())

    ids = sorted({*[sid for sid in context_rows],
                  *[row["shipmentId"] for row in finance if row["shipmentId"]],
                  *[sid for sid in (match.get("shipmentIds") or []) if sid]},
                 key=str.casefold)

    linked: list[dict[str, Any]] = []
    for sid in ids:
        row = dict(context_by_key.get(_key(sid), {}))
        row["shipmentId"] = sid
        row.setdefault("status", None)
        row.setdefault("requiredDate", None)
        row.setdefault("plannedDate", None)
        row.setdefault("attention", None)
        row.setdefault("attentionDetail", None)
        row.setdefault("role", None)
        row.setdefault("route", None)
        row.setdefault("operationalContext", None)
        row["financeCurrencies"] = sorted({
            finance_row["currency"] for finance_row in finance
            if _key(finance_row["shipmentId"]) == _key(sid) and finance_row["currency"]
        })
        row["openHref"] = SHIPMENT_ROUTE_PREFIX + sid
        row["canOpen"] = sid.casefold() in shipment_keys
        if row["canOpen"] is False:
            row["source"] = (
                f"{row['source']} · lô không có trong danh sách lô hiện tại"
                if row.get("source") else "lô tham chiếu từ ledger — không có trong danh sách lô hiện tại"
            )
        linked.append(row)

    truncated = len(linked) > MAX_SHIPMENTS
    documents = [
        {"shipmentId": _text(doc.get("shipment_id")), "document": _text(doc.get("document")),
         "status": _text(doc.get("status")), "source": _text(doc.get("source"))}
        for doc in list((context or {}).get("documents") or [])[:MAX_DOCUMENTS]
        if isinstance(doc, Mapping)
    ]

    by_currency: dict[str, dict[str, Any]] = {}
    for row in finance:
        bucket = by_currency.setdefault(row["currency"] or "UNKNOWN",
                                        {"rowCount": 0, "shipmentIds": [], "obligationCount": 0})
        bucket["rowCount"] += 1
        bucket["obligationCount"] += len(row["obligationIds"])
        if row["shipmentId"] and row["shipmentId"] not in bucket["shipmentIds"]:
            bucket["shipmentIds"].append(row["shipmentId"])
    statuses = {row["status"] for row in finance if row["status"]}
    finance_status = ("UNKNOWN" if not finance
                      else ("REVIEW_REQUIRED" if statuses != {"CONFIRMED"} else "CONFIRMED"))

    gaps: list[str] = []
    if not master:
        gaps.append(_text((context or {}).get("master", {}).get("source"))
                    or "Không có hồ sơ master được phê duyệt cho đối tác này")
    for field, value in (master or {}).items():
        if field in {"id", "legalName"}:
            continue
        if not _text(value):
            gaps.append(f"{field} chưa có trong hồ sơ master")
    # The entity-context projection assumes NO approved master exists; when this
    # partner does have an authority_agents record, those generic notes are
    # contradicted by better data and must not be shown as gaps.
    for gap in list((context or {}).get("gaps") or []):
        text_gap = _text(gap)
        if not text_gap or text_gap in gaps:
            continue
        if master and "master" in text_gap.casefold():
            continue
        gaps.append(text_gap)
    if not linked:
        gaps.append("Chưa có lô nào liên kết với đối tác này trong dữ liệu hiện tại")
    if not finance:
        gaps.append("Chưa có nghĩa vụ/thanh toán canonical nào cho đối tác này — "
                    "phải trả là CHƯA XÁC ĐỊNH, không phải 0")

    return {
        **base,
        "status": OK,
        "selectedKey": key,
        "selectedLabel": label,
        "matchedSources": list(match.get("sources") or []),
        "identity": _identity_block(master, context, label),
        "roles": sorted({text for role in list((context or {}).get("roles") or []) if (text := _text(role))}),
        "shipments": linked[:MAX_SHIPMENTS],
        "shipmentCount": len(linked),
        "shipmentTruncated": truncated,
        "documents": documents,
        "finance": {
            "rows": finance,
            "status": finance_status,
            "statusLabel": _FINANCE_STATUS_LABEL.get(finance_status, finance_status),
            "byCurrency": by_currency,
            "worklistHref": PAYABLE_WORKLIST_ROUTE,
            "note": (
                "Projection canonical theo từng lô từ sổ cái; màn hình này không "
                "tổng hợp công nợ toàn đối tác và không quy đổi tiền tệ."
            ),
        },
        "gaps": gaps,
        "unavailable": list(UNAVAILABLE_CONTEXT),
    }


def partner_context_view(
    selected: str | None = None,
    *,
    payables: Mapping[str, Any] | None = None,
    customers: Any = None,
    shipments: Any = None,
    agents: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The ONE-READ slice the view-model embeds (existing readers only).

    ``payables`` lets the caller hand over the C2D projection it already built
    (``build_view_model`` does exactly that) so one page render never reads the
    canonical ledger twice. Without it the adapter reads the SAME projection
    itself — there is no partner-specific finance query anywhere in this module.

    ``customers`` / ``shipments`` follow the same rule: the component view-model
    passes its fresh uncached reads, while a standalone caller (the Streamlit
    entity workspace, tests) falls back to the session copies the app maintains.

    ``agents`` (LOGI_INTERACTION_LATENCY_FINALIZE_02) is the ``authority_agents``
    master the view-model already read for this same render; ``None`` keeps
    the original read for standalone callers.
    """
    import streamlit as st

    from core.database import load_authority_agents
    from views import logi_real_data as rd

    if agents is None:
        try:
            agents = load_authority_agents() or {}
        except Exception:  # noqa: BLE001 - a missing master must not blank the desk
            agents = {}
    if payables is None:
        payables = rd.partner_payables_projection()
    return partner_context_projection(
        selected,
        agents=agents,
        customers=st.session_state.get("db_customers", {}) if customers is None else customers,
        shipments=st.session_state.get("db_shipments", {}) if shipments is None else shipments,
        payables=payables,
    )


__all__ = ["partner_context_projection", "partner_context_view", "partner_options"]
