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

import base64
import copy
import hashlib
import io
import json
import math
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Mapping
from uuid import uuid4

import streamlit as st

from views import ceo_report as logi_ceo_report
from views import handbook as logi_handbook
from views import logi_c1
from views import logi_real_data as rd
from views import logi_route
import time
import threading

from views import logi_sandbox
from views import partner_context as logi_partner_context
from views import reconciliation_desk as logi_reconciliation
from views import tariff_lookup as logi_tariff
from views import translation as logi_translation
from views import user_access as logi_user_access
from views import user_management as logi_user_management

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

def legacy_numeric_candidate(shipment_id: Any) -> int | None:
    """Return the equivalent legacy numeric BSON id if shipment_id is a canonical decimal integer.

    Returns None for ambiguous text such as leading zeros ('00123'), explicit
    signs ('+123', '-123'), floats ('123.0'), whitespace (' 123 '), non-digits,
    or out-of-range integers.
    """
    if not isinstance(shipment_id, str):
        return None
    if not (shipment_id.isascii() and shipment_id.isdigit()):
        return None
    try:
        val = int(shipment_id)
    except (ValueError, OverflowError):
        return None
    if str(val) != shipment_id:
        return None
    if not (0 <= val <= 0x7FFFFFFFFFFFFFFF):
        return None
    return val


SHIPMENT_IDENTITY_AMBIGUOUS = "AMBIGUOUS_SHIPMENT_IDENTITY"
SHIPMENT_IDENTITY_NOT_FOUND = "SHIPMENT_NOT_FOUND"


def _read_shipment_resolution(shipment_id: Any) -> tuple[dict[str, Any] | None, str]:
    """Resolve one shipment using the SAME text identity the UI projects.

    Exact stored identity remains the fast path. On a miss, one bounded
    identity-field probe covers both the earlier numeric-BSON compatibility
    case and other legacy representations while detecting collisions, compare
    them with ``rd.text(id or shipment_id)`` (the UI's projection rule), and
    re-read the single matching document by immutable Mongo ``_id``.

    The normalized probe is fail-closed: zero matches means not found and more
    than one match means ambiguous identity. It never rewrites stored IDs.
    """
    from core.database import get_db, repair_data

    db = get_db()
    if db is None:
        return None, SHIPMENT_IDENTITY_NOT_FOUND

    # 1. Exact stored identity always wins.
    doc = db.shipments.find_one(
        {"id": shipment_id, "is_deleted": {"$ne": True}},
        {"_id": 0},
    )
    if doc:
        key = rd.text(shipment_id)
        return repair_data({key: doc})[key], "EXACT"

    # 2. The browser always sends rd.text(...), so do not broaden malformed
    # caller input here. This keeps whitespace/sign/float-like request strings
    # fail-closed while allowing legacy STORED representations that the UI
    # already normalizes for display.
    if not isinstance(shipment_id, str) or not shipment_id or rd.text(shipment_id) != shipment_id:
        return None, SHIPMENT_IDENTITY_NOT_FOUND

    # One bounded projected-identity probe covers BOTH the earlier numeric-BSON
    # compatibility case and other legacy storage representations (for example
    # surrounding whitespace) while still detecting collisions before we pick
    # a document. Exact string identity already returned above.
    matches: list[Any] = []
    cursor = db.shipments.find(
        {"is_deleted": {"$ne": True}},
        {"_id": 1, "id": 1, "shipment_id": 1},
    )
    for identity in cursor:
        if rd.text(identity.get("id") or identity.get("shipment_id")) != shipment_id:
            continue
        mongo_id = identity.get("_id")
        if mongo_id is None:
            continue
        matches.append(mongo_id)
        if len(matches) > 1:
            return None, SHIPMENT_IDENTITY_AMBIGUOUS

    if len(matches) != 1:
        return None, SHIPMENT_IDENTITY_NOT_FOUND

    doc = db.shipments.find_one(
        {"_id": matches[0], "is_deleted": {"$ne": True}},
        {"_id": 0},
    )
    if not doc:
        return None, SHIPMENT_IDENTITY_NOT_FOUND

    key = shipment_id
    return repair_data({key: doc})[key], "PROJECTED_IDENTITY"


def read_shipment(shipment_id: str) -> dict[str, Any] | None:
    """Fresh read of ONE shipment straight from the database.

    Deliberately bypasses the Streamlit read cache so a post-write readback is
    the database's own answer, then runs the canonical ``repair_data``
    normalisation the rest of the app uses.

    Identity semantics:
      1. Exact stored identity wins first.
      2. On exact miss, a single document whose identity projects to the same
         UI text may resolve by immutable Mongo ``_id``; this includes the
         legacy numeric-BSON compatibility case.
      3. Ambiguous/malformed identity never guesses.
    """
    shipment, _gate = _read_shipment_resolution(shipment_id)
    return shipment


#: Upper bound on the reads one render issues at the same time (``1`` = the
#: original one-after-another behaviour, the operational fallback).
_READ_WORKERS = 8

#: "No explicit handle supplied" — ``None`` is a real value (the canonical
#: resolution found no database) and must not be re-resolved inside a worker.
_UNSET_DB: Any = object()

# LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — TTL cache for LIVE fx rates (5-15 min)
FX_TTL_SECONDS = 600  # 10 minutes
_FX_CACHE: dict[str, Any] = {"snapshot": None, "expires_at": 0.0}
_FX_CACHE_LOCK = threading.Lock()


def _clear_fx_cache_for_tests() -> None:
    with _FX_CACHE_LOCK:
        _FX_CACHE["snapshot"] = None
        _FX_CACHE["expires_at"] = 0.0


def _get_cached_fx_snapshot() -> dict[str, Any] | None:
    with _FX_CACHE_LOCK:
        snap = _FX_CACHE["snapshot"]
        exp = _FX_CACHE["expires_at"]
        if snap is not None and time.monotonic() < exp:
            return copy.deepcopy(snap)
    return None


def _store_fx_snapshot(snapshot: dict[str, Any]) -> None:
    with _FX_CACHE_LOCK:
        _FX_CACHE["snapshot"] = copy.deepcopy(snapshot)
        _FX_CACHE["expires_at"] = time.monotonic() + FX_TTL_SECONDS


def _read_concurrently(reads: Mapping[str, Callable[[], Any]]) -> dict[str, Any]:
    """Issue this render's INDEPENDENT canonical reads together, then join.

    LOGI_INTERACTION_LATENCY_FINALIZE_02 — measured root cause of the
    post-action slowness: the ONE ``build_view_model`` waited on its reads one
    after another, so its cost was ``round-trips × network RTT`` (network
    waiting, not CPU). The reads handed to this helper do not depend on each
    other, so they are started together on a short-lived stdlib thread pool
    and joined here before anything is projected.

    What this is NOT: no cache, no skipped read, no background work, no
    state. Every reader still runs on every render against the canonical
    collections and keeps its own error handling; an exception is re-raised
    from ``future.result()`` in the script thread exactly as the sequential
    call would have raised it; the pool is torn down before this returns.

    THE WORKERS ARE STREAMLIT-FREE (no unsupported private runtime behaviour is
    relied on).  Every Streamlit-owned resource is resolved on the SCRIPT thread
    before this call — the database handle via ``get_db()``, the session values
    the projections need — and only those explicit, read-only values are closed
    over by the jobs.  A worker therefore performs MongoDB reads and pure Python
    normalisation only:

    * it never calls ``add_script_run_ctx`` / ``get_script_run_ctx``;
    * it never touches ``st.session_state``, ``st.cache_data``,
      ``st.cache_resource``, ``st.secrets`` or any Streamlit command;
    * it never runs a write, an audit, an auth decision, a session mutation or
      a provider call.

    Error semantics stay deterministic: a worker runs inside
    ``core.database.captured_db_errors()``, so a ``_set_last_error`` triggered
    by a reader is COLLECTED on that worker thread instead of being published to
    the shared ``_LAST_DB_ERROR`` / ``st.session_state.last_db_error`` state.
    The envelope survives exceptions — a read that set an error and then raised
    still has its messages replayed in declaration order, and the first
    sequentially-visible exception is re-raised with later reads' errors NOT
    replayed, exactly as the sequential build would have exposed.
    Once every worker is joined, the script thread replays in declaration order.
    No worker can therefore race on shared error state.
    """
    if len(reads) <= 1 or _READ_WORKERS <= 1:
        return {key: read() for key, read in reads.items()}
    from core import database as core_database

    def _run(read: Callable[[], Any]) -> dict[str, Any]:
        # STREAMLIT-FREE worker body: errors captured even when the read raises.
        with core_database.captured_db_errors() as captured:
            try:
                value = read()
            except Exception as exc:  # noqa: BLE001 — must survive to replay its messages
                return {"ok": False, "value": None, "error": exc, "messages": tuple(captured)}
            else:
                return {"ok": True, "value": value, "error": None, "messages": tuple(captured)}

    # Joined in DECLARATION order after ALL workers finish — no worker is left
    # behind and the first sequentially-visible failure is what the caller sees.
    outcomes: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(_READ_WORKERS, len(reads)), thread_name_prefix="logi-read") as pool:
        futures = {key: pool.submit(_run, read) for key, read in reads.items()}
        for key, future in futures.items():
            outcomes[key] = future.result()
    values: dict[str, Any] = {}
    for key in reads.keys():  # declaration order, not completion order
        outcome = outcomes[key]
        for message in outcome["messages"]:  # script thread applies error semantics
            core_database.replay_db_error(message)
        if not outcome["ok"]:
            raise outcome["error"]  # type: ignore[misc]  # same exception the sequential build would have raised
        values[key] = outcome["value"]
    return values


def _resolve_db(db: Any = _UNSET_DB) -> Any:
    """Resolve the canonical database handle ONCE, on the script thread.

    Every service that owns Streamlit state (the cached connection, the
    session) is called here, on the thread that owns the script run, and the
    returned handle is only ever passed DOWN into read workers as an explicit
    argument — the workers themselves never resolve it and never call Streamlit.
    Callers that already hold a handle (a nested read helper) pass it through
    unchanged, so the resolution happens exactly once per render.
    """
    from core.database import get_db

    return get_db() if db is _UNSET_DB else db


# ---------------------------------------------------------------------------
# LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — bounded FX rates projection
# ---------------------------------------------------------------------------

def _intl_fx_rates_projection(*, db: Any = _UNSET_DB, force_refresh: bool = False) -> dict[str, Any]:
    """Build the LIVE fxRates slice for the comparator, fail-closed + TTL cached.

    One bounded live probe per source (BOC / Agribank / BIDV) is enough
    evidence (see SKILL acceptance).  The helper never invents a rate: a
    source that cannot be parsed live returns RATE_UNAVAILABLE and the UI
    keeps manual entry visibly marked MANUAL.  BIDV is marked UNAVAILABLE
    when its official JSON source cannot be proven (TASK §7), even if an
    HTML table could be scraped.
    The projection is read-only; no money is moved.

    TTL: 10 minutes (5-15 acceptable). First read fetches; repeats inside TTL
    reuse snapshot; expired fetches again; force_refresh bypasses cache.
    Thread-safe, no scheduler/daemon/Mongo, per-source failures remain RATE_UNAVAILABLE.
    """
    # Fast path: serve TTL-cached snapshot without network
    if not force_refresh:
        cached = _get_cached_fx_snapshot()
        if cached is not None:
            return cached
    from decimal import Decimal
    try:
        from core.fx_sources import BOC_URL, AGRIBANK_URL, BIDV_URL, fetch_live_fx
    except Exception:
        return {
            "boc": {"status": "RATE_UNAVAILABLE", "reason": "import_error"},
            "agribank": {"status": "RATE_UNAVAILABLE"},
            "bidv": {"status": "RATE_UNAVAILABLE", "bidv_rate_status": "UNAVAILABLE"},
        }
    # The three live fetches are independent — a failure of one must not hide
    # artefacts of another.  fetch_live_fx already isolates per-source errors,
    # but we keep a broad guard so a single import / network defect cannot
    # blank the whole desk.
    try:
        live = fetch_live_fx("all", timeout=4)
    except Exception as exc:  # noqa: BLE001
        live = {
            "boc": {"status": "RATE_UNAVAILABLE", "reason": f"fetch_error: {exc}", "source_url": BOC_URL},
            "agribank": {"status": "RATE_UNAVAILABLE", "reason": f"fetch_error: {exc}", "source_url": AGRIBANK_URL},
            "bidv": {"status": "RATE_UNAVAILABLE", "reason": f"fetch_error: {exc}", "source_url": BIDV_URL, "bidv_rate_status": "UNAVAILABLE"},
        }
    def _norm(entry: Any, default_url: str) -> dict[str, Any]:
        if not isinstance(entry, dict):
            return {"status": "RATE_UNAVAILABLE", "source_url": default_url}
        out = dict(entry)
        # Decimal → float for JSON, keep raw string as provenance
        for k in ("buying_rate", "cash_buying_rate", "selling_rate", "cash_selling_rate", "middle_rate", "usd_to_cny", "sell", "usd_sell_vnd", "buy_cash", "buy_transfer"):
            v = out.get(k)
            if isinstance(v, Decimal):
                out[k] = float(v)
                out[f"{k}_str"] = format(v, "f")
        # Ensure required keys for UI
        out.setdefault("source_url", default_url)
        if "status" not in out:
            out["status"] = "OK" if out.get("usd_to_cny") is not None or out.get("usd_sell_vnd") is not None or out.get("sell") is not None else "RATE_UNAVAILABLE"
        # BIDV truthful UNAVAILABLE marker
        if default_url == BIDV_URL:
            out.setdefault("bidv_rate_status", "UNAVAILABLE" if out.get("status") == "RATE_UNAVAILABLE" else "OK")
        return out
    try:
        boc = _norm(live.get("boc"), BOC_URL)
        agri = _norm(live.get("agribank"), AGRIBANK_URL)
        bidv = _norm(live.get("bidv"), BIDV_URL)
    except Exception:
        boc = {"status": "RATE_UNAVAILABLE", "source_url": BOC_URL}
        agri = {"status": "RATE_UNAVAILABLE", "source_url": AGRIBANK_URL}
        bidv = {"status": "RATE_UNAVAILABLE", "source_url": BIDV_URL, "bidv_rate_status": "UNAVAILABLE"}
    snapshot = {"boc": boc, "agribank": agri, "bidv": bidv}
    _store_fx_snapshot(snapshot)
    return copy.deepcopy(snapshot)


def load_shipments(*, db: Any = _UNSET_DB) -> dict[str, Any]:
    """Fresh shipment read for the component, bypassing the 30s read cache.

    ``core.database.load_data`` is cached for performance in the Streamlit
    runtime. The Logi-good work desk must show a write the moment it lands, so
    it calls the same module's uncached implementation directly — the same
    query, the same ``repair_data`` normalisation, no second source of truth.

    ``db`` is the optional explicit handle a STREAMLIT-FREE read worker was
    handed (see ``_read_concurrently``); standalone callers resolve it as
    before.
    """
    from core.database import _load_data_impl

    return _load_data_impl(db=_resolve_db(db)) or {}


def _load_references(*, db: Any = _UNSET_DB) -> dict[str, Any]:
    # The UNCACHED implementations are what the concurrent path calls: the
    # public ``load_customers`` / ``load_contracts`` wrappers are Streamlit
    # ``cache_data`` objects, and a STREAMLIT-FREE worker may not call them.
    # Same collections, same query, same result — merely resolved through the
    # handle the script thread passed down instead of a cached slice.
    from core.database import _load_contracts_impl, _load_customers_impl, load_quotes, load_tasks

    db = _resolve_db(db)
    # Four independent reference reads, issued together (same readers, same
    # results — see _read_concurrently).
    loaded = _read_concurrently({
        "customers": lambda: _load_customers_impl(db=db),
        "contracts": lambda: _load_contracts_impl(db=db),
        "quotes": lambda: load_quotes(db=db),
        "tasks": lambda: load_tasks(db=db),
    })
    return {
        "customers": loaded["customers"] or {},
        "contracts": loaded["contracts"] or {},
        "quotes": loaded["quotes"] or {},
        "tasks": loaded["tasks"] or [],
    }


def _knowledge_notes(*, db: Any = _UNSET_DB) -> list[dict[str, Any]]:
    """Team notebook, read through the EXISTING canonical reader (read-only).

    ``core.database.load_knowledge_base`` is the same reader the legacy
    ``views/knowledge_base.py`` screen uses — no second store and no new query
    layer are introduced here. An unconfigured deployment yields ``[]``, which
    the handbook renders as an honest empty state.
    """
    from core.database import load_knowledge_base

    try:
        return list(load_knowledge_base(db=_resolve_db(db)) or [])
    except Exception:  # noqa: BLE001 — a missing notebook must not blank the desk
        return []


def _users_reader(*, db: Any = _UNSET_DB) -> list[dict[str, Any]]:
    """User accounts, read through the EXISTING canonical reader (read-only).

    ``core.database.load_users`` is the same reader core.auth uses to
    authenticate.  Only ``views.user_access`` consumes the result and it keeps
    the canonical password-free public fields, so no credential material can
    reach the payload.  A deployment with no user store yields ``[]``, which
    the /nguoi-dung page renders as an honest empty state.
    """
    from core.database import load_users

    try:
        return list(load_users(db=_resolve_db(db)).values())
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
            "to": logi_route.shipment_path(matches[0]["id"]) if matches else "/lo-hang",
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
             "nextAction": r["nextAction"], "to": logi_route.shipment_path(r["id"])}
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
    out: list[dict[str, Any]] = []

    for row in rows:
        if row["priority"] == "BinhThuong" and not row["missingDocs"]:
            continue
        level = row["priority"]
        out.append({
            "id": f"OPS-{row['id']}",
            "level": level,
            "lot": row["id"],
            "customer": row["customer"],
            "job": row["nextAction"],
            # LOGI_UAT_REAL_USE_REPAIR_02 — a derived ops row has no task
            # document, so its responsible person is the CANONICAL owner
            # resolution of the shipment itself (core.shipment_dashboard._owner
            # over internal_sale_owner/sale_owner/owner/assigned_to/assignee,
            # already projected as `sale`, "Chưa phân công" when unassigned).
            # It used to show `support`, i.e. `updated_by` — merely the last
            # person who saved the document, which is not a responsibility.
            # Real rows from the tasks collection keep their own canonical
            # `tasks.assignee` below.
            "assignee": row["sale"] or rd.UNKNOWN_LABEL,
            "due": row["ops"].get("arrivalDateLabel") or rd.UNKNOWN_LABEL,
            "dueNote": row["nextActionDetail"] or (", ".join(f"thiếu {m}" for m in row["missingDocs"][:3])),
            "status": row["status"],
            "statusTone": row["statusTone"],
            # LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 — the composed row.nextRoute
            # (already status-tab aware). Recomputing from the status would
            # diverge from the ONE primary action the detail banner shows.
            "route": row["nextRoute"],
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
            "route": (logi_route.shipment_path(sid) + "?tab=lay-hang") if sid else "/lo-hang",
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


def _read_sources(shipments: Mapping[str, Any], references: Mapping[str, Any], *, db: Any = _UNSET_DB) -> dict[str, Any]:
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

    LOGI_INTERACTION_LATENCY_FINALIZE_02 adds, in the same ONE-read spirit:

    * ``docgenDocumentsRaw`` — the raw docgen map behind ``docgenDocuments``,
      shared with the C1 contract payload (which used to read it again);
    * ``agreements`` / ``companies`` / ``knowledgeNotes`` / ``users`` — the
      single-consumer reads of this render (C1 authority masters, handbook,
      user access), unchanged readers handed to their unchanged consumers;

    and issues all of these independent reads together instead of one after
    another (``_read_concurrently``) — the measured post-action cost was the
    number of sequential round-trips, not CPU.

    Nothing is stored on the session, the module or the process: the next
    Streamlit rerun calls this again and therefore sees the freshest data, so a
    write is visible on the very next render exactly as before.
    """
    from core.database import (
        load_agreements,
        load_authority_agents,
        load_authority_companies,
        load_cost_catalog,
        load_cost_rate_snapshots,
        load_docgen_documents,
        load_shipment_ids,
    )
    from core.financial_ledger import load_ledger_snapshot

    db = _resolve_db(db)
    shipment_ids = [str(sid) for sid in shipments.keys()]

    def _agents() -> dict[str, Any]:
        try:
            return load_authority_agents(db=db) or {}
        except Exception:  # noqa: BLE001 - a missing master must not blank the desk
            return {}

    def _docgen() -> dict[str, Any]:
        # LOGI_INTERACTION_LATENCY_FINALIZE_02 — the raw docgen map is read ONCE
        # and shared by the per-shipment PXK grouping below and the C1 contract
        # payload (which used to issue its own second read of the same collection).
        try:
            return load_docgen_documents(db=db) or {}
        except Exception:  # noqa: BLE001 - a docgen read failure must not blank the desk
            return {}

    # These shared reads are independent of one another (the timelines read
    # only needs the shipment ids already in hand), so they are issued
    # together and joined — same readers, same rows (see _read_concurrently).
    loaded = _read_concurrently({
        # Every job below is a pure read over the explicit handle the script
        # thread resolved; none of them touches Streamlit (see _read_concurrently).
        "ledger": lambda: load_ledger_snapshot(db),
        "agents": _agents,
        "timelines": lambda: rd.timelines_projection(shipment_ids, db=db),
        "docgenDocumentsRaw": _docgen,
        "shipmentIds": lambda: load_shipment_ids(db=db),
        # LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — attachment METADATA for
        # the whole render, read once and grouped (the same repair as the docgen
        # read above). No bytes: the files themselves live in the selected storage backend.
        "attachments": lambda: rd.attachments_by_shipment(db=db),
        # Single-consumer reads of the same render (C1 authority masters, the
        # handbook notebook, the user-access list): unchanged readers, unchanged
        # consumers — joined here so the render no longer waits on them one by one.
        "agreements": lambda: load_agreements(db=db) or {},
        "companies": lambda: load_authority_companies(db=db) or {},
        "knowledgeNotes": lambda: _knowledge_notes(db=db),
        "users": lambda: _users_reader(db=db),
        "costCatalog": lambda: load_cost_catalog(db=db) or {},
        "costRates": lambda: load_cost_rate_snapshots(db=db, limit=1000),
        "intlFxRates": lambda: _intl_fx_rates_projection(db=db),
    })
    return {
        "ledger": loaded["ledger"],
        "agents": loaded["agents"],
        "timelines": loaded["timelines"],
        "docgenDocumentsRaw": loaded["docgenDocumentsRaw"],
        "docgenDocuments": rd.docgen_documents_by_shipment(loaded["docgenDocumentsRaw"]),
        "linkedContracts": rd.linked_contracts_index(references.get("contracts")),
        "shipmentIds": loaded["shipmentIds"],
        "attachments": loaded["attachments"],
        "attachmentDownload": _attachment_download_state(),
        "agreements": loaded["agreements"],
        "companies": loaded["companies"],
        "knowledgeNotes": loaded["knowledgeNotes"],
        "users": loaded["users"],
        "costCatalog": loaded["costCatalog"],
        "costRates": loaded["costRates"],
        "intlFxRates": loaded["intlFxRates"],
    }


def build_view_model() -> dict:
    """Assemble the JSON payload for the component `data` channel."""
    from core.auth import current_user
    from core.config import DISPLAY_COMPANY_NAME
    from core.cost_intelligence import json_safe as _cost_json_safe
    from core.shipment_dashboard import build_dashboard_summary

    transport = logi_sandbox.ensure_backend()
    # LOGI_INTERACTION_LATENCY_FINALIZE_02 — every Streamlit-owned resource this
    # render needs is resolved HERE, on the script thread (the database handle
    # below; the session values inside _attachment_download_state), and only the
    # resulting read-only handle travels into the read workers.
    db = _resolve_db()
    # The shipment read and the reference reads are independent, so they are
    # issued together (see _read_concurrently); the shared sources follow once
    # the shipment ids are in hand.
    loaded = _read_concurrently({
        "shipments": lambda: load_shipments(db=db),
        "references": lambda: _load_references(db=db),
    })
    shipments, references = loaded["shipments"], loaded["references"]
    views = _dashboard_views(shipments)
    sources = _read_sources(shipments, references, db=db)

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
            attachments=sources["attachments"],
            attachment_download=sources["attachmentDownload"],
        )
        for sid, ship in shipments.items()
    ]
    order = {"Khan": 0, "CanXuLy": 1, "BinhThuong": 2}
    rows.sort(key=lambda row: (order.get(row["priority"], 9), row["id"]))

    summary = build_dashboard_summary(views.values())
    user = current_user() or {}
    # The contract→shipment links read the SAME shipment map this render already
    # loaded, so C1 adds no second full shipments read.
    # LOGI_INTERACTION_LATENCY_FINALIZE_02: the same rule now covers the other
    # sources this render already holds (customers / quotes / contracts /
    # agents / raw docgen) — C1 no longer re-reads them, nor one contract per
    # contract for its shipment links. Same reader results, zero caching.
    c1 = logi_c1.assemble_c1_payload(
        shipments=shipments,
        customers=references["customers"],
        quotes=references["quotes"],
        contracts=references["contracts"],
        agents=sources["agents"],
        agreements=sources["agreements"],
        companies=sources["companies"],
        docgen_documents=sources["docgenDocumentsRaw"],
    )

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
            # DISPLAY brand only (core.config.DISPLAY_COMPANY_NAME) — ordinary
            # surfaces identify the business with it; legal party facts keep
            # deriving from the authority_companies master.
            "displayName": DISPLAY_COMPANY_NAME,
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
            agents=sources["agents"],
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
            notes=sources["knowledgeNotes"],
        ),
        # LOGI_USER_ACCESS_WORKSPACE_01 — the /nguoi-dung workspace. A bounded
        # READ-ONLY slice over the auth/user/RBAC capability that already
        # exists (load_users read through core.users' canonical public view,
        # the single ROLE_PERMISSIONS matrix, the real AUTH_REQUIRED mode and
        # the current session identity). No credential material, no invented
        # role/permission, no write path: user mutations stay with the
        # canonical core.database writers and none is exposed by this page.
        "userAccess": logi_user_access.user_access_projection(
            users=sources["users"],
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
        # LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — the ONE canonical service catalog
        # (``core.config.GETFLY_SERVICES_LIST``) projected read-only so the
        # Finance Actual editor can offer the real service picker instead of a
        # free-text box. No second catalog, no copy in the frontend, no write
        # path: picking an entry only pre-fills ``code`` / ``name`` / ``unit`` on
        # the service line that ``finance_actual_save`` books in data.3.4.
        "financeServiceCatalog": rd.finance_service_catalog(sources["costCatalog"]),
        # LOGI_COST_INTELLIGENCE_01 — one bounded read model for the rate inbox,
        # dynamic master data, and supplier-rate history. No provider/network call.
        # json_safe: saved master-data/rate documents carry Mongo audit stamps
        # as datetime objects; a raw datetime silently breaks Streamlit arg
        # delivery for every NEW session (real-browser UAT verified defect).
        "costIntelligence": {
            "catalog": [
                _cost_json_safe(entry)
                for entry in sources["costCatalog"].values()
            ],
            "rates": [
                _cost_json_safe(snapshot)
                for snapshot in sources["costRates"]
            ],
        },
        # LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — live FX rates slice (BOC /
        # Agribank / BIDV) with provenance.  Fail-closed: RATE_UNAVAILABLE
        # keeps manual entry marked MANUAL; BIDV stays UNAVAILABLE when its
        # official JSON source cannot be proven, even if an HTML scrape exists.
        "intlFxRates": sources["intlFxRates"],
        # LOGI_GETFLY_DSDH_IMPORT_PARITY_01 — the only XLSX preview exposed to
        # React. The normalized rows remain in ephemeral session state; this is
        # a projection only and contains no uploaded bytes.
        "getfly": _getfly_preview_projection(),
        # LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the bounded attachment
        # policy delivered to the shipment document form. Read-only facts only:
        # the accepted extensions the server really enforces, the server's own
        # byte ceiling, the real categories, and whether THIS session may upload
        # at all (server RBAC — the form hides itself when the backend says no,
        # but the dispatcher refuses independently either way).
        "attachmentPolicy": _attachment_policy(),
        # LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — the ONE ephemeral
        # read-only review the operator last ran on a shipment's existing
        # attachments. It is projection only: no bytes, no base64, no full
        # extracted text, no storage/GridFS/Drive id, no raw SHA-256, and no
        # persistence — a new review replaces it and it carries its own
        # shipmentId so it can never be shown against another lot.
        "shipmentDocumentReview": _shipment_document_review_projection(),
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
    # LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the customer half of a lot's
    # name, written by the EXISTING core.database.update_shipment_customer.
    "shipment_customer_save",
    # Repeatable lists cannot be represented safely by the scalar field
    # whitelist.  This one shipment-local event writes exactly the canonical
    # operational collections through the existing atomic writer.
    "shipment_transport_save",
    # LOGI_SHIPMENT_EXECUTION_PROFILE_01 — ONE bounded write for the shipment
    # execution profile (Incoterms code/version/named place, Trường Thành
    # service scope, load model, actual cargo insurance). It writes the
    # EXISTING `data.0.0.mode` / `data.0.0.incoterm` paths plus ONE new block,
    # through the existing atomic writer, with RBAC + audit + fresh readback.
    "shipment_profile_save",
    "delivery_confirm",
    "finance_actual_save",
    "payment_record",
    "payment_correction",
    "shipment_create",
    "pxk_generate",
    "gnt_generate",
    # C2B — single-partner payable slice. The canonical writers are
    # core.financial_ledger.save_obligation / save_transaction /
    # allocate_transaction; these events are only the bounded shell boundary
    # (RBAC → writer → audit → fresh readback), mirroring payment_record.
    "partner_payable_record",
    "partner_payment_record",
    # LOGI_GETFLY_DSDH_IMPORT_PARITY_01 — preview transports bounded XLSX
    # bytes; commit carries only the server-issued previewId and explicit VAT
    # choices. Both handlers remain in this ONE dispatcher.
    "getfly_preview",
    "getfly_import",
    # LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the bounded attachment pair
    # for the shipment "Chứng từ" tab. ``shipment_attachment_upload`` carries the
    # ONE chosen file (bounded base64, same transport precedent as the GetFly
    # preview above) and the server owns permission, size/MIME validation,
    # decode, SHA-256, compression, the Drive upload and the metadata write;
    # ``attachment_download`` re-reads ONE stored file from Drive so the bytes
    # can be delivered server-side. There is deliberately NO delete event.
    "shipment_attachment_upload",
    "attachment_download",
}

#: Session key holding the ONE attachment whose bytes were just read back from
#: The selected storage backend for server-authoritative delivery to the browser.
ATTACHMENT_DOWNLOAD_KEY = "logi_attachment_download"

# LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — ONE bounded READ-ONLY event for
# the shipment "Chứng từ / Tệp đính kèm" review surface. It is deliberately NOT
# in PHASE_B_EVENTS: it writes no shipment field, no attachment row and no audit
# entry. The handler only reads bytes the operator selected (through the
# EXISTING core.shipment_attachments.fetch_attachment_bytes), runs the Run 2
# reader and the Run 1 cross-check, and keeps ONE ephemeral bounded result in
# session state for the next fresh view-model.
DOCUMENT_REVIEW_EVENTS = {"shipment_document_review"}

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

# LOGI_USER_MANAGEMENT_01 — the four Admin-only account-management events for
# /nguoi-dung (see views.user_management for the bounded dispatcher). Every
# handler re-checks the Admin RBAC boundary itself; this set only decides
# which typed events the shell forwards to Python at all.
USER_MANAGEMENT_EVENTS = logi_user_management.USER_MANAGEMENT_EVENTS

ALL_EVENTS = (ALLOWED_EVENTS | PHASE_B_EVENTS | logi_c1.C1_EVENTS
              | TARIFF_EVENTS | TRANSLATION_EVENTS | PARTNER_CONTEXT_EVENTS
              | RECONCILIATION_EVENTS | USER_MANAGEMENT_EVENTS
              | DOCUMENT_REVIEW_EVENTS)

#: LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — the ONE ephemeral session slot
#: holding the last read-only shipment document review. It is presentation/read
#: state only: nothing is persisted to shipments, shipment_attachments, audit,
#: GridFS, Drive or any review collection, and a new review REPLACES the
#: previous one. The stored value carries its own ``shipmentId`` so a review
#: belonging to another lot can never project into the current one.
SHIPMENT_DOCUMENT_REVIEW_KEY = "logi_shipment_document_review"

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
    # LOGI_GNT_DOC_EXPORT_REALITY_CHECK_01 — Explicit customs/GNT taxpayer fields:
    #   gnt_taxpayer_name       authoritative importer legal name
    #   gnt_taxpayer_tax_code   authoritative importer tax code (MST)
    #   gnt_taxpayer_address    authoritative importer legal address
    "gnt_taxpayer_name": ("data", "2.4", "gnt", "nguoi_nop"),
    "gnt_taxpayer_tax_code": ("data", "2.4", "gnt", "mst"),
    "gnt_taxpayer_address": ("data", "2.4", "gnt", "dia_chi"),
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
    # LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the shipment's own header date.
    # `data.0.0.created_at` is already the canonical field the legacy desk
    # edits (views/shipment.py "Ngày tạo"), that GetFly import writes
    # (views/dashboard.py) and that every reader already projects back as
    # `createdAt`; only the component whitelist could not reach it. A blank
    # stays blank, so "no date yet" never becomes "today" or "0".
    "created_at": ("data", "0.0", "created_at"),
}

_BOOL_FIELDS = {"customs_status"}
# LOGI_GNT_CANONICAL_FIELDS_01 — the two ACTUAL import-tax amounts coerce
# through the same numeric path `free_time` already uses, so a blank stays ""
# (UNKNOWN) and is never turned into 0. The declaration date joins the
# existing date path, which stores the canonical ISO form.
_NUM_FIELDS = {"free_time", "import_duty_amount", "import_vat_amount"}
_DATE_FIELDS = {"etd", "arrival_date", "delivery_date", "tk_date", "created_at"}


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


# ---------------------------------------------------------------------------
# GetFly DSDH import — one bounded XLSX preview/commit path
# ---------------------------------------------------------------------------

GETFLY_PREVIEW_KEY = "logi_getfly_preview"
GETFLY_MAX_BYTES = 10 * 1024 * 1024
GETFLY_MODE_SHIPMENT_ONLY = "SHIPMENT_ONLY"
GETFLY_MODE_SHIPMENT_AND_FINANCE = "SHIPMENT_AND_FINANCE"


def _getfly_clean(value: Any) -> str:
    """Return a source text fact, keeping missing text blank/UNKNOWN."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    raw = str(value).strip()
    if raw.lower() in {"nan", "none", "null", "<na>", "nat", "-"}:
        return ""
    return raw


def _getfly_date(value: Any) -> str:
    """Normalise a GetFly date to canonical ISO or return blank when invalid."""
    from core.utils import parse_date_optional

    raw = _getfly_clean(value)
    parsed = parse_date_optional(raw)
    return parsed.strftime("%Y-%m-%d") if parsed else ""


def _getfly_customer_key(value: Any) -> str:
    """Exact normalized name key; deliberately no fuzzy similarity."""
    raw = unicodedata.normalize("NFKC", _getfly_clean(value))
    return " ".join(raw.split()).casefold()


def _getfly_customer_match(name: str, code: str, customers: Mapping[str, Any]) -> tuple[str, str]:
    """Resolve a real customer id by exact code first, then exact name only."""
    wanted_code = _getfly_clean(code)
    if wanted_code:
        for customer_id, customer in customers.items():
            if not isinstance(customer, Mapping):
                continue
            stored_id = _getfly_clean(customer.get("id") or customer_id)
            if stored_id == wanted_code:
                return stored_id, "MATCHED_BY_CODE"
        # A supplied but unknown code is an UNKNOWN customer. Do not let a
        # familiar-looking name override the source's stronger identity fact.
        return "", "UNKNOWN"
    wanted_name = _getfly_customer_key(name)
    if wanted_name:
        for customer_id, customer in customers.items():
            if not isinstance(customer, Mapping):
                continue
            if _getfly_customer_key(customer.get("name")) == wanted_name:
                return _getfly_clean(customer.get("id") or customer_id), "MATCHED_BY_NAME"
    return "", "UNKNOWN"


def _getfly_sum_known(lines: list[Mapping[str, Any]], key: str) -> float | None:
    """Sum a source KPI only when every source row states that fact."""
    values = [line.get(key) for line in lines]
    if not values or any(value is None for value in values):
        return None
    return float(sum(float(value) for value in values))


def _getfly_build_preview(df: Any, *, filename: str, fingerprint: str,
                          request_id: str) -> dict[str, Any]:
    """Build normalized server state from the already parsed DataFrame."""
    import pandas as pd

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("File DSDH không có dòng dữ liệu.")
    if "order_id" not in df.columns:
        raise ValueError("File DSDH thiếu cột Mã ĐH / Mã đơn hàng.")

    grouped: dict[str, dict[str, Any]] = {}
    normalized_rows: list[dict[str, Any]] = []
    for row_number, (_, row) in enumerate(df.iterrows(), start=2):
        order_id = _getfly_clean(row.get("order_id"))
        # Blank rows before the first order are not a valid order and are not
        # allowed to become an invented id. Merged order cells are already
        # forward-filled by core.getfly_reader.
        if not order_id:
            continue
        order = grouped.setdefault(order_id, {
            "order_id": order_id,
            "customer_name": "",
            "customer_code": "",
            "order_date": "",
            "source_status": "",
            "lines": [],
        })
        for field in ("customer_name", "customer_code", "order_date", "source_status"):
            raw_key = {
                "customer_name": "customer_name",
                "customer_code": "customer_code",
                "order_date": "order_date",
                "source_status": "status",
            }[field]
            value = _getfly_clean(row.get(raw_key))
            if value and not order[field]:
                order[field] = value
        line = {
            "line_id": f"{order_id}::L{len(order['lines']) + 1}",
            "source_row": row_number,
            "product_code": _getfly_clean(row.get("product_code")),
            "product_name": _getfly_clean(row.get("product_name")),
            "product_note": _getfly_clean(row.get("product_note")),
            "qty": row.get("qty") if row.get("qty") is not None else None,
            "cost": row.get("cost") if row.get("cost") is not None else None,
            "price": row.get("price") if row.get("price") is not None else None,
            "revenue": row.get("revenue") if row.get("revenue") is not None else None,
            "profit": row.get("profit") if row.get("profit") is not None else None,
        }
        # Pandas/numpy scalar values must become ordinary JSON-safe numbers;
        # object columns can turn a ``None`` back into ``NaN`` after map(), so
        # check missingness again at the server preview boundary.
        for key in ("qty", "cost", "price", "revenue", "profit"):
            if line[key] is not None:
                try:
                    line[key] = None if bool(pd.isna(line[key])) else float(line[key])
                    if line[key] is not None and not math.isfinite(line[key]):
                        line[key] = None
                except (TypeError, ValueError):
                    line[key] = None
        order["lines"].append(line)
        normalized_rows.append({"order_id": order_id, **line})

    if not grouped:
        raise ValueError("File DSDH không có Mã ĐH hợp lệ.")

    from core.database import load_customers

    customers = load_customers() or {}
    existing_ids = set(load_shipments().keys())
    orders: list[dict[str, Any]] = []
    for order in grouped.values():
        customer_id, customer_match = _getfly_customer_match(
            order["customer_name"], order["customer_code"], customers
        )
        order_date = _getfly_date(order["order_date"])
        # Preserve an invalid source date for honest preview; commit validation
        # will refuse it rather than choosing today.
        display_date = order_date or order["order_date"]
        lines = [dict(line) for line in order["lines"]]
        orders.append({
            "orderId": order["order_id"],
            "customerName": order["customer_name"],
            "customerCode": order["customer_code"],
            "customerId": customer_id,
            "customerMatch": customer_match,
            "orderDate": display_date,
            "orderDateValid": bool(order_date),
            "sourceStatus": order["source_status"],
            "existing": order["order_id"] in existing_ids,
            "serviceLines": lines,
            "revenue": _getfly_sum_known(lines, "revenue"),
            "profit": _getfly_sum_known(lines, "profit"),
        })

    all_lines = [line for order in orders for line in order["serviceLines"]]
    return {
        "status": "READY",
        "previewId": f"GF-PREVIEW-{uuid4().hex.upper()[:16]}",
        "requestId": request_id,
        "filename": filename,
        "fingerprint": fingerprint,
        "normalizedRows": normalized_rows,
        "orders": orders,
        "summary": {
            "orders": len(orders),
            "revenue": _getfly_sum_known(all_lines, "revenue"),
            "profit": _getfly_sum_known(all_lines, "profit"),
        },
    }


def _getfly_preview_projection() -> dict[str, Any]:
    """Project ephemeral server preview state; never expose source bytes."""
    state = st.session_state.get(GETFLY_PREVIEW_KEY)
    if not isinstance(state, Mapping):
        return {"status": "EMPTY", "previewId": "", "filename": "", "orders": [],
                "normalizedRows": [],
                "summary": {"orders": 0, "revenue": None, "profit": None}, "error": ""}

    orders: list[dict[str, Any]] = []
    for source_order in state.get("orders") or []:
        if not isinstance(source_order, Mapping):
            continue
        lines: list[dict[str, Any]] = []
        for source_line in source_order.get("serviceLines") or []:
            if not isinstance(source_line, Mapping):
                continue
            lines.append({
                "lineId": source_line.get("line_id", ""),
                "code": source_line.get("product_code", ""),
                "name": source_line.get("product_name", ""),
                "description": source_line.get("product_note", ""),
                "qty": source_line.get("qty"),
                "cost": source_line.get("cost"),
                "price": source_line.get("price"),
                "revenue": source_line.get("revenue"),
                "profit": source_line.get("profit"),
            })
        orders.append({
            "orderId": source_order.get("orderId", ""),
            "customer": source_order.get("customerName", ""),
            "customerName": source_order.get("customerName", ""),
            "customerCode": source_order.get("customerCode", ""),
            "customerId": source_order.get("customerId", ""),
            "customerMatch": source_order.get("customerMatch", "UNKNOWN"),
            "orderDate": source_order.get("orderDate", ""),
            "sourceStatus": source_order.get("sourceStatus", ""),
            "existing": bool(source_order.get("existing")),
            "serviceLines": lines,
            "revenue": source_order.get("revenue"),
            "profit": source_order.get("profit"),
        })
    return {
        "status": state.get("status", "READY"),
        "previewId": state.get("previewId", ""),
        "requestId": state.get("requestId", ""),
        "filename": state.get("filename", ""),
        "fingerprint": state.get("fingerprint", ""),
        # Keep the parser's normalized row projection available for audit/UI
        # evidence while never returning the uploaded XLSX bytes.
        "normalizedRows": copy.deepcopy(state.get("normalizedRows") or []),
        "orders": orders,
        "summary": copy.deepcopy(state.get("summary") or {"orders": 0, "revenue": None, "profit": None}),
        "error": state.get("error", ""),
    }


def _decode_getfly_payload(payload: Mapping[str, Any]) -> tuple[bytes, str]:
    filename = _getfly_clean(payload.get("filename"))
    if not filename.lower().endswith(".xlsx"):
        raise ValueError("Chỉ nhận file DSDH.xlsx / .xlsx.")
    encoded = _getfly_clean(payload.get("contentBase64"))
    if "," in encoded and encoded.lower().startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    if not encoded:
        raise ValueError("File DSDH không có dữ liệu.")
    # Bound the encoded transport before decoding as well as the decoded XLSX;
    # otherwise an untrusted event could allocate an arbitrarily large string
    # before the byte limit is checked.
    max_encoded = ((GETFLY_MAX_BYTES + 2) // 3) * 4 + 4
    if len(encoded) > max_encoded:
        raise ValueError(f"File DSDH vượt giới hạn {GETFLY_MAX_BYTES // (1024 * 1024)} MB.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("Không giải mã được bytes XLSX từ file đã chọn.") from exc
    if not raw:
        raise ValueError("File DSDH rỗng.")
    if len(raw) > GETFLY_MAX_BYTES:
        raise ValueError(f"File DSDH vượt giới hạn {GETFLY_MAX_BYTES // (1024 * 1024)} MB.")
    declared_size = payload.get("size")
    if declared_size not in (None, ""):
        try:
            if int(declared_size) != len(raw):
                raise ValueError("Kích thước file không khớp bytes nhận được.")
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ValueError) and str(exc) == "Kích thước file không khớp bytes nhận được.":
                raise
            raise ValueError("Kích thước file không hợp lệ.") from exc
    return raw, filename


def _handle_getfly_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Parse real XLSX bytes into a session-only authoritative preview."""
    from core.auth import can_operate_business

    request_id = _getfly_clean(payload.get("requestId"))
    if not can_operate_business("dashboard"):
        return _result("getfly_preview", "", False,
                       "RBAC: cần đăng nhập nội bộ để xem trước GetFly.",
                       requestId=request_id)
    try:
        raw, filename = _decode_getfly_payload(payload)
        fingerprint = hashlib.sha256(raw).hexdigest()
        from core.getfly_reader import process_getfly_excel

        df, error = process_getfly_excel(io.BytesIO(raw))
        if error:
            raise ValueError(str(error))
        preview = _getfly_build_preview(
            df, filename=filename, fingerprint=fingerprint, request_id=request_id
        )
        st.session_state[GETFLY_PREVIEW_KEY] = preview
        return _result("getfly_preview", "", True, "",
                       requestId=request_id,
                       readback={"previewId": preview["previewId"],
                                 "fingerprint": fingerprint,
                                 "orders": preview["summary"]["orders"]})
    except Exception as exc:  # noqa: BLE001 - bounded user-file failure
        st.session_state.pop(GETFLY_PREVIEW_KEY, None)
        return _result("getfly_preview", "", False,
                       f"Không thể đọc DSDH.xlsx: {exc}", requestId=request_id)


def _getfly_internal_status(source_status: Any) -> str:
    raw = _getfly_clean(source_status).casefold()
    if any(token in raw for token in ("hủy", "cancel", "cancelled")):
        return "cancel"
    if any(token in raw for token in ("hoàn thành", "completed", "done", "đã giao")):
        return "done"
    return "wait"


def _getfly_validate_order(order: Mapping[str, Any], mode: str,
                           vat_by_line: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    order_id = _getfly_clean(order.get("orderId"))
    customer = _getfly_clean(order.get("customerName"))
    order_date = _getfly_date(order.get("orderDate"))
    if not order_id:
        errors.append("Thiếu Mã ĐH.")
    if not customer:
        errors.append("Thiếu Tên KH.")
    if not order_date:
        errors.append("Ngày đặt hàng trống hoặc không hợp lệ.")
    if mode != GETFLY_MODE_SHIPMENT_AND_FINANCE:
        return errors

    for index, line in enumerate(order.get("serviceLines") or [], start=1):
        if not isinstance(line, Mapping):
            errors.append(f"Dòng dịch vụ {index} không hợp lệ.")
            continue
        name = _getfly_clean(line.get("product_name"))
        if not name:
            errors.append(f"Dòng dịch vụ {index} thiếu tên dịch vụ.")
        qty = _actual_amount(line.get("qty"))
        cost = _actual_amount(line.get("cost"))
        price = _actual_amount(line.get("price"))
        if qty is None or qty <= 0:
            errors.append(f"Dòng dịch vụ {index} thiếu/không hợp lệ Số lượng.")
        if cost is None:
            errors.append(f"Dòng dịch vụ {index} thiếu/không hợp lệ Giá vốn.")
        if price is None:
            errors.append(f"Dòng dịch vụ {index} thiếu/không hợp lệ Giá bán.")
        line_id = _getfly_clean(line.get("line_id"))
        raw_vat = vat_by_line.get(line_id) if line_id else None
        vat = _actual_amount(raw_vat)
        if _is_blank_amount(raw_vat):
            errors.append(f"Dòng dịch vụ {index} thiếu VAT — 0 là hợp lệ nhưng để trống thì không.")
        elif vat is None or vat < 0 or vat > 100:
            errors.append(f"Dòng dịch vụ {index} có VAT không hợp lệ (0–100%).")
    return errors


def _getfly_document(order: Mapping[str, Any], mode: str,
                     vat_by_line: Mapping[str, Any]) -> dict[str, Any]:
    order_id = _getfly_clean(order.get("orderId"))
    order_date = _getfly_date(order.get("orderDate"))
    details: list[dict[str, Any]] = []
    if mode == GETFLY_MODE_SHIPMENT_AND_FINANCE:
        for line in order.get("serviceLines") or []:
            line_id = _getfly_clean(line.get("line_id"))
            details.append({
                "id": line_id,
                "name_full": _getfly_clean(line.get("product_name")),
                "display_name": _getfly_clean(line.get("product_name")),
                "code": _getfly_clean(line.get("product_code")),
                "qty": _actual_amount(line.get("qty")),
                "cost": _actual_amount(line.get("cost")),
                "price": _actual_amount(line.get("price")),
                "vat_line": _actual_amount(vat_by_line.get(line_id)),
                "note": _getfly_clean(line.get("product_note")),
            })
    head = {
        "st": _getfly_internal_status(order.get("sourceStatus")),
        # GetFly DSDH does not state operational mode or Incoterm. Keep these
        # explicit UNKNOWN/blank facts so generic repair_data() defaults cannot
        # invent Sea/EXW on this import-specific document.
        "mode": "",
        "incoterm": "",
        "created_at": order_date,
        "order_date": order_date,
        "source_status": _getfly_clean(order.get("sourceStatus")),
        "source_customer_code": _getfly_clean(order.get("customerCode")),
    }
    return {
        "id": order_id,
        "shipment_id": order_id,
        "customer": _getfly_clean(order.get("customerName")),
        "client": _getfly_clean(order.get("customerName")),
        "customer_id": _getfly_clean(order.get("customerId")),
        "status": head["st"],
        # Deliberately no route, mode, Incoterm, customs, vehicle, contract or
        # FX facts: the source file did not state any of them.
        "data": {
            "0.0": head,
            "1.2": {},
            "2.4": {},
            "2.6": {},
            "2.7": {},
            "3.4": {"details": details, "payments": [], "commission": {}},
            "entrustment": {},
        },
    }


def _getfly_readback(shipment: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    head = shipment.get("data", {}).get("0.0", {}) if isinstance(shipment.get("data"), Mapping) else {}
    finance = shipment.get("data", {}).get("3.4", {}) if isinstance(shipment.get("data"), Mapping) else {}
    return {
        "id": _getfly_clean(shipment.get("id")),
        "customer": _getfly_clean(shipment.get("customer") or shipment.get("client")),
        "customerId": _getfly_clean(shipment.get("customer_id")),
        "orderDate": _getfly_clean(head.get("order_date") or head.get("created_at")),
        "sourceStatus": _getfly_clean(head.get("source_status")),
        "status": _getfly_clean(shipment.get("status") or head.get("st")),
        "importMode": mode,
        "transportMode": _getfly_clean(head.get("mode")),
        "financeActualLineCount": len(finance.get("details") or []) if isinstance(finance, Mapping) else 0,
        "route": _getfly_clean(shipment.get("data", {}).get("1.2", {}).get("pol"))
        if isinstance(shipment.get("data", {}).get("1.2"), Mapping) else "",
        "currency": _getfly_clean(shipment.get("currency") or finance.get("currency"))
        if isinstance(finance, Mapping) else "",
    }


def _handle_getfly_import(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Commit only missing orders using one canonical shipment write per order."""
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic

    request_id = _getfly_clean(payload.get("requestId"))
    preview_id = _getfly_clean(payload.get("previewId"))
    mode = _getfly_clean(payload.get("mode")).upper()
    vat_by_line = payload.get("vatByLineId") if isinstance(payload.get("vatByLineId"), Mapping) else {}
    preview = st.session_state.get(GETFLY_PREVIEW_KEY)

    def _failure(message: str, results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return _result("getfly_import", "", False, message, requestId=request_id,
                       previewId=preview_id, mode=mode, results=results or [])

    if not isinstance(preview, Mapping) or preview.get("previewId") != preview_id:
        return _failure("Preview GetFly đã hết hạn hoặc không tồn tại. Hãy chọn lại DSDH.xlsx.")
    if mode not in {GETFLY_MODE_SHIPMENT_ONLY, GETFLY_MODE_SHIPMENT_AND_FINANCE}:
        return _failure("Chưa chọn chế độ nhập GetFly hợp lệ.")
    if not can_operate_business("shipment_create"):
        results = [{"orderId": _getfly_clean(order.get("orderId")),
                    "status": "REFUSED_VALIDATION", "error": "RBAC: không có quyền shipment_create."}
                   for order in preview.get("orders") or []]
        return _failure("RBAC: không có quyền shipment_create.", results)
    if mode == GETFLY_MODE_SHIPMENT_AND_FINANCE and not can_operate_business("finance_write"):
        results = [{"orderId": _getfly_clean(order.get("orderId")),
                    "status": "REFUSED_VALIDATION", "error": "RBAC: không có quyền finance_write."}
                   for order in preview.get("orders") or []]
        return _failure("RBAC: không có quyền finance_write.", results)

    fresh_ids = set(load_shipments().keys())
    results: list[dict[str, Any]] = []
    for order in preview.get("orders") or []:
        order_id = _getfly_clean(order.get("orderId"))
        if order_id in fresh_ids:
            results.append({"orderId": order_id, "status": "SKIPPED_ALREADY_EXISTS",
                            "customer": _getfly_clean(order.get("customerName")),
                            "message": "Đã có trong hệ thống"})
            continue

        errors = _getfly_validate_order(order, mode, vat_by_line)
        if errors:
            results.append({"orderId": order_id, "status": "REFUSED_VALIDATION",
                            "customer": _getfly_clean(order.get("customerName")),
                            "errors": errors})
            continue

        document = _getfly_document(order, mode, vat_by_line)
        if not save_shipment_atomic(document, actor=_actor()):
            results.append({"orderId": order_id, "status": "FAILED_WRITE",
                            "customer": _getfly_clean(order.get("customerName")),
                            "error": get_last_db_error() or "Không tạo được lô từ GetFly."})
            continue
        fresh = read_shipment(order_id)
        if not fresh:
            results.append({"orderId": order_id, "status": "FAILED_WRITE",
                            "error": "Đã ghi nhưng không đọc lại được lô vừa tạo."})
            continue
        fresh_ids.add(order_id)
        results.append({"orderId": order_id, "status": "CREATED",
                        "customer": _getfly_clean(order.get("customerName")),
                        "readback": _getfly_readback(fresh, mode=mode)})

    failed = [row for row in results if row.get("status") in {"REFUSED_VALIDATION", "FAILED_WRITE"}]
    ok = not failed
    return _result("getfly_import", "", ok,
                   "" if ok else "Một hoặc nhiều đơn chưa được nhập; xem kết quả từng đơn.",
                   requestId=request_id, previewId=preview_id, mode=mode,
                   results=results,
                   readback={"previewId": preview_id, "mode": mode, "results": results})


def _attachment_policy() -> dict[str, Any]:
    """The server-enforced, provider-neutral attachment policy."""
    from core.auth import can_generate_documents
    from core.shipment_attachments import (
        ALLOWED_ACCEPT,
        ALLOWED_EXTENSIONS,
        CATEGORIES,
        MAX_UPLOAD_BYTES,
        resolve_storage_backend,
        storage_is_configured,
        storage_label,
    )

    backend = resolve_storage_backend()
    configured = storage_is_configured(backend)
    return {
        "allowUpload": bool(can_generate_documents()),
        "categories": [dict(item) for item in CATEGORIES],
        "allowedExtensions": list(ALLOWED_EXTENSIONS),
        "accept": ALLOWED_ACCEPT,
        "maxUploadBytes": MAX_UPLOAD_BYTES,
        "maxUploadLabel": f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        "storageBackend": backend,
        "storageConfigured": configured,
        "storageLabel": storage_label(backend),
        # Compatibility-only boolean for older fixtures. New UI wording uses
        # storageLabel/storageConfigured and does not expose provider details.
        "driveConfigured": bool(configured) if backend == "drive_shared" else False,
    }


def _attachment_download_state() -> dict[str, Any]:
    """The ONE attachment whose bytes were just read from Drive (session-scoped).

    Holds no credential and no Drive id: only the attachment id, its shipment,
    a monotonically increasing ``seq`` that tells the UI "this is a NEW
    download", and the base64 body of the file the operator asked for.
    """
    state = st.session_state.get(ATTACHMENT_DOWNLOAD_KEY)
    return dict(state) if isinstance(state, Mapping) else {}


def _projection_for(shipment: Mapping[str, Any], *, db: Any = _UNSET_DB) -> dict[str, Any]:
    """Project one canonical shipment for the post-write readback payload."""
    from core.database import _load_contracts_impl, _load_customers_impl, load_quotes
    from core.shipment_dashboard import build_shipment_dashboard_view

    sid = rd.text(shipment.get("id"))
    db = _resolve_db(db)
    try:
        view = build_shipment_dashboard_view(shipment)
    except Exception:  # noqa: BLE001
        view = {}
    # LOGI_INTERACTION_LATENCY_FINALIZE_02 — the readback's five reference /
    # history reads are independent of one another (the fresh shipment document
    # itself was already read, sequentially, by the caller), so they are issued
    # together: same readers, same rows, same projection call as before.  As in
    # the build, the workers get the handle resolved by the script thread and
    # run STREAMLIT-FREE (the uncached implementations are the same reads the
    # public cache wrappers perform).
    loaded = _read_concurrently({
        "customers": lambda: _load_customers_impl(db=db),
        "contracts": lambda: _load_contracts_impl(db=db),
        "quotes": lambda: load_quotes(db=db),
        "history": lambda: rd.timeline_projection(sid, db=db),
        # A fresh, shipment-scoped attachment read: the readback proves the
        # metadata write landed instead of echoing what the browser sent.
        "attachments": (lambda: _attachment_records(sid, db=db)) if sid else (lambda: None),
    })
    return rd.shipment_projection(
        shipment,
        customers=loaded["customers"] or {},
        contracts=loaded["contracts"] or {},
        quotes=loaded["quotes"] or {},
        dashboard=view,
        history=loaded["history"],
        attachments={sid: loaded["attachments"]} if sid else None,
        attachment_download=_attachment_download_state(),
    )


def _attachment_records(shipment_id: str, *, db: Any = _UNSET_DB) -> list[dict[str, Any]]:
    """Raw attachment metadata for ONE shipment, straight from the database."""
    from core.database import load_shipment_attachments

    try:
        return [dict(row) for row in (load_shipment_attachments(shipment_id, db=_resolve_db(db)) or {}).values()]
    except Exception:  # noqa: BLE001 - a read failure must not blank the readback
        return []


def _attachment_result_extras(shipment_id: str) -> dict[str, Any]:
    """Shared readback/audit tail for the two attachment events."""
    return {
        "readback": _projection_for(read_shipment(shipment_id) or {}),
        "audit": _audit_trail(shipment_id),
    }


def _handle_shipment_attachment_upload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — ONE bounded attachment upload.

    Order is deliberate and matches the external-side-effect rule:
    RBAC → shipment exists → bounded decode → validate → SHA-256 → duplicate
    guard → Drive upload → Mongo metadata. Unauthorized, oversized and
    duplicate requests never reach the selected storage backend.
    """
    from core.auth import can_generate_documents
    from core.shipment_attachments import (
        CODE_INVALID,
        CODE_SIZE,
        MAX_UPLOAD_BYTES,
        UploadRefused,
        decode_upload_payload,
        project_attachment,
        storage_label,
        upload_attachment,
    )

    request_id = rd.text(payload.get("requestId"))
    sid = rd.text(payload.get("shipmentId"))
    if not sid:
        return _result("shipment_attachment_upload", sid, False, "Thiếu shipmentId.",
                       gate="INVALID_REQUEST", requestId=request_id)

    # Server RBAC first: the same sales_write boundary document work already
    # uses (core.auth.can_generate_documents). Unauthorized = zero Drive calls.
    if not can_generate_documents():
        return _result("shipment_attachment_upload", sid, False,
                       "RBAC: không có quyền sales_write để tải chứng từ lên lô hàng.",
                       gate="BLOCKED_PERMISSION_DENIED", requestId=request_id)

    # Preserve the long-standing read_shipment seam used by the dispatcher
    # contract/tests and by callers that override the fresh-read boundary.
    # Only unresolved identities need the richer ambiguity classification.
    shipment = read_shipment(sid)
    if shipment is None:
        _unresolved, identity_gate = _read_shipment_resolution(sid)
        if identity_gate == SHIPMENT_IDENTITY_AMBIGUOUS:
            return _result(
                "shipment_attachment_upload", sid, False,
                f"Mã lô {sid} bị trùng định danh dữ liệu cũ; chưa lưu tệp để tránh gắn nhầm lô.",
                gate=SHIPMENT_IDENTITY_AMBIGUOUS, requestId=request_id,
            )
        return _result("shipment_attachment_upload", sid, False, f"Không tìm thấy lô {sid}.",
                       gate=SHIPMENT_IDENTITY_NOT_FOUND, requestId=request_id)

    # The browser's declared size is checked FIRST (cheapest refusal), then the
    # base64 body is bounded before decoding, then the SERVICE re-checks the
    # decoded byte count — a lying client cannot get an oversized file to Drive.
    declared_raw = payload.get("size")
    declared_size: int | None = None
    if declared_raw is not None:
        try:
            declared_size = int(declared_raw)
        except (TypeError, ValueError):
            return _result("shipment_attachment_upload", sid, False, "Kích thước tệp không hợp lệ.",
                           gate=CODE_INVALID, requestId=request_id)
        if declared_size > MAX_UPLOAD_BYTES:
            return _result(
                "shipment_attachment_upload", sid, False,
                f"Tệp vượt giới hạn {MAX_UPLOAD_BYTES // (1024 * 1024)} MB — "
                "chưa gọi kho chứng từ, chưa lưu dữ liệu.",
                gate=CODE_SIZE, requestId=request_id,
            )

    try:
        data, size = decode_upload_payload(payload)
    except UploadRefused as refusal:
        return _result("shipment_attachment_upload", sid, False, refusal.message,
                       gate=refusal.code, requestId=request_id)

    outcome = upload_attachment(
        shipment_id=sid,
        category=payload.get("category"),
        file_name=rd.text(payload.get("fileName")),
        mime=rd.text(payload.get("mime")),
        data=data,
        declared_size=declared_size if declared_size is not None else size,
        uploaded_by=_actor(),
        shipment_context=shipment,
    )

    if not outcome.get("ok"):
        return _result("shipment_attachment_upload", sid, False,
                       rd.text(outcome.get("error")) or "Tải tệp lên thất bại.",
                       gate=rd.text(outcome.get("code")) or "UPLOAD_FAILED",
                       requestId=request_id,
                       orphanRisk=bool(outcome.get("orphan_risk")),
                       compensationAttempted=bool(outcome.get("compensation_attempted", False)),
                       compensated=bool(outcome.get("compensated", False)),
                       metadataCommitted=bool(outcome.get("metadata_committed", False)),
                       readbackProven=bool(outcome.get("readback_proven", False)),
                       **_attachment_result_extras(sid))

    record = outcome.get("record") or {}
    duplicate = bool(outcome.get("duplicate"))
    attachment = project_attachment(record)
    persisted = {
        "attachmentId": attachment["id"],
        "fileName": attachment["name"],
        "category": attachment["category"],
        "originalSize": attachment["originalSize"],
        "storedSize": attachment["storedSize"],
        "compressionMode": attachment["compressionMode"],
        "status": attachment["status"],
        "duplicate": duplicate,
    }
    return _result(
        "shipment_attachment_upload", sid, True,
        rd.text(outcome.get("message")) or (
            f"Đã lưu tệp vào {storage_label()} và ghi metadata vào lô hàng."
        ),
        gate="DUPLICATE" if duplicate else "UPLOADED",
        requestId=request_id, duplicate=duplicate, attachment=attachment,
        persisted=persisted, **_attachment_result_extras(sid),
    )


def _handle_attachment_download(payload: Mapping[str, Any]) -> dict[str, Any]:
    """LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — server-authoritative download.

    Read access is the EXISTING shipment read boundary (``dashboard``), so any
    role that may see the lot may open its files; nothing is written to Mongo
    and no Drive id, folder id or token is ever handed to the browser.
    """
    import base64 as _base64

    from core.auth import can_operate_business
    from core.database import load_shipment_attachment
    from core.shipment_attachments import CODE_NOT_FOUND, fetch_attachment_bytes, storage_label

    request_id = rd.text(payload.get("requestId"))
    sid = rd.text(payload.get("shipmentId"))
    attachment_id = rd.text(payload.get("attachmentId"))
    if not sid or not attachment_id:
        return _result("attachment_download", sid, False, "Thiếu shipmentId hoặc attachmentId.",
                       gate="INVALID_REQUEST", requestId=request_id)

    if not can_operate_business("dashboard"):
        return _result("attachment_download", sid, False,
                       "RBAC: không có quyền đọc chứng từ của lô hàng.",
                       gate="BLOCKED_PERMISSION_DENIED", requestId=request_id)

    # CONTROL_TOWER_REPAIR: ownership is verified from the canonical metadata
    # BEFORE any Drive read, so a mismatched pair costs zero Drive calls. The
    # post-read check below stays as defense-in-depth.
    stored = load_shipment_attachment(attachment_id)
    if stored is None:
        return _result("attachment_download", sid, False,
                       "Không tìm thấy tệp đính kèm này.",
                       gate=CODE_NOT_FOUND, requestId=request_id)
    if rd.text(stored.get("shipment_id")) != sid:
        return _result("attachment_download", sid, False,
                       "Tệp đính kèm không thuộc lô hàng này.",
                       gate="SHIPMENT_MISMATCH", requestId=request_id)

    outcome = fetch_attachment_bytes({"id": attachment_id}, shipment_id=sid)
    if not outcome.get("ok"):
        return _result("attachment_download", sid, False,
                       rd.text(outcome.get("error")) or f"Không đọc được tệp từ {storage_label()}.",
                       gate=rd.text(outcome.get("code")) or "DOWNLOAD_FAILED", requestId=request_id)

    record = outcome.get("record") or {}
    if rd.text(record.get("shipment_id")) != sid:
        # A stored file belongs to exactly one lot; a mismatched pair is refused
        # rather than served under the wrong shipment's permissions.
        return _result("attachment_download", sid, False,
                       "Tệp đính kèm không thuộc lô hàng này.",
                       gate="SHIPMENT_MISMATCH", requestId=request_id)

    data = bytes(outcome.get("data") or b"")
    previous = _attachment_download_state()
    seq = int(previous.get("seq") or 0) + 1
    st.session_state[ATTACHMENT_DOWNLOAD_KEY] = {
        "attachmentId": attachment_id,
        "shipmentId": sid,
        "fileName": rd.text(record.get("original_name")) or rd.text(record.get("stored_name")),
        "mime": rd.text(record.get("mime")),
        "bytes": len(data),
        "seq": seq,
        "base64": _base64.b64encode(data).decode("ascii"),
    }
    return _result(
        "attachment_download", sid, True, "Đã đọc tệp từ kho chứng từ qua máy chủ.",
        gate="DOWNLOADED", requestId=request_id,
        persisted={
            "attachmentId": attachment_id,
            "fileName": rd.text(record.get("original_name")),
            "size": len(data),
            "seq": seq,
        },
        **_attachment_result_extras(sid),
    )


def _shipment_document_review_state() -> dict[str, Any]:
    """The ONE ephemeral read-only review kept for this session.

    Holds no bytes, no base64, no storage id and no full document text — only
    the bounded projection ``core.shipment_document_review`` produced, plus the
    ``requestId``/``shipmentId`` that let the UI correlate the result with the
    exact request that produced it.
    """
    state = st.session_state.get(SHIPMENT_DOCUMENT_REVIEW_KEY)
    return dict(state) if isinstance(state, Mapping) else {}


def _handle_shipment_document_review(payload: Mapping[str, Any]) -> dict[str, Any]:
    """LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — ONE read-only review.

    Server order is the contract and every refusal before the byte read costs
    ZERO storage reads:

      1. request shape (bounded identifiers only — never bytes/base64/storage
         ids/raw SHA/credentials);
      2. RBAC ``can_operate_business("dashboard")`` — the SAME read boundary the
         existing attachment download uses, so a role that may see the lot may
         inspect its documents without needing sales_write;
      3. fresh shipment existence / identity;
      4. 1..6 unique attachment ids;
      5. canonical metadata for every selected attachment (ONE scoped read);
      6. proof that every attachment belongs to THIS shipment;
      7. supported extension preflight;
      8. per-file + aggregate review-byte budget from metadata;
      9. only now read bytes, sequentially, through the EXISTING
         ``core.shipment_attachments.fetch_attachment_bytes``;
     10-13. Run 2 reader → Run 1 cross-check → bounded ephemeral projection.

    It writes nothing: no shipment field, no attachment row, no audit entry.
    """
    from core.auth import can_operate_business
    from core.database import load_shipment_attachment, load_shipment_attachments
    from core.shipment_document_review import (
        CODE_ATTACHMENT_NOT_FOUND,
        CODE_INVALID_REQUEST,
        CODE_SHIPMENT_MISMATCH,
        MAX_REVIEW_FILES,
        run_shipment_document_review,
    )

    request_id = rd.text(payload.get("requestId"))
    sid = rd.text(payload.get("shipmentId"))
    raw_ids = payload.get("attachmentIds")

    # --- 1. request shape ----------------------------------------------------
    if not sid or not request_id:
        return _result("shipment_document_review", sid, False,
                       "Thiếu shipmentId hoặc requestId.",
                       gate=CODE_INVALID_REQUEST, requestId=request_id)
    if not isinstance(raw_ids, (list, tuple)):
        return _result("shipment_document_review", sid, False,
                       "Danh sách tệp đính kèm không hợp lệ.",
                       gate=CODE_INVALID_REQUEST, requestId=request_id)
    attachment_ids = [rd.text(item) for item in raw_ids]
    if any(not item for item in attachment_ids):
        return _result("shipment_document_review", sid, False,
                       "Mã tệp đính kèm không hợp lệ.",
                       gate=CODE_INVALID_REQUEST, requestId=request_id)
    if len(attachment_ids) > MAX_REVIEW_FILES:
        # Cheapest possible refusal: counted before any metadata or byte read.
        return _result(
            "shipment_document_review", sid, False,
            f"Chỉ kiểm tra tối đa {MAX_REVIEW_FILES} tệp một lần — đã chọn {len(attachment_ids)} tệp.",
            gate="SELECTION_LIMIT_EXCEEDED", requestId=request_id,
        )

    # --- 2. dashboard read RBAC ---------------------------------------------
    if not can_operate_business("dashboard"):
        return _result("shipment_document_review", sid, False,
                       "RBAC: không có quyền đọc chứng từ của lô hàng.",
                       gate="BLOCKED_PERMISSION_DENIED", requestId=request_id)

    # --- 3. fresh shipment existence / identity ------------------------------
    shipment = read_shipment(sid)
    if shipment is None:
        _unresolved, identity_gate = _read_shipment_resolution(sid)
        if identity_gate == SHIPMENT_IDENTITY_AMBIGUOUS:
            return _result(
                "shipment_document_review", sid, False,
                f"Mã lô {sid} bị trùng định danh dữ liệu cũ; chưa kiểm tra chứng từ.",
                gate=SHIPMENT_IDENTITY_AMBIGUOUS, requestId=request_id,
            )
        return _result("shipment_document_review", sid, False, f"Không tìm thấy lô {sid}.",
                       gate=SHIPMENT_IDENTITY_NOT_FOUND, requestId=request_id)

    # --- 5. canonical metadata: ONE shipment-scoped read --------------------
    try:
        rows = load_shipment_attachments(sid) or {}
    except Exception:  # noqa: BLE001 - a metadata read failure refuses honestly
        rows = {}
    metadata_rows = {rd.text(key): dict(row) for key, row in rows.items()
                     if isinstance(row, Mapping)}
    for attachment_id in attachment_ids:
        if attachment_id in metadata_rows:
            continue
        # Not in THIS shipment's rows: one extra lookup classifies the honest
        # reason (unknown file vs. a file owned by another lot) instead of
        # guessing. Still metadata only — still zero storage byte reads.
        stored = load_shipment_attachment(attachment_id)
        if stored is None:
            return _result("shipment_document_review", sid, False,
                           "Không tìm thấy tệp đính kèm này trong lô hàng.",
                           gate=CODE_ATTACHMENT_NOT_FOUND, requestId=request_id,
                           attachmentId=attachment_id)
        return _result("shipment_document_review", sid, False,
                       "Tệp đính kèm không thuộc lô hàng này.",
                       gate=CODE_SHIPMENT_MISMATCH, requestId=request_id,
                       attachmentId=attachment_id)

    # --- 4, 6, 7, 8, 9-13: the ONE orchestration seam ------------------------
    review = run_shipment_document_review(
        sid, attachment_ids, metadata_rows=metadata_rows,
    )
    refusal = review.get("refusal") if isinstance(review.get("refusal"), Mapping) else None

    if refusal is not None:
        return _result(
            "shipment_document_review", sid, False,
            rd.text(refusal.get("message")) or "Chưa kiểm tra được chứng từ.",
            gate=rd.text(refusal.get("code")) or "REVIEW_REFUSED",
            requestId=request_id,
            attachmentId=rd.text(refusal.get("attachmentId")),
            review={key: value for key, value in review.items() if key != "refusal"},
        )

    # SESSION ONLY: one bounded slot, replaced by the next review. Nothing is
    # persisted to shipments, shipment_attachments, audit, GridFS or Drive.
    previous = _shipment_document_review_state()
    st.session_state[SHIPMENT_DOCUMENT_REVIEW_KEY] = {
        "requestId": request_id,
        "shipmentId": sid,
        "seq": int(previous.get("seq") or 0) + 1,
        "review": dict(review),
    }
    return _result(
        "shipment_document_review", sid, True,
        "Kết quả chỉ để kiểm tra — chưa ghi vào hồ sơ lô hàng.",
        gate="REVIEWED", requestId=request_id,
        review={key: value for key, value in review.items() if key != "refusal"},
    )


def consume_document_review_triggers(session: dict, result: Any) -> list[dict[str, Any]]:
    """The ONE bounded READ-ONLY shipment document review dispatcher.

    Mirrors ``consume_tariff_triggers`` exactly: the same replay protection (a
    one-shot ``seq``) and NO business mutation. The outcome — refusal or bounded
    review — is delivered through the ordinary ``lastWrites`` readback so the
    pending UI settles only on the matching ``requestId``.
    """
    outcomes: list[dict[str, Any]] = []
    for event_name in sorted(DOCUMENT_REVIEW_EVENTS):
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
        try:
            outcomes.append(_handle_shipment_document_review(data))
        except Exception as exc:  # noqa: BLE001 - one bad event must not break the run
            outcomes.append(_result(
                event_name, rd.text(data.get("shipmentId")), False,
                f"{type(exc).__name__}: {exc}",
                gate="REVIEW_FAILED", requestId=rd.text(data.get("requestId")),
            ))
    return outcomes


def _shipment_document_review_projection() -> dict[str, Any] | None:
    """The bounded review result for the view-model (``None`` when there is none).

    The stored review carries its own shipment id; the UI additionally refuses
    to render a review whose ``shipmentId`` differs from the open lot, so a
    stale cross-shipment result can never be projected onto another shipment.
    """
    state = _shipment_document_review_state()
    review = state.get("review")
    if not isinstance(review, Mapping):
        return None
    return {
        "requestId": rd.text(state.get("requestId")),
        "shipmentId": rd.text(state.get("shipmentId")),
        "seq": int(state.get("seq") or 0),
        **{key: value for key, value in review.items() if key != "refusal"},
    }


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


def _handle_shipment_customer_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Fix the customer half of a lot's name through the EXISTING canonical writer.

    A lot in this app has no separate free-text title: what the shell shows and
    what the team calls "tên lô hàng" is the lot code plus its customer (see
    ``docs/goals/LOG-LG05``), and the customer half is exactly what
    ``core.database.update_shipment_customer`` already writes — with its own
    ``shipment_edit`` gate, ``customer_updated`` audit row and version bump —
    for the legacy Streamlit desk. This handler is only the missing bounded
    shell around it (RBAC → known-customer resolution → writer → fresh read);
    it adds no field, no collection and no fallback name.

    Resolution mirrors ``_handle_shipment_create``: a known ``customerId`` wins
    and its master name is what gets stored; a raw ``customer`` string is
    accepted only when the operator typed it. Nothing is invented and a
    mismatched picker never blanks the master data.
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, load_customers, update_shipment_customer

    sid = rd.text(payload.get("shipmentId"))
    if not sid:
        return _result("shipment_customer_save", sid, False, "Thiếu shipmentId.")
    if not can_operate_business("shipment_edit"):
        return _result("shipment_customer_save", sid, False, "RBAC: không có quyền shipment_edit.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("shipment_customer_save", sid, False, f"Không tìm thấy lô {sid}.")

    customer_id = rd.text(payload.get("customerId")).upper()
    typed_name = rd.text(payload.get("customer"))
    customers = load_customers() or {}
    if customer_id:
        document = customers.get(customer_id)
        if not isinstance(document, Mapping):
            return _result("shipment_customer_save", sid, False,
                           f"Không có khách hàng {customer_id} trong danh bạ.")
        name = rd.text(document.get("name"))
        if not name:
            return _result("shipment_customer_save", sid, False,
                           f"Khách hàng {customer_id} chưa có tên trong danh bạ.")
    else:
        # No invented identity: an empty picker with no typed name is a
        # mistake, not a business fact, and is refused rather than written.
        if not typed_name:
            return _result("shipment_customer_save", sid, False,
                           "Chọn khách hàng trong danh bạ hoặc gõ đúng tên khách.")
        name = typed_name
        customer_id = ""

    previous = rd.text(shipment.get("customer") or shipment.get("client"))
    if name == previous and (not customer_id or customer_id == rd.text(shipment.get("customer_id"))):
        # Nothing to write: report the unchanged truth instead of a no-op
        # version bump that would look like a change in the audit trail.
        return _result("shipment_customer_save", sid, True, "Không có thay đổi để lưu.",
                       readback=_projection_for(shipment), noop=True,
                       persisted={"customer": previous})

    if not update_shipment_customer(sid, name, customer_id):
        return _result("shipment_customer_save", sid, False,
                       get_last_db_error() or "Không cập nhật được khách hàng của lô.")

    fresh = read_shipment(sid) or {}
    return _result("shipment_customer_save", sid, True, readback=_projection_for(fresh),
                   persisted={"customer": rd.text(fresh.get("customer")),
                              "customerId": rd.text(fresh.get("customer_id"))},
                   version=int(fresh.get("version") or 0),
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


#: Operator-facing field names of the execution profile as they arrive from the
#: component. Anything outside this set is ignored (never written) and reported
#: back in ``rejected``, exactly like the scalar whitelist above.
PROFILE_PAYLOAD_KEYS = (
    "mode", "incoterm", "incotermVersion", "namedPlace", "loadModel",
    "serviceScope", "serviceScopeConfirmed", "cargoInsurance",
)


def _handle_shipment_profile_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """LOGI_SHIPMENT_EXECUTION_PROFILE_01 — the ONE bounded write for the profile.

    The execution profile is the shipment's operational contract: Incoterms code
    + VERSION + named place, the operator-confirmed Trường Thành service scope,
    the load model, and the ACTUAL cargo-insurance state. Exactly like every
    other material write in this shell it is:

        typed event → RBAC → validate → the EXISTING atomic shipment writer
        → audit (written by that writer) → fresh authoritative read

    Reuse, not duplication:

    * ``data.0.0.mode`` and ``data.0.0.incoterm`` stay the canonical mode and
      rule fields — this handler writes THOSE paths (canonical Incoterms code,
      existing mode vocabulary), never a ``new_incoterm``/``mode_v2`` twin;
    * only facts no existing field could carry are added, under ONE block
      ``data.0.0.execution_profile``: the Incoterms VERSION, the named place,
      the load model, the confirmed service scope, the raw contract wording
      when it differs from the canonical code (evidence), and the actual
      cargo-insurance state.

    An impossible combination (FOB + ROAD, CIF + AIR, DAT @2020, DPU @2010,
    DAF/DDU outside legacy 2000) is REFUSED with the explanation the UI shows;
    an incomplete new configuration is refused too. Nothing is auto-corrected
    and nothing is partially written.
    """

    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic
    from core.logic import apply_financial_snapshot
    from core.shipment_execution_profile import (
        ACTUAL_INSURANCE_STATES,
        INCOTERM_VERSIONS,
        STORED_MODE_BY_CANONICAL,
        canonical_mode,
        normalize_incoterm,
        normalize_service_scope,
        profile_document,
        profile_facts,
        validate_profile,
    )

    sid = rd.text(payload.get("shipmentId"))
    request_id = rd.text(payload.get("requestId"))

    def _res(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        # The click identity is echoed so the page can match THIS backend answer
        # (including a refusal) to the save that produced it.
        return _result("shipment_profile_save", sid, ok, error,
                       requestId=request_id, **extra)

    if not sid:
        return _res(False, "Thiếu shipmentId.")
    if not can_operate_business("shipment_edit"):
        return _res(False, "RBAC: không có quyền shipment_edit.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _res(False, f"Không tìm thấy lô {sid}.")

    current = profile_facts(shipment)
    rejected = [key for key in payload if key not in PROFILE_PAYLOAD_KEYS
                and key not in {"shipmentId", "requestId"}]

    # A partial submission only moves the facts it actually carries; a key the
    # operator cleared travels as an explicit blank and clears that fact.
    facts: dict[str, Any] = {
        "storedMode": current["storedMode"],
        "mode": current["mode"],
        "incoterm": current["incoterm"],
        "incotermRawInput": current["incotermRawInput"],
        "incotermRawLabel": current["incotermRawLabel"],
        "incotermVersion": current["incotermVersion"],
        "incotermNamedPlace": current["incotermNamedPlace"],
        "loadModel": current["loadModel"],
        "serviceScope": list(current["serviceScope"]),
        "serviceScopeConfirmed": current["serviceScopeConfirmed"],
        "cargoInsuranceStatus": current["cargoInsuranceStatus"],
        "cargoInsuranceArrangedBy": current["cargoInsuranceArrangedBy"],
        "cargoInsuranceInsurer": current["cargoInsuranceInsurer"],
        "cargoInsurancePolicyNo": current["cargoInsurancePolicyNo"],
        "cargoInsuranceCoverageNote": current["cargoInsuranceCoverageNote"],
    }

    if "mode" in payload:
        canonical = canonical_mode(payload.get("mode"))
        facts["mode"] = canonical
        # `data.0.0.mode` keeps the repository's EXISTING mode vocabulary; the
        # canonical profile mode is the derivation/display vocabulary.
        facts["storedMode"] = STORED_MODE_BY_CANONICAL.get(canonical, "")

    if "incoterm" in payload:
        normalized = normalize_incoterm(payload.get("incoterm"))
        # The canonical code is stored; the raw contract wording survives as
        # evidence. A place written inside the term ("FOB Shenzhen") is read as
        # a SUGGESTION by the projection and is never persisted as the
        # confirmed named place by this save; a term this app cannot recognize
        # is refused, never guessed.
        facts["incoterm"] = normalized["code"]
        facts["incotermRawInput"] = rd.text(payload.get("incoterm"))
        facts["incotermRawLabel"] = normalized["rawLabel"]

    if "incotermVersion" in payload:
        version = rd.text(payload.get("incotermVersion"))
        facts["incotermVersion"] = version if version in INCOTERM_VERSIONS else ""
    if "namedPlace" in payload:
        facts["incotermNamedPlace"] = rd.text(payload.get("namedPlace"))
    if "loadModel" in payload:
        facts["loadModel"] = rd.text(payload.get("loadModel")).upper()
    if "serviceScope" in payload:
        facts["serviceScope"] = normalize_service_scope(payload.get("serviceScope"))
    if "serviceScopeConfirmed" in payload:
        facts["serviceScopeConfirmed"] = bool(payload.get("serviceScopeConfirmed"))
    if "cargoInsurance" in payload:
        insurance = payload.get("cargoInsurance")
        insurance = insurance if isinstance(insurance, Mapping) else {}
        status = rd.text(insurance.get("status")).upper()
        facts["cargoInsuranceStatus"] = status if status in ACTUAL_INSURANCE_STATES else ""
        facts["cargoInsuranceArrangedBy"] = rd.text(insurance.get("arrangedBy"))
        facts["cargoInsuranceInsurer"] = rd.text(insurance.get("insurerName"))
        facts["cargoInsurancePolicyNo"] = rd.text(insurance.get("policyNo"))
        facts["cargoInsuranceCoverageNote"] = rd.text(insurance.get("coverageNote"))

    # LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: new profiles imply 2020.
    # Blank incoterm stays blank — only version is implicit when a code is present.
    # Preserve historical 2010 / legacy when editing unrelated fields.
    if facts["incoterm"] and not facts["incotermVersion"]:
        from core.shipment_execution_profile import VERSION_2020, codes_for_version

        if facts["incoterm"] in codes_for_version(VERSION_2020):
            # Only auto-assign when current stored version was blank (new profile)
            # — a historical 2010/legacy already has a version and is preserved above.
            if not current.get("incotermVersion"):
                facts["incotermVersion"] = VERSION_2020

    issues = validate_profile(facts, for_write=True)
    if "cargoInsurance" in payload and rd.text((payload.get("cargoInsurance") or {}).get("status")) \
            and not facts["cargoInsuranceStatus"]:
        issues.append({"code": "INVALID_INSURANCE_STATUS",
                       "message": "Trạng thái bảo hiểm thực tế không hợp lệ."})
    if issues:
        return _res(False, issues[0]["message"], gate="PROFILE_REFUSED",
                    issues=issues, rejected=rejected)

    # Insurance evidence only exists behind an explicit YES: a NO/UNKNOWN never
    # silently keeps the policy details of an earlier state.
    if facts["cargoInsuranceStatus"] != "YES":
        facts.update({"cargoInsuranceArrangedBy": "", "cargoInsuranceInsurer": "",
                      "cargoInsurancePolicyNo": "", "cargoInsuranceCoverageNote": ""})

    document = profile_document(facts)
    head = shipment.setdefault("data", {}).setdefault("0.0", {})
    previous_block = head.get("execution_profile") if isinstance(head.get("execution_profile"), Mapping) else {}
    previous_code = rd.text(head.get("incoterm"))
    previous_mode = rd.text(head.get("mode"))
    stored_mode = rd.text(facts.get("storedMode"))

    if (factual_equal(previous_block, document) and previous_code == facts["incoterm"]
            and previous_mode == stored_mode):
        # Nothing changed: report the stored truth instead of a no-op version
        # bump that would look like a change in the audit trail.
        return _res(True, "Không có thay đổi để lưu.", noop=True, rejected=rejected,
                    persisted={"incoterm": previous_code, "mode": previous_mode,
                               "executionProfile": dict(previous_block)})

    head["mode"] = stored_mode
    head["incoterm"] = facts["incoterm"]
    head["execution_profile"] = document

    apply_financial_snapshot(shipment)
    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _res(False, get_last_db_error() or "Không lưu được hồ sơ thực hiện lô.")

    fresh = read_shipment(sid) or {}
    fresh_head = ((fresh.get("data") or {}).get("0.0") or {})
    return _res(True, readback=_projection_for(fresh),
        rejected=rejected,
        version=int(fresh.get("version") or 0),
        persisted={
            "mode": rd.text(fresh_head.get("mode")),
            "incoterm": rd.text(fresh_head.get("incoterm")),
            "executionProfile": dict(fresh_head.get("execution_profile") or {}),
        },
        audit=_audit_trail(sid),
    )


def factual_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """Value equality for two persisted profile blocks (no key order, no types)."""

    return json.loads(json.dumps(left, sort_keys=True, default=str)) == \
        json.loads(json.dumps(right, sort_keys=True, default=str))


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


#: Money facts a booked Finance Actual line must state explicitly. Keyed by the
#: component payload field → the Vietnamese caption an operator recognises.
FINANCE_ACTUAL_REQUIRED_FIELDS = (("price", "Giá bán"), ("cost", "Giá vốn"), ("vat", "VAT %"))


def _actual_amount(value: Any) -> float | None:
    """Strict amount parse for a BOOKED actual line. None = not stated.

    Parsing itself is the EXISTING canonical money parser
    (``core.utils.to_decimal``), which already understands both desk input
    styles ``1.200.000`` and ``1,234,567``; only its zero-default is refused
    here, because on a booked-actual write path a value the operator did not
    state (or that carries no digit at all) is UNKNOWN — UNKNOWN != ZERO.
    """
    from decimal import InvalidOperation

    from core.utils import to_decimal

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw or not any(ch.isdigit() for ch in raw):
        return None
    try:
        parsed = to_decimal(raw)
    except (InvalidOperation, ValueError):  # pragma: no cover - to_decimal guards
        return None
    return float(parsed)


def _is_blank_amount(value: Any) -> bool:
    """True when the operator stated NOTHING (absent, None or whitespace)."""
    return value is None or (isinstance(value, str) and not value.strip())


def _financial_amount(value: Any) -> float | None:
    """Strict money parse for the financial WRITE boundary, reusing canonical parser.

    Reuses the existing Finance Actual helper's logic which itself is based on
    ``core.utils.to_decimal`` — the canonical money parser that understands
    Vietnamese grouping (``500.000`` → 500000) and mixed separators.

    Contract:
    - blank / None / whitespace / no digit → None (UNKNOWN / invalid)
    - numeric → float
    - string with grouping → parsed via to_decimal
    - garbage like ``abc`` → None, never 0
    - explicit ``0`` → 0.0 (business rule decides if zero is allowed)
    """
    return _actual_amount(value)


def _handle_finance_actual_save(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Finance Actual = a real service line in ``data.3.4.details``.

    Quote Estimate is a separate object and is never written here.

    UNKNOWN != ZERO on this writer path: a booked actual line is a claim about
    money that really happened, so every amount has to be stated. A blank never
    silently becomes ``0.0`` — the save is REFUSED with an explicit Vietnamese
    message and nothing is written; ``0`` itself is a legitimate, deliberate
    answer (a service genuinely billed at 0, or genuinely without VAT).
    """
    from core.auth import can_operate_business
    from core.database import get_last_db_error, save_shipment_atomic
    from core.logic import apply_financial_snapshot

    sid = rd.text(payload.get("shipmentId"))
    line = payload.get("line") if isinstance(payload.get("line"), Mapping) else {}
    # Optional intent identity from the component: it is echoed back on every
    # outcome so the UI can match THIS click's authoritative answer (success or
    # refusal) instead of guessing from "the event was transported".
    request_id = rd.text(payload.get("requestId"))

    def _out(ok: bool, error: str = "", **extra: Any) -> dict[str, Any]:
        return _result("finance_actual_save", sid, ok, error, requestId=request_id, **extra)

    if not sid or not line:
        return _out(False, "Thiếu shipmentId hoặc line.")
    if not can_operate_business("finance_write"):
        return _out(False, "RBAC: không có quyền finance_write.")

    shipment = read_shipment(sid)
    if shipment is None:
        return _out(False, f"Không tìm thấy lô {sid}.")

    finance = shipment.setdefault("data", {}).setdefault("3.4", {})
    details = finance.setdefault("details", [])

    name = rd.text(line.get("name"))
    if not name:
        return _out(False, "Thiếu tên dịch vụ.")

    # Validation happens BEFORE anything is touched, so a refusal leaves no
    # half-written line behind.
    numbers: dict[str, float] = {}
    missing: list[str] = []
    invalid: list[str] = []
    for key, caption in FINANCE_ACTUAL_REQUIRED_FIELDS:
        raw = line.get(key)
        value = _actual_amount(raw)
        if value is None and _is_blank_amount(raw):
            missing.append(caption)
        elif value is None:
            invalid.append(caption)
        else:
            numbers[key] = value
    if missing:
        return _out(False, "Chưa nhập: " + ", ".join(missing)
                    + " — dòng thực tế phải nêu rõ số tiền (0 là giá trị hợp lệ; "
                      "để trống không phải là 0).")
    if invalid:
        return _out(False, "Giá trị không hợp lệ: " + ", ".join(invalid)
                    + " — nhập dạng số, ví dụ 1500000 hoặc VAT 8.")

    qty_raw = line.get("qty")
    qty = _actual_amount(qty_raw)
    qty_blank = _is_blank_amount(qty_raw)
    if qty is None and not qty_blank:
        return _out(False, "Số lượng không hợp lệ — nhập số lớn hơn 0, ví dụ 1 hoặc 2.")
    if qty is None:
        # A service line is booked per unit of service; the quantity itself is
        # not a money claim, so "not stated" keeps the canonical default of 1.
        qty = 1.0
    if qty <= 0:
        return _out(False, "Số lượng phải lớn hơn 0.")

    from uuid import uuid4

    target_id = rd.text(line.get("id"))
    entry: dict[str, Any] | None = None
    if target_id:
        entry = next((d for d in details if isinstance(d, Mapping) and rd.text(d.get("id")) == target_id), None)
        if entry is None:
            # Editing must target an existing canonical row. Minting a row from
            # a client-supplied id would let a stale screen create a second line.
            return _out(False, f"Không tìm thấy dòng thực tế cần sửa (mã {target_id})"
                           " — mở lại lô để đọc dữ liệu mới nhất.")
    else:
        entry = {"id": f"PAY-LINE-{uuid4().hex.upper()[:12]}"}
        details.append(entry)

    entry["name_full"] = name
    entry["display_name"] = name
    entry["unit"] = rd.text(line.get("unit")) or entry.get("unit") or "Lần"
    entry["note"] = rd.text(line.get("note"))
    if rd.text(line.get("code")):
        entry["code"] = rd.text(line.get("code"))
    # Every numeric below was explicitly supplied (or is the canonical qty
    # default) — there is deliberately no zero-filling fallback any more.
    entry["qty"] = qty
    entry["price"] = numbers["price"]
    entry["price_out"] = numbers["price"]
    entry["cost"] = numbers["cost"]
    entry["price_in"] = numbers["cost"]
    entry["vat_line"] = numbers["vat"]
    entry["vat"] = numbers["vat"]

    apply_financial_snapshot(shipment)
    if not save_shipment_atomic(shipment, expected_version=shipment.get("version"), actor=_actor()):
        return _out(False, get_last_db_error() or "Không lưu được.")

    fresh = read_shipment(sid) or {}
    fresh_lines = _get_path(fresh, ("data", "3.4", "details")) or []
    return _out(True, readback=_projection_for(fresh),
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
    amount = _financial_amount(payload.get("amount"))
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
    """One canonical payment reversal via ``save_direct_payment_correction``.

    Semantics are the WRITER's, not the UI's: the original payment is never
    edited in place nor deleted — the canonical writer appends a linked
    ``financial_corrections`` row, marks the payment reversed, audits
    ``payment_reversed`` and recomputes the derived totals. ``amount``/
    ``date``/``note`` are OPTIONAL EVIDENCE attached to the correction; they
    are not a replacement payment. The outcome echoes ``correctionRequestId``
    so the UI can match it to the pending intent exactly like the requestId
    echo on ``payment_record`` — transport success is never treated as write
    success.
    """
    from core.database import save_direct_payment_correction

    sid = rd.text(payload.get("shipmentId"))
    payment_id = rd.text(payload.get("paymentId"))
    correction_request_id = rd.text(payload.get("correctionRequestId"))
    reason = rd.text(payload.get("reason"))
    # Required identity per the write contract — the writer itself also
    # refuses a blank reason, but the handler must never substitute one.
    if not sid or not payment_id or not correction_request_id or not reason:
        return _result("payment_correction", sid, False,
                       "Thiếu shipmentId, paymentId, correctionRequestId hoặc LÝ DO điều chỉnh (bắt buộc).",
                       correctionRequestId=correction_request_id, paymentId=payment_id)
    ok, result, message = save_direct_payment_correction(
        sid,
        payment_id,
        correction_request_id,
        reason,
        {k: v for k, v in {
            "amount": _financial_amount(payload.get("amount")),
            "date": _normalize_date(payload.get("date")) or None,
            "note": rd.text(payload.get("note")) or None,
        }.items() if v is not None},
        actor=_actor(),
    )
    if not ok:
        return _result("payment_correction", sid, False, message or "Không điều chỉnh được.",
                       correctionRequestId=correction_request_id, paymentId=payment_id)
    fresh = read_shipment(sid) or {}
    return _result("payment_correction", sid, True, message, readback=_projection_for(fresh),
                   persisted=result, audit=_audit_trail(sid),
                   correctionRequestId=correction_request_id, paymentId=payment_id)


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
    amount = _financial_amount(payload.get("amount"))
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
    amount = _financial_amount(payload.get("amount"))
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

    # LOGI_SHIPMENT_EXECUTION_PROFILE_01 — the create form may state the profile
    # the detail page will later refine (Incoterms version, named place, load
    # model, Trường Thành service scope, actual cargo insurance). An impossible
    # combination is refused HERE rather than stored and explained later, and
    # nothing is written when the profile is invalid.
    from core.shipment_execution_profile import (
        INCOTERM_VERSIONS,
        STORED_MODE_BY_CANONICAL,
        blocking_write_issues,
        canonical_mode,
        normalize_incoterm,
        normalize_service_scope,
        profile_document,
        validate_profile,
    )

    profile_head: dict[str, Any] = {}
    # A BLANK contract term stays blank. The create form deliberately allows
    # "chưa chọn" (UNKNOWN), so validating or storing an invented ``EXW`` here
    # would fabricate a fact the operator never stated.
    head_incoterm = rd.text(transport.get("incoterm"))
    profile_keys = ("incotermVersion", "namedPlace", "loadModel", "serviceScope",
                    "serviceScopeConfirmed", "cargoInsurance")
    if any(key in transport or key in payload for key in profile_keys):
        insurance_payload = payload.get("cargoInsurance") or transport.get("cargoInsurance")
        insurance_payload = insurance_payload if isinstance(insurance_payload, Mapping) else {}
        insurance_status = rd.text(insurance_payload.get("status")).upper()
        version = rd.text(payload.get("incotermVersion") or transport.get("incotermVersion"))
        profile_facts_in = {
            "mode": canonical_mode(selected_mode),
            "storedMode": STORED_MODE_BY_CANONICAL.get(canonical_mode(selected_mode), ""),
            "incoterm": normalize_incoterm(head_incoterm)["code"],
            "incotermRawLabel": normalize_incoterm(head_incoterm)["rawLabel"],
            "incotermVersion": version if version in INCOTERM_VERSIONS else "",
            "incotermNamedPlace": rd.text(payload.get("namedPlace") or transport.get("namedPlace")),
            "loadModel": rd.text(payload.get("loadModel") or transport.get("loadModel")).upper(),
            "serviceScope": normalize_service_scope(payload.get("serviceScope") or transport.get("serviceScope")),
            "serviceScopeConfirmed": bool(payload.get("serviceScopeConfirmed")
                                          or transport.get("serviceScopeConfirmed")),
            "cargoInsuranceStatus": insurance_status,
            "cargoInsuranceArrangedBy": rd.text(insurance_payload.get("arrangedBy")),
            "cargoInsuranceInsurer": rd.text(insurance_payload.get("insurerName")),
            "cargoInsurancePolicyNo": rd.text(insurance_payload.get("policyNo")),
            "cargoInsuranceCoverageNote": rd.text(insurance_payload.get("coverageNote")),
        }
        # LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: new create implies 2020.
        # Blank incoterm stays blank — only infer when code present in 2020 set.
        if profile_facts_in["incoterm"] and not profile_facts_in["incotermVersion"]:
            from core.shipment_execution_profile import VERSION_2020 as _V2020, codes_for_version as _codes

            if profile_facts_in["incoterm"] in _codes(_V2020):
                profile_facts_in["incotermVersion"] = _V2020
        profile_issues = validate_profile(profile_facts_in, for_write=True)
        # A CONFLICT (FOB + ROAD, DAT + 2020, an unrecognized term the operator
        # actually typed, a foreign load model) refuses the create. A fact that
        # is merely not stated YET does not: the profile block is then simply
        # not written, the lot is created, and the lot detail page asks for the
        # missing facts — exactly what the create form promises the operator.
        blocking = blocking_write_issues(profile_issues, profile_facts_in)
        if blocking:
            return _res(False, blocking[0]["message"], issues=profile_issues)
        if not profile_issues:
            profile_head = profile_document(profile_facts_in)

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
                    # UNKNOWN stays UNKNOWN: a blank Incoterm is persisted as
                    # blank and never silently becomes EXW.
                    "incoterm": rd.text(transport.get("incoterm"))},
            "1.2": transport_section,
            "2.4": {},
            "2.6": {k: _coerce(k, v) for k, v in (("arrival_date", transport.get("etd")),) if v},
            "2.7": {k: _coerce(k, delivery.get(k)) for k in
                    ("addr", "phone_receiver", "delivery_date") if delivery.get(k) not in (None, "")},
            "3.4": {"details": [], "payments": [], "commission": {"list": [], "total": 0}},
            "entrustment": {"active": False},
        },
    }
    if profile_head:
        doc["data"]["0.0"]["execution_profile"] = profile_head
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


def _persist_generated_docgen_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Delegate immutable revision authority to the canonical database seam."""
    from core.database import create_or_observe_docgen_revision

    outcome = create_or_observe_docgen_revision(metadata)
    status = rd.text(outcome.get("status"))
    return {
        "ok": bool(outcome.get("ok")),
        "already_present": status == "ALREADY_MATCHING",
        "collision": status == "COLLISION",
        "metadata_committed": bool(outcome.get("metadata_committed"))
        or status in {"CREATED", "ALREADY_MATCHING"},
        "error": rd.text(outcome.get("error")),
        "record": outcome.get("record"),
        "status": status,
    }


def _next_gnt_revision(shipment_id: str) -> dict[str, Any]:
    """Read the next GNT revision from durable docgen metadata only."""
    from core.database import load_docgen_documents

    logical_id = f"GNT::{shipment_id}"
    try:
        documents = load_docgen_documents(shipment_id) or {}
    except Exception as exc:  # noqa: BLE001 - revision authority must fail closed
        return {"ok": False, "error": f"Không đọc được revision GNT: {exc}", "document_id": logical_id}

    revisions: list[int] = []
    for document in documents.values():
        if not isinstance(document, Mapping):
            continue
        if rd.text(document.get("document_type")).upper() != "GNT":
            continue
        if rd.text(document.get("document_id")) != logical_id:
            continue
        generation_raw = document.get("generation_revision")
        revision_raw = document.get("revision")
        if generation_raw is None and revision_raw is None:
            return {
                "ok": False,
                "error": f"Metadata GNT {document.get('id') or logical_id} thiếu revision; không đoán tiếp.",
                "document_id": logical_id,
            }
        try:
            generation = int(generation_raw if generation_raw is not None else revision_raw)
            revision = int(revision_raw if revision_raw is not None else generation_raw)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "error": f"Metadata GNT {document.get('id') or logical_id} có revision không hợp lệ.",
                "document_id": logical_id,
            }
        if generation < 1 or revision < 1 or generation != revision:
            return {
                "ok": False,
                "error": f"Metadata GNT {document.get('id') or logical_id} có revision không nhất quán.",
                "document_id": logical_id,
            }
        revisions.append(generation)

    return {
        "ok": True,
        "document_id": logical_id,
        "revision": max(revisions) + 1 if revisions else 1,
    }


def _generated_attachment_failure(
    event: str,
    shipment_id: str,
    outcome: Mapping[str, Any],
    *,
    attachment_persisted: bool = False,
    partial_durable: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    """Return one honest generated-file failure without hiding service state."""
    code = rd.text(outcome.get("code")) or "ATTACHMENT_PERSISTENCE_FAILED"
    return _result(
        event,
        shipment_id,
        False,
        rd.text(outcome.get("error")) or "Không lưu được tệp sinh ra vào kho chứng từ.",
        gate=code,
        attachmentPersisted=attachment_persisted,
        partialDurable=partial_durable,
        duplicate=bool(outcome.get("duplicate")),
        metadataCommitted=bool(outcome.get("metadata_committed")),
        readbackProven=bool(outcome.get("readback_proven")),
        orphanRisk=bool(outcome.get("orphan_risk")),
        compensationAttempted=bool(outcome.get("compensation_attempted", False)),
        compensated=bool(outcome.get("compensated", False)),
        **extra,
        **_attachment_result_extras(shipment_id),
    )


def _project_generated_attachment(outcome: Mapping[str, Any]) -> dict[str, Any]:
    record = outcome.get("record")
    if not isinstance(record, Mapping) or not rd.text(record.get("id")):
        return {}
    from core.shipment_attachments import project_attachment

    return project_attachment(record)


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

    metadata = dict(generated.get("metadata") or {})
    record_id = (rd.text(metadata.get("id"))
                 or f"{generated.get('document_id')}::R{generated.get('revision')}")
    metadata["id"] = record_id

    from core.shipment_attachments import upload_attachment

    attachment_outcome = upload_attachment(
        shipment_id=sid,
        category="other",
        file_name=rd.text(generated.get("output_file_name")) or f"PXK_{sid}.xlsx",
        mime=logi_c1._MIME_XLSX,
        data=raw,
        uploaded_by=_actor(),
        declared_size=len(raw),
        shipment_context=shipment,
    )
    attachment_record = attachment_outcome.get("record") or {}
    if not attachment_outcome.get("ok"):
        return _generated_attachment_failure(
            "pxk_generate", sid, attachment_outcome,
            service="core.docgen.generator.generate_document", delivered=True,
        )
    if not isinstance(attachment_record, Mapping) or not rd.text(attachment_record.get("id")):
        return _generated_attachment_failure(
            "pxk_generate", sid,
            {"code": "ATTACHMENT_READBACK_UNPROVEN", "error": "Kho chứng từ báo thành công nhưng thiếu hồ sơ tệp canonical."},
            service="core.docgen.generator.generate_document", delivered=True,
        )
    attachment_view = _project_generated_attachment(attachment_outcome)

    metadata_outcome = _persist_generated_docgen_metadata(metadata)
    if not metadata_outcome.get("ok"):
        return _result(
            "pxk_generate", sid, False, rd.text(metadata_outcome.get("error")) or "Không lưu được metadata PXK.",
            gate="PXK_REVISION_COLLISION" if metadata_outcome.get("collision") else "PXK_METADATA_FAILED",
            delivered=True, service="core.docgen.generator.generate_document",
            failClosed=True, attachmentPersisted=True, partialDurable=True,
            attachment=attachment_view, metadataCommitted=bool(metadata_outcome.get("metadata_committed")),
            duplicate=bool(attachment_outcome.get("duplicate")),
            **_attachment_result_extras(sid),
        )

    session_cache_error = ""
    try:
        logi_c1.store_output(sid, record_id, {
            "file_name": generated.get("output_file_name"), "mime": logi_c1._MIME_XLSX,
            "bytes": raw, "document_type": PXK, "revision": generated.get("revision"),
        })
    except Exception as exc:  # noqa: BLE001 - durable state already proved
        session_cache_error = str(exc)

    return _result("pxk_generate", sid, True, "Đã sinh PXK bằng dịch vụ docgen thật.",
                   gate=gate_state, delivered=True,
                   service="core.docgen.generator.generate_document",
                   persisted={"documentId": rd.text(generated.get("document_id")),
                              "recordId": record_id,
                              "attachmentId": rd.text(attachment_record.get("id")),
                              "fileName": rd.text(generated.get("output_file_name")),
                              "status": rd.text(generated.get("status")),
                              "revision": generated.get("revision"),
                              "outputHash": rd.text(generated.get("output_hash")),
                              "pxkNo": pxk_no, "pxkDate": pxk_date,
                              "bytes": len(raw),
                              "isOfficeFile": is_office,
                              "attachmentDuplicate": bool(attachment_outcome.get("duplicate")),
                              "sessionCachePersisted": not bool(session_cache_error)},
                   attachment=attachment_view,
                   sessionCacheError=session_cache_error,
                   readback=_projection_for(read_shipment(sid) or {}),
                   audit=_audit_trail(sid))


def _handle_gnt_generate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """GNT generation through the existing core.gnt_builder — real 2-sheet XLSX."""
    from datetime import datetime, timezone
    import streamlit as st

    from core.auth import can_generate_documents
    from core.database import load_customers
    from core.gnt_builder import build_gnt_workbook, check_gnt_prerequisites

    sid = rd.text(payload.get("shipmentId"))
    if not sid:
        return _result("gnt_generate", sid, False, "Thiếu shipmentId.")

    # Server RBAC: same sales_write permission used for document generation
    if not can_generate_documents():
        return _result(
            "gnt_generate",
            sid,
            False,
            "RBAC: không có quyền sales_write để sinh giấy nộp thuế.",
            gate="BLOCKED_PERMISSION_DENIED",
        )

    shipment = read_shipment(sid)
    if shipment is None:
        return _result("gnt_generate", sid, False, f"Không tìm thấy lô {sid}.")

    # Load customers to resolve unambiguous taxpayer info
    customers = load_customers() or {}
    customer_id = rd.text(shipment.get("customer_id"))
    customer_doc = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}

    # Check prerequisites with existing builder logic
    prereq = check_gnt_prerequisites(shipment)
    gnt_data = prereq.get("data") or {}
    missing = list(prereq.get("missing") or [])

    if prereq.get("no_payable"):
        return _result(
            "gnt_generate",
            sid,
            False,
            "Không có nghĩa vụ thuế phải nộp qua GNT (Thuế NK và VAT đều bằng 0).",
            gate="NO_PAYABLE_AMOUNT",
        )

    # Taxpayer MST check: must not be empty or guessed
    if not gnt_data.get("taxpayer_tax_code"):
        if "Mã số thuế (MST)" not in missing:
            missing.append("Mã số thuế (MST)")

    if missing:
        return _result(
            "gnt_generate",
            sid,
            False,
            f"Chưa đủ điều kiện tạo GNT. Thiếu: {', '.join(missing)}",
            gate="BLOCKED_MISSING_PREREQUISITES",
            missing=missing,
        )

    revision_state = _next_gnt_revision(sid)
    if not revision_state.get("ok"):
        return _result(
            "gnt_generate", sid, False,
            rd.text(revision_state.get("error")) or "Không xác định được revision GNT bền vững.",
            gate="GNT_REVISION_READ_FAILED", failClosed=True,
        )
    logical_document_id = rd.text(revision_state.get("document_id"))
    rev = int(revision_state["revision"])
    record_id = f"{logical_document_id}::R{rev}"

    try:
        raw_bytes = build_gnt_workbook(gnt_data)
    except Exception as exc:
        return _result(
            "gnt_generate",
            sid,
            False,
            f"Lỗi khi tạo Giấy Nộp Thuế: {exc}",
            gate="FAILED_GENERATION",
        )

    is_office = raw_bytes[:2] == b"PK"
    tk_no = gnt_data.get("tk_no", "")
    file_name = f"GNT_{sid}_{tk_no}.xlsx" if tk_no else f"GNT_{sid}.xlsx"

    from views import logi_c1
    from core.shipment_attachments import upload_attachment

    actor_name = ""
    if hasattr(st, "session_state") and "current_user" in st.session_state:
        actor_name = str(
            st.session_state["current_user"].get("display_name")
            or st.session_state["current_user"].get("username")
            or ""
        )

    attachment_outcome = upload_attachment(
        shipment_id=sid,
        category="customs",
        file_name=file_name,
        mime=logi_c1._MIME_XLSX,
        data=raw_bytes,
        uploaded_by=_actor(),
        declared_size=len(raw_bytes),
        shipment_context=shipment,
    )
    attachment_record = attachment_outcome.get("record") or {}
    if not attachment_outcome.get("ok"):
        return _generated_attachment_failure(
            "gnt_generate", sid, attachment_outcome,
            documentId=logical_document_id, recordId=record_id,
            revision=rev, fileName=file_name,
        )
    if not isinstance(attachment_record, Mapping) or not rd.text(attachment_record.get("id")):
        return _generated_attachment_failure(
            "gnt_generate", sid,
            {"code": "ATTACHMENT_READBACK_UNPROVEN", "error": "Kho chứng từ báo thành công nhưng thiếu hồ sơ tệp canonical."},
            documentId=logical_document_id, recordId=record_id,
            revision=rev, fileName=file_name,
        )
    attachment_view = _project_generated_attachment(attachment_outcome)

    now_iso = datetime.now(timezone.utc).isoformat()
    gnt_metadata = {
        "id": record_id,
        "document_id": logical_document_id,
        "document_type": "GNT",
        "shipment_id": sid,
        "contract_id": "",
        "parent_contract_id": None,
        "counterparty_id": "",
        "template_hash": "",
        "generation_revision": rev,
        "revision": rev,
        "status": "GENERATED",
        "generated_at": now_iso,
        "generated_by": actor_name or _actor(),
        "source_snapshot": {
            key: gnt_data.get(key)
            for key in (
                "tk_no", "tk_date", "taxpayer_name", "taxpayer_tax_code",
                "taxpayer_address", "import_duty_amount", "import_vat_amount",
            )
        },
        "source_reference": f"GNT:{sid}",
        "output_file_name": file_name,
        "output_hash": hashlib.sha256(raw_bytes).hexdigest(),
        "supersedes_document_id": None,
        "superseded_by_document_id": None,
    }
    metadata_outcome = _persist_generated_docgen_metadata(gnt_metadata)
    if not metadata_outcome.get("ok"):
        return _result(
            "gnt_generate", sid, False,
            rd.text(metadata_outcome.get("error")) or "Không lưu được metadata GNT.",
            gate="GNT_REVISION_COLLISION" if metadata_outcome.get("collision") else "GNT_METADATA_FAILED",
            failClosed=True, attachmentPersisted=True, partialDurable=True,
            documentId=logical_document_id, recordId=record_id, revision=rev,
            attachment=attachment_view, metadataCommitted=bool(metadata_outcome.get("metadata_committed")),
            duplicate=bool(attachment_outcome.get("duplicate")),
            **_attachment_result_extras(sid),
        )

    session_cache_error = ""
    try:
        logi_c1.store_output(
            sid,
            record_id,
            {
                "file_name": file_name,
                "mime": logi_c1._MIME_XLSX,
                "bytes": raw_bytes,
                "document_type": "GNT",
                "revision": rev,
                "generated_at": now_iso,
                "generated_by": actor_name,
            },
        )
    except Exception as exc:  # noqa: BLE001 - durable state already proved
        session_cache_error = str(exc)

    return _result(
        "gnt_generate",
        sid,
        True,
        "Đã tạo Giấy Nộp Thuế (GNT) thành công.",
        gate="READY",
        persisted={
            "documentId": logical_document_id,
            "recordId": record_id,
            "attachmentId": rd.text(attachment_record.get("id")),
            "fileName": file_name,
            "revision": rev,
            "bytes": len(raw_bytes),
            "isOfficeFile": is_office,
            "tkNo": tk_no,
            "tkDate": gnt_data.get("tk_date"),
            "duty": gnt_data.get("import_duty_amount"),
            "vat": gnt_data.get("import_vat_amount"),
            "taxpayer": gnt_data.get("taxpayer_name"),
            "taxCode": gnt_data.get("taxpayer_tax_code"),
            "attachmentDuplicate": bool(attachment_outcome.get("duplicate")),
            "sessionCachePersisted": not bool(session_cache_error),
        },
        attachment=attachment_view,
        sessionCacheError=session_cache_error,
        readback=_projection_for(read_shipment(sid) or {}),
        audit=_audit_trail(sid),
    )


_HANDLERS = {
    "shipment_field_save": _handle_field_save,
    "shipment_customer_save": _handle_shipment_customer_save,
    "shipment_transport_save": _handle_shipment_transport_save,
    "shipment_profile_save": _handle_shipment_profile_save,
    "delivery_confirm": _handle_delivery_confirm,
    "finance_actual_save": _handle_finance_actual_save,
    "payment_record": _handle_payment_record,
    "payment_correction": _handle_payment_correction,
    "shipment_create": _handle_shipment_create,
    "pxk_generate": _handle_pxk_generate,
    "gnt_generate": _handle_gnt_generate,
    "partner_payable_record": _handle_partner_payable_record,
    "partner_payment_record": _handle_partner_payment_record,
    "getfly_preview": _handle_getfly_preview,
    "getfly_import": _handle_getfly_import,
    # LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the bounded attachment pair
    # (upload + server-authoritative download). Same dispatcher, same seq replay
    # guard.
    "shipment_attachment_upload": _handle_shipment_attachment_upload,
    "attachment_download": _handle_attachment_download,
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


def dispatch(
    result: Any,
    *,
    allow_rerun: bool = True,
    is_callback: bool = False,
) -> list[dict[str, Any]]:
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

    LOGI_INTERACTION_LATENCY_REPAIR_01: In CALLBACK MODE (``is_callback=True``
    or ``allow_rerun=False``), dispatch executes as a prefix before the script
    body runs. The normal Streamlit rerun already scheduled by the component
    event will build the ONE fresh view model. Therefore, explicit second
    st.rerun() is skipped.
    """
    if is_callback:
        allow_rerun = False

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

    # LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — bounded READ-ONLY document
    # review path. It performs no business mutation (no shipment field, no
    # attachment row, no audit entry): the storage reads it does are only for
    # attachments the operator selected and that were proven to belong to this
    # shipment. This rerun only delivers the bounded ephemeral review result.
    review_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    review_outcomes = consume_document_review_triggers(review_session, result)
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    review_session["seq"])
    outcomes.extend(review_outcomes)

    # LOGI_USER_MANAGEMENT_01 — Admin-only account-management writes for
    # /nguoi-dung. Shares the same seq counter so a replayed trigger can never
    # double-write; every outcome (success or Admin/lockout/duplicate refusal)
    # is embedded in lastWrites exactly like every other write path.
    user_management_session = {"seq": st.session_state.get(SEQ_KEY, 0)}
    user_management_outcomes = logi_user_management.consume_user_management_triggers(
        user_management_session, result
    )
    st.session_state[SEQ_KEY] = max(st.session_state.get(SEQ_KEY, 0),
                                    user_management_session["seq"])
    outcomes.extend(user_management_outcomes)
    write_outcomes.extend(user_management_outcomes)

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
        # A read-only review outcome (bounded review OR honest refusal) also
        # needs ONE rerun so the settled requestId + result reach the component.
        or bool(review_outcomes)
    )
    if needs_rerun and allow_rerun:
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
