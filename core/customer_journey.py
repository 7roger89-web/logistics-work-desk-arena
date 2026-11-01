"""Server-built presentation model for the HEXA customer portal component.

The portal UI is a port of the Owner's ``HEXA_LucGiac_DEMO.html`` reference.
This module is the ONLY bridge between the trusted read boundary
(:mod:`core.customer_portal`) and that UI.  It is pure: no database access, no
browser input, no network.

Hard rules encoded here (they are the acceptance contract, not decoration):

* ``PUBLISHED`` means "this publication version was approved for the customer".
  It does NOT mean a transport stage happened.  A stage is only ever reported
  as ``COMPLETED`` when an approved, version-pinned public event exists for it;
  everything else is ``UNKNOWN`` and labelled ``Chưa xác minh`` /
  ``CHƯA ĐỐI SOÁT``.
* No amount, ETA, contact point, cargo description, route, document or comment
  is ever synthesised.  Missing data renders as an explicit unknown, never as
  the reference HTML's demo figures (53.400.000 VND, 25/10/2026, ...).
* Stage labels follow the shipment's transport mode, so a SEA lot can never
  display ROAD evidence or ROAD step names.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from core.shipment_plan import customer_plan_documents

UNKNOWN_STAGE_LABEL = "Chưa xác minh"
UNKNOWN_STAGE_DETAIL = "Chưa có chứng cứ được duyệt"
UNKNOWN_ETA_LABEL = "Chưa xác minh"
UNKNOWN_UPDATED_LABEL = "Chưa có cập nhật được duyệt"
NO_APPROVED_DATA = "Không có dữ liệu được duyệt"

#: The seven published stages, in the reference 00..06 order, per transport mode.
#: ``None`` (mode not published) gets mode-neutral wording: a customer must never
#: be told a road step happened when the mode itself is unknown.
STAGE_LABELS: dict[str | None, tuple[str, ...]] = {
    "ROAD": (
        "Kế hoạch",
        "Lấy hàng",
        "Nhận & ghép",
        "Vận chuyển",
        "Thông quan",
        "Giao hàng",
        "Thanh toán",
    ),
    "SEA": (
        "Kế hoạch",
        "Lấy hàng",
        "Gom hàng & đóng container",
        "Vận tải biển",
        "Thông quan",
        "Giao hàng",
        "Thanh toán",
    ),
    "AIR": (
        "Kế hoạch",
        "Lấy hàng",
        "Gom hàng & chuyến bay",
        "Vận tải hàng không",
        "Thông quan",
        "Giao hàng",
        "Thanh toán",
    ),
    "RAIL": (
        "Kế hoạch",
        "Lấy hàng",
        "Gom hàng & xếp toa",
        "Vận tải đường sắt",
        "Thông quan",
        "Giao hàng",
        "Thanh toán",
    ),
    None: (
        "Kế hoạch",
        "Lấy hàng",
        "Chặng 02 — chưa xác định phương thức",
        "Chặng 03 — chưa xác định phương thức",
        "Thông quan",
        "Giao hàng",
        "Thanh toán",
    ),
}

STAGE_IDS: tuple[str, ...] = (
    "plan",
    "pickup",
    "consolidate",
    "transit",
    "customs",
    "delivery",
    "finance",
)

#: Public event ``stage`` values that map onto a published stage.  Only exact
#: matches count; an unmapped event is never folded into a neighbouring stage.
_STAGE_ALIASES: dict[str, tuple[str, ...]] = {
    "plan": ("plan", "00", "planning", "quote", "contract"),
    "pickup": ("pickup", "01", "pick_up", "collection"),
    "consolidate": ("consolidate", "consolidation", "02", "road-ltl", "ltl", "cfs"),
    "transit": ("transit", "03", "road-border", "sea-transit", "air-transit", "rail-transit", "in_transit"),
    "customs": ("customs", "customs-import", "customs-export", "04", "clearance"),
    "delivery": ("delivery", "05", "pod", "last-mile"),
    "finance": ("finance", "finance-reconciliation", "settlement", "06", "payment"),
}

_MODE_LABELS = {
    "ROAD": "ROAD",
    "SEA": "SEA",
    "AIR": "AIR",
    "RAIL": "RAIL",
}


def mode_key(transport_mode: Any) -> str | None:
    """Normalise a published transport mode, or ``None`` when not published."""
    text = str(transport_mode or "").strip().upper()
    return text if text in {"ROAD", "SEA", "AIR", "RAIL"} else None


def _text(value: Any, limit: int = 240) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()[:limit]


def _money(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")) or number < 0:
        return None
    return number


_ISO_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


def display_timestamp(value: Any) -> str:
    """Render a published ISO timestamp the way the reference shows dates.

    Presentation only: the value is passed through unchanged when it is not a
    parseable ISO instant, so nothing is ever invented. The clock stays UTC and
    is labelled as such instead of silently implying a local timezone.
    """
    text = _text(value, 40)
    if not text:
        return ""
    match = _ISO_RE.match(text)
    if not match:
        return text
    year, month, day, hour, minute, _second, zone = match.groups()
    suffix = " UTC" if zone in ("Z", None) else f" {zone}"
    return f"{day}/{month}/{year} {hour}:{minute}{suffix}"


def _event_stage(event: Mapping[str, Any]) -> str | None:
    stage = _text(event.get("stage"), 40).lower()
    if not stage:
        return None
    for stage_id, aliases in _STAGE_ALIASES.items():
        if stage == stage_id or stage in aliases:
            return stage_id
        # A published event title may carry the reference's demo-style prefix
        # ("03 Vận chuyển"); match the numeric/leading token only, never a
        # substring of a different stage.
        head = stage.split()[0]
        if head in aliases:
            return stage_id
    return None


def _stage_documents(documents: Sequence[Mapping[str, Any]], stage_id: str) -> list[dict[str, str]]:
    """Documents the publication allowlist ties to one stage, if any.

    Approved public documents carry no stage field in the G1 contract, so this
    returns nothing rather than guessing an owner for a document.
    """
    del documents, stage_id
    return []


def build_stage_nodes(
    *,
    transport_mode: Any,
    public_events: Sequence[Mapping[str, Any]] = (),
    publication: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build the seven 00..06 stages for one lot from approved public events.

    A stage is ``COMPLETED`` only when at least one approved public event maps to
    it.  Everything else stays ``UNKNOWN``: no inference from ordering, from the
    publication version, or from the previous stage's state.
    """
    mode = mode_key(transport_mode)
    labels = STAGE_LABELS[mode]
    pub = dict(publication or {})
    approved_at = _text(pub.get("approved_at"), 40)
    version = _text(pub.get("version"), 20)

    by_stage: dict[str, list[Mapping[str, Any]]] = {}
    for event in public_events or ():
        if not isinstance(event, Mapping):
            continue
        stage_id = _event_stage(event)
        if stage_id:
            by_stage.setdefault(stage_id, []).append(event)

    nodes: list[dict[str, Any]] = []
    for index, (stage_id, label) in enumerate(zip(STAGE_IDS, labels)):
        events = by_stage.get(stage_id, [])
        latest = events[0] if events else None
        if latest is not None:
            evidence = _text(latest.get("title"), 200) or "Đã có mốc xác minh được công bố"
            occurred_at = display_timestamp(latest.get("occurred_at"))
            state = "COMPLETED"
        else:
            evidence = "Chưa có dữ liệu được duyệt cho công đoạn này"
            occurred_at = ""
            state = "UNKNOWN"
        nodes.append({
            "id": stage_id,
            "index": f"{index:02d}",
            "label": label,
            "state": state,
            "completed": state == "COMPLETED",
            # "current" is never inferred: it needs an explicit stage marker
            # that the G1 publication contract does not carry.
            "current": False,
            "evidence": evidence,
            "occurred_at": occurred_at,
            "stage_documents": _stage_documents((), stage_id),
            "stage_comments": [],
            "publication_version": version,
            "approved_at": approved_at,
        })
    return nodes


def build_lot_model(card: Any) -> dict[str, Any]:
    """Project one :class:`core.customer_portal.PublicationCard` for the UI."""
    mode = mode_key(getattr(card, "transport_mode", None))
    public_events = [dict(e) for e in (getattr(card, "timeline", ()) or ()) if isinstance(e, Mapping)]
    documents = [dict(d) for d in (getattr(card, "documents", ()) or ()) if isinstance(d, Mapping)]

    raw_approved_at = _text(getattr(card, "approved_at", ""), 40)
    publication = {
        "version": _text(getattr(card, "publication_version", ""), 20),
        "approved_at": display_timestamp(raw_approved_at),
        "approved_at_raw": raw_approved_at,
    }
    nodes = build_stage_nodes(
        transport_mode=mode,
        public_events=public_events,
        publication=publication,
    )
    completed = [n for n in nodes if n["completed"]]
    current_stage = completed[-1] if completed else None

    verified_eta = _text(getattr(card, "verified_eta_label", ""), 40)
    contact = _text(getattr(card, "contact_point", ""), 120)
    cargo = _text(getattr(card, "cargo_summary", ""), 200)
    route = _text(getattr(card, "route_summary", ""), 200)
    has_cargo = bool(cargo or route)
    next_step = ""
    if current_stage is not None:
        position = STAGE_IDS.index(current_stage["id"])
        upcoming = nodes[position + 1] if position + 1 < len(nodes) else None
        if upcoming is not None and upcoming["completed"]:
            next_step = ""

    public_documents = [
        {
            "id": _text(d.get("id"), 40),
            "version": _text(d.get("version"), 20),
            "kind": _text(d.get("kind"), 40),
            "title": _text(d.get("title"), 160),
        }
        for d in documents
        if _text(d.get("id"), 40)
    ]
    # Issue #244 — Node 00 "Hồ sơ Kế hoạch đã công bố": an EXPLICIT kind-filter
    # (CUSTOMER_QUOTE / CUSTOMER_CONTRACT / PAYMENT_REQUEST) over the documents
    # that already passed the publication allowlist. Metadata only: no amount,
    # no bytes, no storage id. A published document proves neither a signature
    # nor a payment, and ``stage_documents`` stays intentionally empty.
    plan_documents = customer_plan_documents(public_documents)
    # Owner 5C: legacy quote prices cannot reach portal model.
    public_timeline = [
        {
            "stage": _text(e.get("title"), 80),
            "occurred_at": display_timestamp(e.get("occurred_at")),
            "title": _text(e.get("title"), 200),
        }
        for e in public_events
    ]

    return {
        "shipment_id": _text(getattr(card, "reference", ""), 40),
        "transport_mode": _MODE_LABELS.get(mode, ""),
        "mode_known": mode is not None,
        # An unpublished cargo/route is displayed as one explicit unknown, never
        # as a placeholder repeated in the toolbar and the table.
        "cargo_summary": cargo or "Chưa công bố",
        "route_summary": route or ("Chưa công bố" if not has_cargo else ""),
        "has_cargo_route": has_cargo,
        "verified_stage_label": current_stage["label"] if current_stage else UNKNOWN_STAGE_LABEL,
        "verified_stage_title": current_stage["evidence"] if current_stage else UNKNOWN_STAGE_DETAIL,
        "verified_warehouse_eta_label": verified_eta or UNKNOWN_ETA_LABEL,
        "verified_warehouse_eta": bool(verified_eta),
        "last_updated_label": publication["approved_at"] or UNKNOWN_UPDATED_LABEL,
        "contact_point": contact,
        "next_step": next_step,
        "publication": publication,
        # No reconciliation record crosses the G1 publication boundary, so the
        # debt block is explicitly unknown instead of guessing from the quote.
        "debt_summary": {"status": "UNKNOWN", "currency": "VND"},
        "finance_detail": None,
        "quote": None,
        "documents": public_documents,
        # Issue #244 — the three allowed plan document kinds, still bound to
        # this lot's PUBLISHED allowlist. Empty is an explicit statement.
        "plan_documents": plan_documents,
        "plan_documents_empty_label": (
            "" if plan_documents else "Chưa có hồ sơ Kế hoạch được công bố"
        ),
        "timeline": public_timeline,
        "journey": {
            "nodes": nodes,
            "edges": [
                {"from": STAGE_IDS[i], "to": STAGE_IDS[i + 1]}
                for i in range(len(STAGE_IDS) - 1)
            ],
        },
    }


def build_portal_model(
    view: Any,
    *,
    brand_sub: str = "Theo dõi trực quan trên hải đồ theo dữ liệu Trường Thành đã xác minh",
    demo_flag: str | None = None,
    notice: Mapping[str, Any] | None = None,
    account_label: str = "",
    discussion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the whole component payload for one verified principal.

    ``discussion`` is the ONE Journey Map node conversation the customer just
    opened (already tenant-checked and CUSTOMER-visible only). It is attached
    as its own slice and never merged into a node's published evidence, so a
    comment can never look like an approved milestone.
    """
    principal = getattr(view, "principal", None)
    cards = tuple(getattr(view, "cards", ()) or ())
    lots = [build_lot_model(card) for card in cards]
    verified_eta_count = sum(1 for lot in lots if lot["verified_warehouse_eta"])
    return {
        "brand_sub": brand_sub,
        "demo_flag": demo_flag,
        "notice": dict(notice) if notice else None,
        "customer": {
            "name": _text(getattr(principal, "display_name", ""), 120) or "Khách hàng",
            "badge": "HEXA",
            "account_label": _text(account_label, 120),
        },
        "kpi": {
            "tracking": len(lots),
            "verified_eta": verified_eta_count,
            "customer_action": 0,
            "customer_action_sub": "Chưa có yêu cầu được xác nhận",
        },
        "lots": lots,
        "counts": {
            "published": len(lots),
            "denied": int(getattr(view, "denied_lots", 0) or 0),
            "data_issues": int(getattr(view, "data_issues", 0) or 0),
        },
        # Issue #236 — exactly one lot + one stage, or None. Deliberately NOT
        # folded into stage evidence/state: talking does not complete a stage.
        "discussion": dict(discussion) if isinstance(discussion, Mapping) else None,
    }
