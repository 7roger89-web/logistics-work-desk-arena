"""Logistics view-model + the ONE bounded event dispatcher (Phase B).

Phase B replaces the Phase A sandbox seed projection with a presentation
adapter over the CURRENT Logistics readers (``views.logi_real_data``), and
routes every material component event through the canonical write path:

    frontend typed event
      → bounded dispatcher (this module)
      → current RBAC (core.auth)
      → existing writer/service (core.database / core.docgen)
      → audit (written by the canonical writer)
      → fresh backend read
      → refreshed view-model (same route/tab retained by the component)

No frontend-only mutation is treated as persistence: the dispatcher returns a
per-event result carrying the fresh readback, and the UI is refreshed from the
backend, never from local state alone.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

import streamlit as st

from views import ceo_report as logi_ceo_report
from views import handbook as logi_handbook
from views import logi_c1
from views import logi_real_data as rd
from views import logi_sandbox
from views import partner_context as logi_partner_context
from views import reconciliation_desk as logi_reconciliation
from views import tariff_lookup as logi_tariff
from views import translation as logi_translation
from views import user_access as logi_user_access

STATE_KEY = "logi_state"
SEQ_KEY = "logi_seq"

#: Session key where ``dispatch()`` records the authoritative outcome of every
#: business event it handled. Embedding it back into the NEXT view-model is
#: what lets the component learn the backend's real answer (ok + fresh
#: readback, or the actual refusal reason) — never from transport alone.
LAST_WRITES_KEY = "logi_last_writes"


# ---------------------------------------------------------------------------
# Read side
# ---------------------------------------------------------------------------

def read_shipment(shipment_id: str) -> dict[str, Any] | None:
    """Fresh read of ONE shipment straight from the database.

    Deliberately bypasses the Streamlit read cache so a post-write readback is
    the database's own answer, then runs the canonical ``repair_data``
    normalisation the rest of the app uses.
    """
    from core.database import get_db, repair_data

    db = get_db()
    if db is None:
        return None
    doc = db.shipments.find_one({"id": shipment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not doc:
        return None
    return repair_data({shipment_id: doc})[shipment_id]


def load_shipments() -> dict[str, Any]:
    """Fresh shipment read for the component, bypassing the 30s read cache.

    ``core.database.load_data`` is cached for performance in the Streamlit
    runtime. The Logi-good work desk must show a write the moment it lands, so
    it calls the same module's uncached implementation directly — the same
    query, the same ``repair_data`` normalisation, no second source of truth.
    """
    from core.database import _load_data_impl

    return _load_data_impl() or {}


def _load_references() -> dict[str, Any]:
    from core.database import load_contracts, load_customers, load_quotes, load_tasks

    return {
        "customers": load_customers() or {},
        "contracts": load_contracts() or {},
        "quotes": load_quotes() or {},
        "tasks": load_tasks() or [],
    }


def _knowledge_notes() -> list[dict[str, Any]]:
    """Team notebook, read through the EXISTING canonical reader (read-only).

    ``core.database.load_knowledge_base`` is the same reader the legacy
    ``views/knowledge_base.py`` screen uses — no second store and no new query
    layer are introduced here. An unconfigured deployment yields ``[]``, which
    the handbook renders as an honest empty state.
    """
    from core.database import load_knowledge_base

    try:
        return list(load_knowledge_base() or [])
    except Exception:  # noqa: BLE001 — a missing notebook must not blank the desk
        return []


def _users_reader() -> list[dict[str, Any]]:
    """User accounts, read through the EXISTING canonical reader (read-only).

    ``core.database.load_users`` is the same reader core.auth uses to
    authenticate.  Only ``views.user_access`` consumes the result and it keeps
    the canonical password-free public fields, so no credential material can
    reach the payload.  A deployment with no user store yields ``[]``, which
    the /nguoi-dung page renders as an honest empty state.
    """
    from core.database import load_users

    try:
        return list(load_users().values())
    except Exception:  # noqa: BLE001 — a missing user store must not blank the desk
        return []


def _dashboard_views(shipments: Mapping[str, Any]) -> dict[str, Any]:
    from core.shipment_dashboard import build_shipment_dashboard_view

    views: dict[str, Any] = {}
    for sid, ship in shipments.items():
        try:
            views[sid] = build_shipment_dashboard_view(ship)
        except Exception:  # noqa: BLE001 - one bad row must not blank the desk
            views[sid] = {}
    return views


def _home_projection(rows: list[dict[str, Any]], summary: Mapping[str, Any],
                     references: Mapping[str, Any]) -> dict[str, Any]:
    """Home tiles/banners from real shipment facts. No fabricated KPI."""
    def _stage_rows(stage: str) -> list[dict[str, Any]]:
        return [row for row in rows if row["status"] == stage]

    running = [row for row in rows if row["status"] not in {"Đã giao", "Đã hủy"}]

    def _tile(label: str, stage: str) -> dict[str, Any]:
        matches = _stage_rows(stage)
        return {
            "label": label,
            "value": len(matches),
            "sub": ", ".join(m["id"] for m in matches[:4]) or rd.UNKNOWN_LABEL,
            "to": f"/lo-hang/{matches[0]['id']}" if matches else "/lo-hang",
        }

    delivered = _stage_rows("Đã giao")

    outstanding = [row["finance"]["outstanding"] for row in rows
                   if row["finance"]["outstanding"] is not None and row["finance"]["outstanding"] > 0]
    outstanding_total = sum(outstanding) if outstanding else None

    urgent = [row for row in rows if row["priority"] == "Khan"]
    focus = urgent[0] if urgent else (next((r for r in rows if r["priority"] == "CanXuLy"), None) or (rows[0] if rows else None))

    return {
        "tiles": [
            {
                "label": "Lô đang chạy",
                "value": len(running),
                "sub": ", ".join(r["id"] for r in running[:4]) or rd.UNKNOWN_LABEL,
                "to": "/lo-hang",
            },
            _tile("Chờ lấy hàng", "Chờ lấy hàng"),
            _tile("Đang vận chuyển", "Đang vận chuyển"),
            _tile("Chờ thông quan", "Chờ thông quan"),
            _tile("Chờ giao", "Chờ giao"),
            {"label": "Đã giao", "value": len(delivered),
             "sub": ", ".join(m["id"] for m in delivered[:4]) or rd.UNKNOWN_LABEL, "to": "/lo-hang"},
        ],
        "runningCount": len(running),
        "runningSummary": [
            {"id": r["id"], "customer": r["customer"], "status": r["status"],
             "nextAction": r["nextAction"], "to": f"/lo-hang/{r['id']}"}
            for r in running[:6]
        ],
        "outstandingTotal": outstanding_total,
        "outstandingTotalLabel": rd._money_label(outstanding_total) if outstanding_total is not None else rd.UNKNOWN_LABEL,
        "outstandingCount": len(outstanding),
        "summary": {
            "total": int(summary.get("total") or 0),
            "critical": int(summary.get("critical") or 0),
            "warning": int(summary.get("warning") or 0),
            "deadlineSoon": int(summary.get("deadline_soon") or 0),
            "financialAttention": int(summary.get("financial_attention") or 0),
            "missingInfo": int(summary.get("missing_info") or 0),
        },
        "urgentCount": len(urgent),
        "focus": {
            "id": focus["id"], "customer": focus["customer"], "status": focus["status"],
            "nextAction": focus["nextAction"], "nextActionDetail": focus["nextActionDetail"],
            "priority": focus["priority"], "to": focus["nextRoute"],
        } if focus else None,
        "missingDocsTotal": sum(len(r["missingDocs"]) for r in rows),
        "taskCount": len(references.get("tasks") or []),
    }


def _task_projection(rows: list[dict[str, Any]], references: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Tasks from real readiness/dashboard evidence + the real tasks collection.

    Every row routes to the real shipment and the correct tab. No mock rows.
    """
    stage_tab = {
        "Chờ thông quan": "nhap",
        "Chờ giao": "nhap",
        "Chờ lấy hàng": "lay-hang",
        "Đang vận chuyển": "lay-hang",
        "Đã giao": "chung-tu",
    }
    out: list[dict[str, Any]] = []

    for row in rows:
        if row["priority"] == "BinhThuong" and not row["missingDocs"]:
            continue
        level = row["priority"]
        tab = stage_tab.get(row["status"], "lay-hang")
        out.append({
            "id": f"OPS-{row['id']}",
            "level": level,
            "lot": row["id"],
            "customer": row["customer"],
            "job": row["nextAction"],
            "assignee": row["support"] or rd.UNKNOWN_LABEL,
            "due": row["ops"].get("arrivalDateLabel") or rd.UNKNOWN_LABEL,
            "dueNote": row["nextActionDetail"] or (", ".join(f"thiếu {m}" for m in row["missingDocs"][:3])),
            "status": row["status"],
            "statusTone": row["statusTone"],
            "route": f"/lo-hang/{row['id']}?tab={tab}",
            "source": "core.shipment_dashboard (readiness/alerts)",
        })

    by_id = {row["id"]: row for row in rows}
    for task in references.get("tasks") or []:
        if not isinstance(task, Mapping):
            continue
        sid = rd.text(task.get("shipment_id"))
        row = by_id.get(sid)
        done = bool(task.get("done"))
        out.append({
            "id": rd.text(task.get("task_id")),
            "level": "BinhThuong" if done else "CanXuLy",
            "lot": sid or rd.UNKNOWN_LABEL,
            "customer": row["customer"] if row else rd.UNKNOWN_LABEL,
            "job": rd.text(task.get("content")),
            "assignee": rd.text(task.get("assignee")) or rd.UNKNOWN_LABEL,
            "due": rd._ddmmyyyy(task.get("deadline")),
            "dueNote": "Đã hoàn thành" if done else "Việc được giao",
            "status": "Đã xong" if done else "Chưa làm",
            "statusTone": "green" if done else "amber",
            "route": f"/lo-hang/{sid}?tab=lay-hang" if sid else "/lo-hang",
            "source": "core.database.load_tasks",
        })

    order = {"Khan": 0, "CanXuLy": 1, "BinhThuong": 2}
    out.sort(key=lambda item: (order.get(item["level"], 9), item["lot"]))
    return out


def _notifications(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if not row["ops"]["alerts"]:
            continue
        alert = row["ops"]["alerts"][0]
        severity = alert.get("severity")
        out.append({
            "id": f"{row['id']}-{alert.get('code')}",
            "title": f"{row['id']} · {alert.get('title')}",
            "desc": alert.get("message") or row["nextActionDetail"],
            "time": row["updated"],
            "tone": "red" if severity == "critical" else ("amber" if severity == "warning" else "blue"),
            "route": row["nextRoute"],
        })
    return out


def _last_writes_readback() -> list[dict[str, Any]]:
    """Authoritative outcomes of the events the dispatcher already handled.

    ``dispatch()`` stores them under ``LAST_WRITES_KEY``; the component matches
    them by the ``requestId`` it sent with the event, so one outcome can never
    be mistaken for the answer to a different request.
    """
    rows = st.session_state.get(LAST_WRITES_KEY) or []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _read_sources(shipments: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    """ONE fresh request/render-local snapshot of the shared read sources.

    PERFORMANCE REPAIR (no cache layer, no new store): every projection built by
    ``build_view_model`` needs the same canonical rows, and reading them once per
    shipment was the proven N+1 defect — with ~95 real shipments the finance path
    alone issued ~570 full ledger collection reads for a single render.

    This reads each shared source exactly once, for THIS render, and hands the
    very same in-memory rows to every consumer below:

    * ``ledger``          — the three canonical financial collections
      (``core.financial_ledger.load_ledger_snapshot``), shared by the per-shipment
      C2B block, the C2D payables worklist and the reconciliation desk;
    * ``agents``          — the authority_agents legal master;
    * ``timelines``       — shipment audit history for the worklist rows, in ONE
      bounded audit read instead of one read per shipment;
    * ``docgenDocuments`` — canonical docgen metadata grouped by shipment, ONE
      read instead of one per projected PXK;
    * ``linkedContracts`` — the contract ↔ shipment linkage, indexed in memory
      from the contracts already loaded (zero reads);
    * ``shipmentIds``     — the ids the two global finance worklists both need,
      read once instead of once each.

    Nothing is stored on the session, the module or the process: the next
    Streamlit rerun calls this again and therefore sees the freshest data, so a
    write is visible on the very next render exactly as before.
    """
    from core.database import load_authority_agents, load_shipment_ids
    from core.financial_ledger import load_ledger_snapshot

    shipment_ids = [str(sid) for sid in shipments.keys()]
    try:
        agents = load_authority_agents() or {}
    except Exception:  # noqa: BLE001 - a missing master must not blank the desk
        agents = {}
    return {
        "ledger": load_ledger_snapshot(),
        "agents": agents,
        "timelines": rd.timelines_projection(shipment_ids),
        "docgenDocuments": rd.docgen_documents_by_shipment(),
        "linkedContracts": rd.linked_contracts_index(references.get("contracts")),
        "shipmentIds": load_shipment_ids(),
    }


def build_view_model() -> dict:
    """Assemble the JSON payload for the component `data` channel."""
    from core.auth import current_user
    from core.shipment_dashboard import build_dashboard_summary

    transport = logi_sandbox.ensure_backend()
    shipments = load_shipments()
    references = _load_references()
    views = _dashboard_views(shipments)
    sources = _read_sources(shipments, references)

    rows = [
        rd.shipment_projection(
            ship,
            customers=references["customers"],
            contracts=references["contracts"],
            quotes=references["quotes"],
            dashboard=views.get(sid, {}),
            # One bounded audit read for the whole worklist, grouped in memory;
            # a shipment with no audit row stays [] exactly as before.
            history=sources["timelines"].get(sid, []),
            # The SAME render-local snapshot every row and every global worklist
            # below share: one ledger read, one docgen read, one agents read.
            ledger=sources["ledger"],
            agents=sources["agents"],
            docgen_documents=sources["docgenDocuments"],
            linked_contracts=sources["linkedContracts"],
        )
        for sid, ship in shipments.items()
    ]
    order = {"Khan": 0, "CanXuLy": 1, "BinhThuong": 2}
    rows.sort(key=lambda row: (order.get(row["priority"], 9), row["id"]))

    summary = build_dashboard_summary(views.values())
    user = current_user() or {}
    # The contract→shipment links read the SAME shipment map this render already
    # loaded, so C1 adds no second full shipments read.
    c1 = logi_c1.assemble_c1_payload(shipments=shipments)

    # C2D is read ONCE per render and shared by both the global worklist and the
    # /ngu-canh-doi-tac partner-context slice — one payable truth, no second
    # derivation of a partner's financial position. It derives from the SAME
    # render-local ledger snapshot the per-shipment C2B block used.
    payables = rd.partner_payables_projection(
        records=sources["ledger"],
        shipment_ids=sources["shipmentIds"],
        agents=sources["agents"],
    )
    home = _home_projection(rows, summary, references)
    tasks = _task_projection(rows, references)
    receivables = rd.receivables_projection(rows)
    # The reconciliation desk derives from the SAME render-local snapshot (ids +
    # ledger rows) instead of re-reading both collections once per shipment.
    reconciliation = logi_reconciliation.reconciliation_view(
        st.session_state.get(RECONCILIATION_FILTER_KEY),
        known_shipment_ids=list(shipments.keys()),
        shipment_ids=sources["shipmentIds"],
        records=sources["ledger"],
    )
    # LOGI_CEO_REPORT_01 — one bounded READ-ONLY presentation adapter over
    # projections already built above. It does not open a second reader, create
    # a finance model or calculate a cross-currency total.
    ceo_report = logi_ceo_report.ceo_report_projection(
        shipments=rows,
        home=home,
        tasks=tasks,
        receivables=receivables,
        payables=payables,
        reconciliation=reconciliation,
    )

    model = {
        "version": _payload_version(rows, references, c1),
        "environment": {
            "transport": transport,
            "label": "Preview / Staging" if transport == logi_sandbox.SANDBOX_TRANSPORT else "Production",
            "isSandbox": transport == logi_sandbox.SANDBOX_TRANSPORT,
            "database": "isolated staging (mongomock)" if transport == logi_sandbox.SANDBOX_TRANSPORT else "real MongoDB",
        },
        "user": {
            "name": rd.text(user.get("full_name") or user.get("username")) or "Chưa đăng nhập",
            "role": rd.text(user.get("role")).upper() or "VIEWER",
            "username": rd.text(user.get("username")),
            # Display only. Authorization is enforced by core.auth on the server.
            "displayOnly": True,
        },
        "shipments": rows,
        "home": home,
        "tasks": tasks,
        "contracts": c1["contracts"],
        "customers": c1["customers"],
        "quotes": c1["quotes"],
        "agreements": c1["agreements"],
        "authority": c1["authority"],
        "notifications": _notifications(rows),
        # C2C — global customer-receivable worklist, a read-only projection over
        # the SAME shipment finance truth already delivered above. No new ledger,
        # no new accounting model: one row per shipment + per-currency totals.
        "receivables": receivables,
        # C2D — global partner-payable worklist (THANH TOÁN ĐỐI TÁC / PHẢI TRẢ),
        # read-only over the SAME canonical ledger the C2B per-shipment slice
        # uses. No new ledger: one row per SHIPMENT × PARTNER × CURRENCY.
        "payables": payables,
        # LOGI_PARTNER_CONTEXT_WORKSPACE_01 — bounded READ-ONLY exposure of the
        # partner/entity context that already exists (core.entity_context over
        # the shipment-partner index, the authority_agents legal master, and the
        # C2D payable rows just built above) for the /ngu-canh-doi-tac workspace.
        # The selection is a key only; every field comes back from the readers.
        "partnerContext": logi_partner_context.partner_context_view(
            st.session_state.get(PARTNER_CONTEXT_KEY) or "",
            payables=payables,
            customers=references["customers"],
            shipments=shipments,
        ),
        # LOGI_RECONCILIATION_DESK_01 — bounded READ-ONLY exposure of the
        # reconciliation capability that already exists: the allocation matching
        # core.financial_ledger already derives per shipment (obligation ↔
        # allocation ⇒ matched / partial / unmatched, transaction ⇒ allocated /
        # unallocated), over the SAME canonical financial_obligations /
        # financial_transactions / financial_allocations truth. Currencies stay
        # separate, UNKNOWN stays UNKNOWN, and the desk writes nothing.
        "reconciliation": reconciliation,
        # LOGI_CEO_REPORT_01 — a current-position management view only. Its
        # fields are assembled from the projections already in this response;
        # there is no analytics reader, persistence, event or finance rewrite.
        "ceoReport": ceo_report,
        # LOGI_NOTEBOOK_WORKSPACE_01 — the /so-tay handbook. A bounded READ-ONLY
        # slice over reference material this repository already owns and the rest
        # of the app already reads (core.config constants, the locked docgen
        # rules, the trade-compliance source registry, the single RBAC matrix)
        # plus the team's real notes via the existing load_knowledge_base reader.
        # No content store, no authoring event, no search backend: the page
        # filters the delivered text client-side.
        "handbook": logi_handbook.handbook_projection(
            field_paths=FIELD_PATHS,
            notes=_knowledge_notes(),
        ),
        # LOGI_USER_ACCESS_WORKSPACE_01 — the /nguoi-dung workspace. A bounded
        # READ-ONLY slice over the auth/user/RBAC capability that already
        # exists (load_users read through core.users' canonical public view,
        # the single ROLE_PERMISSIONS matrix, the real AUTH_REQUIRED mode and
        # the current session identity). No credential material, no invented
        # role/permission, no write path: user mutations stay with the
        # canonical core.database writers and none is exposed by this page.
        "userAccess": logi_user_access.user_access_projection(
            users=_users_reader(),
            current_user=user,
        ),
        # LOGI_TARIFF_LOOKUP_01 — bounded read-only HS/tariff lookup over the
        # EXISTING governed reference database (see views/tariff_lookup.py).
        # Absent from session state until the user submits a query; the
        # adapter fails honest (UNKNOWN != ZERO) in every empty state.
        "tariff": logi_tariff.tariff_lookup_view(
            st.session_state.get(TARIFF_QUERY_KEY) or ""
        ),
        # LOGI_TRANSLATION_WORKSPACE_01 — bounded exposure of the EXISTING DeepL
        # capability (core.deepl_translation via views.translation) for the
        # /dich-thuat workspace. The translation itself already happened inside
        # the bounded dispatcher, so this is a pure readback: capability state
        # (configured? which languages does the provider really accept?) plus
        # the last request and its authoritative result. No key ever leaves the
        # backend; an unconfigured deployment shows an honest "chưa được cấu
        # hình" state instead of a fabricated translation.
        "translation": logi_translation.translation_view(
            request=st.session_state.get(TRANSLATION_REQUEST_KEY),
            result=st.session_state.get(TRANSLATION_RESULT_KEY),
        ),
        # LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — the authoritative
        # outcome(s) of the business event(s) the bounded dispatcher handled on
        # the previous run. The UI must never treat "event transported" as
        # "write succeeded": success, duplicate/RBAC/validation refusals and the
        # fresh readback all arrive HERE, after the canonical writer ran.
        "lastWrites": _last_writes_readback(),
        "unknownLabel": rd.UNKNOWN_LABEL,
    }
    _remember(model)
    return model


def _payload_version(rows: list[dict[str, Any]], references: Mapping[str, Any],
                     c1: Mapping[str, Any] | None = None) -> str:
    """Deterministic content version: changes only when data actually changes."""
    raw = json.dumps(
        {"s": rows, "t": references.get("tasks"), "c": list((references.get("contracts") or {}).keys()),
         "q": list((references.get("quotes") or {}).keys()),
         "c1": (c1 or {})},
        sort_keys=True, ensure_ascii=False, default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# The ONE bounded event dispatcher
# ---------------------------------------------------------------------------

# Phase A event set — kept verbatim so the Phase A acceptance suite still runs.
ALLOWED_EVENTS = {"shipment_update", "navigate"}

# Phase B typed write events. Anything outside these two sets is dropped.
PHASE_B_EVENTS = {
    "shipment_field_save",
    # Repeatable lists cannot be represented safely by the scalar field
    # whitelist.  This one shipment-local event writes exactly the canonical
    # operational collections through the existing atomic writer.
    "shipment_transport_save",
    "delivery_confirm",
    "finance_actual_save",
    "payment_record",
    "payment_correction",
    "shipment_create",
    "pxk_generate",
    # C2B — single-partner payable slice. The canonical writers are
    # core.financial_ledger.save_obligation / save_transaction /
    # allocate_transaction; these events are only the bounded shell boundary
    # (RBAC → writer → audit → fresh readback), mirroring payment_record.
    "partner_payable_record",
    "partner_payment_record",
}

# LOGI_TARIFF_LOOKUP_01 — one bounded READ-ONLY query event for the
# /tra-cuu-thue workspace. It performs no business mutation: the handler only
# records the query for the next fresh read in build_view_model(). The
# authoritative result always comes from the existing canonical reader
# (core.utils.fast_search_tariff) via views.tariff_lookup.
TARIFF_EVENTS = {"tariff_lookup"}

# LOGI_TRANSLATION_WORKSPACE_01 — one bounded event for the /dich-thuat
# workspace. It is NOT a business mutation (no document, ledger or shipment is
# written): it performs ONE text translation through the EXISTING canonical
# DeepL client and stores the readback for the next fresh view-model.
TRANSLATION_EVENTS = {"translate_text"}

# LOGI_PARTNER_CONTEXT_WORKSPACE_01 — one bounded READ-ONLY selection event for
# the /ngu-canh-doi-tac workspace. Exactly like tariff_lookup it mutates nothing:
# the handler only records WHICH existing entity the Owner picked, and the next
# fresh read in build_view_model() embeds the authoritative context projection
# (core.entity_context + authority_agents + the canonical C2B/C2D ledger).
PARTNER_CONTEXT_EVENTS = {"partner_context_select"}

# LOGI_RECONCILIATION_DESK_01 — ONE bounded READ-ONLY filter event for the
# /tai-chinh/doi-soat desk. It mutates nothing: the handler only records the
# query / currency / state / side the Owner picked, and the next fresh read in
# build_view_model() re-derives every figure from the canonical ledger
# (core.financial_ledger.shipment_partner_position). There is deliberately no
# reconcile/write event here — recording a payable or a payment stays on the
# existing canonical C2B/C2D and C2C surfaces the desk links to.
RECONCILIATION_EVENTS = {"reconciliation_filter"}

ALL_EVENTS = (ALLOWED_EVENTS | PHASE_B_EVENTS | logi_c1.C1_EVENTS
              | TARIFF_EVENTS | TRANSLATION_EVENTS | PARTNER_CONTEXT_EVENTS
              | RECONCILIATION_EVENTS)

#: Session key holding the current tariff lookup query (read-only surface).
TARIFF_QUERY_KEY = "logi_tariff_query"

#: Session readback of the last /dich-thuat request and of its result.
TRANSLATION_REQUEST_KEY = "logi_translation_request"
TRANSLATION_RESULT_KEY = "logi_translation_result"

#: Session readback of the /ngu-canh-doi-tac selection (a partner key only — the
#: context itself is always re-derived from the authoritative readers below).
PARTNER_CONTEXT_KEY = "logi_partner_context_selection"

#: Session readback of the /tai-chinh/doi-soat filter (query / currency / state
#: / side only). Every figure is always re-derived from the canonical ledger on
#: the next read; this key never holds a money value.
RECONCILIATION_FILTER_KEY = "logi_reconciliation_filter"


def _translation_fingerprint(text: str, source_lang: str, target_lang: str) -> str:
    """Stable identity of ONE translation intent (never carries a credential).

    Used by the same-intent guard: an enthusiastic thumb must not pay the
    external provider twice for the identical request.
    """
    raw = f"{text}\x00{source_lang}\x00{target_lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

# Whitelist: component field key → canonical shipment document path.
# Only these paths may be written by the component.
FIELD_PATHS: dict[str, tuple[str, ...]] = {
    "mode": ("data", "0.0", "mode"),
    "incoterm": ("data", "0.0", "incoterm"),
    "booking_no": ("data", "1.2", "booking_no"),
    "carrier": ("data", "1.2", "carrier"),
    "mbl": ("data", "1.2", "mbl"),
    "hbl": ("data", "1.2", "hbl"),
    "vessel": ("data", "1.2", "vessel"),
    "etd": ("data", "1.2", "etd"),
    "pol": ("data", "1.2", "pol"),
    "pod": ("data", "1.2", "pod"),
    "container_no": ("data", "1.2", "container_no"),
    "qty_pkg": ("data", "1.2", "qty_pkg"),
    "tk_no": ("data", "2.4", "tk_no"),
    "customs_status": ("data", "2.4", "customs_status"),
    "phan_luong": ("data", "2.4", "phan_luong"),
    # LOGI_GNT_CANONICAL_FIELDS_01 — Owner-approved business truth
    # (2026-09-12). Exactly three new customs/tax fields, and nothing else:
    #   tk_date             canonical customs declaration date for NEW data
    #   import_duty_amount  ACTUAL import duty in VND
    #   import_vat_amount   ACTUAL import VAT in VND
    # Both amounts are operator-keyed from the real customs notice / GNT
    # paper. They are NEVER calculated here: no rate, no HS lookup, no FX,
    # no arithmetic. A blank stays blank, so UNKNOWN is never written as 0.
    # `reg_date` is deliberately NOT writable — it survives only as a read
    # fallback for legacy documents (see views/logi_real_data.py).
    # `data.2.4.gnt.ds_thue[]` stays legacy evidence and is NOT promoted to a
    # source of truth by this change.
    "tk_date": ("data", "2.4", "tk_date"),
    "import_duty_amount": ("data", "2.4", "import_duty_amount"),
    "import_vat_amount": ("data", "2.4", "import_vat_amount"),
    # LOGI_CN_TRUCK_TYPE_PERSIST_01 — Owner-approved business truth
    # (2026-09-12). Exactly one new pickup/transport field, and nothing else:
    #   pickup_truck_type   free-text fact describing the CN pickup truck
    #                       type/size of THIS shipment (e.g. "17.5m · rộng 3m
    #                       · tải ≤30t"), keyed by the operator. NEVER derived:
    #                       no inference, no capacity/weight/CBM/pricing math.
    # It is NOT the VN delivery truck (data.2.7.truck_no) and NOT the
    # container/plate identifier (data.1.2.container_no). A blank stays blank,
    # so UNKNOWN is never written as a value.
    "pickup_truck_type": ("data", "1.2", "pickup_truck_type"),
    "arrival_date": ("data", "2.6", "arrival_date"),
    "free_time": ("data", "2.6", "free_time"),
    "truck_no": ("data", "2.7", "truck_no"),
    "seal_no": ("data", "2.7", "seal_no"),
    "delivery_date": ("data", "2.7", "delivery_date"),
    "phone_receiver": ("data", "2.7", "phone_receiver"),
    "addr": ("data", "2.7", "addr"),
    "receiver_name": ("data", "2.7", "receiver_name"),
    "receiver_title": ("data", "2.7", "receiver_title"),
    "delivery_location": ("data", "2.7", "delivery_location"),
    "status": ("status",),
}

_BOOL_FIELDS = {"customs_status"}
# LOGI_GNT_CANONICAL_FIELDS_01 — the two ACTUAL import-tax amounts coerce
# through the same numeric path `free_time` already uses, so a blank stays ""
# (UNKNOWN) and is never turned into 0. The declaration date joins the
# existing date path, which stores the canonical ISO form.
_NUM_FIELDS = {"free_time", "import_duty_amount", "import_vat_amount"}
_DATE_FIELDS = {"etd", "arrival_date", "delivery_date", "tk_date"}


def _normalize_date(value: Any) -> str:
    """Accept DD/MM/YYYY or ISO and store the canonical ISO form."""
    from datetime import datetime

    raw = str(value or "").strip()
    if not raw:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def _coerce(key: str, value: Any) -> Any:
    """Coerce one component value to its canonical type.

    An empty value stays empty (None/"") — it is never turned into 0, because
    for these fields a blank means UNKNOWN.
    """
    if key in _BOOL_FIELDS:
        return bool(value)
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return ""
    if key in _NUM_FIELDS:
        parsed = rd.num(raw)
        return parsed if parsed is not None else raw
    if key in _DATE_FIELDS:
        return _normalize_date(raw)
    return raw


def _set_path(doc: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor: Any = doc
    for part in path[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    cursor[path[-1]] = value


def _get_path(doc: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    cursor: Any = doc
    for part in path:
        if not isinstance(cursor, Mapping):
            return None
        cursor = cursor.get(part)
    return cursor


def _actor() -> str:
    from core.auth import current_user

    user = current_user() or {}
    return rd.text(user.get("username")) or "system"


def _result(event: str, shipment_id: str, ok: bool, error: str = "",
            readback: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {"event": event, "shipmentId": shipment_id, "ok": ok, "error": error,
            "readback": readback, **extra}


def _projection_for(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Project one canonical shipment for the post-write readback payload."""
    from core.database import load_contracts, load_customers, load_quotes
    from core.shipment_dashboard import build_shipment_dashboard_view

    sid = rd.text(shipment.get("id"))
    try:
        view = build_shipment_dashboard_view(shipment)
    except Exception:  # noqa: BLE001
        view = {}
    return rd.shipment_projection(
        shipment,
        customers=load_customers() or {},
        contracts=load_contracts() or {},
        quotes=load_quotes() or {},
        dashboard=view,
        history=rd.timeline_projection(sid),
    )


def _audit_trail(shipment_id: str, limit: int = 5) -> list[dict[str, Any]]:
    from core.database import load_audit_logs

    return [
        {"action": rd.text(row.get("action")), "actor": rd.text(row.get("actor")),
         "createdAt": str(row.get("created_at"))}
        for row in (load_audit_logs("shipment", shipment_id, limit=limit) or [])
        if isinstance(row, Mapping)
    ]


# --- individual write handlers -------------------------------------------

def _handle_field_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic
    from core.logic import apply_financial_snapshot

    sid = rd.text(payload.get("shipmentId"))
    fields = payload.get("fields") if isinstance(payload.get("fields"), Mapping) else {}
    if not sid or not fields:
        return _result("shipment_field_save", sid, False, "Thiếu shipmentId hoặc fields.")
    if not can_operate_business("shipment_edit"):
        return _result("shipment_field_save", sid, False, "RBAC: không có quyền shipment_edit.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("shipment_field_save", sid, False, f"Không tìm thấy lô {sid}.")

    applied: dict[str, Any] = {}
    rejected: list[str] = []
    for key, value in fields.items():
        path = FIELD_PATHS.get(str(key))
        if path is None:
            rejected.append(str(key))
            continue
        applied[str(key)] = _coerce(str(key), value)
        _set_path(shipment, path, applied[str(key)])

    if not applied:
        return _result("shipment_field_save", sid, False,
                       "Không có trường nào được phép ghi.", rejected=rejected)

    apply_financial_snapshot(shipment)
    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _result("shipment_field_save", sid, False, get_last_db_error() or "Không lưu được.")

    fresh = read_shipment(sid)
    return _result("shipment_field_save", sid, True, readback=_projection_for(fresh or {}),
                   applied=applied, rejected=rejected,
                   version=int((fresh or {}).get("version") or 0),
                   persisted={k: _get_path(fresh or {}, FIELD_PATHS[k]) for k in applied},
                   audit=_audit_trail(sid))


def _handle_shipment_transport_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Save repeatable legs and/or cargo through the existing atomic writer.

    ``shipment_field_save`` is intentionally scalar and path-whitelisted, so
    replacing an ordered collection through it would be unsafe.  This bounded
    handler is the only added semantic surface: RBAC → fresh document → strict
    normalization → save_shipment_atomic → audit → fresh readback.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic
    from core.logic import apply_financial_snapshot
    from core.shipment_operations import normalize_cargo_summary, normalize_transport_legs

    sid = rd.text(payload.get("shipmentId"))
    has_legs = "transportLegs" in payload
    has_cargo = "cargoSummary" in payload
    if not sid or not (has_legs or has_cargo):
        return _result("shipment_transport_save", sid, False,
                       "Thiếu shipmentId hoặc dữ liệu vận hành.")
    if not can_operate_business("shipment_edit"):
        return _result("shipment_transport_save", sid, False,
                       "RBAC: không có quyền shipment_edit.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("shipment_transport_save", sid, False, f"Không tìm thấy lô {sid}.")

    try:
        section = shipment.setdefault("data", {}).setdefault("1.2", {})
        if has_legs:
            section["transport_legs"] = normalize_transport_legs(payload.get("transportLegs"))
        if has_cargo:
            section["cargo_summary"] = normalize_cargo_summary(payload.get("cargoSummary"))
    except ValueError as exc:
        return _result("shipment_transport_save", sid, False, str(exc))

    apply_financial_snapshot(shipment)
    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _result("shipment_transport_save", sid, False,
                       get_last_db_error() or "Không lưu được dữ liệu vận hành.")

    fresh = read_shipment(sid) or {}
    fresh_section = ((fresh.get("data") or {}).get("1.2") or {})
    persisted: dict[str, Any] = {}
    if has_legs:
        persisted["transport_legs"] = fresh_section.get("transport_legs")
    if has_cargo:
        persisted["cargo_summary"] = fresh_section.get("cargo_summary")
    return _result(
        "shipment_transport_save", sid, True,
        readback=_projection_for(fresh),
        persisted=persisted,
        version=int(fresh.get("version") or 0),
        audit=_audit_trail(sid),
    )


def _handle_delivery_confirm(payload: Mapping[str, Any]) -> dict[str, Any]:
    """✅ XÁC NHẬN ĐÃ GIAO HÀNG → the canonical shipment writer + audit."""
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic

    sid = rd.text(payload.get("shipmentId"))
    if not sid:
        return _result("delivery_confirm", sid, False, "Thiếu shipmentId.")
    if not can_operate_business("shipment_edit"):
        return _result("delivery_confirm", sid, False, "RBAC: không có quyền shipment_edit.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("delivery_confirm", sid, False, f"Không tìm thấy lô {sid}.")

    delivery = shipment.setdefault("data", {}).setdefault("2.7", {})
    if delivery.get("is_delivered"):
        return _result("delivery_confirm", sid, True, "Lô đã được xác nhận giao trước đó.",
                       readback=_projection_for(shipment), alreadyConfirmed=True,
                       audit=_audit_trail(sid))

    delivered_on = _normalize_date(payload.get("deliveredAt")) or _normalize_date(
        payload.get("deliveryDate")) or __import__("datetime").date.today().strftime("%Y-%m-%d")

    delivery["is_delivered"] = True
    delivery["delivered_at"] = delivered_on
    delivery["delivery_date"] = delivery.get("delivery_date") or delivered_on
    for source, target in (("receiverName", "receiver_name"), ("receiverTitle", "receiver_title"),
                           ("deliveryLocation", "delivery_location"), ("receiverPhone", "phone_receiver")):
        value = rd.text(payload.get(source))
        if value:
            delivery[target] = value
    if not delivery.get("delivery_location"):
        delivery["delivery_location"] = delivery.get("addr") or ""

    shipment["status"] = "done"
    shipment["data"]["0.0"]["st"] = "done"

    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _result("delivery_confirm", sid, False, get_last_db_error() or "Không lưu được.")

    fresh = read_shipment(sid) or {}
    return _result("delivery_confirm", sid, True, readback=_projection_for(fresh),
                   deliveredAt=delivered_on,
                   persisted={"is_delivered": _get_path(fresh, ("data", "2.7", "is_delivered")),
                              "delivered_at": _get_path(fresh, ("data", "2.7", "delivered_at")),
                              "status": _get_path(fresh, ("status",))},
                   audit=_audit_trail(sid))


def _handle_finance_actual_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Finance Actual = a real service line in ``data.3.4.details``.

    Quote Estimate is a separate object and is never written here.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic
    from core.logic import apply_financial_snapshot

    sid = rd.text(payload.get("shipmentId"))
    line = payload.get("line") if isinstance(payload.get("line"), Mapping) else {}
    if not sid or not line:
        return _result("finance_actual_save", sid, False, "Thiếu shipmentId hoặc line.")
    if not can_operate_business("finance_write"):
        return _result("finance_actual_save", sid, False, "RBAC: không có quyền finance_write.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("finance_actual_save", sid, False, f"Không tìm thấy lô {sid}.")

    finance = shipment.setdefault("data", {}).setdefault("3.4", {})
    details = finance.setdefault("details", [])

    # UNKNOWN != ZERO: a blank amount stays absent rather than becoming 0.
    qty = rd.num(line.get("qty"))
    price = rd.num(line.get("price"))
    cost = rd.num(line.get("cost"))
    vat = rd.num(line.get("vat"))
    name = rd.text(line.get("name"))
    if not name:
        return _result("finance_actual_save", sid, False, "Thiếu tên dịch vụ.")
    if qty is not None and qty <= 0:
        return _result("finance_actual_save", sid, False, "Số lượng phải lớn hơn 0.")

    from uuid import uuid4

    target_id = rd.text(line.get("id"))
    entry: dict[str, Any] | None = None
    if target_id:
        entry = next((d for d in details if isinstance(d, Mapping) and rd.text(d.get("id")) == target_id), None)
    if entry is None:
        entry = {"id": target_id or f"PAY-LINE-{uuid4().hex.upper()[:12]}"}
        details.append(entry)

    entry["name_full"] = name
    entry["display_name"] = name
    entry["unit"] = rd.text(line.get("unit")) or entry.get("unit") or "Lần"
    entry["note"] = rd.text(line.get("note"))
    if rd.text(line.get("code")):
        entry["code"] = rd.text(line.get("code"))
    # Only write numerics that were actually supplied.
    if qty is not None:
        entry["qty"] = qty
    else:
        entry.setdefault("qty", 1.0)
    if price is not None:
        entry["price"] = price
        entry["price_out"] = price
    else:
        entry.setdefault("price", 0.0)
        entry.setdefault("price_out", 0.0)
    if cost is not None:
        entry["cost"] = cost
        entry["price_in"] = cost
    else:
        entry.setdefault("cost", 0.0)
        entry.setdefault("price_in", 0.0)
    if vat is not None:
        entry["vat_line"] = vat
        entry["vat"] = vat
    else:
        entry.setdefault("vat_line", 0.0)
        entry.setdefault("vat", 0.0)

    apply_financial_snapshot(shipment)
    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _result("finance_actual_save", sid, False, get_last_db_error() or "Không lưu được.")

    fresh = read_shipment(sid) or {}
    fresh_lines = _get_path(fresh, ("data", "3.4", "details")) or []
    return _result("finance_actual_save", sid, True, readback=_projection_for(fresh),
                   lineId=entry["id"],
                   persisted={"lineCount": len(fresh_lines),
                              "line": next((d for d in fresh_lines
                                            if rd.text(d.get("id")) == entry["id"]), None),
                              "receivable": _get_path(fresh, ("data", "3.4", "out")),
                              "cost": _get_path(fresh, ("data", "3.4", "in"))},
                   audit=_audit_trail(sid))


def _handle_payment_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """One real payment via ``save_direct_shipment_payment`` (request identity)."""
    from core.database import save_direct_shipment_payment

    sid = rd.text(payload.get("shipmentId"))
    amount = rd.num(payload.get("amount"))
    request_id = rd.text(payload.get("requestId"))
    if not sid or amount is None or not request_id:
        return _result("payment_record", sid, False,
                       "Thiếu shipmentId, amount hoặc requestId (idempotency key).")

    payment = {
        "id": rd.text(payload.get("paymentId")) or None,
        "request_id": request_id,
        "date": _normalize_date(payload.get("date")) or __import__("datetime").date.today().strftime("%Y-%m-%d"),
        "amount": amount,
        "note": rd.text(payload.get("note")),
    }
    payment = {k: v for k, v in payment.items() if v is not None}

    ok, result, message = save_direct_shipment_payment(sid, payment, actor=_actor())
    if not ok:
        return _result("payment_record", sid, False, message or "Không ghi nhận được khoản thu.",
                       requestId=request_id)

    fresh = read_shipment(sid) or {}
    return _result("payment_record", sid, True, message, readback=_projection_for(fresh),
                   requestId=request_id, paymentId=rd.text(result.get("payment_id")),
                   persisted={"paymentId": rd.text(result.get("payment_id")),
                              "amount": float(result.get("amount") or 0),
                              "derivedPaid": result.get("derived_paid"),
                              "derivedDebt": result.get("derived_debt"),
                              "version": result.get("version")},
                   audit=_audit_trail(sid))


def _handle_payment_correction(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.database import save_direct_payment_correction

    sid = rd.text(payload.get("shipmentId"))
    payment_id = rd.text(payload.get("paymentId"))
    correction_request_id = rd.text(payload.get("correctionRequestId"))
    if not sid or not payment_id or not correction_request_id:
        return _result("payment_correction", sid, False,
                       "Thiếu shipmentId, paymentId hoặc correctionRequestId.")
    ok, result, message = save_direct_payment_correction(
        sid,
        payment_id,
        correction_request_id,
        rd.text(payload.get("reason")) or "Điều chỉnh khoản thu theo yêu cầu vận hành",
        {k: v for k, v in {
            "amount": rd.num(payload.get("amount")),
            "date": _normalize_date(payload.get("date")) or None,
            "note": rd.text(payload.get("note")) or None,
        }.items() if v is not None},
        actor=_actor(),
    )
    if not ok:
        return _result("payment_correction", sid, False, message or "Không điều chỉnh được.")
    fresh = read_shipment(sid) or {}
    return _result("payment_correction", sid, True, message, readback=_projection_for(fresh),
                   persisted=result, audit=_audit_trail(sid))


def _company_party() -> dict[str, str] | None:
    """The payer company party from the existing authority_companies master."""
    from core.database import load_authority_companies

    companies = load_authority_companies() or {}
    doc = next((d for d in companies.values() if isinstance(d, Mapping) and rd.text(d.get("id"))), None)
    if doc is None:
        return None
    return {
        "party_type": "company",
        "party_id": rd.text(doc.get("company_id") or doc.get("id")),
        "name": rd.text(doc.get("legal_name")) or rd.text(doc.get("id")),
    }


def _agent_party(agent_id: str) -> dict[str, str] | None:
    """Resolve ONE partner from the existing authority_agents master.

    Never creates a partner; an unknown id is a hard error so the payable can
    only ever be recorded against a real existing identity.
    """
    from core.database import load_authority_agents

    agents = load_authority_agents() or {}
    doc = agents.get(agent_id) or next(
        (d for d in agents.values() if isinstance(d, Mapping) and rd.text(d.get("agent_id")) == agent_id), None
    )
    if doc is None:
        return None
    return {
        "party_type": "agent",
        "party_id": rd.text(doc.get("agent_id") or doc.get("id")),
        "name": rd.text(doc.get("legal_name")) or rd.text(doc.get("id")),
    }


def _position_readback(sid: str) -> dict[str, Any]:
    from core.financial_ledger import shipment_partner_position

    return shipment_partner_position(sid)


def _load_entity_audit(entity_type: str, entity_id: str) -> list:
    from core.database import load_audit_logs

    return load_audit_logs(entity_type, entity_id, limit=5) or []


def _handle_partner_payable_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """ONE partner payable for ONE shipment = one canonical obligation.

    PAYABLE ≠ COST in the model: the obligation is an explicit, evidence-linked
    write that references the shipment's accrued cost; it is never derived
    silently. Idempotent by requestId via the canonical action registry.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error
    from core.financial_ledger import save_obligation
    from core.logic import calculate_from_shipment

    sid = rd.text(payload.get("shipmentId"))
    partner_id = rd.text(payload.get("partnerId"))
    request_id = rd.text(payload.get("requestId"))
    amount = rd.num(payload.get("amount"))
    if not sid or not partner_id or not request_id:
        return _result("partner_payable_record", sid, False,
                       "Thiếu shipmentId, partnerId hoặc requestId (idempotency key).")

    actor = _actor()
    if not can_operate_business("finance_write"):
        return _result("partner_payable_record", sid, False, "RBAC: không có quyền finance_write.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("partner_payable_record", sid, False, f"Không tìm thấy lô {sid}.")
    agent = _agent_party(partner_id)
    if agent is None:
        return _result("partner_payable_record", sid, False,
                       f"Không tìm thấy đối tác {partner_id} trong danh mục đối tác hiện có.")
    company = _company_party()
    if company is None:
        return _result("partner_payable_record", sid, False,
                       "Thiếu hồ sơ công ty (authority_companies) — không xác định bên trả tiền.")
    if amount is None or amount <= 0:
        return _result("partner_payable_record", sid, False,
                       "Nhập số tiền phải trả đối tác — số tiền trống là UNKNOWN, không tự thành 0.")

    currency = rd.text(payload.get("currency")).upper() or rd.text(
        shipment.get("currency") or _get_path(shipment, ("data", "3.4", "currency"))
    ).upper() or "VND"

    summary = calculate_from_shipment(shipment)
    ok, result, message = save_obligation(
        {
            "from_party": company,
            "to_party": agent,
            "amount": amount,
            "currency": currency,
            "purpose": "partner_cost_payable",
            "shipment_ids": [sid],
            "evidence_refs": [{
                "kind": "shipment_finance_actual",
                "shipment_id": sid,
                "section": "data.3.4",
                "accrued_cost": summary.get("cost"),
                "currency": summary.get("currency"),
            }],
            "note": rd.text(payload.get("note")) or None,
        },
        request_id,
        actor=actor,
    )
    if not ok:
        return _result("partner_payable_record", sid, False,
                       message or get_last_db_error() or "Không ghi nhận được phải trả đối tác.",
                       requestId=request_id)

    fresh = _position_readback(sid)
    return _result("partner_payable_record", sid, True, message, requestId=request_id,
                   obligationId=rd.text(result.get("id")),
                   persisted=result,
                   position=fresh,
                   audit=[
                       {"action": rd.text(row.get("action")), "actor": rd.text(row.get("actor")),
                        "createdAt": str(row.get("created_at"))}
                       for row in _load_entity_audit("financial_obligations", rd.text(result.get("id")))
                   ])


def _handle_partner_payment_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """ONE real payment to ONE partner = one canonical transaction + allocation.

    The transaction is the money event; the allocation binds it to the open
    payable obligation. Each write has its own deterministic request identity
    derived from the ONE payment intent, so replaying the SAME intent never
    double-writes, while a NEW intent (new requestId) stays distinct.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error
    from core.financial_ledger import allocate_transaction, save_transaction

    sid = rd.text(payload.get("shipmentId"))
    partner_id = rd.text(payload.get("partnerId"))
    request_id = rd.text(payload.get("requestId"))
    amount = rd.num(payload.get("amount"))
    if not sid or not partner_id or not request_id:
        return _result("partner_payment_record", sid, False,
                       "Thiếu shipmentId, partnerId hoặc requestId (idempotency key).")

    actor = _actor()
    if not can_operate_business("finance_write"):
        return _result("partner_payment_record", sid, False, "RBAC: không có quyền finance_write.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("partner_payment_record", sid, False, f"Không tìm thấy lô {sid}.")
    agent = _agent_party(partner_id)
    if agent is None:
        return _result("partner_payment_record", sid, False,
                       f"Không tìm thấy đối tác {partner_id} trong danh mục đối tác hiện có.")
    company = _company_party()
    if company is None:
        return _result("partner_payment_record", sid, False,
                       "Thiếu hồ sơ công ty (authority_companies) — không xác định bên trả tiền.")
    if amount is None or amount <= 0:
        return _result("partner_payment_record", sid, False,
                       "Nhập số tiền thanh toán — số tiền trống là UNKNOWN, không tự thành 0.")

    currency = rd.text(payload.get("currency")).upper() or rd.text(
        shipment.get("currency") or _get_path(shipment, ("data", "3.4", "currency"))
    ).upper() or "VND"

    # Bound the intent BEFORE any write: a payment beyond the open outstanding
    # is refused up front (overpay/advance is ledger-representable as unallocated
    # credit, but this slice records only payments that settle an open payable).
    position = _position_readback(sid)
    group = next((g for g in position.get("partners", [])
                  if rd.text((g.get("partner") or {}).get("party_id")) == partner_id), None)
    open_row = None
    if group and group.get("status") == "CONFIRMED":
        for row in group.get("obligations", []):
            if row.get("status") == "CONFIRMED" and float(row.get("outstanding") or 0) > 0 \
                    and rd.text(row.get("currency")) == currency:
                open_row = row
                break
    if open_row is None:
        return _result("partner_payment_record", sid, False,
                       "Chưa có khoản phải trả đối tác nào đang mở cho lô này — ghi nhận phải trả trước khi thanh toán.",
                       requestId=request_id)
    if amount > float(open_row.get("outstanding") or 0):
        return _result("partner_payment_record", sid, False,
                       f"Số tiền vượt còn phải trả ({open_row.get('outstanding'):g} {currency}) — không ghi nhận.",
                       requestId=request_id)
    obligation_id = rd.text(open_row.get("obligation_id"))

    ok, tx_result, message = save_transaction(
        {
            "source_party": company,
            "holder_party": agent,
            "beneficiary_party": agent,
            "transaction_kind": "payment",
            "amount": amount,
            "currency": currency,
            "classification_status": "CONFIRMED",
            "shipment_ids": [sid],
            "occurred_at": _normalize_date(payload.get("date"))
            or __import__("datetime").date.today().strftime("%Y-%m-%d"),
            "evidence_refs": [{"kind": "partner_payment_intent", "obligation_id": obligation_id,
                               "shipment_id": sid}],
            "note": rd.text(payload.get("note")) or None,
        },
        request_id,
        actor=actor,
    )
    if not ok:
        return _result("partner_payment_record", sid, False,
                       message or get_last_db_error() or "Không ghi nhận được thanh toán đối tác.",
                       requestId=request_id)
    transaction_id = rd.text(tx_result.get("id"))

    # Deterministic derived identity: the SAME intent always yields the SAME
    # allocation request id, so a replay is absorbed by the action registry.
    alloc_request_id = f"{request_id}:ALLOC"
    ok, alloc_result, alloc_message = allocate_transaction(
        transaction_id,
        obligation_id,
        amount,
        alloc_request_id,
        currency=currency,
        shipment_ids=[sid],
        evidence_refs=[{"kind": "partner_payment_settlement", "obligation_id": obligation_id,
                        "shipment_id": sid}],
        actor=actor,
    )
    if not ok:
        # The payment itself is already a canonical fact; report the real state
        # instead of hiding it. The remaining payable readback shows the truth.
        return _result("partner_payment_record", sid, False,
                       alloc_message or "Không phân bổ được thanh toán vào phải trả.",
                       requestId=request_id, transactionId=transaction_id,
                       persisted=tx_result, position=_position_readback(sid))

    fresh = _position_readback(sid)
    return _result("partner_payment_record", sid, True, message, requestId=request_id,
                   transactionId=transaction_id,
                   allocationId=rd.text(alloc_result.get("id")),
                   persisted={"transaction": tx_result, "allocation": alloc_result},
                   position=fresh,
                   audit=[
                       {"action": rd.text(row.get("action")), "actor": rd.text(row.get("actor")),
                        "createdAt": str(row.get("created_at"))}
                       for row in _load_entity_audit("financial_transactions", transaction_id)
                   ])


def _handle_shipment_create(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Create Shipment via the existing creation logic; duplicate codes rejected."""
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, save_shipment_atomic
    from core.database import get_db
    from core.logic import apply_financial_snapshot
    from core.validators import validate_shipment

    sid = rd.text(payload.get("shipmentId")).upper()
    customer_id = rd.text(payload.get("customerId"))
    request_id = rd.text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        # Echo the request identity so the component matches THIS backend
        # outcome to the exact click that sent it — it can never navigate or
        # report from transport alone.
        return _result("shipment_create", sid, ok, error, requestId=request_id, **extra)

    if not sid:
        return _res(False, "Thiếu mã lô.")
    if not can_operate_business("shipment_create"):
        return _res(False, "RBAC: không có quyền shipment_create.")

    db = get_db()
    if db is not None and db.shipments.find_one({"id": sid, "is_deleted": {"$ne": True}}):
        return _res(False, f"Mã lô {sid} đã tồn tại.")

    customers = load_customers() or {}
    customer_doc = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}
    customer_name = rd.text(payload.get("customer")) or rd.text(customer_doc.get("name"))
    if not customer_name:
        return _res(False, "Vui lòng chọn khách hàng.")

    created_on = _normalize_date(payload.get("createdAt")) or __import__("datetime").date.today().strftime("%Y-%m-%d")
    transport = payload.get("transport") if isinstance(payload.get("transport"), Mapping) else {}
    delivery = payload.get("delivery") if isinstance(payload.get("delivery"), Mapping) else {}
    selected_mode = rd.text(transport.get("mode"))
    if selected_mode and selected_mode not in {"Truck", "Sea", "Air", "Rail"}:
        return _res(False, "Mode đầu tiên không hợp lệ.")
    if not selected_mode and (rd.text(transport.get("pol")) or rd.text(transport.get("pod"))):
        return _res(False, "Chọn mode đầu tiên trước khi nhập nơi đi/đến.")

    # Keep creation lightweight while starting new shipments on the canonical
    # model whenever an optional first mode is selected.  Scalar POL/POD/ETD
    # are still written once as compatibility fields for existing readers; all
    # subsequent operational editing is authoritative in transport_legs.
    transport_section = {k: _coerce(k, transport.get(k)) for k in
                         ("booking_no", "carrier", "mbl", "hbl", "vessel", "etd",
                          "pol", "pod", "container_no", "qty_pkg")
                         if transport.get(k) not in (None, "")}
    if selected_mode:
        from core.shipment_operations import normalize_transport_legs
        from uuid import uuid4

        first_leg = {
            "id": rd.text(transport.get("first_leg_id")) or f"leg-{uuid4().hex}",
            "sequence": 1,
            "mode": selected_mode,
            "origin": rd.text(transport.get("pol")),
            "destination": rd.text(transport.get("pod")),
            "carrier": rd.text(transport.get("carrier")),
            "etd": transport.get("etd") or "",
            "eta": transport.get("eta") or "",
            "atd": "",
            "ata": "",
            "units": [],
        }
        for key in ("booking_no", "mbl", "hbl", "vessel", "voyage", "mawb", "hawb", "flight_no"):
            if key in transport:
                first_leg[key] = transport.get(key)
        try:
            transport_section["transport_legs"] = normalize_transport_legs([first_leg])
        except ValueError as exc:
            return _res(False, str(exc))

    doc: dict[str, Any] = {
        "id": sid,
        "shipment_id": sid,
        "customer": customer_name,
        "client": customer_name,
        "customer_id": customer_id,
        "status": "wait",
        "currency": rd.text(payload.get("currency")) or "VND",
        "data": {
            "0.0": {"st": "wait", "created_at": created_on,
                    "mode": selected_mode,
                    "incoterm": rd.text(transport.get("incoterm")) or "EXW"},
            "1.2": transport_section,
            "2.4": {},
            "2.6": {k: _coerce(k, v) for k, v in (("arrival_date", transport.get("etd")),) if v},
            "2.7": {k: _coerce(k, delivery.get(k)) for k in
                    ("addr", "phone_receiver", "delivery_date") if delivery.get(k) not in (None, "")},
            "3.4": {"details": [], "payments": [], "commission": {"list": [], "total": 0}},
            "entrustment": {"active": False},
        },
    }
    if rd.text(payload.get("contractId")):
        doc["contract_id"] = rd.text(payload.get("contractId")).upper()

    validation = validate_shipment(doc)
    if not validation.is_valid:
        return _res(False, validation.message)

    apply_financial_snapshot(doc)
    if not save_shipment_atomic(doc, actor=_actor()):
        return _res(False, get_last_db_error() or "Không tạo được lô hàng.")

    # FAST PATH for Create Shipment: the success invariant is
    #   matching backend outcome (event+requestId+ok) AND fresh vm contains id.
    # The full projection (_projection_for) that loads reference/timeline/finance/PXK
    # is redundant because build_view_model() will construct the authoritative
    # complete shipment on the forced rerun.  We therefore return a MINIMAL
    # authoritative readback that proves the fresh persisted document really
    # exists, without the expensive projection reads.
    fresh = read_shipment(sid) or {}
    if not fresh:
        return _res(False, "Không đọc được lô vừa tạo sau khi ghi.")

    minimal = {
        "id": rd.text(fresh.get("id")),
        "customer": rd.text(fresh.get("customer")),
        "version": int(fresh.get("version") or 0),
    }
    return _res(True, readback=minimal, persisted=dict(minimal), audit=_audit_trail(sid))


def _handle_pxk_generate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """PXK through the real docgen rules/service — never a prototype TXT."""
    from core.auth import can_generate_documents
    from core.docgen import generator as docgen
    from core.docgen import rules as docgen_rules
    from core.docgen.rules import PXK, READY
    from core.database import load_authority_agents, load_authority_companies, load_contracts

    sid = rd.text(payload.get("shipmentId"))
    if not sid:
        return _result("pxk_generate", sid, False, "Thiếu shipmentId.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("pxk_generate", sid, False, f"Không tìm thấy lô {sid}.")

    delivery = _get_path(shipment, ("data", "2.7")) or {}
    delivered = bool(delivery.get("is_delivered"))
    missing_delivery = docgen_rules.delivery_facts_missing(delivery)

    # The real delivery gate: an undelivered shipment is blocked by rule.
    if not delivered:
        return _result("pxk_generate", sid, False,
                       "PXK bị chặn: lô hàng chưa được xác nhận giao.",
                       gate="BLOCKED_NOT_DELIVERED", delivered=False)
    if missing_delivery:
        return _result("pxk_generate", sid, False,
                       "PXK bị chặn: " + " ".join(missing_delivery),
                       gate="BLOCKED_MISSING_DELIVERY_FACTS", delivered=True,
                       missing=missing_delivery)

    contract_id = rd.text(shipment.get("contract_id") or _get_path(shipment, ("data", "entrustment", "contract_no")))
    contracts = load_contracts() or {}
    contract = contracts.get(contract_id) if isinstance(contracts.get(contract_id), Mapping) else {}
    if not contract:
        # The canonical N:M linkage written from the contract page
        # ("Lô liên kết → Thêm") is the same fact read back from the shipment
        # side, so a lot linked to exactly ONE contract has an unambiguous
        # source. Several linked contracts stay refused: PXK must be driven by
        # an explicitly selected source, never by a guess.
        from core.database import load_contracts_for_shipment

        try:
            linked = load_contracts_for_shipment(sid) or {}
        except Exception:  # noqa: BLE001 - a linkage read failure must not blank the desk
            linked = {}
        if len(linked) == 1:
            contract_id, contract = next(iter(linked.items()))
        elif len(linked) > 1:
            ids = ", ".join(sorted(str(k).upper() for k in linked))
            return _result("pxk_generate", sid, False,
                           f"PXK cần đúng 1 chứng từ nguồn; lô đang liên kết {len(linked)} hợp đồng ({ids}).",
                           gate="BLOCKED_AMBIGUOUS_SOURCE", delivered=True,
                           missing=["Chọn chứng từ nguồn cho PXK"])
    if not contract:
        return _result("pxk_generate", sid, False,
                       "PXK cần chứng từ nguồn (HDMB hoặc PL) đã liên kết với lô.",
                       gate="BLOCKED_NO_SOURCE", delivered=True)

    agents = load_authority_agents() or {}
    companies = load_authority_companies() or {}
    agent = next(iter(agents.values()), {}) or {}
    company = next(iter(companies.values()), {}) or {}

    finance = _get_path(shipment, ("data", "3.4")) or {}
    goods_lines = [line for line in (finance.get("details") or []) if isinstance(line, Mapping)]
    source_line = goods_lines[0] if len(goods_lines) == 1 else None
    pxk_source = {
        "source_document_type": "HDMB" if "HDMB" in contract_id.upper() else "PL",
        "source_contract_id": contract_id,
        "source_line_count": len(goods_lines),
        "source_goods_line": source_line,
    }

    # PXK owns its own legal identity (``pxk_no`` / ``pxk_date``), exactly like
    # the authoritative docgen desk (views/docgen.py collects "Số PXK" +
    # "Ngày PXK" from the operator). core.docgen.rules refuses to invent them —
    # an absent legal number/date must stay MISSING_INFO — so the shell has to
    # hand them over instead of promising "tự sinh khi xuất".
    pxk_no = rd.text(payload.get("pxkNo")).strip()
    pxk_date = _normalize_date(payload.get("pxkDate"))
    pxk_identity = {
        "id": pxk_no.upper(),
        "pxk_no": pxk_no,
        "pxk_date": pxk_date,
        "currency": rd.text(shipment.get("currency")) or "VND",
    }

    # core.docgen speaks its own delivery view (DELIVERY_COMPLETED + the four
    # receiver facts), while the canonical shipment document stores the same
    # facts as ``is_delivered`` / ``delivered_at``. Translate, never invent:
    # every value below is the one delivery_confirm just persisted.
    delivery_view = {
        "delivery_completed": delivered,
        "delivery_date": rd.text(delivery.get("delivered_at") or delivery.get("delivery_date")),
        "delivery_location": rd.text(delivery.get("delivery_location") or delivery.get("addr")),
        "receiver_name": rd.text(delivery.get("receiver_name")),
        "receiver_title": rd.text(delivery.get("receiver_title")),
    }

    readiness = docgen_rules.evaluate_document_readiness(
        PXK, goods_lines=goods_lines, agent=agent, company=company,
        selected_contract=pxk_identity, delivery_completed=delivered,
        document_identity=pxk_identity, pxk_source=pxk_source, delivery=delivery_view,
    )
    gate_state = "READY" if readiness.state == READY else readiness.state
    if readiness.state != READY:
        missing = list(readiness.missing)
        return _result("pxk_generate", sid, False,
                       (readiness.reason or "PXK chưa sẵn sàng.")
                       + (f" Thiếu: {' '.join(missing)}" if missing else ""),
                       gate=gate_state, delivered=True, missing=missing)

    if not can_generate_documents():
        return _result("pxk_generate", sid, False, "RBAC: không có quyền sales_write để sinh chứng từ.",
                       gate=gate_state, delivered=True)

    # Real service call. Legal templates are Owner-controlled assets; when they
    # are not present the canonical service fails closed — it never falls back
    # to a prototype text file.
    from views import logi_c1

    template_xlsx = rd.text(payload.get("templatePathXlsx"))
    if not template_xlsx:
        # SAME resolution as the contract docgen path: the Owner's
        # DOCGEN_TEMPLATE_DIR when configured, the staging template in sandbox.
        template_xlsx = rd.text(logi_c1._resolve_template_paths()[0])
    try:
        generated = docgen.generate_document(
            PXK, shipment_id=sid, agent=agent, company=company,
            goods_lines=goods_lines, contract=pxk_identity, delivery=delivery_view,
            pxk_source=pxk_source,
            template_path_xlsx=template_xlsx or None,
        )
    except docgen.DocumentGenerationError as exc:
        readiness_err = getattr(exc, "args", [None])[0]
        reason = getattr(readiness_err, "reason", None) or str(exc)
        return _result("pxk_generate", sid, False, f"Dịch vụ docgen chặn: {reason}",
                       gate=gate_state, delivered=True, service="core.docgen.generator.generate_document",
                       failClosed=True)
    except PermissionError:
        return _result("pxk_generate", sid, False, "RBAC: không có quyền sinh chứng từ.",
                       gate=gate_state, delivered=True)

    raw = generated.get("bytes") or b""
    is_office = raw[:2] == b"PK"  # OOXML container

    # Persist the generated document through the canonical metadata writer and
    # keep the file on the SAME session download store the contract documents
    # already use, so "đã sinh PXK" is a durable, downloadable fact and not
    # only a toast that leaves nothing behind.
    from core.database import get_last_db_error, save_docgen_document

    metadata = dict(generated.get("metadata") or {})
    record_id = (rd.text(metadata.get("id"))
                 or f"{generated.get('document_id')}::R{generated.get('revision')}")
    metadata["id"] = record_id
    if not save_docgen_document(metadata):
        return _result("pxk_generate", sid, False,
                       get_last_db_error() or "Không lưu được metadata PXK.",
                       gate=gate_state, delivered=True,
                       service="core.docgen.generator.generate_document", failClosed=True)
    logi_c1.store_output(sid, record_id, {
        "file_name": generated.get("output_file_name"), "mime": logi_c1._MIME_XLSX,
        "bytes": raw, "document_type": PXK, "revision": generated.get("revision"),
    })

    return _result("pxk_generate", sid, True, "Đã sinh PXK bằng dịch vụ docgen thật.",
                   gate=gate_state, delivered=True,
                   service="core.docgen.generator.generate_document",
                   persisted={"documentId": rd.text(generated.get("document_id")),
                              "recordId": record_id,
                              "fileName": rd.text(generated.get("output_file_name")),
                              "status": rd.text(generated.get("status")),
                              "revision": generated.get("revision"),
                              "outputHash": rd.text(generated.get("output_hash")),
                              "pxkNo": pxk_no, "pxkDate": pxk_date,
                              "bytes": len(raw),
                              "isOfficeFile": is_office},
                   readback=_projection_for(read_shipment(sid) or {}),
                   audit=_audit_trail(sid))


_HANDLERS = {
    "shipment_field_save": _handle_field_save,
    "shipment_transport_save": _handle_shipment_transport_save,
    "delivery_confirm": _handle_delivery_confirm,
    "finance_actual_save": _handle_finance_actual_save,
    "payment_record": _handle_payment_record,
    "payment_correction": _handle_payment_correction,
    "shipment_create": _handle_shipment_create,
    "pxk_generate": _handle_pxk_generate,
    "partner_payable_record": _handle_partner_payable_record,
    "partner_payment_record": _handle_partner_payment_record,
}


# ---------------------------------------------------------------------------
# Dispatch entry points
# ---------------------------------------------------------------------------

def consume_phase_b_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded Phase B dispatcher (pure over an explicit session dict).

    Only the declared Phase B event names are handled; anything else is
    ignored. Events with a seq already consumed are ignored, so a replayed
    trigger value can never double-write.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(PHASE_B_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue
        handler = _HANDLERS.get(event_name)
        if handler is None:  # pragma: no cover - PHASE_B_EVENTS and _HANDLERS agree
            continue
        try:
            outcomes.append(handler(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            outcomes.append(_result(event_name, rd.text(data.get("shipmentId")), False,
                                    f"{type(exc).__name__}: {exc}"))
    if outcomes:
        session["writes"] = outcomes
    return outcomes


def consume_tariff_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded READ-ONLY tariff query dispatcher (LOGI_TARIFF_LOOKUP_01).

    Mirrors the phase dispatchers' replay protection (one-shot ``seq``), but
    performs NO business mutation: the handler only records the validated
    query for the next fresh read in ``build_view_model``. Anything outside
    ``TARIFF_EVENTS`` is ignored.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(TARIFF_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        query = str(data.get("query") or "").strip()[:120] if isinstance(data, dict) else ""
        if len(query) < 1:
            outcomes.append(_result(event_name, "", False, "Truy vấn trống."))
            continue
        st.session_state[TARIFF_QUERY_KEY] = query
        outcomes.append(_result(event_name, "", True, readback={"query": query}))
    return outcomes


def consume_translation_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded translation dispatcher (LOGI_TRANSLATION_WORKSPACE_01).

    Same replay protection as the other dispatchers (one-shot ``seq``), plus a
    same-intent guard: when the identical text + language pair already has an
    authoritative translation, the external DeepL call is NOT repeated. ONE
    user intent therefore costs at most ONE provider call, and no job
    framework, queue or worker is involved.

    Authorization uses the EXISTING role matrix (``translation`` permission);
    the provider is the EXISTING ``core.deepl_translation.DeepLClient``.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(TRANSLATION_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if not isinstance(data, dict):
            outcomes.append(_result(event_name, "", False, "Payload không hợp lệ."))
            continue

        text = str(data.get("text") or "")
        source_lang = str(data.get("sourceLang") or "AUTO").strip().upper()
        target_lang = str(data.get("targetLang") or "VI").strip().upper()
        fingerprint = _translation_fingerprint(text, source_lang, target_lang)

        previous = st.session_state.get(TRANSLATION_REQUEST_KEY)
        previous_result = st.session_state.get(TRANSLATION_RESULT_KEY)
        if (isinstance(previous, dict)
                and previous.get("fingerprint") == fingerprint
                and isinstance(previous_result, dict)
                and previous_result.get("status") == logi_translation.STATUS_TRANSLATED):
            outcomes.append(_result(
                event_name, "", True, "",
                readback={"fingerprint": fingerprint, "duplicate": True},
                notice=logi_translation.DUPLICATE_TRANSLATION_MESSAGE,
            ))
            continue

        from core.auth import can_operate_business

        if not can_operate_business("translation"):
            outcomes.append(_result(event_name, "", False,
                                    "RBAC: không có quyền translation."))
            continue

        # Recorded BEFORE the call so a failed attempt still shows WHICH
        # request failed (and the UI leaves its loading state honestly).
        st.session_state[TRANSLATION_REQUEST_KEY] = {
            "text": text,
            "sourceLang": source_lang,
            "targetLang": target_lang,
            "fingerprint": fingerprint,
        }
        translated = logi_translation.run_translation(
            text, source_lang=source_lang, target_lang=target_lang
        )
        st.session_state[TRANSLATION_RESULT_KEY] = translated
        ok = translated.get("status") == logi_translation.STATUS_TRANSLATED
        outcomes.append(_result(
            event_name, "", ok, str(translated.get("error") or ""),
            readback={"fingerprint": fingerprint,
                      "status": translated.get("status")},
        ))
    return outcomes


def consume_partner_context_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded READ-ONLY partner-selection dispatcher.

    Mirrors ``consume_tariff_triggers`` exactly: the same replay protection (one
    shot ``seq``), NO business mutation — the handler only records which
    existing entity the Owner selected, and ``build_view_model`` renders the
    authoritative projection for it on the next fresh read. The partner key is
    never trusted as data: it is a lookup input only, and an unknown key fails
    honest in the projection (``PARTNER_NOT_FOUND``) instead of creating one.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(PARTNER_CONTEXT_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload")
        entity_key = str(data.get("entityKey") or "").strip()[:120] if isinstance(data, dict) else ""
        if not entity_key:
            # An empty selection is a legitimate intent: clear the workspace back
            # to the picker instead of leaving a stale partner on screen.
            st.session_state.pop(PARTNER_CONTEXT_KEY, None)
            outcomes.append(_result(event_name, "", True, readback={"entityKey": ""}))
            continue
        st.session_state[PARTNER_CONTEXT_KEY] = entity_key
        outcomes.append(_result(event_name, "", True, readback={"entityKey": entity_key}))
    return outcomes


#: Filter fields the /tai-chinh/doi-soat desk may record, and their ceilings.
#: Every value is a lookup input only — never a figure, never canonical data.
_RECONCILIATION_FILTER_FIELDS = {
    "query": 120,
    "currency": 12,
    "state": 16,
    "side": 16,
}


def consume_reconciliation_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded READ-ONLY reconciliation-filter dispatcher.

    Mirrors ``consume_partner_context_triggers`` exactly: the same replay
    protection (one-shot ``seq``) and NO business mutation. The handler only
    records which slice of the existing canonical projection the Owner asked
    for; ``build_view_model`` re-derives every amount, match state and currency
    total from ``core.financial_ledger`` on the next fresh read. A filter value
    is never trusted as data, so a nonsense currency or state simply yields an
    honest empty view instead of a fabricated one.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(RECONCILIATION_EVENTS):
        payload = result.get(event_name) if hasattr(result, "get") else None
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        if seq <= session.get("seq", 0):
            continue
        session["seq"] = seq
        data = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        selection = {
            key: str(data.get(key) or "").strip()[:limit]
            for key, limit in _RECONCILIATION_FILTER_FIELDS.items()
        }
        if not any(selection.values()):
            # An empty filter is a legitimate intent: clear the desk back to the
            # full projection instead of leaving a stale filter on screen.
            st.session_state.pop(RECONCILIATION_FILTER_KEY, None)
            outcomes.append(_result(event_name, "", True, readback=dict(selection)))
            continue
        st.session_state[RECONCILIATION_FILTER_KEY] = selection
        outcomes.append(_result(event_name, "", True, readback=dict(selection)))
    return outcomes


def dispatch(result: Any) -> list[dict[str, Any]]:
    """Streamlit-facing entry: consume one script run's component triggers.

    Phase B typed writes are executed first against the real backend; the
    Phase A bounded local merge is kept afterwards so the Phase A acceptance
    contract is unchanged. The read-only tariff query is consumed last; when
    it was consumed, ONE rerun delivers the fresh read-side result (the v2
    trigger is one-shot, so the rerun cannot loop).

    LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01: every material write
    outcome (Phase B + C1) is stored in ``LAST_WRITES_KEY`` BEFORE the rerun
    and forces ONE rerun, so the next fresh view-model carries both the
    persisted data and the authoritative backend outcome to the component.
    The UI must never act on "event transported" — only on that readback.
    """
    logi_sandbox.ensure_backend()
    session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    outcomes = consume_phase_b_triggers(session, result)

    # Phase C1 path (business contracts slice) — shares the same seq counter so
    # a replayed trigger value can never double-write across phase sets.
    outcomes.extend(logi_c1.consume_c1_triggers(session, result))

    # Phase B + C1 material write outcomes: whatever the backend answered
    # (success, duplicate, RBAC, validation) must reach the component.
    write_outcomes = list(outcomes)

    # Phase A path (bounded local merge over the legacy event set).
    phase_a_session = {"seq": st.session_state.get(SEQ_KEY, 0), "shipments": _state().get("shipments", {})}
    consume_triggers(phase_a_session, result)
    st.session_state[SEQ_KEY] = max(session["seq"], phase_a_session["seq"])

    # LOGI_TARIFF_LOOKUP_01 — bounded read-only query path. When a fresh
    # lookup query was recorded, rerun once so build_view_model() embeds the
    # authoritative reader result (UNKNOWN states included) in the payload.
    tariff_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    tariff_outcomes = consume_tariff_triggers(tariff_session, result)
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    tariff_session["seq"])
    outcomes.extend(tariff_outcomes)

    # LOGI_TRANSLATION_WORKSPACE_01 — bounded external-provider path. The
    # translation runs inside consume_translation_triggers (ONE call per user
    # intent); this rerun only delivers its readback through the view-model.
    translation_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    translation_outcomes = consume_translation_triggers(translation_session, result)
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    translation_session["seq"])
    outcomes.extend(translation_outcomes)

    # LOGI_PARTNER_CONTEXT_WORKSPACE_01 — bounded read-only selection path. It
    # writes nothing; this rerun only delivers the projected context for the
    # partner that was just selected (UNKNOWN states included).
    partner_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    partner_outcomes = consume_partner_context_triggers(partner_session, result)
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    partner_session["seq"])
    outcomes.extend(partner_outcomes)

    # LOGI_RECONCILIATION_DESK_01 — bounded read-only filter path. It writes
    # nothing; this rerun only delivers the canonical reconciliation projection
    # for the filter that was just recorded (UNKNOWN states included).
    reconciliation_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    reconciliation_outcomes = consume_reconciliation_triggers(reconciliation_session, result)
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    reconciliation_session["seq"])
    outcomes.extend(reconciliation_outcomes)

    # Store the outcomes BEFORE any rerun so the fresh view-model built on the
    # rerun embeds them (``_last_writes_readback``) — the rerun restarts the
    # script and anything assigned afterwards would be lost.
    if outcomes:
        st.session_state[LAST_WRITES_KEY] = outcomes

    needs_rerun = (
        # A material write was just handled (success OR refusal): ONE rerun
        # delivers the fresh read-side view-model + the authoritative outcome.
        # The v2 trigger is one-shot and the seq guard already consumed it, so
        # the rerun cannot re-execute the write (no double-write, no loop).
        bool(write_outcomes)
        or any(outcome.get("event") == "tariff_lookup" and outcome.get("ok")
               for outcome in tariff_outcomes)
        or bool(translation_outcomes)
        or any(outcome.get("ok") for outcome in partner_outcomes)
        or any(outcome.get("ok") for outcome in reconciliation_outcomes)
    )
    if needs_rerun:
        st.rerun()

    return outcomes


def _state() -> dict:
    """The last view-model delivered to the component (Phase A session shape).

    Shipments are keyed by id, exactly as the Phase A acceptance contract
    expects, so ``consume_triggers`` and the Phase A tests keep working.
    """
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = {
            "version": "", "shipments": {}, "tasks": [], "contracts": [],
            "customers": [], "quotes": [], "notifications": [],
        }
    return st.session_state[STATE_KEY]


def _remember(model: dict) -> None:
    """Store the delivered payload in session state (Phase A contract)."""
    try:
        st.session_state[STATE_KEY] = {
            "version": model["version"],
            "shipments": {row["id"]: row for row in model["shipments"]},
            "tasks": model["tasks"],
            "contracts": model["contracts"],
            "customers": model["customers"],
            "quotes": model["quotes"],
            "notifications": model["notifications"],
        }
    except Exception:  # pragma: no cover - non-Streamlit context
        pass


# ---------------------------------------------------------------------------
# Phase A bounded dispatcher — kept verbatim (Phase A acceptance contract).
# ---------------------------------------------------------------------------

def consume_triggers(session: dict, result) -> None:
    """The Phase A bounded dispatcher (legacy ``shipment_update``/``navigate``).

    Retained unchanged so ``tests/test_phase_a_component.py`` still proves the
    Phase A contract. Phase B persistence does NOT flow through this path: the
    component emits the typed Phase B events above, which write through the
    canonical writers and return a fresh backend readback.
    """
    for event_name in ALLOWED_EVENTS:
        payload = result.get(event_name) if hasattr(result, "get") else None
        if payload is None:
            continue
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        last = session.get("seq", 0)
        if seq <= last:
            continue
        session["seq"] = seq
        data = payload.get("payload")
        if event_name == "shipment_update" and isinstance(data, dict):
            _apply_shipment_update(session.get("shipments", {}), data.get("shipment"))


def _apply_shipment_update(shipments: dict, shipment: dict | None) -> None:
    if not isinstance(shipment, dict):
        return
    sid = shipment.get("id")
    if not isinstance(sid, str) or sid not in shipments:
        return
    server = shipments[sid]
    for key in ("status", "statusTone", "priority", "nextAction", "nextActionDetail",
                "nextLabel", "nextRoute", "updated", "missingDocs", "docs", "pickup",
                "cargo", "exportInfo", "importInfo", "finance", "pxk", "timeline"):
        if key in shipment:
            server[key] = copy.deepcopy(shipment[key])
